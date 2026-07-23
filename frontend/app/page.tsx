'use client';

import { useState } from 'react';

interface Format {
  format_id: string;
  quality: string;
  url: string;
  ext: string;
  type: string;
}

interface VideoInfo {
  title: string;
  thumbnail: string;
  uploader: string;
  formats: Format[];
}

export default function Home() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const [error, setError] = useState('');

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const handleFetchInfo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    setError('');
    setVideoInfo(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/info?url=${encodeURIComponent(url)}`);
      if (!res.ok) {
        throw new Error('تعذر معالجة الرابط، تأكد من صحته ومن دعم المنصة.');
      }
      const data = await res.json();
      setVideoInfo(data);
    } catch (err: any) {
      setError(err.message || 'حدث خطأ أثناء الاتصال بالسيرفر.');
    } finally {
      setLoading(false);
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

        <form onSubmit={handleFetchInfo} className="flex gap-2 mb-6">
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

        {error && (
          <div className="bg-red-500/10 border border-red-500 text-red-400 p-4 rounded-xl text-center mb-6">
            {error}
          </div>
        )}

        {videoInfo && (
          <div className="bg-slate-700/50 p-4 rounded-xl border border-slate-600 space-y-4">
            <div className="flex flex-col sm:flex-row gap-4 items-center">
              {videoInfo.thumbnail && (
                <img
                  src={videoInfo.thumbnail}
                  alt={videoInfo.title}
                  className="w-32 h-24 object-cover rounded-lg"
                />
              )}
              <div className="flex-1 text-center sm:text-right">
                <h3 className="font-semibold text-lg line-clamp-2">{videoInfo.title}</h3>
                {videoInfo.uploader && (
                  <p className="text-slate-400 text-sm mt-1">الناشر: {videoInfo.uploader}</p>
                )}
              </div>
            </div>

            <hr className="border-slate-600" />

            <div>
              <h4 className="font-semibold mb-3 text-indigo-300">اختر الجودة أو التنسيق للتحميل:</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-56 overflow-y-auto">
                {videoInfo.formats.map((fmt, index) => (
                  <a
                    key={index}
                    href={fmt.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    download
                    className="flex justify-between items-center bg-slate-800 hover:bg-indigo-600/30 border border-slate-600 p-3 rounded-lg text-sm transition"
                  >
                    <span>{fmt.quality}</span>
                    <span className="bg-indigo-500 text-xs px-3 py-1 rounded-md font-bold">تحميل</span>
                  </a>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}