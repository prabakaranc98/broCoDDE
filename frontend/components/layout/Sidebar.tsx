"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { LayoutDashboard, ListTodo, Telescope, Brain, Layers, Plus } from "lucide-react";
import { api } from "@/lib/api";
import type { CoddeTask } from "@/lib/types";
import clsx from "clsx";

const NAV = [
    { href: "/", icon: LayoutDashboard, label: "Dashboard" },
    { href: "/queue", icon: ListTodo, label: "Queue" },
    { href: "/observatory", icon: Telescope, label: "Observatory" },
    { href: "/context", icon: Brain, label: "Context" },
    { href: "/series", icon: Layers, label: "Series" },
];

export function Sidebar() {
    const path = usePathname();
    const [recentTasks, setRecentTasks] = useState<CoddeTask[]>([]);
    const [stats, setStats] = useState({ posts: 0, saves: 0, queue: 0 });

    // Active task: the most recently opened workshop task
    const activeTaskMatch = path.match(/^\/workshop\/([^/]+)$/);
    const activeTaskId = activeTaskMatch?.[1];
    const activeTask = recentTasks.find(t => t.id === activeTaskId);

    useEffect(() => {
        api.tasks.list().then(tasks => {
            setRecentTasks(tasks.slice(0, 5));
            setStats({
                posts: tasks.filter(t => t.stage === "post-mortem").length,
                saves: 0, // populated from observatory in a full impl
                queue: tasks.filter(t => t.stage === "ready").length,
            });
        }).catch(() => { });
    }, [path]); // refresh on navigation

    return (
        <aside className="w-56 bg-surface-900 border-r border-border-subtle flex flex-col py-3 px-2 shrink-0 select-none">
            {/* Logo */}
            <div className="px-2 mb-4">
                <span className="font-mono text-gold-400 font-medium tracking-wide text-sm">BroCoDDE</span>
                <span className="font-mono text-text-muted text-xs ml-1">v0.4</span>
            </div>

            {/* New Task CTA */}
            <Link
                href="/workshop/new"
                className="flex items-center gap-2 mx-1 mb-3 px-3 py-2 bg-gold-500/10 hover:bg-gold-500/20
                   border border-gold-500/30 rounded text-gold-400 text-sm font-medium transition-colors"
            >
                <Plus size={14} />
                New CoDDE-Task
            </Link>

            {/* Navigation */}
            <nav className="flex flex-col gap-0.5 mb-3">
                {NAV.map(({ href, icon: Icon, label }) => (
                    <Link
                        key={href}
                        href={href}
                        className={clsx("nav-item", path === href && "active")}
                    >
                        <Icon size={15} />
                        {label}
                    </Link>
                ))}
            </nav>

            {/* Active Task */}
            {activeTask && (
                <div className="mx-1 mb-2">
                    <div className="text-2xs text-text-muted font-mono uppercase tracking-wider px-2 mb-1.5">
                        Active Task
                    </div>
                    <div className="px-2 py-2 bg-surface-800 rounded border border-gold-500/20">
                        <div className="text-2xs text-gold-400 font-mono truncate">{activeTask.id}</div>
                        <div className="text-xs text-text-primary truncate mt-0.5">
                            {activeTask.title || "Untitled"}
                        </div>
                        <div className={`badge-${activeTask.stage} mt-1.5 inline-block`}>{activeTask.stage}</div>
                    </div>
                </div>
            )}

            {/* Recent tasks */}
            {recentTasks.length > 0 && (
                <div className="mx-1 flex-1 overflow-y-auto">
                    <div className="text-2xs text-text-muted font-mono uppercase tracking-wider px-2 mb-1.5">
                        Recent
                    </div>
                    <div className="flex flex-col gap-0.5">
                        {recentTasks.map(t => (
                            <Link
                                key={t.id}
                                href={`/workshop/${t.id}`}
                                className={clsx(
                                    "flex items-center justify-between px-2 py-1.5 rounded text-xs group",
                                    path === `/workshop/${t.id}` ? "bg-surface-700 text-text-primary" : "text-text-muted hover:bg-surface-800 hover:text-text-secondary"
                                )}
                            >
                                <span className="truncate flex-1">
                                    {t.title || <em className="opacity-50">Untitled</em>}
                                </span>
                                <span className="ml-1 opacity-50 shrink-0">›</span>
                            </Link>
                        ))}
                    </div>
                </div>
            )}

            {/* Footer stats */}
            <div className="mx-1 mt-3 pt-3 border-t border-border-subtle grid grid-cols-2 gap-2 px-1">
                <div>
                    <div className="text-2xs text-text-muted font-mono">Posts</div>
                    <div className="text-sm font-medium text-text-primary">{stats.posts || "—"}</div>
                </div>
                <div>
                    <div className="text-2xs text-text-muted font-mono">Queue</div>
                    <div className="text-sm font-medium text-text-primary">{stats.queue || "—"}</div>
                </div>
            </div>

            <div className="mt-4 px-3 pb-2 text-center text-xs font-mono text-text-muted opacity-60">
                prachalabs
            </div>
        </aside>
    );
}
