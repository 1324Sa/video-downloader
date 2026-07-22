import os
from pathlib import Path
from celery import Celery
import yt_dlp

# 1. تحديد المسارات الأساسية
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DOWNLOADS_DIR = BASE_DIR / "temp_downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# 2. قراءة إعدادات Redis من متغيرات البيئة
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("RESULT_BACKEND", "redis://localhost:6379/1")

# 3. إنشاء وتحديث تطبيق Celery
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


# 4. تعريف مهمة التحميل (Task)
@celery_app.task(bind=True)
def download_video_task(self, url: str, options: dict = None, **kwargs):
    """
    تنفذ عملية تحميل الفيديو أو الصوت باستخدام yt-dlp وتسجل التقدم لحظياً.
    """
    options = options or {}

    # استخراج الخيارات الممررة من FastAPI
    download_type = options.get("download_type", "video")
    format_id = options.get("format_id", "best")
    quality = options.get("quality", "192")

    # تحديد اسم ومسار الملف الناتج
    output_filename = "video_output.mp4"
    output_file_path = DOWNLOADS_DIR / output_filename

    # دالة التحديث اللحظي لنسبة التقدم
    def progress_hook(d):
        if d.get("status") == "downloading":
            total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
            downloaded_bytes = d.get("downloaded_bytes", 0)
            percentage = round((downloaded_bytes / total_bytes) * 100, 2)

            # تحديث حالة المهام في Celery بالبيانات اللحظية
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

    # إعداد خيارات yt-dlp بناءً على النوع المطلوب (فيديو أو صوت)
    if download_type == "audio":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(DOWNLOADS_DIR / "audio_output.%(ext)s"),
            "overwrites": True,
            "progress_hooks": [progress_hook],
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": quality,
                }
            ],
        }
        output_filename = "audio_output.mp3"
    else:
        # اختيار صيغة الفيديو
        video_format = (
            f"{format_id}+bestaudio/best"
            if format_id != "best"
            else "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        )
        ydl_opts = {
            "format": video_format,
            "outtmpl": str(output_file_path),
            "overwrites": True,
            "progress_hooks": [progress_hook],
        }

    # تحديث أولّي قبل بدء yt-dlp
    self.update_state(
        state="PROGRESS",
        meta={
            "status": "processing",
            "progress": 0,
            "message": "جاري تجهيز رابط التحميل...",
        },
    )

    # 5. تنزيل الوسائط فعلياً
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # 6. النتيجة النهائية عند الاكتشمال
    return {
        "status": "completed",
        "progress": 100,
        "message": "تم التحميل والمعالجة بنجاح",
        "file_path": output_filename,
    }