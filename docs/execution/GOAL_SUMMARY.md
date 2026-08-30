# Public execution goal summary

Build a practical Odoo 19 accounting capability library first: high-frequency reads and reports, followed by invoices, bills, journal entries, payments and reconciliation. Reuse the existing registry, JSON schemas, CLI, bridge and native ORM/wizard/report paths. Deliver related capabilities in batches of about 8-12 with necessary unit tests and one shared real-Odoo smoke; do not add a separate control framework for each command. Completing an existing accounting workflow is progress even when it adds no command IDs.

Retain native ACLs, configured company/user scope, idempotency and explicit write confirmation. Historical sales, purchasing and inventory-logistics extensions remain registered but are outside current accounting-core development and must not count as accounting-core completion. Financial credit notes/refunds and inventory valuation entries are distinct from picking and physical stock returns.

Consolidated approvals, audit/evidence packaging, Pi end-to-end tests, offline installation/upgrade/rollback and reproducible release gates are later-phase work after practical accounting coverage. The fixed CLI-Anything v0.4.0 generation checkpoint remains historical provenance, not a reason to rebuild the current implementation or put release gates ahead of capabilities.

Automated write verification is limited to the two synthetic databases `odoo_cli_v4_dev` and `odoo_cli_v4_e2e`. All business databases, installed Odoo source/add-ons, Odoo/Nginx/PostgreSQL/Pi bridge services, V2/V3 installations and legacy harnesses remain protected; this goal does not authorize modifying or restarting them.

This public repository contains only independently authored V4 code, public contracts and sanitized documentation. It excludes Odoo Enterprise/custom source, private environment evidence, raw generation transcripts, credentials and real business data.
