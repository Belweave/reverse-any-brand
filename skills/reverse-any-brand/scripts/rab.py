#!/usr/bin/env python3
"""rab.py - deterministic bookkeeping for reverse-any-brand.

Every number in a teardown comes from here, not from mental arithmetic. The
agent gathers rows (dated, linked) and this file turns them into weeks, spend,
sales, tests, a verdict, and pre-publish checks.

Standard library only. No network. No accounts. Python 3.9+.

Commands:
  init    create an output folder with empty, correctly headed files
  window  day 0, the spend windows, D-n, and season labels for a holiday
  ledger  add / list / count dated rows (ads, posts, moves, snapshots)
  spend   estimated spend per week and by type, with low / mid / high
  sales   estimated sales by channel, with ranges, trust, and totals
  tests   the six tests and the verdict gate
  check   pre-publish checks on report.html and the CSVs

Exit codes: 0 ok, 1 check failed, 2 bad input.
"""

import argparse
import csv
import datetime as dt
import hashlib
import html.parser
import json
import os
import sys

D = dt.date
ONE = dt.timedelta(days=1)

LEDGER_FIELDS = [
    "id", "brand", "season", "channel", "kind", "date_start", "date_end",
    "what", "link", "views", "followers", "price", "units_sold",
    "collab_kind", "seen", "pulled", "notes",
]

CHANNELS = ["paid", "collabs", "owned", "site", "retail", "search", "pr", "email"]
CHANNEL_LABEL = {
    "paid": "Paid ads", "collabs": "Social media collabs", "owned": "Owned social",
    "site": "Site & offers", "retail": "Retail & prices", "search": "Search & PR",
    "pr": "PR", "email": "Email & loyalty",
}

# Spend rates. Estimates at market rates, always shown with their range.
# Override any of this with --rates rates.json. Refresh the numbers from a
# current source before a run and cite what you used.
RATES = {
    "ad_live_ad_day": {"mid": 150, "low": 50, "high": 400},
    # paid creator post, by follower tier (max_followers)
    "collab_tiers": [
        {"max_followers": 10000, "mid": 150, "low": 50, "high": 300},
        {"max_followers": 100000, "mid": 750, "low": 250, "high": 1500},
        {"max_followers": 500000, "mid": 3000, "low": 1500, "high": 5000},
        {"max_followers": 1000000, "mid": 8000, "low": 5000, "high": 12000},
        {"max_followers": None, "mid": 20000, "low": 10000, "high": 50000},
    ],
    "affiliate": {
        "conv_low": 0.0006, "conv_mid": 0.002, "conv_high": 0.0036,
        "commission_low": 0.05, "commission_mid": 0.12, "commission_high": 0.20,
    },
    "owned_post": {"mid": 1000, "low": 150, "high": 3000},
    "pr_event": {"mid": 100000, "low": 30000, "high": 200000},
    # a monthly ad budget becomes spend in a window; the budget itself is an estimate
    "budget_spread": {"low": 0.6, "mid": 1.0, "high": 1.5},
}

NOT_ESTIMATED = {
    "retail_coop": "retailer co-op fees",
    "email": "email / SMS sends",
    "staff": "staff time",
}


# ---------------------------------------------------------------- utilities

def die(msg, code=2):
    sys.stderr.write("rab: %s\n" % msg)
    raise SystemExit(code)


def parse_date(s):
    if not s:
        return None
    try:
        return D.fromisoformat(str(s).strip())
    except ValueError:
        die("bad date %r, want YYYY-MM-DD" % s)


def num(v):
    """Parse a number that may come from CSV, CLI, or JSON. Blank is None."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "").replace("$", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def money(v):
    if v is None:
        return "not estimated"
    return "$%s" % format(int(round(v)), ",d")


def rng(d):
    """Format a low/mid/high dict."""
    return "%s (%s - %s)" % (money(d.get("mid")), money(d.get("low")), money(d.get("high")))


def week_of(d, day0):
    """Week index relative to day 0. Negative is before. Floor, so -1 day is week -1."""
    return (d - day0).days // 7


def week_date(day0, w):
    return day0 + dt.timedelta(days=7 * w)


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return [dict(r) for r in csv.DictReader(f)]


def write_csv(path, fields, rows):
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def load_json(path):
    if not path:
        return {}
    if not os.path.exists(path):
        die("no such file: %s" % path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def emit(obj, as_json, text):
    if as_json:
        print(json.dumps(obj, indent=2, ensure_ascii=False))
    else:
        print(text)


# ---------------------------------------------------------------- holidays

def nth_weekday(year, month, weekday, n):
    d = D(year, month, 1)
    off = (weekday - d.weekday()) % 7
    return d + dt.timedelta(days=off + 7 * (n - 1))


def easter(year):
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return D(year, month, day + 1)


HOLIDAY_ALIASES = {
    "black friday": ["black friday", "cyber monday", "bfcm", "black friday sale"],
    "cyber monday": ["cyber monday", "bfcm", "black friday"],
    "christmas": ["christmas sale", "holiday sale", "christmas gifts", "xmas"],
    "singles day": ["singles day", "11.11", "double 11", "11/11"],
    "valentines": ["valentine's day", "valentines", "valentine sale", "gifts for her"],
    "mothers day": ["mother's day", "mothers day gifts", "gifts for mom"],
    "fathers day": ["father's day", "fathers day gifts", "gifts for dad"],
    "halloween": ["halloween", "halloween costume", "spooky season"],
    "easter": ["easter sale", "easter gifts", "easter basket"],
    "back to school": ["back to school", "back to school sale", "school supplies"],
    "prime day": ["prime day", "amazon prime day", "prime big deal days"],
    "thanksgiving": ["thanksgiving sale", "thanksgiving"],
    "july 4th": ["4th of july", "july 4th sale", "independence day sale"],
    "labor day": ["labor day sale", "labor day"],
}


def normalize_holiday(name):
    k = " ".join(str(name).strip().lower().replace("’", "'").split())
    k = k.replace("'s day", "s day").replace("day", "day")
    table = {
        "bf": "black friday", "bfcm": "black friday",
        "black friday / cyber monday": "black friday",
        "xmas": "christmas", "singles' day": "singles day", "11.11": "singles day",
        "double 11": "singles day", "valentine's day": "valentines",
        "valentine": "valentines", "mother's day": "mothers day",
        "father's day": "fathers day", "4th of july": "july 4th",
        "july fourth": "july 4th", "independence day": "july 4th",
        "amazon prime day": "prime day", "prime big deal days": "prime day",
        "back-to-school": "back to school", "bts": "back to school",
        "halloween costume season": "halloween",
    }
    return table.get(k, k)


def holiday_window(name, year):
    """Return (day0, peak_end, note). Day 0 is the anchor the whole report counts from."""
    k = normalize_holiday(name)
    if k == "black friday":
        t = nth_weekday(year, 11, 3, 4)          # US Thanksgiving, Thursday
        return t + ONE, t + dt.timedelta(days=4), "peak ends Cyber Monday"
    if k == "cyber monday":
        t = nth_weekday(year, 11, 3, 4)
        d0 = t + dt.timedelta(days=4)
        return d0, d0, "one-day peak"
    if k == "thanksgiving":
        t = nth_weekday(year, 11, 3, 4)
        return t - ONE, t, "peak ends Thanksgiving"
    if k == "christmas":
        return D(year, 12, 1), D(year, 12, 24), "peak ends Dec 24"
    if k == "singles day":
        return D(year, 11, 1), D(year, 11, 11), "presales from ~Oct 20; peak Nov 11"
    if k == "valentines":
        return D(year, 2, 1), D(year, 2, 14), "peak ends Feb 14"
    if k == "mothers day":
        s = nth_weekday(year, 5, 6, 2)
        return s - dt.timedelta(days=14), s, "peak ends the Sunday itself"
    if k == "fathers day":
        s = nth_weekday(year, 6, 6, 3)
        return s - dt.timedelta(days=14), s, "peak ends the Sunday itself"
    if k == "halloween":
        return D(year, 10, 1), D(year, 10, 31), "peak ends Oct 31"
    if k == "easter":
        e = easter(year)
        return e - dt.timedelta(days=21), e, "peak ends Easter Sunday"
    if k == "back to school":
        return D(year, 8, 1), D(year, 8, 31), "jurisdiction varies; confirm with the user"
    if k == "july 4th":
        return D(year, 7, 1), D(year, 7, 4), "peak ends July 4"
    if k == "labor day":
        m = nth_weekday(year, 9, 0, 1)
        return m - dt.timedelta(days=7), m, "peak ends Labor Day"
    if k == "prime day":
        t = nth_weekday(year, 7, 1, 2)
        return t, t + ONE, "mid-July, two days; confirm the exact dates from the announcement"
    return None, None, ""


def cmd_window(a):
    d0 = parse_date(a.day0) if a.day0 else None
    peak = parse_date(a.peak_end) if a.peak_end else None
    note = "explicit dates"
    if not d0:
        d0, peak, note = holiday_window(a.holiday, a.year)
        if not d0:
            die("unknown holiday %r. Search its dates, then pass --day0 and --peak-end."
                % a.holiday)
    peak = peak or d0
    today = parse_date(a.today) if a.today else D.today()
    if peak < d0:
        die("peak end is before day 0")
    mode = "retro" if today > peak else "live"
    seasons = {
        "last_year": "Last year (%d)" % (a.year - 1),
        "this_year": "This year so far (%d)" if mode == "live" else "This year (%d)",
    }
    seasons["this_year"] = seasons["this_year"] % a.year
    out = {
        "holiday": a.holiday, "year": a.year, "mode": mode, "note": note,
        "day0": d0.isoformat(), "peak_end": peak.isoformat(),
        "today": today.isoformat(), "d_n": (today - d0).days,
        "windows": {
            "baseline": [(d0 - dt.timedelta(days=70)).isoformat(), (d0 - dt.timedelta(days=42)).isoformat()],
            "ramp": [(d0 - dt.timedelta(days=28)).isoformat(), (d0 - ONE).isoformat()],
            "peak": [d0.isoformat(), peak.isoformat()],
            "after": [(peak + ONE).isoformat(), (peak + dt.timedelta(days=14)).isoformat()],
            "chart_weeks": [-12, 2],
            "final_verdict_on": (peak + dt.timedelta(days=14)).isoformat(),
        },
        "seasons": seasons,
        "holiday_terms": HOLIDAY_ALIASES.get(normalize_holiday(a.holiday), [a.holiday]),
    }
    if a.terms:
        out["holiday_terms"] = [t.strip() for t in a.terms.split(",") if t.strip()]
    w = out["windows"]
    text = "\n".join([
        "%s %d - %s" % (a.holiday, a.year, note),
        "day 0            %s" % out["day0"],
        "peak ends        %s" % out["peak_end"],
        "today            %s  (D%+d)" % (out["today"], out["d_n"]),
        "mode             %s" % mode,
        "baseline         %s to %s" % tuple(w["baseline"]),
        "ramp             %s to %s" % tuple(w["ramp"]),
        "peak             %s to %s" % tuple(w["peak"]),
        "after            %s to %s" % tuple(w["after"]),
        "chart weeks      %d to %d" % (w["chart_weeks"][0], w["chart_weeks"][1]),
        "verdict final    %s" % w["final_verdict_on"],
        "season labels    %s / %s" % (seasons["last_year"], seasons["this_year"]),
        "holiday terms    %s" % ", ".join(out["holiday_terms"]),
    ])
    emit(out, a.json, text)


# ---------------------------------------------------------------- ledger

def ledger_path(a):
    return a.file or os.path.join(a.dir, "ledger.csv")


def row_id(r):
    key = "|".join(str(r.get(k, "")) for k in
                   ("brand", "season", "channel", "kind", "date_start", "what"))
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def cmd_ledger_add(a):
    path = ledger_path(a)
    r = {
        "brand": a.brand, "season": a.season, "channel": a.channel, "kind": a.kind,
        "date_start": a.date_start, "date_end": a.date_end or a.date_start,
        "what": a.what or "", "link": a.link or "", "views": a.views or "",
        "followers": a.followers or "", "price": a.price or "",
        "units_sold": a.units_sold or "", "collab_kind": a.collab_kind or "",
        "seen": a.seen, "pulled": a.pulled or D.today().isoformat(),
        "notes": a.notes or "",
    }
    if r["channel"] not in CHANNELS:
        die("channel must be one of: %s" % ", ".join(CHANNELS))
    d0, d1 = parse_date(r["date_start"]), parse_date(r["date_end"])
    if d0 and d1 and d1 < d0:
        die("date_end is before date_start")
    r["id"] = row_id(r)
    rows = read_csv(path)
    if any(x.get("id") == r["id"] for x in rows):
        emit({"id": r["id"], "duplicate": True}, a.json, "duplicate, not added: %s" % r["id"])
        return
    rows.append(r)
    write_csv(path, LEDGER_FIELDS, rows)
    emit(r, a.json, "added %s  %s %s %s %s" % (r["id"], r["brand"], r["channel"], r["kind"], r["date_start"]))


def cmd_ledger_rows(a):
    rows = read_csv(ledger_path(a))
    if a.brand:
        rows = [r for r in rows if r.get("brand") == a.brand]
    if a.season:
        rows = [r for r in rows if r.get("season") == a.season]
    if a.channel:
        rows = [r for r in rows if r.get("channel") == a.channel]
    fields = LEDGER_FIELDS
    if a.json:
        emit(rows, True, "")
        return
    if not rows:
        print("no rows")
        return
    w = [max(len(str(r.get(f, ""))) for r in rows + [{f: f}]) for f in fields]
    for f, n in zip(fields, w):
        print(f.ljust(n), end="  ")
    print()
    for r in rows:
        for f, n in zip(fields, w):
            print(str(r.get(f, ""))[:n].ljust(n), end="  ")
        print()
    print("\n%d rows" % len(rows))


def ledger_summary(rows, day0):
    """Units live per week, per brand, season, channel."""
    weeks = {}
    skipped = []
    for r in rows:
        if r.get("channel") not in ("paid", "collabs", "owned", "site", "retail", "search", "pr", "email"):
            skipped.append(r.get("id"))
            continue
        s, e = parse_date(r.get("date_start")), parse_date(r.get("date_end")) or parse_date(r.get("date_start"))
        if not s or not e:
            skipped.append(r.get("id"))
            continue
        if e < s:
            s, e = e, s
        key = (r.get("brand", ""), r.get("season", ""), r.get("channel", ""))
        for w in range(week_of(s, day0), week_of(e, day0) + 1):
            slot = weeks.setdefault((key, w), {"units": 0, "views": 0.0, "items": []})
            slot["units"] += 1
            slot["views"] += num(r.get("views")) or 0.0
            if len(slot["items"]) < 6:
                slot["items"].append(r.get("what") or r.get("id"))
    return weeks, skipped


def cmd_ledger_count(a):
    day0 = parse_date(a.day0)
    if not day0:
        die("--day0 is required (get it from `rab.py window`)")
    rows = read_csv(ledger_path(a))
    weeks, skipped = ledger_summary(rows, day0)
    out_rows = []
    for (key, w), v in weeks.items():
        brand, season, channel = key
        out_rows.append({
            "brand": brand, "season": season, "week": w,
            "week_start": week_date(day0, w).isoformat(),
            "channel": channel, "units": v["units"], "views": int(v["views"]),
            "pulled": D.today().isoformat(),
        })
    out_rows.sort(key=lambda r: (r["brand"], r["season"], r["channel"], r["week"]))
    if a.out:
        write_csv(a.out, ["brand", "season", "week", "week_start", "channel", "units", "views", "pulled"], out_rows)
    # per-brand readouts
    brands = {}
    for r in out_rows:
        b = brands.setdefault((r["brand"], r["season"]), {"weekly": {}, "channels": {}})
        b["weekly"][r["week"]] = b["weekly"].get(r["week"], 0) + r["units"]
        b["channels"][r["channel"]] = b["channels"].get(r["channel"], 0) + r["units"]
    summary = {}
    for (brand, season), v in brands.items():
        ws = v["weekly"]
        before = [w for w in ws if w < 0]
        top_ch = sorted(v["channels"].items(), key=lambda kv: -kv[1])[:1]
        total = sum(v["channels"].values()) or 1
        summary["%s / %s" % (brand, season)] = {
            "prep_start_week": min(before) if before else None,
            "peak_week": max(ws, key=lambda w: (ws[w], -w)) if ws else None,
            "peak_units": ws[max(ws, key=lambda w: (ws[w], -w))] if ws else 0,
            "top_channel": top_ch[0][0] if top_ch else None,
            "top_channel_share": round(top_ch[0][1] / total, 3) if top_ch else None,
            "units_total": sum(v["channels"].values()),
        }
    text = ["%d rows -> %s" % (len(out_rows), a.out or "(no file written)")]
    if skipped:
        text.append("%d rows skipped (no usable dates): %s" % (len(skipped), ", ".join(map(str, skipped[:6]))))
    for k, v in summary.items():
        text.append("%s: prep week %s, peak week %s (%s units), top channel %s at %s%%" % (
            k, v["prep_start_week"], v["peak_week"], v["peak_units"], v["top_channel"],
            int((v["top_channel_share"] or 0) * 100)))
    emit({"rows": out_rows, "summary": summary, "skipped": skipped}, a.json, "\n".join(text))


# ---------------------------------------------------------------- spend

def tier(followers, rates):
    f = num(followers)
    for t in rates["collab_tiers"]:
        if t["max_followers"] is None or (f is not None and f < t["max_followers"]):
            return {"mid": t["mid"], "low": t["low"], "high": t["high"]}, t["max_followers"]
    return {"mid": 0, "low": 0, "high": 0}, None


def unit_cost(r, rates):
    """One row's estimated spend, with its range, or None if it is not estimated."""
    ch = (r.get("channel") or "").strip()
    kind = (r.get("kind") or "").strip()
    ck = (r.get("collab_kind") or "").strip().lower()
    price = num(r.get("price"))
    if ch == "paid" and kind in ("ad", "move"):
        s, e = parse_date(r.get("date_start")), parse_date(r.get("date_end")) or parse_date(r.get("date_start"))
        days = max(1, (e - s).days + 1) if s and e else 1
        rate = rates["ad_live_ad_day"]
        return {"type": "meta_tiktok_ads", "note": "%d ad-days at $%d/ad-day" % (days, rate["mid"]),
                "low": rate["low"] * days, "mid": rate["mid"] * days, "high": rate["high"] * days}
    if ch == "paid":
        return None
    if ch == "collabs":
        if ck in ("paid", "ad", "partnership", "sponsored", "paid partnership"):
            if num(r.get("followers")) is None:
                return None
            c, cap = tier(r.get("followers"), rates)
            return {"type": "paid_collab", "note": "paid post, %s followers" % format(int(num(r["followers"])), ",d"),
                    "low": c["low"], "mid": c["mid"], "high": c["high"]}
        if ck in ("gifted", "pr", "sample", "gifted/pr"):
            if price is None:
                return None
            return {"type": "gifted_collab", "note": "one product at retail", "low": price, "mid": price, "high": price}
        if ck in ("affiliate", "tiktok shop", "shop", "link", "code", "discount code"):
            views, aff = num(r.get("views")), rates["affiliate"]
            if views is None or price is None:
                return None
            base = {"type": "affiliate_collab"}
            out = {"type": "affiliate_collab",
                   "note": "views x bought-rate x price x commission + one sample",
                   "low": views * aff["conv_low"] * price * aff["commission_low"] + price,
                   "mid": views * aff["conv_mid"] * price * aff["commission_mid"] + price,
                   "high": views * aff["conv_high"] * price * aff["commission_high"] + price}
            sold = num(r.get("units_sold"))
            if sold is not None:  # cap at real sold units x price x commission
                cap = {"low": sold * price * aff["commission_low"],
                       "mid": sold * price * aff["commission_mid"],
                       "high": sold * price * aff["commission_high"]}
                out = {k: (min(out[k], cap[k]) if k in cap else v) for k, v in out.items()}
                out["note"] += "; capped at real sold units"
            out.update({"low": out["low"], "mid": out["mid"], "high": out["high"]})
            del base
            return out
        if ck in ("dupe", "organic", "none"):
            return None
        if num(r.get("followers")) is not None:
            c, _ = tier(r.get("followers"), rates)
            return {"type": "unclassified_collab", "note": "unclassified collab, charged as paid",
                    "low": c["low"], "mid": c["mid"], "high": c["high"]}
        return None
    if ch == "owned" and kind in ("post", "move"):
        c = rates["owned_post"]
        return {"type": "owned_post", "note": "cost of making one post", "low": c["low"], "mid": c["mid"], "high": c["high"]}
    if ch == "pr":
        c = rates["pr_event"]
        return {"type": "pr_event", "note": "PR event or brand collab", "low": c["low"], "mid": c["mid"], "high": c["high"]}
    return None


def budget_rows(budgets, day0, rates):
    """A monthly ad budget becomes spend inside a window. The budget is already an estimate."""
    out = []
    sp = rates["budget_spread"]
    for b in budgets:
        s, e = parse_date(b.get("from")), parse_date(b.get("to"))
        m = num(b.get("monthly_mid"))
        if not s or not e or m is None:
            continue
        days = (e - s).days + 1
        share = days / 30.4375
        out.append({"brand": b.get("brand", ""), "season": b.get("season", ""),
                    "low": m * share * sp["low"], "mid": m * share * sp["mid"],
                    "high": m * share * sp["high"],
                    "type": "google_search",
                    "note": "monthly budget estimate %s spread over %d days" % (money(m), days),
                    "week": week_of(s, day0)})
    return out


def cmd_spend(a):
    rates = json.loads(json.dumps(RATES))
    if a.rates:
        for k, v in load_json(a.rates).items():
            rates[k] = v
    day0 = parse_date(a.day0) or (D.today() - dt.timedelta(days=7))
    rows = read_csv(ledger_path(a))
    if a.brand:
        rows = [r for r in rows if r.get("brand") == a.brand]
    weeks, not_estimated, unestimated_count = {}, [], 0
    for r in rows:
        cost = unit_cost(r, rates)
        if not cost:
            unestimated_count += 1
            if r.get("channel") in ("site", "retail", "search", "email"):
                not_estimated.append(r.get("channel"))
            continue
        s = parse_date(r.get("date_start"))
        if not s:
            continue
        key = (r.get("brand", ""), r.get("season", ""), week_of(s, day0), cost["type"])
        slot = weeks.setdefault(key, {"low": 0.0, "mid": 0.0, "high": 0.0, "notes": []})
        for k in ("low", "mid", "high"):
            slot[k] += cost[k]
        if len(slot["notes"]) < 3:
            slot["notes"].append(cost["note"])
    for b in budget_rows(load_json(a.budget) if a.budget else [], day0, rates):
        key = (b["brand"], b["season"], b["week"], b["type"])
        slot = weeks.setdefault(key, {"low": 0.0, "mid": 0.0, "high": 0.0, "notes": []})
        for k in ("low", "mid", "high"):
            slot[k] += b[k]
        slot["notes"].append(b["note"])
    out = []
    for (brand, season, w, st), v in weeks.items():
        out.append({"brand": brand, "season": season, "week": w,
                    "week_start": week_date(day0, w).isoformat(), "spend_type": st,
                    "low": round(v["low"], 2), "mid": round(v["mid"], 2), "high": round(v["high"], 2),
                    "rate_note": "; ".join(v["notes"]), "pulled": D.today().isoformat()})
    out.sort(key=lambda r: (r["brand"], r["season"], r["week"], r["spend_type"]))
    if a.out:
        write_csv(a.out, ["brand", "season", "week", "week_start", "spend_type", "low", "mid", "high", "rate_note", "pulled"], out)
    brands = {}
    for r in out:
        b = brands.setdefault((r["brand"], r["season"]), {"low": 0.0, "mid": 0.0, "high": 0.0, "by": {}, "weekly": {}})
        for k in ("low", "mid", "high"):
            b[k] += r[k]
        b["by"][r["spend_type"]] = b["by"].get(r["spend_type"], 0.0) + r["mid"]
        b["weekly"][r["week"]] = b["weekly"].get(r["week"], 0.0) + r["mid"]
    summary = {}
    for k, v in brands.items():
        ranked = sorted(v["by"].items(), key=lambda kv: -kv[1])
        peak = max(v["weekly"].items(), key=lambda kv: kv[1]) if v["weekly"] else (None, 0)
        summary[" / ".join(k)] = {
            "low": round(v["low"], 2), "mid": round(v["mid"], 2),
            "high": round(v["high"], 2), "channels_ranked": ranked,
            "peak_spend_week": peak[0],
        }
    text = ["estimated spend, %d rows -> %s" % (len(out), a.out or "(no file written)")]
    for k, v in summary.items():
        text.append("%s: %s" % (k, rng(v)))
        text.append("  by type: " + ", ".join("%s %s" % (t, money(m)) for t, m in v["channels_ranked"]))
        text.append("  peak spend week: %s" % v["peak_spend_week"])
    if unestimated_count:
        text.append("%d rows carry no spend estimate (site, retail, search, email, dupes, or missing inputs)"
                    % unestimated_count)
    emit({"rows": out, "summary": summary, "not_estimated_rows": unestimated_count}, a.json, "\n".join(text))


# ---------------------------------------------------------------- sales

def est_units_price(units, price, floor=False):
    """A counted set of units at a seen price. A marketplace count is a floor, not a census."""
    mid = units * price
    if floor:
        return {"low": mid * 0.6, "mid": mid, "high": mid * 1.8}
    return {"low": mid * 0.85, "mid": mid, "high": mid * 1.15}


def sales_estimate(item):
    m, i = item.get("method"), item.get("inputs") or {}
    if m == "units_x_price":
        units, price = num(i.get("units")), num(i.get("price"))
        if units is None or price is None:
            return None
        r = est_units_price(units, price)
        note = "counted units x seen price"
    elif m == "bought_past_month_x_price":
        listings = i.get("listings") or []
        if not listings:
            return None
        total = sum((num(x.get("units")) or 0) * (num(x.get("price")) or 0) for x in listings)
        r = est_units_price(1, total, floor=True)
        note = "marketplace 'bought in past month' floor x price, %d listings" % len(i.get("listings", []))
    elif m == "visits_x_conv_x_aov":
        v, c, aov = num(i.get("visits")), (i.get("conv") or {}), num(i.get("aov"))
        if v is None or aov is None:
            return None
        cl, cm, ch = num(c.get("low")) or 0.01, num(c.get("mid")) or 0.02, num(c.get("high")) or 0.04
        r = {"low": v * cl * aov * 0.8, "mid": v * cm * aov, "high": v * ch * aov * 1.2}
        note = "visits x category conversion rate x order value"
    elif m == "views_x_share_x_price":
        v, s, p = num(i.get("views")), (i.get("share") or {}), num(i.get("price"))
        if v is None or p is None:
            return None
        r = {"low": v * (num(s.get("low")) or 0.001) * p,
             "mid": v * (num(s.get("mid")) or 0.002) * p,
             "high": v * (num(s.get("high")) or 0.004) * p}
        note = "views x share who buy x price; a ceiling, not a measurement"
    elif m == "review_growth_x_review_rate":
        n, rr, aov = num(i.get("new_reviews")), (i.get("review_rate") or {}), num(i.get("aov"))
        if n is None or aov is None:
            return None
        hi_r, mid_r, lo_r = num(rr.get("high")) or 0.02, num(rr.get("mid")) or 0.015, num(rr.get("low")) or 0.01
        r = {"low": n / hi_r * aov, "mid": n / mid_r * aov, "high": n / lo_r * aov}
        note = "new reviews / review rate x order value; a range because the rate is not public"
    elif m == "reported_share":
        rep, sh = num(i.get("reported_sales")), (i.get("share") or {})
        if rep is None:
            return None
        r = {"low": rep * (num(sh.get("low")) or 0.2), "mid": rep * (num(sh.get("mid")) or 0.25),
             "high": rep * (num(sh.get("high")) or 0.33)}
        note = "reported sales x this channel's share"
    else:
        return None
    lo, mid, hi = r["low"], r["mid"], r["high"]
    if not (lo <= mid <= hi):
        lo, mid, hi = min(lo, mid, hi), sorted([lo, mid, hi])[1], max(lo, mid, hi)
    return {"low": round(lo, 2), "mid": round(mid, 2), "high": round(hi, 2), "note": note}


def cmd_sales(a):
    data = load_json(a.input)
    items = data if isinstance(data, list) else data.get("channels", [])
    rows, skipped = [], []
    for it in items:
        e = sales_estimate(it)
        if not e:
            skipped.append("%s (%s)" % (it.get("channel"), it.get("method")))
            continue
        include = it.get("include_in_total", True)
        if isinstance(include, str):
            include = include.strip().lower() not in ("false", "no", "0", "")
        rows.append({
            "brand": it.get("brand", ""), "channel": it.get("channel", ""),
            "method": it.get("method", ""), "trust": it.get("trust", "low"),
            "low": e["low"], "mid": e["mid"], "high": e["high"],
            "include_in_total": "true" if include else "false",
            "kind": it.get("kind", ""), "note": e["note"],
            "snapshot_date": it.get("snapshot_date", ""),
            "pulled": D.today().isoformat(),
        })
    if a.out:
        write_csv(a.out, ["brand", "channel", "method", "trust", "low", "mid", "high",
                          "include_in_total", "kind", "note", "snapshot_date", "pulled"], rows)
    totals = {}
    for r in rows:
        b = totals.setdefault(r["brand"], {"low": 0.0, "mid": 0.0, "high": 0.0, "excluded": 0})
        if r["include_in_total"] == "true":
            for k in ("low", "mid", "high"):
                b[k] += r[k]
        else:
            b["excluded"] += 1
    text = ["estimated sales by channel, %d rows -> %s" % (len(rows), a.out or "(no file written)")]
    for r in rows:
        text.append("  %s %s %s %s trust=%s%s" % (
            r["brand"], r["channel"], money(r["low"]), money(r["high"]), r["trust"],
            "" if r["include_in_total"] == "true" else "  (kept out of the total)"))
    for b, v in totals.items():
        text.append("%s total: %s" % (b or "(unbranded)", rng(v)))
        if v["excluded"]:
            text.append("  %d row(s) kept out of the total" % v["excluded"])
    if skipped:
        text.append("not estimated: %s" % ", ".join(skipped))
    emit({"rows": rows, "totals": totals, "skipped": skipped}, a.json, "\n".join(text))


# ---------------------------------------------------------------- tests

def grade_demand(x):
    p, ly = num(x.get("peak_multiple")), num(x.get("baseline_multiple_last_year"))
    if p is None:
        return "can't tell", "no search series"
    if p <= 1.0:
        return "fail", "no rise above normal"
    if ly is None:
        return "can't tell", "rose %.1fx, no last-year comparison" % p
    if p > ly:
        return "pass", "%.1fx vs %.1fx last year" % (p, ly)
    return "mixed", "rose, but less than last year (%.1fx vs %.1fx)" % (p, ly)


def grade_reach(x):
    per = {k: num(v) for k, v in (x.get("per_dollar") or {}).items() if num(v) is not None}
    if len(per) < 2:
        return "can't tell", "needs at least two channels"
    ranked = sorted(per.items(), key=lambda kv: -kv[1])
    if ranked[0][1] >= 1.5 * ranked[1][1]:
        return "pass", "%s is %.1fx the next channel" % (ranked[0][0], ranked[0][1] / ranked[1][1])
    return "mixed", "channels are close; nothing is notably cheaper"


def grade_sales(x):
    h, n = num(x.get("holiday_units")), num(x.get("normal_units"))
    if h is None or not n:
        return "can't tell", "no period comparison"
    ch = (h - n) / n
    if ch > 0.15:
        return "pass", "%+.0f%% vs a normal window" % (ch * 100)
    if ch > 0:
        return "mixed", "%+.0f%% vs a normal window" % (ch * 100)
    return "fail", "%+.0f%% vs a normal window" % (ch * 100)


def grade_payback(x):
    s, sp = x.get("sales") or {}, x.get("spend") or {}
    if any(num(s.get(k)) is None for k in ("low", "high")) or any(num(sp.get(k)) is None for k in ("low", "high")):
        return "can't tell", "needs both a sales and a spend range"
    low = num(s["low"]) / num(sp["high"])
    mid = num(s["mid"]) / num(sp["mid"]) if num(s.get("mid")) and num(sp.get("mid")) else None
    high = num(s["high"]) / num(sp["low"])
    detail = "range %.2fx to %.2fx" % (low, high)
    if low > 1:
        return "pass", detail
    if mid is not None and mid > 1:
        return "mixed", detail
    return "fail", detail


def grade_price(x):
    d = num(x.get("discount_depth"))
    held, full = x.get("list_price_held"), x.get("new_models_full_price")
    if d is None:
        return "can't tell", "no price snapshot"
    if d <= 0.20 and full:
        return "pass", "%.0f%% off at most, new models at full price" % (d * 100)
    if d < 0.35 and (held is not False):
        return "mixed", "%.0f%% off" % (d * 100)
    return "fail", "%.0f%% off" % (d * 100)


def grade_retention(x):
    real, dupe = num(x.get("real_units")), num(x.get("dupe_units"))
    if real is None or dupe is None or (real + dupe) == 0:
        return "can't tell", "no dupe comparison"
    share = real / (real + dupe)
    if share >= 0.6:
        return "pass", "%.0f%% of units were the brand's" % (share * 100)
    if share >= 0.4:
        return "mixed", "%.0f%% of units were the brand's" % (share * 100)
    return "fail", "%.0f%% of units were the brand's" % (share * 100)


TESTS = [
    ("Demand rose", "peak-week search / baseline", "last year's multiple at the same D-day", "demand", grade_demand, "medium"),
    ("Reach was cheap", "views per estimated dollar, per channel", "the brand's other channels", "reach", grade_reach, "low"),
    ("Sales rose", "units or sales in the holiday window", "a normal window", "sales", grade_sales, "medium"),
    ("Spend paid back", "estimated sales / estimated spend, as a range", "1x", "payback", grade_payback, "low"),
    ("Price held", "discount depth on hero products", "list price, last year", "price", grade_price, "high"),
    ("Demand was kept", "real units / (real + dupe units)", "none", "retention", grade_retention, "high"),
]


def cmd_tests(a):
    data = load_json(a.input)
    out, grades = [], {}
    for name, number, compared, key, fn, trust in TESTS:
        block = data.get(key) or {}
        if key == "payback" and not block:
            block = {"sales": data.get("sales_est") or data.get("sales") or {},
                     "spend": data.get("spend") or {}}
        g, detail = fn(block)
        grades[name] = g
        out.append({"test": name, "number": number, "compared_with": compared,
                    "grade": g, "detail": detail, "trust": trust})
    d0 = parse_date(data.get("day0"))
    today = parse_date(data.get("today")) or D.today()
    final_on = d0 + dt.timedelta(days=14) if d0 else None
    sales_grade = grades["Sales rose"]
    passes = sum(1 for k, v in grades.items() if v == "pass")
    payback = grades["Spend paid back"]
    if final_on and today < final_on:
        verdict, why = "too early to call", "before day 0 + 14 (%s)" % final_on.isoformat()
    elif sales_grade == "can't tell":
        verdict, why = "can't tell yet", "no result number yet: volume alone never decides"
    elif sales_grade == "fail" or payback == "fail":
        verdict, why = "didn't work", "sales flat or down, or spend clearly not paid back"
    elif sales_grade == "pass" and passes >= 4:
        verdict, why = "worked", "sales rose and %d other tests pass" % (passes - 1)
    else:
        verdict, why = "mixed", "sales %s, %d of 6 tests pass" % (sales_grade, passes)
    text = ["%-18s %-8s %-6s %s" % (t["test"], t["grade"], t["trust"], t["detail"]) for t in out]
    text.append("")
    text.append("verdict: %s (%s)" % (verdict, why))
    if final_on:
        text.append("final on: %s" % final_on.isoformat())
    emit({"tests": out, "verdict": verdict, "why": why,
          "passes": passes, "final_on": final_on.isoformat() if final_on else None},
         a.json, "\n".join(text))


# ---------------------------------------------------------------- check

class Collector(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.imgs, self.text = set(), [], []
        self.counts = {}
        self.scripts = 0

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        self.counts[tag] = self.counts.get(tag, 0) + 1
        if d.get("id"):
            self.ids.add(d["id"])
        if tag == "img":
            self.imgs.append(d)
        if tag == "script":
            self.scripts += 1

    def handle_data(self, data):
        self.text.append(data)


REQUIRED_IDS = ("hero", "part-1", "part-2", "verdict")
REQUIRED_FILES = ("report.html", "ledger.csv", "volume_weekly.csv", "spend_weekly.csv",
                  "sales_channels.csv", "tests.json")


def cmd_check(a):
    d = a.dir
    fails, notes = [], []
    for f in REQUIRED_FILES:
        if not os.path.exists(os.path.join(d, f)):
            fails.append("missing file: %s" % f)
    report = os.path.join(d, "report.html")
    if not os.path.exists(report):
        emit({"failures": fails, "notes": notes}, a.json,
             "\n".join(["FAIL " + x for x in fails]))
        raise SystemExit(1)
    c = Collector()
    with open(report, encoding="utf-8") as f:
        c.feed(f.read())
    body = " ".join(c.text)
    for i in REQUIRED_IDS:
        if i not in c.ids:
            fails.append("report.html has no element with id=%r" % i)
    for img in c.imgs:
        src = img.get("src", "")
        if src.startswith(("http://", "https://")):
            fails.append("remote image will expire: %s" % src[:70])
        if not img.get("alt"):
            notes.append("image without alt: %s" % src[:50])
    if c.counts.get("h1", 0) != 1:
        fails.append("want exactly one h1, found %d" % c.counts.get("h1", 0))
    for b in a.brand or []:
        if b.lower() not in body.lower():
            fails.append("brand %r never appears in the report" % b)
    if "not pulled" not in body.lower():
        notes.append("no 'not pulled' anywhere: a week with no data must not read as zero")
    if "estimate" not in body.lower():
        fails.append("no 'estimate' label anywhere: every dollar figure needs one")
    # counts reconcile with the ledger; nothing scaled
    ledger = read_csv(os.path.join(d, "ledger.csv"))
    vol = read_csv(os.path.join(d, "volume_weekly.csv"))
    day0_hint = None
    if os.path.exists(os.path.join(d, "tests.json")):
        day0_hint = load_json(os.path.join(d, "tests.json")).get("day0")
    if ledger and vol:
        d0 = parse_date(a.day0 or day0_hint or "")
        if not d0:
            notes.append("no day 0 to reconcile weeks against: pass --day0")
        if d0:
            weeks, _ = ledger_summary(ledger, d0)
            want = {}
            for (key, w), v in weeks.items():
                want[(key[0], key[1], key[2])] = want.get((key[0], key[1], key[2]), 0) + v["units"]
            got = {}
            for r in vol:
                k = (r.get("brand", ""), r.get("season", ""), r.get("channel", ""))
                got[k] = got.get(k, 0) + int(num(r.get("units")) or 0)
            for k in sorted(set(want) | set(got)):
                if want.get(k, 0) != got.get(k, 0):
                    fails.append("volume_weekly disagrees with the ledger for %s: %s vs %s units"
                                 % (k, got.get(k, 0), want.get(k, 0)))
    # every count is dated
    for name in ("volume_weekly.csv", "spend_weekly.csv", "sales_channels.csv"):
        for i, r in enumerate(read_csv(os.path.join(d, name))):
            if not (r.get("pulled") or r.get("snapshot_date")):
                fails.append("%s row %d has no pulled/snapshot date" % (name, i + 2))
    # ranges are ordered, and dupes stay out of the totals
    for name in ("spend_weekly.csv", "sales_channels.csv"):
        for i, r in enumerate(read_csv(os.path.join(d, name))):
            lo, mid, hi = num(r.get("low")), num(r.get("mid")), num(r.get("high"))
            if None in (lo, mid, hi):
                if "" in (str(r.get("low")), str(r.get("mid")), str(r.get("high"))):
                    notes.append("%s row %d has a blank in a range: label it, don't zero it" % (name, i + 2))
                continue
            if not (lo <= mid <= hi):
                fails.append("%s row %d range is out of order: %s %s %s" % (name, i + 2, lo, mid, hi))
    for r in read_csv(os.path.join(d, "sales_channels.csv")):
        if r.get("include_in_total") == "false" and not r.get("kind"):
            notes.append("row kept out of the total without saying why: %s" % r.get("channel"))
    # a verdict needs a date it becomes final
    tests = load_json(os.path.join(d, "tests.json")) if os.path.exists(os.path.join(d, "tests.json")) else {}
    if tests and not tests.get("final_on") and tests.get("verdict") in ("too early to call", "can't tell yet"):
        fails.append("an open verdict needs the date it becomes final")
    status = "FAIL" if fails else "PASS"
    text = [status, "%d checks failed, %d notes" % (len(fails), len(notes))]
    text += ["  fail: " + f for f in fails]
    text += ["  note: " + n for n in notes]
    emit({"status": status, "failures": fails, "notes": notes}, a.json, "\n".join(text))
    if fails:
        raise SystemExit(1)


# ---------------------------------------------------------------- init

def cmd_init(a):
    d = a.dir
    os.makedirs(d, exist_ok=True)
    write_csv(os.path.join(d, "ledger.csv"), LEDGER_FIELDS, [])
    with open(os.path.join(d, "rates.json"), "w", encoding="utf-8") as f:
        json.dump(RATES, f, indent=2)
        f.write("\n")
    with open(os.path.join(d, "budget.json"), "w", encoding="utf-8") as f:
        json.dump([{"brand": "", "season": "", "source": "which tool or page said this",
                    "monthly_mid": 0, "from": "YYYY-MM-DD", "to": "YYYY-MM-DD",
                    "note": "already an estimate; say where it came from"}], f, indent=2)
        f.write("\n")
    with open(os.path.join(d, "sales.json"), "w", encoding="utf-8") as f:
        json.dump({"channels": [{
            "brand": "", "channel": "tiktok_shop", "method": "units_x_price",
            "inputs": {"units": 0, "price": 0}, "trust": "high",
            "include_in_total": True, "kind": "own", "snapshot_date": "YYYY-MM-DD",
            "note": "one row per channel; kind='dupe' rows set include_in_total false",
        }]}, f, indent=2)
        f.write("\n")
    with open(os.path.join(d, "tests.json"), "w", encoding="utf-8") as f:
        json.dump({
            "day0": "YYYY-MM-DD", "today": D.today().isoformat(),
            "demand": {"peak_multiple": None, "baseline_multiple_last_year": None},
            "reach": {"per_dollar": {}},
            "sales": {"holiday_units": None, "normal_units": None},
            "payback": {"sales": {"low": None, "mid": None, "high": None},
                        "spend": {"low": None, "mid": None, "high": None}},
            "price": {"discount_depth": None, "list_price_held": None, "new_models_full_price": None},
            "retention": {"real_units": None, "dupe_units": None},
        }, f, indent=2)
        f.write("\n")
    with open(os.path.join(d, "README.txt"), "w", encoding="utf-8") as f:
        f.write(
            "reverse-any-brand working folder\n\n"
            "ledger.csv         one row per ad, post, move or snapshot. Add with `rab.py ledger add`.\n"
            "volume_weekly.csv  units live per week, from `rab.py ledger count`.\n"
            "spend_weekly.csv   estimated spend per week and type, from `rab.py spend`.\n"
            "sales_channels.csv estimated sales per channel, from `rab.py sales`.\n"
            "tests.json         the measured inputs for the six tests, from `rab.py tests`.\n"
            "report.html        the report. Run `rab.py check` before you publish.\n"
            "images/            every image the report shows, downloaded at pull time.\n\n"
            "Blank is not zero. A week you did not pull says 'not pulled'.\n"
        )
    emit({"dir": d}, a.json, "created %s with ledger.csv, rates.json, budget.json, sales.json, tests.json, README.txt" % d)


# ---------------------------------------------------------------- main

def build_parser():
    p = argparse.ArgumentParser(prog="rab.py", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="create an output folder")
    s.add_argument("--dir", default="output")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("window", help="day 0, windows, D-n, season labels")
    s.add_argument("name", nargs="?", default="black friday")
    s.add_argument("--holiday", default=None)
    s.add_argument("--year", type=int, default=D.today().year)
    s.add_argument("--today", default=None)
    s.add_argument("--day0", default=None)
    s.add_argument("--peak-end", dest="peak_end", default=None)
    s.add_argument("--terms", default=None)
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_window)

    s = sub.add_parser("ledger", help="dated rows")
    lsub = s.add_subparsers(dest="lcmd", required=True)
    add = lsub.add_parser("add", help="add one row")
    add.add_argument("--dir", default="output")
    add.add_argument("--file", default=None)
    add.add_argument("--brand", required=True)
    add.add_argument("--season", required=True)
    add.add_argument("--channel", required=True)
    add.add_argument("--kind", required=True)
    add.add_argument("--date-start", dest="date_start", required=True)
    add.add_argument("--date-end", dest="date_end", default=None)
    add.add_argument("--what", default="")
    add.add_argument("--link", default="")
    add.add_argument("--views", default="")
    add.add_argument("--followers", default="")
    add.add_argument("--price", default="")
    add.add_argument("--units-sold", dest="units_sold", default="")
    add.add_argument("--collab-kind", dest="collab_kind", default="")
    add.add_argument("--seen", choices=["seen", "inferred"], default="seen")
    add.add_argument("--pulled", default=None)
    add.add_argument("--notes", default="")
    add.add_argument("--json", action="store_true")
    add.set_defaults(fn=cmd_ledger_add)
    rows = lsub.add_parser("rows", help="list rows")
    rows.add_argument("--dir", default="output")
    rows.add_argument("--file", default=None)
    rows.add_argument("--brand", default=None)
    rows.add_argument("--season", default=None)
    rows.add_argument("--channel", default=None)
    rows.add_argument("--json", action="store_true")
    rows.set_defaults(fn=cmd_ledger_rows)
    cnt = lsub.add_parser("count", help="units live per week")
    cnt.add_argument("--dir", default="output")
    cnt.add_argument("--file", default=None)
    cnt.add_argument("--day0", required=True)
    cnt.add_argument("--out", default=None)
    cnt.add_argument("--json", action="store_true")
    cnt.set_defaults(fn=cmd_ledger_count)

    s = sub.add_parser("spend", help="estimated spend")
    s.add_argument("--dir", default="output")
    s.add_argument("--file", default=None)
    s.add_argument("--day0", dest="day0", default=None)
    s.add_argument("--brand", default=None)
    s.add_argument("--rates", default=None)
    s.add_argument("--budget", default=None)
    s.add_argument("--out", default=None)
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_spend)

    s = sub.add_parser("sales", help="estimated sales by channel")
    s.add_argument("--input", default="output/sales.json")
    s.add_argument("--out", default=None)
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_sales)

    s = sub.add_parser("tests", help="six tests and the verdict")
    s.add_argument("--input", default="output/tests.json")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_tests)

    s = sub.add_parser("check", help="pre-publish checks")
    s.add_argument("--dir", default="output")
    s.add_argument("--brand", action="append", default=None)
    s.add_argument("--day0", dest="day0", default=None)
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_check)
    return p


def main(argv):
    p = build_parser()
    a = p.parse_args(argv)
    if a.cmd == "window" and getattr(a, "holiday", None):
        a.name = a.holiday
    if a.cmd == "window":
        a.holiday = a.name
    return a.fn(a) or 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
