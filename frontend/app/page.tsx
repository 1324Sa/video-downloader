'use client';

import React, { useState, useEffect } from 'react';
import { 
  Video, 
  Download, 
  Music, 
  Film, 
  Sparkles, 
  Loader2, 
  Type, 
  AlertCircle,
  CheckCircle2 
} from 'lucide-react';

interface VideoFormat {
  format_id: string;
  resolution: string;
  height?: number;
  ext?: string;
  format_note?: string;
}

interface VideoInfoData {
  title: string;
  thumbnail?: string;
  extractor_key?: string;
  extractor?: string;
  platform?: string;
  video_formats?: VideoFormat[];
  formats?: VideoFormat[];
}

export default function Home() {
  const [url, setUrl] = useState('');
  const [loadingInfo, setLoadingInfo] = useState(false);
  const [videoInfo, setVideoInfo] = useState<VideoInfoData | null>(null);
  
  // خيارات التنزيل
  const [downloadType, setDownloadType] = useState<'video' | 'audio'>('video');
  const [selectedFormat, setSelectedFormat] = useState('best');
  const [selectedQuality, setSelectedQuality] = useState('192');
  const [enhanceMode, setEnhanceMode] = useState('none');
  
  // التحكم بالخط والواجهة
  const [selectedFont, setSelectedFont] = useState('var(--font-cairo)');
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [downloadLink, setDownloadLink] = useState('');
  const [isCompleted, setIsCompleted] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // 1. جلب وفحص معلومات الفيديو
  const handleFetchInfo = async () => {
    if (!url.trim()) return;
    setLoadingInfo(true);
    setErrorMessage('');
    setVideoInfo(null);
    setIsCompleted(false);

    try {
      const res = await fetch('http://localhost:8000/api/fetch-info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      const result = await res.json();

      if (res.ok) {
        const data: VideoInfoData = result.data || result;
        setVideoInfo(data);

        const availableFormats = data.video_formats || data.formats || [];
        if (availableFormats.length > 0) {
          setSelectedFormat(String(availableFormats[0].height || availableFormats[0].format_id));
        } else {
          setSelectedFormat('best');
        }
      } else {
        setErrorMessage(result.detail || result.error || 'فشلت عملية جلب معلومات الفيديو');
      }
    } catch {
      setErrorMessage('تعذر الاتصال بالسيرفر، تأكد من تشغيل Uvicorn');
    } finally {
      setLoadingInfo(false);
    }
  };

  // 2. تتبع نسبة التحميل لحظياً (Polling)
  const pollTaskStatus = async (taskId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/status/${taskId}`);
      const data = await res.json();

      if (data.status === 'processing' || data.status === 'downloading') {
        setDownloadProgress(data.progress || 0);
        setStatusMessage(data.message || 'جاري التحميل والمعالجة...');
        setTimeout(() => pollTaskStatus(taskId), 1000);
      } else if (data.status === 'completed' || data.status === 'SUCCESS') {
        setDownloadProgress(100);
        setIsDownloading(false);
        setIsCompleted(true);
        const rawPath = data.result?.file_path || data.file_path || data.filename || '';
        const fileName = rawPath.split('\\').pop()?.split('/').pop() || '';
        setDownloadLink(`http://localhost:8000/api/files/${fileName}`);
      } else if (data.status === 'failed' || data.status === 'ERROR') {
        setIsDownloading(false);
        setErrorMessage(data.error || 'فشلت عملية التنزيل في السيرفر');
      } else {
        setTimeout(() => pollTaskStatus(taskId), 1000);
      }
    } catch {
      setIsDownloading(false);
      setErrorMessage('حدث خطأ أثناء تتبع حالة التحميل');
    }
  };

  // 3. إرسال طلب التنزيل
  const handleStartDownload = async () => {
    setIsDownloading(true);
    setDownloadProgress(0);
    setStatusMessage('جاري بدء التحميل...');
    setIsCompleted(false);
    setErrorMessage('');

    try {
      const res = await fetch('http://localhost:8000/api/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          download_type: downloadType,
          format_id: selectedFormat,
          quality: selectedQuality,
          enhance_mode: enhanceMode
        })
      });
      const data = await res.json();

      if (res.ok && data.task_id) {
        pollTaskStatus(data.task_id);
      } else {
        setIsDownloading(false);
        setErrorMessage(data.detail || 'تعذر بدء المهمة في السيرفر');
      }
    } catch {
      setIsDownloading(false);
      setErrorMessage('فشل الاتصال بالسيرفر لبدء التحميل');
    }
  };

  const formatsList = videoInfo?.video_formats || videoInfo?.formats || [];

  return (
    <div 
      style={{ fontFamily: selectedFont }} 
      className="min-h-screen bg-[#0d111d] text-white py-8 px-4 flex flex-col items-center justify-start space-y-4"
      dir="rtl"
    >
      {/* منتقي خط الواجهة */}
      <div className="w-full max-w-xl bg-[#171e31] border border-slate-800/80 rounded-xl p-3 flex justify-between items-center text-xs">
        <div className="flex items-center gap-2 text-indigo-400 font-medium">
          <Type className="w-4 h-4" />
          <span>اختر خط الواجهة:</span>
        </div>
        <select
          value={selectedFont}
          onChange={(e) => setSelectedFont(e.target.value)}
          className="bg-[#0d111d] text-slate-200 border border-slate-700/60 rounded-lg px-3 py-1.5 outline-none cursor-pointer"
        >
          <option value="var(--font-cairo)">خط كايـرو (Cairo)</option>
          <option value="var(--font-tajawal)">خط تجـوّل (Tajawal)</option>
          <option value="var(--font-readex)">خط ريـدكس (Readex Pro)</option>
          <option value="var(--font-almarai)">خط المـراعي (Almarai)</option>
        </select>
      </div>

      {/* الكارت الرئيسي */}
      <div className="w-full max-w-xl bg-[#171e31] border border-slate-800/80 rounded-2xl p-6 shadow-2xl space-y-5">
        
        {/* عنوان الصفحة */}
        <div className="flex items-center justify-center gap-2.5 text-center">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            مُحمل الميديا الذكي
          </h1>
          <Video className="w-7 h-7 text-indigo-400" />
        </div>

        {/* حقل إدخال الرابط وزر الفحص */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleFetchInfo}
            disabled={loadingInfo || !url.trim()}
            className="bg-[#5842f6] hover:bg-[#4833e3] disabled:opacity-50 text-white text-xs font-semibold px-5 py-3 rounded-xl flex items-center justify-center gap-2 transition-all shrink-0 cursor-pointer"
          >
            {loadingInfo ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              'فحص الرابط'
            )}
          </button>
          <input
            type="text"
            placeholder="أدخل رابط الفيديو (YouTube, Shorts...)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="flex-1 bg-[#0a0d16] border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-left dir-ltr"
          />
        </div>

        {/* عرض رسائل الخطأ */}
        {errorMessage && (
          <div className="bg-[#2a131f] border border-red-500/30 text-red-400 p-3 rounded-xl flex items-center gap-2 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* بطاقة معلومات الفيديو والخيارات */}
        {videoInfo && (
          <div className="space-y-5 pt-1">
            
            {/* المعاينة */}
            <div className="flex gap-3 bg-[#0d111d] p-3 rounded-xl border border-slate-800 items-center">
              {videoInfo.thumbnail && (
                <img 
                  src={videoInfo.thumbnail} 
                  alt={videoInfo.title} 
                  className="w-24 h-16 object-cover rounded-lg shrink-0 border border-slate-800"
                />
              )}
              <div className="space-y-1 overflow-hidden text-right flex-1">
                <h3 className="font-semibold text-xs line-clamp-2 text-slate-200">
                  {videoInfo.title}
                </h3>
                <p className="text-[11px] text-slate-400">
                  المنصة: <span className="text-slate-300">{videoInfo.extractor_key || videoInfo.extractor || videoInfo.platform || 'YouTube'}</span>
                </p>
              </div>
            </div>

            {/* 1. نوع التنزيل */}
            <div className="space-y-2">
              <div className="flex justify-start text-[11px] text-slate-400 items-center gap-1">
                <span>نوع التنزيل:</span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setDownloadType('video')}
                  className={`py-2.5 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer ${
                    downloadType === 'video'
                      ? 'bg-[#5842f6] text-white shadow-lg'
                      : 'bg-[#0d111d] text-slate-400 border border-slate-800/80'
                  }`}
                >
                  <Film className="w-3.5 h-3.5" />
                  فيديو وصوت
                </button>
                <button
                  type="button"
                  onClick={() => setDownloadType('audio')}
                  className={`py-2.5 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer ${
                    downloadType === 'audio'
                      ? 'bg-[#5842f6] text-white shadow-lg'
                      : 'bg-[#0d111d] text-slate-400 border border-slate-800/80'
                  }`}
                >
                  <Music className="w-3.5 h-3.5" />
                  صوت فقط (MP3)
                </button>
              </div>
            </div>

            {/* 2. الدقة / الجودة */}
            {downloadType === 'video' ? (
              <div className="space-y-1.5 text-right">
                <label className="text-[11px] text-slate-400 block">اختر دقة الفيديو:</label>
                <select
                  value={selectedFormat}
                  onChange={(e) => setSelectedFormat(e.target.value)}
                  className="w-full bg-[#0d111d] border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 outline-none text-center cursor-pointer"
                >
                  <option value="best">أعلى دقة متاحة تلقائياً (Best Resolution)</option>
                  {formatsList.map((fmt, idx) => (
                    <option key={idx} value={fmt.height || fmt.format_id}>
                      {fmt.resolution || `${fmt.height}p` || fmt.format_note} ({fmt.ext || 'mp4'})
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div className="space-y-1.5 text-right">
                <label className="text-[11px] text-slate-400 block">اختر جودة الصوت (Bitrate):</label>
                <select
                  value={selectedQuality}
                  onChange={(e) => setSelectedQuality(e.target.value)}
                  className="w-full bg-[#0d111d] border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 outline-none text-center cursor-pointer"
                >
                  <option value="320">320 kbps (جودة فائقة - MP3)</option>
                  <option value="192">192 kbps (جودة عالية - موصى بها)</option>
                  <option value="128">128 kbps (جودة قياسية)</option>
                </select>
              </div>
            )}

            {/* 3. معالجة الفيديو */}
            <div className="space-y-1.5 text-right">
              <label className="text-[11px] text-slate-400 flex items-center justify-start gap-1">
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                <span>تحسين ومعالجة الفيديو (اختياري):</span>
              </label>
              <select
                value={enhanceMode}
                onChange={(e) => setEnhanceMode(e.target.value)}
                className="w-full bg-[#0d111d] border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 outline-none text-center cursor-pointer"
              >
                <option value="none">بدون تحسين (الحفاظ على الملف الأصلي)</option>
                <option value="denoise">إزالة الضوضاء وتحسين الوضوح (Denoise)</option>
                <option value="color_boost">تعزيز الألوان والإضاءة (Color Boost)</option>
              </select>
            </div>

            {/* زر البدء */}
            <button
              onClick={handleStartDownload}
              disabled={isDownloading}
              className="w-full bg-[#05a863] hover:bg-[#049356] disabled:opacity-50 text-white text-xs font-bold py-3 rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg cursor-pointer"
            >
              {isDownloading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  جاري التحميل والمعالجة...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  بدء التحميل الآن
                </>
              )}
            </button>

            {/* شريط التقدم */}
            {isDownloading && (
              <div className="bg-[#0d111d] border border-slate-800/80 p-3.5 rounded-xl space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-indigo-400 font-medium flex items-center gap-1.5">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    {statusMessage || 'جاري التحميل...'}
                  </span>
                  <span className="text-[#05a863] font-bold">{downloadProgress}%</span>
                </div>
                <div className="w-full bg-[#171e31] h-2 rounded-full overflow-hidden p-0.5 border border-slate-800">
                  <div
                    className="bg-[#05a863] h-full rounded-full transition-all duration-300"
                    style={{ width: `${downloadProgress}%` }}
                  />
                </div>
              </div>
            )}

          </div>
        )}

      </div>

      {/* كارت اكتمال التحميل */}
      {isCompleted && (
        <div className="w-full max-w-xl bg-[#0f2128] border border-emerald-500/30 p-6 rounded-2xl text-center space-y-4 shadow-2xl">
          <p className="text-slate-300 text-xs font-semibold">اكتمل التجهيز بنجاح!</p>
          
          <div className="w-10 h-10 rounded-full border-2 border-[#05a863] bg-[#05a863]/10 flex items-center justify-center mx-auto text-[#05a863]">
            <CheckCircle2 className="w-6 h-6" />
          </div>

          <p className="text-[#05a863] text-xs font-bold">الملف جاهز للتنزيل!</p>

          <a
            href={downloadLink}
            download
            className="inline-flex items-center gap-2 bg-[#05a863] hover:bg-[#049356] text-white text-xs font-bold px-6 py-2.5 rounded-xl transition-all shadow-lg"
          >
            <Download className="w-4 h-4" />
            حفظ الملف على جهازك
          </a>
        </div>
      )}

    </div>
  );
}