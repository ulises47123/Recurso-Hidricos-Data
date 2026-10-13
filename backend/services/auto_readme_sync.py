import os
import re
import sys
import atexit
import threading
import time
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

from backend.database import get_db_connection
from backend.services.git_manager_service import (
    obtener_o_generar_deploy_key,
    probar_conexion_ssh_github,
    convertir_a_ssh_url,
    DEFAULT_REPO_URL,
    SSH_KEY_PATH
)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GH_PAGES_DIR = os.path.join(ROOT_DIR, ".gh_pages_repo")

# Estado en memoria de subprocesos y sincronización
_proceso_tunel: Optional[subprocess.Popen] = None
_tunnel_url_actual: Optional[str] = None
_sync_lock = threading.Lock()
_ultimo_error_sync: Optional[str] = None
_hilo_daemon_activo = False

def _limpiar_proceso_tunel():
    """Detiene el proceso del túnel de Cloudflare en atexit o shutdown."""
    global _proceso_tunel, _tunnel_url_actual
    if _proceso_tunel is not None:
        try:
            _proceso_tunel.terminate()
            _proceso_tunel.wait(timeout=3)
        except Exception:
            try:
                _proceso_tunel.kill()
            except Exception:
                pass
        _proceso_tunel = None
    _tunnel_url_actual = None

atexit.register(_limpiar_proceso_tunel)

def tiene_senal_verde() -> bool:
    """Verifica si el flag github_signal_ok es true en la tabla configuracion."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM configuracion WHERE clave = 'github_signal_ok'")
        row = cursor.fetchone()
        conn.close()
        return bool(row and row[0] and row[0].strip().lower() in ("true", "1"))
    except Exception:
        return False

def guardar_senal_verde(estado: bool) -> None:
    """Persiste el flag github_signal_ok ('true' o 'false') en la tabla configuracion."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        val = "true" if estado else "false"
        cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('github_signal_ok', ?)", (val,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[AutoReadme] Error al guardar señal verde: {e}")

def obtener_llave_publica() -> str:
    """Retorna la clave pública ed25519 dedicada para Deploy Key (generándola si no existe)."""
    info = obtener_o_generar_deploy_key()
    return info.get("clave_publica", "")

def probar_conexion() -> dict:
    """
    Prueba la conexión SSH con GitHub usando la Deploy Key dedicada ed25519.
    Realiza prueba de autenticación y confirma permiso en el repo.
    Actualiza github_signal_ok en consecuencia.
    """
    key_info = obtener_o_generar_deploy_key()
    if not key_info.get("success"):
        guardar_senal_verde(False)
        return {"success": False, "mensaje": key_info.get("error", "No se pudo obtener/generar la llave SSH.")}

    ssh_res = probar_conexion_ssh_github()
    if not ssh_res.get("autenticado"):
        guardar_senal_verde(False)
        deploy_url = key_info.get("deploy_url", "https://github.com")
        msg = f"Permission denied (publickey). Configure la Deploy Key en GitHub: {deploy_url} con permiso de escritura."
        return {
            "success": False,
            "autenticado": False,
            "mensaje": msg,
            "deploy_url": deploy_url,
            "clave_publica": key_info.get("clave_publica", "")
        }

    # Intentar verificar si podemos sincronizar con gh-pages o commit de prueba
    guardar_senal_verde(True)
    return {
        "success": True,
        "autenticado": True,
        "mensaje": "Conexión SSH exitosa. Señal verde activada.",
        "clave_publica": key_info.get("clave_publica", ""),
        "deploy_url": key_info.get("deploy_url", "")
    }

def iniciar_tunel_cloudflare(timeout: int = 90) -> str:
    """
    Inicia o reutiliza el túnel cloudflared.exe tunnel --url https://127.0.0.1:8000.
    Captura la URL publica mediante regex https://[a-z0-9-]+\\.trycloudflare\\.com.
    """
    global _proceso_tunel, _tunnel_url_actual

    if _tunnel_url_actual and _proceso_tunel and _proceso_tunel.poll() is None:
        return _tunnel_url_actual

    # Limpiar cualquier instancia previa o colgada de cloudflared.exe para evitar WinError 32
    try:
        subprocess.run(["taskkill", "/IM", "cloudflared.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    from pycloudflared.util import get_info, download
    info = get_info()
    if not Path(info.executable).exists():
        download(info)

    cmd = [
        info.executable,
        "tunnel",
        "--url", "https://127.0.0.1:8000",
        "--no-tls-verify",
        "--heartbeat-interval", "5s",
        "--heartbeat-count", "5"
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        bufsize=1,
        errors="replace"
    )

    _proceso_tunel = proc

    url_regex = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
    found_url = None
    start_time = time.time()

    while time.time() - start_time < timeout:
        if proc.poll() is not None:
            break
        line = proc.stderr.readline()
        if not line:
            time.sleep(0.1)
            continue
        match = url_regex.search(line)
        if match:
            found_url = match.group(0)
            break

    if not found_url:
        _limpiar_proceso_tunel()
        raise RuntimeError("Timeout o error al obtener la URL del túnel Cloudflare.")

    _tunnel_url_actual = found_url

    # Guardar en BD para referencia del sistema
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('github_last_url', ?)", (found_url,))
        conn.commit()
        conn.close()
    except Exception:
        pass

    return found_url

def generar_readme_content(tunnel_url: Optional[str] = None, estado: str = "encendido") -> str:
    """Genera el contenido markdown EXACTO del README.md para el portal gh-pages con indicador de estado."""
    if estado == "encendido" and tunnel_url:
        return f"""<div align="center">
  <img src="logo.png" width="150" alt="Logo DPRH">
  
  # Dirección Provincial de Recursos Hídricos
  ### Gobierno de la Provincia de Jujuy

  [![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&pause=1000&color=00D2FF&center=true&vcenter=true&width=500&lines=Bienvenido+al+Sistema+DPRH;Gestion+de+Personal+y+Licencias;Acceso+Remoto+Seguro+Cloudflare)](https://git.io/typing-svg)

  [![Ver Proyecto](https://img.shields.io/badge/Ver_Proyecto-Acceder_al_Sistema-007ACC?style=for-the-badge&logo=cloudflare&logoColor=white)]({tunnel_url})

  <br><br>

  [![Estado](https://img.shields.io/badge/Servidor-Encendido_%E2%97%8F-2e7d32?style=for-the-badge)](https://recursoshidricos.jujuy.gob.ar)

  ---

  *Dirección Provincial de Recursos Hídricos - San Salvador de Jujuy, Argentina*
</div>
"""
    else:
        return f"""<div align="center">
  <img src="logo.png" width="150" alt="Logo DPRH">
  
  # Dirección Provincial de Recursos Hídricos
  ### Gobierno de la Provincia de Jujuy

  [![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&pause=1000&color=00D2FF&center=true&vcenter=true&width=500&lines=Bienvenido+al+Sistema+DPRH;Gestion+de+Personal+y+Licencias;Servidor+temporalmente+fuera+de+linea)](https://git.io/typing-svg)

  [![Servidor Apagado](https://img.shields.io/badge/Servidor-Apagado_%E2%97%8B-d32f2f?style=for-the-badge)](https://recursoshidricos.jujuy.gob.ar)

  <br><br>

  *El servidor local se encuentra actualmente apagado o fuera de línea. Estará disponible al iniciar el sistema en la estación central.*

  ---

  *Dirección Provincial de Recursos Hídricos - San Salvador de Jujuy, Argentina*
</div>
"""

def actualizar_readme_gh_pages(tunnel_url: Optional[str] = None, estado: str = "encendido") -> dict:
    """
    Clona o prepara el repo en gh-pages, actualiza README.md y realiza pull --ff-only
    seguido de push con --force-with-lease usando la clave SSH ed25519.
    """
    obtener_o_generar_deploy_key()
    os.makedirs(GH_PAGES_DIR, exist_ok=True)
    git_dir = os.path.join(GH_PAGES_DIR, ".git")

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT valor FROM configuracion WHERE clave = 'github_remote_url'")
    row = c.fetchone()
    conn.close()
    remote_url = row[0].strip() if row and row[0] else DEFAULT_REPO_URL
    remote_ssh = convertir_a_ssh_url(remote_url)

    key_path_norm = SSH_KEY_PATH.replace("\\", "/")
    ssh_cmd = f'ssh -i "{key_path_norm}" -o StrictHostKeyChecking=no -o BatchMode=yes'
    env = os.environ.copy()
    env["GIT_SSH_COMMAND"] = ssh_cmd
    env["GIT_TERMINAL_PROMPT"] = "0"

    # Preparar repositorio en gh-pages
    if not os.path.exists(git_dir):
        subprocess.run(["git", "clone", "-b", "gh-pages", remote_ssh, GH_PAGES_DIR], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not os.path.exists(git_dir):
            # Si no existe la rama gh-pages remotamente, inicializar localmente e intentar huérfana
            subprocess.run(["git", "init", "-b", "gh-pages"], cwd=GH_PAGES_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "remote", "add", "origin", remote_ssh], cwd=GH_PAGES_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Configurar usuario git
    subprocess.run(["git", "config", "user.name", "DPRH AutoSync"], cwd=GH_PAGES_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "sistema@recursoshidricos.jujuy.gob.ar"], cwd=GH_PAGES_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "remote", "set-url", "origin", remote_ssh], cwd=GH_PAGES_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Copiar logo.png
    import shutil
    logo_src = os.path.join(ROOT_DIR, "frontend", "img", "logo.png")
    if os.path.exists(logo_src):
        try:
            shutil.copy2(logo_src, os.path.join(GH_PAGES_DIR, "logo.png"))
        except Exception:
            pass

    # Escribir README.md
    readme_path = os.path.join(GH_PAGES_DIR, "README.md")
    readme_content = generar_readme_content(tunnel_url, estado=estado)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    # Escribir y copiar index.html para GitHub Pages
    index_html_path = os.path.join(GH_PAGES_DIR, "index.html")
    dest_url = tunnel_url if (estado == "encendido" and tunnel_url) else "#"
    status_text = "Servidor Corriendo" if estado == "encendido" else "Servidor Apagado"
    status_badge_color = "bg-emerald-500" if estado == "encendido" else "bg-rose-500"
    status_ping_color = "bg-emerald-400" if estado == "encendido" else "hidden"
    status_text_color = "text-emerald-400" if estado == "encendido" else "text-rose-400"

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  {"<meta http-equiv='refresh' content='3; url=" + dest_url + "'>" if estado == "encendido" and tunnel_url else ""}
  <title>Recursos Hídricos - Portal Oficial de Acceso</title>
  <link rel="icon" type="image/x-icon" href="favicon.ico">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4">
  <div class="max-w-md w-full bg-slate-900 p-8 rounded-3xl text-center border border-slate-700 shadow-2xl">
    <div class="flex justify-center mb-4">
      <img src="logo.png" alt="Logo DPRH" class="h-24 w-auto object-contain">
    </div>
    <div class="mb-3 text-xs font-semibold text-cyan-400">Gobierno de Jujuy – Dirección de Recursos Hídricos</div>
    <h1 class="text-2xl font-bold mb-3">Dirección de Recursos Hídricos</h1>
    <a id="login-button" href="{dest_url}" target="_blank" class="block w-full py-4 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-xl font-bold text-white shadow-lg hover:from-cyan-400 hover:to-blue-500 mb-6">
      {"Iniciar Sesión en Recursos Hídricos" if estado == "encendido" else "Servidor Temporalmente Apagado"}
    </a>
    
    <!-- Cartel de estado en la parte inferior -->
    <div id="status-card" class="mt-4 pt-4 border-t border-slate-800 flex items-center justify-center space-x-2">
      <span class="relative flex h-3 w-3">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full {status_ping_color} opacity-75"></span>
        <span class="relative inline-flex rounded-full h-3 w-3 {status_badge_color}"></span>
      </span>
      <span id="status-text" class="text-xs font-bold uppercase tracking-wider {status_text_color}">{status_text}</span>
    </div>
  </div>
</body>
</html>"""
    with open(index_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Copiar index.html actualizado también al directorio docs/ local
    try:
        docs_dir = os.path.join(ROOT_DIR, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        with open(os.path.join(docs_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_content)
    except Exception:
        pass

    # Pull --ff-only antes del commit/push
    try:
        subprocess.run(["git", "fetch", "origin", "gh-pages"], cwd=GH_PAGES_DIR, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "pull", "--ff-only", "origin", "gh-pages"], cwd=GH_PAGES_DIR, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # Commit
    subprocess.run(["git", "add", "README.md", "index.html", "logo.png"], cwd=GH_PAGES_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    commit_msg = f"Auto-Sync README Portal ({time.strftime('%Y-%m-%d %H:%M:%S')})"
    res_commit = subprocess.run(["git", "commit", "-m", commit_msg], cwd=GH_PAGES_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res_commit.returncode == 0:
        print(f"[AutoSync] Commit realizado con éxito: {commit_msg}")
    else:
        print(f"[AutoSync Info] Sin cambios nuevos en la plantilla o enlace. Omitiendo push innecesario.")
        return {"success": True, "mensaje": "Sin cambios pendientes de publicar."}

    # Push --force-with-lease
    print(f"[AutoSync] Ejecutando git push a gh-pages (URL túnel: {tunnel_url})...")
    push_cmd = ["git", "push", "--force-with-lease", "origin", "gh-pages"]
    try:
        res_push = subprocess.run(push_cmd, cwd=GH_PAGES_DIR, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=45)

        if res_push.returncode != 0:
            # Reintentar con -u si es la primera vez
            print(f"[AutoSync Warning] Primer intento de push falló ({res_push.stderr.strip()}). Reintentando con -u origin gh-pages...")
            push_cmd_u = ["git", "push", "--force-with-lease", "-u", "origin", "gh-pages"]
            res_push = subprocess.run(push_cmd_u, cwd=GH_PAGES_DIR, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=45)

        if res_push.returncode == 0:
            print(f"[AutoSync] Git Push realizado con éxito a gh-pages. README.md actualizado con badge: {tunnel_url}")
            return {"success": True, "mensaje": "README.md publicado exitosamente en gh-pages."}
        else:
            err = (res_push.stderr or res_push.stdout or "").strip()
            print(f"[AutoSync Error] Error al ejecutar git push (código {res_push.returncode}): {err}")
            return {"success": False, "error": f"Error al ejecutar git push: {err}"}
    except subprocess.TimeoutExpired:
        print("[AutoSync Error] Timeout (45s) alcanzado durante git push a gh-pages.")
        return {"success": False, "error": "Timeout durante git push a gh-pages."}
    except Exception as ex:
        print(f"[AutoSync Error] Excepción no controlada durante git push: {ex}")
        return {"success": False, "error": str(ex)}

def sincronizacion_automatica() -> dict:
    """
    Orquestador principal de Auto-README Sync:
    1. Verifica si tiene señal verde (github_signal_ok). Si no, no procede.
    2. Inicia/obtiene el túnel Cloudflare.
    3. Genera y actualiza README.md en gh-pages.
    """
    global _ultimo_error_sync
    with _sync_lock:
        if not tiene_senal_verde():
            _ultimo_error_sync = "Sin señal verde (Falta autorizar Deploy Key en GitHub)."
            return {
                "success": False,
                "reason": "sin_senal_verde",
                "mensaje": _ultimo_error_sync
            }

        try:
            tunnel_url = iniciar_tunel_cloudflare()
            res_readme = actualizar_readme_gh_pages(tunnel_url)
            if res_readme.get("success"):
                _ultimo_error_sync = None
                return {
                    "success": True,
                    "tunnel_url": tunnel_url,
                    "mensaje": "Sincronización de README.md completada con éxito."
                }
            else:
                _ultimo_error_sync = res_readme.get("error")
                return {
                    "success": False,
                    "reason": "error_push",
                    "mensaje": res_readme.get("error")
                }
        except Exception as e:
            _ultimo_error_sync = str(e)
            return {
                "success": False,
                "reason": "excepcion",
                "mensaje": str(e)
            }

def obtener_estado_sync() -> Dict[str, Any]:
    """Retorna el estado general de auto_readme_sync para ser consumido por la API/UI."""
    return {
        "github_signal_ok": tiene_senal_verde(),
        "tunnel_url": _tunnel_url_actual,
        "ultimo_error": _ultimo_error_sync,
        "llave_publica": obtener_llave_publica()
    }

def iniciar_demonio_auto_readme(intervalo_base: int = 600, max_intervalo: int = 1800) -> None:
    """Inicia el hilo daemon de sincronización periódica con un intervalo optimizado de 10 minutos."""
    global _hilo_daemon_activo
    if _hilo_daemon_activo:
        return

    _hilo_daemon_activo = True

    def _bucle_daemon():
        delay = intervalo_base
        while True:
            try:
                res = sincronizacion_automatica()
                if res.get("success"):
                    delay = intervalo_base  # Reset a 10 minutos
                else:
                    delay = min(delay * 2, max_intervalo)  # Backoff si hay fallo
            except Exception as e:
                print(f"[AutoReadme Daemon Warning] {e}")
                delay = min(delay * 2, max_intervalo)

            time.sleep(delay)

    t = threading.Thread(target=_bucle_daemon, daemon=True, name="AutoReadmeSyncDaemon")
    t.start()

def marcar_servidor_apagado() -> None:
    """Actualiza el README.md en gh-pages marcando el servidor como apagado/fuera de línea."""
    try:
        if tiene_senal_verde():
            print("[AutoSync Shutdown] Actualizando estado a 'Servidor Apagado' en GitHub Pages...")
            actualizar_readme_gh_pages(None, estado="apagado")
    except Exception as e:
        print(f"[AutoSync Shutdown Warning] No se pudo marcar como apagado: {e}")

# Registrar handler de apagado del proceso
import atexit
atexit.register(marcar_servidor_apagado)

