# Open Atlas Standard & Reference Implementation

Build an atlas of your subject—not another locked mapping platform.

**Open Atlas Standard 0.1.0** is a proposed, openly licensed package contract
and working Python/static-web implementation by **Sid J.A. Hubbard**. A project
combines geographic or globally relevant content, dated observations, original
analysis, source evidence, and explicit relationships into a self-contained
research publication. The same validated package produces the interactive web
atlas, vector-print PDF, CSV, GeoJSON, and a reproducible build manifest.

- [Open the system](https://sjah9.github.io/open-atlas-standard/)
- [Explore the working reference atlas](https://sjah9.github.io/open-atlas-standard/demo/)
- [Explore the point/event reference](https://sjah9.github.io/open-atlas-standard/events/)
- [Read the standard](standard/OPEN_ATLAS_STANDARD.md)
- [Review the three founding projects](analysis/FOUNDING_PROJECTS.md)
- [Browse the 46-source library](catalog/sources.json)
- [Download the print reference](https://sjah9.github.io/open-atlas-standard/demo/atlas.pdf)

This is an author-proposed standard and reference release, not an ISO/OGC/W3C
endorsement or a claim that every atlas implements it. It is independent of
the existing [OpenAtlas humanities database](https://openatlas.eu/).

## Five-minute start

Python 3.10+; no API keys, map accounts, CDN, database, Node build, or paid hosting.

```sh
git clone https://github.com/SJAH9/open-atlas-standard.git
cd open-atlas-standard
python3 -m venv .venv
. .venv/bin/activate
python -m pip install '.[print]'
open-atlas validate examples/reference
open-atlas build examples/reference --output published --pdf
python -m http.server 8765 --directory published
```

Open `http://localhost:8765/`. A static HTTP server is required; do not open the
app with `file://`. All atlas data are local after building. The service worker
requires HTTPS or localhost and caches the app shell/data, not external source
websites. The print PDF remains a normal separately downloadable artifact.

Create your own:

```sh
open-atlas init ../my-atlas --title 'Our Open Atlas' --owner 'Your organization' --kind organization
open-atlas sources --search water
open-atlas validate ../my-atlas
open-atlas build ../my-atlas --output ../my-atlas-web --pdf
```

Use `--kind individual` for a sole-maintainer project. Both
[organization](templates/organization/) and [individual](templates/individual/)
templates are included. They intentionally contain **no invented findings**.
Replace their editorial instructions and declare your own source rights before
publishing. Small states without a bundled polygon remain available as records;
replace the geometry for local or higher-resolution work.

## Import your data

The toolkit includes explicit CSV, World Bank JSON, RTLDI published-output,
War Maps event, and Global Life-Support observation adapters. An importer writes
observations; it does not invent the matching metric definition, geographic
join, license, or analytical conclusion. Validate the complete package after
an import. [Adapter recipes](docs/ADAPTERS.md) document each boundary.

```sh
open-atlas import rtldi path/to/rtl_di_atlas_un_members_2026.csv --output rtldi-observations.json
open-atlas import life-support path/to/observations.csv --output life-support-observations.json
open-atlas import war-maps path/to/war_maps.json --output event-observations.json
open-atlas fetch-wdi --indicator SP.POP.TOTL --countries 'FRA;USA' --year 2025 --output population.json
open-atlas import world-bank population.json --countries FRA,USA --years 2025 --output population-observations.json
```

Live fetching is an explicit command, never a side effect of build or display.
The 46-source catalog wraps provenance and access rules from the founding
projects; it does **not** pretend that manual/restricted sources already have
working automated connectors or that their datasets can be freely mirrored.

## What the reference demonstrates

- Real World Bank population records retained from War Maps' frozen snapshot.
- Published RTLDI right-to-life protection and annual capital-exclusion model
  outputs, **without recalculating or replacing the project's model**.
- A life-support composite that remains explicitly **not measured** because
  the founding project's accepted observation table is empty.
- Searchable place register, source inspector, shared view links, day/night,
  single fullscreen control, installable offline-capable static shell,
  equirectangular and cylindrical equal-area projections, and vector print.

These quantities are not blended. Currency, source years, model states,
missingness, absent geometry, and source ownership remain visible. The examples
are interoperability demonstrations, not replacements for the three source
atlases or new research findings.

## Structure

```text
standard/                 Normative requirements and conformance checklist
open_atlas/               Loader, validator, adapters, web and vector-PDF builder
open_atlas/schemas/       JSON Schema 2020-12 plus semantic validation
catalog/                  46 source records; capabilities and rights
examples/reference/      Reproducible, source-bearing atlas package
examples/war-events/     Bounded provisional event/point interoperability example
templates/               Organization and individual starting packages
analysis/                Source-code/output audit, immutable upstream lock
docs/                    Published system/demo and user/developer guidance
tests/                   Positive/negative data, build and adapter tests
```

## Reproduce, inspect, extend

```sh
python -m unittest discover -s tests -v
python scripts/import_foundations.py --upstream /path/to/fresh/clones
open-atlas build examples/reference --output docs/demo --pdf
```

`analysis/upstream-lock.json` identifies the examined commits. The import script
requires the three named clones and does not fetch, edit them, change their
models, or collect private data. Builds record input/output SHA-256 checksums.
The standard's optional enclosure extension can express nested geography,
systems and sourced causal models without making one theory mandatory for
every atlas. Relationships retain their evidence state; a graph layout is not
an observed causal finding.

## License and contribution

Original code and documentation: [MIT](LICENSE). Source data and maps retain
their [separate terms and attributions](THIRD_PARTY_NOTICES.md). No linked book
is relicensed. See [governance](GOVERNANCE.md), [security](SECURITY.md), and
[contribution guidance](CONTRIBUTING.md). Corrections and replications are
welcome. No user login, payment gateway, telemetry, or third-party tracking is
part of this reference implementation.
