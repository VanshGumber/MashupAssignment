import sys, os, subprocess
from yt_dlp import YoutubeDL
from moviepy.video.io.VideoFileClip import VideoFileClip

if len(sys.argv)!=5:
    print("Usage: python file.py <Singer> <N> <Seconds> <Output>")
    sys.exit()

singer=sys.argv[1].strip()
if singer=="":
    print("Singer required"); sys.exit()

try: n=int(sys.argv[2])
except: print("N must be integer"); sys.exit()
if n<=10:
    print("N must be > 10"); sys.exit()

try: sec=int(sys.argv[3])
except: print("Duration must be integer"); sys.exit()
if sec<=20:
    print("Duration must be > 20"); sys.exit()

out=sys.argv[4].strip()
if out=="":
    print("Output filename required"); sys.exit()

try:
    os.makedirs("v",exist_ok=True)
    os.makedirs("a",exist_ok=True)
    os.makedirs("c",exist_ok=True)

    print("Downloading videos...")

    y={
        'format':'bestaudio/best',
        'outtmpl':'v/%(id)s.%(ext)s',
        'quiet':True,
        'noplaylist':True,
        'ignoreerrors':True,
        'extractor_args':{
            'youtube':{
                'player_client':['android']
            }
        },
        'http_headers':{
            'User-Agent':'com.google.android.youtube/17.31.35 (Linux; U; Android 11)'
        }
    }

    with YoutubeDL(y) as d:
        r=d.extract_info(f"ytsearch{n*3}:{singer} official audio",download=True)

        vids=[]
        for e in r.get('entries',[]):
            if not e: continue
            path=f"v/{e['id']}.{e['ext']}"
            if os.path.exists(path):
                vids.append(path)
            if len(vids)>=n: break

    if not vids:
        print("No videos downloaded"); sys.exit()

    print("Extracting audio...")
    auds=[]
    for v in vids:
        a="a/"+os.path.basename(v).rsplit(".",1)[0]+".mp3"
        VideoFileClip(v).audio.write_audiofile(a,verbose=False,logger=None)
        auds.append(a)

    print("Trimming...")
    clips=[]
    for a in auds:
        outp="c/"+os.path.basename(a)
        subprocess.run([
            "ffmpeg","-y","-i",a,
            "-t",str(sec),
            "-acodec","copy",
            outp
        ],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        clips.append(outp)

    print("Merging...")
    with open("list.txt","w") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c)}'\n")

    subprocess.run([
        "ffmpeg","-y",
        "-f","concat",
        "-safe","0",
        "-i","list.txt",
        "-c","copy",
        out
    ],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

    print("Mashup created:",out)

except Exception as e:
    print("Error:",e)
