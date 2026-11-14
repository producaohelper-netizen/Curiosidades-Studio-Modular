"""Optional local ComfyUI image generation, based on API-format workflow JSON.

No remote paid endpoint is contacted. Model/ComfyUI installation is separate.
The workflow is supplied by the user and may require checkpoint-specific nodes.
"""
from __future__ import annotations
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from dataclasses import dataclass
import json, time, secrets

class GenerationError(RuntimeError):
    pass

@dataclass(frozen=True)
class GeneratedImage:
    file: str
    prompt: str
    workflow: str
    source: str = "local-comfyui"
    license_note: str = "Rights depend on installed model checkpoint and generated content"

def _base(url):
    normalized=url.rstrip("/")
    if normalized not in ("http://127.0.0.1:8188","http://localhost:8188"):
        raise GenerationError("Somente ComfyUI local em porta 8188 é permitido")
    return normalized

def _json_request(url, method="GET", payload=None, timeout=20):
    if payload is None:
        req=Request(url,headers={"User-Agent":"CuriosidadesStudio/0.1"})
    else:
        req=Request(url,data=json.dumps(payload).encode("utf8"),
                    headers={"Content-Type":"application/json"},method=method)
    with urlopen(req,timeout=timeout) as response:
        return json.load(response)

def prepare_workflow(template_path, prompt, seed):
    p=Path(template_path)
    template=p.read_text(encoding="utf8")
    if "{{PROMPT}}" not in template or "{{SEED}}" not in template:
        raise GenerationError("O workflow API precisa conter {{PROMPT}} e {{SEED}}")
    # JSON-encode prompt inside the JSON string context to prevent injection
    safe_prompt=json.dumps(prompt,ensure_ascii=False)[1:-1]
    template=template.replace("{{PROMPT}}",safe_prompt)
    template=template.replace("{{SEED}}",str(int(seed)))
    try:
        workflow=json.loads(template)
    except json.JSONDecodeError as err:
        raise GenerationError("Workflow API JSON inválido") from err
    if not isinstance(workflow,dict) or not workflow:
        raise GenerationError("Workflow API vazio")
    return workflow

def generate(prompt, template_path, output_path,
             *, server="http://127.0.0.1:8188", timeout_sec=480, seed=None,
             request_json=None, request_bytes=None, interval=2.0):
    """A single image; no silent substitution if ComfyUI cannot render."""
    base=_base(server)
    if not isinstance(prompt,str) or len(prompt.strip())<12:
        raise GenerationError("Prompt visual insuficiente")
    if seed is None: seed=secrets.randbelow(2**31)
    workflow=prepare_workflow(template_path,prompt,seed)
    if request_json is None: request_json=_json_request
    if request_bytes is None:
        def request_bytes(url):
            with urlopen(Request(url,headers={"User-Agent":"CuriosidadesStudio/0.1"}),timeout=40) as response:
                return response.read()
    try:
        response=request_json(base+"/prompt",method="POST",
                              payload={"prompt":workflow,"client_id":"curiosidades-studio"})
        prompt_id=response["prompt_id"]
    except (OSError,KeyError,TypeError) as err:
        raise GenerationError("ComfyUI não aceitou o workflow; verificar servidor e checkpoints") from err
    deadline=time.monotonic()+timeout_sec
    while time.monotonic()<deadline:
        try:
            history=request_json(base+"/history/"+prompt_id)
        except (OSError,ValueError) as err:
            raise GenerationError("Falha consultando resultado de ComfyUI") from err
        if prompt_id in history:
            info=history[prompt_id]
            if info.get("status",{}).get("status_str")=="error":
                raise GenerationError("ComfyUI reportou falha no workflow")
            for node in info.get("outputs",{}).values():
                for img in node.get("images",[]):
                    name=img.get("filename")
                    if not name: continue
                    query=urlencode({"filename":name,"subfolder":img.get("subfolder",""),
                                     "type":img.get("type","output")})
                    data=request_bytes(base+"/view?"+query)
                    if not data or len(data)<32:
                        raise GenerationError("ComfyUI devolveu imagem vazia")
                    target=Path(output_path)
                    target.parent.mkdir(parents=True,exist_ok=True)
                    # Must be a real decoded image; do not save arbitrary server bytes as PNG.
                    from PIL import Image
                    from io import BytesIO
                    try:
                        with Image.open(BytesIO(data)) as im:
                            im.verify()
                        with Image.open(BytesIO(data)) as im:
                            im.convert("RGB").save(target,format="PNG")
                    except Exception as err:
                        raise GenerationError("A saída não é imagem válida") from err
                    return GeneratedImage(str(target),prompt,str(template_path))
            raise GenerationError("ComfyUI terminou mas não retornou imagens")
        time.sleep(max(.1,interval))
    raise GenerationError("Tempo limite aguardando o gerador de imagens local")
