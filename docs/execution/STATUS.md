# Execution status

- G0: passed (private environment baseline retained outside this public repository)
- G1: passed
- G2: in progress (source-snapshot sub-gate verified; isolated databases and deterministic fixtures pending)
- G3: in progress (first capability-contract checkpoint verified; full matrix,
  write state machine, and real Odoo validation pending)
- G4: in progress (reviewed initial generation baseline retained; six focused
  refinement rounds and generation validation pending)
- G5-G10: not started
- Release readiness: not ready

Current gate: G2. G2 cannot pass until its isolated-database and deterministic-fixture requirements are verified.

G3/G4 work is proceeding in parallel because its source and contract work is
independent of database creation. Neither later gate can pass before its own
requirements and the earlier gate dependencies are verified.

No existing Odoo database, service, V2/V3 installation, Odoo source tree, or legacy harness is a V4 write target.
