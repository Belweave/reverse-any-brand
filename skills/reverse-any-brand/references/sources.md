# Routes to evidence

Pick a **capability**, not a vendor. This teardown has been run with a browser
tool, with a search API, with a scraping API, and with a paid marketing-data
stack. The method is the same; only the number of calls changes. Never stop to
install something, and never report a finding as unavailable because the "right"
tool wasn't connected.

## The order that always applies

1. **The brand's own pages and data.** Site, store JSON, help centre, press page,
   robots-permitted sitemaps, the brand's own social handles.
2. **The public ad libraries.** These are pages. Read them.
3. **Creator and marketplace pages.** Profiles, posts, listings, review counts.
4. **Search results and AI answer surfaces** for what buyers saw and asked.
5. **A paid data tool**, if the stack has one, to widen coverage or answer
   faster. It is an accelerator, never a prerequisite.

## Capability table

| Capability | A usable answer contains | Free public route | If the stack has a paid tool | What it can't tell you |
| --- | --- | --- | --- | --- |
| Brand and site map | Offers, handles, product names, where-to-buy, retail partners | The site, store JSON, help centre, sitemap | A crawl/extract API for bulk pages | Whether a page was shown to real buyers |
| Meta ad archive | Every ad: start, platforms, copy, creative, landing page | `facebook.com/ads/library` filtered by advertiser, country, dates, page by page | An ad-library scraper API for cursor paging | Spend (for most advertisers), and reach against the country's population |
| Google ad history | Copy, keywords bought, landing pages, an ad-budget estimate | `adstransparency.google.com` for live creatives; a keyword/domain tool for history | A domain-overview tool for the monthly budget figure | Actual spend; it is modelled, not published |
| TikTok ad archive | Ads, formats, landing pages, and which ran from creator accounts | `ads.tiktok.com/business/creativecenter` and the TikTok Ad Library | An ad-library API | Small always-on ads the library drops |
| Creator posts | Post id, date, views, followers, caption, hashtags, shop anchor, partnership flag | Platform search and hashtag pages, creator profiles, the post page itself | A social search API for volume | The whole set: no platform lists every collab. Say how many searches you ran |
| Owned social timeline | Every post back to the window start, with dates and products shown | The profile pages, paged back by scroll or cursor | A profile-scrape API | Deleted posts, and reach where the platform hides it |
| Email, SMS, loyalty, affiliate tools | Which tools the site loads, and a dated launch or news item | Script tags and DNS records on the site; the vendor's own customer page | An adtech or news-events detector | Send volume and revenue |
| Retail and price snapshots | Price today, list price, seller, stock hints, per product | The product pages, marketplace listings, shopping results | A shopping or marketplace API | Prices before you started looking |
| Demand series | Weekly interest relative to normal, for one term | A public keyword-series page or a trends endpoint | A keyword-data API with a date range | Sales. Interest is not demand met |
| AI answer presence | Whether the brand is named for the buyer's question | Ask the question on an AI answer surface, twice, and record the answer | A search API with AI results | Why the model chose it |
| Reviews and complaints | Review count over time, shipping and stock-out themes | Trustpilot, marketplace reviews, the brand's own reviews | A review-scrape API | Non-buyers |
| Marketplace sales signals | Sold counts, review counts, price, seller type | Amazon and TikTok Shop listing pages, eBay sold filter | A marketplace API for many listings | Units the marketplace doesn't publish; sold counts are a floor |
| Store traffic | Visits or a popularity curve | Google Maps popular times where there are stores; click and CPC modelling otherwise | A traffic-estimate API | Anything precise |

## The fallback ladder

For each capability, in order, and stop at the first that answers the question:

1. A native tool in this stack whose response you can read.
2. The public page, read with the browser or fetch tool you have.
3. A search-index proxy: `site:` queries against the same library or platform.
4. **"Unavailable"**, with the route you tried and what it would have told you.

An empty answer is a finding only when a second, different route agrees. Two
searches against the same index are not two routes.

## Reading pages without an API

- **Filter on the server.** Use the library's own advertiser, country, status and
  date filters; do not fetch everything and sift in your head.
- **Page until the cursor is empty.** Then check the count you hold against the
  total the page reports. A mismatch is a limitation to state, not a rounding
  error to hide.
- **One sample, then counts.** Open one ad or post fully to describe format and
  copy; take only dates and ids from the rest.
- **Screenshots are evidence.** An ad that disappears is still shown by its
  screenshot. Save it into `images/` with a name that says what it is.
- **Logins are walls.** A public library that asks you to sign in is not
  evidence. Say which library was behind a wall.

## Big responses

Never page raw JSON through the chat. The tool writes a file, `python3` reads it:

```bash
python3 -I - <<'PY'
import json, csv, sys
rows = json.load(open("raw/meta-ads.json"))
# keep the fields the ledger needs; drop the rest
PY
```

Trim to the fields in `ledger.csv`, save the trimmed file, and keep the raw file
so a later question doesn't need a second pull. Attributes, ids and cursors
expire between sessions: restart from page one if a cursor is old.

## Caps and cost

- **Free routes still have a cap: your patience.** Set a call budget per step
  before you start, and say when you stop because of it rather than because the
  source ran out.
- **A billed tool needs a quoted price before its first call.** Ask what one call
  costs, and set a per-brand cap (a common default is a few dollars). Never let a
  single step outspend the whole teardown.
- If a step hits the cap, the row count is "pulled N of M" and part 1 says so.

## Country and language

The market decides what counts. Record the country and language in the working
folder, filter every library and search by them, and state the market on the
report. A US-only brand's EU ads are not evidence about a US holiday.
