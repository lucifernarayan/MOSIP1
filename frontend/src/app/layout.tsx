import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/AppShell";

export const metadata: Metadata = {
  title: "MOSIP — Orbital Intelligence Platform",
  description:
    "Multi-Agent Orbital Sustainability Intelligence Platform. Real-time satellite tracking, collision risk assessment, and regulatory compliance analysis.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
