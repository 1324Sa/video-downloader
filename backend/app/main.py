import os
from pathlib import Path
from typing import Any, Dict, Optional

from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.downloader import extract_video_info
from app.workers.tasks import celery_app, download_video_task

# --- المسارات والثوابت ---
BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = BASE_DIR / "temp_downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# --- إعداد التطبيق ---
app = FastAPI(
    title="Social Media Downloader API",
    description="API لجلب ومعالجة فيديوهات وصوتيات منصات التواصل الاجتماعي",
)

# --- إعدادات CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- مخططات الطلبات (Request Schemas) ---
class VideoRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    download_type: str = "video"  # "video" أو "audio"
    format_id: Optional[str] = "best"  # دقة الفيديو
    quality: Optional[str] = "192"  # جودة الصوت (kbps)
    enhance_mode: Optional[str] = "none"  # تحسين الدقة/المعالجة


# --- المسارات (Endpoints) ---
@app.get("/", summary="Health Check")
def home() -> Dict[str, str]:
    """التحقق من حالة الخادم."""
    return {"message": "API Server is running successfully!"}


@app.post("/api/fetch-info", summary="Fetch Video Information")
async def fetch_info(payload: VideoRequest) -> Dict[str, Any]:
    """استقبال رابط الوسائط وإرجاع تفاصيله للواجهة الأمامية."""
    result = extract_video_info(payload.url)
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "حدث خطأ أثناء جلب البيانات"),
        )
    return result


@app.post("/api/download", summary="Enqueue Media Download Task")
async def start_download(payload: DownloadRequest) -> Dict[str, str]:
    """إضافة طلب التحميل إلى طابور Celery وإرجاع رقم المهمة (Task ID)."""
    options = {
        "download_type": payload.download_type,
        "format_id": payload.format_id,
        "quality": payload.quality,
        "enhance_mode": payload.enhance_mode,
    }
    task = download_video_task.delay(url=payload.url, options=options)

    return {
        "message": "تمت إضافة المهمة للانتظار بنجاح",
        "task_id": str(task.id),
    }


@app.get("/api/status/{task_id}", summary="Check Task Status & Progress")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """التحقق من حالة تنفيذ المهمة في Celery ونسبة التقدم الحالية."""
    task_result = AsyncResult(task_id, app=celery_app)
    state = task_result.state

    if state == "PENDING":
        return {"status": "pending", "progress": 0}

    elif state == "PROGRESS":
        info = task_result.info or {}
        return {
            "status": "processing",
            "progress": info.get("progress", 0),
            "speed": info.get("speed", 0),
            "eta": info.get("eta", 0),
            "message": info.get("message") or info.get("status", "جاري المعالجة..."),
        }

    elif state == "SUCCESS":
        return {
            "status": "completed",
            "progress": 100,
            "result": task_result.result,
        }

    elif state == "FAILURE":
        return {
            "status": "failed",
            "progress": 0,
            "error": str(task_result.info),
        }

    return {"status": state.lower(), "progress": 0}


@app.get("/api/files/{filename}", summary="Download File")
async def download_file(filename: str) -> FileResponse:
    """تخديم وتحميل الملف مع طباعة المسار للتأكد عند حدوث أي أخطاء."""
    file_path = DOWNLOADS_DIR / filename

    print(f"--> Searching for file at: {file_path.absolute()}")

    if not file_path.exists() or not file_path.is_file():
        print(f"--> ERROR: File not found at {file_path.absolute()}")
        raise HTTPException(
            status_code=404,
            detail=f"الملف غير موجود في المسار: {file_path}",
        )

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
    )