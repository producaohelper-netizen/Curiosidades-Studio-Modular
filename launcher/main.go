package main

import (
 "bufio"
 "errors"
 "fmt"
 "io"
 "os"
 "os/exec"
 "path/filepath"
 "runtime"
 "strings"
 "time"
)

var stepNames=[]string{"Google Trends","Escolha editorial","Roteiro Ollama","Cenas ilustradas","Narracao Piper","Video final"}
var filenames=[]string{"Google_Trends","Escolher_Tema","Gerar_Roteiro","Gerar_Cenas","Gerar_Audio","Montar_Video"}

func appDir()(string,error){p,e:=os.Executable();if e!=nil{return "",e};return filepath.Dir(p),nil}
func run(base string,index int,log io.Writer)error{
 suffix:="";if runtime.GOOS=="windows"{suffix=".exe"}
 target:=filepath.Join(base,fmt.Sprintf("0%d_%s%s",index,filenames[index-1],suffix))
 var c *exec.Cmd
 if index==3{
  script:=filepath.Join(base,"03_Gerar_Roteiro_SEGURO.py")
  if _,e:=os.Stat(script);e!=nil{return fmt.Errorf("etapa 03 em Python ausente: %w",e)}
  py:=os.Getenv("CSTUDIO_PYTHON")
  if py==""{if runtime.GOOS=="windows"{py="py"}else{py="python3"}}
  args:=[]string{"-u",script};if py=="py"{args=[]string{"-3","-u",script}}
  c=exec.Command(py,args...)
 }else{
  if _,e:=os.Stat(target);e!=nil{return fmt.Errorf("modulo %02d ausente: %s",index,target)}
  c=exec.Command(target)
 }
 c.Dir=base
 c.Stdout=io.MultiWriter(os.Stdout,log)
 c.Stderr=io.MultiWriter(os.Stderr,log)
 c.Stdin=strings.NewReader("\n")
 if e:=c.Run();e!=nil{return fmt.Errorf("etapa %d (%s): %w",index,stepNames[index-1],e)}
 return nil
}
func execute(base string,log io.Writer)error{
 fmt.Fprintln(log,"Iniciando producao",time.Now().Format(time.RFC3339))
 for i:=1;i<=6;i++{
  start:=time.Now()
  fmt.Printf("\n===== ETAPA %d/6: %s =====\n",i,stepNames[i-1])
  fmt.Fprintf(log,"\n===== ETAPA %d/6: %s =====\n",i,stepNames[i-1])
  if os.Getenv("CSTUDIO_SKIP_TRENDS_TEST")=="1" && i==1{
   fixture:=filepath.Join(base,"PROJETO","01_top5_google_trends.json")
   if _,e:=os.Stat(fixture);e!=nil{return errors.New("fixture de Trends ausente em modo de teste")}
   fmt.Fprintln(log,"AVISO: Google Trends SIMULADO; somente teste")
   continue
  }
  if e:=run(base,i,log);e!=nil{return e}
  fmt.Fprintf(log,"Etapa %d concluida em %s\n",i,time.Since(start).Round(time.Second))
 }
 return nil
}
func main(){
 base,e:=appDir();if e!=nil{fmt.Fprintln(os.Stderr,e);os.Exit(1)}
 project:=filepath.Join(base,"PROJETO");if v:=os.Getenv("CSTUDIO_ROOT");v!=""{project=v}
 if e:=os.MkdirAll(filepath.Join(project,"LOGS"),0755);e!=nil{fmt.Fprintln(os.Stderr,e);os.Exit(1)}
 file,e:=os.Create(filepath.Join(project,"LOGS",time.Now().Format("20060102_150405")+"_executor.log"))
 if e!=nil{fmt.Fprintln(os.Stderr,e);os.Exit(1)}
 defer file.Close()
 e=execute(base,file)
 if e!=nil{
  fmt.Fprintf(os.Stderr,"\nFALHA. Video final nao aprovado: %v\n",e)
  fmt.Fprintf(file,"FALHA: %v\n",e)
  if os.Getenv("CSTUDIO_NO_PAUSE")!="1"{fmt.Println("Pressione ENTER para fechar");bufio.NewReader(os.Stdin).ReadString('\n')}
  os.Exit(1)
 }
 fmt.Println("\nTodas as etapas concluidas; confira o video antes de publicar")
 if os.Getenv("CSTUDIO_NO_PAUSE")!="1"{fmt.Println("Pressione ENTER para fechar");bufio.NewReader(os.Stdin).ReadString('\n')}
}