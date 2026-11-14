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
