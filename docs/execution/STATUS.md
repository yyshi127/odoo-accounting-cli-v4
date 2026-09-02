# Execution status

## Current accounting phase — 2026-09-02

The active objective is capability-first accounting delivery in
[GOAL_SUMMARY.md](GOAL_SUMMARY.md). Historical sales, purchasing and inventory
logistics are outside this phase; picking and physical-return commands are not
accounting-core completion. Financial credit notes/refunds remain in scope.

The current registry has 390 IDs, 375 enabled handlers (215 reads, 160 writes),
and 756 schemas. Statuses are 330 `unconfigured`, 45 `degraded`, and 15 `disabled`.
These are implementation totals including historical non-accounting extensions,
not 390 accounting operations, a completion percentage, or proof that every
configured user is authorized. Capability-ID-list SHA-256 is
`bb55de04032b66b931e4d84fa93ac7cda3ac5f01b6717ab0feef97cd16b1e52c`;
canonical registry SHA-256 is
`b55e75a5932ea9b14eda8024a965fffe2f913d5d962bbe074beb0e143fff9764`.

The latest batch adds eight product/accounting master-data writes:
`product.create`, `product.update`, `product.duplicate`, `product.archive`,
`product.restore`, `product.cost.update`, `product.accounting_profile.update`,
and `product.category.accounting_profile.update`. The fixed scope is a
company-specific, single-variant, non-storable product. It does not expose picking,
physical returns, routes, costing methods, or stock-valuation workflows. Create and
duplicate remain honestly `degraded`: an exact pre-existing natural-key match can
be treated as a replay because this batch deliberately adds no operation store.

All eight commands require `product.group_product_manager`. On this Odoo 19 server,
archive and restore additionally require `stock.group_stock_manager` plus read and
write access to `stock.warehouse.orderpoint`, because the installed stock extension
updates attached orderpoints while changing a variant's active state. The configured
uid 5 has neither required group by default. The guarded smoke granted both only
inside each outer test transaction; every capability call still ran as uid 5 with
`su=False`, and fresh cursors verified both grants were rolled back. Therefore the
commands are implemented and live-tested, but they are not available to uid 5 in
ordinary runtime until an administrator grants the documented groups.

The final local selection passed `206 passed in 62.12s`; the synchronized server
selection passed `206 passed in 93.55s`. The explicit dual-alias real-Odoo run passed
`1 passed in 8.95s`; each alias executed all eight writes and eight immediate
replays, attached a real orderpoint, verified its archived/restored state, exercised
the existing product reads, and verified rollback. Final database audits found zero
marked templates, variants, orderpoints, or temporary group memberships in both
isolated databases. Earlier attempts remain as diagnostics: they found the stock
relation dependency and the correct native variant-restore path. A later independent
review then found that read-only stock-user access did not cover a nonempty
orderpoint; the final stock-manager/write-ACL smoke above supersedes the earlier
empty-orderpoint acceptance.

The private evidence directory is
`/opt/odoo-accounting-cli-v4/.tooling/product-accounting-writes-20260902-8f2b73c1`.
The initial 26-file deployment archive SHA-256 is
`70f7d176951f5faccad05274bd95b2c6568c1d05e9e7497b34e1e04dc8021e9b`;
the two focused correction archives are
`2067b590f2ee6852640d746f1416e485fb886d8e67213df9be167c701fdbefba`
and `2dd560d001052ff5c5f1782552e5de5157e94d38339173fb3c54326006d6d4f0`.
The pre-fix4 registry-evidence archive SHA-256 is
`626be98fb84df6c4d14f7871485659e0f7123786ff785ce20836f3fed1798640`.
The final six-file orderpoint-write correction archive SHA-256 is
`1ff6e1f2a25818754821003d98995501c1dcf4bef6e0d18d2f4bcaa747b45ff6`;
its pre-change backup is
`28fb7a4d4af5c19088c33fa48880671bb9bd7a2bfc41d10aaa1090485bf46d09`.
The final server 206-test, `odoo`-identity live-smoke, and rollback/service-audit
log SHA-256 values are respectively
`b43427f3e0636260dd1d66bed62f939c9f3c5c14e984889cf5d469abcabd8c2a`,
`8329b54d0192be6ae54369acf70f1effd9ab451cd6deee41e27ad5bbe3d1e0c0`,
and `a23afe6358e4b9e7fbf0666c68b8f1100047e31c4f672d096c8ac00a78f7cfdb`.
Odoo stayed on PID `959127` with `NRestarts=1`; no service-control command was
issued, no live worker remains, and root disk use remains 96% with about 3.5 GB free.

The preceding manual account-return batch added eight commands and retains its
separate compatibility-fixture qualification in the detailed checkpoint below.

The earlier analytic-accounting batch added eight commands:
`analytic.plan.create/update`, `analytic.account.archive/restore`,
`analytic.line.create/update/delete`, and `analytic.line.summary`.

The earlier batch added no capability ID or handler. It deepened nine existing
invoice, journal-entry and payment post/cancel/reset commands with plural forms.

Final local scope, payment-runtime, lifecycle-contract and registry verification
passed 181 cases in 332.51 seconds. The server had already passed 286 focused cases
in 318.13 seconds and an intermediate 159-case compatibility selection in 136.85
seconds; the final scope-aware selection passed 181 cases in 309.57 seconds. The
final shared dual-alias real-ORM workflow passed in 487.94 seconds. Each alias
exercised all nine batch lifecycles as uid 5,
company 1 and `su=False`, using two invoices, two journal entries and two payments,
nine immediate replays, and one representative valid-plus-missing-ID preflight.
Both outer transactions rolled back and the fresh-cursor residual checks passed.
The two earlier payment-post failures are retained only as diagnostic evidence;
both workers verified rollback before reporting the confirmed custom-add-on
`Expected singleton` failure.

The private server evidence directory is
`/opt/odoo-accounting-cli-v4/.tooling/accounting-batch-lifecycle-20260901-9c04f8fe22ae`.
Its final 31-file code/schema/registry/test archive is 250614 bytes with SHA-256
`f52c18b43b13d70f2d65a63b531e8501f05e1670e192879b5fedfe5bf1d373ed`;
all 31 deployed files were compared byte-for-byte with that archive. The original
26-file backup SHA-256 is
`de8316450408a70221f161e00a7d6df4cda06f6d6f37fe1afa21732cde871f92`.
Final focused and live log SHA-256 values are
`e9941f9e2cfc4bd1ca62ded3c655ebb46c370dc501f5b8cf1cc14200ce391161`
and `00e7a4668b58240ee7baf2e374fb5d1a08ef3d195b50e933c47def6e25d4ab12`.
Odoo, Nginx and PostgreSQL remained active; Odoo stayed on PID `3995891` with
`NRestarts=4`, no service was restarted, and no live worker remains.

The accounting-delivery batch adds nine real commands:
`invoice.send.inspect`, `invoice.send`, `payment.receipt.send.inspect`,
`payment.receipt.send`, `report.customer_statement.export`,
`report.customer_statement.send`, `report.followup.export`,
`report.followup.send`, and `invoice.followup.update`. A proposed
`journal_item.followup.update` command was deliberately removed before delivery:
native Odoo 19 does not expose an independent writable line-level follow-up state,
so retaining it would have advertised a false capability. The two successful send
paths use native Odoo wizards with `mail_notify_force_send=False`; their result is
`record_ids` plus `processed_count`, and their evidence proves marked Odoo messages
and serial replay only. It does not claim mail-queue persistence, SMTP delivery, or
concurrent exactly-once execution.

Local evidence passed 344 broad affected cases, 299 focused delivery/export cases,
662 central core-write cases, and the final 53-case registry/live-evidence closure.
The server passed the same 344-case focused selection in 781.53 seconds and the
final 53-case metadata selection in 339.05 seconds. The shared dual-alias live
workflow passed in 319.93 seconds. Per alias it ran all nine target commands as uid
5 with `su=False` and company 1: seven commands completed positively, while
`report.customer_statement.send` and `report.followup.send` returned the expected
clean authorization denial because the configured user lacks `res.partner:write`.
The positive paths verified two readiness inspections, two PDF exports, two native
marked messages, three immediate replays, invoice/receivable-line `no_followup`
propagation, and fresh-cursor rollback. Both fixed customers have no email and the
accountant cannot write partners, so the smoke used a test-only sudo recordset to
apply a temporary `example.invalid` address inside the same outer transaction;
every CLI call still used uid 5/su=False, and a fresh cursor proved the email was
restored to null. No external-delivery claim was made.

Four earlier live attempts are retained but are not acceptance evidence. They
stopped respectively on an unrelated split-receipt fixture requirement, a wrong
caller-selected key for `partner.create`, the configured user's correct partner-
create denial, and a test assertion that incorrectly required every core write to
have a framework-mandated key. Each worker rolled back before reporting failure;
none justified changing accounting configuration, ACLs, or production runtime.
The final 41-file server snapshot has SHA-256
`e38f86f57348f202be9f4bdd48ad2fbe26619c014edd85fc7700005c9961f08e`.
The pre-deployment backup is
`/opt/odoo-accounting-cli-v4/.tooling/accounting-delivery-359fb86e-63d4-47b9-95cd-ea09c856afed`
and its original-file archive SHA-256 is
`b1b72e228b8a2a8265089df3da1b643c44a1a8dd29aed050d4d778831180fe05`.
The successful focused, live, and post-live metadata logs have SHA-256 values
`df05d8cf7bc3b611a82d1463e99a6a8de30ffc0f62eb7fffab91acb943325555`,
`1887848a69ae83c01a4ac985a83d43475e717d9150108bf04c8a7b565dcac0fc`,
and `102d592df49ac12dd5b478c3452d459bac2a072d19bcf7321602f02dd8e74265`.
Odoo, Nginx, and PostgreSQL remained active; Odoo stayed on PID `3995891` with
`NRestarts=4`. No service was restarted.

The current invoice-copy/type batch adds `invoice.duplicate` and
`invoice.type.switch`. Duplication uses native `account.move.copy()` for the four
financial invoice/bill types, returns a new draft, preserves business origin text,
and binds replay to a caller-chosen key without preventing a deliberate second copy
under another key. Type switching uses native `action_switch_move_type()` only for
a never-posted draft and only between the customer invoice/credit pair or supplier
bill/refund pair. Its deterministic key binds move ID and target type. Neither
command invokes an arbitrary model/method dispatcher or bypasses native ACLs.

The live workflow also exposed an existing read-contract defect: Odoo 19 returns
`account.move.name=False` for a valid unnamed draft, while `journal_item.search/get`
previously required a nonempty move name. The runtime now represents that exact
state as JSON `null`; the public validator and shared item schema accept null but
still reject empty strings. `journal_item.get` inherits the same item schema by
reference. This is a compatibility correction for legitimate draft journal items,
not a fabricated move number.

Twenty-two code/schema/registry/test files are deployed after backing up all 15
pre-existing targets. Local contract/closure, long-origin runtime, and affected
journal-item selections passed 51, 20, and 849 cases respectively; Ruff, JSON,
compile, and diff checks passed. The final server selection passed 901 cases in
95.97s. The corrected shared dual-alias live workflow passed: 1 passed in 687.67s,
exit 0. Each alias executed 46 CLI calls across seven capabilities, including 12
immediate replays, two native duplicates, and two documents switched to refund and
back. Business headers, lines, totals, draft/posted journal items, storno balance
inversion/restoration, unchanged originals, and fresh-cursor rollback audits all
passed as uid 5/su=False/company 1.

Two failed live attempts and one diagnostic run are retained and are not counted
as acceptance. The first stopped before a new capability because the test supplied
a non-deterministic key to `invoice.post`; the second duplicated successfully but
found the valid unnamed-draft journal-item defect above. Every worker rolled back
and completed its residual audit before reporting failure. Final evidence is for
positive, untaxed, company-currency documents with `account_storno=True`; taxed or
negative-total switch branches and concurrent exactly-once duplication remain
outside that proof.

The preceding grouped-payment batch extends the existing
receivable.payment.register and payable.payment.register commands with a bounded
`move_ids` mode for two through 100 posted documents. One native
account.payment.register wizard creates exactly one full customer receipt or one
full supplier payment for documents sharing company, exact move type, partner and
currency. The normalized source set is part of the operation key and persisted
marker; immediate replay resolves the same payment even after every source residual
is zero. The original `move_id` path, including partial payment, write-off and refund
support, is unchanged. This is invoice/bill settlement, not account_batch_payment,
an internal bank transfer or bank-statement matching.

Nine code/schema/registry/test files are deployed after backing up six existing
targets. Counts remain 355 IDs / 340 handlers / 685 schemas: this batch adds no
command ID or schema file. Local necessary regression passed 234 cases plus the
initial 43-case contract/registry suite. Pre-commit review then found that the
direct bridge did not enforce the public layer's grouped-payment deterministic key
and that registry.json had mixed line endings. Both were corrected: public and
bridge keys now match, a wrong key is rejected before Odoo access, registry bytes are
LF-normalized, and the final post-review selection passed 42 local and 42 server
cases. Server focused regression passed 234 cases in 220.88s; the registry suite
passed three cases in 20.27s. The corrected shared
dual-alias live workflow passed: 1 passed in 482.74s, exit 0. Each alias verified
30 CLI calls / nine existing capabilities / ten immediate replays, four posted
source documents, two combined payments and balanced trial-balance debit/credit
delta 400/400. All test records rolled back and the fresh-cursor audit passed.
The first live attempt failed only because the new test expected generic payment
readback to expose source reconciliation IDs; rollback and residual audit completed,
then the test was corrected to verify each source document's payment status. No
production code changed for that correction. Internal bank transfer remains deferred:
the isolated databases expose neither a second suitable liquidity journal nor a
verified native Odoo 19 paired-transfer action for this CLI contract.

At 10:24:27 CST the pre-existing Odoo19 process exited on its recurring missing-
`passlib` startup/import defect and systemd restarted it at 10:24:38. The same daily
sequence is present for August 29-31; no deployment or test issued a restart. Odoo19
is active as PID 3995891 / restart-count 4, and Nginx/PostgreSQL remain active. This
external service defect is recorded, not repaired within the CLI capability scope.

The preceding cash-refund batch extends receivable.payment.register to customer
credit notes and payable.payment.register to supplier refunds. Odoo's native
wizard determines the payment direction; the write-off readback uses the actual
source-document type for its sign. Requests, schemas, IDs, ACLs and operation keys
are unchanged. Registry summaries and aliases expose the existing commands' refund
support. Six code/registry/test files are deployed after backing up five existing
targets. Necessary server regression passed 318 cases with one authorization skip
in 21.72s. The shared dual-alias real workflow passed: 1 passed in 919.40s,
exit 0. Each alias verified 62 CLI calls / 12 existing capabilities / 14 immediate
replays, two settled originals, customer credit 40 refunded as 20 plus 20,
supplier refund 60 received as 30 plus 30, six payments, 20 posted journal items,
unchanged original reconciliations and trial-balance debit/credit delta 400/400.
All test records rolled back; the fresh-cursor residual audits passed. Business
execution is uid 5/su=False/company 1; those separate audits are superuser read-only.
This is refund payment accounting, not bank transfers or bank-statement matching.

The preceding taxed-invoice batch adds tax_line_id, tax_ids and signed
company-currency tax_base_amount to journal_item.search/get. Thirteen
code/schema/registry/test files are deployed after backing up eleven existing
targets across the initial deployment and report correction. report.tax also
preserves the native Generic Tax group rows' exact empty net values as null;
numeric tax cells and other reports retain strict validation. The server's
necessary regression passed 199 journal-item cases in 27.04s and nine
tax-report/registry/helper cases in 27.31s, with one authorization skip. Separate
helper and report corrections passed two and 28 targeted cases respectively.

The shared real workflow passed both aliases: 1 passed in 501.48s, exit 0. Each
alias verified 34 CLI calls / 11 existing capabilities / six immediate replays,
sales base/tax 180/23.40 and purchase base/tax 120/15.60, six posted journal items,
the two actual tax-report child-row deltas, and trial-balance debit/credit delta
339/339. All test records rolled back; the fresh-cursor residual audit passed.
Business execution is uid 5/su=False/company 1; that separate audit is superuser
read-only. No worker remains. Odoo19 PID 2855713 / restart-count 3, protected
installed source and the earlier bank/deferred failure logs stayed unchanged.

Two earlier failed attempts are retained with completed rollback audits: the
4.32s test-only technical-model read before any CLI call, and the 251.96s failure
at the populated tax report after both first-alias invoices and their tax items
had passed. The latter exposed the real empty-net adapter defect described above;
neither failed run is counted as complete acceptance. This is company-currency,
13% price-excluded/on-invoice, in-process CLI/real-ORM evidence, not statutory
returns, price-included/cash-basis/FX tax, external transport or durable replay.
No command IDs, tax configuration, permissions or second-stage controls are added.

The preceding financial-header batch extends customer_invoice.create,
vendor_bill.create and invoice.update with optional partner_bank_id and
fiscal_position_id (strict positive integer or null). Invoice.get reads both as
IDs/null without loading the related bank/fiscal-position display names. Omission
does not inject a default; null writes False. Bank validation uses native-user
ACLs, active state and shared/selected-company scope, without a UI-only owner,
currency or trust lock. Fiscal positions retain Odoo's parent-company scope.
No implicit full-line fiscal remapping or configuration write is added.

Eighteen code/test/schema/registry files are deployed and hash-verified after
backing up fourteen existing targets; four test paths are new. Necessary local
checks pass: 263 new contract/runtime/read cases, 62 existing create/update cases,
and the registry-alignment case. Server focused regression passed 622 cases with
one authorization skip in 172.91s, exit 0. The separately authorized shared
prepayment workflow passed both aliases: 1 passed in 709.21s, exit 0. Each alias
verified 48 CLI calls / 12 existing capabilities / 14 immediate replays, customer
advance 120 and supplier advance 90, later invoicing, zero residual, eight posted
journal items and trial-balance debit/credit delta 420/420. Test records rolled
back, followed by the fresh-cursor read-only residual audit. No worker remains;
Odoo19 PID 2855713 / restart-count 3 and protected file hashes stayed unchanged.
This is untaxed company-currency in-process CLI/real-ORM evidence, not external
bridge, durable replay, concurrent execution or bank-matching acceptance.
Both isolated databases
lack eligible bank/fiscal-position fixtures for nonempty selection: null-to-null
readback is not a real selection or nonempty clearing test. No command IDs,
bank matching, configuration changes or second-stage controls are added.

### Accounting workstreams (not a completion denominator)

These are progress-tracking workstreams, not a newly approved complete scope or
equally weighted percentage. Passing a bounded scenario does not prove every
tax, currency or configuration variant.

| Workstream | Current evidence and remaining boundary |
| --- | --- |
| Queries and reports | Selected report/filter/export, aging and populated generic-tax workflows passed; this is not all reports or statutory tax regimes. |
| Invoices, bills and financial credits | Selected lifecycle, credit, currency, adjustment and 13% price-excluded customer/vendor tax workflows passed; actual journal/financial-reference switches and other tax variants remain unaccepted. |
| Manual entries | Maturity, posting, aging, reconciliation/undo and trial-balance workflow passed; do not count unexecuted later steps from the blocked bank batch. |
| Payments and reconciliation | Payment-difference, credit-settlement and advance-payment workflows passed in their stated scenarios; FX/early-payment variants remain outside that evidence. |
| Bank matching | Implementations exist, but the combined receipt/matching workflow remains blocked by suspense/outstanding account configuration. |
| Assets and deferrals | Limited earlier scenarios do not prove real depreciation/disposal amounts; the installed multi-move singleton defect blocks the newer deferral workflow. |

Approvals, consolidated audit/release controls and inventory logistics do not
belong in this first-phase progress denominator. The known configuration/add-on
blockers remain required follow-up items, not exclusions used to inflate progress.

The preceding manual-entry batch adds optional date_maturity (YYYY-MM-DD or null)
to journal_entry.create and journal_entry.lines.replace. Explicit null clears
the date; omission preserves old request fingerprints and unchanged replays.
An actual full replacement still rebuilds the submitted lines, so dates to keep
must be supplied with other edits. Native ORM behavior and draft-only editing
remain unchanged. Eight code/test/schema files are deployed after backing up the
five existing targets. Local necessary regressions passed 318 cases, plus six
selected existing-entry cases. Server regression passed 318 cases / 2 authorization
skips in 75.26s, then six existing-entry cases in 25.50s. The first shared live run
failed on its initial aged-report read before creating entries: the test helper
omitted capability IDs when constructing report/open-item ports. Its rollback
audit completed and the failure log is retained. The test-only correction is
deployed; its regression passed locally and on the server (1 passed / 2
authorization skips, server 0.71s). Corrected shared acceptance passed both aliases:
1 passed in 921.11s, exit 0. Each alias verified 62 CLI calls / 12 capabilities /
16 immediate replays, four manual entries, eight current posted items, AR 120 /
AP 90, due/future open items, native aging, reconciliation/undo and trial-balance
debit/credit delta 420/420. All test records rolled back. Business execution is
uid 5/su=False/company 1; the fresh-cursor rollback audit is superuser read-only.
This is in-process CLI/real-ORM acceptance, not external bridge transport,
durable replay, concurrency, tax or foreign-currency acceptance. No worker remains;
Odoo19 PID 2855713 / restart-count 3 and protected file hashes remained unchanged.
It adds no command IDs, stock operations, configuration or permission changes.

The preceding invoice-header batch extends existing invoice.update.changes with
optional journal_id/currency_id. Both are strict positive integer IDs; journals
must match the selected company and customer/supplier document type, and currencies
must be active and accessible. Native write/inverses handle the changes without
an artificial journal-currency lock or manual journal-item reconstruction. The
registry adds the two reference-model read dependencies, not new IDs or handlers.
Seven code/test/schema files are deployed and hash-verified after a six-file
backup; the dedicated public-contract test file is new. Server focused tests
passed: 285 passed / 4 authorization skips in 74.61s, followed by 4 existing-update
and registry cases in 22.66s. The shared dual-alias live run passed: 1 passed in
517.22s, exit 0. Each alias verified 35 CLI calls / 12 existing capabilities /
10 immediate replays, changing customer and supplier documents from CNY to USD
and posting them as 110/90 USD with 150.70/123.30 CNY journal totals using the
historical fixture rate. Nine current posted journal items, negative storno
lines and analytic distributions were checked. All three documents, three
analytic lines and one temporary analytic account were rolled back. Business
execution is uid 5/su=False/company 1; the fresh-cursor rollback audit is read-only
superuser inspection. This is untaxed in-process CLI/real-ORM evidence, not
external bridge transport, durable replay or manual-rate/tax/refund acceptance.
The runner is finished; Odoo19 PID 2855713 / restart-count 3, installed source,
and the earlier blocker evidence remained unchanged.

Actual journal-switch acceptance remains a fixture gap: both isolated databases
have only one sale journal and one purchase journal, including archived records,
and uid 5 cannot create journals. The shared case keeps those journal IDs and
changes the actual currency; it must not be described as a real journal switch.
No configuration or permission change is authorized to fill this gap.

The preceding completed batch allows negative unit-price adjustment lines through
the existing customer_invoice.create and vendor_bill.create interfaces. It reuses
the signed decimal validators without changing quantities, discounts, native
posting, access checks or command counts. Eight code/test/schema files are
deployed and hash-verified after a seven-file backup. Server focused tests passed:
252 passed and 4 authorization skips in 74.55s; the separate existing-create
selection passed 19 tests in 34.15s. The shared dual-alias real-ORM case passed:
1 passed in 443.49s, exit 0. Each alias verified 30 CLI calls / 11 existing
capabilities / eight immediate replays, customer total 110 and supplier total 90,
the two negative adjustment lines' native storno debit/credit signs, nine current
posted journal items, and rollback of all three documents, three analytic lines
and one temporary analytic account. No worker remains. This covers untaxed,
company-currency in-process CLI/ORM execution, not external bridge transport,
durable replay or tax/foreign-currency acceptance. A pre-deployment Odoo automatic
restart is recorded in HANDOFF; the resulting PID 2855713 / restart-count 3
remained stable throughout this batch. No service or dependency was modified.

The preceding completed batch adds analytic-distribution readback to the four existing
invoice.get, journal_entry.get and journal_item.search/get interfaces. Native keys and finite
signed percentages are preserved; empty distributions read as objects, and no
new account lookups, write-input expansion, IDs or schema files are introduced.
The 21 code/test/schema files are deployed and hash-verified after a 20-file
backup. Server focused tests passed: 641 passed and 4 authorization skips in
30.45s, exit 0. The first shared live case failed in v4-dev before line replacement
because the test omitted the existing required product_id and discount fields;
its rollback audit completed, and the 91.47s failure log is retained. Only those
two test-fixture fields were corrected; production code did not change. The
separate corrected shared run passed both aliases: 1 passed in 470.78s, exit 0.
Each alias verified 30 CLI calls across 11 existing capabilities, eight immediate
replays, modification/clearing readbacks before and after posting, seven posted
journal items, and rollback of the three documents, one temporary analytic account
and three generated analytic lines. This is in-process CLI/real-ORM acceptance,
not external bridge or durable replay evidence. No worker remains; the installed
add-on digest and Odoo19 service state remain unchanged. See HANDOFF.md for the
retained failure, correction, passing logs and recovery archives.

The preceding completed payment-difference batch extended the two existing
receivable/payable payment.register commands with explicit open/reconcile handling,
an active company-scoped write-off account and an optional label. Reconcile
requires an explicit amount and closes the remaining document difference through
the native payment wizard. Omitted new fields retain the old behavior. No IDs,
handlers or schema files are added. Local contract and runtime regressions pass;
eight code/test files are deployed and hash-verified after a nine-file backup.
Server focused tests passed: 267 passed and 3 authorization skips in 88.42s,
exit 0. The separately authorized shared live case passed both isolated aliases:
1 passed in 330.64s, exit 0. Each alias used 22 CLI calls across 8 existing IDs to
settle customer and supplier residuals of 100 with payments of 99 and signed
write-offs of 1/-1. Source balances reached zero; exact accounts/labels/amounts,
balanced entries, six immediate replays, two changed-payload conflicts, unchanged
bank configuration and fresh-cursor rollback audit passed. This is in-process
CLI/real-ORM evidence for untaxed company-currency documents, not external bridge
transport, durable replay, early-payment discounts, foreign currency or bank
matching. No worker remains, and Odoo19 state and the installed add-on digest
remain unchanged. See HANDOFF.md for retained logs and recovery files.

The negative-price creation gap is completed above; signed line replacement
already existed and is not a new command. The draft invoice.update journal/currency
fields are implemented; actual currency acceptance and the journal-switch fixture
limitation are distinguished above. Optional date_maturity on manual-entry lines
is now implemented and passed corrected shared acceptance as described above. Its
source/contract findings and 12-capability accounting workflow are recorded in
HANDOFF. Continue
coherent workflows without adding inventory IDs or treating mixed-domain totals
as completion.

Independent accounting dates extend three existing invoice/bill commands.
Their 14-capability CLI/ORM lifecycle smoke passed
on both isolated aliases with rollback verification. The subsequent financial
credit-note settlement acceptance passed on both aliases: 11 existing commands,
zero new production interfaces, and customer/supplier residuals of 120, 80, then
0. Native automatic reconciliation, targeted undo, reapplication, journal items,
trial balance and fresh-cursor rollback were verified. The shared smoke passed
in 1293.65s with exit 0; this is in-process CLI/real-ORM evidence, not a
cross-process bridge or durable commit/replay test. See
[HANDOFF.md](HANDOFF.md) for exact batch evidence and recovery artifacts.

The preceding report batch added optional `journal_ids` to eight existing report
interfaces: trial balance, general ledger, balance sheet and profit and loss,
each with JSON reads and PDF/XLSX export. It adds no command IDs or schema files.
The configured native partner ledger does not support journal selection and is
not included. Existing unfiltered requests remain compatible; pagination binds
the selected journal set, and unavailable selections cannot silently become an
all-journal report. Local relevant tests passed, followed by 266 focused server
tests (2 authorization skips and 12 already-tested CLI cases deselected).
The first shared read-only live run failed in v4-dev at the general-ledger XLSX
comparison: native print export unfolds journal-item detail, unlike the ordinary
JSON result. The test expectation has been corrected against independently
requested native print-mode lines; production filtering did not change for this
test correction. The separate corrected shared run passed both v4-dev and v4-e2e:
`1 passed in 465.22s`, exit 0. Each alias verified all 8 interfaces, 30 CLI calls,
16 exports, combined/all journal selection, the unfiltered baseline and pagination.
Trial-balance amounts matched posted journal items; all 8 XLSX amount comparisons
per alias passed. PDF checks cover structure and hash, not extracted amounts.
Both transactions were read-only and rolled back/closed, and no worker remains.

Two separate real-workflow blockers remain unresolved: the isolated bank journal
uses the same account for suspense and outstanding payments, and the installed
exchange-rate add-on fails on multi-record move creation. Neither configuration
nor add-on repair is authorized. No current claim of complete accounting coverage
or release readiness is made.

## Historical 289-ID checkpoint and earlier execution record

The remainder preserves past checkpoints, counts and gate definitions. Its
references to "current" or "latest" describe those historical snapshots and do
not supersede the current accounting phase above.

- G0: passed (private environment baseline retained outside this public repository)
- G1: passed
- G2: in progress (source snapshot, two provenance-bound synthetic databases,
  and accounting fixture v1 passed; full payment, assets/depreciation,
  deferrals, inventory valuation, and report golden cases remain pending)
- G3: in progress (289-ID current baseline recorded after the eight-command
  sales-invoice/stock-transfer write batch, the nine-command specialist/
  localized report-export extension, the ten-command native
  financial-report export batch, the nine-command fiscal-position/journal-group/
  localization-readiness batch, the nine-command
  accounting follow-up batch, the twelve-command sales/purchase order-write
  batch, the historical 236-ID order-document read
  batch, the historical 228-ID operational-
  inventory read batch, the historical 218-ID account-return/
  journal-analysis read batch, the 210-ID management-reporting/
  period-context read batch, and the historical 202-ID,
  190-ID partner master-data, 179-ID analytic/budget-write, and 170-ID
  payment/bank reconciliation, 160-ID document-lifecycle, 152-ID
  analytic/budget, 141-ID
  payment/reconciliation-object, 133-ID accounting-configuration, 125-ID
  reference-object, and historical 113-ID core-object read checkpoints; 289 is
  not a proven final count; the
  earlier V2/V3 semantic crosswalk recorded at least two additional required
  IDs, 52 contracts needing expansion, and nine product-boundary decisions;
  those historical gap counts have not yet been re-audited against the current
  289-ID implementation;
  272 handlers cover 165 reads and 107 accounting writes; 164 reads and 106
  writes have live success-path evidence (270 total), 17 capabilities remain
  disabled/planned (8 reads and 9 writes), and 549 versioned JSON Schema
  documents are retained; current statuses are 251 `unconfigured`, 21
  `degraded`, and 17
  `disabled`;
  `asset.validate` is implemented but its live success path is blocked by a
  server add-on defect and its rollback behavior is verified)
- G4: passed for official generation provenance and baseline review (initial
  generation, six focused refinement rounds, official test/validate, complete
  transcript, and independent adjudication recorded; generated code remains a
  non-authoritative adapter draft)
- G5: in progress (real dual-environment bridge, 164 read success paths, and
  106 write success paths are verified; the latest eight-command batch adds
  native sales-order invoicing plus stock-transfer create, confirm, assign,
  quantity setting, validate, unreserve, and cancel; the preceding nine-command
  batch adds native PDF/XLSX exports for journal, asset, deferred expense/revenue,
  multicurrency revaluation, three China reports, and Singapore GST; the
  preceding ten-command batch adds native
  PDF/XLSX exports for trial balance, balance sheet, profit and loss, cash flow,
  tax, general ledger, partner ledger, aged receivable/payable, and executive
  summary; the preceding nine-command batch adds fiscal-position lifecycle/
  account mappings, journal-group create/update, and China/Singapore readiness
  reads; the preceding nine-command batch adds
  purchase-bill creation/matching/unmatching, payment-term lifecycle, and
  period-accrual generation; the preceding twelve-command batch adds
  sales/purchase order create, draft update, line replacement, confirm, cancel,
  and reset-to-draft writes; the preceding eight-command batch adds
  sales/purchase order search, detail, line, and analysis reads; the earlier
  ten-command batch adds fixed inventory master, transfer, move, on-hand, and
  availability reads; the earlier eight-command batch adds six account-return reads plus effective
  journal-date and journal-item analysis reads; the earlier
  management-reporting/period-context batch adds customer
  statement, follow-up, invoice analysis, lock-date, and fiscal-year reads; the
  earlier accounting-depth checkpoint deepens 12 existing invoice,
  bill, journal-entry, payment, payment-status, and reconciliation interfaces
  without changing its historical 202-ID count; the preceding
  twelve-command accounting-configuration write batch adds create, update,
  archive, and restore for accounts, journals, and taxes; the earlier eleven-
  command partner
  master-data batch adds two partner reads plus partner, accounting-property,
  and bank-account writes; the earlier nine-command analytic/budget write
  batch adds analytic-account create/update plus budget create, draft update,
  line replacement, and four native lifecycle actions; the earlier
  ten-command payment/bank reconciliation batch adds three reads plus seven
  payment and cash-application writes; the earlier eight-write lifecycle batch
  closes draft update,
  full-line replacement, cancel, and reset-to-draft for invoices/bills and
  journal entries; the historical nine-write batch adds three
  asset lifecycle actions, three accounting-entry generators, automatic
  reconciliation, and generic/China period transfers; the fixed-asset batch
  also retains four reads, `asset.create`, and the
  implemented-but-server-blocked `asset.validate`;
  product-profile routing/not-found is verified but its live success mapping
  awaits product fixture data; the registry is now a 289-ID baseline, after the
  281-ID specialist/localized report-export checkpoint, the 272-ID native
  financial-report export checkpoint, the 262-ID fiscal-position/
  journal-group/localization-readiness checkpoint, and the
  historical 236-ID order-document read, 228-ID operational-inventory, 218-ID account-return/journal-analysis, 210-ID management-
  reporting/period-context, and 202-ID accounting-
  configuration/depth checkpoints,
  190-ID partner master-data and 179-ID analytic/budget-write,
  170-ID payment/bank reconciliation, 160-ID document-lifecycle, 152-ID
  analytic/budget, 141-ID
  payment/reconciliation-object, 133-ID
  accounting-configuration,
  125-ID reference-object, and historical
  113-ID core-object checkpoints, with 17 disabled/planned capabilities)
- G6-G10: not started
- Release readiness: not ready

The historical 125-ID checkpoint was only the `102 + 11 + 12` delivery
lineage, not a target or sizing basis. Capability sufficiency is evaluated by
closed workflows and live evidence.

The current 289-ID checkpoint is live-verified for the latest eight writes.
The synchronized server runtime regression passed `73 tests in 0.52s`; the
shared guarded smoke passed `2 tests in 13.78s` and exercised all eight first
executions plus immediate replays in both `odoo_cli_v4_dev` and
`odoo_cli_v4_e2e` as uid 5/company 1. The same smoke proved one real stock
backorder per database and verified transaction and temporary-group rollback.
The Odoo 19 runtime now uses `uom.uom._has_common_reference()` rather than the
removed `category_id` field. The retained live log SHA-256 is
`d22c43c5d1ee330dcf7bdccf9928dd87bc6bbdf16feb8023eee35d5bc3207794`;
the canonical registry digest is
`72b2a90c0e8da798156856ccb9285a80ce4b1572e108147ff81feb8b8c21eb71`.
Odoo, Nginx, and PostgreSQL retained the pre-run start timestamps and restart
counts; no service-control command was issued.

Current implementation work: capability-first G5 batches. The latest batch adds
`sale.order.invoice.create`, `stock.transfer.create`,
`stock.transfer.confirm`, `stock.transfer.assign`,
`stock.transfer.quantities.set`, `stock.transfer.validate`,
`stock.transfer.unreserve`, and `stock.transfer.cancel`. The preceding batch adds
`report.journal.export`, `report.asset.export`,
`report.deferred_expense.export`, `report.deferred_revenue.export`,
`report.multicurrency_revaluation.export`, `report.china.balance_sheet.export`,
`report.china.profit_and_loss.export`, `report.china.cash_flow.export`, and
`report.singapore.gst.export`. The preceding batch adds
`report.trial_balance.export`, `report.balance_sheet.export`,
`report.profit_and_loss.export`, `report.cash_flow.export`, `report.tax.export`,
`report.general_ledger.export`, `report.partner_ledger.export`,
`report.aged_receivable.export`, `report.aged_payable.export`, and
`report.executive_summary.export`. The preceding batch adds
`fiscal_position.create`, `fiscal_position.update`,
`fiscal_position.account_mappings.replace`, `fiscal_position.archive`,
`fiscal_position.restore`, `journal.group.create`, `journal.group.update`,
`localization.china.configuration.inspect`, and
`localization.singapore.configuration.inspect`. The preceding accounting
follow-up batch adds or enables `purchase.order.bill.create`,
`purchase_bill.match`, `purchase_bill.lines.unmatch`, `payment_term.create`,
`payment_term.update`, `payment_term.lines.replace`, `payment_term.archive`,
`payment_term.restore`, and `period.accrual.generate`. The preceding order-
write batch adds `sale.order.create`, `sale.order.update_draft`,
`sale.order.lines.replace`, `sale.order.confirm`, `sale.order.cancel`,
`sale.order.reset_to_draft`, `purchase.order.create`,
`purchase.order.update_draft`, `purchase.order.lines.replace`,
`purchase.order.confirm`, `purchase.order.cancel`, and
`purchase.order.reset_to_draft`. The preceding order-document read batch added
`sale.order.search`, `sale.order.get`,
`sale.order.line.search`, `sale.order.analysis.summary`,
`purchase.order.search`, `purchase.order.get`, `purchase.order.line.search`,
and `purchase.order.analysis.summary`. The earlier operational-inventory
batch adds `product.category.list`, `warehouse.list`,
`stock.location.list`, `stock.operation_type.list`, `stock.route.list`,
`stock.transfer.search`, `stock.transfer.get`, `stock.move.search`,
`inventory.on_hand.summary`, and `inventory.availability.inspect`. The preceding
account-return/journal-analysis batch added `account.return.search`,
`account.return.get`, `account.return.summary`, `account.return.type.list`,
`account.return.check.list`, `account.return.check.get`,
`journal.accounting_date.resolve`, and `journal_item.analysis.summary`. The
preceding management-reporting/period-context batch adds `report.customer_statement`,
`report.followup`, `invoice.analysis.search`, `invoice.analysis.summary`,
`company.lock_dates.inspect`, `company.fiscal_year.resolve`,
`fiscal_year.search`, and `fiscal_year.get`. The first two core
accounting write batches, the fixed-asset batch, the five-command
inventory-accounting read batch, the nine-command remaining-read batch, the
historical nine-command extended-write batch, the historical twelve-command
core-object read batch, the twelve-command reference-object read batch, and the
eight-command accounting-configuration read batch, the eight-command
payment/reconciliation object read batch, the eleven-command analytic/budget
read batch, the eight-command document-lifecycle write batch, the ten-command
payment/bank reconciliation batch, the nine-command analytic/budget write
batch, the eleven-command partner master-data batch, the twelve-command
accounting-configuration write batch, and the twelve-command sales/purchase
order-write batch are implemented. The latest accounting-
depth checkpoint additionally deepens 12 existing invoice, bill, journal-entry,
payment, payment-status, and reconciliation interfaces without increasing the
the historical 202-ID inventory. The preceding command-expansion batch added
`account.account.create`, `account.account.update`,
`account.account.archive`, `account.account.restore`, `journal.create`,
`journal.update`, `journal.archive`, `journal.restore`, `tax.create`,
`tax.update`, `tax.archive`, and `tax.restore`. The preceding partner batch
added `partner.search`, `partner.get`,
`partner.create`, `partner.update`, `partner.archive`, `partner.restore`,
`partner.accounting.update`, `partner.bank_account.create`,
`partner.bank_account.update`, `partner.bank_account.archive`, and
`partner.bank_account.restore`. The earlier analytic/budget write batch
added `analytic.account.create`, `analytic.account.update`, `budget.create`,
`budget.update_draft`, `budget.lines.replace`, `budget.confirm`,
`budget.reset_to_draft`, `budget.cancel`, and `budget.mark_done`. The earlier
payment/bank reconciliation batch added `bank.transaction.search`,
`bank.transaction.reconciliation.get`,
`bank.transaction.match_candidates.list`, `payment.create`,
`payment.update_draft`, `payment.reset_to_draft`, `bank.transaction.update`,
`bank.transaction.match`, `bank.transaction.unmatch`, and
`reconciliation.write_off`. The historical core-object read batch added
`account.account.get`, `journal.get`, `tax.get`, `payment_term.get`,
`currency.get`, `partner.accounting.get`, `bank.transaction.get`,
`journal_item.search`, `journal_item.get`, `payment.method.list`, and
`reconciliation.model.list`, and enables `report.bank_reconciliation` with a
required company-scoped bank `journal_id`. The accounting-configuration batch adds
`payment.method.get`, `reconciliation.model.get`, `cash_rounding.list`,
`cash_rounding.get`, `journal.group.list`, `journal.group.get`,
`incoterm.list`, and `incoterm.get`. The payment/reconciliation batch adds
`partner.bank_account.search`, `partner.bank_account.get`,
`bank.statement.search`, `bank.statement.get`, `reconciliation.partial.list`,
`reconciliation.partial.get`, `reconciliation.full.list`, and
`reconciliation.full.get`. The preceding analytic/budget batch adds
`analytic.line.search`,
`analytic.line.get`, `analytic.distribution_model.list`,
`analytic.distribution_model.get`, `analytic.applicability.list`,
`analytic.applicability.get`, `budget.search`, `budget.get`,
`budget.line.list`, `budget.line.get`, and `report.budget`. The preceding
reference-object batch added
`product.search`, `product.get`, `analytic.plan.list`, `analytic.plan.get`,
`analytic.account.search`, `analytic.account.get`, `fiscal_position.search`,
`fiscal_position.get`, `account.tag.list`, `account.tag.get`,
`tax.group.list`, and `tax.group.get`. The lifecycle batch adds
`invoice.update`, `invoice.lines.replace`,
`invoice.cancel`, `invoice.reset_to_draft`, `journal_entry.update`,
`journal_entry.lines.replace`, `journal_entry.cancel`, and
`journal_entry.reset_to_draft`. New invoice, bill, and journal-entry creates no
longer occupy the business `account.move.ref` field with an idempotency key;
new records use a capability/company/key marker plus a parameter fingerprint,
while legacy `ref=key` records remain replay-compatible. `asset.validate`
still safely returns
`odoo_write_error` and rolls back because the current server's
`exchange_currency_rate` constraint fails on multiple depreciation moves. The
full G2 fixture matrix and consolidated G3 write controls remain open for a
later phase.

For the preceding specialist/localized report-export extension, the focused
local selection passed 219 tests with one opt-in live test skipped, and the
synchronized server selection passed 219 tests in 547.23 seconds. One shared
read-only smoke passed in 63.06 seconds and performed 76 native exports: all 19
fixed report-export capabilities in PDF and XLSX in both isolated aliases.
Public CLI checks passed for a 47,484-byte journal PDF in `v4-dev`/company 1
and a 7,133-byte Singapore GST XLSX in `v4-e2e`/company 2. A post-review
journal-metadata regression passed 117 tests locally and 72 on the synchronized
server. At that checkpoint the registry had
281 IDs, 264 handlers (165 reads and 99 writes), 533 schemas, and statuses of
245 `unconfigured`, 19 `degraded`, and 17 `disabled`. Capability-ID SHA-256 is
`04f3e17865e63eeb5a3765a8f7de6f7c93e755d6687e5b3dcffcd33f912f29da`;
canonical registry digest is
`a0d195d91a32dfd012f4b76909d51e0302339399ffe3802bf00f6f799f99f9a7`.
Evidence is retained under
`/opt/odoo-accounting-cli-v4/.tooling/financial-report-export-extension-838b729d-342c-49a2-86ff-04846b2ae30e`.
The final 30-file deployed-source archive SHA-256 is
`8ea9a5a6cd28fa2ec43e45f7ec40e79fbae1a561e451b79bce60b59d0cd76394`;
the pre-sync rollback archive SHA-256 is
`aa6726e94967370fe31f17a8d5b9d76b7e8ddd7573ff45312efa5cf7dad7ec04`.
Pre/post service snapshots are byte-identical with SHA-256
`ce322158b9bf7d81e844f198095ac920cff2436ca1436e3c01c9f15595634fdc`.
The uncounted first live attempt used `root` and stopped at PostgreSQL peer
authentication before reaching capability logic; the passing run used the
Odoo service account.

For the preceding ten-command native financial-report export batch, the server focused
regression passed 269 tests in 498.97 seconds, and the final client/runtime
selection passed 47 tests in 0.23 seconds locally and on the synchronized
server. One shared read-only smoke passed in 33.50 seconds and performed 40
native exports: ten report commands times PDF/XLSX in each of `v4-dev` and
`v4-e2e` as uid 5/company 1. Public CLI end-to-end checks also passed for a
39,097-byte trial-balance PDF in `v4-dev` and a 7,482-byte general-ledger XLSX
in `v4-e2e`. Capability-ID SHA-256 is
`b14c19b3fcc05787deb9c924f200166a5ce7139d4648a404f697aabee493ba64`;
registry-file SHA-256 is
`51511d050cd6b28f037741f61107acab9734b618fc6029e82a55b185383b0d48`;
canonical registry digest is
`2c3009784a48c56fe337cd3f09a634c2f4a411302575aac0b6a61930343654b2`.
Evidence is retained under
`/opt/odoo-accounting-cli-v4/.tooling/financial-report-export-batch-2282bf69-1a4f-4356-a6b1-a19103d11f86`.
The pre/post service snapshots are byte-identical with SHA-256
`baa61f348401615814ebee1a2f59071036d5be8ae79765febcb87fa5217de105`.
The seven-file and two-file pre-overwrite rollback archives are readable; they
are batch-level file backups, not a full server or database snapshot.

For coverage planning, both isolated databases have an identical set of 82
installed modules. A read-only audit identified 39 accounting or adjacent
modules, partitioned into 25 primary-scope, five conditional EDI/compliance, and
nine UI/communication/technical modules that do not need independent CLI
commands. Command count is therefore not treated as a coverage percentage;
future completion requires an explicit module/workflow/lifecycle gap matrix.

At the historical core-object checkpoint, the clean full local regression
passed 2052 tests with 127 opt-in live tests skipped in 1086.74 seconds. That
batch's synchronized server-focused selection passed 258 tests in 110.05
seconds. Its guarded read-only live runs recorded
`1 passed in 154.45s` for `v4-dev` and `1 passed in 152.27s` for `v4-e2e`,
covering all twelve commands. The batch performed no business write. The live
check also established that Odoo 19 exposes
`account.payment.term.line.days_next_month` as a numeric string; the response
validator and schema now accept that validated representation.

For the preceding reference-object batch, 382 focused local tests passed in
78.94 seconds, the final complete local regression passed 2208 tests with 129
opt-in live tests skipped in 827.35 seconds, and the synchronized
server-focused selection passed 382 tests in 118.32 seconds. The guarded
transactional live smoke covered all twelve commands in both dedicated aliases
and recorded `2 passed in 6.71s`, taking retained live evidence to 77 reads and
25 writes. The first live run exposed the legitimate Odoo value
`categ_id=False`; product `category` normalization and schema now accept either
a named reference or `null`, and the repeated live run passed. Temporary
product, analytic-account, and fiscal-position fixtures were rolled back with
the whole transaction, and a fresh cursor proved zero residue. There was no
persistent business write and no Odoo, Nginx, PostgreSQL, Pi, V2, or V3 service
restart. The registry capability-ID SHA-256 is
`cd8d1f5672ec9d779875389c00ec3276a890927cb5b5543a67ed840cf714736d`;
the verified wheel SHA-256 is
`a7f5e50cde6b10bd75c515463db3bc57387c845bc3afa3941cd52f625a123f96`.

For the preceding accounting-configuration read batch, the final focused local
selection passed 484 tests in 86.71 seconds, the complete local regression
passed 2310 tests with 131 opt-in live tests skipped in 526.90 seconds, and the
synchronized server-focused selection passed 484 tests in 124.70 seconds. The
guarded transactional live smoke covered all eight commands in both dedicated
aliases and recorded `2 passed in 6.41s`, taking retained live evidence to 85
reads and 25 writes. Temporary cash-rounding and journal-group fixtures were
rolled back with the whole transaction, and a fresh cursor proved zero residue.
There was no persistent business write and no Odoo, Nginx, PostgreSQL, Pi, V2,
or V3 service restart. That checkpoint's registry capability-ID SHA-256 is
`91dc2d269fd70d4b0badfae1e0a255750a9201ffb6c1194f013672503256fb64`;
the verified wheel SHA-256 is
`bf280a27dac85f681f2fd9767f771d68f08d7f3507c8b71cabafa8efc3206476`.

For the historical payment/reconciliation object read batch, the final focused
local selection passed 618 tests in 77.48 seconds, the complete local
regression passed 2444 tests with 133 opt-in live tests skipped in 492.22
seconds, and the synchronized server-focused selection passed 618 tests in
134.89 seconds. The guarded transactional live smoke covered all eight
commands in both dedicated aliases and recorded `2 passed in 6.80s`, taking
retained live evidence to 93 reads and 25 writes. Each alias used one rollback-
only transaction: temporary partner, bank-account, and bank-statement fixtures
were removed, a fresh cursor proved zero marker residue, and the original bank
statement line was restored to its unbound state. Existing partial and full
reconciliations supplied the remaining live rows. There was no persistent
business write and no Odoo, Nginx, PostgreSQL, Pi, V2, or V3 service restart.
That checkpoint's registry capability-ID SHA-256 is
`9d0dd71415220c7a05e6a1e600f56d811459c978d840aee91d14cb94b6af66c6`;
the verified wheel SHA-256 is
`20c663f1637c35c0433d08c364b920c784296f3854e21cddc0cc96217c2c7c85`.

For the preceding analytic/budget read batch, the final focused local selection
passed 825 tests with 2 guarded live cases skipped in 96.40 seconds. The final
complete local regression passed 2651 tests with 135 opt-in live tests skipped
in 553.11 seconds, and the synchronized server-focused selection passed 825
tests in 164.16 seconds. The guarded transactional smoke covered all eleven
commands in both dedicated aliases and recorded `2 passed in 7.54s`, taking
retained live evidence to 104 reads and 25 writes. Each alias created temporary
analytic, distribution, applicability, and budget fixtures inside one
transaction; two overlapping budget lines deliberately produced two official
`budget.report` rows with the same `aal{id}` row key, and the dedicated
composite cursor preserved both. Whole-transaction rollback and a fresh cursor
proved zero fixture residue. There was no persistent business write and no
Odoo, Nginx, PostgreSQL, Pi, V2, or V3 service restart. That checkpoint's
registry capability-ID SHA-256 is
`f06fde8711e20a7e4a2853301707e946bb49fe38aec65dcb6c836e14d96de46b`;
the verified wheel SHA-256 is
`0f2f8c3ae75c0a0c8c07e88322bdab0e7a8381df0f2db11e8c4f34d153de729f`.

For the preceding document-lifecycle write batch, 326 focused local tests passed
in 178.43 seconds. The final complete local regression passed 2732 tests with
136 opt-in live tests skipped in 598.63 seconds, and the synchronized
server-focused selection passed 326 tests in 302.59 seconds. One guarded
transactional smoke exercised all eight new commands, the existing create and
post prerequisites, immediate replay, the `ref` marker migration, and fresh-
cursor rollback verification in both dedicated aliases; it recorded `1 passed
in 10.10s` and raised retained live evidence to 104 reads and 33 writes. No
business record was committed and no Odoo, Nginx, PostgreSQL, Pi, V2, or V3
service was restarted. The capability-ID-list SHA-256 is
`a9ef0676628249f342fbdf580f85fdca85d4bb1e68e8f48fd026b2627fb43b47`;
the registry-file SHA-256 is
`71398c69324d16a26a3b5efa79577197a3db51c495f3d3726a0ecde9e20e2ee9`;
the verified wheel SHA-256 is
`b3e6be281ef21dad90bc96994e09d9acf9360648a4a1dffddeca268d63ea3ba5`.

For the preceding payment/bank reconciliation batch, 72 focused local tests
passed, followed by a complete local regression of 2802 passed with 137 opt-in
live tests skipped. The synchronized server-focused selection also passed all
72 tests. One shared guarded smoke ran all ten commands across both
`odoo_cli_v4_dev` and `odoo_cli_v4_e2e` as configured uid 5/company 1 and
recorded `1 passed in 10.78s`. Whole-transaction rollback and fresh-cursor
absence checks proved that the temporary payment, invoice, and bank-transaction
fixtures left no residue. Retained live evidence is now 107 reads and 40
writes. The capability-ID-list SHA-256 is
`d7685dbfd2461eb436593566ece52efdbf0120fbea00aeeceafed864e54c120e`;
the registry-file SHA-256 is
`95a41290f9feb72e3b786247834a131635ca003144b4bdd0c766f5d69cfef618`.
The synchronized source archive is 574618 bytes with SHA-256
`cae7e6fe2aff2f27751282803d1cf2daeb80f149388450186f0d13136a5fe994`.
The clean wheel is 574779 bytes with SHA-256
`e5c185984a198fda856b1caa921373e91e4a3c2d4ee8c3c0dfd28fb37315fc09`;
it contains 303 schemas and all 170 capabilities, with no backslash-named
archive entries. No business database, Odoo source, V2/V3 chain, or service was
modified or restarted.

For the preceding analytic/budget write batch, the focused local selection passed
386 tests, the synchronized server-focused selection passed the same 386 tests,
and the final server runtime selection passed 79 tests. The complete local
regression passed 2,926 tests with 138 explicitly gated live tests skipped and
zero failures in 1,927.74 seconds. One guarded transactional smoke exercised
all nine commands, their first execution, and immediate deterministic replay in
both `odoo_cli_v4_dev` and `odoo_cli_v4_e2e` as configured uid 5/company 1; it
recorded `1 passed in 6.09s`. Whole-transaction rollback and a fresh cursor
proved zero residual analytic accounts, budgets, or budget lines. Retained live
evidence is now 107 reads and 49 writes. The capability-ID-list SHA-256 is
`41d06b41aa49596ad0f67d9c343761af0918c68c902c1046bcf0d1684e2ddcda`;
the registry-file SHA-256 is
`72b03d16135e337c2407b05aa77df265c143c8f6f95e3a6a75ece2fffbc225dd`.
The synchronized source archive is 132872 bytes with SHA-256
`18e0c881861e770754ccca8e055f804e0cd0d464d0f6d9678c4f72ad6db24ea1`.
The clean wheel is 595273 bytes with SHA-256
`b93dd572f61d07953645b300c67a846b565af1514d90dab8ad8a3970b15e341e`;
its 392 entries contain 321 schemas, all 179 capabilities, and 158 handlers,
with no backslash-named entries. Thirty-six malformed schema-name duplicates
and 28 malformed project-name duplicates were moved recoverably out of the
active tree to `/tmp/odacv4-malformed-schema-names-20260826` and
`/tmp/odacv4-malformed-project-names-20260826`; the active tree contains zero
such names. `analytic.account.create` and `budget.create` are honestly
`degraded`: their visible markers are not database-unique and do not prove
concurrent exactly-once creation. The other seven writes use deterministic keys
plus current/target-state rechecks; without an operation store, an old request
may become effective again after an intervening state change. No business
database, Odoo source, V2/V3 chain, or service was modified or restarted.

For the preceding partner master-data batch, 11 commands are handler-backed:
`partner.search`, `partner.get`, `partner.create`, `partner.update`,
`partner.archive`, `partner.restore`, `partner.accounting.update`,
`partner.bank_account.create`, `partner.bank_account.update`,
`partner.bank_account.archive`, and `partner.bank_account.restore`. The final
post-fix partner selection passed 98 tests locally with its guarded live case
skipped, and the synchronized server-focused selection passed 428 tests in
84.24 seconds. The final post-sync server registry evidence selection passed
24 tests in 81.97 seconds. The complete local regression passed 3,060 tests with 139
explicitly gated live tests skipped and zero failures in 1,687.53 seconds
(28:07). One guarded transactional smoke exercised first execution and
immediate replay for all eleven commands in both `odoo_cli_v4_dev` and
`odoo_cli_v4_e2e` as configured uid 5/company 1; it recorded `1 passed in
7.03s`. The smoke temporarily linked `base.group_partner_manager` inside the
rollback-only transaction; this is fixture authorization, not a default-runtime
permission claim. Whole-transaction rollback plus fresh-cursor SQL checks
proved zero residual partner, bank-account, or temporary user-group rows.
Retained live evidence is now 109 reads and 58 writes. The capability-ID-list
SHA-256 is
`c42bdb67c1a540293d91ef5e84d1a4e0291a36a2b5eb8e7261660cf73dc7238a`;
the registry-file SHA-256 is
`5583f4b43a7532774b3e8c3365205321b6ed38be8fc9aaaafc4868d1a3fae181`.
The final 42-entry source archive is 199107 bytes with SHA-256
`f6364dadeb9fe53a91cc52685b52218e4f546da8863701a972a60ffcc9203c8c`;
every archived file is byte-identical to the final active-tree file. The clean
wheel is 622561 bytes with SHA-256
`dce638bc8e9b15a60e39f6045868ff277be4545ef52697bf283da065fac38388`;
its 414 entries contain 343 schemas, all 190 capabilities, and 169 handlers,
with no duplicate or backslash-named entries. `partner.create` is honestly
`degraded` because its visible `ref` marker is not database-unique and does not
prove concurrent exactly-once creation. The other eight writes use
deterministic target-state rechecks without an operation store. In these
isolated databases the optional `phone_validation` module is absent, so reads
retain `mobile: null`; writes accept null/omission and fail closed for a
non-null mobile value. This batch issued no service restart and modified no
business database, Odoo source, or V2/V3 chain. A later 2026-08-27 06:23 Odoo
restart was traced to `apt-daily-upgrade`/`needrestart` after an OpenSSL upgrade;
the service stopped cleanly, and the audit found no V4 deployment relation.

For the preceding accounting-configuration write batch, 12 commands are handler-
backed: `account.account.create`, `account.account.update`,
`account.account.archive`, `account.account.restore`, `journal.create`,
`journal.update`, `journal.archive`, `journal.restore`, `tax.create`,
`tax.update`, `tax.archive`, and `tax.restore`. The registry now contains 202
capabilities and 181 executable handlers (110 reads and 71 writes), with 109
read and 70 write live success paths. It retains 367 versioned schemas and has
168 `unconfigured`, 13 `degraded`, and 21 `disabled` statuses. The earlier
broad server selection passed 423 tests in 767.33 seconds, and the final
focused server selection passed 103 tests in 61.13 seconds. One guarded dual-
database transactional smoke exercised first execution and immediate replay
for all 12 commands and recorded `1 passed in 9.55s`. The complete local
regression then recorded `3186 passed, 140 skipped, 1 failed in 3314.58s`; its
sole failure was a stale CLI-contract assertion that still expected the prior
190-ID registry instead of the actual 202 IDs. After that test-only expectation
was corrected to 202, the complete CLI-contract file passed `14 tests in
167.25s`. No second 55-minute full sweep was run after changing only that
assertion, so this checkpoint does not misreport an inferred 3187-pass run.
The capability-ID-list SHA-256 is
`6ecb58789446447a2d3e4d89957eb6cd87147b0346fd68a6fa3cef23b5dc08f3`;
the registry-file SHA-256 is
`5f224b7661ad07844b2cebb694fb5e864eb78dbcbefc2b9e1b91c28c0e97e81a`;
and the canonical registry digest is
`91d087511423deb5c7aede88ec28452468ec570b44b8a8d79649e7cdbf8563d0`.
The clean 438-entry wheel is 649140 bytes with SHA-256
`37646e68151cbbfcefe70f5e3e74df0919b1dd6a3e18c50876a5a95f7b1dbf55`.
The synchronized 58-file source archive is 158280 bytes with SHA-256
`f51cdcf1da0ff7d85f811cff08cb27866c00871549c55972546f8b2adec453ee`.
This batch modified no business database, Odoo source tree, or V2/V3 chain and
issued no service-restart command. During verification, the pre-existing Odoo
main process nevertheless restarted automatically on 2026-08-27: at 10:25:26
its VMS exceeded the configured 2 GiB soft limit and Odoo initiated a phoenix
reload; `_reexec()` then resolved basename `python` outside the virtual
environment, failed to import the venv-only `passlib`, and exited. The existing
systemd `Restart=always` policy recovered the service at 10:25:38. Server logs
show the same daily-pattern failure on prior dates, and the current batch has no
service-control, signal, package-install, or persistent `PYTHONPATH` path.

The latest accounting-depth batch does not add capability IDs. It deepens 12
existing interfaces: `customer_invoice.create`, `vendor_bill.create`,
`invoice.lines.replace`, `customer_credit_note.create`, `vendor_refund.create`,
`journal_entry.create`, `journal_entry.lines.replace`,
`receivable.payment.register`, `payable.payment.register`,
`invoice.payment_status.inspect`, `reconciliation.apply`, and
`reconciliation.undo`. Invoice and bill creation now covers payment terms or a
due date, business references, product-backed lines, discounts, and optional
analytic distribution; journal entries cover references, foreign-currency
amount pairs, and optional analytic distribution; payment registration accepts
a partial amount; payment-status inspection returns validated outstanding
items; and reconciliation apply/undo uses Odoo's native invoice-widget paths,
including targeted undo without discarding unrelated partial reconciliations.
The batch retains the fixed ACL, company/user scope, confirmation, replay, and
isolated-database boundaries and introduces no arbitrary ORM dispatcher.

The final current-tree four-file contract/runtime selection passed all 496
tests in 826.41 seconds. The independent current registry selection passed all
17 tests in 197.19 seconds. The synchronized server retained its final 56-test
invoice/runtime critical pass plus the six directly affected public undo tests;
no inferred 496-test server run is claimed.

One guarded shared smoke ran the full chain in both `odoo_cli_v4_dev` and
`odoo_cli_v4_e2e`; it recorded `1 passed in 16.91s`. All 11 target writes ran
once and then replayed immediately, while payment status was inspected before
assignment, after assignment, and after targeted undo. Each alias used one
outer rollback transaction, and a fresh cursor proved the recorded move,
payment, and product-fixture IDs plus markers absent. The configured uid 5
executed every handler without `sudo` or
temporary group elevation. Optional analytic fields have contract/runtime
coverage but no positive live analytic example because uid 5 does not have the
analytic group. Unrelated-partial preservation is live-verified; multi-term
graph preservation has contract/runtime coverage but no positive multi-term
live fixture. At that accounting-depth checkpoint the 202/181 inventory and
109-read, 70-write live-success counts were unchanged.

That checkpoint's capability-ID-list SHA-256 is
`6ecb58789446447a2d3e4d89957eb6cd87147b0346fd68a6fa3cef23b5dc08f3`;
the registry-file SHA-256 is
`c2f0fe18d1646b0b218fe3860400a26ae997f691291e438eef684acd377db5be`;
and the canonical registry digest is
`6eb4404cf3f31d7ce140db41f0346444a6edcd85d7e9720ff9163760623f02b2`.
The final 23-file batch source archive is 201732 bytes with SHA-256
`de9bf4ccce8f76502d835e001f2880d346dc0b8dcd77264e556c74302d179c36`.
The final wheel is 660021 bytes with SHA-256
`7f8ab0ba3b6e9ac877d74ca9855df1a720248f43631db0d60c7b1071447baa00`;
its 438 unique entries contain all 367 schemas, 202 capabilities, and 181
handlers. A clean-wheel install returned the same 202-ID registry and canonical
digest. All 23 active server files match the local tree byte-for-byte. A
post-smoke read-only check found `odoo19`, Nginx, and PostgreSQL 16 active; the
Odoo start timestamp remains 2026-08-27 10:25:38 CST, so this batch caused no
new service start or restart.

The preceding management-reporting/period-context batch adds eight reads:
`report.customer_statement`, `report.followup`, `invoice.analysis.search`,
`invoice.analysis.summary`, `company.lock_dates.inspect`,
`company.fiscal_year.resolve`, `fiscal_year.search`, and `fiscal_year.get`.
The registry now has exactly 210 IDs, 189 handlers (118 reads and 71 writes),
383 schemas, and statuses of 176 `unconfigured`, 13 `degraded`, and 21
`disabled`. Live success evidence now covers 117 reads and 70 writes.

Focused capability/bridge/runtime tests passed 131 cases; the unified new CLI
selection passed 6, the two report CLI cases passed 2, the registry selection
passed 17, and final count-related selections passed 14 locally and 43 on the
synchronized server. One shared guarded live test ran all eight reads in both
dedicated database aliases as uid 5/company 1 and recorded
`2 passed in 6.62s`; rollback plus a fresh cursor proved the transaction-local
fiscal-year fixture absent.

The current capability-ID-list SHA-256 is
`6ba5e3d877b6fa857d1689c14da30132b63572c801e2d25b4af4e30c10a6dd82`;
the registry-file SHA-256 is
`58de9401661a4ebeefc7892c3a4da20d38bda1fe34d1502b9588d957ee936d94`;
and the canonical registry digest is
`50451ae4a3b6d145ad4d89c3b3f6f7a11b70472a6f35099b609842d19fc3e19f`.
The explicit 41-file source archive is 156351 bytes with SHA-256
`37258845be076e3c6432d6291ed6fc690578b2befd8e3674a9e848d5f01d0191`.

The historical 218-ID account-return/journal-analysis checkpoint added eight reads:
`account.return.search`, `account.return.get`, `account.return.summary`,
`account.return.type.list`, `account.return.check.list`,
`account.return.check.get`, `journal.accounting_date.resolve`, and
`journal_item.analysis.summary`. At that checkpoint the registry had exactly 218 IDs, 197
handlers (126 reads and 71 writes), 399 schemas, and statuses of 184
`unconfigured`, 13 `degraded`, and 21 `disabled`. At that checkpoint live
success evidence covered 125 reads and 70 writes.

The focused local feature selection passed 84 cases and the independent
registry/schema selection passed 29. The synchronized server passed 48 core
feature tests. One shared guarded live test ran all eight reads in both
dedicated aliases as uid 5/company 1 and recorded `2 passed in 5.09s`.
Transaction rollback plus a fresh cursor and an independent SQL query proved
zero return/check marker residue in both databases. No result is claimed for
the interrupted broader server pytest run; its SSH output stream closed before
an exit status was available.

That checkpoint's capability-ID-list SHA-256 is
`c96f9c1510501eaa3ca09b62a697b6577ddaa79688a9b30c563f704926c8cef3`;
the registry-file SHA-256 is
`e9180a7f420030debed3f535d920f1deae7e61b5a8f0d417af1a1720c686a4f3`;
and the canonical registry digest is
`274533a2aaf573b32029b507e21db7864fbd2ac2587637a14e344cfcffb299ec`.
All 37 synchronized files match the local tree byte-for-byte. The 37-file
synchronization archive is 149640 bytes with SHA-256
`f28becccf575a506d41fbed487f796e39e76e68ebd15c4d59580836556ba3140`.
The retained live log is
`/opt/odoo-accounting-cli-v4/.tooling/return-journal-analysis-live-run-1787882134143.log`
with SHA-256
`6e9d2ac69f14bfc2c9b00ba8609493cba67870f7173df29807d73eb5e09f033a`.
Odoo, Nginx, and PostgreSQL remained active with unchanged start timestamps and
restart counts; no service-control command was issued.

The historical 2026-08-28 order-document read batch added eight reads:
`sale.order.search`, `sale.order.get`, `sale.order.line.search`,
`sale.order.analysis.summary`, `purchase.order.search`, `purchase.order.get`,
`purchase.order.line.search`, and `purchase.order.analysis.summary`. The
registry now has 236 IDs and 215 handlers (144 reads and 71 writes), with 202
`unconfigured`, 13 `degraded`, 21 `disabled`, and 435 schemas. Local focused
tests passed 126 cases; the synchronized server selection passed 112. The
shared dual-database smoke recorded `2 passed in 7.26s`, and independent SQL
checks found zero partner, product, sale-order, sale-line, purchase-order, and
purchase-line residue in both isolated databases. Live evidence now covers 143
reads and 70 writes (213 total). Odoo/Nginx/PostgreSQL service snapshots were
identical before and after: `NRestarts=2/0/0`.

The 236-ID list SHA-256 is
`9032699a10ce3113c27e8ef538d180b331be143edaa365abb79bc0b3702c7232`;
the canonical registry digest is
`284657bf0e4292039cb85d15767c08ce0bf77c415cfb62addaffa8b123525a2f`;
the registry-file and CLI-list-file SHA-256 values are
`94c9b07f09ea72422c6d30626a330586d3f4bcfa3782ea9a159a9532705c3930`
and `43aa2ceaefbb34d7b55b4fc79e4a0e5e0b202fb40e21c1222bea7d0d6ad51604`.
The live JUnit and pre-live archive SHA-256 values are
`3e6c5463b10057ec287b0a5f3b2cccdce4167797a242bc4971e15389b979dfd1`
and `fe89d7cc0a6351e50e1639ebb0aafa82d63fa6b57962fa5d84cc4ab7272255e9`.

The current 2026-08-28 order-write batch adds twelve writes:
`sale.order.create`, `sale.order.update_draft`, `sale.order.lines.replace`,
`sale.order.confirm`, `sale.order.cancel`, `sale.order.reset_to_draft`,
`purchase.order.create`, `purchase.order.update_draft`,
`purchase.order.lines.replace`, `purchase.order.confirm`,
`purchase.order.cancel`, and `purchase.order.reset_to_draft`. The registry now
has 248 IDs and 227 handlers (144 reads and 83 writes), with 212
`unconfigured`, 15 `degraded`, 21 `disabled`, and 459 schemas. Live evidence
now covers 143 reads and 82 writes (225 total).

The new focused local selection passed `135 tests in 109.91s`. After repairing
pre-existing exact-count expectations, the affected regression passed `428
tests in 567.86s`; registry/runtime alignment passed `44 tests in 4.07s`, and
the cumulative-count selection passed `5 tests in 45.46s`. The synchronized
server focused selection passed `136 tests in 68.52s`, and its cumulative-count
selection passed `5 tests in 36.47s`. The final shared dual-database evidence
run recorded `2 passed in 7.74s`; another successful run recorded `2 passed in
8.29s`. Fresh SQL checks found zero temporary partners, products, sale orders,
sale lines, purchase orders, purchase lines, and temporary standard-group
memberships in each isolated database. Odoo 19, Nginx, and PostgreSQL
before/after snapshots were byte-identical.

The 248-ID list SHA-256 is
`383bc6b03694c40eeef978244f28f6e28e2440905e98c43e02274726db9f9d25`;
the canonical registry digest is
`5d10bd54a83a2d375f458fc1c8800ca0691068c054b3f9927dd00a03fba942c3`;
the registry-file SHA-256 is
`6f9caa3efc7c2c6d46d3a1ba6aa801a58e598590a9f77490e6506f036cc82d22`;
and the 107962-byte CLI list SHA-256 is
`509015066be34db397e1b0d623da791f435837a98a607adec384ec31ab8a4f07`.
The live log and JUnit SHA-256 values are
`8cb502a4b7c5a493a16646f81911231c96931da21d00488037de53b89f1d3a69`
and `bbacbeaa3b5aaa0ebd2e61e547565ee8eaff40bd6d5cca567b7a3d6383962c18`.
The identical service snapshots have SHA-256
`89933ce14d537588ccfa76126b7d1c7b476cbd44a2ff7ae68a1808ffe1b452ef`;
each residue file has SHA-256
`b9e038a67cb826e6fe86c15a414a3d485e2c7b95acce772508f6f66a7a8ef11c`.
The final 49-member, 205556-byte archive has SHA-256
`49c0a091fc8a2f10763acd05833bb20f42e3c1df6de0cdcff81c7a5bc3fd96e2`,
matching the synchronized server copy.

The historical 2026-08-28 accounting follow-up batch added or enabled nine writes:
`purchase.order.bill.create`, `purchase_bill.match`,
`purchase_bill.lines.unmatch`, `payment_term.create`, `payment_term.update`,
`payment_term.lines.replace`, `payment_term.archive`, `payment_term.restore`,
and `period.accrual.generate`. At that checkpoint the registry had 255 IDs and 236 handlers
(144 reads and 92 writes), with 218 `unconfigured`, 18 `degraded`, 19
`disabled`, and 477 schemas. The dual-database smoke passed `2 tests in 8.40s`;
each isolated database completed nine first executions and nine immediate
replays, with transaction rollback and temporary-group rollback both true.
The final focused local selection passed 123 tests; the synchronized server
selection passed 121. The server public `capabilities list` returned all 255
IDs with the canonical digest below. The live test used the public contract and
real runtime inside one rollback transaction; the public CLI/model mapping was
verified separately by the focused CLI tests.
The batch also corrected the Odoo 19 draft-vendor-bill contract to accept a
null native bill name. Capability-ID-list SHA-256 is
`af1c980ecac6e516ed988b152f7a69158ec7523f4e9d7e1cbfba874f5e4c8f0d`;
canonical registry digest is
`c8fff1a9975d6adcc23d32b1e5a39fd2b6ae5be6de6a8961d5bb61f0f9565b1f`.
The Odoo (`3547689`), Nginx (`2193677`), PostgreSQL (`2193725`), and Pi bridge
(`3296254`) process IDs and start times were unchanged after deployment and
verification; Nginx and PostgreSQL remained active.

The historical 2026-08-28 operational-inventory read batch added ten reads:
`product.category.list`, `warehouse.list`, `stock.location.list`,
`stock.operation_type.list`, `stock.route.list`, `stock.transfer.search`,
`stock.transfer.get`, `stock.move.search`, `inventory.on_hand.summary`, and
`inventory.availability.inspect`. The registry now has exactly 228 IDs and 207
handlers (136 reads and 71 writes), 419 schemas, and statuses of 194
`unconfigured`, 13 `degraded`, and 21 `disabled`. Live success evidence now
covers 135 reads and 70 writes.

The synchronized remote selection passed 138 tests. The final shared guarded
live run executed all ten reads in both `odoo_cli_v4_dev` and
`odoo_cli_v4_e2e` as uid 5/company 1 and recorded `2 passed in 5.49s`.
Independent post-rollback residue checks returned `0|0|0|0` for each database.
The retained log is
`/opt/odoo-accounting-cli-v4/.tooling/inventory-read-live-run-1787885244043.log`
with SHA-256
`b8b6afa9754d7f32236ba2fa43fdd01f66b9523f2fdeccc0601ee542d969bc6b`.

Two earlier attempts are not counted as evidence. The root-side attempt stopped
at peer authentication. The first Odoo-user run then failed because its fixture
had `categ_id=False`; that transaction rolled back and committed nothing. After
the fixture was corrected, the dual-database run above passed.

The CLI returned 228 unique, sorted capability IDs; their list SHA-256 is
`709e4ce12c7d8cf5dcfebb9dbf45a6082aff1ebca380f73aec823d70a1d3088f`.
The canonical registry digest is
`bc644e686f863ae6cca947c4c040bfecce7395d1c84e9dd8a43b9c83984d7b94`,
and the registry-file SHA-256 is
`3e357d2cf4ba748ff4175603dd4c8daf1b6b635efb948291da63b06b7e965391`.

Nginx and PostgreSQL are active with `NRestarts=0`. Odoo is active with
`NRestarts=2`: it exited automatically at 10:24:43 after a passlib
`ModuleNotFoundError`, and systemd restarted it at 10:24:53. That event preceded
the 10:40 deployment and the successful live run at 10:47. This batch issued no
service-control command, but the evidence does not support claiming that no
restart occurred during the overall observation window.

G4 completion does not make generated capabilities available. G2 database
provisioning and accounting fixture v1 are independently verified, but G2
remains open until the full fixture matrix is versioned and verified. G3
remains open until the remaining specialized contracts and consolidated write
controls are implemented; G5 remains open until all enabled capabilities pass
real Odoo verification.

No pre-existing Odoo database, service, V2/V3 installation, Odoo source tree,
or legacy harness is a V4 write target.

## Foreign-currency settlement workflow checkpoint — 2026-09-01

This checkpoint starts from local/GitHub baseline
`22df4510ead3f0f3ef5402c2467f0b5d0736812f`. It adds no capability ID, schema,
production handler, or Odoo configuration. The authoritative totals therefore
remain 366 mixed-domain IDs, 351 enabled handlers (214 reads and 137 writes),
708 schemas, 314 `unconfigured`, 37 `degraded`, and 15 `disabled`.

The new guarded integration workflow proves twelve existing public capabilities
together rather than counting their registration as coverage:
`currency.rate.list`, `currency.convert`, `customer_invoice.create`,
`vendor_bill.create`, `invoice.post`, `invoice.get`,
`receivable.payment.register`, `payable.payment.register`,
`invoice.payment_status.inspect`, `payment.get`, `journal_item.search`, and
`report.trial_balance`. The shared real-ORM CLI helper only gained the two
currency port mappings needed to dispatch the first two reads.

Each isolated alias created one USD 100 customer invoice and one USD 100 vendor
bill dated 2025-01-15, when 1 USD equalled CNY 1.36. It registered the inbound
and outbound payments on 2025-02-01, when 1 USD equalled CNY 1.37. Both source
documents were fully reconciled, each payment read back at CNY 137, and Odoo
created one balanced CNY 1 exchange-difference entry per settlement. Odoo 19's
monthly journal sequence assigned those exchange moves the accounting date
2025-02-28. The workflow therefore queries the trial balance through that
accounting date and verifies an exact debit and credit delta of CNY 548.

The final server run passed both `v4-dev` / `odoo_cli_v4_dev` and `v4-e2e` /
`odoo_cli_v4_e2e` in one pytest case: `1 passed in 443.73s`, exit 0. Per alias it
recorded 29 public CLI calls, six immediate idempotent replays, two source
documents, two payments, two exchange moves, uid 5, company 1, `su=False`, and
`rollback_verified=true`. Every write stayed inside one outer transaction per
database; a fresh cursor verified the marked records absent after rollback.

Five earlier executions are retained but are not acceptance evidence. They
respectively exposed the root/peer-authentication launch mismatch, an overly
strict decimal-text assertion, an incorrect assumption that exchange entries
retain the payment date, a test-only string/date type mismatch, and a trial
balance range that stopped before the exchange accounting date. The first and
second stopped before target writes, as did the fourth test-only type failure;
all workers that entered a database ran the same rollback/fresh-cursor cleanup
path. One additional process preflight exited before pytest because its own
command line matched the check; it was not a live execution.

Local collection, Ruff check/format, and `git diff --check` passed. Server
collection found exactly one guarded test; the server project virtualenv does
not contain Ruff, so the corrected server static check intentionally used pytest
collection while local Ruff remained authoritative. Independent review found no
submission blocker.

Private server evidence directory:
`/opt/odoo-accounting-cli-v4/.tooling/accounting-fx-settlement-20260901-6d19c2a9f4b7`.
The passing log SHA-256 is
`923bc7d8cf2431d098cd546cffe10f413585363fd253a63173ba958e1d6a472e`;
the corrected collection log SHA-256 is
`e0199936360688128e2eae2261c0aa60c96e2b4dc2f198785bf7c5b6eb74e3ce`.
The final deployed test and shared-helper SHA-256 values are
`8415273c0f8031d436e26f77a393c53ccf367e0bfa4c09936eb778fe5526578f`
and `2d20199ad019a299c37589319dda45d8fbd8afc2e4c45c47909cecc33a7201b4`.

Before and after the successful run, Odoo19 remained active on PID `3995891`
with `NRestarts=4`; Nginx and PostgreSQL remained active. No service-control
command was issued. Root filesystem use remains 96%, with about 3.6 GB free.
This checkpoint proves one positive, untaxed, full-settlement USD/CNY workflow;
it does not prove partial settlement, early-payment discount, write-off,
multi-company, arbitrary currencies, or complete accounting coverage.

## Analytic plan, account, and manual-line lifecycle checkpoint — 2026-09-02

Starting from pushed baseline `b8eda33b0b6f6caeedd2f616216ad5e968bdfcbe`,
this batch adds eight capabilities: `analytic.plan.create/update`,
`analytic.account.archive/restore`, `analytic.line.create/update/delete`, and
`analytic.line.summary`. The authoritative totals are now 374 IDs, 359 enabled
handlers (215 reads and 144 writes), 724 schemas, 318 `unconfigured`, 41
`degraded`, and 15 `disabled`. The capability-ID-list SHA-256 is
`ab1e11c994f6c3d27c4eaa310e04f4967c5c9c3f275a3fcde0dbf9f1c2ba0992`;
the canonical registry digest is
`77325bffca94023803ce765b6a30d8fb3d2b913d2f43b91ab9986d30fcce25bc`.

Plan writes only create or update child plans. Account state changes are company
scoped. Manual line writes are restricted to the Project root plan,
`category=other`, and `move_line_id=False`; they do not mutate accounting-generated
lines. Summary reads use Odoo 19's dynamic analytic-plan column and aggregate
canonical amount and unit-amount strings by analytic account. Create uses a
visible deterministic marker without claiming concurrent exactly-once behavior.
Delete verifies absence but has no tombstone, so later retries honestly return
`record_not_found` instead of pretending to replay.

Final local selections passed 119 core/public/runtime cases, 28 CLI cases, and
11 affected schema/contract cases; Ruff, Python compilation, and `git diff
--check` passed. On the synchronized server, collect-only found one guarded live
case, the final fast selection passed `148 passed in 148.17s`, and the slow
registry/schema closure passed `4 passed in 186.80s`. The shared real-ORM test
passed both `v4-dev` / `odoo_cli_v4_dev` and `v4-e2e` / `odoo_cli_v4_e2e` in one
pytest case: `1 passed in 10.64s`. Per alias it exercised all eight new commands
inside the existing 17-capability analytic/budget chain as uid 5, company 1, and
`su=False`. A savepoint proved that line deletion rolls back to a restored row;
the outer transaction then rolled back and a fresh cursor proved all marked plan,
account, line, budget, and budget-line records absent.

Private evidence directory:
`/opt/odoo-accounting-cli-v4/.tooling/analytic-lifecycle-20260902-W54c2yQO`.
The 35-file deployment archive is 2652160 bytes with SHA-256
`b38659ebdccfe04ee923c1f3806aeb0b420c347fb24144f1642fef8dc405c7f3`;
all deployed files were rehashed unchanged after acceptance. The pre-sync backup
contains 19 existing files. Fast, registry, collect, and live log SHA-256 values
are respectively
`9416afd3ec73a8c2a55436c18f8e8d1455fc5f7d7cd40c0df8c7dfa9b06b045a`,
`450ab25e22f875a58368c7b4e52cc16aaa65c9da1021a922c12c1b760cb97adb`,
`0ef55d33e8e19da0af221a2572360fd4e639bbf56d0c1b6755728213b82dba18`,
and `f81b8b08942e88c5bdf8ce7e89f2bd10fd5e96c512d37a7395f767a97d68564a`.

No service-control command was issued. Odoo nevertheless exited automatically at
10:25:36 with the server's existing `ModuleNotFoundError: passlib` environment
problem and systemd restarted it at 10:25:46. That event happened before live
acceptance and is not attributed to this CLI batch. Live-before, live-after, and
final snapshots are byte-identical: Odoo PID `959127`, `NRestarts=1`, with Odoo,
Nginx, and PostgreSQL active. No live worker remains. Root disk use remains 96%
with about 3.5 GB free.
