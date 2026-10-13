import os
import sys
import shutil
import subprocess

def limpiar_datos_edge():
    print("=" * 60)
    print(" LIMPIADOR DE DATOS DE NAVEGADOR MICROSOFT EDGE")
    print("=" * 60)

    # 1. Cerrar procesos de Edge si están abiertos
    print("\n[1/2] Cerrando procesos de Microsoft Edge...")
    subprocess.run(["taskkill", "/f", "/im", "msedge.exe"], capture_output=True, text=True)

    # 2. Rutas del perfil predeterminado de Edge
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    edge_default = os.path.join(local_appdata, "Microsoft", "Edge", "User Data", "Default")

    if not os.path.exists(edge_default):
        print("[Aviso] No se encontró el directorio de usuario de Microsoft Edge.")
        return

    print(f"\n[2/2] Borrando caché, cookies, historial y almacenamiento local en:\n >>> {edge_default}\n")

    carpetas = [
        "Cache", "Code Cache", "GPUCache", "Local Storage", 
        "Session Storage", "WebStorage", "IndexedDB", "Service Worker"
    ]
    archivos = [
        "History", "Visited Links", "Web Data", "Favicons", "Top Sites",
        os.path.join("Network", "Cookies"), "Cookies"
    ]

    borrados = 0
    for c in carpetas:
        target = os.path.join(edge_default, c)
        if os.path.exists(target):
            try:
                shutil.rmtree(target, ignore_errors=True)
                print(f" [OK] Carpeta eliminada: {c}")
                borrados += 1
            except Exception as e:
                print(f" [Aviso] No se pudo borrar {c}: {e}")

    for f in archivos:
        target = os.path.join(edge_default, f)
        if os.path.exists(target):
            try:
                os.remove(target)
                print(f" [OK] Archivo eliminado: {f}")
                borrados += 1
            except Exception as e:
                print(f" [Aviso] No se pudo borrar {f}: {e}")

    print("\n" + "=" * 60)
    print(f" ¡ÉXITO! Se borraron {borrados} elementos de datos de Microsoft Edge.")
    print("=" * 60)

if __name__ == "__main__":
    limpiar_datos_edge()
