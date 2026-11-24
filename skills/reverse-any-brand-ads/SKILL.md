---
name: reverse-any-brand-ads
description: Pull every ad, every creator collab and every owned post a brand ran in a window — counted in full, dated, labelled and linked, saved as rows another step can compute from. Use when asked what ads a brand is running or ran, how many, on which channels and formats, whether creators were paid, gifted or affiliated, which posts went viral, or to build the what-ran-when evidence for a brand teardown. Public ad libraries and creator pages only — no accounts, no paid API required.
license: MIT
compatibility: Needs a filesystem and some way to read public web pages (a browser tool is best). Python 3 is optional; it only saves you typing.
metadata:
  author: reverse-any-brand
  version: "1.0.0"
---

# Reverse any brand: the ads and collabs archive

One job: turn "the brand ran some ads" into rows. Every ad, every collab post,
every owned post in the window, dated and linked, with the labelling the
teardown later counts and prices.

This is steps 2-4 of `reverse-any-brand` on their own. Use it standalone when
the question is just about ads or creators, or hand it the middle of a full
teardown. Its output is rows, not a narrative: a paragraph saying "they ran a
lot of ads" is a failed pull.

## Inputs

- Brand, exactly as the user names it.
- Country and language. The library filter decides what counts.
- Window: `date_start` and `date_end`. From a teardown, take them from
  `rab.py window`. Standalone, ask for the window or default to the last 90 days
  and say so.
- Season label, if a teardown will consume the rows ("Last year (2025)").

If two of these are missing and cannot be inferred, ask once, in one message.

## What "every" means

Page until the source is empty. Then compare the count you hold with the total the
source reports, and write the difference in the notes: "pulled 214 of 214" or
"pulled 180 of 214, cursor expired". Never scale, never extrapolate, never round
to "about 200".

An empty result is a finding only when a second, different route agrees. Two
searches against the same index are one route.

## 1 · Paid ads

Per network: Meta ad archive, Google ads transparency, TikTok ad library and
creative centre, plus any network the brand obviously uses (LinkedIn for B2B,
Pinterest for home, Snapchat for youth). For each network:

- Filter by advertiser, country, status and the window. If the library offers a
  "started running" filter, use the window; if it only offers "active", pull
  active and note that ended ads may be missing.
- Page through. Keep per ad: first seen date, last seen date, network, format
  (image, video, carousel, collection), the offer in the copy, the landing page,
  and whether it runs from a creator or partner page.
- Open one ad per format and network fully to describe the creative. Screenshot
  it into `images/` if the teardown will show it; a creative that disappears is
  still evidence when it's saved.
- No ads for that country → say "none found in the <country> library", not "no
  ads".

## 2 · Creator collabs

Search wide, then clean. Searches, per brand: brand name, each holiday or
campaign term, "tiktok shop", "deal", "code", "gifted", "partner", "haul", and one
per product name. Then the hashtag and tagged-post pages, and the brand's own
tagged post list.

Clean and label from the raw item, never from the vibe:

| Label | What the item shows |
| --- | --- |
| paid | `is_paid_partnership`, `branded_content_accounts`, #ad, #partner, "paid partnership" |
| gifted | gifted, PR, sent me, unboxing with no code |
| affiliate | a shop anchor, "creator earns commission", a storefront link |
| code | a discount code or affiliate link in the caption |
| ad | the same post also appears in the ad library from the creator's page |
| dupe | the product doesn't carry the brand or model name, or the caption says dupe / "$X vs $Y" |

Keep for each post: post id, date, creator handle, followers, views, caption
hook, kind label, product shown, link. Tier by followers: under 10k, 10-100k,
100-500k, 500k-1M, 1M+.

A post can carry two labels (affiliate and ad). Record the strongest commercial
one in the kind field and the rest in notes.

## 3 · Owned posts

Every post on the brand's own handles back to the window start, both seasons
where dates allow. Tag each: holiday | offer (%, sale, code, gift) | launch |
none, and record which product it shows. Owned posts are read for the offer
calendar and the product line-up, not ranked against collabs.

## Write the rows

One row per unit, in `ledger.csv`. If `reverse-any-brand` is installed as a
sibling skill, use its script:

```bash
RAB="../reverse-any-brand/scripts/rab.py"
python3 "$RAB" ledger add --dir ./brand-teardown \
  --brand "Acme" --season "Last year (2025)" --channel collabs --kind post \
  --collab-kind affiliate --date-start 2025-11-12 --followers 8400 \
  --views 120000 --price 49 --units-sold 300 \
  --what "TikTok Shop affiliate, hero product, 20% code" \
  --link "https://tiktok.com/@creator/video/123" --seen seen
```

Otherwise append plain CSV rows with this header, which is the same schema:

```
id,brand,season,channel,kind,date_start,date_end,what,link,views,followers,price,units_sold,collab_kind,seen,pulled,notes
```

Channels: `paid`, `collabs`, `owned`. Kinds: `ad`, `post`. `seen` is `seen` when
a page or image shows it and `inferred` when you reasoned it (say from what, in
notes). Never write a field you didn't see.

## Hand back

Report, in a few lines:

- Per network and channel: units pulled, and "pulled N of M" where the source
  stopped early.
- The labels: how many paid, gifted, affiliate, dupe; which tiers carried them.
- The three loudest units by views, with links.
- What you could not see: a library behind a login, a country with no coverage, a
  cursor that expired, a product page that hid its price.

Then stop. Pricing, counting per week, spend and the verdict belong to
`reverse-any-brand`; this skill's job ends when the rows are saved.
