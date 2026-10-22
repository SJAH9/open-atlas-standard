"""Reproduce the public catalog and examples from three explicit local clones.

No keys, private paths, live downloads, regressions or inferred observations.
"""

from pathlib import Path
import argparse, csv, json, subprocess, sys, re

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from open_atlas.core import dump, read_json, sha
from open_atlas.adapters import rtldi, world_bank, life_support, observation, timestamp

ROOT = Path(__file__).resolve().parents[1]


def main(upstream):
    upstream = Path(upstream)
    war = upstream / "war-maps-project"
    rtl = upstream / "rtldi-atlas"
    life = upstream / "global-life-support-atlas"
    catalog = {}
    foundation = []
    for name in ["war-maps-project", "rtldi-atlas", "global-life-support-atlas"]:
        p = upstream / name
        foundation.append(
            {
                "repository": "https://github.com/SJAH9/" + name,
                "commit": subprocess.check_output(
                    ["git", "-C", str(p), "rev-parse", "HEAD"], text=True
                ).strip(),
                "readme_sha256": sha(p / "README.md"),
                "license": "MIT for project software; upstream data retain separate terms",
            }
        )
    for project, base in [
        ("war-maps-project", war),
        ("global-life-support-atlas", life),
    ]:
        for raw in read_json(base / "data/SOURCES.json")["sources"]:
            source = dict(raw)
            source["publisher"] = str(raw.get("publisher", "See source"))
            source["license"] = raw.get(
                "license", "UNSPECIFIED: review publisher terms before reuse"
            )
            source["access"] = "manual"
            source["status"] = (
                "candidate" if raw.get("status") == "candidate" else "used"
            )
            source["usage_note"] = str(
                raw.get(
                    "enclosure",
                    raw.get("domain", "Source terms and definitions must be reviewed."),
                )
            )
            if "verified" in source:
                source["upstream_verified"] = source.pop("verified")
            source["projects"] = [
                {"id": project, "role": source["status"], "path": "data/SOURCES.json"}
            ]
            source["adapter"] = "manual"
            source["download_policy"] = "manual-review"
            if source["id"].startswith("world-bank-wdi"):
                source["adapter"] = "world-bank"
                source["access"] = "api"
            if source["id"].startswith("ucdp-"):
                source["access"] = "download"
                source["adapter"] = "war-maps"
                source["download_url"] = source["url"]
            if source["id"] == "natural-earth-110m-geometry":
                source["adapter"] = "geojson"
                source["access"] = "download"
                source["download_policy"] = "redistributable"
                source["terms_url"] = (
                    "https://www.naturalearthdata.com/about/terms-of-use/"
                )
            if source["id"] in catalog:
                catalog[source["id"]]["projects"] += source["projects"]
            else:
                catalog[source["id"]] = source
    extra = [
        (
            "rtldi-published",
            "RTLDI Atlas published model outputs",
            "RTLDI Atlas Project",
            "https://github.com/SJAH9/rtldi-atlas",
            "MIT project outputs; underlying V-Dem and World Bank terms retained",
            "rtldi",
            "modeled national capital exclusions, not an observed transfer or a recalculated model",
        ),
        (
            "vdem-core-v15",
            "V-Dem v15 institutional source used by RTLDI",
            "V-Dem Institute",
            "https://github.com/vdeminstitute/vdemdata/releases/tag/V15",
            "CC BY-SA 4.0 as recorded in upstream project; review original distribution",
            "manual",
            "Distinct vintage from the War Maps v16 country-year fields",
        ),
        (
            "world-bank-gdp",
            "GDP per capita and local-currency baselines",
            "World Bank",
            "https://data.worldbank.org/indicator/NY.GDP.PCAP.CD",
            "CC BY 4.0; source-specific exceptions may apply",
            "world-bank",
            "Keep currency, valuation basis, matched population year and projection year separate",
        ),
        (
            "world-bank-basic-needs",
            "Undernourishment and poverty indicators",
            "World Bank",
            "https://data.worldbank.org/indicator/SN.ITK.DEFC.ZS",
            "CC BY 4.0; source-specific exceptions may apply",
            "world-bank",
            "SN.ITK.DEFC.ZS and SI.POV.DDAY retain their independent source years and definitions",
        ),
        (
            "life-support-project",
            "Global Life-Support Atlas observation contract",
            "Global Life-Support Atlas Project",
            "https://github.com/SJAH9/global-life-support-atlas",
            "MIT project materials; upstream dataset terms retained",
            "life-support",
            "Initial observation table is empty. Candidate sources are not accepted observations.",
        ),
        (
            "aaa-fuel",
            "State pump-price averages",
            "AAA",
            "https://gasprices.aaa.com/state-gas-price-averages/",
            "Publisher terms; no blanket redistribution right asserted",
            "manual",
            "Source-date, fuel-grade and sampling boundary must remain",
        ),
        (
            "eia-fuel",
            "Gasoline and diesel retail survey",
            "US Energy Information Administration",
            "https://www.eia.gov/petroleum/gasdiesel/",
            "Review EIA source conditions",
            "manual",
            "Weekly survey; distinct from AAA daily state means",
        ),
        (
            "ec-oil-bulletin",
            "Weekly Oil Bulletin",
            "European Commission",
            "https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en",
            "Review EU reuse terms",
            "manual",
            "Match workbook date, fuel, unit, and tax-inclusive/exclusive tables",
        ),
        (
            "japan-anre-fuel",
            "Japanese petroleum price statistics",
            "Agency for Natural Resources and Energy",
            "https://www.enecho.meti.go.jp/statistics/petroleum_and_lpgas/pl007/index.html",
            "Review publisher terms",
            "manual",
            "Retain prefecture-level sampling and original units",
        ),
        (
            "india-ppac-fuel",
            "Selected outlet fuel prices",
            "Petroleum Planning and Analysis Cell",
            "https://ppac.gov.in/all-imp-news?page=1",
            "Review publisher terms",
            "manual",
            "An outlet observation is not a national mean",
        ),
        (
            "taiwan-cpc-fuel",
            "Published CPC fuel schedule",
            "CPC Corporation",
            "https://vipmbr.cpc.com.tw/mbwebs/showhistoryprice_oil.aspx",
            "Review publisher terms",
            "manual",
            "Effective schedule date; original fuel grade retained",
        ),
        (
            "australia-accc-fuel",
            "Weekly fuel-price monitoring",
            "Australian Competition and Consumer Commission",
            "https://www.accc.gov.au/consumers/petrol-and-fuel",
            "Review ACCC report reuse terms",
            "manual",
            "Preserve report date, city/region and calculated-tax method",
        ),
        (
            "nz-mbie-fuel",
            "Weekly fuel-price monitoring",
            "New Zealand MBIE",
            "https://www.mbie.govt.nz/building-and-energy/energy-and-natural-resources/energy-statistics-and-modelling/energy-statistics/weekly-fuel-price-monitoring/price-for-fuel-response-support",
            "Review MBIE source terms",
            "manual",
            "Failed refreshes must retain the actual last-verified observation date",
        ),
        (
            "ecb-fx",
            "Euro foreign-exchange reference rates",
            "European Central Bank",
            "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml",
            "Review ECB reuse terms",
            "manual",
            "Dated conversion reference, not local purchasing power",
        ),
        (
            "taiwan-cbc-fx",
            "TWD/USD closing rate",
            "Central Bank of the Republic of China (Taiwan)",
            "https://www.cbc.gov.tw/tw/lp-645-1-1-40.html",
            "Review publisher terms",
            "manual",
            "Preserve currency direction and date",
        ),
        (
            "geonames",
            "Geographic names",
            "GeoNames",
            "https://download.geonames.org/export/dump/",
            "CC BY 4.0",
            "manual",
            "Unmatched locations stay unresolved rather than being guessed",
        ),
    ]
    for sid, title, pub, url, license, adapter, note in extra:
        project = (
            "rtldi-atlas"
            if sid
            in [
                "rtldi-published",
                "vdem-core-v15",
                "world-bank-gdp",
                "world-bank-basic-needs",
            ]
            else (
                "global-life-support-atlas"
                if sid == "life-support-project"
                else "war-maps-project"
            )
        )
        catalog[sid] = {
            "id": sid,
            "title": title,
            "publisher": pub,
            "url": url,
            "license": license,
            "access": "api" if adapter == "world-bank" else "manual",
            "status": "reference",
            "usage_note": note,
            "adapter": adapter,
            "download_policy": "manual-review",
            "projects": [
                {
                    "id": project,
                    "role": "reference",
                    "path": (
                        "src/atlas_evidence.py"
                        if project == "rtldi-atlas"
                        else (
                            "data/SOURCES.json"
                            if project == "global-life-support-atlas"
                            else "docs/GAS_MAP.md"
                        )
                    ),
                }
            ],
        }
    registry = {
        "standard_version": "0.1.0",
        "description": "Source adapters and attribution records, not a grant of upstream redistribution rights. Used/candidate status is retained per founding project.",
        "foundations": foundation,
        "sources": list(catalog.values()),
    }
    dump(ROOT / "catalog/sources.json", registry)
    dump(ROOT / "open_atlas/resources/sources.json", registry)
    dump(ROOT / "analysis/upstream-lock.json", foundation)
    geo = read_json(war / "data/raw/ne_110m_admin_0_countries.geojson")
    features = []
    entities = {}
    now = timestamp()
    for i, f in enumerate(geo["features"]):
        p = f["properties"]
        eid = p.get("ISO_A3")
        if not eid or eid == "-99":
            eid = p.get("ADM0_A3") or "geo-" + str(i)
        eid = str(eid)
        name = p.get("ADMIN", p.get("NAME", eid))
        entities[eid] = {
            "id": eid,
            "name": name,
            "kind": "country",
            "parent": "world",
            "identifiers": {"natural_earth": p.get("ADM0_A3"), "iso3": p.get("ISO_A3")},
            "notes": "Cartographic unit from Natural Earth; not a claim about sovereignty.",
        }
        features.append(
            {
                "type": "Feature",
                "id": "ne-" + str(i),
                "properties": {"entity": eid, "name": name},
                "geometry": f["geometry"],
            }
        )
    entities["world"] = {"id": "world", "name": "World", "kind": "global"}
    rtlpath = rtl / "outputs/atlas/rtl_di_atlas_un_members_2026.csv"
    rtlrows = list(csv.DictReader(rtlpath.open()))
    for row in rtlrows:
        eid = row["iso3"]
        entities.setdefault(
            eid,
            {
                "id": eid,
                "name": row["country"],
                "kind": "country",
                "parent": "world",
                "identifiers": {"iso3": eid},
                "notes": "No polygon in the bundled 1:110m geometry. The record remains available in the table.",
            },
        )
    geometry = {"type": "FeatureCollection", "features": features}
    dump(ROOT / "open_atlas/resources/world.geojson", geometry)
    # .geojson package data is explicitly included in pyproject.
    package = ROOT / "examples/reference"
    all_entities = list(entities.values())
    observations = rtldi(rtlpath)
    wbpath = war / "data/raw/world-bank-SP.POP.TOTL-1960-2025.json"
    observations += world_bank(
        wbpath, years=[2024, 2025], allowed={row["iso3"] for row in rtlrows}
    )
    for e in all_entities:
        if e["id"] != "world":
            observations.append(
                observation(
                    e["id"],
                    "life-support",
                    "2026",
                    None,
                    "life-support-project",
                    "development-0.1",
                    e["id"],
                    reason="The founding Life-Support Atlas contains no accepted observations; a complete nine-domain composite cannot be calculated.",
                    digest=sha(life / "data/observations.csv"),
                    retrieved=now,
                )
            )
    metrics = [
        {
            "id": "population",
            "title": "Population",
            "unit": "people",
            "description": "World Bank / UN total population. Select an actual observed year; absent records stay missing.",
            "domain": [0, 1_500_000_000],
            "aggregation": "none",
            "direction": "neutral",
        },
        {
            "id": "rtlp",
            "title": "Right-to-Life Protection",
            "unit": "index (0–1)",
            "description": "Published RTLDI nine-condition score. Model-vintage and baseline notes are attached to each record.",
            "domain": [0, 1],
            "aggregation": "none",
            "direction": "higher",
        },
        {
            "id": "capital-exclusions",
            "title": "Annual capital exclusions",
            "unit": "USD / year (model estimate)",
            "description": "Copied from the published RTLDI model; no equation or regression recalculated. The original source years and qualifications remain attached.",
            "domain": [0, 5_000_000_000_000],
            "aggregation": "none",
            "direction": "neutral",
        },
        {
            "id": "life-support",
            "title": "Life-support resilience",
            "unit": "composite (0–1)",
            "description": "No composite is available without accepted evidence in all nine domains. The initial founding project has no accepted observations.",
            "domain": [0, 1],
            "aggregation": "none",
            "direction": "higher",
        },
    ]
    sources = [
        catalog[sid]
        for sid in [
            "natural-earth-110m-geometry",
            "rtldi-published",
            "world-bank-wdi-total-population",
            "life-support-project",
        ]
    ]
    project = {
        "standard_version": "0.1.0",
        "id": "atlas-of-evidence",
        "title": "An Atlas of Evidence",
        "description": "One map is not one kind of knowledge. Explore population observations, published capital-exclusion models, and an explicitly unmeasured life-support field.",
        "owner": "Sid J.A. Hubbard · Open Atlas Standard",
        "license": "MIT for original project software and documentation; source-data rights remain with their publishers.",
        "scope": "193 UN-member RTLDI records plus Natural Earth cartographic units; the map is not the country register.",
        "method": "Three founding systems contribute reusable contracts, not interchangeable measurements. No upstream analytical model is recomputed.",
        "publication_url": "https://sjah9.github.io/open-atlas-standard/demo/",
        "geometry_source": "natural-earth-110m-geometry",
        "files": {
            n: "data/" + n + (".geojson" if n == "geometry" else ".json")
            for n in [
                "entities",
                "metrics",
                "observations",
                "sources",
                "relations",
                "geometry",
            ]
        },
    }
    dump(package / "atlas.json", project)
    for name, value in [
        ("entities", all_entities),
        ("metrics", metrics),
        ("observations", observations),
        ("sources", sources),
        ("relations", []),
        ("geometry", geometry),
    ]:
        dump(package / project["files"][name], value)
    # Validate the original empty life-support import; do not promote candidates.
    assert life_support(life / "data/observations.csv") == []
    print(
        json.dumps(
            {
                "catalog_sources": len(catalog),
                "entities": len(all_entities),
                "observations": len(observations),
                "geometry_features": len(features),
                "foundations": foundation,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--upstream", required=True)
    a = p.parse_args()
    main(a.upstream)
