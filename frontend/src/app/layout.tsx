import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "智能办公Agent",
  description: "全模态AI办公助手",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
