import numpy as np, subprocess as sp, asyncio, edge_tts, wave
from pathlib import Path
W,H,FPS=720,1280,30
lines=[(0,3,"Esse buraco negro cresceu rápido demais!"),(3,7,"Com uma massa equivalente a 360 milhões de sóis..."),(7,11,"Ele já existia apenas 630 milhões de anos após o Big Bang."),(11,15,"Os cientistas ainda tentam explicar como ele cresceu tão rápido."),(15,18,"E é por isso que...")]
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
music=.10*np.sin(2*np.pi*55*t)+.045*np.sin(2*np.pi*83*t+np.sin(2*np.pi*t/18))+.025*np.sin(2*np.pi*110*t)
with wave.open("music.wav","wb") as f:
    f.setparams((1,2,48000,0,"NONE","not compressed")); f.writeframes((music*32767).astype("<i2").tobytes())
assert all((Path("frames")/f"{i:04d}.png").is_file() for i in range(1,541)), "Missing frames"
run("ffmpeg","-y","-framerate","30","-i","frames/%04d.png","-filter_complex","[0:v]split[base][glow];[glow]gblur=sigma=8[blur];[base][blur]blend=all_mode=screen:all_opacity=0.35","-c:v","libx264","-pix_fmt","yuv420p","silent.mp4")
def stamp(t): return f"0:00:{t:05.2f}"
ass="[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,DejaVu Sans,64,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,5,2,2,100,150,430,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
for a,b,s in lines:
    words=s.split(); groups=[words[j:j+4] for j in range(0,len(words),4)]
    for j,g in enumerate(groups):
        start=a+(b-a)*j/len(groups); end=a+(b-a)*(j+1)/len(groups)
        caption=" ".join(g[:-1])+r" {\c&H00FFFF&}"+g[-1]+r"{\c&HFFFFFF&}"
        ass+=f"Dialogue: 0,{stamp(start)},{stamp(end)},Default,,0,0,0,,{caption}\n"
Path("captions.ass").write_text(ass)
run("ffmpeg","-y","-i","silent.mp4","-i","voice.wav","-i","music.wav","-vf","scale=1080:1920:flags=lanczos,ass=captions.ass","-filter_complex","[1:a][2:a]amix=inputs=2:weights=1 0.6:normalize=0[a]","-map","0:v","-map","[a]","-c:v","libx264","-crf","18","-preset","fast","-c:a","aac","-b:a","192k","-t","18","-movflags","+faststart","buraco-negro-cgi.mp4")
