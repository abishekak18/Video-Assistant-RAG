import static_ffmpeg
static_ffmpeg.add_paths()

import yt_dlp
from pydub import AudioSegment
import os

DOWNLOAD_DIR = 'downloades'
os.makedirs(DOWNLOAD_DIR,exist_ok = True)

def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "restrictfilenames": True,
        "nocheckcertificate": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "web"]
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        },
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "postprocessor_args": {
            "FFmpegExtractAudio": ["-ar", "16000", "-ac", "1"]
        },
        "quiet": True,
    }

    # Support cookies for cloud environments (Render/AWS) where YouTube blocks datacenter IPs
    cookie_file = "cookies.txt"
    if os.path.exists(cookie_file):
        ydl_opts["cookiefile"] = cookie_file
    elif os.getenv("YOUTUBE_COOKIES"):
        cookie_path = os.path.join(DOWNLOAD_DIR, "render_cookies.txt")
        with open(cookie_path, "w", encoding="utf-8") as f:
            f.write(os.getenv("YOUTUBE_COOKIES"))
        ydl_opts["cookiefile"] = cookie_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            raw_file = ydl.prepare_filename(info)
            base, _ = os.path.splitext(raw_file)
            filename = base + ".wav"
        return filename
    except Exception as e:
        err_msg = str(e)
        if "confirm you're not a bot" in err_msg or "Sign in" in err_msg:
            raise RuntimeError(
                "YouTube has blocked downloads from this cloud server IP ('Sign in to confirm you're not a bot'). "
                "👉 Solution: Please use the '📁 Upload File' tab in the sidebar to upload the video/audio file directly, "
                "or provide cookies.txt."
            )
        raise



def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000) #16khz
    audio.export(output_path, format="wav")
    return output_path



def chunk_audio(wav_path : str , chunk_minutes : int = 3) -> list:
    audio = AudioSegment.from_file(wav_path)
    audio = audio.set_channels(1).set_frame_rate(16000) # 16kHz mono
    chunk_ms = chunk_minutes * 60 * 1000 

    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start : start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")

        chunks.append(chunk_path)
    
    return chunks

def process_input(source: str) -> list:
    is_remote = source.startswith("http://") or source.startswith("https://")
    if is_remote:
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")

    # Remove the master WAV to save disk/RAM space once chunks are created
    # If it was a downloaded YouTube file or converted local copy
    if is_remote or wav_path.endswith("_converted.wav"):
        if os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except Exception:
                pass

    return chunks

