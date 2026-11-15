# Revisão visual e técnica — 15/11/2026

## Evidência validada

- **CI do motor 2D** (Windows/Linux): [43675611489](https://github.com/producaohelper-netizen/Curiosidades-Studio-Modular/actions/runs/43675611489), aprovado; inclui preservação de transparência, limites de efeitos, reações e cenários determinísticos.
- **CI do executável candidato** (Windows/Linux): [43675611490](https://github.com/producaohelper-netizen/Curiosidades-Studio-Modular/actions/runs/43675611490), aprovado para compilação e testes, **não homologado como produto final**.
- **Render real ilustrado com Wikimedia + OpenCLIP + Piper + FFmpeg**: [43675401883](https://github.com/producaohelper-netizen/Curiosidades-Studio-Modular/actions/runs/43675401883), aprovado tecnicamente; MP4 polvo ~8,3s, vulcão ~8,9s (H.264/AAC, 960×540, com narração real brasileira).
- Os desenhos usados foram `Red_octopus.svg` (CC0) e `Gunung_Berapi_Erupsi.svg` (CC BY-SA 4.0) do Wikimedia Commons. Licenças devem acompanhar qualquer publicação/derivação.
- A primeira versão das cenas tinha nuvem de tinta enorme, fundo errado para vulcão e luz submarina opaca; esses pontos foram corrigidos e testados novamente.
- O gerador experimental Qwen JSON/Pillow, mesmo produzindo PNGs para alguns assuntos, criou círculos sem relação com os personagens. **Desabilitado por padrão** para não gerar episódios falsamente aprovados.

## Avaliação artística

**REPROVADO — ainda não semelhante ao vídeo de referência.** As duas amostras têm imagens reconhecíveis, efeitos 2D e movimentos ambientais, mas não representam uma animação articulada profissional: falta movimento independente de membros, mudanças expressivas de poses, maior riqueza visual e encenação de interações entre vários personagens.

O modelo atual ainda não demonstrou três vídeos completos de ~5 minutos com assuntos distintos, pesquisa real, imagens coerentes e qualidade aceitável. Testes com peças simuladas ou vídeos técnicos curtos **não comprovam** funcionamento integral do executável para uso final.

## Proteções e melhorias integradas

1. Clipes da pasta `clips/` são concatenados corretamente no MP4 da pasta do episódio (antes havia erro por caminhos diferentes).
2. A duração de todas as falas reais é calculada **antes** da renderização; ajustes modestos de velocidade são possíveis sem acelerar artificialmente o vídeo.
3. A mesma identidade visual é mantida por `asset_id` ao longo das cenas.
4. Fotografias e desenhos de baixa qualidade não são aceitos silenciosamente no modo cartoon.
5. Fundo, nuvem de tinta, vulcão e partículas possuem animação determinística e canal alfa composto corretamente.
6. O programa não informa aprovação artística automática.

## Critérios ainda obrigatórios

- Renderização real completa no Windows a partir de um clique, sem passos escondidos ou bloqueios.
- Três assuntos muito diferentes, vídeos de 285–315 segundos, 24 FPS e resolução adequada.
- Narração e cenas correspondentes frase a frase; áudio não pode ser cortado.
- Articulação consistente e ações/encenação além de zoom e translação simples.
- Comparação visual documentada com a amostra do usuário, seguida de **aprovação final somente quando alcançada**.
