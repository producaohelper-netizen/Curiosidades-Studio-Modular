package main
import (
 "bytes"
 "os"
 "path/filepath"
 "runtime"
 "strings"
 "testing"
)
func stub(t *testing.T,dir string,n int,fail bool){
 t.Helper()
 if n==3{return}
 names:=[]string{"Google_Trends","Escolher_Tema","Gerar_Roteiro","Gerar_Cenas","Gerar_Audio","Montar_Video"}
 name:=filepath.Join(dir,"0"+string(rune('0'+n))+"_"+names[n-1])
 script:="#!/bin/sh\necho "+string(rune('0'+n))+" >> \"$MOCK_COUNTER\"\n"
 if fail{script+="exit 3\n"}
 if e:=os.WriteFile(name,[]byte(script),0755);e!=nil{t.Fatal(e)}
}
func TestOrderAndFailures(t *testing.T){
 if runtime.GOOS=="windows"{t.Skip("Shell stubs tested on Linux runner")}
 for _,stop:=range []int{0,2,5}{
  dir:=t.TempDir();counter:=filepath.Join(dir,"steps.txt")
  t.Setenv("MOCK_COUNTER",counter);t.Setenv("CSTUDIO_PYTHON","python3");t.Setenv("CSTUDIO_SKIP_TRENDS_TEST","")
  for n:=1;n<=6;n++{stub(t,dir,n,n==stop)}
  py:="from pathlib import Path\nimport os\np=Path(os.environ['MOCK_COUNTER']); p.write_text((p.read_text() if p.exists() else '')+'3\\n')\n"
  if e:=os.WriteFile(filepath.Join(dir,"03_Gerar_Roteiro_SEGURO.py"),[]byte(py),0644);e!=nil{t.Fatal(e)}
  var b bytes.Buffer;e:=execute(dir,&b)
  if (e!=nil)!=(stop!=0){t.Fatalf("stop %d: %v",stop,e)}
  raw,e:=os.ReadFile(counter);if e!=nil{t.Fatal(e)}
  expected:="1\n2\n3\n4\n5\n6"
  if stop!=0{expected=strings.Join(strings.Split(expected,"\n")[:stop],"\n")}
  if strings.TrimSpace(string(raw))!=expected{t.Fatalf("stop=%d got=%q want=%q",stop,string(raw),expected)}
 }
}
