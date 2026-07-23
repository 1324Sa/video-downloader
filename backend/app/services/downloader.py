import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, Optional
import yt_dlp

# --- تحديد المسارات وثوابت التنزيل ودعم الـ Environment Variables ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
COOKIES_PATH = BASE_DIR / "cookies.txt"

# إذا كان متغير البيئة موجوداً في Render، قم بإنشاء ملف cookies.txt تلقائياً من محتواه
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
    """استخراج تفاصيل الفيديو مع دعم الفيديوهات العادية و الـ Shorts."""
    
    print(f"=== CHECK COOKIES ===")
    print(f"Path: {COOKIES_PATH.absolute()}")
    print(f"Exists: {COOKIES_PATH.exists()}")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }

    if COOKIES_PATH.exists():
        ydl_opts['cookiefile'] = str(COOKIES_PATH.absolute())
        print("-> Cookie file successfully attached to yt_dlp options.")
    else:
        print("-> WARNING: Cookie file NOT found on the server path!")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            formats = info.get('formats', [])
            seen_heights = set()
            video_formats = []

            for f in formats:
                height = f.get('height')
                # السماح بالصيغ التي تحتوي على فيديو (حتى لو كان الصوت منفصلاً أو مدمجاً لتوافق Shorts)
                if height and height not in seen_heights:
                    seen_heights.add(height)
                    video_formats.append({
                        "format_id": f.get('format_id'),  # استخدام الـ format_id الفعلي لضمان نجاح التحميل لاحقاً
                        "resolution": f"{height}p",
                        "height": height,
                        "ext": f.get('ext', 'mp4'),
                    })

            # إذا لم يتم العثور على صيغ مفصلة (مثل بعض روابط Shorts)، أضف صيغة افتراضية آمنة
            if not video_formats:
                video_formats.append({
                    "format_id": "best",
                    "resolution": "Best Quality",
                    "height": 1080,
                    "ext": "mp4",
                })

            # ترتيب الدقات من الأعلى للأقل
            video_formats = sorted(
                video_formats, key=lambda x: x['height'], reverse=True
            )

            return {
                "success": True,
                "data": {
                    "title": info.get('title', 'فيديو بدون عنوان'),
                    "thumbnail": info.get('thumbnail'),
                    "extractor": info.get('extractor_key', 'Unknown'),
                    "video_formats": video_formats,
                },
            }
    except Exception as e:
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
    """تنزيل الميديا بالدقة المطلوبة مع دعم متابعة نسبة التنزيل وتمرير الكوكيز."""
    outtmpl = os.path.join(TEMP_DOWNLOAD_DIR, '%(id)s.%(ext)s')

    # خطاف متابعة تقدم التنزيل لتوفير القراءة اللحظية للفرونت إند
    def progress_hook(d: Dict[str, Any]) -> None:
        if d.get('status') == 'downloading' and progress_callback:
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            percentage = round((downloaded / total) * 100, 1) if total > 0 else 0

            progress_callback({
                'progress': percentage,
                'speed': d.get('speed', 0),
                'eta': d.get('eta', 0),
                'status': 'downloading',
            })

    ydl_opts: Dict[str, Any] = {
        'outtmpl': outtmpl,
        'quiet': True,
        'no_warnings': True,
        'overwrites': True,
        'progress_hooks': [progress_hook],
    }

    # ربط ملف الكوكيز لعمليات التحميل أيضاً
    if COOKIES_PATH.exists():
        ydl_opts['cookiefile'] = str(COOKIES_PATH.absolute())

    if download_type == "audio":
        # تنزيل الصوت فقط وتحويله إلى MP3
        ydl_opts['format'] = 'bestaudio/best'
        if use_ffmpeg:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality if quality in ["320", "192", "128"] else "192",
            }]
    else:
        # تنزيل الفيديو والدقة المختارة
        height_match = re.search(r'\d+', str(format_id)) if format_id else None

        if use_ffmpeg:
            if height_match:
                target_height = height_match.group()
                ydl_opts['format'] = (
                    f"bestvideo[height<={target_height}]+bestaudio/best[height<={target_height}]/best"
                )
            elif format_id and format_id != "best":
                ydl_opts['format'] = f"{format_id}+bestaudio/best"
            else:
                ydl_opts['format'] = 'bestvideo+bestaudio/best'

            ydl_opts['merge_output_format'] = 'mp4'
        else:
            # تنزيل مباشر لملف فيديو محتوي على صوت مسبقاً (بدون الحاجة لـ FFmpeg)
            if height_match:
                target_height = height_match.group()
                ydl_opts['format'] = f"b[height<={target_height}]/best[ext=mp4]/best"
            else:
                ydl_opts['format'] = 'b/best[ext=mp4]/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            # معالجة امتداد الملف الناتج بعد التنزيل
            if download_type == "audio" and use_ffmpeg:
                filename = os.path.splitext(filename)[0] + ".mp3"
            elif download_type == "video" and not filename.endswith('.mp4'):
                base = os.path.splitext(filename)[0]
                if os.path.exists(base + '.mp4'):
                    filename = base + '.mp4'

            return {
                "status": "completed",
                "file_path": filename,
                "title": info.get('title', 'Media File'),
            }
    except Exception as e:
        print(f"Download Error Details: {str(e)}")
        raise Exception(f"فشل التحميل: {str(e)}")
    # update timestamp 2026).