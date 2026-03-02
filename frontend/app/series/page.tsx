"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { Series, CoddeTask } from "@/lib/types";
import Link from "next/link";
import { Plus, Layers, ChevronDown, ChevronRight, Trash2, Pencil, Check, X, ExternalLink } from "lucide-react";
import clsx from "clsx";

// ── Stage colour helpers ───────────────────────────────────────────────────────

const STAGE_COLORS: Record<string, string> = {
    discovery: "text-blue-400",
    extraction: "text-purple-400",
    structuring: "text-cyan-400",
    drafting: "text-gold-400",
    vetting: "text-orange-400",
    ready: "text-green-400",
    "post-mortem": "text-text-muted",
};

// Series with task list (from GET /series/{id})
interface SeriesDetail extends Series {
    tasks: { id: string; title: string; stage: string }[];
}

// ── Unassigned tasks panel ─────────────────────────────────────────────────────

function UnassignedPanel({
    seriesList,
    onAssigned,
}: {
    seriesList: Series[];
    onAssigned: () => void;
}) {
    const [tasks, setTasks] = useState<CoddeTask[]>([]);
    const [open, setOpen] = useState(false);
    const [assigning, setAssigning] = useState<string | null>(null);

    useEffect(() => {
        if (!open) return;
        api.tasks.list().then(all => {
            setTasks(all.filter(t => !t.series_id && t.stage !== "post-mortem"));
        });
    }, [open]);

    const assign = async (taskId: string, seriesId: string) => {
        setAssigning(taskId);
        await api.series.assignTask(seriesId, taskId);
        setTasks(prev => prev.filter(t => t.id !== taskId));
        setAssigning(null);
        onAssigned();
    };

    return (
        <div className="panel rounded-lg mb-6">
            <button
                onClick={() => setOpen(o => !o)}
                className="w-full flex items-center justify-between px-4 py-3 text-sm text-text-secondary hover:text-text-primary transition-colors"
            >
                <span className="flex items-center gap-2 font-medium">
                    {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    Unassigned tasks
                </span>
                {!open && tasks.length === 0 && (
                    <span className="text-2xs text-text-muted font-mono">click to load</span>
                )}
                {tasks.length > 0 && (
                    <span className="text-2xs text-gold-400 font-mono">{tasks.length} task{tasks.length !== 1 ? "s" : ""}</span>
                )}
            </button>

            {open && (
                <div className="border-t border-border-subtle px-4 pb-3">
                    {tasks.length === 0 ? (
                        <div className="text-xs text-text-muted py-3">All tasks are assigned to a series.</div>
                    ) : (
                        <div className="flex flex-col gap-1.5 mt-3">
                            {tasks.map(t => (
                                <div key={t.id} className="flex items-center justify-between gap-2 py-1">
                                    <div className="min-w-0">
                                        <div className="text-xs text-text-primary truncate">{t.title || "Untitled"}</div>
                                        <div className="text-2xs text-text-muted font-mono">{t.id} · {t.stage}</div>
                                    </div>
                                    <div className="flex items-center gap-1 shrink-0">
                                        <select
                                            className="text-2xs bg-surface-800 border border-border-subtle rounded px-1.5 py-0.5 text-text-secondary outline-none"
                                            defaultValue=""
                                            onChange={e => { if (e.target.value) assign(t.id, e.target.value); }}
                                            disabled={assigning === t.id}
                                        >
                                            <option value="" disabled>Add to series…</option>
                                            {seriesList.map(s => (
                                                <option key={s.id} value={s.id}>{s.icon ? `${s.icon} ` : ""}{s.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

// ── Series card ────────────────────────────────────────────────────────────────

function SeriesCard({
    series,
    onDeleted,
    onUpdated,
}: {
    series: Series;
    onDeleted: (id: string) => void;
    onUpdated: (s: Series) => void;
}) {
    const [detail, setDetail] = useState<SeriesDetail | null>(null);
    const [open, setOpen] = useState(false);
    const [editing, setEditing] = useState(false);
    const [editName, setEditName] = useState(series.name);
    const [editDesc, setEditDesc] = useState(series.description || "");
    const [saving, setSaving] = useState(false);
    const [removing, setRemoving] = useState<string | null>(null);

    const loadDetail = useCallback(async () => {
        const d = await api.series.get(series.id);
        setDetail(d as SeriesDetail);
    }, [series.id]);

    useEffect(() => {
        if (open && !detail) loadDetail();
    }, [open, detail, loadDetail]);

    const save = async () => {
        if (!editName.trim()) return;
        setSaving(true);
        const updated = await api.series.update(series.id, {
            name: editName.trim(),
            description: editDesc.trim() || undefined,
        });
        onUpdated(updated);
        setSaving(false);
        setEditing(false);
    };

    const deleteS = async () => {
        if (!confirm(`Delete series "${series.name}"? Tasks will be unlinked but not deleted.`)) return;
        await api.series.delete(series.id);
        onDeleted(series.id);
    };

    const removeTask = async (taskId: string) => {
        setRemoving(taskId);
        await api.series.removeTask(series.id, taskId);
        setDetail(prev => prev ? { ...prev, tasks: prev.tasks.filter(t => t.id !== taskId) } : prev);
        setRemoving(null);
    };

    return (
        <div className="panel rounded-lg">
            {/* Header */}
            <div className="flex items-start gap-3 px-4 py-3">
                <button
                    onClick={() => setOpen(o => !o)}
                    className="w-8 h-8 rounded bg-gold-500/10 border border-gold-500/20 flex items-center justify-center text-lg shrink-0 mt-0.5 hover:bg-gold-500/15 transition-colors"
                >
                    {series.icon || "📚"}
                </button>

                <div className="flex-1 min-w-0">
                    {editing ? (
                        <div className="flex flex-col gap-1.5">
                            <input
                                value={editName}
                                onChange={e => setEditName(e.target.value)}
                                className="bg-surface-800 border border-border-default rounded px-2 py-1 text-sm text-text-primary outline-none focus:border-border-emphasis w-full"
                                autoFocus
                            />
                            <input
                                value={editDesc}
                                onChange={e => setEditDesc(e.target.value)}
                                placeholder="Description (optional)"
                                className="bg-surface-800 border border-border-default rounded px-2 py-1 text-xs text-text-secondary placeholder:text-text-muted outline-none focus:border-border-emphasis w-full"
                            />
                            <div className="flex gap-1.5">
                                <button onClick={save} disabled={saving} className="btn-gold text-2xs px-2 py-0.5 flex items-center gap-1">
                                    <Check size={10} /> Save
                                </button>
                                <button onClick={() => setEditing(false)} className="btn-ghost text-2xs px-2 py-0.5 flex items-center gap-1">
                                    <X size={10} /> Cancel
                                </button>
                            </div>
                        </div>
                    ) : (
                        <button onClick={() => setOpen(o => !o)} className="text-left w-full">
                            <div className="flex items-center gap-2">
                                {open ? <ChevronDown size={12} className="text-text-muted shrink-0" /> : <ChevronRight size={12} className="text-text-muted shrink-0" />}
                                <span className="text-sm font-medium text-text-primary">{series.name}</span>
                            </div>
                            {series.description && (
                                <div className="text-xs text-text-muted mt-0.5 ml-5">{series.description}</div>
                            )}
                        </button>
                    )}
                </div>

                {/* Actions */}
                {!editing && (
                    <div className="flex items-center gap-1 shrink-0">
                        <button
                            onClick={() => setEditing(true)}
                            className="p-1 text-text-muted hover:text-text-secondary transition-colors"
                            title="Rename"
                        >
                            <Pencil size={12} />
                        </button>
                        <button
                            onClick={deleteS}
                            className="p-1 text-text-muted hover:text-red-400 transition-colors"
                            title="Delete series"
                        >
                            <Trash2 size={12} />
                        </button>
                    </div>
                )}
            </div>

            {/* Progress bar */}
            <div className="px-4 pb-3">
                <div className="flex items-center justify-between mb-1">
                    <span className="text-2xs text-text-muted font-mono">
                        {series.post_count} / {series.target_post_count} posts
                    </span>
                    <span className="text-2xs text-text-muted font-mono">{series.progress_pct.toFixed(0)}%</span>
                </div>
                <div className="h-1 bg-surface-800 rounded overflow-hidden">
                    <div
                        className="h-full bg-gold-500/50 rounded transition-all"
                        style={{ width: `${series.progress_pct}%` }}
                    />
                </div>
            </div>

            {/* Expandable task list */}
            {open && (
                <div className="border-t border-border-subtle px-4 py-3">
                    {!detail ? (
                        <div className="text-xs text-text-muted">Loading…</div>
                    ) : detail.tasks.length === 0 ? (
                        <div className="text-xs text-text-muted">No tasks in this series yet.</div>
                    ) : (
                        <div className="flex flex-col gap-1">
                            {detail.tasks.map(t => (
                                <div key={t.id} className="flex items-center justify-between gap-2 py-0.5 group">
                                    <div className="flex items-center gap-2 min-w-0">
                                        <span className={clsx("text-2xs font-mono shrink-0", STAGE_COLORS[t.stage] || "text-text-muted")}>
                                            {t.stage}
                                        </span>
                                        <span className="text-xs text-text-secondary truncate">{t.title}</span>
                                    </div>
                                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                                        <Link href={`/workshop/${t.id}`} title="Open task">
                                            <ExternalLink size={11} className="text-text-muted hover:text-gold-400 transition-colors" />
                                        </Link>
                                        <button
                                            onClick={() => removeTask(t.id)}
                                            disabled={removing === t.id}
                                            title="Remove from series"
                                            className="text-text-muted hover:text-red-400 transition-colors"
                                        >
                                            <X size={11} />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function SeriesPage() {
    const [series, setSeries] = useState<Series[]>([]);
    const [loading, setLoading] = useState(true);
    const [creating, setCreating] = useState(false);
    const [showForm, setShowForm] = useState(false);
    const [newName, setNewName] = useState("");
    const [newDesc, setNewDesc] = useState("");
    const [newTarget, setNewTarget] = useState("5");

    const reload = useCallback(() => {
        api.series.list().then(s => { setSeries(s); setLoading(false); }).catch(() => setLoading(false));
    }, []);

    useEffect(() => { reload(); }, [reload]);

    const create = async () => {
        if (!newName.trim()) return;
        setCreating(true);
        const s = await api.series.create({
            name: newName.trim(),
            description: newDesc.trim() || undefined,
            target_post_count: parseInt(newTarget) || 5,
        });
        setSeries(prev => [s, ...prev]);
        setNewName(""); setNewDesc(""); setNewTarget("5"); setShowForm(false); setCreating(false);
    };

    return (
        <div className="h-full overflow-y-auto p-6">
            <div className="max-w-3xl mx-auto">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <div className="text-xs text-text-muted font-mono uppercase tracking-wider mb-1">Series</div>
                        <h1 className="text-2xl font-medium text-text-primary">Content Series</h1>
                        <p className="text-xs text-text-muted mt-1">Group related tasks into arcs. Tasks auto-assign when domain matches a series name.</p>
                    </div>
                    <button onClick={() => setShowForm(true)} className="btn-gold flex items-center gap-2">
                        <Plus size={14} />
                        New Series
                    </button>
                </div>

                {/* New Series Form */}
                {showForm && (
                    <div className="panel rounded-lg p-4 mb-6">
                        <div className="flex flex-col gap-2">
                            <input
                                type="text"
                                placeholder="Series name (e.g., World Models in 4 Posts)"
                                value={newName}
                                onChange={e => setNewName(e.target.value)}
                                autoFocus
                                onKeyDown={e => e.key === "Enter" && create()}
                                className="w-full bg-surface-800 border border-border-default rounded px-3 py-2 text-sm
                             text-text-primary placeholder:text-text-muted outline-none focus:border-border-emphasis"
                            />
                            <input
                                type="text"
                                placeholder="Description (optional)"
                                value={newDesc}
                                onChange={e => setNewDesc(e.target.value)}
                                className="w-full bg-surface-800 border border-border-default rounded px-3 py-2 text-sm
                             text-text-primary placeholder:text-text-muted outline-none focus:border-border-emphasis"
                            />
                            <div className="flex items-center gap-2">
                                <label className="text-xs text-text-muted shrink-0">Target posts:</label>
                                <input
                                    type="number"
                                    min={1}
                                    max={20}
                                    value={newTarget}
                                    onChange={e => setNewTarget(e.target.value)}
                                    className="w-16 bg-surface-800 border border-border-default rounded px-2 py-1 text-xs
                                 text-text-primary outline-none focus:border-border-emphasis"
                                />
                            </div>
                        </div>
                        <div className="flex gap-2 justify-end mt-3">
                            <button onClick={() => setShowForm(false)} className="btn-ghost text-xs">Cancel</button>
                            <button onClick={create} disabled={creating} className="btn-gold text-xs">
                                {creating ? "Creating…" : "Create Series"}
                            </button>
                        </div>
                    </div>
                )}

                {loading && <div className="text-text-muted text-sm">Loading…</div>}

                {/* Unassigned tasks panel */}
                {series.length > 0 && (
                    <UnassignedPanel seriesList={series} onAssigned={reload} />
                )}

                {/* Series list */}
                {series.length > 0 ? (
                    <div className="flex flex-col gap-3">
                        {series.map(s => (
                            <SeriesCard
                                key={s.id}
                                series={s}
                                onDeleted={id => setSeries(prev => prev.filter(x => x.id !== id))}
                                onUpdated={updated => setSeries(prev => prev.map(x => x.id === updated.id ? updated : x))}
                            />
                        ))}
                    </div>
                ) : !loading && (
                    <div className="panel rounded-lg p-12 text-center">
                        <Layers size={32} className="text-text-muted mx-auto mb-3" />
                        <div className="text-text-muted text-sm mb-3">No series yet.</div>
                        <div className="text-xs text-text-muted max-w-sm mx-auto">
                            Series let you plan multi-part content arcs. Create one, then tasks with matching domains auto-assign on first chat.
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
