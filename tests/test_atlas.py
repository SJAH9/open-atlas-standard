from __future__ import annotations
import copy, csv, json, math, tempfile, unittest
from pathlib import Path
from open_atlas.core import (
    AtlasError,
    dump,
    load,
    read_json,
    validate,
    select,
    geometric_mean,
    csv_export,
    sha,
)
from open_atlas.cli import initialize, main
from open_atlas import adapters
from open_atlas.render import build, color, MISSING, project, svg_map

ROOT = Path(__file__).resolve().parents[1]


class AtlasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = load(ROOT / "examples/reference")

    def setUp(self):
        self.b = copy.deepcopy(self.reference)

    def bad(self, phrase):
        self.assertTrue(any(phrase in e for e in validate(self.b)), validate(self.b))

    def test_reference(self):
        self.assertFalse(validate(self.b))
        self.assertEqual(len(self.b["observations"]), 977)

    def test_templates(self):
        for name in ["individual", "organization"]:
            self.assertEqual(load(ROOT / "templates" / name)["observations"], [])

    def test_zero_is_not_missing(self):
        self.b["observations"][0]["value"] = 0
        self.assertFalse(validate(self.b))
        self.assertNotEqual(color(0, [0, 1]), MISSING)

    def test_null_needs_reason(self):
        self.b["observations"][0]["value"] = None
        self.bad("Null requires")

    def test_missing_cannot_be_numeric(self):
        self.b["observations"][0]["status"] = "missing"
        self.bad("Missing observations")

    def test_boolean(self):
        self.b["observations"][0]["value"] = True
        self.assertTrue(validate(self.b))

    def test_nonfinite(self):
        self.b["observations"][0]["value"] = float("inf")
        self.bad("finite numeric")

    def test_nonfinite_json(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "invalid.json"
            p.write_text('{"value": NaN}')
            with self.assertRaises(AtlasError):
                read_json(p)

    def test_duplicate_address(self):
        o = copy.deepcopy(self.b["observations"][0])
        o["id"] = "different"
        self.b["observations"].append(o)
        self.bad("Duplicate observation address")

    def test_unknown_source(self):
        self.b["observations"][0]["source"] = "unknown"
        self.bad("Unknown observation source")

    def test_unknown_entity(self):
        self.b["observations"][0]["entity"] = "unknown"
        self.bad("Unknown observation entity")

    def test_unknown_metric(self):
        self.b["observations"][0]["metric"] = "unknown"
        self.bad("Unknown observation metric")

    def test_model_needs_method(self):
        o = next(o for o in self.b["observations"] if o["status"] == "modeled")
        o.pop("method")
        self.bad("require a method")

    def test_entity_cycle(self):
        self.b["entities"][0]["parent"] = self.b["entities"][1]["id"]
        self.b["entities"][1]["parent"] = self.b["entities"][0]["id"]
        self.bad("Cyclic")

    def test_coordinates(self):
        self.b["geometry"]["features"][0]["geometry"] = {
            "type": "Point",
            "coordinates": [999, 10],
        }
        self.bad("Invalid WGS84")

    def test_open_ring(self):
        self.b["geometry"]["features"][0]["geometry"] = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1]]],
        }
        self.bad("ring must be closed")

    def test_unsafe_url(self):
        self.b["sources"][0]["url"] = "javascript:alert(1)"
        self.assertTrue(validate(self.b))

    def test_no_source_credentials(self):
        self.b["sources"][0]["url"] = "https://secret:pass@example.com/"
        self.bad("Unsafe source URL")

    def test_invalid_date(self):
        self.b["observations"][0]["period"] = "2026-02-30"
        self.bad("Invalid observation date")

    def test_exact_period_only(self):
        self.assertEqual(select(self.b, "population", "1900"), {})

    def test_geometry_independent_register(self):
        self.assertGreater(len(self.b["entities"]), len(self.b["geometry"]["features"]))

    def test_complete_domain_helper(self):
        self.assertIsNone(geometric_mean([1, None]))
        self.assertEqual(geometric_mean([1, 0]), 0)
        self.assertAlmostEqual(geometric_mean([0.5, 0.5]), 0.5)
        with self.assertRaises(AtlasError):
            geometric_mean([2])

    def test_projection(self):
        self.assertEqual(project([0, 0]), (500, 250))
        self.assertAlmostEqual(project([0, 90], "equal-area")[1], 0)
        self.assertAlmostEqual(project([0, -90], "equal-area")[1], 2000 / math.pi)

    def test_path_escape(self):
        from open_atlas.core import local

        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(AtlasError):
                local(Path(d), "../secret")
            with self.assertRaises(AtlasError):
                local(Path(d), "/etc/passwd")

    def test_csv_formula(self):
        self.b["observations"][0]["source_record"] = "=1+1"
        self.b["observations"][0]["value"] = -2
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "o.csv"
            csv_export(self.b, p)
            r = list(csv.DictReader(p.read_text().splitlines()))[0]
            self.assertEqual(r["source_record"], "'=1+1")
            self.assertEqual(r["value"], "-2")

    def test_svg_escapes(self):
        self.b["entities"][1]["name"] = "<script>alert(1)</script>"
        s = svg_map(self.b, self.b["metrics"][0], "2025")
        self.assertNotIn("<script>", s)

    def test_boolean_adapter(self):
        with self.assertRaises(AtlasError):
            adapters.number(True)

    def test_wdi_filter(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "wdi.json"
            rows = [
                {
                    "countryiso3code": c,
                    "date": "2025",
                    "value": v,
                    "indicator": {"id": "X"},
                }
                for c, v in [("FRA", 0), ("WLD", 100), ("USA", None)]
            ]
            dump(p, [{"lastupdated": "2026-01-01"}, rows])
            out = adapters.world_bank(p, indicator="X", allowed={"FRA", "USA"})
            self.assertEqual(len(out), 2)
            self.assertEqual(out[0]["value"], 0)
            self.assertEqual(out[1]["status"], "missing")
            rows.append(rows[0])
            dump(p, [{}, rows])
            with self.assertRaises(AtlasError):
                adapters.world_bank(p, indicator="X")

    def test_rtldi_preserves_published_value(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.csv"
            p.write_text(
                "iso3,r,g0_year,vdem_year,total_deficit_usd,data_notes\nABC,0,2026,2024,1234,original model\n"
            )
            o = adapters.rtldi(p)
            self.assertEqual([v["value"] for v in o], [0, 1234])
            self.assertEqual(o[1]["status"], "modeled")
            self.assertIn("2024", o[1]["notes"])

    def test_no_invented_life_support(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "l.csv"
            p.write_text("region_id,domain,indicator_id\n")
            self.assertEqual(adapters.life_support(p), [])

    def test_war_nested_fatalities(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "war.json"
            dump(
                p,
                {
                    "events": [
                        {
                            "id": "1",
                            "date_start": "2026-01-01",
                            "fatalities": {"best": 7},
                            "map_point_eligible": False,
                        }
                    ]
                },
            )
            o = adapters.war_maps(p)[0]
            self.assertEqual(o["value"], 7)
            self.assertFalse(o["raw_event"]["map_point_eligible"])
            self.assertIn("no country aggregation", o["method"])

    def test_actual_event_package(self):
        b = load(ROOT / "examples/war-events")
        self.assertGreater(len(b["observations"]), 0)
        self.assertEqual(b["metrics"][0]["aggregation"], "none")
        self.assertTrue(
            all(o["raw_event"]["date_start"] == "2026-01-01" for o in b["observations"])
        )
        for f in b["geometry"]["features"]:
            if f["geometry"]["type"] == "Point":
                self.assertTrue(
                    next(
                        o
                        for o in b["observations"]
                        if o["entity"] == f["properties"]["entity"]
                    )["raw_event"]["map_point_eligible"]
                )

    def test_init_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            initialize(d, "Test", "Owner", "individual")
            load(d)
            with self.assertRaises(AtlasError):
                initialize(d, "Test", "Owner", "individual")

    def test_build_integrity_and_parity(self):
        with tempfile.TemporaryDirectory() as d:
            result = build(ROOT / "examples/reference", d, False)
            out = read_json(Path(d) / "data.json")
            self.assertEqual(out["observations"], self.b["observations"])
            for name, digest in result["outputs"].items():
                self.assertEqual(sha(Path(d) / name), digest)
            self.assertEqual(
                load(Path(d) / "input")["observations"], self.b["observations"]
            )

    def test_build_cannot_overwrite_source(self):
        with self.assertRaises(AtlasError):
            build(ROOT / "examples/reference", ROOT / "examples/reference")

    def test_source_catalog(self):
        c = read_json(ROOT / "catalog/sources.json")["sources"]
        self.assertEqual(len(c), 46)
        self.assertEqual(len({s["id"] for s in c}), 46)
        self.assertTrue(any(s["access"] == "manual" for s in c))

    def test_pdf(self):
        from pypdf import PdfReader

        with tempfile.TemporaryDirectory() as d:
            build(ROOT / "examples/reference", d, True)
            r = PdfReader(Path(d) / "atlas.pdf")
            self.assertGreater(len(r.pages), 10)
            self.assertIn("An Atlas of Evidence", r.pages[0].extract_text())
            self.assertTrue(r.outline)


if __name__ == "__main__":
    unittest.main()
