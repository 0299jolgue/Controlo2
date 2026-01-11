import discord
from discord.ext import commands
from datetime import datetime

# ============================================
#          CONFIGURAÇÃO - ALTERA AQUI
# ============================================

TOKEN = "COLA_AQUI_O_TOKEN_DO_BOT"
AUTHORIZED_USERS = [123456789012345678]  # Teu ID Discord
COMMAND_CHANNEL_ID = 123456789012345678  # ID do canal #controlo

# ============================================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

def is_authorized(ctx):
    return ctx.author.id in AUTHORIZED_USERS

async def send_cmd(cmd: str, params: str = ""):
    channel = bot.get_channel(COMMAND_CHANNEL_ID)
    if channel:
        await channel.send(f"CMD:{cmd}:{params}:{datetime.now().timestamp()}")

@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")

# ========== COMANDOS ==========

@bot.command()
async def block(ctx):
    if not is_authorized(ctx): return
    await send_cmd("LOCK")
    await ctx.send("🔒 PC **bloqueado**!")

@bot.command()
async def unblock(ctx):
    if not is_authorized(ctx): return
    await send_cmd("UNLOCK")
    await ctx.send("🔓 PC **desbloqueado**!")

@bot.command()
async def shutdown(ctx):
    if not is_authorized(ctx): return
    await send_cmd("SHUTDOWN")
    await ctx.send("⚡ PC a **desligar**...")

@bot.command()
async def restart(ctx):
    if not is_authorized(ctx): return
    await send_cmd("RESTART")
    await ctx.send("🔄 PC a **reiniciar**...")

@bot.command()
async def cancelshutdown(ctx):
    if not is_authorized(ctx): return
    await send_cmd("CANCELSHUTDOWN")
    await ctx.send("✅ Desligamento **cancelado**")

@bot.command(aliases=['ss'])
async def screenshot(ctx):
    if not is_authorized(ctx): return
    await send_cmd("SCREENSHOT", str(ctx.channel.id))
    await ctx.send("📸 A capturar...")

@bot.command(aliases=['ps'])
async def processes(ctx):
    if not is_authorized(ctx): return
    await send_cmd("PROCESSES", str(ctx.channel.id))
    await ctx.send("📋 A obter processos...")

@bot.command()
async def kill(ctx, *, processo: str):
    if not is_authorized(ctx): return
    await send_cmd("KILL", processo)
    await ctx.send(f"💀 A terminar `{processo}`...")

@bot.command()
async def blockapp(ctx, *, app: str):
    if not is_authorized(ctx): return
    await send_cmd("BLOCKAPP", app)
    await ctx.send(f"🚫 App `{app}` **bloqueada**")

@bot.command()
async def unblockapp(ctx, *, app: str):
    if not is_authorized(ctx): return
    await send_cmd("UNBLOCKAPP", app)
    await ctx.send(f"✅ App `{app}` **desbloqueada**")

@bot.command()
async def blockedapps(ctx):
    if not is_authorized(ctx): return
    await send_cmd("BLOCKEDAPPS", str(ctx.channel.id))
    await ctx.send("📋 A obter lista...")

@bot.command()
async def clearblocked(ctx):
    if not is_authorized(ctx): return
    await send_cmd("CLEARBLOCKED")
    await ctx.send("🗑️ Lista **limpa**")

@bot.command()
async def blockgames(ctx):
    if not is_authorized(ctx): return
    await send_cmd("BLOCKGAMES")
    await ctx.send("🎮🚫 **Jogos bloqueados!**")

@bot.command()
async def unblockgames(ctx):
    if not is_authorized(ctx): return
    await send_cmd("UNBLOCKGAMES")
    await ctx.send("🎮✅ **Jogos desbloqueados!**")

@bot.command()
async def blockbrowsers(ctx):
    if not is_authorized(ctx): return
    await send_cmd("BLOCKBROWSERS")
    await ctx.send("🌐🚫 **Browsers bloqueados!**")

@bot.command()
async def unblockbrowsers(ctx):
    if not is_authorized(ctx): return
    await send_cmd("UNBLOCKBROWSERS")
    await ctx.send("🌐✅ **Browsers desbloqueados!**")

@bot.command()
async def studyon(ctx):
    if not is_authorized(ctx): return
    await send_cmd("STUDYMODE", "ON")
    await ctx.send("📚 Modo estudo **ATIVADO**")

@bot.command()
async def studyoff(ctx):
    if not is_authorized(ctx): return
    await send_cmd("STUDYMODE", "OFF")
    await ctx.send("🎮 Modo estudo **DESATIVADO**")

@bot.command()
async def msg(ctx, *, texto: str):
    if not is_authorized(ctx): return
    await send_cmd("MESSAGE", texto)
    await ctx.send(f"💬 Mensagem enviada!")

@bot.command()
async def volume(ctx, nivel: int):
    if not is_authorized(ctx): return
    await send_cmd("VOLUME", str(max(0, min(100, nivel))))
    await ctx.send(f"🔊 Volume: **{nivel}%**")

@bot.command()
async def mute(ctx):
    if not is_authorized(ctx): return
    await send_cmd("MUTE")
    await ctx.send("🔇 **Mutado**")

@bot.command()
async def unmute(ctx):
    if not is_authorized(ctx): return
    await send_cmd("UNMUTE")
    await ctx.send("🔊 **Desmutado**")

@bot.command()
async def status(ctx):
    if not is_authorized(ctx): return
    await send_cmd("STATUS", str(ctx.channel.id))
    await ctx.send("📊 A obter status...")

@bot.command()
async def sysinfo(ctx):
    if not is_authorized(ctx): return
    await send_cmd("SYSINFO", str(ctx.channel.id))
    await ctx.send("💻 A obter info...")

@bot.command()
async def windows(ctx):
    if not is_authorized(ctx): return
    await send_cmd("WINDOWS", str(ctx.channel.id))
    await ctx.send("🪟 A obter janelas...")

@bot.command()
async def uptime(ctx):
    if not is_authorized(ctx): return
    await send_cmd("UPTIME", str(ctx.channel.id))
    await ctx.send("⏱️ A obter uptime...")

@bot.command()
async def screenoff(ctx):
    if not is_authorized(ctx): return
    await send_cmd("SCREENOFF")
    await ctx.send("🖥️ Monitor **desligado**")

@bot.command(name='abrir')
async def openapp(ctx, *, programa: str):
    if not is_authorized(ctx): return
    await send_cmd("OPEN", programa)
    await ctx.send(f"📂 A abrir `{programa}`...")

@bot.command(name='fechar')
async def closeapp(ctx, *, programa: str):
    if not is_authorized(ctx): return
    await send_cmd("CLOSE", programa)
    await ctx.send(f"❌ A fechar `{programa}`...")

@bot.command()
async def openurl(ctx, url: str):
    if not is_authorized(ctx): return
    await send_cmd("OPENURL", url)
    await ctx.send(f"🌐 A abrir `{url}`...")

@bot.command()
async def closebrowser(ctx):
    if not is_authorized(ctx): return
    await send_cmd("CLOSEBROWSER")
    await ctx.send("🌐 Browsers **fechados**")

@bot.command()
async def ping(ctx):
    if not is_authorized(ctx): return
    await send_cmd("PING", str(ctx.channel.id))
    await ctx.send("🏓 A verificar...")

@bot.command()
async def lockpc(ctx, minutos: int):
    if not is_authorized(ctx): return
    await send_cmd("LOCKFOR", str(minutos))
    await ctx.send(f"🔒 PC bloqueado por **{minutos} minutos**")

@bot.command(name='ajuda', aliases=['comandos'])
async def ajuda(ctx):
    if not is_authorized(ctx): return
    
    embed = discord.Embed(title="🛡️ Controlo Parental", color=0x3498db)
    
    embed.add_field(name="🖥️ PC", value="""
`!block` - Bloquear
`!unblock` - Desbloquear
`!shutdown` - Desligar
`!restart` - Reiniciar
`!cancelshutdown` - Cancelar
`!screenoff` - Desligar ecrã
`!lockpc [min]` - Bloquear X min
""", inline=True)
    
    embed.add_field(name="📸 Monitor", value="""
`!screenshot` - Print ecrã
`!processes` - Processos
`!windows` - Janelas
`!status` - Estado
`!sysinfo` - Sistema
`!uptime` - Tempo ligado
`!ping` - Verificar
""", inline=True)
    
    embed.add_field(name="🚫 Apps", value="""
`!blockapp [app]`
`!unblockapp [app]`
`!blockedapps`
`!clearblocked`
`!kill [app]`
""", inline=True)
    
    embed.add_field(name="🎮 Atalhos", value="""
`!blockgames`
`!unblockgames`
`!blockbrowsers`
`!unblockbrowsers`
`!studyon` / `!studyoff`
""", inline=True)
    
    embed.add_field(name="🔊 Som", value="""
`!volume [0-100]`
`!mute`
`!unmute`
""", inline=True)
    
    embed.add_field(name="📦 Outros", value="""
`!msg [texto]`
`!abrir [programa]`
`!fechar [programa]`
`!openurl [url]`
`!closebrowser`
""", inline=True)
    
    await ctx.send(embed=embed)

bot.run(TOKEN)
