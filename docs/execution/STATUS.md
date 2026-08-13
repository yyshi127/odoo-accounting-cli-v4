# Execution status

- G0: passed (private environment baseline retained outside this public repository)
- G1: passed
- G2: in progress (source snapshot, two provenance-bound synthetic databases,
  and accounting fixture v1 passed; full payment, assets/depreciation,
  deferrals, inventory valuation, and report golden cases remain pending)
- G3: in progress (102-ID current baseline recorded; the V2/V3 semantic
  crosswalk identifies at least two additional required IDs, 52 existing
  contracts needing expansion, and nine product-boundary decisions;
  25 read implementations are live-verified, 77 capabilities remain
  disabled/planned, and 53 versioned JSON Schema documents are retained)
- G4: passed for official generation provenance and baseline review (initial
  generation, six focused refinement rounds, official test/validate, complete
  transcript, and independent adjudication recorded; generated code remains a
  non-authoritative adapter draft)
- G5: in progress (real dual-environment bridge and 25 read vertical slices
  verified; the registry remains a 102-ID baseline with 77 disabled/planned
  capabilities, and remaining reads and reports are pending)
- G6-G10: not started
- Release readiness: not ready

Current implementation work: G5 vertical slices, while the full G2 fixture
matrix and G3 specialized contracts/write state machine remain open in
parallel.

G4 completion does not make generated capabilities available. G2 database
provisioning and accounting fixture v1 are independently verified, but G2
remains open until the full fixture matrix is versioned and verified. G3
remains open until specialized contracts and the write state machine are
implemented; G5 remains open until all enabled reads and reports pass real
Odoo verification.

No pre-existing Odoo database, service, V2/V3 installation, Odoo source tree,
or legacy harness is a V4 write target.
