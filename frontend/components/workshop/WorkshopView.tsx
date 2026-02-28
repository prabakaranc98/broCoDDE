"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { streamChat } from "@/lib/sse";
import { ChatInput } from "@/components/workshop/ChatInput";
import { LifecycleBar } from "@/components/workshop/LifecycleBar";
import type { CoddeTask, ChatMessage, LifecycleStage, Role, Intent } from "@/lib/types";
import { STAGE_LABELS } from "@/lib/types";
import { ChevronRight, ArrowUpCircle } from "lucide-react";
import clsx from "clsx";

interface WorkshopViewProps {
    taskId: string;
}

export function WorkshopView({ taskId }: WorkshopViewProps) {
    const router = useRouter();
    const [task, setTask] = useState<CoddeTask | null>(null);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamingContent, setStreamingContent] = useState("");
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Load task
    useEffect(() => {
        api.tasks.get(taskId).then(setTask).catch(console.error);
    }, [taskId]);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, streamingContent]);

    const handleSend = useCallback(async (text: string) => {
        if (!task) return;

        const userMsg: ChatMessage = {
            id: crypto.randomUUID(),
            role: "user",
            content: text,
            timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, userMsg]);
        setIsStreaming(true);
        setStreamingContent("");

        let accumulated = "";

        await streamChat({
            taskId,
            message: text,
            onChunk: (chunk) => {
                accumulated += chunk;
                setStreamingContent(accumulated);
            },
            onDone: () => {
                const agentMsg: ChatMessage = {
                    id: crypto.randomUUID(),
                    role: "agent",
                    content: accumulated,
                    agent_name: getAgentName(task.stage),
                    stage: task.stage,
                    timestamp: new Date().toISOString(),
                };
                setMessages(prev => [...prev, agentMsg]);
                setIsStreaming(false);
                setStreamingContent("");
            },
            onError: (err) => {
                setMessages(prev => [...prev, {
                    id: crypto.randomUUID(),
                    role: "agent",
                    content: `[Error: ${err.message}]`,
                    timestamp: new Date().toISOString(),
                }]);
                setIsStreaming(false);
                setStreamingContent("");
            },
        });
    }, [task, taskId]);

    const advanceStage = async () => {
        if (!task) return;
        const stages: LifecycleStage[] = [
            "discovery", "extraction", "structuring", "drafting", "vetting", "ready", "post-mortem"
        ];
        const current = stages.indexOf(task.stage);
        const next = stages[current + 1];
        if (!next) return;
        const updated = await api.tasks.updateStage(taskId, next);
        setTask(updated);
    };

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
                        <div className="text-xs max-w-sm mx-auto">
                            {stagePrompt(task.stage)}
                        </div>
                    </div>
                )}

                {messages.map(msg => (
                    <MessageBubble key={msg.id} message={msg} />
                ))}

                {/* Streaming in-progress */}
                {isStreaming && streamingContent && (
                    <div className="flex gap-3">
                        <div className="w-6 h-6 rounded bg-gold-500/20 flex items-center justify-center shrink-0 mt-0.5">
                            <span className="text-gold-400 text-xs">{agentInitial(task.stage)}</span>
                        </div>
                        <div className="flex-1 text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">
                            {streamingContent}
                            <span className="inline-block w-1.5 h-3.5 bg-gold-400 ml-0.5 animate-pulse" />
                        </div>
                    </div>
                )}

                {isStreaming && !streamingContent && (
                    <div className="flex gap-3">
                        <div className="w-6 h-6 rounded bg-gold-500/20 flex items-center justify-center shrink-0">
                            <span className="text-gold-400 text-xs">{agentInitial(task.stage)}</span>
                        </div>
                        <div className="flex gap-1 items-center py-1">
                            {[0, 150, 300].map(d => (
                                <div key={d} className="w-1.5 h-1.5 rounded-full bg-gold-400/60 animate-bounce"
                                    style={{ animationDelay: `${d}ms` }} />
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

function MessageBubble({ message }: { message: ChatMessage }) {
    const isUser = message.role === "user";
    return (
        <div className={clsx("flex gap-3", isUser && "flex-row-reverse")}>
            <div className={clsx(
                "w-6 h-6 rounded flex items-center justify-center shrink-0 mt-0.5 text-xs",
                isUser ? "bg-surface-700 text-text-muted" : "bg-gold-500/20 text-gold-400"
            )}>
                {isUser ? "U" : (message.agent_name?.[0] || "A")}
            </div>
            <div className={clsx(
                "flex-1 text-sm leading-relaxed whitespace-pre-wrap",
                isUser ? "text-text-primary text-right" : "text-text-secondary"
            )}>
                {message.content}
            </div>
        </div>
    );
}

// ── Helpers ───────────────────────────────────────────────────────────────────

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
        discovery: "The Strategist will open with a brief — three angles worth exploring based on your domains, performance, and what's trending.",
        extraction: "The Interviewer will pull the insight out of you. One question at a time. Be specific.",
        structuring: "The Strategist will propose a skeleton — archetype, hook, three key points, landing.",
        drafting: "You write. Ask the Shaper for feedback on specific choices.",
        vetting: "Paste your draft. The Shaper will run all six lint checks using AI.",
        ready: "Publish-ready. Use the Shaper for platform formatting if needed.",
        "post-mortem": "Share your metrics. The Analyst will do a causal breakdown.",
    };
    return map[stage] || "Start chatting.";
}

function inputPlaceholder(stage: LifecycleStage): string {
    const map: Record<LifecycleStage, string> = {
        discovery: "What are you thinking about lately? Or just say 'open a brief'…",
        extraction: "Keep going — the Interviewer has one more question…",
        structuring: "React to the skeleton, ask for changes, or say 'looks good'…",
        drafting: "Paste a section or ask a specific question about your draft…",
        vetting: "Paste your full draft here to run the lint check…",
        ready: "Paste the final draft for platform formatting, or say 'done'…",
        "post-mortem": "Share your metrics: impressions, saves, comments, DMs…",
    };
    return map[stage] || "Message the agent…";
}
