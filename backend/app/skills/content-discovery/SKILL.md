---
name: content-discovery
description: >
  Generate a Discovery brief combining trending topics, user expertise, and performance
  patterns. Use during the Discovery stage to open a CoDDE-task session.
---
# Content Discovery Skill

## When to Use
Activate when a CoDDE-task enters the Discovery stage. Load alongside `audience-psychology` and `framework-library`.

## Discovery Brief Protocol

### 1. Context Gathering (before opening message)
- Search memory for user's identity, recent content history, and domain expertise.
- Use `web_search` to find: trending papers, LinkedIn/Twitter discussions, emerging debates in user's domains.
- Use `compute_patterns` to retrieve what's worked: best archetypes, best domains, best timing.

### 2. Brief Structure
Present exactly three options. Each option is one paragraph:
- **Option A — Trending Angle**: Something the world is talking about that the user can own because of their specific expertise.
- **Option B — Unexplored Connection**: A cross-domain synthesis nobody has articulated yet. Requires naming both domains.
- **Option C — Audience Demand**: Something practitioners are struggling with that the user can definitively address.

### 3. Naming the Direction
When the user picks a direction, confirm:
- What archetype fits this material (Bridge, Framework Drop, Field Note, Micro-Learning, etc.)
- What intent this serves (Teach, Connect, Provoke, Demonstrate, Curate, Bridge)
- What the metric target is given historical performance

### 4. Transition Signal
When direction is confirmed, say: "Ready for Extraction. Which role fits this best?" — present the role grid.

## Anti-Patterns
- Don't open with: "What would you like to write about today?"
- Don't present more than three options.
- Don't suggest topics the user has covered in recent tasks (check history first).
- Don't recommend a domain with zero posts in the knowledge graph unless it's a deliberate expansion.
