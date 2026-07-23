'use client';

import { useState } from 'react';

export default function Home() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // خيارات التحميل
  const [quality, setQuality] = useState('best');
  const [audioOnly, setAudioOnly] = useState(false);
  const [filterType, setFilterType] = useState('none');

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // دالة التحقق من الرابط
  const handleFetchInfo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    setError('');
    setSuccess('');
    setDownloading(false);

    try {
      const res = await fetch(`${API_BASE_URL}/api/info?url=${encodeURIComponent(url)}`);
      if (!res.ok) {
        throw new Error('تعذر معالجة الرابط، تأكد من صحته ومن دعم المنصة.');
      }
      // لا نحتاج لتخزين المعلومات هنا لأننا سنرسل الخيارات مباشرة للتحميل
      setSuccess('✅ تم التحقق من الرابط بنجاح! اختر الإعدادات واضغط تحميل.');
    } catch (err: any) {
      setError(err.message || 'حدث خطأ أثناء الاتصال بالسيرفر.');
    } finally {
      setLoading(false);
    }
  };

  // دالة التحميل (الزر الأخضر)
  const handleDownload = async () => {
    if (!url) {
      setError('الرجاء إدخال رابط الفيديو أولاً.');
      return;
    }

    setDownloading(true);
    setError('');
    setSuccess('');

    try {
      // إرسال الخيارات إلى الباك إند
      const res = await fetch(`${API_BASE_URL}/api/download`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url,
          quality: quality,
          audio_only: audioOnly,
          filter_type: filterType
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'فشل في تحميل الفيديو.');
      }

      // تحويل الاستجابة إلى Blob لتنزيل الملف مباشرة
      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      
      // محاولة استخراج اسم الملف من الهيدر إذا وجد، أو تعيين اسم افتراضي
      const contentDisposition = res.headers.get('content-disposition');
      let filename = 'video_download.mp4';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }

      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);

      setSuccess('✅ تم التحميل بنجاح!');

    } catch (err: any) {
      setError(err.message || 'حدث خطأ أثناء تحميل الملف.');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-900 text-white flex flex-col items-center justify-center p-4" dir="rtl">
      <div className="max-w-2xl w-full bg-slate-800 p-6 rounded-2xl shadow-xl border border-slate-700">
        <h1 className="text-3xl font-bold text-center mb-2 text-indigo-400">
          مُنزّل الفيديوهات الشامل 🚀
        </h1>
        <p className="text-center text-slate-400 mb-6 text-sm">
          يدعم التحميل من X (تويتر)، YouTube، Instagram، و LinkedIn بدقة عالية وصوت MP3
        </p>

        {/* حقل إدخال الرابط وزر الفحص */}
        <form onSubmit={handleFetchInfo} className="flex gap-2 mb-4">
          <input
            type="url"
            placeholder="ضع رابط الفيديو هنا..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
            className="flex-1 bg-slate-700 text-white px-4 py-3 rounded-xl border border-slate-600 focus:outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-3 rounded-xl transition disabled:opacity-50"
          >
            {loading ? 'جاري الفحص...' : 'فحص الرابط'}
          </button>
        </form>

        {/* رسائل الخطأ والنجاح */}
        {error && (
          <div className="bg-red-500/10 border border-red-500 text-red-400 p-4 rounded-xl text-center mb-4">
            {error}
          </div>
        )}
        {success && (
          <div className="bg-green-500/10 border border-green-500 text-green-400 p-4 rounded-xl text-center mb-4">
            {success}
          </div>
        )}

        {/* منتقيات التحميل (تظهر بعد فحص الرابط بنجاح أو عند وجود الرابط) */}
        {url && !error && (
          <div className="bg-slate-700/50 p-4 rounded-xl border border-slate-600 space-y-4 mt-2">
            <h4 className="font-semibold mb-2 text-indigo-300">إعدادات التحميل:</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* منتقي الدقة */}
              <div>
                <label className="block text-sm text-slate-300 mb-1">جودة الفيديو:</label>
                <select 
                  value={quality} 
                  onChange={(e) => setQuality(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-600 text-white p-2 rounded-lg"
                >
                  <option value="best">أعلى جودة متاحة (Best)</option>
                  <option value="1080p">1080p (FHD)</option>
                  <option value="720p">720p (HD)</option>
                  <option value="480p">480p</option>
                  <option value="360p">360p</option>
                </select>
              </div>

              {/* منتقي الصوت / الفلتر */}
              <div>
                <label className="block text-sm text-slate-300 mb-1">فلتر المعالجة:</label>
                <select 
                  value={filterType} 
                  onChange={(e) => setFilterType(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-600 text-white p-2 rounded-lg"
                >
                  <option value="none">بدون فلتر</option>
                  <option value="blur">تضبيش الخلفية (Blur)</option>
                  <option value="grayscale">أبيض وأسود</option>
                </select>
              </div>
            </div>

            {/* خيار الصوت فقط */}
            <div className="flex items-center gap-3">
              <input 
                type="checkbox" 
                id="audioOnly" 
                checked={audioOnly} 
                onChange={(e) => setAudioOnly(e.target.checked)}
                className="w-5 h-5 text-indigo-600 bg-slate-700 border-slate-600 rounded focus:ring-indigo-500"
              />
              <label htmlFor="audioOnly" className="text-sm text-slate-300 cursor-pointer">
                تحميل كصوت فقط (MP3)
              </label>
            </div>

            {/* زر التحميل الأخضر مع الأيقونة */}
            <button
              onClick={handleDownload}
              disabled={downloading}
              className="w-full flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-full transition duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-green-900/20"
            >
              {downloading ? (
                <>جاري التحميل...</>
              ) : (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v3.586L7.707 9.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 10.586V7z" clipRule="evenodd" />
                  </svg>
                  تحميل الفيديو الآن
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </main>
  );
}