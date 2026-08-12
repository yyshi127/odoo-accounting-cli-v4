# Execution status

- G0: passed (private environment baseline retained outside this public repository)
- G1: passed
- G2: in progress (source-snapshot sub-gate verified; isolated databases and deterministic fixtures pending)
- G3: in progress (102-ID planned capability matrix frozen; write state
  machine, implementations, and real Odoo validation pending)
- G4: passed for official generation provenance and baseline review (initial
  generation, six focused refinement rounds, official test/validate, complete
  transcript, and independent adjudication recorded; generated code remains a
  non-authoritative adapter draft)
- G5-G10: not started
- Release readiness: not ready

Current gate: G2. G2 cannot pass until its isolated-database and deterministic-fixture requirements are verified.

G3/G4 source and contract work proceeded independently of database creation.
G4 completion does not make any generated capability available. G2 remains
open until the two synthetic databases and fixtures are verified, and G3
remains open until specialized contracts and the write state machine are
implemented.

No existing Odoo database, service, V2/V3 installation, Odoo source tree, or legacy harness is a V4 write target.
