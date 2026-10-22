# Contributing

Use Python 3.10+ and install `pip install '.[print]'`. Run
`python -m unittest discover -s tests -v` and rebuild the reference before
submitting a change. New adapters need a source/version boundary, unit and
missingness tests, a license note, and explicit network behavior. No credentials
belong in packages, generated artifacts, tests, or source URLs.

Keep analytical results with their originating projects. New renderers should
consume the package rather than fork/recompute source models. A view must have
a register alternative, explicit units/time/evidence state, and source access.
Never fix missing data by making up a plausible value.

Use issues for proposed contract changes and examples. Include browser/device
details for layout faults and a minimal public fixture for data faults. The
software is MIT; all contributed data must include their own rights statement.
