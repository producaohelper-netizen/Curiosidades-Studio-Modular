"""Style-aware matching so realistic photographs are not sold as cartoons.

Scores relative cartoon-vs-photo descriptions using the SAME OpenCLIP model.
A margin is only a heuristic; results require visual human review.
"""
from pathlib import Path

class StyleMismatch(RuntimeError):
    pass

CARTOON_PROMPT=("A clean colorful flat two dimensional cartoon illustration "
                "with bold ink outlines, clear shapes and hand-drawn characters")
PHOTO_PROMPT=("A realistic high detail documentary photograph with natural "
              "lighting, real world textures and photographic camera depth")

def cartoon_indices(matcher, images, minimum_advantage=.015):
    images=[Path(p) for p in images]
    if not images:return []
    a=matcher.score(CARTOON_PROMPT,images)
    b=matcher.score(PHOTO_PROMPT,images)
    if len(a)!=len(images) or len(b)!=len(images):
        raise StyleMismatch("Pontuação visual incompleta")
    return [i for i,(cartoon,photo) in enumerate(zip(a,b))
            if cartoon-photo>=minimum_advantage]

# A scientific chart often appears "cartoon-like" to CLIP because it uses
# line art. For *actors*, compare against diagrams explicitly.
ACTOR_PROMPT=(
    "A single complete recognizable cute cartoon character, clean silhouette, "
    "simple expressive pose, no writing, no labels, no arrows, isolated on a "
    "transparent background, ready for a children's animated story"
)
DIAGRAM_PROMPT=(
    "A scientific anatomy diagram with labels, arrows, lines, measurements "
    "and annotations showing parts of an animal, encyclopedia education chart"
)

def actor_indices(matcher, images, minimum_advantage=.015):
    """Reject annotated diagrams for animated actors; heuristic, not approval."""
    images=[Path(p) for p in images]
    if not images:return []
    a=matcher.score(ACTOR_PROMPT,images)
    b=matcher.score(DIAGRAM_PROMPT,images)
    if len(a)!=len(images) or len(b)!=len(images):
        raise StyleMismatch("Pontuação de diagrama incompleta")
    return [i for i,(actor,diagram) in enumerate(zip(a,b))
            if actor-diagram>=minimum_advantage]
