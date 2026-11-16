"""Build timed captions from independently synthesized speech segments.

Each WAV is one spoken caption phrase. Boundaries are derived from actual PCM
sample counts, not guessed speaking rates. This is phrase-level sync, not
forced word alignment.
"""
from __future__ import annotations
from pathlib import Path
import wave
from .reel_caption_timing import validate_cues, CaptionTimingError


def phrase_cues(segments):
    """Return cues and total duration for [(text, wav_path), ...]."""
    if not isinstance(segments, (list, tuple)) or not segments:
        raise CaptionTimingError("Nenhum segmento narrado")
    cues = []
    total_frames = 0
    expected = None
    for index, item in enumerate(segments):
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise CaptionTimingError(f"Segmento {index} inválido")
        text, path = item
        if not isinstance(text, str) or not text.strip() or len(text) > 160:
            raise CaptionTimingError(f"Texto do segmento {index} inválido")
        try:
            with wave.open(str(Path(path)), "rb") as audio:
                spec = (audio.getnchannels(), audio.getsampwidth(), audio.getframerate(),
                        audio.getcomptype())
                frames = audio.getnframes()
        except (OSError, EOFError, wave.Error) as exc:
            raise CaptionTimingError(f"WAV inválido no segmento {index}: {exc}") from exc
        if frames <= 0 or spec[0] != 1 or spec[1] != 2 or spec[3] != "NONE":
            raise CaptionTimingError("Exige WAV PCM mono 16-bit não vazio")
        if expected is None:
            expected = spec
        elif expected != spec:
            raise CaptionTimingError("Segmentos WAV incompatíveis")
        rate = spec[2]
        start = total_frames / rate
        total_frames += frames
        cues.append({"start": start, "end": total_frames / rate, "text": text.strip()})
    duration = total_frames / expected[2]
    validate_cues(cues, duration)
    return {"cues": cues, "duration": duration, "sample_rate": expected[2]}


def join_phrase_wavs(segments, output):
    """Concatenate the exact PCM frames and return matching caption cues."""
    timing = phrase_cues(segments)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    first = Path(segments[0][1])
    with wave.open(str(first), "rb") as source:
        params = source.getparams()
    with wave.open(str(destination), "wb") as combined:
        combined.setparams(params)
        for _, path in segments:
            with wave.open(str(path), "rb") as source:
                while True:
                    data = source.readframes(65536)
                    if not data:
                        break
                    combined.writeframesraw(data)
    return timing
