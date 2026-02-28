/**
 * BroCoDDE — API Client
 * Typed fetch wrapper for the FastAPI backend.
 */

const BASE_URL = typeof window !== "undefined"
    ? "http://localhost:8000"
    : (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000");

class ApiError extends Error {
    constructor(public status: number, message: string) {
        super(message);
        this.name = "ApiError";
    }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${BASE_URL}${path}`, {
        headers: { "Content-Type": "application/json", ...options?.headers },
        ...options,
    });
    if (!res.ok) {
        const text = await res.text().catch(() => "Unknown error");
        throw new ApiError(res.status, text);
    }
    return res.json() as Promise<T>;
}

// ── Tasks ─────────────────────────────────────────────────────────────────────

export const api = {
    tasks: {
        list: (stage?: string, series_id?: string) => {
            const params = new URLSearchParams();
            if (stage) params.append("stage", stage);
            if (series_id) params.append("series_id", series_id);
            const qs = params.toString();
            return request<import("./types").CoddeTask[]>(`/tasks${qs ? `?${qs}` : ""}`);
        },
        get: (id: string) => request<import("./types").CoddeTask>(`/tasks/${id}`),
        create: (data: { role: string; intent: string; domain?: string; series_id?: string; title?: string }) =>
            request<import("./types").CoddeTask>("/tasks", {
                method: "POST",
                body: JSON.stringify(data),
            }),
        updateStage: (id: string, stage: string) =>
            request<import("./types").CoddeTask>(`/tasks/${id}/stage`, {
                method: "PATCH",
                body: JSON.stringify({ stage }),
            }),
        update: (id: string, data: Record<string, unknown>) =>
            request<import("./types").CoddeTask>(`/tasks/${id}`, {
                method: "PATCH",
                body: JSON.stringify(data),
            }),
        saveDraft: (id: string, content: string) =>
            request<{ version: number; saved: boolean }>(`/tasks/${id}/drafts`, {
                method: "POST",
                body: JSON.stringify({ content }),
            }),
        logMetrics: (id: string, metrics: Record<string, unknown>) =>
            request<unknown>(`/tasks/${id}/metrics`, {
                method: "POST",
                body: JSON.stringify(metrics),
            }),
    },

    series: {
        list: () => request<import("./types").Series[]>("/series"),
        get: (id: string) => request<import("./types").Series & { tasks: any[] }>(`/series/${id}`),
        create: (data: { name: string; description?: string; archetype?: string; icon?: string }) =>
            request<import("./types").Series>("/series", {
                method: "POST",
                body: JSON.stringify(data),
            }),
    },

    memory: {
        list: () => request<import("./types").MemoryEntry[]>("/memory"),
        create: (data: { type: string; text: string; tags?: string[] }) =>
            request<import("./types").MemoryEntry>("/memory", {
                method: "POST",
                body: JSON.stringify(data),
            }),
        update: (id: string, text: string) =>
            request<import("./types").MemoryEntry>(`/memory/${id}`, {
                method: "PATCH",
                body: JSON.stringify({ text }),
            }),
        delete: (id: string) =>
            fetch(`${BASE_URL}/memory/${id}`, { method: "DELETE" }),
        domains: {
            list: () => request<import("./types").KnowledgeDomain[]>("/memory/domains"),
            create: (data: { name: string; color?: string; tags?: string[] }) =>
                request<import("./types").KnowledgeDomain>("/memory/domains", {
                    method: "POST",
                    body: JSON.stringify(data),
                }),
        },
    },

    observatory: {
        get: () => request<import("./types").ObservatoryData>("/observatory"),
    },

    skills: {
        list: () => request<{ name: string; description: string; dir: string }[]>("/skills"),
        get: (name: string) => request<{ name: string; content: string }>(`/skills/${name}`),
    },

    health: () => request<{ status: string; version: string; provider: string; mock_mode: boolean }>("/health"),
};
