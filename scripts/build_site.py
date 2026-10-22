"""Publish the standard's entry point and searchable, source-bearing library."""

from pathlib import Path
import html, shutil
from open_atlas.core import read_json, dump

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"
H = html.escape


def page(title, body):
    return (
        """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Open Atlas Standard: source-bearing atlases, web and print, for geographic and globally relevant research."><title>"""
        + H(title)
        + """</title><link rel="stylesheet" href="site.css"><link rel="icon" href="demo/icon.svg"></head><body><header><a class="brand" href="./"><img src="demo/icon.svg" alt="" width="32" height="32">OPEN ATLAS</a><nav aria-label="Project"><a href="demo/">Reference</a><a href="library.html">Sources</a><a href="https://github.com/SJAH9/open-atlas-standard">Repository ↗</a></nav></header><main>"""
        + body
        + """</main><footer><span>Sid J.A. Hubbard · Proposed standard 0.1.0 · MIT original software &amp; documentation</span><a href="https://github.com/SJAH9/open-atlas-standard/blob/main/THIRD_PARTY_NOTICES.md">Data rights</a></footer></body></html>"""
    )


def main():
    OUT.mkdir(exist_ok=True)
    body = """<section class="hero"><p class="kicker">A PORTABLE RESEARCH PUBLICATION</p><h1>Your subject.<br>Your evidence.<br><em>An open atlas.</em></h1><p class="lede">Make geographic and globally relevant knowledge navigable. One source-bearing package becomes a web atlas, a vector-print publication, and reusable data—without a map account, paid platform, or proprietary backend.</p><div class="actions"><a class="primary" href="demo/">Explore the reference atlas →</a><a href="https://github.com/SJAH9/open-atlas-standard/generate">Start your atlas ↗</a><a href="demo/atlas.pdf">Print edition ↓</a></div></section>
<section class="split"><div><p class="kicker">THE CONTRACT</p><h2>A map is a view.<br>The evidence is the atlas.</h2><p>Places and systems. Dated observations. Explicit units and model states. Source versions, relationships, and replaceable geometry. Nothing turns an unknown into zero or an estimate into a measurement.</p><a href="https://github.com/SJAH9/open-atlas-standard/blob/main/standard/OPEN_ATLAS_STANDARD.md">Read the proposed standard →</a></div><div class="package"><span>atlas.json</span><ul><li>entities &amp; nested places</li><li>metrics &amp; observation periods</li><li>observations &amp; evidence states</li><li>sources &amp; rights</li><li>relationships &amp; geometry</li></ul><strong>Web · PDF · CSV · GeoJSON · integrity manifest</strong></div></section>
<section><p class="kicker">WORKING PUBLICATIONS</p><div class="cards"><article><span class="number">01</span><h2>An Atlas of Evidence</h2><p>World Bank population records, published RTLDI capital-exclusion models, and an explicitly unmeasured life-support field. Not blended into a single score.</p><a href="demo/">Country register &amp; maps →</a></article><article><span class="number">02</span><h2>Events, Not Totals</h2><p>A January 1, 2026 slice of provisional UCDP candidate records from War Maps. Individual source estimates and eligible points, not a summed death toll.</p><a href="events/">Event register &amp; map →</a></article><article><span class="number">46</span><h2>A source library</h2><p>Geography, institutions, living conditions, conflict, energy, ecology and more. Access modes and rights stay visible; not every source is a live API.</p><a href="library.html">Browse the source library →</a></article></div></section>
<section class="split foundations"><div><p class="kicker">BUILT FROM WORK THAT EXISTS</p><h2>Three atlases.<br>One reusable foundation.</h2><p>The War Maps Project contributes event/network and curated print practices. The RTLDI Atlas contributes a canonical analytical pipeline across UN member states. The Global Life-Support Atlas contributes strict evidence and completeness contracts.</p><a href="https://github.com/SJAH9/open-atlas-standard/blob/main/analysis/FOUNDING_PROJECTS.md">Read the project analysis →</a></div><div><h3>For organizations and individuals</h3><p>Both templates begin with an honest empty register. Define your purpose, source rights, measures, and editorial process. Import evidence and publish a static, offline-capable atlas.</p><pre><code>pip install '.[print]'
open-atlas init ../my-atlas
open-atlas validate ../my-atlas
open-atlas build ../my-atlas \\
  --output ../published --pdf</code></pre><a href="https://github.com/SJAH9/open-atlas-standard#five-minute-start">Build instructions →</a></div></section>
<p class="notice">An author-proposed open standard by Sid J.A. Hubbard. No external standards endorsement is implied. Independent of the unrelated OpenAtlas humanities database. The reference examples preserve upstream research; they do not replace the founding atlases.</p>"""
    (OUT / "index.html").write_text(
        page("Open Atlas — Your evidence, web and print", body), encoding="utf-8"
    )
    catalog = read_json(ROOT / "catalog/sources.json")
    dump(OUT / "catalog.json", catalog)
    cards = []
    for s in catalog["sources"]:
        projects = ", ".join(p["id"] for p in s["projects"])
        cards.append(
            '<article data-search="'
            + H(
                (
                    s["title"]
                    + " "
                    + s["publisher"]
                    + " "
                    + s["id"]
                    + " "
                    + s.get("usage_note", "")
                    + " "
                    + projects
                ).lower(),
                quote=True,
            )
            + '"><p class="kicker">'
            + H(s["access"] + " / " + s["status"])
            + "</p><h2>"
            + H(s["title"])
            + "</h2><p>"
            + H(s["publisher"])
            + "</p><p>"
            + H(s.get("usage_note", ""))
            + '</p><p class="small"><b>Rights:</b> '
            + H(s["license"])
            + '</p><p class="small"><b>Capability:</b> '
            + H(s["adapter"])
            + " · "
            + H(s["download_policy"])
            + '</p><p class="small">'
            + H(projects)
            + '</p><a href="'
            + H(s["url"], quote=True)
            + '" target="_blank" rel="noopener">Source ↗</a></article>'
        )
    body = (
        '<section class="hero compact"><p class="kicker">46 SOURCE RECORDS / THREE FOUNDING PROJECTS</p><h1>Follow the source.</h1><p class="lede">Discover data for an atlas of your subject. Automated, downloadable, manual, and reference-only sources are distinguished. Public visibility is not a redistribution license.</p><label for="query">Find a source, domain, publisher or project</label><input id="query" type="search" placeholder="Water, energy, institutions, World Bank…"><p id="count" role="status">46 sources</p><a href="catalog.json">Download the full catalog JSON ↓</a></section><section class="cards library">'
        + "".join(cards)
        + '</section><script src="library.js" defer></script>'
    )
    (OUT / "library.html").write_text(
        page("Source library — Open Atlas", body), encoding="utf-8"
    )
    (OUT / "schema").mkdir(exist_ok=True)
    shutil.copy2(
        ROOT / "open_atlas/schemas/bundle.schema.json", OUT / "schema/bundle-0.1.json"
    )
    (OUT / ".nojekyll").touch()
    print("Built entry point, source library and published schema")


if __name__ == "__main__":
    main()
