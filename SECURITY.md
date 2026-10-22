# Security and privacy

The reference is a static public publication, not an access-control system.
Everything inside a published package can be downloaded. Do not include private
observations, personal identifiers, credentials, or commercially restricted data.
There is no account system, server upload endpoint, or payment layer.

Source URLs are restricted to HTTP(S), package file paths must remain within
the input directory, rendered labels are escaped, and CSV formula-leading text
is neutralized. These controls are not a sandbox for untrusted Python code.
Do not execute a third party's scripts without review. GeoJSON topology and
malicious oversized inputs require producer review beyond the core validator.

Report security concerns privately via the maintainer's GitHub contact channels
before posting a sensitive proof of concept. No formal response SLA is claimed.
The offline cache is origin/scope-bound and caches only declared local files;
it is not encryption or a backup for data that should never have been public.
