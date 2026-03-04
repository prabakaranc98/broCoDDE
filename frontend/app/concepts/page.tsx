"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { ConceptNode } from "@/lib/types";
import { Lightbulb, ExternalLink, Trash2 } from "lucide-react";

export default function ConceptsPage() {
    const [concepts, setConcepts] = useState<ConceptNode[]>([]);
    const [loading, setLoading] = useState(true);
    const [deleting, setDeleting] = useState<string | null>(null);

    useEffect(() => {
        api.concepts.list().then(setConcepts).catch(console.error).finally(() => setLoading(false));
    }, []);

    const handleDelete = async (id: string) => {
        setDeleting(id);
        try {
            await api.concepts.delete(id);
            setConcepts(prev => prev.filter(c => c.id !== id));
        } catch (e) {
            console.error(e);
        } finally {
            setDeleting(null);
        }
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center text-text-muted text-sm">
                Loading concepts…
            </div>
        );
    }

    return (
        <div className="h-full overflow-y-auto p-6">
            <div className="max-w-3xl mx-auto">
                <div className="mb-6 flex items-center gap-3">
                    <Lightbulb size={20} className="text-gold-400" />
                    <div>
                        <h1 className="text-xl font-medium text-text-primary">Concepts</h1>
                        <p className="text-text-muted text-sm">
                            Crystallized insights from your Spark sessions. {concepts.length} concept{concepts.length !== 1 ? "s" : ""} saved.
                        </p>
                    </div>
                </div>

                {concepts.length === 0 ? (
                    <div className="text-center py-16 text-text-muted">
                        <div className="text-4xl mb-3">⚡</div>
                        <p className="text-sm">No concepts yet.</p>
                        <p className="text-xs mt-1">Start a Spark session to build your knowledge graph.</p>
                        <Link
                            href="/workshop/new"
                            className="inline-block mt-4 px-4 py-2 bg-gold-500/10 border border-gold-500/30 text-gold-400 text-sm rounded hover:bg-gold-500/20 transition-colors"
                        >
                            New Spark Session →
                        </Link>
                    </div>
                ) : (
                    <div className="flex flex-col gap-3">
                        {concepts.map(concept => (
                            <div
                                key={concept.id}
                                className="panel rounded-lg p-4 hover:border-border-default transition-colors group"
                            >
                                <div className="flex items-start justify-between gap-3">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1.5">
                                            <h2 className="text-sm font-medium text-text-primary truncate">
                                                {concept.title}
                                            </h2>
                                            {concept.domain && (
                                                <span className="shrink-0 text-2xs text-text-muted font-mono bg-surface-700 px-1.5 py-0.5 rounded">
                                                    {concept.domain}
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-sm text-text-secondary leading-relaxed">
                                            {concept.core_insight}
                                        </p>
                                        <div className="flex items-center gap-3 mt-2.5">
                                            {concept.source_url && (
                                                <a
                                                    href={concept.source_url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="flex items-center gap-1 text-2xs text-gold-400/60 hover:text-gold-400 transition-colors"
                                                >
                                                    <ExternalLink size={10} />
                                                    {concept.source_title || "Source"}
                                                </a>
                                            )}
                                            {concept.task_id && (
                                                <Link
                                                    href={`/workshop/${concept.task_id}`}
                                                    className="text-2xs text-text-muted hover:text-gold-400 transition-colors font-mono"
                                                >
                                                    → Session
                                                </Link>
                                            )}
                                            {concept.tags.length > 0 && (
                                                <div className="flex gap-1">
                                                    {concept.tags.slice(0, 3).map(tag => (
                                                        <span key={tag} className="text-2xs text-text-muted/60 font-mono">
                                                            #{tag}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                            <span className="text-2xs text-text-muted/40 ml-auto">
                                                {new Date(concept.created_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => handleDelete(concept.id)}
                                        disabled={deleting === concept.id}
                                        className="shrink-0 p-1.5 text-text-muted/30 hover:text-red-400/60 opacity-0 group-hover:opacity-100 transition-all rounded"
                                    >
                                        <Trash2 size={13} />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
