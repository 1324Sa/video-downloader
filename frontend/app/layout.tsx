import type { Metadata } from "next";
import { Geist, Geist_Mono, Cairo, Tajawal, Readex_Pro, Almarai } from "next/font/google";
import "./globals.css";

// --- إعداد الخطوط اللاتينية ---
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// --- إعداد الخطوط العربية ---
const cairo = Cairo({
  subsets: ["arabic"],
  variable: "--font-cairo",
});

const tajawal = Tajawal({
  weight: ["400", "700"],
  subsets: ["arabic"],
  variable: "--font-tajawal",
});

const readex = Readex_Pro({
  subsets: ["arabic"],
  variable: "--font-readex",
});

const almarai = Almarai({
  weight: ["400", "700"],
  subsets: ["arabic"],
  variable: "--font-almarai",
});

// --- البيانات الوصفية (Metadata) ---
export const metadata: Metadata = {
  title: "مُنزل الوسائط - Social Media Downloader",
  description: "تطبيق تحويل وتنزيل الفيديوهات والصوتيات بأعلى جودة",
};

// --- المخطط الرئيسي (Root Layout) ---
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // تجميع كافة متغيرات الخطوط في نص واحد
  const fontVariables = [
    geistSans.variable,
    geistMono.variable,
    cairo.variable,
    tajawal.variable,
    readex.variable,
    almarai.variable,
  ].join(" ");

  return (
    <html
      lang="ar"
      dir="rtl"
      className={`${fontVariables} h-full antialiased`}
    >
      <body className="font-cairo bg-slate-950 text-white min-h-screen flex flex-col">
        {children}
      </body>
    </html>
  );
}