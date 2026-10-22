# Data adapters and source library

All importers read local snapshots and write observation JSON. The project
owner must define matching entities, metrics, units, and source records and
then validate the complete package. The importer is not an inference engine.

| Adapter | Input | Preserved meaning / boundary |
| --- | --- | --- |
| `rtldi` | Published RTLDI country CSV | Protection index and USD annual capital exclusions copied as modeled outputs; GDP/institutional years retained in notes; no model recalculation |
| `world-bank` | Two-element WDI API JSON response | Exact indicator, country IDs and years; nulls retained; duplicate addresses rejected; explicit ISO allowlist excludes aggregate regions |
| `war-maps` | Built War Maps JSON | Individual candidate estimates, full upstream event record and precision; no event/country death totals |
| `life-support` | GLSA observations CSV | Evidence status, domain/indicator, source/version, normalization bounds; empty input stays empty; no composite invented |
| `csv` | UTF-8 CSV plus mapping | Explicit entity/period/value columns; numeric values and missingness; named source and snapshot |

The importer records the snapshot SHA-256 and import timestamp. Inherited
source dates/versions remain distinct from the time the kit read the snapshot.
GLSA community-submitted observations remain claims, not accepted measurements.
An imported War Maps record is not automatically point-map eligible: the
example builder requires the upstream `map_point_eligible` flag and plot
coordinates before producing a point.

## Commands

```sh
open-atlas sources --search health
open-atlas sources --json
open-atlas import world-bank snapshot.json --indicator SP.POP.TOTL --metric population --countries FRA,USA --years 2025 --output observations.json
open-atlas import rtldi rtl_di_atlas_un_members_2026.csv --output rtldi.json
open-atlas import war-maps war_maps.json --output events.json
open-atlas import life-support observations.csv --output life-support.json
```

For CSV, make a mapping file such as
`{"entity":"iso3","period":"year","value":"water_access_pct"}`:

```sh
open-atlas import csv water.csv --mapping mapping.json --metric water-access --source your-source --source-version '2026-10 snapshot' --output water.json
```

The explicit network connector is:

```sh
open-atlas fetch-wdi --indicator SP.POP.TOTL --countries 'FRA;USA' --year 2025 --output population.json
```

It uses the World Bank API, limits response size, rejects unhandled pagination,
and writes a retrieval receipt. Builds and displays do not fetch new evidence.
Source APIs can change; a failed retrieval must be reported, not replaced by
zeros or guessed rows. The catalog's other `adapter` entries denote source
families/capabilities; they do not imply a built connector. Keep raw snapshots
outside public publication when redistribution is not permitted.

## Rebuild the founding examples

Clone the three repositories named in `analysis/upstream-lock.json` into a
directory using their repository names. Check out the recorded commits, then:

```sh
python scripts/import_foundations.py --upstream /path/to/clones
open-atlas validate examples/reference
open-atlas build examples/reference --output docs/demo --pdf
```

The optional event example requires running `python -m src.build_atlas` in the
fresh War Maps clone first; no network refresh is necessary for its tracked
snapshot. Then run `python scripts/import_war_events.py --upstream /path/to/clones`.
The standard does not require those projects to remain frozen forever; update
the lock, record changes, and review outputs when adopting new source releases.
