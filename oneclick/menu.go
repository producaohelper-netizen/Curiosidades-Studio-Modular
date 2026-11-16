package main

import (
 "bufio"
 "fmt"
 "os"
 "path/filepath"
 "strings"
)

// interactiveMode provides a simple keyboard-operated menu for the Windows
// executable. No browser, paid service or additional GUI library is required.
func interactiveMode(base string) error {
 reader:=bufio.NewReader(os.Stdin)
 fmt.Println("\nCURIOSIDADES STUDIO — ESCOLHA O FORMATO")
 fmt.Println("1 — Reels vertical (rascunho para revisão)")
 fmt.Println("2 — Vídeo longo (modo anterior)")
 fmt.Println("0 — Sair")
 fmt.Print("Escolha [1/2/0]: ")
 choice,err:=reader.ReadString('\n')
 if err!=nil{return fmt.Errorf("não foi possível ler a opção: %w",err)}
 switch strings.TrimSpace(choice) {
 case "0": return nil
 case "2": return run(base)
 case "1":
  prompts:=[]string{
   "Arquivo do roteiro JSON",
   "Imagem do gancho",
   "Imagem do contexto",
   "Imagem do desenvolvimento",
   "Imagem da revelação",
  }
  paths:=make([]string,0,len(prompts))
  fmt.Println("Abrindo janelas para selecionar os arquivos do Reel...")
  for index,prompt:=range prompts {
   selected,e:=chooseFile(prompt,index>0)
   if e!=nil {
    fmt.Println("Seletor indisponível ou cancelado:",e)
    fmt.Print(prompt," (digite o caminho ou ENTER para cancelar): ")
    value,readErr:=reader.ReadString('\n')
    if readErr!=nil{return fmt.Errorf("entrada incompleta: %w",readErr)}
    value=strings.Trim(strings.TrimSpace(value),"\"")
    if value=="" {return fmt.Errorf("seleção cancelada: %s",prompt)}
    selected,e=filepath.Abs(value)
    if e!=nil{return e}
   }
   info,e:=os.Stat(selected)
   if e!=nil{return fmt.Errorf("%s: %w",prompt,e)}
   if info.IsDir(){return fmt.Errorf("%s deve ser um arquivo",prompt)}
   paths=append(paths,selected)
  }
  fmt.Println("\nGerando rascunho. Publicação exige revisão humana.")
  return runReelDraft(base,paths[0],paths[1:])
 default: return fmt.Errorf("opção inválida: escolha 1, 2 ou 0")
 }
}
