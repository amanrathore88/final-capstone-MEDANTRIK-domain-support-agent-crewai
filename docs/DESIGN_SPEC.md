# Visual design specification: Medantrik Assist / Support OS

Create an **original** editorial healthcare operations interface rather than a cloned Intercom/ChatGPT/Ola dashboard. Aim for calm clinical professionalism, warm human support, spacious information architecture and immediately legible status.

## Design language
- UI name: **MEDANTRIK / ASSIST**; always show small footer chip **UNOFFICIAL CAPSTONE DEMO**.
- Fonts: `Plus Jakarta Sans` or `Manrope` headings; `Inter` body; local system fallbacks and no paid font requirement.
- Colors: warm canvas `#F6F8F6`, white `#FFFFFF`, deep ink `#193339`, evergreen `#0D6864`, mint `#DDF3ED`, accent `#22AA9F`, pale line `#E5EBE8`, amber `#A87531`, alert `#BB564B`.
- Typography: 28–34 px desktop hero, 18–21 px panel titles, 13–15 px body, 11–12 px eyebrow labels. Adequate line-height, WCAG AA contrast, no tiny gray text.
- Layout: desktop left rail 220 px, center workspace flexible, optional right evidence panel 280–310 px; max canvas 1600 px. Responsive: rail becomes bottom/tab navigation on mobile, evidence drawer overlays, chat composer remains sticky.
- Radius 12–18px cards; subtle 1px borders, virtually no shadows, generous 22–36px gaps, no cheap gradient glassmorphism, no heavy stock photos.
- Signature motif: slim teal pulse/airwave strokes and a circular breathing mark used sparingly. Prefer vectors over fake medical-device photos.
- Keep interactions smooth (160–240 ms), fully keyboard accessible, respect reduced motion and high contrast.

## Desktop shell
Top bar: Medantrik wordmark | breadcrumb | green `Demo mode` indicator | local clock only if real | help icon. Left rail: Overview, Conversations, Tickets, Knowledge, Analytics, Settings. Distinct active state and text labels. Sidebar footer: seeded mock mode + disclaimer.

### Overview
- Hero area, e.g. "A calmer way to resolve care-device questions." plus one short subtitle.
- Stat tiles: Open tickets, Escalations, Resolved today, Knowledge coverage. Values MUST come from API, not hardcoded UI.
- "Start a conversation" clear CTA, recent ticket table, triage lane with priority.
- **Safety cue:** "Device safety reports route to a trained human" (prototype policy; never imply actual staff availability).

### Conversations
- Left: search + active thread list, icon avatars, snippets and time, labels.
- Main: large clean chat with agent/system/customer message styles, contextual chips (OxySense, NODex, Iron Lung), auto-scroll, typing indicator only while pending.
- Assistant message: factual answer, source chips (clickable to display KB source), confidence/sufficiency state and visible "Escalate / Create ticket" control.
- Right "Evidence & context" drawer: KB source title, snippet, policy v1/demo warning, linked ticket ID, urgency score and audit timeline. On mobile, open as overlay.
- For medical requests: visually prominent but non-alarmist warning with safe handoff; no medical instructions.

### Tickets
- Search, filters for category/status/severity/product; compact structured table; dedicated detail drawer with 5 status values, evidence trace, escalation reason and human-review-only action. All edits must persist only to demo database and create audit records.
- Customer-facing ticket status lookup; ticket IDs with `MED-` prefix, never `OLA-`.

### Knowledge
- Public source facts separate from **Synthetic Demo Policy** docs. Show document source, last reviewed, topic tags, scope, and citations. For generated advice, evidence confidence and article links are visible.

### Analytics
- Ticket count by category/status, escalation share, measured retrieval precision/recall, 15-query evaluation results. Do not hardcode perfect scores. If metrics not calculated, show “Not measured yet”.

## Critical UI behaviors
- All buttons and filters must actually work, no decorative controls.
- Loading, empty, no-results, error, offline and successful ticket creation states.
- Keyboard enter-to-send, shift-enter newline, accessible labels and visible focus outline.
- Clear session control confirms reset; new session cannot remember a previous session's ticket context.
- Use lucide icons; no emoji as primary icons.
- Dates displayed IST, but store timestamps as UTC ISO8601.

## Quality gate
Take desktop screenshot at 1440x900 and mobile at 390x844; inspect overflow, hierarchy, spelling, contrast and data accuracy. Fix UI before continuing. Compare against `design_preview/index.html` for quality direction, not literal component-by-component copying.
