/**
 * BroCoDDE TypeScript Types
 * Mirrors all backend Pydantic models exactly.
 */

// ── Lifecycle ─────────────────────────────────────────────────────────────────

export type LifecycleStage =
    | "discovery"
    | "extraction"
    | "structuring"
    | "drafting"
    | "vetting"
    | "ready"
    | "post-mortem";

export const LIFECYCLE_STAGES: LifecycleStage[] = [
    "discovery",
    "extraction",
    "structuring",
    "drafting",
    "vetting",
    "ready",
    "post-mortem",
];

export const STAGE_LABELS: Record<LifecycleStage, string> = {
    discovery: "Discovery",
    extraction: "Extraction",
    structuring: "Structuring",
    drafting: "Drafting",
    vetting: "Vetting",
    ready: "Ready",
    "post-mortem": "Post-Mortem",
};

// ── Roles ─────────────────────────────────────────────────────────────────────

export type Role =
    | "researcher"
    | "reviewer"
    | "archaeologist"
    | "teacher"
    | "interviewer"
    | "coder"
    | "synthesizer"
    | "contrarian"
    | "storyteller"
    | "cartographer"
    | "scientific-illustrator"
    | "communicator";

export const ROLES: { id: Role; name: string; description: string; icon: string }[] = [
    { id: "researcher", name: "Researcher", description: "Methodological depth, hypothesis-driven", icon: "🔬" },
    { id: "reviewer", name: "Reviewer", description: "Critical evaluation of papers, tools, approaches", icon: "⚖️" },
    { id: "archaeologist", name: "Archaeologist", description: "Dig into past experience for buried insights", icon: "🏺" },
    { id: "teacher", name: "Teacher", description: "Explain deeply understood concepts clearly", icon: "📚" },
    { id: "interviewer", name: "Interviewer", description: "Structured interview drawing out perspectives", icon: "🎙️" },
    { id: "coder", name: "Coder", description: "Technical implementation, algorithms, code insights", icon: "⌨️" },
    { id: "synthesizer", name: "Synthesizer", description: "Unify multiple ideas into a perspective", icon: "🔗" },
    { id: "contrarian", name: "Contrarian", description: "Position against prevailing consensus", icon: "⚡" },
    { id: "storyteller", name: "Storyteller", description: "Narrate experiences and journeys", icon: "📖" },
    { id: "cartographer", name: "Cartographer", description: "Map landscapes, fields, problem spaces", icon: "🗺️" },
    { id: "scientific-illustrator", name: "Scientific Illustrator", description: "Design visual and conceptual accessibility", icon: "🎨" },
    { id: "communicator", name: "Communicator", description: "Translation from expert jargon to accessible framing", icon: "🌉" },
];

// ── Intents ───────────────────────────────────────────────────────────────────

export type Intent = "teach" | "connect" | "curate" | "provoke" | "demonstrate" | "bridge";

export const INTENTS: { id: Intent; label: string; target: string }[] = [
    { id: "teach", label: "Teach", target: "Saves & reshares" },
    { id: "connect", label: "Connect", target: "Comment quality, inner-ring DMs" },
    { id: "curate", label: "Curate", target: "Saves, follower growth" },
    { id: "provoke", label: "Provoke", target: "Comments, profile visits" },
    { id: "demonstrate", label: "Demonstrate", target: "Inner-ring engagement" },
    { id: "bridge", label: "Bridge", target: "Memorability, reshares" },
];

// ── CoDDE Task ────────────────────────────────────────────────────────────────

export interface LintResults {
    overall_pass: boolean;
    rant_detection: { pass: boolean; notes: string };
    fluff_detection: { pass: boolean; notes: string };
    opening_strength: { pass: boolean; notes: string };
    credential_stating: { pass: boolean; notes: string };
    engagement_bait: { pass: boolean; notes: string };
    micro_learning: { pass: boolean; notes: string };
    error?: string;
}

export interface Draft {
    version: number;
    content: string;
    created_at: string;
}

export interface Skeleton {
    hook?: string;
    insight?: string;
    key_points?: string[];
    landing?: string;
    archetype?: string;
}

export interface CoddeTask {
    id: string;
    title: string | null;
    role: Role | null;
    intent: Intent | null;
    archetype: string | null;
    domain: string | null;
    series_id: string | null;
    stage: LifecycleStage;
    lint_results: LintResults | null;
    skeleton: Skeleton | null;
    chat_history?: ChatMessage[];
    created_at: string;
    updated_at: string;
}

// ── Series ────────────────────────────────────────────────────────────────────

export interface Series {
    id: string;
    name: string;
    description: string | null;
    archetype: string | null;
    icon: string | null;
    target_post_count: number;
    post_count: number;
    progress_pct: number;
}

// ── Memory ────────────────────────────────────────────────────────────────────

export type MemoryType = "Experience" | "Research" | "Collaboration" | "Philosophy" | "Current" | "Voice" | "Goal";

export interface MemoryEntry {
    id: string;
    type: MemoryType;
    text: string;
    tags: string[];
    created_at: string;
    updated_at: string;
}

export interface KnowledgeDomain {
    id: string;
    name: string;
    color: string;
    tags: string[];
    post_count: number;
    connections: string[];
    created_at: string;
}

// ── Observatory ───────────────────────────────────────────────────────────────

export interface PostMetrics {
    task_id: string;
    title: string;
    role: string;
    archetype: string;
    domain: string;
    published_at: string | null;
    impressions: number;
    saves: number;
    save_rate: number;
    comments: number;
    dms: number;
}

export interface ObservatoryData {
    total_posts: number;
    avg_impressions: number;
    avg_saves: number;
    avg_save_rate: number;
    avg_comments: number;
    best_archetype: string | null;
    posts: PostMetrics[];
    patterns: Record<string, unknown>;
}

// ── Chat ──────────────────────────────────────────────────────────────────────

export interface ChatMessage {
    id: string;
    role: "user" | "agent";
    content: string;
    agent_name?: string;
    stage?: LifecycleStage;
    timestamp: string;
}
