"""Deterministic, audio-envelope-driven mouth pose selection.

No phoneme recognition is claimed. The WAV signal is measured in windows;
a compatible mouth sprite sheet can show closed, small and wide mouth poses.
"""
from __future__ import annotations
import math
import wave
from pathlib import Path


class MouthSyncError(ValueError):
    pass


def wav_envelope(path, *, window_ms=50):
    if not 10 <= window_ms <= 200:
        raise MouthSyncError("Janela de audio fora da faixa")
    with wave.open(str(path), "rb") as wav:
        channels, width, rate = wav.getnchannels(), wav.getsampwidth(), wav.getframerate()
        if width not in (1, 2) or channels not in (1, 2) or rate <= 0:
            raise MouthSyncError("WAV PCM 8/16 bits mono ou stereo necessario")
        count = max(1, round(rate * window_ms / 1000))
        amplitudes = []
        while True:
            frames = wav.readframes(count)
            if not frames:
                break
            if width == 1:
                values = [abs(v - 128) / 128 for v in frames]
            else:
                from array import array
                import sys
                samples = array("h")
                samples.frombytes(frames[:len(frames) - len(frames) % 2])
                if sys.byteorder != "little":
                    samples.byteswap()
                values = [abs(v) / 32768 for v in samples]
            amplitudes.append(math.sqrt(sum(v * v for v in values) / max(1, len(values))))
    if not amplitudes:
        raise MouthSyncError("Audio vazio")
    return {"window_ms": window_ms, "amplitudes": amplitudes,
            "duration_seconds": len(amplitudes) * window_ms / 1000}


def mouth_pose_at(envelope, time_sec, *, silence=0.018, wide=0.11):
    if not isinstance(time_sec, (int, float)) or not math.isfinite(time_sec):
        raise MouthSyncError("Tempo invalido")
    if not 0 <= silence < wide <= 1:
        raise MouthSyncError("Limiares invalidos")
    amplitudes = envelope["amplitudes"]
    if not amplitudes:
        raise MouthSyncError("Envelope vazio")
    index = min(len(amplitudes) - 1, max(0, int(time_sec * 1000 / envelope["window_ms"])))
    amplitude = amplitudes[index]
    return 0 if amplitude < silence else 1 if amplitude < wide else 2
