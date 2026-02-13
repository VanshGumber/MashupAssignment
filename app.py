import streamlit as st, os, subprocess, zipfile, smtplib
from yt_dlp import YoutubeDL
from moviepy.video.io.VideoFileClip import VideoFileClip
from email.message import EmailMessage

st.title("Mashup Generator")

singer=st.text_input("Singer name")
n=st.number_input("Number of videos (>10)",min_value=0,step=1)
sec=st.number_input("Seconds per clip (>20)",min_value=0,step=1)
mail=st.text_input("Email")

if st.button("Generate Mashup"):

    if singer.strip()=="":
        st.error("Singer required"); st.stop()
    if n<=10:
        st.error("Videos must be >10"); st.stop()
    if sec<=20:
        st.error("Seconds must be >20"); st.stop()
    if "@" not in mail or "." not in mail:
        st.error("Invalid email"); st.stop()

    try:
        os.makedirs("v",exist_ok=True)
        os.makedirs("a",exist_ok=True)
        os.makedirs("c",exist_ok=True)

        st.write("Downloading videos...")
        y={
            'format':'bestaudio/best',
            'outtmpl':'v/%(id)s.%(ext)s',
            'quiet':True,
            'noplaylist':True,
            'extractor_args':{
                'youtube':{
                    'player_client':['android']
                }
            },
            'http_headers':{
                'User-Agent':'com.google.android.youtube/17.31.35 (Linux; U; Android 11)',
            }
        }

        with YoutubeDL(y) as d:
            r=d.extract_info(f"ytsearch{n}:{singer}",download=True)
            vids=[]
            for e in r['entries']:
                path=f"v/{e['id']}.{e['ext']}"
                if os.path.exists(path):
                    vids.append(path)

        if not vids:
            st.error("No videos downloaded"); st.stop()

        st.write("Extracting audio...")
        auds=[]
        for v in vids:
            a="a/"+os.path.basename(v).rsplit(".",1)[0]+".mp3"
            VideoFileClip(v).audio.write_audiofile(a,verbose=False,logger=None)
            auds.append(a)

        st.write("Trimming...")
        clips=[]
        for a in auds:
            out="c/"+os.path.basename(a)
            subprocess.run([
                "ffmpeg","-y","-i",a,
                "-t",str(sec),
                "-acodec","copy",
                out
            ],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            clips.append(out)

        st.write("Merging...")
        with open("list.txt","w") as f:
            for c in clips:
                f.write(f"file '{os.path.abspath(c)}'\n")

        subprocess.run([
            "ffmpeg","-y",
            "-f","concat",
            "-safe","0",
            "-i","list.txt",
            "-c","copy",
            "out.mp3"
        ],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

        with zipfile.ZipFile("out.zip","w") as z:
            z.write("out.mp3")

        email_from = st.secrets["EMAIL"]
        app_pass = st.secrets["PASSWORD"]

        st.write("Sending email...")
        msg=EmailMessage()
        msg['Subject']="Mashup File"
        msg['From']=email_from
        msg['To']=mail
        msg.set_content("Mashup attached")

        with open("out.zip","rb") as f:
            msg.add_attachment(f.read(),maintype='application',subtype='zip',filename="mashup.zip")

        with smtplib.SMTP('smtp.gmail.com',587) as s:
            s.starttls()
            s.login(email_from,app_pass)
            s.send_message(msg)

        st.success("Mashup sent to email")

    except Exception as e:
        st.error(str(e))
