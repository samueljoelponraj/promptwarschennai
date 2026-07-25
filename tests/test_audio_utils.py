"""
Unit tests for audio processing utilities.
Verifies conversion and resampling correctness.
"""

import numpy as np
from backend.audio_utils import float32_to_int16, resample_pcm16


def test_float32_to_int16_conversion():
    # Generate 1 second of silent 32-bit floats
    floats = np.zeros(16000, dtype=np.float32)
    pcm_bytes = float32_to_int16(floats.tobytes())

    # Should be 16000 samples * 2 bytes/sample = 32000 bytes
    assert len(pcm_bytes) == 32000

    # Verify silent inputs convert to zero bytes
    int16_array = np.frombuffer(pcm_bytes, dtype=np.int16)
    assert np.all(int16_array == 0)


def test_float32_to_int16_clipping():
    # Test clipping values exceeding [-1.0, 1.0] limit
    floats = np.array([-1.5, 0.0, 1.5], dtype=np.float32)
    pcm_bytes = float32_to_int16(floats.tobytes())

    int16_array = np.frombuffer(pcm_bytes, dtype=np.int16)
    assert int16_array[0] == -32768
    assert int16_array[1] == 0
    assert int16_array[2] == 32767


def test_float32_to_int16_nan_handling():
    # Test handling of NaN and Inf values (critical fix)
    floats = np.array([np.nan, np.inf, -np.inf], dtype=np.float32)
    pcm_bytes = float32_to_int16(floats.tobytes())

    int16_array = np.frombuffer(pcm_bytes, dtype=np.int16)
    # NaNs should map to 0, Inf to max int16, -Inf to min int16
    assert int16_array[0] == 0
    assert int16_array[1] == 32767
    assert int16_array[2] == -32768


def test_resample_pcm16():
    # Resample 16-bit Int16 PCM array from 48000 Hz to 16000 Hz
    original_rate = 48000
    target_rate = 16000
    duration = 0.5  # half second

    original_samples = int(duration * original_rate)
    pcm_in = np.random.randint(-1000, 1000, original_samples, dtype=np.int16).tobytes()

    resampled = resample_pcm16(pcm_in, original_rate, target_rate)

    # Output size should be exactly 1/3 of the input
    expected_length = int(duration * target_rate) * 2  # 2 bytes per sample
    assert len(resampled) == expected_length
