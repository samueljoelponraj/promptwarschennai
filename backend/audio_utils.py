"""
Audio utilities for processing PCM audio streams between Browser & Gemini Live API.
"""

import numpy as np


def float32_to_int16(float_bytes: bytes) -> bytes:
    """Converts 32-bit float PCM audio bytes from browser AudioWorklet to 16-bit Int16 PCM bytes."""
    float_array = np.frombuffer(float_bytes, dtype=np.float32)
    # Replace NaN and Inf with 0.0 before processing
    float_array = np.nan_to_num(float_array, nan=0.0, posinf=1.0, neginf=-1.0)
    # Clip values to [-1.0, 1.0] range
    clipped = np.clip(float_array, -1.0, 1.0)
    int16_array = (clipped * 32767).astype(np.int16)
    return int16_array.tobytes()


def resample_pcm16(pcm_bytes: bytes, orig_rate: int, target_rate: int = 16000) -> bytes:
    """Resamples 16-bit Int16 PCM audio from orig_rate to target_rate using linear interpolation."""
    if orig_rate == target_rate or not pcm_bytes:
        return pcm_bytes

    audio_data = np.frombuffer(pcm_bytes, dtype=np.int16)
    duration = len(audio_data) / orig_rate
    target_samples = int(duration * target_rate)

    if target_samples <= 0:
        return b""

    old_indices = np.linspace(0, len(audio_data) - 1, num=len(audio_data))
    new_indices = np.linspace(0, len(audio_data) - 1, num=target_samples)

    resampled_data = np.interp(new_indices, old_indices, audio_data).astype(np.int16)
    return resampled_data.tobytes()
