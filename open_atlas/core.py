"""Canonical, offline package loading and semantic validation."""

from __future__ import annotations
import csv, hashlib, json, math, re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit
from jsonschema import Draft202012Validator

ROOT = Path(__file__).parent
KINDS = {
    "observed",
    "derived",
    "modeled",
    "estimated",
    "inference",
    "claim",
    "synthetic",
    "missing",
}


class AtlasError(ValueError):
    pass


def read_json(p):
    def bad(s):
        raise AtlasError("Non-finite JSON number: " + s)

    return json.loads(Path(p).read_text(encoding="utf-8"), parse_constant=bad)


def dump(p, value):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def local(root, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise AtlasError("Package paths must be relative")
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise AtlasError("Package path escapes its directory: " + name)
    return path


def load(root):
    root = Path(root).resolve()
    project = read_json(root / "atlas.json")
    files = project.get("files", {})
    bundle = {"project": project}
    for name in [
        "entities",
        "metrics",
        "observations",
        "sources",
        "relations",
        "geometry",
    ]:
        if name not in files:
            raise AtlasError("atlas.json must name " + name)
        bundle[name] = read_json(local(root, files[name]))
    errors = validate(bundle)
    if errors:
        raise AtlasError("\n".join(errors))
    bundle["integrity"] = {
        "atlas.json": sha(root / "atlas.json"),
        **{p: sha(local(root, p)) for p in files.values()},
    }
    return bundle


def validate(b):
    schema = read_json(ROOT / "schemas/bundle.schema.json")
    errors = [
        "/".join(map(str, e.absolute_path)) + ": " + e.message
        for e in Draft202012Validator(schema).iter_errors(b)
    ]
    if errors:
        return errors

    def issue(s):
        errors.append(s)

    def ids(rows, name):
        values = [r["id"] for r in rows]
        if len(set(values)) != len(values):
            issue("Duplicate " + name + " IDs")
        return {r["id"]: r for r in rows}

    entities = ids(b["entities"], "entity")
    metrics = ids(b["metrics"], "metric")
    sources = ids(b["sources"], "source")
    obs = ids(b["observations"], "observation")
    ids(b["relations"], "relation")
    for e in entities.values():
        if e.get("parent") not in [None, *entities]:
            issue("Unknown parent: " + e["id"])
        seen = {e["id"]}
        current = e
        while current.get("parent") in entities:
            pid = current["parent"]
            if pid in seen:
                issue("Cyclic entity containment: " + e["id"])
                break
            seen.add(pid)
            current = entities[pid]
    for source in sources.values():
        for field in ["url", "terms_url", "download_url"]:
            if source.get(field):
                url = urlsplit(source[field])
                if (
                    url.scheme not in ["http", "https"]
                    or not url.netloc
                    or url.username
                    or url.password
                ):
                    issue("Unsafe source URL: " + source["id"] + " " + field)
    for metric in metrics.values():
        if not all(math.isfinite(v) for v in metric["domain"]):
            issue("Non-finite metric domain: " + metric["id"])
        if metric["domain"][0] >= metric["domain"][1]:
            issue("Invalid color domain: " + metric["id"])
        if metric["aggregation"] == "weighted_mean" and not metric.get("weight_metric"):
            issue("Weighted mean requires an explicit weight metric: " + metric["id"])
        if metric.get("weight_metric") and metric["weight_metric"] not in metrics:
            issue("Unknown weight metric: " + metric["id"])
    keys = set()
    for o in obs.values():
        if o["entity"] not in entities:
            issue("Unknown observation entity: " + o["id"])
        if o["metric"] not in metrics:
            issue("Unknown observation metric: " + o["id"])
        if o["source"] not in sources:
            issue("Unknown observation source: " + o["id"])
        key = (o["entity"], o["metric"], o["period"])
        if key in keys:
            issue(
                "Duplicate observation address; reconcile revisions explicitly: "
                + str(key)
            )
        keys.add(key)
        try:
            if len(o["period"]) == 4:
                if not 1 <= int(o["period"]) <= 9999:
                    raise ValueError("Invalid year")
            else:
                date.fromisoformat(o["period"])
            datetime.fromisoformat(o["retrieved_at"].replace("Z", "+00:00"))
        except ValueError:
            issue("Invalid observation date: " + o["id"])
        if o["value"] is None:
            if o["status"] != "missing" or not o.get("missing_reason"):
                issue("Null requires missing status and reason: " + o["id"])
        elif o["status"] == "missing":
            issue("Missing observations cannot have numeric values: " + o["id"])
        elif isinstance(o["value"], bool) or not math.isfinite(o["value"]):
            issue("Value must be finite numeric, not boolean: " + o["id"])
        if o["status"] in [
            "derived",
            "modeled",
            "estimated",
            "inference",
        ] and not o.get("method"):
            issue("Transformed observations require a method: " + o["id"])
        for upstream in o.get("input_observations", []):
            if upstream not in obs:
                issue("Unknown input observation: " + o["id"] + " -> " + upstream)
    for relation in b["relations"]:
        if relation["from"] not in entities or relation["to"] not in entities:
            issue("Unknown relation endpoint: " + relation["id"])
        if relation["source"] not in sources:
            issue("Unknown relation source: " + relation["id"])
    features = b["geometry"]["features"]
    feature_ids = []

    def positions(value):
        if isinstance(value, list) and value and isinstance(value[0], (int, float)):
            yield value
        elif isinstance(value, list):
            for child in value:
                yield from positions(child)

    for f in features:
        p = f["properties"]
        eid = p.get("entity")
        feature_ids.append(f["id"])
        if eid not in entities:
            issue("Unknown geometry entity: " + str(eid))
        g = f["geometry"]
        if g is None:
            continue
        if g["type"] not in [
            "Point",
            "MultiPoint",
            "LineString",
            "MultiLineString",
            "Polygon",
            "MultiPolygon",
        ]:
            issue("Unsupported geometry type: " + g["type"])
            continue
        for point in positions(g["coordinates"]):
            if (
                len(point) < 2
                or not all(
                    isinstance(x, (int, float))
                    and not isinstance(x, bool)
                    and math.isfinite(x)
                    for x in point
                )
                or not (-180 <= point[0] <= 180 and -90 <= point[1] <= 90)
            ):
                issue("Invalid WGS84 longitude/latitude: " + str(f["id"]))
                break
        rings = (
            [g["coordinates"]]
            if g["type"] == "Polygon"
            else g["coordinates"] if g["type"] == "MultiPolygon" else []
        )
        for polygon in rings:
            for ring in polygon:
                if len(ring) < 4 or ring[0] != ring[-1]:
                    issue("Polygon ring must be closed: " + str(f["id"]))
    if len(feature_ids) != len(set(feature_ids)):
        issue("Duplicate geometry feature IDs")
    if b["project"]["geometry_source"] not in sources:
        issue("Unknown geometry source")
    if b["project"].get("publication_url"):
        url = urlsplit(b["project"]["publication_url"])
        if (
            url.scheme not in ["http", "https"]
            or not url.netloc
            or url.username
            or url.password
        ):
            issue("Unsafe project publication URL")
    return errors


def csv_export(bundle, path):
    fields = [
        "id",
        "entity",
        "metric",
        "period",
        "value",
        "status",
        "source",
        "source_version",
        "retrieved_at",
        "missing_reason",
        "method",
        "source_record",
    ]
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=fields, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        for o in bundle["observations"]:
            row = {k: o.get(k, "") for k in fields}
            # Spreadsheet formula defenses apply to text, never to real negative values.
            for k, v in row.items():
                if isinstance(v, str) and v.startswith(
                    ("=", "+", "-", "@", "\t", "\r")
                ):
                    row[k] = "'" + v
            writer.writerow(row)


def select(bundle, metric, period):
    return {
        o["entity"]: o
        for o in bundle["observations"]
        if o["metric"] == metric and o["period"] == period
    }


def geometric_mean(values):
    """Complete-domain profile: missing is not zero; genuine zero stays zero."""
    if not values or any(v is None for v in values):
        return None
    if any(
        not isinstance(v, (int, float))
        or isinstance(v, bool)
        or not math.isfinite(v)
        or not 0 <= v <= 1
        for v in values
    ):
        raise AtlasError("Normalized values must be finite in [0,1]")
    return (
        0.0 if 0 in values else math.exp(sum(math.log(v) for v in values) / len(values))
    )
