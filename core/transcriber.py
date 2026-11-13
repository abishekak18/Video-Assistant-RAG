import os
import requests
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

# Sarvam's sync STT-translate API rejects audio longer than 30s.
# We slice each chunk into 25s pieces (with a 5s safety margin) before sending.
SARVAM_PIECE_SECONDS = 25

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"
SARVAM_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")

_model = None


def load_model():
    """Load local Whisper model only if explicitly opted in (high RAM/GPU required)."""
    global _model  

    if _model is None: 
        try:
            import whisper
        except ImportError:
            raise RuntimeError(
                "openai-whisper is not installed. To use cloud transcription (0 MB server RAM), "
                "please set GROQ_API_KEY in your environment variables."
            )
        print(f"Loading Whisper model: {WHISPER_MODEL} ...")
        _model = whisper.load_model(WHISPER_MODEL) 
        print("Whisper model loaded.")
    return _model 


def transcribe_chunk_groq(chunk_path: str) -> str:
    """Fast Cloud STT using Groq Whisper API (whisper-large-v3-turbo). Uses ~0 MB RAM."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing! Please configure GROQ_API_KEY in your environment variables "
            "(e.g. Render Dashboard -> Environment) to enable fast cloud transcription."
        )

    from groq import Groq
    client = Groq(api_key=api_key)
    
    with open(chunk_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(chunk_path), file.read()),
            model="whisper-large-v3-turbo",
            response_format="text"
        )
    return str(transcription)


def transcribe_chunk_whisper(chunk_path: str) -> str:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        return transcribe_chunk_groq(chunk_path)

    # Local Whisper is ONLY loaded if explicitly opted in via USE_LOCAL_WHISPER=true
    # Disabled by default on cloud hosting (Render Free Tier 512MB RAM cannot run local Whisper)
    if os.getenv("USE_LOCAL_WHISPER", "false").lower() in ("true", "1"):
        model = load_model()  
        result = model.transcribe(chunk_path, task="transcribe")  
        return result["text"]  

    raise RuntimeError(
        "GROQ_API_KEY is not set in environment variables! "
        "Render Free Tier (512MB RAM) cannot run local Whisper without running out of memory. "
        "Please add GROQ_API_KEY to your Render Dashboard Environment Variables."
    )


def _send_to_sarvam(piece_path: str) -> str:
    """Send one <=30s WAV file to Sarvam and return the English transcript."""
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY is not set in environment variables / .env")

    headers = {"api-subscription-key": api_key}

    with open(piece_path, "rb") as f:
        files = {"file": (os.path.basename(piece_path), f, "audio/wav")}
        data = {"model": SARVAM_MODEL, "with_diarization": "false"}
        response = requests.post(
            SARVAM_STT_TRANSLATE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120,
        )

    if not response.ok:
        print(f"\n❌ Sarvam returned {response.status_code}")
        print(f"Response body: {response.text}\n")
        response.raise_for_status()

    return response.json().get("transcript", "")


def transcribe_chunk_sarvam(chunk_path: str) -> str:
    """
    Sarvam sync API only accepts <=30s audio. We split this chunk into
    25-second pieces, send each separately, and join the transcripts.
    """
    if not os.getenv("SARVAM_API_KEY"):
        raise RuntimeError("SARVAM_API_KEY is not set in environment variables / .env")

    audio = AudioSegment.from_wav(chunk_path)
    piece_ms = SARVAM_PIECE_SECONDS * 1000

    full_text = ""
    total_pieces = (len(audio) + piece_ms - 1) // piece_ms

    for i, start in enumerate(range(0, len(audio), piece_ms)):
        piece = audio[start: start + piece_ms]
        piece_path = f"{chunk_path}_sv_{i}.wav"
        piece.export(piece_path, format="wav")

        try:
            print(f"  → Sarvam piece {i + 1}/{total_pieces} ...")
            full_text += _send_to_sarvam(piece_path) + " "
        finally:
            if os.path.exists(piece_path):
                os.remove(piece_path)

    return full_text.strip()


def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    """
    Route one chunk to Groq Whisper or Sarvam depending on language choice.
    - english  → Groq Whisper Cloud STT (whisper-large-v3-turbo)
    - hinglish → Sarvam Cloud STT (translates to English while transcribing)
    """
    if language.lower() == "hinglish":
        return transcribe_chunk_sarvam(chunk_path)
    return transcribe_chunk_whisper(chunk_path)


def transcribe_all(chunks: list, language: str = "english") -> str:
    full_transcript = "" 
    engine = "Sarvam AI" if language.lower() == "hinglish" else "Groq Cloud Whisper"
    print(f"Using {engine} for transcription.")

    try:
        for i, chunk in enumerate(chunks):  
            print(f"Transcribing chunk {i + 1}/{len(chunks)}...")
            text = transcribe_chunk(chunk, language=language)  
            full_transcript += text + " "  

        print("Transcription complete.")
        return full_transcript.strip()  
    finally:
        # Clean up chunk files after transcription to prevent disk/RAM bloat
        for chunk in chunks:
            if os.path.exists(chunk):
                try:
                    os.remove(chunk)
                except Exception:
                    pass
  