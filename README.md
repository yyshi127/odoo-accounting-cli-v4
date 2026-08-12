# Odoo Accounting CLI V4

Independent accounting automation CLI for Odoo 19. This repository is currently in the bootstrap phase and is not a production release.

The V4 boundary is deliberately narrow: accounting capabilities, structured JSON contracts, real Odoo ORM/wizard/report integration, and safe preview/approval/idempotency/verification flows. It is not a generic ORM browser and does not implement CRM, HR, website, sales execution, purchasing execution, or warehouse operations.

## Bootstrap development

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r lock/requirements-dev.txt
.venv/bin/python -m pip install -e .
.venv/bin/python -m pytest
.venv/bin/odoo-accounting-cli-v4 version
```

The private Odoo source snapshot, raw generation transcripts, environment evidence, credentials, databases, logs, runtime state, and installed release directories are intentionally excluded from Git and release artifacts.
