import os
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# استدعاء الخدمات المباشرة من مشروعك
from app.services.downloader import download_media, extract_video_info

# --- المسارات والثوابت ---
BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = BASE_DIR / "temp_downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# --- إعداد التطبيق ---
app = FastAPI(
    title="Video Downloader API",
    description="API لجلب ومعالجة فيديوهات وصوتيات منصات التواصل الاجتماعي",
)

# --- إعدادات CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- مخططات الطلبات (Schemas) ---
class VideoRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    download_type: str = "video"  # "video" أو "audio"
    format_id: Optional[str] = "best"
    quality: Optional[str] = "192"
    enhance_mode: Optional[str] = "none"


# --- المسارات (Endpoints) ---
@app.get("/", summary="Health Check")
def home() -> Dict[str, str]:
    """التحقق من حالة الخادم."""
    return {"status": "ok", "message": "API Server Running"}


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


@app.post("/api/download", summary="Direct Media Download")
def start_download(payload: DownloadRequest) -> Dict[str, Any]:
    """تنفيذ التحميل مباشرة دون الاعتماد على Celery أو Redis."""
    try:
        result = download_media(
            url=payload.url,
            download_type=payload.download_type,
            format_id=payload.format_id,
            quality=payload.quality,
            enhance_mode=payload.enhance_mode,
            use_ffmpeg=True,
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@app.get("/api/files/{filename}", summary="Download File")
async def download_file(filename: str) -> FileResponse:
    """تخديم وتحميل الملف مباشرة لجهاز المستخدم عبر Header التنزيل."""
    file_path = DOWNLOADS_DIR / filename

    print(f"--> Searching for file at: {file_path.absolute()}")

    if not file_path.exists() or not file_path.is_file():
        print(f"--> ERROR: File not found at {file_path.absolute()}")
        raise HTTPException(
            status_code=404,
            detail=f"الملف غير موجود على السيرفر: {filename}",
        )

    # إجبار المتصفح على تنزيل الملف بدلاً من عرضه داخل الصفحة
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )