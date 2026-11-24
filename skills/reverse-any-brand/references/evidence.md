# Evidence, rows, and honesty

A teardown is only worth the rows behind it. This file is how a row gets
written, dated, kept, and cited. Read it before the first pull, not after.

## The row

`ledger.csv` has one fixed schema. `rab.py ledger add` writes it for you and
refuses a duplicate. Never hand-edit the header.

| Field | What goes in it |
| --- | --- |
| `id` | Set by the script: a short hash of brand, season, channel, kind, start date, what |
| `brand` | Exactly as the user named it |
| `season` | The season label from `rab.py window` |
| `channel` | `paid`, `collabs`, `owned`, `site`, `retail`, `search`, `pr`, `email` |
| `kind` | `ad`, `post`, `move`, `price`, `snapshot` |
| `date_start`, `date_end` | When the unit was live, not when you found it |
| `what` | One line: the offer, the format, the move. Not a paragraph |
| `link` | The public page you saw it on |
| `views`, `followers`, `price`, `units_sold` | Only where a page states them |
| `collab_kind` | `paid`, `gifted`, `affiliate`, `code`, `dupe`, `none` |
| `seen` | `seen` or `inferred` |
| `pulled` | The date you pulled it |
| `notes` | Anything that changes how the row should be read |

```bash
python3 "$RAB" ledger add --dir ./brand-teardown \
  --brand "Acme" --season "Last year (2025)" --channel paid --kind ad \
  --date-start 2025-11-01 --date-end 2025-11-21 \
  --what "BFCM sale, 30% off, countdown creative" \
  --link "https://www.facebook.com/ads/library/?id=123" \
  --views 48000 --seen seen --pulled 2025-12-02
```

A row without a date is not a row: the script reports it as skipped instead of
silently dropping it. Fix the date or remove the row.

## SEEN and INFERRED

- **SEEN** means a page, call result or image shows it, and the row carries the
  link. If you opened it, it is seen.
- **INFERRED** means you reasoned from something seen. The `notes` field says
  from what ("budget inferred from 14 ads live 3 weeks; rate card in estimates.md").
- **Not seen** means the field stays blank in the table and "not seen" in the
  prose. It never becomes a zero, a guess, or an average of the neighbours.
- **Causation is always inferred.** "Demand rose when the ads went live" is a
  correlation you report; "the ads caused the rise" is not.

## What a count is

- **Counted** means every unit the source lists, paged to the end, dated inside
  the window, deduped by its own id. Nothing scaled, nothing extrapolated, no
  "about 40 ads".
- **Pulled N of M** is what you write when the source stopped early, when a
  cursor expired, or when a cap ended the pull. M comes from the source's own
  total, not from your estimate.
- **A sample** is what you call a set you know is incomplete (TikTok Shop search
  returns a different set each call). Say how many searches ran and how you
  combined them.

## Snapshots and periods

Lifetime and rolling counters are not period numbers. Two dated pulls are:

```bash
# snapshot 1 at pull time, snapshot 2 after the window, then the difference
python3 -I - <<'PY'
import csv
a = {r["product"]: int(r["sold"]) for r in csv.DictReader(open("snap/tiktok-1.csv"))}
b = {r["product"]: int(r["sold"]) for r in csv.DictReader(open("snap/tiktok-2.csv"))}
for k in sorted(set(a) & set(b)):
    print(k, b[k] - a[k])
PY
```

- Save both pulls with their dates, and keep the pairing in `notes`.
- A negative difference means the counter was redefined or the listing changed.
  Say so; don't clamp it to zero.
- In live mode, schedule the second pull before day 0 + 14 and tell the user when
  it runs.

## Dupes and other brands

- A dupe is another brand's product sold as a substitute. It is a unit, not a
  dollar of the brand's revenue: `--collab-kind dupe`, and `include_in_total`
  false in `sales.json`.
- A real rival is "other brands", not a dupe.
- A collab post that shows a dupe link is labelled `dupe` and counted apart.

## When something contradicts something

1. Re-pull once, from a different route, to see which is wrong.
2. If the newer figure holds, replace it everywhere — the table, the chart, the
   CSV, the prose. A report with two numbers for one thing is worse than a stale
   one.
3. Tell the user what changed and why, in the chat reply, in one line.

## What never goes in the report

- A number with no date.
- A dollar figure with no "estimate" and no range.
- A week with no data shown as zero.
- A count the source lists as a floor, presented as exact.
- The tool you used. (It goes in the chat reply, or the method note.)
- A brand the user didn't ask about.

## The method note

End the report with a short method note: SEEN vs INFERRED, the routes used and
what each covered, the snapshot dates, and every known gap. This is the part a
reader checks when a number looks wrong.
