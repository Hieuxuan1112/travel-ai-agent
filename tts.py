"""Doc cau tra loi cua agent bang giong Gemini TTS that (tra phi qua
GOOGLE_API_KEY, AI Studio pay-as-you-go) - cung mot key voi phan chat, khong
can them provider nao.

Rieng chieu NGHE cau hoi (STT) van dung Web Speech API mien phi cua trinh
duyet - xem app.py. Chi doi CHIEU DOC vi chat luong Gemini TTS tot hon han
speechSynthesis mac dinh cua trinh duyet; STT trinh duyet da du dung.
"""

import base64
import os
import wave
from io import BytesIO

TTS_MODEL = os.environ.get("TTS_MODEL", "gemini-3.1-flash-tts-preview")
TTS_VOICE = os.environ.get("TTS_VOICE", "Kore")

# ponytail: cung PCM 16-bit/24kHz/mono ma Gemini TTS tra ve luc viet code nay
# (da kiem tra that bang mot lan goi song). Neu Google doi format, wave.open
# se ghi sai header - nang cap: doc tu interaction.output_audio.mime_type
# thay vi hardcode, khi that su can.
_SAMPLE_RATE_HZ = 24000
_SAMPLE_WIDTH_BYTES = 2
_CHANNELS = 1


def synthesize(text: str) -> bytes | None:
    """Tra WAV bytes doc duoc bang <audio>, hoac None neu goi Gemini that bai.

    Loi o day (mang hong, het quota pay-as-you-go...) KHONG duoc lam sap app -
    nuot loi, tra None de caller lui ve TTS trinh duyet.
    """
    try:
        from google import genai

        client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        interaction = client.interactions.create(
            model=TTS_MODEL,
            input=text,
            response_format={"type": "audio"},
            generation_config={"speech_config": [{"voice": TTS_VOICE}]},
        )
        pcm = base64.b64decode(interaction.output_audio.data)
    except Exception as exc:
        print(f"   [tts] Gemini TTS that bai ({exc}) - lui ve doc bang trinh duyet.")
        return None

    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(_CHANNELS)
        wav_file.setsampwidth(_SAMPLE_WIDTH_BYTES)
        wav_file.setframerate(_SAMPLE_RATE_HZ)
        wav_file.writeframes(pcm)
    return buffer.getvalue()
