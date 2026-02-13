import streamlit as st, os, zipfile, smtplib
from yt_dlp import YoutubeDL
from moviepy.video.io.VideoFileClip import VideoFileClip
from pydub import AudioSegment
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

        st.write("Downloading videos...")
        y={'format':'mp4','outtmpl':'v/%(id)s.%(ext)s','quiet':True}
        with YoutubeDL(y) as d:
            r=d.extract_info(f"ytsearch{n}:{singer}",download=True)
            vids=[f"v/{e['id']}.mp4" for e in r['entries']]

        if not vids:
            st.error("No videos found"); st.stop()

        parts=[]
        st.write("Processing audio...")
        for v in vids:
            a=v.replace(".mp4",".mp3")
            VideoFileClip(v).audio.write_audiofile(a,verbose=False,logger=None)
            seg=AudioSegment.from_file(a)[:sec*1000]
            name="c_"+os.path.basename(a)
            seg.export(name,format="mp3")
            parts.append(name)

        st.write("Merging...")
        m=AudioSegment.empty()
        for p in parts: m+=AudioSegment.from_file(p)
        m.export("out.mp3",format="mp3")

        with zipfile.ZipFile("out.zip","w") as z: z.write("out.mp3")

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
