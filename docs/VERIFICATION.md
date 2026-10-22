# Release verification — 0.1.0

The founding project snapshots and README checksums are recorded in
`analysis/upstream-lock.json`. Reproduction uses those local snapshots;
building does not refresh remote data or rerun RTLDI's analytical model.

## Automated checks

`python -m unittest discover -s tests -v` covers the package contract, missingness
and true zero, non-finite/boolean values, unknown references, duplicate observation
addresses, containment cycles, unsafe URLs/path traversal, dates, polygon closure,
CSV formula defense, projection coordinates, exact-year selection, all importers,
the actual event example, templates, input/export parity, build hashes, PDF
generation and outlines. The first release has 37 passing tests.

The checks also passed against the public GitHub Pages deployment. GitHub's
validation/build workflow passed on Python 3.10 and 3.12.

The optional `scripts/browser_qa.cjs` uses Playwright; it is not a runtime
dependency. Set `PLAYWRIGHT_MODULE` to the module path if not installed locally,
`BROWSER_EXECUTABLE` to a Chromium-family executable if needed, and `ATLAS_BASE`
to a server rooted at `docs/`. It checks 14 desktop/mobile/offline behaviors:
source-library search; shared selection; model/missing state; period/projection;
small-country access; day/night; settings dismissal; fullscreen entry;
offline reload; 390px no-horizontal-overflow; event precision/non-rollup;
no JavaScript errors; no external runtime requests; and entry links.

## Publication review

- The 34-page A4 PDF was rendered page-by-page with Poppler and inspected as a
  contact sheet, with detailed review of map, register and source pages.
- PDF geography is vector, not a screenshot. All four metrics select their own
  latest actual period and carry units and evidence state into their registers.
- Web and print rounding are declared; source JSON/CSV retain input precision.
- The build manifest records all top-level artifact hashes and original inputs.
- A distributable Python wheel is built, including schema, geometry, source
  catalog, web assets and mobile icons. Optional PDF dependencies are separate.
- No tokens, upstream active worktrees, personal records or private evidence
  are part of this repository. Source visibility is separate from participation.

## Limits to retain

This is the first reference release, not every feature of the founding atlases.
It does not include their terrain engine, live ship tracks, curated art-poster
pipeline, regression models, arbitrary raster ingestion or network layout.
The core validator is not a topology engine. The source catalog has 46 discovery
records, not 46 live connectors. The sole network-fetch command is a bounded
World Bank connector. Offline functionality requires an initial successful
HTTPS/localhost load; the PDF must be downloaded separately. Accessibility
checks cover keyboard-operable controls and register alternatives, not a claim
of a complete independent WCAG audit or tagged accessible PDF.
