import os
import sys
import platform
import socket
import datetime
import ipaddress
import subprocess
import urllib.request
import shutil
from pathlib import Path
try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTOGRAPHY = True
except Exception as _e_crypto:
    HAS_CRYPTOGRAPHY = False

CERTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "certs")
BIN_DIR = os.path.join(CERTS_DIR, "bin")

def obtener_ip_lan() -> str:
    """Detecta dinámicamente la IP LAN activa de la máquina."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "192.168.100.38"

def obtener_o_descargar_mkcert() -> str:
    """Obtiene la ruta a mkcert o descarga el binario correspondiente (32-bit o 64-bit)."""
    # 1. Verificar si ya está en el sistema PATH
    which_mkcert = shutil.which("mkcert") or shutil.which("mkcert.exe")
    if which_mkcert:
        return which_mkcert

    # 2. Verificar en certs/bin/mkcert.exe
    os.makedirs(BIN_DIR, exist_ok=True)
    local_mkcert = os.path.join(BIN_DIR, "mkcert.exe")
    if os.path.exists(local_mkcert) and os.path.getsize(local_mkcert) > 10000:
        return local_mkcert

    # 3. Descargar según arquitectura (32-bit x86 vs 64-bit x64)
    is_64bit = sys.maxsize > 2**32 or "64" in platform.machine()
    arch_str = "windows-amd64" if is_64bit else "windows-386"
    url = f"https://github.com/FiloSottile/mkcert/releases/download/v1.4.4/mkcert-v1.4.4-{arch_str}.exe"

    try:
        print(f"[SSL mkcert] Descargando mkcert para Windows ({arch_str})...")
        urllib.request.urlretrieve(url, local_mkcert)
        if os.path.exists(local_mkcert) and os.path.getsize(local_mkcert) > 10000:
            print("[SSL mkcert] Descarga de mkcert completada con éxito.")
            return local_mkcert
    except Exception as e:
        print(f"[SSL mkcert Aviso] No se pudo descargar mkcert automáticamente ({e}). Se usará generador criptográfico nativo.")

    return ""

def generar_con_mkcert(mkcert_bin: str, server_crt_path: str, server_key_path: str, ca_crt_path: str) -> bool:
    """Genera certificados SSL confiables para LAN usando mkcert."""
    try:
        print("[SSL mkcert] Instalando Root CA local en el almacén de Windows...")
        subprocess.run([mkcert_bin, "-install"], capture_output=True, check=False)

        lan_ip = obtener_ip_lan()
        dominios = [
            "recursoshidricos.local",
            "*.recursoshidricos.local",
            "localhost",
            "127.0.0.1",
            "::1",
            "192.168.100.38"
        ]
        if lan_ip not in dominios:
            dominios.append(lan_ip)

        print(f"[SSL mkcert] Generando certificado firmado para LAN: {', '.join(dominios)}...")
        cmd = [
            mkcert_bin,
            "-cert-file", server_crt_path,
            "-key-file", server_key_path
        ] + dominios

        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore", check=False)
        if res.returncode == 0 and os.path.exists(server_crt_path) and os.path.exists(server_key_path):
            # Obtener y copiar la Root CA de mkcert a certs/ca.crt
            res_caroot = subprocess.run([mkcert_bin, "-CAROOT"], capture_output=True, text=True, encoding="utf-8", errors="ignore", check=False)
            if res_caroot.returncode == 0:
                caroot_dir = res_caroot.stdout.strip()
                root_ca_src = os.path.join(caroot_dir, "rootCA.pem")
                if os.path.exists(root_ca_src):
                    shutil.copy2(root_ca_src, ca_crt_path)
            print("[SSL mkcert] Certificados SSL LAN generados e instalados correctamente.")
            return True
    except Exception as e:
        print(f"[SSL mkcert Error] Fallo al ejecutar mkcert: {e}")
    return False

def generar_con_cryptography_fallback(server_crt_path: str, server_key_path: str, ca_crt_path: str, ca_key_path: str):
    """Fallback con librería cryptography nativa en caso de no disponer de mkcert."""
    if not HAS_CRYPTOGRAPHY:
        print("[SSL] Librería cryptography no disponible en este entorno. Omitiendo generación fallback.")
        return False
    # 1. Crear CA si no existe
    if not os.path.exists(ca_key_path) or not os.path.exists(ca_crt_path):
        print("[SSL] Generando Autoridad Certificadora Local (Root CA)...")
        ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        ca_subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "AR"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Jujuy"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Recursos Hidricos CA"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Recursos Hidricos Local Root CA"),
        ])
        ca_cert = (
            x509.CertificateBuilder()
            .subject_name(ca_subject)
            .issuer_name(ca_subject)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
            .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650))
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None), critical=True
            )
            .sign(ca_key, hashes.SHA256())
        )

        with open(ca_key_path, "wb") as f:
            f.write(ca_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        with open(ca_crt_path, "wb") as f:
            f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
    else:
        with open(ca_key_path, "rb") as f:
            ca_key = serialization.load_pem_private_key(f.read(), password=None)
        with open(ca_crt_path, "rb") as f:
            ca_cert = x509.load_pem_x509_certificate(f.read())

    # 2. Generar Certificado de Servidor para recursoshidricos.local
    print("[SSL] Generando Certificado SSL con cryptography...")
    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    
    server_subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "AR"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Jujuy"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Recursos Hidricos"),
        x509.NameAttribute(NameOID.COMMON_NAME, "recursoshidricos.local"),
    ])

    lan_ip = obtener_ip_lan()
    san_list = [
        x509.DNSName("recursoshidricos.local"),
        x509.DNSName("*.recursoshidricos.local"),
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        x509.IPAddress(ipaddress.IPv4Address("192.168.100.38")),
    ]
    try:
        if lan_ip not in ("127.0.0.1", "192.168.100.38"):
            san_list.append(x509.IPAddress(ipaddress.IPv4Address(lan_ip)))
    except Exception:
        pass

    server_cert = (
        x509.CertificateBuilder()
        .subject_name(server_subject)
        .issuer_name(ca_cert.subject)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1825))
        .add_extension(
            x509.SubjectAlternativeName(san_list),
            critical=False,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH, ExtendedKeyUsageOID.CLIENT_AUTH]),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    with open(server_key_path, "wb") as f:
        f.write(server_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    with open(server_crt_path, "wb") as f:
        f.write(server_cert.public_bytes(serialization.Encoding.PEM))

    instalar_ca_en_windows(ca_crt_path)

def ensure_ssl_certificates():
    """Garantiza la existencia e instalación de certificados SSL locales (prioridad mkcert)."""
    os.makedirs(CERTS_DIR, exist_ok=True)
    ca_key_path = os.path.join(CERTS_DIR, "ca.key")
    ca_crt_path = os.path.join(CERTS_DIR, "ca.crt")
    server_key_path = os.path.join(CERTS_DIR, "server.key")
    server_crt_path = os.path.join(CERTS_DIR, "server.crt")

    # Intentar con mkcert primero
    mkcert_bin = obtener_o_descargar_mkcert()
    mkcert_ok = False
    if mkcert_bin:
        mkcert_ok = generar_con_mkcert(mkcert_bin, server_crt_path, server_key_path, ca_crt_path)

    # Si mkcert no pudo o no existen certificados, usar fallback
    if not mkcert_ok and (not os.path.exists(server_key_path) or not os.path.exists(server_crt_path)):
        generar_con_cryptography_fallback(server_crt_path, server_key_path, ca_crt_path, ca_key_path)

    # Configurar archivo hosts
    configurar_hosts_local()

    return server_key_path, server_crt_path, ca_crt_path

def instalar_ca_en_windows(ca_crt_path):
    if os.name == 'nt' and os.path.exists(ca_crt_path):
        try:
            subprocess.run(["certutil", "-addstore", "-f", "ROOT", ca_crt_path], capture_output=True, check=False)
            print("[SSL] Certificado Root CA instalado en el Almacén de Confianza de Windows.")
        except Exception as e:
            print(f"[SSL Aviso] No se pudo registrar certificado automáticamente en Windows: {e}")

def configurar_hosts_local():
    if os.name == 'nt':
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        try:
            if os.path.exists(hosts_path):
                with open(hosts_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                lan_ip = obtener_ip_lan()
                entradas = ["127.0.0.1 recursoshidricos.local", "192.168.100.38 recursoshidricos.local"]
                if lan_ip not in ("127.0.0.1", "192.168.100.38"):
                    entradas.append(f"{lan_ip} recursoshidricos.local")

                nuevas = [e for e in entradas if e not in content]
                
                if nuevas:
                    with open(hosts_path, "a", encoding="utf-8") as f:
                        f.write("\n# Recursos Hidricos Sistema Local\n" + "\n".join(nuevas) + "\n")
                    print("[Hosts] Dominio recursoshidricos.local agregado al archivo hosts.")
        except Exception as e:
            print(f"[Hosts Aviso] No se pudo editar hosts directamente: {e}")

if __name__ == "__main__":
    ensure_ssl_certificates()
