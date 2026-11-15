"""Narration-aware expressive pose timing.

Uses a verified WAV duration, never estimated text length, to align visual
poses with the spoken line. This is NOT phoneme-level lip synchronization.
"""
from __future__ import annotations
import math
from .expressive_poses import expressive_frame


class PoseSyncError(ValueError):
    pass


def speech_pose_time(time_sec, speech_duration, *, lead_in=0.0, lead_out=0.0):
    values = (time_sec, speech_duration, lead_in, lead_out)
    if any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
        raise PoseSyncError("Tempos de narracao invalidos")
    if speech_duration <= 0 or lead_in < 0 or lead_out < 0:
        raise PoseSyncError("Duracao ou margens invalidas")
    if lead_in + lead_out >= speech_duration:
        raise PoseSyncError("Margens excedem a narracao")
    return max(0.0, min(float(time_sec) - lead_in,
                         speech_duration - lead_in - lead_out))


def speech_pose_frame(sheet, time_sec, speech_duration, *, rows, columns, frames,
                      fps=8, loop=True, lead_in=0.0, lead_out=0.0):
    elapsed = speech_pose_time(time_sec, speech_duration,
                               lead_in=lead_in, lead_out=lead_out)
    return expressive_frame(sheet, elapsed, rows=rows, columns=columns,
                            frames=frames, fps=fps, loop=loop)
