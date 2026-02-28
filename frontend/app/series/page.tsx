"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Series } from "@/lib/types";
import Link from "next/link";
import { Plus, Layers } from "lucide-react";

export default function SeriesPage() {
    const [series, setSeries] = useState<Series[]>([]);
    const [loading, setLoading] = useState(true);
    const [creating, setCreating] = useState(false);
    const [newName, setNewName] = useState("");
    const [newDesc, setNewDesc] = useState("");
    const [showForm, setShowForm] = useState(false);

    useEffect(() => {
        api.series.list().then(s => { setSeries(s); setLoading(false); }).catch(() => setLoading(false));
    }, []);

    const create = async () => {
        if (!newName.trim()) return;
        setCreating(true);
        const s = await api.series.create({ name: newName.trim(), description: newDesc.trim() || undefined });
        setSeries(prev => [s, ...prev]);
        setNewName(""); setNewDesc(""); setShowForm(false); setCreating(false);
    };

    return (
        <div className="h-full overflow-y-auto p-6">
            <div className="max-w-4xl mx-auto">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <div className="text-xs text-text-muted font-mono uppercase tracking-wider mb-1">Series</div>
                        <h1 className="text-2xl font-medium text-text-primary">Content Series</h1>
                    </div>
                    <button onClick={() => setShowForm(true)} className="btn-gold flex items-center gap-2">
                        <Plus size={14} />
                        New Series
                    </button>
                </div>

                {/* New Series Form */}
                {showForm && (
                    <div className="panel rounded-lg p-4 mb-6 animate-fade-in">
                        <input
                            type="text"
                            placeholder="Series name (e.g., Causal Discovery in 4 Posts)"
                            value={newName}
                            onChange={e => setNewName(e.target.value)}
                            className="w-full bg-surface-800 border border-border-default rounded px-3 py-2 text-sm
                         text-text-primary placeholder:text-text-muted outline-none focus:border-border-emphasis mb-2"
                        />
                        <input
                            type="text"
                            placeholder="Description (optional)"
                            value={newDesc}
                            onChange={e => setNewDesc(e.target.value)}
                            className="w-full bg-surface-800 border border-border-default rounded px-3 py-2 text-sm
                         text-text-primary placeholder:text-text-muted outline-none focus:border-border-emphasis mb-3"
                        />
                        <div className="flex gap-2 justify-end">
                            <button onClick={() => setShowForm(false)} className="btn-ghost text-xs">Cancel</button>
                            <button onClick={create} disabled={creating} className="btn-gold text-xs">
                                {creating ? "Creating…" : "Create Series"}
                            </button>
                        </div>
                    </div>
                )}

                {loading && <div className="text-text-muted text-sm">Loading…</div>}

                {/* Series grid */}
                {series.length > 0 ? (
                    <div className="flex flex-col gap-3">
                        {series.map(s => (
                            <div key={s.id} className="panel rounded-lg p-4">
                                <div className="flex items-start justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded bg-gold-500/10 border border-gold-500/20 flex items-center justify-center text-lg">
                                            {s.icon || "📚"}
                                        </div>
                                        <div>
                                            <div className="text-base font-medium text-text-primary">{s.name}</div>
                                            {s.description && (
                                                <div className="text-xs text-text-muted mt-0.5">{s.description}</div>
                                            )}
                                        </div>
                                    </div>
                                    <Link href={`/queue?series=${s.id}`} className="btn-ghost text-xs shrink-0">
                                        View posts
                                    </Link>
                                </div>

                                {/* Progress bar */}
                                <div className="mt-4">
                                    <div className="flex items-center justify-between mb-1.5">
                                        <span className="text-2xs text-text-muted font-mono">
                                            {s.post_count} / {s.target_post_count} posts
                                        </span>
                                        <span className="text-2xs text-text-muted font-mono">{s.progress_pct.toFixed(0)}%</span>
                                    </div>
                                    <div className="h-1.5 bg-surface-800 rounded overflow-hidden">
                                        <div
                                            className="h-full bg-gold-500/60 rounded transition-all"
                                            style={{ width: `${s.progress_pct}%` }}
                                        />
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : !loading && (
                    <div className="panel rounded-lg p-12 text-center">
                        <Layers size={32} className="text-text-muted mx-auto mb-3" />
                        <div className="text-text-muted text-sm mb-3">No series yet.</div>
                        <div className="text-xs text-text-muted max-w-sm mx-auto">
                            Series let you plan multi-part content arcs — like "Causal Discovery in 4 Posts" or "The Pracha Bridge."
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
