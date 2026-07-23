import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, Optional
import yt_dlp

# --- تحديد المسارات وثوابت التنزيل ودعم الـ Environment Variables ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
COOKIES_PATH = BASE_DIR / "cookies.txt"

# إنشاء ملف cookies.txt تلقائياً إن وجد في متغيرات البيئة
youtube_cookies_env = os.getenv("YOUTUBE_COOKIES")
if youtube_cookies_env:
    try:
        with open(COOKIES_PATH, "w", encoding="utf-8") as f:
            f.write(youtube_cookies_env)
        print("-> Successfully generated cookies.txt from environment variable.")
    except Exception as e:
        print(f"-> Error writing cookies.txt from env: {e}")

TEMP_DOWNLOAD_DIR = "temp_downloads"
os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)


def extract_video_info(url: str) -> Dict[str, Any]:
    """استخراج تفاصيل الفيديو أو الشورتس مع تجاوز القيود وصيغ يوتيوب."""

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "format": "bestvideo+bestaudio/best",
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            }
        },
    }

    if COOKIES_PATH.exists():
        ydl_opts["cookiefile"] = str(COOKIES_PATH.absolute())

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            formats = info.get("formats", [])
            seen_heights = set()
            video_formats = []

            for f in formats:
                height = f.get("height")
                if height and height not in seen_heights:
                    seen_heights.add(height)
                    video_formats.append({
                        "format_id": str(height),
                        "resolution": f"{height}p",
                        "height": height,
                        "ext": f.get("ext", "mp4"),
                    })

            if not video_formats:
                video_formats.append({
                    "format_id": "best",
                    "resolution": "Best Quality",
                    "height": 1080,
                    "ext": "mp4",
                })

            video_formats = sorted(
                video_formats, key=lambda x: x["height"], reverse=True
            )

            return {
                "success": True,
                "data": {
                    "title": info.get("title", "فيديو بدون عنوان"),
                    "thumbnail": info.get("thumbnail"),
                    "extractor": info.get("extractor_key", "Unknown"),
                    "video_formats": video_formats,
                },
            }
    except Exception as e:
        print(f"Extraction Error: {str(e)}")
        return {"success": False, "error": str(e)}


def download_media(
    url: str,
    download_type: str = "video",
    format_id: str = "best",
    quality: str = "192",
    enhance_mode: str = "none",
    use_ffmpeg: bool = True,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    """تنزيل الميديا بالدقة المطلوبة مع معالجة حماية الدقة للشورتس."""
    outtmpl = os.path.join(TEMP_DOWNLOAD_DIR, "%(id)s.%(ext)s")

    def progress_hook(d: Dict[str, Any]) -> None:
        if d.get("status") == "downloading" and progress_callback:
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            percentage = round((downloaded / total) * 100, 1) if total > 0 else 0

            progress_callback({
                "progress": percentage,
                "speed": d.get("speed", 0),
                "eta": d.get("eta", 0),
                "status": "downloading",
            })

    # معالجة مرنة للصيغ لمنع خطأ Requested format is not available
    if download_type == "audio":
        format_option = "bestaudio/best"
    else:
        # فحص إذا كانت الدقة محددة برقم أو نص غير best
        clean_format = str(format_id).strip()
        if clean_format and clean_format not in ["best", "undefined", "null", "None"]:
            # البحث عن صيغة بحد أقصى للارتفاع وفي حال التعثر الانتقال تلقائياً لأفضل المتاح
            format_option = (
                f"bestvideo[height<={clean_format}]+bestaudio/"
                f"bestvideo[height<={clean_format}]/best[height<={clean_format}]/best"
            )
        else:
            format_option = "bestvideo+bestaudio/best"

    ydl_opts: Dict[str, Any] = {
        "outtmpl": outtmpl,
        "format": format_option,
        "quiet": True,
        "no_warnings": True,
        "overwrites": True,
        "progress_hooks": [progress_hook],
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            }
        },
    }

    if COOKIES_PATH.exists():
        ydl_opts["cookiefile"] = str(COOKIES_PATH.absolute())

    if download_type == "audio" and use_ffmpeg:
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": (
                quality if quality in ["320", "192", "128"] else "192"
            ),
        }]
    elif download_type == "video" and use_ffmpeg:
        ydl_opts["merge_output_format"] = "mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            if download_type == "audio" and use_ffmpeg:
                filename = os.path.splitext(filename)[0] + ".mp3"
            elif download_type == "video" and not filename.endswith(".mp4"):
                base = os.path.splitext(filename)[0]
                if os.path.exists(base + ".mp4"):
                    filename = base + ".mp4"

            return {
                "status": "completed",
                "file_path": filename,
                "title": info.get("title", "Media File"),
            }
    except Exception as e:
        print(f"Download Error Details: {str(e)}")
        raise Exception(f"فشل التحميل: {str(e)}")