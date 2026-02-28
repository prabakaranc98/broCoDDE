"use client";

import type { CoddeTask, LifecycleStage } from "@/lib/types";
import { LIFECYCLE_STAGES, STAGE_LABELS } from "@/lib/types";
import { ChevronRight } from "lucide-react";
import clsx from "clsx";

const STAGE_COLORS: Record<LifecycleStage, string> = {
    discovery: "bg-blue-500",
    extraction: "bg-purple-500",
    structuring: "bg-teal-500",
    drafting: "bg-amber-500",
    vetting: "bg-orange-500",
    ready: "bg-green-500",
    "post-mortem": "bg-stone-500",
};

interface LifecycleBarProps {
    task: CoddeTask;
    onAdvance: () => void;
}

export function LifecycleBar({ task, onAdvance }: LifecycleBarProps) {
    const currentIdx = LIFECYCLE_STAGES.indexOf(task.stage);
    const canAdvance = currentIdx < LIFECYCLE_STAGES.length - 1;

    return (
        <div className="flex items-center gap-1 px-4 py-2.5 bg-surface-900 border-b border-border-subtle overflow-x-auto">
            {LIFECYCLE_STAGES.map((stage, i) => {
                const isActive = stage === task.stage;
                const isPast = i < currentIdx;
                const isFuture = i > currentIdx;
                return (
                    <div key={stage} className="flex items-center gap-1 shrink-0">
                        <div className={clsx(
                            "flex items-center gap-1.5 px-2 py-1 rounded text-2xs font-mono transition-all",
                            isActive && "bg-surface-700 border border-border-default text-text-primary",
                            isPast && "text-text-muted",
                            isFuture && "text-text-muted opacity-40",
                        )}>
                            <div className={clsx(
                                "w-1.5 h-1.5 rounded-full",
                                isActive ? STAGE_COLORS[stage] : isPast ? "bg-green-700" : "bg-surface-600"
                            )} />
                            {STAGE_LABELS[stage]}
                        </div>
                        {i < LIFECYCLE_STAGES.length - 1 && (
                            <ChevronRight size={10} className="text-border-emphasis shrink-0" />
                        )}
                    </div>
                );
            })}

            {canAdvance && (
                <button
                    onClick={onAdvance}
                    className="ml-auto shrink-0 btn-ghost text-2xs"
                >
                    → Next stage
                </button>
            )}
        </div>
    );
}
