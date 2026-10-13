# Sistema DPRH Jujuy — Gestión de Personal

Sistema integral de gestión de personal para la Dirección Provincial de Recursos Hídricos de Jujuy (DPRH Jujuy).

---

## 🚀 Arquitectura del Sistema y Seguridad

- **Frontend / Aplicación de Escritorio**: Electron wrapper cargando la interfaz cliente local o remota.
- **Backend API**: FastAPI (Python) ejecutándose en puerto `8000` con SQLite/PostgreSQL.
- **Acceso Remoto / Túnel**: Cloudflare Tunnel (`cloudflared`) enviando tráfico de lectura/escritura seguro.
- **Sincronización Automática**: Módulo de sincronización automática de estado y documentación (`docs/index.html`) publicado vía GitHub Pages / Git SSH.
- **Seguridad**:
  - Claves SSH sin passphrase (`.ssh_deploy/id_ed25519`) configuradas como Deploy Keys en GitHub con permiso de escritura.
  - Variable de entorno `GIT_SSH_COMMAND` apuntando a la clave privada del sistema sin requerir interacción por consola.
  - Subprocesos gestionados en segundo plano sin bloquiar el hilo principal.

---

## ⚙️ Arranque Automático en Windows (Servicio / Tarea Programada)

Para garantizar que el sistema inicie automáticamente al encender la PC o iniciar sesión en Windows:

### 1. Activar Arranque Automático
Ejecutar el script de registro con permisos de Administrador:
```cmd
scripts\registrar_arranque.bat
```
Este script utiliza `schtasks` para registrar la tarea programada `DPRH_Jujuy_ArranqueAutomatico` con nivel de privilegio `/RL HIGHEST` y activador `/SC ONLOGON`, vinculada a `iniciar_sistema.bat`.

### 2. Desactivar Arranque Automático
Si desea remover el arranque automático del sistema al iniciar sesión:
```cmd
scripts\desregistrar_arranque.bat
```
Este script elimina la tarea programada `DPRH_Jujuy_ArranqueAutomatico` de Windows de forma limpia e idempotente.

---

## 🧪 Verificación y Tests

Para ejecutar la suite completa de pruebas automatizadas:
```cmd
.\venv\Scripts\python -m pytest tests/ -v
```
