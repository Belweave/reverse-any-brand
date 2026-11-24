# reverse-any-brand

**Give it a brand and a moment. Get back what they did, what it cost, and whether it worked.**

An [Agent Skill](https://agentskills.io) for taking apart a brand's marketing:
every ad, every creator collab, every price move, what each one probably cost,
and what it probably sold — then one graded verdict and a published report.

Works in Claude Code, Codex, Cursor, Gemini CLI and any agent that reads
`SKILL.md`. It needs a filesystem, `python3`, and some way to read public web
pages. **No account, no key, no paid API.**

## Why

Campaign teardowns are usually one of two things: a press-release summary that
counts nothing, or a dashboard nobody can read. The interesting questions —
how early did they start, what did it cost, did it pay back — have no public
answer, so they get skipped or hand-waved.

This skill answers them by separating the two kinds of number:

| Kind | How it's handled |
| --- | --- |
| Counts (ads, posts, collabs, moves, prices) | Pulled in full. Paged to the end, dated, deduped, linked. "Pulled N of M" when a source stops early. Never scaled |
| Money (spend, sales) | Estimated at market rates, each with a low / mid / high range and the rate shown |
| Causation | Always marked INFERRED. A verdict needs a result number, never just volume |

Everything else follows from that: SEEN or INFERRED on every claim, a verdict gate
that refuses "worked" without a sales number, and pre-publish checks that fail a
report with an undated row, a remote image, or a count that disagrees with the
ledger.

## Install

```bash
# every agent, every skill in this repo, globally
npx skills add Belweave/reverse-any-brand --all -g

# or pick interactively
npx skills add Belweave/reverse-any-brand
```

**Claude Code plugin:**

```
/plugin marketplace add Belweave/reverse-any-brand
/plugin install reverse-any-brand@belweave
```

**By hand:** copy `skills/reverse-any-brand` into your agent's skills folder.

```bash
git clone https://github.com/Belweave/reverse-any-brand.git
cp -R reverse-any-brand/skills/reverse-any-brand ~/.claude/skills/
cp -R reverse-any-brand/skills/reverse-any-brand ~/.agents/skills/
```

## Use

```
reverse engineer Acme's Black Friday
tear down what Rhino did for Singles' Day this year and last
what did this brand's Q3 launch cost, and did it sell
audit every ad and creator collab Acme ran in November
did Acme's holiday campaign work
```

Nothing to configure first. The skill asks for the brand and the moment, fixes
day 0 and the windows in code, and starts pulling. Say `D-n` and it counts from
day 0 like the people who ran the campaign did.

Two skills ship here:

| Skill | Does |
| --- | --- |
| `reverse-any-brand` | The full teardown: calendar, every channel, spend and sales ranges, six tests, verdict, `report.html` |
| `reverse-any-brand-ads` | Only the archive: every ad, every collab, every owned post, labelled and saved. Standalone, or the middle of a teardown |

## What you get

A self-contained `report.html` next to the data it came from:

- **Part 1** — a week-by-week timeline against day 0, per channel: what ran, when
  it started, estimated spend with its range, the real ads and post covers, the
  offer and price ladder, and how the viral posts were built.
- **Part 2** — real marketplace numbers, estimated sales by channel with trust
  labels, the six-test table, and one verdict: worked, mixed, didn't work, or too
  early to call.
- **Close** — plays to copy, things to skip, and a method note listing every gap.

The working folder holds `ledger.csv`, `volume_weekly.csv`, `spend_weekly.csv`,
`sales_channels.csv` and `tests.json`, so any number on the page traces back to a
dated row.

## Bring your own tools

There is no dependency on a data vendor, and nothing needs to be connected.

- **The default route is public pages**: the brand's own site and store JSON
  (`/products.json`, `/products/<handle>.js`), the Meta ad library, Google Ads
  Transparency Center, TikTok Creative Center, creator profiles, marketplaces,
  search results, review sites.
- **A browser tool is the strongest option.** `WebFetch` and search results work
  for most steps. A scraping or marketing-data API is an accelerator; the skill
  routes by capability, so it uses what you have and names what it couldn't see.
- **Nothing stops to install.** Missing tool ≠ missing finding: it falls back, and
  says "unavailable" only when two different routes both come up empty.
- **Billed tools need a quoted price and a per-brand cap before the first call.**
  Free routes need a call budget, because the limit is your patience.

## The script

`skills/reverse-any-brand/scripts/rab.py` does the arithmetic and the
bookkeeping. Standard library only, Python 3.9+, no network.

| Command | Does |
| --- | --- |
| `window` | Day 0, baseline / ramp / peak / after windows, `D-n`, season labels, search terms |
| `ledger add \| rows \| count` | Dated rows in, units live per week out, with prep start and peak week |
| `spend` | Estimated spend per week and type, ranges, channels ranked, peak spend week |
| `sales` | Estimated sales per channel from a stated method, ranges, trust, dupes kept out |
| `tests` | The six tests, their grades, and the verdict gate |
| `check` | Pre-publish checks on `report.html` and the CSVs |
| `init` | An empty, correctly headed working folder |

```bash
python3 skills/reverse-any-brand/scripts/rab.py window "black friday" --year 2026 --json
python3 skills/reverse-any-brand/scripts/rab.py init --dir ./acme-bf
```

The agent writes every number from this script's output. It does not do the sums
in prose, and it does not decide a grade.

## Repo

```
skills/reverse-any-brand/            the teardown skill
  references/sources.md              capability routing, free routes, fallback ladder
  references/evidence.md             rows, dating, dedupe, SEEN vs INFERRED
  references/estimates.md            spend rates, sales methods, the six tests, the verdict
  references/report.md               the artifact spec
  scripts/rab.py                     the maths and the checks
skills/reverse-any-brand-ads/        the ads and collabs archive on its own
tests/test_rab.py                    the arithmetic and the checks
```

## Development

```bash
python3 tests/test_rab.py
```

The tests run the real script in temp folders and check the maths: holiday dates,
ad-days, creator tiers, affiliate caps, marketplace floors, dupe exclusion, the
verdict gate, and every failure the publish check claims to catch. If a test
fails, a number in a report is wrong.

See [AGENTS.md](AGENTS.md) for how to change a rule without breaking the promise.

## Provenance

The teardown method here began life as a single-file prompt written against one
marketing-data product, and the evidence discipline borrows from reverse
engineering practice: name the observation, name the inference, and never let a
tool's silence look like a fact. This is a provider-neutral rewrite: no vendor in
the instructions, no account to connect, and the numbers in code.

## License

MIT.
