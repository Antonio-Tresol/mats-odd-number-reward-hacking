# MATS 12.0 application: the rules that bind this project

Derived from `mats-admissions-faq.md` in this directory, a markdown export of
Neel Nanda's "MATS 12.0 (Winter 2026-27) Admissions Procedure + FAQ", fetched
2026-08-21 (the document was last modified 2026-08-19). Line numbers below
refer to that file. Quotes keep the document's own words and punctuation and
drop the export's escape backslashes and link markup. Written 2026-09-01, the
day this repository was forked from the SPAR take-home to carry the same
investigation into the application.

## Deadline and where it goes

- "Due Fri Sept 4th 11:59pm PT" (line 7). Extensions run to Sept 11 through a
  separate form, <https://forms.gle/gpceDYrxTUaZBoHA8> (line 54).
- The application is two things (line 199): "a summary of your findings in the
  application form, and a google doc describing your key findings which begins
  with an executive summary and ideally contains a bunch of graphs, and enough
  detail to follow what you did without needing to read your code."
- "Remember to let anyone with the link access the doc!" (line 199).
- The form comes first in his reading order (line 201): "Prioritize the
  application form summary Qs, I read these first and use them as a preliminary
  filter, I don't have time to read every write-up." Same line: "Specifics beat
  vibes: name the models, the key experiment, the surprising number."
- Code is optional and read through his agents (line 199): "I'll largely use it
  to give my agents context and ask them questions about what you actually did".
  Line 473: "I will use LLMs to help me with application review."

## The executive summary

- Line 207: "The first 1-3 pages of the google doc should be an executive
  summary, which gives the broad strokes of what you did and what you learned.
  Something at ~1 page (including graphs) is great, max 3 pages and max 600
  words. Please include graphs! Bullet points can work well".
- The format he suggests (lines 211 to 214): what problem and why it is
  interesting; the high-level takeaways and the most interesting parts; "One
  paragraph and graph per key experiment, giving the gist of what it was, what
  you found, and why this supports your key takeaways".
- Raw examples follow it (line 216): "If bad data would sink your project, show
  me the data." And: "include some randomly selected qualitative examples in
  the write-up, ideally just after the executive summary. Randomly selected,
  not cherry-picked!" This project's judgement calls are the LLM judge on
  non-integer answers and the confusion labels read from traces, so the examples
  shown are random draws from those.
- Line 450: "if you do have an interesting finding, please structure the
  write-up to emphasise it, don't do chronological order!"

## Who writes what

- Line 203: "Please do not just submit raw LLM output for the application form
  or executive summary. Write these yourself, in your own voice, even if you
  think an LLM will sound better." Line 162: "Docs that read like LLM slop will
  be rejected."
- Line 343: "A crucial thing I am evaluating is whether you add value beyond me
  just prompting Fable myself. An application that is clearly "an agent did a
  project and a human forwarded it to me" will be rejected".
- What he does want from LLMs (lines 334 to 338): drafting, brainstorming,
  critique of a draft "with an anti-sycophancy prompt", agent-written technical
  reports as a starting point, and graphs.
- So in this repository: Antonio writes the form answers and the executive
  summary. Agents draft, critique, make figures, and write the technical
  reports and notes he draws from.

## The 20 hours plus 2

Counted (line 237): "I consider any time you spend actively working towards the
project goals to be within the 20 hour time limit." His list (lines 238 to
242): writing code, reading papers chosen for the project, analysing results,
"Thinking and planning time", and "Writing up the google doc".

Excluded (lines 230 to 236): general preparation done before choosing a
project, "Generic tech set up, like renting and setting up a cloud GPU",
breaks, "Time spent waiting for things to train (assuming you're doing
something else during this time, eg training an SAE overnight)", and "Writing
your answers to the MATS application form".

The extra two hours (lines 243 to 244): "So the executive summary doesn't get
super rushed, you can take another 2 hours for it." With a restriction: "I ask
that you don't edit the rest of the write-up, and don't write any new
experiment code, though you're welcome to write code to make new
graphs/visualisations from data you already have, if it'll help present the
results better".

Tracking (line 245): "You're encouraged to track your time with a tool like
Toggl and include a screenshot with the application doc". Pivots reset the
clock (line 246): "If you decide your project is doomed, you're welcome to give
up and start a new one, and reset the timer".

Reading is capped by advice (line 366): "I recommend spending at most 5 of the
12-20 hours reading papers and tutorials".

## Work done before the application

This project began on 2026-08-24 as a SPAR Model Forensics take-home. The
document's rule (line 226): "If the previous work was done on your own and in
<=20 hours, but not for the application, this is obviously fine, and you can
just treat it as a normal application project." So the clock started with the
SPAR hours and the rest of the budget continues the same investigation. The
write-up says so in as many words: this is the SPAR take-home, extended under
the MATS budget, with every result, trace reading, and open question carried
forward.

Two consequences.

- The SPAR rules excluded replication from their 5-hour limit. The MATS rules
  count every hour of active work on the project, so the estimate of hours
  spent must include the replication runs of `Q1.H1.E1`. The record holds no
  hour count; Antonio supplies it.
- The other route, submitting existing research with an executive summary, is
  judged "more harshly than normal applications (you likely had much more
  time)" (line 224) and asks for "an estimate of how many hours the project
  took you" (line 221). Treating the work as a normal application avoids that
  route as long as the total stays within 20 hours.

## How the write-up is judged

- Clarity (line 425): "If I understand what you're claiming, what evidence
  you're providing, and think that evidence supports your conclusion, that
  instantly puts you in the top 20% of applicants."
- Truth-seeking (line 433): "Negative or inconclusive results that are
  well-analysed are much better than a poorly supported positive result." Line
  434: "It's OK if you show self-awareness of where the holes are, which parts
  are speculative, what you would investigate next, etc. If you seem
  overconfident in shaky results, that is not. Make plausible claims over
  ambitious ones."
- Simplicity (line 438): "Being biased towards trying the simple, obvious
  methods first (or explaining why they were unsuitable)."
- Prioritisation (lines 441 to 445): one or two insights in depth; rabbit
  holes and spreading thin are the two named failures.
- Sanity checks (line 483): "A really positive sign about an application is
  when I think of a way the results could be false, then discover you've
  already checked it!"
- Honesty about nulls (line 481): "Not acknowledging limitations in their
  results (worse, trying to pretend negative results are positive - negative
  results are fine! Lying about them is not)".
- Replication first (line 489): "Building on a phenomenon without first
  checking it replicates in your setting (your model, your dataset, your
  prompts). If the effect isn't there for your setup, everything downstream is
  noise." `Q1.H1.E1` is that check for this project.
- Cheap controls (line 490): "Skipping the cheap control: fine-tune on random
  data, replace your vector with a random one, compare against "just ask the
  model"."

## Sanity-checking the agent, in his words

Lines 346 to 350, the section he calls "the most important piece of advice in
this doc": "Read the raw data." "Verify the load-bearing claims." "Be
suspicious of success." "Design experiments yourself." "Document your checking
in the write-up. Tell me what you verified and how - "I read 30 transcripts and
confirmed the probe's positives were real" is strong evidence of research
skill. In past rounds, some otherwise-promising applications were sunk because
the write-up claimed things the applicant's own numbers contradicted - I do
check."

In this repository the trace readings under `notes/`, the reader notes in the
explainer, the `validate-claims` gate that ran on 2026-08-29, and the `falsify`
gate still to run are that checking. The write-up states which of them ran and
what each found.

## Where this project sits in his interests

The Model Forensics section (lines 606 to 624) describes the setting. Line 608:
"when a model has taken a seemingly sketchy action, can we figure out the
motivations, especially whether it was true misalignment or has a benign
explanation like confusion." Line 613: "As discussed in our paper, the
strongest techniques here seem to be reading the chain of thought to form
hypotheses, and constructing precise changes to causally test counterfactuals".
Line 614: "I'm pretty interested in whether you can take a setting where the
model acts plausibly deceptively and this does not work, and see if you can
understand this better with more involved techniques (chain of thought
resampling, internals based methods, etc)". Line 617: "Good projects here look
like taking some instance of sketchy behaviour and doing a deep dive into
what's going on and what drove it, and trying to form rigorously backed
conclusion". Line 621: "One major issue in forensics is eval awareness."

Two neighbouring lines also apply. Line 662, under interesting phenomena:
"Conflicting information: How do models deal with conflicts between
instructions or goals, or their prior knowledge and the context?" Line 610
names "our model forensics paper and task gaming blog post" as the sources of
good settings; the Odd Number environment is from the task-gaming line of work.

`neel-research-taste.md` in this directory maps his last year of papers
against these stated interests. Its reading: Model Forensics gets the
second-most space in the document and two papers in the year, so stated demand
runs ahead of supply.

## Tooling he recommends that this project already uses

- Line 375: "If you need an LLM API, I recommend OpenRouter". Every rollout
  here went through OpenRouter with pinned endpoints.
- Line 376: for chain-of-thought intervention "a la thought anchors, I
  recommend Nebius". This project branches through OpenRouter's completions
  endpoint instead, and `Q1.H8.E1.C2` records that the endpoint drops the `n`
  parameter, so each resample is one request.
- Line 379: "The Qwen 3.5 and 3.6 family are good default models, especially
  dense ones like 4B, 9B and 27B". The slate here is the three dense 27B Qwens
  plus three others, with `qwen3.8-27b` doing most of the work.

## The reading archive

`data/mats/` holds a local copy of the workspace's archive, gitignored except
for its README: `data/mats/INDEX.md`, a ledger of the 189 links in the admissions document;
`data/mats/sources/papers/` (arXiv PDFs by identifier); `data/mats/sources/web/` (LessWrong
and Alignment Forum posts as markdown, and text extractions of web articles);
and `data/mats/sources/gdocs/` (six past applications shared in confidence, plus the
303k-word compiled reader the document recommends as context). The past
applications are read there and never copied elsewhere or quoted in a
deliverable. The canonical copy stays in the workspace one level up.
