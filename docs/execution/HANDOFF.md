# Odoo Accounting CLI V4 handoff

Updated: 2026-08-31 (Asia/Shanghai)

## Objective and working rule

Build a broad, practical Odoo 19 accounting CLI capability library first. Add heavier
approval, audit, and policy controls in a later phase. New work should normally
land in batches of 8-12 related commands, reuse one shared contract/runtime
path where the real Odoo API permits it, and use one shared live smoke per
batch. Do not create a generic arbitrary model/method dispatcher.

All live writes remain restricted to the two dedicated V4 databases. Do not
restart or modify Odoo, Nginx, PostgreSQL, Pi, V2, V3, business databases, or
the Odoo source/add-on tree while building CLI capabilities.

## Current authoritative count

- Registry: 355 capability IDs; 340 enabled handlers (210 reads and 130 writes)
  and 15 disabled IDs.
- Runtime status: 307 `unconfigured`, 33 `degraded`, and 15 `disabled`.
- Versioned JSON Schema documents: 685.
- Latest registry-expansion checkpoint: `44314c8`, pushed to `rebuild/v4`.
  The final supporting-object checkpoint and its evidence limits are recorded
  near the end of this document.
- The subsequent independent-accounting-date implementation is checkpoint
  `63b5288`; its 14-capability lifecycle passed on both isolated aliases. The
  financial credit-note auto/undo/apply acceptance is recorded near the
  end of this document: all 11 existing capabilities passed on both aliases,
  with rollback verification and no new production interfaces.
- The current eight-interface financial-report journal-filter extension is
  implemented, with local and focused server tests passing. Its shared dual-alias
  read-only acceptance passed in 465.22s; see the newest checkpoint at the end.
- These totals include historical inventory, sales, and purchase extensions.
  They are neither a count of pure-accounting commands nor a completion
  percentage for the accounting module. Picking, delivery, and stock-return
  documents are outside the current accounting-core acceptance scope.
- Prioritize verified invoice/payment/reconciliation and journal workflows;
  reuse existing commands instead of increasing the count with supporting
  objects or logistics commands that do not close an accounting workflow gap.
- The combined receipt/bank-matching workflow is blocked by the isolated databases' bank
  configuration: outstanding receipts and bank suspense both use account 153.
  The new 24-capability workflow test is not a completed live acceptance pass.
  See the accounting-core workflow checkpoint below before attempting another run.
- Deferred invoice/bill line dates and date readback now extend existing
  commands without adding IDs. The shared real workflow reached automatic
  generation but hit the existing `exchange_currency_rate` singleton defect;
  see the separate deferred-date checkpoint below. Neither blocked workflow
  is counted as a full live acceptance pass.

## Historical 2026-08-28 baseline (289 IDs)

- Registry baseline: 289 capability IDs, after the eight-command sales-invoice/
  stock-transfer write batch, the nine-command localized and specialist
  financial-report export extension, the ten-command native
  financial-report export batch, the nine-command fiscal-position, journal-group, and
  localization-readiness batch, the nine-command accounting
  follow-up batch, the twelve-command sales/purchase order-write batch, the
  historical 236-ID order-document read batch, the
  historical 228-ID operational-inventory read
  batch, the historical 218-ID account-return/journal-analysis
  read batch, the 210-ID management-reporting/period-
  context read batch, the historical 202-ID checkpoint, the
  190-ID partner master-data,
  179-ID analytic/budget-write, 170-ID payment/bank reconciliation,
  160-ID document-lifecycle,
  152-ID analytic/budget, 141-ID payment/reconciliation-object, 133-ID
  accounting-configuration, 125-ID reference-object, and historical 113-ID
  core-object read checkpoints.
- Implemented handlers: 272 (165 reads and 107 writes).
- Disabled/planned: 17 (8 reads and 9 writes).
- Runtime status: 251 `unconfigured`, 21 `degraded`, 17 `disabled`.
- Versioned JSON Schema documents: 549.
- Live success-path evidence: 164 reads and 106 writes (270 total).
- The latest 2026-08-28 batch added sales-order invoice creation and seven
  stock-transfer lifecycle writes.
- The preceding 2026-08-28 batch added fixed native PDF/XLSX exports for nine
  specialist and localized financial reports.
- The preceding 2026-08-28 batch added fixed native PDF/XLSX exports for ten
  core financial reports.
- The preceding 2026-08-28 batch added fiscal-position create/update/account-
  mapping replacement/archive/restore, journal-group create/update, and China/
  Singapore localization-readiness inspection.
- The preceding 2026-08-28 batch added purchase-bill create/match/unmatch, five
  payment-term writes, and period-accrual generation.
- The preceding 2026-08-28 batch added sales/purchase order create, draft update,
  line replacement, confirm, cancel, and reset-to-draft writes.
- The preceding 2026-08-28 batch added sales/purchase order search, detail,
  line, and analysis reads.
- The earlier 2026-08-28 batch added five inventory master-data reads, transfer
  search/get, stock-move search, on-hand summary, and availability inspection.
- The preceding 2026-08-28 batch added six account-return reads plus effective
  journal-date resolution and journal-item analysis summary.
- The preceding 2026-08-28 batch added eight read IDs for customer/follow-up
  reports, invoice analysis, company lock/fiscal-year context, and fiscal-year
  search/get.
- The 2026-08-28 accounting-depth batch added no IDs, handlers, or schema files;
  it deepened 12 existing interfaces (11 writes and one read).
- Known implemented exceptions and degraded boundaries:
  - `product.accounting_profile.get` has live routing/not-found evidence but no
    positive product fixture.
  - `asset.validate` reaches native Odoo but the server's
    `exchange_currency_rate` add-on raises `Expected singleton`; V4's sanitized
    failure and rollback are live-verified.
  - `asset.create` uses a visible deterministic name suffix, which supports
    ordinary replay but does not prove concurrent exactly-once creation.
  - `analytic.account.create` and `budget.create` likewise use visible
    deterministic name markers without a database uniqueness constraint. They
    support ordinary replay but do not prove concurrent exactly-once creation.
  - The other seven analytic/budget writes use deterministic keys plus
    current/target-state rechecks. There is no operation store, so an old
    request can become effective again after an intervening state change.
  - `partner.create` uses a visible deterministic `ref` marker without a
    database uniqueness constraint. It supports ordinary replay but does not
    prove concurrent exactly-once creation.
  - The other eight partner writes use deterministic target-state rechecks but
    no operation store, so an old request can become effective again after an
    intervening state change.
  - `account.account.create` and `tax.create` use company-scoped natural-key
    rereads but do not have a database-unique operation marker, so concurrent
    exactly-once creation is not proven. The other ten accounting-configuration
    writes use deterministic target-state rechecks without an operation store.
  - `sale.order.create` and `purchase.order.create` support ordinary marker
    replay but have no database-unique operation marker, so concurrent
    exactly-once creation is not proven. The other ten order writes use
    deterministic target-state rechecks without an operation store.
  - Accounting-account updates and archive/restore reject accounts shared with
    any other company because the affected Odoo fields are shared. This is a
    deliberate company-boundary guard, not a missing cross-company feature.
  - `partner.accounting.update` declares accounting-user and partner-manager
    deployment requirements. Runtime explicitly checks the accounting-user
    group and relies on native `res.partner:write` ACL for partner-management
    authority; it does not duplicate that ACL as a second `has_group` call.
  - `asset.pause` has no reliable persisted native pause-date field.
  - Both deferred generators, multicurrency revaluation generation, and both
    period transfers use visible replay markers that are not database-unique
    under concurrency.
  - New invoice, bill, and journal-entry creates no longer occupy
    `account.move.ref`: they store a capability/company/key token and parameter
    fingerprint in `invoice_origin`. Legacy `ref=key` records remain
    replay-compatible. `invoice_origin` is also an Odoo business source field,
    so this is a pragmatic compatibility location, not a permanent operation
    store or proof of concurrent exactly-once behavior.
  - `budget.line.list/get` indirectly uses `budget.report` for computed amounts.
    Standard Odoo ACLs pass in both isolated databases, but that indirect model
    is not yet represented in preflight metadata for custom-ACL deployments.

The current 289-ID baseline is exact for this checkpoint but is not a proven
final capability count.

Count lineage is historical, not a sizing formula: the original reviewed
matrix had 102 IDs, the core-object batch brought the checkpoint to 113, the
reference-object batch to 125, and the accounting-configuration batch to 133.
The payment/reconciliation object batch brought it to 141, the analytic/budget
batch to 152, the document-lifecycle batch to 160, the payment/bank
reconciliation batch to 170, the analytic/budget write batch to 179, the partner
master-data batch to 190, and the accounting-configuration write batch to 202.
The management-reporting/period-context read batch then brought it to 210.
The account-return/journal-analysis read batch then brought the historical
checkpoint to 218. The operational-inventory read batch brought the current
checkpoint to 228. The sales/purchase order-document read batch brought the
checkpoint to 236. The sales/purchase order-write batch brought the current
checkpoint to 248. The accounting follow-up batch brought the current checkpoint
to 255. The fiscal-position/journal-group/localization-readiness batch brought
it to 262, the native financial-report export batch brought it to 272, and the
specialist/localized export extension brought it to 281.
The sales-invoice/stock-transfer write batch brought it to 289.
The 125-ID checkpoint was therefore only the historical `102 + 11 + 12`
lineage, not a target or sizing basis.
Sufficiency must be judged by closed Odoo workflows and live evidence, not by
reaching any one of those numbers.

The coverage boundary is also not inferred from command count. Both isolated
databases currently have the same 82 installed modules. A read-only audit found
39 accounting or accounting-adjacent modules: 25 belong to the primary coverage
boundary, five EDI/compliance modules are conditional follow-up scope, and nine
UI/communication/technical modules do not require independent CLI commands.
Uninstalled modules such as `hr_expense`, `stock_landed_costs`, MRP, POS, bank-
file import, batch payment, consolidation, and SEPA are not claimed as covered.
Future completion must be supported by a module/workflow/lifecycle matrix with
every in-scope gap implemented or explicitly excluded.

## Latest completed batch: sales invoicing and stock transfers

Implemented through the fixed public JSON write contract:

1. `sale.order.invoice.create`
2. `stock.transfer.create`
3. `stock.transfer.confirm`
4. `stock.transfer.assign`
5. `stock.transfer.quantities.set`
6. `stock.transfer.validate`
7. `stock.transfer.unreserve`
8. `stock.transfer.cancel`

The server runtime regression passed `73 tests in 0.52s`. The guarded shared
smoke passed `2 tests in 13.78s`; in each of `odoo_cli_v4_dev` and
`odoo_cli_v4_e2e`, uid 5/company 1 completed all eight first executions and
immediate replays, created one real backorder from a partially completed
transfer, and then verified transaction, record, operation-type, and temporary-
group rollback.

Real Odoo 19 testing found one runtime compatibility defect: `uom.uom` no
longer has `category_id`. The bridge now calls Odoo 19's
`_has_common_reference()` to preserve the same-dimension guard. The other
changes were smoke-fixture corrections: an explicit income account for the
temporary sale product, acceptance of the normal null name on a draft invoice,
and a caller origin outside the reserved `ODACV4` marker namespace.

Evidence is retained at
`/opt/odoo-accounting-cli-v4/.tooling/stock-transfer-write-batch-22d9cdc2-0c95-489f-aeeb-8bf41eb2516e`:

- live log: `live-smoke-retry-8.log`, SHA-256
  `d22c43c5d1ee330dcf7bdccf9928dd87bc6bbdf16feb8023eee35d5bc3207794`;
- runtime unit log: `runtime-unit-after-fix-8.log`, SHA-256
  `32a4c93fb4cc386e01085534b38275d22eb1543759d56b797e85286ad4c12a45`;
- final three-file patch: `smoke-fix-8.tar.gz`, SHA-256
  `a8bbeb1e2e703a6e5d1e12c337b202b79b4e1ae63e7b89e34d276ce91893432d`;
- pre-patch backup: `pre-smoke-fix-8.tar.gz`, SHA-256
  `e430f658707d0b0e47142cced269e8c005d2ff63efbdb1bc748b8262639ac583`.

The public server capability list returned 289 IDs and canonical registry
digest `72b2a90c0e8da798156856ccb9285a80ce4b1572e108147ff81feb8b8c21eb71`.
Independent read-only SQL checks found zero residue for every retained failed-
attempt marker. Odoo, Nginx, and PostgreSQL retained their exact pre-run start
timestamps and restart counts; no service-control command was issued.

`sale.order.invoice.create` and `stock.transfer.create` are marked `degraded`
only because sequential replay is proven but concurrent exactly-once creation
is not backed by a database-unique request key. The other six writes use fixed
target-state replay checks. This batch is synchronized to the server but is not
yet committed to Git; the last pushed checkpoint remains the 272-ID commit
`06bf335e4ad6ce3272bb280a74e845627b05dd35`. The server working tree contains
the synchronized current files, but its repository metadata still points to
the older base commit `2e190bcdd70313c0a10dcc479e1a2834db240a50`; do not use
that server `HEAD` to reset or infer the deployed source state.

## Earlier completed batch: specialist and localized report exports

Implemented and verified:

1. `report.journal.export`
2. `report.asset.export`
3. `report.deferred_expense.export`
4. `report.deferred_revenue.export`
5. `report.multicurrency_revaluation.export`
6. `report.china.balance_sheet.export`
7. `report.china.profit_and_loss.export`
8. `report.china.cash_flow.export`
9. `report.singapore.gst.export`

All nine reuse the existing fixed export capability and bridge path. Journal
export calls Odoo's official `dispatch_report_action` because its report
handler overrides PDF/XLSX export behavior; the other eight call the official
fixed report exports directly. China and Singapore exports fail closed unless
the company fiscal country and chart match the corresponding localization.
No generic report, model, or method dispatcher was added.

### Verification

- Focused local selection: 219 passed and one opt-in live test skipped in
  622.49 seconds. Targeted Ruff and `git diff --check` passed.
- Synchronized server selection: 219 passed in 547.23 seconds.
- Post-review journal-metadata regression: 117 passed locally in 481.11
  seconds and 72 passed on the synchronized server in 6.16 seconds.
- One shared read-only live smoke passed in 63.06 seconds. It performed 76
  native exports: all 19 fixed report-export capabilities in PDF and XLSX in
  both `v4-dev` and `v4-e2e`, using only `odoo_cli_v4_dev` and
  `odoo_cli_v4_e2e`.
- Public CLI end-to-end checks passed for a 47,484-byte journal PDF in
  `v4-dev`/company 1 and a 7,133-byte Singapore GST XLSX in
  `v4-e2e`/company 2. Base64, byte count, SHA-256, alias/company binding, and
  file magic were independently verified.
- Registry: 281 IDs, 264 handlers (165 reads and 99 writes), 533 schemas, and
  statuses of 245 `unconfigured`, 19 `degraded`, and 17 `disabled`.
  Capability-ID SHA-256:
  `04f3e17865e63eeb5a3765a8f7de6f7c93e755d6687e5b3dcffcd33f912f29da`.
  Canonical registry digest:
  `a0d195d91a32dfd012f4b76909d51e0302339399ffe3802bf00f6f799f99f9a7`.
- Evidence directory:
  `/opt/odoo-accounting-cli-v4/.tooling/financial-report-export-extension-838b729d-342c-49a2-86ff-04846b2ae30e`.
  Focused-log SHA-256:
  `e47f6da4082242d3edc6f4faa5745fedb483454792b1f7eb0282fe4163b202ce`.
  Live-log SHA-256:
  `76e920d6272f33039ccefd9cac89cbfaa0d5658c0b8b7115806ed43afdc89379`.
  Public-CLI summary SHA-256:
  `dd426f89da4344536a5357a5e700ac8770411dfb3848a3edd66250eb4f0938f8`.
- The 30-file deployed-source archive has SHA-256
  `8ea9a5a6cd28fa2ec43e45f7ec40e79fbae1a561e451b79bce60b59d0cd76394`.
  The validated pre-sync rollback archive has SHA-256
  `aa6726e94967370fe31f17a8d5b9d76b7e8ddd7573ff45312efa5cf7dad7ec04`.
- Odoo, Nginx, PostgreSQL, and Pi snapshots are byte-identical before and
  after, both with SHA-256
  `ce322158b9bf7d81e844f198095ac920cff2436ca1436e3c01c9f15595634fdc`.
  No service-control command or business-database write was used.

The first server smoke attempt is retained but is not counted: it ran as
`root` and stopped at PostgreSQL peer authentication before reaching any
capability. The successful rerun used the Odoo service account. These exports
prove valid native files on the current fixtures; they are not golden-value
tests for every possible accounting dataset.

## Previous completed batch: native financial-report exports

Implemented and verified:

1. `report.trial_balance.export`
2. `report.balance_sheet.export`
3. `report.profit_and_loss.export`
4. `report.cash_flow.export`
5. `report.tax.export`
6. `report.general_ledger.export`
7. `report.partner_ledger.export`
8. `report.aged_receivable.export`
9. `report.aged_payable.export`
10. `report.executive_summary.export`

All ten use the fixed `account.report.fixed_export` action, native Odoo 19
`account.report` definitions, posted entries, company/user scope, and strict
PDF/XLSX response contracts. There is no generic report or model dispatcher.
The runtime transaction is read-only and exported files are checked for Base64,
byte count, SHA-256, native file type, and PDF/XLSX magic bytes. The bridge
response limit is 96 MiB, which safely carries the Base64 form of the fixed
64 MiB file limit.

### Verification

- Server focused regression: 269 passed in 498.97 seconds.
- Final bridge-client/runtime regression: 47 passed in 0.23 seconds locally and
  on the synchronized server.
- One shared dual-database smoke passed in 33.50 seconds. It performed 40 native
  exports: ten capabilities times PDF/XLSX in each of `v4-dev` and `v4-e2e`, as
  uid 5/company 1, inside read-only transactions.
- Public CLI end-to-end verification passed for a 39,097-byte trial-balance PDF
  in `v4-dev` and a 7,482-byte general-ledger XLSX in `v4-e2e`.
- Capability-ID SHA-256:
  `b14c19b3fcc05787deb9c924f200166a5ce7139d4648a404f697aabee493ba64`.
  Registry-file SHA-256:
  `51511d050cd6b28f037741f61107acab9734b618fc6029e82a55b185383b0d48`.
  Canonical registry digest:
  `2c3009784a48c56fe337cd3f09a634c2f4a411302575aac0b6a61930343654b2`.
- Evidence is retained under
  `/opt/odoo-accounting-cli-v4/.tooling/financial-report-export-batch-2282bf69-1a4f-4356-a6b1-a19103d11f86`.
  The focused log SHA-256 is
  `de680148ba680ed4f8b74e3989bc10de2acc681210c0841e86ceb153fb46548b`;
  the live-smoke log SHA-256 is
  `63025c82e5e9b777024580d048eda07275dfe6b6ff776b46a7ac1fb8533f6c21`;
  the public-CLI verification summary SHA-256 is
  `920f738f6cd635d49785f8c6fbd1f5e78788d12de72493d54531558a421a2c08`.
- Before/after service snapshots are byte-identical, both with SHA-256
  `baa61f348401615814ebee1a2f59071036d5be8ae79765febcb87fa5217de105`.
  No Odoo, Nginx, PostgreSQL, Pi, V2, or V3 service was restarted or modified.
- Pre-overwrite rollback archives are readable: the seven-file
  `pre-sync-backup.tar.gz` has SHA-256
  `7b69df96e0bb7961b16d6306dba725c8e887ea1edd033041547a4e0d95262000`;
  the two-file `pre-client-limit-backup.tar.gz` has SHA-256
  `936dbf8bce53914419377b7087a56de2904eba8ed21532d1ef22352bafee1279`.
  These are batch-level file backups, not a whole-server or database snapshot.

## Previous completed batch: fiscal positions, journal groups, and localization readiness

Implemented and verified:

1. `fiscal_position.create`
2. `fiscal_position.update`
3. `fiscal_position.account_mappings.replace`
4. `fiscal_position.archive`
5. `fiscal_position.restore`
6. `journal.group.create`
7. `journal.group.update`
8. `localization.china.configuration.inspect`
9. `localization.singapore.configuration.inspect`

The write path uses the existing closed core-write contract and native Odoo 19
models. Account mapping replacement accepts an empty list to clear mappings.
Fiscal-position HTML notes are verified against Odoo's sanitized value rather
than against unsanitized input. Journal-group creation relies on Odoo's native
company/name uniqueness. The two readiness reads use one read-only action and
return localization-specific missing checks; they do not submit filings or
render vouchers.

### Verification

- Final local and synchronized-server write regression: 75 passed on each.
- Broader local and server focused selections: 111 passed on each before the
  live-derived default/HTML comparison correction; the final 75-test regression
  includes that correction.
- One guarded shared live test passed in 6.18 seconds. It ran all seven writes
  with immediate replay and both reads in each of `v4-dev` and `v4-e2e`, then
  rolled back and used fresh cursors to prove no fiscal-position, mapping,
  journal-group, or temporary manager-group residue.
- Four full public CLI localization reads passed: China/company 1 and
  Singapore/company 2 in both aliases.
- Capability-ID SHA-256:
  `9212e9829355e5a3c44c1a0eb314e63a15240c84b5e310a540307f2e6b8a9ce8`.
  Registry-file SHA-256:
  `42d535a3520d1807cf9a22c843687573db056e81b42fc5a92f6e1966b3f50d3f`.
  Canonical registry digest:
  `64d0308eece99ad4f419642a447582d4d2e8408bd42c8c0500030f0657950dce`.
- Evidence is retained under
  `/opt/odoo-accounting-cli-v4/.tooling/accounting-configuration-batch-150e0d50-7fa3-48fb-9ee3-a6123945260b`.
  The final live log SHA-256 is
  `be5cf6902f9fb5f96b73aa3597a59d9bb45d4e2f5cb1b3c94029a7877f7d9d4c`;
  the public-read log SHA-256 is
  `580d0a674a430a1144b71bda206bf05840280dd3e1d649fa9aae0debe5fb3083`.
- Before/after service snapshots are byte-identical, both with SHA-256
  `8b733a18fb71202470a3a387acdae26a11493f9f5e452d67110ed9da81845ecb`.
  No Odoo, Nginx, PostgreSQL, Pi, V2, or V3 service was restarted or modified.

### Evidence limits

- `fiscal_position.create` replays by company/name plus the complete requested
  configuration, but Odoo has no native unique operation key; concurrent
  exactly-once creation is not claimed and the registry marks it degraded.
- Fiscal-position tax mappings are deliberately outside this command. Odoo 19
  represents source-tax relations on shared destination tax records, so adding
  them here would require a separate cross-company contract rather than one
  more field on account-mapping replacement.

## Previous completed batch: accounting follow-up writes

Added or enabled `purchase.order.bill.create`, `purchase_bill.match`,
`purchase_bill.lines.unmatch`, `payment_term.create`, `payment_term.update`,
`payment_term.lines.replace`, `payment_term.archive`, `payment_term.restore`,
and `period.accrual.generate`. At that checkpoint the registry had 255 IDs, 236 handlers (144
reads and 92 writes), 218 `unconfigured`, 18 `degraded`, 19 `disabled`, and 477
schemas.

The shared dual-database smoke passed `2 tests in 8.40s`. Each isolated database
completed nine first executions and nine immediate replays; transaction rollback
and temporary-group rollback were both true. Odoo 19 draft vendor bills expose
`name = null`, so the result contract was corrected to accept that native value.
The final focused local selection passed 123 tests and the synchronized server
selection passed 121. The server public `capabilities list` returned all 255
IDs with the canonical digest below. The live smoke exercised the public
contract plus real runtime inside one rollback transaction; focused tests
separately verified the public CLI and model mapping.

- Capability-ID-list SHA-256:
  `af1c980ecac6e516ed988b152f7a69158ec7523f4e9d7e1cbfba874f5e4c8f0d`
- Canonical registry digest:
  `c8fff1a9975d6adcc23d32b1e5a39fd2b6ae5be6de6a8961d5bb61f0f9565b1f`

Odoo PID `3547689`, Nginx master PID `2193677`, PostgreSQL PID `2193725`, and
Pi bridge PID `3296254` retained their pre-deployment start times. No service
was restarted; Nginx and PostgreSQL remained active.

This is the current capability-first checkpoint, not completion of G5 or the
overall capability target.

The worktree contains the cumulative capability-first implementation and is
intentionally dirty/uncommitted. Do not reset, clean, or replace it with HEAD.

## Previous completed batch: sales and purchase order-document reads

Added and dual-database live-verified:

1. `sale.order.search`
2. `sale.order.get`
3. `sale.order.line.search`
4. `sale.order.analysis.summary`
5. `purchase.order.search`
6. `purchase.order.get`
7. `purchase.order.line.search`
8. `purchase.order.analysis.summary`

The registry now has 236 IDs and 215 handlers (144 reads and 71 writes), with
202 `unconfigured`, 13 `degraded`, 21 `disabled`, and 435 schemas. Local
focused tests passed 126 cases and the synchronized server selection passed
112. The shared dual-database smoke recorded `2 passed in 7.26s`; independent
SQL checks found zero partner, product, sale-order, sale-line, purchase-order,
and purchase-line residue in both isolated databases. Live evidence now covers
143 reads and 70 writes (213 total). Before/after service snapshots were
identical: Odoo `NRestarts=2`, Nginx `0`, and PostgreSQL `0`.

Exact fingerprints:

- Capability-ID-list SHA-256:
  `9032699a10ce3113c27e8ef538d180b331be143edaa365abb79bc0b3702c7232`
- Canonical registry digest:
  `284657bf0e4292039cb85d15767c08ce0bf77c415cfb62addaffa8b123525a2f`
- Registry-file SHA-256:
  `94c9b07f09ea72422c6d30626a330586d3f4bcfa3782ea9a159a9532705c3930`
- CLI-list-file SHA-256:
  `43aa2ceaefbb34d7b55b4fc79e4a0e5e0b202fb40e21c1222bea7d0d6ad51604`
- Live JUnit SHA-256:
  `3e6c5463b10057ec287b0a5f3b2cccdce4167797a242bc4971e15389b979dfd1`
- Pre-live archive SHA-256:
  `fe89d7cc0a6351e50e1639ebb0aafa82d63fa6b57962fa5d84cc4ab7272255e9`

## Historical completed batch: sales and purchase order writes

Added and dual-database live-verified:

1. `sale.order.create`
2. `sale.order.update_draft`
3. `sale.order.lines.replace`
4. `sale.order.confirm`
5. `sale.order.cancel`
6. `sale.order.reset_to_draft`
7. `purchase.order.create`
8. `purchase.order.update_draft`
9. `purchase.order.lines.replace`
10. `purchase.order.confirm`
11. `purchase.order.cancel`
12. `purchase.order.reset_to_draft`

The registry now has 248 IDs and 227 handlers (144 reads and 83 writes), with
212 `unconfigured`, 15 `degraded`, 21 `disabled`, and 459 schemas. Live
success-path evidence covers 143 reads and 82 writes (225 total).

The new focused local selection passed `135 tests in 109.91s`. After repairing
pre-existing exact-count expectations, the affected regression passed `428
tests in 567.86s`; registry/runtime alignment passed `44 tests in 4.07s`, and
the cumulative-count selection passed `5 tests in 45.46s`. The synchronized
server focused selection passed `136 tests in 68.52s`, and its cumulative-count
selection passed `5 tests in 36.47s`. The final dual-database evidence run
recorded `2 passed in 7.74s`; another successful evidence run recorded `2
passed in 8.29s`.

Fresh SQL checks found zero temporary partners, products, sale orders, sale
lines, purchase orders, purchase lines, and temporary standard-group
memberships in each isolated database. Before/after service files are
byte-identical: Odoo 19 `NRestarts=2`, Nginx `0`, and PostgreSQL `0`. The first
root-side attempt stopped at PostgreSQL peer authentication before connecting
to either database. The subsequent run under the `odoo` OS user succeeded; the
authentication-only attempt is not a capability failure or live evidence.

Exact fingerprints:

- Capability-ID-list SHA-256:
  `383bc6b03694c40eeef978244f28f6e28e2440905e98c43e02274726db9f9d25`
- Canonical registry digest:
  `5d10bd54a83a2d375f458fc1c8800ca0691068c054b3f9927dd00a03fba942c3`
- Registry-file SHA-256:
  `6f9caa3efc7c2c6d46d3a1ba6aa801a58e598590a9f77490e6506f036cc82d22`
- CLI-list-file SHA-256 and size:
  `509015066be34db397e1b0d623da791f435837a98a607adec384ec31ab8a4f07`,
  107962 bytes
- Live-log SHA-256:
  `8cb502a4b7c5a493a16646f81911231c96931da21d00488037de53b89f1d3a69`
- Live JUnit SHA-256:
  `bbacbeaa3b5aaa0ebd2e61e547565ee8eaff40bd6d5cca567b7a3d6383962c18`
- Identical before/after service-snapshot SHA-256:
  `89933ce14d537588ccfa76126b7d1c7b476cbd44a2ff7ae68a1808ffe1b452ef`
- Each database residue-file SHA-256:
  `b9e038a67cb826e6fe86c15a414a3d485e2c7b95acce772508f6f66a7a8ef11c`
- Final archive: 49 members, 205556 bytes, SHA-256
  `49c0a091fc8a2f10763acd05833bb20f42e3c1df6de0cdcff81c7a5bc3fd96e2`;
  the synchronized server archive has the same hash.

## Previous completed batch: operational inventory reads

Added and dual-database live-verified:

1. `product.category.list`
2. `warehouse.list`
3. `stock.location.list`
4. `stock.operation_type.list`
5. `stock.route.list`
6. `stock.transfer.search`
7. `stock.transfer.get`
8. `stock.move.search`
9. `inventory.on_hand.summary`
10. `inventory.availability.inspect`

The commands use fixed request/response contracts, two allowlisted bridge
actions, ordinary-accountant ACL checks, strict company scope, and native Odoo
inventory models. No generic ORM or model/method dispatcher was introduced.

The synchronized remote selection recorded `138 passed`. The final shared
guarded live run executed all ten reads in both `odoo_cli_v4_dev` and
`odoo_cli_v4_e2e` as uid 5/company 1 and recorded `2 passed in 5.49s`.
Independent post-rollback residue checks returned `0|0|0|0` for each database.

Two earlier attempts are not evidence. Root peer authentication stopped the
first attempt. The first Odoo-user run failed because its fixture had
`categ_id=False`; its transaction rolled back and committed nothing. Correcting
the fixture produced the passing dual-database run above.

Current exact fingerprints:

- The CLI returned 228 unique, sorted capability IDs.
- Capability-ID-list SHA-256:
  `709e4ce12c7d8cf5dcfebb9dbf45a6082aff1ebca380f73aec823d70a1d3088f`
- Registry-file SHA-256:
  `3e357d2cf4ba748ff4175603dd4c8daf1b6b635efb948291da63b06b7e965391`
- Canonical registry digest:
  `bc644e686f863ae6cca947c4c040bfecce7395d1c84e9dd8a43b9c83984d7b94`
- Retained live log:
  `/opt/odoo-accounting-cli-v4/.tooling/inventory-read-live-run-1787885244043.log`;
  SHA-256
  `b8b6afa9754d7f32236ba2fa43fdd01f66b9523f2fdeccc0601ee542d969bc6b`.

Nginx and PostgreSQL are active with `NRestarts=0`. Odoo is active with
`NRestarts=2`: the passlib `ModuleNotFoundError` caused an automatic exit at
10:24:43 and systemd restarted it at 10:24:53. This occurred before the 10:40
deployment and the successful live run at 10:47. The batch issued no
service-control command, but it does not claim that no restart occurred during
the overall observation window.

## Previous completed batch: historical 218-ID account returns and journal analysis

Added and dual-database live-verified:

1. `account.return.search`
2. `account.return.get`
3. `account.return.summary`
4. `account.return.type.list`
5. `account.return.check.list`
6. `account.return.check.get`
7. `journal.accounting_date.resolve`
8. `journal_item.analysis.summary`

The return commands expose fixed company-scoped return, type, check, and
deadline-summary reads without dynamic actions, attachments, audit-only fields,
or a generic ORM dispatcher. Journal-date resolution uses Odoo's native
`accounting_date`; journal-item analysis uses posted, company/date-scoped
`_read_group` with a fixed account-or-journal grouping choice.

The focused local feature selection recorded `84 passed`; the independent
registry/schema selection recorded `29 passed`. The synchronized server core
selection recorded `48 passed`. The broader server selection lost its SSH
output stream before returning an exit status, so no result is inferred from
that run. Local Ruff checks passed; Ruff is not installed in the server project
virtual environment.

One shared guarded smoke ran all eight reads in both `odoo_cli_v4_dev` and
`odoo_cli_v4_e2e` as uid 5/company 1 and recorded `2 passed in 5.09s`. Each
alias created one non-Audit return and one check only inside its outer
transaction. Full rollback, a fresh Odoo cursor, and an independent SQL query
all found zero marker residue. Only fixture setup used the Odoo superuser; all
eight public capability executions used uid 5 without `sudo` or group changes.

Historical 218-ID checkpoint fingerprints:

- Capability-ID-list SHA-256:
  `c96f9c1510501eaa3ca09b62a697b6577ddaa79688a9b30c563f704926c8cef3`
- Registry-file SHA-256:
  `e9180a7f420030debed3f535d920f1deae7e61b5a8f0d417af1a1720c686a4f3`
- Canonical registry digest:
  `274533a2aaf573b32029b507e21db7864fbd2ac2587637a14e344cfcffb299ec`
- 37-file synchronization archive: 149640 bytes; SHA-256
  `f28becccf575a506d41fbed487f796e39e76e68ebd15c4d59580836556ba3140`.
- Retained live log:
  `/opt/odoo-accounting-cli-v4/.tooling/return-journal-analysis-live-run-1787882134143.log`;
  SHA-256
  `6e9d2ac69f14bfc2c9b00ba8609493cba67870f7173df29807d73eb5e09f033a`.

All 37 synchronized files match the local tree byte-for-byte. Odoo, Nginx, and
PostgreSQL remained active with their pre-batch start timestamps and restart
counts; no service-control command was issued.

## Previous completed batch: management reporting and period context

Added and dual-database live-verified:

1. `report.customer_statement`
2. `report.followup`
3. `invoice.analysis.search`
4. `invoice.analysis.summary`
5. `company.lock_dates.inspect`
6. `company.fiscal_year.resolve`
7. `fiscal_year.search`
8. `fiscal_year.get`

The two partner reports are fixed to one company, one partner, posted entries,
and official Odoo report handlers. Invoice analysis uses the native
`account.invoice.report` model with fixed filters, grouping choices, and
cursor order. Lock dates and fiscal years use fixed company-scoped fields and
native fiscal-year resolution; no nonexistent `account.fiscal.period` model or
generic ORM dispatcher was introduced.

One shared guarded smoke ran all eight reads in both `odoo_cli_v4_dev` and
`odoo_cli_v4_e2e` as uid 5/company 1 and recorded `2 passed in 6.62s`. A fiscal-
year fixture was created only inside each outer transaction, followed by full
rollback and a fresh-cursor absence check. No service was restarted.

Focused module/runtime tests recorded 131 passes locally. The unified new CLI
selection recorded 6 passes, the two report CLI cases recorded 2 passes, the
registry selection recorded 17 passes, and the final count-related selections
recorded 14 local passes and 43 synchronized-server passes.

Current exact fingerprints:

- Capability-ID-list SHA-256:
  `6ba5e3d877b6fa857d1689c14da30132b63572c801e2d25b4af4e30c10a6dd82`
- Registry-file SHA-256:
  `58de9401661a4ebeefc7892c3a4da20d38bda1fe34d1502b9588d957ee936d94`
- Canonical registry digest:
  `50451ae4a3b6d145ad4d89c3b3f6f7a11b70472a6f35099b609842d19fc3e19f`
- Final explicit 41-file source archive: 156351 bytes; SHA-256
  `37258845be076e3c6432d6291ed6fc690578b2befd8e3674a9e848d5f01d0191`.
  Its entries are unique, relative, and present in the active tree.

## Previous completed batch: accounting depth for twelve existing capabilities

Deepened and dual-database live-verified without increasing the command count:

1. `customer_invoice.create`
2. `vendor_bill.create`
3. `invoice.lines.replace`
4. `customer_credit_note.create`
5. `vendor_refund.create`
6. `journal_entry.create`
7. `journal_entry.lines.replace`
8. `receivable.payment.register`
9. `payable.payment.register`
10. `invoice.payment_status.inspect`
11. `reconciliation.apply`
12. `reconciliation.undo`

Invoice and bill creation now accepts either a payment term or due date,
business references, product-backed lines, discounts, and optional analytic
distribution. Refund creation supports complete replacement lines and the
caller-supplied request idempotency key while retaining a narrowly matched
legacy replay marker.
Journal-entry creation/replacement supports references, paired currency and
amount-currency values, and optional analytic distribution. Payment
registration supports a positive partial amount. Payment-status inspection
returns validated outstanding items and the reconciliation graph.

Reconciliation apply delegates to the native Odoo invoice-widget assignment.
Invoice-targeted undo removes only the requested partial reconciliation and
returns the remaining graph, including other partials and multi-term invoice
lines. The older exact two-line apply/undo mode remains compatible. Optional
product, payment-term, currency, and analytic records are checked through their
real ORM ACL and company scope only when requested; no `sudo`, arbitrary ORM
dispatcher, or new control plane was introduced.

### Verification

- Final current-tree four-file public/runtime selection: 496 passed in 826.41
  seconds. It covers `test_core_writes.py`, `test_core_writes_runtime.py`,
  `test_invoices.py`, and `test_invoice_runtime.py` after the final undo-
  validator correction.
- Final synchronized server evidence: 56 invoice/runtime critical tests passed
  in 0.55 seconds, and the six directly affected public undo tests passed in
  4.44 seconds. No full 496-test server rerun is inferred.
- Earlier cross-layer selection: 215 passed in 266.76 seconds. Earlier
  synchronized focused selection: 200 passed in 93.97 seconds. Current registry
  selection: 17 passed in 197.19 seconds.
- One guarded pytest case ran the complete Odoo chain in both
  `odoo_cli_v4_dev` and `odoo_cli_v4_e2e` as uid 5/company 1 and recorded
  `1 passed in 16.91s`. All 11 target writes ran once and replayed immediately;
  payment status was inspected before assignment, after assignment, and after
  targeted undo.
- Each alias used one outer transaction. Rollback plus a new read-only cursor
  proved the recorded move, payment, and product-fixture IDs plus operation
  markers absent. Four earlier smoke attempts failed on real Odoo integration
  differences, but each used the same rollback and fresh-cursor verifier before
  re-raising; only the fifth run is the accepted success.
- The product fixture was created with superuser authority only inside the
  rollback transaction. Every capability handler ran as uid 5 without `sudo`
  or temporary group elevation. Optional analytic distribution has contract
  and runtime coverage but no positive live analytic example because uid 5 does
  not have the analytic group.
- Preservation of an unrelated partial reconciliation is live-verified. The
  multi-term remaining-graph behavior has contract/runtime coverage but no
  positive multi-term live fixture.
- Capability-ID-list SHA-256 (unchanged):
  `6ecb58789446447a2d3e4d89957eb6cd87147b0346fd68a6fa3cef23b5dc08f3`
- Registry-file SHA-256:
  `c2f0fe18d1646b0b218fe3860400a26ae997f691291e438eef684acd377db5be`
- Canonical registry digest:
  `6eb4404cf3f31d7ce140db41f0346444a6edcd85d7e9720ff9163760623f02b2`
- Final explicit 23-file batch source archive: 201732 bytes; SHA-256
  `de9bf4ccce8f76502d835e001f2880d346dc0b8dcd77264e556c74302d179c36`.
  Its 23 unique safe regular-file entries are byte-identical to the active
  local tree.
- Final wheel: 660021 bytes; SHA-256
  `7f8ab0ba3b6e9ac877d74ca9855df1a720248f43631db0d60c7b1071447baa00`.
  Its 438 unique entries contain 367 schemas, all 202 capabilities, and all 181
  handlers, with no duplicate, backslash, or unsafe path. A clean install and
  `capabilities list` returned 202 IDs and the same canonical registry digest.
- All 23 active files on `43.165.173.80` match the local files byte-for-byte.
  Accepted server artifacts are retained at
  `/opt/odoo-accounting-cli-v4/.tooling/accounting-depth-batch-final-20260828.tar.gz`
  and
  `/opt/odoo-accounting-cli-v4/.tooling/odoo_accounting_cli_v4-0.0.0-accounting-depth-final-20260828.whl`;
  server-side hashes match the local artifacts.
- This batch issued no service-control or restart command. The post-smoke
  read-only check found `odoo19`, Nginx, and `postgresql@16-main`
  active/running. Odoo's start timestamp remains 2026-08-27 10:25:38 CST, the
  already documented phoenix/systemd recovery time; Nginx and PostgreSQL start
  times are likewise unchanged during this batch.

The authoritative counts remain 202 registered interfaces, 181 implemented
handlers (110 reads and 71 writes), 21 disabled descriptors, and 367 schemas.
Retained live-success counts remain 109 reads and 70 writes because every
interface in this depth batch already had a live success path before it was
deepened.

## Previous completed batch: twelve accounting-configuration writes

Implemented and dual-database live-verified:

1. `account.account.create`
2. `account.account.update`
3. `account.account.archive`
4. `account.account.restore`
5. `journal.create`
6. `journal.update`
7. `journal.archive`
8. `journal.restore`
9. `tax.create`
10. `tax.update`
11. `tax.archive`
12. `tax.restore`

The batch uses closed request/response schemas and fixed ORM paths over
`account.account`, `account.journal`, and `account.tax`. All commands require
`account.group_account_manager`, native ACL checks, configured uid/company
scope, exact confirmation, deterministic replay checks, and one of the two
isolated databases. `journal.create` also declares `account.account:create`
because Odoo may automatically create a liquidity account for bank, cash, or
credit-card journals.

Practical defaults are aligned with Odoo 19: receivable/payable accounts become
reconcilable, a missing journal default account may be assigned by Odoo, tax
amounts are limited to four decimal places, and `tax_group_id=null` restores the
company's automatic tax group. Shared multi-company accounts fail closed for
update and archive/restore, preventing a company-scoped command from mutating
fields visible to another company.

### Verification

- Pre-fix synchronized broad selection: 423 passed in 767.33 seconds; the final
  103-test synchronized selection covering every subsequent compatibility and
  company-boundary fix passed in 61.13 seconds.
- The complete local regression recorded `3186 passed, 140 skipped, 1 failed in
  3314.58s`. The sole failure was a stale CLI-contract assertion that still
  expected the preceding 190-ID registry. After correcting that test-only
  expectation to 202, the full CLI-contract file passed `14 tests in 167.25s`.
  No second 55-minute full sweep was run after changing only that assertion, so
  no inferred 3187-pass result is claimed.
- One guarded transactional smoke exercised all twelve commands, first
  execution, and immediate replay in both `odoo_cli_v4_dev` and
  `odoo_cli_v4_e2e` as configured uid 5/company 1; pytest recorded
  `1 passed in 9.55s`.
- The smoke temporarily linked `account.group_account_manager` inside each
  rollback-only transaction. Fresh-cursor checks proved that the created
  receivable account, bank journal, automatic liquidity account, tax, and
  temporary user-group relation left no residue.
- Live success-path evidence: 109 reads and 70 writes.
- Capability-ID-list SHA-256:
  `6ecb58789446447a2d3e4d89957eb6cd87147b0346fd68a6fa3cef23b5dc08f3`
- Registry-file SHA-256:
  `5f224b7661ad07844b2cebb694fb5e864eb78dbcbefc2b9e1b91c28c0e97e81a`
- Canonical registry digest:
  `91d087511423deb5c7aede88ec28452468ec570b44b8a8d79649e7cdbf8563d0`
- Final source archive: 158280 bytes; SHA-256
  `f51cdcf1da0ff7d85f811cff08cb27866c00871549c55972546f8b2adec453ee`.
  Its 58 entries are byte-identical to the active files, with no duplicate or
  backslash-named entries.
- Clean wheel: 649140 bytes; SHA-256
  `37646e68151cbbfcefe70f5e3e74df0919b1dd6a3e18c50876a5a95f7b1dbf55`.
  It contains 438 entries, 367 schemas, all 202 capabilities, and all 181
  handlers, with no duplicate or backslash-named entries.
- The source archive and wheel were copied to
  `/opt/odoo-accounting-cli-v4/dist/` on `43.165.173.80`; server-side hashes
  match the local accepted artifacts. The active server source was synchronized
  separately and used by the final focused tests and transactional smoke.
- `account.account.create` and `tax.create` are honestly `degraded`: their
  company-scoped natural keys are not database-unique operation records and do
  not prove concurrent exactly-once creation. The other ten commands use
  deterministic target-state checks but no operation store.
- No persistent business write occurred. No business database, Odoo source,
  V2/V3 chain, or service configuration was modified, and this batch issued no
  service-restart command. At 2026-08-27 10:25:26 the existing Odoo main process
  crossed its configured 2 GiB VMS soft limit and initiated a phoenix reload.
  `_reexec()` resolved basename `python` outside the virtual environment, failed
  to import the venv-only `passlib`, and exited; the existing systemd
  `Restart=always` policy recovered the service at 10:25:38. Logs show the same
  daily-pattern operational defect on prior dates. The current batch contains no
  service-control, signal, package-install, or persistent `PYTHONPATH` path; the
  defect was documented and deliberately left outside this capability batch.

## Previous completed batch: eleven partner master-data capabilities

Implemented and dual-database live-verified:

1. `partner.search`
2. `partner.get`
3. `partner.create`
4. `partner.update`
5. `partner.archive`
6. `partner.restore`
7. `partner.accounting.update`
8. `partner.bank_account.create`
9. `partner.bank_account.update`
10. `partner.bank_account.archive`
11. `partner.bank_account.restore`

The batch uses closed request/response schemas and fixed allowlisted ORM paths
over `res.partner` and `res.partner.bank`. Partner and bank-owner company scope,
Odoo ACLs, exact write confirmation, and both isolation-database boundaries
remain in force. The live smoke temporarily linked
`base.group_partner_manager` to the configured test user inside its rollback-
only transaction; that is test authorization, not a claim that the default
runtime user already has partner-manager access.

### Verification

- Final post-fix partner selection: 98 passed, with the guarded local live case
  skipped because it was not authorized locally.
- Complete local regression: 3,060 passed, 139 explicitly gated live tests
  skipped, zero failed, in 1,687.53 seconds (28:07).
- Synchronized server-focused selection: 428 passed in 84.24 seconds.
- Post-sync server registry evidence selection: 24 passed in 81.97 seconds.
- One shared guarded smoke covered all eleven commands, first execution, and
  immediate replay in both `odoo_cli_v4_dev` and `odoo_cli_v4_e2e` as configured
  uid 5/company 1; pytest recorded `1 passed in 7.03s`.
- Whole-transaction rollback and fresh-cursor checks proved zero residual
  partner, bank-account, or temporary user-group rows.
- Live success-path evidence: 109 reads and 58 writes.
- Capability-ID-list SHA-256:
  `c42bdb67c1a540293d91ef5e84d1a4e0291a36a2b5eb8e7261660cf73dc7238a`
- Registry-file SHA-256:
  `5583f4b43a7532774b3e8c3365205321b6ed38be8fc9aaaafc4868d1a3fae181`
- Final source archive: 199107 bytes; SHA-256
  `f6364dadeb9fe53a91cc52685b52218e4f546da8863701a972a60ffcc9203c8c`.
  Its 42 entries are byte-identical to the final active-tree files, with no
  duplicate or backslash-named entries.
- Clean wheel: 622561 bytes; SHA-256
  `dce638bc8e9b15a60e39f6045868ff277be4545ef52697bf283da065fac38388`.
  It contains 414 entries, 343 schemas, all 190 capabilities, and all 169
  handlers, with no duplicate or backslash-named entries.
- `partner.create` is honestly `degraded`: its visible `ref` marker is not
  database-unique and does not prove concurrent exactly-once creation. The
  other eight writes use deterministic target-state rechecks but no operation
  store; an old request may act again after an intervening state change.
- Isolated Odoo without the optional `phone_validation` module has no stored
  `res.partner.mobile` field. Reads retain the stable `mobile: null` response;
  writes accept null/omission and fail closed for a non-null mobile value.
- This batch issued no service restart and modified no business database, Odoo
  source, or V2/V3 chain. A later 2026-08-27 06:23 Odoo restart was traced to
  `apt-daily-upgrade`/`needrestart` after an OpenSSL upgrade; the service stopped
  cleanly, and the audit found no V4 deployment relation.

## Previous completed batch: nine analytic/budget writes

Implemented and dual-database live-verified:

1. `analytic.account.create`
2. `analytic.account.update`
3. `budget.create`
4. `budget.update_draft`
5. `budget.lines.replace`
6. `budget.confirm`
7. `budget.reset_to_draft`
8. `budget.cancel`
9. `budget.mark_done`

The batch uses fixed public contracts and allowlisted ORM actions over
`account.analytic.account`, `budget.analytic`, and `budget.line`. The four budget
lifecycle commands invoke native Odoo transitions. Ordinary-user ACL,
uid/company scope, exact confirmation, deterministic replay checks, and the two
isolation-database boundaries remain in force; no generic model, field, or
method dispatcher was added.

### Verification

- Focused local selection: 386 passed.
- Synchronized server-focused selection: 386 passed.
- Final server runtime selection: 79 passed.
- Complete local regression: 2,926 passed, 138 explicitly gated live tests
  skipped, zero failed, in 1,927.74 seconds.
- One shared guarded smoke covered all nine commands in both
  `odoo_cli_v4_dev` and `odoo_cli_v4_e2e` as configured uid 5/company 1. Every
  command executed once and then returned an immediate deterministic replay;
  pytest recorded `1 passed in 6.09s`. Whole-transaction rollback and a fresh
  cursor proved zero residual analytic accounts, budgets, and budget lines.
- Live success-path evidence: 107 reads and 49 writes.
- Capability-ID-list SHA-256:
  `41d06b41aa49596ad0f67d9c343761af0918c68c902c1046bcf0d1684e2ddcda`
- Registry-file SHA-256:
  `72b03d16135e337c2407b05aa77df265c143c8f6f95e3a6a75ece2fffbc225dd`
- Synchronized source archive: 132872 bytes; SHA-256
  `18e0c881861e770754ccca8e055f804e0cd0d464d0f6d9678c4f72ad6db24ea1`
- Clean wheel: 595273 bytes; SHA-256
  `b93dd572f61d07953645b300c67a846b565af1514d90dab8ad8a3970b15e341e`.
  It contains 392 entries, 321 schemas, all 179 capabilities, and 158 handlers,
  with no backslash-named entries.
- Two historical Windows backslash-name duplicate sets were moved recoverably
  out of the active tree: 36 schema-name duplicates to
  `/tmp/odacv4-malformed-schema-names-20260826` and 28 project-name duplicates
  to `/tmp/odacv4-malformed-project-names-20260826`. The active tree contains
  zero such names.
- `analytic.account.create` and `budget.create` are `degraded`: visible markers
  are not database-unique and do not prove concurrent exactly-once behavior.
  The other seven writes have deterministic keys and current/target-state
  rechecks but no operation store; an old request may execute again after an
  intervening state change.
- No business database, Odoo source, V2/V3 chain, or service was modified or
  restarted.

## Previous completed batch: ten payment/bank reconciliation capabilities

Implemented and dual-database live-verified:

1. `bank.transaction.search`
2. `bank.transaction.reconciliation.get`
3. `bank.transaction.match_candidates.list`
4. `payment.create`
5. `payment.update_draft`
6. `payment.reset_to_draft`
7. `bank.transaction.update`
8. `bank.transaction.match`
9. `bank.transaction.unmatch`
10. `reconciliation.write_off`

The three reads and seven writes use fixed public contracts and allowlisted ORM
actions. Payment draft reset and bank matching/unmatching/write-off delegate to
the corresponding native Odoo paths; no generic model, field, or method
dispatcher was added. Ordinary-user ACL, uid/company scope, exact write
confirmation, idempotency, and isolation-database boundaries remain in force.

### Verification

- Focused local selection: 72 passed.
- Complete local regression: 2802 passed, 137 opt-in live tests skipped.
- Synchronized server-focused selection: 72 passed.
- One shared guarded smoke covered both `odoo_cli_v4_dev` and
  `odoo_cli_v4_e2e` as configured uid 5/company 1 and recorded `1 passed in
  10.78s`. Whole-transaction rollback and a fresh cursor proved that its
  temporary payment, invoice, and bank-transaction fixtures were absent.
- Capability-ID-list SHA-256:
  `d7685dbfd2461eb436593566ece52efdbf0120fbea00aeeceafed864e54c120e`
- Registry-file SHA-256:
  `95a41290f9feb72e3b786247834a131635ca003144b4bdd0c766f5d69cfef618`
- Synchronized source archive: 574618 bytes; SHA-256
  `cae7e6fe2aff2f27751282803d1cf2daeb80f149388450186f0d13136a5fe994`
- Clean wheel: 574779 bytes; SHA-256
  `e5c185984a198fda856b1caa921373e91e4a3c2d4ee8c3c0dfd28fb37315fc09`.
  It contains 303 schemas and all 170 capabilities, with no backslash-named
  entries.
- No business database, Odoo source, V2/V3 chain, or service was modified or
  restarted.

## Previous completed batch: eight document-lifecycle writes

Implemented and dual-database live-verified:

1. `invoice.update`
2. `invoice.lines.replace`
3. `invoice.cancel`
4. `invoice.reset_to_draft`
5. `journal_entry.update`
6. `journal_entry.lines.replace`
7. `journal_entry.cancel`
8. `journal_entry.reset_to_draft`

The update contracts expose only fixed business fields. Full-line replacement
is atomic and accepts a complete balanced target rather than unsafe per-line
mutations; invoice replacement rejects sales- or purchase-linked source lines.
Cancel and reset call native `button_cancel()` and `button_draft()` rather than
writing `state`. Every path retains exact company scope, the configured ordinary
accountant, Odoo ACLs, exact confirmation, and deterministic replay behavior.

### Verification

- Final focused local selection: 326 passed in 178.43 seconds.
- Final complete local regression: 2732 passed, 136 opt-in live tests skipped
  in 598.63 seconds.
- Targeted lint and format checks: passed.
- Synchronized server-focused selection: 326 passed in 302.59 seconds.
- One guarded transactional smoke covered both `v4-dev` and `v4-e2e` and
  recorded `1 passed in 10.10s`. It exercised the eight new commands, existing
  create/post prerequisites, immediate replay, and the technical-marker
  migration, taking retained evidence to 104 reads and 33 writes.
- Capability-ID-list SHA-256:
  `a9ef0676628249f342fbdf580f85fdca85d4bb1e68e8f48fd026b2627fb43b47`
- Registry-file SHA-256:
  `71398c69324d16a26a3b5efa79577197a3db51c495f3d3726a0ecde9e20e2ee9`
- Verified wheel SHA-256:
  `b3e6be281ef21dad90bc96994e09d9acf9360648a4a1dffddeca268d63ea3ba5`

### Evidence and limits

- Both aliases used company 1 and configured uid 5. Each alias created one
  customer invoice, one vendor bill, and one journal entry through the public
  write contract, then exercised draft updates, complete line replacement,
  posting, native reset/cancel, and replay.
- New creates left `ref` available for business references. Replaying the same
  create after assigning a business reference still returned the original
  move. Legacy marker compatibility remains covered by unit tests.
- Each alias used one outer transaction. Whole-transaction rollback and a
  fresh superuser cursor proved all created move IDs absent.
- No persistent business write occurred, and no Odoo, Nginx, PostgreSQL, Pi,
  V2, or V3 service was restarted or modified.

## Previous completed batch: eleven analytic/budget reads

Implemented and dual-database live-verified:

1. `analytic.line.search`
2. `analytic.line.get`
3. `analytic.distribution_model.list`
4. `analytic.distribution_model.get`
5. `analytic.applicability.list`
6. `analytic.applicability.get`
7. `budget.search`
8. `budget.get`
9. `budget.line.list`
10. `budget.line.get`
11. `report.budget`

The first ten reuse the fixed core-object read contract and real Odoo ORM
models. `report.budget` is deliberately separate because Odoo 19
`budget.report` is SQL-backed and can emit the same text `aal{id}` row key once
for each overlapping budget line. Its fixed composite cursor includes date,
row key, budget-line ID, line type, source model, and source ID, preserving both
rows without exposing a generic model, method, or SQL dispatcher.

### Verification

- Final focused local selection: 825 passed, 2 guarded live cases skipped in
  96.40 seconds.
- Final complete local regression: 2651 passed, 135 opt-in live tests skipped
  in 553.11 seconds.
- Targeted lint and format checks: passed.
- Draft 2020-12 validation: all 267 canonical schema documents passed.
- Synchronized server-focused selection: 825 passed in 164.16 seconds.
- Guarded transactional live smoke across `v4-dev` and `v4-e2e`:
  `2 passed in 7.54s`, covering all eleven commands and taking retained
  evidence to 104 read and 25 write success paths.
- Registry capability-ID SHA-256:
  `f06fde8711e20a7e4a2853301707e946bb49fe38aec65dcb6c836e14d96de46b`
- Verified wheel SHA-256:
  `0f2f8c3ae75c0a0c8c07e88322bdab0e7a8381df0f2db11e8c4f34d153de729f`

### Evidence and limits

- Both aliases used company 1 and configured uid 5. Temporary analytic
  account/line, distribution model, applicability rule, budget, and two
  overlapping budget lines existed only inside one transaction. A fresh cursor
  verified complete rollback.
- The live report returned two rows for the same analytic line under the two
  budget lines and exercised one-item pagination, proving the composite cursor
  does not merge repeated official row keys.
- Independent audit found one pre-server defect: report filtering required
  exact plan membership. It now follows Odoo's `plan_id child_of` semantics;
  regression coverage accepts a child-plan account under its root and rejects
  a sibling-plan account. No other blocker remained.
- Empty analytic-distribution allocations are accepted because they are valid
  in the real Odoo model; the response does not invent allocations.
- The server schema directory also contains 36 legacy malformed duplicate JSON
  filenames from an earlier transfer. They predate this batch, are not registry
  targets, and were not deleted during capability work; at that checkpoint the
  canonical registry resolved exactly 267 schemas.
- No persistent business write occurred, and no Odoo, Nginx, PostgreSQL, Pi,
  V2, or V3 service was restarted or modified.

## Previous completed batch: eight payment/reconciliation object reads

Implemented and dual-database live-verified through the fixed core-object read
contract:

1. `partner.bank_account.search`
2. `partner.bank_account.get`
3. `bank.statement.search`
4. `bank.statement.get`
5. `reconciliation.partial.list`
6. `reconciliation.partial.get`
7. `reconciliation.full.list`
8. `reconciliation.full.get`

These four collection/search and exact-ID pairs close the object-inspection
side of existing payment, bank-transaction, and reconciliation writes. They
reuse fixed schemas, Odoo ORM models, configured uid 5, ordinary-accountant
read ACLs, company scope, and the existing keyset cursor. Partial and full
relations are normalized and cross-checked; no arbitrary model/method
dispatcher was added.

### Verification

- Final focused local selection: 618 passed in 77.48 seconds.
- Complete local regression: 2444 passed, 133 opt-in live tests skipped in
  492.22 seconds.
- Synchronized server-focused selection: 618 passed in 134.89 seconds.
- Guarded transactional live smoke across `v4-dev` and `v4-e2e`:
  `2 passed in 6.80s`, covering all eight commands and taking retained evidence
  to 93 read and 25 write success paths.
- Registry capability-ID SHA-256:
  `9d0dd71415220c7a05e6a1e600f56d811459c978d840aee91d14cb94b6af66c6`
- Verified wheel SHA-256:
  `20c663f1637c35c0433d08c364b920c784296f3854e21cddc0cc96217c2c7c85`

### Evidence limits

- Both isolated databases initially had no partner-bank or bank-statement rows.
  Each smoke worker created a marker partner, bank account, and statement only
  inside one transaction, then rolled back. A fresh cursor proved all three
  markers absent and the selected pre-existing bank line restored to an
  unbound statement state.
- Partial and full reconciliation reads used existing positive records in each
  isolated database; normalization verified all returned relations remained in
  company 1.
- No persistent business write occurred, and no Odoo, Nginx, PostgreSQL, Pi,
  V2, or V3 service was restarted or modified.

## Previous completed batch: eight accounting-configuration reads

Implemented and dual-database live-verified through the fixed core-object read
contract:

1. `payment.method.get`
2. `reconciliation.model.get`
3. `cash_rounding.list`
4. `cash_rounding.get`
5. `journal.group.list`
6. `journal.group.get`
7. `incoterm.list`
8. `incoterm.get`

The two exact-ID commands close existing payment-method and reconciliation-
model list surfaces. Cash rounding, journal groups, and incoterms add three
closed collection/exact-ID pairs. They reuse fixed schemas, ORM models,
configured-user/company scope, ordinary-accountant read ACL gates, and the
existing keyset cursor contract; they do not expose arbitrary model or method
dispatch.

### Verification

- Final focused local selection: 484 passed in 86.71 seconds.
- Complete local regression: 2310 passed, 131 opt-in live tests skipped in
  526.90 seconds.
- Synchronized server-focused selection: 484 passed in 124.70 seconds.
- Guarded transactional live smoke across `v4-dev` and `v4-e2e`:
  `2 passed in 6.41s`, covering all eight commands and taking retained evidence
  to 85 read and 25 write success paths.
- Registry capability-ID SHA-256:
  `91dc2d269fd70d4b0badfae1e0a255750a9201ffb6c1194f013672503256fb64`
- Verified wheel SHA-256:
  `bf280a27dac85f681f2fd9767f771d68f08d7f3507c8b71cabafa8efc3206476`

### Evidence limits

- Cash-rounding and journal-group rows were absent in the isolated databases,
  so the live smoke created marker fixtures only inside its guarded transaction.
  The whole transaction was rolled back, and a fresh cursor proved zero
  residue; no persistent business write occurred.
- Payment-method, reconciliation-model, and incoterm reads used the existing
  isolated-database data visible to configured uid 5.
- No Odoo, Nginx, PostgreSQL, Pi, V2, or V3 service was restarted or modified.

## Previous completed batch: twelve reference-object reads

Implemented and dual-database live-verified through the fixed core-object read
contract:

1. `product.search`
2. `product.get`
3. `analytic.plan.list`
4. `analytic.plan.get`
5. `analytic.account.search`
6. `analytic.account.get`
7. `fiscal_position.search`
8. `fiscal_position.get`
9. `account.tag.list`
10. `account.tag.get`
11. `tax.group.list`
12. `tax.group.get`

These are six closed collection/search and exact-ID pairs. They reuse fixed
schemas, ORM models, company/configured-user scope, ordinary-accountant read
ACL gates, and the existing keyset cursor contract; they do not expose arbitrary
model or method dispatch.

### Verification

- Focused local selection: 382 passed in 78.94 seconds.
- Final complete local regression: 2208 passed, 129 opt-in live tests skipped
  in 827.35 seconds.
- Synchronized server-focused selection: 382 passed in 118.32 seconds.
- Guarded transactional live smoke across `v4-dev` and `v4-e2e`:
  `2 passed in 6.71s`, covering all twelve commands and taking retained
  evidence to 77 read and 25 write success paths.
- The first live run exposed the legitimate Odoo value `categ_id=False`.
  Product `category` normalization and schema now accept either a named
  reference or `null`, and the repeated live run passed.
- Registry capability-ID SHA-256:
  `cd8d1f5672ec9d779875389c00ec3276a890927cb5b5543a67ed840cf714736d`
- Verified wheel SHA-256:
  `a7f5e50cde6b10bd75c515463db3bc57387c845bc3afa3941cd52f625a123f96`

### Evidence limits

- The public capabilities are reads, but the live smoke created temporary
  product, analytic-account, and fiscal-position fixtures inside its guarded
  transaction. The whole transaction was rolled back, and a fresh cursor
  proved zero residue; no persistent business write occurred.
- No Odoo, Nginx, PostgreSQL, Pi, V2, or V3 service was restarted or modified.
- The temporary product proves `product.search` and `product.get`; it does not
  supply the missing positive accounting-property mapping fixture for
  `product.accounting_profile.get`.

## Earlier completed batch: twelve core-object reads

Implemented and dual-database live-verified through the public fixed `read`
contract:

1. `account.account.get`
2. `journal.get`
3. `tax.get`
4. `payment_term.get`
5. `currency.get`
6. `partner.accounting.get`
7. `bank.transaction.get`
8. `journal_item.search`
9. `journal_item.get`
10. `payment.method.list`
11. `reconciliation.model.list`
12. `report.bank_reconciliation`

The first eleven commands share the closed core-object read path: eight exact
ID gets, two support-object lists, and one filterable journal-item search.
`report.bank_reconciliation` reuses the typed financial-report path but
requires an explicit company-scoped bank `journal_id`; that journal is also
bound into the pagination cursor.

### Verification

- Dedicated shared live smoke against `v4-dev`: passed in 154.45 seconds.
- Dedicated shared live smoke against `v4-e2e`: passed in 152.27 seconds.
- Clean full local regression: 2052 passed, 127 opt-in live tests skipped in
  1086.74 seconds.
- Synchronized server-focused selection: 258 passed in 110.05 seconds.
- The smoke established that Odoo 19 returns payment-term `days_next_month` as
  a numeric string. The response validator and schema now accept that validated
  representation, and both database smokes pass.
- This batch performed reads only. It made no database writes and did not
  restart or modify Odoo, Nginx, PostgreSQL, Pi, V2, V3, or their services.

### Evidence limits

- The live evidence covers the fixed company/user routing, ACL gates, response
  schemas, exact-ID behavior, pagination, and the bank-journal scope. It does
  not expand the capability surface into arbitrary model or method dispatch.
- Empty or sparse isolated-database fixtures remain valid success-path
  evidence only for the exact objects and reports returned by those fixtures.

## Earlier completed batch: nine writes

Implemented and verified through the public fixed `write run` contract:

1. `asset.cancel`
2. `asset.dispose`
3. `asset.pause`
4. `deferred_expense.generate_entries`
5. `deferred_revenue.generate_entries`
6. `multicurrency.revaluation.generate_entries`
7. `reconciliation.automatic.run`
8. `period.transfer.run`
9. `localization.china.period_transfer.run`

The three asset commands delegate to native asset lifecycle actions. The three
entry generators use the official deferred/revaluation handlers and return the
generated source/reversal move pair. Automatic reconciliation uses the fixed
native wizard for an exact company-scoped line set. Both transfer commands use
native transfer models; the China command additionally fails closed unless the
company has the China fiscal/chart context.

### Verification

- Complete local suite: 1854 passed, 125 opt-in live tests skipped in 434.28
  seconds.
- Synchronized server-focused suite: 301 passed in 149.06 seconds.
- Guarded shared live smoke: `1 passed in 10.46s`. Inside that one test, all
  nine commands ran through the public contract in both `v4-dev` and `v4-e2e`,
  and every command was immediately replayed with the same result.
- The smoke rolled back its shared transaction. A fresh read-only cursor then
  proved the tracked assets, moves, and move lines absent and the temporarily
  changed deferred-company settings restored.
- No Odoo, Nginx, PostgreSQL, Pi, V2, or V3 service was restarted or changed.

### Evidence limits

- The live cancel/dispose fixtures use zero-value assets, so they prove native
  lifecycle state transitions but not non-zero depreciation reversal or
  disposal gain/loss accounting.
- Odoo does not persist the requested pause date on a stable asset field.
  `asset.pause` therefore treats the native `paused` terminal state as replay
  evidence and is marked `degraded` with
  `odoo_asset_pause_date_not_persisted`.
- Deferred/revaluation move-pair markers and transfer markers prevent ordinary
  sequential replay, but they are not database-unique under concurrent calls.
  Those five capabilities are marked `degraded`; exactly-once concurrency is
  not claimed in this capability-first phase.
- `asset.modify` and `asset.resume` remain disabled because the server's
  `exchange_currency_rate` add-on hits its multiple-depreciation-move singleton
  defect on the required non-zero path. No ACL bypass, add-on edit, or service
  change was used.

## Earlier completed batch: nine reads

Implemented and dual-database live-verified:

1. `report.deferred_expense`
2. `report.deferred_revenue`
3. `report.multicurrency_revaluation`
4. `report.china.balance_sheet`
5. `report.china.profit_and_loss`
6. `report.china.cash_flow`
7. `report.singapore.gst`
8. `fiscal_position.resolve`
9. `diagnostic.journal_integrity.inspect`

The seven reports reuse the closed typed-report request/response and pagination
path. They resolve fixed official XML IDs; no database record ID is hard-coded.
CN reports are guarded by fiscal country `CN` plus chart `cn_oscg`, and SG GST
by fiscal country `SG` plus chart `sg`.

Fiscal-position resolution delegates to Odoo's `_get_fiscal_position` and,
when requested, `map_account`/`map_tax`. Journal integrity delegates to
`res.company._check_hash_integrity`; V4 does not reimplement hash calculation.

### Verification

- Focused local tests: 169 passed (final post-registry-conflict rerun).
- Full local suite: 1747 passed, 124 skipped in 512.79 seconds.
- Synchronized server-focused suite: 169 passed in 154.64 seconds.
- Final server registry suite after the last sync: 13 passed in 33.09 seconds.
- Shared live smoke: 18 passed in 135.97 seconds (nine commands × two aliases).
- Retained live log:
  `/opt/odoo-accounting-cli-v4/.tooling/remaining-read-batch-live-e8026729-6c8d-401d-8b41-8a6dcfb919f8.log`
- Log SHA-256:
  `e342e93c397d12549b432f08e4720661d4ac9e7d360d679c0977fc6a0be4bf81`

No write smoke or service restart was used for this batch.

### Evidence limits

- Deferred expense, deferred revenue, and multicurrency revaluation currently
  return valid empty reports in both isolated databases.
- Partner ID 1 currently resolves to no fiscal position; optional account/tax
  mappings have unit coverage but no positive live mapping fixture.
- Journal integrity currently returns an empty result because there are no
  hashed moves.
- The localized report fixtures are non-empty in each database: CN balance
  sheet 66 lines, CN profit and loss 16, CN cash flow 32, SG GST 28.

## Read candidates deliberately not implemented in that batch

- `report.bank_reconciliation` was deliberately deferred from that earlier
  batch because the official handler requires a specific bank journal and
  otherwise falls back to the first one. The core-object read batch has now
  implemented it with required company-scoped `journal_id` validation and
  cursor binding.
- `validation.period_close.check`: Odoo 19 has no native composite readiness
  API matching the current descriptor. The native lock-date wizard checks only
  narrower draft/tax conditions and requires a target date.
- `operation.status.get` / `operation.audit.get`: there is no V4 operation
  store or Odoo model/table. Implementing these now would prematurely build the
  later control plane.
- Singapore compliance reads: uid 5 lacks the compliance ACL and both isolated
  databases contain no compliance rows.
- `compliance.singapore.registration.verify`: the frozen registry is wrong;
  the real operation is a manager-only write that updates verification state
  and creates an audit event. Re-freeze it as a write before implementation.
- `localization.china.voucher.render`: requires a binary/PDF contract and the
  server currently lacks `cn2an`, leaving amount-in-words incomplete.
- `invoice.singapore.pint.export`: the native builder works, but the current SG
  invoice fixture has three validation errors and the binary/XML response
  contract is not frozen.
- China/Singapore configuration inspectors were deferred in that earlier batch;
  the current batch implements them after freezing genuinely localization-
  specific readiness outputs.

## Remaining disabled IDs

Reads (8, noting that registration verification is misclassified in the
current frozen registry):

- `compliance.singapore.filing.list`
- `compliance.singapore.findings.list`
- `compliance.singapore.registration.verify`
- `invoice.singapore.pint.export`
- `localization.china.voucher.render`
- `operation.audit.get`
- `operation.status.get`
- `validation.period_close.check`

Writes (9):

- `asset.modify`, `asset.resume`
- `compliance.singapore.assessment.run`
- `compliance.singapore.filing.prepare`
- `compliance.singapore.filing.submit`
- `currency.rate.record`
- `inventory.valuation.adjust`
- `period.adjustment.create`
- `period.lock.change`

## Recommended next checkpoint

Do not assume that 289 registered IDs are sufficient, and do not force the
remaining 17 disabled descriptors merely to increase the count. The current
sales-invoice/stock-transfer checkpoint is complete, as are the preceding
specialist/localized report-export, configuration/readiness, and order-write
checkpoints, but this is not a claim that the overall
library is complete. Select the next coherent 8-12-command high-frequency
cluster from verified remaining workflow gaps, freeze it against native Odoo
models, ordinary-user ACL, company scope, and one shared isolated rollback
smoke, and do not start the later approval/control plane early.

The previously recommended payment/bank-cash-application, analytic/budget,
partner master-data, basic accounting-configuration, accounting-depth,
management-reporting/period-context, and account-return/journal-analysis
clusters, plus the operational-inventory, sales/purchase order read/write, and
all 19 currently selected native report-export paths, are complete. Re-audit
the installed module/workflow/lifecycle matrix before choosing the next batch;
do not select work merely from the command count or the 17 disabled descriptors.

Period locking should not displace the next ability batch merely to consume
disabled IDs:
the configured uid 5 is not an accounting manager, and the audited native lock/
adjustment paths do not safely match the frozen descriptors. Keep genuinely
blocked descriptors disabled; do not use `sudo`, service changes, add-on edits,
or weakened validation merely to inflate the count.

## 2026-08-31 operational accounting read checkpoint (latest)

This checkpoint adds twelve pure-accounting reads and supersedes the older
command-count snapshots above:

1. `invoice.duplicate_candidates.list`
2. `invoice.tax_breakdown.inspect`
3. `recurring.journal_entry.search`
4. `recurring.journal_entry.get`
5. `account.transfer_model.search`
6. `account.transfer_model.get`
7. `partner.credit_exposure.inspect`
8. `journal.sequence_irregularity.list`
9. `account.lock_exception.search`
10. `account.lock_exception.get`
11. `report.external_value.search`
12. `report.external_value.get`

The exact registry closure is now 345 capability IDs: 330 enabled, including
200 reads and 130 writes, plus 15 disabled. Statuses are 297 `unconfigured`,
33 `degraded`, and 15 `disabled`; the registry references 665 schema files.
The sorted ID-list SHA-256 is
`79e2fb08cf06789c3689f536a1c447f5b936413810de63df7ef0d3a51b677c8c`,
the canonical registry digest is
`28a6c7249a106bd3fd8ca38147e489761e72431e17eb0180d063277521140dea`,
and the registry-file SHA-256 is
`fc2b8634fee7572c259233ca915e14988383fa6eb3b41852b0c165608f3b357e`.

Focused local regression passed 1006 tests. The post-smoke local registry
selection passed 24 tests. The synchronized server regression also passed
1006 tests, followed by 24 post-status registry tests. The single shared live
smoke passed in 497.83 seconds and covered every new command in both
`odoo_cli_v4_dev` and `odoo_cli_v4_e2e` as ordinary accounting user uid 5.
It performed reads only. Local/server SHA-256 values matched for all 40 files
in the exact deployment manifest.

The pre-deployment targeted backup is retained at
`/opt/odoo-accounting-cli-v4/.tooling/accounting-operational-reads-20260831-9f7d2a1c/overwritten-files.tgz`
with SHA-256
`314d3407e5a860f533b889309f8fd28f313910c49384ec937b34196ff81c86fb`.
Odoo remained active with `MainPID=1678372`, `NRestarts=2`, and
`ActiveEnterTimestamp=Sun 2026-08-30 10:25:07 CST`; this checkpoint issued no
service restart or control command.

Review fixed three correctness issues before live verification: partner credit
exposure no longer reads Odoo's cross-company/bypass-access DSO computation;
a missing source invoice now returns `record_not_found`; and external report
value commands preserve their real record IDs in CLI audit metadata. Registry
source/ACL provenance was also aligned with the partner and currency models
used by duplicate-invoice normalization.

Inventory logistics are outside this accounting batch. Existing
`stock.delivery_slip.pdf.export`, `stock.picking_operations.pdf.export`, and
`stock.return_slip.pdf.export` commands are not counted as accounting coverage,
and no new stock or picking capability was added here. Do not interpret the
345 total registry IDs as proof of complete accounting coverage; continue with
the next verified 8-12-command accounting gap rather than command-count
inflation or the deferred control plane.

## 2026-08-31 accounting supporting-object checkpoint (latest completed batch)

This batch adds ten pure-accounting reads. It does not add stock, picking,
sales-order, or purchase-order capabilities:

1. `asset.group.search`
2. `asset.group.get`
3. `report.budget_definition.search`
4. `report.budget_definition.get`
5. `report.budget_item.search`
6. `report.budget_item.get`
7. `tax.unit.search`
8. `tax.unit.get`
9. `account.return.account_status.search`
10. `account.return.account_status.get`

The exact registry closure is 355 capability IDs: 340 enabled, including
210 reads and 130 writes, plus 15 disabled. Statuses are 307 `unconfigured`,
33 `degraded`, and 15 `disabled`; there are 685 public schema files. These
totals include earlier non-accounting capabilities and are not a percentage
of complete accounting coverage. This supporting-object batch must not be
presented as another high-frequency core-workflow breakthrough.

Implementation, independent review, and targeted regressions are complete:
1042 local tests and the same 1042 server tests passed (889 focused tests plus
153 existing core-object CLI regressions). After the smoke status was recorded,
the focused registry/CLI metadata selection passed another 15 tests locally and
15 on the server. Ruff and diff checks passed. The
initial deployment contained exactly 36 files; local/server SHA-256 manifest
digests matched at
`a9804362f797d56576c45d23e45973e4d9fa673017ea7401d855077eaf02067c`.
After recording the smoke result, the final 36-code-file manifest digest is
`5ef93ec319e23f091fc7696a1fc6899beab6c1e5b4d9674ea11c2d09ebc0648d`.
The sorted ID-list SHA-256 is
`19ebbf7a41194146c4e89056ca81eab166fc2c23af4984b4c4d9dd9c86e47a72`,
the canonical registry digest is
`e327439190b9521cfc16e5a05c8cbf77822a21c2d0dfe067aa728157f518d702`,
and the registry-file SHA-256 is
`21b6a57b0bd3b7f17432663de5c82c25b0d63a38c8c9ed6bad2e58732c75572e`.

The server retained a targeted backup of the twelve overwritten files at
`/opt/odoo-accounting-cli-v4/.tooling/accounting-supporting-reads-20260831-a5e2b90d/overwritten-files.tgz`,
SHA-256
`2304fc42b5da06bab6699fc0bf384c57bff8f16c214fbb84679de90df9aa0e10`.
The other twenty-four deployment files were new. Do not replace the server
checkout wholesale: it still has the older Git HEAD plus accumulated deployed
files, while the local/GitHub checkpoint is the source-control baseline.
The four-file evidence/handoff update also has a pre-update backup at
`/opt/odoo-accounting-cli-v4/.tooling/accounting-supporting-reads-20260831-a5e2b90d/metadata-before.tgz`,
SHA-256
`f659f32429b0ade0c46b47c365a674832af478a55223e3ef4fa299c61ec03ea4`.

The single shared read-only smoke passed in 382.14 seconds as uid 5 against
exactly `odoo_cli_v4_dev` and `odoo_cli_v4_e2e`. Its durable result files are:

- `/opt/odoo-accounting-cli-v4/.tooling/accounting-supporting-reads-20260831-a5e2b90d/live-smoke.log`
- `/opt/odoo-accounting-cli-v4/.tooling/accounting-supporting-reads-20260831-a5e2b90d/live-smoke.exit`

The exit file contains `0` and the log reports `1 passed in 382.14s`.
The log SHA-256 is
`0f3fdcc479703327cd16a7948e01cc0e787056f5c8ea3796f9223d087eac2ce9`.
The first SSH-attached attempt lost its output connection; only that exact
test process group was terminated before the logged retry.
No business service was stopped or restarted. Odoo19 remained active with
`MainPID=1678372`, `NRestarts=2`, and
`ActiveEnterTimestamp=Sun 2026-08-30 10:25:07 CST`.

Review corrections included preserving native empty audit-account status as
`null` (not `todo`), accepting an unnamed asset group, aligning nullable
status filters and unbounded native VAT text with schemas, preserving verified
audit context for missing `get` records, and including only the selected
`company_id` in tax-unit output for contract-level company validation. No
member-company details or ACL bypass were introduced.

Both isolated databases currently have zero rows in these five object types.
The live smoke therefore verifies real model/field availability, ordinary-user
ACL, company domains, empty pages, and missing-record behavior. It cannot prove
populated-row normalization or the native `count_linked_assets` and
`fpos_synced` computations. Those paths have source review and unit coverage,
but populated live fixtures remain an explicitly unverified boundary.

### Next highest-value work

The invoice/bill, journal-entry, payment, and reconciliation command chains
already cover the ordinary daily workflow at code level. Prefer a complete
pure-CLI acceptance flow next (customer invoice, partial payment, final payment,
bank match; supplier bill and payment; adjustment journal and reversal), checking
residual amounts and trial-balance consistency. Reuse the existing core-write
and payment/bank shared tests rather than registering more supporting objects
solely to increase the count.

Two conditional gaps remain explicit:

- `period.lock.change` is disabled, so final period locking is not yet an
  end-to-end CLI action. Native locking requires an accounting manager; uid 5
  must not be elevated or bypassed to force it through.
- The missing `deferred_start_date` / `deferred_end_date` line parameters
  identified at this checkpoint are addressed by the later deferred-date
  checkpoint below. The older extended-write fixture still sets them through
  ORM; it is not evidence of a fully CLI-driven date-entry workflow.

`period.adjustment.create` is not a reason to duplicate functionality: ordinary
`journal_entry.create`, `journal_entry.post`, and `journal_entry.reverse` already
provide the manual adjustment route. These are source/contract audit findings,
not a claim that a fresh end-to-end business acceptance run has passed.

## 2026-08-31 accounting-core workflow acceptance (configuration blocked)

This checkpoint adds no capability IDs, schemas, or production handlers. It
upgrades `tests/integration/test_payment_bank_capability_batch_live.py` to run
24 existing public CLI capabilities through `cli.main`, normal Odoo ports, and
the real ORM dispatcher in one rollback-only business transaction per alias.
It does not claim cross-process CLI/bridge transport or durable commit/replay
coverage. Read-only ORM access selects existing master data and audits rollback;
all test business records are created and changed through public CLI commands.

The shared smoke retains standalone-payment lifecycle and bank
match/unmatch/write-off checks, and adds these accounting-only workflows:

- Customer invoice 100: post, collect 40 (residual 60), collect 60 (residual 0),
  record a bank deposit of 100, match the two payments' outstanding-receipt
  lines, and verify the invoice and both payments are paid/matched.
- Supplier bill 80: post and pay 80, then verify zero payable residual. This
  does not include the subsequent bank-outflow match; `in_payment` is allowed.
- Adjustment 25: post and reverse through public CLI commands, posting the
  reversal when necessary; verify balanced entries and a zero combined balance
  on each affected account.
- Trial balance: compare the report before and after those three new workflows,
  excluding the two legacy scenarios. Period debit and credit must each
  increase by 510; opening and closing total net balances remain zero.

Every write is immediately replayed with the same key. The two partial receipts
use separate explicit keys. The worker tracks payments, moves, move lines,
bank statement lines, and partial/full reconciliations, including automatically
created related records. It rolls back on both success and failure and checks
the tracked IDs and run marker from a fresh cursor. The readonly cleanup audit
uses the existing superuser verifier; business execution remains uid 5/company 1.

Local regression evidence: 564 core-write/bank tests passed in 798.03 seconds
and 40 CLI tests passed in 287.58 seconds. Four new tests for the fixture's
account-role precondition and test-only failure diagnostics also passed (608
local passes in total). Ruff, format, and diff checks passed;
the unconfigured live test correctly skipped (one skip, not a live pass).
Independent source/contract review found no blocking mismatch. The Odoo
interpreter lacks `jsonschema`; only the worker's `PYTHONPATH` includes the
project virtualenv dependencies. No package was installed in the running Odoo
environment and no runtime configuration or service was changed.

The server's previous test and handoff files were backed up before deployment:

- Backup: `/opt/odoo-accounting-cli-v4/.tooling/accounting-core-workflows-20260831-87c4e26a/overwritten-files.tgz`
- Backup SHA-256: `bd984ae6484db00945a98d5683486600c9a52dca5216b60d3025866b62dc33aa`
- Initial test SHA-256 (the failed live attempt): `53d90eaa26368452c19c58828c7a9b329b3a63915270a31357b2482d36f0a41a`
- Updated test SHA-256 (fail-fast precondition): `f4c6e8b453e414ad25aead38f3f81207c5f1f6abf4b9014f085c76bd9c41d770`
- New unit-test SHA-256: `3b30a0173b4b62e45eb65a4bcdfce037bc0997ef7293ca4ceba808bb99da0b98`

The updated test and new unit test were subsequently synchronized to the server
and both hashes were verified. Before that update, the failed-attempt test and
previous handoff were preserved in
`/opt/odoo-accounting-cli-v4/.tooling/accounting-core-workflows-20260831-87c4e26a/precondition-update-before.tgz`
(SHA-256 `98739255753edfeaf056acddb166a4169b510b1de96bf74a02926f622c041e34`).
The four new unit tests also passed on the server in 0.25 seconds. The live smoke
was not retried against the known invalid configuration. Odoo19 remained active
with `MainPID=1678372`, `NRestarts=2`, and the unchanged start timestamp
`Sun 2026-08-30 10:25:07 CST`; no service was restarted.

The first shared smoke failed in `odoo_cli_v4_dev` after 349.93 seconds;
`odoo_cli_v4_e2e` was not reached. The exit file contains `1`. Durable evidence is under
`/opt/odoo-accounting-cli-v4/.tooling/accounting-core-workflows-20260831-87c4e26a/`
(`live-smoke.log`, `live-smoke.exit`, and `live-smoke.pid`).
The failed-run log SHA-256 is
`dbd3480e6bf7cd4bdf5a55a481cc2266c5ab6f41fd3bd6b1b2bcfc31b8f56685`.

The two legacy scenarios and the trial-balance baseline completed in `v4-dev`.
The customer invoice was posted, receipts of 40 and 60 produced residuals of
60 and 0, and both outstanding receipt lines were returned as bank-match
candidates. Matching them together raised the public `business_rule_error`.
The transaction was rolled back and the fresh-cursor verifier detected no
surviving tracked records before the original failure was re-raised. Supplier
payment, adjustment/reversal, the final trial-balance delta, and the second
database are not successful live evidence from this attempt.

Subsequent public CLI reads (`journal.list`, `payment.method.list`, and
`journal.configuration.inspect`) confirmed the same configuration in both
isolated databases, with no alternative company-1 bank journal:

| Role | Configuration |
| --- | --- |
| Bank journal | 14 (`BNK1`) |
| Bank/liquidity account | 152 (`1003`) |
| Bank suspense account | 153 (`1004`) |
| Inbound manual payment method | 3, payment account 153 |
| Outbound manual payment method | 4, payment account 153 |

Native Odoo creates a counterpart line for each selected source. Its
`account.bank.statement.line._seek_for_lines` classifies lines by the journal's
default and suspense accounts, and `_synchronize_from_moves` rejects multiple
suspense lines. Thus the current shared outstanding/suspense configuration
cannot support this two-receipt matching scenario. This is not evidence that
normal multiple-source matching with distinct account roles is unsupported.
No production handler was changed or native constraint bypassed.

The test now rejects an outstanding account shared with either liquidity or
suspense before writing any business fixtures. It also retains native exception
causes for test diagnostics only; the production CLI's sanitized error output
is unchanged. Do not rerun expecting success until a separately authorized
fixture-configuration correction has been made. Do not elevate uid 5, split
the bank deposit, remove assertions, or use direct ORM business writes to force
this acceptance test through. The older draft-payment fixture still expects
outstanding account 153; review that expectation when approving configuration
changes rather than restoring the invalid shared-account setup.

Next action requires permission to correct only the two isolated test banks'
account-role configuration, without modifying business databases or promoting
the test user. Then rerun the unchanged six-scenario acceptance test and record
the actual result. Until then, the registry stays at 355 IDs and the full
accounting-core workflow acceptance remains incomplete.

## 2026-08-31 deferred invoice dates (native add-on blocks live acceptance)

This batch closes an accounting input/readback gap without increasing the
registry: 355 IDs, 340 enabled handlers, and 685 schema files remain unchanged.
The registry file SHA-256 remains
`21b6a57b0bd3b7f17432663de5c82c25b0d63a38c8c9ed6bad2e58732c75572e`.

Five existing writes now accept optional line-level `deferred_start_date` and
`deferred_end_date`: `customer_invoice.create`, `vendor_bill.create`,
`invoice.lines.replace`, `customer_credit_note.create`, and `vendor_refund.create`.
Three request schema files cover all five through the existing refund references.
The dates must either both be omitted, both be null, or both be ISO dates with
start <= end. Same-day and pre-invoice-date periods are allowed. Requiring an
explicit pair is a CLI choice, not an Odoo restriction: native Odoo can infer
the start from invoice_date for an end-only input.

No defaults are injected into old requests or their idempotency fingerprints.
Line replacement/refund comparisons only compare deferred dates when the request
explicitly includes them. Thus an otherwise identical old request remains a
no-write replay even if the actual draft/posted record now has deferred dates.
Explicit null/null clears the dates; other full-line replacements retain their
existing semantics, so callers must include dates they want on replacement lines.
Existing draft-state, external sales/purchase-source, ACL, and company guards are
unchanged. No generic ORM write API or additional control plane was introduced.

`invoice.get` now returns both date fields for each line. They are read only
when present on the native model; otherwise they normalize to null. This does
not add an `account_accountant` prerequisite to all invoice reads. Read validation
checks each date independently, so existing end-only or unusual native records
are not rejected just because new CLI writes require a pair. Usage is in README.

Local evidence: the combined relevant contract/schema/runtime/bridge/CLI selection
passed 464 tests in 220.72 seconds; four shared helper/precondition tests also
passed. The opt-in live test correctly skipped without authorization (not a live
pass). After deployment, 311 focused schema/runtime/helper tests passed on the
server in 9.26 seconds. Ruff and diff checks passed.

Read-only native-source and database inspection confirmed existing company-1
configuration in both isolated databases: journal 11 (active/general), deferred
expense account 50 (asset_current), deferred revenue account 92
(liability_current), both generation methods `on_validation` and both computation
methods `month`. These settings were not changed. The native source is
`account_accountant/models/account_move.py` (date fields/constraints and automatic
generation). This batch tests automatic generation on invoice posting, not the
separate manual month-end generate commands.

Seventeen code/schema/test/README files were synchronized after exact baseline
checks. One server test file (`test_invoice_cli.py`) was an older known repository
blob `d82deb75b554c5a1d08a49554e9d655bf031d2e7`; inspection showed only the already
committed `outstanding_items: []` fixture addition was missing, not an unknown
server edit. The other existing targets matched the local pre-batch commit.

- Uploaded archive SHA-256: `64196fc78394f35864f9cd7037d25c7ecab17294372ce8dab9ec44f5c426fc63`
- Backup: `/opt/odoo-accounting-cli-v4/.tooling/accounting-deferred-lines-20260831-4b691adc/overwritten-files.tgz`
- Backup SHA-256: `41a3f6cd457745b345fd8bfb3d5a6739b6c0c12f5f4a0f7a1e23b2b84680c4e7`
- Shared test: `tests/integration/test_deferred_invoice_lines_live.py`
- Live artifacts: `/opt/odoo-accounting-cli-v4/.tooling/accounting-deferred-lines-20260831-4b691adc/live-smoke.{log,exit,pid}`

The shared smoke uses eight existing public CLI capabilities, two source
invoices/bills of 120 per alias, five scenarios, and one rollback-only business
transaction per alias. It checks date set/clear/restore and exact replay,
automatic deferral of 120 plus two future recognitions of 60, and date-bearing
customer/vendor refund drafts. Automatic deferred moves and their lines are
explicitly tracked for fresh-cursor rollback verification. The two future
recognition entries per source must remain draft with `auto_post=at_date`; the
test never posts them early. The common test helpers execute `cli.main` and normal
ports against the real ORM in-process, not external bridge transport or durable
commit/replay.

### Actual live result and remaining authority boundary

The shared smoke failed in `odoo_cli_v4_dev` after 98.34 seconds, exit code 1.
It did not reach `odoo_cli_v4_e2e`. In the first database, customer invoice
creation, `invoice.get` date readback, and date modification/clear/restore with
exact CLI replay succeeded. The next `invoice.post` failed while Odoo created
the two future recognition entries. The supplier and refund scenarios were not
reached, and the automatic 120/60/60 verification did not complete. Do not infer
their live success from the local test counts or the shared adapter.

The retained native traceback points to
`/mnt/odoo/odoo19/custom/addons/exchange_currency_rate/models/account_move.py:50`:
the `@api.constrains('company_currency_id', 'currency_id')` method reads
`self.is_exchange` on multiple moves and raises
`ValueError: Expected singleton: account.move(265, 266)`.
Native `account_accountant/models/account_move.py:333` calls
`self.create(deferral_moves_vals)` for that multi-period batch. Read-only source
inspection confirms this constraint has no per-record loop or supported context
escape. This is the same existing third-party add-on issue already recorded for
asset validation, not a missing deferred-account configuration or a date-schema
failure. The inspected add-on file SHA-256 is
`724ae3b4eb753b00b273d96641ce7639473a6f37740b6ce3aeba5ca669ee54e9`.

All writes were rolled back. The fresh-cursor tracked-record/run-marker verifier
completed before the original exception was re-raised. The failed log SHA-256 is
`0b5a18470dbb10de1100693f3eb67778e2915ad3c011589dba87bb5bee440fbe`.
The live process completed; it was not left running. Odoo19 stayed active with
`MainPID=1678372`, `NRestarts=2`, and the unchanged 2026-08-30 10:25:07 CST
activation timestamp. No business database, company setting, installed add-on,
runtime configuration, permission, or service was modified for this smoke.

Keep the failed test and assertions intact. Do not shorten the period to force a
single generated move, patch/monkey-patch the shared add-on, skip the constraint,
or elevate the test user. The active goal forbids changes to existing Odoo and
add-on code; a repair therefore needs separate user authorization and an agreed
isolated validation/deployment scope before rerunning this full smoke.

The separate bank-matching configuration correction also remains unauthorized
and was not attempted. Both real-workflow blockers remain open; the new input and
readback implementation is not a claim that accounting-core acceptance is done.

## 2026-08-31 independent invoice and bill accounting dates

This batch extends three existing commands; it adds no capability IDs or schema
files. The registry remains at 355 IDs (including historical non-accounting
extensions), 340 enabled handlers, and 685 schema files. Registry SHA-256 is still
`21b6a57b0bd3b7f17432663de5c82c25b0d63a38c8c9ed6bad2e58732c75572e`.
Picking and stock-return operations remain outside accounting-core development
and must not be counted as accounting-core completion.

`customer_invoice.create` and `vendor_bill.create` now accept optional header
`date`, independently of `invoice_date`. `invoice.update` accepts `changes.date`
on draft invoices, bills, and refunds. The field must be a canonical YYYY-MM-DD
string, not null. Omitting it does not inject a default or change old request
fingerprints. Creation fingerprints include an explicitly supplied date; changing
an update's date changes its existing content-derived idempotency key. The native
date is forwarded in the existing create/write call, with no new handler, generic
ORM endpoint, permission gate, or configuration change. Existing posted-state
protection and no-write replay behavior remain intact. `invoice.get` already
returns both dates and needed no production change in this batch.

Read-only inspection of the installed Odoo 19 source confirmed that
`addons/account/models/account_move.py:121-127` defines date as required, stored,
editable, computed, and precomputed. Explicit create values are protected by
`odoo/orm/models.py:4682,4809-4843`; draft writes protect explicit computed values
at `account_move.py:3789,3880`. A later invoice_date-only write can recompute date
(`:838-852`), while posting can adjust a date that violates native locks
(`:5502-5506`). The CLI does not bypass those rules or promise that a requested
date remains unchanged after posting. Both isolated databases have l10n_pl and
l10n_cz uninstalled; those are the additional date-algorithm overrides found in
the community source. Usage and the recomputation boundary are in README.

Local evidence: 233 distinct relevant runtime, contract/schema, bridge, CLI, and
shared-helper tests passed across the focused runs. The disabled live test skipped
as intended and is not a live pass. After deployment, the focused server selection
passed 153 tests in 147.06 seconds. The earlier broader unit run was deliberately
stopped before completion because it included unrelated historical modules; its
partial log and exit status remain in `unit-tests.{log,exit}` and are not counted
as a complete pass. The successful selection is in `unit-focused.{log,exit}`.

The existing `tests/integration/test_document_lifecycle_write_batch_live.py` now
reuses the established in-process CLI/real-ORM helper instead of its former direct
capability port. It exercises 13 existing write IDs plus invoice.get, preserving
the original customer invoice, supplier bill, and adjustment-entry lifecycles and
immediate replay checks. For both invoice and bill it verifies independent dates
on create, a draft accounting-date edit, a simultaneous date/invoice_date edit,
and readback after posting. It also checks that replaying the original bill-create
request does not undo a later date update. No bank scenario or deferred-generation
scenario is invoked merely by importing the shared helper.

The worker uses uid 5/company 1 in each isolated alias, rolls back on success or
failure, and performs the existing fresh-cursor tracked-record/run-marker audit.
This proves in-process CLI/real-ORM behavior, not external bridge transport or
durable commit/replay. It never writes to a business database, changes an installed
add-on or company configuration, promotes the business user, or restarts services.

Deployment and recovery evidence:

- Baseline: every existing target matched the local pre-batch commit bd2c145.
- Uploaded 11-file archive SHA-256: `d880a5612270d9b2791fd71f2f76204dffef1e80550ae42fb3ef4ff29cff3ed8`.
- Backup of the 12 original targets, including this handoff: `/opt/odoo-accounting-cli-v4/.tooling/accounting-dates-20260831-96b33845/overwritten-files.tgz`.
- Backup SHA-256: `18d97c830f1971889f04254afdcd60f441e61bdf90bda49569a4ad68f513ac6b`.
- Original target ownership and modes were restored from the backup metadata after extraction.
- Live artifacts: `/opt/odoo-accounting-cli-v4/.tooling/accounting-dates-20260831-96b33845/live-smoke.{log,exit,pid}`.
- Launcher PID/process group: 2654824; run UUID: `2befb92c-e7d1-4d04-b38d-4a0387f0f2cc`.

The shared live test passed on both v4-dev and v4-e2e: `1 passed in 789.41s`,
exit 0. Both per-alias results confirm independent accounting dates, all 14
expected existing CLI capabilities, marker/replay checks, and successful
fresh-cursor rollback verification. The launcher and its process group have
finished; no live worker was left running. Live log SHA-256 is
`4e76544d7992d4f45e5eb4a37de1c005e72048a65652b435ce4d622d2275ce41`;
focused unit log SHA-256 is
`6cd8edc1aa3c309b1db77b98c39a7240e8c6a2ef47f19786d101c4cec3d36b50`.
The deliberately stopped broad unit run has exit 143, not a completed pass.

Final read-only audit confirmed Odoo19 remained active/running with
MainPID=1678372, NRestarts=2, and the unchanged 2026-08-30 10:25:07 CST activation
timestamp. The installed exchange_currency_rate file and both earlier failed
workflow logs retain their previously recorded SHA-256 values.

The separate bank-account-role conflict and exchange_currency_rate singleton
failure described above remain unresolved. Neither configuration nor add-on
repair was authorized or attempted during this accounting-date batch. Passing
this narrower lifecycle test does not turn those failed full workflows into passes.

## 2026-08-31 financial credit-note settlement acceptance (passed)

This batch adds no capability IDs, schemas or production handlers. It targets
existing customer/supplier financial credit-note workflows, not physical stock
returns or cash refunds. The registry remains 355 IDs, including historical
non-accounting extensions; this is not an accounting completion percentage.
GOAL_SUMMARY now reflects the user's capability-first phase. STATUS/G3/G5 mark
their old 289-ID inventory-heavy narrative as historical and point to the current
accounting-only scope without deleting earlier evidence.

The existing document-lifecycle smoke has a separately authorized refund-only
case. The original 14-capability lifecycle remains the default and retains its
earlier evidence; it is not unnecessarily rerun by the refund-only selection.
The revised refund chain targets 11 existing commands: customer_invoice.create,
vendor_bill.create, customer_credit_note.create, vendor_refund.create,
invoice.post, invoice.get, invoice.payment_status.inspect, reconciliation.apply,
reconciliation.undo, journal_item.search, and report.trial_balance. Each alias
uses uid 5/company 1 in one real transaction, with public CLI commands, normal
ports and the actual ORM. Read-only ORM access selects master data and audits
cleanup. This is in-process CLI/ORM coverage, not cross-process bridge transport
or durable commit/replay evidence.

Each side starts with a posted 120-unit source document in company currency and
creates positive-price credits of 40 and 80. Native posting reconciles each
linked credit automatically. The revised test reads that result, undoes only the
identified partial reconciliation, verifies that the earlier partial survives,
and reapplies the released outstanding item through public CLI commands. All
explicit writes retain immediate replay checks. This also exercises targeted
undo of a fully reconciled multi-credit graph, rather than only a two-line pair.

Both isolated companies have account_storno enabled. The test preserves red
debit/credit signs and checks that the customer source alone increases the
trial-balance debit and credit totals by 120 each, then checks zero signed net
movement after full credits. Absolute
movement is 480 on each side across both workflows; it is not the signed report
delta. Coverage is limited to this existing same-currency, no-tax fixture and
does not prove foreign-currency, tax or bank-refund workflows.

The shared test helper now tracks line/partial/full IDs when a reconciliation
result has no single primary ID; it no longer adds None to rollback ID sets.
Its CLI metadata check requires exact line IDs for such results. This changes
test adaptation, not production permissions or reconciliation behavior. Three
new cases failed against the old helper; the corrected helper selection passes
9 tests. The focused selection, including these cases and existing refund/undo
contracts and runtime tests, passed 16 locally (23.78s) and the same 16 on the
server (20.62s). The two live nodes skip when their respective authorization
variables are off; skips are not real-run passes.

The first real refund attempt failed in v4-dev after 92.15s, before manual
reconciliation and before the supplier or v4-e2e scenarios. It had already
created/posted the source, verified its 120 residual and +120 trial-balance
movement, and created/posted a credit with total/untaxed amount 40 and zero tax.
The failing assertion expected that posted credit to retain a residual of 40;
its actual residual was not printed. Installed Odoo source inspection then
confirmed the missed native behavior: account_move._post selects linked draft
reversals at lines 5524-5525 and reconciles them at line 5574, even with
move_reverse_cancel false. Production invoice.get reads the native residual
unchanged apart from decimal formatting. No production fix or native bypass is
warranted by this failure. The original test error was re-raised only after its
rollback and fresh-cursor cleanup verification succeeded.

The original failed attempt remains in
`/opt/odoo-accounting-cli-v4/.tooling/accounting-refund-settlement-20260831-3898a5be/live-smoke.{log,exit,pid}`.
Its log SHA-256 is
`eedd1c8504037e6f58a43feec4ce4c19199a27374b266c5f58e9fccfdcecc72d`;
run UUID is `01a5fd52-7b01-483b-bbc1-d9c865f71b8a`. Launcher/process group
2691141 has finished. This failed attempt is not acceptance evidence for the
complete workflow. The corrected auto/undo/apply chain ran separately under
process group 2701075, with `live-smoke-attempt2.{log,exit,pid}` in the same
artifact directory. It has now finished: `1 passed in 1293.65s (0:21:33)`, exit
0. Both v4-dev and v4-e2e passed all 11 capabilities, both 120/80/0 residual
traces, and fresh-cursor rollback verification. Per alias, the test verified
2 source documents, 4 credit notes and 12 posted journal items. The final
reconciliation graph contains 4 partial and 2 full records; rollback tracking
also includes deleted automatic reconciliations, for 8 partial and 4 full IDs
in total. Those tracked totals are not the final live graph. No worker remains
in either attempt's process group.

Corrected live log SHA-256:
`aa7f30dedf72b7fd8275830f9a8063964aa0afd4e5c7f1f6953eaa23ce54569b`.
Focused server unit log SHA-256:
`f6b90b4e78aa3e55be9fe3ca0e6cf2640af6dfe58ce2275cb88e698f4cdb0a63`.

All nine pre-batch targets matched commit 63b5288 before deployment. Their
original contents and ownership/modes are retained in
`/opt/odoo-accounting-cli-v4/.tooling/accounting-refund-settlement-20260831-3898a5be/overwritten-files.tgz`
(SHA-256 `32b50110fe24cfd8b63f3364e23f9c5f352e332715c7ebd91ea79dcde18a64a5`).
The initial eight-file upload has SHA-256
`8917f9643f7d8640fdde8c469f04dc566cc9d7932e85dbaf0aca099777619a2e`;
it retains the first attempt's test version. Every uploaded file was hash checked
and its original ownership/mode restored. The separate bank-account-role and
exchange-rate-addon blockers remain unresolved; no business database, installed
add-on, accounting configuration or service was modified for this batch.

The corrected two-file test/README upload is retained as
`/tmp/accounting-refund-settlement-20260831-3898a5be-attempt2.tgz`, SHA-256
`1cab3a76dbc06c424f2d542c2f03074baef1e06735ce1c2eb50131ad7502a9ac`.
The test file SHA-256 is
`b0d8c43c87b6e4d605317b91bc6d04fa3f66b0640e3716d8e568b729889f2260`.

The post-run read-only audit confirmed the registry digest and the installed
exchange-rate add-on digest were unchanged, as were the earlier failed bank and
deferred-workflow logs. Odoo19 remained active/running with MainPID 1678372,
NRestarts 2 and the same 2026-08-30 10:25:07 CST activation timestamp. No service
control was issued. The bank configuration and add-on repair still need separate
authorization; this narrower successful workflow does not clear those blockers.

Read-only local profiling identified repeated full-registry/schema structural
validation on every CLI invocation: the normal no-Odoo invoice.get descriptor
took about 4.8 seconds, and the profile observed 685 check_schema calls. Each
refund alias has 87 CLI calls across 11 IDs, including 40 write invocations with
replays. The profiler's extra runtime is not a normal-operation timing, and the
server's exact cost distribution was not measured. No production caching or
validation bypass was introduced while this live test was running.

## 2026-08-31 financial-report journal filtering (passed)

This batch extends eight existing interfaces without adding IDs, handlers or
schema files: report.trial_balance, report.general_ledger, report.balance_sheet,
report.profit_and_loss and their four .export counterparts. It does not add
logistics commands. The registry remains 355 IDs/340 enabled handlers/685 schemas;
these historical mixed-domain totals are not pure-accounting coverage.

The optional parameters.journal_ids accepts 1-1000 distinct positive integers.
IDs are sorted without mutating the request. Omission preserves existing
unfiltered behavior, validator tuples, bridge payloads and cursor structure.
Filtered cursors contain the SHA-256 of the canonical ID set, keeping them within
the existing size limit even with 1000 IDs. Changing the set, or switching between
filtered and unfiltered requests, requires starting a new page sequence.

The native source and both isolated databases confirmed filter_journals=true for
the four selected reports, but false for partner_ledger. The latter is explicitly
excluded; no report settings or installed source were changed. Runtime checks
account.journal read access and exact company-scoped visibility, builds native
journal options, and verifies the final effective report retained the exact
selection. Native all-selected normalization is checked via
_get_options_journals, not by assuming individual selected flags stay true.
Missing, inaccessible, foreign-company or unsupported selections fail explicitly
instead of broadening the report. Posted-entry basis is unchanged.

Relevant local selections passed: 164 public journal-filter tests, 120 existing
public report/bridge/CLI tests (8 runtime cases deselected there), and 114 runtime
tests including the 36 new cases. These are distinct selections, not cumulative
rerun totals. Ruff and git diff --check pass. The server focused run passed
266 tests in 8.18s, with 2 authorization skips and the 12 already-tested public
CLI cases deselected. Skips are not live acceptance evidence. Focused log SHA-256:
`6494e0bd77e6aef513ecdcced28e47e87d1c065ac4b8a208d304c6eb7033a909`.

The existing financial-report-export live test now has a separate
ODACV4_ALLOW_FINANCIAL_REPORT_JOURNAL_FILTER_SMOKE=1 case. The original 19-report
export case and its own authorization remain intact. The new case uses uid 5,
company 1 and existing posted sale/purchase fixtures in each exact isolated
database, with SET TRANSACTION READ ONLY and finally rollback/close. It makes
30 real in-process CLI calls per alias across the eight interfaces: 16 exports,
single/multiple/all journal selection, the unfiltered baseline and pagination.
One deliberate invalid-cursor call must stop before the bridge, leaving 29
runtime calls. Trial-balance period debit/credit vectors are checked against
native posted journal items. Eight XLSX files per alias had
their complete nonzero numeric rows checked: the six trial-balance/balance-sheet/
profit-and-loss files against JSON with native folding, and the two general-ledger
files against independently requested native print-mode lines, including expanded
detail. PDF checks cover structure, byte count and hash, not extracted numeric
content. This is not external bridge transport, business-data writes or durable
commit/replay proof.

The first run failed in v4-dev after 76.53s, exit 1. Trial-balance sale/purchase
JSON and both export formats had passed their checks; the general-ledger sale
XLSX comparison then expected each account vector once but observed it twice.
Installed account_general_ledger.py:26-27 forces unfold_all when export_mode is
print and no explicit unfolded_lines are given. The XLSX exporter sets that mode
before get_options (account_report.py:6104,6112), then obtains the expanded lines
(6256-6257). Each fixture account has one journal item, so its summary and detail
naturally have the same amount. A folded JSON Counter was the wrong expectation;
this does not call for changing production export behavior or weakening amount
checks. The original failed log is preserved with SHA-256
`c917a984400741fe3ec1e3d718e40eed66bdf84cf6859eb8a706def4d886eb3b`.
The worker's finally block rolled back/closed; launcher/process group 2750449
has finished. The corrected second shared run passed: `1 passed in 465.22s
(0:07:45)`, exit 0, with both v4-dev and v4-e2e successful. Only the GL test oracle
changed, not production code. Launcher/process group 2758410 has finished as well.
Its artifacts use live-smoke-attempt2.{log,exit,pid}, preserving the original
failure separately. Each worker returned its summary after rollback/close:
30 CLI calls, 16 exports, 8 XLSX amount checks, combined/all journal selection,
unfiltered baseline and pagination. Sale and purchase period debit/credit totals
are each 113 in both aliases; their per-account vectors differ, which is the
meaningful filter check. Corrected live log SHA-256:
`0ee1df510bb9297fe7b1177665868ce6406fa7b8cbc8f32f3c3ea22a6007755b`.
Artifacts are under
`/opt/odoo-accounting-cli-v4/.tooling/accounting-report-journals-20260831-8e673c1a/`:

- live-smoke.log, live-smoke.exit and live-smoke.pid retain the original failed
  attempt; live-smoke-attempt2.* records the corrected successful shared run.
- All 16 existing target files matched pre-batch commit 5281dcf before overwrite;
  the three new source/test paths were absent. Their backup is
  overwritten-files.tgz, SHA-256
  `80eccf36e80df6fc22fd89c880b438202f67f6bc77765164be303d566e98dd97`.
- The initial 17-file code/README upload is code.tgz, SHA-256
  `4d4095e0cbdf7dbeaafe8597d63c2a664ca448d66a1dd5dcdcf9e60a20322f4b`.
  All deployed file hashes were verified, original modes/owners restored, and
  the three new files use mode 644/uid 999/gid 1003. The final handoff/status
  updates are the other two files in this 19-file checkpoint.
- The corrected one-file test upload is attempt2-test.tgz, SHA-256
  `fc727470341fcebf9e02c039d3ab5378856ef9f5a03c283b0e66eeed7ba86e4d`.
  Corrected test SHA-256:
  `1aabe541290a0cdbd9aca8fc93b100f77800f31382e3fe1c136948ac140fc30f`.
- Before the run, Odoo19 remained active/running with MainPID 1678372,
  NRestarts 2 and activation timestamp 2026-08-30 10:25:07 CST. The registry and
  installed exchange-rate add-on digests were unchanged. No service control,
  database configuration or installed add-on modification was issued.

The post-run read-only audit verified all 17 deployed code/README/test files
still matched their frozen local versions. Both process groups have finished.
Odoo19 retained the same active/running status, MainPID, restart count and
activation timestamp. Registry, installed exchange-rate add-on, the original
failed report-filter log/backup, and the earlier failed bank/deferred workflow
logs retained their recorded digests. The server Git checkout still has its
older HEAD 2e190bc; accumulated working-tree changes were preserved, not reset
or pulled over. This batch does not repair the separate bank or add-on blockers.

### Next verified accounting gaps (not implemented by this batch)

Prioritize explicit payment-difference settlement on the existing receivable/
payable payment.register interfaces: for example, settle a 100-unit invoice with
99 cash and a caller-selected 1-unit write-off account. Current explicit-amount
registration forces payment_difference_handling=open; the native payment wizard
supports reconciliation/write-off fields. The existing reconciliation.write_off
command requires a bank transaction and does not fill this payment-wizard gap.
Native early-payment-discount behavior may already apply in other paths, so this
is not a claim that every kind of write-off is unavailable. The proposed narrow
single-invoice, base-currency path still needs implementation and live evidence;
source/ACL inspection alone is not proof that it passes. Preserve the current
omitted-amount behavior, including native early-payment discounts, rather than
globally forcing open. Existing payment replay validation compares source,
amount, date and journal; the extension must also reject same-key changes to
write-off mode/account/label. Reuse the existing schemas, public validator and
runtime; the generic parameter bridge and response need no new framework.

Other bounded existing-interface gaps: invoice.update cannot change journal_id
or currency_id although create accepts them; create does not accept a negative
adjustment price although line replacement does; analytic_distribution is
writable but absent from invoice/journal-item readback, obstructing lossless line
editing. These are independent of the unresolved bank-account-role conflict and
installed add-on singleton defect. Do not keep repeating those blocked workflows,
change configuration/add-ons without authority, or expand inventory command counts.
