# The report

One file, `report.html`, self-contained, opening from the filesystem with no
server. Images live in `images/` next to it. It is the whole deliverable: plain,
casual US English whatever the chat language, about the brands, not the tooling.

## Voice and titles

- Every title says what its section contains ("How early Acme started, where it
  pushed, and what it got"). No slogans, no abstractions, no "insights".
- No data-platform names, no coverage table, no bill on the page. Those go in the
  chat reply.
- A number that isn't public says "not public". A week not pulled says "not
  pulled". A figure not out yet says "not out yet".

## Hero

"<Moment YYYY> marketing teardown: <brand(s)>", a D-n badge, one sentence per
brand on what it did, a verdict pill per brand, and 4 KPI tiles.

## Part 1 · What <brand> did

1. **Timeline: which channel ran when, and what it cost.** One card, one brand at
   a time, season toggle. Four readouts: prep started · biggest push (volume) ·
   biggest estimated spend · result. One chart on weeks -12 to +2: top, estimated
   spend per week stacked by type; bottom, one small square per live unit stacked
   by channel, with the search line (1× = normal) and the views line (dashed).
   Spend colours follow their channel's colour family; legend in two labelled
   rows (Squares, Spend bars). Ramp shaded, day 0 marked, future weeks hatched.
   Every axis is labelled: spend panel titled "Estimated spend per week (US$,
   bars)" with $0 / half / max ticks and the week's total above each bar; squares
   panel titled "Campaign units live per week (count, squares · left axis)" with
   count ticks on the left, gridlines and the week's total above each column; the
   search line names its right axis ("Search vs normal", 1× marked).
   Hover shows a tooltip only: no fading, highlighting, zooming or other
   animation. The tooltip appears at once and leads with a colour swatch and the
   channel or spend type in bold, then the week, the count or amount with its
   range and share of that week, then the single ad or post. Hovering a search
   point shows "N× normal" and what 1× means. Under it: "Where the money most
   likely went, in order", named moves as channel lanes on the same weeks (chips
   stay inside their lane), then a note listing every rate and anything not
   pulled.
2. **Each channel, week by week** (keep section titles this short). Tabs: Paid
   ads | Social media collabs | Owned social | Site & offers | Retail & prices |
   Search & PR. Every tab reads top to bottom in the same order:
   - **Summary block**, three boxes: *Estimated budget* (one big number, its
     range, how it was worked out; "Not estimated" with the reason where it can't
     be) · *What <brand> did* (2-3 counted bullets) · *When* (first seen, peak
     week, still running or not). The boxes are tinted in the channel's colour
     (paid orange, collabs purple, owned teal, others grey).
   - **Week by week chart**: bars = this channel's units live per week (count on
     each bar, left axis), the estimated spend under each week in the channel's
     colour, and the search line (1× = usual) on the same weeks. Charts first,
     text short.
   - **Show, don't describe**: Paid ads → 1-2 real ad examples (creative image,
     page name, "Sponsored", first line of copy, dates live, platforms, link to
     the ad); Social media collabs → the top 8 posts as cards (cover, views, kind
     pill, the creator's profile photo as a small circle, handle, followers, date,
     link); Owned social → the top 4 posts with covers. Download images at pull
     time and embed them.
   - The week-by-week table folded under "Show the week-by-week table": one row
     per week with what ran, the top post, est. spend and range, search, views.
     A number that isn't public says "not public"; a week not pulled says "not
     pulled" and is never shown as zero; a week whose data isn't out says "not out
     yet". Search is brand-wide, not caused by one channel.
   - Then the dated moves. No stat tiles or cards that repeat or contradict the
     summary.
3. **Content strategy and how the viral posts were made.** Tabs: *What the
   content says* (each model name counted in ads, collab posts, owned posts and
   the holiday page: products pushed on social vs sold at the holiday; hooks;
   whether the offer is in the copy; formats) | *Viral teardown* (top 5 real
   collab posts and top 2 dupes by views, covers opened and read: hook, format,
   length, call to action, views ÷ followers; the shared formula as counted
   points; which kind of collab makes the hits; dupes outlined in red).
4. **Other strategies and every move.** Show, don't list: every point is a
   picture, a chart or a marked-up example with a link, never a numbered
   paragraph.
   - *Offer and pricing*: offer cards from the brand's own store, one per
     discounted product plus the hero product: a real screenshot of the product
     page (popups closed, cropped to image + price), price now, struck-through
     list price, a "-N% · save $X" pill (or "list price, no discount yet") and a
     link. Prices from the store's own data; say "N of M variants discounted".
     Then a price-by-seller bar chart for the hero product (own store, big
     retailers, marketplace sellers, refurbished; coloured, linked) and tiles for
     where the offer shows up (yes / partly / no per channel).
   - *Patterns*: one card per pattern, each with its own visual. Always include
     how the top collab clips are built: the 5 most-viewed real posts, each with
     cover, hook text, a bar as long as the clip split into hook → body → call to
     action, length, views, followers, kind, link. Others as fits: one real ad's
     copy marked up by part, with a link; posts-per-week mini bars; views by
     collab kind; real vs other-brand units. Never fill a bar with a guessed
     value.
   - *All moves*: the full dated table with lift, kept plain and scannable.

## Part 2 · Did it work

5. **Sales: real numbers and estimates.** Charts over text. Tabs: *Real numbers*
   first (a bar per Amazon listing with thumbnail, price, list price and link;
   TikTok Shop units by product for the brand; a share bar and top listings for
   the hero product's searches, coloured own shop / retailer / pre-owned / other
   brands) | *Estimated sales by channel* (a range chart: band low to high, mark
   at mid, coloured by trust; the table under it) | *Indirect signals* | *Earnings*
   (public brands only). No text cards that repeat the charts.
   TikTok Shop search returns a different set of listings on each call: run 4-5
   searches (brand, hero product full name, short name, the category phrase),
   include each listing's id, combine and dedupe by id, save the rows, and say it
   is a combined sample, not a census.
6. **Verdict: did <brand>'s <moment> strategy work.** The verdict in one line, the
   six-test table (number, compared with, grade, trust), estimated spend next to
   estimated sales, then "What worked" and "What didn't". In live mode: "so far",
   plus the date it becomes final.

## Close

"N plays to copy" (3-6 cards drawn from what passed the tests, each with
evidence, when to start, effort and the number to watch), "N things to skip"
(from what failed), and a short method note (SEEN vs INFERRED, routes and their
coverage, snapshot dates, known gaps).

## Look

Light and dark via CSS variables, both built from the same tokens: warm-grey
cards (#F4F2EE), hairlines, one green accent (#1F7A4D), one colour per brand.
Headings in a tight grotesque at 600 weight, body text in a neutral sans, labels
and numbers in a mono. Max width 1120px; generous vertical rhythm; no drop
shadows heavier than a hairline. Tabs are a centred segmented control with a
one-line caption. SEEN = solid pill, INFERRED = dashed. Tables stack and the nav
scrolls on mobile.

- No external CSS, no webfont fetch, no library. A report that breaks on a plane
  is a broken report.
- Every chart is inline SVG or CSS, with a text equivalent in a folded table.
- Contrast at least 4.5:1 in both themes; every image has alt text; nothing
  scrolls sideways at 390px.

## Checks before publishing

```bash
python3 "$RAB" check --dir ./brand-teardown --brand "<brand>"
```

Then, by eye: render headless in light and dark at 1280px and at 390px and look
at the hero, the timeline per brand and every tab. Squares add up to
`volume_weekly.csv`; counts match the pulled rows; every number traces to a CSV;
every estimate shows its range; no chip outside its lane, no broken image, no
sideways scroll; one brand → no other brand named. Fix, then publish.
