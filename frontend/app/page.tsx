import Link from "next/link";
import { ChevronRight, Zap } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchSafe<T>(path: string, fallback: T): Promise<T> {
    try {
        const res = await fetch(`${API}${path}`, { next: { revalidate: 30 } });
        if (!res.ok) return fallback;
        return res.json();
    } catch { return fallback; }
}

interface FeedCard {
    type: string;
    source: string;
    title: string;
    summary: string;
    url?: string | null;
    domain?: string | null;
    upvotes?: number | null;
}

export default async function DashboardPage() {
    const [tasks, concepts, feed] = await Promise.all([
        fetchSafe<{ id: string; title: string | null; stage: string; role: string | null; task_type?: string; domain?: string | null }[]>("/tasks?limit=50", []),
        fetchSafe<{ id: string }[]>("/concepts", []),
        fetchSafe<FeedCard[]>("/discovery/feed?limit=9", []),
    ]);

    const activeTasks = tasks.filter(t => !["ready", "post-mortem"].includes(t.stage));
    const completeTasks = tasks.filter(t => ["ready", "post-mortem"].includes(t.stage));
    const sparkSessions = tasks.filter(t => t.task_type === "spark");
    const domains = [...new Set(tasks.map(t => t.domain).filter(Boolean))];

    return (
        <div className="h-full overflow-y-auto p-6">
            <div className="max-w-5xl mx-auto">
                {/* Hero */}
                <div className="flex items-start justify-between mb-6">
                    <div>
                        <div className="text-xs text-text-muted font-mono uppercase tracking-wider mb-1">Learning Studio</div>
                        <h1 className="text-3xl font-medium text-text-primary mb-1">BroCoDDE</h1>
                        <p className="text-text-muted text-sm">
                            {activeTasks.length > 0
                                ? `${activeTasks.length} active session${activeTasks.length > 1 ? "s" : ""}`
                                : "Ready for a new session."}
                            {concepts.length > 0 && ` · ${concepts.length} concept${concepts.length > 1 ? "s" : ""} saved`}
                        </p>
                    </div>
                    <Link href="/workshop/new" className="btn-gold flex items-center gap-2 text-sm px-5 py-2.5">
                        + New Session
                    </Link>
                </div>

                {/* Stats Row */}
                <div className="grid grid-cols-4 gap-3 mb-8">
                    <StatCard label="Active Sessions" value={activeTasks.length > 0 ? String(activeTasks.length) : "—"} sub="In progress" />
                    <StatCard label="Concepts Saved" value={concepts.length > 0 ? String(concepts.length) : "—"} sub="Knowledge graph" />
                    <StatCard label="Spark Sessions" value={sparkSessions.length > 0 ? String(sparkSessions.length) : "—"} sub="Feynman loops" large={false} />
                    <StatCard label="Domains" value={domains.length > 0 ? String(domains.length) : "—"} sub="Explored" large={false} />
                </div>

                {/* ── Explore Feed ─────────────────────────────────────────── */}
                {feed.length > 0 && (
                    <div className="mb-8">
                        <div className="flex items-center justify-between mb-3">
                            <div className="text-xs text-text-muted font-mono uppercase tracking-wider">
                                Explore — personalized for you
                            </div>
                            <span className="text-2xs text-text-muted/50 font-mono">
                                {feed.filter(c => c.source === "HuggingFace").length} papers · {feed.filter(c => c.source === "HackerNews").length} discussions · {feed.filter(c => c.source === "Exa").length} perspectives
                            </span>
                        </div>
                        <div className="grid grid-cols-3 gap-3">
                            {feed.map((card, i) => (
                                <FeedCardComponent key={i} card={card} />
                            ))}
                        </div>
                    </div>
                )}

                {/* Active Sessions */}
                {activeTasks.length > 0 && (
                    <div className="mb-6">
                        <div className="text-xs text-text-muted font-mono uppercase tracking-wider mb-3">Active Sessions</div>
                        <div className="flex flex-col gap-2">
                            {activeTasks.slice(0, 4).map(t => (
                                <Link
                                    key={t.id}
                                    href={`/workshop/${t.id}`}
                                    className="panel rounded-lg p-4 flex items-center justify-between hover:border-border-default transition-colors"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={`w-2 h-2 rounded-full shrink-0 ${
                                            t.task_type === "spark" ? "bg-cyan-400" :
                                            t.stage === "vetting" ? "bg-orange-400" :
                                            t.stage === "drafting" ? "bg-amber-400" : "bg-blue-400"
                                        } animate-pulse`} />
                                        <div>
                                            <div className="text-sm font-medium text-text-primary flex items-center gap-1.5">
                                                {t.task_type === "spark" && <span className="text-cyan-400 text-xs">⚡</span>}
                                                {t.title || <em className="text-text-muted font-normal">Untitled</em>}
                                            </div>
                                            <div className="text-2xs text-text-muted font-mono mt-0.5">
                                                {t.domain && <span className="text-teal-400/70">{t.domain}</span>}
                                                {t.domain && " · "}
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

                {/* Complete */}
                {completeTasks.length > 0 && (
                    <div className="mb-6">
                        <div className="flex items-center justify-between mb-3">
                            <div className="text-xs text-text-muted font-mono uppercase tracking-wider">Complete</div>
                            <Link href="/queue" className="text-2xs text-text-muted hover:text-gold-400 font-mono">All sessions →</Link>
                        </div>
                        <div className="flex flex-col gap-2">
                            {completeTasks.slice(0, 2).map(t => (
                                <Link
                                    key={t.id}
                                    href={`/workshop/${t.id}`}
                                    className="panel rounded-lg p-3 flex items-center justify-between hover:border-border-default transition-colors"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className="w-2 h-2 rounded-full bg-green-400/50 shrink-0" />
                                        <span className="text-sm text-text-secondary truncate">
                                            {t.title || <em className="opacity-50">Untitled</em>}
                                        </span>
                                    </div>
                                    <span className="text-2xs text-text-muted font-mono capitalize shrink-0">{t.stage}</span>
                                </Link>
                            ))}
                        </div>
                    </div>
                )}

                {/* Empty state */}
                {tasks.length === 0 && feed.length === 0 && (
                    <div className="panel rounded-lg p-12 text-center">
                        <div className="text-4xl mb-4">⚡</div>
                        <div className="text-text-muted text-sm mb-2">No sessions yet.</div>
                        <div className="text-xs text-text-muted/60 mb-6 max-w-sm mx-auto">
                            Start a Spark session to explore a paper, or a Deep session to develop a full synthesis.
                        </div>
                        <Link href="/workshop/new" className="btn-gold">New Session →</Link>
                    </div>
                )}
            </div>
        </div>
    );
}

// ── Feed card component ────────────────────────────────────────────────────────

const CARD_STYLES: Record<string, { badge: string; label: string; viewLabel: string; upvoteIcon: string }> = {
    paper:       { badge: "bg-blue-900/30 text-blue-300 border border-blue-800/40",    label: "paper",       viewLabel: "View paper ↗",       upvoteIcon: "▲" },
    discussion:  { badge: "bg-orange-900/20 text-orange-400 border border-orange-800/30", label: "discussion", viewLabel: "View discussion ↗", upvoteIcon: "●" },
    perspective: { badge: "bg-purple-900/20 text-purple-300 border border-purple-800/30", label: "perspective", viewLabel: "Read ↗",          upvoteIcon: "◆" },
};

function FeedCardComponent({ card }: { card: FeedCard }) {
    const style = CARD_STYLES[card.type] ?? CARD_STYLES.discussion;
    const sparkHref = card.url
        ? `/workshop/new?mode=spark&url=${encodeURIComponent(card.url)}`
        : "/workshop/new?mode=spark";

    return (
        <div className="panel rounded-lg p-4 flex flex-col gap-3 hover:border-border-default transition-colors">
            {/* Header row */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                    <span className={`text-2xs font-mono px-1.5 py-0.5 rounded uppercase tracking-wider ${style.badge}`}>
                        {style.label}
                    </span>
                    <span className="text-2xs text-text-muted/60 font-mono">{card.source}</span>
                </div>
                {card.upvotes != null && card.upvotes > 0 && (
                    <span className="text-2xs text-text-muted/50 font-mono">
                        {style.upvoteIcon} {card.upvotes}
                    </span>
                )}
            </div>

            {/* Title */}
            <div className="text-sm font-medium text-text-primary leading-snug line-clamp-2 flex-1">
                {card.title}
            </div>

            {/* Summary */}
            {card.summary && (
                <div className="text-xs text-text-muted leading-relaxed line-clamp-2">
                    {card.summary}
                </div>
            )}

            {/* Domain tag */}
            {card.domain && (
                <div className="text-2xs text-teal-400/70 font-mono truncate">{card.domain}</div>
            )}

            {/* Actions */}
            <div className="flex items-center justify-between mt-auto pt-1">
                {card.url ? (
                    <a
                        href={card.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-2xs text-text-muted/50 hover:text-text-muted font-mono transition-colors"
                    >
                        {style.viewLabel}
                    </a>
                ) : (
                    <span />
                )}
                <Link
                    href={sparkHref}
                    className="flex items-center gap-1 text-2xs text-cyan-400/70 hover:text-cyan-300 font-mono transition-colors"
                >
                    <Zap size={10} />
                    Spark
                </Link>
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
