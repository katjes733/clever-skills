# Presentation Guide

How to use the Claude desktop app's presentation capabilities. The principle: **chat is for the conversation; the artifact is for the findings.** Findings (ballot, profiles, fit, guide) are visual, revisited, and used later at the polls, so they live in a private, interactive page that updates in place.

## Contents
1. The living guide artifact
2. Build steps
3. Staged views and checkpoints
4. Data file essentials
5. Accessibility rules
6. Privacy and labeling
7. Other desktop-app capabilities to use
8. Fallbacks

## 1. The living guide artifact

Use **one** artifact per election session. Republish to the same file path each time so the person sees one page that grows instead of a trail of near-duplicates. It is rendered from a single data file by `assets/voter-guide-template.html`, so you never hand-write the page; you fill data, build, and publish.

Tabs appear automatically as data arrives:

| Stage (`meta.stage`) | Tabs shown | When |
|---|---|---|
| `ballot` | Overview, Ballot, Sources | Ballot-only fallback (voter declined the interview) |
| `profile` | + Your priorities | First artifact, after the interview and ballot research |
| `guide` | + Guide, Measures, Cheat sheet | Final guide with fit assessments, picks, and the polling-place cheat sheet |

Features the template provides: live countdown to Election Day, key dates with Passed/Today/Soon status computed when the page is opened, race cards with per-candidate fit, best-case and strongest-criticism panels, a clearly marked best-fit pick, an optional "Your pick" selector per race, ballot-measure cards with Yes/No meaning, filters and search, a printable cheat sheet, source lists, light and dark themes, and mobile layout.

## 2. Build steps

1. Create or update a data JSON file (`guide-data.json`) in the session's scratchpad directory if one is listed, otherwise the working directory. It holds the voter's political preferences, so keep it out of shared or synced folders. `assets/sample-guide.json` shows every field. Fill what you know; leave optional blocks out.
2. Validate and build:
   ```
   python3 <skill-dir>/scripts/build_guide.py guide-data.json guide.html
   ```
   Fix every error. Read every warning; they flag things like missing sources, unverified statuses, and uneven treatment of candidates.
3. Before the **first** publish, load the `artifact-design` skill. The template already follows its page contract (title, theme tokens in light and dark, explicit background, 16px mobile gutters), but that skill is authoritative if they differ.
4. If you want picks to persist reliably across devices, load `artifact-capabilities` and use a capability that keeps state instead of the template's browser storage. Browser storage works for personal convenience on one browser and is the default.
5. Publish with the Artifact tool, passing `file_path: guide.html`, a short `description` (one sentence), and on the first publish `icon: "ballot"` (any generic word such as "checklist" also works). For updates, rebuild to the **same** `guide.html` and call Artifact again; the URL stays the same.
6. After publishing, reply with one sentence on what changed and, at the checkpoint, the confirmation question. The app shows the artifact card; do not paste the link.

Edit the data file with the Edit tool for small changes (a corrected date, a new source) and rebuild; do not regenerate the whole file.

## 3. Staged views and checkpoints

The first artifact appears only **after the core interview** (see the prime directive in `SKILL.md`). Nothing is published during the location and interview questions.

- **First artifact (after ballot research).** `stage: "profile"`, with `election`, `timeline`, `rules`, the full `races` and `measures` lists (names, parties, incumbency, verified status, no fit yet), `open_questions` (for example, "Confirm your district numbers"), and the `profile` block from the interview. Set `default_tab` to `ballot`. Ask: "Does this ballot look complete, and does the priorities summary look right?"
- **After local-issue questions.** Update `profile.local_positions` and republish quietly with one line saying what changed.
- **Final.** `stage: "guide"`, `default_tab: "guide"` (or `cheat` if the voter is about to vote). Include `method_notes` and general `sources`.
- **Ballot-only fallback.** If the voter declines the interview entirely, build `stage: "ballot"` (Overview, Ballot, Sources) and say it is not personalized.
- **Follow-ups.** Update the same data file and republish. Mention what changed, for example "Updated the sheriff race with the new jail report; the pick is unchanged."

## 4. Data file essentials

- **`completeness` block (required at every stage).** `checked_on`, `district_basis`, `levels_checked`, `sources` (`label`, `url`, `kind` among `county_candidate_list`, `state_candidate_list`, `sample_ballot`, `voter_sample_ballot`, `voter_pamphlet`, `measure_list`, `official_other`, `aggregator`, `news`, plus `retrieved`), `expected` (every office and measure from the official sources: `id`, `type` race or measure, `label`, `level`, `source`), `unresolved` (`item`, `reason`), and `independent_check` (`done`, `method`, `discrepancies` with `item` and `resolution`, or `skipped_reason`). Inventory ids must match the race and measure ids; the build script errors on an inventory item missing from the guide, warns about guide items missing from the inventory, and (at the guide stage) errors if the independent check is neither done nor explained. The Ballot tab shows a "How this list was checked" card from this block and the cheat sheet notes the sources and unresolved items. Never word the chat as if the ballot were complete.
- Every race has `id`, `level` (use consistent labels such as Federal, State, County, Local), `office`, `status` (`verified` or `unverified`), a `key_dynamic`, candidates, and sources. More than one candidate means contested. One candidate counts as "Uncontested" only when `status` is `verified`; no candidates shows "No candidates found". Set `vote_for` above 1 for multi-seat races and `method` to `ranked` (or similar) for ranked-choice, which changes the pick controls. List candidates in official ballot order, or alphabetically, never best-fit first. Keep candidate ids stable across rebuilds so saved picks survive.
- `fit.by_issue` lists issues in the voter's priority order (biggest priorities first, then also-important). Rate only issues the office can influence. The page shows the first five and folds the rest under "N more of your issues".
- **Tickets (governor and lieutenant governor, president and vice president).** Keep `name` to the candidate at the top of the ticket only and put the running mate in `running_mate`. Never write "Name (running mate: X)" or "A / B" in `name`: bar labels and cheat sheets use the surname of `name`, so a ticket string would show the wrong person. Set `short_name` if the usual label is not the last word of `name`.
- Every candidate has a unique `id`, party, incumbency, a one-line background, `record_depth`, and (in the guide stage) `fit`, `best_case`, and `strongest_criticism`.
- Ratings are only `strong`, `good`, `mixed`, `weak`, `poor`, `unknown`, or `na`. Each rating takes a short evidence `note` and a `basis` of `record`, `statement`, or `party_platform` (capped at good, half weight).
- Do not write `fit.score`, `fit.score_low`, `fit.score_high`, `fit.coverage`, `recommendation.margin`, `.decision`, `.top_score`, or `.suggested_confidence`: `build_guide.py` computes them from the ratings and the profile order, and the page shows them (alignment out of 100, evidence coverage, decision label, five-level confidence).
- A recommendation lists `candidate_ids` in best-fit order (empty if no clear best fit, with `none_reason`), plus `reasoning`, `confidence`, and `caveats`. Set `tie: true` when two or more are effectively tied.
- Measures need `yes_means` and `no_means` from the actual text or official analysis, `by_issue` ratings for Yes and No, a `lean` (`yes`, `no`, or `undecided`), and sources. Judicial **retention votes** use the same block: Yes means retain, No means do not retain. Optional `status: "unverified"` flags a measure you could not confirm.
- Timeline items are `{label, date, end_date?, date_text?, status?, note, url}`. Use `end_date` for windows such as early voting so the page shows "Opens in N days", "Open now", or "Closed" instead of a misleading "Passed". Use `status: "unverified"` for anything not confirmed on an official page.
- The `profile` block carries `top_issues` (the voter's biggest priorities in their order, however many; labeled "Biggest priorities" on the page), `issue_positions` (`{issue, position}` from the stance questions), `other_issues` (also important, shown as "Also important to you"), `style`, `local_positions`, `dealbreakers`, and `notes`.
- All text is rendered as plain text by the template. Do not include HTML. URLs must be http or https. Sources carry a `retrieved` date.
- Keep the voter's address out of the file. Location is ZIP or city level.

## 5. Accessibility rules

The template implements these; keep them when customizing.

- **Never color alone.** Every rating shows a text label, a shape-distinct symbol (✓✓, ✓, ~, ✗, ✗✗, ?, –), a bar glyph (▰▰▰▰▰ to ▱▱▱▱▱), and a distinct border style (solid, thin, dashed, dotted, heavy dotted, double). The horizontal bars add distinct fill patterns (solid, hatched, dotted, striped) and always sit next to the text label. Color is a reinforcing layer.
- Ballot-measure leans use shape-distinct symbols (▲, ▼, ◆) with text.
- Symbols are decorative; the text label carries the meaning for screen readers.
- Tabs follow the tablist pattern with arrow-key navigation; radio groups have labels; focus outlines are strong; layout works from phone width up; tables scroll horizontally rather than clip.
- Contrast: tokens are chosen for readable contrast in light and dark themes. If you change colors, verify contrast.
- Respect reduced motion; no autoplay or flashing.
- Plain, short sentences. Define terms on first use ("a parcel tax is...").

## 6. Privacy and labeling

- Artifacts are private until the person shares them. The guide records political preferences. Mention once that it is private and that sharing is their choice; do not suggest posting it publicly or push sharing.
- The page carries an **unofficial, personal guide** banner (the template adds it, and `meta.disclaimer` can customize it). Do not style it like a government ballot, add seals or logos, or use a look-alike of any official site. It must not be mistaken for a real sample ballot.
- Do not publish a page that contains advocacy material, scripted persuasion, or fabricated records. Everything cited must be real and retrieved.
- If the voter asks you to share a "recommended ballot" with others, remind them that the guide reflects only their own priorities and offer to produce a neutral candidate-and-measure summary without picks.

## 7. Other desktop-app capabilities to use

| Capability | Use it for |
|---|---|
| **Task list** (TaskCreate/TaskUpdate) | Show progress through Identify, Research ballot, Interview, Research races, Build guide, Verify. Add one task per large research chunk. Mark each complete as it finishes. |
| **Subagents** (Agent) | Parallel research per level of government; the independent verifier at the end. Briefs are in the research playbook. |
| **Places search and map** (places_search, then places_map_display_v0) | Show early-voting sites, county election offices, and drop boxes near the voter's ZIP. Call the map straight after the search, then write picks below it. This data is a convenience; the official county page is authoritative for hours and locations. Never show ratings or reviews. |
| **Link cards** (link_preview_display_v0) | Present 2 to 6 official links (registration, ballot tracker, voter ID rules) at the end, without repeating the URLs in prose. |
| **Clickable questions** (AskUserQuestion) | Opt-in only; see the interview playbook. |
| **Scheduled tasks** | Offer a reminder for a deadline, early voting, or Election Day; create it only after the voter says yes. A scheduled task starts a fresh session, so write the prompt as a complete, standalone instruction with no private details beyond what the reminder needs. Say plainly that it is a "scheduled task". |
| **Date tool** (current_time) | Anchor all relative dates. |
| **Printing** | The cheat sheet has a print button. If the voter wants a file, build a PDF from the cheat sheet content with the pdf skill and send it. |
| **Inline visual** (chart/visualizer) | Only for a quick explanation inside the chat, such as a diagram of how ranked-choice transfers votes. Do not duplicate findings that already live in the artifact. |

Do not run image searches of candidates; political photos add nothing to a fit assessment and risk misidentification.

## Resuming from a published guide

The published page embeds its data in a `guide-data` script tag. In a later session, read the artifact with the Artifact `read` action, extract that JSON, update it, and rebuild to the same artifact URL. Do not rebuild from scratch.

## 8. Fallbacks

- **No Artifact tool.** Build `guide.html` anyway and send it with SendUserFile (the person can open it in a browser). Say the page works offline and that picks are saved only in that browser.
- **No file or shell tools.** Present a compact Markdown version in chat: one table per level, with the rating text and symbols in every cell, and a short "best fit" list. Keep the same neutrality rules.
- **No web search.** Tell the person you cannot produce a verified guide, and help them with the official sources, the interview, and a framework for comparing candidates on their own.
- **No subagents.** Research races sequentially and run the verification pass yourself with extra care, noting that it was not independent.
- **Build script missing or failing.** Fix the data file; do not hand-edit the generated HTML.
