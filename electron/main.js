/**
 * electron/main.js
 * Controlador principal de Electron.
 *
 * Responsabilidades:
 *  - Garantizar UNA SOLA instancia de la app (single instance lock)
 *  - Arrancar el backend Python (FastAPI/Uvicorn) como proceso hijo
 *  - Esperar a que el backend responda antes de abrir la ventana
 *  - Bandeja del sistema (Tray) y Notificaciones nativas con logo
 *  - Soporte de inicio en segundo plano al encender la PC (--hidden)
 *  - Cerrar el backend de forma segura al salir
 */

'use strict';


const { app, BrowserWindow, dialog, Tray, Menu, Notification, ipcMain, shell } = require('electron');
app.commandLine.appendSwitch('ignore-certificate-errors');
const path   = require('path');
const { spawn, execSync } = require('child_process');
const http   = require('http');
const https  = require('https');
const fs     = require('fs');

// â”€â”€â”€ ConfiguraciÃ³n â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const PYTHON_PORT  = 8000;
const SERVER_URL   = `https://127.0.0.1:${PYTHON_PORT}`;
const MAX_RETRIES  = 40;          // 40 Ã— 500 ms = 20 segundos mÃ¡ximo de espera
const RETRY_MS     = 500;

let mainWindow    = null;
let pythonProcess = null;
let pythonPid     = null;
let tray          = null;
let appIsQuitting = false;
const isHiddenBoot = process.argv.includes('--hidden') || process.argv.includes('--background');

// â”€â”€â”€ INSTANCIA ÃšNICA â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const gotLock = app.requestSingleInstanceLock();

if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.show();
      mainWindow.focus();
    } else {
      createWindow(true);
    }
  });
}

// â”€â”€â”€ VerificaciÃ³n y ElevaciÃ³n AutomÃ¡tica de Permisos (UAC) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function checkAndElevatePermissions() {
  if (process.platform !== 'win32') return true;
  if (process.argv.includes('--elevated')) return true;
  try {
    execSync('net session', { stdio: 'ignore' });
    
    // Configurar regla de Firewall para puerto 8000 automáticamente
    try {
      execSync('netsh advfirewall firewall add rule name="Sistema Recursos Hidricos (Puerto 8000)" dir=in action=allow protocol=TCP localport=8000 profile=any', { stdio: 'ignore' });
    } catch (_) {}

    // Configurar hosts para recursoshidricos.local automáticamente
    try {
      const hostsPath = 'C:\\Windows\\System32\\drivers\\etc\\hosts';
      if (fs.existsSync(hostsPath)) {
        const hostsContent = fs.readFileSync(hostsPath, 'utf8');
        let toAppend = '';
        if (!hostsContent.includes('127.0.0.1 recursoshidricos.local')) {
          toAppend += '\r\n127.0.0.1 recursoshidricos.local';
        }
        if (!hostsContent.includes('192.168.100.38 recursoshidricos.local')) {
          toAppend += '\r\n192.168.100.38 recursoshidricos.local';
        }
        if (toAppend) {
          fs.appendFileSync(hostsPath, '\r\n# Recursos Hidricos Sistema Local' + toAppend + '\r\n');
        }
      }
    } catch (_) {}
    
    return true;
  } catch (_) {
    try {
      const exePath = process.execPath;
      const scriptArg = process.argv[1] || 'electron/main.js';
      const psCommand = `$exe='${exePath.replace(/'/g, "''")}'; $arg='${scriptArg} --elevated'; Start-Process -FilePath $exe -ArgumentList $arg -Verb RunAs`;
      execSync(`powershell -NoProfile -ExecutionPolicy Bypass -Command "${psCommand}"`, { stdio: 'ignore' });
      app.exit(0);
      return false;
    } catch (err) {
      console.warn('[UAC] No se pudo solicitar elevación automática:', err.message);
      return true;
    }
  }
}

// â”€â”€â”€ Matar proceso previo en el puerto (por si quedÃ³ huÃ©rfano) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function killOrphanOnPort(port) {
  try {
    if (process.platform === 'win32') {
      const result = execSync(
        `netstat -ano | findstr :${port} | findstr LISTENING`,
        { encoding: 'utf8', timeout: 3000 }
      ).trim();
      const parts = result.trim().split(/\s+/);
      const pid   = parts[parts.length - 1];
      if (pid && !isNaN(pid)) {
        execSync(`taskkill /PID ${pid} /F /T`, { timeout: 3000 });
        console.log(`[Inicio] Proceso huerfano en puerto ${port} (PID ${pid}) terminado.`);
      }
    }
  } catch (_) {}
}

// â”€â”€â”€ Iniciar backend Python â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function startPythonBackend() {
  const rootDir    = path.join(__dirname, '..');
  const isWindows  = process.platform === 'win32';

  const arch = process.arch === 'ia32' ? 'ia32' : 'x64';
  const resourcesDir = process.resourcesPath || rootDir;

  let pythonExe = path.join(resourcesDir, 'bin', arch, isWindows ? 'python.exe' : 'python');
  if (!fs.existsSync(pythonExe)) {
    pythonExe = path.join(
      rootDir, 'venv',
      isWindows ? 'Scripts' : 'bin',
      isWindows ? 'python.exe' : 'python'
    );
  }
  if (!fs.existsSync(pythonExe)) {
    pythonExe = isWindows ? 'python' : 'python3';
  }

  console.log(`[Backend] Arquitectura detectada: ${arch}. Iniciando con: ${pythonExe}`);

  const env = Object.assign({}, process.env, {
    PYTHONPATH:       rootDir,
    PYTHONUNBUFFERED: '1',
    PYTHONIOENCODING: 'utf-8',
    PYTHONUTF8:       '1'
  });

  pythonProcess = spawn(pythonExe, ['-m', 'backend.main'], {
    cwd:   rootDir,
    env:   env,
    stdio: 'pipe'
  });

  if (pythonProcess && pythonProcess.pid) {
    pythonPid = pythonProcess.pid;
    console.log(`[Backend] Proceso Python iniciado con PID: ${pythonPid}`);
  }

  pythonProcess.stdout.on('data', d => process.stdout.write(`[Python] ${d}`));
  pythonProcess.stderr.on('data', d => process.stderr.write(`[Python ERR] ${d}`));

  pythonProcess.on('close', code => {
    console.log(`[Backend] Proceso Python cerrado con código: ${code}`);
    pythonProcess = null;
    pythonPid = null;
    if (process.platform === 'win32') {
      try {
        execSync('taskkill /IM cloudflared.exe /F /T', { timeout: 3000, stdio: 'ignore' });
      } catch (_) {}
    }
    if (!appIsQuitting && mainWindow) {
      dialog.showErrorBox(
        'Backend detenido',
        'El servidor Python se detuvo inesperadamente. La aplicación se cerrará.'
      );
      app.quit();
    }
  });

  pythonProcess.on('error', err => {
    console.error(`[Backend] No se pudo iniciar Python: ${err.message}`);
    dialog.showErrorBox(
      'Error al iniciar el servidor',
      `No se pudo iniciar el backend Python.\n\n${err.message}\n\nVerificá que el entorno virtual (venv) esté instalado.`
    );
    app.quit();
  });
}

// ─── Esperar a que el backend esté listo ───────────────────────────────────────
function waitForBackend(callback, retries = MAX_RETRIES) {
  if (retries === 0) {
    console.error('[Backend] Sin respuesta después de los reintentos.');
    return callback(false);
  }
  
  const client = SERVER_URL.startsWith('https') ? https : http;
  const options = { rejectUnauthorized: false };

  client.get(`${SERVER_URL}/api/health`, options, res => {
    if (res.statusCode === 200) {
      console.log('[Backend] Listo y respondiendo.');
      callback(true);
    } else {
      setTimeout(() => waitForBackend(callback, retries - 1), RETRY_MS);
    }
  }).on('error', () => {
    setTimeout(() => waitForBackend(callback, retries - 1), RETRY_MS);
  });
}

// â”€â”€â”€ Crear ventana principal â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function createWindow(showImmediately = false) {
  const logoPath = path.join(__dirname, '../frontend/img/logo.png');
  const iconExists = fs.existsSync(logoPath);

  mainWindow = new BrowserWindow({
    width:           1280,
    height:          820,
    minWidth:        1024,
    minHeight:       700,
    title:           'GestiÃ³n de Personal - Recursos HÃ­dricos',
    icon:            iconExists ? logoPath : undefined,
    backgroundColor: '#f8fafc',
    show:            false,
    webPreferences: {
      preload:          path.join(__dirname, 'preload.js'),
      nodeIntegration:  false,
      contextIsolation: true,
      webSecurity:      false
    }
  });

  mainWindow.once('ready-to-show', () => {
    if (!isHiddenBoot || showImmediately) {
      mainWindow.show();
      mainWindow.focus();
    }
  });

  mainWindow.webContents.session.clearCache().then(() => {
    mainWindow.loadURL(SERVER_URL);
  });

  mainWindow.on('close', (event) => {
    if (!appIsQuitting && tray) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// â”€â”€â”€ Bandeja del Sistema (Tray) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function createTray() {
  if (tray) return;
  const logoPath = path.join(__dirname, '../frontend/img/logo.png');
  const iconPath = fs.existsSync(logoPath) ? logoPath : path.join(__dirname, '../logo.png');
  
  try {
    tray = new Tray(iconPath);
    tray.setToolTip('GestiÃ³n de Personal - Recursos HÃ­dricos');

    const contextMenu = Menu.buildFromTemplate([
      {
        label: 'ðŸ–¥ï¸ Abrir Sistema',
        click: () => {
          if (mainWindow) {
            mainWindow.show();
            mainWindow.focus();
          } else {
            createWindow(true);
          }
        }
      },
      {
        label: 'ðŸŒ Abrir en Navegador Web',
        click: () => {
          shell.openExternal(SERVER_URL);
        }
      },
      { type: 'separator' },
      {
        label: 'âœ… Servidor Activo (Puerto 8000)',
        enabled: false
      },
      { type: 'separator' },
      {
        label: 'âŒ Salir por Completo',
        click: () => {
          appIsQuitting = true;
          app.quit();
        }
      }
    ]);

    tray.setContextMenu(contextMenu);
    tray.on('double-click', () => {
      if (mainWindow) {
        mainWindow.show();
        mainWindow.focus();
      } else {
        createWindow(true);
      }
    });
  } catch (err) {
    console.warn('[Tray] No se pudo crear icono de bandeja:', err.message);
  }
}

// â”€â”€â”€ NotificaciÃ³n del Sistema con Logo â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function showStartupNotification() {
  try {
    if (Notification.isSupported()) {
      const logoPath = path.join(__dirname, '../frontend/img/logo.png');
      const notification = new Notification({
        title: 'ðŸŒŠ Recursos HÃ­dricos - Sistema Iniciado',
        body: 'El servidor se iniciÃ³ correctamente en segundo plano.\nAcceso: https://127.0.0.1:8000',
        icon: fs.existsSync(logoPath) ? logoPath : undefined,
        silent: false
      });
      notification.on('click', () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        } else {
          createWindow(true);
        }
      });
      notification.show();
    }
  } catch (err) {
    console.warn('[Notificacion] No se pudo emitir notificaciÃ³n nativa:', err.message);
  }
}

// â”€â”€â”€ Handlers IPC para ConfiguraciÃ³n â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
ipcMain.handle('get-auto-launch', () => {
  if (process.platform === 'win32') {
    try {
      const regQuery = execSync('reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "GestionPersonalRecursosHidricos"', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
      return regQuery.includes('GestionPersonalRecursosHidricos');
    } catch (_) {
      const settings = app.getLoginItemSettings();
      return settings.openAtLogin;
    }
  }
  return app.getLoginItemSettings().openAtLogin;
});

ipcMain.handle('set-auto-launch', (event, enable) => {
  try {
    const rootDir = path.join(__dirname, '..');
    const batPath = path.join(rootDir, 'iniciar_sistema.bat');
    const exePath = process.execPath;
    
    const targetCommand = app.isPackaged 
      ? `\\"${exePath}\\" --hidden` 
      : (fs.existsSync(batPath) ? `\\"${batPath}\\"` : `\\"${exePath}\\" \\"${path.join(rootDir, 'electron', 'main.js')}\\" --hidden`);

    if (process.platform === 'win32') {
      if (enable) {
        execSync(`reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "GestionPersonalRecursosHidricos" /t REG_SZ /d "${targetCommand}" /f`, { stdio: 'ignore' });
      } else {
        try {
          execSync(`reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "GestionPersonalRecursosHidricos" /f`, { stdio: 'ignore' });
        } catch (_) {}
      }
    }
    
    app.setLoginItemSettings({
      openAtLogin: enable,
      args: ['--hidden']
    });

    return { success: true, enabled: enable };
  } catch (err) {
    console.error('[AutoLaunch] Error configurando auto-inicio:', err);
    return { success: false, error: err.message };
  }
});

ipcMain.handle('show-notification', (event, { title, body }) => {
  const logoPath = path.join(__dirname, '../frontend/img/logo.png');
  if (Notification.isSupported()) {
    new Notification({
      title: title || 'Recursos HÃ­dricos',
      body: body || 'NotificaciÃ³n del sistema',
      icon: fs.existsSync(logoPath) ? logoPath : undefined
    }).show();
  }
  return true;
});

// â”€â”€â”€ Cierre seguro del backend â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function shutdownBackend() {
  appIsQuitting = true;
  console.log('[Cierre] Terminando backend Python y subprocesos hijos (Python, cloudflared)...');

  const pidToKill = pythonProcess ? pythonProcess.pid : pythonPid;
  if (process.platform === 'win32') {
    // 1. Matar el árbol completo del proceso Python con /T (termina el proceso y todos sus subprocesos hijos)
    if (pidToKill) {
      try {
        execSync(`taskkill /PID ${pidToKill} /F /T`, { timeout: 4000, stdio: 'ignore' });
        console.log(`[Cierre] Proceso Python (PID ${pidToKill}) y árbol de subprocesos terminados.`);
      } catch (_) {}
    }

    // 2. Garantizar que ningún subproceso de Cloudflare quede zombie en segundo plano
    try {
      execSync('taskkill /IM cloudflared.exe /F /T', { timeout: 4000, stdio: 'ignore' });
      console.log('[Cierre] Subprocesos cloudflared.exe terminados sin dejar zombies.');
    } catch (_) {}

    // 3. Matar cualquier proceso huérfano remanente en el puerto del backend
    killOrphanOnPort(PYTHON_PORT);
  } else {
    // Entorno Unix/macOS
    if (pythonProcess) {
      try {
        pythonProcess.kill('SIGTERM');
      } catch (_) {}
    }
    try {
      execSync('pkill -f cloudflared', { timeout: 2000, stdio: 'ignore' });
    } catch (_) {}
  }

  pythonProcess = null;
  pythonPid = null;
}

// ─── Ciclo de vida de la app ────────────────────────────────────────────────
app.whenReady().then(() => {
  if (!checkAndElevatePermissions()) return;

  killOrphanOnPort(PYTHON_PORT);
  createTray();
  startPythonBackend();

  waitForBackend(ready => {
    if (ready) {
      if (isHiddenBoot) {
        createWindow(false);
        showStartupNotification();
      } else {
        createWindow(true);
      }
    } else {
      dialog.showErrorBox(
        'Sin conexión al servidor',
        `El servidor Python no respondió en ${(MAX_RETRIES * RETRY_MS) / 1000} segundos.\n\nVerificá que Python y las dependencias estén instaladas.`
      );
      shutdownBackend();
      app.quit();
    }
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow(true);
  });
});

app.on('window-all-closed', () => {
  if (!tray || appIsQuitting) {
    shutdownBackend();
    if (process.platform !== 'darwin') {
      app.quit();
    }
  }
});

app.on('before-quit', () => {
  appIsQuitting = true;
  shutdownBackend();
});

app.on('will-quit', () => {
  shutdownBackend();
});

process.on('exit', () => {
  shutdownBackend();
});

process.on('SIGTERM', () => {
  shutdownBackend();
  app.quit();
});

process.on('SIGINT', () => {
  shutdownBackend();
  app.quit();
});

process.on('uncaughtException', (err) => {
  console.error('[Cierre Forzado] Error no controlado:', err);
  shutdownBackend();
  process.exit(1);
});
