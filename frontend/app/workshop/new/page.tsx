"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { ROLES, INTENTS } from "@/lib/types";
import type { Role, Intent } from "@/lib/types";
import clsx from "clsx";

export default function NewTaskPage() {
    const router = useRouter();
    const [role, setRole] = useState<Role | "">("");
    const [intent, setIntent] = useState<Intent | "">("");
    const [domain, setDomain] = useState("");
    const [creating, setCreating] = useState(false);

    const handleCreate = async () => {
        if (!role || !intent) return;
        setCreating(true);
        try {
            const task = await api.tasks.create({ role, intent, domain: domain || undefined });
            router.push(`/workshop/${task.id}`);
        } catch (e) {
            console.error(e);
            setCreating(false);
        }
    };

    return (
        <div className="h-full overflow-y-auto p-6">
            <div className="max-w-2xl mx-auto">
                <div className="mb-6">
                    <h1 className="text-xl font-medium text-text-primary mb-1">New Task</h1>
                    <p className="text-text-muted text-sm">Choose a role and intent to open a Workshop session.</p>
                </div>

                {/* Role selection */}
                <div className="mb-6">
                    <div className="text-xs font-medium text-text-muted uppercase tracking-wider font-mono mb-3">
                        Role — how are you approaching this content?
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                        {ROLES.map(r => (
                            <button
                                key={r.id}
                                onClick={() => setRole(r.id)}
                                className={clsx(
                                    "panel rounded-lg p-3 text-left transition-all",
                                    role === r.id
                                        ? "border-gold-500/60 bg-gold-500/5"
                                        : "hover:border-border-default"
                                )}
                            >
                                <div className="text-lg mb-1">{r.icon}</div>
                                <div className="text-sm font-medium text-text-primary">{r.name}</div>
                                <div className="text-2xs text-text-muted mt-0.5 leading-tight">{r.description}</div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Intent selection */}
                <div className="mb-6">
                    <div className="text-xs font-medium text-text-muted uppercase tracking-wider font-mono mb-3">
                        Intent — what do you want this content to do?
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                        {INTENTS.map(i => (
                            <button
                                key={i.id}
                                onClick={() => setIntent(i.id)}
                                className={clsx(
                                    "panel rounded-lg p-3 text-left transition-all",
                                    intent === i.id
                                        ? "border-gold-500/60 bg-gold-500/5"
                                        : "hover:border-border-default"
                                )}
                            >
                                <div className="text-sm font-medium text-text-primary">{i.label}</div>
                                <div className="text-2xs text-text-muted mt-0.5">{i.target}</div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Domain (optional) */}
                <div className="mb-8">
                    <label className="text-xs font-medium text-text-muted uppercase tracking-wider font-mono block mb-2">
                        Domain (optional)
                    </label>
                    <input
                        type="text"
                        value={domain}
                        onChange={e => setDomain(e.target.value)}
                        placeholder="e.g., Causal Inference, RL, Decision Science…"
                        className="w-full bg-surface-800 border border-border-default rounded px-3 py-2
                       text-sm text-text-primary placeholder:text-text-muted outline-none
                       focus:border-border-emphasis transition-colors"
                    />
                </div>

                <button
                    onClick={handleCreate}
                    disabled={!role || !intent || creating}
                    className="btn-gold w-full py-3 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed"
                >
                    {creating ? "Opening Workshop…" : "Start Discovery →"}
                </button>
            </div>
        </div>
    );
}
