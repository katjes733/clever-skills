# Recommendation Logic

How to turn research and the voter's priorities into a fair, transparent "best fit" for each race and measure. Everything here serves one idea: **decision support, not persuasion.** You show how options line up with what the voter said they care about, and they decide.

## Contents
1. Principles
2. The fit method (2b: the alignment score)
3. Rating definitions
4. Logic by election type
5. Party-ballot analysis (primary, "help me figure out")
6. Ballot measures
7. Judges, low-information races, and "no pick"
8. Neutrality protocol
9. Confidence and caveats
10. Output shape

## 1. Principles

1. **Fit to stated priorities.** The label is "best fit to your priorities", never "best candidate" or "you should vote for".
2. **Evidence over vibes.** Ratings come from records and sourced statements. Record outranks statement.
3. **Transparent numbers only.** Ratings are qualitative (Strong fit, Good fit, Mixed, Weak fit, Poor fit, Not enough info, Not applicable). The only numbers are the alignment score and evidence coverage, which the build script computes from those ratings by a published formula (section 2b), so anyone can reproduce them. Never invent other percentages, win probabilities, or precision the evidence does not support.
4. **Equal scrutiny.** Every candidate gets the same questions: the same issues, the same kind of sources, a best case and a strongest criticism.
5. **Say what you do not know.** "Not enough info" is a legitimate rating and often the most honest one.
6. **The voter owns the decision.** Offer the pick, show reasoning, and make it easy to disagree. Let them mark their own choice in the guide.
7. **No personal opinions.** Do not share your own views on contested political questions. Method and evidence are your contribution.
8. **Substance, not identity.** Match on positions, records, and style the voter named. Do not match or filter on a candidate's protected characteristics. If a voter asks you to, say that the guide works from policy positions and records, and continue.

## 2. The fit method

1. **Direction.** The voter's position on each issue they gave a position for comes from the stance questions (`profile.issue_positions`). Rate alignment *with that position*. If the voter skipped the stance question or answered "not sure", rate record and delivery on that issue instead and say in the evidence note that direction was not checked; do not guess their stance.
2. **Weights.** The voter's *biggest priorities* (any number, in their order) are high weight, and earlier in the order counts more in a close call. Their *also-important* issues are medium weight. Issues they did not select carry no weight. Dealbreakers are filters, not weights.
3. **Relevance filter.** For each race, decide which of the voter's issues the office can meaningfully influence (`offices-primer.md`). Rate only those; mark the rest "Not applicable" so the guide does not penalize a school-board candidate for foreign policy.
4. **Issue ratings.** For each relevant issue and candidate, assign one of the five fit levels (or Not enough info) using section 3, citing evidence and tagging it `record` or `statement`.
5. **Overall rating.** Make a holistic judgment, weighted toward high-weight issues, that explains itself in a sentence. Do not average mechanically. A Weak or Poor fit on a biggest priority should usually pull the overall rating down, and a pile of small matches on also-important issues should not outweigh it. Unknowns on biggest priorities should usually yield "Not enough info" or Mixed with a caveat rather than a confident Strong fit.
6. **Dealbreakers.** If a candidate clearly conflicts with a stated dealbreaker, set the dealbreaker flag with the evidence, and say so on the card. The overall rating may still show issue fit, but the best-fit pick should not be a candidate who triggers a dealbreaker unless every option does.
7. **Style.** Use the voter's style preference as a secondary signal and a tiebreaker. Say when it decided a close call.
8. **Pick, always the best available.** Voters need a usable answer, so a thin race still gets a pick. The build script computes an **alignment score (0 to 100)** and **evidence coverage (%)** for each candidate (section 2b), and a **decision label** from the gap between the top two: Clear best fit, Leaning, Slight edge, or Too close to call. Set `candidate_ids` to the top scorer (or both, with `tie: true`, for a toss-up) and say in `reasoning` what decided it and what would change it. Use "no pick" only for the cases in section 7 (no candidate has any rated issue, or an informationless judicial retention). A weak pick is labeled weak by the label and confidence, not hidden as "no clear pick".

## 2b. The alignment score

Computed by `scripts/build_guide.py` from your ratings; do not hand-write `score`, `score_low`, `score_high`, `coverage`, `margin`, or `decision`.

- **Weights.** The voter's #1 priority weighs 5, #2 weighs 4, every other biggest priority 3, every other issue 1.
- **Points.** Strong fit counts 100% of an issue's weight, Good 75%, Mixed 50%, Weak 25%, Poor 0%. Statements and party platforms count at most as Good. Not enough info and Not applicable are left out of the score.
- **Score** = weighted points divided by weighted rated issues, rounded. It answers: *on the issues where there is evidence, how closely does this candidate match you?*
- **Likely range.** Each unrated issue could land anywhere from Weak to Good, so the script shows a range around the score. A "Clear best fit" requires the top candidate's range to sit entirely above the runner-up's; otherwise it shows as Leaning and the page says unrated issues could change the result.
- **Evidence coverage** = share of the weighted relevant issues that actually had a rating. A score of 80 with 30% coverage is weak; the page flags coverage under 50% as limited.
- **Party-platform evidence** (`basis: party_platform`): when a candidate has no individual record or statement on an issue, you may rate it from their party's published platform, capped at Good and counted at half weight, and say so in the note. Use this only after a real search for individual evidence.
- **Decision label.** Gap of 15+ points is Clear best fit, 8 to 14 Leaning, 3 to 7 Slight edge, under 3 Too close to call. Coverage under 60% caps Clear at Leaning; under 40% caps at Slight edge.
- **Confidence** has five levels: very low, low, medium, high, very high. The script suggests one from the label and coverage (and record depth); you may adjust by one step with a reason in `caveats`.
- The score is a transparent summary of your ratings, not a measurement of the candidate and not a prediction. The ratings and their evidence remain the substance.

## 3. Rating definitions

| Rating | Meaning | Symbol | Bar |
|---|---|---|---|
| Strong fit (`strong`) | Documented record (votes, actions, enacted measures) clearly aligns with the voter's stated position on this issue, backed by at least one primary source. Statements alone cap at Good | ✓✓ | ▰▰▰▰▰ |
| Good fit (`good`) | Aligns with the voter's position, but by statements, a thinner record, or party platform; or a record that aligns with minor gaps | ✓ | ▰▰▰▰▱ |
| Mixed (`mixed`) | Partial alignment, a record that cuts both ways, or a position that has changed | ~ | ▰▰▰▱▱ |
| Weak fit (`weak`) | Leans away from the voter's position: statements or a record that mostly diverge | ✗ | ▰▰▱▱▱ |
| Poor fit (`poor`) | Documented record or clear statements directly conflict with the voter's position | ✗✗ | ▰▱▱▱▱ |
| Not enough info (`unknown`) | Insufficient public evidence to judge (dig first; see section 7) | ? | ▱▱▱▱▱ |
| Not applicable (`na`) | The office has little power over this issue | – | none |

Every rating needs a short evidence note and a basis (`record`, `statement`, or `party_platform`). Do not round a mixed record up to Good; use Mixed. Pick the level that matches the evidence, not the level that makes the race easier to call.

## 4. Logic by election type

Identify the type first (Phase 1) and apply the matching logic. For mixed ballots, apply the right logic to each race.

**Partisan primary.** The voter chooses one party's ballot. Within it, rank candidates by fit and pick the best in each contested race. For races with one candidate, profile that candidate so the voter knows who they are endorsing by default. Primaries often turn on style and intra-party differences; evaluate on the voter's issues, and note intra-party disagreements neutrally. Do not assess electability. If the voter's registration limits them (closed primary), say so.

**General or nonpartisan election.** Evaluate all candidates across all parties on equal footing. Report party factually, but do not use it as a filter or as evidence for or against fit. Where multiple parties compete, compare directly on issues.

**Ranked-choice, jungle, or top-two primaries.** Rate every candidate, then propose a *full ranking*, not only a top pick. Explain how the system works in one or two plain sentences and any ranking effect (ranking fewer candidates, order mattering only if earlier choices are eliminated). Strategic-voting considerations are the voter's call; mention them only if asked or if the system makes a ranking choice materially consequential, and describe them neutrally.

**Runoffs and multi-round elections.** Note the date of the next round and which candidates advance under the rules. If the voter's first choice might not advance, say that the guide can be updated after the first round.

**Multi-seat races ("vote for up to N").** Set `vote_for` to N and list the top N in `candidate_ids`, saying whether the voter may vote for fewer than N and what that does. The page offers checkboxes capped at N.

**Ballot measures.** Section 6.

**Parliamentary, list, and mixed-member systems.** Treat the party or list as a separate decision from the local candidate where the system has both (see `election-systems.md`). Say which choice moves which outcome. Rate parties on platform and record in office; rate local candidates on their own record and the party they carry. To fit the data model, represent the party decision as its own race (office "Party list vote", level "National" or similar) whose *candidates are the parties*.

## 5. Party-ballot analysis (primary, "help me figure out")

Used only when the voter chose "independent or not sure" for a partisan primary.

1. Use the voter's issues, biggest priorities, positions, and style.
2. For each available party's primary field, summarize how its candidates and platform line up with each biggest priority using the same rating method. In the data file, represent this as a race with office "Which primary ballot?", level "Ballot choice", and one *candidate per party* (party platform and field as the summary, fit by issue with text labels in every cell). The guide tab then shows the parties side by side.
3. Say clearly that this is a fit to their stated priorities, that platforms differ from individual candidates, and that primary rules may restrict their choice.
4. Present it in the artifact, then ask them to type which ballot to proceed with. Do not proceed on your own selection.

## 6. Ballot measures

For each measure:

- State in one line what **Yes** does and what **No** does, from the official text or analysis.
- Map the effects to the voter's priorities and rate Yes and No separately for each relevant issue.
- Give a **lean**: Lean Yes, Lean No, or Undecided, with reasoning and confidence. Use Undecided honestly when the effects are mixed or the evidence is thin.
- List the strongest arguments on each side in the proponents' and opponents' own terms, who funds each campaign, the fiscal effect, and any legal challenge or effective-date wrinkle.
- Flag measures that are hard to understand (long, technical, or with bundled provisions) and suggest the official analysis for a closer read.

## 7. Judges, low-information races, and "no pick"

When evidence is sparse, do not manufacture certainty, but do not withhold the best available answer either. Try these in order:

0. **Dig first.** Check the candidate's own site, the state or county voter pamphlet, Ballotpedia, Vote411 or similar nonpartisan questionnaires, local news candidate Q&As, and (for incumbents) voting records, before rating anything "Not enough info".
1. Rate what exists (including party-platform evidence at half weight) and let the score, coverage, and label show how strong the evidence is.
2. Recommend *no pick* for this race only when no candidate has any rated issue (or for a retention vote with no evaluation), and say why. Leaving a race blank (an undervote) is allowed in most places; verify the local rule before saying so.
3. Suggest where the voter can look (official voter pamphlet, nonpartisan guide, the candidate's questionnaire).

Retention votes: summarize the official evaluation and any documented concerns; do not editorialize.

## 8. Neutrality protocol

- **Same questions, same depth, same tone.** Draw both columns of "best case" and "strongest criticism" for every candidate, with attributions.
- **No loaded words** such as "radical", "dangerous", "corrupt", "extreme", or equivalents, unless quoting and attributing a named source. Prefer verbs and nouns that describe actions.
- **No horse race.** No predictions, polls, or "electability" unless asked.
- **No inference of motives.** Describe what was said, voted, or enacted.
- **Endorsements** are listed, not counted.
- **Money** is stated from official records; do not imply wrongdoing.
- **Check yourself.** Before finalizing a race, ask: if the party labels were swapped, would I have written this the same way?
- **Asymmetric evidence** is explained as a data limitation, not a judgment.
- **Display order.** List candidates in official ballot order when known, otherwise alphabetically by last name. Never put the best-fit candidate first because of the fit result.

## 9. Confidence and caveats

For each recommendation, set confidence:

- **Very high**: most priority issues backed by records, evidence coverage 80% or more, a clear gap, deep public records, no unresolved dealbreaker questions.
- **High**: several priority ratings backed by records and a clear gap.
- **Medium**: solid evidence on some issues, statements-only or party-platform on others, or a modest gap.
- **Low**: thin records, mostly unknowns, a slight edge, or conflicting evidence.
- **Very low**: almost no evidence or a toss-up on thin evidence.

Always include one caveat or "do more research" note when confidence is not high. Mention things like a newly formed campaign, a recent change in position, or litigation over a measure.

## 10. Output shape

Per contested race: a fit card per candidate with overall rating, per-issue ratings with evidence, best case, strongest criticism, record depth, links; a recommendation block with the pick(s), reasoning, confidence, and caveats; and the central dynamic of the race. Per uncontested race: a profile card. Per measure: Yes/No meaning, effects, funding, rating by issue, lean, reasoning, confidence. Fill `assets/sample-guide.json`'s structure for each. The template handles layout and the symbol-plus-text encoding.
