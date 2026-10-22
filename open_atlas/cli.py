from __future__ import annotations
import argparse, json, re, shutil, sys
from pathlib import Path
from . import __version__
from .core import ROOT, AtlasError, dump, load, read_json
from .render import build
from . import adapters


def initialize(path, title, owner, kind):
    path = Path(path)
    if path.exists() and any(path.iterdir()):
        raise AtlasError("Refusing to overwrite a non-empty project directory")
    path.mkdir(parents=True, exist_ok=True)
    geo = read_json(ROOT / "resources/world.geojson")
    entities = [{"id": "world", "name": "World", "kind": "global"}]
    seen = {"world"}
    for f in geo["features"]:
        eid = f["properties"]["entity"]
        if eid not in seen:
            entities.append(
                {
                    "id": eid,
                    "name": f["properties"]["name"],
                    "kind": "country",
                    "parent": "world",
                }
            )
            seen.add(eid)
    catalog = read_json(ROOT / "resources/sources.json")
    source = next(
        s for s in catalog["sources"] if s["id"] == "natural-earth-110m-geometry"
    )
    project = {
        "standard_version": "0.1.0",
        "id": re.sub("[^a-z0-9]+", "-", title.lower()).strip("-") or "atlas",
        "title": title,
        "description": "An open atlas in development. No findings have been entered yet.",
        "owner": owner,
        "license": "Specify the license for your original work; upstream data rights remain separate.",
        "geometry_source": source["id"],
        "scope": "Replace with your geography, audience and temporal boundary.",
        "method": "Define each indicator and source before importing observations. Missingness is not a score.",
        "extensions": {
            "governance": {
                "kind": kind,
                "review": (
                    "Named editorial reviewer and correction log"
                    if kind == "organization"
                    else "Maintainer review with dated corrections"
                ),
                "privacy": "Do not include personal or confidential observations in this public package.",
            }
        },
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
    dump(path / "atlas.json", project)
    for name, value in [
        ("entities", entities),
        ("sources", [source]),
        ("observations", []),
        ("relations", []),
        ("geometry", geo),
        (
            "metrics",
            [
                {
                    "id": "measure",
                    "title": "Your first measure",
                    "unit": "Declare native unit",
                    "description": "Define what is measured, the source population, time interval and whether this is observed, estimated, modeled or derived.",
                    "domain": [0, 100],
                    "aggregation": "none",
                    "direction": "neutral",
                }
            ],
        ),
    ]:
        dump(path / project["files"][name], value)
    (path / "START-HERE.txt").write_text(
        "1. Edit atlas.json with your name, license, purpose and scope.\n2. Define the metric and source rights in data/.\n3. Import observations with explicit units, years and provenance.\n4. Run open-atlas validate .\n5. Run open-atlas build . --output ../published --pdf\nDo not publish example labels as completed research. Blank data are intentional.\n"
    )
    return project


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Open Atlas Standard reference toolkit"
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init")
    p.add_argument("directory")
    p.add_argument("--title", default="My Open Atlas")
    p.add_argument("--owner", default="Your name or organization")
    p.add_argument(
        "--kind", choices=["individual", "organization"], default="individual"
    )
    p = sub.add_parser("validate")
    p.add_argument("directory")
    p = sub.add_parser("build")
    p.add_argument("directory")
    p.add_argument("--output", required=True)
    p.add_argument("--pdf", action="store_true")
    p = sub.add_parser("sources")
    p.add_argument("--search", default="")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("import")
    p.add_argument(
        "adapter", choices=["csv", "world-bank", "rtldi", "life-support", "war-maps"]
    )
    p.add_argument("input")
    p.add_argument("--output", required=True)
    p.add_argument("--metric", default="population")
    p.add_argument("--source", default="world-bank-wdi-total-population")
    p.add_argument("--source-version", default="Declared source snapshot")
    p.add_argument(
        "--mapping", help="JSON file mapping entity/period/value to CSV columns"
    )
    p.add_argument("--years", help="Comma-separated actual observation years")
    p.add_argument(
        "--countries",
        help="Comma-separated explicit ISO3 allowlist, excluding regional aggregates",
    )
    p.add_argument(
        "--indicator",
        default="SP.POP.TOTL",
        help="Exact World Bank indicator ID for a JSON import",
    )
    p = sub.add_parser("fetch-wdi")
    p.add_argument("--indicator", required=True)
    p.add_argument("--countries", required=True, help="Semicolon-separated ISO3 codes")
    p.add_argument("--year", required=True)
    p.add_argument("--output", required=True)
    a = parser.parse_args(argv)
    try:
        if a.command == "init":
            initialize(a.directory, a.title, a.owner, a.kind)
            print("Created editable atlas:", a.directory)
        elif a.command == "validate":
            b = load(a.directory)
            print(
                f"Valid: {len(b['entities'])} entities, {len(b['observations'])} observations, {len(b['geometry']['features'])} features"
            )
        elif a.command == "build":
            m = build(a.directory, a.output, a.pdf)
            print("Built", len(m["outputs"]), "verified artifacts in", a.output)
        elif a.command == "sources":
            found = [
                s
                for s in read_json(ROOT / "resources/sources.json")["sources"]
                if a.search.lower() in json.dumps(s).lower()
            ]
            print(
                json.dumps(found, indent=2)
                if a.json
                else "\n".join(
                    f"{s['id']:<43} {s['adapter']:<14} {s['title']}" for s in found
                )
            )
        elif a.command == "import":
            if a.adapter == "csv":
                if not a.mapping:
                    raise AtlasError("CSV import requires --mapping")
                data = adapters.generic_csv(
                    a.input,
                    read_json(a.mapping),
                    source=a.source,
                    version=a.source_version,
                    metric=a.metric,
                )
            elif a.adapter == "world-bank":
                data = adapters.world_bank(
                    a.input,
                    indicator=a.indicator,
                    metric=a.metric,
                    years=a.years.split(",") if a.years else None,
                    allowed=set(a.countries.split(",")) if a.countries else None,
                    source=a.source,
                )
            else:
                data = getattr(adapters, a.adapter.replace("-", "_"))(a.input)
            dump(a.output, data)
            print(
                "Imported",
                len(data),
                "observations; now define matching entities, metrics and sources and run validate.",
            )
        elif a.command == "fetch-wdi":
            receipt = adapters.fetch_wdi(a.indicator, a.countries, a.year, a.output)
            dump(str(a.output) + ".receipt.json", receipt)
            print(json.dumps(receipt, indent=2))
    except (AtlasError, ValueError, OSError, KeyError) as e:
        print("Open Atlas:", e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
