# Execution status

- G0: passed (private environment baseline retained outside this public repository)
- G1: passed
- G2: in progress (source snapshot and two provenance-bound synthetic database
  sub-gates passed; the full deterministic accounting fixture matrix is pending)
- G3: in progress (102-ID capability matrix frozen; five read implementations
  and specialized contracts verified; remaining specialized contracts and the
  write state machine are pending)
- G4: passed for official generation provenance and baseline review (initial
  generation, six focused refinement rounds, official test/validate, complete
  transcript, and independent adjudication recorded; generated code remains a
  non-authoritative adapter draft)
- G5: in progress (real dual-environment bridge and five read vertical slices
  verified; remaining reads and reports pending)
- G6-G10: not started
- Release readiness: not ready

Current implementation work: G5 vertical slices, while the full G2 fixture
matrix and G3 specialized contracts/write state machine remain open in
parallel.

G4 completion does not make generated capabilities available. G2 database
provisioning is independently verified, but G2 remains open until the full
fixture matrix is versioned and verified. G3 remains open until specialized
contracts and the write state machine are implemented; G5 remains open until
all enabled reads and reports pass real Odoo verification.

No pre-existing Odoo database, service, V2/V3 installation, Odoo source tree,
or legacy harness is a V4 write target.
