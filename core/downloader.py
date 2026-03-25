"""yt-dlp wrapper for downloading videos and extracting audio."""

import tempfile
from pathlib import Path

import yt_dlp

_ffmpeg_location = None


def _get_ffmpeg_location() -> str:
    """Find ffmpeg path — checks system PATH first, then imageio-ffmpeg.

    For imageio-ffmpeg, the binary has a non-standard name, so we need to
    pass the full executable path to yt-dlp (it accepts both dir and exe path).
    """
    global _ffmpeg_location
    if _ffmpeg_location:
        return _ffmpeg_location
    import shutil
    path = shutil.which("ffmpeg")
    if path:
        _ffmpeg_location = str(Path(path).parent)
        return _ffmpeg_location
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        # yt-dlp accepts a direct path to the ffmpeg executable
        _ffmpeg_location = exe
        return _ffmpeg_location
    except ImportError:
        pass
    return ""


def _base_opts() -> dict:
    """Shared yt-dlp options."""
    opts = {
        "quiet": True,
        "no_warnings": True,
    }
    loc = _get_ffmpeg_location()
    if loc:
        opts["ffmpeg_location"] = loc
    return opts


def download_video(url: str, output_dir: Path | None = None) -> Path:
    """Download a video and return the path to the downloaded file."""
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp())

    output_template = str(output_dir / "%(id)s.%(ext)s")
    opts = _base_opts()
    opts["outtmpl"] = output_template

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return Path(filename)


def extract_audio(url: str, output_dir: Path | None = None) -> Path:
    """Download only the audio track as mp3 and return the file path."""
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp())

    output_template = str(output_dir / "%(id)s.%(ext)s")
    opts = _base_opts()
    opts.update({
        "outtmpl": output_template,
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    })

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # yt-dlp changes extension after postprocessing
        base = output_dir / f"{info['id']}.mp3"
        return base


def get_video_info(url: str) -> dict:
    """Extract metadata without downloading the video."""
    opts = _base_opts()
    opts["skip_download"] = True
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)
