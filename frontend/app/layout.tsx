import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { StatusBar } from "@/components/layout/StatusBar";

export const metadata: Metadata = {
    title: "BroCoDDE",
    description: "Content Development Life Cycle Engine",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en" className="h-full">
            <body className="h-full flex flex-col bg-surface-950 text-text-primary font-sans">
                {/* IDE Layout: Sidebar + Main content + Status bar */}
                <div className="flex flex-1 overflow-hidden">
                    <Sidebar />
                    <main className="flex-1 overflow-hidden relative">
                        {children}
                    </main>
                </div>
                <StatusBar />
            </body>
        </html>
    );
}
