/**
 * Controlador Principal SPA - Gestión de Personal Recursos Hídricos
 */

const API_BASE = window.location.origin.includes('http') ? window.location.origin : 'http://127.0.0.1:8000';

async function apiFetch(url, options = {}) {
  options.headers = options.headers || {};
  const token = localStorage.getItem('dprh_auth_token');
  if (token) {
    if (options.headers instanceof Headers) {
      if (!options.headers.has('Authorization')) {
        options.headers.set('Authorization', 'Bearer ' + token);
      }
    } else {
      if (!options.headers['Authorization'] && !options.headers['authorization']) {
        options.headers['Authorization'] = 'Bearer ' + token;
      }
    }
  }
  const response = await fetch(url, options);
  if (response.status === 401) {
    localStorage.removeItem('dprh_auth_token');
    localStorage.removeItem('dprh_user_session');
    AppState.currentUser = null;
    mostrarPantallaLogin();
  }
  return response;
}

if (typeof window.AppIcons === 'undefined') {
  window.AppIcons = {
    eye: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M10 12a2 2 0 1 0 4 0a2 2 0 0 0 -4 0" /><path d="M21 12c-2.4 4 -5.4 6 -9 6c-3.6 0 -6.6 -2 -9 -6c2.4 -4 5.4 -6 9 -6c3.6 0 6.6 2 9 6" /></svg>`,
    eyeOff: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M10.585 10.587a2 2 0 0 0 2.829 2.828" /><path d="M16.681 16.673a8.717 8.717 0 0 1 -4.681 1.327c-3.6 0 -6.6 -2 -9 -6c1.272 -2.12 2.712 -3.678 4.32 -4.674m2.86 -1.146a9.055 9.055 0 0 1 1.82 -.18c3.6 0 6.6 2 9 6c-.666 1.11 -1.379 2.067 -2.138 2.87" /><path d="M3 3l18 18" /></svg>`,
    lock: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M5 13a2 2 0 0 1 2 -2h10a2 2 0 0 1 2 2v6a2 2 0 0 1 -2 2h-10a2 2 0 0 1 -2 -2v-6z" /><path d="M11 16a1 1 0 1 0 2 0a1 1 0 0 0 -2 0" /><path d="M8 11v-4a4 4 0 0 1 8 0v4" /></svg>`,
    user: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M8 7a4 4 0 1 0 8 0a4 4 0 0 0 -8 0" /><path d="M6 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2" /></svg>`,
    userPlus: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M8 7a4 4 0 1 0 8 0a4 4 0 0 0 -8 0" /><path d="M16 19h6" /><path d="M19 16v6" /><path d="M6 21v-2a4 4 0 0 1 4 -4h4" /></svg>`,
    users: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M9 7m-4 0a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /><path d="M3 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /><path d="M21 21v-2a4 4 0 0 0 -3 -3.85" /></svg>`,
    logout: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M14 8v-2a2 2 0 0 0 -2 -2h-7a2 2 0 0 0 -2 2v12a2 2 0 0 0 2 2h7a2 2 0 0 0 2 -2v-2" /><path d="M9 12h12l-3 -3" /><path d="M18 15l3 -3" /></svg>`,
    refresh: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M20 11a8.1 8.1 0 0 0 -15.5 -2m-.5 -4v4h4" /><path d="M4 13a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4" /></svg>`,
    trash: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M4 7l16 0" /><path d="M10 11l0 6" /><path d="M14 11l0 6" /><path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12" /><path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3" /></svg>`,
    edit: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M4 20h4l10.5 -10.5a2.828 2.828 0 1 0 -4 -4l-10.5 10.5v4" /><path d="M13.5 6.5l4 4" /></svg>`,
    save: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M6 4h10l4 4v10a2 2 0 0 1 -2 2h-12a2 2 0 0 1 -2 -2v-12a2 2 0 0 1 2 -2" /><path d="M12 14m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /><path d="M14 4l0 4l-6 0l0 -4" /></svg>`,
    plus: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 5l0 14" /><path d="M5 12l14 0" /></svg>`,
    search: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M10 10m-7 0a7 7 0 1 0 14 0a7 7 0 1 0 -14 0" /><path d="M21 21l-6 -6" /></svg>`,
    download: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2 -2v-2" /><path d="M7 11l5 5l5 -5" /><path d="M12 4l0 12" /></svg>`,
    upload: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2 -2v-2" /><path d="M7 9l5 -5l5 5" /><path d="M12 4l0 12" /></svg>`,
    calendar: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M4 7a2 2 0 0 1 2 -2h12a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-12a2 2 0 0 1 -2 -2v-12z" /><path d="M16 3v4" /><path d="M8 3v4" /><path d="M4 11h16" /></svg>`,
    printer: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M17 17h2a2 2 0 0 0 2 -2v-4a2 2 0 0 0 -2 -2h-14a2 2 0 0 0 -2 2v4a2 2 0 0 0 2 2h2" /><path d="M17 9v-4a2 2 0 0 0 -2 -2h-6a2 2 0 0 0 -2 2v4" /><path d="M7 13m0 2a2 2 0 0 1 2 -2h6a2 2 0 0 1 2 2v4a2 2 0 0 1 -2 2h-6a2 2 0 0 1 -2 -2z" /></svg>`,
    building: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M3 21l18 0" /><path d="M9 8l1 0" /><path d="M9 12l1 0" /><path d="M9 16l1 0" /><path d="M14 8l1 0" /><path d="M14 12l1 0" /><path d="M14 16l1 0" /><path d="M5 21v-16a2 2 0 0 1 2 -2h10a2 2 0 0 1 2 2v16" /></svg>`,
    shield: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 3a12 12 0 0 0 8.5 3a12 12 0 0 1 -8.5 15a12 12 0 0 1 -8.5 -15a12 12 0 0 0 8.5 -3" /></svg>`,
    shieldLock: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 3a12 12 0 0 0 8.5 3a12 12 0 0 1 -8.5 15a12 12 0 0 1 -8.5 -15a12 12 0 0 0 8.5 -3" /><path d="M12 11m-1 0a1 1 0 1 0 2 0a1 1 0 1 0 -2 0" /><path d="M12 12l0 2.5" /></svg>`,
    settings: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M10.325 4.317c.426 -1.756 2.924 -1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543 -.94 3.31 .826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756 .426 1.756 2.924 0 3.35a1.724 1.724 0 0 0 -1.066 2.573c.94 1.543 -.826 3.31 -2.37 2.37a1.724 1.724 0 0 0 -2.572 1.065c-.426 1.756 -2.924 1.756 -3.35 0a1.724 1.724 0 0 0 -2.573 -1.066c-1.543 .94 -3.31 -.826 -2.37 -2.37a1.724 1.724 0 0 0 -1.065 -2.572c-1.756 -.426 -1.756 -2.924 0 -3.35a1.724 1.724 0 0 0 1.066 -2.573c-.94 -1.543 .826 -3.31 2.37 -2.37c1 .608 2.296 .07 2.572 -1.065z" /><path d="M9 12a3 3 0 1 0 6 0a3 3 0 0 0 -6 0" /></svg>`,
    bell: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M10 5a2 2 0 1 1 4 0a7 7 0 0 1 4 6v3a4 4 0 0 0 2 3h-16a4 4 0 0 0 2 -3v-3a7 7 0 0 1 4 -6" /><path d="M9 17v1a3 3 0 0 0 6 0v-1" /></svg>`,
    check: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M5 12l5 5l10 -10" /></svg>`,
    checkCircle: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M9 12l2 2l4 -4" /></svg>`,
    restore: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M9 14l-4 -4l4 -4" /><path d="M5 10h11a4 4 0 1 1 0 8h-1" /></svg>`,
    fileText: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M14 3v4a1 1 0 0 0 1 1h4" /><path d="M17 21h-10a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h7l5 5v11a2 2 0 0 1 -2 2z" /><path d="M9 9l1 0" /><path d="M9 13l6 0" /><path d="M9 17l6 0" /></svg>`,
    fileSpreadsheet: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M14 3v4a1 1 0 0 0 1 1h4" /><path d="M17 21h-10a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h7l5 5v11a2 2 0 0 1 -2 2z" /><path d="M8 11h8v7h-8z" /><path d="M8 15h8" /><path d="M11 11v7" /></svg>`,
    alertTriangle: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 9v4" /><path d="M10.363 3.591l-8.106 13.534a1.914 1.914 0 0 0 1.636 2.871h16.214a1.914 1.914 0 0 0 1.636 -2.87l-8.106 -13.536a1.914 1.914 0 0 0 -3.274 0z" /><path d="M12 16h.01" /></svg>`,
    ambulance: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M7 17m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /><path d="M17 17m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /><path d="M5 17h-2v-11a1 1 0 0 1 1 -1h9v12m-4 0h6m4 0h2v-6h-2.5a1.5 1.5 0 0 1 -1.5 -1.5v-3.5h-2" /><path d="M9 8h4m-2 -2v4" /><path d="M19 12m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /></svg>`,
    stethoscope: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M6 4h-1a2 2 0 0 0 -2 2v3.5h0a5.5 5.5 0 0 0 11 0v-3.5a2 2 0 0 0 -2 -2h-1" /><path d="M8 15a6 6 0 0 0 12 0v-3" /><path d="M11 3v2" /><path d="M6 3v2" /><path d="M20 10m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /></svg>`,
    power: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M7 6a7.75 7.75 0 1 0 10 0" /><path d="M12 4l0 8" /></svg>`,
    paperclip: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M15 7l-6.5 6.5a1.5 1.5 0 0 0 3 3l6.5 -6.5a3 3 0 0 0 -6 -6l-6.5 6.5a4.5 4.5 0 0 0 9 9l4 -4" /></svg>`,
    x: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M18 6l-12 12" /><path d="M6 6l12 12" /></svg>`
  };
}

const AppState = {
  activeTab: 'tab-dashboard',
  currentUser: null, // { id, username, nombre_completo, rol, permisos: [] }
  personalList: [],
  selectedPersonalIds: new Set(),
  feriadosList: [],
  areasList: [],
  licenciasList: [],
  papeleraData: { personal: [], licencias: [] },
  sortCol: 'apellido',
  sortOrder: 'ASC',
  searchQuery: '',
  filterArea: '',
  filterRevista: '',
  filterEstado: '',
  selectedExcelFile: null,
  fichaPersonalActivaId: null
};

// ==========================================
// INICIALIZACIÓN
// ==========================================
document.addEventListener('DOMContentLoaded', async () => {
  verificarSesionGuardada();
  setupNavigation();
  setupGlobalEvents();
  await loadAreas();
  await cargarCatalogosUI();
  loadNormativaCatalog();
});

// ==========================================
// MÓDULO 1: AUTENTICACIÓN Y SESIONES
// ==========================================
function verificarSesionGuardada() {
  const sessionStr = localStorage.getItem('dprh_user_session');
  const token = localStorage.getItem('dprh_auth_token');
  if (sessionStr && token) {
    try {
      AppState.currentUser = JSON.parse(sessionStr);
      aplicarSesionUsuario();
      return;
    } catch (e) {
      localStorage.removeItem('dprh_user_session');
      localStorage.removeItem('dprh_auth_token');
    }
  }
  mostrarPantallaLogin();
}

function mostrarPantallaLogin() {
  const overlay = document.getElementById('login-overlay');
  if (overlay) overlay.style.display = 'flex';
}

function ocultarPantallaLogin() {
  const overlay = document.getElementById('login-overlay');
  if (overlay) overlay.style.display = 'none';
}

async function ejecutarLogin(e) {
  if (e) e.preventDefault();
  const usernameInput = document.getElementById('login-username');
  const passwordInput = document.getElementById('login-password');
  const errorMsg = document.getElementById('login-error-msg');

  errorMsg.style.display = 'none';

  const payload = {
    username: usernameInput.value.trim(),
    password: passwordInput.value
  };

  try {
    const res = await apiFetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      AppState.currentUser = data.usuario;
      if (data.token) {
        localStorage.setItem('dprh_auth_token', data.token);
      }
      localStorage.setItem('dprh_user_session', JSON.stringify(data.usuario));
      passwordInput.value = '';
      ocultarPantallaLogin();
      aplicarSesionUsuario();
    } else {
      const errData = await res.json();
      errorMsg.innerText = errData.detail || "Usuario o contraseña incorrectos.";
      errorMsg.style.display = 'block';
    }
  } catch (err) {
    errorMsg.innerText = "Error de conexión con el servidor backend.";
    errorMsg.style.display = 'block';
  }
}

function cerrarSesion() {
  if (!confirm("¿Desea cerrar la sesión actual?")) return;
  AppState.currentUser = null;
  localStorage.removeItem('dprh_auth_token');
  localStorage.removeItem('dprh_user_session');
  mostrarPantallaLogin();
}

function startPasswordReveal(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.type = 'text';
  if (btn) {
    btn.innerHTML = `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M10.585 10.587a2 2 0 0 0 2.829 2.828" /><path d="M16.681 16.673a8.717 8.717 0 0 1 -4.681 1.327c-3.6 0 -6.6 -2 -9 -6c1.272 -2.12 2.712 -3.678 4.32 -4.674m2.86 -1.146a9.055 9.055 0 0 1 1.82 -.18c3.6 0 6.6 2 9 6c-.666 1.11 -1.379 2.067 -2.138 2.87" /><path d="M3 3l18 18" /></svg>`;
  }
}

function endPasswordReveal(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.type = 'password';
  if (btn) {
    btn.innerHTML = `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M10 12a2 2 0 1 0 4 0a2 2 0 0 0 -4 0" /><path d="M21 12c-2.4 4 -5.4 6 -9 6c-3.6 0 -6.6 -2 -9 -6c2.4 -4 5.4 -6 9 -6c3.6 0 6.6 2 9 6" /></svg>`;
  }
}

function togglePasswordVisibility(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  if (input.type === 'password') {
    startPasswordReveal(inputId, btn);
  } else {
    endPasswordReveal(inputId, btn);
  }
}

function tienePermiso(permisoClave) {
  if (!AppState.currentUser) return false;
  if (AppState.currentUser.rol === 'admin') return true;
  const permisos = AppState.currentUser.permisos || [];
  return permisos.includes(permisoClave);
}

function aplicarSesionUsuario() {
  const u = AppState.currentUser;
  if (!u) return;

  // Actualizar Header
  document.getElementById('user-display-name').innerText = u.nombre_completo;
  document.getElementById('user-display-role').innerText = u.rol === 'admin' ? 'Administrador General' : 'Operador Personalizado';

  // Ocultar sección de gestión de usuarios en Tab Config si no es Admin
  const boxUsuarios = document.getElementById('card-gestion-usuarios-box');
  if (boxUsuarios) {
    boxUsuarios.style.display = u.rol === 'admin' ? 'block' : 'none';
  }

  // Ocultar / Mostrar botones según permisos
  document.querySelectorAll('[data-permiso]').forEach(el => {
    const reqPermiso = el.getAttribute('data-permiso');
    if (tienePermiso(reqPermiso)) {
      el.style.display = '';
    } else {
      el.style.display = 'none';
    }
  });

  loadDashboard();
}

// ==========================================
// NAVEGACIÓN ENTRE MÓDULOS (1 a 10)
// ==========================================
function setupNavigation() {
  const navButtons = document.querySelectorAll('.sidebar-nav .nav-item');
  navButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const targetId = btn.getAttribute('data-target');
      switchTab(targetId);
    });
  });
}

function switchTab(tabId) {
  // Proteger pestaña de Configuración y Ajustes: Solo Administrador
  if (tabId === 'tab-config' && AppState.currentUser?.rol !== 'admin') {
    alert("⛔ Acceso Restringido: El módulo de Configuración y Ajustes del Sistema es exclusivo para la Administradora General.");
    switchTab('tab-dashboard');
    return;
  }

  AppState.activeTab = tabId;

  // Actualizar Sidebar
  document.querySelectorAll('.sidebar-nav .nav-item').forEach(btn => {
    if (btn.getAttribute('data-target') === tabId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Actualizar Paneles
  document.querySelectorAll('.tab-pane').forEach(pane => {
    if (pane.id === tabId) {
      pane.classList.add('active');
    } else {
      pane.classList.remove('active');
    }
  });

  // Ejecutar carga según módulo
  if (tabId === 'tab-dashboard') loadDashboard();
  if (tabId === 'tab-personal') loadPersonal();
  if (tabId === 'tab-licencias') loadLicencias();
  if (tabId === 'tab-compensatorios') loadCompensatorios();
  if (tabId === 'tab-cargar-datos') poblarSelectsCatalogos();
  if (tabId === 'tab-organigrama') loadOrganigrama();
  if (tabId === 'tab-papelera') loadPapelera();
  if (tabId === 'tab-config') {
    loadAuditoriaLogs();
    cargarCatalogosUI();
    cargarEstadoAutoLaunch();
    cargarConfiguracionTunelRapidoUI();
    cargarEstadoGitDeployKeyUI();
    cargarConfiguracionGithubSyncUI();
    cargarConfiguracionGDriveUI();
    cargarEstadoPublicacionPortalUI();
  }
}

// ==========================================
// MÓDULO 1: DASHBOARD
// ==========================================
async function loadDashboard() {
  try {
    const res = await apiFetch(`${API_BASE}/api/dashboard`);
    const data = await res.json();

    // Actualizar KPIs
    document.getElementById('kpi-total-personal').innerText = data.kpis.total_personal;
    document.getElementById('kpi-activos').innerText = data.kpis.total_activos;
    document.getElementById('kpi-en-licencia').innerText = data.kpis.total_en_licencia;
    document.getElementById('kpi-licencias-pendientes').innerText = data.kpis.licencias_pendientes;

    // Renderizar Gráficos Offline
    if (window.AppCharts) {
      window.AppCharts.renderDonut('chart-revista', data.distribucion_revista);
      window.AppCharts.renderBarChart('chart-area', data.distribucion_area);
    }

    // Tabla de Licencias Recientes
    const tbodyLic = document.getElementById('tbody-dash-licencias');
    if (tbodyLic) {
      tbodyLic.innerHTML = data.licencias_recientes.map(l => `
        <tr>
          <td><strong>${escapeHtml(l.agente)}</strong><br><small class="text-muted">DNI: ${l.dni}</small></td>
          <td>${escapeHtml(l.tipo_licencia)}</td>
          <td>${l.fecha_inicio} al ${l.fecha_fin} (${l.dias_totales} d)</td>
          <td><span class="badge badge-${l.estado_justificacion.toLowerCase()}">${l.estado_justificacion}</span></td>
        </tr>
      `).join('') || '<tr><td colspan="4" class="text-center">No hay licencias recientes</td></tr>';
    }

    // Tabla de Actividades de Auditoría
    const tbodyAud = document.getElementById('tbody-dash-actividad');
    if (tbodyAud) {
      tbodyAud.innerHTML = data.actividades_recientes.map(a => `
        <tr>
          <td><small class="text-muted">${a.timestamp}</small></td>
          <td><strong>${a.usuario}</strong></td>
          <td><span class="badge badge-info">${a.accion}</span></td>
          <td><small>${escapeHtml(a.detalles || '')}</small></td>
        </tr>
      `).join('') || '<tr><td colspan="4" class="text-center">No hay actividad registrada</td></tr>';
    }

    // Panel Novedades Diarias (Módulo 4)
    if (data.novedades_diarias) {
      const fechaEl = document.getElementById('fecha-novedades-hoy');
      if (fechaEl) fechaEl.innerText = `— Jornada: ${data.novedades_diarias.fecha}`;

      const tbodyMed = document.getElementById('tbody-dash-novedades-medicas');
      if (tbodyMed) {
        tbodyMed.innerHTML = data.novedades_diarias.licencias_medicas.map(l => `
          <tr>
            <td><strong>${escapeHtml(l.agente)}</strong><br><small>Leg: ${l.legajo || 'S/L'}</small></td>
            <td>${escapeHtml(l.area_nombre || 'Sin Área')}</td>
            <td>${escapeHtml(l.tipo_licencia)}</td>
            <td>${l.fecha_inicio} al ${l.fecha_fin} (${l.dias_totales}d)</td>
          </tr>
        `).join('') || '<tr><td colspan="4" class="text-center text-muted">Sin ausencias médicas registradas para hoy.</td></tr>';
      }

      const tbodyComp = document.getElementById('tbody-dash-novedades-compensatorios');
      if (tbodyComp) {
        tbodyComp.innerHTML = data.novedades_diarias.compensatorios_vigentes.map(c => `
          <tr>
            <td><strong>${escapeHtml(c.agente)}</strong><br><small>Form: ${c.acta_numero || ('CMP-'+c.id)}</small></td>
            <td>${escapeHtml(c.area_nombre || 'Sin Área')}</td>
            <td>${c.fecha_inicio} al ${c.fecha_fin} (${c.dias_descontados}d hábiles)</td>
            <td><span class="badge badge-${c.estado.toLowerCase()}">${c.estado}</span></td>
          </tr>
        `).join('') || '<tr><td colspan="4" class="text-center text-muted">Sin compensatorios vigentes hoy.</td></tr>';
      }
    }

    updatePapeleraBadge();
  } catch (err) {
    console.error("Error al cargar dashboard:", err);
  }
}

// ==========================================
// MÓDULO 2: PERSONAL (LISTADO, BÚSQUEDA, FILTROS)
// ==========================================
async function loadPersonal() {
  const query = AppState.searchQuery;
  const areaId = AppState.filterArea;
  const revista = AppState.filterRevista;
  const estado = AppState.filterEstado;
  const sortCol = AppState.sortCol;
  const sortOrder = AppState.sortOrder;

  const url = new URL(`${API_BASE}/api/personal`);
  if (query) url.searchParams.append('busqueda', query);
  if (areaId) url.searchParams.append('area_id', areaId);
  if (revista) url.searchParams.append('situacion_revista', revista);
  if (estado) url.searchParams.append('estado', estado);
  url.searchParams.append('ordenar_por', sortCol);
  url.searchParams.append('orden', sortOrder);

  try {
    const res = await apiFetch(url);
    const personal = await res.json();
    AppState.personalList = personal;
    renderPersonalTable(personal);
  } catch (err) {
    console.error("Error al cargar personal:", err);
  }
}

function renderPersonalTable(list) {
  const tbody = document.getElementById('tbody-personal');
  if (!tbody) return;

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="padding: 24px;">No se encontraron registros con los filtros aplicados.</td></tr>`;
    actualizarBarraSeleccionPersonal();
    return;
  }

  tbody.innerHTML = list.map(p => {
    const isChecked = AppState.selectedPersonalIds.has(p.id) ? 'checked' : '';
    return `
    <tr class="${isChecked ? 'row-selected' : ''}" id="row-personal-${p.id}">
      <td style="text-align: center; vertical-align: middle;">
        <input type="checkbox" class="check-personal-row" value="${p.id}" ${isChecked} onchange="toggleSelectPersonal(${p.id}, this.checked)" style="cursor: pointer; width: 16px; height: 16px;">
      </td>
      <td><strong>${escapeHtml(p.apellido)}, ${escapeHtml(p.nombre)}</strong><br><small class="text-muted">Leg: ${escapeHtml(p.legajo || 'S/L')}</small></td>
      <td><code>${escapeHtml(p.dni)}</code></td>
      <td><span class="badge badge-${getBadgeRevistaClass(p.situacion_revista)}">${escapeHtml(p.situacion_revista)}</span></td>
      <td>${escapeHtml(p.cargo || '-')}</td>
      <td>${escapeHtml(p.area_nombre || 'Sin Área')}</td>
      <td><span class="badge badge-${p.estado.toLowerCase()}">${p.estado}</span></td>
      <td>
        <div style="display: flex; gap: 6px;">
          <button class="btn btn-outline btn-sm" onclick="verFichaPersonal(${p.id})" title="Ver Ficha Individual e Imprimir" style="display: inline-flex; align-items: center; gap: 4px;">
            ${AppIcons.fileText} <span>Ficha</span>
          </button>
          <button class="btn btn-outline btn-sm btn-icon-only" onclick="abrirModalEditarPersonal(${p.id})" title="Editar">
            ${AppIcons.edit}
          </button>
          <button class="btn btn-outline btn-sm btn-icon-only" style="color: var(--danger);" onclick="moverPersonalAPapelera(${p.id})" title="Enviar a Papelera">
            ${AppIcons.trash}
          </button>
        </div>
      </td>
    </tr>
  `}).join('');

  actualizarBarraSeleccionPersonal();
}

function toggleSelectPersonal(id, isChecked) {
  if (isChecked) {
    AppState.selectedPersonalIds.add(id);
    document.getElementById(`row-personal-${id}`)?.classList.add('row-selected');
  } else {
    AppState.selectedPersonalIds.delete(id);
    document.getElementById(`row-personal-${id}`)?.classList.remove('row-selected');
  }
  actualizarBarraSeleccionPersonal();
}

function toggleSelectAllPersonal(isChecked) {
  const checkboxes = document.querySelectorAll('.check-personal-row');
  checkboxes.forEach(cb => {
    const id = parseInt(cb.value);
    cb.checked = isChecked;
    const row = document.getElementById(`row-personal-${id}`) || cb.closest('tr');
    if (isChecked) {
      AppState.selectedPersonalIds.add(id);
      if (row) row.classList.add('row-selected');
    } else {
      AppState.selectedPersonalIds.delete(id);
      if (row) row.classList.remove('row-selected');
    }
  });
  actualizarBarraSeleccionPersonal();
}

function deseleccionarTodoPersonal() {
  AppState.selectedPersonalIds.clear();
  const checkAll = document.getElementById('check-all-personal');
  if (checkAll) {
    checkAll.checked = false;
    checkAll.indeterminate = false;
  }
  document.querySelectorAll('.check-personal-row').forEach(cb => {
    cb.checked = false;
    const row = cb.closest('tr');
    if (row) row.classList.remove('row-selected');
  });
  actualizarBarraSeleccionPersonal();
}

function actualizarBarraSeleccionPersonal() {
  const toolbar = document.getElementById('personal-selection-toolbar');
  const countEl = document.getElementById('personal-selection-count');
  const checkAll = document.getElementById('check-all-personal');
  const count = AppState.selectedPersonalIds.size;

  if (countEl) {
    countEl.textContent = `${count} agente${count === 1 ? '' : 's'} seleccionado${count === 1 ? '' : 's'}`;
  }

  if (toolbar) {
    toolbar.style.display = count > 0 ? 'flex' : 'none';
  }

  if (checkAll) {
    const visibleCheckboxes = document.querySelectorAll('.check-personal-row');
    if (visibleCheckboxes.length > 0) {
      const allChecked = Array.from(visibleCheckboxes).every(cb => cb.checked);
      const someChecked = Array.from(visibleCheckboxes).some(cb => cb.checked);
      checkAll.checked = allChecked;
      checkAll.indeterminate = someChecked && !allChecked;
    } else {
      checkAll.checked = false;
      checkAll.indeterminate = false;
    }
  }
}

function descargarPDFNominaSeleccion() {
  if (AppState.selectedPersonalIds.size === 0) {
    alert("Selecciona al menos un agente mediante los checkboxes.");
    return;
  }
  const idsParam = Array.from(AppState.selectedPersonalIds).join(',');
  descargarPDFNomina(idsParam);
}

function imprimirPersonalSeleccion() {
  if (AppState.selectedPersonalIds.size === 0) {
    alert("Selecciona al menos un agente mediante los checkboxes.");
    return;
  }
  imprimirListadoPersonal(true);
}

async function exportarExcelPersonalSeleccion() {
  if (AppState.selectedPersonalIds.size === 0) {
    alert("Selecciona al menos un agente mediante los checkboxes.");
    return;
  }
  try {
    const idsParam = Array.from(AppState.selectedPersonalIds).join(',');
    const url = `${API_BASE}/api/personal/excel/seleccion?ids=${idsParam}`;
    const res = await apiFetch(url);
    if (!res.ok) throw new Error("Error al generar el Excel de personal seleccionado");
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = `Personal_Seleccionado_DPRH_${new Date().toISOString().slice(0, 10)}.xlsx`;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(blobUrl); }, 200);
  } catch (err) {
    alert("Error al exportar selección a Excel: " + err.message);
  }
}

function getBadgeRevistaClass(revista) {
  if (revista.includes('Permanente')) return 'planta';
  if (revista.includes('Contratado')) return 'contrato';
  if (revista.includes('Locación')) return 'locacion';
  if (revista.includes('Contrato de Obra')) return 'contrato-obra';
  if (revista.includes('Gabinete')) return 'gabinete';
  return 'planta';
}

// ==========================================
// FICHA INDIVIDUAL (MODAL E IMPRESIÓN OFICIAL DPRH)
// ==========================================
async function verFichaPersonal(personalId) {
  try {
    AppState.fichaPersonalActivaId = personalId;
    const res = await apiFetch(`${API_BASE}/api/personal/${personalId}`);
    const p = await res.json();

    const container = document.getElementById('ficha-modal-body');
    container.innerHTML = `
      <div class="ficha-card" id="ficha-print-area">
        <div class="ficha-header-official">
          <div style="display: flex; align-items: center; gap: 14px;">
            <img src="img/logo.png" alt="Logo DPRH" style="height: 46px; width: auto; object-fit: contain;">
            <div>
              <h2>GOBIERNO DE LA PROVINCIA DE JUJUY</h2>
              <h3 style="color: var(--primary-light); font-size: 15px;">Dirección Provincial de Recursos Hídricos</h3>
              <p style="font-size: 11px; color: var(--text-muted);">Legajo Único de Personal - Ficha Oficial de Agente</p>
            </div>
          </div>
          <div style="text-align: right;">
            <span class="badge badge-${p.estado.toLowerCase()}" style="font-size: 13px; padding: 6px 12px;">${p.estado}</span>
            <p style="font-size: 11px; margin-top: 4px; color: var(--text-muted);">Generado: ${new Date().toLocaleDateString('es-AR')}</p>
          </div>
        </div>

        <!-- 1. IDENTIFICACIÓN Y DATOS PERSONALES -->
        <div class="ficha-section-title">1. Datos Personales y de Identificación</div>
        <div class="form-grid" style="grid-template-columns: repeat(3, 1fr); margin-bottom: 12px; font-size: 13px;">
          <div><strong>Apellido y Nombre:</strong><br>${escapeHtml(p.apellido)}, ${escapeHtml(p.nombre)}</div>
          <div><strong>DNI:</strong><br>${escapeHtml(p.dni)}</div>
          <div><strong>CUIL:</strong><br>${escapeHtml(p.cuil || '-')}</div>
          <div><strong>Legajo:</strong><br>${escapeHtml(p.legajo || 'No Asignado')}</div>
          <div><strong>Fecha Nacimiento:</strong><br>${p.fecha_nacimiento || '-'} ${p.edad_calculada ? `(${p.edad_calculada} años)` : ''}</div>
          <div><strong>Género:</strong><br>${p.genero || '-'}</div>
          <div><strong>Teléfono:</strong><br>${escapeHtml(p.telefono || '-')}</div>
          <div><strong>Correo Electrónico:</strong><br>${escapeHtml(p.email || '-')}</div>
          <div><strong>Dirección:</strong><br>${escapeHtml(p.direccion || '-')}</div>
        </div>

        <!-- 2. REVISTA Y ANTIGÜEDADES OFICIALES DPRH -->
        <div class="ficha-section-title">2. Situación de Revista y Antigüedad Oficial</div>
        <div class="form-grid" style="grid-template-columns: repeat(3, 1fr); margin-bottom: 12px; font-size: 13px;">
          <div><strong>Situación de Revista:</strong><br><span class="badge badge-${getBadgeRevistaClass(p.situacion_revista)}">${escapeHtml(p.situacion_revista)}</span></div>
          <div><strong>Cargo Oficial:</strong><br>${escapeHtml(p.cargo || '-')}</div>
          <div><strong>Función Operativa:</strong><br>${escapeHtml(p.funcion || '-')}</div>
          <div><strong>Área / Sector:</strong><br>${escapeHtml(p.area_nombre || 'Sin Asignar')}</div>
          <div><strong>Fecha Ingreso General:</strong><br>${p.fecha_ingreso || '-'}</div>
          <div><strong>Lugar de Trabajo:</strong><br>${escapeHtml(p.lugar_trabajo || 'Oficina Central')}</div>
          <div><strong>Antigüedad Adm. Pública:</strong><br><strong>${p.antiguedad_admin_pub_calc || '-'}</strong></div>
          <div><strong>Antigüedad Obra DPRH:</strong><br><strong>${p.antiguedad_obra_calc || '-'}</strong></div>
          <div><strong>Antigüedad Planta DPRH:</strong><br><strong>${p.antiguedad_planta_calc || '-'}</strong></div>
        </div>

        ${p.contrato_actual ? `
          <div class="ficha-section-title">3. Información Contractual Vigente</div>
          <div class="form-grid" style="grid-template-columns: repeat(3, 1fr); margin-bottom: 12px; font-size: 13px;">
            <div><strong>Tipo:</strong> ${escapeHtml(p.contrato_actual.tipo_contrato)}</div>
            <div><strong>Resolución:</strong> ${escapeHtml(p.contrato_actual.resolucion_numero || '-')}</div>
            <div><strong>Vigencia:</strong> ${p.contrato_actual.fecha_inicio} al ${p.contrato_actual.fecha_fin || 'Indefinido'}</div>
          </div>
        ` : ''}

        <!-- 4. LEGAJO DIGITAL Y DOCUMENTOS ADJUNTOS -->
        <div class="ficha-section-title" style="display:flex; justify-content:space-between; align-items:center;">
          <span>4. Legajo Digital (Documentos Adjuntos)</span>
          <button class="btn btn-outline btn-sm no-print" onclick="toggleSubirDocForm(${p.id})" style="display: inline-flex; align-items: center; gap: 4px;">
            ${AppIcons.paperclip} <span>Adjuntar Documento</span>
          </button>
        </div>

        <!-- Formulario para subir nuevo documento (oculto por defecto) -->
        <div id="form-subir-doc-box" class="card no-print" style="display:none; margin: 10px 0; padding: 14px; background:#f8fafc; border: 1px dashed #94a3b8;">
          <h4 style="font-size:13px; margin-bottom:10px;">Subir Documento al Legajo de ${escapeHtml(p.apellido)}, ${escapeHtml(p.nombre)}</h4>
          <div class="form-grid" style="grid-template-columns: 1fr 1fr 1fr; gap:10px;">
            <div>
              <label style="font-size:11.5px; font-weight:bold;">Tipo de Documento</label>
              <select id="doc-tipo" class="form-control" style="font-size:12px; padding:6px;">
                <option value="DNI Copia">DNI Copia</option>
                <option value="Contrato Escaneado">Contrato Escaneado</option>
                <option value="Título Profesional">Título Profesional</option>
                <option value="Decreto / Resolución">Decreto / Resolución</option>
                <option value="Certificado Médico">Certificado Médico</option>
                <option value="Currículum Vitae">Currículum Vitae</option>
                <option value="Otro">Otro</option>
              </select>
            </div>
            <div>
              <label style="font-size:11.5px; font-weight:bold;">Título o Referencia</label>
              <input type="text" id="doc-titulo" class="form-control" placeholder="Ej: Copia DNI anverso y reverso" style="font-size:12px; padding:6px;">
            </div>
            <div>
              <label style="font-size:11.5px; font-weight:bold;">Seleccionar Archivo</label>
              <input type="file" id="doc-file" class="form-control" style="font-size:12px; padding:4px;">
            </div>
          </div>
          <div style="margin-top:10px; display:flex; gap:8px;">
            <button class="btn btn-primary btn-sm" onclick="subirDocumentoLegajo(${p.id})" style="display: inline-flex; align-items: center; gap: 4px;">
              ${AppIcons.upload} <span>Subir y Guardar</span>
            </button>
            <button class="btn btn-outline btn-sm" onclick="toggleSubirDocForm(${p.id})">Cancelar</button>
          </div>
        </div>

        <table class="custom-table" style="font-size: 12px; margin-bottom: 14px;">
          <thead>
            <tr>
              <th>Tipo</th>
              <th>Título / Descripción</th>
              <th>Archivo</th>
              <th>Fecha Subida</th>
              <th class="no-print">Acción</th>
            </tr>
          </thead>
          <tbody id="tbody-docs-legajo">
            ${p.documentos_legajo && p.documentos_legajo.length > 0 ? p.documentos_legajo.map(d => `
              <tr>
                <td><span class="badge badge-info">${escapeHtml(d.tipo_documento)}</span></td>
                <td><strong>${escapeHtml(d.titulo)}</strong></td>
                <td><small class="text-muted">${escapeHtml(d.nombre_archivo)}</small></td>
                <td><small>${d.fecha_subida ? d.fecha_subida.slice(0, 10) : '-'}</small></td>
                <td class="no-print">
                  <a href="${API_BASE}/api/documentos/${d.id}/descargar" target="_blank" class="btn btn-outline btn-sm btn-icon-only" title="Descargar / Abrir">${AppIcons.download}</a>
                  <button class="btn btn-outline btn-sm btn-icon-only" style="color:var(--danger);" onclick="eliminarDocumentoLegajoUI(${d.id}, ${p.id})" title="Eliminar">${AppIcons.trash}</button>
                </td>
              </tr>
            `).join('') : '<tr><td colspan="5" class="text-center" style="padding:12px; color:var(--text-muted);">Sin documentos digitalizados en el legajo</td></tr>'}
          </tbody>
        </table>

        <!-- 5. FAMILIARES Y BENEFICIARIOS -->
        <div class="ficha-section-title" style="display:flex; justify-content:space-between; align-items:center;">
          <span>5. Familiares y Beneficiarios</span>
          <button class="btn btn-outline btn-sm no-print" onclick="toggleFamiliarForm(${p.id})" style="display: inline-flex; align-items: center; gap: 4px;">
            ${AppIcons.users} <span>Agregar Familiar</span>
          </button>
        </div>

        <!-- Formulario para agregar familiar -->
        <div id="form-familiar-box" class="card no-print" style="display:none; margin: 10px 0; padding: 14px; background:#f8fafc; border: 1px dashed #94a3b8;">
          <h4 style="font-size:13px; margin-bottom:10px;">Registrar Familiar a Cargo de ${escapeHtml(p.apellido)}, ${escapeHtml(p.nombre)}</h4>
          <div class="form-grid" style="grid-template-columns: repeat(4, 1fr); gap:10px;">
            <div>
              <label style="font-size:11.5px; font-weight:bold;">Apellido</label>
              <input type="text" id="fam-apellido" class="form-control" style="font-size:12px; padding:6px;">
            </div>
            <div>
              <label style="font-size:11.5px; font-weight:bold;">Nombre</label>
              <input type="text" id="fam-nombre" class="form-control" style="font-size:12px; padding:6px;">
            </div>
            <div>
              <label style="font-size:11.5px; font-weight:bold;">DNI</label>
              <input type="text" id="fam-dni" class="form-control" style="font-size:12px; padding:6px;">
            </div>
            <div>
              <label style="font-size:11.5px; font-weight:bold;">Parentesco</label>
              <select id="fam-parentesco" class="form-control" style="font-size:12px; padding:6px;">
                <option value="Hijo/a">Hijo/a</option>
                <option value="Cónyuge">Cónyuge</option>
                <option value="Concubino/a">Concubino/a</option>
                <option value="Padre/Madre">Padre/Madre</option>
                <option value="Familiar a cargo">Familiar a cargo</option>
                <option value="Otro">Otro</option>
              </select>
            </div>
          </div>
          <div style="margin-top:10px; display:flex; gap:8px;">
            <button class="btn btn-primary btn-sm" onclick="guardarFamiliarUI(${p.id})" style="display: inline-flex; align-items: center; gap: 4px;">
              ${AppIcons.save} <span>Guardar Familiar</span>
            </button>
            <button class="btn btn-outline btn-sm" onclick="toggleFamiliarForm(${p.id})">Cancelar</button>
          </div>
        </div>

        <table class="custom-table" style="font-size: 12px; margin-bottom: 14px;">
          <thead>
            <tr>
              <th>Apellido y Nombre</th>
              <th>Parentesco</th>
              <th>DNI</th>
              <th class="no-print">Acción</th>
            </tr>
          </thead>
          <tbody>
            ${p.familiares && p.familiares.length > 0 ? p.familiares.map(f => `
              <tr>
                <td><strong>${escapeHtml(f.apellido)}, ${escapeHtml(f.nombre)}</strong></td>
                <td><span class="badge badge-info">${escapeHtml(f.parentesco)}</span></td>
                <td><code>${escapeHtml(f.dni || '-')}</code></td>
                <td class="no-print">
                  <button class="btn btn-outline btn-sm btn-icon-only" style="color:var(--danger);" onclick="eliminarFamiliarUI(${f.id}, ${p.id})" title="Eliminar">${AppIcons.trash}</button>
                </td>
              </tr>
            `).join('') : '<tr><td colspan="4" class="text-center" style="padding:12px; color:var(--text-muted);">Sin familiares a cargo registrados</td></tr>'}
          </tbody>
        </table>

        <!-- 6. HISTORIAL DE LICENCIAS -->
        <div class="ficha-section-title">6. Historial de Licencias y Certificados</div>
        <table class="custom-table" style="font-size: 12px; margin-top: 8px;">
          <thead>
            <tr>
              <th>Tipo Licencia</th>
              <th>Período</th>
              <th>Días</th>
              <th>Diagnóstico / Justificación</th>
              <th>Estado</th>
              <th class="no-print">Constancia</th>
            </tr>
          </thead>
          <tbody>
            ${p.historial_licencias && p.historial_licencias.length > 0 ? p.historial_licencias.map(l => `
              <tr>
                <td>${escapeHtml(l.tipo_licencia)}</td>
                <td>${l.fecha_inicio} al ${l.fecha_fin}</td>
                <td><strong>${l.dias_totales} d</strong></td>
                <td>${escapeHtml(l.diagnostico || '-')}</td>
                <td><span class="badge badge-${l.estado_justificacion.toLowerCase()}">${l.estado_justificacion}</span></td>
                <td class="no-print" style="white-space: nowrap;">
                  <button class="btn btn-outline btn-sm" onclick="descargarPDFLicencia(${l.id})" title="Descargar en PDF" style="display: inline-flex; align-items: center; gap: 4px;">
                    ${AppIcons.download} <span>PDF</span>
                  </button>
                  <button class="btn btn-outline btn-sm" onclick="imprimirConstanciaLicencia(${l.id})" title="Imprimir Constancia Oficial" style="display: inline-flex; align-items: center; gap: 4px;">
                    ${AppIcons.printer} <span>Constancia</span>
                  </button>
                </td>
              </tr>
            `).join('') : '<tr><td colspan="6" class="text-center" style="padding:12px; color:var(--text-muted);">Sin licencias registradas</td></tr>'}
          </tbody>
        </table>
      </div>
    `;

    abrirModal('modal-ficha');
  } catch (err) {
    alert("Error al cargar la ficha del personal: " + err.message);
  }
}

// ── Gestores UI de Legajo Digital y Familiares ──
function toggleSubirDocForm() {
  const box = document.getElementById('form-subir-doc-box');
  if (box) box.style.display = box.style.display === 'none' ? 'block' : 'none';
}

async function subirDocumentoLegajo(personalId) {
  const fileInput = document.getElementById('doc-file');
  const tipo = document.getElementById('doc-tipo')?.value || 'Otro';
  const titulo = document.getElementById('doc-titulo')?.value || '';

  if (!fileInput || fileInput.files.length === 0) {
    alert("Por favor seleccione un archivo para subir.");
    return;
  }
  if (!titulo) {
    alert("Por favor ingrese un título o referencia para el documento.");
    return;
  }

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('tipo_documento', tipo);
  formData.append('titulo', titulo);

  try {
    const res = await apiFetch(`${API_BASE}/api/personal/${personalId}/documentos`, {
      method: 'POST',
      body: formData
    });
    if (res.ok) {
      alert("✅ Documento subido y guardado en el legajo digital.");
      verFichaPersonal(personalId);
    } else {
      alert("Error al subir el documento.");
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

async function eliminarDocumentoLegajoUI(docId, personalId) {
  if (!confirm("¿Está seguro de eliminar este documento del legajo digital?")) return;
  try {
    const res = await apiFetch(`${API_BASE}/api/documentos/${docId}`, { method: 'DELETE' });
    if (res.ok) {
      verFichaPersonal(personalId);
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

function toggleFamiliarForm() {
  const box = document.getElementById('form-familiar-box');
  if (box) box.style.display = box.style.display === 'none' ? 'block' : 'none';
}

async function guardarFamiliarUI(personalId) {
  const apellido = document.getElementById('fam-apellido')?.value || '';
  const nombre = document.getElementById('fam-nombre')?.value || '';
  const dni = document.getElementById('fam-dni')?.value || '';
  const parentesco = document.getElementById('fam-parentesco')?.value || 'Hijo/a';

  if (!apellido || !nombre) {
    alert("Por favor complete nombre y apellido del familiar.");
    return;
  }

  const payload = {
    personal_id: personalId,
    apellido,
    nombre,
    dni,
    parentesco
  };

  try {
    const res = await apiFetch(`${API_BASE}/api/personal/${personalId}/familiares`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      alert("✅ Familiar registrado correctamente.");
      verFichaPersonal(personalId);
    } else {
      alert("Error al registrar familiar.");
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

async function eliminarFamiliarUI(famId, personalId) {
  if (!confirm("¿Desea eliminar este familiar?")) return;
  try {
    const res = await apiFetch(`${API_BASE}/api/familiares/${famId}`, { method: 'DELETE' });
    if (res.ok) {
      verFichaPersonal(personalId);
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// ==========================================
// CONSTANCIA OFICIAL DE LICENCIA (IMPRIMIBLE OFICIAL DPRH)
// ==========================================
async function imprimirConstanciaLicencia(licenciaId) {
  try {
    const res = await apiFetch(`${API_BASE}/api/licencias`);
    const licencias = await res.json();
    const l = licencias.find(item => item.id === licenciaId);
    if (!l) {
      alert("No se encontró la información de la licencia.");
      return;
    }

    const ventana = window.open('', '_blank', 'width=850,height=750');
    ventana.document.write(`<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Constancia Oficial de Licencia – DPRH Jujuy</title>
  <style>
    body { font-family: "Segoe UI", Arial, sans-serif; font-size: 13px; color: #1e293b; margin: 30px; line-height: 1.6; }
    .header { text-align: center; border-bottom: 2px solid #1a365d; padding-bottom: 12px; margin-bottom: 24px; }
    .header h1 { font-size: 16px; margin: 0; color: #0f2444; letter-spacing: 1px; }
    .header h2 { font-size: 14px; margin: 4px 0; color: #2b6cb0; }
    .header p { font-size: 11px; margin: 0; color: #64748b; }
    .doc-title { text-align: center; margin: 24px 0; font-size: 16px; font-weight: bold; text-decoration: underline; color: #1a365d; }
    .section { margin-bottom: 18px; }
    .section-title { font-weight: bold; color: #2b6cb0; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; margin-bottom: 8px; text-transform: uppercase; font-size: 12px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; }
    .box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; margin: 16px 0; }
    .signatures { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 70px; text-align: center; }
    .sig-line { border-top: 1px solid #333; margin-bottom: 4px; }
    .footer { text-align: center; font-size: 10px; color: #94a3b8; margin-top: 50px; border-top: 1px solid #e2e8f0; padding-top: 8px; }
    @media print { body { margin: 15mm; } }
  </style>
</head>
<body>
  <div class="header" style="display: flex; align-items: center; justify-content: center; gap: 16px;">
    <img src="img/logo.png" alt="Logo DPRH" style="height: 50px; width: auto;">
    <div>
      <h1>GOBIERNO DE LA PROVINCIA DE JUJUY</h1>
      <h2>DIRECCIÓN PROVINCIAL DE RECURSOS HÍDRICOS</h2>
      <p>DEPARTAMENTO DE RECURSOS HUMANOS — LEGAJO DE PERSONAL</p>
    </div>
  </div>

  <div class="doc-title">CONSTANCIA OFICIAL DE CONCESIÓN DE LICENCIA</div>

  <p>Por la presente, la <strong>Dirección Provincial de Recursos Hídricos</strong> hace constar que al agente cuyos datos se detallan a continuación, se le ha registrado y concedido la correspondiente licencia conforme a la normativa vigente:</p>

  <div class="section">
    <div class="section-title">1. Datos del Agente</div>
    <div class="grid">
      <div><strong>Apellido y Nombre:</strong> ${escapeHtml(l.personal_apellido)}, ${escapeHtml(l.personal_nombre)}</div>
      <div><strong>D.N.I. N°:</strong> ${escapeHtml(l.personal_dni)}</div>
      <div><strong>Situación de Revista:</strong> ${escapeHtml(l.situacion_revista || '-')}</div>
      <div><strong>Área / Dependencia:</strong> ${escapeHtml(l.area_nombre || 'Recursos Hídricos')}</div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">2. Detalle de la Licencia Concedida</div>
    <div class="box">
      <div style="font-size: 14px; margin-bottom: 8px;"><strong>Tipo de Licencia:</strong> ${escapeHtml(l.tipo_licencia)}</div>
      <div class="grid">
        <div><strong>Fecha de Inicio:</strong> ${l.fecha_inicio}</div>
        <div><strong>Fecha de Finalización:</strong> ${l.fecha_fin}</div>
        <div><strong>Cantidad de Días:</strong> <strong>${l.dias_totales} día(s) corridos/hábiles</strong></div>
        <div><strong>Período Anual:</strong> ${l.periodo_anual || new Date().getFullYear()}</div>
        <div><strong>Estado de Justificación:</strong> ${escapeHtml(l.estado_justificacion)}</div>
        <div><strong>Certificado / Ref.:</strong> ${escapeHtml(l.certificado_numero || 'Sin número')}</div>
      </div>
      ${l.diagnostico ? `<div style="margin-top:6px;"><strong>Motivo / Diagnóstico:</strong> ${escapeHtml(l.diagnostico)}</div>` : ''}
      ${l.observaciones ? `<div style="margin-top:4px; font-size:12px; color:#555;"><strong>Observaciones:</strong> ${escapeHtml(l.observaciones)}</div>` : ''}
    </div>
  </div>

  <p style="font-size: 12px; color: #475569;">
    La presente constancia se expide a solicitud de la parte interesada y a los efectos que correspondan en San Salvador de Jujuy, a los ${new Date().toLocaleDateString('es-AR', { day: 'numeric', month: 'long', year: 'numeric' })}.
  </p>

  <div class="signatures">
    <div>
      <div class="sig-line"></div>
      <strong>Firma del Agente</strong><br>
      <span style="font-size:11px; color:#666;">Aclaración / D.N.I.</span>
    </div>
    <div>
      <div class="sig-line"></div>
      <strong>Jefatura de Recursos Humanos</strong><br>
      <span style="font-size:11px; color:#666;">Dirección Provincial de Recursos Hídricos</span>
    </div>
  </div>

  <div class="footer">
    Sistema de Gestión de Personal — DPRH Jujuy — Documento oficial generado digitalmente
  </div>
</body>
</html>`);
    ventana.document.close();
    ventana.focus();
    ventana.print();
  } catch (err) {
    alert("Error al generar constancia: " + err.message);
  }
}

// ── Descargas de Archivos PDF Nativos (xhtml2pdf) ──
async function descargarPDFFichaActiva() {
  const personalId = AppState.fichaPersonalActivaId;
  if (!personalId) {
    alert("No hay un agente seleccionado.");
    return;
  }
  try {
    const res = await apiFetch(`${API_BASE}/api/personal/${personalId}/pdf`);
    if (!res.ok) throw new Error("Error al generar el PDF de la ficha");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Ficha_Personal_${personalId}.pdf`;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 200);
  } catch (err) {
    alert("Error: " + err.message);
  }
}

async function descargarPDFLicencia(licenciaId) {
  try {
    const res = await apiFetch(`${API_BASE}/api/licencias/${licenciaId}/pdf`);
    if (!res.ok) throw new Error("Error al generar el PDF de la constancia");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Constancia_Licencia_${licenciaId}.pdf`;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 200);
  } catch (err) {
    alert("Error al descargar PDF: " + err.message);
  }
}

async function descargarPDFNomina(overrideIds = null) {
  try {
    const query = AppState.searchQuery || '';
    const areaId = AppState.filterArea || '';
    const revista = AppState.filterRevista || '';
    const estado = AppState.filterEstado || '';

    const url = new URL(`${API_BASE}/api/personal/pdf/nomina`);
    
    // Si se pasan IDs explícitos o hay agentes seleccionados en la tabla
    const idsToFilter = overrideIds || (AppState.selectedPersonalIds.size > 0 ? Array.from(AppState.selectedPersonalIds).join(',') : null);
    if (idsToFilter) {
      url.searchParams.append('ids', idsToFilter);
    } else {
      if (query) url.searchParams.append('busqueda', query);
      if (areaId) url.searchParams.append('area_id', areaId);
      if (revista) url.searchParams.append('situacion_revista', revista);
      if (estado) url.searchParams.append('estado', estado);
    }

    const res = await apiFetch(url);
    if (!res.ok) throw new Error("Error al generar el PDF de la nómina");
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    const suffix = idsToFilter ? "Seleccion" : "DPRH";
    a.download = `Nomina_Personal_${suffix}_${new Date().toISOString().slice(0, 10)}.pdf`;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(blobUrl); }, 200);
  } catch (err) {
    alert("Error al descargar la nómina en PDF: " + err.message);
  }
}



// ==========================================
// MÓDULO 3: LICENCIAS & CERTIFICADOS MÉDICOS
// ==========================================
async function loadLicencias() {
  const query = document.getElementById('search-licencia')?.value || '';
  const estado = document.getElementById('filter-licencia-estado')?.value || '';
  const tipo = document.getElementById('filter-licencia-tipo')?.value || '';

  const url = new URL(`${API_BASE}/api/licencias`);
  if (query) url.searchParams.append('busqueda', query);
  if (estado) url.searchParams.append('estado_justificacion', estado);
  if (tipo) url.searchParams.append('tipo_licencia', tipo);

  try {
    const res = await apiFetch(url);
    const licencias = await res.json();
    AppState.licenciasList = licencias;
    renderLicenciasTable(licencias);
  } catch (err) {
    console.error("Error al cargar licencias:", err);
  }
}

function renderLicenciasTable(list) {
  const tbody = document.getElementById('tbody-licencias');
  if (!tbody) return;

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding: 24px;">No hay licencias registradas.</td></tr>`;
    return;
  }

  tbody.innerHTML = list.map(l => `
    <tr>
      <td><strong>${escapeHtml(l.personal_apellido)}, ${escapeHtml(l.personal_nombre)}</strong><br><small class="text-muted">DNI: ${l.personal_dni} | ${escapeHtml(l.situacion_revista || '')}</small></td>
      <td><strong>${escapeHtml(l.tipo_licencia)}</strong><br><small class="text-muted">${escapeHtml(l.diagnostico || '-')}</small></td>
      <td>${l.fecha_inicio} al ${l.fecha_fin}<br><small><strong>${l.dias_totales} días</strong>${l.periodo_anual ? ` | Período ${l.periodo_anual}` : ''}</small></td>
      <td><code>${escapeHtml(l.certificado_numero || '-')}</code><br><small>${escapeHtml(l.medico_nombre || '')} ${l.medico_matricula ? '(' + l.medico_matricula + ')' : ''}</small></td>
      <td><span class="badge badge-${l.estado_justificacion.toLowerCase()}">${l.estado_justificacion}</span></td>
      <td>
        <div style="display: flex; gap: 4px; flex-wrap: wrap;">
          <button class="btn btn-outline btn-sm btn-icon-only" style="color: var(--success);" onclick="cambiarEstadoLicencia(${l.id}, 'Justificada')" title="Marcar Justificada">${AppIcons.checkCircle}</button>
          <button class="btn btn-outline btn-sm btn-icon-only" style="color: var(--warning);" onclick="cambiarEstadoLicencia(${l.id}, 'Observada')" title="Marcar Observada">${AppIcons.alertTriangle}</button>
          <button class="btn btn-outline btn-sm btn-icon-only" style="color: var(--danger);" onclick="cambiarEstadoLicencia(${l.id}, 'Rechazada')" title="Marcar Rechazada">${AppIcons.x}</button>
          <button class="btn btn-outline btn-sm btn-icon-only" onclick="imprimirConstanciaLicencia(${l.id})" title="Imprimir Constancia Oficial">${AppIcons.printer}</button>
          <button class="btn btn-outline btn-sm" onclick="descargarPDFLicencia(${l.id})" title="Descargar Constancia en PDF" style="display: inline-flex; align-items: center; gap: 4px;">
            ${AppIcons.download} <span>PDF</span>
          </button>
          <button class="btn btn-outline btn-sm btn-icon-only" style="color: var(--primary);" 
            onclick="abrirModalSuspension(${l.id}, ${l.personal_id}, '${escapeHtml(l.personal_apellido)}, ${escapeHtml(l.personal_nombre)}', '${escapeHtml(l.tipo_licencia).replace(/'/g, "\\'")}', ${l.dias_totales})"
            title="Registrar Suspensión con días pendientes">
            <svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M12 7v5l3 3" /></svg>
          </button>
          <button class="btn btn-outline btn-sm btn-icon-only" style="color: var(--danger);" onclick="moverLicenciaAPapelera(${l.id})" title="Enviar a papelera">${AppIcons.trash}</button>
        </div>
      </td>
    </tr>
  `).join('');
}

async function cambiarEstadoLicencia(licenciaId, nuevoEstado) {
  try {
    const formData = new FormData();
    formData.append('estado', nuevoEstado);
    const res = await apiFetch(`${API_BASE}/api/licencias/${licenciaId}/estado`, {
      method: 'PUT',
      body: formData
    });
    if (res.ok) {
      loadLicencias();
      loadDashboard();
    }
  } catch (err) {
    alert("Error al actualizar estado: " + err.message);
  }
}

async function loadNormativaCatalog() {
  try {
    const res = await apiFetch(`${API_BASE}/api/licencias/normativa`);
    const catalog = await res.json();
    const container = document.getElementById('normativa-container');
    if (!container) return;

    container.innerHTML = catalog.map(item => `
      <div class="card" style="margin-bottom: 12px; padding: 14px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <h4 style="color: var(--primary-light); font-size: 14px;">${escapeHtml(item.tipo)}</h4>
          <span class="badge badge-info">${escapeHtml(item.articulo)}</span>
        </div>
        <p style="font-size: 12.5px; margin-bottom: 4px;"><strong>Planta Permanente:</strong> ${escapeHtml(item.limite_planta)}</p>
        <p style="font-size: 12.5px; margin-bottom: 4px;"><strong>Contratados / Locación:</strong> ${escapeHtml(item.limite_contratados)}</p>
        <p style="font-size: 11.5px; color: var(--text-muted);"><strong>Requisitos:</strong> ${escapeHtml(item.requisito)}</p>
      </div>
    `).join('');
  } catch (err) {
    console.error("Error al cargar normativa:", err);
  }
}

// ==========================================
// MÓDULO 4: CARGAR DATOS (FORMULARIO MANUAL)
// ==========================================
async function guardarNuevoEmpleado(e) {
  e.preventDefault();
  const form = document.getElementById('form-nuevo-empleado');
  const formData = new FormData(form);

  const payload = {
    dni: formData.get('dni'),
    cuil: formData.get('cuil'),
    legajo: formData.get('legajo'),
    nombre: formData.get('nombre'),
    apellido: formData.get('apellido'),
    email: formData.get('email'),
    telefono: formData.get('telefono'),
    fecha_nacimiento: formData.get('fecha_nacimiento'),
    genero: formData.get('genero'),
    direccion: formData.get('direccion'),
    fecha_ingreso: formData.get('fecha_ingreso'),
    situacion_revista: formData.get('situacion_revista'),
    cargo: formData.get('cargo'),
    funcion: formData.get('funcion'),
    area_id: formData.get('area_id') ? parseInt(formData.get('area_id')) : null,
    estado: formData.get('estado') || 'Activo'
  };

  try {
    const res = await apiFetch(`${API_BASE}/api/personal`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      alert("¡Empleado registrado exitosamente en la base de datos!");
      form.reset();
      switchTab('tab-personal');
    } else {
      const errData = await res.json();
      alert("Error al registrar: " + (errData.detail || "Verifique los datos (DNI duplicado, etc.)"));
    }
  } catch (err) {
    alert("Error de conexión: " + err.message);
  }
}

// ==========================================
// MÓDULO 5: IMPORTAR EXCEL (CON INSPECCIÓN Y PREVIEW)
// ==========================================
async function inspeccionarExcelSeleccionado(file) {
  AppState.selectedExcelFile = file;
  const formData = new FormData();
  formData.append('file', file);

  const container = document.getElementById('excel-preview-area');
  container.innerHTML = '<p>Analizando archivo Excel y hojas...</p>';

  try {
    const res = await apiFetch(`${API_BASE}/api/excel/inspeccionar`, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();

    if (data.success && data.hojas.length > 0) {
      renderExcelInspector(data.hojas);
    } else {
      container.innerHTML = '<p class="text-danger">No se encontraron hojas válidas en el archivo.</p>';
    }
  } catch (err) {
    container.innerHTML = `<p class="text-danger">Error: ${err.message}</p>`;
  }
}

function renderExcelInspector(hojas) {
  const container = document.getElementById('excel-preview-area');
  
  let html = `
    <div class="card" style="margin-top: 16px;">
      <div class="form-group">
        <label><strong>1. Seleccione la Hoja de Cálculo para Importar:</strong></label>
        <select id="select-import-sheet" class="form-control" onchange="mostrarPreviewHoja(${JSON.stringify(hojas).replace(/"/g, '&quot;')})">
          ${hojas.map((h, i) => `<option value="${escapeHtml(h.nombre)}">${escapeHtml(h.nombre)} (~${h.total_filas_aprox} filas)</option>`).join('')}
        </select>
      </div>

      <div id="sheet-preview-table" style="margin-top: 14px;"></div>

      <div style="margin-top: 18px; display: flex; gap: 12px; align-items: center;">
        <button class="btn btn-primary" onclick="ejecutarImportacionExcel()">
          🚀 Importar y Unificar por DNI
        </button>
        <small class="text-muted">Si un DNI ya existe, se actualizarán sus datos; si es nuevo, se creará el registro.</small>
      </div>
    </div>
  `;
  container.innerHTML = html;
  mostrarPreviewHoja(hojas);
}

function mostrarPreviewHoja(hojas) {
  const sel = document.getElementById('select-import-sheet');
  if (!sel) return;
  const selectedName = sel.value;
  const hoja = hojas.find(h => h.nombre === selectedName) || hojas[0];
  const container = document.getElementById('sheet-preview-table');

  if (!hoja || hoja.encabezados.length === 0) {
    container.innerHTML = '<p>La hoja seleccionada está vacía.</p>';
    return;
  }

  container.innerHTML = `
    <h4 style="font-size: 13px; margin-bottom: 8px;">Previsualización de los primeros registros:</h4>
    <div class="table-container" style="max-height: 220px; overflow-y: auto;">
      <table class="custom-table" style="font-size: 11.5px;">
        <thead>
          <tr>
            ${hoja.encabezados.map(h => `<th>${escapeHtml(h)}</th>`).join('')}
          </tr>
        </thead>
        <tbody>
          ${hoja.vista_previa.map(row => `
            <tr>
              ${row.map(cell => `<td>${escapeHtml(cell)}</td>`).join('')}
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

async function ejecutarImportacionExcel() {
  if (!AppState.selectedExcelFile) {
    alert("Por favor seleccione un archivo Excel primero.");
    return;
  }

  const sheetName = document.getElementById('select-import-sheet')?.value || 'Personal';
  const formData = new FormData();
  formData.append('file', AppState.selectedExcelFile);
  formData.append('sheet_name', sheetName);
  formData.append('modo', 'upsert');

  try {
    const res = await apiFetch(`${API_BASE}/api/excel/importar`, {
      method: 'POST',
      body: formData
    });
    const result = await res.json();

    if (res.ok) {
      alert(`¡Importación completada con éxito!\n\nNuevos registrados: ${result.nuevos}\nActualizados: ${result.actualizados}\nErrores: ${result.errores}`);
      document.getElementById('excel-preview-area').innerHTML = '';
      document.getElementById('input-excel-file').value = '';
      loadPersonal();
      loadDashboard();
      switchTab('tab-personal');
    } else {
      alert("Error al importar: " + (result.detail || "Error en el formato de datos"));
    }
  } catch (err) {
    alert("Error de conexión: " + err.message);
  }
}

// ==========================================
// MÓDULO 6: EXPORTAR EXCEL
// ==========================================
async function descargarExcelCompleto() {
  try {
    // Usamos fetch+blob para compatibilidad con Electron (window.open falla con binarios)
    const res = await apiFetch(`${API_BASE}/api/excel/exportar`);
    if (!res.ok) {
      const errText = await res.text();
      alert('Error al generar el Excel: ' + errText);
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Nomina_RecursosHidricos_${new Date().toISOString().slice(0, 10)}.xlsx`;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 200);
  } catch (err) {
    alert('Error de conexión al exportar: ' + err.message);
  }
}

// ==========================================
// MÓDULO 7: ORGANIGRAMA
// ==========================================
async function loadOrganigrama() {
  try {
    const res = await apiFetch(`${API_BASE}/api/organigrama`);
    const tree = await res.json();
    const container = document.getElementById('organigrama-container');
    if (!container) return;

    function renderNode(node) {
      return `
        <div class="org-node level-${node.nivel}">
          <div class="org-node-header">
            <div>
              <span class="badge badge-planta" style="font-size: 10px;">${escapeHtml(node.codigo || 'UNIDAD')}</span>
              <div class="org-node-title">${escapeHtml(node.nombre)}</div>
              <div class="org-node-resp">${AppIcons.user} Responsable: <strong>${escapeHtml(node.responsable || 'A designar')}</strong></div>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span class="badge badge-info" style="font-size: 12px;">${node.personal ? node.personal.length : 0} Agentes</span>
              <button class="btn btn-outline btn-sm btn-icon-only" onclick="abrirModalEditarArea(${node.id})" title="Editar Unidad Organizativa">${AppIcons.edit}</button>
              <button class="btn btn-outline btn-sm btn-icon-only" style="color: var(--danger);" onclick="eliminarAreaUI(${node.id})" title="Eliminar Unidad Organizativa">${AppIcons.trash}</button>
            </div>
          </div>

          ${node.personal && node.personal.length > 0 ? `
            <div style="margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--surface-border); display: flex; flex-wrap: wrap; gap: 6px;">
              ${node.personal.map(p => `
                <span class="badge badge-outline" style="background: #fff; border: 1px solid #cbd5e1; font-size: 11px; cursor: pointer;" onclick="verFichaPersonal(${p.id})">
                  ${escapeHtml(p.apellido)}, ${escapeHtml(p.nombre)} (${escapeHtml(p.cargo || 'Agente')})
                </span>
              `).join('')}
            </div>
          ` : ''}

          ${node.subareas && node.subareas.length > 0 ? `
            <div style="margin-top: 12px; display: flex; flex-direction: column; gap: 10px;">
              ${node.subareas.map(sub => renderNode(sub)).join('')}
            </div>
          ` : ''}
        </div>
      `;
    }

    container.innerHTML = tree.map(rootNode => renderNode(rootNode)).join('');
  } catch (err) {
    console.error("Error al cargar organigrama:", err);
  }
}

// ==========================================
// MÓDULO 8: PAPELERA DE RECICLAJE
// ==========================================
async function loadPapelera() {
  try {
    const res = await apiFetch(`${API_BASE}/api/papelera`);
    const data = await res.json();
    AppState.papeleraData = data;

    const tbodyP = document.getElementById('tbody-papelera-personal');
    if (tbodyP) {
      tbodyP.innerHTML = data.personal.map(p => `
        <tr>
          <td><strong>${escapeHtml(p.apellido)}, ${escapeHtml(p.nombre)}</strong> (DNI: ${p.dni})</td>
          <td>${escapeHtml(p.area_nombre || 'Sin Área')}</td>
          <td><small class="text-muted">${p.deleted_at || 'Reciente'}</small></td>
          <td>
            <button class="btn btn-success btn-sm" onclick="restaurarPersonal(${p.id})" style="display: inline-flex; align-items: center; gap: 4px;">
              ${AppIcons.restore} <span>Restaurar</span>
            </button>
            <button class="btn btn-danger btn-sm" onclick="eliminarPersonalDefinitivo(${p.id})" style="display: inline-flex; align-items: center; gap: 4px;">
              ${AppIcons.trash} <span>Eliminar Definitivo</span>
            </button>
          </td>
        </tr>
      `).join('') || '<tr><td colspan="4" class="text-center">No hay personal en la papelera</td></tr>';
    }

    const tbodyL = document.getElementById('tbody-papelera-licencias');
    if (tbodyL) {
      tbodyL.innerHTML = data.licencias.map(l => `
        <tr>
          <td><strong>${escapeHtml(l.personal_apellido)}, ${escapeHtml(l.personal_nombre)}</strong></td>
          <td>${escapeHtml(l.tipo_licencia)} (${l.dias_totales} d)</td>
          <td><small class="text-muted">${l.deleted_at || 'Reciente'}</small></td>
          <td>
            <button class="btn btn-success btn-sm" onclick="restaurarLicencia(${l.id})" style="display: inline-flex; align-items: center; gap: 4px;">
              ${AppIcons.restore} <span>Restaurar</span>
            </button>
            <button class="btn btn-danger btn-sm" onclick="eliminarLicenciaDefinitiva(${l.id})" style="display: inline-flex; align-items: center; gap: 4px;">
              ${AppIcons.trash} <span>Eliminar Definitivo</span>
            </button>
          </td>
        </tr>
      `).join('') || '<tr><td colspan="4" class="text-center">No hay licencias en la papelera</td></tr>';
    }

    updatePapeleraBadge();
  } catch (err) {
    console.error("Error al cargar papelera:", err);
  }
}

async function updatePapeleraBadge() {
  try {
    const res = await apiFetch(`${API_BASE}/api/papelera`);
    const data = await res.json();
    const badge = document.getElementById('badge-papelera-count');
    if (badge) {
      badge.innerText = data.total;
      badge.style.display = data.total > 0 ? 'inline-block' : 'none';
    }
  } catch (err) {}
}

async function moverPersonalAPapelera(id) {
  if (confirm("¿Está seguro de enviar este empleado a la papelera de reciclaje?")) {
    await apiFetch(`${API_BASE}/api/personal/${id}`, { method: 'DELETE' });
    loadPersonal();
    loadDashboard();
  }
}

async function restaurarPersonal(id) {
  await apiFetch(`${API_BASE}/api/personal/${id}/restaurar`, { method: 'POST' });
  loadPapelera();
  loadPersonal();
  loadDashboard();
}

async function eliminarPersonalDefinitivo(id) {
  if (confirm("⚠️ Esta acción es irreversible. ¿Eliminar definitivamente el registro y todo su historial de la base de datos?")) {
    try {
      const res = await apiFetch(`${API_BASE}/api/personal/${id}/definitivo`, { method: 'DELETE' });
      const data = await res.json();
      if (data.success !== false) {
        loadPapelera();
        loadPersonal();
        loadDashboard();
      } else {
        alert("No se pudo eliminar: " + (data.detail || "Error desconocido"));
      }
    } catch (err) {
      alert("Error al eliminar definitivamente: " + err.message);
    }
  }
}

async function moverLicenciaAPapelera(id) {
  if (confirm("¿Enviar esta licencia a la papelera?")) {
    await apiFetch(`${API_BASE}/api/licencias/${id}`, { method: 'DELETE' });
    loadLicencias();
    loadDashboard();
  }
}

async function restaurarLicencia(id) {
  await apiFetch(`${API_BASE}/api/licencias/${id}/restaurar`, { method: 'POST' });
  loadPapelera();
  loadLicencias();
}

async function eliminarLicenciaDefinitiva(id) {
  if (confirm("Esta acción es irreversible. ¿Eliminar definitivamente la licencia?")) {
    await apiFetch(`${API_BASE}/api/licencias/${id}/definitivo`, { method: 'DELETE' });
    loadPapelera();
  }
}

async function vaciarPapeleraCompleta() {
  if (confirm("⚠️ ¿Desea eliminar definitivamente TODOS los registros en la papelera?")) {
    await apiFetch(`${API_BASE}/api/papelera/vaciar`, { method: 'DELETE' });
    loadPapelera();
    loadDashboard();
  }
}

// ==========================================
// MÓDULO 10: CONFIGURACIÓN, AUDITORÍA & VBA
// ==========================================
async function loadAuditoriaLogs() {
  try {
    const res = await apiFetch(`${API_BASE}/api/auditoria?limite=100`);
    const logs = await res.json();
    const tbody = document.getElementById('tbody-auditoria');
    if (tbody) {
      tbody.innerHTML = logs.map(l => `
        <tr>
          <td><small>${l.timestamp}</small></td>
          <td><strong>${l.usuario}</strong></td>
          <td><span class="badge badge-info">${l.accion}</span></td>
          <td><code>${l.tabla_afectada}</code> (ID: ${l.registro_id || '-'})</td>
          <td>${escapeHtml(l.detalles || '')}</td>
        </tr>
      `).join('') || '<tr><td colspan="5" class="text-center">Sin logs de auditoría</td></tr>';
    }
  } catch (err) {
    console.error("Error al cargar auditoría:", err);
  }
}

async function mostrarModalVBA() {
  try {
    const res = await apiFetch(`${API_BASE}/api/vba/codigo`);
    const data = await res.json();

    document.getElementById('vba-userform-code').innerText = data.userform_code;
    document.getElementById('vba-dashboard-code').innerText = data.dashboard_macro;
    document.getElementById('vba-instrucciones').innerText = data.instrucciones;

    abrirModal('modal-vba');
  } catch (err) {
    alert("Error al obtener código VBA: " + err.message);
  }
}

function copiarTexto(elementId) {
  const text = document.getElementById(elementId).innerText;
  navigator.clipboard.writeText(text).then(() => {
    alert("¡Código VBA copiado al portapapeles!");
  });
}

async function reiniciarDatosDemo() {
  if (confirm("⚠️ ¿Desea reiniciar la base de datos con los datos de ejemplo originales de Recursos Hídricos?")) {
    await apiFetch(`${API_BASE}/api/sistema/reseed`, { method: 'POST' });
    alert("Base de datos reiniciada con éxito.");
    loadDashboard();
    loadPersonal();
  }
}

function descargarBackupDB() {
  window.open(`${API_BASE}/api/sistema/db-backup`, '_blank');
}

// ==========================================
// AJUSTES: AUTO-INICIO CON WINDOWS
// ==========================================
async function cargarEstadoAutoLaunch() {
  const chk = document.getElementById('chk-auto-launch');
  const label = document.getElementById('label-auto-launch-text');
  if (!chk) return;

  try {
    let enabled = false;
    if (window.electronAPI && typeof window.electronAPI.getAutoLaunch === 'function') {
      enabled = await window.electronAPI.getAutoLaunch();
    } else {
      const res = await apiFetch(`${API_BASE}/api/sistema/auto-launch`);
      const data = await res.json();
      enabled = !!data.enabled;
    }
    chk.checked = enabled;
    if (label) {
      label.innerText = enabled ? '✅ Activo' : 'Inactivo';
      label.style.color = enabled ? 'var(--success)' : 'var(--text-muted)';
    }
  } catch (err) {
    console.warn("Error al consultar estado de auto-inicio:", err);
  }
}

async function cambiarAutoLaunch(enabled) {
  const label = document.getElementById('label-auto-launch-text');
  const statusMsg = document.getElementById('status-auto-launch-msg');

  if (label) {
    label.innerText = enabled ? '✅ Activo' : 'Inactivo';
    label.style.color = enabled ? 'var(--success)' : 'var(--text-muted)';
  }

  try {
    let ok = false;
    if (window.electronAPI && typeof window.electronAPI.setAutoLaunch === 'function') {
      const res = await window.electronAPI.setAutoLaunch(enabled);
      ok = res.success !== false;
    } else {
      const formData = new FormData();
      formData.append('enabled', enabled);
      const res = await apiFetch(`${API_BASE}/api/sistema/auto-launch`, { method: 'POST', body: formData });
      const data = await res.json();
      ok = data.success;
    }

    if (ok) {
      if (statusMsg) {
        statusMsg.style.display = 'block';
        statusMsg.style.color = enabled ? 'var(--success)' : 'var(--text-muted)';
        statusMsg.innerText = enabled 
          ? '✔️ El sistema se iniciará automáticamente en segundo plano con Windows.'
          : '✖️ Auto-inicio con el sistema desactivado.';
        setTimeout(() => { statusMsg.style.display = 'none'; }, 4000);
      }
    }
  } catch (err) {
    alert("Error al configurar auto-inicio: " + err.message);
  }
}

// ==========================================
// CARGAR ÁREAS Y EVENTOS GLOBALES
// ==========================================
async function loadAreas() {
  try {
    const res = await apiFetch(`${API_BASE}/api/areas`);
    const areas = await res.json();
    AppState.areasList = areas;
    if (AppState.catalogos) AppState.catalogos.areas = areas;

    poblarSelectsCatalogos();

    if (window.$ && $.fn.select2) {
      setTimeout(() => {
        $('#nuevo-area-id').select2({ placeholder: "Seleccione Área...", allowClear: true, width: '100%' });
      }, 50);
    }
  } catch (err) {
    console.error("Error cargando áreas:", err);
  }
}

function setupGlobalEvents() {
  // Búsqueda en Personal
  const searchInput = document.getElementById('search-personal');
  if (searchInput) {
    searchInput.addEventListener('input', debounce((e) => {
      AppState.searchQuery = e.target.value;
      loadPersonal();
    }, 300));
  }

  // Filtros en Personal
  ['filter-personal-area', 'filter-personal-revista', 'filter-personal-estado'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('change', () => {
        AppState.filterArea = document.getElementById('filter-personal-area')?.value || '';
        AppState.filterRevista = document.getElementById('filter-personal-revista')?.value || '';
        AppState.filterEstado = document.getElementById('filter-personal-estado')?.value || '';
        loadPersonal();
      });
    }
  });

  // Formulario Nuevo Empleado
  const formNuevo = document.getElementById('form-nuevo-empleado');
  if (formNuevo) formNuevo.addEventListener('submit', guardarNuevoEmpleado);

  // Formulario Nueva Licencia
  const formLicencia = document.getElementById('form-nueva-licencia');
  if (formLicencia) formLicencia.addEventListener('submit', guardarNuevaLicencia);

  // ── Cálculo automático de días totales en modal licencias ──
  function calcularDiasLicencia() {
    const inicio = document.getElementById('lic-fecha-inicio')?.value;
    const fin    = document.getElementById('lic-fecha-fin')?.value;
    const campoD = document.getElementById('lic-dias-totales');
    if (inicio && fin && campoD) {
      const d1 = new Date(inicio);
      const d2 = new Date(fin);
      const diff = Math.round((d2 - d1) / (1000 * 60 * 60 * 24)) + 1; // días inclusivos
      campoD.value = diff > 0 ? diff : 1;
    }
  }
  document.getElementById('lic-fecha-inicio')?.addEventListener('change', calcularDiasLicencia);
  document.getElementById('lic-fecha-fin')?.addEventListener('change', calcularDiasLicencia);

  // ── Búsqueda en tiempo real de Agente por Apellido o DNI ──
  const buscarAgente = document.getElementById('lic-buscar-agente');
  if (buscarAgente) {
    buscarAgente.addEventListener('input', () => {
      const query = buscarAgente.value.trim().toLowerCase();
      const sel   = document.getElementById('lic-personal-id');
      if (!sel) return;
      Array.from(sel.options).forEach(opt => {
        if (!opt.value) return; // placeholder
        const visible = opt.text.toLowerCase().includes(query);
        opt.style.display = visible ? '' : 'none';
      });
    });
  }

  // Input Excel File
  const fileInput = document.getElementById('input-excel-file');
  if (fileInput) {
    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        inspeccionarExcelSeleccionado(e.target.files[0]);
      }
    });
  }
}


// ==========================================
// SUB-PESTAÑAS DE LICENCIAS
// ==========================================
function switchSubtabLicencias(subtab) {
  ['todas', 'pendientes', 'alertas'].forEach(name => {
    const el = document.getElementById(`subtab-${name}`);
    const btn = document.getElementById(`subtab-btn-${name}`);
    if (el) el.style.display = name === subtab ? 'block' : 'none';
    if (btn) {
      btn.className = name === subtab
        ? 'btn btn-primary btn-sm'
        : 'btn btn-outline btn-sm';
      if (name === subtab) btn.style.background = 'var(--primary)';
      else btn.style.background = '';
    }
  });

  if (subtab === 'pendientes') loadDiasPendientes();
  if (subtab === 'alertas') loadAlertasLicencias();
  if (subtab === 'todas') loadLicencias();
}

// ==========================================
// DÍAS PENDIENTES POR SUSPENSIÓN
// ==========================================
async function loadDiasPendientes() {
  try {
    const res = await apiFetch(`${API_BASE}/api/licencias/pendientes`);
    const data = await res.json();
    const tbody = document.getElementById('tbody-pendientes');
    if (!tbody) return;

    if (data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="padding:24px;">No hay días pendientes por suspensión de licencia. ✅</td></tr>`;
      return;
    }

    tbody.innerHTML = data.map(s => `
      <tr>
        <td><strong>${escapeHtml(s.apellido)}, ${escapeHtml(s.nombre)}</strong><br><small class="text-muted">DNI: ${s.dni}</small></td>
        <td>${escapeHtml(s.tipo_licencia)}</td>
        <td><strong>${s.periodo || '-'}</strong></td>
        <td>${s.fecha_suspension}</td>
        <td style="text-align:center;">${s.dias_tomados_hasta_suspension}</td>
        <td><span style="background:#e0f2fe; color:#0369a1; padding:4px 10px; border-radius:12px; font-weight:bold;">${s.dias_pendientes} días</span></td>
        <td>${escapeHtml(s.motivo_suspension || '-')}</td>
        <td>
          <button class="btn btn-success btn-sm" onclick="marcarRetomada(${s.suspension_id})">▶️ Retomada</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    console.error("Error cargando días pendientes:", err);
  }
}

async function marcarRetomada(suspensionId) {
  const fechaAlta = prompt("Ingrese la fecha en que el agente retomó los días pendientes (AAAA-MM-DD):");
  if (!fechaAlta) return;
  const obs = prompt("Observaciones (opcional):") || "";
  
  const formData = new FormData();
  formData.append('fecha_alta', fechaAlta);
  formData.append('observaciones', obs);
  
  try {
    const res = await apiFetch(`${API_BASE}/api/suspensiones/${suspensionId}/retomar`, {
      method: 'PUT',
      body: formData
    });
    if (res.ok) {
      alert("✅ Suspensión marcada como retomada correctamente.");
      loadDiasPendientes();
    } else {
      alert("Error al actualizar la suspensión.");
    }
  } catch(err) {
    alert("Error: " + err.message);
  }
}

// ==========================================
// ALERTAS DE LICENCIAS MÉDICAS
// ==========================================
async function loadAlertasLicencias() {
  try {
    const res = await apiFetch(`${API_BASE}/api/licencias/alertas`);
    const data = await res.json();
    const container = document.getElementById('alertas-container');
    if (!container) return;

    let html = '';

    if (data.alertas_exceso_dias.length > 0) {
      html += `
        <h4 style="font-size:14px; color:var(--danger); margin-bottom:8px;">⚠️ Agentes con exceso de días de licencia médica en el año</h4>
        <div class="table-container" style="margin-bottom:20px;">
          <table class="custom-table">
            <thead><tr><th>Agente</th><th>Área</th><th>Días Acumulados</th><th>Certificados</th><th>Sin Auditar</th></tr></thead>
            <tbody>
              ${data.alertas_exceso_dias.map(a => `
                <tr>
                  <td><strong>${escapeHtml(a.apellido)}, ${escapeHtml(a.nombre)}</strong><br><small>${a.dni}</small></td>
                  <td>${escapeHtml(a.area_nombre)}</td>
                  <td><span style="color:var(--danger);font-weight:bold;">${a.dias_acumulados} días</span></td>
                  <td>${a.cantidad_certificados}</td>
                  <td>${a.certificados_sin_auditar > 0 ? `<span style="color:var(--warning);font-weight:bold;">${a.certificados_sin_auditar} pendientes</span>` : '✅ Todos auditados'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    }

    if (data.pendientes_auditoria_oficial.length > 0) {
      html += `
        <h4 style="font-size:14px; color:var(--warning); margin-bottom:8px;">🔍 Certificados médicos pendientes de auditoría provincial (≥7 días)</h4>
        <div class="table-container">
          <table class="custom-table">
            <thead><tr><th>Agente</th><th>Tipo</th><th>Período</th><th>Días</th><th>Diagnóstico</th><th>Acciones</th></tr></thead>
            <tbody>
              ${data.pendientes_auditoria_oficial.map(p => `
                <tr>
                  <td><strong>${escapeHtml(p.agente)}</strong><br><small>${p.dni}</small></td>
                  <td>${escapeHtml(p.tipo_licencia)}</td>
                  <td>${p.fecha_inicio} al ${p.fecha_fin}</td>
                  <td><strong>${p.dias_totales}</strong></td>
                  <td>${escapeHtml(p.diagnostico || '-')}</td>
                  <td>
                    <button class="btn btn-success btn-sm" onclick="marcarAuditada(${p.licencia_id})">✅ Marcar Auditada</button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    }

    if (data.total_alertas === 0) {
      html = `<p style="text-align:center; color:var(--success); padding:24px;">✅ No hay alertas activas. Todo el sistema está al día.</p>`;
    }

    container.innerHTML = html;
  } catch (err) {
    console.error("Error cargando alertas:", err);
  }
}

async function marcarAuditada(licenciaId) {
  const obs = prompt("Observación de auditoría (opcional):") || "";
  const formData = new FormData();
  formData.append('auditado', '1');
  formData.append('observacion', obs);
  try {
    const res = await apiFetch(`${API_BASE}/api/licencias/${licenciaId}/auditoria`, {
      method: 'PUT',
      body: formData
    });
    if (res.ok) {
      alert("✅ Licencia marcada como auditada por el servicio de salud provincial.");
      loadAlertasLicencias();
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// ==========================================
// MODAL SUSPENSIÓN DE LICENCIA
// ==========================================
function abrirModalSuspension(licenciaId, personalId, nombreAgente, tipoLicencia, diasTotales) {
  document.getElementById('susp-licencia-id').value = licenciaId;
  document.getElementById('susp-personal-id').value = personalId;
  document.getElementById('susp-agente-nombre').value = nombreAgente;
  document.getElementById('susp-tipo-licencia').value = tipoLicencia;
  document.getElementById('susp-dias-totales-ref').value = `${diasTotales} días en total`;
  document.getElementById('susp-dias-tomados').value = '';
  document.getElementById('susp-dias-pendientes').value = '';
  abrirModal('modal-suspension');
}

function calcularDiasPendientes() {
  const tomados = parseInt(document.getElementById('susp-dias-tomados')?.value || 0);
  const refText = document.getElementById('susp-dias-totales-ref')?.value || '';
  const match = refText.match(/(\d+)/);
  const total = match ? parseInt(match[1]) : 0;
  const pendientes = Math.max(0, total - tomados);
  const campoP = document.getElementById('susp-dias-pendientes');
  if (campoP) campoP.value = pendientes;
}

// Formulario de suspensión
document.addEventListener('DOMContentLoaded', () => {
  const formSusp = document.getElementById('form-suspension');
  if (formSusp) {
    formSusp.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(formSusp);
      const payload = {
        licencia_id: parseInt(fd.get('licencia_id')),
        personal_id: parseInt(fd.get('personal_id')),
        fecha_suspension: fd.get('fecha_suspension'),
        dias_tomados_hasta_suspension: parseInt(fd.get('dias_tomados_hasta_suspension') || 0),
        dias_pendientes: parseInt(fd.get('dias_pendientes') || 0),
        motivo_suspension: fd.get('motivo_suspension'),
        autorizado_por: fd.get('autorizado_por'),
        fecha_alta: fd.get('fecha_alta') || null,
        observaciones: fd.get('observaciones')
      };
      try {
        const licId = payload.licencia_id;
        const res = await apiFetch(`${API_BASE}/api/licencias/${licId}/suspender`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          alert(`✅ Suspensión registrada. Días pendientes: ${payload.dias_pendientes}`);
          cerrarModal('modal-suspension');
          loadLicencias();
        } else {
          alert("Error al registrar la suspensión.");
        }
      } catch (err) {
        alert("Error: " + err.message);
      }
    });
  }
});

// ==========================================
// LÓGICA CONTEXTUAL DEL MODAL LICENCIAS
// ==========================================
function onTipoLicenciaChange() {
  const tipo = document.getElementById('lic-tipo-licencia')?.value || '';
  
  const esMedica = tipo.includes('Médica') || tipo.includes('Ginecológicos');
  const esFamiliar = tipo.includes('Familiar') || tipo.includes('Duelo') || tipo.includes('Discapacidad');
  const esViaje = tipo.includes('Viaje') || tipo.includes('Comisión');
  
  // Campos médicos (certificado, médico, matrícula)
  const camposMedicos = document.getElementById('lic-campos-medicos');
  if (camposMedicos) camposMedicos.style.display = esMedica ? 'grid' : 'none';

  // Campos de familiar
  const camposFamiliar = document.getElementById('lic-campos-familiar');
  if (camposFamiliar) camposFamiliar.style.display = esFamiliar ? 'grid' : 'none';

  // Campos de viaje
  const camposViaje = document.getElementById('lic-campos-viaje');
  if (camposViaje) camposViaje.style.display = esViaje ? 'grid' : 'none';

  // Auditoría médica
  const camposAuditoria = document.getElementById('lic-auditoria-medica');
  if (camposAuditoria) camposAuditoria.style.display = esMedica ? 'block' : 'none';
}

// ==========================================
// MODAL EDITAR PERSONAL
// ==========================================
async function abrirModalEditarPersonal(personalId) {
  try {
    const res = await apiFetch(`${API_BASE}/api/personal/${personalId}`);
    const p = await res.json();

    // Reusar el tab de carga de datos como modal de edición
    // Cambiamos a la sección de carga y pre-cargamos los datos
    switchTab('tab-cargar-datos');

    // Pre-cargar formulario
    const form = document.getElementById('form-nuevo-empleado');
    if (!form) return;

    const setVal = (name, val) => {
      const el = form.querySelector(`[name="${name}"]`);
      if (!el) return;
      if (el.tagName === 'SELECT' && val) {
        let exists = Array.from(el.options).some(o => o.value == val);
        if (!exists) {
          const opt = document.createElement('option');
          opt.value = val;
          opt.textContent = val;
          el.appendChild(opt);
        }
      }
      el.value = val || '';
    };

    setVal('dni', p.dni);
    setVal('legajo', p.legajo);
    setVal('nombre', p.nombre);
    setVal('apellido', p.apellido);
    setVal('email', p.email);
    setVal('telefono', p.telefono);
    setVal('fecha_nacimiento', p.fecha_nacimiento);
    setVal('genero', p.genero);
    setVal('direccion', p.direccion);
    setVal('fecha_ingreso', p.fecha_ingreso);
    setVal('situacion_revista', p.situacion_revista);
    setVal('lugar_trabajo', p.lugar_trabajo || 'Oficina Central');
    setVal('cargo', p.cargo);
    setVal('funcion', p.funcion);
    setVal('estado', p.estado);
    if (p.area_id) setVal('area_id', p.area_id);

    // Cambiar título y comportamiento del botón submit
    const card = form.closest('.card');
    if (card) {
      const title = card.querySelector('.card-title');
      if (title) title.textContent = `✏️ Editando: ${p.apellido}, ${p.nombre} (DNI: ${p.dni})`;
    }

    // Override submit para PUT en lugar de POST
    form.dataset.editingId = personalId;
    form.dataset.editMode = 'true';
    
    // Cambiar botón submit
    const submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn) {
      submitBtn.textContent = '💾 Guardar Cambios';
      submitBtn.style.background = 'var(--warning)';
      submitBtn.style.color = '#000';
    }

    // Agregar botón cancelar edición si no existe
    if (!form.querySelector('#btn-cancel-edit')) {
      const cancelBtn = document.createElement('button');
      cancelBtn.type = 'button';
      cancelBtn.id = 'btn-cancel-edit';
      cancelBtn.className = 'btn btn-outline';
      cancelBtn.textContent = '✖ Cancelar Edición';
      cancelBtn.onclick = () => {
        form.reset();
        form.dataset.editMode = 'false';
        delete form.dataset.editingId;
        const title = form.closest('.card')?.querySelector('.card-title');
        if (title) title.textContent = 'Alta Individual de Personal (Carga Manual)';
        const sb = form.querySelector('[type="submit"]');
        if (sb) { sb.textContent = '💾 Guardar y Registrar en Base de Datos'; sb.style = ''; }
        cancelBtn.remove();
      };
      form.querySelector('[type="reset"]')?.after(cancelBtn);
    }

  } catch (err) {
    alert("Error al cargar datos del personal: " + err.message);
  }
}

// Override del formulario de nuevo empleado para soportar edición
const _originalGuardarNuevoEmpleado = guardarNuevoEmpleado;
async function guardarNuevoEmpleado(e) {
  e.preventDefault();
  const form = document.getElementById('form-nuevo-empleado');
  
  if (form?.dataset.editMode === 'true' && form.dataset.editingId) {
    // Modo edición: PUT
    const personalId = form.dataset.editingId;
    const formData = new FormData(form);

    const payload = {
      dni: formData.get('dni'),
      legajo: formData.get('legajo'),
      nombre: formData.get('nombre'),
      apellido: formData.get('apellido'),
      email: formData.get('email'),
      telefono: formData.get('telefono'),
      fecha_nacimiento: formData.get('fecha_nacimiento'),
      genero: formData.get('genero'),
      direccion: formData.get('direccion'),
      fecha_ingreso: formData.get('fecha_ingreso'),
      situacion_revista: formData.get('situacion_revista'),
      lugar_trabajo: formData.get('lugar_trabajo') || 'Oficina Central',
      cargo: formData.get('cargo'),
      funcion: formData.get('funcion'),
      area_id: formData.get('area_id') ? parseInt(formData.get('area_id')) : null,
      estado: formData.get('estado') || 'Activo'
    };

    try {
      const res = await apiFetch(`${API_BASE}/api/personal/${personalId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        alert("✅ ¡Registro actualizado exitosamente!");
        form.reset();
        form.dataset.editMode = 'false';
        delete form.dataset.editingId;
        const title = form.closest('.card')?.querySelector('.card-title');
        if (title) title.textContent = 'Alta Individual de Personal (Carga Manual)';
        const sb = form.querySelector('[type="submit"]');
        if (sb) { sb.textContent = '💾 Guardar y Registrar en Base de Datos'; sb.style = ''; }
        document.getElementById('btn-cancel-edit')?.remove();
        switchTab('tab-personal');
      } else {
        const errData = await res.json();
        alert("Error al actualizar: " + (errData.detail || "Verifique los datos"));
      }
    } catch (err) {
      alert("Error de conexión: " + err.message);
    }
    return;
  }

  // Modo nuevo: POST (comportamiento original)
  const formData = new FormData(form);
  const payload = {
    dni: formData.get('dni'),
    legajo: formData.get('legajo'),
    nombre: formData.get('nombre'),
    apellido: formData.get('apellido'),
    email: formData.get('email'),
    telefono: formData.get('telefono'),
    fecha_nacimiento: formData.get('fecha_nacimiento'),
    genero: formData.get('genero'),
    direccion: formData.get('direccion'),
    fecha_ingreso: formData.get('fecha_ingreso'),
    situacion_revista: formData.get('situacion_revista'),
    lugar_trabajo: formData.get('lugar_trabajo') || 'Oficina Central',
    cargo: formData.get('cargo'),
    funcion: formData.get('funcion'),
    area_id: formData.get('area_id') ? parseInt(formData.get('area_id')) : null,
    estado: formData.get('estado') || 'Activo'
  };

  try {
    const res = await apiFetch(`${API_BASE}/api/personal`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      alert("¡Empleado registrado exitosamente en la base de datos!");
      form.reset();
      switchTab('tab-personal');
    } else {
      const errData = await res.json();
      alert("Error al registrar: " + (errData.detail || "Verifique los datos (DNI duplicado, etc.)"));
    }
  } catch (err) {
    alert("Error de conexión: " + err.message);
  }
}

// ==========================================
// MODAL NUEVA LICENCIA (CON SELECT2 OFFLINE)
// ==========================================
async function abrirModalNuevaLicencia() {
  // Si no tenemos la lista cargada, la cargamos
  if (!AppState.personalList || AppState.personalList.length === 0) {
    await loadPersonal();
  }
  const selPersonal = document.getElementById('lic-personal-id');
  if (selPersonal) {
    selPersonal.innerHTML = '<option value="">Seleccione o busque un agente por apellido o DNI...</option>';
    AppState.personalList.forEach(p => {
      selPersonal.innerHTML += `<option value="${p.id}">${escapeHtml(p.apellido)}, ${escapeHtml(p.nombre)} (DNI: ${p.dni} - ${escapeHtml(p.situacion_revista || '')})</option>`;
    });
  }

  // Resetear campos contextuales
  const camposMedicos = document.getElementById('lic-campos-medicos');
  const camposFamiliar = document.getElementById('lic-campos-familiar');
  const camposViaje = document.getElementById('lic-campos-viaje');
  const camposAuditoria = document.getElementById('lic-auditoria-medica');
  if (camposMedicos) camposMedicos.style.display = 'none';
  if (camposFamiliar) camposFamiliar.style.display = 'none';
  if (camposViaje) camposViaje.style.display = 'none';
  if (camposAuditoria) camposAuditoria.style.display = 'none';

  // Pre-cargar el año actual como período
  const periodoInput = document.getElementById('lic-periodo-anual');
  if (periodoInput && !periodoInput.value) {
    periodoInput.value = new Date().getFullYear();
  }

  abrirModal('modal-nueva-licencia');

  // Inicialización de Select2 si está disponible
  if (window.$ && $.fn.select2) {
    setTimeout(() => {
      $('#lic-personal-id').select2({
        placeholder: "🔍 Buscar agente por apellido o DNI...",
        allowClear: true,
        width: '100%',
        dropdownParent: $('#modal-nueva-licencia .modal-box')
      });

      $('#lic-tipo-licencia').select2({
        placeholder: "Seleccione un tipo de licencia...",
        allowClear: false,
        width: '100%',
        dropdownParent: $('#modal-nueva-licencia .modal-box')
      }).off('select2:select').on('select2:select', function() {
        onTipoLicenciaChange();
      });
    }, 50);
  }
}


async function guardarNuevaLicencia(e) {
  e.preventDefault();
  const form = document.getElementById('form-nueva-licencia');
  const formData = new FormData(form);

  const payload = {
    personal_id: parseInt(formData.get('personal_id')),
    tipo_licencia: formData.get('tipo_licencia'),
    fecha_inicio: formData.get('fecha_inicio'),
    fecha_fin: formData.get('fecha_fin'),
    dias_totales: parseInt(formData.get('dias_totales') || 1),
    diagnostico: formData.get('diagnostico'),
    certificado_numero: formData.get('certificado_numero'),
    medico_nombre: formData.get('medico_nombre'),
    medico_matricula: formData.get('medico_matricula'),
    estado_justificacion: formData.get('estado_justificacion') || 'Pendiente',
    auditado_salud_provincial: parseInt(formData.get('auditado_salud_provincial') || 0),
    observaciones: formData.get('observaciones'),
    // Campos extendidos DPRH
    periodo_anual: formData.get('periodo_anual') ? parseInt(formData.get('periodo_anual')) : new Date().getFullYear(),
    familiar_nombre: formData.get('familiar_nombre') || null,
    familiar_parentesco: formData.get('familiar_parentesco') || null,
    km_distancia: formData.get('km_distancia') ? parseInt(formData.get('km_distancia')) : null,
    dias_adicionales_viaje: parseInt(formData.get('dias_adicionales_viaje') || 0)
  };

  try {
    const res = await apiFetch(`${API_BASE}/api/licencias`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      alert("✅ Licencia registrada exitosamente.");
      cerrarModal('modal-nueva-licencia');
      form.reset();
      loadLicencias();
      loadDashboard();
    } else {
      const errData = await res.json();
      alert("Error al registrar licencia: " + (errData.detail || "Verifique los datos"));
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// Modal Helpers
function abrirModal(modalId) {
  document.getElementById(modalId)?.classList.add('active');
}

function cerrarModal(modalId) {
  document.getElementById(modalId)?.classList.remove('active');
}

function imprimirFicha() {
  window.print();
}

/**
 * Imprime exclusivamente el listado de personal actualmente visible o los agentes seleccionados,
 * abriendo una ventana nueva limpia sin sidebar ni modales.
 */
function imprimirListadoPersonal(soloSeleccionados = false) {
  const tbody = document.getElementById('tbody-personal');
  if (!tbody) return;

  let filas = Array.from(tbody.querySelectorAll('tr'));
  if (filas.length === 0) {
    alert('No hay personal para imprimir.');
    return;
  }

  if (soloSeleccionados) {
    filas = filas.filter(tr => tr.querySelector('.check-personal-row')?.checked);
    if (filas.length === 0) {
      alert('No hay agentes seleccionados para imprimir.');
      return;
    }
  }

  // Construir tabla HTML imprimible (excluyendo celda 0 de checkbox y la última celda de acciones)
  let filasHtml = '';
  filas.forEach(tr => {
    const celdas = tr.querySelectorAll('td');
    if (celdas.length < 3) return; // fila vacía o mensaje
    let row = '<tr>';
    for (let i = 1; i < celdas.length - 1; i++) {
      row += `<td>${celdas[i].innerText || ''}</td>`;
    }
    row += '</tr>';
    filasHtml += row;
  });

  const subTitulo = soloSeleccionados
    ? `Agentes Seleccionados (${filas.length}) — Dirección Provincial de Recursos Hídricos`
    : `Nómina General de Personal — Dirección Provincial de Recursos Hídricos`;

  const ventana = window.open('', '_blank', 'width=900,height=700');
  ventana.document.write(`<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Nómina de Personal – Recursos Hídricos</title>
  <style>
    body { font-family: Arial, sans-serif; font-size: 11px; margin: 20px; color: #000; }
    h2 { text-align: center; font-size: 14px; margin-bottom: 4px; }
    p.sub { text-align: center; font-size: 10px; color: #555; margin-bottom: 14px; }
    table { width: 100%; border-collapse: collapse; }
    th { background: #1e3a5f; color: #fff; padding: 6px 8px; text-align: left; font-size: 10px; }
    td { padding: 5px 8px; border-bottom: 1px solid #ddd; }
    tr:nth-child(even) td { background: #f5f8fc; }
    @media print { body { margin: 10mm; } }
  </style>
</head>
<body>
  <div style="display: flex; align-items: center; justify-content: center; gap: 14px; margin-bottom: 10px;">
    <img src="img/logo.png" alt="Logo DPRH" style="height: 42px; width: auto;">
    <div>
      <h2 style="margin: 0;">${subTitulo}</h2>
      <p class="sub" style="margin: 2px 0 0 0;">Generado el ${new Date().toLocaleDateString('es-AR', { dateStyle: 'long' })} — Sistema de Gestión de Personal</p>
    </div>
  </div>
  <table>
    <thead>
      <tr>
        <th>Agente / Legajo</th>
        <th>DNI</th>
        <th>Situación Revista</th>
        <th>Cargo</th>
        <th>Área Asignada</th>
        <th>Estado</th>
      </tr>
    </thead>
    <tbody>${filasHtml}</tbody>
  </table>
</body>
</html>`);
  ventana.document.close();
  ventana.focus();
  ventana.print();
}


function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

function escapeHtml(text) {
  if (!text) return '';
  return text.toString()
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ==========================================
// MÓDULO 1: GESTIÓN DE USUARIOS Y PERMISOS UI
// ==========================================
function toggleAccesoUsuarios() {
  const panel = document.getElementById('panel-usuarios-content');
  const btn = document.getElementById('btn-acceder-usuarios');
  if (!panel) return;
  const estaOculto = panel.style.display === 'none' || panel.style.display === '';
  if (estaOculto) {
    panel.style.display = 'block';
    if (btn) btn.innerHTML = `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M18 6l-12 12" /><path d="M6 6l12 12" /></svg><span>Cerrar Panel</span>`;
    loadUsuariosTable();
  } else {
    panel.style.display = 'none';
    if (btn) btn.innerHTML = `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M15 12a3 3 0 1 1 -6 0 3 3 0 0 1 6 0z" /><path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg><span>Acceder</span>`;
  }
}
async function loadUsuariosTable() {
  if (!tienePermiso('admin') && AppState.currentUser?.rol !== 'admin') return;
  try {
    const res = await apiFetch(`${API_BASE}/api/usuarios`);
    const users = await res.json();
    renderUsuariosTable(users);
  } catch (err) {
    console.error("Error al cargar lista de usuarios:", err);
  }
}

function renderUsuariosTable(users) {
  const tbody = document.getElementById('tbody-usuarios-list');
  if (!tbody) return;

  if (users.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="padding:16px;">No hay usuarios registrados.</td></tr>`;
    return;
  }

  tbody.innerHTML = users.map(u => {
    const esAdmin = u.rol === 'admin';
    const permisosCount = (u.permisos || []).length;
    const permisosBadge = esAdmin 
      ? '<span class="badge badge-planta">Control Total (Admin)</span>'
      : `<span class="badge badge-info">${permisosCount} permiso(s) otorgado(s)</span>`;

    return `
      <tr>
        <td><strong><code>${escapeHtml(u.username)}</code></strong></td>
        <td>${escapeHtml(u.nombre_completo)}</td>
        <td><span class="badge badge-${esAdmin ? 'gabinete' : 'contrato'}">${esAdmin ? 'Administrador General' : 'Personalizado'}</span></td>
        <td>${permisosBadge}</td>
        <td><span class="badge badge-${u.activo ? 'activo' : 'baja'}">${u.activo ? 'Activo' : 'Inactivo'}</span></td>
        <td>
          <div style="display: flex; gap: 6px;">
            <button class="btn btn-outline btn-sm" onclick="abrirModalEditarUsuario(${u.id})" title="Editar Usuario y Permisos" style="display: inline-flex; align-items: center; gap: 4px;">
              ${AppIcons.edit} <span>Editar</span>
            </button>
            ${u.username !== 'admin' ? `
              <button class="btn btn-outline btn-sm btn-icon-only" style="color:var(--danger);" onclick="eliminarUsuarioUI(${u.id})" title="Eliminar Usuario">${AppIcons.trash}</button>
            ` : ''}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function togglePermisosSegunRol() {
  const rolSelect = document.getElementById('usr-rol');
  const boxPermisos = document.getElementById('box-permisos-granulares');
  if (rolSelect && boxPermisos) {
    boxPermisos.style.display = rolSelect.value === 'admin' ? 'none' : 'block';
  }
}

function abrirModalUsuario() {
  const titleText = document.getElementById('modal-usuario-title-text');
  if (titleText) titleText.innerText = 'Crear Nuevo Usuario';
  else document.getElementById('modal-usuario-title').innerText = 'Crear Nuevo Usuario';

  document.getElementById('usuario-id').value = '';
  document.getElementById('usr-username').value = '';
  document.getElementById('usr-username').readOnly = false;
  document.getElementById('usr-nombre-completo').value = '';
  document.getElementById('usr-password').value = '';
  document.getElementById('usr-password').required = true;
  document.getElementById('usr-password').placeholder = 'Ingrese contraseña';
  
  const rolSelect = document.getElementById('usr-rol');
  if (rolSelect) {
    rolSelect.value = 'personalizado';
    rolSelect.disabled = false;
  }

  document.querySelectorAll('.chk-permiso').forEach(chk => chk.checked = false);
  togglePermisosSegunRol();
  abrirModal('modal-usuario');
}

async function abrirModalEditarUsuario(usuarioId) {
  try {
    const res = await apiFetch(`${API_BASE}/api/usuarios`);
    const users = await res.json();
    const u = users.find(x => x.id === usuarioId || x.id == usuarioId);
    if (!u) {
      alert("No se encontró el usuario solicitado.");
      return;
    }

    const titleText = document.getElementById('modal-usuario-title-text');
    if (titleText) titleText.innerText = `Editar Usuario: ${u.username}`;
    else {
      const modalTitle = document.getElementById('modal-usuario-title');
      if (modalTitle) modalTitle.innerText = `Editar Usuario: ${u.username}`;
    }

    document.getElementById('usuario-id').value = u.id;
    document.getElementById('usr-username').value = u.username || '';
    document.getElementById('usr-username').readOnly = true;
    document.getElementById('usr-nombre-completo').value = u.nombre_completo || '';
    document.getElementById('usr-password').value = '';
    document.getElementById('usr-password').required = false;
    document.getElementById('usr-password').placeholder = 'Dejar en blanco para mantener la contraseña actual';

    const rolSelect = document.getElementById('usr-rol');
    if (rolSelect) {
      rolSelect.value = u.rol || (u.username === 'admin' ? 'admin' : 'personalizado');
      // Proteger cuenta admin para que siempre mantenga rol admin
      rolSelect.disabled = (u.username === 'admin');
    }

    const permisosArr = u.permisos || [];
    document.querySelectorAll('.chk-permiso').forEach(chk => {
      chk.checked = permisosArr.includes(chk.value);
    });

    togglePermisosSegunRol();
    abrirModal('modal-usuario');
  } catch (err) {
    alert("Error al cargar datos del usuario: " + err.message);
  }
}

async function guardarUsuario(e) {
  if (e) e.preventDefault();
  const id = document.getElementById('usuario-id').value;
  const username = document.getElementById('usr-username').value.trim();
  const nombreCompleto = document.getElementById('usr-nombre-completo').value.trim();
  const password = document.getElementById('usr-password').value;
  const rolSelect = document.getElementById('usr-rol');
  let rol = rolSelect ? rolSelect.value : 'personalizado';
  if (username === 'admin') rol = 'admin';

  if (!nombreCompleto) {
    alert("Por favor ingrese el Nombre Completo.");
    return;
  }

  const permisos = [];
  if (rol !== 'admin') {
    document.querySelectorAll('.chk-permiso:checked').forEach(chk => permisos.push(chk.value));
  }

  const isEdit = !!id;
  const url = isEdit ? `${API_BASE}/api/usuarios/${id}` : `${API_BASE}/api/usuarios`;
  const method = isEdit ? 'PUT' : 'POST';

  const payload = {
    username,
    nombre_completo: nombreCompleto,
    rol,
    permisos
  };
  if (password && password.trim() !== '') {
    payload.password = password.trim();
  }

  try {
    const res = await apiFetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      alert(isEdit ? "✅ Usuario y credenciales actualizados correctamente." : "✅ Usuario creado exitosamente.");
      
      // Si se editó el usuario activo en sesión (ej: admin), actualizar su nombre visible en la cabecera
      if (AppState.currentUser && (AppState.currentUser.username === username || AppState.currentUser.id == id)) {
        AppState.currentUser.nombre_completo = nombreCompleto;
        const userDisplay = document.getElementById('user-display-name');
        if (userDisplay) userDisplay.innerText = nombreCompleto || username;
        try {
          localStorage.setItem('dprh_user_session', JSON.stringify(AppState.currentUser));
        } catch (_) {}
      }

      cerrarModal('modal-usuario');
      loadUsuariosTable();
    } else {
      const errData = await res.json();
      alert("Error: " + (errData.detail || "Verifique los datos"));
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

async function eliminarUsuarioUI(usuarioId) {
  if (!confirm("¿Está seguro de eliminar esta cuenta de usuario?")) return;
  try {
    const res = await apiFetch(`${API_BASE}/api/usuarios/${usuarioId}`, { method: 'DELETE' });
    if (res.ok) {
      alert("✅ Usuario eliminado.");
      loadUsuariosTable();
    } else {
      const err = await res.json();
      alert("Error: " + err.detail);
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// ==========================================
// GESTOR DE CONTENIDO Y CATÁLOGOS DINÁMICOS
// ==========================================
async function cargarCatalogosUI() {
  try {
    const res = await apiFetch(`${API_BASE}/api/catalogos`);
    if (!res.ok) return;
    const cat = await res.json();
    AppState.catalogos = cat;

    // 1. Render Situaciones de Revista
    renderCatalogoRevistasUI(cat.situaciones_revista || []);

    // 2. Render Áreas y Dependencias
    renderCatalogoAreasUI(cat.areas || []);

    // 3. Render Lugares y Funciones
    renderCatalogoLugaresUI(cat.lugares_trabajo || []);
    renderCatalogoFuncionesUI(cat.funciones || []);

    // 4. Render Normativas de Licencias
    const resNorm = await apiFetch(`${API_BASE}/api/licencias/normativa`);
    if (resNorm.ok) {
      const normativas = await resNorm.json();
      AppState.normativa = normativas;
      renderCatalogoNormativaUI(normativas);
    }

    // Poblar dinámicamente todos los select de la app
    poblarSelectsCatalogos();
  } catch (err) {
    console.error("Error al cargar catálogos:", err);
  }
}

function cambiarPestanaCatalogo(pestana) {
  document.querySelectorAll('.catalog-tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.catalog-tab-pane').forEach(p => p.style.display = 'none');

  if (pestana === 'revistas') {
    document.getElementById('btn-cat-tab-revistas')?.classList.add('active');
    const p = document.getElementById('cat-tab-content-revistas');
    if (p) p.style.display = 'block';
  } else if (pestana === 'areas') {
    document.getElementById('btn-cat-tab-areas')?.classList.add('active');
    const p = document.getElementById('cat-tab-content-areas');
    if (p) p.style.display = 'block';
  } else if (pestana === 'lugares-funciones') {
    document.getElementById('btn-cat-tab-lugares-funciones')?.classList.add('active');
    const p = document.getElementById('cat-tab-content-lugares-funciones');
    if (p) p.style.display = 'block';
  } else if (pestana === 'normativa') {
    document.getElementById('btn-cat-tab-normativa')?.classList.add('active');
    const p = document.getElementById('cat-tab-content-normativa');
    if (p) p.style.display = 'block';
  }
}

function renderCatalogoRevistasUI(items) {
  const container = document.getElementById('catalogo-revistas-container');
  const countEl = document.getElementById('cat-count-revistas');
  if (countEl) countEl.innerText = items.length;
  if (!container) return;

  if (items.length === 0) {
    container.innerHTML = '<div style="color:var(--text-muted); font-size:13px; padding:12px;">No hay situaciones de revista configuradas.</div>';
    return;
  }

  container.innerHTML = items.map((item, idx) => {
    const badgeClass = getBadgeRevistaClass(item);
    return `
      <div class="catalog-item-card">
        <div class="catalog-item-title">
          <span class="badge badge-${badgeClass}">${escapeHtml(item)}</span>
        </div>
        <div class="catalog-item-actions">
          <button type="button" class="btn btn-outline btn-xs" onclick="editarCatalogoItem('situacion_revista', ${idx})" title="Editar">✏️ Editar</button>
          <button type="button" class="btn btn-outline btn-xs" style="color:var(--danger);" onclick="eliminarCatalogoItem('situacion_revista', ${idx})" title="Eliminar">🗑️</button>
        </div>
      </div>
    `;
  }).join('');
}

function renderCatalogoAreasUI(areas) {
  const tbody = document.getElementById('tbody-catalogo-areas');
  const countEl = document.getElementById('cat-count-areas');
  if (countEl) countEl.innerText = areas.length;
  if (!tbody) return;

  if (areas.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="padding:16px;">No hay áreas registradas.</td></tr>';
    return;
  }

  const areasMap = {};
  areas.forEach(a => { areasMap[a.id] = a.nombre; });

  const getNivelBadge = (nivel) => {
    switch (nivel) {
      case 1: return '<span class="badge badge-planta">1 - Dirección General</span>';
      case 2: return '<span class="badge badge-gabinete">2 - Área / Dirección</span>';
      case 3: return '<span class="badge badge-info">3 - Departamento</span>';
      case 4: return '<span class="badge badge-contrato">4 - División / Sector</span>';
      default: return `<span class="badge badge-outline">Nivel ${nivel}</span>`;
    }
  };

  tbody.innerHTML = areas.map(a => {
    const parentNombre = a.parent_id && areasMap[a.parent_id] ? escapeHtml(areasMap[a.parent_id]) : '<em>— Nivel Superior —</em>';
    const personalCount = a.total_personal !== undefined ? a.total_personal : (a.personal ? a.personal.length : 0);
    return `
      <tr>
        <td>${getNivelBadge(a.nivel)}</td>
        <td><strong>${escapeHtml(a.nombre)}</strong> ${a.codigo ? `<small class="text-muted">(${escapeHtml(a.codigo)})</small>` : ''}</td>
        <td>${parentNombre}</td>
        <td>${escapeHtml(a.responsable || '—')}</td>
        <td><span class="badge badge-activo">${personalCount} agente(s)</span></td>
        <td>
          <div style="display:flex; gap:6px;">
            <button class="btn btn-outline btn-sm" onclick="abrirModalEditarArea(${a.id})" title="Editar Dependencia" style="display:inline-flex; align-items:center; gap:4px;">
              ${AppIcons.edit} <span>Editar</span>
            </button>
            <button class="btn btn-outline btn-sm btn-icon-only" style="color:var(--danger);" onclick="eliminarAreaCatalogoUI(${a.id})" title="Eliminar Dependencia">
              ${AppIcons.trash}
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function renderCatalogoLugaresUI(items) {
  const container = document.getElementById('catalogo-lugares-container');
  const countEl = document.getElementById('cat-count-lugares');
  if (countEl) countEl.innerText = items.length;
  if (!container) return;

  if (items.length === 0) {
    container.innerHTML = '<div style="color:var(--text-muted); font-size:12px; padding:8px;">No hay lugares registrados.</div>';
    return;
  }

  container.innerHTML = items.map((item, idx) => `
    <div class="catalog-subitem-row">
      <span style="font-weight:600; color:var(--text-main);">📍 ${escapeHtml(item)}</span>
      <div style="display:flex; gap:4px;">
        <button type="button" class="btn btn-outline btn-xs" onclick="editarCatalogoItem('lugares_trabajo', ${idx})" title="Editar">✏️</button>
        <button type="button" class="btn btn-outline btn-xs" style="color:var(--danger);" onclick="eliminarCatalogoItem('lugares_trabajo', ${idx})" title="Eliminar">🗑️</button>
      </div>
    </div>
  `).join('');
}

function renderCatalogoFuncionesUI(items) {
  const container = document.getElementById('catalogo-funciones-container');
  const countEl = document.getElementById('cat-count-funciones');
  if (countEl) countEl.innerText = items.length;
  if (!container) return;

  if (items.length === 0) {
    container.innerHTML = '<div style="color:var(--text-muted); font-size:12px; padding:8px;">No hay funciones registradas.</div>';
    return;
  }

  container.innerHTML = items.map((item, idx) => `
    <div class="catalog-subitem-row">
      <span style="font-weight:600; color:var(--text-main);">💼 ${escapeHtml(item)}</span>
      <div style="display:flex; gap:4px;">
        <button type="button" class="btn btn-outline btn-xs" onclick="editarCatalogoItem('funciones', ${idx})" title="Editar">✏️</button>
        <button type="button" class="btn btn-outline btn-xs" style="color:var(--danger);" onclick="eliminarCatalogoItem('funciones', ${idx})" title="Eliminar">🗑️</button>
      </div>
    </div>
  `).join('');
}

async function agregarCatalogoItem(tipo) {
  if (tipo === 'area') {
    abrirModalCrearArea();
    return;
  }

  let promptMsg = "";
  if (tipo === 'situacion_revista') promptMsg = "Ingrese el nombre de la nueva Situación de Revista:";
  else if (tipo === 'lugares_trabajo') promptMsg = "Ingrese el nombre del nuevo Lugar de Trabajo / Sede:";
  else if (tipo === 'funciones') promptMsg = "Ingrese el nombre de la nueva Función Operativa:";

  const nuevo = prompt(promptMsg);
  if (!nuevo || !nuevo.trim()) return;
  const valorLimpio = nuevo.trim();

  let endpoint = "";
  let items = [];
  if (tipo === 'situacion_revista') {
    endpoint = `${API_BASE}/api/catalogos/situacion_revista`;
    items = [...(AppState.catalogos?.situaciones_revista || [])];
  } else if (tipo === 'lugares_trabajo') {
    endpoint = `${API_BASE}/api/catalogos/lugares_trabajo`;
    items = [...(AppState.catalogos?.lugares_trabajo || [])];
  } else if (tipo === 'funciones') {
    endpoint = `${API_BASE}/api/catalogos/funciones`;
    items = [...(AppState.catalogos?.funciones || [])];
  }

  if (items.some(x => x.toLowerCase() === valorLimpio.toLowerCase())) {
    alert("Este elemento ya existe en el catálogo.");
    return;
  }

  items.push(valorLimpio);

  try {
    const res = await apiFetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(items)
    });
    if (res.ok) {
      await cargarCatalogosUI();
    } else {
      alert("Error al guardar en el catálogo.");
    }
  } catch (err) {
    alert("Error de conexión: " + err.message);
  }
}

async function editarCatalogoItem(tipo, index) {
  let items = [];
  let endpoint = "";
  let nombreTipo = "";
  if (tipo === 'situacion_revista') {
    items = [...(AppState.catalogos?.situaciones_revista || [])];
    endpoint = `${API_BASE}/api/catalogos/situacion_revista`;
    nombreTipo = "Situación de Revista";
  } else if (tipo === 'lugares_trabajo') {
    items = [...(AppState.catalogos?.lugares_trabajo || [])];
    endpoint = `${API_BASE}/api/catalogos/lugares_trabajo`;
    nombreTipo = "Lugar de Trabajo";
  } else if (tipo === 'funciones') {
    items = [...(AppState.catalogos?.funciones || [])];
    endpoint = `${API_BASE}/api/catalogos/funciones`;
    nombreTipo = "Función Operativa";
  }

  if (index < 0 || index >= items.length) return;
  const actual = items[index];
  const editado = prompt(`Editar ${nombreTipo}:`, actual);
  if (!editado || !editado.trim() || editado.trim() === actual) return;

  items[index] = editado.trim();

  try {
    const res = await apiFetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(items)
    });
    if (res.ok) {
      await cargarCatalogosUI();
    } else {
      alert("Error al actualizar el elemento en el catálogo.");
    }
  } catch (err) {
    alert("Error de conexión: " + err.message);
  }
}

async function eliminarCatalogoItem(tipo, index) {
  let items = [];
  let endpoint = "";
  if (tipo === 'situacion_revista') {
    items = [...(AppState.catalogos?.situaciones_revista || [])];
    endpoint = `${API_BASE}/api/catalogos/situacion_revista`;
  } else if (tipo === 'lugares_trabajo') {
    items = [...(AppState.catalogos?.lugares_trabajo || [])];
    endpoint = `${API_BASE}/api/catalogos/lugares_trabajo`;
  } else if (tipo === 'funciones') {
    items = [...(AppState.catalogos?.funciones || [])];
    endpoint = `${API_BASE}/api/catalogos/funciones`;
  }

  if (index < 0 || index >= items.length) return;
  const item = items[index];
  if (!confirm(`¿Está seguro de eliminar "${item}" del catálogo?`)) return;

  items.splice(index, 1);

  try {
    const res = await apiFetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(items)
    });
    if (res.ok) {
      await cargarCatalogosUI();
    } else {
      alert("Error al eliminar el elemento del catálogo.");
    }
  } catch (err) {
    alert("Error de conexión: " + err.message);
  }
}

async function eliminarAreaCatalogoUI(areaId) {
  if (!confirm("¿Está seguro de eliminar esta área / dependencia del organigrama?")) return;
  try {
    const res = await apiFetch(`${API_BASE}/api/areas/${areaId}`, { method: 'DELETE' });
    if (res.ok) {
      await loadAreas();
      await cargarCatalogosUI();
      if (typeof loadOrganigrama === 'function') loadOrganigrama();
    } else {
      alert("Error al eliminar el área.");
    }
  } catch (err) {
    alert("Error de conexión: " + err.message);
  }
}

function renderCatalogoNormativaUI(items) {
  const container = document.getElementById('catalogo-normativa-container');
  const countEl = document.getElementById('cat-count-normativa');
  if (countEl) countEl.innerText = items.length;
  if (!container) return;

  if (items.length === 0) {
    container.innerHTML = '<div style="color:var(--text-muted); font-size:13px; padding:12px;">No hay normas de licencia configuradas.</div>';
    return;
  }

  container.innerHTML = items.map((item, idx) => `
    <div class="card" style="padding: 14px; margin-bottom: 8px; border: 1px solid var(--surface-border); border-left: 4px solid var(--primary-light);">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; margin-bottom: 8px; flex-wrap: wrap;">
        <div>
          <h4 style="color: var(--primary-dark); font-size: 14px; margin: 0 0 4px 0; font-weight: 700;">${escapeHtml(item.tipo)}</h4>
          <span class="badge badge-info">${escapeHtml(item.articulo || 'Sin artículo')}</span>
          ${item.regimen ? `<span class="badge badge-outline" style="margin-left:4px;">${escapeHtml(item.regimen)}</span>` : ''}
        </div>
        <div style="display: flex; gap: 6px;">
          <button type="button" class="btn btn-outline btn-xs" onclick="abrirModalNormativa(${idx})" style="display:inline-flex; align-items:center; gap:4px;">
            ✏️ Editar
          </button>
          <button type="button" class="btn btn-outline btn-xs" style="color:var(--danger);" onclick="eliminarNormativaItem(${idx})" title="Eliminar">
            🗑️
          </button>
        </div>
      </div>
      <div style="font-size: 12.5px; color: var(--text-main); display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 6px;">
        <p style="margin: 0;"><strong>Planta Permanente:</strong> ${escapeHtml(item.limite_planta || '—')}</p>
        <p style="margin: 0;"><strong>Contratados / Locación:</strong> ${escapeHtml(item.limite_contratados || '—')}</p>
      </div>
      ${item.requisito ? `<p style="font-size: 11.5px; color: var(--text-muted); margin: 0;"><strong>Requisitos:</strong> ${escapeHtml(item.requisito)}</p>` : ''}
    </div>
  `).join('');
}

function abrirModalNormativa(index = null) {
  const titleText = document.getElementById('modal-normativa-title-text');
  const indexInput = document.getElementById('normativa-edit-index');

  const tipoInput = document.getElementById('normativa-input-tipo');
  const artInput = document.getElementById('normativa-input-articulo');
  const regInput = document.getElementById('normativa-input-regimen');
  const limPlantaInput = document.getElementById('normativa-input-limite-planta');
  const limContrInput = document.getElementById('normativa-input-limite-contratados');
  const reqInput = document.getElementById('normativa-input-requisito');

  if (index !== null && index >= 0 && AppState.normativa && AppState.normativa[index]) {
    const item = AppState.normativa[index];
    if (titleText) titleText.innerText = "Editar Norma de Licencia";
    if (indexInput) indexInput.value = index;
    if (tipoInput) tipoInput.value = item.tipo || '';
    if (artInput) artInput.value = item.articulo || '';
    if (regInput) regInput.value = item.regimen || '';
    if (limPlantaInput) limPlantaInput.value = item.limite_planta || '';
    if (limContrInput) limContrInput.value = item.limite_contratados || '';
    if (reqInput) reqInput.value = item.requisito || '';
  } else {
    if (titleText) titleText.innerText = "Nueva Norma de Licencia";
    if (indexInput) indexInput.value = -1;
    if (tipoInput) tipoInput.value = '';
    if (artInput) artInput.value = '';
    if (regInput) regInput.value = 'Descanso Anual';
    if (limPlantaInput) limPlantaInput.value = '';
    if (limContrInput) limContrInput.value = '';
    if (reqInput) reqInput.value = '';
  }

  abrirModal('modal-normativa');
}

async function guardarNormativaModal(e) {
  e.preventDefault();
  const index = parseInt(document.getElementById('normativa-edit-index').value, 10);
  const tipo = document.getElementById('normativa-input-tipo').value.trim();
  const articulo = document.getElementById('normativa-input-articulo').value.trim();
  const regimen = document.getElementById('normativa-input-regimen').value.trim();
  const limite_planta = document.getElementById('normativa-input-limite-planta').value.trim();
  const limite_contratados = document.getElementById('normativa-input-limite-contratados').value.trim();
  const requisito = document.getElementById('normativa-input-requisito').value.trim();

  if (!tipo || !articulo) {
    alert("El tipo de licencia y el artículo son obligatorios.");
    return;
  }

  const items = [...(AppState.normativa || [])];
  const itemData = {
    tipo,
    articulo,
    regimen: regimen || 'General',
    limite_planta: limite_planta || 'No especificado',
    limite_contratados: limite_contratados || 'No especificado',
    requisito: requisito || 'Requisitos normativos habituales'
  };

  if (index >= 0 && index < items.length) {
    items[index] = itemData;
  } else {
    items.push(itemData);
  }

  try {
    const res = await apiFetch(`${API_BASE}/api/catalogos/normativa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(items)
    });
    if (res.ok) {
      AppState.normativa = items;
      renderCatalogoNormativaUI(items);
      if (typeof loadNormativaCatalog === 'function') loadNormativaCatalog();
      cerrarModal('modal-normativa');
      alert("✅ Catálogo normativo actualizado correctamente.");
    } else {
      alert("Error al guardar la norma en el catálogo.");
    }
  } catch (err) {
    alert("Error de conexión: " + err.message);
  }
}

async function eliminarNormativaItem(index) {
  const items = [...(AppState.normativa || [])];
  if (index < 0 || index >= items.length) return;
  const item = items[index];
  if (!confirm(`¿Está seguro de eliminar la norma "${item.tipo}" (${item.articulo}) del catálogo?`)) return;

  items.splice(index, 1);

  try {
    const res = await apiFetch(`${API_BASE}/api/catalogos/normativa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(items)
    });
    if (res.ok) {
      AppState.normativa = items;
      renderCatalogoNormativaUI(items);
      if (typeof loadNormativaCatalog === 'function') loadNormativaCatalog();
    } else {
      alert("Error al eliminar la norma del catálogo.");
    }
  } catch (err) {
    alert("Error de conexión: " + err.message);
  }
}

function poblarSelectsCatalogos() {
  const cat = AppState.catalogos;
  if (!cat) return;

  // 1. Situación de Revista en Cargar Datos
  const selRevistaNuevo = document.getElementById('nuevo-situacion-revista');
  if (selRevistaNuevo) {
    const valPrev = selRevistaNuevo.value;
    selRevistaNuevo.innerHTML = '<option value="">Seleccione Situación de Revista...</option>';
    (cat.situaciones_revista || []).forEach(r => {
      selRevistaNuevo.innerHTML += `<option value="${escapeHtml(r)}">${escapeHtml(r)}</option>`;
    });
    if (valPrev) selRevistaNuevo.value = valPrev;
    else if (cat.situaciones_revista?.length > 0) selRevistaNuevo.value = cat.situaciones_revista[0];
  }

  // 2. Filtro Situación de Revista en Personal
  const selRevistaFiltro = document.getElementById('filter-personal-revista');
  if (selRevistaFiltro) {
    const valPrev = selRevistaFiltro.value;
    selRevistaFiltro.innerHTML = '<option value="">Todas las Revistas</option>';
    (cat.situaciones_revista || []).forEach(r => {
      selRevistaFiltro.innerHTML += `<option value="${escapeHtml(r)}">${escapeHtml(r)}</option>`;
    });
    if (valPrev) selRevistaFiltro.value = valPrev;
  }

  // 3. Lugar de Trabajo en Cargar Datos
  const selLugarNuevo = document.getElementById('nuevo-lugar-trabajo');
  if (selLugarNuevo) {
    const valPrev = selLugarNuevo.value;
    selLugarNuevo.innerHTML = '<option value="">Seleccione Lugar de Trabajo...</option>';
    (cat.lugares_trabajo || []).forEach(l => {
      selLugarNuevo.innerHTML += `<option value="${escapeHtml(l)}">${escapeHtml(l)}</option>`;
    });
    if (valPrev) selLugarNuevo.value = valPrev;
    else selLugarNuevo.value = "Oficina Central";
  }

  // 4. Función Operativa en Cargar Datos
  const selFuncionNuevo = document.getElementById('nuevo-funcion');
  if (selFuncionNuevo) {
    const valPrev = selFuncionNuevo.value;
    selFuncionNuevo.innerHTML = '<option value="">Seleccione Función...</option>';
    (cat.funciones || []).forEach(f => {
      selFuncionNuevo.innerHTML += `<option value="${escapeHtml(f)}">${escapeHtml(f)}</option>`;
    });
    if (valPrev) selFuncionNuevo.value = valPrev;
  }

  // 5. Áreas y Dependencias en Cargar Datos, Filtros y Modal Área
  const areas = cat.areas || AppState.areasList || [];
  const selAreaNuevo = document.getElementById('nuevo-area-id');
  const selAreaFiltro = document.getElementById('filter-personal-area');
  const selAreaParent = document.getElementById('area-parent-id');

  if (selAreaNuevo) {
    const valPrev = selAreaNuevo.value;
    selAreaNuevo.innerHTML = '<option value="">Seleccione Área...</option>';
    areas.forEach(a => {
      selAreaNuevo.innerHTML += `<option value="${a.id}">${escapeHtml(a.nombre)}</option>`;
    });
    if (valPrev) selAreaNuevo.value = valPrev;
  }

  if (selAreaFiltro) {
    const valPrev = selAreaFiltro.value;
    selAreaFiltro.innerHTML = '<option value="">Todas las Áreas</option>';
    areas.forEach(a => {
      selAreaFiltro.innerHTML += `<option value="${a.id}">${escapeHtml(a.nombre)}</option>`;
    });
    if (valPrev) selAreaFiltro.value = valPrev;
  }

  if (selAreaParent) {
    const valPrev = selAreaParent.value;
    selAreaParent.innerHTML = '<option value="">-- Ninguna (Nivel Superior Principal) --</option>';
    areas.forEach(a => {
      selAreaParent.innerHTML += `<option value="${a.id}">${escapeHtml(a.nombre)}</option>`;
    });
    if (valPrev) selAreaParent.value = valPrev;
  }
}

// ==========================================
// MÓDULO 4: GESTIÓN Y DESCUENTO DE COMPENSATORIOS
// ==========================================
async function loadCompensatorios() {
  try {
    // 1. Cargar agentes en los selects de compensatorios
    const resPers = await apiFetch(`${API_BASE}/api/personal`);
    const personal = await resPers.json();
    
    const selCarga = document.getElementById('comp-carga-agente-id');
    const selSoli = document.getElementById('comp-solicitar-agente-id');

    const optionsHtml = '<option value="">-- Seleccionar Agente --</option>' + personal.map(p => 
      `<option value="${p.id}">${escapeHtml(p.apellido)}, ${escapeHtml(p.nombre)} (DNI: ${p.dni})</option>`
    ).join('');

    if (selCarga) selCarga.innerHTML = optionsHtml;
    if (selSoli) selSoli.innerHTML = optionsHtml;

    // Establecer fecha de hoy en fecha de carga por defecto
    const hoyStr = new Date().toISOString().split('T')[0];
    const fechaCargaEl = document.getElementById('comp-carga-fecha');
    if (fechaCargaEl && !fechaCargaEl.value) fechaCargaEl.value = hoyStr;

    // 2. Cargar tabla de solicitudes
    const resSol = await apiFetch(`${API_BASE}/api/compensatorios/solicitudes`);
    const solicitudes = await resSol.json();
    renderTablaCompensatorios(solicitudes);
  } catch (err) {
    console.error("Error al cargar compensatorios:", err);
  }
}

async function actualizarInfoSaldoAgente(personalId, tipo) {
  const infoEl = document.getElementById(tipo === 'carga' ? 'comp-carga-saldo-info' : 'comp-solicitar-saldo-info');
  if (!infoEl) return;
  if (!personalId) {
    infoEl.innerText = '';
    return;
  }
  try {
    const res = await apiFetch(`${API_BASE}/api/compensatorios/saldo/${personalId}`);
    const saldoData = await res.json();
    const ultCarga = saldoData.fecha_ultima_carga ? ` (Última carga: ${saldoData.fecha_ultima_carga})` : '';
    infoEl.innerText = `Saldo Disponible Actual: ${saldoData.dias_disponibles} día(s)${ultCarga}`;
  } catch (err) {
    infoEl.innerText = '';
  }
}

async function calcularPreviaDiasHabiles() {
  const fIni = document.getElementById('comp-solicitar-fecha-inicio')?.value;
  const fFin = document.getElementById('comp-solicitar-fecha-fin')?.value;
  const prevEl = document.getElementById('comp-preview-dias-habiles');
  if (!prevEl) return;

  if (fIni && fFin) {
    if (fIni > fFin) {
      prevEl.innerHTML = `<span style="color: var(--danger); font-weight: 500;">⚠️ La fecha de inicio no puede ser posterior a la fecha de cierre.</span>`;
      return;
    }

    try {
      const res = await apiFetch(`${API_BASE}/api/compensatorios/calcular-dias-habiles?fecha_inicio=${fIni}&fecha_fin=${fFin}`);
      if (res.ok) {
        const data = await res.json();
        const dias = data.dias_habiles;
        const fines = data.fines_semana;
        const feriados = data.feriados || [];

        let detalles = [];
        if (fines > 0) detalles.push(`${fines} día(s) de fin de semana`);
        if (feriados.length > 0) {
          const nombresFeriados = feriados.map(f => `${f.fecha.slice(8,10)}/${f.fecha.slice(5,7)}: ${escapeHtml(f.descripcion)}`).join(', ');
          detalles.push(`${feriados.length} feriado(s) [${nombresFeriados}]`);
        }

        let detalleTexto = detalles.length > 0 ? `(excluye ${detalles.join(' y ')})` : '(sin feriados ni fines de semana intermedios)';

        if (dias === 0) {
          prevEl.innerHTML = `Cómputo estimado: <strong style="color: var(--danger); font-size: 13.5px;">0 días hábiles</strong> <span style="font-size: 11.5px; color: var(--text-muted);">${detalleTexto}</span>`;
        } else {
          prevEl.innerHTML = `Cómputo estimado: <strong style="color: #0284c7; font-size: 14px;">${dias} día(s) hábil(es)</strong> <br><span style="font-size: 11.5px; color: #475569;">${detalleTexto}</span>`;
        }
        return;
      }
    } catch (_) {}

    // Fallback local en caso de desconexión momentánea
    const p1 = fIni.split('-').map(Number);
    const p2 = fFin.split('-').map(Number);
    const d1 = new Date(p1[0], p1[1] - 1, p1[2]);
    const d2 = new Date(p2[0], p2[1] - 1, p2[2]);
    let count = 0;
    let cur = new Date(d1);
    while (cur <= d2) {
      const day = cur.getDay();
      if (day !== 0 && day !== 6) count++;
      cur.setDate(cur.getDate() + 1);
    }
    prevEl.innerHTML = `Cómputo estimado: <strong style="color: var(--primary);">${count} día(s) hábil(es)</strong>`;
  } else {
    prevEl.innerHTML = `Cómputo estimado: <strong>- días hábiles</strong> (excluye fines de semana y feriados oficiales)`;
  }
}

async function guardarCargaCompensatorio(e) {
  e.preventDefault();
  const personalId = parseInt(document.getElementById('comp-carga-agente-id').value);
  const dias = parseFloat(document.getElementById('comp-carga-dias').value);
  const fechaCarga = document.getElementById('comp-carga-fecha').value;
  const actaNumero = document.getElementById('comp-carga-acta').value.trim();
  const motivo = document.getElementById('comp-carga-motivo').value.trim();

  try {
    const res = await apiFetch(`${API_BASE}/api/compensatorios/cargar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ personal_id: personalId, dias, fecha_carga: fechaCarga, acta_numero: actaNumero, motivo })
    });
    if (res.ok) {
      const resData = await res.json();
      alert(`✅ Días cargados exitosamente. Nuevo saldo del agente: ${resData.nuevo_saldo} días.`);
      document.getElementById('form-cargar-compensatorio').reset();
      actualizarInfoSaldoAgente(personalId, 'carga');
      loadCompensatorios();
    } else {
      const err = await res.json();
      alert("Error: " + (err.detail || "No se pudo realizar la carga"));
    }
  } catch (err) {
    alert("Error de red: " + err.message);
  }
}

async function guardarSolicitudCompensatorio(e) {
  e.preventDefault();
  const personalId = parseInt(document.getElementById('comp-solicitar-agente-id').value);
  const fechaInicio = document.getElementById('comp-solicitar-fecha-inicio').value;
  const fechaFin = document.getElementById('comp-solicitar-fecha-fin').value;
  const actaNumero = document.getElementById('comp-solicitar-acta').value.trim();
  const observaciones = document.getElementById('comp-solicitar-obs').value.trim();

  try {
    const res = await apiFetch(`${API_BASE}/api/compensatorios/solicitar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ personal_id: personalId, fecha_inicio: fechaInicio, fecha_fin: fechaFin, acta_numero: actaNumero, observaciones })
    });

    if (res.ok) {
      const resData = await res.json();
      alert(`✅ Solicitud registrada correctamente.\n- Días Hábiles Descontados: ${resData.dias_descontados}\n- Nuevo Saldo Disponible: ${resData.nuevo_saldo} día(s)`);
      document.getElementById('form-solicitar-compensatorio').reset();
      actualizarInfoSaldoAgente(personalId, 'solicitud');
      loadCompensatorios();
    } else {
      const err = await res.json();
      alert("⚠️ " + (err.detail || "Error al procesar la solicitud"));
    }
  } catch (err) {
    alert("Error de red: " + err.message);
  }
}

function renderTablaCompensatorios(solicitudes) {
  const tbody = document.getElementById('tbody-compensatorios-solicitudes');
  if (!tbody) return;

  if (solicitudes.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding: 20px;">No hay solicitudes de compensatorios registradas.</td></tr>`;
    return;
  }

  tbody.innerHTML = solicitudes.map(s => `
    <tr>
      <td><strong>${escapeHtml(s.agente)}</strong><br><small class="text-muted">Leg: ${s.legajo || 'S/L'} | Área: ${escapeHtml(s.area_nombre || 'Sin Área')}</small></td>
      <td><code>${escapeHtml(s.acta_numero || ('CMP-'+s.id))}</code></td>
      <td>${s.fecha_inicio}</td>
      <td>${s.fecha_fin}</td>
      <td><strong>${s.dias_descontados} día(s) hábil(es)</strong></td>
      <td>
        <select class="form-control" style="padding: 2px 6px; font-size: 12px; width: auto;" onchange="cambiarEstadoCompensatorio(${s.id}, this.value)">
          <option value="Pendiente" ${s.estado === 'Pendiente' ? 'selected' : ''}>Pendiente</option>
          <option value="Aprobada" ${s.estado === 'Aprobada' || s.estado === 'Justificada' || s.estado === 'Autorizada' ? 'selected' : ''}>Aprobada / Autorizada</option>
          <option value="Observada" ${s.estado === 'Observada' ? 'selected' : ''}>Observada</option>
          <option value="Rechazada" ${s.estado === 'Rechazada' ? 'selected' : ''}>Rechazada (Reembolsa Saldo)</option>
        </select>
      </td>
      <td>
        <button class="btn btn-outline btn-sm" onclick="descargarPDFCompensatorio(${s.id})" title="Imprimir Formulario Oficial con 3 Firmas" style="display: inline-flex; align-items: center; gap: 4px;">
          ${AppIcons.printer} <span>Formulario PDF</span>
        </button>
      </td>
    </tr>
  `).join('');
}

async function cambiarEstadoCompensatorio(solicitudId, nuevoEstado) {
  try {
    const res = await apiFetch(`${API_BASE}/api/compensatorios/solicitudes/${solicitudId}/estado`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ estado: nuevoEstado })
    });
    if (res.ok) {
      alert(`✅ Estado de la solicitud de compensatorio actualizado a '${nuevoEstado}'.`);
      loadCompensatorios();
    } else {
      const err = await res.json();
      alert("Error: " + err.detail);
      loadCompensatorios();
    }
  } catch (err) {
    alert("Error de conexión: " + err.message);
  }
}

function descargarPDFCompensatorio(solicitudId) {
  window.open(`${API_BASE}/api/compensatorios/solicitudes/${solicitudId}/pdf`, '_blank');
}

// ==========================================
// MÓDULO 5: GESTIÓN DE ORGANIGRAMA Y ESTRUCTURA
// ==========================================
function abrirModalCrearArea() {
  const titleText = document.getElementById('modal-area-title-text');
  if (titleText) titleText.innerText = 'Agregar Nueva Unidad Organizativa';
  else document.getElementById('modal-area-title').innerText = 'Agregar Nueva Unidad Organizativa';

  document.getElementById('area-id').value = '';
  document.getElementById('area-nombre').value = '';
  document.getElementById('area-codigo').value = '';
  document.getElementById('area-nivel').value = '3';
  document.getElementById('area-responsable').value = '';
  document.getElementById('area-descripcion').value = '';

  // Poblar áreas padres
  const parentSel = document.getElementById('area-parent-id');
  if (parentSel) {
    parentSel.innerHTML = '<option value="">-- Ninguna (Nivel Superior Principal) --</option>' + 
      AppState.areasList.map(a => `<option value="${a.id}">${escapeHtml(a.nombre)}</option>`).join('');
  }

  abrirModal('modal-area');
}

function abrirModalEditarArea(areaId) {
  const a = AppState.areasList.find(x => x.id === areaId);
  if (!a) return;

  const titleText = document.getElementById('modal-area-title-text');
  if (titleText) titleText.innerText = `Editar Unidad: ${a.nombre}`;
  else document.getElementById('modal-area-title').innerText = `Editar Unidad: ${a.nombre}`;
  document.getElementById('area-id').value = a.id;
  document.getElementById('area-nombre').value = a.nombre;
  document.getElementById('area-codigo').value = a.codigo || '';
  document.getElementById('area-nivel').value = a.nivel;
  document.getElementById('area-responsable').value = a.responsable || '';
  document.getElementById('area-descripcion').value = a.descripcion || '';

  const parentSel = document.getElementById('area-parent-id');
  if (parentSel) {
    parentSel.innerHTML = '<option value="">-- Ninguna (Nivel Superior Principal) --</option>' + 
      AppState.areasList.filter(x => x.id !== areaId).map(x => 
        `<option value="${x.id}" ${x.id === a.parent_id ? 'selected' : ''}>${escapeHtml(x.nombre)}</option>`
      ).join('');
  }

  abrirModal('modal-area');
}

async function guardarAreaOrganigrama(e) {
  e.preventDefault();
  const id = document.getElementById('area-id').value;
  const nombre = document.getElementById('area-nombre').value.trim();
  const codigo = document.getElementById('area-codigo').value.trim();
  const nivel = parseInt(document.getElementById('area-nivel').value);
  const parentIdVal = document.getElementById('area-parent-id').value;
  const parent_id = parentIdVal ? parseInt(parentIdVal) : null;
  const responsable = document.getElementById('area-responsable').value.trim();
  const descripcion = document.getElementById('area-descripcion').value.trim();

  const isEdit = !!id;
  const url = isEdit ? `${API_BASE}/api/areas/${id}` : `${API_BASE}/api/areas`;
  const method = isEdit ? 'PUT' : 'POST';

  try {
    const res = await apiFetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nombre, codigo, nivel, parent_id, responsable, descripcion })
    });

    if (res.ok) {
      alert(isEdit ? "✅ Unidad organizativa actualizada." : "✅ Nueva unidad organizativa agregada correctamente.");
      cerrarModal('modal-area');
      await loadAreas();
      await cargarCatalogosUI();
      loadOrganigrama();
    } else {
      const err = await res.json();
      alert("Error: " + (err.detail || "Verifique los datos ingresados"));
    }
  } catch (err) {
    alert("Error de conexión: " + err.message);
  }
}

async function eliminarAreaUI(areaId) {
  if (!confirm("¿Está seguro de eliminar esta unidad organizativa? El personal asignado quedará temporalmente 'Sin Área'.")) return;
  try {
    const res = await apiFetch(`${API_BASE}/api/areas/${areaId}`, { method: 'DELETE' });
    if (res.ok) {
      alert("✅ Unidad organizativa eliminada.");
      await loadAreas();
      await cargarCatalogosUI();
      loadOrganigrama();
    } else {
      alert("Error al eliminar el área.");
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// ==========================================
// CLOUDFLARE TUNNEL (Token Oficial Permanente & Quick Tunnel)
// ==========================================
function limpiarTokenCloudflare(texto) {
  if (!texto) return '';
  texto = texto.trim().replace(/^["']|["']$/g, '');
  
  // 1. Si contiene "service install <TOKEN>", descartar el comando previo
  if (/service\s+install\s+/i.test(texto)) {
    const partes = texto.split(/service\s+install\s+/i);
    return partes[partes.length - 1].trim().replace(/^["']|["']$/g, '');
  }
  
  // 2. Si contiene "--token <TOKEN>", descartar el prefijo
  if (/--token\s+/i.test(texto)) {
    const partes = texto.split(/--token\s+/i);
    return partes[partes.length - 1].trim().replace(/^["']|["']$/g, '');
  }
  
  // 3. Si empieza con cloudflared... <TOKEN>
  if (/^cloudflared(?:\.exe)?\s+/i.test(texto)) {
    const partes = texto.split(/\s+/);
    return partes[partes.length - 1].trim().replace(/^["']|["']$/g, '');
  }
  
  // 4. Si es el token directo, retornar tal cual
  return texto;
}

// ==========================================
// ACCESO REMOTO - CLOUDFLARE QUICK TUNNEL
// ==========================================
async function cargarConfiguracionTunelRapidoUI() {
  try {
    const res = await apiFetch(`${API_BASE}/api/sistema/tunel-rapido-config`);
    const data = await res.json();
    
    const chkAutostart = document.getElementById('chk-cf-quick-autostart');
    const badgeHeader = document.getElementById('cf-status-badge-header');
    const btnIniciar = document.getElementById('btn-iniciar-tunel-cf');
    const btnDetener = document.getElementById('btn-detener-tunel-cf');
    const resultBox = document.getElementById('cf-tunnel-result');
    const urlLink = document.getElementById('cf-tunnel-url-link');

    if (chkAutostart) chkAutostart.checked = !!data.autostart;
    const labelAutostart = document.getElementById('label-cf-autostart-text');
    if (labelAutostart) {
      labelAutostart.innerText = data.autostart ? '● Activo' : 'Inactivo';
      labelAutostart.style.color = data.autostart ? 'var(--success)' : 'var(--text-muted)';
    }

    if (data.activo && data.url) {
      if (badgeHeader) {
        badgeHeader.innerText = "● Conectado (En línea)";
        badgeHeader.style.background = "var(--success-bg)";
        badgeHeader.style.color = "var(--success)";
      }
      if (btnIniciar) btnIniciar.style.display = "none";
      if (btnDetener) btnDetener.style.display = "inline-flex";
      if (resultBox && urlLink) {
        resultBox.style.display = "block";
        urlLink.href = data.url;
        urlLink.innerText = data.url;
      }
    } else {
      if (badgeHeader) {
        badgeHeader.innerText = "○ Inactivo";
        badgeHeader.style.background = "#e2e8f0";
        badgeHeader.style.color = "#64748b";
      }
      if (btnIniciar) {
        btnIniciar.style.display = "inline-flex";
        btnIniciar.disabled = false;
        btnIniciar.innerHTML = `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M7 6a7.75 7.75 0 1 0 10 0" /><path d="M12 4l0 8" /></svg><span>Habilitar Enlace Remoto</span>`;
      }
      if (btnDetener) btnDetener.style.display = "none";
      if (resultBox) resultBox.style.display = "none";
    }
  } catch (err) {
    console.warn("Error al cargar configuración de túnel rápido:", err);
  }
}

async function guardarConfiguracionTunelRapidoUI(autostart) {
  const labelAutostart = document.getElementById('label-cf-autostart-text');
  if (labelAutostart) {
    labelAutostart.innerText = autostart ? '● Activo' : 'Inactivo';
    labelAutostart.style.color = autostart ? 'var(--success)' : 'var(--text-muted)';
  }
  try {
    const formData = new FormData();
    formData.append('autostart', autostart);
    await apiFetch(`${API_BASE}/api/sistema/tunel-rapido-config`, { method: 'POST', body: formData });
  } catch (err) {
    console.warn("Error al guardar auto-inicio del túnel rápido:", err);
  }
}

async function iniciarTunelRapidoUI() {
  const btn = document.getElementById('btn-iniciar-tunel-cf');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span>Iniciando Túnel Temporal...</span>`;
  }
  try {
    const res = await apiFetch(`${API_BASE}/api/sistema/tunel-cloudflare/iniciar`, { method: 'POST' });
    if (!res.ok) {
      const errText = await res.text();
      let errMsg = "No se pudo iniciar el túnel de Cloudflare.";
      try {
        const errJson = JSON.parse(errText);
        errMsg = errJson.detail || errMsg;
      } catch (_) {
        if (errText.includes("Internal Server Error")) {
          errMsg = "El servidor encontró un bloqueo al iniciar el túnel de Cloudflare. Por favor intente nuevamente en unos segundos.";
        }
      }
      alert("⚠️ " + errMsg);
      await cargarConfiguracionTunelRapidoUI();
      return;
    }
    const data = await res.json();
    if (data.success && data.url) {
      await cargarConfiguracionTunelRapidoUI();
      await cargarConfiguracionGithubSyncUI();
    } else {
      alert("No se pudo iniciar el enlace remoto: " + (data.detail || "Error desconocido"));
      await cargarConfiguracionTunelRapidoUI();
    }
  } catch (err) {
    alert("Error al iniciar enlace remoto: " + err.message);
    await cargarConfiguracionTunelRapidoUI();
  }
}

async function detenerTunelRapidoUI() {
  try {
    await apiFetch(`${API_BASE}/api/sistema/tunel-cloudflare/detener`, { method: 'POST' });
    await cargarConfiguracionTunelRapidoUI();
  } catch (err) {
    alert("Error al detener enlace: " + err.message);
  }
}

async function copiarEnlaceRemoto() {
  const linkEl = document.getElementById('cf-tunnel-url-link');
  const btn = document.getElementById('btn-copiar-enlace-remoto');
  const url = linkEl ? (linkEl.innerText || linkEl.href || '') : '';
  if (!url || url === '#' || url.trim() === '') {
    alert("No hay ningún enlace activo para copiar.");
    return;
  }

  const aplicarFeedback = () => {
    if (btn) {
      const origHtml = btn.innerHTML;
      btn.innerHTML = '<span>✅ ¡Enlace Copiado!</span>';
      btn.style.background = '#d1fae5';
      btn.style.borderColor = '#10b981';
      btn.style.color = '#065f46';
      setTimeout(() => {
        btn.innerHTML = origHtml;
        btn.style.background = '#ffffff';
        btn.style.borderColor = '#10b981';
        btn.style.color = '#047857';
      }, 2500);
    }
  };

  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(url);
      aplicarFeedback();
    } else {
      throw new Error("Clipboard API directa no disponible");
    }
  } catch (_) {
    // Fallback universal para HTTP / Electron
    const textArea = document.createElement("textarea");
    textArea.value = url;
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    textArea.style.top = "-999999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand('copy');
      aplicarFeedback();
    } catch (e) {
      prompt("Copie el enlace manualmente:", url);
    }
    textArea.remove();
  }
}

function descargarPlantillaExcelEjemplo() {
  window.location.href = `${API_BASE}/api/excel/plantilla-ejemplo`;
}

// Compatibilidad
async function cargarConfiguracionTunelToken() { await cargarConfiguracionTunelRapidoUI(); }
async function guardarConfiguracionTunelTokenUI() {}
async function toggleTunelTokenUI() {}
async function generarTunelCloudflareUI() { await iniciarTunelRapidoUI(); }

// ==========================================
// GESTOR DE GIT Y DEPLOY KEY SSH (100% GUI)
// ==========================================
async function cargarEstadoGitDeployKeyUI() {
  try {
    const res = await apiFetch(`${API_BASE}/api/sistema/git-estado`);
    const data = await res.json();

    const git = data.git || {};
    const key = data.deploy_key || {};

    const badge = document.getElementById('git-deploy-badge');
    const installText = document.getElementById('git-install-text');
    const installIcon = document.getElementById('git-install-icon');
    const btnInstalar = document.getElementById('btn-instalar-git');
    const txtKey = document.getElementById('txt-deploy-key-pub');
    const linkDeployGithub = document.getElementById('btn-abrir-deploy-keys-github');

    // 1. Estado de Git
    if (git.instalado) {
      if (badge) {
        badge.innerText = `● Git Activo (${git.arquitectura || '64-bit'})`;
        badge.style.background = "var(--success-bg)";
        badge.style.color = "var(--success)";
      }
      if (installIcon) installIcon.innerText = "✅";
      if (installText) installText.innerHTML = `<strong>Git detectado en este equipo:</strong> ${escapeHtml(git.version || 'Instalado')} (${git.arquitectura || '64-bit'})`;
      if (btnInstalar) btnInstalar.style.display = "none";
    } else {
      if (badge) {
        badge.innerText = "❌ Git No Instalado";
        badge.style.background = "#fee2e2";
        badge.style.color = "#dc2626";
      }
      if (installIcon) installIcon.innerText = "⚠️";
      if (installText) installText.innerHTML = `<strong>Git no está instalado</strong> en este equipo (${git.arquitectura || '64-bit'}). Presiona el botón para instalarlo automáticamente:`;
      if (btnInstalar) btnInstalar.style.display = "inline-flex";
    }

    // 2. Llave pública
    if (txtKey && key.clave_publica) {
      txtKey.value = key.clave_publica;
    }
    if (linkDeployGithub && key.deploy_url) {
      linkDeployGithub.href = key.deploy_url;
    }
  } catch (err) {
    console.warn("Error al cargar estado de Git/Deploy Key:", err);
  }
}

async function instalarGitAutomaticoUI() {
  const btn = document.getElementById('btn-instalar-git');
  const alertText = document.getElementById('git-install-text');
  if (btn) {
    btn.disabled = true;
    btn.innerText = "⏳ Descargando e instalando Git...";
  }
  if (alertText) {
    alertText.innerText = "Descargando e instalando Git para Windows en segundo plano... por favor espere.";
  }

  try {
    const res = await apiFetch(`${API_BASE}/api/sistema/git-instalar`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      alert("✅ " + data.mensaje);
      await cargarEstadoGitDeployKeyUI();
    } else {
      alert("❌ Error instalando Git: " + (data.error || "Ocurrió un error inesperado"));
    }
  } catch (err) {
    alert("Error de conexión al instalar Git: " + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerText = "📥 Descargar e Instalar Git para Windows";
    }
  }
}

function copiarDeployKeyUI() {
  const txt = document.getElementById('txt-deploy-key-pub');
  const btn = document.getElementById('btn-copiar-deploy-key');
  if (!txt || !txt.value) {
    alert("No hay llave disponible para copiar.");
    return;
  }

  navigator.clipboard.writeText(txt.value).then(() => {
    if (btn) {
      const orig = btn.innerHTML;
      btn.innerHTML = "✅ ¡Llave Copiada!";
      btn.style.background = "var(--success)";
      setTimeout(() => {
        btn.innerHTML = orig;
        btn.style.background = "";
      }, 3000);
    }
  }).catch(() => {
    txt.select();
    document.execCommand('copy');
    alert("¡Llave copiada al portapapeles!");
  });
}

async function probarConexionSSHUI() {
  const feedback = document.getElementById('git-action-feedback');
  if (feedback) {
    feedback.style.display = 'block';
    feedback.style.background = '#e0f2fe';
    feedback.style.color = '#0369a1';
    feedback.innerText = "⏳ Verificando autenticación SSH con GitHub...";
  }

  try {
    const res = await apiFetch(`${API_BASE}/api/sistema/git-probar-conexion`, { method: 'POST' });
    const data = await res.json();

    if (feedback) {
      feedback.style.display = 'block';
      if (data.autenticado) {
        feedback.style.background = 'var(--success-bg)';
        feedback.style.color = 'var(--success)';
        feedback.innerText = "🎉 " + data.mensaje;
      } else {
        feedback.style.background = '#fee2e2';
        feedback.style.color = '#b91c1c';
        feedback.innerText = "⚠️ " + data.mensaje;
      }
    }
  } catch (err) {
    if (feedback) {
      feedback.style.display = 'block';
      feedback.style.background = '#fee2e2';
      feedback.style.color = '#b91c1c';
      feedback.innerText = "Error probando conexión: " + err.message;
    }
  }
}

async function subirProyectoCompletoUI() {
  if (!confirm("¿Desea subir todo el código y la base de datos a la rama 'main' de GitHub ahora mismo?")) return;

  const feedback = document.getElementById('git-action-feedback');
  if (feedback) {
    feedback.style.display = 'block';
    feedback.style.background = '#e0f2fe';
    feedback.style.color = '#0369a1';
    feedback.innerText = "⏳ Preparando archivos y subiendo proyecto a GitHub...";
  }

  try {
    const res = await apiFetch(`${API_BASE}/api/sistema/git-subir-proyecto`, { method: 'POST' });
    const data = await res.json();

    if (feedback) {
      feedback.style.display = 'block';
      if (data.success) {
        feedback.style.background = 'var(--success-bg)';
        feedback.style.color = 'var(--success)';
        feedback.innerText = "✅ " + data.mensaje;
      } else {
        feedback.style.background = '#fee2e2';
        feedback.style.color = '#b91c1c';
        feedback.innerText = "❌ No se pudo subir: " + (data.error || "Asegúrate de haber agregado la Deploy Key con 'Allow write access' en GitHub.");
      }
    }
    await cargarConfiguracionGithubSyncUI();
  } catch (err) {
    if (feedback) {
      feedback.style.display = 'block';
      feedback.style.background = '#fee2e2';
      feedback.style.color = '#b91c1c';
      feedback.innerText = "Error: " + err.message;
    }
  }
}

async function subirPortalWebUI() {
  const feedback = document.getElementById('git-action-feedback');
  if (feedback) {
    feedback.style.display = 'block';
    feedback.style.background = '#e0f2fe';
    feedback.style.color = '#0369a1';
    feedback.innerText = "⏳ Publicando portal de acceso web en la rama 'gh-pages'...";
  }

  try {
    const res = await apiFetch(`${API_BASE}/api/sistema/git-subir-portal`, { method: 'POST' });
    const data = await res.json();

    if (feedback) {
      feedback.style.display = 'block';
      if (data.success) {
        feedback.style.background = 'var(--success-bg)';
        feedback.style.color = 'var(--success)';
        const pUrl = data.pages_url || 'https://ulises47123.github.io/Recursos-H-dricos/';
        feedback.innerHTML = `🎉 <strong>¡Página de acceso actualizada y subida a GitHub!</strong><br><span style="font-size:11.5px;">Los agentes pueden acceder a través de: </span><a href="${pUrl}" target="_blank" style="color:#0369a1; font-weight:bold; text-decoration:underline;">${pUrl}</a>`;
      } else {
        feedback.style.background = '#fee2e2';
        feedback.style.color = '#b91c1c';
        feedback.innerText = "❌ " + (data.error || "Asegúrate de haber agregado la Deploy Key en GitHub.");
      }
    }
    await cargarConfiguracionGithubSyncUI();
  } catch (err) {
    if (feedback) {
      feedback.style.display = 'block';
      feedback.style.background = '#fee2e2';
      feedback.style.color = '#b91c1c';
      feedback.innerText = "Error: " + err.message;
    }
  }
}

// ==========================================
// PUBLICACIÓN WEB / GITHUB PAGES SYNC
// ==========================================
async function cargarConfiguracionGithubSyncUI() {
  try {
    const res = await apiFetch(`${API_BASE}/api/sistema/github-sync-config`);
    const data = await res.json();
    const inputDir = document.getElementById('git-input-repo-dir');
    const inputRemote = document.getElementById('git-input-remote-url');
    const inputBranch = document.getElementById('git-input-branch');
    const pagesLink = document.getElementById('git-pages-url-link');
    const chkEnabled = document.getElementById('chk-git-sync-enabled');
    const badge = document.getElementById('git-status-badge');
    const info = document.getElementById('git-sync-info');

    if (inputDir) inputDir.value = data.repo_dir || '';
    if (inputRemote) inputRemote.value = data.remote_url || 'https://github.com/ulises47123/Recursos-H-dricos.git';
    if (inputBranch) inputBranch.value = data.branch || 'gh-pages';
    if (chkEnabled) chkEnabled.checked = !!data.enabled;

    if (pagesLink && data.pages_url) {
      pagesLink.href = data.pages_url;
      pagesLink.innerText = data.pages_url;
    }

    if (badge) {
      if (data.push_ok) {
        badge.innerText = "● Sincronizado";
        badge.style.background = "var(--success-bg)";
        badge.style.color = "var(--success)";
      } else {
        badge.innerText = "⚠️ Push pendiente";
        badge.style.background = "#fef3c7";
        badge.style.color = "#b45309";
      }
    }

    if (info) {
      const ultima = data.last_sync ? `Última sincronización: ${data.last_sync}` : 'Sin sincronizaciones previas';
      const urlTxt = data.last_url ? `<br>Enlace Cloudflare publicado: <code style="word-break:break-all;">${escapeHtml(data.last_url)}</code>` : '';
      info.innerHTML = `${ultima}${urlTxt}`;
    }
  } catch (err) {
    console.warn("Error al cargar configuración de GitHub Sync:", err);
  }
}

async function guardarConfiguracionGithubSyncUI() {
  const dir = document.getElementById('git-input-repo-dir')?.value.trim() || '';
  const remoteUrl = document.getElementById('git-input-remote-url')?.value.trim() || '';
  const branch = document.getElementById('git-input-branch')?.value.trim() || 'gh-pages';
  const enabled = document.getElementById('chk-git-sync-enabled')?.checked || false;
  const msg = document.getElementById('git-sync-msg');

  const formData = new FormData();
  formData.append('repo_dir', dir);
  formData.append('remote_url', remoteUrl);
  formData.append('branch', branch);
  formData.append('enabled', enabled);

  try {
    const res = await apiFetch(`${API_BASE}/api/sistema/github-sync-config`, { method: 'POST', body: formData });
    const data = await res.json();
    if (data.repo_dir || data.success !== false) {
      if (msg) {
        msg.style.display = 'block';
        msg.style.background = 'var(--success-bg)';
        msg.style.color = 'var(--success)';
        msg.innerText = "✅ Configuración de publicación en GitHub Pages guardada correctamente.";
        setTimeout(() => { msg.style.display = 'none'; }, 3500);
      }
      await cargarConfiguracionGithubSyncUI();
    }
  } catch (err) {
    alert("Error al guardar configuración Git: " + err.message);
  }
}

async function reintentarPushGitUI() {
  const msg = document.getElementById('git-sync-msg');
  if (msg) {
    msg.style.display = 'block';
    msg.style.background = '#e0f2fe';
    msg.style.color = '#0369a1';
    msg.innerText = "⏳ Sincronizando y ejecutando push a GitHub Pages...";
  }

  try {
    const res = await apiFetch(`${API_BASE}/api/sistema/github-sync/reintentar`, { method: 'POST' });
    const data = await res.json();
    if (msg) {
      msg.style.display = 'block';
      if (data.push_exitoso) {
        msg.style.background = 'var(--success-bg)';
        msg.style.color = 'var(--success)';
        msg.innerText = "✅ Push a GitHub Pages completado con éxito. El portal web está actualizado.";
      } else {
        msg.style.background = '#fef3c7';
        msg.style.color = '#b45309';
        msg.innerText = data.mensaje || "⚠️ Intento de push registrado. Si no hay conexión o falta autenticación, el sistema reintentará en segundo plano cada hora.";
      }
      setTimeout(() => { msg.style.display = 'none'; }, 4500);
    }
    await cargarConfiguracionGithubSyncUI();
  } catch (err) {
    alert("Error al reintentar push: " + err.message);
  }
}

// ==========================================
// PUBLICACIÓN AUTOMÁTICA DEL PORTAL (SUBAGENTE 3)
// ==========================================
async function cargarEstadoPublicacionPortalUI() {
  try {
    const resEst = await apiFetch(`${API_BASE}/api/sistema/github/estado`);
    const dataEst = await resEst.json();
    const badge = document.getElementById('portal-status-badge');
    const boxSinSenal = document.getElementById('portal-box-sin-senal');
    const boxConSenal = document.getElementById('portal-box-con-senal');
    const txtLlave = document.getElementById('txt-portal-llave-pub');
    const lblTunnelUrl = document.getElementById('lbl-portal-tunnel-url');
    const lblUltimoSync = document.getElementById('lbl-portal-ultimo-sync');

    if (dataEst.senal_verde) {
      if (badge) {
        badge.innerText = "● Señal Verde Activa";
        badge.style.background = "var(--success-bg)";
        badge.style.color = "var(--success)";
      }
      if (boxSinSenal) boxSinSenal.style.display = "none";
      if (boxConSenal) boxConSenal.style.display = "block";
      if (lblTunnelUrl) lblTunnelUrl.innerText = dataEst.tunnel_url || "Esperando túnel activo...";
      if (lblUltimoSync) lblUltimoSync.innerText = dataEst.ultimo_sync || "Sin sincronizaciones registradas";
    } else {
      if (badge) {
        badge.innerText = "○ Sin Señal Verde";
        badge.style.background = "#fee2e2";
        badge.style.color = "#b91c1c";
      }
      if (boxSinSenal) boxSinSenal.style.display = "block";
      if (boxConSenal) boxConSenal.style.display = "none";

      const resKey = await apiFetch(`${API_BASE}/api/sistema/github/llave-publica`);
      const dataKey = await resKey.json();
      if (txtLlave) txtLlave.value = dataKey.llave_publica || '';
    }
  } catch (err) {
    console.warn("Error al cargar estado de publicación del portal:", err);
  }
}

function copiarLlavePublicaPortalUI() {
  const txt = document.getElementById('txt-portal-llave-pub');
  const btn = document.getElementById('btn-copiar-portal-llave');
  if (!txt || !txt.value) {
    alert("No hay llave pública disponible para copiar.");
    return;
  }

  navigator.clipboard.writeText(txt.value).then(() => {
    if (btn) {
      const orig = btn.innerText;
      btn.innerText = "✅ ¡Copiada!";
      btn.style.background = "var(--success)";
      btn.style.color = "#ffffff";
      setTimeout(() => {
        btn.innerText = orig;
        btn.style.background = "";
        btn.style.color = "";
      }, 3000);
    }
  }).catch(() => {
    txt.select();
    document.execCommand('copy');
    alert("¡Llave copiada al portapapeles!");
  });
}

async function probarConexionPortalUI() {
  const btn = document.getElementById('btn-probar-conexion-portal');
  const msg = document.getElementById('portal-action-msg');
  if (btn) {
    btn.disabled = true;
    btn.innerText = "⏳ Probando conexión SSH...";
  }
  if (msg) {
    msg.style.display = 'block';
    msg.style.background = '#e0f2fe';
    msg.style.color = '#0369a1';
    msg.innerText = "⏳ Verificando autenticación SSH y permisos con GitHub...";
  }

  try {
    const res = await apiFetch(`${API_BASE}/api/sistema/github/probar`, { method: 'POST' });
    const data = await res.json();

    if (msg) {
      msg.style.display = 'block';
      if (data.ok) {
        msg.style.background = 'var(--success-bg)';
        msg.style.color = 'var(--success)';
        msg.innerHTML = "🎉 <strong>Señal verde guardada — reiniciá el sistema</strong><br><span style='font-size:11.5px;'>Conexión SSH y Deploy Key validadas exitosamente.</span>";
        await cargarEstadoPublicacionPortalUI();
      } else {
        msg.style.background = '#fee2e2';
        msg.style.color = '#b91c1c';
        msg.innerText = "❌ Error de conexión: " + (data.mensaje || "Permission denied. Asegúrese de haber agregado la Deploy Key con permisos de escritura.");
      }
    }
  } catch (err) {
    if (msg) {
      msg.style.display = 'block';
      msg.style.background = '#fee2e2';
      msg.style.color = '#b91c1c';
      msg.innerText = "Error probando conexión: " + err.message;
    }
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerText = "Enviar archivo de prueba (logo.png)";
    }
  }
}

async function forzarSincronizacionPortalUI() {
  const btn = document.getElementById('btn-forzar-sync-portal');
  const msg = document.getElementById('portal-action-msg');
  if (btn) {
    btn.disabled = true;
    btn.innerText = "⏳ Sincronizando...";
  }
  if (msg) {
    msg.style.display = 'block';
    msg.style.background = '#e0f2fe';
    msg.style.color = '#0369a1';
    msg.innerText = "⏳ Iniciando túnel Cloudflare y actualizando README.md en gh-pages...";
  }

  try {
    const res = await apiFetch(`${API_BASE}/api/auto-readme/sincronizar`, { method: 'POST' });
    const data = await res.json();

    if (msg) {
      msg.style.display = 'block';
      if (data.success) {
        msg.style.background = 'var(--success-bg)';
        msg.style.color = 'var(--success)';
        msg.innerText = "✅ Sincronización completada con éxito. Enlace Cloudflare publicado en GitHub Pages.";
      } else {
        msg.style.background = '#fef3c7';
        msg.style.color = '#b45309';
        msg.innerText = "⚠️ No se pudo sincronizar: " + (data.mensaje || "Ocurrió un error");
      }
      setTimeout(() => { msg.style.display = 'none'; }, 4500);
    }
    await cargarEstadoPublicacionPortalUI();
  } catch (err) {
    if (msg) {
      msg.style.display = 'block';
      msg.style.background = '#fee2e2';
      msg.style.color = '#b91c1c';
      msg.innerText = "Error de sincronización: " + err.message;
    }
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerText = "Forzar sincronización ahora";
    }
  }
}

// ==========================================
// COPIAS DE SEGURIDAD - GOOGLE DRIVE
// ==========================================
async function cargarConfiguracionGDriveUI() {
  try {
    const res = await apiFetch(`${API_BASE}/api/sistema/gdrive/config`);
    const cfg = await res.json();

    const inputEmail = document.getElementById('gdrive-input-email');
    const inputFolder = document.getElementById('gdrive-input-folder');
    const badge = document.getElementById('gdrive-status-badge');
    const btnConectar = document.getElementById('btn-conectar-gdrive');
    const btnDesconectar = document.getElementById('btn-desconectar-gdrive');
    const info = document.getElementById('gdrive-info');

    if (inputEmail) inputEmail.value = cfg.email || '';
    if (inputFolder) inputFolder.value = cfg.folder_path || '';

    if (cfg.conectado) {
      if (badge) {
        badge.innerText = "● Conectado";
        badge.style.background = "var(--success-bg)";
        badge.style.color = "var(--success)";
      }
      if (btnDesconectar) btnDesconectar.style.display = "inline-flex";
      if (btnConectar) btnConectar.innerText = "Guardar Cambios";
    } else {
      if (badge) {
        badge.innerText = "○ Desconectado";
        badge.style.background = "#e2e8f0";
        badge.style.color = "#64748b";
      }
      if (btnDesconectar) btnDesconectar.style.display = "none";
      if (btnConectar) btnConectar.innerText = "Conectar / Guardar";
    }

    if (info) {
      const ult = cfg.last_backup ? `Última copia automática: ${cfg.last_backup}` : 'Sin copias automáticas previas';
      info.innerText = ult;
    }

    await cargarListaBackupsGDriveUI();
  } catch (err) {
    console.warn("Error al cargar configuración de Google Drive:", err);
  }
}

async function cargarListaBackupsGDriveUI() {
  const tbody = document.getElementById('tbody-gdrive-backups');
  if (!tbody) return;
  try {
    const res = await apiFetch(`${API_BASE}/api/sistema/gdrive/backups`);
    const backups = await res.json();

    if (!Array.isArray(backups) || backups.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center" style="padding:12px; color:var(--text-muted);">No hay copias de seguridad registradas en la carpeta.</td></tr>`;
      return;
    }

    tbody.innerHTML = backups.map(b => {
      const tamKb = Math.round(b.tamano / 1024);
      return `
        <tr>
          <td><strong><code>${escapeHtml(b.nombre)}</code></strong></td>
          <td>${escapeHtml(b.fecha_modificacion)}</td>
          <td><span class="badge badge-info">${tamKb} KB</span></td>
          <td>
            <button class="btn btn-outline btn-sm" onclick="restaurarBackupGDriveUI('${escapeHtml(b.nombre)}')" style="color:var(--primary); display:inline-flex; align-items:center; gap:4px;">
              <svg class="icon-svg" viewBox="0 0 24 24"><path d="M20 11a8.1 8.1 0 0 0 -15.5 -2m-.5 -4v4h4" /><path d="M4 13a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4" /></svg>
              <span>Restaurar</span>
            </button>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-center" style="padding:12px; color:var(--danger);">Error cargando copias.</td></tr>`;
  }
}

async function conectarGDriveUI() {
  const email = document.getElementById('gdrive-input-email')?.value.trim() || '';
  const folder = document.getElementById('gdrive-input-folder')?.value.trim() || '';
  const msg = document.getElementById('gdrive-msg');

  if (!email) {
    alert("Ingrese una dirección de correo de Google Drive.");
    return;
  }

  const formData = new FormData();
  formData.append('email', email);
  formData.append('folder_path', folder);

  try {
    const res = await apiFetch(`${API_BASE}/api/sistema/gdrive/conectar`, { method: 'POST', body: formData });
    const data = await res.json();
    if (data.success) {
      if (msg) {
        msg.style.display = 'block';
        msg.style.background = 'var(--success-bg)';
        msg.style.color = 'var(--success)';
        msg.innerText = "✅ Cuenta y carpeta de Google Drive vinculadas exitosamente.";
        setTimeout(() => { msg.style.display = 'none'; }, 3500);
      }
      await cargarConfiguracionGDriveUI();
    }
  } catch (err) {
    alert("Error al conectar: " + err.message);
  }
}

async function desconectarGDriveUI() {
  if (!confirm("¿Desea desconectar la cuenta de Google Drive para los respaldos automáticos?")) return;
  try {
    await apiFetch(`${API_BASE}/api/sistema/gdrive/desconectar`, { method: 'POST' });
    await cargarConfiguracionGDriveUI();
  } catch (err) {
    alert("Error al desconectar: " + err.message);
  }
}

async function generarBackupGDriveAhoraUI() {
  const msg = document.getElementById('gdrive-msg');
  try {
    const res = await apiFetch(`${API_BASE}/api/sistema/gdrive/backup-ahora`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      if (msg) {
        msg.style.display = 'block';
        msg.style.background = 'var(--success-bg)';
        msg.style.color = 'var(--success)';
        msg.innerText = `✅ Copia creada: ${data.backup_creado} (Total vigentes: ${data.total_backups_vigentes}/3)`;
        setTimeout(() => { msg.style.display = 'none'; }, 4000);
      }
      await cargarConfiguracionGDriveUI();
    }
  } catch (err) {
    alert("Error al generar copia de seguridad: " + err.message);
  }
}

async function restaurarBackupGDriveUI(nombre) {
  if (!confirm(`⚠️ ATENCIÓN: ¿Está seguro que desea restaurar la base de datos a la copia "${nombre}"?\n\nSe realizará un respaldo de seguridad del estado actual antes de proceder.`)) {
    return;
  }
  const formData = new FormData();
  formData.append('backup_nombre', nombre);
  try {
    const res = await apiFetch(`${API_BASE}/api/sistema/gdrive/restaurar`, { method: 'POST', body: formData });
    const data = await res.json();
    if (data.success) {
      alert("✅ Base de datos restaurada correctamente. La aplicación se recargará para reflejar los datos restaurados.");
      window.location.reload();
    } else {
      alert("No se pudo restaurar: " + (data.detail || "Error desconocido"));
    }
  } catch (err) {
    alert("Error al restaurar: " + err.message);
  }
}

// ==========================================
// MODAL DE INFORMACIÓN DEL DESARROLLADOR Y CRÉDITOS
// ==========================================
window.abrirModalInfoDesarrollador = function() {
  abrirModal('modal-info-desarrollador');
};

window.cerrarModalInfoDesarrollador = function() {
  cerrarModal('modal-info-desarrollador');
};


