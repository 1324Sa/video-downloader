import yt_dlp

def download_video(url, quality='best', audio_only=False, filter_type='none'):
    """
    تحميل الفيديو مع الخيارات المطلوبة
    """
    ydl_opts = {
        'outtmpl': 'temp_downloads/%(title)s.%(ext)s',
        'format': 'bestvideo+bestaudio/best' if not audio_only else 'bestaudio',
        'merge_output_format': 'mp4'
    }

    # 1. خيارات الدقة (منتقي الدقة)
    if quality == '1080p':
        ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
    elif quality == '720p':
        ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
    elif quality == '480p':
        ydl_opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
    
    # 2. خيار الصوت فقط (منتقي صوتي)
    if audio_only:
        ydl_opts['format'] = 'bestaudio'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    
    # 3. خيار الفلتر (هذا يعتمد على كيفية تنفيذك للفلتر، مثلاً إضافة text watermark)
    if filter_type != 'none':
        # يمكنك هنا استخدام ffmpeg-python لإضافة نص أو تأثير على الفيديو قبل حفظه
        # مثال: ydl_opts['postprocessors'].append(...)
        pass

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        
    return filename