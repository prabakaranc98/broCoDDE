"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { MemoryEntry, KnowledgeDomain, MemoryType } from "@/lib/types";
import { Plus, Copy, Trash2 } from "lucide-react";

const TYPE_COLORS: Record<MemoryType, string> = {
    Experience: "bg-blue-900/40 text-blue-300 border-blue-800/50",
    Research: "bg-purple-900/40 text-purple-300 border-purple-800/50",
    Collaboration: "bg-teal-900/40 text-teal-300 border-teal-800/50",
    Philosophy: "bg-amber-900/40 text-amber-300 border-amber-800/50",
    Current: "bg-green-900/40 text-green-300 border-green-800/50",
    Voice: "bg-rose-900/40 text-rose-300 border-rose-800/50",
    Goal: "bg-indigo-900/40 text-indigo-300 border-indigo-800/50",
};

const DOMAIN_PALETTE = [
    "bg-blue-500", "bg-purple-500", "bg-teal-500",
    "bg-amber-500", "bg-rose-500", "bg-orange-500",
    "bg-cyan-500", "bg-emerald-500",
];

export default function ContextPage() {
    const [entries, setEntries] = useState<MemoryEntry[]>([]);
    const [domains, setDomains] = useState<KnowledgeDomain[]>([]);
    const [showAddEntry, setShowAddEntry] = useState(false);
    const [newText, setNewText] = useState("");
    const [newType, setNewType] = useState<MemoryType>("Experience");

    useEffect(() => {
        api.memory.list().then(setEntries).catch(() => { });
        api.memory.domains.list().then(setDomains).catch(() => { });
    }, []);

    const addEntry = async () => {
        if (!newText.trim()) return;
        const entry = await api.memory.create({ type: newType, text: newText.trim() });
        setEntries(prev => [entry, ...prev]);
        setNewText("");
        setShowAddEntry(false);
    };

    const deleteEntry = async (id: string) => {
        await api.memory.delete(id);
        setEntries(prev => prev.filter(e => e.id !== id));
    };

    return (
        <div className="h-full overflow-y-auto p-6">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <div className="text-xs text-text-muted font-mono uppercase tracking-wider mb-1">Context & Memory</div>
                        <h1 className="text-2xl font-medium text-text-primary">Knowledge Graph</h1>
                    </div>
                    <button
                        onClick={() => setShowAddEntry(true)}
                        className="btn-gold flex items-center gap-2"
                    >
                        <Plus size={14} />
                        Add Entry
                    </button>
                </div>

                {/* Add Entry Form */}
                {showAddEntry && (
                    <div className="panel rounded-lg p-4 mb-6 animate-fade-in">
                        <div className="flex gap-2 mb-3">
                            {(Object.keys(TYPE_COLORS) as MemoryType[]).map(t => (
                                <button
                                    key={t}
                                    onClick={() => setNewType(t)}
                                    className={`text-2xs px-2 py-1 rounded border font-mono transition-all ${newType === t ? TYPE_COLORS[t] : "text-text-muted border-border-subtle hover:border-border-default"}`}
                                >
                                    {t}
                                </button>
                            ))}
                        </div>
                        <textarea
                            value={newText}
                            onChange={e => setNewText(e.target.value)}
                            placeholder="Describe a fact about yourself — experience, research focus, philosophy, voice…"
                            className="w-full bg-surface-800 border border-border-default rounded px-3 py-2 text-sm
                         text-text-primary placeholder:text-text-muted resize-none outline-none
                         focus:border-border-emphasis mb-3"
                            rows={2}
                        />
                        <div className="flex gap-2 justify-end">
                            <button onClick={() => setShowAddEntry(false)} className="btn-ghost text-xs">Cancel</button>
                            <button onClick={addEntry} className="btn-gold text-xs">Save</button>
                        </div>
                    </div>
                )}

                {/* Knowledge Domains */}
                <div className="mb-8">
                    <div className="text-xs text-text-muted font-mono uppercase tracking-wider mb-3">Domains</div>
                    {domains.length === 0 ? (
                        <div className="panel rounded-lg p-6 text-center text-text-muted text-sm">
                            No knowledge domains yet. They're seeded from the Context view or added via Post-Mortem.
                        </div>
                    ) : (
                        <div className="grid grid-cols-3 gap-3">
                            {domains.map((domain, i) => (
                                <div key={domain.id} className="panel rounded-lg p-3">
                                    <div className="flex items-center gap-2 mb-2">
                                        <div className={`w-2 h-2 rounded-full shrink-0 ${DOMAIN_PALETTE[i % DOMAIN_PALETTE.length]}`} />
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

                {/* Identity Memory */}
                <div>
                    <div className="text-xs text-text-muted font-mono uppercase tracking-wider mb-3">Identity Memory</div>
                    {entries.length === 0 ? (
                        <div className="panel rounded-lg p-6 text-center text-text-muted text-sm">
                            No identity memory yet. Add entries to give agents context about who you are.
                        </div>
                    ) : (
                        <div className="flex flex-col gap-2">
                            {entries.map(entry => (
                                <div
                                    key={entry.id}
                                    className="panel rounded-lg flex items-start gap-3 p-3 group hover:border-border-default transition-colors"
                                >
                                    <span className={`text-2xs px-2 py-0.5 rounded border font-mono shrink-0 mt-0.5 ${TYPE_COLORS[entry.type]}`}>
                                        {entry.type}
                                    </span>
                                    <div className="flex-1 text-sm text-text-secondary leading-relaxed">{entry.text}</div>
                                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                                        <button
                                            onClick={() => navigator.clipboard.writeText(entry.text)}
                                            className="p-1 rounded hover:bg-surface-700 text-text-muted hover:text-text-secondary transition-colors"
                                            title="Copy"
                                        >
                                            <Copy size={12} />
                                        </button>
                                        <button
                                            onClick={() => deleteEntry(entry.id)}
                                            className="p-1 rounded hover:bg-surface-700 text-text-muted hover:text-red-400 transition-colors"
                                            title="Delete"
                                        >
                                            <Trash2 size={12} />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
