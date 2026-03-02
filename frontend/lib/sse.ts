/**
 * BroCoDDE — SSE Client for streaming chat
 * Connects to /tasks/:id/chat and streams agent response chunks.
 *
 * SSE event types:
 *   (default) — regular message content → onChunk
 *   event: thinking — model reasoning/thinking → onThinking
 *   data: [DONE] — stream complete → onDone
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface StreamOptions {
    taskId: string;
    message: string;
    userId?: string;
    deepCritique?: boolean;
    onAdvanceStage?: () => void;
    onChunk: (text: string) => void;
    onThinking?: (text: string) => void;
    onTitleUpdate?: (title: string) => void;
    onDone: () => void;
    onError: (err: Error) => void;
}

/**
 * Stream a chat message to the agent via SSE.
 * Uses fetch + ReadableStream since EventSource doesn't support POST.
 */
export async function streamChat(options: StreamOptions): Promise<void> {
    const { taskId, message, userId = "default_user", deepCritique = false, onChunk, onDone, onError } = options;

    try {
        const response = await fetch(`${BASE_URL}/tasks/${taskId}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message,
                user_id: userId,
                deep_critique: deepCritique,
            }),
        });

        if (!response.ok || !response.body) {
            throw new Error(`Chat request failed: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        // Tracks the event type set by `event:` lines — resets to "message" on blank line
        let currentEventType = "message";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
                // Blank line = SSE event boundary — reset event type (per SSE spec)
                if (line === "" || line === "\r") {
                    currentEventType = "message";
                    continue;
                }

                // Event type declaration
                if (line.startsWith("event: ")) {
                    currentEventType = line.slice(7).replace(/\r$/, "");
                    continue;
                }

                if (!line.startsWith("data: ")) continue;

                // Preserve leading spaces — meaningful tokens in markdown content.
                // Only strip trailing carriage return (Windows line-ending safety).
                const data = line.slice(6).replace(/\r$/, "");

                if (data === "[DONE]") {
                    onDone();
                    return;
                }

                if (!data) continue;

                // Unescape newlines encoded by the backend
                let unescaped = data.replace(/\\n/g, "\n");

                if (currentEventType === "thinking") {
                    // Route reasoning tokens to the thinking callback
                    if (options.onThinking && unescaped.length > 0) {
                        options.onThinking(unescaped);
                    }
                } else {
                    // Regular message content
                    if (unescaped.includes("[ADVANCE_STAGE]")) {
                        if (options.onAdvanceStage) {
                            options.onAdvanceStage();
                        }
                        unescaped = unescaped.replace("[ADVANCE_STAGE]", "");
                    }
                    // Auto title update — strip macro, fire callback with extracted title
                    if (unescaped.includes("[TITLE:")) {
                        const titleMatch = unescaped.match(/\[TITLE:\s*([^\]]+)\]/);
                        if (titleMatch) {
                            const extracted = titleMatch[1].trim();
                            if (options.onTitleUpdate) {
                                options.onTitleUpdate(extracted);
                            }
                        }
                        unescaped = unescaped.replace(/\s*\[TITLE:[^\]]+\]\s*/g, " ").trim();
                    }
                    if (unescaped.length > 0) {
                        onChunk(unescaped);
                    }
                }
            }
        }

        onDone();
    } catch (err) {
        onError(err instanceof Error ? err : new Error(String(err)));
    }
}
