# Design notes

Why the skill works the way it does, and what went wrong along the way. Read this before changing the interview or the scoring.

## 1. Interview first, build last

**Failure observed:** an early version asked only where the user lived, then researched and produced a generic ballot guide. The user wanted to be interviewed about preferences and topics.

**Causes:** the workflow built a ballot-stage artifact before asking about preferences, and it defaulted to typed question-and-answer, which felt like a form.

**Fix:** a *prime directive* in `SKILL.md`: no candidate research, artifact, or guide until the core interview is complete, plus a self-check ("Have I asked their issues, which matter most, positions, style, and dealbreakers?"). The first artifact appears only after the interview and ballot research. Questions default to tap-to-answer via the app's question tool, with numbered text as the fallback.

## 2. Wide net, then prioritize

A fixed "top three" lost most of what people care about. The interview now walks about 50 topics in seven themed rounds (cards of up to three issues plus "None of these", because the question tool allows four options), then sorts selections into ranked *biggest priorities* and *also important*, then asks a position question for every priority. Issue names are alphabetical within each theme and neutrally worded so no issue is favored.

## 3. Findings are visual, the interview is chat

Chat carries the interview and one-line pointers. Ballot overviews, candidate profiles, fit assessments, and the cheat sheet live in the artifact, where they can be revisited, printed, and picked from.

## 4. Scoring: why a number, and why a range

Three-bin ratings and three-bin confidence made many races read as "inconclusive". Pure bins cannot combine many weighted issues; a bare score looks more precise than the evidence is. The compromise:

- A five-level rating per issue (so "mixed" is distinct from "directly opposes you").
- A reproducible weighted score computed by `build_guide.py`, never hand-written.
- A **likely range** from unrated issues, and an **evidence coverage** figure, so thin evidence shows up as uncertainty instead of false precision.
- A label from the gap between the top two, with "Clear best fit" requiring non-overlapping ranges.
- Statements and party platforms cap at Good; party platform counts at half weight. A race always gets the best available pick, labeled by strength.

The score summarizes ratings; the evidence notes remain the substance.

## 4b. Completeness is the skill's job

**Failure observed:** a guide was presented as if it had been checked, the only completeness check was asking the voter "does this look complete?", the claim verifier only sampled claims already in the guide (so it could never find what was missing), and a warning that official lookups need a street address steered research away from the county's candidate PDF, the one county-level source that needs no address.

**Fix:** inventory first, from address-free official sources; a required `completeness` block that the build script reconciles against the guide (a missing item is an error); an independent blind re-check that never sees the guide; and honest wording in chat and on the page about what was checked and what could not be confirmed. The voter's sample ballot is an extra check, not the primary one.

## 5. Neutrality safeguards

Equal questions and sources for every candidate; best case and strongest criticism for each; ballot-order display; stance options worded as their own supporters would word them, with one for each main camp; ratings tagged `record` or `statement`; no personal opinions; "who would you pick?" is answered with the method, not a pick.

## 6. Safety and privacy

ZIP or city only; official address lookups are handed to the voter, never filled in by the skill; web pages, PDFs, and pasted profiles are treated as data, never instructions; the guide stays a private artifact; embedded JSON escapes `<`, `>`, `&`, and U+2028/9 so content cannot break out of the page.

## 7. Distribution lessons

- Uploading an updated `.skill` did not replace an existing installed copy, so the old interview kept running. Remove the old skill first, then upload, and verify the new behavior.
- Updating only `SKILL.md` through an in-app proposal replaces just that file, not the bundled references, scripts, or template. So the interview script is embedded in `SKILL.md` and wins on any conflict with a stale reference file.
- A skill cannot pre-approve tools such as web search. The skill reduces approvals with a research budget and tells the user to choose "Always allow" if offered.
- `build_guide.py` refuses to write over the template (an early mistake did exactly that).

## 8. Testing status

- Unit tests cover scoring, caps, ranges, labels, validation, escaping, the template guard, and skill metadata.
- The page was checked in headless Chromium at phone and desktop widths in light and dark.
- The interview was dry-run by independent readers following only the skill files, which confirmed it asks interview questions before researching or building.
- **Not tested:** full real-ballot sessions with the final scoring, behavior of the question tool on phones, and long research runs under real approval settings.
