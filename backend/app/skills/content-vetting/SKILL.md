---
name: content-vetting
description: >
  Run quality gates on content drafts. Checks for rant tone, fluff, opening
  strength, credential-stating, engagement bait, and micro-learning verification.
  Use when a CoDDE-task is in the Vetting stage.
---
# Content Vetting Skill

## When to Use
Activate when a CoDDE-task enters the Vetting stage and a draft needs quality assessment before moving to Ready.

## The Six Lint Checks

### 1. Rant Detection
A post is a rant if it is primarily reactive rather than generative — it responds to something irritating rather than illuminating something.

**Signs of rant tone:**
- The post would make less sense if the triggering event hadn't happened.
- Emotional register is higher than intellectual content.
- Reader learns nothing actionable; they only share the author's frustration.
- Sentences like "This is why X is broken" without explaining the mechanism.

**Redirect**: "This reads as a reaction. Where's the learning for the reader? What would they do differently after reading this?"

**Pass criteria**: Post is generative independent of its trigger. Emotion, if present, serves the argument.

### 2. Fluff Detection
Fluff is content that could appear in anyone's post — it has no fingerprint.

**Signs of fluff:**
- Generic opener: "In today's rapidly changing world…"
- Motivational filler: "It's important to remember that…"
- Platitudes that don't require expertise to say.
- Any sentence that a content mill could have generated.

**Redirect**: "What detail here is uniquely yours? Which sentence could only *you* have written?"

**Pass criteria**: Every paragraph contains at least one specific, non-transferable element: a number, a name, a failure, a mechanism, a counterintuitive claim.

### 3. Opening Strength
The first line must create cognitive tension or a strong pull to continue.

**Weak openings:**
- Starting with "I" (centers the author, not the reader).
- Starting with a question (usually rhetorical and weak).
- Context-setting before the hook ("For the past six months, I've been thinking about…").
- Any sentence that could be cut without loss.

**Strong openings:**
- State a counterintuitive claim.
- Drop into the middle of a scene or decision.
- Begin with a number that demands unpacking.
- Name a tension the reader already feels but hasn't named.

**Pass criteria**: First line creates tension, curiosity, or recognition within 10 words.

### 4. Credential Stating
Explicit credential-stating is a signal of insecurity and alienates readers.

**Patterns to catch:**
- "As a Columbia PhD student…"
- "With 6+ years of experience in ML…"
- "Having worked at [prestigious company]…"
- "My research shows…" (possessive credential framing)

**Redirect**: "Embed the credential through the specificity of what you know, not by naming the institution. Show the expertise, don't cite it."

**Pass criteria**: No explicit credential statements. Authority is implicit in the precision and specificity of the claims.

### 5. Engagement Bait
Engagement bait is any device designed to generate shallow interaction rather than genuine response.

**Patterns:**
- Ending with "What do you think?" or "Comment below."
- "I'm excited to announce…" openings.
- Emoji overuse (more than 2 in a professional post).
- "Tag someone who…"
- Rhetorical questions designed to prompt agreement, not thought.
- Motivational tone ("You've got this!").

**Pass criteria**: No explicit CTAs for engagement. If the ending prompts anything, it should be reflection or action, not a comment.

### 6. Micro-Learning Verification
The post must contain a discrete, extractable learning — something the reader didn't know and can now use or think with.

**Check**: Ask — "What did the creator learn from making this? What does the reader now know they didn't before?"

**If nothing concrete surfaces**: Return to Extraction. The material isn't ready.

**Pass criteria**: Reader can articulate one non-obvious thing they learned. It must be specific, not vague ("the importance of X").

## Output Format
Return structured JSON with `pass` (boolean) and `notes` (specific, line-level) per check.
Overall `pass` is true only if ALL six checks pass.
