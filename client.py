# client.py - Corre no PC do filho
import discord
from discord.ext import commands
import os
import asyncio
import threading
import time
from datetime import datetime
from io import BytesIO

try:
    import psutil
    import pyautogui
except ImportError:
    print("ERRO: Instala as dependências!")
    print("pip install psutil pyautogui pillow")
    exit()

# ============================================
#          CONFIGURAÇÃO - ALTERA AQUI
# ============================================

TOKEN = "MTQ1OTkzNzAwNTU3NTM0MDA1Mw.GlqK3a.QqbhnlZ8iVFwHVYtMv965X_C-GpYF-VC0t07PI"
COMMAND_CHANNEL_ID = 1459936738993635340  # Mesmo ID do canal #controlo

# ============================================

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Estado
class State:
    blocked_apps = []
    study_mode = False
    last_command_time = 0

state = State()

# Lista de jogos
GAMES = [
    "steam.exe", "steamwebhelper.exe", "epicgameslauncher.exe",
    "minecraft.exe", "javaw.exe", "riotclientservices.exe",
    "valorant.exe", "leagueclient.exe", "fortnite.exe",
    "robloxplayerbeta.exe", "origin.exe", "battle.net.exe",
    "uplay.exe", "gog.exe", "bethesda.exe"
]

BROWSERS = [
    "chrome.exe", "firefox.exe", "msedge.exe", 
    "opera.exe", "brave.exe", "vivaldi.exe"
]

STUDY_BLOCKED = GAMES + ["discord.exe", "spotify.exe", "vlc.exe"]

# ============== MONITOR DE APPS ==============

def monitor_apps():
    """Thread que fecha apps bloqueadas"""
    while True:
        try:
            # Juntar todas as apps a bloquear
            to_block = state.blocked_apps.copy()
            
            if state.study_mode:
                to_block.extend(STUDY_BLOCKED)
            
            # Remover duplicados
            to_block = list(set(to_block))
            
            # Verificar processos
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    name = proc.info['name'].lower()
                    if name in [a.lower() for a in to_block]:
                        proc.kill()
                        print(f"[BLOQUEADO] {name}")
                except:
                    pass
        except:
            pass
        
        time.sleep(2)

# ============== FUNÇÕES DE EXECUÇÃO ==============

def execute_lock():
    os.system("rundll32.exe user32.dll,LockWorkStation")

def execute_shutdown():
    os.system('shutdown /s /t 30 /c "Desligado pelos pais"')

def execute_restart():
    os.system('shutdown /r /t 30 /c "Reiniciado pelos pais"')

def execute_cancel_shutdown():
    os.system("shutdown /a")

def execute_kill(process_name):
    killed = 0
    for p in psutil.process_iter(['pid', 'name']):
        try:
            if process_name.lower() in p.info['name'].lower():
                p.kill()
                killed += 1
        except:
            pass
    return killed

def execute_message(text):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, text, "Mensagem dos Pais", 0x40)
    except:
        pass

def execute_volume(level):
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(int(level) / 100, None)
    except:
        pass

def execute_mute(muted=True):
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(1 if muted else 0, None)
    except:
        pass

def execute_screenoff():
    try:
        import ctypes
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)
    except:
        pass

def get_screenshot():
    try:
        img = pyautogui.screenshot()
        img.thumbnail((1280, 720))
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer
    except:
        return None

def get_processes():
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            mem = p.info['memory_info'].rss / 1024 / 1024
            procs.append((p.info['name'], p.info['pid'], mem))
        except:
            pass
    procs.sort(key=lambda x: x[2], reverse=True)
    return procs[:20]

def get_windows():
    try:
        import win32gui
        janelas = []
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                titulo = win32gui.GetWindowText(hwnd)
                if titulo:
                    janelas.append(titulo)
        win32gui.EnumWindows(callback, None)
        return janelas[:20]
    except:
        return []

def get_status():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    return {
        "cpu": cpu,
        "ram": ram,
        "study_mode": state.study_mode,
        "blocked_count": len(state.blocked_apps)
    }

def get_sysinfo():
    import platform
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        "os": f"{platform.system()} {platform.release()}",
        "cpu": psutil.cpu_percent(),
        "ram_used": f"{ram.used/1024**3:.1f}GB",
        "ram_total": f"{ram.total/1024**3:.1f}GB",
        "ram_percent": ram.percent,
        "disk_percent": disk.percent
    }

def get_uptime():
    boot = psutil.boot_time()
    uptime_sec = time.time() - boot
    hours = int(uptime_sec // 3600)
    minutes = int((uptime_sec % 3600) // 60)
    return f"{hours}h {minutes}min"

# ============== CLIENTE DISCORD ==============

@client.event
async def on_ready():
    print("=" * 50)
    print(f"✅ CLIENTE ONLINE")
    print(f"📡 A ouvir canal: {COMMAND_CHANNEL_ID}")
    print("=" * 50)
    
    # Iniciar monitor de apps
    threading.Thread(target=monitor_apps, daemon=True).start()
    print("[MONITOR] A monitorizar apps bloqueadas...")

@client.event
async def on_message(message):
    # Ignorar mensagens próprias
    if message.author == client.user:
        return
    
    # Só processar mensagens do canal de comandos
    if message.channel.id != COMMAND_CHANNEL_ID:
        return
    
    # Verificar se é um comando
    if not message.content.startswith("CMD:"):
        return
    
    # Parsear comando: CMD:COMANDO:PARAMS:TIMESTAMP
    parts = message.content.split(":", 3)
    if len(parts) < 4:
        return
    
    cmd = parts[1]
    params = parts[2]
    timestamp = float(parts[3])
    
    # Ignorar comandos antigos (mais de 30 segundos)
    if time.time() - timestamp > 30:
        return
    
    # Ignorar comandos já processados
    if timestamp <= state.last_command_time:
        return
    
    state.last_command_time = timestamp
    
    print(f"[CMD] {cmd} | {params}")
    
    # ============== EXECUTAR COMANDOS ==============
    
    if cmd == "LOCK":
        execute_lock()
    
    elif cmd == "UNLOCK":
        pass  # Desbloquear é manual
    
    elif cmd == "SHUTDOWN":
        execute_shutdown()
    
    elif cmd == "RESTART":
        execute_restart()
    
    elif cmd == "CANCELSHUTDOWN":
        execute_cancel_shutdown()
    
    elif cmd == "SCREENSHOT":
        channel_id = int(params) if params else None
        buffer = get_screenshot()
        if buffer and channel_id:
            channel = client.get_channel(channel_id)
            if channel:
                file = discord.File(buffer, filename="screenshot.png")
                await channel.send("📸 **Screenshot:**", file=file)
    
    elif cmd == "PROCESSES":
        channel_id = int(params) if params else None
        procs = get_processes()
        if channel_id:
            channel = client.get_channel(channel_id)
            if channel:
                msg = "**📋 Processos (Top 20):**\n```\n"
                for name, pid, mem in procs:
                    msg += f"{name[:25]:25} PID:{pid:6} {mem:6.1f}MB\n"
                msg += "```"
                await channel.send(msg)
    
    elif cmd == "KILL":
        killed = execute_kill(params)
        # Responder no canal de comandos
        await message.channel.send(f"💀 Terminados **{killed}** processos: `{params}`")
    
    elif cmd == "BLOCKAPP":
        app = params.lower()
        if not app.endswith('.exe'):
            app += '.exe'
        if app not in state.blocked_apps:
            state.blocked_apps.append(app)
        await message.channel.send(f"🚫 App bloqueada: `{app}`")
    
    elif cmd == "UNBLOCKAPP":
        app = params.lower()
        if not app.endswith('.exe'):
            app += '.exe'
        if app in state.blocked_apps:
            state.blocked_apps.remove(app)
        await message.channel.send(f"✅ App desbloqueada: `{app}`")
    
    elif cmd == "BLOCKEDAPPS":
        channel_id = int(params) if params else None
        if channel_id:
            channel = client.get_channel(channel_id)
            if channel:
                if state.blocked_apps:
                    apps = "\n".join([f"• {a}" for a in state.blocked_apps])
                    await channel.send(f"**🚫 Apps Bloqueadas:**\n{apps}")
                else:
                    await channel.send("Nenhuma app bloqueada")
    
    elif cmd == "CLEARBLOCKED":
        state.blocked_apps.clear()
        await message.channel.send("🗑️ Lista de bloqueados limpa")
    
    elif cmd == "BLOCKGAMES":
        for g in GAMES:
            if g not in state.blocked_apps:
                state.blocked_apps.append(g)
        await message.channel.send("🎮🚫 Jogos bloqueados!")
    
    elif cmd == "UNBLOCKGAMES":
        for g in GAMES:
            if g in state.blocked_apps:
                state.blocked_apps.remove(g)
        await message.channel.send("🎮✅ Jogos desbloqueados!")
    
    elif cmd == "BLOCKBROWSERS":
        for b in BROWSERS:
            if b not in state.blocked_apps:
                state.blocked_apps.append(b)
        await message.channel.send("🌐🚫 Browsers bloqueados!")
    
    elif cmd == "UNBLOCKBROWSERS":
        for b in BROWSERS:
            if b in state.blocked_apps:
                state.blocked_apps.remove(b)
        await message.channel.send("🌐✅ Browsers desbloqueados!")
    
    elif cmd == "STUDYMODE":
        state.study_mode = (params.upper() == "ON")
        status = "ATIVADO 📚" if state.study_mode else "DESATIVADO 🎮"
        await message.channel.send(f"Modo estudo: **{status}**")
    
    elif cmd == "MESSAGE":
        execute_message(params)
    
    elif cmd == "VOLUME":
        execute_volume(params)
        await message.channel.send(f"🔊 Volume: **{params}%**")
    
    elif cmd == "MUTE":
        execute_mute(True)
        await message.channel.send("🔇 **Mutado**")
    
    elif cmd == "UNMUTE":
        execute_mute(False)
        await message.channel.send("🔊 **Desmutado**")
    
    elif cmd == "STATUS":
        channel_id = int(params) if params else None
        if channel_id:
            channel = client.get_channel(channel_id)
            if channel:
                s = get_status()
                study = "📚 Ativo" if s['study_mode'] else "🎮 Inativo"
                msg = f"""**🖥️ Estado do PC:**

🟢 **Online**
💻 CPU: **{s['cpu']}%**
🧠 RAM: **{s['ram']}%**
📚 Modo Estudo: {study}
🚫 Apps bloqueadas: **{s['blocked_count']}**"""
                await channel.send(msg)
    
    elif cmd == "SYSINFO":
        channel_id = int(params) if params else None
        if channel_id:
            channel = client.get_channel(channel_id)
            if channel:
                info = get_sysinfo()
                msg = f"""**💻 Info do Sistema:**

🖥️ OS: {info['os']}
📊 CPU: **{info['cpu']}%**
🧠 RAM: {info['ram_used']} / {info['ram_total']} (**{info['ram_percent']}%**)
💾 Disco: **{info['disk_percent']}%** usado"""
                await channel.send(msg)
    
    elif cmd == "WINDOWS":
        channel_id = int(params) if params else None
        if channel_id:
            channel = client.get_channel(channel_id)
            if channel:
                janelas = get_windows()
                if janelas:
                    msg = "**🪟 Janelas Abertas:**\n```\n"
                    for j in janelas:
                        msg += f"• {j[:50]}\n"
                    msg += "```"
                    await channel.send(msg)
                else:
                    await channel.send("Nenhuma janela encontrada")
    
    elif cmd == "UPTIME":
        channel_id = int(params) if params else None
        if channel_id:
            channel = client.get_channel(channel_id)
            if channel:
                up = get_uptime()
                await channel.send(f"⏱️ PC ligado há **{up}**")
    
    elif cmd == "SCREENOFF":
        execute_screenoff()
    
    elif cmd == "OPEN":
        try:
            os.startfile(params)
            await message.channel.send(f"✅ A abrir: `{params}`")
        except:
            await message.channel.send(f"❌ Erro ao abrir: `{params}`")
    
    elif cmd == "CLOSE":
        os.system(f"taskkill /f /im {params} 2>nul")
        await message.channel.send(f"❌ A fechar: `{params}`")
    
    elif cmd == "OPENURL":
        import webbrowser
        webbrowser.open(params)
        await message.channel.send(f"🌐 A abrir: `{params}`")
    
    elif cmd == "CLOSEBROWSER":
        for b in BROWSERS:
            os.system(f"taskkill /f /im {b} 2>nul")
        await message.channel.send("🌐 Browsers fechados!")
    
    elif cmd == "PING":
        channel_id = int(params) if params else None
        if channel_id:
            channel = client.get_channel(channel_id)
            if channel:
                await channel.send("🟢 **Cliente online!**")

# Iniciar
print("=" * 50)
print("   CONTROLO PARENTAL - CLIENTE")
print("   A iniciar...")
print("=" * 50)
client.run(TOKEN)
