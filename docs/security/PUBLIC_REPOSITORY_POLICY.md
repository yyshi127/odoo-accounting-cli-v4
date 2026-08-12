# Public repository policy

The repository must not contain credentials, authentication files, database dumps, real business data, raw environment logs, private absolute key paths, Odoo Enterprise/custom source, copied restricted-source snippets, private source snapshots, generated private evidence, runtime state, or installed releases.

Every push is gated by staged-tree path checks, secret and PII scanning, restricted-source exact-hash and long-snippet similarity checks, and license policy checks appropriate to the files being published. A private dependency installed on the target system is runtime-provided and is never vendored into this repository or its release artifacts.
