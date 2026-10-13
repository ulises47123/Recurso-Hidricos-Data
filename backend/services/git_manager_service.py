import os
import re
import sys
import struct
import platform
import tempfile
import urllib.request
import subprocess
from datetime import datetime
from backend.database import get_db_connection

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEPLOY_DIR = os.path.join(ROOT_DIR, ".ssh_deploy")
SSH_KEY_PATH = os.path.join(DEPLOY_DIR, "id_ed25519")
SSH_KEY_PUB_PATH = SSH_KEY_PATH + ".pub"
DEFAULT_REPO_URL = "https://github.com/ulises47123/Recursos-H-dricos.git"

def obtener_arquitectura() -> str:
    """Detecta si la máquina es de 64-bit o 32-bit."""
    is_64 = struct.calcsize("P") * 8 == 64 or "64" in platform.machine() or "AMD64" in os.environ.get("PROCESSOR_ARCHITECTURE", "")
    return "64-bit" if is_64 else "32-bit"

def verificar_git_instalado() -> dict:
    """Verifica si Git está instalado y disponible en el sistema."""
    arch = obtener_arquitectura()
    try:
        res = subprocess.run(["git", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        if res.returncode == 0:
            version_str = res.stdout.strip()
            return {
                "instalado": True,
                "version": version_str,
                "arquitectura": arch
            }
    except Exception:
        pass

    # Buscar en rutas estándar de Windows si no está en PATH
    rutas_comunes = [
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\cmd\git.exe")
    ]
    for r in rutas_comunes:
        if os.path.exists(r):
            # Agregar al PATH del proceso actual
            git_bin_dir = os.path.dirname(r)
            if git_bin_dir not in os.environ["PATH"]:
                os.environ["PATH"] = git_bin_dir + os.pathsep + os.environ["PATH"]
            return {
                "instalado": True,
                "version": f"Git detectado en {r}",
                "arquitectura": arch,
                "ruta_ejecutable": r
            }

    return {
        "instalado": False,
        "version": None,
        "arquitectura": arch
    }

def instalar_git_sistema() -> dict:
    """
    Descarga e instala Git para Windows automáticamente según la arquitectura de la máquina (64 o 32 bits).
    Ejecución 100% silenciosa y sin intervención en PowerShell.
    """
    arch = obtener_arquitectura()
    
    # 1. Intentar mediante winget primero
    try:
        res_winget = subprocess.run(
            ["winget", "install", "--id", "Git.Git", "-e", "--source", "winget", "--accept-source-agreements", "--accept-package-agreements", "--silent"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=180
        )
        if res_winget.returncode == 0:
            return {"success": True, "mensaje": "Git instalado con éxito en el sistema mediante Windows Package Manager (winget)."}
    except Exception:
        pass

    # 2. Descarga directa oficial de Git for Windows
    url_descarga = (
        "https://github.com/git-for-windows/git/releases/latest/download/Git-64-bit.exe"
        if arch == "64-bit" else
        "https://github.com/git-for-windows/git/releases/latest/download/Git-32-bit.exe"
    )

    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, f"Git-Installer-{arch}.exe")

    try:
        urllib.request.urlretrieve(url_descarga, installer_path)
        if not os.path.exists(installer_path) or os.path.getsize(installer_path) < 1000000:
            return {"success": False, "error": "No se pudo descargar el instalador oficial de Git."}

        # Ejecución silenciosa oficial de Git para Windows
        cmd = [
            installer_path,
            "/VERYSILENT",
            "/NORESTART",
            "/NOCANCEL",
            "/SP-",
            "/CLOSEAPPLICATIONS",
            "/RESTARTAPPLICATIONS",
            "/COMPONENTS=icons,ext\\reg\\shellhere,assoc,assoc_sh"
        ]
        res_install = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
        if res_install.returncode == 0:
            # Re-verificar
            rutas_posibles = [
                r"C:\Program Files\Git\cmd",
                r"C:\Program Files (x86)\Git\cmd"
            ]
            for rp in rutas_posibles:
                if os.path.exists(rp) and rp not in os.environ["PATH"]:
                    os.environ["PATH"] = rp + os.pathsep + os.environ["PATH"]
            return {"success": True, "mensaje": f"Git ({arch}) descargado e instalado exitosamente."}
        else:
            return {"success": False, "error": f"El instalador finalizó con código {res_install.returncode}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def convertir_a_ssh_url(url: str) -> str:
    """Convierte una URL de repositorio GitHub HTTPS a formato SSH."""
    if not url:
        url = DEFAULT_REPO_URL
    if url.startswith("git@github.com:"):
        return url
    match = re.search(r'github\.com[/:]([^/]+)/([^/\.]+)', url)
    if match:
        user = match.group(1)
        repo = match.group(2)
        return f"git@github.com:{user}/{repo}.git"
    return "git@github.com:ulises47123/Recursos-H-dricos.git"

def obtener_repo_url() -> str:
    """Obtiene la URL configurada del repositorio GitHub de la base de datos o retorna la default."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT valor FROM configuracion WHERE clave = 'github_remote_url'")
        row = c.fetchone()
        conn.close()
        return row[0].strip() if row and row[0] else DEFAULT_REPO_URL
    except Exception:
        return DEFAULT_REPO_URL

def guardar_repo_url(url: str) -> dict:
    """Guarda la nueva URL remota del repositorio en la base de datos y resetea la señal verde para requerir nueva prueba."""
    url = url.strip()
    if not url:
        return {"success": False, "error": "La URL del repositorio no puede estar vacía."}
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('github_remote_url', ?)", (url,))
        c.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('github_signal_ok', 'false')")
        conn.commit()
        conn.close()
        return {"success": True, "mensaje": "URL del repositorio actualizada correctamente."}
    except Exception as e:
        return {"success": False, "error": f"Error al guardar URL del repositorio: {e}"}

def obtener_deploy_keys_url(repo_url: str) -> str:
    """Genera el enlace web directo a la página de Deploy Keys del repositorio en GitHub."""
    match = re.search(r'github\.com[/:]([^/]+)/([^/\.]+)', repo_url or DEFAULT_REPO_URL)
    if match:
        user = match.group(1)
        repo = match.group(2)
        return f"https://github.com/{user}/{repo}/settings/keys"
    return "https://github.com/ulises47123/Recursos-H-dricos/settings/keys"

def obtener_o_generar_deploy_key() -> dict:
    """
    Obtiene la llave SSH Deploy Key existente o genera un nuevo par ed25519 de forma 100% desatendida.
    """
    os.makedirs(DEPLOY_DIR, exist_ok=True)
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT valor FROM configuracion WHERE clave = 'github_remote_url'")
    row = c.fetchone()
    conn.close()
    remote_url = row[0].strip() if row and row[0] else DEFAULT_REPO_URL

    if not os.path.exists(SSH_KEY_PATH) or not os.path.exists(SSH_KEY_PUB_PATH):
        try:
            # Generar llave ed25519 sin contraseña
            cmd = [
                "ssh-keygen",
                "-t", "ed25519",
                "-C", "dprh-recursos-hidricos-deploy-key",
                "-f", SSH_KEY_PATH,
                "-N", ""
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            if res.returncode != 0:
                # Fallback a RSA si el sistema no soporta ed25519
                cmd_rsa = [
                    "ssh-keygen",
                    "-t", "rsa",
                    "-b", "4096",
                    "-C", "dprh-recursos-hidricos-deploy-key",
                    "-f", SSH_KEY_PATH,
                    "-N", ""
                ]
                subprocess.run(cmd_rsa, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        except Exception as e:
            return {"success": False, "error": f"Error al generar llave SSH: {e}"}

    # Leer la clave pública
    clave_publica = ""
    if os.path.exists(SSH_KEY_PUB_PATH):
        with open(SSH_KEY_PUB_PATH, "r", encoding="utf-8") as f:
            clave_publica = f.read().strip()

    # Obtener fingerprint
    fingerprint = ""
    try:
        res_fp = subprocess.run(["ssh-keygen", "-lf", SSH_KEY_PUB_PATH], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res_fp.returncode == 0:
            fingerprint = res_fp.stdout.strip()
    except Exception:
        pass

    deploy_url = obtener_deploy_keys_url(remote_url)
    ssh_url = convertir_a_ssh_url(remote_url)

    return {
        "success": True,
        "clave_publica": clave_publica,
        "fingerprint": fingerprint,
        "deploy_url": deploy_url,
        "remote_url": remote_url,
        "ssh_url": ssh_url,
        "ruta_privada": SSH_KEY_PATH
    }

def resetear_deploy_key() -> dict:
    """
    Elimina la llave SSH privada y pública existente y genera un nuevo par de llaves ed25519 desde cero.
    """
    try:
        if os.path.exists(SSH_KEY_PATH):
            os.remove(SSH_KEY_PATH)
        if os.path.exists(SSH_KEY_PUB_PATH):
            os.remove(SSH_KEY_PUB_PATH)
    except Exception as e:
        return {"success": False, "error": f"No se pudieron eliminar las llaves anteriores: {e}"}

    # Desactivar la señal verde previa en la base de datos
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('github_signal_ok', 'false')")
        conn.commit()
        conn.close()
    except Exception:
        pass

    return obtener_o_generar_deploy_key()

def probar_conexion_ssh_github() -> dict:
    """
    Prueba si GitHub reconoce y acepta la Deploy Key para el repositorio.
    """
    if not os.path.exists(SSH_KEY_PATH):
        obtener_o_generar_deploy_key()

    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "never"

    cmd = [
        "ssh",
        "-i", SSH_KEY_PATH,
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=10",
        "-T", "git@github.com"
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, timeout=12)
        salida = (res.stdout + "\n" + res.stderr).strip()

        # GitHub responde con éxito: "Hi <usuario>/<repo>! You've successfully authenticated..." (código de salida 1)
        if "successfully authenticated" in salida:
            return {
                "success": True,
                "autenticado": True,
                "mensaje": "¡Conexión SSH exitosa! La Deploy Key está activa y autorizada en GitHub.",
                "detalle": salida
            }
        elif "Permission denied (publickey)" in salida:
            return {
                "success": False,
                "autenticado": False,
                "mensaje": "Permiso denegado. Aún no has agregado la llave en GitHub Deploy Keys o falta marcar la casilla 'Allow write access'.",
                "detalle": salida
            }
        else:
            return {
                "success": False,
                "autenticado": False,
                "mensaje": f"Respuesta de GitHub: {salida}",
                "detalle": salida
            }
    except subprocess.TimeoutExpired:
        return {"success": False, "autenticado": False, "mensaje": "Tiempo de espera agotado al conectar con GitHub."}
    except Exception as e:
        return {"success": False, "autenticado": False, "mensaje": f"Error probando conexión: {e}"}

def ejecutar_push_con_deploy_key(repo_dir: str, remote_ssh_url: str, branch: str = "main") -> dict:
    """
    Ejecuta un git push forzando el uso de la llave SSH privada (Deploy Key) de forma desatendida.
    """
    if not os.path.exists(SSH_KEY_PATH):
        return {"success": False, "error": "No existe la llave SSH privada del sistema."}

    # Configurar comando SSH específico
    # Normalizar ruta para evitar problemas con backslashes en OpenSSH
    key_path_normalized = SSH_KEY_PATH.replace("\\", "/")
    ssh_cmd = f'ssh -i "{key_path_normalized}" -o StrictHostKeyChecking=no -o BatchMode=yes'

    env = os.environ.copy()
    env["GIT_SSH_COMMAND"] = ssh_cmd
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "never"

    try:
        # Asegurar remote SSH
        subprocess.run(["git", "remote", "set-url", "origin", remote_ssh_url], cwd=repo_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Ejecutar push
        cmd_push = ["git", "push", "-u", "origin", branch]
        res = subprocess.run(cmd_push, cwd=repo_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, timeout=30)
        
        if res.returncode == 0:
            return {"success": True, "mensaje": f"Push completado exitosamente a la rama {branch}."}
        else:
            err = res.stderr or res.stdout
            return {"success": False, "error": err.strip()}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Tiempo de espera agotado al enviar los cambios a GitHub."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def subir_todo_el_proyecto_github(mensaje_commit: str = "") -> dict:
    """
    Realiza commit y push del proyecto principal (rama main) a GitHub utilizando la Deploy Key SSH.
    """
    git_check = verificar_git_instalado()
    if not git_check["instalado"]:
        return {"success": False, "error": "Git no está instalado en este equipo."}

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT valor FROM configuracion WHERE clave = 'github_remote_url'")
    row = c.fetchone()
    conn.close()
    remote_url = row[0].strip() if row and row[0] else DEFAULT_REPO_URL
    remote_ssh = convertir_a_ssh_url(remote_url)

    # Preparar commit
    if not mensaje_commit or not mensaje_commit.strip():
        mensaje_commit = f"Actualización institucional de Recursos Hídricos ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"

    try:
        subprocess.run(["git", "add", "."], cwd=ROOT_DIR, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", mensaje_commit], cwd=ROOT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # Push con Deploy Key
    res_push = ejecutar_push_con_deploy_key(ROOT_DIR, remote_ssh, branch="main")
    return res_push

def subir_portal_github_pages() -> dict:
    """
    Genera la página HTML con la plantilla 'recurso hidrico.html' y la sube al repositorio remoto en las ramas gh-pages y main usando la Deploy Key SSH.
    """
    from backend.services import github_sync_service

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT valor FROM configuracion WHERE clave = 'github_last_url'")
    row = c.fetchone()
    conn.close()

    url_actual = row[0].strip() if row and row[0] else "https://recursos-hidricos.trycloudflare.com"

    from backend.services.github_sync_service import PAGE_DIR
    res_sync = github_sync_service.sincronizar_link_en_repo(url_actual, git_repo_dir=PAGE_DIR)
    if res_sync.get("push_exitoso"):
        return {
            "success": True,
            "mensaje": f"Página de acceso generada y publicada con éxito en GitHub Pages ({res_sync.get('pages_url')}).",
            "pages_url": res_sync.get("pages_url")
        }
    else:
        return {
            "success": False,
            "error": "El commit se realizó pero el push falló. Verifique la conexión o que la Deploy Key tenga marcado 'Allow write access' en GitHub."
        }
