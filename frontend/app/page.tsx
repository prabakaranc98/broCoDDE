import Link from "next/link";
import { ChevronRight, TrendingUp } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchSafe<T>(path: string, fallback: T): Promise<T> {
    try {
        const res = await fetch(`${API}${path}`, { next: { revalidate: 30 } });
        if (!res.ok) return fallback;
        return res.json();
    } catch { return fallback; }
}

export default async function DashboardPage() {
    const [tasks, observatory] = await Promise.all([
        fetchSafe<{ id: string; title: string | null; stage: string; role: string | null; stage_label?: string; lint_results?: Record<string, { pass: boolean }> | null; archetype?: string | null }[]>("/tasks?limit=20", []),
        fetchSafe<{ total_posts: number; avg_save_rate: number; avg_impressions: number; best_archetype?: string | null; posts: { task_id: string; title: string; impressions: number; saves: number; save_rate: number; comments: number; published_at?: string }[] }>("/observatory", { total_posts: 0, avg_save_rate: 0, avg_impressions: 0, posts: [] }),
    ]);

    const ready = tasks.filter(t => t.stage === "ready");
    const inProgress = tasks.filter(t => !["ready", "post-mortem"].includes(t.stage));
    const recentPerformance = observatory.posts.slice(0, 2);
    const totalSaves = observatory.posts.reduce((s, p) => s + p.saves, 0);

    const LINT_LABELS = [
        { key: "opening_strength", label: "Opening Strength" },
        { key: "micro_learning", label: "Teaches Something" },
        { key: "credential_stating", label: "Credential Stating" },
        { key: "rant_detection", label: "Rant Detection" },
    ];

    return (
        <div className="h-full overflow-y-auto p-6">
            <div className="max-w-5xl mx-auto">
                {/* Hero */}
                <div className="flex items-start justify-between mb-6">
                    <div>
                        <div className="text-xs text-text-muted font-mono uppercase tracking-wider mb-1">Content IDE</div>
                        <h1 className="text-3xl font-medium text-text-primary mb-1">BroCoDDE</h1>
                        <p className="text-text-muted text-sm">
                            {inProgress.length > 0 ? `${inProgress.length} task${inProgress.length > 1 ? "s" : ""} in progress` : "Ready for a new session."}
                            {ready.length > 0 && ` · ${ready.length} in queue`}
                        </p>
                    </div>
                    <Link href="/workshop/new" className="btn-gold flex items-center gap-2 text-sm px-5 py-2.5">
                        + New CoDDE-Task
                    </Link>
                </div>

                {/* Stats Row */}
                <div className="grid grid-cols-4 gap-3 mb-6">
                    <StatCard label="Total Saves" value={totalSaves > 0 ? totalSaves.toLocaleString() : "—"} sub={`${(observatory.avg_save_rate * 100).toFixed(1)}% avg rate`} />
                    <StatCard label="Total Posts" value={observatory.total_posts > 0 ? String(observatory.total_posts) : "—"} sub={`${tasks.filter(t => t.stage !== "post-mortem").length} active series`} />
                    <StatCard label="Top Archetype" value={observatory.best_archetype || "—"} sub="Highest save rate" large={false} />
                    <StatCard label="Queue" value={ready.length > 0 ? String(ready.length) : "—"} sub="Ready to publish" />
                </div>

                {/* In Progress */}
                {inProgress.length > 0 && (
                    <div className="mb-6">
                        <div className="text-xs text-text-muted font-mono uppercase tracking-wider mb-3">In Progress</div>
                        <div className="flex flex-col gap-2">
                            {inProgress.slice(0, 3).map(t => (
                                <Link
                                    key={t.id}
                                    href={`/workshop/${t.id}`}
                                    className="panel rounded-lg p-4 flex items-center justify-between hover:border-border-default transition-colors"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={`w-2 h-2 rounded-full ${t.stage === "vetting" ? "bg-orange-400" : t.stage === "drafting" ? "bg-amber-400" : "bg-blue-400"} animate-pulse`} />
                                        <div>
                                            <div className="text-sm font-medium text-text-primary">
                                                {t.title || <em className="text-text-muted font-normal">Untitled</em>}
                                            </div>
                                            <div className="text-2xs text-text-muted font-mono mt-0.5">
                                                {t.role && <span className="capitalize">{t.role}</span>}
                                                {t.role && " · "}
                                                <span className="capitalize">{t.stage}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <ChevronRight size={16} className="text-text-muted" />
                                </Link>
                            ))}
                        </div>
                    </div>
                )}

                {/* Ready to Publish */}
                {ready.length > 0 && (
                    <div className="mb-6">
                        <div className="text-xs text-text-muted font-mono uppercase tracking-wider mb-3">Ready to Publish</div>
                        {ready.slice(0, 1).map(t => (
                            <Link key={t.id} href={`/workshop/${t.id}`} className="panel rounded-lg p-4 block hover:border-border-default transition-colors">
                                <div className="flex items-center gap-2 mb-2">
                                    <div className="w-2 h-2 rounded-full bg-green-400" />
                                    <span className="text-2xs text-gold-400 font-mono">{t.id}</span>
                                    {t.archetype && <span className="text-2xs text-teal-400 font-mono">{t.archetype}</span>}
                                </div>
                                <div className="text-base font-medium text-text-primary mb-3">
                                    {t.title || "Untitled"}
                                </div>
                                {t.lint_results && (
                                    <div className="flex flex-wrap gap-1.5">
                                        {LINT_LABELS.map(({ key, label }) => {
                                            const check = t.lint_results?.[key];
                                            if (!check) return null;
                                            return (
                                                <span
                                                    key={key}
                                                    className={`text-2xs px-2 py-0.5 rounded-full border font-mono ${check.pass ? "bg-green-900/30 text-green-400 border-green-800/40" : "bg-orange-900/30 text-orange-400 border-orange-800/40"}`}
                                                >
                                                    {check.pass ? "✓" : "⚠"} {label}
                                                </span>
                                            );
                                        })}
                                    </div>
                                )}
                            </Link>
                        ))}
                    </div>
                )}

                {/* Recent Performance */}
                {recentPerformance.length > 0 && (
                    <div>
                        <div className="flex items-center justify-between mb-3">
                            <div className="text-xs text-text-muted font-mono uppercase tracking-wider">Recent Performance</div>
                            <Link href="/observatory" className="text-2xs text-text-muted hover:text-gold-400 font-mono">Observatory →</Link>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            {recentPerformance.map(post => (
                                <div key={post.task_id} className="panel rounded-lg p-4">
                                    <div className="text-2xs text-gold-400 font-mono mb-1">{post.task_id}</div>
                                    <div className="text-sm font-medium text-text-primary mb-3 truncate">{post.title}</div>
                                    <div className="grid grid-cols-3 gap-2 text-xs">
                                        <Metric label="Impressions" value={post.impressions.toLocaleString()} />
                                        <Metric label="Saves" value={String(post.saves)} />
                                        <Metric label="Save Rate" value={`${(post.save_rate * 100).toFixed(1)}%`} highlight />
                                        <Metric label="Comments" value={String(post.comments)} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Empty state */}
                {tasks.length === 0 && (
                    <div className="panel rounded-lg p-12 text-center">
                        <div className="text-text-muted text-sm mb-4">No tasks yet — let's start something worth creating.</div>
                        <Link href="/workshop/new" className="btn-gold">New CoDDE-Task →</Link>
                    </div>
                )}
            </div>
        </div>
    );
}

function StatCard({ label, value, sub, large = true }: { label: string; value: string; sub?: string; large?: boolean }) {
    return (
        <div className="panel rounded-lg p-4">
            <div className="text-2xs text-text-muted font-mono uppercase tracking-wider mb-1">{label}</div>
            <div className={`font-medium text-text-primary ${large ? "text-2xl" : "text-lg"}`}>{value}</div>
            {sub && <div className="text-2xs text-text-muted mt-0.5">{sub}</div>}
        </div>
    );
}

function Metric({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
    return (
        <div>
            <div className="text-2xs text-text-muted font-mono">{label}</div>
            <div className={`text-sm font-medium ${highlight ? "text-gold-400" : "text-text-secondary"}`}>{value}</div>
        </div>
    );
}
