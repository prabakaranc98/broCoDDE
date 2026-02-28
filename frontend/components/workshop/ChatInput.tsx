"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { Mic, MicOff, Send, Loader2 } from "lucide-react";
import clsx from "clsx";

interface ChatInputProps {
    onSend: (message: string) => void;
    isStreaming: boolean;
    placeholder?: string;
}

// Type augmentation for Web Speech API (not in @types/react-dom yet)
declare global {
    interface Window {
        SpeechRecognition?: SpeechRecognitionConstructor;
        webkitSpeechRecognition?: SpeechRecognitionConstructor;
    }
    type SpeechRecognitionConstructor = new () => SpeechRecognitionInstance;
    interface SpeechRecognitionInstance extends EventTarget {
        continuous: boolean;
        interimResults: boolean;
        lang: string;
        start(): void;
        stop(): void;
        onresult: ((event: SpeechRecognitionEvent) => void) | null;
        onend: (() => void) | null;
        onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
    }
    interface SpeechRecognitionEvent extends Event {
        results: SpeechRecognitionResultList;
        resultIndex: number;
    }
    interface SpeechRecognitionErrorEvent extends Event {
        error: string;
    }
    interface SpeechRecognitionResultList {
        readonly length: number;
        [index: number]: SpeechRecognitionResult;
    }
    interface SpeechRecognitionResult {
        readonly length: number;
        readonly isFinal: boolean;
        [index: number]: SpeechRecognitionAlternative;
    }
    interface SpeechRecognitionAlternative {
        readonly transcript: string;
        readonly confidence: number;
    }
}

export function ChatInput({ onSend, isStreaming, placeholder }: ChatInputProps) {
    const [text, setText] = useState("");
    const [isListening, setIsListening] = useState(false);
    const [voiceSupported, setVoiceSupported] = useState(false);
    const [interimTranscript, setInterimTranscript] = useState("");
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);

    // Check for Web Speech API support
    useEffect(() => {
        const SpeechRecognition =
            window.SpeechRecognition || window.webkitSpeechRecognition;
        setVoiceSupported(!!SpeechRecognition);
    }, []);

    // Auto-resize textarea
    useEffect(() => {
        const ta = textareaRef.current;
        if (!ta) return;
        ta.style.height = "auto";
        ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`;
    }, [text]);

    const startListening = useCallback(() => {
        const SpeechRecognition =
            window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) return;

        const rec = new SpeechRecognition();
        rec.continuous = true;
        rec.interimResults = true;
        rec.lang = "en-US";

        rec.onresult = (event) => {
            let interim = "";
            let final = "";
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    final += transcript;
                } else {
                    interim += transcript;
                }
            }
            if (final) {
                setText(prev => {
                    const joined = (prev + " " + final).trim();
                    return joined;
                });
                setInterimTranscript("");
            } else {
                setInterimTranscript(interim);
            }
        };

        rec.onend = () => {
            setIsListening(false);
            setInterimTranscript("");
        };

        rec.onerror = (event) => {
            console.warn("SpeechRecognition error:", event.error);
            setIsListening(false);
            setInterimTranscript("");
        };

        recognitionRef.current = rec;
        rec.start();
        setIsListening(true);
    }, []);

    const stopListening = useCallback(() => {
        recognitionRef.current?.stop();
        setIsListening(false);
        setInterimTranscript("");
    }, []);

    const handleVoiceToggle = useCallback(() => {
        if (isListening) stopListening();
        else startListening();
    }, [isListening, startListening, stopListening]);

    const handleSend = useCallback(() => {
        const trimmed = text.trim();
        if (!trimmed || isStreaming) return;
        onSend(trimmed);
        setText("");
        setInterimTranscript("");
        if (isListening) stopListening();
    }, [text, isStreaming, onSend, isListening, stopListening]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const displayText = text + (interimTranscript ? " " + interimTranscript : "");

    return (
        <div className={clsx(
            "border rounded-lg transition-colors",
            isListening
                ? "border-gold-500/60 bg-surface-800"
                : "border-border-default bg-surface-800 focus-within:border-border-emphasis"
        )}>
            {/* Voice interim transcript indicator */}
            {isListening && interimTranscript && (
                <div className="px-3 pt-2 text-xs text-text-muted italic">
                    {interimTranscript}
                </div>
            )}

            <div className="flex items-end gap-2 p-2">
                <textarea
                    ref={textareaRef}
                    value={displayText}
                    onChange={e => setText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder || "Message the agent… (⏎ to send, Shift+⏎ for newline)"}
                    className="flex-1 bg-transparent text-sm text-text-primary placeholder:text-text-muted
                     resize-none outline-none min-h-[36px] max-h-[200px] py-1.5 px-1 font-sans leading-relaxed"
                    rows={1}
                    disabled={isStreaming}
                />

                <div className="flex items-center gap-1.5 pb-0.5 shrink-0">
                    {/* Voice button */}
                    {voiceSupported && (
                        <button
                            onClick={handleVoiceToggle}
                            title={isListening ? "Stop recording" : "Voice input"}
                            className={clsx(
                                "p-1.5 rounded transition-colors",
                                isListening
                                    ? "text-gold-400 bg-gold-500/10 hover:bg-gold-500/20 animate-pulse-slow"
                                    : "text-text-muted hover:text-text-secondary hover:bg-surface-700"
                            )}
                        >
                            {isListening ? <MicOff size={16} /> : <Mic size={16} />}
                        </button>
                    )}

                    {/* Send button */}
                    <button
                        onClick={handleSend}
                        disabled={!text.trim() || isStreaming}
                        className="p-1.5 rounded bg-gold-500/10 hover:bg-gold-500/20 text-gold-400
                       disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                        title="Send (⏎)"
                    >
                        {isStreaming ? (
                            <Loader2 size={16} className="animate-spin" />
                        ) : (
                            <Send size={16} />
                        )}
                    </button>
                </div>
            </div>

            {/* Voice status strip */}
            {isListening && (
                <div className="flex items-center gap-2 px-3 pb-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-gold-400 animate-pulse" />
                    <span className="text-2xs text-gold-400 font-mono">Listening…</span>
                    <span className="text-2xs text-text-muted">|  Shift+⏎ for newline  |  ⏎ to send</span>
                </div>
            )}
        </div>
    );
}
