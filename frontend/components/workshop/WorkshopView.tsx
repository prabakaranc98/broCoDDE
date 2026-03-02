"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { streamChat } from "@/lib/sse";
import { ChatInput } from "@/components/workshop/ChatInput";
import { LifecycleBar } from "@/components/workshop/LifecycleBar";
import type { CoddeTask, ChatMessage, LifecycleStage, Role, Intent } from "@/lib/types";
import { STAGE_LABELS } from "@/lib/types";
import { ArrowUpCircle, ChevronDown, ChevronRight } from "lucide-react";
import clsx from "clsx";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface WorkshopViewProps {
    taskId: string;
}

// ── Shared markdown renderer ───────────────────────────────────────────────────
// Used for both completed messages and live streaming content.

const MARKDOWN_COMPONENTS = {
    p: ({ node, ...props }: any) => (
        <p className="mb-3 last:mb-0 leading-relaxed" {...props} />
    ),
    h1: ({ node, ...props }: any) => (
        <h1 className="text-base font-semibold text-text-primary mb-2 mt-5 first:mt-0" {...props} />
    ),
    h2: ({ node, ...props }: any) => (
        <h2 className="text-sm font-semibold text-text-primary mb-2 mt-4 first:mt-0 border-b border-border-subtle pb-1" {...props} />
    ),
    h3: ({ node, ...props }: any) => (
        <h3 className="text-sm font-medium text-gold-300/80 mb-1.5 mt-3 first:mt-0" {...props} />
    ),
    ul: ({ node, ...props }: any) => (
        <ul className="list-disc ml-5 mb-3 space-y-1" {...props} />
    ),
    ol: ({ node, ...props }: any) => (
        <ol className="list-decimal ml-5 mb-3 space-y-1" {...props} />
    ),
    li: ({ node, ...props }: any) => (
        <li className="leading-relaxed" {...props} />
    ),
    strong: ({ node, ...props }: any) => (
        <strong className="font-semibold text-text-primary" {...props} />
    ),
    em: ({ node, ...props }: any) => (
        <em className="italic text-text-muted" {...props} />
    ),
    hr: ({ node, ...props }: any) => (
        <hr className="border-border-subtle my-4" {...props} />
    ),
    blockquote: ({ node, ...props }: any) => (
        <blockquote
            className="border-l-2 border-gold-500/40 pl-3 my-3 italic text-text-muted"
            {...props}
        />
    ),
    // Block code: pre wraps code — pre component handles the container to avoid <pre> inside <p>
    pre: ({ node, children, ...props }: any) => (
        <pre
            className="bg-surface-800 text-text-secondary p-3 rounded-lg overflow-x-auto my-3 text-xs font-mono border border-border-subtle"
            {...props}
        >
            {children}
        </pre>
    ),
    code: ({ node, inline, children, ...props }: any) =>
        inline ? (
            <code
                className="bg-surface-800 text-gold-200 px-1 py-0.5 rounded text-xs font-mono"
                {...props}
            >
                {children}
            </code>
        ) : (
            <code {...props}>{children}</code>
        ),
    // Links — open in new tab
    a: ({ node, href, children, ...props }: any) => (
        <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-gold-400 hover:text-gold-300 underline underline-offset-2 decoration-gold-400/40 hover:decoration-gold-300/60 transition-colors"
            {...props}
        >
            {children}
        </a>
    ),
    // Tables
    table: ({ node, ...props }: any) => (
        <div className="overflow-x-auto my-3 rounded-lg border border-border-subtle">
            <table className="min-w-full text-xs border-collapse" {...props} />
        </div>
    ),
    thead: ({ node, ...props }: any) => (
        <thead className="bg-surface-700/60 border-b border-border-default" {...props} />
    ),
    tbody: ({ node, ...props }: any) => (
        <tbody className="divide-y divide-border-subtle" {...props} />
    ),
    tr: ({ node, ...props }: any) => (
        <tr className="hover:bg-surface-700/20 transition-colors" {...props} />
    ),
    th: ({ node, ...props }: any) => (
        <th
            className="text-left px-3 py-2 font-medium text-text-primary whitespace-nowrap text-xs"
            {...props}
        />
    ),
    td: ({ node, ...props }: any) => (
        <td className="px-3 py-2 text-text-secondary" {...props} />
    ),
};

// ── Component ──────────────────────────────────────────────────────────────────

export function WorkshopView({ taskId }: WorkshopViewProps) {
    const router = useRouter();
    const [task, setTask] = useState<CoddeTask | null>(null);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamingContent, setStreamingContent] = useState("");
    const [thinkingActive, setThinkingActive] = useState(false);
    const [toolLog, setToolLog] = useState<string[]>([]);  // tool calls fired this stream
    const thinkingRef = useRef("");           // accumulates thinking during current stream
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const proactiveTriggered = useRef(false);

    // Load task
    useEffect(() => {
        api.tasks.get(taskId).then((t) => {
            setTask(t);
            if (t.chat_history && t.chat_history.length > 0) {
                setMessages(t.chat_history);
            }
        }).catch(console.error);
    }, [taskId]);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, streamingContent, thinkingActive]);

    // Proactive agent opening — fires once when a fresh task loads with no history
    useEffect(() => {
        if (!task || proactiveTriggered.current || messages.length > 0 || isStreaming) return;
        if (task.stage !== "discovery") return;
        proactiveTriggered.current = true;

        setIsStreaming(true);
        setStreamingContent("");
        setToolLog([]);
        thinkingRef.current = "";
        let accumulated = "";

        streamChat({
            taskId,
            message: `[AUTO_OPEN] New session started. Role: ${task.role || "creator"}, Intent: ${task.intent || "teach"}, Domain: ${task.domain || "general"}. Open with a Discovery brief — scan your memory, run compute_patterns, then present 3 specific content angles.`,
            onAdvanceStage: () => {},
            onTitleUpdate: (title) => {
                setTask(prev => prev ? { ...prev, title } : prev);
                api.tasks.update(taskId, { title }).catch(console.error);
            },
            onToolCall: (name) => {
                setToolLog(prev => prev.includes(name) ? prev : [...prev, name]);
            },
            onThinking: (chunk) => {
                thinkingRef.current += chunk;
                setThinkingActive(true);
            },
            onChunk: (chunk) => {
                setThinkingActive(false);
                accumulated += chunk;
                setStreamingContent(accumulated);
            },
            onDone: () => {
                const agentMsg: ChatMessage = {
                    id: Math.random().toString(36).substring(2, 15),
                    role: "agent",
                    content: accumulated,
                    thinking: thinkingRef.current || undefined,
                    agent_name: "Strategist",
                    stage: task.stage,
                    timestamp: new Date().toISOString(),
                };
                setMessages([agentMsg]);
                setIsStreaming(false);
                setStreamingContent("");
                setThinkingActive(false);
                setToolLog([]);
            },
            onError: () => {
                setIsStreaming(false);
                setStreamingContent("");
                setThinkingActive(false);
                setToolLog([]);
                proactiveTriggered.current = false;
            },
        });
    }, [task, messages.length, isStreaming, taskId]);

    const advanceStage = useCallback(async () => {
        if (!task) return;
        const stages: LifecycleStage[] = [
            "discovery", "extraction", "structuring", "drafting", "vetting", "ready", "post-mortem"
        ];
        const current = stages.indexOf(task.stage);
        const next = stages[current + 1];
        if (!next) return;
        const updated = await api.tasks.updateStage(taskId, next);
        setTask(updated);
    }, [task, taskId]);

    const handleSend = useCallback(async (text: string) => {
        if (!task) return;

        const userMsg: ChatMessage = {
            id: (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function")
                ? crypto.randomUUID()
                : Math.random().toString(36).substring(2, 15),
            role: "user",
            content: text,
            timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, userMsg]);
        setIsStreaming(true);
        setStreamingContent("");
        setToolLog([]);
        thinkingRef.current = "";

        let accumulated = "";

        await streamChat({
            taskId,
            message: text,
            onAdvanceStage: () => advanceStage(),
            onTitleUpdate: (title) => {
                setTask(prev => prev ? { ...prev, title } : prev);
                api.tasks.update(taskId, { title }).catch(console.error);
            },
            onToolCall: (name) => {
                setToolLog(prev => prev.includes(name) ? prev : [...prev, name]);
            },
            onThinking: (chunk) => {
                thinkingRef.current += chunk;
                setThinkingActive(true);
            },
            onChunk: (chunk) => {
                setThinkingActive(false);
                accumulated += chunk;
                setStreamingContent(accumulated);
            },
            onDone: () => {
                const agentMsg: ChatMessage = {
                    id: (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function")
                        ? crypto.randomUUID()
                        : Math.random().toString(36).substring(2, 15),
                    role: "agent",
                    content: accumulated,
                    thinking: thinkingRef.current || undefined,
                    agent_name: getAgentName(task.stage),
                    stage: task.stage,
                    timestamp: new Date().toISOString(),
                };
                setMessages(prev => [...prev, agentMsg]);
                setIsStreaming(false);
                setStreamingContent("");
                setThinkingActive(false);
                setToolLog([]);
            },
            onError: (err) => {
                setMessages(prev => [...prev, {
                    id: (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function")
                        ? crypto.randomUUID()
                        : Math.random().toString(36).substring(2, 15),
                    role: "agent",
                    content: `[Error: ${err.message}]`,
                    timestamp: new Date().toISOString(),
                }]);
                setIsStreaming(false);
                setStreamingContent("");
                setThinkingActive(false);
                setToolLog([]);
            },
        });
    }, [task, taskId, advanceStage]);

    if (!task) {
        return (
            <div className="h-full flex items-center justify-center text-text-muted text-sm">
                Loading task…
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col">
            {/* Lifecycle stage bar */}
            <LifecycleBar task={task} onAdvance={advanceStage} />

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
                {messages.length === 0 && (
                    <div className="text-center text-text-muted text-sm py-12">
                        <div className="text-2xl mb-3">
                            {stageEmoji(task.stage)}
                        </div>
                        <div className="font-medium text-text-secondary mb-1">
                            {STAGE_LABELS[task.stage]} stage
                        </div>
                        <div className="text-xs max-w-sm mx-auto leading-relaxed">
                            {stagePrompt(task.stage)}
                        </div>
                    </div>
                )}

                {messages.map(msg => (
                    <MessageBubble key={msg.id} message={msg} />
                ))}

                {/* ── Loading indicator with collapsible activity details ── */}
                {isStreaming && !streamingContent && (
                    <StreamingIndicator
                        stage={task.stage}
                        toolLog={toolLog}
                        thinkingActive={thinkingActive}
                        thinkingRef={thinkingRef}
                    />
                )}

                {/* ── Streaming response — rendered as markdown ── */}
                {isStreaming && streamingContent && (
                    <div className="flex gap-3">
                        <div className="w-6 h-6 rounded bg-gold-500/20 flex items-center justify-center shrink-0 mt-0.5">
                            <span className="text-gold-400 text-xs">{agentInitial(task.stage)}</span>
                        </div>
                        <div className="flex-1 text-sm text-text-secondary min-w-0">
                            <div className="markdown-body">
                                <ReactMarkdown
                                    remarkPlugins={[remarkGfm]}
                                    components={MARKDOWN_COMPONENTS}
                                >
                                    {streamingContent}
                                </ReactMarkdown>
                            </div>
                            <span className="inline-block w-1.5 h-3.5 bg-gold-400 ml-0.5 animate-pulse align-text-bottom" />
                        </div>
                    </div>
                )}


                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="px-6 pb-4 pt-2 border-t border-border-subtle">
                <ChatInput
                    onSend={handleSend}
                    isStreaming={isStreaming}
                    placeholder={inputPlaceholder(task.stage)}
                />
                <div className="flex items-center justify-between mt-1.5">
                    <span className="text-2xs text-text-muted font-mono">
                        {getAgentName(task.stage)} · {task.role || "no role set"}
                    </span>
                    {task.stage !== "post-mortem" && (
                        <button
                            onClick={advanceStage}
                            className="flex items-center gap-1 text-2xs text-text-muted hover:text-gold-400 transition-colors font-mono"
                        >
                            <ArrowUpCircle size={11} />
                            Advance stage
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

// ── Message bubble ─────────────────────────────────────────────────────────────

function MessageBubble({ message }: { message: ChatMessage }) {
    const isUser = message.role === "user";
    const [thinkingOpen, setThinkingOpen] = useState(false);

    return (
        <div className={clsx("flex gap-3 items-end", isUser && "flex-row-reverse")}>
            {/* Avatar — hidden for user (bubble speaks for itself) */}
            {!isUser && (
                <div className="w-6 h-6 rounded bg-gold-500/20 flex items-center justify-center shrink-0 mb-0.5 text-xs text-gold-400">
                    {message.agent_name?.[0] || "A"}
                </div>
            )}
            <div className={clsx(
                "min-w-0",
                isUser ? "flex justify-end" : "flex-1 text-sm text-text-secondary"
            )}>
                {isUser ? (
                    // ── User bubble — contained, compact, right-aligned ──
                    <div className="max-w-[72%] bg-surface-700 border border-border-subtle rounded-2xl rounded-br-sm px-3.5 py-2 text-sm text-text-primary leading-relaxed whitespace-pre-wrap break-words">
                        {message.content}
                    </div>
                ) : (
                    <>
                        {/* Thinking — collapsible, frontier style */}
                        {message.thinking && (
                            <button
                                onClick={() => setThinkingOpen(o => !o)}
                                className="flex items-center gap-1.5 mb-2 text-[11px] text-text-muted/50 hover:text-text-muted/80 transition-colors font-mono group"
                            >
                                {thinkingOpen
                                    ? <ChevronDown size={11} className="text-gold-400/40 group-hover:text-gold-400/60" />
                                    : <ChevronRight size={11} className="text-gold-400/40 group-hover:text-gold-400/60" />
                                }
                                <span>
                                    {thinkingOpen ? "Hide" : "Show"} reasoning
                                    <span className="ml-1 opacity-50">
                                        ({Math.round(message.thinking.length / 5)} tokens est.)
                                    </span>
                                </span>
                            </button>
                        )}
                        {message.thinking && thinkingOpen && (
                            <div className="mb-3 border-l-2 border-border-subtle/40 pl-3">
                                <div className="text-[11px] text-text-muted/40 font-mono leading-relaxed whitespace-pre-wrap max-h-64 overflow-y-auto">
                                    {message.thinking}
                                </div>
                            </div>
                        )}
                        {/* Main response */}
                        <div className="markdown-body">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={MARKDOWN_COMPONENTS}
                            >
                                {message.content}
                            </ReactMarkdown>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}

// ── Streaming activity indicator ───────────────────────────────────────────────
// Collapsed by default — just bounce dots. Expand to see tool calls + reasoning.

function StreamingIndicator({
    stage,
    toolLog,
    thinkingActive,
    thinkingRef,
}: {
    stage: LifecycleStage;
    toolLog: string[];
    thinkingActive: boolean;
    thinkingRef: React.MutableRefObject<string>;
}) {
    const [open, setOpen] = useState(false);
    const hasActivity = toolLog.length > 0 || thinkingActive;

    return (
        <div className="flex gap-3">
            <div className="w-6 h-6 rounded bg-gold-500/20 flex items-center justify-center shrink-0 mt-0.5">
                <span className="text-gold-400 text-xs">{agentInitial(stage)}</span>
            </div>
            <div className="flex-1 min-w-0">
                {/* Primary row: bounce dots + optional expand toggle */}
                <div className="flex items-center gap-2 py-1">
                    <div className="flex gap-1 items-center">
                        {[0, 150, 300].map(d => (
                            <div
                                key={d}
                                className="w-1.5 h-1.5 rounded-full bg-gold-400/60 animate-bounce"
                                style={{ animationDelay: `${d}ms` }}
                            />
                        ))}
                    </div>
                    {hasActivity && (
                        <button
                            onClick={() => setOpen(o => !o)}
                            className="flex items-center gap-0.5 text-[10px] text-text-muted/35 hover:text-text-muted/60 transition-colors font-mono"
                        >
                            {open
                                ? <ChevronDown size={9} />
                                : <ChevronRight size={9} />
                            }
                            <span>{open ? "hide" : "details"}</span>
                        </button>
                    )}
                </div>

                {/* Expandable details — tool calls + reasoning snippet */}
                {open && hasActivity && (
                    <div className="mt-0.5 pl-1 border-l border-border-subtle/30 space-y-1">
                        {toolLog.map((name, i) => {
                            const isActive = i === toolLog.length - 1 && thinkingActive === false;
                            return (
                                <div key={name} className="flex items-center gap-1.5">
                                    <span className={clsx(
                                        "text-[9px] font-mono px-1.5 py-px rounded border",
                                        isActive
                                            ? "border-gold-400/30 text-gold-400/50 bg-gold-500/5"
                                            : "border-border-subtle/30 text-text-muted/25"
                                    )}>
                                        {friendlyToolName(name)}
                                    </span>
                                    {!isActive && (
                                        <span className="text-[8px] text-text-muted/20">✓</span>
                                    )}
                                </div>
                            );
                        })}
                        {thinkingActive && (
                            <div className="text-[9px] text-text-muted/30 font-mono italic truncate max-w-xs">
                                {thinkingRef.current.trim().split("\n").filter(Boolean).at(-1) || "Reasoning…"}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}


// ── Helpers ────────────────────────────────────────────────────────────────────

function getAgentName(stage: LifecycleStage): string {
    const map: Record<LifecycleStage, string> = {
        discovery: "Strategist",
        extraction: "Interviewer",
        structuring: "Shaper",
        drafting: "Shaper",
        vetting: "Shaper",
        ready: "Shaper",
        "post-mortem": "Analyst",
    };
    return map[stage] || "Agent";
}

function agentInitial(stage: LifecycleStage): string {
    return getAgentName(stage)[0];
}

function stageEmoji(stage: LifecycleStage): string {
    const map: Record<LifecycleStage, string> = {
        discovery: "🔭", extraction: "🎙️", structuring: "🗺️",
        drafting: "✍️", vetting: "⚖️", ready: "✅", "post-mortem": "📊",
    };
    return map[stage] || "💬";
}

function stagePrompt(stage: LifecycleStage): string {
    const map: Record<LifecycleStage, string> = {
        discovery: "The Strategist opens with a brief — three angles worth exploring based on your domains, performance, and what's trending.",
        extraction: "The Interviewer pulls insight out of you. One question at a time. Be specific.",
        structuring: "The Shaper proposes a skeleton — archetype, hook, three key points, landing.",
        drafting: "You write. Ask the Shaper for feedback on specific choices.",
        vetting: "Paste your draft. The Shaper runs all six lint checks using AI.",
        ready: "Publish-ready. Use the Shaper for platform formatting.",
        "post-mortem": "Share your metrics. The Analyst does a causal breakdown.",
    };
    return map[stage] || "Start chatting.";
}

function friendlyToolName(raw: string): string {
    const map: Record<string, string> = {
        get_hf_daily_papers: "Scanning today's papers",
        search_hf_papers: "Searching HF papers",
        search_hackernews: "Checking HackerNews",
        search_news: "Scanning tech news",
        search_research: "Searching research",
        search_underrated: "Finding niche angles",
        compute_patterns: "Computing your patterns",
        compute_patterns_tool: "Computing your patterns",
        search_memories: "Reading memory",
        add_memory: "Writing to memory",
        update_memory: "Updating memory",
        memory_update: "Updating memory",
        web_search: "Web search",
        web_search_tool: "Web search",
        web_fetch: "Fetching article",
        web_fetch_tool: "Fetching article",
        skill_load: "Loading skill",
        lint_draft_tool: "Running lint checks",
        export_task_tool: "Exporting task",
        format_for_platform_tool: "Formatting for platform",
    };
    return map[raw] ?? raw.replace(/_/g, " ");
}

function inputPlaceholder(stage: LifecycleStage): string {
    const map: Record<LifecycleStage, string> = {
        discovery: "What are you thinking about lately? Or say 'open a brief'…",
        extraction: "Keep going — one more question…",
        structuring: "React to the skeleton, or say 'looks good'…",
        drafting: "Paste a section or ask about a specific choice…",
        vetting: "Paste your full draft to run the lint check…",
        ready: "Paste the final draft for platform formatting, or say 'done'…",
        "post-mortem": "Share your metrics: impressions, saves, comments, DMs…",
    };
    return map[stage] || "Message the agent…";
}
