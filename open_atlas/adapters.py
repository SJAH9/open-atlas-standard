"""Explicit import boundaries. Importing never silently fetches fresh data."""

from __future__ import annotations
import csv, io, json, hashlib, math
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from .core import AtlasError, read_json, sha


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def number(value):
    if isinstance(value, bool):
        raise AtlasError("Boolean is not a measured number")
    if value is None or str(value).strip() in ["", "NA", "N/A", "null", "None"]:
        return None
    n = float(value)
    if not math.isfinite(n):
        raise AtlasError("Non-finite input value")
    return n


def observation(
    eid,
    metric,
    period,
    value,
    source,
    version,
    record,
    *,
    status="observed",
    method=None,
    reason=None,
    digest=None,
    retrieved=None,
):
    out = {
        "id": f"{eid}.{metric}.{period}",
        "entity": eid,
        "metric": metric,
        "period": str(period),
        "value": value,
        "status": "missing" if value is None else status,
        "source": source,
        "source_version": version,
        "retrieved_at": retrieved or timestamp(),
        "source_record": str(record),
    }
    if value is None:
        out["missing_reason"] = (
            reason or "No observation in the selected source snapshot"
        )
    if method:
        out["method"] = method
    if digest:
        out["snapshot_sha256"] = digest
    return out


def rtldi(path):
    """Preserve the published model, including its own missingness choices."""
    path = Path(path)
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig"))))
    result = []
    digest = sha(path)
    now = timestamp()
    for row in rows:
        eid = row["iso3"]
        period = str(row.get("g0_year") or "2026")
        for field, metric in [
            ("r", "rtlp"),
            ("total_deficit_usd", "capital-exclusions"),
        ]:
            value = number(row.get(field))
            o = observation(
                eid,
                metric,
                period,
                value,
                "rtldi-published",
                "2026 snapshot",
                eid + ":" + field,
                status="modeled",
                method="Copied from the published RTLDI output; no regression, lever thresholds, missing-value rules or capital-exclusion model recomputed.",
                digest=digest,
                retrieved=now,
            )
            o["notes"] = (
                f"Institutional observation year: {row.get('vdem_year','not supplied')}; GDP baseline year: {row.get('g0_year','not supplied')}. "
                + row.get("data_notes", "")
            )
            result.append(o)
    return result


def world_bank(
    path,
    indicator="SP.POP.TOTL",
    metric="population",
    years=None,
    allowed=None,
    source="world-bank-wdi-total-population",
):
    path = Path(path)
    raw = read_json(path)
    if not isinstance(raw, list) or len(raw) != 2 or not isinstance(raw[1], list):
        raise AtlasError("Expected a World Bank API metadata/rows response")
    out = []
    digest = sha(path)
    now = timestamp()
    seen = set()
    for row in raw[1]:
        eid = row.get("countryiso3code")
        year = str(row.get("date", ""))
        value = number(row.get("value"))
        if (
            row.get("indicator", {}).get("id") != indicator
            or not eid
            or years
            and year not in set(map(str, years))
            or allowed is not None
            and eid not in allowed
        ):
            continue
        key = (eid, year)
        if key in seen:
            raise AtlasError("Duplicate World Bank observation: " + str(key))
        seen.add(key)
        out.append(
            observation(
                eid,
                metric,
                year,
                value,
                source,
                "WDI updated " + str(raw[0].get("lastupdated", "unspecified")),
                eid + ":" + indicator + ":" + year,
                digest=digest,
                retrieved=now,
            )
        )
    return out


def life_support(path):
    """Read observations, not candidate-source availability or imagined scores."""
    path = Path(path)
    out = []
    digest = sha(path)
    now = timestamp()
    for row in csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig"))):
        status = {
            "official": "observed",
            "reviewed": "observed",
            "modeled": "modeled",
            "estimated": "estimated",
            "imputed": "derived",
            "community-submitted": "claim",
        }.get(row["provenance_status"])
        if not status:
            raise AtlasError("Unknown life-support provenance state")
        o = observation(
            row["region_id"],
            row["domain"] + "." + row["indicator_id"],
            row["year"],
            number(row["value"]),
            row["source_id"],
            row["source_version"],
            row["indicator_id"],
            status=status,
            method="Source contract normalization bounds retained; no composite calculated by this importer.",
            digest=digest,
            retrieved=now,
        )
        o["notes"] = row["notes"]
        o["normalization"] = {
            k: row[k] for k in ["direction", "normalization_min", "normalization_max"]
        }
        o["upstream_provenance_status"] = row["provenance_status"]
        out.append(o)
    return out


def war_maps(path):
    """Retain individual candidate events; never sum overlapping death estimates."""
    path = Path(path)
    raw = read_json(path)
    events = raw.get("current_events", raw.get("events", []))
    out = []
    digest = sha(path)
    now = timestamp()
    for i, event in enumerate(events):
        eid = "event-" + str(event.get("id", i))
        period = str(event.get("date_start") or event.get("date") or "")[:10]
        if len(period) != 10:
            raise AtlasError("An event needs a retained source date; no invented year")
        value = number(
            event.get("fatalities", {}).get(
                "best", event.get("best", event.get("deaths_best"))
            )
        )
        o = observation(
            eid,
            "reported-deaths",
            period,
            value,
            event.get("source_id", "ucdp-candidate-ged-2026-08"),
            "UCDP candidate snapshot",
            event.get("id", i),
            status="estimated",
            method="Preserved individual provisional candidate estimate. Not a deduplicated incident-only total; no country aggregation.",
            digest=digest,
            retrieved=now,
        )
        o["notes"] = (
            "Location precision: "
            + str(event.get("location_precision", "not supplied"))
            + "; code status: "
            + str(event.get("code_status", "not supplied"))
        )
        o["raw_event"] = event
        out.append(o)
    return out


def generic_csv(path, mapping, *, source, version, metric):
    required = ["entity", "period", "value"]
    if any(k not in mapping for k in required):
        raise AtlasError("CSV mapping must declare entity, period and value columns")
    path = Path(path)
    out = []
    digest = sha(path)
    now = timestamp()
    for i, row in enumerate(
        csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig"))), 2
    ):
        if any(mapping[k] not in row for k in required):
            raise AtlasError("Mapped CSV field missing")
        out.append(
            observation(
                row[mapping["entity"]],
                metric,
                row[mapping["period"]],
                number(row[mapping["value"]]),
                source,
                version,
                f"CSV row {i}",
                digest=digest,
                retrieved=now,
            )
        )
    return out


def fetch_wdi(indicator, countries, year, out):
    """A deliberately narrow live adapter. Explicit command, bounded response."""
    import re

    if (
        not re.fullmatch(r"[A-Z0-9.]+", indicator)
        or not re.fullmatch(r"[A-Z]{3}(;[A-Z]{3})*", countries)
        or not re.fullmatch(r"\d{4}(:\d{4})?", year)
    ):
        raise AtlasError("Invalid World Bank selection")
    url = f"https://api.worldbank.org/v2/country/{countries}/indicator/{indicator}?date={year}&format=json&per_page=20000"
    with urlopen(
        Request(url, headers={"User-Agent": "OpenAtlasReference/0.1"}), timeout=60
    ) as r:
        raw = r.read(16_000_001)
        if len(raw) > 16_000_000:
            raise AtlasError("Response exceeds the adapter limit")
    value = json.loads(raw)
    if (
        not isinstance(value, list)
        or len(value) != 2
        or not isinstance(value[0], dict)
        or not isinstance(value[1], list)
    ):
        raise AtlasError("Unexpected World Bank response")
    if int(value[0].get("pages", 1)) != 1:
        raise AtlasError(
            "Response is paginated; narrow the selection rather than truncating data"
        )
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_bytes(raw)
    return {
        "url": url,
        "sha256": sha(out),
        "retrieved_at": timestamp(),
        "rows": len(value[1]),
    }
