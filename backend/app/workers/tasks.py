import os
from pathlib import Path
import yt_dlp

# تجنب انهيار السيرفر في حال عدم وجود مكتبة Celery
try:
    from celery import Celery
    HAS_CELERY = True
except ImportError:
    HAS_CELERY = False
    Celery = None
    print("--> Warning: Celery is not installed. Running in synchronous mode.")

# 1. تحديد المسارات الأساسية
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DOWNLOADS_DIR = BASE_DIR / "temp_downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# مسار ملف الكوكيز إن وجد
COOKIES_PATH = BASE_DIR / "cookies.txt"

# 2. قراءة إعدادات Redis وإنشاء التطبيق فقط عند توفر Celery
if HAS_CELERY:
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    RESULT_BACKEND = os.getenv("RESULT_BACKEND", "redis://localhost:6379/1")

    celery_app = Celery(
        "downloader_tasks",
        broker=REDIS_URL,
        backend=RESULT_BACKEND,
    )

    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
    )
else:
    celery_app = None

# دالة وهمية لـ decorator في حال عدم وجود celery
def task_decorator(*args, **kwargs):
    def wrapper(func):
        return func
    return wrapper

task = celery_app.task if HAS_CELERY else task_decorator

# 4. تعريف مهمة التحميل
@task(bind=True)
def download_video_task(self, url: str, options: dict = None, **kwargs):
    options = options or {}
    download_type = options.get("download_type", "video")
    format_id = options.get("format_id", "best")
    quality = options.get("quality", "192")

    output_filename = "video_output.mp4"
    output_file_path = DOWNLOADS_DIR / output_filename

    def progress_hook(d):
        if d.get("status") == "downloading" and HAS_CELERY and hasattr(self, 'update_state'):
            total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
            downloaded_bytes = d.get("downloaded_bytes", 0)
            percentage = round((downloaded_bytes / total_bytes) * 100, 2)

            self.update_state(
                state="PROGRESS",
                meta={
                    "status": "processing",
                    "progress": percentage,
                    "speed": d.get("speed", 0),
                    "eta": d.get("eta", 0),
                    "message": "جاري تحميل الملف...",
                },
            )

    ydl_opts = {
        "outtmpl": str(output_file_path),
        "overwrites": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [progress_hook],
    }

    if COOKIES_PATH.exists():
        ydl_opts["cookiefile"] = str(COOKIES_PATH.absolute())

    if download_type == "audio":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality,
            }
        ]
    else:
        if format_id and format_id != "best":
            ydl_opts["format"] = f"{format_id}+bestaudio/best/best"
        else:
            ydl_opts["format"] = "best"
        ydl_opts["merge_output_format"] = "mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            output_filename = os.path.basename(filename)
            if download_type == "video" and not output_filename.endswith('.mp4'):
                base = os.path.splitext(output_filename)[0]
                if os.path.exists(os.path.join(DOWNLOADS_DIR, base + '.mp4')):
                    output_filename = base + '.mp4'
    except Exception as e:
        print(f"Task Download Error: {str(e)}")
        raise Exception(f"فشل التحميل: {str(e)}")

    return {
        "status": "completed",
        "progress": 100,
        "message": "تم التحميل والمعالجة بنجاح",
        "file_path": output_filename,
    }