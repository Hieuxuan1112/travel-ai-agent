"""Unit test cho tts.py - khong goi Gemini that, gia lap google.genai.Client."""

import base64
import os
import sys
import wave
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-used")

import tts  # noqa: E402


class _FakeOutputAudio:
    def __init__(self, data: str):
        self.data = data


class _FakeInteraction:
    def __init__(self, data: str):
        self.output_audio = _FakeOutputAudio(data)


class _FakeInteractions:
    def __init__(self, data: str):
        self._data = data

    def create(self, **kwargs):
        return _FakeInteraction(self._data)


class _FakeClient:
    def __init__(self, api_key=None, data: str = ""):
        self.interactions = _FakeInteractions(data)


def test_synthesize_returns_valid_wav_bytes(monkeypatch):
    pcm_silence = b"\x00\x00" * 100  # 100 sample gia, 16-bit mono
    encoded = base64.b64encode(pcm_silence).decode()

    monkeypatch.setattr("google.genai.Client", lambda api_key=None: _FakeClient(data=encoded))

    wav_bytes = tts.synthesize("Have a wonderful day!")

    assert wav_bytes is not None
    with wave.open(BytesIO(wav_bytes), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 24000
        assert wav_file.readframes(wav_file.getnframes()) == pcm_silence


def test_synthesize_returns_none_on_api_failure(monkeypatch):
    def _boom(api_key=None):
        raise RuntimeError("quota exceeded")

    monkeypatch.setattr("google.genai.Client", _boom)

    assert tts.synthesize("anything") is None
