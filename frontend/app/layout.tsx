import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ASX Announcements - AI-Powered Market Insights",
  description: "Track and analyze ASX price-sensitive company announcements with AI-powered insights",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
