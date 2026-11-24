---
name: reverse-any-brand
description: Reverse engineer any brand's marketing — what ran on each channel, when, at what estimated budget, and whether it sold. Give a brand and a holiday, season, launch or date range and get a published teardown with a counted timeline, estimated spend and sales ranges, and one graded verdict. Use when asked to reverse engineer a brand, tear down a campaign, explain how a competitor's Black Friday, Christmas, Singles' Day or launch worked, audit a brand's ads and creator collabs, estimate a brand's ad budget or channel sales, or answer whether a campaign worked. Public evidence only — no accounts, no sign-ups, no paid API required.
license: MIT
compatibility: Needs a filesystem, python3, and some way to read public web pages. A browser tool is the strongest option; WebFetch or search results work too. Nothing to install, no account, no API key required.
metadata:
  author: reverse-any-brand
  version: "1.0.0"
---

# Reverse any brand

Two inputs from the user: a brand or brands, and a moment — a holiday, a season,
a product launch, a sale, a date range. Two parts out.

- **Part 1 · What the marketing team did.** Per channel: what ran, in which week,
  at what estimated budget; what the content says and how the viral posts were
  made; every other strategy and move.
- **Part 2 · Did it work.** Real sales numbers plus estimated sales by channel,
  set against the spend, ending in one verdict: worked, mixed, didn't work, or
  too early to call.

The report closes with a few plays to copy. It runs on public evidence: the
brand's own site and store, the ad libraries, creator profiles, marketplaces,
search results, press. A paid data tool makes it faster; nothing in here needs
one.

How the work goes:

- **Ask for the two inputs, then start.** Don't interview past what you need.
  Don't ask permission to read a public page.
- **Cheap evidence before expensive evidence.** The site first, then the ad
  libraries, then creators, then marketplaces. Stop climbing a source when the
  question it answers is answered.
- **State lives in files, not in chat.** Rows go in `ledger.csv` as you pull
  them; the maths runs in `rab.py`; a compaction loses nothing because the
  working folder is on disk.
- **`RAB` below is the absolute path of `scripts/rab.py` next to this file.**
  Write the full path into every command. Run teardown commands from a working
  folder such as `./brand-teardown/`, never inside the user's source tree.
- **Read only the guide you need.** The four reference files are for the step
  you're on, not a required reading list.

| Read | When |
| --- | --- |
| [references/sources.md](references/sources.md) | Before the first pull: which capability, which free route, what it can't tell you |
| [references/evidence.md](references/evidence.md) | Before the first row: what counts as seen, how rows are dated, deduped and kept honest |
| [references/estimates.md](references/estimates.md) | Before you put a dollar on the page: spend rates, sales methods, the six tests |
| [references/report.md](references/report.md) | Before you build `report.html` |

## Four principles

1. **Counts are pulled in full; only money is estimated.** Ads, posts and moves
   are counted as found: page until the source is empty, never scale or
   extrapolate a count. If a source stops early, show "pulled N of M". Dollars
   (spend, sales) are never public, so they are estimates at market rates, each
   with a low / mid / high range and the rate shown.
2. **SEEN or INFERRED.** SEEN = a page, call result or image shows it (link it).
   INFERRED = reasoned from what was seen (say from what). Nothing seen → "not
   seen", never guessed. That a move caused a result is always INFERRED.
3. **HOLIDAY and BRAND(S) come from the user.** Nothing here assumes a holiday
   or a brand. If the request says only "my app" or "this brand" with no name
   and no obvious target, ask which one. Never pick one for the user.
4. **Public evidence only.** No accounts, forms, sign-ups, purchases or
   contacting anyone. If a page demands a login, it is not evidence; say so.

## 0 · Set up, in this order

**Interview first** — no data pull before these are answered (use the harness's
question tool when it has one; otherwise ask in one short message):

1. Which holiday, season, launch or window — and which country (say the market
   code you'll use, such as US / GB / DE, and the language).
2. Which brand or brands. One or several; the user names them.
3. Optional: their own company and stage (for the plays), and anything to focus
   on or leave out.

If the first message already names the moment and the brands, restate them in one
line and go.

**Then fix the calendar with the script**, never by hand:

```bash
python3 "$RAB" window "black friday" --year 2026 --today 2026-12-05 --json
```

It returns `day0`, `peak_end`, the baseline (-70 to -42), ramp (-28 to -1), peak
(day 0 to its end) and after (+1 to +14) windows, the chart window (-12 to +2
weeks), `D-n`, the season labels, and search terms. For a holiday it does not
know, search its dates, then pass `--day0` and `--peak-end`. Say "D-n" against
day 0 in the report. Modes:

- **live** (moment ahead or running): last year's season plus this year so far.
- **retro** (moment over): that season plus the one before.

A user-supplied window ("the Q3 launch", "last 90 days") is a valid day 0: set
it explicitly and keep every window relative to it.

**Then make the working folder:**

```bash
python3 "$RAB" init --dir ./brand-teardown
```

That writes `ledger.csv`, `rates.json`, `budget.json`, `sales.json`, `tests.json`
and a README. Work there.

◆ After each step below: a three-line finding, what the next step checks, and the
cost so far (calls made, minutes spent, or dollars if a tool bills).

## Part 1 · what ran, when (steps 1-7)

Every step saves dated rows so the counting steps can count them. Add rows with
`rab.py ledger add` as you go — one row per ad, post, move, price snapshot or
site finding, with `--link` and `--seen seen`. Never hold rows in your head or in
the chat.

1. **Brand map.** Read the home, where-to-buy, rewards, holiday/gift and FAQ
   pages. Look for the holiday terms, "sale", "early access", "price match".
   Official handles from the site. Retail map: own site, Amazon (official store
   or resellers), TikTok Shop, Walmart, key retailers. Product line-up from the
   nav and best-sellers. A Shopify store exposes
   `/products/<handle>.js` (price and compare-at price per variant) and
   `/products.json?limit=250`; count tags that name a promo or an exclusion
   (sale, bfcm, early-access, exclude, gwp, bundle).
2. **Paid ads, every ad, both seasons.** Meta Ad Library, Google Ads
   Transparency Center, TikTok Creative Center / Ad Library, and the brand's own
   platform pages. Page until the cursor is empty; check the count you hold
   against the total the library reports. Keep per ad: start, end, network,
   format, offer in the copy, landing page, and whether it runs from a creator's
   page (a partnership ad, also a collab). No ads for that country → say "none
   found in the <country> library", not "no ads".
3. **Social media collabs.** Search wide (brand + each holiday term, "tiktok
   shop", "deal", "code", "gifted", "partner", "haul", and one search per
   product name), then clean: keep the report's country, drop the brand's own
   accounts, dedupe by post id, keep posts inside the window. Label each post
   from the raw item: paid (`is_paid_partnership`, `branded_content_accounts`,
   #ad, #partner) | gifted/PR | affiliate or TikTok Shop (a shop anchor, "creator
   earns commission") | link or code | run as an ad. Tier by followers: under
   10k, 10-100k, 100-500k, 500k-1M, 1M+. Flag dupes apart: the product doesn't
   carry the brand or model name, or the caption says dupe / "$X vs $Y".
4. **Owned social.** Pull each handle back to the start of the window, both
   seasons where dates allow. Tag every post: holiday | offer (%, sale, code,
   gift) | launch | none. Owned posts are read for the offer calendar and
   products, not ranked.
5. **Site, offers and email.** What the home, holiday and sale pages say now:
   offer, popups, early access, rewards. Which email, SMS, loyalty and affiliate
   tools the site loads (a script tag, a DNS record, or an adtech detector is
   enough), and any launches or news dated inside the window.
6. **Retail and prices.** Per retailer and marketplace: official store or
   resellers, the retailer's own event and the brand's discount in it, who
   discounts first. 5-10 hero products: own-site price vs list, then the same
   product across every merchant you can read. Discount depth = 1 - price / list.
   Note products never discounted. Past prices can't be rebuilt: in retro mode
   use dated ads and posts that quote prices, and say so.
7. **Search, AI answers and word of mouth.** A demand line, one call per season,
   from a public keyword-series source: express each week as a multiple of the
   baseline (1× = normal). Pick a term that means the brand ("rhode skin", not
   "rhode"). Seasons are on separate scales: compare shape and timing, not
   height. A spike no move explains is "unexplained, check", not credited. Then
   3-5 holiday buyer questions asked of an AI answer surface (is the brand named),
   and what buyers say: comments, "is BRAND having a sale" searches, and after
   the peak, reviews about shipping and stock-outs.

If `reverse-any-brand-ads` is installed, hand it steps 2-4 and take back its
rows; otherwise follow [sources.md](references/sources.md) yourself. Either way
the rows land in `ledger.csv`.

## Part 2 · what it got (steps 8-12)

8. **Sales.** Real numbers first, each labelled with its date and what it is:
   Amazon "bought in past month" (a floor per listing), price, review count;
   TikTok Shop `soldCount` by shop — official, authorised resellers, dupes; eBay
   `quantity_sold`; a public parent's holiday-quarter sales ÷ full year (25% = an
   average quarter); store traffic where there are stores. Private company → "not
   disclosed".
9. **Periods need two snapshots.** Lifetime and rolling counts become "sold
   during the holiday" only as the difference between two dated pulls. In live
   mode, schedule daily snapshots (sold counts, reviews, stock, prices) from today
   to day 0 + 14 and tell the user.

Then the counts and the money come from the script, not from arithmetic in prose:

```bash
python3 "$RAB" ledger count --dir ./brand-teardown --day0 <day0> --out ./brand-teardown/volume_weekly.csv
python3 "$RAB" spend  --dir ./brand-teardown --day0 <day0> --budget ./brand-teardown/budget.json --out ./brand-teardown/spend_weekly.csv
python3 "$RAB" sales  --input ./brand-teardown/sales.json --out ./brand-teardown/sales_channels.csv
python3 "$RAB" tests  --input ./brand-teardown/tests.json --out ./brand-teardown/tests_result.json
```

- **Volume per week.** One unit = one ad live that week (counted in every week
  between its start and end), one collab post, one owned holiday/offer/launch
  post, one site, retail or PR move. `ledger count` writes `volume_weekly.csv`
  and reports prep start (first unit, weeks before day 0, which channel), peak
  week and the top channel's share.
- **Estimated spend.** `spend` applies the rates in `references/estimates.md`
  (overridable in `rates.json`) and writes spend per week by type, channels
  ranked by spend, and the peak spend week. Every figure is labelled "estimate"
  and carries its range. Refresh the rates from a current source before a run and
  cite what you used.
- **Estimated sales by channel.** `sales` turns each channel's method and inputs
  into a low / mid / high with a trust label, and keeps dupes out of the total.
- **Did it work.** `tests` grades the six tests and applies the verdict gate. Read
  the table, don't re-derive it.

Never call success from marketing volume alone: a verdict needs a result number.
"Too early to call" needs the date it becomes final, and `tests` gives you that
date.

## The report

`report.html` in the working folder, built to
[references/report.md](references/report.md): hero, Part 1 (timeline, each channel
week by week, content strategy, patterns and every move), Part 2 (sales, verdict),
then "plays to copy" and "things to skip". Plain, casual US English whatever the
chat language. About the brands, not the tooling: no data-platform names, no
coverage table, no bill on the page — those go in the chat reply.

Show, don't describe: real ad examples, real post covers, real product
screenshots, real price charts. Download every image at pull time and embed it;
a CDN link expires within hours.

## Before you publish

```bash
python3 "$RAB" check --dir ./brand-teardown --brand "<brand>"
```

It fails on a remote image, a missing section, an undated row, an out-of-order
range, a blank rendered as a range, a count that disagrees with the ledger, or an
open verdict with no final date. Then read the look yourself: render headless in
light and dark at 1280px and at 390px, and look at the hero, the timeline per
brand and every tab. Fix, then publish.

## When the data is missing

- **A source is empty.** One alternative route (see [sources.md](references/sources.md)),
  then "unavailable". An empty answer is a finding only if a second route agrees.
- **A source stops early.** "pulled N of M", never a scaled estimate.
- **A week wasn't pulled.** "not pulled" in the table. Never zero.
- **The moment isn't over.** "so far", the tests that can already be read, and the
  date the verdict becomes final.
- **A new pull contradicts an earlier figure.** Replace it everywhere, and tell
  the user what changed and why.
- **The brand is private.** No earnings tab. Say "not disclosed" and lean on
  marketplaces and collabs.

## Finish

Close the checklist from the interview: for each question say answered, partly
answered, or unresolved — with the evidence id or link behind it. Keep the
working folder: a later session resumes by reading `ledger.csv` and re-running
`count`, `spend`, `sales` and `tests`, not by pulling again.

In the chat reply: the verdict, the bill (estimated spend range, with the rates
used), what's coarse, and the two or three things worth checking yourself.
