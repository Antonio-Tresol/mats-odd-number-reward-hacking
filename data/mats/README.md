# The MATS reading archive (local only)

Everything in this directory except this file is gitignored. It is a copy of
the `sources/` archive and `INDEX.md` ledger from the private application
workspace, a separate repository whose location is recorded in
`CLAUDE.local.md`, fetched 2026-08-21:

| Path | What |
|---|---|
| `INDEX.md` | Every link in the admissions document, mapped to a local file or the reason it was not downloaded |
| `sources/papers/<arxiv-id>.pdf` | 76 arXiv papers. Model Forensics is `2606.26071.pdf`, Thought Anchors `2506.19143.pdf` |
| `sources/web/lw_*.md` | Neel Nanda's and others' LessWrong and Alignment Forum posts as markdown |
| `sources/web/*.txt` | Text extractions of web articles; the original HTML is in `sources/web/raw_html/` |
| `sources/gdocs/*.pdf`, `*.md` | Six past applications, shared in confidence |
| `sources/gdocs/default_600k_md.md` | The compiled reader the admissions document recommends as context, about 303k words |
| `notes/` | Moved out of the public tree on 2026-09-08: the admissions document export with its image, the synthesis of the mentor's papers, and the SPAR take-home text. `notes/mats/application-brief.md` and `AGENTS.md` point here |

To restore it on a fresh clone, copy `sources/` and `INDEX.md` from that
workspace into this directory. It sits beside `data/papers/`, the store the
arXiv MCP server writes to as markdown, under the same rule: raw sources stay
local and gitignored, and the notes derived from them are committed under
`notes/`. `sources/web/notion_empathic_machines.md` is a
summary written by an LLM, so it is never quoted as the author's words.

The past applications are other people's work, shared with one applicant. They
stay in this directory and are never copied elsewhere in the repository or
quoted in a deliverable.
