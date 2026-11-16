## Novo direcionamento editorial — Reels (em desenvolvimento)

### Modo Reels no executável Windows (experimental)

Com Python, Piper, FFmpeg e dependências já instalados, o executável
agora oferece um comando de revisão:

```powershell
.\\CuriosidadesStudio_Unificado_Windows_CANDIDATO.exe --reels roteiro.json gancho.png contexto.png desenvolvimento.png revelacao.png
```

O roteiro JSON deve passar pela validação editorial de
`universal_engine.shortform` e conter duas referências registradas.
O programa narra quatro partes com Piper, monta as legendas por trecho e
gera `Videos/CuriosidadesStudio/reels/reel_revisao.mp4`. **Não verifica
automaticamente a autenticidade das fontes ou direitos das imagens.**
Esse comando ainda exige fornecer roteiro e quatro imagens; não é o
fluxo automático de um clique, não publica conteúdo e não substitui
revisão humana.

### Renderização vertical experimental para revisão

Depois de criar o áudio com `python -m universal_engine.reel_narration`,
é possível renderizar um MP4 vertical com **quatro imagens próprias ou
licenciadas**, uma para cada seção do roteiro:

```bash
python -m universal_engine.reel_render \
  --narration-json saida/narracao_e_legendas.json \
  --images gancho.png contexto.png desenvolvimento.png revelacao.png \
  --output saida/reel_revisao.mp4
```

Requer FFmpeg e Pillow instalados. A montagem usa a duração real da narração
e legendas temporizadas por trecho, mas ainda não implementa cortes a cada
1–3 segundos, trilha, transições, verificação factual independente ou seleção
automática de visuais. **Não é a versão final do modo Reels do executável**.
A saída inclui `reel_revisao.review.json` com aprovação de publicação falsa.


O plano **Fatos Que Parecem Mentira** exige uma segunda linha de produção,
separada dos episódios horizontais de cinco minutos.

- **Formato-alvo:** 1080 × 1920 (9:16), 24 fps, 25 ou 45 segundos.
- **Quatro séries:** história real (35%), ciência/natureza (30%),
  mistérios documentados (20%) e cotidiano (15%).
- **Roteiro obrigatório:** gancho, contexto, desenvolvimento e revelação.
- **Evidências:** no mínimo duas referências registradas e afirmações
  classificadas como fato, hipótese ou questão em aberto. Referências
  informadas por IA **não** são automaticamente verificadas.
- **Aprovação:** bloqueada até checagem independente das fontes e revisão
  editorial/artística. A futura renderização deve incluir legendas sincronizadas,
  trilha baixa, cortes frequentes e visuais pertinentes.

O contrato e a checagem de roteiro estão em
`universal_engine/shortform.py`. Para validar um roteiro JSON existente:

```bash
python -m universal_engine.shortform_preflight --input roteiro_reel.json --output plano_reel.json
```

**Estado real:** essa etapa prepara e valida o plano editorial; **ainda não
gera um Reel**. O executável Windows atual continua usando o pipeline de
cinco minutos. A integração de narração curta, renderização vertical,
legendas, música, checagem independente e exportação MP4 é trabalho pendente.
Não use a aprovação dos testes de cinco minutos como prova de que o novo
formato está pronto.

---

# Curiosidades Studio — integração e validação

Repositório destinado ao desenvolvimento do gerador de vídeos de curiosidades para YouTube.

**Critérios de aceite:** pesquisa de tendências reais, escolha editorial, roteiro de ~5 minutos coerente, cenas que representem efetivamente a narração, voz em português, vídeo sincronizado e validação audiovisual. O sucesso de um teste de compilação NÃO significa aprovação artística.

A automação deve usar GitHub Actions em Windows para compilar/testar o programa e testes de integração com dados simulados em ambiente separado. Modelos Ollama, Piper e fontes web reais precisam de validação adicional. Não há garantia de viralização.

O projeto original será integrado aqui em mudanças revisadas, sem desabilitar antivírus ou instalar componentes silenciosamente.

## Status de validação — 14/11/2026

- GitHub Actions (Linux e Windows): compilação e integração básica passaram no workflow [43622825547](https://github.com/producaohelper-netizen/Curiosidades-Studio-Modular/actions/runs/43622825547).
- Correção de cache de cenas implementada: alteração do roteiro agora invalida os trechos visuais antigos; confirmado em duas renderizações locais.
- Gate de qualidade: o workflow [43621872797](https://github.com/producaohelper-netizen/Curiosidades-Studio-Modular/actions/runs/43621872797) confirmou que vídeos inadequados são rejeitados.
- Episódio de 292,15 segundos foi reprovado: resolução 1280×720, apenas 24 tomadas (média 12,17 s), ausência de ações explícitas nos 6 capítulos; narração de diagnóstico, não a voz final.
- O MP4 NÃO está aprovado artisticamente. Nenhum executável deve ser divulgado como versão final até a animação, as vozes, a correspondência cena/roteiro e o teste nativo Windows serem aprovados.

## Revisão da arquitetura visual — 14/11/2026

Os módulos em `universal_engine/` agora incluem:
- `trends.py`: tendências brasileiras via RSS e filtro de temas inadequados;
- `storyboard_planner.py`: divisão do roteiro em cenas e direção visual pelo Ollama;
- `media_sources.py`: busca e registro de autoria/licença no Wikimedia Commons;
- `visual_matcher.py`: OpenCLIP local para associar imagem/roteiro;
- `local_generator.py`: geração opcional via API local do ComfyUI;
- `visual_pipeline.py`: Commons → OpenCLIP → ComfyUI, sem inserir imagens aleatórias;
- `scenespec.py`, `camera.py`, `sprites.py`, `layer_renderer.py`: animação em camadas e movimentos de câmera;
- `narration.py`: Piper com cache de falas e adaptação da cena ao áudio real.

**Evidências dos testes**:
- [Windows + Linux: testes do motor, narração, sprites e render curto](https://github.com/producaohelper-netizen/Curiosidades-Studio-Modular/actions/runs/43653760232): aprovado.
- [Wikimedia Commons e OpenCLIP reais](https://github.com/producaohelper-netizen/Curiosidades-Studio-Modular/actions/runs/43653640498): aprovado; 15 imagens licenciadas encontradas. Exemplo de correspondência: texto de polvo contra imagem de polvo (0,3105) versus imagem de vulcão (0,0951).
- [Gate audiovisual](https://github.com/producaohelper-netizen/Curiosidades-Studio-Modular/actions/runs/43653570640): reprovou corretamente um vídeo tecnicamente inadequado.

**Não há aprovação de produto final:** não foram comprovados a geração de imagens local com modelo real, a extração automática de personagens consistentes em camadas, a produção de cinco minutos sobre vários assuntos com todas as dependências reais, a qualidade de narração, nem a semelhança artística com a amostra de animação do usuário. Não publicar/entregar um executável como final baseado apenas nos testes unitários.

A amostra do usuário e o episódio anterior foram amostrados a cada 4 segundos; o vídeo antigo teve mais mudanças de pixels, mas **menos coerência narrativa**. Portanto, qualidade não é só número de cortes; a prioridade é ação visual correspondente à fala.

## Integração híbrida atual (desenvolvimento, não liberar como produto final)

Novo fluxo `python -m universal_engine.production` com `oneclick/main.go`:
- Google Trends Brasil + Ollama (roteiro e direção de 40–100 cenas);
- Wikimedia Commons/atribuição + OpenCLIP para associação semântica;
- geração local opcional pelo ComfyUI, seleção de checkpoint já instalado;
- sprites consistentes por asset_id + recorte local rembg; modo CPU opcional com foto isolada;
- verificação semântica dos sujeitos e distinção de fotografias vs cartoons;
- Piper pt-BR real com WAV por cena, sincronização temporal, FFmpeg 24 FPS, créditos de licença;
- falha explícita quando cenas, direitos, áudio ou duração não atendem aos critérios.

**Evidência:** [GitHub Actions Piper real](https://github.com/producaohelper-netizen/Curiosidades-Studio-Modular/actions/runs/43658995573) passou. [Compilação e integração simulada](https://github.com/producaohelper-netizen/Curiosidades-Studio-Modular/actions/runs/43659910434) não provam produção real. A tentativa de três assuntos reais encontrou falhas de correspondência/qualidade; os curtos vídeos inspecionados tinham borrões de recorte e não eram semelhantes à amostra. Por isso foi adicionado controle de estilo 2D. **Nenhum .exe foi homologado como produto final**, a instalação local de ComfyUI/checkpoints depende do computador, e nenhum vídeo de 5 minutos com esse novo fluxo passou revisão artística ou testes sobre três temas reais.


## Continuação: motor ilustrado reutilizável e isolamento de episódios

Melhorias integradas após a comparação com os três clipes reais:
- cada execução cria `episodes/AAAAmmdd_HHMMSS_assunto_id`, preservando roteiros, imagens, vozes e MP4 de assuntos diferentes sem mistura;
- movimentos consecutivos passam a interpolar a partir da posição anterior, sem teletransporte; ação `orbit` possui movimento real;
- o cache de imagens reconhece o estilo escolhido, não reaproveitando fotos antigas quando a produção está configurada para desenho animado;
- buscas Wikimedia priorizam ilustrações vetoriais (`filetype:drawing`); PNGs com transparência são preservados como sprites originais;
- cenas ilustradas podem utilizar fundos 2D gerados por código, sem cicatrizes fotográficas deixadas por inpainting;
- o inicializador Windows inclui uma etapa de preparação das dependências Python e modelo Piper se o Python já estiver instalado.

**Limitações ainda não resolvidas:** o executável não inclui instaladores completos de Python/Ollama/ComfyUI nem os pesos de IA; animação plenamente articulada de personagens arbitrários ainda não foi demonstrada; o motor 2D ilustrado precisa de execução com modelos e assets reais em múltiplos vídeos completos, com avaliação lado a lado da referência. Os clipes anteriores sobre polvo, Terra e vulcão comprovam apenas a integração técnica e continuam reprovados artisticamente.

Testes de unidade do motor de cenários ilustrados em [Windows e Linux](https://github.com/producaohelper-netizen/Curiosidades-Studio-Modular/actions/runs/43667959659) concluíram com sucesso. Isto **não significa** aprovação para YouTube.

## Progresso adicional — motor universal sem GPU (em desenvolvimento)

- Wikimedia Commons vetorial: teste real encontrou ilustrações transparentes licenciadas para **polvo** (CC0) e **vulcão** (CC BY-SA 4.0), mas **não encontrou Terra** com o limiar visual conservador. O resultado 2/3 não é cobertura universal.
- Criado fallback local para desenhos 2D por formas com Ollama + Pillow (JSON estritamente validado, sem execução de código arbitrário). O modelo pequeno Qwen2.5 1.5B falhou ao emitir JSON completo nas duas primeiras execuções; uma versão compacta com JSON Schema está em validação e NÃO foi aprovada.
- Movimento: corrigidos saltos de atores e órbitas; adicionados efeitos temporais de tinta, erupção e deformação orgânica sutil em animais 2D. Isso não substitui rigging/articulação profissional.
- Preparação inicial: bibliotecas gratuitas e voz Piper são obtidas quando necessário; detecção de FFmpeg anterior e inicialização automática do Ollama instalado. Ainda depende de Python existente, acesso a modelos e eventuais serviços locais.
- [Testes unitários Windows/Linux das mudanças](https://github.com/producaohelper-netizen/Curiosidades-Studio-Modular/actions/runs/43669742260): aprovados. **Sem validação artística final, sem comprovação de três episódios completos com um clique.**
