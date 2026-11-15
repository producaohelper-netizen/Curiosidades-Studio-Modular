// Curiosidades Studio: entrypoint único para motor local de produção.
// Não altera Defender, não instala software escondido e não publica vídeos.
package main

import (
 "bufio"
 "encoding/json"
 "fmt"
 "os"
 "os/exec"
 "path/filepath"
 "runtime"
 "strings"
 "time"
)

func pythonCommand() (string, []string, error) {
 if p:=os.Getenv("CSTUDIO_PYTHON");p!="" { return p,nil,nil }
 for _,candidate:=range [][]string{{"py","-3"},{"python"},{"python3"}} {
  p,e:=exec.LookPath(candidate[0]);if e!=nil{continue}
  pre:=candidate[1:]
  args:=append(append([]string{},pre...),"-c","import sys;print(sys.version_info.major)")
  cmd:=exec.Command(p,args...)
  out,e:=cmd.Output()
  if e==nil && strings.TrimSpace(string(out))=="3"{return p,pre,nil}
 }
 return "",nil,fmt.Errorf("Python 3 indisponível; instale Python 3.12 antes de executar")
}

func run(base string)error{
 py,pre,e:=pythonCommand();if e!=nil{return e}
 root:=os.Getenv("CSTUDIO_ROOT")
 if root=="" {
  home,e:=os.UserHomeDir();if e!=nil{return e}
  root=filepath.Join(home,"Videos","CuriosidadesStudio")
 }
 model:=os.Getenv("CSTUDIO_VOICE_MODEL")
 if model==""{
  model=filepath.Join(root,"models","pt_BR-faber-medium.onnx")
 }
 env:=os.Environ()
 env=append(env,"PYTHONUNBUFFERED=1","PYTHONPATH="+base)
 // Prepare free local Python dependencies and voice assets on first run.
 bootargs:=append(append([]string{},pre...),"-u","-m","universal_engine.bootstrap",
  "--workspace",root,"--voice-model",model)
 if llm:=os.Getenv("CSTUDIO_OLLAMA_MODEL");llm!=""{bootargs=append(bootargs,"--ollama-model",llm)}
 boot:=exec.Command(py,bootargs...)
 boot.Dir=base;boot.Env=env
 boot.Stdout=os.Stdout;boot.Stderr=os.Stderr
 fmt.Println("Preparando dependências gratuitas e voz brasileira, se necessário...")
 if err:=boot.Run();err!=nil{return fmt.Errorf("etapa de preparação: %w",err)}
 configPath:=filepath.Join(root,"runtime_configuration.json")
 content,err:=os.ReadFile(configPath)
 if err!=nil{return fmt.Errorf("configuração de runtime ausente: %w",err)}
 var settings struct { Piper string `json:"piper"`; FFmpegBin string `json:"ffmpeg_bin_dir"` }
 if err=json.Unmarshal(content,&settings);err!=nil || settings.Piper=="" {
  return fmt.Errorf("Piper não foi configurado corretamente")
 }
 args:=append([]string{},pre...)
 quality:=os.Getenv("CSTUDIO_QUALITY")
 if quality=="" {quality="1080"}
 if quality!="720" && quality!="1080" {return fmt.Errorf("CSTUDIO_QUALITY invalido: use 720 ou 1080")}
 args=append(args,"-u","-m","universal_engine.production","--workspace",root,
  "--voice-model",model,"--piper",settings.Piper,"--quality",quality)
 if t:=os.Getenv("CSTUDIO_TOPIC");t!=""{args=append(args,"--topic",t)}
 if wf:=os.Getenv("CSTUDIO_COMFY_WORKFLOW");wf!=""{args=append(args,"--comfy-workflow",wf)}
 if wf:=os.Getenv("CSTUDIO_SPRITE_WORKFLOW");wf!=""{args=append(args,"--sprite-workflow",wf)}
 if voice:=os.Getenv("CSTUDIO_PIPER");voice!=""{args=append(args,"--piper",voice)}
 if llm:=os.Getenv("CSTUDIO_OLLAMA_MODEL");llm!=""{args=append(args,"--llm",llm)}
 if settings.FFmpegBin!="" { env=append(env,"PATH="+settings.FFmpegBin+string(os.PathListSeparator)+os.Getenv("PATH")) }
 cmd:=exec.Command(py,args...)
 cmd.Dir=base;cmd.Env=env
 cmd.Stdout=os.Stdout;cmd.Stderr=os.Stderr
 fmt.Println("Curiosidades Studio — gerando vídeo com um clique")
 fmt.Println("Toda geração exige revisão antes de publicação.")
 fmt.Println("Pasta:",root)
 return cmd.Run()
}
func main(){
 exe,e:=os.Executable();if e!=nil{fmt.Fprintln(os.Stderr,e);os.Exit(1)}
 base:=filepath.Dir(exe)
 if len(os.Args)>1 && os.Args[1]=="--verificar-pacote" {
  for _,name:=range []string{"universal_engine/production.py","universal_engine/bootstrap.py","universal_engine/layer_renderer.py","universal_engine/mouth_overlay.py","qa/video_integrity_audit.py"} {
   if _,err:=os.Stat(filepath.Join(base,filepath.FromSlash(name)));err!=nil {
    fmt.Fprintln(os.Stderr,"Pacote incompleto:",name,err);os.Exit(2)
   }
  }
  fmt.Println("Pacote do executavel completo; geracao real ainda nao validada.")
  return
 }
 if e=run(base);e!=nil{
  fmt.Fprintln(os.Stderr,"Produção interrompida:",e)
  fmt.Fprintln(os.Stderr,"Verifique status.json na pasta de trabalho.")
  if runtime.GOOS=="windows" {
   fmt.Println("Pressione ENTER para fechar.")
   bufio.NewReader(os.Stdin).ReadString('\n')
  }
  os.Exit(1)
 }
 fmt.Println("Vídeo montado. A revisão artística ainda é obrigatória.")
 fmt.Println("Encerrado em",time.Now().Format(time.RFC1123))
 if runtime.GOOS=="windows" {
  fmt.Println("Pressione ENTER para fechar.")
  bufio.NewReader(os.Stdin).ReadString('\n')
 }
}
