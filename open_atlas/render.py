"""One canonical selection, projection and color scale for web and vector print."""

from __future__ import annotations
import html, json, math, re, shutil
from pathlib import Path
from .core import ROOT, AtlasError, csv_export, dump, load, read_json, select, sha

PALETTE = ["#e4e8d5", "#b9d3ba", "#75a8a4", "#357582", "#163f56"]
MISSING = "#d9d4c8"


def color(value, domain):
    if value is None:
        return MISSING
    t = max(0, min(1, (value - domain[0]) / (domain[1] - domain[0])))
    return PALETTE[min(4, int(t * 5))]


def project(point, projection="equirectangular", width=1000):
    lon, lat = point[:2]
    if projection == "equal-area":
        return (
            (lon + 180) / 360 * width,
            (1 - math.sin(math.radians(lat))) / 2 * width * 2 / math.pi,
        )
    return ((lon + 180) / 360 * width, (90 - lat) / 180 * width / 2)


def lines(geometry):
    if not geometry:
        return []
    k = geometry["type"]
    v = geometry["coordinates"]
    if k == "Polygon":
        return v
    if k == "MultiPolygon":
        return [r for p in v for r in p]
    if k == "LineString":
        return [v]
    if k == "MultiLineString":
        return v
    return []


def svg_map(bundle, metric, period, projection="equirectangular"):
    height = 1000 * 2 / math.pi if projection == "equal-area" else 500
    rows = select(bundle, metric["id"], period)
    entities = {e["id"]: e for e in bundle["entities"]}
    paths = []
    for f in bundle["geometry"]["features"]:
        g = f["geometry"]
        eid = f["properties"]["entity"]
        o = rows.get(eid)
        value = o["value"] if o else None
        name = entities[eid]["name"]
        label = f"{name}: {value if value is not None else 'not measured'} {metric['unit']if value is not None else ''}"
        fill = color(value, metric["domain"]) if value is not None else "url(#missing)"
        body = ""
        for ring in lines(g):
            pts = [project(p, projection) for p in ring]
            if pts:
                body += (
                    "M"
                    + "L".join(f"{x:.3f},{y:.3f}" for x, y in pts)
                    + ("Z" if g["type"] in ["Polygon", "MultiPolygon"] else "")
                )
        if body:
            shape = f'<path data-shape="{g["type"]}" d="{body}" fill="{fill if g["type"]in["Polygon","MultiPolygon"]else "none"}" fill-rule="evenodd" stroke="{fill if g["type"]in["LineString","MultiLineString"]else "#faf7ef"}" stroke-width=".8"/>'
        elif g and g["type"] in ["Point", "MultiPoint"]:
            pts = [g["coordinates"]] if g["type"] == "Point" else g["coordinates"]
            shape = "".join(
                f'<circle cx="{project(p,projection)[0]:.3f}" cy="{project(p,projection)[1]:.3f}" r="3" fill="{fill}" stroke="#234d5a"/>'
                for p in pts
            )
        else:
            continue
        paths.append(
            '<a href="#entity='
            + html.escape(eid, quote=True)
            + '" data-entity="'
            + html.escape(eid, quote=True)
            + '" aria-label="'
            + html.escape(label, quote=True)
            + '"><title>'
            + html.escape(label)
            + "</title>"
            + shape
            + "</a>"
        )
    grid = []
    for lon in range(-120, 181, 60):
        x, _ = project([lon, 0], projection)
        grid.append(f'<path d="M{x},0V{height}"/>')
    for lat in range(-60, 61, 30):
        _, y = project([0, lat], projection)
        grid.append(f'<path d="M0,{y}H1000"/>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 {height}" role="group" aria-label="{html.escape(metric["title"])} world map; tab through places or use the place selector"><defs><pattern id="missing" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="{MISSING}"/><path d="M-1,1L1,-1M0,6L6,0M5,7L7,5" stroke="#a19a8d" stroke-width=".6"/></pattern></defs><rect width="1000" height="{height}" fill="#edf1ed"/><g stroke="#c9d3ce" stroke-width=".5" fill="none">'
        + "".join(grid)
        + "</g>"
        + "".join(paths)
        + "</svg>"
    )


def default_selection(b, metric):
    periods = sorted(
        {o["period"] for o in b["observations"] if o["metric"] == metric["id"]}
    )
    return periods[-1] if periods else "not-measured"


def build(source, out, make_pdf=False):
    source = Path(source).resolve()
    out = Path(out).resolve()
    if source == out or source.is_relative_to(out):
        raise AtlasError("Output may not enclose the source package")
    b = load(source)
    out.mkdir(parents=True, exist_ok=True)
    m = b["metrics"][0]
    period = default_selection(b, m)
    for name in [
        "atlas.css",
        "atlas.js",
        "icon.svg",
        "icon-192.png",
        "icon-512.png",
        "worker.js",
        "manifest.webmanifest",
    ]:
        shutil.copy2(ROOT / "assets" / name, out / name)
    manifest = read_json(out / "manifest.webmanifest")
    manifest["name"] = b["project"]["title"]
    manifest["short_name"] = b["project"]["title"][:18]
    dump(out / "manifest.webmanifest", manifest)
    dump(out / "data.json", b)
    csv_export(b, out / "observations.csv")
    dump(out / "geometry.geojson", b["geometry"])
    for projection in ["equirectangular", "equal-area"]:
        (out / (projection + ".svg")).write_text(
            svg_map(b, m, period, projection), encoding="utf-8"
        )
    title = html.escape(b["project"]["title"])
    description = html.escape(b["project"]["description"])
    content = (
        (ROOT / "assets/atlas.html")
        .read_text()
        .replace("{{TITLE}}", title)
        .replace("{{DESCRIPTION}}", description)
        .replace("{{MAP}}", svg_map(b, m, period))
    )
    (out / "index.html").write_text(content, encoding="utf-8")
    # Exact input package accompanies each published build for offline re-use.
    dump(out / "input/atlas.json", b["project"])
    for path in b["project"]["files"].values():
        p = out / "input" / path
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / path, p)
    if make_pdf:
        print_atlas(b, out / "atlas.pdf")
    manifest = {
        "standard_version": "0.1.0",
        "input_integrity": b["integrity"],
        "outputs": {
            p.name: sha(p)
            for p in sorted(out.iterdir())
            if p.is_file() and p.name != "build-manifest.json"
        },
    }
    dump(out / "build-manifest.json", manifest)
    return manifest


def print_atlas(b, path):
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.colors import HexColor
    except ImportError as e:
        raise AtlasError('Install the print extra: pip install ".[print]"') from e
    from reportlab.pdfbase.pdfmetrics import stringWidth

    W, H = A4
    c = canvas.Canvas(str(path), pagesize=A4, invariant=1)
    c.setTitle(b["project"]["title"])
    c.setAuthor(b["project"]["owner"])
    c.setSubject("Open Atlas Standard 0.1 reference publication")
    page = 0

    def text(s, x, y, size=10, font="Helvetica", color="#263d43"):
        c.setFillColor(HexColor(color))
        c.setFont(font, size)
        c.drawString(
            x, y, str(s).replace("–", "-").replace("—", "-").replace("∞", "infinity")
        )

    def wrap(s, x, y, width=500, size=10, font="Helvetica", leading=15):
        words = str(s).replace("–", "-").replace("—", "-").split()
        row = ""
        for word in words:
            test = (row + " " + word).strip()
            if row and stringWidth(test, font, size) > width:
                text(row, x, y, size, font)
                y -= leading
                row = word
            else:
                row = test
        if row:
            text(row, x, y, size, font)
            y -= leading
        return y

    def new(title, kicker="OPEN ATLAS / REFERENCE EDITION"):
        nonlocal page
        if page:
            c.showPage()
        page += 1
        c.bookmarkPage("page-" + str(page))
        c.addOutlineEntry(title + " / " + str(page), "page-" + str(page), level=0)
        c.setFillColor(HexColor("#faf7ef"))
        c.rect(0, 0, W, H, stroke=0, fill=1)
        text(kicker, 44, H - 42, 8, "Helvetica-Bold")
        wrap(title, 44, H - 82, W - 88, 24, "Times-Bold", 28)
        c.setStrokeColor(HexColor("#c3c6b6"))
        c.line(44, 40, W - 44, 40)
        text(b["project"]["id"], 44, 25, 8)
        text(str(page), W - 55, 25, 8)

    def draw_map(m, period):
        rows = select(b, m["id"], period)
        x0, y0, w, h = 44, 420, W - 88, (W - 88) / 2
        c.setFillColor(HexColor("#edf1ed"))
        c.rect(x0, y0, w, h, fill=1, stroke=0)
        for f in b["geometry"]["features"]:
            o = rows.get(f["properties"]["entity"])
            v = o["value"] if o else None
            g = f["geometry"]
            c.setFillColor(HexColor(color(v, m["domain"])))
            c.setStrokeColor(HexColor("#ffffff"))
            c.setLineWidth(0.22)
            rings = lines(g)
            if rings:
                p = c.beginPath()
                for ring in rings:
                    for i, point in enumerate(ring):
                        x, y = project(point, width=w)
                        (p.moveTo if i == 0 else p.lineTo)(x0 + x, y0 + h - y)
                    if g["type"] in ["Polygon", "MultiPolygon"]:
                        p.close()
                c.drawPath(
                    p,
                    stroke=1,
                    fill=int(g["type"] in ["Polygon", "MultiPolygon"]),
                    fillMode=0,
                )
            elif g and g["type"] in ["Point", "MultiPoint"]:
                for point in (
                    [g["coordinates"]] if g["type"] == "Point" else g["coordinates"]
                ):
                    x, y = project(point, width=w)
                    c.circle(x0 + x, y0 + h - y, 2, stroke=1, fill=1)
            if v is None:
                # Missingness is additionally named in the register. Do not draw a zero.
                pass
        text(
            "Equirectangular / WGS84 longitude-latitude / source geometry retained",
            44,
            402,
            8,
        )
        for i, col in enumerate(PALETTE):
            c.setFillColor(HexColor(col))
            c.rect(44 + i * 55, 372, 55, 10, fill=1, stroke=0)
        text(str(m["domain"][0]), 44, 355, 8)
        text(str(m["domain"][1]), 280, 355, 8)
        c.setFillColor(HexColor(MISSING))
        c.rect(375, 372, 18, 10, fill=1, stroke=0)
        text("Not measured / no record", 400, 373, 8)

    new(b["project"]["title"])
    y = wrap(
        b["project"]["description"],
        44,
        H - 150,
        size=15,
        font="Times-Roman",
        leading=21,
    )
    y = wrap(b["project"].get("scope", ""), 44, y - 26)
    y = wrap(b["project"].get("method", ""), 44, y - 18)
    y = wrap(
        "Web, print, CSV and GeoJSON are built from the same validated input package. No forecast, source refresh or alternate model is silently substituted.",
        44,
        y - 25,
    )
    y = wrap("Project owner: " + b["project"]["owner"], 44, y - 25)
    y = wrap("Software/documentation license: " + b["project"]["license"], 44, y - 14)
    url = b["project"].get("publication_url", "")
    if url:
        text("WEB COMPANION", 44, 150, 9, "Helvetica-Bold")
        wrap(url, 44, 130, width=W - 90, size=9)
        c.linkURL(url, (44, 102, W - 44, 145), relative=0)
        try:
            from reportlab.graphics.barcode import qr
            from reportlab.graphics.shapes import Drawing
            from reportlab.graphics import renderPDF

            q = qr.QrCodeWidget(url)
            a, z, ww, hh = q.getBounds()
            size = 65
            drawing = Drawing(
                size, size, transform=[size / (ww - a), 0, 0, size / (hh - z), 0, 0]
            )
            drawing.add(q)
            renderPDF.draw(drawing, c, W - 118, 160)
        except ImportError:
            pass
    for m in b["metrics"]:
        period = default_selection(b, m)
        new(m["title"], m["unit"] + " / " + period)
        draw_map(m, period)
        y = wrap(m["description"], 44, 315)
        y = wrap(
            "Fixed linear color domain: "
            + str(m["domain"])
            + ". Missing cells are not zero; model estimates and measurements remain distinct.",
            44,
            y - 15,
        )
        wrap(
            "Map polygons may not cover every registered entity. The following register preserves those entities rather than omitting them.",
            44,
            y - 14,
        )
        rows = select(b, m["id"], period)
        entries = sorted(b["entities"], key=lambda e: e["name"])
        y = 0
        for i, e in enumerate(entries):
            if i % 32 == 0:
                new(m["title"] + " / register", period + " / " + m["unit"])
                y = H - 141
                text("PLACE", 44, y, 8, "Helvetica-Bold")
                text("VALUE (5 SIG. DIGITS)", 275, y, 8, "Helvetica-Bold")
                text("STATE", 392, y, 8, "Helvetica-Bold")
                y -= 21
            o = rows.get(e["id"])
            value = o["value"] if o else None
            value = f"{value:,.5g}" if value is not None else "Not measured"
            name = e["name"]
            font_size = min(9, 9 * 218 / max(218, stringWidth(name, "Helvetica", 9)))
            text(name, 44, y, font_size)
            text(value, 275, y, 9)
            text(o["status"] if o else "no record", 392, y, 8)
            y -= 19
    new("Sources, rights, and methods")
    y = H - 135
    for source in b["sources"]:
        if y < 190:
            new("Sources / continued")
            y = H - 135
        y = wrap(
            source["title"] + " - " + source["publisher"],
            44,
            y,
            size=11,
            font="Helvetica-Bold",
        )
        y = wrap(source["url"], 44, y, width=W - 88, size=8, leading=12)
        y = wrap("Rights: " + source["license"], 44, y - 3, size=9)
        y = wrap(source.get("usage_note", ""), 44, y - 2, size=9)
        y -= 16
    c.save()
