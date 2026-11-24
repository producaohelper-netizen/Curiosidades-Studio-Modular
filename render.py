import numpy as np, subprocess as sp, asyncio, edge_tts, wave
from pathlib import Path
W,H,FPS=540,960,30
lines=[(0,3,"Você sabe o que existe dentro de um buraco negro?"),(3,7,"Depois do horizonte de eventos, nem a luz consegue escapar."),(7,12,"Lá dentro, o espaço e o tempo se deformam de maneira extrema."),(12,16,"Mas ninguém sabe exatamente o que existe no centro."),(16,18,"E é por isso que...")]
def run(*a): sp.run(a,check=True)
async def voice():
    for i,(a,b,s) in enumerate(lines):
        await edge_tts.Communicate(s,"pt-BR-AntonioNeural",rate="+20%",pitch="-8Hz").save(f"v{i}.mp3")
        d=float(sp.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f"v{i}.mp3"]))
        run("ffmpeg","-y","-i",f"v{i}.mp3","-af",f"atempo={max(1,d/(b-a-.08))},apad","-t",str(b-a),"-ar","48000","-ac","1",f"v{i}.wav")
asyncio.run(voice())
Path("concat.txt").write_text("\n".join(f"file 'v{i}.wav'" for i in range(5)))
run("ffmpeg","-y","-f","concat","-safe","0","-i","concat.txt","voice.wav")
t=np.arange(18*48000)/48000
music=.10*np.sin(2*np.pi*55*t)+.045*np.sin(2*np.pi*82.5*t+np.sin(2*np.pi*t/18))+.025*np.sin(2*np.pi*110*t)
with wave.open("music.wav","wb") as f:
    f.setparams((1,2,48000,0,"NONE","not compressed")); f.writeframes((music*32767).astype("<i2").tobytes())
y,x=np.mgrid[-1:1:complex(H),-W/H:W/H:complex(W)].astype(np.float32)
rng=np.random.default_rng(42)
stars=np.zeros((H,W),np.float32)
for _ in range(1700):
    j,k=rng.integers(0,H),rng.integers(0,W); stars[j,k]=rng.uniform(.1,1)
from scipy.ndimage import gaussian_filter,map_coordinates
stars=stars+gaussian_filter(stars,1)*2
p=sp.Popen(["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r","30","-i","-","-c:v","libx264","-preset","fast","-pix_fmt","yuv420p","silent.mp4"],stdin=sp.PIPE)
for i in range(540):
    t=i/30; phase=2*np.pi*t/18
    zoom=1+4.5*(1-np.cos(phase))/2
    X=x*zoom; Y=y*zoom
    # Continuous cyclic camera trajectory; artistic, not a physical interior simulation.
    radius=.22
    r=np.sqrt(X*X+Y*Y)+.0001
    theta=np.arctan2(Y,X)
    bend=.025/(r*r+.018)
    u=(X*(1+bend)/zoom/(W/H)+1)*(W-1)/2
    v=(Y*(1+bend)/zoom+1)*(H-1)/2
    bg=map_coordinates(stars,[v,u],order=1,mode="wrap")*.65
    diskR=np.sqrt(X*X+(Y/.23)**2)
    noise=.62+.18*np.sin(35*diskR-8*theta+phase*3)+.12*np.sin(87*diskR+13*theta-phase*5)+.08*np.cos(151*diskR-21*theta+phase*7)
    disk=np.exp(-((diskR-.36)/.16)**2)*noise*(diskR>radius)
    ring=np.exp(-((r-radius)/.013)**2)*(.65+.35*np.cos(theta-phase))
    arc=np.exp(-((r-.29)/.045)**2)*np.exp(-((np.abs(Y)-.23)/.09)**2)*noise
    glow=np.exp(-((r-.27)/.18)**2)*.09
    light=disk*1.4+ring*.8+arc*.65+glow
    mask=np.clip((r-radius)/.012,0,1)
    # Abstract interior: warped luminous filaments, strongest near midpoint.
    inside=np.sin(phase/2)**8
    q=np.sqrt(x*x+y*y)+.003
    spiral=np.exp(-3*q)*(.5+.5*np.cos(18*np.log(q)+5*np.arctan2(y,x)+phase*4))**7
    core=np.exp(-q*q/.002)*inside
    channels=[(bg+light*c)*mask*(1-inside*.8)+inside*(spiral*c*.55+core*.7) for c in (1,.46,.13)]
    img=np.clip(np.stack(channels,-1),0,1)
    p.stdin.write((img**.85*255).astype(np.uint8).tobytes())
p.stdin.close()
assert p.wait()==0
def stamp(t): return f"0:00:{t:05.2f}"
ass="[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,DejaVu Sans,64,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,5,2,2,100,150,430,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
for a,b,s in lines:
    words=s.split(); groups=[words[j:j+4] for j in range(0,len(words),4)]
    for j,g in enumerate(groups):
        start=a+(b-a)*j/len(groups); end=a+(b-a)*(j+1)/len(groups)
        caption=" ".join(g[:-1])+r" {\c&H00FFFF&}"+g[-1]+r"{\c&HFFFFFF&}"
        ass+=f"Dialogue: 0,{stamp(start)},{stamp(end)},Default,,0,0,0,,{caption}\n"
Path("captions.ass").write_text(ass)
run("ffmpeg","-y","-i","silent.mp4","-i","voice.wav","-i","music.wav","-vf","scale=1080:1920:flags=lanczos,ass=captions.ass","-filter_complex","[1:a][2:a]amix=inputs=2:weights=1 0.6:normalize=0[a]","-map","0:v","-map","[a]","-c:v","libx264","-crf","18","-preset","fast","-c:a","aac","-b:a","192k","-t","18","-movflags","+faststart","buraco-negro.mp4")
