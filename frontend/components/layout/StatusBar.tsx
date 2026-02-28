"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export function StatusBar() {
    const [provider, setProvider] = useState<string>("…");
    const [mockMode, setMockMode] = useState(false);
    const time = new Date().toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit" });

    useEffect(() => {
        api.health().then(h => {
            setProvider(h.provider);
            setMockMode(h.mock_mode);
        }).catch(() => setProvider("offline"));
    }, []);

    return (
        <div className="h-6 bg-surface-950 border-t border-border-subtle flex items-center px-3
                    text-2xs font-mono text-text-muted gap-4 shrink-0">
            <span className="text-gold-400 font-medium">BroCoDDE</span>
            <div className="flex items-center gap-1.5">
                <div className={`w-1.5 h-1.5 rounded-full ${provider === "offline" ? "bg-red-500" : mockMode ? "bg-amber-500" : "bg-green-500"}`} />
                <span>{mockMode ? "mock-mode" : provider}</span>
            </div>
            <span className="flex-1" />
            <span>{time}</span>
        </div>
    );
}
