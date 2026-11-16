package main

import (
 "fmt"
 "os"
 "os/exec"
 "path/filepath"
 "runtime"
 "strings"
)

// chooseFile opens the native Windows file picker. It never executes a path
// supplied by the user as PowerShell code; paths are returned via stdout.
func chooseFile(title string, image bool) (string, error) {
 if runtime.GOOS!="windows" { return "",fmt.Errorf("seletor gráfico disponível apenas no Windows") }
 filter:="Roteiros JSON (*.json)|*.json|Todos os arquivos (*.*)|*.*"
 if image {filter="Imagens (*.png;*.jpg;*.jpeg;*.webp)|*.png;*.jpg;*.jpeg;*.webp|Todos os arquivos (*.*)|*.*"}
 // Constant PowerShell source. Parameters are passed through environment
 // variables, avoiding interpolation/injection in the script.
 script:=`Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = $env:CSTUDIO_PICK_TITLE
$dialog.Filter = $env:CSTUDIO_PICK_FILTER
$dialog.CheckFileExists = $true
$dialog.Multiselect = $false
if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
 [Console]::Out.WriteLine($dialog.FileName)
}`
 cmd:=exec.Command("powershell.exe","-NoProfile","-NonInteractive","-STA","-Command",script)
 cmd.Env=append(os.Environ(),"CSTUDIO_PICK_TITLE="+title,"CSTUDIO_PICK_FILTER="+filter)
 output,err:=cmd.Output()
 if err!=nil{return "",fmt.Errorf("não foi possível abrir seletor de arquivos: %w",err)}
 selected:=strings.TrimSpace(string(output))
 if selected=="" {return "",fmt.Errorf("seleção cancelada")}
 selected,err=filepath.Abs(selected)
 if err!=nil{return "",err}
 info,err:=os.Stat(selected)
 if err!=nil{return "",err}
 if info.IsDir(){return "",fmt.Errorf("selecione um arquivo")}
 return selected,nil
}
