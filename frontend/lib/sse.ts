/**
 * BroCoDDE — SSE Client for streaming chat
 * Connects to /tasks/:id/chat and streams agent response chunks.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface StreamOptions {
    taskId: string;
    message: string;
    userId?: string;
    deepCritique?: boolean;
    onAdvanceStage?: () => void;
    onChunk: (text: string) => void;
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

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
                if (!line.startsWith("data: ")) continue;
                const data = line.slice(6).trim();

                if (data === "[DONE]") {
                    onDone();
                    return;
                }
                if (data && data !== "") {
                    // Unescape newlines encoded by the backend
                    let unescaped = data.replace(/\\n/g, "\n");
                    if (unescaped.includes("[ADVANCE_STAGE]")) {
                        if (options.onAdvanceStage) {
                            options.onAdvanceStage();
                        }
                        unescaped = unescaped.replace("[ADVANCE_STAGE]", "");
                    }
                    if (unescaped.trim().length > 0) {
                        onChunk(unescaped);
                    } else if (unescaped.includes(" ")) {
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
