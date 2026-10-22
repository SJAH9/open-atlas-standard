# Three founding atlases: code, maps, and publication analysis

This audit uses new working clones, not the author's active development trees.
Exact commits and README digests are in [upstream-lock.json](upstream-lock.json).
The original projects remain independent; the reference kit is not a migration
or a replacement for their analytical work.

## War Maps Project

Examined commit: `976d92a510c3c73f9de76c5997c0c1c89d188ef4`.
Release documentation: `docs/RELEASE_0_12_0.txt`.

War Maps is an event, state, network, and publication system. Its substantive
data boundary distinguishes established conflict series, provisional candidate
events, sourced claims, model projections, missingness, and uncertainty. Events
retain source identities, date/location precision, code status, fatality ranges,
and map-point eligibility. Candidate records can mix incidents with aggregate
coverage, so adding their fatality estimates is not a valid death total.

The project supports world and regional maps, country/state profiles, conflict
networks, event timelines, 3D/isometric/terrain products, and specialized layers.
These are distinct views of different units, not interchangeable choropleths.
The examined offline build generated 813 conflict records, 2,816 conflict-year
records, and 13,659 candidate event rows; these are record counts, not findings
about the number of distinct incidents or deaths.

Print is an editorial product rather than a browser screenshot. Its vector
print/publication pipeline builds curated collections, notes, QR links, and
source-bearing selected artwork. The 0.12 release describes two 29-page
collections in 18×24-inch and Letter formats. The reusable lessons are explicit
selection, stable input artifacts, layout profiles, and source-bearing print.
The new kit does not pretend to reproduce its terrain or all of its specialized
posters in a generic country map.

Primary inspected entry points:
[README](https://github.com/SJAH9/war-maps-project/blob/976d92a510c3c73f9de76c5997c0c1c89d188ef4/README.md),
`data/SOURCES.json`, `docs/SOURCES.md`, `docs/GAS_MAP.md`,
`src/build_atlas.py`, `src/generate_print_atlas.py`, and
`src/generate_publications.py`.

## 2026 RTLDI Atlas of UN Member States

Examined commit: `c338deb69543056459ff5a783e33e4cef182d955`.
Latest examined release: `v2026.8.8`.

The RTLDI Atlas is an analytical publication: nine protection levers and a
bounded capital-exclusion model organized across 193 UN member states and
22 regions. Its value is not merely a comparative map. The current README
reports approximately $19.29 trillion in annual capital exclusions under its
declared model. This is a model output, not a number computed by Open Atlas.
The reference preserves each published CSV value, institutional year, GDP
baseline year, and model state rather than inventing a substitute calculation.

One canonical analytical preparation pipeline feeds HTML, structured outputs,
and the 290-page atlas. Country pages, evidence crosswalks, small-country
locators, QR links, and PDF outlines bridge detailed analysis and navigation.
The code also addresses geometry pitfalls such as metropolitan France and
countries smaller than a low-resolution world map can show reliably.

The latest release's Eurozone supplement uses actual World Bank EUR GDP data;
it is not a USD total relabeled as euros. The new reference does not combine
that EUR supplement with its USD model values. Earlier theory/specification
files describe model development and must not silently override release data.

Primary inspected entry points:
[README](https://github.com/SJAH9/rtldi-atlas/blob/c338deb69543056459ff5a783e33e4cef182d955/README.md),
`docs/releases/v2026.8.8.md`, `src/atlas_evidence.py`,
`src/map_geometry.py`, `src/generate_html_atlas.py`,
`docs/RTLDI_SPEC.md`, and `outputs/atlas/rtl_di_atlas_un_members_2026.csv`.

## Global Life-Support Atlas

Examined public-source commit: `8adbbd06b902e6b0da0bf93ee1f0d9c7e5b0b39d`.
The source repository was made public at the author's request during this work.
Public source visibility does **not** activate public submissions or declare
the project's launch complete.

This is a contract-first atlas across water, food, heat, soil, energy,
transport, health, ecology, and institutions. It keeps normalization bounds,
direction, provenance state, source version, and retrieval time with the data.
Its central safeguard is substantive: candidate source availability cannot
become a life-support score. A composite requires accepted evidence in all
nine domains. Its observation register is currently empty, so the new
reference's life-support view is explicitly unmeasured.

The project already produces a static geographic web product and method/data
contracts. No print generator was found in the examined implementation; print
is an added general capability in this reference, not attributed retrospectively
to the source project. Its own normalization and small positive flooring rule
belong to that model. The kit's independent `geometric_mean` helper retains
genuine zero; it is not presented as a reproduction of the GLSA model.

Primary inspected entry points:
[README](https://github.com/SJAH9/global-life-support-atlas/blob/8adbbd06b902e6b0da0bf93ee1f0d9c7e5b0b39d/README.md),
`docs/METHOD.md`, `docs/LAUNCH.md`, `project.json`,
`data/SOURCES.json`, `data/observations.csv`, `src/build.py`,
`src/generate_web.py`, and `tests/test_build.py`.

## Reusable architecture

| Concern | Source lesson | Reference implementation |
| --- | --- | --- |
| Canonical analysis | RTLDI's shared preparation pipeline | One validated package feeds every output |
| Evidence states | War Maps' candidates/claims/estimates | Per-observation status, source, method, version |
| Incomplete systems | GLSA's nine-domain requirement | Null plus reason; no invented composite |
| Geometry | Different resolutions, exactness, small states | Replaceable GeoJSON; register independent of polygons |
| Relationships | Conflict/membership and nested systems | Sourced typed edges; containment must be acyclic |
| Print | Curated vector products and source notes | Vector PDF, register, outlines, source notes, web QR |
| Reproduction | Frozen inputs and named releases | Input/output hashes, input package, versioned source library |
| Open participation | Separate source visibility from evidence acceptance | No submission endpoint or implied public review launch |

The catalog contains 46 records. These are source capabilities, not 46 working
API integrations. Automated adapters exist only where documented; other sources
remain manual, downloadable, or link-only. New organizations can begin with an
empty but valid template instead of copying somebody else's findings.
