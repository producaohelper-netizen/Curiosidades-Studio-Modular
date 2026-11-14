#!/usr/bin/env python3
"""Apply the renderer cache fix identically on Linux and Windows."""
from pathlib import Path

source = Path("CuriosidadesStudio_Modular_Fonte/assets/render.py")
code = source.read_text(encoding="utf-8")
if "render_cache_manifest.json" in code:
    print("Cache fix already present.")
    raise SystemExit(0)

updates = [
    (
        "import os,sys,json,math,random,subprocess,argparse,re,wave,struct,time",
        "import os,sys,json,math,random,subprocess,argparse,re,wave,struct,time,hashlib",
    ),
    (
        "    scenes=st['scenes'][:a.limit or None];fps=12;clips=[];subs=[];offset=0\n",
        """    scenes=st['scenes'][:a.limit or None];fps=12;clips=[];subs=[];offset=0
    manifest_path=work/'render_cache_manifest.json'
    try:old_cache=json.loads(manifest_path.read_text(encoding='utf8'))
    except (OSError,ValueError):old_cache={}
    new_cache={}
    for chapter_index,chapter in enumerate(scenes):
        payload=json.dumps({'scene':chapter,'art':st.get('art'),'quality':a.quality,
                            'fps':fps,'renderer':'scene-cache-v2'},sort_keys=True,ensure_ascii=False)
        scene_hash=hashlib.sha256(payload.encode('utf8')).hexdigest()
        new_cache[str(chapter_index)]=scene_hash
        if old_cache.get(str(chapter_index))!=scene_hash:
            for stale in work.glob(f'{chapter_index:02}_*.mp4'):stale.unlink(missing_ok=True)
            (work/f'c_{chapter_index}.mp4').unlink(missing_ok=True)
            old_script_cache=old_cache.get('script_'+str(chapter_index))
            text_hash=hashlib.sha256(chapter.get('script','').encode('utf8')).hexdigest()
            if old_script_cache is not None and old_script_cache!=text_hash:
                (work/f'voz_{chapter_index:02}.wav').unlink(missing_ok=True)
        new_cache['script_'+str(chapter_index)]=hashlib.sha256(chapter.get('script','').encode('utf8')).hexdigest()
    # Cache manifest only written after successful render.
""",
    ),
    (
        "    event(f'Pronto: vídeo com {len(scenes)*4} cenas encenadas, {actual:.0f} segundos',100)",
        """    manifest_path.write_text(json.dumps(new_cache,indent=2),encoding='utf8')
    event(f'Pronto: vídeo com {len(scenes)*4} cenas encenadas, {actual:.0f} segundos',100)""",
    ),
]
for before, after in updates:
    count=code.count(before)
    if count!=1:
        raise SystemExit(f"Unexpected renderer version; anchor occurred {count} times")
    code=code.replace(before,after,1)
source.write_text(code,encoding="utf-8")
compile(code,str(source),"exec")
print("Renderer cache fix applied and syntax checked.")
