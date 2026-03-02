"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AgnoMemory, MemoryEntry, KnowledgeDomain, MemoryType } from "@/lib/types";
import { Plus, Copy, Trash2, Brain, User, Map } from "lucide-react";
import clsx from "clsx";

// ── Colour palettes ────────────────────────────────────────────────────────────

const TYPE_COLORS: Record<MemoryType, string> = {
    Experience:    "bg-blue-900/40 text-blue-300 border-blue-800/50",
    Research:      "bg-purple-900/40 text-purple-300 border-purple-800/50",
    Collaboration: "bg-teal-900/40 text-teal-300 border-teal-800/50",
    Philosophy:    "bg-amber-900/40 text-amber-300 border-amber-800/50",
    Current:       "bg-green-900/40 text-green-300 border-green-800/50",
    Voice:         "bg-rose-900/40 text-rose-300 border-rose-800/50",
    Goal:          "bg-indigo-900/40 text-indigo-300 border-indigo-800/50",
};

// Deterministic colour per topic string
const TOPIC_PALETTE = [
    "bg-blue-500/15 text-blue-300 border-blue-500/30",
    "bg-purple-500/15 text-purple-300 border-purple-500/30",
    "bg-teal-500/15 text-teal-300 border-teal-500/30",
    "bg-amber-500/15 text-amber-300 border-amber-500/30",
    "bg-rose-500/15 text-rose-300 border-rose-500/30",
    "bg-orange-500/15 text-orange-300 border-orange-500/30",
    "bg-cyan-500/15 text-cyan-300 border-cyan-500/30",
    "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
    "bg-indigo-500/15 text-indigo-300 border-indigo-500/30",
    "bg-lime-500/15 text-lime-300 border-lime-500/30",
];

function topicColor(topic: string): string {
    let hash = 0;
    for (let i = 0; i < topic.length; i++) hash = (hash * 31 + topic.charCodeAt(i)) | 0;
    return TOPIC_PALETTE[Math.abs(hash) % TOPIC_PALETTE.length];
}

function fmtTs(unix: number): string {
    return new Date(unix * 1000).toLocaleDateString("en-US", {
        month: "short", day: "numeric", year: "numeric",
    });
}

function relativeTime(unix: number): string {
    const diff = Date.now() / 1000 - unix;
    if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.round(diff / 3600)}h ago`;
    if (diff < 86400 * 7) return `${Math.round(diff / 86400)}d ago`;
    return fmtTs(unix);
}

// ── Page ──────────────────────────────────────────────────────────────────────

type Tab = "agno" | "identity" | "domains";

export default function ContextPage() {
    const [tab, setTab] = useState<Tab>("agno");
    const [agnoMemories, setAgnoMemories] = useState<AgnoMemory[]>([]);
    const [identityEntries, setIdentityEntries] = useState<MemoryEntry[]>([]);
    const [domains, setDomains] = useState<KnowledgeDomain[]>([]);
    const [activeTopic, setActiveTopic] = useState<string | null>(null);

    // Add identity entry form
    const [showAdd, setShowAdd] = useState(false);
    const [newText, setNewText] = useState("");
    const [newType, setNewType] = useState<MemoryType>("Experience");

    useEffect(() => {
        api.memory.agnoList().then(setAgnoMemories).catch(() => {});
        api.memory.list().then(setIdentityEntries).catch(() => {});
        api.memory.domains.list().then(setDomains).catch(() => {});
    }, []);

    const addEntry = async () => {
        if (!newText.trim()) return;
        const entry = await api.memory.create({ type: newType, text: newText.trim() });
        setIdentityEntries(prev => [entry, ...prev]);
        setNewText("");
        setShowAdd(false);
    };

    const deleteEntry = async (id: string) => {
        await api.memory.delete(id);
        setIdentityEntries(prev => prev.filter(e => e.id !== id));
    };

    // All unique topics across agno memories (for filter cloud)
    const allTopics = Array.from(
        new Set(agnoMemories.flatMap(m => m.topics))
    ).sort();

    const filteredAgno = activeTopic
        ? agnoMemories.filter(m => m.topics.includes(activeTopic))
        : agnoMemories;

    const evolvedCount = agnoMemories.filter(m => m.evolved).length;

    return (
        <div className="h-full overflow-y-auto p-6">
            <div className="max-w-4xl mx-auto">

                {/* Header */}
                <div className="mb-6">
                    <div className="text-xs text-text-muted font-mono uppercase tracking-wider mb-1">
                        Context & Memory
                    </div>
                    <h1 className="text-2xl font-medium text-text-primary mb-1">
                        What the system knows about you
                    </h1>
                    <p className="text-sm text-text-muted leading-relaxed">
                        Three layers: what <strong className="text-text-secondary">you told it</strong>,
                        what <strong className="text-text-secondary">agents learned</strong>, and your
                        <strong className="text-text-secondary"> knowledge map</strong>.
                    </p>
                </div>

                {/* Tab bar */}
                <div className="flex gap-1 mb-6 border-b border-border-subtle">
                    {([
                        { id: "agno",     icon: Brain, label: "Agent Memory",    count: agnoMemories.length },
                        { id: "identity", icon: User,  label: "Identity",        count: identityEntries.length },
                        { id: "domains",  icon: Map,   label: "Knowledge Domains", count: domains.length },
                    ] as const).map(({ id, icon: Icon, label, count }) => (
                        <button
                            key={id}
                            onClick={() => setTab(id)}
                            className={clsx(
                                "flex items-center gap-2 px-4 py-2 text-xs font-mono border-b-2 transition-colors",
                                tab === id
                                    ? "border-gold-400 text-gold-400"
                                    : "border-transparent text-text-muted hover:text-text-secondary"
                            )}
                        >
                            <Icon size={12} />
                            {label}
                            <span className={clsx(
                                "px-1.5 py-0.5 rounded-full text-[10px]",
                                tab === id ? "bg-gold-500/20 text-gold-400" : "bg-surface-700 text-text-muted"
                            )}>
                                {count}
                            </span>
                        </button>
                    ))}
                </div>

                {/* ── Tab: Agent Memory ── */}
                {tab === "agno" && (
                    <div>
                        {/* Summary stats */}
                        {agnoMemories.length > 0 && (
                            <div className="flex gap-4 mb-5 text-xs font-mono text-text-muted">
                                <span><span className="text-text-primary">{agnoMemories.length}</span> memories</span>
                                {evolvedCount > 0 && (
                                    <span><span className="text-gold-400">{evolvedCount}</span> evolved</span>
                                )}
                                <span><span className="text-text-primary">{allTopics.length}</span> topics</span>
                            </div>
                        )}

                        {/* Topic filter cloud */}
                        {allTopics.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mb-5">
                                <button
                                    onClick={() => setActiveTopic(null)}
                                    className={clsx(
                                        "text-[10px] font-mono px-2 py-0.5 rounded-full border transition-colors",
                                        activeTopic === null
                                            ? "border-gold-400/60 text-gold-400 bg-gold-500/10"
                                            : "border-border-subtle text-text-muted hover:text-text-secondary"
                                    )}
                                >
                                    all
                                </button>
                                {allTopics.map(topic => (
                                    <button
                                        key={topic}
                                        onClick={() => setActiveTopic(topic === activeTopic ? null : topic)}
                                        className={clsx(
                                            "text-[10px] font-mono px-2 py-0.5 rounded-full border transition-colors",
                                            activeTopic === topic
                                                ? topicColor(topic)
                                                : "border-border-subtle text-text-muted hover:text-text-secondary"
                                        )}
                                    >
                                        {topic}
                                    </button>
                                ))}
                            </div>
                        )}

                        {/* Explanation */}
                        <div className="panel rounded-lg px-4 py-3 mb-5 border-l-2 border-gold-500/30">
                            <p className="text-xs text-text-muted leading-relaxed">
                                <span className="text-text-secondary font-medium">Agent memory</span> is written automatically by agents as they work.
                                Entries marked <span className="text-gold-400 font-medium">evolved</span> were updated after first creation — the agent revised its understanding.
                                Agents read these before every session to build continuity.
                            </p>
                        </div>

                        {filteredAgno.length === 0 ? (
                            <div className="panel rounded-lg p-6 text-center text-text-muted text-sm">
                                {agnoMemories.length === 0
                                    ? "No agent memories yet. Start a Discovery session — the Strategist will write its findings here."
                                    : "No memories match this topic filter."
                                }
                            </div>
                        ) : (
                            <div className="relative">
                                {/* Timeline line */}
                                <div className="absolute left-2 top-3 bottom-3 w-px bg-border-subtle" />

                                <div className="space-y-3 pl-8">
                                    {filteredAgno.map((mem) => (
                                        <AgnoMemoryCard key={mem.id} memory={mem} />
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* ── Tab: Identity Memory ── */}
                {tab === "identity" && (
                    <div>
                        <div className="flex items-center justify-between mb-5">
                            <div className="panel rounded-lg px-4 py-3 flex-1 mr-4 border-l-2 border-gold-500/30">
                                <p className="text-xs text-text-muted leading-relaxed">
                                    <span className="text-text-secondary font-medium">Identity memory</span> is what you explicitly tell the system about yourself.
                                    Agents inject these at session start — they shape voice, framing, and angle selection.
                                </p>
                            </div>
                            <button onClick={() => setShowAdd(true)} className="btn-gold flex items-center gap-2 shrink-0">
                                <Plus size={14} /> Add
                            </button>
                        </div>

                        {showAdd && (
                            <div className="panel rounded-lg p-4 mb-5">
                                <div className="flex flex-wrap gap-1.5 mb-3">
                                    {(Object.keys(TYPE_COLORS) as MemoryType[]).map(t => (
                                        <button key={t} onClick={() => setNewType(t)}
                                            className={clsx(
                                                "text-2xs px-2 py-1 rounded border font-mono transition-all",
                                                newType === t ? TYPE_COLORS[t] : "text-text-muted border-border-subtle hover:border-border-default"
                                            )}>
                                            {t}
                                        </button>
                                    ))}
                                </div>
                                <textarea
                                    value={newText}
                                    onChange={e => setNewText(e.target.value)}
                                    placeholder="Describe a fact about yourself — experience, research focus, philosophy, voice…"
                                    className="w-full bg-surface-800 border border-border-default rounded px-3 py-2 text-sm text-text-primary placeholder:text-text-muted resize-none outline-none focus:border-border-emphasis mb-3"
                                    rows={2}
                                />
                                <div className="flex gap-2 justify-end">
                                    <button onClick={() => setShowAdd(false)} className="btn-ghost text-xs">Cancel</button>
                                    <button onClick={addEntry} className="btn-gold text-xs">Save</button>
                                </div>
                            </div>
                        )}

                        {identityEntries.length === 0 ? (
                            <div className="panel rounded-lg p-6 text-center text-text-muted text-sm">
                                No identity memory yet. Add entries to give agents context about who you are.
                            </div>
                        ) : (
                            <div className="flex flex-col gap-2">
                                {identityEntries.map(entry => (
                                    <div key={entry.id}
                                        className="panel rounded-lg flex items-start gap-3 p-3 group hover:border-border-default transition-colors">
                                        <span className={clsx("text-2xs px-2 py-0.5 rounded border font-mono shrink-0 mt-0.5", TYPE_COLORS[entry.type])}>
                                            {entry.type}
                                        </span>
                                        <div className="flex-1 text-sm text-text-secondary leading-relaxed">{entry.text}</div>
                                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                                            <button onClick={() => navigator.clipboard.writeText(entry.text)}
                                                className="p-1 rounded hover:bg-surface-700 text-text-muted hover:text-text-secondary transition-colors">
                                                <Copy size={12} />
                                            </button>
                                            <button onClick={() => deleteEntry(entry.id)}
                                                className="p-1 rounded hover:bg-surface-700 text-text-muted hover:text-red-400 transition-colors">
                                                <Trash2 size={12} />
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* ── Tab: Knowledge Domains ── */}
                {tab === "domains" && (
                    <div>
                        <div className="panel rounded-lg px-4 py-3 mb-5 border-l-2 border-gold-500/30">
                            <p className="text-xs text-text-muted leading-relaxed">
                                <span className="text-text-secondary font-medium">Knowledge domains</span> are the topical areas your content lives in.
                                They're used by Discovery to find relevant angles and by the Analyst to identify performance by domain.
                            </p>
                        </div>

                        {domains.length === 0 ? (
                            <div className="panel rounded-lg p-6 text-center text-text-muted text-sm">
                                No knowledge domains yet. They're added via Post-Mortem or the Identity editor.
                            </div>
                        ) : (
                            <div className="grid grid-cols-3 gap-3">
                                {domains.map((domain, i) => (
                                    <div key={domain.id} className="panel rounded-lg p-3">
                                        <div className="flex items-center gap-2 mb-2">
                                            <div className="w-2 h-2 rounded-full shrink-0"
                                                style={{ backgroundColor: domain.color || "#D4A853" }} />
                                            <div className="text-sm font-medium text-text-primary">{domain.name}</div>
                                        </div>
                                        <div className="flex flex-wrap gap-1 mb-2">
                                            {domain.tags.map(tag => (
                                                <span key={tag} className="text-2xs bg-surface-700 text-text-muted px-1.5 py-0.5 rounded">
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>
                                        <div className="text-2xs text-text-muted font-mono">
                                            {domain.post_count} post{domain.post_count !== 1 ? "s" : ""}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

            </div>
        </div>
    );
}

// ── Agent Memory Card ──────────────────────────────────────────────────────────

function AgnoMemoryCard({ memory }: { memory: AgnoMemory }) {
    const [expanded, setExpanded] = useState(false);
    const preview = memory.text.length > 160 && !expanded
        ? memory.text.slice(0, 160) + "…"
        : memory.text;

    return (
        <div className="relative">
            {/* Timeline dot */}
            <div className={clsx(
                "absolute -left-6 top-3 w-2 h-2 rounded-full border-2 border-surface-900",
                memory.evolved ? "bg-gold-400" : "bg-border-default"
            )} />

            <div className={clsx(
                "panel rounded-lg p-3 transition-colors",
                memory.evolved && "border-gold-500/20"
            )}>
                {/* Header row */}
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <span className="text-[10px] text-text-muted font-mono">
                        {relativeTime(memory.created_at)}
                    </span>
                    {memory.evolved && (
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded border border-gold-500/40 text-gold-400/80 bg-gold-500/10">
                            evolved · {fmtTs(memory.updated_at!)}
                        </span>
                    )}
                </div>

                {/* Text */}
                <p className="text-sm text-text-secondary leading-relaxed mb-2">
                    {preview}
                    {memory.text.length > 160 && (
                        <button
                            onClick={() => setExpanded(e => !e)}
                            className="ml-1 text-gold-400/70 hover:text-gold-400 text-xs font-mono"
                        >
                            {expanded ? "less" : "more"}
                        </button>
                    )}
                </p>

                {/* Topics */}
                {memory.topics.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                        {memory.topics.map(topic => (
                            <span key={topic} className={clsx(
                                "text-[10px] font-mono px-1.5 py-0.5 rounded border",
                                topicColor(topic)
                            )}>
                                {topic}
                            </span>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
