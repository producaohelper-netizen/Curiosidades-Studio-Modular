# Arquitetura universal de animação — requisito de produto

**Objetivo:** o mesmo programa produz vídeos de curiosidades sobre qualquer domínio (animais, ciência, história, tecnologia, espaço etc.) sem código específico por tema.

## Contrato entre roteiro e animação

Cada trecho narrado gera uma **SceneSpec** estruturada e verificável:

```json
{
  "scene_id": "s01",
  "narration": "O polvo solta tinta e escapa.",
  "duration_target_seconds": 6,
  "setting": {"kind": "underwater", "style": "illustrated-2d"},
  "actors": [
    {"id": "polvo", "kind": "octopus", "asset_id": "octopus-v1"},
    {"id": "predador", "kind": "shark", "asset_id": "shark-v1"}
  ],
  "timeline": [
    {"at": 0, "action": "approach", "target": "predador", "towards": "polvo"},
    {"at": 1.4, "action": "react", "target": "polvo", "emotion": "surprised"},
    {"at": 2.2, "action": "emit_particles", "target": "polvo", "effect": "ink_cloud"},
    {"at": 3.5, "action": "escape", "target": "polvo", "direction": "left"},
    {"at": 4.0, "action": "camera_push", "target": "predador"}
  ],
  "visual_fact": "O polvo pode liberar tinta para confundir predadores."
}
```

Não exigir propriedades opcionais para cenas que não as usem. Rejeitar especificações com ações ou referências ausentes, ao invés de produzir algo sem nexo.

## Reutilização

- **Assets:** uma identidade consistente para cada personagem/objeto dentro do vídeo, com catálogo e cache por asset_id.
- **Ações:** timeline baseada em operações genéricas (move, rotate, scale, morph, react, enter, exit, follow, pan, zoom, reveal, compare, particles, highlight).
- **Montagem:** sincronizar as ações com fonemas/trechos narrados, usando durações de áudio reais.
- **Estilo:** cores, espessura, composição, iluminação e tipografia comuns em todas as cenas do mesmo vídeo.
- **Fallback:** quando faltar uma ilustração confiável, produzir representação esquemática correta e registrar queda de qualidade; não substituir por personagem aleatório.
- **Aprovação:** cada cena deve demonstrar visualmente a afirmação narrada; registrar relatório cena↔frase, diversidade de planos, ritmo, inteligibilidade e direitos de uso.
- **Atualização:** tendências recentes exigem fontes e Internet; IA local pode orquestrar, mas não conhecer novidades sozinha.

## Limite realista

A biblioteca de ações é reutilizável, **mas a qualidade de ilustrações inéditas para temas arbitrários depende de geração ou obtenção de novos assets**. Não garantir animação artística profissional universal sem testes e disponibilidade de recursos. O motor precisa degradar de maneira transparente ou pedir intervenção quando uma cena não puder ser representada adequadamente.

**Não criar dezenas de animações rigidamente codificadas por tema.**
