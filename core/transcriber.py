"""Whisper transcription pipeline — YouTube captions first, Whisper fallback."""

from pathlib import Path

from rich.console import Console

console = Console()


def transcribe_youtube(video_id: str) -> str | None:
    """Try to pull existing YouTube captions. Returns None if unavailable."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        api = YouTubeTranscriptApi()
        result = api.fetch(video_id)
        return " ".join(snippet.text for snippet in result)
    except Exception:
        return None


def transcribe_audio(audio_path: Path, model_size: str = "base") -> str:
    """Transcribe an audio file using faster-whisper."""
    from faster_whisper import WhisperModel

    # Use CPU with int8 — avoids needing CUDA/cuBLAS
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(str(audio_path))
    return " ".join(segment.text.strip() for segment in segments)


async def get_transcript(
    url: str,
    audio_path: Path,
    model_size: str = "base",
    platform: str = "instagram",
) -> str:
    """Get transcript for a video — YouTube captions first, then Whisper.

    For YouTube videos, attempts to pull existing captions before falling back
    to Whisper. For all other platforms, goes straight to Whisper.
    """
    # YouTube: try captions first (free and fast)
    if platform == "youtube":
        # Extract video ID from URL
        video_id = _extract_youtube_id(url)
        if video_id:
            caption_text = transcribe_youtube(video_id)
            if caption_text:
                console.print(f"  [green]✓[/green] Captions found for {video_id}")
                return caption_text
            console.print(f"  [yellow]![/yellow] No captions, using Whisper for {video_id}")

    # Whisper fallback for all platforms
    return transcribe_audio(audio_path, model_size)


def _extract_youtube_id(url: str) -> str | None:
    """Extract video ID from various YouTube URL formats."""
    import re

    patterns = [
        r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:embed/)([a-zA-Z0-9_-]{11})",
        r"(?:shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None
