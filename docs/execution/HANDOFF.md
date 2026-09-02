# Odoo Accounting CLI V4 handoff

Updated: 2026-09-02 (Asia/Shanghai)

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

- Registry: 398 capability IDs; 383 enabled handlers (215 reads and 168 writes)
  and 15 disabled IDs.
- Runtime status: 335 `unconfigured`, 48 `degraded`, and 15 `disabled`.
- Versioned JSON Schema documents: 772.
- The latest batch adds eight account-transfer-model lifecycle writes:
  `account.transfer_model.create`, `account.transfer_model.update`,
  `account.transfer_model.duplicate`, `account.transfer_model.enable`,
  `account.transfer_model.disable`, `account.transfer_model.archive`,
  `account.transfer_model.restore`, and `account.transfer_model.delete`. The
  final dual-alias rollback smoke passed all eight; uid 5 still lacks
  `account.group_account_manager` in ordinary runtime. The exact contract,
  replay limits, test evidence, and server state are recorded in the last
  checkpoint below.
- The preceding batch added eight product/accounting master-data writes:
  `product.create`, `product.update`, `product.duplicate`, `product.archive`,
  `product.restore`, `product.cost.update`, `product.accounting_profile.update`,
  and `product.category.accounting_profile.update`. They cover only
  company-specific, single-variant, non-storable products. The final dual-alias
  rollback smoke passed; uid 5 still lacks the required product-manager and
  stock-manager groups in ordinary runtime. The exact scope, diagnostic history,
  orderpoint-backed acceptance, and server evidence are recorded below.
- The preceding batch added eight manual account-return lifecycle commands:
  `account.return.create`, `account.return.checks.refresh`,
  `account.return.check.result.update`, `account.return.validate`,
  `account.return.mark_submitted`, `account.return.archive`,
  `account.return.restore`, and `account.return.delete`. The exact scope and the
  server's missing-view compatibility fixture are recorded in the final
  checkpoint below. Do not describe that fixture-backed run as an unmodified
  Odoo-environment pass.
- The preceding batch added eight analytic-accounting commands:
  `analytic.plan.create/update`, `analytic.account.archive/restore`,
  `analytic.line.create/update/delete`, and `analytic.line.summary`. The write
  scope is child plans, company-scoped accounts, and Project-root manual lines;
  summary reads use Odoo 19 dynamic analytic-plan columns. Delete has no
  tombstone and is therefore explicitly degraded rather than claiming replay.
  The exact server acceptance is recorded in the current checkpoint below.
- The preceding batch added no command ID or handler. It extends nine existing
  invoice, journal-entry and payment post/cancel/reset commands with a closed
  2-100-ID batch form while preserving every singular request. Full-scope
  preflight, deterministic full-set keys, sorted explicit results, serial replay
  and one outer transaction are verified. The final server focused selection
  passed 181 cases and the dual-alias real-ORM smoke passed in 487.94 seconds with
  rollback. The detailed checkpoint is at the end of this file.
- The accounting-delivery batch adds nine commands for invoice/payment readiness,
  native queue-only invoice and payment-receipt processing, customer-statement and
  follow-up PDF export, report-delivery attempts, and invoice/bill follow-up
  exclusion. Seven commands passed positively on both isolated aliases; the two
  report-send commands remain positive-live pending because configured uid 5 lacks
  native `res.partner:write`, and the smoke verified their clean authorization
  denial instead. Server focused tests passed 344 cases, the shared dual-alias smoke
  passed in 319.93 seconds with rollback, and the final metadata closure passed 53
  cases. The exact deployment and evidence checkpoint is at the end of this file.
- The invoice-copy/type batch adds `invoice.duplicate` and `invoice.type.switch`.
  Its final server regression passed 901 cases and its shared dual-alias real-Odoo
  workflow passed in 687.67s with rollback verification. It also corrects
  `journal_item.search/get` to represent an unnamed draft move's native
  `name=False` as JSON null. The detailed checkpoint and evidence boundaries are
  at the end of this document. The pushed baseline before this batch is
  `e7ab43be4fda36f82eb2b9840ebdd3dc5d801af6` on `rebuild/v4`.
- The subsequent independent-accounting-date implementation is checkpoint
  `63b5288`; its 14-capability lifecycle passed on both isolated aliases. The
  financial credit-note auto/undo/apply acceptance is recorded near the
  end of this document: all 11 existing capabilities passed on both aliases,
  with rollback verification and no new production interfaces.
- The preceding eight-interface financial-report journal-filter extension is
  implemented, with local and focused server tests passing. Its shared dual-alias
  read-only acceptance passed in 465.22s; see its checkpoint near the end.
- Explicit payment-difference settlement is checkpoint `45fa807`, pushed to
  `rebuild/v4`; both isolated aliases passed its shared eight-capability workflow.
- The four-interface analytic-distribution readback implementation is deployed.
  Server focused tests passed (641 passed, 4 authorization skips). The corrected
  shared run passed both isolated aliases with rollback (1 passed in 470.78s).
  The first test-fixture request failure and its separate correction are retained
  below; no worker remains.
- Negative-price invoice/bill creation is checkpoint `e1510a1`, pushed to
  `rebuild/v4`. Invoice.update journal/currency is checkpoint `3c71911`;
  both isolated aliases passed real currency-change/posting acceptance in 517.22s.
  Actual journal-switch acceptance remains pending because there is no alternate
  permitted journal fixture. See its checkpoint for this distinction.
- Manual-entry date_maturity inputs are deployed. Necessary server regressions
  and the corrected shared dual-alias workflow passed (1 passed in 921.11s), with
  rollback verified. The original test-helper failure and its separate correction
  are retained in the final checkpoint; no worker remains.
- Invoice/bill partner_bank_id and fiscal_position_id inputs and invoice.get
  ID/null readback are implemented and deployed. The shared advance-payment
  workflow passed both aliases in 709.21s after 622 server regressions; its checkpoint
  below distinguishes null readback from the unavailable nonempty fixtures.
- Journal-item tax IDs and company-currency tax-base readback are deployed.
  Server regressions passed 208 cases plus two corrected-helper checks. The first
  shared tax run failed on an unnecessary test-only technical-model metadata read
  before its first CLI call; its rollback audit completed and the failure log is
  retained. The next run exposed report.tax's rejection of native empty net cells
  on group rows after its invoice/tax-item checks passed. A scoped adapter fix
  and 28 targeted regressions followed. The final shared run passed both aliases
  in 501.48s, with rollback verified; neither earlier failed run is counted as
  full acceptance. See the final taxed-invoice checkpoint for the evidence scope.
- Cash-refund registration now accepts customer credit notes and supplier refunds
  through the two existing payment.register commands. Six code/registry/test files
  are deployed; 318 server regressions passed with one authorization skip. The
  shared settled-invoice/partial-refund workflow passed both aliases in 919.40s,
  with rollback verified. See the cash-refund checkpoint below for its boundary.
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

## 2026-08-31 payment-difference settlement (passed)

This batch extends receivable.payment.register and payable.payment.register;
it adds no command IDs, handlers or schema files. The intended shared workflow
uses eight existing accounting interfaces, not inventory operations. The old
355-ID/340-handler/685-schema totals remain mixed-domain implementation counts.

Optional payment_difference_handling accepts open or reconcile. Reconcile
requires an explicit positive amount and an active, accessible writeoff_account_id
in the selected company; writeoff_label is optional trimmed text of 1-200
characters, defaulting to the native wizard label. The amount must not exceed
the source residual. Write-off fields without reconcile are invalid. The source
must be a posted customer invoice or vendor bill with a positive residual.
Existing requests omitting the new fields retain their native defaults, including
early-payment-discount behavior when amount is omitted; explicit amount alone
still leaves the unpaid difference open.

The native single-document wizard uses full installments and grouped payment
for explicit reconcile, allowing one payment and one balanced payment move to
settle the entire source residual. Both explicit modes require payment currency
to equal source-document currency. Explicit reconcile rejects native early-payment
discount, exchange-account, noneditable or inconsistent installment routes before
payment creation when they cannot honor the selected account. These are explicit
boundaries, not claims that all currencies, discounts or installments were tested.
Native source account_payment_register.py:811-836,1000-1040 explains these paths.

The existing operation-marker helper fingerprints the full explicit request.
The standard default_invoice_origin context writes it during native payment-move
creation, avoiding an additional write to a posted move. Native source confirmed
context propagation through account_payment_register.py:1112, account_payment.py:
845,998,1002 and account_move.py:3798. Runtime requires marker readback and rejects
same-key changes to mode/account/label, including removal of explicit mode. Legacy
unmarked payments retain the original source/date/journal/amount replay behavior.
Successful reconcile also requires source residual zero and the exact requested
write-off account, label, currency and signed amount in the resulting move.

Local selections passed: 96 new public-contract cases; 29 new runtime cases plus
120 existing runtime cases; 10 existing public full/partial-payment cases; and
2 registry matrix/runtime-metadata cases. These are distinct selections, not
cumulative rerun totals. Changed Python lint and git diff --check pass. Independent
source review found no definite defect; native account.group_account_invoice
already grants account.account read, so the added read requirement does not
change normal native-group access or grant any new rights.

The shared live case is test_payment_differences_settle_and_roll_back_per_alias
in tests/integration/test_document_lifecycle_write_batch_live.py, enabled only
with ODACV4_ALLOW_PAYMENT_DIFFERENCE_SMOKE=1. The original lifecycle and refund
cases retain separate authorizations. Successful acceptance per alias used uid 5/
company 1 for 22 in-process CLI calls: create/post/replay two 100-unit documents,
register/replay two 99-unit payments, reject two changed-key-payload attempts,
read the payment and three-line journal entry, and inspect residuals of zero.
It verified unchanged bank configuration and finally rolled back, then audited
tracked IDs and run markers using a fresh cursor. No durable write, external
bridge transport or bank-statement matching claim follows from this test.

Artifacts are under
/opt/odoo-accounting-cli-v4/.tooling/accounting-payment-differences-20260831-15dc8a7d/.
All nine existing targets matched pre-batch commit 41614de; two new test paths
were absent. overwritten-files.tgz retains contents/ownership/modes, SHA-256
`e6a180b3a10384e19904d38f5d01d770f466e9550f974cc1732bce4c1f163543`.
The initial eight-file code.tgz has SHA-256
`c8a6852a2f2e40bf16d2f72ee96f77064cbc93a4a0e9d5e7793984b8c1bd36b7`.
All eight deployed hashes match local files; existing modes/owners were restored,
and the two new test files use mode 644, uid 999, gid 1003. Server Git HEAD remains
2e190bc; accumulated working-tree changes were preserved, not reset or pulled.
The registry digest is now
`aa86c26d53290343c1b8ce105aa7945f4f2f93575c99be2e77a6185fbb7acc96`.

Server focused tests passed: 267 passed and 3 authorization skips in 88.42s,
exit 0. SSH disconnected before the client received completion; reconnecting
confirmed the saved exit file and full test log, rather than rerunning or treating
the transport failure as a test failure. Focused log SHA-256:
`4d6313692e63a46cdb655383a76848eb636dfeae1c99eab808ef54dc99335b4f`.
The shared live case passed both v4-dev and v4-e2e: 1 passed in 330.64s, exit 0.
Each alias returned two successful 99-unit payments, source residuals 100 to 0
for both customer and supplier, six immediate replays and two idempotency
conflicts. Customer payment balances were +99 outstanding, -100 receivable and
+1 write-off; supplier balances were -99 outstanding, +100 payable and -1
write-off. Exact write-off account/label/currency, balanced debit/credit totals
of 100, and source-line reconciliation were verified. Payment state may still be
in_payment: no bank-statement match was attempted. This acceptance uses untaxed
company-currency documents and does not establish foreign-currency, EPD, split
installment or durable-commit/replay behavior.

Per alias, rollback tracked 2 account.payment, 4 account.move, 10 account.move.line,
2 account.partial.reconcile and 2 account.full.reconcile records, with no bank
statement line. A fresh cursor confirmed all tracked records/run markers absent.
The separate live-smoke.log, live-smoke.exit and live-smoke.pid retain the outcome;
launcher/process group 2798478 has finished with no remaining worker. Live log
SHA-256:
`2c4f9f62900d65032b365d067f153f751d9815870014a65e3e52f1bd528523e9`.

Preflight confirmed Odoo19 active/running, MainPID 1678372, NRestarts 2 and unchanged
activation time 2026-08-30 10:25:07 CST. The exchange-rate add-on digest remains
`724ae3b4eb753b00b273d96641ce7639473a6f37740b6ce3aeba5ca669ee54e9`.
The separate bank-account-role and native add-on singleton blockers are unchanged;
no service, installed source, account/journal configuration or business database
modification is authorized by this batch.

The post-run audit confirmed all eight code/test files still matched their frozen
local hashes, the backup/code archives and current test logs retained their
digests, and the earlier failed bank/deferred logs and installed add-on digest
were unchanged. Odoo19 retained the same PID, restart count, activation timestamp
and active/running state; Nginx and PostgreSQL remained active. The remaining
three changed files are README.md and this batch's STATUS/HANDOFF updates.

### Next accounting work

Read-only code review confirmed analytic_distribution is writable but absent
from invoice.get lines, journal_entry.get lines and journal_item.search/get items.
These four existing interfaces are the next coherent completion batch, not four
new IDs. Three public read validators, two runtime modules and three response
schemas need coordinated changes; journal_item.get already reuses the search
item definition, and the bridge ports already pass nested data through. Header-
only invoice.search and journal_entry.search are not part of this line-data gap.

Prefer a lossless mapping compatible with existing write snapshots, including
combined analytic-account keys and decimal percentages. Do not assume the CLI's
restricted write-input limits describe all valid native stored distributions.
Verify the native field/access rules first. Reuse the existing document lifecycle
smoke for create/edit/clear/post/readback, check shared validation.journal_entry.check
compatibility, and include generated account.analytic.line records in rollback
auditing. Select existing visible analytic accounts if possible; do not change
analytic configuration, elevate the business user or add an unrelated framework.
No analytic readback change or live acceptance is claimed by this payment batch.

## 2026-08-31 analytic-distribution readback checkpoint (completed batch)

This accounting-only batch completes existing line-data responses, not new command
IDs: `invoice.get` lines, `journal_entry.get` lines, and `journal_item.search/get`
items now require `analytic_distribution`. The registry remains unchanged at
355 mixed-domain IDs, 340 enabled handlers and 685 schema files. Historical stock,
sales and purchase extensions remain outside current accounting-core coverage.

### Implementation and native boundaries

- Five production Python files and three response schemas change. The public
  readers reuse one small validator; the two runtime modules share one normalizer.
  `journal_item.get` already reuses the search item schema, and bridge ports pass
  nested line data through unchanged. No new model lookup, ACL, command, bridge
  action or control framework is added. `validation.journal_entry.check` retains
  its existing response and checks.
- Native `False`, `None` and empty JSON objects read as `{}`. Nonempty string keys
  are preserved verbatim, including comma-separated combinations, their order
  within each key, and accounts repeated across different keys. Reads do not
  resolve account names or apply the CLI write restrictions to stored data.
- Percentages accept finite native int/float/Decimal values and return canonical
  signed decimal strings. Zero and negative zero become `"0"`; trailing fractional
  zeros are removed, without a new quantization step. Values are not bounded to
  0-100, four decimal places, sixteen entries or a global total of 100. This retains
  ORM-returned precision, not precision already rounded away by native writes.
- Existing line writes still clear a distribution with `null`, not `{}`. No write
  schema or write handler is changed. Header-only invoice/journal-entry searches
  do not gain line data. `journal_entry.get` is used for ordinary entries only;
  invoices, bills and financial credit notes use `invoice.get`.

Read-only native inspection found stored writable JSON with no field-level group
restriction. Native writes round using the configured analytic precision (two
digits in these isolated databases), and validate totals conditionally by mandatory
root plan rather than unconditionally across the mapping. Both aliases have an
existing optional root plan 1 but no usable analytic accounts. The shared smoke
therefore creates one temporary account through `analytic.account.create`, reuses
plan 1 without configuration changes, and includes the account and generated
analytic lines in the normal rollback audit.

### Verification and the retained fixture correction

Local selections passed: 158 new public/schema cases, 670 existing public read and
journal-check cases, 9 focused CLI cases, 96 invoice/journal runtime cases, 261 core
read runtime cases, and 115 bridge/helper cases. Authorization-off integration
cases skip as intended. Ruff passed after excluding only three independently
confirmed pre-existing diagnostics on their original files; no unrelated lint or
formatting changes were made.

The server's focused selection passed `641 passed, 4 skipped in 30.45s`, exit 0.
The skips were the four separately authorized database tests; the analytic case
is executed explicitly in the shared run, not accepted via a skipped test.

The first shared run failed in v4-dev after creating and reading the three draft
documents, before `invoice.lines.replace` reached the runtime. The test copied
creation lines but omitted `product_id` and `discount`, which the existing
replacement request schema requires. Failure-time collection, rollback and the
fresh-cursor audit completed before the error was re-raised. The result was
`1 failed in 91.47s`; v4-e2e was not attempted in that run. Only those two test
fields were added. Offline validation accepts the corrected request and rejects
each missing field; no production contract or handler changed for this fix.

The corrected shared run passed both aliases: `1 passed in 470.78s`, exit 0. Each
alias demonstrated 30 CLI invocations across 11 existing capabilities: create
the temporary analytic account, create a customer invoice, supplier bill and
ordinary entry, replace the customer lines once, post all three documents, and
read through the four completed interfaces. The customer example changes one
distribution from 100 to 75.25 and clears another with null; reads must return
75.25 and `{}` before and after posting. Eight immediate replays, seven posted
journal items, three generated analytic lines and one temporary analytic account
are checked. No payment, bank transaction or reconciliation record is created.

Business execution uses uid 5, `su=False`, company 1, solely in `odoo_cli_v4_dev`
and `odoo_cli_v4_e2e`. All records are rolled back. The fresh-cursor residual audit
uses the existing superuser read-only inspection, not an elevated business write.
The old smoke branches do not gain analytic-model lookups or tracking. Live
coverage is in-process CLI with real ORM in one transaction per alias, not external
bridge transport, durable commit/replay, concurrent exactly-once behavior, or live
acceptance of every composite-key/signed-percentage boundary covered by units.

### Deployment and recovery

Local baseline is `45fa80738f051056980d355dd67ad608700c35bc`. All 20 existing code/
test/schema targets matched their baseline Git blobs on the server before backup;
the new test path was absent. The 21 deployed files were hash-verified, with
existing modes/owners preserved. The later fixture correction has its own backup
and archive; `verified-code.sha256` records the final 21-file code set.

Private artifact directory on the server:
`/opt/odoo-accounting-cli-v4/.tooling/accounting-analytic-readback-20260831-20f6a347`

- `before-code.tgz` backs up 20 original code/test/schema files; SHA-256
  `8d3fe3db0366df6a058becb3774a8fe3ade91e685d64691be4e351e15d23a22a`.
- Initial `code.tgz` SHA-256:
  `006a75a5d5a69a02d0588d776aacd229363ef82fbd79883c24ef2408e292efa9`.
- `before-smoke-fixture-fix.tgz` SHA-256:
  `423cf31765f62049ed8b3315288e1379de855fe850670e2654937a01daf3da3e`.
- `smoke-fixture-fix.tgz` SHA-256:
  `75f8021d132d5073a699493b90cac92e1c51cec0fd4a0d3c3c1447fb41025520`.
- `before-docs.tgz` backs up README, STATUS and HANDOFF after baseline comparison;
  SHA-256 `f3897680c2c5bfc5ada72ad8be4d2f2e2a467083b253d79c18ed176325451d10`.
- Focused `focused.log` SHA-256:
  `623d62135cdaf9b4e67a282b3d3b1da6de2d912da124b5e3c85157dc34a9025c`.
- First failed `live-smoke.log` SHA-256:
  `f0f5196a20e475bbaf26dcf60927342e6afa1137e231b3c8f43ce4a1b32430d1`.
- Corrected `live-corrected.log` SHA-256:
  `f964a6bd6af79020908c8bdf24e57196c9469086c594de90c8c11830376b6d16`.
  `live-corrected.exit` is 0; runner/process group 2836072 has finished. The original
  failed runner 2830801 has also finished; do not overwrite either run's evidence.

The server Git HEAD remains `2e190bcdd70313c0a10dcc479e1a2834db240a50`; its prior
working-tree changes are preserved. Do not reset, pull over or otherwise replace
that checkout to manufacture a matching HEAD. Services, installed Odoo/add-ons,
bank and analytic configuration, and business databases are outside this change.

The post-run audit confirmed all 21 final code/test/schema file hashes, retained
archives and logs, and the unchanged registry digest. The earlier failed bank and
deferred workflow logs and installed exchange-rate add-on digest were unchanged.
Odoo19 retained MainPID 1678372, NRestarts 2, active/running state and its
2026-08-30 10:25:07 CST activation timestamp; Nginx and PostgreSQL remained active.
Both verification process groups were empty. The final documentation consists of
README.md and these STATUS/HANDOFF updates; no installed-service change is needed.

### Next accounting work

The next compact high-frequency gap is direct creation with a negative unit-price
adjustment line. `customer_invoice.create` and `vendor_bill.create` reject signed
negative prices in schema, public validation and runtime, while
`invoice.lines.replace` already accepts them. Complete those existing creation
interfaces and verify a positive overall document such as 100 plus -10 equals 90
through create/read/post/replay; do not count existing signed line replacement as
a new ability. Native accounting behavior still needs verification before changes.

A second verified contract gap is draft `invoice.update.changes` lacking
`journal_id` and `currency_id`. Reuse existing company/type/access checks and the
changes fingerprint if taking that on; investigate native currency recomputation
and journal fixed-currency constraints without changing configuration. Neither
follow-up is implemented or accepted by this readback batch. The separate bank
configuration and installed-addon singleton blockers remain unresolved; this
batch does not authorize their repair or establish full accounting coverage.

## 2026-08-31 negative-price creation checkpoint

This batch extends two existing accounting interfaces, customer_invoice.create
and vendor_bill.create. Only their price_unit validation changes to the existing
signed decimal behavior at schema, public-validation and runtime layers. Quantity
remains positive, discount remains 0-100, all other line/header fields and replay
fingerprints remain unchanged. No IDs, handlers, bridge actions, schema files or
control framework are added; the registry remains 355 mixed-domain IDs, not 355
accounting operations. Stock/picking/physical-return work remains outside scope.

Native source inspection confirms signed line prices are valid. A negative-total
draft remains possible, but account_move.py's native posting check rejects a
negative normal invoice/bill using currency rounding; the CLI adds no new total
policy or automatic conversion to a credit note. Both isolated company-1 fixtures
use storno accounting. The shared case therefore checks the negative customer
line as debit 0 / credit -10 and supplier line as debit -10 / credit 0, not only
an equivalent balance with incorrectly flipped debit/credit sides.

Local validation passed 40 public/schema signed-price cases, 134 runtime cases,
78 existing bridge/lifecycle cases and 19 selected existing-create cases. The
reviewed test requests for both aliases passed full registry schema validation;
missing product_id or discount in replacement lines was rejected. Ruff and
git diff --check passed. Server selections passed 252 tests / 4 authorization
skips in 74.55s, followed by 19 existing-create cases in 34.15s; both exits are 0.

The existing analytic-readback shared case is extended, not a new smoke framework
or authorization flag. Each alias retains 30 CLI calls / 11 capabilities / eight
immediate replays. It adds a -10 line to the customer invoice (100 + 20 - 10 = 110)
and supplier bill (100 - 10 = 90), retains distribution replacement/clearing, and
checks create/read/post totals, residuals, line prices and signed journal items.
It verified nine current posted journal items and three analytic lines, with
one temporary analytic account and three documents, all rolled back. Nine is
not the count of all historically tracked/deleted replacement-line IDs.
Business execution stays uid 5, su=False, company 1; the existing fresh-cursor
residual audit is a superuser read-only check, not an elevated business write.

The dual-alias shared run passed: 1 passed in 443.49s, exit 0. Runner/process
group 2862642 is empty; run ID is 0da7f926-5798-41b8-8687-519b7248962d. Both
odoo_cli_v4_dev and odoo_cli_v4_e2e returned rollback_verified=true. Preserve
live-smoke.log and live-smoke.exit; no failed live attempt occurred in this batch.
Acceptance is untaxed company-currency in-process CLI with real ORM, not external
bridge transport, durable commit/replay, concurrent execution, foreign currency,
taxed negative lines or a real cash refund. Negative-total posting refusal was
checked in native source, not an extra business-write test in this shared run.

Server artifact directory:
`/opt/odoo-accounting-cli-v4/.tooling/accounting-negative-prices-20260831-1a49a5f6`

- before-code.tgz: seven existing targets, SHA-256
  `2eecb04d9bbb203fe75ca7f50af0b72e19d327bff767fe079b5286d96127e638`.
- code.tgz: eight current code/test/schema files, SHA-256
  `906e78edb62c5f72b3b21341c8c1b94fe23c6714f801af976880b27fee452b0b`.
- before-docs.tgz: README, STATUS and HANDOFF, SHA-256
  `a00f52da8acb02492897aca1b9e0a731d12a0a91059c541bae82c110670cfa81`.
- focused.log: SHA-256
  `87f13adaa11d29ba968c4db68512f70121790987672b44b27abbf12093d4704d`.
- existing-create.log: SHA-256
  `7a235a60853c6c4c027d45f6696b463a5ea4be8b5bd06e07359cc4066fe356b8`.
- live-smoke.log: SHA-256
  `e3aa8da8c035b74b87e19c60a3bfef07b2d9eb44afead93e529896f1ef841124`.

code.sha256 identifies the eight deployed code/test/schema files; final.sha256
adds README, STATUS and HANDOFF for the complete eleven-file checkpoint.

All existing targets matched baseline commit d817a3bca2d16f8907fa253d06077ee0577f9ef1
before backup; the new unit-test path was absent. Existing owners/modes were
preserved. The server Git HEAD remains 2e190bcdd70313c0a10dcc479e1a2834db240a50;
do not reset or pull over its accumulated working-tree changes.

Pre-deployment inspection found an intervening service event: systemd records
the prior Odoo19 process exiting with a missing-passlib import error at 10:24:11
CST, then an automatic restart at 10:24:22. This preceded this batch's deployment
and tests. Current baseline is MainPID 2855713 / NRestarts 3 / active-running;
the chosen test interpreter imports passlib successfully. No service, dependency,
installed-source or configuration change/restart was issued by this batch.
The previous batch's PID 1678372 / restart-count 2 is historical, not this run's
baseline. The separate bank-account-role and installed-addon blockers remain
unresolved; their repair and real-business database writes are not authorized.

The post-run audit verified all eight frozen code/test/schema hashes, retained
archives/logs, the unchanged registry, the installed exchange-rate add-on digest,
and both earlier bank/deferred failure logs. Odoo19 retained the new baseline
PID, restart count and activation timestamp; Nginx and PostgreSQL remained active.

### Next accounting work

The remaining compact contract gap is draft invoice.update.changes lacking
journal_id/currency_id. Read-only inspection of the installed Odoo19 source found:

- Ordinary ORM write invokes the fields' registered inverses; do not simulate UI
  onchange calls or manually rebuild journal items. Native write handles dynamic
  lines, numbering and previously-posted protections.
- Retain the CLI's exact selected-company and invoice-type journal checks.
  Native journal changes can also change the inferred company, so native branch-
  company compatibility alone is not sufficient isolation.
- A journal's currency is a default, not an immutable invoice-currency lock.
  Native test_account_move_out_invoice.py:3899-3935 explicitly permits a currency-
  only change to differ from that default; journal-only changes adopt its default
  at :3954-3975. Existing accounts' forced currencies can still reject the change.
- Currency changes recompute line currencies, base-currency balances and tax/
  payment-term lines, not a conversion of the entered unit prices. The installed
  exchange-rate add-on can select a manual-rate path; do not assume system rates.

These findings are for the next batch only: no header-write implementation or
live acceptance is claimed here. Reuse the existing update/fingerprint/ORM path
and verify both ordinary journal/currency edits and native refusal cases without
changing account/journal configuration, services or installed source.

## 2026-08-31 invoice-header update checkpoint

This batch extends existing invoice.update, not stock/logistics operations.
changes.journal_id and changes.currency_id accept strict positive integer IDs.
The existing lifecycle supports customer invoices, supplier bills and financial
credit notes/refunds. Journal lookup requires the exact selected company and
sale/purchase type appropriate to the document; currency lookup requires an active
accessible record. Native write/inverses recompute balances and numbering. A
journal currency is a default, not a hard lock, and numeric unit prices are not
exchanged automatically. Forced account currency, previous posting/numbering and
installed manual-rate rules remain native restrictions. Existing confirmations,
fingerprints and posted no-change replay are retained; actual edits require draft.

The registry adds account.journal/res.currency read-model dependencies to this
existing handler. Counts remain 355 mixed-domain IDs / 340 handlers / 685 schemas,
not pure-accounting coverage. Current registry SHA-256 is
90162a226b7bb79da51b14446472309152a2990093c49d0ab9136132a5d4c8b3.

Local validation passed 183 runtime cases, 102 public/bridge/lifecycle cases and
4 selected registry/existing-update cases (451 deselected). All 70 requests for
the two-alias shared case passed offline schema/contract checks; Ruff and diff
checks passed. Server focused tests passed 285 cases / 4 authorization skips in
74.61s, followed by 4 selected registry/existing-update cases in 22.66s; exits 0.

The existing analytic-readback smoke passed with 35 CLI calls / 12 existing
capabilities / 10 immediate replays per alias. It changes the customer invoice
and supplier bill from CNY to USD, leaves them in USD through posting, and checks
the same numeric totals 110/90 plus company-currency totals 150.70/123.30. The
USD-to-CNY rate 1.37 is an existing historical fixture, not a current market rate.
The case verifies no manual-rate override, currency/amount_currency/balance,
negative storno lines, analytic distributions, balanced journal items and the
existing rollback audit. It verified three documents, nine current posted journal
items, three analytic lines and one temporary analytic account per alias. The
dual-alias run passed: 1 passed in 517.22s, exit 0, with rollback_verified=true for
both databases. Business writes use uid 5/su=False/company 1; the existing
fresh-cursor residual audit is superuser read-only inspection. This is untaxed
in-process CLI/real-ORM acceptance, not external bridge transport, durable replay,
concurrency, tax, manual-rate or financial-credit-note acceptance. No failed live
attempt occurred in this batch; the process group is empty.

Read-only inspection under uid 5/su=False/company 1 found only sale journal 9
and purchase journal 10 in both databases, even with active_test=False. The user
cannot create journals. The shared case therefore submits the existing journal
ID with the real currency change: combined-input validation is not evidence of
an actual journal switch. Unit tests cover alternate journals, all four invoice
types, missing/wrong-company/wrong-type references, inactive currency, read-ACL
failure and posted-state refusal. Positive real journal-switch acceptance remains
pending an authorized suitable fixture; do not change configuration or elevate.

Server artifact directory:
`/opt/odoo-accounting-cli-v4/.tooling/accounting-invoice-headers-20260831-5d97b31a`

- Baseline local/GitHub commit: e1510a116adfc54efacb8444ead11e8ebbe43191.
- before-code.tgz: six existing files; new public-contract test was absent.
  SHA-256 ec063eb07ef094b76438d648e0d027f0ae728f0fdce0a57edda9f3031ad84cc7.
- code.tgz: seven files, SHA-256
  78125368bf26005fa24f13db655b66029a7cc994b0a4080b71447348a2dc1b34.
- before-docs.tgz: README, STATUS, HANDOFF; SHA-256
  86e28f4c7e75bbf0de2d3e6eccd6fcd8e07cdcc59f6332dbe29537397f46d512.
- focused.log: SHA-256
  2050254568d265c07f39fa12c1bc310d5334c14593382e61432b3b698132c3d1.
- existing-update.log: SHA-256
  01e75b0051165e63fa85167dca33b0f14f50c87896640ebb8a28e262bd8ac140.
- live-smoke.log: SHA-256
  fb2f23b93c8c39ab9f45dc8bdf8c325dec4ba3874c06bc227df620e946514dd8.

All existing code and document targets matched the baseline before their backup;
code.sha256 verifies the seven deployed code/test/schema files. final.sha256
includes the three updated documents for the ten-file checkpoint. Existing
owners and modes were preserved. Server Git HEAD remains
2e190bcdd70313c0a10dcc479e1a2834db240a50; do not reset/pull over its working tree.
The runner/process group 2903827 finished and is empty. Post-run verification
confirmed all seven frozen code hashes, backup archives, the installed exchange
addon and both earlier bank/deferred failure logs. Odoo19 retained PID 2855713 /
NRestarts 3 / active-running / activation 10:24:22 CST; Nginx/PostgreSQL remain
active. No service, dependency, configuration or installed-source changes were
issued. The two pre-change archives and completed test logs/exits are also retained
in the same relative private .tooling directory locally, with matching hashes.

### Follow-up identified at the invoice-header checkpoint

At that checkpoint, manual receivable/payable journal-entry lines could not accept
date_maturity in journal_entry.create or journal_entry.lines.replace. Both
closed request schemas, public/runtime validators, ORM values and replacement
snapshots omit it. Existing journal_entry/journal_item reads expose the field,
and receivable/payable open-items filters already use it for ordinary entries.
Add only an optional YYYY-MM-DD-or-null line value through those existing paths;
preserve omitted-field fingerprints and target comparison, and treat explicit
null as clearing. Full line replacement still rebuilds the submitted line set.

Read-only installed-source review found a plain writable Date field at
account/models/account_move_line.py:369-375, with no default/compute/required
attribute. The constraint at :1364-1377 applies to invoice/payment-term types,
not a new requirement for manual entry lines. Do not invent AR/AP-required,
non-AR/AP-forbidden or maturity-on/after-accounting-date restrictions. Native
reconciliation sorting and installed aged-partner reports use maturity or fall
back to accounting date. Keep the current CLI draft-only replacement boundary.

A coherent follow-up can reuse 12 existing capabilities: journal_entry.create,
journal_entry.lines.replace, journal_entry.post, journal_entry.get,
journal_item.search, receivable.open_items.list, payable.open_items.list,
report.aged_receivable, report.aged_payable, report.trial_balance,
reconciliation.apply and reconciliation.undo. The reconciliation request must
use the two-line line_ids branch, not invoice_id (which rejects manual entries).
Undo covers an isolated two-line reconciliation, not arbitrary multi-counterpart
graphs. Verify due/future amounts, report/open-item changes, reconciliation and
undo, immediate replays and final rollback under uid 5 without configuration
changes. Those were source/contract findings, not acceptance evidence; the
implementation and current verification state follow below. The bank
configuration and installed-addon blockers remain open.

## 2026-08-31 manual-entry maturity checkpoint

Existing journal_entry.create and journal_entry.lines.replace now accept optional
date_maturity on each line: a canonical real YYYY-MM-DD string or null. Explicit
null writes native False; an omitted key is not added to ORM input or request
fingerprints. Snapshots include the native date. An otherwise unchanged old
replacement request ignores only its omitted maturity fields, so it does not
rewrite or clear them; an actual full replacement rebuilds all submitted lines.
Supply dates to retain when replacing lines for another change. Native ORM and
the CLI's draft-only actual-edit boundary are preserved. No mandatory AR/AP date,
date/account-type restriction or maturity-after-accounting-date rule is invented.

Existing journal_entry/journal_item reads expose the value. Open-item date bounds
filter the raw maturity date (unset dates do not match); installed aged reports
fall back to accounting date. No IDs, handlers, registry dependencies, schema
files, configuration, permissions or inventory capabilities are added.

Local necessary regression: 318 passed in 137.57s; six selected existing-entry
cases also passed. Both shared modules skip with write authorization disabled.
All 66 complete request templates for the two aliases passed offline schema and
public-contract checks. Independent review corrected two test-only mistakes
before deployment: journal_entry.get takes entry_id, and journal_item.search
exposes balance/reconciled rather than amount_residual. Residuals are verified
through open_items. Ruff and diff checks passed. Server regression passed 318
cases / 2 authorization skips in 75.26s and six selected existing-entry cases in
25.50s. The first shared live run failed in 11.18s on the initial aged-receivable
read, before creating entries; its rollback audit completed. The helper omitted
capability_id when constructing financial-report and open-item ports, selecting
trial balance for an aged request. Only test code was corrected locally; a new
five-route regression first reproduced the bug, then passed with both live tests
unauthorized (1 passed / 2 skipped, 0.65s). No production validation was relaxed.
The corrected two test files are deployed; the server helper regression passed
1 case / 2 authorization skips in 0.71s. The default production CLI already binds
both port types to the requested capability; this was a shared-helper-only fix.
Corrected shared acceptance passed both aliases: 1 passed in 921.11s, exit 0.
Each alias verified 62 CLI calls / 12 capabilities / 16 immediate replays, four
manual entries, eight current posted items and rollback_verified=true. It verified
AR 120/AP 90, both reconciliation/undo pairs and trial-balance debit/credit delta
420/420. Past-due sources moved to period2; future counterparts restored after
undo moved to period0 with the opposite sign, retaining a zero combined total.
This is company-currency in-process CLI/real-ORM acceptance, not external bridge
transport, durable replay, concurrency, tax or foreign-currency acceptance.

The new shared case uses 12 existing accounting capabilities and verifies
four manual entries per alias: AR 120 and AP 90, future/cleared/past maturity,
posting, open items, native aged reports, opposite future-dated entries,
reconciliation, undo, immediate replay and trial balance. Business actions use
uid 5/su=False/company 1 only in odoo_cli_v4_dev and odoo_cli_v4_e2e. It always
rolls back, followed by the existing fresh-cursor superuser read-only residual
audit. It does not run the known blocked bank workflow or modify fixtures.

Baseline local/GitHub commit: 3c7191149c162e0854980d24329b2713c5f11134.
Server artifact directory:
`/opt/odoo-accounting-cli-v4/.tooling/accounting-entry-maturity-20260831-a9503a31`

- before-code.tgz contains five existing targets, all matching baseline blobs;
  the three new test paths were absent. SHA-256
  3b216038ae6ae078b0966b2a78eab925a55d094135e0f83b2960c15c32c7c10b.
- code.tgz contains eight files, SHA-256
  e65c5326c754b9a26ec3e0243805857f93ceeaba25cef862c4fe5798ac1c6b0c.
- code.sha256 verified all eight deployed files. Existing ownership and modes
  were retained. The pre-change archive is also downloaded locally with its
  matching SHA-256; local artifacts use the same relative private directory.
- runner/process group 2999206 finished and is empty. focused.exit and
  existing-entry.exit are 0; live-smoke.exit is 1. Retain these original logs
  when deploying the test-only fix and rerunning under distinct log names.
- before-docs.tgz contains the three baseline documents, SHA-256
  ec8d962ad490b82ae0afd46ae9d869ab26e94bef8ad4470e68b845b750d9aa67.
- focused.log SHA-256:
  77b89be585e0530df8b495536e6f4e9703da24e6d68b0a8af5b1caff43dc6431.
- existing-entry.log SHA-256:
  8371825d795d1c3e6a2769af00d32ed4ae824d389cefbfe3a4e4b38a86686dd1.
- initial live-smoke.log SHA-256:
  9eb036657cd23b26fe157aed2d83e3f1e079bf19e49f0292fab9842612754dea.
- test-fix.tgz contains only the corrected helper and new shared test; SHA-256
  6b4b9fc0f98434e75f4e5b38d32426d8e4a0edff9bb6549bdcc31e1c24240f18.
  Both prior versions remain in code.tgz. verified-code.sha256 verifies all eight
  final code/test/schema targets, without overwriting the initial manifest.
- Corrected runner/process group 3009611 finished and is empty. The new result
  files are helper-regression.log/.exit and live-smoke-corrected.log/.exit;
  both exit files are 0. Keep the initial failure log alongside the passing run.
- helper-regression.log SHA-256:
  5e2d006d3dc1c85e532b8f218a106f4e2b38ccb6eba86b58cb2d67e5b87f9af8.
- live-smoke-corrected.log SHA-256:
  d1bf2997b1a12ab10325617a3e388f77df5117522e3b30c56bc3e1365d06dfe3.

verified-code.sha256 records the eight final code/test/schema files; final.sha256
adds README, STATUS and HANDOFF for the eleven-file checkpoint. The original and
corrected test logs/exits and both pre-change archives are retained in the same
relative private artifact directory locally as well as on the server.

Post-run Odoo19 state remains PID 2855713 / NRestarts 3 / active-running;
Nginx and PostgreSQL are active. Registry, installed exchange-rate addon and the
earlier bank/deferred failure logs matched their recorded hashes. Server Git HEAD
remains 2e190bcdd70313c0a10dcc479e1a2834db240a50; do not reset/pull over its working
tree. This batch has not restarted services or changed business databases,
installed source, dependencies or accounting setup. Prior journal-switch fixture,
bank-account-role and installed-addon limitations remain unresolved.

### Prior financial-header finding

This is the source/fixture finding that led to the implementation below; its
nonempty-fixture limitation remains unresolved.

Read-only contract/source review identified missing per-document
fiscal_position_id input in customer_invoice.create, vendor_bill.create and
invoice.update. Native account.move exposes a writable company-checked field;
partner defaults do not replace the ability to explicitly select it per document.
Read-only probes under uid 5/company 1/su=False found read access but zero
company-matching or shared fiscal positions in both isolated databases, including
inactive records. Both transactions were forced read-only, rolled back and
closed. A positive selection/switch therefore has no existing acceptance fixture;
do not label clearing an empty value as a successful real selection, or create
configuration without authorization.

The implementation reuses the three existing inputs and native write.
Distinguish omission from explicit null and validate the referenced company and
ordinary-user access. Creation already submits explicit account_id/tax_ids on
lines: do not silently map those inputs again. Changing or clearing the header
does not mean reapplying the position to every existing line. The separate native
action_update_fpos_values also recomputes unit prices, so do not invoke it
implicitly. Preserve native country/tax consistency and posted-state refusal.
This finding does not add a command or authorize configuration/source repair.

## Financial invoice headers and advance payments — 2026-08-31

The batch adds partner_bank_id/fiscal_position_id to the two invoice/bill create
inputs and invoice.update.changes, and reads both IDs/null through invoice.get.
No IDs or schema files are added: 355 mixed-domain IDs, 340 enabled handlers
(210 read/130 write), 685 schemas; statuses remain 307 unconfigured, 33 degraded,
15 disabled. Registry changes only describe the new reference dependencies and
test files. Its current raw SHA-256 is
4cd4a7e99d28ab683b292fc3daae82c099c262a42bdfb24313a325e851b328da.

Strict nullable IDs, omitted-field preservation, create-key conflicts, draft
updates, current-state replay and native write readback reuse existing paths.
Selected banks must be active, visible to the configured user and shared/current
company. Do not add a UI-only recipient-owner rule: native
account_move._compute_partner_bank_id prefers a payment method's journal bank
before the usual recipient-bank selection. Currency and allow_out_payment are
native sorting preferences, not hard bank-selection constraints. This field
selection does not verify or execute a bank-payment instruction.

Fiscal-position scope uses company_id parent_of [selected_company], matching
the installed model's company rule and relation checks. Explicit input does not
invoke action_update_fpos_values or independently remap caller-supplied accounts,
taxes or prices. Native dependencies and country/tax constraints still apply.
The get-only load=None read avoids fetching display names for bank/fiscal-position
relations; invoice.search and its public contract are unchanged.

Necessary local checks pass: 263 new contract/runtime/read cases, 62 selected
existing create/update cases and the registry consistency case. The original
combined local selection had one outdated exact test-reference expectation;
the registry test was updated for these three commands and passed separately.
This is a test-metadata correction, not an Odoo business-operation failure.

Server focused regression passed 622 cases and one authorization skip in 172.91s,
exit 0. The separately authorized shared real case passed both aliases: 1 passed
in 709.21s, exit 0. Each alias verified 48 CLI calls / 12 existing capabilities /
14 immediate replays, customer advance 120 and supplier advance 90 before later
invoicing/posting, zero residual after reconciliation, eight posted journal items
and trial-balance debit/credit delta 420/420. This is untaxed company-currency
in-process CLI/real-ORM evidence, not external bridge, durable replay, concurrent
execution, FX, tax or bank-matching acceptance.
Business execution is uid 5/su=False/company 1 in only odoo_cli_v4_dev
and odoo_cli_v4_e2e, with unconditional rollback and a fresh-cursor superuser
read-only residual audit. It does not run bank.transaction.match or change bank,
tax, journal, fiscal-position or access configuration. Existing eligible bank
accounts and fiscal positions are absent; actual nonempty selection/clearing
therefore remains unverified despite the passing null/omission workflow. A final
superuser read-only SQL count independently found zero rows in res_partner_bank
and account_fiscal_position in each of the two synthetic databases; each count
transaction explicitly rolled back. This absence check is not a business-user
write test or permission expansion.

Baseline local/GitHub commit: 47b3e13f214a48f4ed3b8ca5765a9951faac9cf5.
Private artifact directory, on both local workspace and server:
.tooling/accounting-financial-headers-20260831-fc900013.

- before-code.tgz contains fourteen existing files matching baseline Git blobs;
  the four new test paths were absent. SHA-256:
  576e64d9845f32c8b4754995dd813e72a77c4db230dce94f804d17d0f7f9bda2.
- code.tgz contains eighteen code/test/schema/registry files. SHA-256:
  73d763e56ff5fd8266a06a140256cf877be58d8399b2596ffa24ba7121d54908.
- code.sha256 verified every deployed file. Existing ownership and modes were
  restored after extraction; new test files use mode 644 and the runtime owner.
  The pre-change archive and metadata are also downloaded locally and hash-checked.
- Runner/process group 3065111 is finished and empty. focused.exit and
  live-smoke.exit are both 0. The shared run UUID is
  c580091b-a20a-4a4c-9005-fd0c4b6aaddd. Preserve the completed logs and archives.
- focused.log SHA-256:
  10c266df6c3ab1e63ce7fb12ef3cddf8d9ac0d894f6b7b03c87bdd1bfd718ed1.
- before-docs.tgz contains the three baseline documents, SHA-256:
  798f218f7710db4899735ba601556edcdcfd242c5c5f0230513a18a496e6b400.
- live-smoke.log SHA-256:
  6f27a4bc50d51d58dccc14615ea4985b949861ef2058f8851bd7b6d6e9d7833c.
- Before and after this run, Odoo19 remained PID 2855713 / NRestarts 3 / active-running;
  Nginx and PostgreSQL were active, and the protected exchange-rate addon matched
  724ae3b4eb753b00b273d96641ce7639473a6f37740b6ce3aeba5ca669ee54e9.

The earlier bank and deferred failure logs still match their retained hashes:
dbd3480e6bf7cd4bdf5a55a481cc2266c5ab6f41fd3bd6b1b2bcfc31b8f56685 and
0b5a18470dbb10de1100693f3eb67778e2915ad3c011589dba87bb5bee440fbe.
Their blockers, the actual journal-switch fixture gap and nonempty financial
reference selection remain unresolved; none is turned into a passing workflow.

The completed logs/exits and both pre-change archives are retained locally and
on the server in the same private artifact directory. final.sha256 covers the
eighteen code/test/schema/registry files and the three updated public documents.

The server Git HEAD remains 2e190bcdd70313c0a10dcc479e1a2834db240a50. Its accumulated
working tree is intentional; never reset or pull over it. No service restart,
installed-source edit, dependency change or business-database write is authorized.

## Tax-linked journal items and populated tax reports — 2026-08-31

This batch extends journal_item.search/get with tax_line_id (ID/null), tax_ids
(sorted unique IDs, possibly empty), and tax_base_amount (signed company-currency
decimal). Both paths use native search_read(load=None) and reuse the shared item
schema. They do not read related tax display names, add tax-model ACL requirements
to journal-item reads, elevate the user or change company scope.

It also fixes a real populated-report defect: Generic Tax group rows have
no_format='' for net, while the tax detail rows carry numbers. Only report.tax's
exact empty net cell becomes null, never zero. Empty tax amounts, whitespace and
numeric strings remain invalid; other financial-report behavior is unchanged.
Native source account_generic_tax_report.py:518-525 supplies the blank, and
account_report.py:3106-3153 preserves it in no_format. No report framework or
configuration is added.

Counts stay 355 mixed-domain IDs / 340 enabled implementations (210 reads,
130 writes) / 685 schemas, with 307 unconfigured, 33 degraded and 15 disabled.
Registry SHA-256 is
409af5cb25a85e7a31e067b6d3addcd94d562d52721fbbdb4cb34f366f16f977.
These are not pure-accounting totals or a completion percentage.

Necessary server checks, in separately logged phases, passed:

- 199 journal-item cases in 27.04s and nine report/registry/helper cases in 27.31s;
  the shared live entry was skipped while its authorization flag was off.
- Two test-helper checks in 0.69s, after removing a needless ir.model metadata
  access from the fixture setup. Ordinary accounting users do not need that
  administrator-only permission.
- 28 report/amount/helper cases in 15.68s after the empty-net adapter correction.
  Its new reproduction failed before the change and passed afterward; it also
  verifies strict tax amounts and no blank-string relaxation in trial balance.

The final shared case passed: 1 passed in 501.48s, exit 0, covering both v4-dev
and v4-e2e. Per alias it ran 34 CLI calls / 11 existing capabilities / six immediate
replays and inspected six current posted journal items. It creates customer and
supplier documents at 100+13, then replaces the draft lines with quantity and
discount changes: sales 2 x 100 less 10% = base 180, tax 23.40, total 203.40;
purchases 3 x 50 less 20% = base 120, tax 15.60, total 135.60.

Existing taxes 5 (sale) and 11 (purchase) are 13%, price-excluded, on-invoice.
No tax or repartition configuration is created. Invoice/group totals, tax IDs,
signed tax bases, tax-account balances, and search/get equality all pass. Native
sales tax base/credit balance are negative on journal items, and the generic tax
report reverses that display sign. Only the actual tax-ID child rows are compared
against their pre-write report baseline; parent totals are not added again.
Trial-balance debit/credit increases are 339/339 with zero net difference.

The 11 capabilities are tax.get, customer_invoice.create, vendor_bill.create,
invoice.lines.replace, invoice.get, invoice.tax_breakdown.inspect, invoice.post,
journal_item.search, journal_item.get, report.tax and report.trial_balance.
Business execution is uid 5/su=False/company 1, only in odoo_cli_v4_dev and
odoo_cli_v4_e2e. All synthetic records roll back; the separate fresh-cursor
superuser read-only residual audit also passes. This is in-process CLI/real-ORM
evidence, not external bridge transport, concurrent/durable replay, statutory
returns, price-included/cash-basis tax, tax refunds or FX-tax acceptance.

Preserve both earlier failed runs and their completed rollback audits:

- live-smoke.log: 4.32s, failed on the unnecessary fixture ir.model read before
  any CLI call; SHA-256 c47828358971681509cffb504bd746af15521258fd5aca9bc2d82e956040d94a.
- live-smoke-corrected.log: 251.96s, first-alias invoice and journal-item checks
  passed, but the final populated tax report hit the empty-net defect;
  SHA-256 9a05573e21f5b554ecf0c4067a8d2f055d1c521ef2527f7b723688b1739d5453.

Baseline local/GitHub commit is 07d0aa9747804819e0c2a91c4d6863270fecf972.
Private artifact directory: .tooling/accounting-tax-flow-20260831-6766e3c4.
Thirteen code/schema/registry/test files were deployed. Initial deployment backed
up nine existing targets and added two test files; the report correction backed
up its two additional existing targets. Existing ownership/modes are preserved.

- before-code.tgz SHA-256:
  4798677597739a1bebd11819a0e990a622ff5c57d517c5425ef1c81ab68a1da5.
- before-helper-fix.tgz SHA-256:
  576e81c9b58c57dc3defaaeb0890f98352c540b62860044fe53b6026a538860b.
- before-report-fix.tgz SHA-256:
  6ef4a9edf7fe2ff3f7e3f54e751d0f3617f5b8ccb1d347001f1cc289c71d2d70.
- before-docs.tgz SHA-256:
  0776b914f19a08f4123d5d222a018abdf2e05b1bcced4ada263e133c2908681c.
- Successful live-smoke-report-fixed.log SHA-256:
  c4968b4b1d35a125ea9373994978b915d62ea6e97a8298deae0a06ac1a9ef4e3.
- The successful run UUID is 57ecea6e-061f-408f-9378-b388b5704baf. Process groups
  3146781, 3151709 and 3162676 are finished and empty. report-fix-code.sha256
  identifies the final thirteen code files; final.sha256 also includes the three
  public documents. Earlier code archives/manifests deliberately remain unchanged.

Odoo19 remains PID 2855713 / NRestarts 3 / active-running. Nginx and PostgreSQL
remain active. The protected installed addon and prior bank/deferred failure
logs retain the hashes in the preceding checkpoint. There was no service restart,
business-database write, installed-source edit or configuration/permission change.
The server Git HEAD remains 2e190bcdd70313c0a10dcc479e1a2834db240a50; do not reset
or pull over its accumulated working tree.

Next candidate is the accounting cash-refund path for an already settled invoice:
financial credit, opposite-direction customer/supplier payment record and
reconciliation, using existing commands. This is not an actual bank transfer and
must not be confused with bank.transaction.match. Determine any contract gap before
adding code. Known bank configuration, asset/deferred addon, alternate-journal and
nonempty financial-header fixture limitations remain unresolved. No new overall
completion denominator or second-stage control project is introduced here.

## Cash-refund registration checkpoint — 2026-09-01

The preceding taxed-invoice batch is committed at
9bc4180c7ea41ee5f081962c2eb6c65a33d21aba, the local baseline for this batch.
Counts remain 355 mixed-domain IDs / 340 handlers / 685 schemas. Registry SHA-256
is aafdbd1570639a61c3be8a4c53999ed6ed7904a694a9d7548443b696dabaa2e1.

Two existing commands are extended, not replaced or supplemented with new IDs:

- receivable.payment.register accepts out_invoice and out_refund.
- payable.payment.register accepts in_invoice and in_refund.
- Native account.payment.register determines direction and customer/supplier type.
  Refund amounts stay positive; customers receive outbound refunds and suppliers
  return funds through inbound payments. Request/response schemas, operation keys,
  company scope and ACLs are unchanged. Registry summaries/aliases expose refunds.
- Explicit write-off readback uses the actual source type: out_invoice/in_refund
  positive; in_invoice/out_refund negative. Refund write-off is unit-tested here,
  not added to the shared live scenario or claimed as live acceptance.

The production change is confined to source-family selection and difference sign.
Local necessary regression passed 317 tests in 6.42s, after four refund cases first
failed against the old source-type filter. The initial broader registry run had
18 passes and one failure because the new evidence references were not in its old
expectations; the aligned write-registry test then passed in 6.31s, with one
authorization skip for the live file. No business smoke ran on the local machine.

Private artifact directory: .tooling/accounting-cash-refunds-20260831-6d31f902.
Six code/registry/test files are deployed after a five-existing-file backup;
test_invoice_cash_refund_batch_live.py is the new file. Existing file ownership
and modes are restored. The server baseline was compared by Git blob against the
local pre-batch commit before any overwrite; deployed bytes match deploy.sha256.

- before-code.tgz SHA-256:
  820318dc5b89e41651cd21cd63f11e0e4fc84469fc2b0a0165517faf58d079da.
- code-final.tgz SHA-256:
  e9491b333dcc0df15b3b69190a4c55912c00556d2ba7f9efe441fb417f983c9f.
- before-docs.tgz SHA-256:
  abc35890fbc36e0831f5af25a95d00992635bc9f473addadca0ede36f950bd4f.
- Server focused regression: 318 passed / one authorization skip, 21.72s, exit 0.
- Shared live run: 1 passed in 919.40s, exit 0. Run UUID
  565204ee-7264-41f4-9fab-50df73d5533d. Runner/process group 3197634 is finished
  and empty. focused.log SHA-256 is
  62a00106261cfd3944b360674ffa64b3ecb30dd3d50cf691e39c8592970db306;
  live-smoke.log SHA-256 is
  228602009c8e96cab9e662e6ab8199e698c106185890f06b1860756c1c17ff17.

The shared scenario targets each isolated alias with uid 5/company 1/su=False:
settle customer invoice 100 and supplier bill 100 first, then create/post customer
credit 40 and supplier refund 60. Record customer refunds 20 plus default remainder
20 and supplier refund receipts 30 plus default remainder 30. Verify that original
reconciliations remain unchanged, credit residuals decrease to zero, refunds use
opposite payment directions, and posted storno journal items balance. Each alias
passed 12 existing capabilities / 62 CLI calls / 14 immediate replays, six payments,
20 journal items, six partial/four full reconciliations and trial-balance debit/
credit delta 400/400.

All business activity must roll back; the reused fresh-cursor residual audit is
separately superuser read-only. The existing CNY/storno/manual-payment fixtures are
read, not reconfigured. This is not a bank transfer, bank-statement matching,
foreign-currency/taxed-refund, external bridge or durable/concurrent replay proof.

Next bounded candidate is correction of an already reconciled refund: payment.cancel
or payment.reset_to_draft, with restored credit residual and the other refund/original
settlement preserved. Both commands already exist; prior smoke checks cancellation
state or an unallocated payment reset, not this complete refund-correction result.
Inspect for an actual gap before changing production code. Known bank configuration,
asset/deferred addon and financial-reference fixture blockers remain unchanged.

After the run, Odoo19 remains MainPID 2855713 / NRestarts 3 / active-running;
Nginx and PostgreSQL remain active. The protected addon and earlier bank/deferred
failure logs retain their recorded hashes. No service was restarted and no master
configuration, permissions, installed Odoo/addon source or business database was
changed.

## Grouped invoice/bill payment checkpoint — 2026-09-01

The local baseline is c1e4b1ae889af2e83471a28a0b35c20c039711be. Counts remain
355 mixed-domain command IDs / 340 handlers (210 reads, 130 writes) / 685 schema
files; no command ID or schema file is added. The final registry SHA-256 is
272fcf3c261ee1b36f7f2471545e41bf803bdc4d9ed5875d3acf3baf12f1d38f.

Two existing write commands gain a deliberately narrow multi-document mode:

- `receivable.payment.register` accepts `move_ids` for two through 100 posted
  customer invoices (`out_invoice`) and creates one full customer receipt.
- `payable.payment.register` accepts the same shape for posted supplier bills
  (`in_invoice`) and creates one full supplier payment.
- Multi-document requests allow only `move_ids`, `journal_id` and `payment_date`.
  Source IDs must be distinct and are sorted before hashing. Every document must share
  company, exact move type, partner and currency, have positive residual,
  and form one native Odoo payment-register batch. The wizard must return exactly
  one payment. Partial amounts, write-offs and refunds remain on the unchanged
  single-`move_id` path.
- The operation key binds the normalized source set; the marker is stored on the
  payment. Replay validates that marker, date, journal and exact source-document set,
  including after all residuals reach zero. Generic payment readback intentionally
  does not claim source reconciliation IDs; live acceptance verifies reconciliation
  through all source invoices/bills.

Nine files form the implementation checkpoint: the registry, two request schemas,
the core write contract and runtime, one existing registry test, and three new
payment-register-many tests. Necessary local regression passed 234 tests with 576
deselected in 313.82s; the initial new contract/runtime/registry selection passed 43
tests in 24.80s. Pre-commit review found one contract/bridge mismatch: the public
layer generated the grouped deterministic key while a direct bridge payload could
provide an arbitrary key. The bridge now computes the identical key and rejects a
mismatch before model access. Registry line endings were also normalized to LF so
deployed bytes, committed bytes and the documented SHA agree. After those corrections,
41 contract/runtime tests passed in 7.20s and the registry-alignment test passed in
7.30s; a combined selection passed 42 cases with 18 deselected. Ruff passed for the
changed Python files, and the live integration module compiled and skipped cleanly
without authorization.

Private server artifact directory:
`.tooling/accounting-grouped-payments-20260901-f8f80a94`.
The six pre-existing code targets were archived before deployment, all deployed
bytes were hash-verified, and the corrected test file was separately backed up
before replacement.

- `before-code.tgz` SHA-256:
  e4f2c75c5c80b7cacc92424520922148c86fca1809a4d5f2d14b47b0f0d17a00.
- `before-live-test-fix.tgz` SHA-256:
  28b51c95993a7489a4a550425aeab99c974a68249a695ff06fcc92ff6a5b7373.
- Pre-review `code-final.tgz` SHA-256:
  e8a549dc1b15439cf7141db9ae76c7acb3b9ae5efd50c7b6a305b5b261c46da8.
- `before-key-binding-fix.tgz` SHA-256:
  4522da5ebc925645881724be020a8ab64e49ac3a47224208dee9bff57bba66a5.
- Final `code-final-keyfix.tgz` SHA-256:
  cf01d4f3110dcbd97d6ecd385eed9dcbd14ef11edae96cd9d1e7ad07f05b4f1b.
- `before-docs.tgz` SHA-256:
  57b5d9ca425001bcf57299159aff3b53116b7f79630706462d33491119e79cdd.
- Server focused regression: 234 passed / 573 deselected in 220.88s, exit 0;
  log SHA-256 49c537c5fdd5e4d2643bcfae1c75fb330edaefa010842bf0c1a75615ebc876ea.
- Server registry selection: three passed in 20.27s, exit 0; log SHA-256
  e4f22fc7749a73d5094f57ceb56fe6589cf17ae65668409845c22b00b8d8d3b4.
- Final server key-binding/contract/registry selection: 42 passed in 14.68s,
  exit 0; log SHA-256
  7bc02cfa6c036832a3b56d1ce2efcca7b203a2d6abbea3b9ddd97a138989fcd7.
- Corrected shared live workflow: one passed in 482.74s, exit 0; log SHA-256
  964c186ee810336dc8c67289f7c1e72ba58a00fcf8730b1506c6e3e71e3bbc21.

The first live attempt is retained, but is not counted as acceptance. It failed
after 145.54s solely because the new test asserted that the generic payment result
must expose partial-reconciliation IDs. The worker completed rollback and the
fresh-cursor residual audit before raising. The assertion was corrected to check
the four source documents; production code was unchanged. That failed-attempt log
SHA-256 is f1927491114351cf22e1a165cacab548564706babecdbd84000369ff7159fab1.
The successful live run was not repeated after the key-enforcement correction:
it already entered through the public layer with the same final deterministic key,
while the new local/server unit case covers rejection of a forged bridge key.

The successful shared scenario ran against both isolated aliases as uid 5,
company 1, su=False. Per alias it created and posted two customer invoices and two
supplier bills, registered one combined receipt and one combined payment, exercised
nine existing capabilities through 30 CLI calls with ten immediate replays, and
observed trial-balance debit/credit delta 400/400. Across both aliases that is 60
calls, 20 replays, eight source documents and four combined payments. All business
records rolled back; a separate fresh-cursor read-only audit confirmed no residual
records. No worker remains. At 10:24:27 CST, after the final tests, the pre-existing
Odoo19 process exited with `ModuleNotFoundError: passlib`; systemd restarted it at
10:24:38 as PID 3995891 / NRestarts 4. The same approximately daily failure appears
on August 29-31. This deployment did not issue a restart or alter that environment.
Odoo19, Nginx and PostgreSQL are active. No installed addon, permission,
configuration or business database was changed. The server Git HEAD intentionally
remains 2e190bcdd70313c0a10dcc479e1a2834db240a50; do not pull or reset over that
working tree.

Internal bank transfer is not included. The current isolated configuration has only
one suitable bank/cash journal per database, and source inspection did not establish
a native Odoo 19 action that safely creates the paired transfer required by this
CLI contract. Do not synthesize two unrelated payments and call that complete.
The following checkpoint implements the then-next bounded candidates,
`invoice.duplicate` and `invoice.type.switch`. A payment-hold flag remains outside
this batch because it is not payment enforcement, and fiscal-position application
still lacks safe writable fixtures.

## Invoice duplication and type switching checkpoint - 2026-09-01

The pre-batch local/GitHub baseline is
`e7ab43be4fda36f82eb2b9840ebdd3dc5d801af6`. The registry now contains 357
mixed-domain IDs and 342 enabled handlers (210 reads and 132 writes), with 309
`unconfigured`, 33 `degraded`, and 15 `disabled` statuses. There are 689 public
schema files. The exact sorted-ID SHA-256 is
`70afbb625e34ce065b06e4d058fd1ff9c41b17174f80e15109b246e0824ec8c3`;
the registry-file SHA-256 is
`631c6e916c6ff2248a000995395dc9890e7d00d366ebf7fd0b60009c125f75cd`.
These mixed-domain totals are implementation inventory, not an accounting
completion percentage.

Two fixed write capabilities are added:

- `invoice.duplicate` accepts only `move_id` and a caller-chosen operation key.
  It uses native `account.move.copy()` for `out_invoice`, `out_refund`,
  `in_invoice`, and `in_refund`, then verifies a distinct, unpaid, never-posted
  draft of the same type. Same-key replay resolves the same draft; a changed
  source conflicts, while another valid key deliberately creates another copy.
  Human `invoice_origin` tokens are preserved, inherited `ODACV4/ODACV4K`
  tokens are stripped on copy-of-copy, and the new key/fingerprint markers are
  appended in one write. A 400-character native origin is covered without the
  unrelated period-transfer helper's 255-character limit.
- `invoice.type.switch` accepts only `move_id` and one of the four fixed financial
  document types. The exact deterministic key is
  `invoice.type.switch:{move_id}:{target_move_type}`. Runtime permits only a draft
  with `posted_before=False`, treats an already selected target as replay, and
  otherwise allows only the native customer-side or supplier-side counterpart.
  It calls `action_switch_move_type()` and verifies the same move ID, target type,
  and draft state. General journal entries and cross-side conversions fail closed.

The batch retains native business-user ACLs and company/record-rule scope.
Duplication requires fixed `account.move` read/create/write and
`account.move.line` read/create access; type switching requires fixed
`account.move` read/write, `account.move.line` read/write, and `account.tax` read
access. There is no sudo path, configuration change, arbitrary ORM dispatcher, or
business-database write target.

The shared workflow exposed a separate legitimate read edge. Odoo 19 stores an
unnamed draft move as `name=False`; `journal_item.search/get` previously rejected
the normalized item because their public contract required a nonempty move name.
The runtime now maps only native false/none/empty to JSON null, the public contract
accepts null or a nonempty string, and the shared search-item schema uses
`string|null`. `journal_item.get` already references that item schema. Empty and
whitespace move names remain invalid, and the journal item's own line name remains
a string. This does not synthesize `/` or another document number.

Twenty-two final code/schema/registry/test files were deployed together. Fifteen
pre-existing targets matched the local pre-batch Git blobs before overwrite and
were archived; seven new paths were verified absent. Existing owners/modes were
restored and every final deployed byte matches `deploy.sha256`. Necessary local
evidence includes the 51-case contract/closure selection, 20 invoice-copy/type
runtime cases after the long-origin correction, and 849 affected journal-item
public/runtime/schema cases. Ruff, JSON parsing, Python compilation, and
`git diff --check` passed. Independent reviews found no blocking contract/runtime,
ACL, schema, count, or live-test inconsistency.

Final server regression passed 901 cases in 95.97s, exit 0. The shared real-Odoo
workflow passed both isolated aliases: 1 passed in 687.67s, exit 0, run UUID
`a6536a63-fa30-4da5-a601-0a3a4bd33c24`. Per alias it ran as uid 5, company 1,
su=False and verified seven capabilities through 46 CLI calls and 12 immediate
replays. It created and posted one customer and one supplier source, duplicated
both into distinct drafts, created two additional never-posted drafts, switched
each to its financial refund counterpart and back, and reread the documents and
journal items. Header/line business signatures, amounts, new line IDs, unchanged
originals, balanced entries, storno sign inversion, and balance restoration passed.
Each alias tracked six `account.move` records; all synthetic rows rolled back and
the separate fresh-cursor residual audit passed. No worker remains.

Three unsuccessful runs are retained and are not counted as acceptance:

- Attempt 1 failed in 26.90s before invoking either new command because the live
  fixture supplied a custom key to deterministic `invoice.post`. The fixture was
  corrected to `invoice.post:{move_id}`; rollback/residual verification passed.
- Attempt 2 failed in 78.99s after duplication succeeded, when
  `journal_item.search` rejected the duplicate's valid unnamed draft move.
  Rollback/residual verification passed.
- A separately retained diagnostic run printed the normalized native
  `move.name=false`, proving the exact read-contract defect. Its diagnostic test
  file is archived and is not the final deployed test. The scoped runtime/public/
  schema correction then passed 849 local cases and the final 901-case server run.

Private artifact directory:
`.tooling/accounting-invoice-copy-type-20260901-42f9c7d1`.

- Initial six-target backup `before-code.tgz` SHA-256:
  `73e40b3b620c09a11a5d6b0c39119035f0218f5dde1da073a1052683c93bb69f`.
- Three frozen-closure targets `before-frozen-closures.tgz` SHA-256:
  `0184d7622df4a00d4e71514db5bceff7497cd3f9546bc4266bd4e1e5aeab006a`.
- First live-test correction `before-live-test-fix.tgz` SHA-256:
  `34f46b69861ffba43c463340e5b1d6b8f553b21f12d716b9546a0e4328fcc392`.
- Pre-diagnostic live test `before-live-diagnostic.tgz` SHA-256:
  `3cca39c2cb52821cbd62d27d5699c926cc9563d0674244175d456a1a7b5e9996`.
- Six-target draft-name backup `before-journal-item-draft-name.tgz` SHA-256:
  `fc16e558f57dc7bf7674408cd17f3b69787639e1416c59d61705480fe019c75f`.
- Diagnostic live test archive `diagnostic-live-test.tgz` SHA-256:
  `2f1ac4532c34a69aa2fee7644c65cd869effb6b8cf30953cd58c9fe9dcebf737`.
- Pre-change public documents `before-docs.tgz` SHA-256:
  `fde6566181368de3d26e7d4901cf697ba8f10b0a50cee9dcbe9968c1600994e4`.
- Final 22-file `code-final.tgz` SHA-256:
  `da4f7ebc06af15aba7ea941038229076adf913cad66a01c6c1ca8f9eea888aa3`.
- Final focused log SHA-256:
  `6956c5639a0cdbd9610ed92485462bb6f3c747352865088f7086621284ad7676`.
- Final passing live log SHA-256:
  `5013208c4ededde58d2d6e45d3471d5d15eda85980ed123ab404bce2d0094baa`.
- Failed attempt logs SHA-256:
  `03044ef73d1f0bc39c4f46ac064c411c37f5bdbac9b47b225c7a098bdac0c722`
  and `4108aa49bdbb1c355e56278379b0e9fd72693e1597ff579fddd5d48c3b5d106c`.
- Diagnostic log SHA-256:
  `f1fc3c9bfe93e1bf1c575ec847667607569cb43f19d3614549ab17f76917dfbe`.

Before and after deployment and all live runs, Odoo19 remained active as PID
3995891 / NRestarts 4; Nginx and PostgreSQL remained active. No service-control
command, installed Odoo/add-on edit, permission/configuration change, or business
database write was issued. Server Git HEAD intentionally remains
`2e190bcdd70313c0a10dcc479e1a2834db240a50`; do not pull or reset over its
accumulated working tree.

Acceptance is deliberately bounded: the real workflow used positive, untaxed,
company-currency documents with `account_storno=True`. The native negative-total
and taxed switch branches remain unaccepted. Marker-based duplicate replay has no
database uniqueness constraint or lock, so concurrent same-key exactly-once
creation is not proven. These are later coverage/control gaps, not reasons to add
speculative framework code to this capability-first batch. Select the next compact
accounting batch from a re-audited module/workflow/lifecycle gap, not from command
count or historical stock operations.

## Accounting-delivery checkpoint — 2026-09-01

This batch starts from local/GitHub baseline
`862bdf926558ff4112578299df39256294db6525` on `rebuild/v4`. It adds exactly nine
capability IDs:

1. `invoice.send.inspect`
2. `invoice.send`
3. `payment.receipt.send.inspect`
4. `payment.receipt.send`
5. `report.customer_statement.export`
6. `report.customer_statement.send`
7. `report.followup.export`
8. `report.followup.send`
9. `invoice.followup.update`

The proposed `journal_item.followup.update` was removed before delivery. Odoo 19's
journal-item field is computed/inverse-coupled to the whole invoice and does not
provide an independent line-level follow-up state; keeping that command would have
created a misleading duplicate of the invoice-level operation. The final registry
is 366 mixed-domain IDs / 351 enabled handlers (214 reads and 137 writes) / 707
schemas, with 314 `unconfigured`, 37 `degraded`, and 15 `disabled`. Registry file
SHA-256 is
`ddc36d6eaad3fedeea4927244316112d52be02136ed30eeecd3b2750e2edb083`.

The two native send handlers return `record_ids` and `processed_count`; this means
Odoo accepted/processed the targets, not that an external mailbox received them.
They force `mail_notify_force_send=False`, verify a marked `mail.message`, and
support immediate serial replay. They do not promise mail-queue persistence,
external SMTP delivery, concurrent same-key exactly-once behavior, or reversal of
already queued mail. The two inspection commands are rollback-only reads of native
wizard readiness. Customer-statement and follow-up exports use the fixed native
account-report export path. `invoice.followup.update` writes the invoice/bill
`no_followup` value and verifies the receivable/payable term-line propagation; it
does not target customer receipts or independent journal items.

Local verification completed as follows:

- 344 broad affected registry/contract/delivery/export cases passed in 578.84s.
- 299 focused delivery and financial-export cases passed in 64.87s.
- 662 central core-write compatibility cases passed in 2064.62s.
- The final 53-case registry and live-evidence closure passed in 308.05s.
- Ruff checks, Ruff formatting for new/touched batch tests, JSON parsing,
  integration collection, Python compilation, and `git diff --check` passed.
- Independent final review found no remaining P1/P2 defect. Remaining P3 coverage
  debt is plural/batch positive live execution, invoice receipt/credit-note send,
  supplier-bill follow-up update, and exact ACL-metadata symmetry.

Server deployment used a fixed 41-file allowlist: one registry, eight source files,
18 schemas, 13 unit-test files, and one integration test. Fourteen existing targets
were archived and 27 paths were new. The server tree has mixed historical
ownership; the initial attempt to extract as `odoo` stopped before overwrite because
root-owned 0755 directories do not allow new files. The successful path extracted
only the allowlisted files as root, then restored every existing target's recorded
UID/GID/mode individually. No directory permission was changed and no recursive
source ownership operation was used.

Server evidence:

- Focused regression: 344 passed in 781.53s, exit 0.
- Shared real-Odoo smoke: 1 passed in 319.93s, exit 0, run UUID
  `56c1ee25-adc7-40f1-9c28-807def54f8c8`.
- Final post-live metadata closure: 53 passed in 339.05s, exit 0.
- Each alias ran as uid 5, company 1, `su=False`. All nine target commands were
  exercised; seven completed positively. `report.customer_statement.send` and
  `report.followup.send` returned the expected clean authorization denial because
  configured uid 5 has `res.partner:read` but not `res.partner:write`. Their generic
  implementation remains available to eligible users, but positive native report
  sending is not yet accepted and stays `planned` in registry evidence.
- Each alias verified two readiness inspections, two valid PDF exports, two native
  marked messages, three immediate replays, invoice/receivable-line follow-up
  propagation, no external-delivery claim, outer rollback, and fresh-cursor residual
  absence.
- Both fixed test customers have no email, while uid 5 cannot create or write a
  partner. A test-only sudo recordset therefore applied a temporary
  `example.invalid` email to the existing customer inside the same outer transaction.
  Every CLI call still ran as uid 5 with `su=False`; a fresh cursor proved both
  customer emails returned to null after rollback.

Four failed live attempts are retained and not counted as acceptance:

- Attempt 1 stopped before a target command because the test reused the unrelated
  split-receipt fixture, which requires an outstanding account absent from these
  isolated databases. Its attachment audit also mixed Odoo's implicit `res_field`
  filter with an explicit ID query; both test-only dependencies were removed.
- Attempt 2 supplied a caller-selected key to deterministic `partner.create` and
  was rejected before Odoo write access.
- Attempt 3 used the proper key but was correctly denied because uid 5 cannot create
  partners; the test switched to the existing isolated fixture partner instead of
  changing ACLs.
- Attempt 4 incorrectly asserted that every core fixture write has a mandatory
  framework-generated key. The test now uses the framework key when required and a
  normalized-parameter hash when caller selection is permitted.

Every failed worker rolled back and passed residual verification. The first focused
server command also retained a non-test attempt that ran zero cases because its cwd
was omitted; the corrected attempt is the 344-case result above.

Private server evidence directory:
`/opt/odoo-accounting-cli-v4/.tooling/accounting-delivery-359fb86e-63d4-47b9-95cd-ea09c856afed`.

- Original-target backup archive SHA-256:
  `b1b72e228b8a2a8265089df3da1b643c44a1a8dd29aed050d4d778831180fe05`.
- Final 41-file deployed snapshot SHA-256:
  `e38f86f57348f202be9f4bdd48ad2fbe26619c014edd85fc7700005c9961f08e`.
- Successful 344-case focused log SHA-256:
  `df05d8cf7bc3b611a82d1463e99a6a8de30ffc0f62eb7fffab91acb943325555`.
- Successful dual-alias live log SHA-256:
  `1887848a69ae83c01a4ac985a83d43475e717d9150108bf04c8a7b565dcac0fc`.
- Successful final metadata log SHA-256:
  `102d592df49ac12dd5b478c3452d459bac2a072d19bcf7321602f02dd8e74265`.

Before and after deployment, tests, and live workers, Odoo19 remained active as PID
`3995891` with `NRestarts=4`; Nginx and PostgreSQL remained active. No service was
restarted. Root filesystem use remains 96%, so future work must continue using
small per-batch backups. The remote Git tree remains intentionally old and heavily
dirty; never use pull/reset/checkout as deployment. Continue with explicit file
allowlists, pre-overwrite backups, and byte verification.

## Batch lifecycle support checkpoint — 2026-09-01

This batch starts from local/GitHub baseline
`8a24a0848a74b0ece19aed989f48b1554066e8ec` on `rebuild/v4`. It adds no
capability ID and no production handler. The authoritative totals are 366
mixed-domain IDs, 351 enabled handlers (214 reads and 137 writes), 708 schemas,
314 `unconfigured`, 37 `degraded`, and 15 `disabled`. Registry-file SHA-256 is
`4a80f295b9b0008fee915af6d7612e8f7a2067099009fc40bd3e0e8d1b71f7df`.

The following nine existing capabilities now accept either their original
singular field or a closed batch field:

1. `invoice.post`, `invoice.cancel`, `invoice.reset_to_draft`
2. `journal_entry.post`, `journal_entry.cancel`,
   `journal_entry.reset_to_draft`
3. `payment.post`, `payment.cancel`, `payment.reset_to_draft`

Invoice and journal-entry commands use `move_id` or `move_ids`; payment commands
use `payment_id` or `payment_ids`. The plural form requires 2-100 distinct positive
integer IDs. Public validation rejects duplicates and mixed singular/plural input,
then normalizes IDs into ascending order. The deterministic key binds the complete
normalized ID set and company, so caller order cannot create a different operation.
Batch responses use the shared `core-write-batch-result` schema with sorted
`items` and an exact `processed_count`; singular response shapes remain unchanged.

Runtime execution resolves the complete record set and validates access, company,
document type and every state before changing any record. Invoice and journal-entry
transitions use the native recordset action. Payment transitions call the native
action once per payment only after the complete preflight, while retaining the
single outer write cursor and transaction. This narrow compatibility is required
because the installed custom module
`/mnt/odoo/odoo19/custom/addons/exchange_currency_rate` reads `self.is_exchange`
inside a multi-record `account.move` constraint and raises `Expected singleton`.
The CLI did not modify that add-on, the Odoo source tree, configuration or ACLs.
Any propagated ORM error still reaches the existing bridge rollback path; this is
a database-transaction guarantee, not a claim about external side effects from an
arbitrary custom module.

Final review also found and closed one scope gap before commit: batch
`journal_entry.post` had checked `move_type=entry` but had not applied the same
`journal.type=general` boundary as the other journal-entry lifecycle commands.
All three batch journal lifecycles now reject a non-general journal during the
full preflight, before any native action; three parameterized unit cases lock this
boundary.

Local verification included:

- 139 new lifecycle contract cases for normalization, invalid ID sets,
  full-set idempotency keys, bridge/capability result validation, and CLI output.
- 132 existing singular document/payment cases, 642 central core-write cases,
  and 41 grouped-payment regressions passed during production review.
- After the payment compatibility correction, the combined payment-runtime and
  lifecycle-contract selection passed 159 cases in 105.78 seconds.
- After the final journal-type scope correction, the combined scope,
  payment-runtime, lifecycle-contract and registry selection passed 181 cases in
  332.51 seconds.
- The full capability-registry test passed 19 cases; Ruff, JSON parsing,
  compilation, formatting checks for the new standalone batch tests, and
  `git diff --check` passed.

Server deployment and verification used an explicit allowlist only. The initial
29-file archive added one shared schema and two new tests while overwriting 26
existing targets. Before overwrite, those 26 targets were byte-identical to the
local baseline and were backed up. The later compatibility correction backed up
the deployed runtime and the existing payment-runtime test separately before
synchronizing them. Ownership and modes were restored per file; no recursive
ownership or service-control command was used.

Server evidence:

- Initial focused regression: 286 passed in 318.13 seconds, exit 0.
- Intermediate payment-runtime/lifecycle-contract regression: 159 passed in
  136.85 seconds, exit 0.
- Final scope/payment/runtime/contract/registry regression: 181 passed in 309.57
  seconds, exit 0.
- Final shared dual-alias real-Odoo smoke: 1 passed in 487.94 seconds, exit 0.
- Both `v4-dev` / `odoo_cli_v4_dev` and `v4-e2e` /
  `odoo_cli_v4_e2e` ran as uid 5, company 1, `su=False`.
- Each alias created two invoices, two balanced journal entries and two inbound
  payments inside its outer transaction. All nine batch capabilities completed
  their native post/cancel/reset transitions and immediate replay; result IDs were
  sorted and `processed_count` was exact.
- One representative `invoice.post` request mixed a valid ID with a missing ID;
  full preflight rejected it before the valid draft changed. This negative live
  case is not evidence that all nine commands received the same invalid-ID case.
- Both outer transactions rolled back, fresh cursors found no marked records, and
  no live worker remains.

Two failed live attempts are retained and are not acceptance evidence. The first
reported only the public `odoo_write_error`; a diagnostic-only assertion-chain
improvement then exposed the exact stack. In both attempts, invoice and
journal-entry batches had passed before `payment.post` tried to create two payment
moves together. The custom currency module's multi-record constraint raised
`Expected singleton: account.move(...)`. Both worker paths completed rollback and
fresh-cursor residual verification before surfacing the failure. The production
fix was limited to singleton native payment actions within the unchanged outer
transaction; the final dual-alias run passed.

Private server evidence directory:
`/opt/odoo-accounting-cli-v4/.tooling/accounting-batch-lifecycle-20260901-9c04f8fe22ae`.

- Original 26-target backup `before-existing-files.tgz` SHA-256:
  `de8316450408a70221f161e00a7d6df4cda06f6d6f37fe1afa21732cde871f92`.
- Initial 29-file archive `code-and-tests.tgz` SHA-256:
  `92182517eeed738227734511879b2f34276eec3a09bea2f98fa9b411bd25c9ee`.
- Final 31-file archive `code-final-31-files.tgz`: 250614 bytes, SHA-256
  `f52c18b43b13d70f2d65a63b531e8501f05e1670e192879b5fedfe5bf1d373ed`;
  all 31 deployed targets matched it byte-for-byte.
- Pre-compatibility runtime and payment-test backup SHA-256 values:
  `398c6635075e318224f39ff6169e37a9fb208d58e8d5777ae067b3afa78f818e`
  and `7892bd0c966853840dbe387d631078956d572585f48549c7c89d78f6a172c165`.
- Pre-journal-type-scope three-file backup SHA-256:
  `5b8f9b737e87f0ea28628c781f6a000c014275083e2d2ae774ba1279c0c5e024`.
- Final focused and passing-live log SHA-256 values:
  `e9941f9e2cfc4bd1ca62ded3c655ebb46c370dc501f5b8cf1cc14200ce391161`
  and `00e7a4668b58240ee7baf2e374fb5d1a08ef3d195b50e933c47def6e25d4ab12`.
- The first public-error and exact-cause diagnostic log SHA-256 values:
  `5c31e6156b0520e6f59f91c159a5bc30daf1977543752d856aa239731e768eca`
  and `446d11be4810c345c3344b19df087b0275377326d41db2c11f8708f628cfac86`.

Before and after the final live run, Odoo19 remained active on PID `3995891` with
`NRestarts=4`; Nginx and PostgreSQL remained active. No service was restarted.
Root filesystem use remains 96% with about 3.4 GB free, so continue using compact
per-batch backups. Server Git HEAD remains intentionally old and the tree remains
dirty; never use pull/reset/checkout as deployment.

Acceptance remains bounded. The live workflow used positive, untaxed,
company-currency invoices, balanced entries and inbound manual payments. It does
not prove every invoice/payment variant, concurrent exactly-once behavior, a
database uniqueness constraint, external effects from custom modules, or full
Odoo accounting coverage. Choose the next compact accounting workflow from the
remaining module/workflow/lifecycle gap matrix; do not infer completion from the
unchanged command count.

## Foreign-currency settlement workflow checkpoint — 2026-09-01

### Scope and files

This checkpoint starts from committed baseline
`22df4510ead3f0f3ef5402c2467f0b5d0736812f` on `rebuild/v4`. It deliberately
adds no capability ID, schema, registry entry, or production implementation.
Only these two test-side files change:

- `tests/integration/test_foreign_currency_settlement_batch_live.py` is a new
  guarded dual-database workflow.
- `tests/integration/test_payment_bank_capability_batch_live.py` adds the
  existing `OdooCurrencyRateListPort` and `OdooCurrencyConvertPort` mappings to
  the shared in-process public-CLI harness.

The registry remains at 366 IDs, 351 enabled handlers (214 read / 137 write),
708 schemas, 314 `unconfigured`, 37 `degraded`, and 15 `disabled`. This is a
workflow-depth checkpoint, not a command-count increase.

### Accepted workflow

The test uses these twelve public interfaces:

1. `currency.rate.list`
2. `currency.convert`
3. `customer_invoice.create`
4. `vendor_bill.create`
5. `invoice.post`
6. `invoice.get`
7. `receivable.payment.register`
8. `payable.payment.register`
9. `invoice.payment_status.inspect`
10. `payment.get`
11. `journal_item.search`
12. `report.trial_balance`

For each of `v4-dev` and `v4-e2e`, uid 5/company 1 creates a USD 100 customer
invoice and a USD 100 vendor bill at the fixed 2025-01-15 rate of CNY 1.36,
posts them, and settles them on 2025-02-01 at CNY 1.37. It proves:

- source moves balance at CNY 136 each;
- inbound and outbound payment moves balance at CNY 137 each;
- both documents reach zero foreign- and company-currency residuals;
- both payment-status reads link the native reconciliation and payment;
- Odoo creates two separate balanced CNY 1 exchange-difference moves;
- the exchange journal's monthly sequence assigns 2025-02-28 as their actual
  accounting date;
- the trial-balance delta through 2025-02-28 is exactly debit CNY 548 and credit
  CNY 548;
- six writes immediately replay through the existing idempotency path without
  creating another record;
- all marked records disappear after outer rollback and fresh-cursor checking.

Per alias the workflow performs exactly 29 CLI calls: three rate/conversion
reads, two before/after trial-balance reads, and twelve calls for each of the
customer and vendor branches. An independent static review recomputed both the
29-call total and the CNY 548 total and found no blocker.

### Verification and evidence

Local verification passed integration collection, Ruff check, Ruff formatting,
and `git diff --check`. Server collection found exactly the one guarded case.
The final real-Odoo command, run as the `odoo` system user, recorded:

- `v4-dev` / `odoo_cli_v4_dev`: 29 calls, six replays, 548/548, rollback true;
- `v4-e2e` / `odoo_cli_v4_e2e`: 29 calls, six replays, 548/548, rollback true;
- final pytest result: `1 passed in 443.73s`, exit 0.

Private evidence directory:
`/opt/odoo-accounting-cli-v4/.tooling/accounting-fx-settlement-20260901-6d19c2a9f4b7`.

- Initial two-file upload archive: 14275 bytes, SHA-256
  `c8cde2ba3bb1d82b1bb2eb5fe57b237d922cde04c0f6ba072be337a9cc938f15`.
- Original existing-helper backup: SHA-256
  `0d9e080f6813c249b2dcb1bd78feb708a31ca2af19a82ba6027682a9bbeea1b6`.
- Final test file: SHA-256
  `8415273c0f8031d436e26f77a393c53ccf367e0bfa4c09936eb778fe5526578f`.
- Final shared helper: SHA-256
  `2d20199ad019a299c37589319dda45d8fbd8afc2e4c45c47909cecc33a7201b4`.
- Passing attempt-6 log: SHA-256
  `923bc7d8cf2431d098cd546cffe10f413585363fd253a63173ba958e1d6a472e`.
- Corrected server collection log: SHA-256
  `e0199936360688128e2eae2261c0aa60c96e2b4dc2f198785bf7c5b6eb74e3ce`.

Five failed executions remain in the same private directory and are not counted
as acceptance: root peer authentication; decimal-string representation; payment
date versus exchange accounting date; string versus Python `date`; and a report
end date that excluded the exchange moves. The peer-authentication attempt never
entered a database. Every later worker that entered one reached its
rollback/fresh-cursor cleanup before surfacing an assertion. The separate
self-matching process preflight never launched pytest. The first combined server
static attempt also failed only because the project virtualenv has no Ruff; the
corrected server collection and local Ruff checks passed.

After the final run Odoo19, Nginx, and PostgreSQL were all active. Odoo PID
`3995891` and `NRestarts=4` were unchanged; no service was restarted. Root disk
use is still 96%, so retain the small explicit-allowlist deployment approach.
The server Git tree remains intentionally old and dirty; never use pull, reset,
or checkout as deployment.

### Next work

Do not add more variants to this workflow in the same batch. The remaining
foreign-currency variants—partial settlement, early-payment discount and explicit
write-off—stay as later workflow-depth gaps.

The next compact capability candidate found by the read-only server audit is the
analytic-accounting lifecycle. A minimal 8-10-interface batch can extend plan
reads, create/update child plans, archive/restore company-scoped analytic
accounts, and CRUD/summarize manual analytic lines. Keep manual lines restricted
to `move_line_id=False` and `category=other`; do not expose root-plan creation,
plan deletion, or edits that propagate back into posted accounting entries. This
candidate has not been implemented or accepted yet.

## Analytic lifecycle capability checkpoint — 2026-09-02

The analytic candidate above is now implemented and accepted; do not treat it as
pending. Starting from pushed baseline
`b8eda33b0b6f6caeedd2f616216ad5e968bdfcbe`, the batch adds exactly eight commands:

1. `analytic.plan.create`
2. `analytic.plan.update`
3. `analytic.account.archive`
4. `analytic.account.restore`
5. `analytic.line.create`
6. `analytic.line.update`
7. `analytic.line.delete`
8. `analytic.line.summary`

The registry now has 374 IDs and 359 enabled handlers (215 reads and 144 writes),
724 schemas, and statuses of 318 `unconfigured`, 41 `degraded`, and 15 `disabled`.
Capability-ID-list SHA-256 is
`ab1e11c994f6c3d27c4eaa310e04f4967c5c9c3f275a3fcde0dbf9f1c2ba0992`;
canonical registry digest is
`77325bffca94023803ce765b6a30d8fb3d2b913d2f43b91ab9986d30fcce25bc`.

The fixed scope is deliberately small: only child plans can be created or
updated; accounts are company scoped; line writes accept only Project-root manual
lines and never accounting-generated lines. Summary can use any valid Odoo 19
plan column and optionally narrow to one analytic account. Amount and unit amount
are canonical signed decimal strings. `analytic.line.delete` has no persistent
tombstone, is marked degraded, executes only once in the live smoke, verifies
absence, and returns `record_not_found` on a later retry.

Verification evidence:

- Local: 119 core/public/runtime cases, 28 CLI cases, and 11 affected
  schema/contract cases passed; Ruff, compilation, and `git diff --check` passed.
- Server: one live case collected; `148 passed in 148.17s` for the final fast
  selection and `4 passed in 186.80s` for the registry/schema closure.
- Real Odoo: `1 passed in 10.64s` across both `odoo_cli_v4_dev` and
  `odoo_cli_v4_e2e`, as uid 5/company 1/`su=False`, with all eight new commands in
  the shared 17-capability analytic/budget chain.
- Delete rollback was independently observable through a forced savepoint
  rollback that restored the line. The final outer rollback and fresh-cursor
  checks found no marked plan, account, line, budget, or budget-line residue.

Private evidence directory:
`/opt/odoo-accounting-cli-v4/.tooling/analytic-lifecycle-20260902-W54c2yQO`.
The 35-file deployment archive SHA-256 is
`b38659ebdccfe04ee923c1f3806aeb0b420c347fb24144f1642fef8dc405c7f3`;
the 19 overwritten files have a separate pre-sync backup. Fast, registry,
collect, and live logs have SHA-256 values
`9416afd3ec73a8c2a55436c18f8e8d1455fc5f7d7cd40c0df8c7dfa9b06b045a`,
`450ab25e22f875a58368c7b4e52cc16aaa65c9da1021a922c12c1b760cb97adb`,
`0ef55d33e8e19da0af221a2572360fd4e639bbf56d0c1b6755728213b82dba18`,
and `f81b8b08942e88c5bdf8ce7e89f2bd10fd5e96c512d37a7395f767a97d68564a`.

No service-control command was issued. During the observation window, before the
live run, Odoo automatically exited on the server's pre-existing missing
`passlib` environment problem at 10:25:36 and systemd restarted it at 10:25:46.
Live-before, live-after, and final service snapshots are identical at PID
`959127`, `NRestarts=1`; Odoo, Nginx, and PostgreSQL are active, and no live worker
remains. Root disk use is 96% with about 3.5 GB free. The server Git tree remains
intentionally old and dirty; deploy by explicit allowlist only, never by pull,
reset, or checkout.

Next work should return to the capability-first gap audit and choose another
bounded 8-12-command accounting batch. Do not spend the next batch adding generic
ORM dispatch, duplicate commands, or heavy policy gates.

## Manual account-return lifecycle checkpoint — 2026-09-02

Starting from pushed baseline `25f6815003f9fd378e4195b8e33dc9275c36c2e7`,
this batch adds exactly eight commands:

1. `account.return.create`
2. `account.return.checks.refresh`
3. `account.return.check.result.update`
4. `account.return.validate`
5. `account.return.mark_submitted`
6. `account.return.archive`
7. `account.return.restore`
8. `account.return.delete`

The registry now has 382 IDs and 367 enabled handlers (215 reads and 152 writes),
740 schemas, and statuses of 324 `unconfigured`, 43 `degraded`, and 15 `disabled`.
Capability-ID-list SHA-256 is
`e72188eb3fae0df6b67afd41b7a8b5671b04c41ec8d02d37ba9ec7d20715d064`;
canonical registry SHA-256 is
`99cbd280f04184fea14911aaa6db9d0d1f52fed32bb70a09d39c5d409f909a76`.

### Fixed boundary

- Creation uses Odoo 19's `account.return.creation.wizard` and accepts only a
  standalone root company. The runtime uses Odoo's sudo-backed
  `_all_branches_selected()` helper so a business user's company record rule
  cannot hide a child branch and cause cross-company return creation.
- The selected dates must equal exactly one period returned by the native
  `account.return.type._get_period_boundaries(company, date)` method.
- The return type must be reportless, category `account_return`, and use
  `generic_state_review_submit`. Audit returns and report-bound tax closing are
  not exposed by this batch.
- Check-result update accepts only `todo` and `reviewed`, and only on a current,
  unsupervised check belonging to an active new manual return.
- Validate, submit, archive, restore, and delete call the corresponding native
  Odoo actions. `mark_submitted` means Odoo's internal submitted/completed state;
  it is not evidence of filing with a tax authority.
- Archive/restore are limited to new incomplete returns. Delete is limited to an
  active new manual return, has no tombstone, is not replayed after deletion, and
  is honestly marked degraded. Creation is also degraded because its natural key
  does not prove concurrent exactly-once creation. The other six commands remain
  `unconfigured` until a runtime context is selected.
- Write results deliberately return `line_ids=[]`; callers use the existing
  `account.return.check.list/get` reads for check IDs. Public validation rejects a
  nonempty write-result line list.

### Verification

- Final local changed-path regression: `44 passed, 471 deselected`; metadata and
  protected-integration selection: `3 passed, 2 skipped`. Ruff, compilation,
  JSON/schema validation, and `git diff --check` passed.
- Server focused regression: `111 passed, 649 deselected in 119.74s`.
  Registry/protected-integration closure: `2 passed, 2 skipped in 14.55s`.
- Final explicitly authorized real-Odoo run: `2 passed in 8.93s`. Each of
  `v4-dev` / `odoo_cli_v4_dev` and `v4-e2e` / `odoo_cli_v4_e2e` ran as uid 5,
  company 1 and reported 16 positive results: the existing eight return/journal
  reads plus all eight new writes. Immediate replay was required except for delete.
- Fresh-cursor verification found zero persistent `account.return` rows, zero
  marked checks, zero temporary compatibility views, and zero temporary XML IDs in
  both databases. PostgreSQL sequence increments do not roll back, so this is a
  no-persistent-row guarantee, not a bit-for-bit unchanged-database claim.

### Server environment defect and acceptance qualification

The first authorized run failed identically in both isolated databases before an
account return could be accepted. The server's custom `account_reports` manifest
comments out `views/account_move_views.xml`, but annual-closing checks still call
`env.ref('account_reports.view_draft_entries_tree')`. The source XML defines that
view, yet both databases lack its XML ID. The other annual-closing report and
expression XML IDs were checked and are present.

The final smoke therefore creates the exact missing `account.move` primary list
view and its XML ID inside the same outer test transaction, reports it as
`environment_fixtures=["account_reports.view_draft_entries_tree"]`, and verifies
both rows disappear after rollback. This is valid evidence that all 16 public
paths execute under a rollback-only compatibility fixture. It is not evidence that
the unmodified server package is healthy. Ordinary runtime creation/check refresh
can still fail until the Odoo package manifest/data mismatch is repaired. Do not
silently add the XML ID to a business database or modify the protected Odoo source
tree within the CLI capability task; that requires a separately authorized server
maintenance change.

### Deployment and evidence

Private evidence directory:
`/opt/odoo-accounting-cli-v4/.tooling/account-return-lifecycle-20260902-114136`.

- Final 27-file code/schema/registry/test archive: 2652160 bytes, SHA-256
  `3bcf94eee2d20407c8ceb39ecd8afecf6a21dcd801c86a0199c9e4e2a9522978`;
  every deployed target matched it byte-for-byte.
- Ten pre-existing targets have an exact backup; 17 targets were new. The two
  later integration-test revisions also have separate round-two/round-three
  backups.
- Focused-test, protected-integration, final-live, direct-worker JSON, and final
  residual-count log SHA-256 values are
  `71c480ea7ee339df7be973370b0434c106b424876cc8c9386101205fcdd22965`,
  `ba542d686d806cbd854089c968c184cb0ec1956e2bc54bfee15d6433750ae73c`,
  `3ea42ee6ab3f5a259dde99221524f0b85ee4bf5ea4984c2cac61aa1b5caddedc`,
  `13ca14ab6f4f2246165aa21125848c4206adcb767cabd5c1a2ac122b57d253af`,
  and `3e21136938b846ab8296a501fab08b4004900c9aafd8743a52ed0a8554a464ac`.
- No service-control command was issued. Odoo remained on PID `959127` with
  `NRestarts=1`; no live worker remains. Root filesystem use remains 96% with
  about 3.5 GB free. Server Git is intentionally old/dirty; continue using an
  explicit allowlist and never pull, reset, or checkout there.

The next action is a choice, not an assumption: either authorize a separate,
carefully scoped repair of the protected Odoo package so these return commands run
without the compatibility fixture, or leave that environment defect recorded and
select the next bounded 8-12-command accounting capability batch.

## Product/accounting master-data write checkpoint — 2026-09-02

Starting from pushed baseline `0d8b95d0afbd35a36b65214792a9792fe5707e53`,
this batch adds exactly eight commands:

1. `product.create`
2. `product.update`
3. `product.duplicate`
4. `product.archive`
5. `product.restore`
6. `product.cost.update`
7. `product.accounting_profile.update`
8. `product.category.accounting_profile.update`

The registry now has 390 IDs and 375 enabled handlers (215 reads and 160 writes),
756 schemas, and statuses of 330 `unconfigured`, 45 `degraded`, and 15 `disabled`.
Capability-ID-list SHA-256 is
`bb55de04032b66b931e4d84fa93ac7cda3ac5f01b6717ab0feef97cd16b1e52c`;
canonical registry digest is
`b55e75a5932ea9b14eda8024a965fffe2f913d5d962bbe074beb0e143fff9764`.

### Fixed boundary

- Products must be company-specific, single-variant, non-storable, non-combo,
  and have no attribute lines. This batch is accounting master data, not picking,
  stock-return, route, costing-method, or inventory-valuation workflow support.
- Create/update cover basic product fields only. Cost has its own canonical-decimal
  command. Product and category accounting profiles have their own closed account
  and tax contracts; tax IDs are normalized to sorted unique IDs. The category
  profile idempotency key includes company because those properties are
  company-dependent.
- Create and duplicate use a company/code natural-key recheck and are marked
  `degraded`. Without an operation store, an unrelated exact pre-existing match
  can be attributed as a serial replay, and concurrent exactly-once creation is
  not claimed.
- `product.cost.update` does not require the optional `product.value` model.
  The live rollback check compares those rows only when that stock-account model
  exists.
- All eight commands require `product.group_product_manager`. Archive and restore
  also require `stock.group_stock_manager` plus
  `stock.warehouse.orderpoint:read` and `stock.warehouse.orderpoint:write`: Odoo
  19's installed stock extension reads and updates attached orderpoints while
  changing product active state. Restore calls the native
  `product.product.action_unarchive()` path so the variant is restored before Odoo
  reactivates its template.

### Verification and diagnostic history

- Final local focused selection: `206 passed in 62.12s`; Ruff, integration collection,
  JSON/schema loading, and `git diff --check` passed.
- Final synchronized server selection: `206 passed in 93.55s`. Final registry
  closure separately passed two cases and reports all eight integration statuses
  as `implemented`.
- Explicit real-Odoo acceptance: `1 passed in 8.95s`. One pytest case ran both
  `v4-dev` / `odoo_cli_v4_dev` and `v4-e2e` / `odoo_cli_v4_e2e`. Each worker ran
  all eight writes and eight immediate replays as uid 5, company 1, and `su=False`,
  attached one real orderpoint, verified it followed archive and restore, then used
  a fresh cursor to verify rollback.
- The configured uid 5 has neither required product/stock group by default. The
  test linked both groups inside the same outer transaction and verified both
  direct memberships absent afterward. Final SQL audit found zero marked product
  templates, zero marked variants, zero marked orderpoints, and zero temporary
  memberships in both databases. No ordinary business database was used.
- Attempt 1 is not acceptance evidence. It failed at archive because the initial
  contract omitted stock-user access. Its rollback path completed, and direct SQL
  found zero product or group residue. The resulting minimal fix added the real
  stock module/model/group/ACL dependency.
- Attempt 2 is also not acceptance evidence. Archive then succeeded, but restore
  exposed that `product.template.action_unarchive()` leaves its archived variant
  inactive in Odoo 19. Its rollback and direct SQL audit were clean. The runtime
  now uses the native variant unarchive path.
- Attempt 3 passed the empty-orderpoint path, but a final independent source review
  found that `product.product.write(active=...)` writes every attached orderpoint.
  Stock-user read access was therefore incomplete. Fix4 requires stock-manager
  access and orderpoint write ACL, and the acceptance run above supersedes attempt 3
  by exercising an actual attached orderpoint. A separate root-launched harness run
  was rejected by PostgreSQL peer authentication before any Odoo transaction; the
  recorded `odoo`-identity run is the acceptance evidence.

### Deployment and evidence

Private evidence directory:
`/opt/odoo-accounting-cli-v4/.tooling/product-accounting-writes-20260902-8f2b73c1`.

- Initial 26-file archive: 278911 bytes, SHA-256
  `70f7d176951f5faccad05274bd95b2c6568c1d05e9e7497b34e1e04dc8021e9b`.
- Six-file stock-access correction: 192910 bytes, SHA-256
  `2067b590f2ee6852640d746f1416e485fb886d8e67213df9be167c701fdbefba`.
- Two-file restore correction: 80900 bytes, SHA-256
  `2dd560d001052ff5c5f1782552e5de5157e94d38339173fb3c54326006d6d4f0`.
- Pre-fix4 two-file registry-evidence archive: 102804 bytes, SHA-256
  `626be98fb84df6c4d14f7871485659e0f7123786ff785ce20836f3fed1798640`.
- Final six-file orderpoint-write correction: 192813 bytes, SHA-256
  `1ff6e1f2a25818754821003d98995501c1dcf4bef6e0d18d2f4bcaa747b45ff6`;
  pre-change backup SHA-256 is
  `28fb7a4d4af5c19088c33fa48880671bb9bd7a2bfc41d10aaa1090485bf46d09`.
  Every deployment round has its own pre-change backup in the same directory.
- Final server 206-test, `odoo`-identity live-smoke, and rollback/service-audit log
  SHA-256 values are
  `b43427f3e0636260dd1d66bed62f939c9f3c5c14e984889cf5d469abcabd8c2a`,
  `8329b54d0192be6ae54369acf70f1effd9ab451cd6deee41e27ad5bbe3d1e0c0`,
  and `a23afe6358e4b9e7fbf0666c68b8f1100047e31c4f672d096c8ac00a78f7cfdb`.
  Earlier failed-attempt logs and their independent rollback audits are retained.

No service-control command was issued. Odoo remained active on PID `959127` with
`NRestarts=1`; Nginx remained on PID `2193677` with `NRestarts=0`, PostgreSQL
remained active, and no live worker remains. Root disk use is still 96%, with about
3.5 GB free. Server Git is intentionally old and dirty; continue deploying only an
explicit allowlist and never pull, reset, or checkout there.

Next work should return to the accounting capability-gap audit and select another
bounded 8-12-command batch. Do not count aliases as new commands, add a generic ORM
dispatcher, or spend the next batch building heavy policy gates. The separate
account-return package defect remains recorded and is not silently repaired by
this product batch.

## Account-transfer-model lifecycle checkpoint — 2026-09-02

Starting from pushed baseline `d4949745285069c1e074e89f543c21e7a2d224ec`,
this batch adds exactly eight commands:

1. `account.transfer_model.create`
2. `account.transfer_model.update`
3. `account.transfer_model.duplicate`
4. `account.transfer_model.enable`
5. `account.transfer_model.disable`
6. `account.transfer_model.archive`
7. `account.transfer_model.restore`
8. `account.transfer_model.delete`

The registry now has 398 IDs and 383 enabled handlers (215 reads and 168 writes),
772 schemas, and statuses of 335 `unconfigured`, 48 `degraded`, and 15 `disabled`.
Capability-ID-list SHA-256 is
`ff74667373c5ed4e3b2cbb8af933c130a7d51903d092aaed6d5486ff77fe55c4`;
canonical registry SHA-256 is
`6edac2cefd98864db125ea697969dc88cb553535013a1d51ebd81bcc03dbadf0`;
the registry file SHA-256 is
`cbb47da5d1881213e3d32dfe520022ebb47bda02d00b1277f1f66537c394bc8a`.

### Fixed boundary

- These commands configure Odoo 19 `account.transfer.model`; they are not stock
  transfers, pickings, or physical returns. All eight require
  `account.group_account_manager` and remain company scoped.
- Create has exactly seven fields: name, general journal, start/optional stop date,
  month/quarter/year frequency, nonempty origin-account IDs, and nonempty
  destination lines. Update accepts a nonempty subset of those fields. Origin IDs
  are sorted and unique; destination accounts are unique. Each percentage is a
  canonical positive decimal no greater than 100, uses at most six decimal places,
  and the batch total is positive and no greater than 100.
- Updating origin accounts also rebuilds Odoo's hidden account-domain condition, so
  later automatic transfers do not silently use stale source accounts. Journals
  must be active general journals in the selected company; accounts must be visible
  to that company and cannot be off-balance.
- Enable/disable use native `action_enable()` / `action_disable()`. Archive uses the
  native archive path, which first disables the model. Restore uses native
  unarchive and deliberately returns an active but disabled model.
- Delete is limited to an active, disabled model with no generated moves. It has no
  persistent tombstone and is not replayed after success. Create and duplicate use
  exact company/name/configuration rechecks but do not claim concurrent exactly-once
  creation. Those three commands therefore remain honestly `degraded`; the other
  five are `unconfigured` until a valid runtime context and manager authorization
  are present.

### Verification

- The broad local `test_core_writes.py` run passed `527 passed in 1087.25s` before
  the final two boundary corrections. After those corrections, the dedicated
  public/runtime suite passed `49 passed in 56.76s`, the three affected registry
  checks passed `3 passed in 35.10s`, and Ruff plus `git diff --check` passed.
- On the synchronized server, the final dedicated suite passed `49 passed in
  64.86s`. The central runtime/registry selection passed `180 passed in 22.42s`,
  and final implemented-live registry closure passed `3 passed in 21.71s`.
- The final explicit real-Odoo smoke passed `1 passed in 10.45s`. One pytest case
  exercised both `v4-dev` / `odoo_cli_v4_dev` and `v4-e2e` /
  `odoo_cli_v4_e2e`. Per alias it ran all eight commands as uid 5, company 1,
  `su=False`, immediately replayed seven commands, and deliberately did not replay
  delete because no tombstone exists.
- Uid 5 does not have the accounting-manager group by default. Each worker granted
  it only inside the same outer transaction as the created model and copy. After
  rollback, a fresh cursor found zero marked transfer models, destination lines,
  generated moves, or temporary group memberships in both databases.

### Deployment and evidence

Private evidence directory:
`/opt/odoo-accounting-cli-v4/.tooling/account-transfer-model-writes-20260902-live1`.

- Initial 26-file deployment archive: 279808 bytes, SHA-256
  `4676ba954414ff1bb8a31b177ad564555d4dabba1df9440144079b9c5fb7b570`.
- Six-file active-delete/percentage-precision correction: 116209 bytes, SHA-256
  `448b70452ecc2050d1239b301869cba20163ff110b0ff5371c714bda299c03cc`.
- Final 26-file code/schema/registry/test archive: 280085 bytes, SHA-256
  `c314518c72367c93750a855ebd3b94650d8aa477feed557dd0c4272acad15860`.
  The remote archive checksum was verified before extraction.
- Pre-deployment, pre-correction, and pre-final backups have SHA-256 values
  `6753dda0118a20f5e177581dad9a8fdded65e62cfc945186dbc84bf6c89c09d1`,
  `19cd3e2b52abbe32089690d1c2859404e7ae3125bf038d662e1042f73ad6762f`,
  and `68d69e73a9c1534c80724c16953c4ff9ea2ddb0cd73a789619a381630a10d02c`.
- Final focused, central, registry, live, and service log SHA-256 values are
  `3c50b2e6e737700daf81470929a5fdbfe0af1172478c84de065a70f052dc5a0e`,
  `f3992702cf56622a3af3cde490a2050f2c634d5740922b5297424e2848c3072b`,
  `69df416240691d931fa3da18e7808c0058db581c4155cbbba4d3f6665922108e`,
  `c9479d29f201ce96b0e38dbf81fcef68563932f4d5cd2724f561b65d62bbb3fd`,
  and `5ea524f976faedcbb249d74b3139ab14e90d51d2b4e40a1218c653d9fd770f5d`.

No service-control command was issued. Odoo remained active on PID `959127` with
`NRestarts=1`; Nginx remained on PID `2193677` with `NRestarts=0`; PostgreSQL
remained active, and no live worker remains. Root disk use is 96%, with about
3.6 GB free. SSH still has intermittent timeout/reset behavior, but it did not
invalidate the persistent-session test results. Server Git remains intentionally
old and dirty; continue with explicit allowlists and never pull, reset, or checkout
there.

Next work should select another bounded 8–12-command accounting capability batch.
Do not count aliases as commands, add a generic ORM dispatcher, or divert the next
batch into heavyweight approval/audit controls.
