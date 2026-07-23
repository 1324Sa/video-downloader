import os
import shutil
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

# إعدادات CORS للسماح للـ Frontend بالتواصل مع الـ Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # يمكنك تحديد النطاق الخاص بـ Vercel هنا لمزيد من الأمان
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# مجلد مؤقت لتنزيل الملفات
DOWNLOAD_FOLDER = "temp_downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# ------------------------------------------------------------------
# 1. المسار الأساسي للفحص (Check)
# ------------------------------------------------------------------
@app.get("/")
def home():
    return {"message": "Social Media Video Downloader API is running"}

# ------------------------------------------------------------------
# 2. مسار معلومات الفيديو (الذي أرسلته)
# ------------------------------------------------------------------
@app.get("/api/info")
def get_video_info(url: str = Query(..., description="رابط الفيديو")):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = []
            if 'formats' in info:
                for f in info['formats']:
                    # فلترة الروابط التي تحتوي على فيديو وصوت أو روابط تنزيل مباشرة
                    if f.get('url') and (f.get('vcodec') != 'none' or f.get('acodec') != 'none'):
                        res = f.get('format_note') or f.get('resolution') or f"{f.get('height', 'SD')}p"
                        ext = f.get('ext', 'mp4')
                        is_audio = f.get('vcodec') == 'none'
                        
                        formats.append({
                            'format_id': f.get('format_id'),
                            'quality': f"🎵 صوت فقط (MP3/M4A)" if is_audio else f"🎬 {res} ({ext})",
                            'url': f.get('url'),
                            'ext': ext,
                            'type': 'audio' if is_audio else 'video'
                        })
            
            # إزالة التكرار
            unique_formats = list({f['quality']: f for f in formats}.values())

            return {
                "title": info.get('title', 'Video'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration'),
                "uploader": info.get('uploader'),
                "formats": unique_formats
            }
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"تعذر جلب معلومات الفيديو: {str(e)}")

# ------------------------------------------------------------------
# 3. نموذج البيانات لمسار التحميل (Download)
# ------------------------------------------------------------------
class DownloadRequest(BaseModel):
    url: str
    quality: str = "best"
    audio_only: bool = False
    filter_type: str = "none"

# ------------------------------------------------------------------
# 4. مسار التحميل (الذي طلبته في الواجهة الجديدة)
# ------------------------------------------------------------------
@app.post("/api/download")
async def download_video(request: DownloadRequest):
    try:
        # تحضير خيارات yt-dlp بناءً على طلب المستخدم
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }

        # 1. اختيار الجودة
        if request.quality == '1080p':
            ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
        elif request.quality == '720p':
            ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
        elif request.quality == '480p':
            ydl_opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
        elif request.quality == '360p':
            ydl_opts['format'] = 'bestvideo[height<=360]+bestaudio/best[height<=360]'
        else:
            ydl_opts['format'] = 'bestvideo+bestaudio/best'  # أعلى جودة

        # 2. التحقق من الصوت فقط (MP3)
        if request.audio_only:
            ydl_opts['format'] = 'bestaudio'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        # 3. الفلاتر (تطبيق بسيط، يمكنك التوسع فيه لاحقاً)
        # ملاحظة: تطبيق الفلاتر يتطلب ffmpeg-python وتعديلاً معقداً
        # إذا اخترت فلتر، سنقوم بتحميله ثم معالجته (احتياطي)
        postprocessors = []
        
        if request.filter_type != 'none' and not request.audio_only:
            # مثال على فلتر التضبيش (Blur) أو تدرج الرمادي
            # يجب كتابة كود ffmpeg هنا لمعالجة الفيديو بعد تحميله
            # نضع هذا الكود كمثال مستقبلي، حالياً سنقوم بالتحميل العادي
            pass

        # تنفيذ التحميل
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            filename = ydl.prepare_filename(info)

            # تعديل اسم الملف إذا كان صوتاً (لأنه سيصبح mp3 بدلاً من m4a/webm)
            if request.audio_only:
                filename = os.path.splitext(filename)[0] + '.mp3'

        # التأكد من وجود الملف
        if not os.path.exists(filename):
            raise HTTPException(status_code=500, detail="فشل في إنشاء ملف التحميل.")

        # إعادة الملف للمستخدم (يمكنك إضافة حذف الملف بعد الإرسال لاحقاً)
        return FileResponse(
            path=filename, 
            media_type='video/mp4' if not request.audio_only else 'audio/mpeg', 
            filename=os.path.basename(filename)
        )

    except Exception as e:
        # تنظيف الملفات في حال حدوث خطأ
        raise HTTPException(status_code=400, detail=f"حدث خطأ أثناء التحميل: {str(e)}")

# ------------------------------------------------------------------
# 5. (اختياري) دالة لحذف الملفات القديمة بعد التحميل لتنظيف السيرفر
# ------------------------------------------------------------------
import threading
import time

def delete_file_after_delay(file_path, delay=60):
    """حذف الملف بعد مدة زمنية محددة لتوفير مساحة السيرفر"""
    def delete():
        time.sleep(delay)
        if os.path.exists(file_path):
            os.remove(file_path)
    threading.Thread(target=delete).start()