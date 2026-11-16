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
  for _,prompt:=range prompts {
   fmt.Print(prompt, ": ")
   value,e:=reader.ReadString('\n')
   if e!=nil{return fmt.Errorf("entrada incompleta: %w",e)}
   value=strings.Trim(strings.TrimSpace(value), "\"")
   if value=="" {return fmt.Errorf("%s não informado",prompt)}
   absolute,e:=filepath.Abs(value)
   if e!=nil{return e}
   info,e:=os.Stat(absolute)
   if e!=nil{return fmt.Errorf("%s: %w",prompt,e)}
   if info.IsDir(){return fmt.Errorf("%s deve ser um arquivo",prompt)}
   paths=append(paths,absolute)
  }
  fmt.Println("\nGerando rascunho. Publicação exige revisão humana.")
  return runReelDraft(base,paths[0],paths[1:])
 default: return fmt.Errorf("opção inválida: escolha 1, 2 ou 0")
 }
}
