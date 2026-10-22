# Open Atlas Standard 0.1.0

Author: Sid J.A. Hubbard · Status: proposed standard / reference release

An open atlas is a portable, source-bearing research publication about places,
globally relevant entities, their conditions, and their relationships. Its
publication is not limited to a map or to one proprietary renderer. It can
produce a navigable web product, printable publication, and reusable data from
one declared body of evidence.

This document defines the 0.1 core contract. **MUST**, **MUST NOT**, **SHOULD**,
and **MAY** express requirements within this proposed standard, not external
certification. The reference software is not an OGC, ISO, or W3C certification.
It is unrelated to the existing OpenAtlas humanities database.

## 1. Package and identity

A conforming package MUST contain an `atlas.json` manifest with
`standard_version: "0.1.0"`, stable `id`, `title`, `description`, `owner`,
`license`, `geometry_source`, and `files`. The six file roles are `entities`,
`metrics`, `observations`, `sources`, `relations`, and `geometry`. Paths MUST
be relative and resolve inside the package, including when symlinks are used.
No executable input or remote fetch is needed to open a package.

The package MUST validate against the included JSON Schema and semantic
validator. Unknown extension fields MAY be included; consumers MUST NOT infer
that validating an extension's presence validates its scientific claims.
Identifiers MUST be stable within a release, not derived from translated labels.
Source snapshots, release versions, and correction notes SHOULD be retained.

## 2. Entities, scale, and geography

Each entity MUST have an ID, name, and kind. A country, locality, organization,
region, event, or globally relevant non-geographic entity is permissible.
An optional `parent` MUST reference an existing entity; containment MUST be
acyclic. Administrative containment is not evidence of a causal mechanism.

Geometry MUST be a GeoJSON FeatureCollection with stable feature IDs and
`properties.entity` references to the entity register. The core geographic
profile accepts Point, MultiPoint, LineString, MultiLineString, Polygon, and
MultiPolygon or null geometry. Coordinates MUST be WGS84 longitude then
latitude in decimal degrees; rings MUST be closed. Uncertainty, source
resolution, location precision, disputed boundaries, and schematic positions
SHOULD be disclosed. A point estimate MUST NOT silently become an exact site.

The reference validator checks bounds, finite positions, ring closure, and
references, but is **not a full topology or GeoJSON conformance engine**.
Input owners remain responsible for valid coordinate nesting, polygon topology,
antimeridian treatment, and appropriate boundary choices. GeometryCollections,
rasters, terrain, maritime tracks, and 3D scenes are extension territory in 0.1.
The register MUST retain entities without map geometry. A missing polygon is
not a missing country, zero value, or finding of nonexistence.

## 3. Metrics, units, and time

Each metric MUST define ID, title, unit, description, increasing two-number
color domain, and aggregation policy. Policy is `none`, `sum`, or
`weighted_mean`; the last MUST name a registered weight metric. These are
declarations: the reference viewer does **not** calculate aggregations.
A producer adding aggregation MUST document compatible units, populations,
periods, weights, overlap rules, and missingness treatment before computing it.

An observation address is `(entity, metric, period)`. It MUST be unique in
one release; revisions MUST be reconciled rather than silently duplicated.
The 0.1 period is a calendar year or ISO calendar date. Event intervals and
different source/model years MAY be carried as explicit extension fields or
notes, not silently collapsed into a falsely common measurement date.

The renderer MUST select an exact period. It MUST NOT silently interpolate,
carry forward values, join a different year, convert currencies, or replace a
published model. Shared links SHOULD encode the selected entity, metric,
period, and projection. Local files, rather than URLs, remain the canonical
package boundary.

## 4. Evidence and missingness

Every observation MUST contain a finite number or null, status, source ID,
source version, and timezone-bearing retrieval/import timestamp. `source_record`
and a snapshot digest SHOULD identify its upstream address. Statuses are:

| Status | Meaning in the package |
| --- | --- |
| observed | Reported observation from the named source, not a guarantee of accuracy |
| derived | Explicit transformation of inputs |
| modeled | Output of a declared model |
| estimated | Estimate, including provisional event estimates |
| inference | Analytical inference with declared method |
| claim | Attributed assertion not promoted to measurement |
| synthetic | Deliberately constructed demonstration data |
| missing | No usable value under the declared selection |

Null MUST use `missing` and include `missing_reason`. Zero MUST remain a real
numeric zero; booleans, NaN, and infinities MUST NOT be accepted as quantities.
Derived, modeled, estimated, and inferred values MUST include a method.
If `input_observations` is provided, each reference MUST exist. Status labels
are evidence metadata, not a hierarchy of importance or a substitute for review.

An atlas MUST NOT convert candidate source availability into accepted evidence,
sum overlapping incident/aggregate rows, or report an incomplete composite as a
complete measurement. Model-specific conventions MUST remain with that model.
For example, importing RTLDI published outputs does not apply a different
life-support project's normalization or missingness rules to them.

## 5. Sources and relationships

Each source MUST identify ID, title, publisher, HTTP(S) URL, rights/license,
access mode (`api`, `download`, `manual`, `link-only`), and role/status
(`used`, `candidate`, or `reference`; upstream verification is separately labeled).
URL credentials and active script schemes MUST NOT be accepted. Source terms,
raw snapshot digests, version, retrieval date, transformations, and limitations
SHOULD be accessible from the rendered record. Public visibility alone is not
a redistribution license. Publishers MUST review third-party terms.

The shared library is a discovery/capability catalog, not a promise of live
connectors for every source. Fetches MUST be explicit, bounded, and separate
from rendering. A reproducible build MUST NOT secretly refresh its evidence.

Relationships MUST name existing `from` and `to` entities, predicate, source,
and evidence status. A graph edge MAY describe conflict, membership, exchange,
containment, or a proposed mechanism. Its visual appearance MUST NOT promote
an inference into measured causality. The core viewer exposes relationships in
the inspector; a force-directed network renderer is not included in 0.1.

## 6. Web, print, and data publication

One validated package MUST drive the selected web and print values, units,
time periods, legend domains, and evidence labels. A PDF MAY choose a smaller
set of views if its selection is declared. This reference PDF prints the
latest **available period per metric**, not a secretly mixed-year global map.
The web interface also offers other recorded periods.

The reference PDF register rounds display to five significant digits; the web
display uses six. Canonical JSON/CSV retain input precision. A renderer MUST
declare display rounding and MUST NOT rewrite the underlying observations.

A full reference publication MUST include:

1. A self-contained web atlas with a place register, map, exact-period selection,
   record-level source inspector, methods, and shareable view URLs.
2. A printable PDF with vector geography, legends, evidence-state registers,
   source/rights notes, page navigation, and a link to its web companion.
3. Observations CSV, geometry GeoJSON, canonical JSON bundle, and original input
   package. CSV formula-leading text MUST be neutralized without changing
   numeric negatives; canonical JSON retains exact input strings.
4. A build manifest containing SHA-256 digests of source inputs and generated
   artifacts. This detects changes; it is not a cryptographic signature of
   research correctness or authorship.

## 7. Accessibility, privacy, and offline use

The map MUST have an accessible register alternative. Value/state text MUST
distinguish missingness from color alone. Keyboard-operable controls, visible
focus, responsive layouts, readable day/night modes, and source labels SHOULD
be provided. Tiny states and non-geographic entities MUST remain selectable.
Color is not an appropriate sole indicator of model/observation status.

The reference product uses no accounts, analytics, remote tiles, remote fonts,
or CDN scripts. It requires a static HTTP server; `file://` is not supported.
On HTTPS or localhost, its service worker caches only the local atlas shell
and declared data. It does not mirror source websites or guarantee offline
PDF availability; a PDF can be downloaded separately. Install behavior varies
by browser. Publication is the maintainer's responsibility: private or sensitive
data MUST NOT be included merely because the software can display them.

## 8. Optional enclosure extension

Projects MAY express nested systems using entity parents and sourced relations.
For an NCM analytical extension, the project SHOULD declare the focal departure,
containing system, contained systems, direction of exchange/causality, boundary,
scale address, and evidence state. These are project-defined analytical fields,
not an automated claim to have performed an NCM or established a mechanism.
The standard neither requires nor rewrites the originating research method.

## 9. Conformance and evolution

- **Core package:** sections 1–5; schema plus semantic validation passes.
- **Web publication:** core plus web/accessibility requirements in 6–7.
- **Print publication:** core plus declared PDF selection, registers, and sources.
- **Reference distribution:** core, web, print, data exports, and integrity manifest.

A release MUST state its supported profile and implementation limits. A
conformance statement is about this data contract, not the truth of a model.
Changes to required fields or meanings require a new standard version and
migration notes. New optional fields do not justify silently changing old data.

## Foundations

This contract was developed from the [three-project audit](../analysis/FOUNDING_PROJECTS.md).
Geographic serialization follows the WGS84 longitude/latitude convention of
[GeoJSON RFC 7946](https://www.rfc-editor.org/rfc/rfc7946).
Its separation of dataset, distributions, and provenance is informed by
[DCAT 3](https://www.w3.org/TR/vocab-dcat-3/); it does not claim to implement a
DCAT RDF exporter. The machine schema is [included here](../open_atlas/schemas/bundle.schema.json).
