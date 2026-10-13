"""
backend/gui_launcher.py
Panel de Control y Lanzador Ligero en Tkinter para el Sistema DPRH.
Reemplaza la aplicación pesada de Electron y permite gestionar el Servidor Web, Red LAN, Túnel Cloudflare, GitHub y Backups.
"""

import os
import sys
import time
import socket
import threading
import webbrowser
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request

# Agregar directorio raíz al PATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.ssl_generator import ensure_ssl_certificates, obtener_ip_lan
from backend.services import auto_readme_sync, gdrive_service, github_sync_service

class ServidorDPRHApp:
    def __init__(self, root, is_background=False):
        self.root = root
        self.is_background = is_background
        self.server_thread = None
        self.tunnel_thread = None
        self.tunnel_proc = None
        self.tunnel_url = None
        self.server_running = True
        
        # Configuración de Ventana
        self.root.title("Gestión de Personal - Servidor Central DPRH")
        self.root.geometry("680x620")
        self.root.minsize(620, 560)
        self.root.configure(bg="#f8fafc")

        # Configurar icono si existe
        logo_ico = os.path.join(ROOT_DIR, "frontend", "img", "favicon.ico")
        logo_png = os.path.join(ROOT_DIR, "frontend", "img", "logo.png")
        if os.path.exists(logo_ico):
            try:
                self.root.iconbitmap(logo_ico)
            except Exception:
                pass

        # Iniciar Servidor FastAPI en segundo plano
        self.iniciar_servidor_uvicorn()

        # Construir Interfaz
        self.crear_estilos()
        self.crear_widgets()

        # Iniciar monitores en segundo plano
        self.actualizar_estado_lan()
        self.actualizar_estado_github()
        self.monitorear_estado_tunel()
        
        # Si se pidió inicio en segundo plano, ocultar ventana
        if self.is_background:
            self.root.withdraw()

        # Manejo de cierre seguro
        self.root.protocol("WM_DELETE_WINDOW", self.on_cerrar_aplicacion)

    def crear_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#f8fafc", borderwidth=0)
        style.configure("TNotebook.Tab", background="#e2e8f0", foreground="#1e293b", padding=[14, 8], font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#0284c7")], foreground=[("selected", "#ffffff")])

    def crear_widgets(self):
        # ── Header ──
        header_frame = tk.Frame(self.root, bg="#0b69a3", height=80)
        header_frame.pack(fill=tk.X, side=tk.TOP)

        lbl_titulo = tk.Label(
            header_frame, 
            text="Dirección Provincial de Recursos Hídricos", 
            font=("Segoe UI", 13, "bold"), 
            fg="#ffffff", 
            bg="#0b69a3"
        )
        lbl_titulo.pack(anchor="w", padx=20, pady=(12, 2))

        lbl_sub = tk.Label(
            header_frame, 
            text="Panel de Administración del Servidor y Control de Red", 
            font=("Segoe UI", 9), 
            fg="#bae6fd", 
            bg="#0b69a3"
        )
        lbl_sub.pack(anchor="w", padx=20, pady=(0, 12))

        # ── Botón Principal: Abrir en Navegador ──
        btn_box = tk.Frame(self.root, bg="#f8fafc")
        btn_box.pack(fill=tk.X, padx=20, pady=(15, 10))

        btn_abrir = tk.Button(
            btn_box,
            text="🌐  ABRIR SISTEMA EN EL NAVEGADOR WEB",
            font=("Segoe UI", 11, "bold"),
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0369a1",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=16,
            pady=10,
            cursor="hand2",
            command=self.abrir_navegador_local
        )
        btn_abrir.pack(fill=tk.X)

        # ── Notebook (Pestañas) ──
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 15))

        # Pestaña 1: Red y Acceso Remoto
        tab_red = tk.Frame(self.notebook, bg="#ffffff", padx=15, pady=15)
        self.notebook.add(tab_red, text="🌐 Red & Acceso Remoto")
        self.crear_tab_red(tab_red)

        # Pestaña 2: GitHub y Portal
        tab_portal = tk.Frame(self.notebook, bg="#ffffff", padx=15, pady=15)
        self.notebook.add(tab_portal, text="🔑 GitHub & Portal")
        self.crear_tab_portal(tab_portal)

        # Pestaña 3: Ajustes & Backups
        tab_ajustes = tk.Frame(self.notebook, bg="#ffffff", padx=15, pady=15)
        self.notebook.add(tab_ajustes, text="⚙️ Ajustes & Backups")
        self.crear_tab_ajustes(tab_ajustes)

        # Pestaña 4: Más Información
        tab_info = tk.Frame(self.notebook, bg="#ffffff", padx=15, pady=15)
        self.notebook.add(tab_info, text="ℹ️ Más Información")
        self.crear_tab_info(tab_info)

        # ── Footer / Barra de Estado ──
        footer = tk.Frame(self.root, bg="#f1f5f9", height=32)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        self.lbl_status = tk.Label(
            footer,
            text="● Servidor Activo (HTTPS Puerto 8000) | 32/64-bit Compatible",
            font=("Segoe UI", 8, "bold"),
            fg="#16a34a",
            bg="#f1f5f9"
        )
        self.lbl_status.pack(side=tk.LEFT, padx=15, pady=6)

    def crear_tab_red(self, parent):
        # Grupo LAN
        lbl_lan_title = tk.Label(parent, text="Direcciones de Conexión Local (LAN):", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#0f172a")
        lbl_lan_title.pack(anchor="w", pady=(0, 4))

        self.txt_lan_info = tk.Label(
            parent,
            text="• Localhost: https://localhost:8000\n• Dominio Oficial: https://recursoshidricos.local:8000\n• IP Red: Detectando...",
            font=("Consolas", 9),
            bg="#f8fafc",
            fg="#334155",
            justify=tk.LEFT,
            relief=tk.SOLID,
            borderwidth=1,
            padx=10,
            pady=8
        )
        self.txt_lan_info.pack(fill=tk.X, pady=(0, 15))

        # Grupo Túnel Remoto
        lbl_tunel_title = tk.Label(parent, text="Acceso Remoto por Internet (Cloudflare):", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#0f172a")
        lbl_tunel_title.pack(anchor="w", pady=(0, 4))

        self.lbl_tunel_status = tk.Label(
            parent,
            text="Estado: Consultando o iniciando túnel seguro...",
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",
            fg="#0284c7"
        )
        self.lbl_tunel_status.pack(anchor="w", pady=(0, 4))

        self.ent_tunel_url = tk.Entry(parent, font=("Consolas", 9), bg="#f8fafc", relief=tk.SOLID, borderwidth=1)
        self.ent_tunel_url.pack(fill=tk.X, pady=(0, 10))

        btn_row = tk.Frame(parent, bg="#ffffff")
        btn_row.pack(fill=tk.X)

        self.btn_iniciar_tunel = tk.Button(
            btn_row,
            text="Iniciar Túnel",
            font=("Segoe UI", 9, "bold"),
            bg="#16a34a",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.accion_iniciar_tunel
        )
        self.btn_iniciar_tunel.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_detener_tunel = tk.Button(
            btn_row,
            text="Detener Túnel",
            font=("Segoe UI", 9, "bold"),
            bg="#dc2626",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.accion_detener_tunel
        )
        self.btn_detener_tunel.pack(side=tk.LEFT, padx=(0, 8))

        btn_copiar_url = tk.Button(
            btn_row,
            text="Copiar URL Remota",
            font=("Segoe UI", 9),
            bg="#e2e8f0",
            fg="#1e293b",
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.copiar_url_remota
        )
        btn_copiar_url.pack(side=tk.LEFT)

    def crear_tab_portal(self, parent):
        # Grupo URL del Repositorio GitHub
        lbl_repo_title = tk.Label(parent, text="URL del Repositorio GitHub:", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#0f172a")
        lbl_repo_title.pack(anchor="w", pady=(0, 2))

        repo_row = tk.Frame(parent, bg="#ffffff")
        repo_row.pack(fill=tk.X, pady=(0, 10))

        self.ent_repo_url = tk.Entry(repo_row, font=("Consolas", 8), bg="#f8fafc", relief=tk.SOLID, borderwidth=1)
        self.ent_repo_url.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        btn_guardar_repo = tk.Button(
            repo_row,
            text="💾 Guardar URL",
            font=("Segoe UI", 8, "bold"),
            bg="#0284c7",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=8,
            pady=3,
            cursor="hand2",
            command=self.guardar_url_repositorio
        )
        btn_guardar_repo.pack(side=tk.RIGHT)

        # Grupo Señal GitHub
        lbl_gh_title = tk.Label(parent, text="Conexión con GitHub y Deploy Key:", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#0f172a")
        lbl_gh_title.pack(anchor="w", pady=(0, 4))

        self.lbl_gh_signal = tk.Label(
            parent,
            text="Estado: Verificando señal de conexión...",
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",
            fg="#64748b"
        )
        self.lbl_gh_signal.pack(anchor="w", pady=(0, 6))

        btn_test_gh = tk.Button(
            parent,
            text="🔍 Probar Conexión con GitHub",
            font=("Segoe UI", 9, "bold"),
            bg="#0284c7",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.probar_conexion_github
        )
        btn_test_gh.pack(anchor="w", pady=(0, 10))

        # Llave Pública SSH
        lbl_key_title = tk.Label(parent, text="Llave Pública SSH (Deploy Key):", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155")
        lbl_key_title.pack(anchor="w", pady=(0, 2))

        self.ent_pub_key = tk.Entry(parent, font=("Consolas", 8), bg="#f8fafc", relief=tk.SOLID, borderwidth=1)
        self.ent_pub_key.pack(fill=tk.X, pady=(0, 6))

        key_btn_row = tk.Frame(parent, bg="#ffffff")
        key_btn_row.pack(fill=tk.X, pady=(0, 12))

        btn_copiar_key = tk.Button(
            key_btn_row,
            text="📋 Copiar Llave Pública",
            font=("Segoe UI", 8, "bold"),
            bg="#e2e8f0",
            fg="#1e293b",
            relief=tk.FLAT,
            padx=8,
            pady=4,
            cursor="hand2",
            command=self.copiar_llave_ssh
        )
        btn_copiar_key.pack(side=tk.LEFT, padx=(0, 6))

        btn_reset_key = tk.Button(
            key_btn_row,
            text="🔄 Restablecer / Generar Nueva Llave",
            font=("Segoe UI", 8, "bold"),
            bg="#f59e0b",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=8,
            pady=4,
            cursor="hand2",
            command=self.resetear_llave_ssh
        )
        btn_reset_key.pack(side=tk.LEFT)

        # Publicación Automática
        lbl_auto_title = tk.Label(parent, text="Publicación Automática del Portal (gh-pages):", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#0f172a")
        lbl_auto_title.pack(anchor="w", pady=(0, 4))

        self.btn_forzar_sync = tk.Button(
            parent,
            text="🚀 Forzar Sincronización Inmediata a GitHub Pages",
            font=("Segoe UI", 9, "bold"),
            bg="#94a3b8",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=10,
            pady=6,
            state=tk.DISABLED,
            cursor="arrow",
            command=self.forzar_sincronizacion_portal
        )
        self.btn_forzar_sync.pack(anchor="w")

    def crear_tab_ajustes(self, parent):
        # Auto-inicio con Windows
        lbl_boot_title = tk.Label(parent, text="Comportamiento del Sistema:", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#0f172a")
        lbl_boot_title.pack(anchor="w", pady=(0, 6))

        self.var_autoboot = tk.BooleanVar(value=self.verificar_autoboot())
        chk_autoboot = tk.Checkbutton(
            parent,
            text="Iniciar automáticamente con Windows en segundo plano (--hidden)",
            variable=self.var_autoboot,
            font=("Segoe UI", 9),
            bg="#ffffff",
            activebackground="#ffffff",
            command=self.cambiar_autoboot
        )
        chk_autoboot.pack(anchor="w", pady=(0, 15))

        # Copias de Seguridad
        lbl_bkp_title = tk.Label(parent, text="Copias de Seguridad (Base de Datos):", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#0f172a")
        lbl_bkp_title.pack(anchor="w", pady=(0, 4))

        lbl_bkp_desc = tk.Label(
            parent,
            text="El sistema guarda automáticamente una copia sincronizada en:\n• Documentos\\Backup\\recursos_hidricos_backup.db\n• backups_gdrive_sync\\ (historial rotativo de 3 copias)",
            font=("Segoe UI", 9),
            bg="#f8fafc",
            fg="#475569",
            justify=tk.LEFT,
            relief=tk.SOLID,
            borderwidth=1,
            padx=10,
            pady=8
        )
        lbl_bkp_desc.pack(fill=tk.X, pady=(0, 10))

        btn_crear_bkp = tk.Button(
            parent,
            text="💾  Crear Copia de Seguridad Ahora",
            font=("Segoe UI", 9, "bold"),
            bg="#0284c7",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.crear_backup_ahora
        )
        btn_crear_bkp.pack(anchor="w")

    def crear_tab_info(self, parent):
        # Crear Canvas con Scrollbar para permitir desplazamiento si el contenido es largo
        canvas = tk.Canvas(parent, bg="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_content = tk.Frame(canvas, bg="#ffffff")

        scroll_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ── Sección 1: Acerca del Proyecto ──
        lbl_info_title = tk.Label(scroll_content, text="ℹ️ Proyecto de Código Abierto", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#0f172a")
        lbl_info_title.pack(anchor="w", pady=(0, 4))

        lbl_info_desc = tk.Label(
            scroll_content,
            text="Este software es un proyecto de código abierto desarrollado para la gestión de personal.\nSi encontrás algún error, querés proponer mejoras o colaborar, podés abrir un issue o enviar un pull request.",
            font=("Segoe UI", 9),
            bg="#f8fafc",
            fg="#334155",
            justify=tk.LEFT,
            relief=tk.SOLID,
            borderwidth=1,
            padx=10,
            pady=8
        )
        lbl_info_desc.pack(fill=tk.X, pady=(0, 12))

        # ── Sección 2: Créditos y Agradecimientos ──
        lbl_cred_title = tk.Label(scroll_content, text="👨‍💻 Créditos y Agradecimientos", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#0f172a")
        lbl_cred_title.pack(anchor="w", pady=(0, 6))

        # Desarrollador Principal
        lbl_dev_title = tk.Label(scroll_content, text="• Desarrollador Principal:", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#0b69a3")
        lbl_dev_title.pack(anchor="w", pady=(0, 2))

        dev_box = tk.Frame(scroll_content, bg="#ffffff")
        dev_box.pack(anchor="w", padx=12, pady=(0, 8))

        lbl_dev_name = tk.Label(dev_box, text="Ulises  |  GitHub: @ulises47123  |  Contacto: cajulian213@gmail.com", font=("Segoe UI", 9), bg="#ffffff", fg="#334155")
        lbl_dev_name.pack(side=tk.LEFT)

        btn_gh_profile = tk.Button(
            dev_box,
            text="🌐 Abrir GitHub",
            font=("Segoe UI", 8, "bold"),
            bg="#24292e",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=6,
            pady=2,
            cursor="hand2",
            command=lambda: webbrowser.open("https://github.com/ulises47123")
        )
        btn_gh_profile.pack(side=tk.LEFT, padx=(8, 0))

        # QA / Pruebas
        lbl_qa_title = tk.Label(scroll_content, text="• Pruebas y Control de Calidad (QA):", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#0b69a3")
        lbl_qa_title.pack(anchor="w", pady=(0, 2))

        lbl_qa_desc = tk.Label(scroll_content, text="   Candela Geronimo – Pruebas de funcionamiento, detección y reporte de errores.", font=("Segoe UI", 9), bg="#ffffff", fg="#334155")
        lbl_qa_desc.pack(anchor="w", pady=(0, 8))

        # Consultores de Datos
        lbl_data_title = tk.Label(scroll_content, text="• Consultores de Datos:", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#0b69a3")
        lbl_data_title.pack(anchor="w", pady=(0, 2))

        lbl_data_desc = tk.Label(scroll_content, text="   Asesoramiento en estructura, validación y gestión de datos.", font=("Segoe UI", 9), bg="#ffffff", fg="#334155")
        lbl_data_desc.pack(anchor="w", pady=(0, 14))

        # ── Sección 3: Apoyo al Proyecto (Cafecito) ──
        lbl_cafecito_title = tk.Label(scroll_content, text="☕ Apoyo al Proyecto", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#0f172a")
        lbl_cafecito_title.pack(anchor="w", pady=(0, 4))

        lbl_cafecito_desc = tk.Label(
            scroll_content,
            text="Si el proyecto te resulta útil y querés colaborar con el desarrollo continuo, podés invitarme un café:",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg="#334155"
        )
        lbl_cafecito_desc.pack(anchor="w", pady=(0, 6))

        btn_cafecito = tk.Button(
            scroll_content,
            text="☕ Invitame un café en cafecito.app (ulisesjc)",
            font=("Segoe UI", 10, "bold"),
            bg="#d97706",
            fg="#ffffff",
            activebackground="#b45309",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=14,
            pady=8,
            cursor="hand2",
            command=lambda: webbrowser.open("https://cafecito.app/ulisesjc")
        )
        btn_cafecito.pack(anchor="w", pady=(0, 10))

    def iniciar_servidor_uvicorn(self):
        def _run():
            try:
                import uvicorn
                key_path, crt_path, _ = ensure_ssl_certificates()
                uvicorn.run(
                    "backend.main:app",
                    host="0.0.0.0",
                    port=8000,
                    ssl_keyfile=key_path,
                    ssl_certfile=crt_path,
                    reload=False,
                    log_level="warning"
                )
            except Exception as e:
                print(f"[Error Uvicorn] {e}")

        self.server_thread = threading.Thread(target=_run, daemon=True, name="FastAPIServerThread")
        self.server_thread.start()

    def actualizar_estado_lan(self):
        lan_ip = obtener_ip_lan()
        texto = f"• Localhost: https://localhost:8000\n• Dominio Oficial LAN: https://recursoshidricos.local:8000\n• IP Local Directa: https://{lan_ip}:8000"
        self.txt_lan_info.config(text=texto)

    def monitorear_estado_tunel(self):
        """Monitorea periódicamente si el túnel Cloudflare o la URL están activos y actualiza los campos de la interfaz."""
        try:
            url_actual = auto_readme_sync._tunnel_url_actual
            if url_actual:
                if self.ent_tunel_url.get().strip() != url_actual:
                    self.ent_tunel_url.delete(0, tk.END)
                    self.ent_tunel_url.insert(0, url_actual)
                self.lbl_tunel_status.config(text="● Túnel Activo en Internet", fg="#16a34a")
            else:
                if not self.ent_tunel_url.get().strip():
                    self.lbl_tunel_status.config(text="○ Túnel Inactivo / Presione 'Iniciar Túnel'", fg="#64748b")
        except Exception:
            pass

        # Repetir la verificación cada 3 segundos en el bucle principal de Tkinter
        self.root.after(3000, self.monitorear_estado_tunel)

    def actualizar_estado_github(self):
        try:
            from backend.services import git_manager_service
            # Cargar URL actual del repositorio
            repo_url = git_manager_service.obtener_repo_url()
            self.ent_repo_url.delete(0, tk.END)
            self.ent_repo_url.insert(0, repo_url)

            # Cargar llave pública
            pub_key = auto_readme_sync.obtener_llave_publica()
            self.ent_pub_key.delete(0, tk.END)
            self.ent_pub_key.insert(0, pub_key)

            if auto_readme_sync.tiene_senal_verde():
                self.lbl_gh_signal.config(text="● Señal Verde: Conexión establecida con éxito.", fg="#16a34a")
                self.btn_forzar_sync.config(state=tk.NORMAL, bg="#0b69a3", cursor="hand2")
            else:
                self.lbl_gh_signal.config(text="○ Sin Señal: Agregue la llave SSH como Deploy Key en GitHub.", fg="#dc2626")
                self.btn_forzar_sync.config(state=tk.DISABLED, bg="#94a3b8", cursor="arrow")
        except Exception:
            pass

    def guardar_url_repositorio(self):
        url = self.ent_repo_url.get().strip()
        from backend.services import git_manager_service
        res = git_manager_service.guardar_repo_url(url)
        if res.get("success"):
            self.actualizar_estado_github()
            messagebox.showinfo("Repositorio Guardado", "URL del repositorio actualizada correctamente.\n\nPor favor presione 'Probar Conexión con GitHub' para validar la nueva URL.")
        else:
            messagebox.showerror("Error", res.get("error", "No se pudo guardar la URL del repositorio."))

    def abrir_navegador_local(self):
        webbrowser.open("https://recursoshidricos.local:8000")

    def accion_iniciar_tunel(self):
        def _iniciar():
            self.lbl_tunel_status.config(text="Iniciando túnel Cloudflare...", fg="#0284c7")
            try:
                url = auto_readme_sync.iniciar_tunel_cloudflare()
                self.tunnel_url = url
                self.ent_tunel_url.delete(0, tk.END)
                self.ent_tunel_url.insert(0, url)
                self.lbl_tunel_status.config(text=f"● Túnel Activo en Internet", fg="#16a34a")
            except Exception as e:
                self.lbl_tunel_status.config(text=f"Error al iniciar túnel: {e}", fg="#dc2626")

        threading.Thread(target=_iniciar, daemon=True).start()

    def accion_detener_tunel(self):
        auto_readme_sync.marcar_servidor_apagado()
        self.ent_tunel_url.delete(0, tk.END)
        self.lbl_tunel_status.config(text="○ Túnel Detenido / Fuera de Línea", fg="#dc2626")

    def copiar_url_remota(self):
        url = self.ent_tunel_url.get().strip()
        if url:
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            messagebox.showinfo("Copiado", "Enlace público copiado al portapapeles.")

    def copiar_llave_ssh(self):
        key = self.ent_pub_key.get().strip()
        if key:
            self.root.clipboard_clear()
            self.root.clipboard_append(key)
            messagebox.showinfo("Copiado Exitoso", "La llave pública SSH ha sido copiada al portapapeles.")

    def resetear_llave_ssh(self):
        if messagebox.askyesno("Confirmar Restablecimiento", "¿Está seguro de que desea generar una nueva llave SSH?\n\nAl restablecerla, deberá copiar la nueva llave pública y actualizarla en GitHub (Deploy Keys) para mantener la sincronización activa."):
            try:
                from backend.services import git_manager_service
                res = git_manager_service.resetear_deploy_key()
                if res.get("success"):
                    nueva_key = res.get("clave_publica", "")
                    self.ent_pub_key.delete(0, tk.END)
                    self.ent_pub_key.insert(0, nueva_key)
                    self.actualizar_estado_github()
                    messagebox.showinfo(
                        "Llave SSH Restablecida",
                        "Se ha generado exitosamente una nueva llave Deploy Key (ed25519).\n\nPor favor copie la nueva llave pública y agréguela a GitHub."
                    )
                else:
                    messagebox.showerror("Error al Restablecer", f"No se pudo generar la nueva llave: {res.get('error')}")
            except Exception as e:
                messagebox.showerror("Error de Llave", f"Ocurrió un error al restablecer la llave: {e}")

    def probar_conexion_github(self):
        def _probar():
            res = auto_readme_sync.probar_conexion()
            self.actualizar_estado_github()
            if res.get("autenticado") or res.get("success"):
                messagebox.showinfo("GitHub OK", "¡Conexión SSH autorizada y activa con GitHub!")
            else:
                messagebox.showwarning("Sin Señal", f"No se pudo autenticar con GitHub.\nPor favor copie la llave pública y agréguela como Deploy Key con permiso de escritura.")

        threading.Thread(target=_probar, daemon=True).start()

    def forzar_sincronizacion_portal(self):
        def _sync():
            res = auto_readme_sync.sincronizacion_automatica()
            if res.get("success"):
                messagebox.showinfo("Sincronización Exitosa", f"Portal web actualizado correctamente en GitHub Pages.\nURL Túnel: {res.get('tunnel_url')}")
            else:
                messagebox.showwarning("Aviso", f"No se pudo sincronizar: {res.get('mensaje')}")

        threading.Thread(target=_sync, daemon=True).start()

    def verificar_autoboot(self) -> bool:
        if os.name != 'nt':
            return False
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, "RecursosHidricosDPRH")
            winreg.CloseKey(key)
            return bool(val)
        except Exception:
            return False

    def cambiar_autoboot(self):
        if os.name != 'nt':
            return
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if self.var_autoboot.get():
                py_exe = sys.executable
                script_path = os.path.abspath(__file__)
                cmd = f'"{py_exe}" "{script_path}" --hidden'
                winreg.SetValueEx(key, "RecursosHidricosDPRH", 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, "RecursosHidricosDPRH")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cambiar inicio con Windows: {e}")

    def crear_backup_ahora(self):
        try:
            res = gdrive_service.realizar_backup_gdrive(usuario="PanelTkinter")
            docs_dir = gdrive_service.obtener_directorio_documentos_backup()
            messagebox.showinfo(
                "Copia de Seguridad Creada",
                f"Respaldo generado exitosamente:\n\n• Archivo: {res.get('backup_creado')}\n• Copia Sincronizada en: {docs_dir}"
            )
        except Exception as e:
            messagebox.showerror("Error Backup", f"No se pudo generar la copia de seguridad: {e}")

    def on_cerrar_aplicacion(self):
        if messagebox.askokcancel("Salir", "¿Desea cerrar el Servidor Central DPRH?\n(El sistema dejará de estar disponible en red e internet)"):
            try:
                auto_readme_sync.marcar_servidor_apagado()
            except Exception:
                pass
            self.root.destroy()
            sys.exit(0)

def main():
    is_bg = "--hidden" in sys.argv or "--background" in sys.argv
    root = tk.Tk()
    app = ServidorDPRHApp(root, is_background=is_bg)
    root.mainloop()

if __name__ == "__main__":
    main()
