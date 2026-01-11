# bot.py - Corre no PC do pai
import discord
from discord.ext import commands
import asyncio
from datetime import datetime

# ============================================
#          CONFIGURAÇÃO - ALTERA AQUI
# ============================================

TOKEN = "MTQ1OTkzNzAwNTU3NTM0MDA1Mw.GlqK3a.QqbhnlZ8iVFwHVYtMv965X_C-GpYF-VC0t07PI"
AUTHORIZED_USERS = [1456686602112860356]  # Teu ID Discord
COMMAND_CHANNEL_ID = 1459936738993635340  # ID do canal #controlo

# ============================================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def is_authorized(ctx):
    return ctx.author.id in AUTHORIZED_USERS

async def send_command(cmd: str, params: str = ""):
    """Envia comando para o canal que o cliente lê"""
    channel = bot.get_channel(COMMAND_CHANNEL_ID)
    if channel:
        await channel.send(f"CMD:{cmd}:{params}:{datetime.now().timestamp()}")

@bot.event
async def on_ready():
    print("=" * 50)
    print(f"✅ BOT ONLINE: {bot.user}")
    print(f"📡 Canal de comandos: {COMMAND_CHANNEL_ID}")
    print("=" * 50)
    print("\nEscreve !ajuda no Discord para ver comandos\n")

# ================== COMANDOS ==================

# 1. Bloquear PC
@bot.command(name='block')
async def block(ctx):
    if not is_authorized(ctx): return
    await send_command("LOCK")
    await ctx.send("🔒 Comando enviado: **Bloquear PC**")

# 2. Desbloquear
@bot.command(name='unblock')
async def unblock(ctx):
    if not is_authorized(ctx): return
    await send_command("UNLOCK")
    await ctx.send("🔓 Comando enviado: **Desbloquear PC**")

# 3. Desligar PC
@bot.command(name='shutdown')
async def shutdown(ctx):
    if not is_authorized(ctx): return
    await send_command("SHUTDOWN")
    await ctx.send("⚡ Comando enviado: **Desligar PC**")

# 4. Reiniciar PC
@bot.command(name='restart')
async def restart(ctx):
    if not is_authorized(ctx): return
    await send_command("RESTART")
    await ctx.send("🔄 Comando enviado: **Reiniciar PC**")

# 5. Cancelar desligar
@bot.command(name='cancelshutdown')
async def cancelshutdown(ctx):
    if not is_authorized(ctx): return
    await send_command("CANCELSHUTDOWN")
    await ctx.send("✅ Comando enviado: **Cancelar desligamento**")

# 6. Screenshot
@bot.command(name='screenshot', aliases=['ss'])
async def screenshot(ctx):
    if not is_authorized(ctx): return
    await send_command("SCREENSHOT", str(ctx.channel.id))
    await ctx.send("📸 A pedir screenshot...")

# 7. Ver processos
@bot.command(name='processes', aliases=['ps'])
async def processes(ctx):
    if not is_authorized(ctx): return
    await send_command("PROCESSES", str(ctx.channel.id))
    await ctx.send("📋 A pedir lista de processos...")

# 8. Matar processo
@bot.command(name='kill')
async def kill(ctx, *, processo: str):
    if not is_authorized(ctx): return
    await send_command("KILL", processo)
    await ctx.send(f"💀 Comando enviado: **Terminar {processo}**")

# 9. Bloquear app
@bot.command(name='blockapp')
async def blockapp(ctx, *, app: str):
    if not is_authorized(ctx): return
    await send_command("BLOCKAPP", app)
    await ctx.send(f"🚫 Comando enviado: **Bloquear {app}**")

# 10. Desbloquear app
@bot.command(name='unblockapp')
async def unblockapp(ctx, *, app: str):
    if not is_authorized(ctx): return
    await send_command("UNBLOCKAPP", app)
    await ctx.send(f"✅ Comando enviado: **Desbloquear {app}**")

# 11. Ver apps bloqueadas
@bot.command(name='blockedapps')
async def blockedapps(ctx):
    if not is_authorized(ctx): return
    await send_command("BLOCKEDAPPS", str(ctx.channel.id))
    await ctx.send("📋 A pedir lista de apps bloqueadas...")

# 12. Limpar apps bloqueadas
@bot.command(name='clearblocked')
async def clearblocked(ctx):
    if not is_authorized(ctx): return
    await send_command("CLEARBLOCKED")
    await ctx.send("🗑️ Comando enviado: **Limpar lista de bloqueados**")

# 13. Bloquear jogos
@bot.command(name='blockgames')
async def blockgames(ctx):
    if not is_authorized(ctx): return
    await send_command("BLOCKGAMES")
    await ctx.send("🎮🚫 Comando enviado: **Bloquear jogos**")

# 14. Desbloquear jogos
@bot.command(name='unblockgames')
async def unblockgames(ctx):
    if not is_authorized(ctx): return
    await send_command("UNBLOCKGAMES")
    await ctx.send("🎮✅ Comando enviado: **Desbloquear jogos**")

# 15. Bloquear browsers
@bot.command(name='blockbrowsers')
async def blockbrowsers(ctx):
    if not is_authorized(ctx): return
    await send_command("BLOCKBROWSERS")
    await ctx.send("🌐🚫 Comando enviado: **Bloquear browsers**")

# 16. Desbloquear browsers
@bot.command(name='unblockbrowsers')
async def unblockbrowsers(ctx):
    if not is_authorized(ctx): return
    await send_command("UNBLOCKBROWSERS")
    await ctx.send("🌐✅ Comando enviado: **Desbloquear browsers**")

# 17. Modo estudo ON
@bot.command(name='studyon')
async def studyon(ctx):
    if not is_authorized(ctx): return
    await send_command("STUDYMODE", "ON")
    await ctx.send("📚 Comando enviado: **Modo estudo ATIVADO**")

# 18. Modo estudo OFF
@bot.command(name='studyoff')
async def studyoff(ctx):
    if not is_authorized(ctx): return
    await send_command("STUDYMODE", "OFF")
    await ctx.send("🎮 Comando enviado: **Modo estudo DESATIVADO**")

# 19. Enviar mensagem popup
@bot.command(name='msg')
async def msg(ctx, *, texto: str):
    if not is_authorized(ctx): return
    await send_command("MESSAGE", texto)
    await ctx.send(f"💬 Mensagem enviada: **{texto}**")

# 20. Definir volume
@bot.command(name='volume')
async def volume(ctx, nivel: int):
    if not is_authorized(ctx): return
    nivel = max(0, min(100, nivel))
    await send_command("VOLUME", str(nivel))
    await ctx.send(f"🔊 Comando enviado: **Volume {nivel}%**")

# 21. Mutar
@bot.command(name='mute')
async def mute(ctx):
    if not is_authorized(ctx): return
    await send_command("MUTE")
    await ctx.send("🔇 Comando enviado: **Mutar**")

# 22. Desmutar
@bot.command(name='unmute')
async def unmute(ctx):
    if not is_authorized(ctx): return
    await send_command("UNMUTE")
    await ctx.send("🔊 Comando enviado: **Desmutar**")

# 23. Status do PC
@bot.command(name='status')
async def status(ctx):
    if not is_authorized(ctx): return
    await send_command("STATUS", str(ctx.channel.id))
    await ctx.send("📊 A pedir status...")

# 24. Info do sistema
@bot.command(name='sysinfo')
async def sysinfo(ctx):
    if not is_authorized(ctx): return
    await send_command("SYSINFO", str(ctx.channel.id))
    await ctx.send("💻 A pedir informação do sistema...")

# 25. Listar janelas
@bot.command(name='windows')
async def windows(ctx):
    if not is_authorized(ctx): return
    await send_command("WINDOWS", str(ctx.channel.id))
    await ctx.send("🪟 A pedir lista de janelas...")

# 26. Tempo ligado
@bot.command(name='uptime')
async def uptime(ctx):
    if not is_authorized(ctx): return
    await send_command("UPTIME", str(ctx.channel.id))
    await ctx.send("⏱️ A pedir uptime...")

# 27. Desligar monitor
@bot.command(name='screenoff')
async def screenoff(ctx):
    if not is_authorized(ctx): return
    await send_command("SCREENOFF")
    await ctx.send("🖥️ Comando enviado: **Desligar monitor**")

# 28. Abrir programa
@bot.command(name='open')
async def openapp(ctx, *, programa: str):
    if not is_authorized(ctx): return
    await send_command("OPEN", programa)
    await ctx.send(f"📂 Comando enviado: **Abrir {programa}**")

# 29. Fechar programa
@bot.command(name='close')
async def closeapp(ctx, *, programa: str):
    if not is_authorized(ctx): return
    await send_command("CLOSE", programa)
    await ctx.send(f"❌ Comando enviado: **Fechar {programa}**")

# 30. Abrir URL
@bot.command(name='openurl')
async def openurl(ctx, url: str):
    if not is_authorized(ctx): return
    await send_command("OPENURL", url)
    await ctx.send(f"🌐 Comando enviado: **Abrir {url}**")

# 31. Fechar browsers
@bot.command(name='closebrowser')
async def closebrowser(ctx):
    if not is_authorized(ctx): return
    await send_command("CLOSEBROWSER")
    await ctx.send("🌐 Comando enviado: **Fechar browsers**")

# 32. Ping (verificar se cliente está online)
@bot.command(name='ping')
async def ping(ctx):
    if not is_authorized(ctx): return
    await send_command("PING", str(ctx.channel.id))
    await ctx.send("🏓 A verificar conexão...")

# AJUDA
@bot.command(name='ajuda', aliases=['help', 'comandos'])
async def ajuda(ctx):
    if not is_authorized(ctx): return
    
    embed = discord.Embed(title="🛡️ Controlo Parental - Comandos", color=0x3498db)
    
    embed.add_field(name="🖥️ Controlo PC", value="""
`!block` - Bloquear PC
`!unblock` - Desbloquear
`!shutdown` - Desligar
`!restart` - Reiniciar
`!cancelshutdown` - Cancelar
`!screenoff` - Desligar monitor
""", inline=True)
    
    embed.add_field(name="📸 Monitorização", value="""
`!screenshot` - Capturar ecrã
`!processes` - Ver processos
`!windows` - Ver janelas
`!status` - Estado do PC
`!sysinfo` - Info sistema
`!uptime` - Tempo ligado
`!ping` - Verificar conexão
""", inline=True)
    
    embed.add_field(name="🚫 Bloquear Apps", value="""
`!blockapp [nome]` - Bloquear
`!unblockapp [nome]` - Desbloquear
`!blockedapps` - Ver lista
`!clearblocked` - Limpar lista
`!kill [nome]` - Terminar app
""", inline=True)
    
    embed.add_field(name="🎮 Atalhos", value="""
`!blockgames` - Bloquear jogos
`!unblockgames` - Desbloquear
`!blockbrowsers` - Bloquear browsers
`!unblockbrowsers` - Desbloquear
`!studyon` - Modo estudo ON
`!studyoff` - Modo estudo OFF
""", inline=True)
    
    embed.add_field(name="🔊 Som", value="""
`!volume [0-100]` - Volume
`!mute` - Mutar
`!unmute` - Desmutar
""", inline=True)
    
    embed.add_field(name="📦 Outros", value="""
`!msg [texto]` - Enviar popup
`!open [programa]` - Abrir
`!close [programa]` - Fechar
`!openurl [url]` - Abrir URL
`!closebrowser` - Fechar browsers
""", inline=True)
    
    await ctx.send(embed=embed)

# Iniciar
bot.run(TOKEN)
