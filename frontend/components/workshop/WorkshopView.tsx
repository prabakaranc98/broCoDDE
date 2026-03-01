"use client";

import { useState, useEffect, useRef, useCallback } from "react";
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
    code: ({ node, inline, ...props }: any) =>
        inline ? (
            <code
                className="bg-surface-800 text-gold-200 px-1 py-0.5 rounded text-xs font-mono"
                {...props}
            />
        ) : (
            <pre className="bg-surface-800 text-text-secondary p-3 rounded-lg overflow-x-auto my-3 text-xs font-mono border border-border-subtle">
                <code {...props} />
            </pre>
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
        thinkingRef.current = "";
        let accumulated = "";

        streamChat({
            taskId,
            message: `[AUTO_OPEN] New session started. Role: ${task.role || "creator"}, Intent: ${task.intent || "teach"}, Domain: ${task.domain || "general"}. Open with a Discovery brief — scan your memory, run compute_patterns, then present 3 specific content angles.`,
            onAdvanceStage: () => {},
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
            },
            onError: () => {
                setIsStreaming(false);
                setStreamingContent("");
                setThinkingActive(false);
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
        thinkingRef.current = "";

        let accumulated = "";

        await streamChat({
            taskId,
            message: text,
            onAdvanceStage: () => advanceStage(),
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

                {/* ── Thinking indicator — shown while reasoning, before content starts ── */}
                {isStreaming && thinkingActive && (
                    <div className="flex gap-3">
                        <div className="w-6 h-6 rounded bg-gold-500/20 flex items-center justify-center shrink-0 mt-0.5">
                            <span className="text-gold-400 text-xs">{agentInitial(task.stage)}</span>
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 text-xs text-text-muted/70 font-mono mb-1">
                                <span className="flex gap-0.5 items-center">
                                    {[0, 150, 300].map(d => (
                                        <span
                                            key={d}
                                            className="w-1 h-1 rounded-full bg-gold-400/50 animate-pulse"
                                            style={{ animationDelay: `${d}ms` }}
                                        />
                                    ))}
                                </span>
                                <span>Reasoning…</span>
                            </div>
                            {/* Last line of thinking as a subtle preview */}
                            <div className="text-[11px] text-text-muted/30 font-mono italic truncate max-w-md">
                                {thinkingRef.current.trim().split("\n").filter(Boolean).at(-1) || ""}
                            </div>
                        </div>
                    </div>
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

                {/* Typing indicator — waiting for first chunk, no thinking either */}
                {isStreaming && !streamingContent && !thinkingActive && (
                    <div className="flex gap-3">
                        <div className="w-6 h-6 rounded bg-gold-500/20 flex items-center justify-center shrink-0">
                            <span className="text-gold-400 text-xs">{agentInitial(task.stage)}</span>
                        </div>
                        <div className="flex gap-1 items-center py-1">
                            {[0, 150, 300].map(d => (
                                <div
                                    key={d}
                                    className="w-1.5 h-1.5 rounded-full bg-gold-400/60 animate-bounce"
                                    style={{ animationDelay: `${d}ms` }}
                                />
                            ))}
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
        <div className={clsx("flex gap-3", isUser && "flex-row-reverse")}>
            <div className={clsx(
                "w-6 h-6 rounded flex items-center justify-center shrink-0 mt-0.5 text-xs",
                isUser ? "bg-surface-700 text-text-muted" : "bg-gold-500/20 text-gold-400"
            )}>
                {isUser ? "U" : (message.agent_name?.[0] || "A")}
            </div>
            <div className={clsx(
                "flex-1 text-sm min-w-0 overflow-hidden",
                isUser ? "text-text-primary text-right" : "text-text-secondary"
            )}>
                {isUser ? (
                    <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>
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

// ── Helpers ────────────────────────────────────────────────────────────────────

function getAgentName(stage: LifecycleStage): string {
    const map: Record<LifecycleStage, string> = {
        discovery: "Strategist",
        extraction: "Interviewer",
        structuring: "Strategist",
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
        structuring: "The Strategist proposes a skeleton — archetype, hook, three key points, landing.",
        drafting: "You write. Ask the Shaper for feedback on specific choices.",
        vetting: "Paste your draft. The Shaper runs all six lint checks using AI.",
        ready: "Publish-ready. Use the Shaper for platform formatting.",
        "post-mortem": "Share your metrics. The Analyst does a causal breakdown.",
    };
    return map[stage] || "Start chatting.";
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
