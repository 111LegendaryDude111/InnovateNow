# Feature release description

**Prompt Name:** Feature release description  
**Category:** Product descriptions  
**Persona/Role:** Release marketing writer  
**Goal:** Explain a new feature in plain language for release notes or a product update.  
**Prompt Text:**

```text
Context: We released [FEATURE NAME] in [PRODUCT NAME]. It helps [AUDIENCE] do [USER JOB]. Availability details are [AVAILABILITY DETAILS].
Objective: Write a short feature description for a release note.
Style: Clear, practical and product-accurate.
Tone: [TONE].
Audience: [AUDIENCE].
Response: Return Summary, What Changed, Why It Matters, How to Try It and Caveats. Do not invent availability, permissions or roadmap commitments.
```

**Variables/Placeholders:** `[FEATURE NAME]`, `[PRODUCT NAME]`, `[AUDIENCE]`, `[USER JOB]`, `[AVAILABILITY DETAILS]`, `[TONE]`  
**Example Output:**

**Summary:** Forecast Views are now available in Atlas Analytics for Pro and Enterprise workspaces.  
**What Changed:** Finance teams can group account movement by renewal period and owner.  
**Why It Matters:** This makes renewal planning easier to review before close and forecast meetings.  
**How to Try It:** Open Revenue Reports, then choose Forecast Views.  
**Caveats:** Access depends on workspace permissions.

**Best Practices/Tips:** Confirm plan availability and permissions. Keep roadmap language out unless approved. Use this prompt after product review, not before specs are stable.  
**Date Created:** 2026-06-14  
**Author:** Codex
