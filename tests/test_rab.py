#!/usr/bin/env python3
"""Tests for rab.py. Run: python3 tests/test_rab.py

These run the real script in temp folders and check the arithmetic and the
checks, not the prose. If a test fails, the numbers in a report are wrong.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RAB = os.path.join(HERE, "..", "skills", "reverse-any-brand", "scripts", "rab.py")


def run(*args, ok=True):
    p = subprocess.run([sys.executable, RAB] + list(args), capture_output=True, text=True)
    if ok and p.returncode != 0:
        raise AssertionError("rab.py %s failed:\n%s\n%s" % (" ".join(args), p.stdout, p.stderr))
    return p


def jrun(*args, ok=True):
    return json.loads(run(*args, "--json", ok=ok).stdout)


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="rab-")

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def path(self, name):
        return os.path.join(self.d, name)

    def write(self, name, obj):
        with open(self.path(name), "w", encoding="utf-8") as f:
            json.dump(obj, f)

    def csv(self, name):
        import csv
        with open(self.path(name), newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def add(self, **kw):
        base = dict(dir=self.d, brand="Acme", season="Last year (2025)", channel="paid",
                    kind="ad", date_start="2025-11-10", date_end="2025-11-10")
        base.update(kw)
        args = ["ledger", "add"]
        for k, v in base.items():
            args += ["--" + k.replace("_", "-"), str(v)]
        return jrun(*args)


class Holidays(Base):
    def test_black_friday_is_the_day_after_us_thanksgiving(self):
        w = jrun("window", "black friday", "--year", "2026", "--today", "2026-11-01")
        self.assertEqual(w["day0"], "2026-11-27")     # 4th Thursday is Nov 26
        self.assertEqual(w["peak_end"], "2026-11-30")  # Cyber Monday
        self.assertEqual(w["mode"], "live")
        self.assertEqual(w["d_n"], -26)

    def test_windows_are_relative_to_day_zero(self):
        w = jrun("window", "christmas", "--year", "2025", "--today", "2025-11-01")
        self.assertEqual(w["windows"]["baseline"], ["2025-09-22", "2025-10-20"])
        self.assertEqual(w["windows"]["ramp"], ["2025-11-03", "2025-11-30"])
        self.assertEqual(w["windows"]["after"], ["2025-12-25", "2026-01-07"])
        self.assertEqual(w["windows"]["final_verdict_on"], "2026-01-07")

    def test_retro_mode_after_the_peak(self):
        w = jrun("window", "halloween", "--year", "2025", "--today", "2025-11-05")
        self.assertEqual(w["mode"], "retro")
        self.assertEqual(w["seasons"]["this_year"], "This year (2025)")

    def test_live_mode_labels_a_partial_season(self):
        w = jrun("window", "halloween", "--year", "2025", "--today", "2025-10-05")
        self.assertEqual(w["mode"], "live")
        self.assertEqual(w["seasons"]["this_year"], "This year so far (2025)")

    def test_mothers_day_counts_back_two_weeks(self):
        w = jrun("window", "mothers day", "--year", "2026", "--today", "2026-01-01")
        self.assertEqual(w["peak_end"], "2026-05-10")
        self.assertEqual(w["day0"], "2026-04-26")

    def test_unknown_holiday_asks_for_dates(self):
        p = run("window", "diwali", "--year", "2026", ok=False)
        self.assertEqual(p.returncode, 2)
        self.assertIn("--day0", p.stderr)

    def test_explicit_dates_win(self):
        w = jrun("window", "diwali", "--year", "2026", "--today", "2026-10-01",
                 "--day0", "2026-11-08", "--peak-end", "2026-11-08")
        self.assertEqual(w["day0"], "2026-11-08")


class Ledger(Base):
    def test_a_row_is_added_once(self):
        first = self.add(what="bfcm ad")
        second = self.add(what="bfcm ad")
        self.assertEqual(first["id"], second["id"])
        self.assertTrue(second.get("duplicate"))
        self.assertEqual(len(self.csv("ledger.csv")), 1)

    def test_a_bad_channel_is_refused(self):
        p = run("ledger", "add", "--dir", self.d, "--brand", "A", "--season", "S",
                "--channel", "tv", "--kind", "ad", "--date-start", "2025-11-01", ok=False)
        self.assertEqual(p.returncode, 2)
        self.assertIn("channel must be one of", p.stderr)

    def test_an_ad_counts_in_every_week_it_ran(self):
        self.add(date_start="2025-11-01", date_end="2025-11-21", what="long ad")
        out = jrun("ledger", "count", "--dir", self.d, "--day0", "2025-11-28",
                   "--out", self.path("volume.csv"))
        weeks = [r["week"] for r in out["rows"]]
        self.assertEqual(weeks, [-4, -3, -2, -1])  # 1 Nov to 21 Nov spans four weeks
        self.assertTrue(all(r["units"] == 1 for r in out["rows"]))
        self.assertEqual(len(self.csv("volume.csv")), 4)

    def test_summary_finds_prep_start_and_peak(self):
        self.add(date_start="2025-11-01", date_end="2025-11-07", what="early")
        self.add(date_start="2025-11-20", date_end="2025-11-26", what="late")
        self.add(date_start="2025-11-20", date_end="2025-11-26", channel="owned", kind="post", what="own")
        out = jrun("ledger", "count", "--dir", self.d, "--day0", "2025-11-28")
        s = out["summary"]["Acme / Last year (2025)"]
        self.assertEqual(s["prep_start_week"], -4)
        self.assertEqual(s["peak_week"], -2)
        self.assertEqual(s["units_total"], 6)          # week units: 2 + 2 + 2
        self.assertEqual(s["top_channel"], "paid")

    def test_a_row_without_dates_is_reported_not_dropped_silently(self):
        self.add(date_start="", date_end="")
        out = jrun("ledger", "count", "--dir", self.d, "--day0", "2025-11-28")
        self.assertEqual(out["rows"], [])
        self.assertEqual(len(out["skipped"]), 1)


class Spend(Base):
    def spend(self, *extra, **kw):
        out = jrun("spend", "--dir", self.d, "--day0", "2025-11-28",
                   "--out", self.path("spend.csv"), *extra)
        return out

    def test_an_ad_costs_its_days(self):
        self.add(date_start="2025-11-10", date_end="2025-11-12")
        row = self.spend()["rows"][0]
        self.assertEqual(row["mid"], 450)    # 3 days x $150
        self.assertEqual(row["low"], 150)    # 3 x $50
        self.assertEqual(row["high"], 1200)  # 3 x $400

    def test_collab_tiers_do_not_leak_between_bands(self):
        self.add(channel="collabs", kind="post", collab_kind="paid", followers=9999,
                 date_start="2025-11-03", date_end="2025-11-03")
        self.add(channel="collabs", kind="post", collab_kind="paid", followers=100000,
                 date_start="2025-11-10", date_end="2025-11-10")
        self.add(channel="collabs", kind="post", collab_kind="paid", followers=1500000,
                 date_start="2025-11-17", date_end="2025-11-17")
        mids = sorted(r["mid"] for r in self.spend()["rows"])
        self.assertEqual(mids, [150, 3000, 20000])

    def test_a_gifted_post_costs_the_product(self):
        self.add(channel="collabs", kind="post", collab_kind="gifted", price=79)
        row = self.spend()["rows"][0]
        self.assertEqual((row["low"], row["mid"], row["high"]), (79, 79, 79))

    def test_an_affiliate_post_is_capped_at_real_sales(self):
        self.add(channel="collabs", kind="post", collab_kind="affiliate",
                 views=10000000, price=50, units_sold=100)
        row = self.spend()["rows"][0]
        self.assertLessEqual(row["mid"], 100 * 50 * 0.12 + 50)
        self.assertIn("capped", row["rate_note"])

    def test_owned_posts_and_pr_events_use_their_rates(self):
        self.add(channel="owned", kind="post")
        self.add(channel="pr", kind="move", what="launch event")
        rows = {r["spend_type"]: r for r in self.spend()["rows"]}
        self.assertEqual(rows["owned_post"]["mid"], 1000)
        self.assertEqual(rows["pr_event"]["mid"], 100000)

    def test_site_retail_search_email_are_not_estimated(self):
        for ch in ("site", "retail", "search", "email"):
            self.add(channel=ch, kind="move", what="x " + ch)
        out = self.spend()
        self.assertEqual(out["rows"], [])
        self.assertEqual(out["not_estimated_rows"], 4)

    def test_a_monthly_budget_becomes_spend_in_the_window(self):
        self.write("budget.json", [{"brand": "Acme", "season": "Last year (2025)",
                                    "monthly_mid": 30000,
                                    "from": "2025-11-01", "to": "2025-11-30"}])
        out = jrun("spend", "--dir", self.d, "--day0", "2025-11-28",
                   "--budget", self.path("budget.json"))
        row = out["rows"][0]
        self.assertEqual(row["spend_type"], "google_search")
        self.assertAlmostEqual(row["mid"], 30000, delta=500)  # 30 of ~30.4 days

    def test_the_total_is_the_sum_of_its_parts(self):
        self.add(date_start="2025-11-10", date_end="2025-11-10")
        self.add(channel="collabs", kind="post", collab_kind="paid", followers=250000)
        out = self.spend()
        total = sum(r["mid"] for r in out["rows"])
        self.assertAlmostEqual(out["summary"]["Acme / Last year (2025)"]["mid"], total, places=2)

    def test_rates_can_be_overridden(self):
        self.write("rates.json", {"ad_live_ad_day": {"mid": 200, "low": 100, "high": 300}})
        self.add(date_start="2025-11-10", date_end="2025-11-10")
        row = jrun("spend", "--dir", self.d, "--day0", "2025-11-28",
                   "--rates", self.path("rates.json"))["rows"][0]
        self.assertEqual(row["mid"], 200)


class Sales(Base):
    def sales(self, channels):
        self.write("sales.json", {"channels": channels})
        return jrun("sales", "--input", self.path("sales.json"),
                    "--out", self.path("sales.csv"))

    def test_counted_units_at_a_seen_price(self):
        out = self.sales([{"brand": "Acme", "channel": "tiktok_shop", "method": "units_x_price",
                           "inputs": {"units": 1000, "price": 50}, "trust": "high",
                           "snapshot_date": "2025-12-01"}])
        row = out["rows"][0]
        self.assertEqual(row["mid"], 50000)
        self.assertLess(row["low"], row["mid"])
        self.assertLess(row["mid"], row["high"])

    def test_a_marketplace_floor_is_widened_downwards(self):
        out = self.sales([{"brand": "Acme", "channel": "amazon",
                           "method": "bought_past_month_x_price",
                           "inputs": {"listings": [{"units": 100, "price": 50}]},
                           "snapshot_date": "2025-12-01"}])
        row = out["rows"][0]
        self.assertEqual(row["mid"], 5000)
        self.assertLess(row["low"], 5000 * 0.7)  # a floor, so the range reaches lower

    def test_dupes_stay_out_of_the_total(self):
        out = self.sales([
            {"brand": "Acme", "channel": "own_shop", "method": "units_x_price",
             "inputs": {"units": 100, "price": 50}, "snapshot_date": "2025-12-01"},
            {"brand": "Acme", "channel": "dupes", "method": "units_x_price",
             "inputs": {"units": 900, "price": 50}, "kind": "dupe",
             "include_in_total": False, "snapshot_date": "2025-12-01"}])
        self.assertEqual(out["totals"]["Acme"]["mid"], 5000)
        self.assertEqual(out["totals"]["Acme"]["excluded"], 1)

    def test_review_growth_needs_the_rate_that_helps_most(self):
        out = self.sales([{"brand": "Acme", "channel": "other_retail",
                           "method": "review_growth_x_review_rate",
                           "inputs": {"new_reviews": 300, "aov": 40,
                                      "review_rate": {"low": 0.01, "mid": 0.015, "high": 0.02}},
                           "snapshot_date": "2025-12-01"}])
        row = out["rows"][0]
        self.assertEqual(row["mid"], 800000)       # 300 / 0.015 x 40
        self.assertGreater(row["high"], row["mid"])  # a low review rate means more orders

    def test_a_missing_input_is_skipped_not_guessed(self):
        out = self.sales([{"brand": "Acme", "channel": "own_site",
                           "method": "visits_x_conv_x_aov", "inputs": {"visits": 1000}}])
        self.assertEqual(out["rows"], [])
        self.assertEqual(len(out["skipped"]), 1)

    def test_every_range_is_ordered_after_the_write(self):
        self.sales([{"brand": "Acme", "channel": "c", "method": "views_x_share_x_price",
                     "inputs": {"views": 100000, "price": 20,
                                "share": {"low": 0.001, "mid": 0.002, "high": 0.004}},
                     "snapshot_date": "2025-12-01"}])
        for r in self.csv("sales.csv"):
            self.assertLessEqual(float(r["low"]), float(r["mid"]))
            self.assertLessEqual(float(r["mid"]), float(r["high"]))


class Tests(Base):
    def verdict(self, **data):
        base = {"day0": "2025-11-28", "today": "2025-12-20"}
        base.update(data)
        self.write("tests.json", base)
        return jrun("tests", "--input", self.path("tests.json"))

    def full(self, **over):
        data = {
            "demand": {"peak_multiple": 4.0, "baseline_multiple_last_year": 2.0},
            "reach": {"per_dollar": {"collabs": 80, "paid": 20}},
            "sales": {"holiday_units": 1200, "normal_units": 800},
            "payback": {"sales": {"low": 150000, "mid": 200000, "high": 250000},
                        "spend": {"low": 20000, "mid": 30000, "high": 40000}},
            "price": {"discount_depth": 0.1, "list_price_held": True, "new_models_full_price": True},
            "retention": {"real_units": 900, "dupe_units": 100},
        }
        data.update(over)
        return data

    def test_a_clear_win_is_worked(self):
        out = self.verdict(**self.full())
        self.assertEqual(out["verdict"], "worked")

    def test_before_day_zero_plus_14_it_is_too_early(self):
        out = self.verdict(today="2025-12-05", **self.full())
        self.assertEqual(out["verdict"], "too early to call")
        self.assertEqual(out["final_on"], "2025-12-12")

    def test_volume_alone_never_decides(self):
        d = self.full()
        d["sales"] = {}
        out = self.verdict(**d)
        self.assertEqual(out["verdict"], "can't tell yet")

    def test_flat_sales_is_a_failure(self):
        d = self.full()
        d["sales"] = {"holiday_units": 800, "normal_units": 800}
        out = self.verdict(**d)
        self.assertEqual(out["verdict"], "didn't work")

    def test_spend_that_clearly_did_not_pay_back_fails(self):
        d = self.full()
        d["payback"] = {"sales": {"low": 1000, "mid": 2000, "high": 3000},
                        "spend": {"low": 20000, "mid": 30000, "high": 40000}}
        out = self.verdict(**d)
        self.assertEqual(out["verdict"], "didn't work")

    def test_a_mixed_picture_is_mixed(self):
        d = self.full()
        d["demand"] = {"peak_multiple": 1.5, "baseline_multiple_last_year": 2.0}
        d["price"] = {"discount_depth": 0.30, "list_price_held": True, "new_models_full_price": False}
        d["retention"] = {"real_units": 300, "dupe_units": 700}
        out = self.verdict(**d)
        self.assertEqual(out["verdict"], "mixed")
        grades = {t["test"]: t["grade"] for t in out["tests"]}
        self.assertEqual(grades["Demand rose"], "mixed")
        self.assertEqual(grades["Price held"], "mixed")
        self.assertEqual(grades["Demand was kept"], "fail")

    def test_a_sale_needs_three_other_passes(self):
        d = self.full()
        d["demand"] = {}          # can't tell
        d["reach"] = {"per_dollar": {"collabs": 80}}   # can't tell
        d["price"] = {"discount_depth": 0.5, "new_models_full_price": False}
        out = self.verdict(**d)
        self.assertEqual(out["verdict"], "mixed")


class Check(Base):
    def setUp(self):
        super().setUp()
        run("init", "--dir", self.d)
        self.add(date_start="2025-11-20", date_end="2025-11-26")
        jrun("ledger", "count", "--dir", self.d, "--day0", "2025-11-28",
             "--out", self.path("volume_weekly.csv"))
        jrun("spend", "--dir", self.d, "--day0", "2025-11-28",
             "--out", self.path("spend_weekly.csv"))
        self.write("sales.json", {"channels": [
            {"brand": "Acme", "channel": "tiktok_shop", "method": "units_x_price",
             "inputs": {"units": 10, "price": 50}, "snapshot_date": "2025-12-01"}]})
        jrun("sales", "--input", self.path("sales.json"), "--out", self.path("sales_channels.csv"))
        self.write("tests.json", {"day0": "2025-11-28", "today": "2025-12-20",
                                  "sales": {"holiday_units": 1200, "normal_units": 800},
                                  "payback": {"sales": {"low": 150000, "mid": 200000, "high": 250000},
                                              "spend": {"low": 20000, "mid": 30000, "high": 40000}}})
        jrun("tests", "--input", self.path("tests.json"),
             "--out", self.path("tests_result.json"))
        self.report("""<!doctype html><html><body>
<h1 id="hero">Black Friday 2025 marketing teardown: Acme</h1>
<section id="part-1"><p>Every dollar is an estimate with its range. Not pulled is not zero.</p></section>
<section id="part-2"><p>Sales</p></section>
<p id="verdict">Mixed</p><img src="images/a.jpg" alt="an ad">
</body></html>""")

    def report(self, html):
        with open(self.path("report.html"), "w", encoding="utf-8") as f:
            f.write(html)

    def check(self, *extra, ok=True):
        return run("check", "--dir", self.d, *extra, ok=ok)

    def test_a_clean_report_passes(self):
        p = self.check("--brand", "Acme")
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertIn("PASS", p.stdout)

    def test_a_remote_image_fails(self):
        self.report('<h1 id="hero">Acme</h1><p id="verdict">estimate</p>'
                    '<section id="part-1"></section><section id="part-2"></section>'
                    '<img src="https://cdn.example.com/a.jpg" alt="a">')
        p = self.check(ok=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("remote image", p.stdout)

    def test_a_missing_section_fails(self):
        self.report('<h1 id="hero">Acme estimate</h1><p id="verdict">x</p>')
        p = self.check(ok=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("id='part-1'", p.stdout.replace('"', "'"))

    def test_counts_that_do_not_match_the_ledger_fail(self):
        rows = self.csv("volume_weekly.csv")
        rows[0]["units"] = "5"
        import csv
        with open(self.path("volume_weekly.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        p = self.check(ok=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("disagrees with the ledger", p.stdout)

    def test_an_undated_row_fails(self):
        rows = self.csv("spend_weekly.csv")
        rows[0]["pulled"] = ""
        import csv
        with open(self.path("spend_weekly.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        p = self.check(ok=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("no pulled/snapshot date", p.stdout)

    def test_an_out_of_order_range_fails(self):
        rows = self.csv("sales_channels.csv")
        rows[0]["high"] = "1"
        import csv
        with open(self.path("sales_channels.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        p = self.check(ok=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("range is out of order", p.stdout)

    def test_a_hand_typed_verdict_fails(self):
        self.write("tests_result.json", {"verdict": "worked"})
        p = self.check(ok=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("no date it becomes final", p.stdout)

    def test_a_report_that_hides_its_verdict_fails(self):
        self.report('<h1 id="hero">Acme estimate</h1><p id="verdict">Good campaign</p>'
                    '<section id="part-1"></section><section id="part-2"></section>')
        p = self.check(ok=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("does not state the graded verdict", p.stdout)

    def test_a_missing_file_fails(self):
        os.remove(self.path("sales_channels.csv"))
        p = self.check(ok=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("missing file", p.stdout)


class Docs(unittest.TestCase):
    """The guidance and the code must quote the same rates. A silent drift here
    is how a published range becomes wrong."""

    def setUp(self):
        self.estimates = os.path.join(HERE, "..", "skills", "reverse-any-brand",
                                      "references", "estimates.md")
        with open(self.estimates, encoding="utf-8") as f:
            self.text = f.read()
        out = subprocess.run([sys.executable, RAB, "window", "black friday", "--json"],
                             capture_output=True, text=True)
        self.rab = out.stdout

    def row(self, label):
        for line in self.text.splitlines():
            if line.startswith("|") and label in line:
                return line
        raise AssertionError("no row for %r in estimates.md" % label)

    def test_ad_day_rate_matches_the_code(self):
        self.assertEqual(sorted(int(x) for x in __import__("re").findall(r"\$([\d,]+)", self.row("An ad live for a day"))),
                         [50, 150, 400])

    def test_creator_tiers_match_the_code(self):
        self.assertIn("$150", self.row("under 10k followers"))
        self.assertIn("$20,000", self.row("1M+"))
        self.assertIn("100-500k", self.row("100-500k"))

    def test_affiliate_rates_match_the_code(self):
        row = self.row("Affiliate / TikTok Shop post")
        for token in ("0.2%", "0.06-0.36%", "12%", "5-20%"):
            self.assertIn(token, row, token)

    def test_owned_post_and_pr_rates_match_the_code(self):
        self.assertIn("$1,000", self.row("Making an owned post"))
        self.assertIn("$100,000", self.row("PR event"))

    def test_the_never_estimated_list_is_stated(self):
        for token in ("co-op", "email", "staff"):
            self.assertIn(token, self.text)

    def test_the_four_principles_stay_in_the_skill(self):
        with open(os.path.join(HERE, "..", "skills", "reverse-any-brand", "SKILL.md"),
                  encoding="utf-8") as f:
            skill = f.read()
        for token in ("Counts are pulled in full", "SEEN or INFERRED",
                      "come from the user", "Public evidence only"):
            self.assertIn(token, skill, token)

    def test_no_data_vendor_is_named_as_a_requirement(self):
        with open(os.path.join(HERE, "..", "skills", "reverse-any-brand", "SKILL.md"),
                  encoding="utf-8") as f:
            skill = f.read().lower()
        for vendor in ("ahrefs", "semrush", "spyfu", "similarweb", "apify", "treg"):
            self.assertNotIn(vendor, skill, vendor)


class Init(Base):
    def test_init_writes_the_working_set(self):
        out = jrun("init", "--dir", self.path("work"))
        for name in ("ledger.csv", "rates.json", "budget.json", "sales.json",
                     "tests.json", "README.txt"):
            self.assertTrue(os.path.exists(os.path.join(out["dir"], name)), name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
