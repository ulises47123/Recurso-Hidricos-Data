"""
Lanzador de Túnel Seguro Cloudflare (pycloudflared)
Permite acceder al Sistema de Gestión de Personal DPRH desde cualquier lugar por Internet de forma segura y cifrada (HTTPS).
"""

import sys
import time
import subprocess
import re
from pathlib import Path
from pycloudflared.util import get_info, download

def main():
    print("=" * 65)
    print(" SISTEMA DPRH - INICIANDO TÚNEL SEGURO CLOUDFLARE")
    print("=" * 65)
    print("\nConectando con la red global de Cloudflare...")
    
    try:
        info = get_info()
        if not Path(info.executable).exists():
            print("Descargando binario de Cloudflare...")
            download(info)
            
        args = [
            info.executable, 
            "tunnel", 
            "--url", "https://127.0.0.1:8000", 
            "--no-tls-verify",
            "--heartbeat-interval", "5s",
            "--heartbeat-count", "5"
        ]
        
        proc = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            bufsize=1
        )
        
        url_pat = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
        found_url = None
        for _ in range(80):
            line = proc.stderr.readline()
            if not line:
                break
            m = url_pat.search(line)
            if m:
                found_url = m.group(0)
                break
                
        if not found_url:
            raise RuntimeError("No se pudo obtener la URL de Cloudflare")

        print("\n" + "=" * 65)
        print(" [OK] TÚNEL CLOUDFLARE ACTIVO Y CONECTADO A INTERNET")
        print("=" * 65)
        print(f"\n >>> URL Pública de Acceso Remoto: {found_url}")

        # Sincronización autónoma inmediata con GitHub Pages
        try:
            print("\n [AutoSync] Publicando enlace en GitHub Pages de forma autónoma...")
            from backend.services import github_sync_service
            res_sync = github_sync_service.sincronizar_link_en_repo(found_url, git_repo_dir=github_sync_service.PAGE_DIR)
            if res_sync.get("push_exitoso"):
                print(f" >>> GitHub Pages Actualizado con Éxito: {res_sync.get('pages_url')}")
            else:
                print(" >>> Commit realizado (Push pendiente o verifique Deploy Key).")
        except Exception as e_sync:
            print(f" [!] Advertencia al sincronizar con GitHub: {e_sync}")

        print("\n" + "=" * 65)
        print("Mantenga esta ventana ABIERTA para mantener el enlace en línea.")
        print("Presione CTRL + C para cerrar el túnel.\n")
        
        # Drenar continuamente la salida para que Windows no bloquee el proceso
        for line in proc.stderr:
            pass
            
    except KeyboardInterrupt:
        print("\n[!] Cerrando túnel Cloudflare...")
        if 'proc' in locals() and proc:
            proc.terminate()
    except Exception as e:
        print(f"\n[ERROR] No se pudo iniciar el túnel: {e}")
        input("\nPresione Enter para salir...")

if __name__ == "__main__":
    main()
