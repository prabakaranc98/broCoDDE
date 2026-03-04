"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { ROLES, INTENTS } from "@/lib/types";
import type { Role, Intent } from "@/lib/types";
import clsx from "clsx";

type Mode = "deep" | "spark";

function NewTaskForm() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [mode, setMode] = useState<Mode>("deep");

    // Deep mode fields
    const [role, setRole] = useState<Role | "">("");
    const [intent, setIntent] = useState<Intent | "">("");
    const [domain, setDomain] = useState("");

    // Spark mode fields
    const [sourceUrl, setSourceUrl] = useState("");
    const [sparkDomain, setSparkDomain] = useState("");

    const [creating, setCreating] = useState(false);

    // Pre-fill from dashboard "Start Spark" links (?mode=spark&url=...)
    useEffect(() => {
        const modeParam = searchParams.get("mode");
        const urlParam = searchParams.get("url");
        if (modeParam === "spark") {
            setMode("spark");
            if (urlParam) setSourceUrl(urlParam);
        }
    }, [searchParams]);

    const canCreate = mode === "deep" ? (!!role && !!intent) : true;

    const handleCreate = async () => {
        if (!canCreate) return;
        setCreating(true);
        try {
            let task;
            if (mode === "spark") {
                task = await api.tasks.create({
                    task_type: "spark",
                    source_url: sourceUrl.trim() || undefined,
                    domain: sparkDomain.trim() || undefined,
                    role: "researcher",
                    intent: "teach",
                });
            } else {
                task = await api.tasks.create({
                    role: role as Role,
                    intent: intent as Intent,
                    domain: domain.trim() || undefined,
                    task_type: "deep",
                });
            }
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
                    <h1 className="text-xl font-medium text-text-primary mb-1">New Session</h1>
                    <p className="text-text-muted text-sm">Choose a mode to start your session.</p>
                </div>

                {/* Mode toggle */}
                <div className="flex gap-2 mb-8 p-1 bg-surface-800 rounded-lg border border-border-subtle w-fit">
                    {(["deep", "spark"] as Mode[]).map(m => (
                        <button
                            key={m}
                            onClick={() => setMode(m)}
                            className={clsx(
                                "px-5 py-2 rounded-md text-sm font-medium transition-all",
                                mode === m
                                    ? "bg-gold-500/20 text-text-primary border border-gold-500/40"
                                    : "text-text-muted hover:text-text-secondary"
                            )}
                        >
                            {m === "deep" ? "Deep Mode" : "⚡ Spark"}
                        </button>
                    ))}
                </div>

                {mode === "deep" ? (
                    <>
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
                    </>
                ) : (
                    <>
                        {/* Spark mode — minimal form */}
                        <div className="mb-4 p-4 bg-surface-800 border border-border-subtle rounded-lg">
                            <p className="text-sm text-text-secondary leading-relaxed">
                                Spark sessions use the Feynman technique — you explain a paper or idea,
                                the agent probes your understanding. Concepts are auto-saved to your knowledge graph.
                                Publishing is optional and user-driven.
                            </p>
                        </div>

                        <div className="mb-6">
                            <label className="text-xs font-medium text-text-muted uppercase tracking-wider font-mono block mb-2">
                                Source URL (optional)
                            </label>
                            <input
                                type="url"
                                value={sourceUrl}
                                onChange={e => setSourceUrl(e.target.value)}
                                placeholder="Paste a paper URL, arxiv link, or article — or leave blank to start raw"
                                className="w-full bg-surface-800 border border-border-default rounded px-3 py-2
                                   text-sm text-text-primary placeholder:text-text-muted outline-none
                                   focus:border-border-emphasis transition-colors"
                            />
                        </div>

                        <div className="mb-8">
                            <label className="text-xs font-medium text-text-muted uppercase tracking-wider font-mono block mb-2">
                                Domain (optional)
                            </label>
                            <input
                                type="text"
                                value={sparkDomain}
                                onChange={e => setSparkDomain(e.target.value)}
                                placeholder="e.g., Cognitive Science, Machine Learning…"
                                className="w-full bg-surface-800 border border-border-default rounded px-3 py-2
                                   text-sm text-text-primary placeholder:text-text-muted outline-none
                                   focus:border-border-emphasis transition-colors"
                            />
                        </div>
                    </>
                )}

                <button
                    onClick={handleCreate}
                    disabled={!canCreate || creating}
                    className="btn-gold w-full py-3 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed"
                >
                    {creating
                        ? (mode === "spark" ? "Starting session…" : "Opening Workshop…")
                        : (mode === "spark" ? "Start Learning →" : "Start Discovery →")}
                </button>
            </div>
        </div>
    );
}

export default function NewTaskPage() {
    return (
        <Suspense fallback={<div className="p-6 text-sm text-text-muted">Loading…</div>}>
            <NewTaskForm />
        </Suspense>
    );
}
