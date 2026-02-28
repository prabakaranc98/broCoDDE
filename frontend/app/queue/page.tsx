"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { CoddeTask, LintResults } from "@/lib/types";
import { STAGE_LABELS } from "@/lib/types";
import { CheckCircle2, AlertCircle, ChevronRight } from "lucide-react";
import clsx from "clsx";

const LINT_CHECKS: { checkKey: keyof LintResults; label: string }[] = [
    { checkKey: "opening_strength", label: "Opening Strength" },
    { checkKey: "micro_learning", label: "Teaches Something" },
    { checkKey: "credential_stating", label: "Credential Stating" },
    { checkKey: "rant_detection", label: "Rant Detection" },
    { checkKey: "fluff_detection", label: "Fluff" },
    { checkKey: "engagement_bait", label: "Engagement Bait" },
];

function LintBadge({ checkKey, label, results }: { checkKey: keyof LintResults; label: string; results: LintResults }) {
    const check = results[checkKey] as { pass: boolean; notes: string } | undefined;
    if (!check || typeof check !== "object") return null;
    return (
        <span className={clsx(
            "inline-flex items-center gap-1 text-2xs px-2 py-0.5 rounded-full font-mono",
            check.pass
                ? "bg-green-900/30 text-green-400 border border-green-800/40"
                : "bg-orange-900/30 text-orange-400 border border-orange-800/40"
        )}>
            {check.pass ? <CheckCircle2 size={10} /> : <AlertCircle size={10} />}
            {label}
        </span>
    );
}

export default function QueuePage() {
    const [tasks, setTasks] = useState<CoddeTask[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            api.tasks.list("ready"),
            api.tasks.list("vetting"),
            api.tasks.list("drafting"),
            api.tasks.list("structuring"),
            api.tasks.list("extraction"),
            api.tasks.list("discovery"),
        ]).then(results => {
            setTasks(results.flat());
            setLoading(false);
        }).catch(() => setLoading(false));
    }, []);

    const ready = tasks.filter(t => t.stage === "ready");
    const inProgress = tasks.filter(t => t.stage !== "ready");

    return (
        <div className="h-full overflow-y-auto p-6">
            <div className="max-w-4xl mx-auto">
                <div className="mb-6">
                    <div className="text-xs text-text-muted font-mono uppercase tracking-wider mb-1">Publish Queue</div>
                    <h1 className="text-2xl font-medium text-text-primary">
                        {ready.length === 0 ? "No posts ready to publish" : `${ready.length} ready to publish`}
                    </h1>
                </div>

                {loading && <div className="text-text-muted text-sm">Loading…</div>}

                {ready.length > 0 && (
                    <div className="mb-8">
                        {ready.map(task => (
                            <TaskCard key={task.id} task={task} showPublish />
                        ))}
                    </div>
                )}

                {inProgress.length > 0 && (
                    <div>
                        <div className="text-xs text-text-muted font-mono uppercase tracking-wider mb-3">In Progress</div>
                        <div className="flex flex-col gap-3">
                            {inProgress.map(task => (
                                <TaskCard key={task.id} task={task} />
                            ))}
                        </div>
                    </div>
                )}

                {!loading && tasks.length === 0 && (
                    <div className="text-center text-text-muted text-sm py-16">
                        No tasks yet.{" "}
                        <Link href="/workshop/new" className="text-gold-400 hover:underline">Start one →</Link>
                    </div>
                )}
            </div>
        </div>
    );
}

function TaskCard({ task, showPublish }: { task: CoddeTask; showPublish?: boolean }) {
    const [publishing, setPublishing] = useState(false);

    const markPublished = async () => {
        setPublishing(true);
        await api.tasks.updateStage(task.id, "post-mortem");
        window.location.reload();
    };

    return (
        <div className="panel rounded-lg p-4 mb-3">
            <div className="flex items-start justify-between mb-3">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <span className="text-2xs text-gold-400 font-mono">{task.id}</span>
                        {task.series_id && (
                            <span className="text-2xs text-text-muted font-mono">· {task.series_id}</span>
                        )}
                    </div>
                    <div className="text-base font-medium text-text-primary">
                        {task.title || <em className="text-text-muted font-normal">Untitled</em>}
                    </div>
                    <div className="flex items-center gap-1.5 mt-1 text-xs text-text-muted">
                        {task.role && <span className="capitalize">{task.role}</span>}
                        {task.intent && (
                            <>
                                <ChevronRight size={10} />
                                <span className="capitalize">{task.intent}</span>
                            </>
                        )}
                        {task.domain && (
                            <>
                                <ChevronRight size={10} />
                                <span className="text-teal-400">{task.domain}</span>
                            </>
                        )}
                    </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                    <Link href={`/workshop/${task.id}`} className="btn-ghost text-xs">
                        Edit
                    </Link>
                    {showPublish ? (
                        <button
                            onClick={markPublished}
                            disabled={publishing}
                            className="btn-gold text-xs disabled:opacity-50"
                        >
                            {publishing ? "…" : "Mark Published"}
                        </button>
                    ) : (
                        <span className={`badge-${task.stage}`}>{STAGE_LABELS[task.stage]}</span>
                    )}
                </div>
            </div>

            {task.skeleton?.hook && (
                <div className="bg-surface-800 rounded p-3 mb-3 font-mono text-xs text-text-secondary leading-relaxed">
                    {task.skeleton.hook}
                    {task.skeleton.insight && (
                        <div className="mt-1 text-text-muted">{task.skeleton.insight}</div>
                    )}
                </div>
            )}

            {task.lint_results && (
                <div className="flex flex-wrap gap-1.5">
                    {LINT_CHECKS.map(({ checkKey, label }) => (
                        <LintBadge key={checkKey} checkKey={checkKey} label={label} results={task.lint_results!} />
                    ))}
                </div>
            )}
        </div>
    );
}
