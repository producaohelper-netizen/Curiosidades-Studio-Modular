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
