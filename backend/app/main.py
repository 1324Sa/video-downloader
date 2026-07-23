from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Social Media Video Downloader API is running"}

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