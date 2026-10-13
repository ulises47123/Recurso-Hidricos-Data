import os
import re
import subprocess
from datetime import datetime
from backend.database import get_db_connection
from backend.services.git_manager_service import (
    convertir_a_ssh_url,
    ejecutar_push_con_deploy_key,
    SSH_KEY_PATH
)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DESKTOP_DIR = os.path.join(os.path.expanduser("~"), "Desktop")
PAGE_DIR = os.path.join(DESKTOP_DIR, "recursoshidricos-acceso-web")
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
DEFAULT_REMOTE_URL = "https://github.com/ulises47123/Recursos-H-dricos.git"

def calcular_url_github_pages(remote_url: str) -> str:
    """
    Calcula la URL pública de GitHub Pages a partir del repositorio remoto.
    Ej: https://github.com/ulises47123/Recursos-H-dricos.git -> https://ulises47123.github.io/Recursos-H-dricos/
    """
    if not remote_url:
        return "https://ulises47123.github.io/Recursos-H-dricos/"
    
    match = re.search(r'github\.com[/:]([^/]+)/([^/\.]+)', remote_url)
    if match:
        user = match.group(1)
        repo = match.group(2)
        return f"https://{user}.github.io/{repo}/"
    return "https://ulises47123.github.io/Recursos-H-dricos/"

def generar_html_acceso(url_temporal: str) -> str:
    """
    Genera la página web institucional oficial de acceso remoto basada en el diseño propio del sistema.
    Incluye el logotipo oficial de Dirección Provincial de Recursos Hídricos, auto-redirección e indicadores de estado.
    """
    fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    backend_template = os.path.join(ROOT_DIR, "backend", "templates", "recurso_hidrico_template.html")
    
    # 1. Usar plantilla oficial construida en backend/templates
    if os.path.exists(backend_template):
        try:
            with open(backend_template, "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace("{url_dinamico}", url_temporal).replace("{fecha_actual}", fecha_actual)
            return content
        except Exception:
            pass

    # 2. Fallback embebido de emergencia con logotipo
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="3; url={url_temporal}">
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
    <a id="login-button" href="{url_temporal}" target="_blank" class="block w-full py-4 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-xl font-bold text-white shadow-lg hover:from-cyan-400 hover:to-blue-500">
      Iniciar Sesión en Recursos Hídricos
    </a>
  </div>
</body>
</html>"""

def obtener_config_github_sync() -> dict:
    """Obtiene la configuración completa de sincronización con Git/GitHub Pages."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT clave, valor FROM configuracion 
            WHERE clave IN (
                'github_repo_dir', 'github_sync_enabled', 'github_remote_url', 
                'github_branch', 'github_token', 'github_last_sync', 
                'github_last_url', 'github_push_ok', 'github_pages_url'
            )
        """)
        cfgs = dict(cursor.fetchall())
        conn.close()
    except Exception:
        cfgs = {}

    default_dir = PAGE_DIR
    remote_url = cfgs.get("github_remote_url") or DEFAULT_REMOTE_URL
    pages_url = cfgs.get("github_pages_url") or calcular_url_github_pages(remote_url)

    return {
        "repo_dir": cfgs.get("github_repo_dir") or default_dir,
        "enabled": cfgs.get("github_sync_enabled", "1") == "1",
        "remote_url": remote_url,
        "branch": cfgs.get("github_branch", "main"),
        "pages_url": pages_url,
        "has_token": bool(cfgs.get("github_token")),
        "last_sync": cfgs.get("github_last_sync", ""),
        "last_url": cfgs.get("github_last_url", ""),
        "push_ok": cfgs.get("github_push_ok", "0") == "1"
    }

def guardar_config_github_sync(data: dict) -> dict:
    """Guarda la configuración de sincronización con Git/GitHub Pages."""
    conn = get_db_connection()
    cursor = conn.cursor()
    for k, v in data.items():
        cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)", (k, str(v)))
    
    if "github_remote_url" in data:
        p_url = calcular_url_github_pages(data["github_remote_url"])
        cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('github_pages_url', ?)", (p_url,))

    conn.commit()
    res = obtener_config_github_sync()
    res["success"] = True
    return res

def preparar_repositorio_git(target_dir: str, remote_url: str, branch: str = "main") -> bool:
    """Inicializa el repositorio Git si no existe y asegura que el remoto y branch estén configurados."""
    os.makedirs(target_dir, exist_ok=True)
    git_dir = os.path.join(target_dir, ".git")

    if not os.path.exists(git_dir):
        try:
            subprocess.run(["git", "init", "-b", branch], cwd=target_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "config", "user.name", "DPRH AutoSync"], cwd=target_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "config", "user.email", "sistema@recursoshidricos.jujuy.gob.ar"], cwd=target_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if remote_url:
                subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=target_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"[Git Init Warning] {e}")
            return False
    else:
        if remote_url:
            try:
                subprocess.run(["git", "remote", "set-url", "origin", remote_url], cwd=target_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        return True

def sincronizar_link_en_repo(url_temporal: str, git_repo_dir: str = None) -> dict:
    """
    Escribe el HTML con la URL temporal y realiza commit/push a GitHub Pages usando la Deploy Key SSH.
    Garantiza que la base de datos y el backend nunca se suban, subiendo únicamente la página de acceso.
    """
    cfg = obtener_config_github_sync()
    if not cfg["enabled"]:
        return {"success": True, "skipped": True, "mensaje": "Sincronización Git deshabilitada."}

    if git_repo_dir:
        target_dir = git_repo_dir
    else:
        target_dir = cfg["repo_dir"] if (cfg.get("repo_dir") and os.path.exists(os.path.join(cfg.get("repo_dir"), ".git"))) else PAGE_DIR
    remote_url = cfg["remote_url"]
    branch = cfg["branch"]
    html_content = generar_html_acceso(url_temporal)

    # 1. Escribir index.html en target_dir
    os.makedirs(target_dir, exist_ok=True)
    html_file = os.path.join(target_dir, "index.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Copiar recursos estáticos (logo y favicon)
    import shutil
    logo_src = os.path.join(ROOT_DIR, "frontend", "img", "logo.png")
    favicon_src = os.path.join(ROOT_DIR, "frontend", "img", "favicon.ico")
    if os.path.exists(logo_src):
        try:
            shutil.copy2(logo_src, os.path.join(target_dir, "logo.png"))
        except Exception:
            pass
    if os.path.exists(favicon_src):
        try:
            shutil.copy2(favicon_src, os.path.join(target_dir, "favicon.ico"))
        except Exception:
            pass

    # 2. Escribir también en docs/index.html del proyecto actual (por si se utiliza /docs en el repo)
    try:
        os.makedirs(DOCS_DIR, exist_ok=True)
        docs_file = os.path.join(DOCS_DIR, "index.html")
        with open(docs_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        if os.path.exists(logo_src):
            shutil.copy2(logo_src, os.path.join(DOCS_DIR, "logo.png"))
        if os.path.exists(favicon_src):
            shutil.copy2(favicon_src, os.path.join(DOCS_DIR, "favicon.ico"))
    except Exception:
        pass

    # 3. Preparar repo y hacer commit
    preparar_repositorio_git(target_dir, remote_url, branch)

    commit_hecho = False
    push_exitoso = False
    commit_msg = f"Auto-sync Cloudflare Link: {url_temporal} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"

    if os.path.exists(os.path.join(target_dir, ".git")):
        try:
            subprocess.run(["git", "add", "index.html", "logo.png", "favicon.ico"], cwd=target_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            res_commit = subprocess.run(["git", "commit", "-m", commit_msg], cwd=target_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res_commit.returncode == 0 or "nothing to commit" in res_commit.stdout or "nothing to commit" in res_commit.stderr:
                commit_hecho = True

            # 4. Push prioritario con Deploy Key SSH (sin diálogos interactivos)
            remote_ssh = convertir_a_ssh_url(remote_url)
            if os.path.exists(SSH_KEY_PATH):
                res_ssh = ejecutar_push_con_deploy_key(target_dir, remote_ssh, branch=f"HEAD:{branch}")
                push_exitoso = res_ssh.get("success", False)
                # Intentar también sincronizar con 'main' en el repo de acceso web
                try:
                    ejecutar_push_con_deploy_key(target_dir, remote_ssh, branch="HEAD:main")
                except Exception:
                    pass

            # Fallback opcional por token HTTPS si no hay Deploy Key o falló
            if not push_exitoso:
                conn_tok = get_db_connection()
                c_tok = conn_tok.cursor()
                c_tok.execute("SELECT valor FROM configuracion WHERE clave = 'github_token'")
                row_tok = c_tok.fetchone()
                conn_tok.close()
                if row_tok and row_tok[0] and row_tok[0].strip() and remote_url.startswith("https://"):
                    token = row_tok[0].strip()
                    push_remote = remote_url.replace("https://", f"https://{token}@")
                    env = os.environ.copy()
                    env["GIT_TERMINAL_PROMPT"] = "0"
                    env["GCM_INTERACTIVE"] = "never"
                    push_cmd = ["git", "push", "-u", push_remote, f"HEAD:{branch}"]
                    res_push = subprocess.run(push_cmd, cwd=target_dir, timeout=12, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
                    push_exitoso = (res_push.returncode == 0)
        except Exception as e:
            print(f"[Git Sync Warning] {e}")

    # 5. Guardar último estado de sync en BD
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('github_last_sync', ?)", (now_str,))
        cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('github_last_url', ?)", (url_temporal,))
        cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('github_push_ok', ?)", ("1" if push_exitoso else "0",))
        cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('github_pages_url', ?)", (cfg["pages_url"],))
        conn.commit()
        conn.close()
    except Exception:
        pass

    return {
        "success": True,
        "html_path": html_file,
        "url": url_temporal,
        "pages_url": cfg["pages_url"],
        "commit_hecho": commit_hecho,
        "push_exitoso": push_exitoso
    }

def reintentar_push_fallidos() -> dict:
    """Intenta un git push a GitHub si el último push había fallado o quedó pendiente."""
    try:
        cfg = obtener_config_github_sync()
        if not cfg["enabled"]:
            return {"success": True, "reintentado": False, "mensaje": "Sync deshabilitado"}

        repo_dir = cfg["repo_dir"] if (cfg.get("repo_dir") and os.path.exists(cfg.get("repo_dir"))) else PAGE_DIR
        branch = cfg["branch"]
        remote_url = cfg["remote_url"]

        if os.path.exists(os.path.join(repo_dir, ".git")):
            subprocess.run(["git", "add", "index.html", "logo.png", "favicon.ico"], cwd=repo_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            commit_msg = f"Retry push Cloudflare Link ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=repo_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            remote_ssh = convertir_a_ssh_url(remote_url)
            push_exitoso = False
            if os.path.exists(SSH_KEY_PATH):
                res_ssh = ejecutar_push_con_deploy_key(repo_dir, remote_ssh, branch=f"HEAD:{branch}")
                push_exitoso = res_ssh.get("success", False)

            if not push_exitoso:
                conn_tok = get_db_connection()
                c_tok = conn_tok.cursor()
                c_tok.execute("SELECT valor FROM configuracion WHERE clave = 'github_token'")
                row_tok = c_tok.fetchone()
                conn_tok.close()
                if row_tok and row_tok[0] and row_tok[0].strip() and remote_url.startswith("https://"):
                    token = row_tok[0].strip()
                    push_remote = remote_url.replace("https://", f"https://{token}@")
                    env = os.environ.copy()
                    env["GIT_TERMINAL_PROMPT"] = "0"
                    env["GCM_INTERACTIVE"] = "never"
                    res_push = subprocess.run(["git", "push", "-u", push_remote, f"HEAD:{branch}"], cwd=repo_dir, timeout=12, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
                    push_exitoso = (res_push.returncode == 0)

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('github_push_ok', ?)", ("1" if push_exitoso else "0",))
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('github_last_sync', ?)", (now_str,))
            conn.commit()
            conn.close()

            return {
                "success": True,
                "reintentado": True,
                "push_exitoso": push_exitoso,
                "pages_url": cfg["pages_url"],
                "mensaje": "Push exitoso a GitHub Pages." if push_exitoso else "Push pendiente (verifique credenciales o conexión a GitHub)."
            }
    except Exception as e:
        print(f"[Git Retry Warning] {e}")
        return {"success": False, "reintentado": True, "error": str(e)}

    return {"success": True, "reintentado": False}
