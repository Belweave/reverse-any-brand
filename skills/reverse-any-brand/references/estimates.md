# Estimates, tests, verdict

Nobody publishes spend or sales. Both are modelled here, at market rates, with
the rate shown and a range around every figure. The script holds these numbers;
this file explains them so you can defend one.

Refresh the rates from a current source before a run — a rate card, a CPM
report, a commission page — and cite what you used in the method note. A stale
rate is the most common way a teardown is wrong.

## Spend

`rab.py spend` applies this table. Override any part in `rates.json`.

| Spend | Mid | Low - high |
| --- | --- | --- |
| An ad live for a day (Meta / TikTok) | $150 per ad-day | $50 - $400 |
| Paid collab post, under 10k followers | $150 | $50 - $300 |
| Paid collab post, 10-100k | $750 | $250 - $1,500 |
| Paid collab post, 100-500k | $3,000 | $1,500 - $5,000 |
| Paid collab post, 500k-1M | $8,000 | $5,000 - $12,000 |
| Paid collab post, 1M+ | $20,000 | $10,000 - $50,000 |
| Gifted post | one product at retail | equal |
| Affiliate / TikTok Shop post | views × 0.2% who buy × price × 12% commission, plus one sample | 0.06-0.36% who buy, 5-20% commission, capped at real sold units × price × commission where a sold count exists |
| Making an owned post | $1,000 | $150 - $3,000 |
| PR event or brand collab | $100,000 | $30,000 - $200,000 |
| Google search | a monthly budget estimate, spread across the days it covers | budget × 0.6 - 1.5 |

Never estimated, and said so on the page: retailer co-op fees, email and SMS
sends, staff time. A row whose inputs are missing is not estimated — the script
counts it and says how many, so a report never silently loses spend.

Rules that keep this honest:

- **One ad-day is one ad live for one day.** A three-week ad is 21 ad-days, not
  one ad.
- **A creator's followers tier the price, not their rate card.** If the post says
  the rate, use it and note that you did.
- **An affiliate post costs commission, not a fee.** Cap it at real sold units
  where a sold count exists, and say the cap applied.
- **A budget you found is already an estimate.** Label it, name where it came
  from, and spread it over the days it covers rather than over the whole quarter.

## Sales

`rab.py sales` computes each method from its inputs. One row per channel in
`sales.json`; `include_in_total` false for anything that isn't the brand's
revenue (dupes, a ceiling used only for comparison).

| Method | Inputs | How the range is built | Trust |
| --- | --- | --- | --- |
| `units_x_price` | units, price | counted units × seen price, ±15% for mix and bundles | high |
| `bought_past_month_x_price` | listings: units, price | the marketplace's own floor, widened down to 0.6× and up to 1.8× | medium |
| `visits_x_conv_x_aov` | visits, conv low/mid/high, aov | visits × category conversion × order value, ±20% | low |
| `views_x_share_x_price` | views, share low/mid/high, price | views × share who buy × price; a ceiling, not a measurement | low |
| `review_growth_x_review_rate` | new_reviews, review_rate low/mid/high, aov | new reviews ÷ review rate × order value; the rate is what widens it | low |
| `reported_share` | reported_sales, share low/mid/high | reported sales × this channel's share | medium |

Find the category's conversion rate, CPC and order value from a current source
and cite them. Where the same product sells at several sellers, a bar chart of
prices beats a paragraph.

Rules:

- **A floor is a floor.** "Bought in past month" on a marketplace is the least
  units sold, not the units sold. The range reaches down, never up to a precise
  number.
- **A ceiling is a ceiling.** Collab views × share is the most the channel could
  have sold. Check it against real sold units before you quote it.
- **Dupes are units, not revenue.** Own row, out of the total, labelled.
- **Totals compare channels with each other.** They are not the brand's true
  revenue. Where a public brand reports a figure, check the model against it and
  say how far off it is.

## The six tests

`rab.py tests` grades these from the measured inputs in `tests.json` and applies
the verdict gate. Do not re-derive a grade in prose.

| Test | Number | Compared with |
| --- | --- | --- |
| Demand rose | peak-week search ÷ baseline | last year's multiple at the same D-day |
| Reach was cheap | views per estimated dollar, per channel | the brand's other channels |
| Sales rose | units or sales in the holiday window | a normal window (snapshot difference), or holiday-quarter share vs 25% |
| Spend paid back | estimated sales ÷ estimated spend, as a range (low sales ÷ high spend, to high ÷ low) | 1× |
| Price held | discount depth on hero products; new models at full price | list price, last year |
| Demand was kept | real units ÷ (real + dupe units) | — |

Grades are pass, mixed, fail, or can't tell, each with its trust. A grade with a
missing input is "can't tell", never a guess.

## The verdict

| Verdict | When |
| --- | --- |
| **Worked** | sales rose and at least three other tests pass |
| **Didn't work** | sales flat or down, or spend clearly not paid back |
| **Mixed** | anything between; say which tests split |
| **Too early to call** | before day 0 + 14, or no second snapshot. Give the reading "so far" from what can already be read, and the date the verdict becomes final |

A verdict needs a result number. Marketing volume alone — more ads, more posts,
higher search — is never "worked". If the only thing you have is volume, the
verdict is "can't tell yet", and the report says what would settle it.

## Moves and lift

From the dated rows: search in the 7 days before a move against the 8 days from
it; moves under 3 days apart share one lift. Same move, same D-day, last year
against this year, side by side. Every lift is INFERRED and says so.

## Plays to copy

3-6 cards, each drawn from a test that passed: what the brand did, the evidence,
when to start (D-n), the effort, and the number to watch. Plays that are pure
writing or planning get no data prompt; plays whose first step is a pull get a
short prompt naming the data, not the tool.
