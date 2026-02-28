"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ObservatoryData, PostMetrics } from "@/lib/types";
import Link from "next/link";
import clsx from "clsx";

export default function ObservatoryPage() {
    const [data, setData] = useState<ObservatoryData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.observatory.get().then(d => { setData(d); setLoading(false); }).catch(() => setLoading(false));
    }, []);

    if (loading) return <div className="h-full flex items-center justify-center text-text-muted text-sm">Loading…</div>;
    if (!data || data.total_posts === 0) {
        return (
            <div className="h-full flex items-center justify-center text-center">
                <div>
                    <div className="text-text-muted text-sm mb-3">No published posts yet.</div>
                    <Link href="/workshop/new" className="text-gold-400 text-sm hover:underline">Start your first CoDDE-Task →</Link>
                </div>
            </div>
        );
    }

    const maxSaveRate = Math.max(...data.posts.map(p => p.save_rate), 0.001);

    return (
        <div className="h-full overflow-y-auto p-6">
            <div className="max-w-5xl mx-auto">
                <div className="mb-6">
                    <div className="text-xs text-text-muted font-mono uppercase tracking-wider mb-1">Observatory</div>
                    <h1 className="text-2xl font-medium text-text-primary">Content Performance</h1>
                </div>

                {/* Stats Row */}
                <div className="grid grid-cols-4 gap-3 mb-6">
                    {[
                        { label: "Avg Impressions", value: data.avg_impressions.toLocaleString() },
                        { label: "Avg Save Rate", value: `${(data.avg_save_rate * 100).toFixed(1)}%` },
                        { label: "Avg Comments", value: data.avg_comments.toFixed(1) },
                        { label: "Total Posts", value: data.total_posts },
                    ].map(s => (
                        <div key={s.label} className="panel rounded-lg p-4">
                            <div className="text-2xs text-text-muted font-mono uppercase tracking-wider mb-1">{s.label}</div>
                            <div className="text-2xl font-medium text-text-primary">{s.value}</div>
                        </div>
                    ))}
                </div>

                {/* Best archetype */}
                {data.best_archetype && (
                    <div className="panel rounded-lg p-4 mb-6 flex items-center gap-4">
                        <div>
                            <div className="text-2xs text-text-muted font-mono uppercase tracking-wider mb-1">Top Archetype</div>
                            <div className="text-lg font-medium text-gold-400">{data.best_archetype}</div>
                            <div className="text-xs text-text-muted mt-0.5">Highest save rate</div>
                        </div>
                    </div>
                )}

                {/* Save Rate Bar Chart (pure CSS — no chart lib needed) */}
                <div className="panel rounded-lg p-4 mb-6">
                    <div className="text-2xs text-text-muted font-mono uppercase tracking-wider mb-4">Save Rate by Post</div>
                    <div className="flex flex-col gap-2">
                        {data.posts.slice(0, 10).map(post => (
                            <div key={post.task_id} className="flex items-center gap-3">
                                <div className="text-2xs text-text-muted font-mono w-28 shrink-0 truncate">
                                    {post.title || post.task_id}
                                </div>
                                <div className="flex-1 h-4 bg-surface-800 rounded overflow-hidden">
                                    <div
                                        className="h-full bg-gold-500/60 rounded transition-all"
                                        style={{ width: `${(post.save_rate / maxSaveRate) * 100}%` }}
                                    />
                                </div>
                                <div className="text-2xs text-text-secondary font-mono w-12 text-right shrink-0">
                                    {(post.save_rate * 100).toFixed(1)}%
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Published content table */}
                <div className="panel rounded-lg overflow-hidden">
                    <div className="px-4 py-3 border-b border-border-subtle">
                        <div className="text-2xs text-text-muted font-mono uppercase tracking-wider">Published Content</div>
                    </div>
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-border-subtle">
                                {["Task", "Title", "Role", "Impressions", "Saves", "Rate", "Comments", "DMs"].map(col => (
                                    <th key={col} className="px-4 py-2.5 text-left text-2xs font-mono text-text-muted uppercase tracking-wider">
                                        {col}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {data.posts.map(post => (
                                <tr key={post.task_id} className="border-b border-border-subtle hover:bg-surface-800 transition-colors">
                                    <td className="px-4 py-3">
                                        <Link href={`/workshop/${post.task_id}`} className="text-2xs text-gold-400 font-mono hover:underline">
                                            {post.task_id}
                                        </Link>
                                    </td>
                                    <td className="px-4 py-3 text-text-primary max-w-[200px] truncate">{post.title}</td>
                                    <td className="px-4 py-3 text-text-muted capitalize text-xs">{post.role}</td>
                                    <td className="px-4 py-3 text-text-secondary">{post.impressions.toLocaleString()}</td>
                                    <td className="px-4 py-3 text-text-secondary">{post.saves}</td>
                                    <td className={clsx("px-4 py-3 font-medium", post.save_rate > 0.04 ? "text-green-400" : post.save_rate > 0.02 ? "text-amber-400" : "text-orange-400")}>
                                        {(post.save_rate * 100).toFixed(1)}%
                                    </td>
                                    <td className="px-4 py-3 text-text-secondary">{post.comments}</td>
                                    <td className="px-4 py-3 text-text-muted">{(post as PostMetrics & { dms?: number }).dms ?? "—"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
