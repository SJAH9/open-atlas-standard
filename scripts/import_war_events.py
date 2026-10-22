"""A sourced point/event interoperability example; not a new conflict analysis."""

from __future__ import annotations
import argparse
from pathlib import Path
from open_atlas.core import dump, load, read_json, sha
from open_atlas.adapters import war_maps


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--upstream", required=True)
    a = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    up = Path(a.upstream) / "war-maps-project"
    path = up / "data/processed/war_maps.json"
    raw = read_json(path)
    # A deliberately bounded date slice, not an attribution-based conflict claim.
    chosen = [e for e in raw["events"] if e["date_start"] == "2026-01-01"]
    if not chosen:
        raise ValueError("No source events for the declared date")
    imported = {o["source_record"]: o for o in war_maps(path)}
    entities = [{"id": "world", "name": "World", "kind": "global"}]
    features = []
    observations = []
    for e in chosen:
        eid = "event-" + e["id"]
        entities.append(
            {
                "id": eid,
                "name": e["country"] + " / " + e["place"] + " / " + e["id"],
                "kind": "event",
                "parent": "world",
                "notes": "Provisional candidate record; date/location precision and source reporting retained in raw_event. Not a deduplicated total.",
            }
        )
        observations.append(imported[e["id"]])
        if (
            e.get("map_point_eligible")
            and e.get("plot_longitude") is not None
            and e.get("plot_latitude") is not None
        ):
            features.append(
                {
                    "type": "Feature",
                    "id": eid,
                    "properties": {
                        "entity": eid,
                        "name": e["place"],
                        "precision": e.get("location_precision"),
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [e["plot_longitude"], e["plot_latitude"]],
                    },
                }
            )
    # Context geography has no event metric; it is explicitly not measured.
    world = read_json(root / "open_atlas/resources/world.geojson")
    for f in world["features"]:
        eid = f["properties"]["entity"]
        entities.append(
            {
                "id": eid,
                "name": f["properties"]["name"],
                "kind": "country",
                "parent": "world",
            }
        )
    # Draw context first, then event points; polygons must not cover the evidence.
    features = world["features"] + features
    sources = read_json(root / "catalog/sources.json")["sources"]
    used = {o["source"] for o in observations} | {"natural-earth-110m-geometry"}
    project = {
        "standard_version": "0.1.0",
        "id": "candidate-event-register",
        "title": "Events, Not Totals",
        "owner": "Sid J.A. Hubbard",
        "description": "A bounded January 1, 2026 slice of provisional UCDP candidate records, preserved from War Maps. Select an event to inspect the source and uncertainty; estimates are never summed.",
        "license": "MIT original software and documentation; upstream data terms remain separate.",
        "geometry_source": "natural-earth-110m-geometry",
        "publication_url": "https://sjah9.github.io/open-atlas-standard/events/",
        "scope": "Only candidate records whose source start date is 2026-01-01. Points appear only where War Maps declares map_point_eligible; not all events have precise locations.",
        "method": "Individual best estimates are copied unchanged. Country polygons are context, not a country fatality map. Source record_class and fatality_rollup_eligible are retained, not overridden.",
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
        "extensions": {
            "snapshot_sha256": sha(path),
            "selected_event_count": len(chosen),
            "mapped_event_count": len(features) - len(world["features"]),
        },
    }
    values = {
        "entities": entities,
        "observations": observations,
        "metrics": [
            {
                "id": "reported-deaths",
                "title": "Individual provisional candidate estimate",
                "unit": "reported deaths / source record",
                "description": "Not a distinct incident count or an additive total. Low/high bounds, source reports, date precision, code status and rollup eligibility remain in each raw_event.",
                "domain": [0, 100],
                "aggregation": "none",
            }
        ],
        "sources": [s for s in sources if s["id"] in used],
        "relations": [],
        "geometry": {"type": "FeatureCollection", "features": features},
    }
    out = root / "examples/war-events"
    dump(out / "atlas.json", project)
    for n, v in values.items():
        dump(out / project["files"][n], v)
    load(out)
    print(
        "Validated event example:",
        len(chosen),
        "records;",
        project["extensions"]["mapped_event_count"],
        "eligible points",
    )


if __name__ == "__main__":
    main()
