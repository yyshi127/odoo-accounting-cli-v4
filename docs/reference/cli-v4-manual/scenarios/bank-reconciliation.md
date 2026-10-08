# 银行流水、对账单、核销及核销差额

录入和维护银行流水、对账单，配置银行默认科目和日记账流动性，查找匹配候选，建立或撤销银行匹配、部分或全额核销，维护对账模型及其行，并查看银行对账报告。核销与实际现金收付是不同操作；reconciliation.write_off 针对银行流水，支付登记差额由相应支付接口参数控制。

[回到总说明书](../../CLI_V4_MANUAL.md) · [新会话使用指南](../USAGE_GUIDE.md)

<a id="cap-bank-statement-create"></a>

## bank.statement.create — 创建含期初与期末余额的银行对账单

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`concurrent_idempotency_limit` — Optional native name/date override generated statement header; omitted fields keep native defaults and old keys. Later membership changes can recompute native date.
- 内部domain：`bank_reconciliation`；来源模型：account.bank.statement, account.bank.statement.line, account.journal, account.move, res.company, res.currency；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.bank.statement.line:read, account.bank.statement.line:write, account.bank.statement:create, account.bank.statement:read, account.journal:read, account.move:read, res.currency:read。
- 请求/响应合同：`schemas/v1/bank.statement.create.request.schema.json` / `schemas/v1/bank.statement.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run bank.statement.create --request "@request.json" --idempotency-key "bank.statement.create:1:a67d85e5d7924e5c91cbf9d8afb41975" --confirm "bank.statement.create"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "transaction_ids": [
      1
    ],
    "reference": "Example",
    "balance_end_real": "1"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transaction_ids","reference","balance_end_real"]} |
| parameters.transaction_ids | array | 必填（所在对象出现时） |  | Unique transaction IDs; the public contract normalizes them to ascending order. | {"maxItems":100,"minItems":1,"uniqueItems":true} |
| parameters.transaction_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.reference | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| parameters.reference | null | 分支约束 | oneOf[1] |  |  |
| parameters.reference | string | 分支约束 | oneOf[2] |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |
| parameters.balance_end_real | string | 必填（所在对象出现时） |  |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])","resolved_ref":"#/$defs/signedDecimal"} |
| parameters.balance_start | string | 可选（可能有条件限制） |  |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])","resolved_ref":"#/$defs/signedDecimal"} |
| parameters.name | string | 可选（可能有条件限制） |  | 名称/行说明 | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |
| parameters.date | string | 可选（可能有条件限制） |  |  | {"format":"date"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"bank.statement.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"bank.statement.create"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：native_statement_create_or_write_with_optional_currency_rounded_balance_start_and_existing_contiguous_membership_rules
- `verify`：explicit_start_and_end_reread_or_native_end_recompute_for_start_only_without_financial_line_change
- `idempotency`：company_contiguous_transaction_set_and_full_normalized_parameters_recheck_without_concurrent_exactly_once_guarantee
- `reverse`：bank.statement.delete

### 已登记测试与证据范围

- `unit`：`implemented`；Focused closed preview inputs/results, native scopes, optional field normalization and unchanged legacy omission/key tests; execution is required before acceptance.；引用：tests/unit/test_accounting_settlement_batch.py, tests/unit/test_bank_settlement_write_contract.py, tests/unit/test_bank_settlement_inputs_runtime.py, tests/unit/test_bank_settlement_reads.py, tests/unit/test_bank_settlement_inputs_cli.py
- `integration`：`implemented`；Shared public CLI/native ORM workflow passed both isolated aliases in 21.89s as uid5/su=False/company1. Tax/invoice and installment/schedule consumers, signed nonzero discount cash rounding, nullable tax-group accounts, statement start/end/replay, foreign denials, preserved financial graphs and full fresh rollback verified. Callers supply both currencies and already-cash-rounded totals; native Float residuals stay unchanged. Transaction-only roles, no sudo business calls. Tax-closing/CABA posting, all hierarchy/localization/precision paths, automatic FX, sends and concurrent exactly-once are not claimed. Details: docs/execution/STATUS.md.；引用：tests/integration/test_accounting_settlement_batch_live.py, tests/integration/test_bank_settlement_inputs_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-bank-statement-delete"></a>

## bank.statement.delete — 删除银行对账单并保留银行流水

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`deleted_record_tombstone_unavailable` — The handler verifies statement absence and preserved ungrouped transactions after deletion, but keeps no persistent tombstone, so a later retry cannot distinguish its prior deletion from an unrelated disappearance.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.bank.statement, account.bank.statement.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.bank.statement:read, account.bank.statement:unlink, account.bank.statement.line:read, account.bank.statement.line:write。
- 请求/响应合同：`schemas/v1/bank.statement.delete.request.schema.json` / `schemas/v1/bank.statement.delete.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run bank.statement.delete --request "@request.json" --idempotency-key "bank.statement.delete:1" --confirm "bank.statement.delete"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "statement_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["statement_id"]} |
| parameters.statement_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"bank.statement.delete"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"bank.statement.delete"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_company_scoped_bank_statement_unlink_preserving_transactions
- `verify`：same_transaction_statement_absence_and_ungrouped_transaction_reread_and_response_schema_validation
- `idempotency`：record_absence_recheck_without_operation_store_or_persistent_tombstone
- `reverse`：not_reversible_deleted_statement_must_be_recreated

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover confirmation, runtime result contract, CLI dispatch, registry descriptor, delete boundary, and schemas.；引用：tests/unit/test_bank_statement_payment_maintenance_public.py, tests/unit/test_bank_statement_payment_maintenance_runtime.py, tests/unit/test_core_writes.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases through the public CLI as uid 5 with su=False, exercising all six bank/payment-maintenance commands, three immediate replays, native statement/payment readbacks, and fresh-cursor rollback verification.；引用：tests/integration/test_bank_statement_payment_maintenance_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-bank-statement-get"></a>

## bank.statement.get — 获取银行对账单详情

- 类型：只读；静态状态：`unconfigured`；handler：`bank_statement_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.bank.statement, account.bank.statement.line, account.journal, res.currency；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.bank.statement:read, account.bank.statement.line:read, account.journal:read, res.currency:read。
- 请求/响应合同：`schemas/v1/bank.statement.get.request.schema.json` / `schemas/v1/bank.statement.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read bank.statement.get --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "bank_statement_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["bank_statement_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.bank_statement_id | integer | 必填（所在对象出现时） |  | 银行对账单ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"bank.statement.search.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"bank.statement.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"bank.statement.search.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","reference","date","company_id","journal","currency","balance_start","balance_end","balance_end_real","is_complete","is_valid","problem_description","transaction_count"],"resolved_ref":"bank.statement.search.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.reference | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.balance_start | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.balance_end | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.balance_end_real | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.is_complete | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.is_valid | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.problem_description | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.transaction_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"bank.statement.search.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","reference","date","company_id","journal","currency","balance_start","balance_end","balance_end_real","is_complete","is_valid","problem_description","transaction_count"],"resolved_ref":"bank.statement.search.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.reference | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.balance_start | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.balance_end | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.balance_end_real | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.is_complete | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.is_valid | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.problem_description | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.transaction_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_company_scoped_core_object_read_action
- `verify`：same_transaction_acl_result_cursor_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request and response, fixed bridge action, company scope, ACL gates, ORM normalization, pagination where applicable, and CLI dispatch.；引用：tests/unit/test_core_object_reads.py, tests/unit/test_core_object_reads_bridge.py, tests/unit/test_core_object_reads_runtime.py, tests/unit/test_core_object_read_cli.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The shared live read-only smoke verifies the capability against both dedicated isolated database aliases as the ordinary accounting user.；引用：tests/integration/test_payment_reconciliation_read_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-bank-statement-pdf-export"></a>

## bank.statement.pdf.export — 导出银行对账单 PDF

- 类型：只读；静态状态：`unconfigured`；handler：`document_bank_statement_pdf_export`。
- 状态原因：`runtime_context_required` — The fixed native PDF handler is installed; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`document_exports`；来源模型：account.bank.statement, res.company, ir.actions.report；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.bank.statement:read, res.company:read, ir.actions.report:read。
- 请求/响应合同：`schemas/v1/bank.statement.pdf.export.request.schema.json` / `schemas/v1/bank.statement.pdf.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read bank.statement.pdf.export --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "statement_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["statement_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.statement_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"bank.statement.pdf.export"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["filename","format","mimetype","byte_count","sha256","content_base64"],"resolved_ref":"#/$defs/data"} |
| response.data.filename | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":255,"minLength":1} |
| response.data.format | 未限定 | 必填（所在对象出现时） | oneOf[2] | 输出格式 | {"const":"pdf"} |
| response.data.mimetype | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.byte_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.sha256 | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^[0-9a-f]{64}$"} |
| response.data.content_base64 | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==&#124;[A-Za-z0-9+/]{3}=)?$"} |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["filename","format","mimetype","byte_count","sha256","content_base64"],"resolved_ref":"#/$defs/data"} |
| response.data.filename | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":255,"minLength":1} |
| response.data.format | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 输出格式 | {"const":"pdf"} |
| response.data.mimetype | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.byte_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.sha256 | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^[0-9a-f]{64}$"} |
| response.data.content_base64 | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==&#124;[A-Za-z0-9+/]{3}=)?$"} |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_native_bank_statement_qweb_pdf_action
- `verify`：bound_record_pdf_bytes_hash_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover the fixed action, exact contract, bridge, runtime, CLI routing, registry metadata, and schemas.；引用：tests/unit/test_document_exports.py, tests/unit/test_document_exports_bridge.py, tests/unit/test_document_exports_runtime.py, tests/unit/test_document_export_cli.py, tests/unit/test_document_export_registry.py
- `integration`：`implemented`；The shared read-only live smoke covers the fixed document export batch in both isolated databases.；引用：tests/integration/test_document_export_batch_live.py
- `golden`：`planned`；Golden PDF evidence is pending.；引用：无
- `e2e`：`planned`；End-to-end natural-language routing evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-bank-statement-search"></a>

## bank.statement.search — 搜索银行对账单

- 类型：只读；静态状态：`unconfigured`；handler：`bank_statement_search`。
- 状态原因：`runtime_context_required` — Optional is_complete/is_valid boolean filters use native ORM search including the native validity search before paging.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.bank.statement, account.bank.statement.line, account.journal, res.currency；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.bank.statement:read, account.bank.statement.line:read, account.journal:read, res.currency:read。
- 请求/响应合同：`schemas/v1/bank.statement.search.request.schema.json` / `schemas/v1/bank.statement.search.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read bank.statement.search --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {}
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"resolved_ref":"#/$defs/parameters"} |
| parameters.journal_id | integer/null | 可选（可能有条件限制） |  | 日记账ID | {"default":null,"minimum":1} |
| parameters.date_from | string/null | 可选（可能有条件限制） |  | 开始日期 | {"default":null,"format":"date"} |
| parameters.date_to | string/null | 可选（可能有条件限制） |  | 结束日期 | {"default":null,"format":"date"} |
| parameters.is_complete | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.is_valid | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"bank.statement.search"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","reference","date","company_id","journal","currency","balance_start","balance_end","balance_end_real","is_complete","is_valid","problem_description","transaction_count"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].reference | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].balance_start | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].balance_end | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].balance_end_real | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].is_complete | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].is_valid | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].problem_description | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].transaction_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.has_more | boolean | 必填（所在对象出现时） | oneOf[2] | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | oneOf[2] | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2]/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | oneOf[2]/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | oneOf[2]/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | oneOf[2]/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | oneOf[2]/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | oneOf[2]/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","reference","date","company_id","journal","currency","balance_start","balance_end","balance_end_real","is_complete","is_valid","problem_description","transaction_count"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].reference | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].balance_start | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].balance_end | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].balance_end_real | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].is_complete | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].is_valid | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].problem_description | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].transaction_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[1]/then | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[1]/then | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | allOf[1]/then/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_company_scoped_core_object_read_action
- `verify`：same_transaction_acl_result_cursor_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request and response, fixed bridge action, company scope, ACL gates, ORM normalization, pagination where applicable, and CLI dispatch.；引用：tests/unit/test_core_object_reads.py, tests/unit/test_core_object_reads_bridge.py, tests/unit/test_core_object_reads_runtime.py, tests/unit/test_core_object_read_cli.py, tests/unit/test_capability_registry.py, tests/unit/test_bank_settlement_write_contract.py, tests/unit/test_bank_settlement_inputs_runtime.py, tests/unit/test_bank_settlement_reads.py, tests/unit/test_bank_settlement_inputs_cli.py
- `integration`：`implemented`；The shared live read-only smoke verifies the capability against both dedicated isolated database aliases as the ordinary accounting user.；引用：tests/integration/test_payment_reconciliation_read_batch_live.py, tests/integration/test_bank_settlement_inputs_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-bank-statement-update"></a>

## bank.statement.update — 维护银行对账单期初期末余额及流水归组

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Optional native name/date exact set and current-state replay; no changes to posted transaction journal items.
- 内部domain：`bank_reconciliation`；来源模型：account.bank.statement, account.bank.statement.line, account.journal, account.move, res.company, res.currency；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.bank.statement.line:read, account.bank.statement.line:write, account.bank.statement:read, account.bank.statement:write, account.journal:read, account.move:read, res.currency:read。
- 请求/响应合同：`schemas/v1/bank.statement.update.request.schema.json` / `schemas/v1/bank.statement.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run bank.statement.update --request "@request.json" --idempotency-key "bank.statement.update:1:28f952be0becb59b1ebc10645d8fc3da" --confirm "bank.statement.update"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "statement_id": 1,
    "changes": {
      "reference": "Example"
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["statement_id","changes"]} |
| parameters.statement_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.reference | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"oneOf":[{"type":"null"},{"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| parameters.changes.reference | null | 分支约束 | oneOf[1] |  |  |
| parameters.changes.reference | string | 分支约束 | oneOf[2] |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |
| parameters.changes.balance_end_real | string | 可选（可能有条件限制） |  |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])","resolved_ref":"#/$defs/signedDecimal"} |
| parameters.changes.balance_start | string | 可选（可能有条件限制） |  |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])","resolved_ref":"#/$defs/signedDecimal"} |
| parameters.changes.name | string | 可选（可能有条件限制） |  | 名称/行说明 | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |
| parameters.changes.date | string | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.changes.transaction_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":100,"minItems":1,"uniqueItems":true} |
| parameters.changes.transaction_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"bank.statement.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"bank.statement.update"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：native_statement_create_or_write_with_optional_currency_rounded_balance_start_and_existing_contiguous_membership_rules
- `verify`：explicit_start_and_end_reread_or_native_end_recompute_for_start_only_without_financial_line_change
- `idempotency`：requested_target_state_hash_and_result_replay
- `reverse`：bank.statement.update_with_prior_values

### 已登记测试与证据范围

- `unit`：`implemented`；Focused closed preview inputs/results, native scopes, optional field normalization and unchanged legacy omission/key tests; execution is required before acceptance.；引用：tests/unit/test_accounting_settlement_batch.py, tests/unit/test_bank_settlement_write_contract.py, tests/unit/test_bank_settlement_inputs_runtime.py, tests/unit/test_bank_settlement_reads.py, tests/unit/test_bank_settlement_inputs_cli.py
- `integration`：`implemented`；Shared public CLI/native ORM workflow passed both isolated aliases in 21.89s as uid5/su=False/company1. Tax/invoice and installment/schedule consumers, signed nonzero discount cash rounding, nullable tax-group accounts, statement start/end/replay, foreign denials, preserved financial graphs and full fresh rollback verified. Callers supply both currencies and already-cash-rounded totals; native Float residuals stay unchanged. Transaction-only roles, no sudo business calls. Tax-closing/CABA posting, all hierarchy/localization/precision paths, automatic FX, sends and concurrent exactly-once are not claimed. Details: docs/execution/STATUS.md.；引用：tests/integration/test_accounting_settlement_batch_live.py, tests/integration/test_bank_settlement_inputs_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-bank-transaction-counterparts-replace"></a>

## bank.transaction.counterparts.replace — 拆分或重新分类银行流水损益分录

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — 2–100 explicit P&L rows; same company currency only, native rounding and bank-account consumer; reject external/source-linked, tax-bearing and foreign-currency states. Runtime company/ACL context required. Native bank-account creation permission is required only when the helper actually creates an absent account.
- 内部domain：`bank_reconciliation`；来源模型：account.account, account.bank.statement.line, account.full.reconcile, account.journal, account.move, account.move.line, account.partial.reconcile, account.payment, res.company, res.currency, res.partner, res.partner.bank；向导：无。
- 必需模块：account, account_accountant；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.account:read, account.bank.statement.line:read, account.bank.statement.line:write, account.full.reconcile:read, account.journal:read, account.move.line:create, account.move.line:read, account.move.line:unlink, account.move.line:write, account.move:read, account.move:write, account.partial.reconcile:read, account.payment:read, res.company:read, res.currency:read, res.partner.bank:read, res.partner:read。
- 请求/响应合同：`schemas/v1/bank.transaction.counterparts.replace.request.schema.json` / `schemas/v1/bank.transaction.counterparts.replace.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run bank.transaction.counterparts.replace --request "@request.json" --idempotency-key "bank.transaction.counterparts.replace:1:399484b721ecb2c05b3fb6a05ccd2c74" --confirm "bank.transaction.counterparts.replace"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "transaction_id": 1,
    "lines": [
      {
        "account_id": 1,
        "label": "1",
        "balance": "1"
      },
      {
        "account_id": 2,
        "label": "1",
        "balance": "1"
      }
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transaction_id","lines"]} |
| parameters.transaction_id | integer | 必填（所在对象出现时） |  | 银行流水记录ID | {"minimum":1} |
| parameters.lines | array | 必填（所在对象出现时） |  | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":100,"minItems":2} |
| parameters.lines[] | object | 每个数组元素 |  | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["account_id","label","balance"]} |
| parameters.lines[].account_id | integer | 必填（所在对象出现时） |  | 会计科目ID | {"minimum":1} |
| parameters.lines[].label | string | 必填（所在对象出现时） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |
| parameters.lines[].balance | string | 必填（所在对象出现时） |  | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?)$(?![\\s\\S])"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"bank.transaction.counterparts.replace"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"bank.transaction.counterparts.replace"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：closed_inputs_and_exact_confirmation
- `execute`：fixed_native_bank_widget_counterpart_helper_as_business_user
- `verify`：original_liquidity_and_exact_rounded_PnL_multiset_posted_balanced_no_suspense
- `idempotency`：current_counterpart_state_recheck_without_store_old_request_can_act_again_after_changes
- `reverse`：bank.transaction.unmatch

### 已登记测试与证据范围

- `unit`：`implemented`；Focused fixed SDK/schema/CLI/native adapter contracts.；引用：tests/unit/test_bank_settlement_write_contract.py, tests/unit/test_bank_settlement_inputs_runtime.py, tests/unit/test_bank_settlement_reads.py, tests/unit/test_bank_settlement_inputs_cli.py
- `integration`：`implemented`；One shared public CLI/native dual-isolated smoke: UID5 su=False, split/replace/replay/liquidity/manual undo; existing bank reuse and native conditional creation ACL denial; temporary installed contact role only for creation fixture, restored inline. Fresh all-fixtures/settings/defaults/currency/all-user-group rollback verified.；引用：tests/integration/test_bank_settlement_inputs_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-bank-transaction-delete"></a>

## bank.transaction.delete — 删除未分组且未匹配的银行流水

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`deleted_record_tombstone_unavailable` — The handler verifies bank-transaction and journal-entry absence after deleting an ungrouped, completely unmatched transaction, but keeps no persistent tombstone for later retry attribution.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.bank.statement.line, account.move, account.move.line, account.payment, account.partial.reconcile, account.full.reconcile；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.bank.statement.line:read, account.bank.statement.line:unlink, account.move:read, account.move:unlink, account.move.line:read, account.payment:read, account.partial.reconcile:read, account.full.reconcile:read。
- 请求/响应合同：`schemas/v1/bank.transaction.delete.request.schema.json` / `schemas/v1/bank.transaction.delete.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run bank.transaction.delete --request "@request.json" --idempotency-key "bank.transaction.delete:1" --confirm "bank.transaction.delete"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "transaction_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transaction_id"]} |
| parameters.transaction_id | integer | 必填（所在对象出现时） |  | 银行流水记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"bank.transaction.delete"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"bank.transaction.delete"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_company_scoped_ungrouped_unmatched_bank_transaction_unlink
- `verify`：same_transaction_bank_transaction_and_journal_entry_absence_and_response_schema_validation
- `idempotency`：record_absence_recheck_without_operation_store_or_persistent_tombstone
- `reverse`：not_reversible_deleted_transaction_must_be_recorded_again

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover confirmation, runtime result contract, CLI dispatch, registry descriptor, delete boundary, and schemas.；引用：tests/unit/test_bank_statement_payment_maintenance_public.py, tests/unit/test_bank_statement_payment_maintenance_runtime.py, tests/unit/test_core_writes.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases through the public CLI as uid 5 with su=False, exercising all six bank/payment-maintenance commands, three immediate replays, native statement/payment readbacks, and fresh-cursor rollback verification.；引用：tests/integration/test_bank_statement_payment_maintenance_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-bank-transaction-get"></a>

## bank.transaction.get — 获取银行流水详情

- 类型：只读；静态状态：`unconfigured`；handler：`bank_transaction_get`。
- 状态原因：`runtime_context_required` — Returns account_number and partner_name as independently optional nullable metadata; old result shapes remain accepted and list/search shapes are unchanged.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.bank.statement.line, account.bank.statement, account.move, account.journal, res.partner, res.currency, account.payment；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.bank.statement.line:read, account.bank.statement:read, account.move:read, account.journal:read, res.partner:read, res.currency:read, account.payment:read。
- 请求/响应合同：`schemas/v1/bank.transaction.get.request.schema.json` / `schemas/v1/bank.transaction.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read bank.transaction.get --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "transaction_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transaction_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.transaction_id | integer | 必填（所在对象出现时） |  | 银行流水记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"bank.transaction.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","date","payment_date","name","reference","partner","journal","amount","currency","move","reconciled","statement_id"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.payment_date | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}]} |
| response.data.payment_date | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.payment_date | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"bank.transaction.list.response.schema.json#/$defs/nullableText"} |
| response.data.name | null | 分支约束 | oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.name | string | 分支约束 | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.reference | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"bank.transaction.list.response.schema.json#/$defs/nullableText"} |
| response.data.reference | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.reference | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.partner | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"bank.transaction.list.response.schema.json#/$defs/partner"}]} |
| response.data.partner | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.partner | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"bank.transaction.list.response.schema.json#/$defs/partner"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"bank.transaction.list.response.schema.json#/$defs/journal"} |
| response.data.journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":5,"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.amount | string | 必填（所在对象出现时） | oneOf[2] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"bank.transaction.list.response.schema.json#/$defs/decimal"} |
| response.data.currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"bank.transaction.list.response.schema.json#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.move | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","state"],"resolved_ref":"bank.transaction.list.response.schema.json#/$defs/move"} |
| response.data.move.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.move.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.move.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.reconciled | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.statement_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.account_number | 组合/开放结构 | 可选（可能有条件限制） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"bank.transaction.list.response.schema.json#/$defs/nullableText"} |
| response.data.account_number | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.account_number | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.partner_name | 组合/开放结构 | 可选（可能有条件限制） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"bank.transaction.list.response.schema.json#/$defs/nullableText"} |
| response.data.partner_name | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.partner_name | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","date","payment_date","name","reference","partner","journal","amount","currency","move","reconciled","statement_id"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.payment_date | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}]} |
| response.data.payment_date | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.payment_date | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date"} |
| response.data.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"bank.transaction.list.response.schema.json#/$defs/nullableText"} |
| response.data.name | null | 分支约束 | allOf[1]/then/oneOf[1] | 名称/行说明 |  |
| response.data.name | string | 分支约束 | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.reference | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"bank.transaction.list.response.schema.json#/$defs/nullableText"} |
| response.data.reference | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.reference | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"bank.transaction.list.response.schema.json#/$defs/partner"}]} |
| response.data.partner | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.partner | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"bank.transaction.list.response.schema.json#/$defs/partner"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"bank.transaction.list.response.schema.json#/$defs/journal"} |
| response.data.journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":5,"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.amount | string | 必填（所在对象出现时） | allOf[1]/then | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"bank.transaction.list.response.schema.json#/$defs/decimal"} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"bank.transaction.list.response.schema.json#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.move | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","state"],"resolved_ref":"bank.transaction.list.response.schema.json#/$defs/move"} |
| response.data.move.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.move.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.move.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.statement_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.account_number | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"bank.transaction.list.response.schema.json#/$defs/nullableText"} |
| response.data.account_number | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.account_number | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.partner_name | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"bank.transaction.list.response.schema.json#/$defs/nullableText"} |
| response.data.partner_name | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.partner_name | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_company_scoped_core_object_read_action
- `verify`：same_transaction_acl_result_cursor_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Closed typed inputs, schema and target binding; compatible legacy branches remain covered.；引用：tests/unit/test_accounting_workflows_batch.py, tests/unit/test_bank_settlement_write_contract.py, tests/unit/test_bank_settlement_inputs_runtime.py, tests/unit/test_bank_settlement_reads.py, tests/unit/test_bank_settlement_inputs_cli.py
- `integration`：`implemented`；Shared native CLI workflow: both isolated aliases passed32.80s as uid5/su=False/company1. Verified sale/purchase reversal plus draft reissue and replay, native foreign-currency line edits, full/partial matching-group leaf undo and shrinking replay, statement-scoped bank pagination and actual payment bank matches, three company account assignments/clearing/readback and product fallback, purchase self-billing sequence. Native configuration roles and independent bank fixtures exist only in the test transaction. Fresh-cursor objects, caller groups, company settings, defaults and currency/rate rollback checks passed. Bank response additions require synchronized SDK/bridge/schema. No business DB, native source/addon, service, external-send or operation-store changes. Prior-paid reissue, cashbasis/exchange undo workflows, all ancestry/currency/localization/lock/hash branches, all setting consumers and concurrent exactly-once are not claimed.；引用：tests/integration/test_accounting_workflows_batch_live.py, tests/integration/test_bank_settlement_inputs_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-bank-transaction-list"></a>

## bank.transaction.list — 列出银行流水

- 类型：只读；静态状态：`unconfigured`；handler：`bank_transaction_list`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.bank.statement.line, account.move, account.journal, res.partner, res.currency, account.payment, account.bank.statement；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.bank.statement.line:read, account.move:read, account.journal:read, res.partner:read, res.currency:read, account.payment:read, account.bank.statement:read。
- 请求/响应合同：`schemas/v1/bank.transaction.list.request.schema.json` / `schemas/v1/bank.transaction.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read bank.transaction.list --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {}
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"bank.transaction.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","date","payment_date","name","reference","partner","journal","amount","currency","move","reconciled","statement_id"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].payment_date | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | Earliest date among Odoo auto-generated payment_ids, or null when none exists. | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}]} |
| response.data.items[].payment_date | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].payment_date | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.items[].name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | The account.bank.statement.line payment_ref label. | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].name | null | 分支约束 | oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].name | string | 分支约束 | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].reference | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | The inherited account.move ref value. | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].reference | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].reference | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.items[].partner | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/partner"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/journal"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":5,"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].amount | string | 必填（所在对象出现时） | oneOf[2] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].move | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","state"],"resolved_ref":"#/$defs/move"} |
| response.data.items[].move.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].move.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].move.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.items[].reconciled | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].statement_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.has_more | boolean | 必填（所在对象出现时） | oneOf[2] | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | oneOf[2] | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2]/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | oneOf[2]/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | oneOf[2]/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | oneOf[2]/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | oneOf[2]/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | oneOf[2]/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","date","payment_date","name","reference","partner","journal","amount","currency","move","reconciled","statement_id"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].payment_date | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | Earliest date among Odoo auto-generated payment_ids, or null when none exists. | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}]} |
| response.data.items[].payment_date | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].payment_date | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date"} |
| response.data.items[].name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | The account.bank.statement.line payment_ref label. | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].name | null | 分支约束 | allOf[1]/then/oneOf[1] | 名称/行说明 |  |
| response.data.items[].name | string | 分支约束 | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].reference | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | The inherited account.move ref value. | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].reference | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].reference | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.items[].partner | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/partner"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/journal"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":5,"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].amount | string | 必填（所在对象出现时） | allOf[1]/then | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].move | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","state"],"resolved_ref":"#/$defs/move"} |
| response.data.items[].move.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].move.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].move.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.items[].reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].statement_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[1]/then | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[1]/then | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | allOf[1]/then/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_company_scoped_bank_transaction_read
- `verify`：date_id_cursor_related_records_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Closed typed inputs, schema and target binding; compatible legacy branches remain covered.；引用：tests/unit/test_accounting_workflows_batch.py
- `integration`：`implemented`；Shared native CLI workflow: both isolated aliases passed32.80s as uid5/su=False/company1. Verified sale/purchase reversal plus draft reissue and replay, native foreign-currency line edits, full/partial matching-group leaf undo and shrinking replay, statement-scoped bank pagination and actual payment bank matches, three company account assignments/clearing/readback and product fallback, purchase self-billing sequence. Native configuration roles and independent bank fixtures exist only in the test transaction. Fresh-cursor objects, caller groups, company settings, defaults and currency/rate rollback checks passed. Bank response additions require synchronized SDK/bridge/schema. No business DB, native source/addon, service, external-send or operation-store changes. Prior-paid reissue, cashbasis/exchange undo workflows, all ancestry/currency/localization/lock/hash branches, all setting consumers and concurrent exactly-once are not claimed.；引用：tests/integration/test_accounting_workflows_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-bank-transaction-match"></a>

## bank.transaction.match — 匹配银行流水

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.account, account.bank.statement.line, account.move, account.move.line, account.partial.reconcile, account.full.reconcile；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.account:read, account.bank.statement.line:read, account.bank.statement.line:write, account.move:read, account.move.line:read, account.move.line:write, account.partial.reconcile:read, account.partial.reconcile:create, account.full.reconcile:read。
- 请求/响应合同：`schemas/v1/bank.transaction.match.request.schema.json` / `schemas/v1/bank.transaction.match.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run bank.transaction.match --request "@request.json" --idempotency-key "bank.transaction.match:1:080a9ed428559ef602668b4c00f114f1" --confirm "bank.transaction.match"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "transaction_id": 1,
    "candidate_line_ids": [
      1
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transaction_id","candidate_line_ids"]} |
| parameters.transaction_id | integer | 必填（所在对象出现时） |  | 银行流水记录ID | {"minimum":1} |
| parameters.candidate_line_ids | array | 必填（所在对象出现时） |  |  | {"maxItems":50,"minItems":1,"uniqueItems":true} |
| parameters.candidate_line_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"bank.transaction.match"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"bank.transaction.match"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_accounting_core_write_action_as_configured_business_user
- `verify`：post_write_same_transaction_reread_and_response_schema_validation
- `idempotency`：requested_reconciliation_state_hash_and_result_replay
- `reverse`：bank.transaction.unmatch

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the bounded candidate IDs, exact confirmation, fixed reconciliation path, replay, and CLI response contract.；引用：tests/unit/test_payment_bank_writes.py, tests/unit/test_payment_bank_writes_runtime.py, tests/unit/test_payment_bank_write_cli.py
- `integration`：`implemented`；The shared live smoke verifies execution and rollback in both dedicated isolated database aliases.；引用：tests/integration/test_payment_bank_capability_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-bank-transaction-match_candidates-list"></a>

## bank.transaction.match_candidates.list — 列出银行流水匹配候选项

- 类型：只读；静态状态：`unconfigured`；handler：`bank_transaction_match_candidates_list`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.bank.statement.line, account.move, account.move.line, account.account, account.journal, res.partner, res.currency, account.reconcile.model；向导：无。
- 必需模块：account, account_accountant；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.bank.statement.line:read, account.move:read, account.move.line:read, account.account:read, account.journal:read, res.partner:read, res.currency:read, account.reconcile.model:read。
- 请求/响应合同：`schemas/v1/bank.transaction.match_candidates.list.request.schema.json` / `schemas/v1/bank.transaction.match_candidates.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read bank.transaction.match_candidates.list --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "transaction_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transaction_id"]} |
| parameters.transaction_id | integer | 必填（所在对象出现时） |  | 银行流水记录ID | {"minimum":1} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"reconciliation.candidates.list.response.schema.json#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"bank.transaction.match_candidates.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"reconciliation.candidates.list.response.schema.json#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"reconciliation.candidates.list.response.schema.json#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","date","invoice_date","date_maturity","state","move","label","account","partner","journal","company_id","company_currency","currency","balance","amount_currency","amount_residual","amount_residual_currency","matching_number","reconciliation_model"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].invoice_date | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| response.data.items[].invoice_date | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].invoice_date | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.items[].date_maturity | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| response.data.items[].date_maturity | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].date_maturity | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted"]} |
| response.data.items[].move | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","ref"],"resolved_ref":"#/$defs/move"} |
| response.data.items[].move.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].move.name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].move.name | null | 分支约束 | oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].move.name | string | 分支约束 | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].move.move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["entry","out_invoice","out_refund","in_invoice","in_refund","out_receipt","in_receipt"]} |
| response.data.items[].move.ref | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].move.ref | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].move.ref | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].label | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].label | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].label | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].account | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name","account_type"],"resolved_ref":"#/$defs/account"} |
| response.data.items[].account.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].account.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":64,"minLength":1,"pattern":"^[A-Za-z0-9.]+$(?![\\s\\S])"} |
| response.data.items[].account.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].account.account_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["asset_receivable","asset_cash","asset_current","asset_non_current","asset_prepayments","asset_fixed","liability_payable","liability_credit_card","liability_current","liability_non_current","equity","equity_unaffected","income","income_other","expense","expense_depreciation","expense_direct_cost","expense_other","off_balance"]} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.items[].partner | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/partner"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].partner.name | null | 分支约束 | oneOf[2]/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].partner.name | string | 分支约束 | oneOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name","type"],"resolved_ref":"#/$defs/journal"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":5,"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].journal.type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["sale","purchase","cash","bank","credit","general"]} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].company_currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].company_currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].balance | string | 必填（所在对象出现时） | oneOf[2] | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/money"} |
| response.data.items[].amount_currency | string | 必填（所在对象出现时） | oneOf[2] | 外币/交易币数值，非默认公司币金额 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/money"} |
| response.data.items[].amount_residual | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:(?:[1-9][0-9]*)(?:\\.[0-9]+)?&#124;0\\.(?=[0-9]*[1-9])[0-9]+)$(?![\\s\\S])","resolved_ref":"#/$defs/nonzeroMoney"} |
| response.data.items[].amount_residual_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/money"} |
| response.data.items[].matching_number | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].matching_number | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].matching_number | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].reconciliation_model | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/historicalReconciliationModel"}]} |
| response.data.items[].reconciliation_model | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].reconciliation_model | object | 分支约束 | oneOf[2]/oneOf[2] | The reconciliation rule that historically created this move line; it is not a recommended matching rule. | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/historicalReconciliationModel"} |
| response.data.items[].reconciliation_model.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].reconciliation_model.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.has_more | boolean | 必填（所在对象出现时） | oneOf[2] | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | oneOf[2] | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"reconciliation.candidates.list.response.schema.json#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"reconciliation.candidates.list.response.schema.json#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","date","invoice_date","date_maturity","state","move","label","account","partner","journal","company_id","company_currency","currency","balance","amount_currency","amount_residual","amount_residual_currency","matching_number","reconciliation_model"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].invoice_date | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| response.data.items[].invoice_date | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].invoice_date | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date"} |
| response.data.items[].date_maturity | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| response.data.items[].date_maturity | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].date_maturity | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date"} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted"]} |
| response.data.items[].move | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","ref"],"resolved_ref":"#/$defs/move"} |
| response.data.items[].move.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].move.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].move.name | null | 分支约束 | allOf[1]/then/oneOf[1] | 名称/行说明 |  |
| response.data.items[].move.name | string | 分支约束 | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].move.move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["entry","out_invoice","out_refund","in_invoice","in_refund","out_receipt","in_receipt"]} |
| response.data.items[].move.ref | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].move.ref | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].move.ref | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].label | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].label | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].label | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].account | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name","account_type"],"resolved_ref":"#/$defs/account"} |
| response.data.items[].account.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].account.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":64,"minLength":1,"pattern":"^[A-Za-z0-9.]+$(?![\\s\\S])"} |
| response.data.items[].account.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].account.account_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["asset_receivable","asset_cash","asset_current","asset_non_current","asset_prepayments","asset_fixed","liability_payable","liability_credit_card","liability_current","liability_non_current","equity","equity_unaffected","income","income_other","expense","expense_depreciation","expense_direct_cost","expense_other","off_balance"]} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.items[].partner | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/partner"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].partner.name | null | 分支约束 | allOf[1]/then/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].partner.name | string | 分支约束 | allOf[1]/then/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name","type"],"resolved_ref":"#/$defs/journal"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":5,"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].journal.type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["sale","purchase","cash","bank","credit","general"]} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].company_currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].company_currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].balance | string | 必填（所在对象出现时） | allOf[1]/then | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/money"} |
| response.data.items[].amount_currency | string | 必填（所在对象出现时） | allOf[1]/then | 外币/交易币数值，非默认公司币金额 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/money"} |
| response.data.items[].amount_residual | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:(?:[1-9][0-9]*)(?:\\.[0-9]+)?&#124;0\\.(?=[0-9]*[1-9])[0-9]+)$(?![\\s\\S])","resolved_ref":"#/$defs/nonzeroMoney"} |
| response.data.items[].amount_residual_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/money"} |
| response.data.items[].matching_number | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].matching_number | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].matching_number | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].reconciliation_model | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/historicalReconciliationModel"}]} |
| response.data.items[].reconciliation_model | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].reconciliation_model | object | 分支约束 | allOf[1]/then/oneOf[2] | The reconciliation rule that historically created this move line; it is not a recommended matching rule. | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/historicalReconciliationModel"} |
| response.data.items[].reconciliation_model.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].reconciliation_model.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[1]/then | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[1]/then | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_bank_transaction_match_candidate_read
- `verify`：same_transaction_acl_residual_cursor_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the transaction-bound candidate search, stable cursor, company scope, ACL gates, response reuse, and CLI dispatch.；引用：tests/unit/test_bank_reconciliation_reads.py, tests/unit/test_payment_bank_write_cli.py
- `integration`：`implemented`；The shared live smoke verifies the capability in both dedicated isolated database aliases with transaction rollback.；引用：tests/integration/test_payment_bank_capability_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-bank-transaction-reconciliation-get"></a>

## bank.transaction.reconciliation.get — 获取银行流水核销详情

- 类型：只读；静态状态：`unconfigured`；handler：`bank_transaction_reconciliation_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.bank.statement.line, account.move, account.move.line, account.account, res.partner, res.currency, account.payment, account.partial.reconcile, account.full.reconcile；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.bank.statement.line:read, account.move:read, account.move.line:read, account.account:read, res.partner:read, res.currency:read, account.payment:read, account.partial.reconcile:read, account.full.reconcile:read。
- 请求/响应合同：`schemas/v1/bank.transaction.reconciliation.get.request.schema.json` / `schemas/v1/bank.transaction.reconciliation.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read bank.transaction.reconciliation.get --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "transaction_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transaction_id"]} |
| parameters.transaction_id | integer | 必填（所在对象出现时） |  | 银行流水记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"bank.transaction.reconciliation.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["transaction","liquidity_line","suspense_line","matched_lines","writeoff_lines","payment_ids"],"resolved_ref":"#/$defs/data"} |
| response.data.transaction | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","move_id","move_state","date","journal_id","partner_id","amount","currency_id","foreign_currency_id","amount_currency","amount_residual","is_reconciled","checked"],"resolved_ref":"#/$defs/transaction"} |
| response.data.transaction.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.transaction.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.transaction.move_id | integer | 必填（所在对象出现时） | oneOf[2] | 会计单据记录ID | {"minimum":1} |
| response.data.transaction.move_state | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["draft","posted","cancel"]} |
| response.data.transaction.date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.transaction.journal_id | integer | 必填（所在对象出现时） | oneOf[2] | 日记账ID | {"minimum":1} |
| response.data.transaction.partner_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 合作伙伴ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| response.data.transaction.amount | string | 必填（所在对象出现时） | oneOf[2] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.transaction.currency_id | integer | 必填（所在对象出现时） | oneOf[2] | 币种ID | {"minimum":1} |
| response.data.transaction.foreign_currency_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| response.data.transaction.amount_currency | string | 必填（所在对象出现时） | oneOf[2] | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.transaction.amount_residual | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.transaction.is_reconciled | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.transaction.checked | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.liquidity_line | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","account_id","partner_id","currency_id","balance","amount_currency","amount_residual","amount_residual_currency"],"resolved_ref":"#/$defs/line"} |
| response.data.liquidity_line.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.liquidity_line.account_id | integer | 必填（所在对象出现时） | oneOf[2] | 会计科目ID | {"minimum":1} |
| response.data.liquidity_line.partner_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 合作伙伴ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| response.data.liquidity_line.currency_id | integer | 必填（所在对象出现时） | oneOf[2] | 币种ID | {"minimum":1} |
| response.data.liquidity_line.balance | string | 必填（所在对象出现时） | oneOf[2] | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.liquidity_line.amount_currency | string | 必填（所在对象出现时） | oneOf[2] | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.liquidity_line.amount_residual | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.liquidity_line.amount_residual_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.suspense_line | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/line"}]} |
| response.data.suspense_line | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.suspense_line | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","account_id","partner_id","currency_id","balance","amount_currency","amount_residual","amount_residual_currency"],"resolved_ref":"#/$defs/line"} |
| response.data.suspense_line.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.suspense_line.account_id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 会计科目ID | {"minimum":1} |
| response.data.suspense_line.partner_id | integer/null | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 合作伙伴ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| response.data.suspense_line.currency_id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 币种ID | {"minimum":1} |
| response.data.suspense_line.balance | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.suspense_line.amount_currency | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.suspense_line.amount_residual | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.suspense_line.amount_residual_currency | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.matched_lines | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.matched_lines[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["bank_move_line_id","source_line_id","source_move_id","account_id","partner_id","currency_id","applied_balance","applied_amount_currency","source_amount_residual","source_amount_residual_currency","full_reconcile_id"],"resolved_ref":"#/$defs/matchedLine"} |
| response.data.matched_lines[].bank_move_line_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.matched_lines[].source_line_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.matched_lines[].source_move_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.matched_lines[].account_id | integer | 必填（所在对象出现时） | oneOf[2] | 会计科目ID | {"minimum":1} |
| response.data.matched_lines[].partner_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 合作伙伴ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| response.data.matched_lines[].currency_id | integer | 必填（所在对象出现时） | oneOf[2] | 币种ID | {"minimum":1} |
| response.data.matched_lines[].applied_balance | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.matched_lines[].applied_amount_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.matched_lines[].source_amount_residual | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.matched_lines[].source_amount_residual_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.matched_lines[].full_reconcile_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 完整核销关系ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| response.data.writeoff_lines | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.writeoff_lines[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","account_id","partner_id","currency_id","balance","amount_currency"],"resolved_ref":"#/$defs/writeoffLine"} |
| response.data.writeoff_lines[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.writeoff_lines[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.writeoff_lines[].account_id | integer | 必填（所在对象出现时） | oneOf[2] | 会计科目ID | {"minimum":1} |
| response.data.writeoff_lines[].partner_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 合作伙伴ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| response.data.writeoff_lines[].currency_id | integer | 必填（所在对象出现时） | oneOf[2] | 币种ID | {"minimum":1} |
| response.data.writeoff_lines[].balance | string | 必填（所在对象出现时） | oneOf[2] | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.writeoff_lines[].amount_currency | string | 必填（所在对象出现时） | oneOf[2] | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.payment_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.payment_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["transaction","liquidity_line","suspense_line","matched_lines","writeoff_lines","payment_ids"],"resolved_ref":"#/$defs/data"} |
| response.data.transaction | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","move_id","move_state","date","journal_id","partner_id","amount","currency_id","foreign_currency_id","amount_currency","amount_residual","is_reconciled","checked"],"resolved_ref":"#/$defs/transaction"} |
| response.data.transaction.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.transaction.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.transaction.move_id | integer | 必填（所在对象出现时） | allOf[1]/then | 会计单据记录ID | {"minimum":1} |
| response.data.transaction.move_state | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["draft","posted","cancel"]} |
| response.data.transaction.date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.transaction.journal_id | integer | 必填（所在对象出现时） | allOf[1]/then | 日记账ID | {"minimum":1} |
| response.data.transaction.partner_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 合作伙伴ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| response.data.transaction.amount | string | 必填（所在对象出现时） | allOf[1]/then | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.transaction.currency_id | integer | 必填（所在对象出现时） | allOf[1]/then | 币种ID | {"minimum":1} |
| response.data.transaction.foreign_currency_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| response.data.transaction.amount_currency | string | 必填（所在对象出现时） | allOf[1]/then | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.transaction.amount_residual | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.transaction.is_reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.transaction.checked | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.liquidity_line | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","account_id","partner_id","currency_id","balance","amount_currency","amount_residual","amount_residual_currency"],"resolved_ref":"#/$defs/line"} |
| response.data.liquidity_line.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.liquidity_line.account_id | integer | 必填（所在对象出现时） | allOf[1]/then | 会计科目ID | {"minimum":1} |
| response.data.liquidity_line.partner_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 合作伙伴ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| response.data.liquidity_line.currency_id | integer | 必填（所在对象出现时） | allOf[1]/then | 币种ID | {"minimum":1} |
| response.data.liquidity_line.balance | string | 必填（所在对象出现时） | allOf[1]/then | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.liquidity_line.amount_currency | string | 必填（所在对象出现时） | allOf[1]/then | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.liquidity_line.amount_residual | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.liquidity_line.amount_residual_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.suspense_line | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/line"}]} |
| response.data.suspense_line | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.suspense_line | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","account_id","partner_id","currency_id","balance","amount_currency","amount_residual","amount_residual_currency"],"resolved_ref":"#/$defs/line"} |
| response.data.suspense_line.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.suspense_line.account_id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 会计科目ID | {"minimum":1} |
| response.data.suspense_line.partner_id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 合作伙伴ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| response.data.suspense_line.currency_id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 币种ID | {"minimum":1} |
| response.data.suspense_line.balance | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.suspense_line.amount_currency | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.suspense_line.amount_residual | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.suspense_line.amount_residual_currency | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.matched_lines | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.matched_lines[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["bank_move_line_id","source_line_id","source_move_id","account_id","partner_id","currency_id","applied_balance","applied_amount_currency","source_amount_residual","source_amount_residual_currency","full_reconcile_id"],"resolved_ref":"#/$defs/matchedLine"} |
| response.data.matched_lines[].bank_move_line_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.matched_lines[].source_line_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.matched_lines[].source_move_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.matched_lines[].account_id | integer | 必填（所在对象出现时） | allOf[1]/then | 会计科目ID | {"minimum":1} |
| response.data.matched_lines[].partner_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 合作伙伴ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| response.data.matched_lines[].currency_id | integer | 必填（所在对象出现时） | allOf[1]/then | 币种ID | {"minimum":1} |
| response.data.matched_lines[].applied_balance | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.matched_lines[].applied_amount_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.matched_lines[].source_amount_residual | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.matched_lines[].source_amount_residual_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.matched_lines[].full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 完整核销关系ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| response.data.writeoff_lines | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.writeoff_lines[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","account_id","partner_id","currency_id","balance","amount_currency"],"resolved_ref":"#/$defs/writeoffLine"} |
| response.data.writeoff_lines[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.writeoff_lines[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.writeoff_lines[].account_id | integer | 必填（所在对象出现时） | allOf[1]/then | 会计科目ID | {"minimum":1} |
| response.data.writeoff_lines[].partner_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 合作伙伴ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| response.data.writeoff_lines[].currency_id | integer | 必填（所在对象出现时） | allOf[1]/then | 币种ID | {"minimum":1} |
| response.data.writeoff_lines[].balance | string | 必填（所在对象出现时） | allOf[1]/then | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.writeoff_lines[].amount_currency | string | 必填（所在对象出现时） | allOf[1]/then | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.payment_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.payment_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_bank_transaction_reconciliation_read
- `verify`：same_transaction_acl_reconciliation_graph_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request and response, fixed reconciliation graph traversal, company scope, ACL gates, normalization, and CLI dispatch.；引用：tests/unit/test_bank_reconciliation_reads.py, tests/unit/test_payment_bank_write_cli.py
- `integration`：`implemented`；The shared live smoke verifies the capability in both dedicated isolated database aliases with transaction rollback.；引用：tests/integration/test_payment_bank_capability_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-bank-transaction-record"></a>

## bank.transaction.record — 记录银行流水

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Optional account_number and partner_name preserve bank import identity; native creation may retrieve a partner. Omitted inputs retain old keys and defaults.
- 内部domain：`bank_reconciliation`；来源模型：account.bank.statement.line, account.journal, account.move, account.move.line, res.company, res.currency, res.currency.rate, res.partner；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.bank.statement.line:create, account.bank.statement.line:read, account.journal:read, account.move.line:create, account.move.line:read, account.move.line:write, account.move:create, account.move:read, account.move:write, res.currency.rate:read, res.currency:read, res.partner:read。
- 请求/响应合同：`schemas/v1/bank.transaction.record.request.schema.json` / `schemas/v1/bank.transaction.record.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run bank.transaction.record --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "bank.transaction.record"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "journal_id": 1,
    "date": "2026-10-31",
    "amount": "1",
    "payment_ref": "Example",
    "partner_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  |  |
| parameters | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"amount_currency":{"maxLength":256,"pattern":"^-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?)$(?![\\s\\S])","type":"string"}}},"if":{"properties":{"foreign_currency_id":{"type":"null"}},"required":["foreign_currency_id"]},"then":{"properties":{"amount_currency":{"const":"0"}}}}],"dependentRequired":{"amount_currency":["foreign_currency_id"],"foreign_currency_id":["amount_currency"]},"required_in_object":["journal_id","date","amount","payment_ref","partner_id"]} |
| parameters.foreign_currency_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.amount_currency | string | 可选（可能有条件限制） |  | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| parameters.account_number | string/null | 可选（可能有条件限制） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |
| parameters.partner_name | string/null | 可选（可能有条件限制） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |
| parameters.journal_id | integer | 必填（所在对象出现时） |  | 日记账ID | {"minimum":1} |
| parameters.date | string | 必填（所在对象出现时） |  |  | {"format":"date"} |
| parameters.amount | string | 必填（所在对象出现时） |  | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^-?(?:(?:[1-9][0-9]*)(?:\\.[0-9]+)?&#124;0\\.(?=[0-9]*[1-9])[0-9]+)$(?![\\s\\S])"} |
| parameters.payment_ref | string | 必填（所在对象出现时） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$"} |
| parameters.partner_id | 组合/开放结构 | 必填（所在对象出现时） |  | 合作伙伴ID | {"oneOf":[{"type":"null"},{"minimum":1,"type":"integer"}]} |
| parameters.partner_id | null | 分支约束 | oneOf[1] | 合作伙伴ID |  |
| parameters.partner_id | integer | 分支约束 | oneOf[2] | 合作伙伴ID | {"minimum":1} |
| parameters | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"amount_currency":{"maxLength":256,"pattern":"^-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?)$(?![\\s\\S])","type":"string"}}},"if":{"properties":{"foreign_currency_id":{"type":"null"}},"required":["foreign_currency_id"]},"then":{"properties":{"amount_currency":{"const":"0"}}}} |
| parameters | 未限定 | 条件分支 | allOf[1]/then |  |  |
| parameters.amount_currency | 未限定 | 可选（可能有条件限制） | allOf[1]/then | 外币/交易币数值，非默认公司币金额 | {"const":"0"} |
| parameters | 未限定 | 条件分支 | allOf[1]/else |  |  |
| parameters.amount_currency | string | 可选（可能有条件限制） | allOf[1]/else | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?)$(?![\\s\\S])"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"bank.transaction.record"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"bank.transaction.record"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：native_bank_line_create_or_default_unmatched_write_with_optional_paired_foreign_amount
- `verify`：native_bank_line_amount_currency_pair_reread_and_balanced_posted_entry
- `idempotency`：legacy_omitted_pair_key_unchanged_or_closed_explicit_foreign_target_state_recheck
- `reverse`：reconciliation.undo_then_record_correcting_transaction

### 已登记测试与证据范围

- `unit`：`implemented`；Focused closed-input, legacy omission/key, company/state/ACL and result binding tests; execution is required before acceptance.；引用：tests/unit/test_accounting_maintenance_batch.py, tests/unit/test_bank_settlement_write_contract.py, tests/unit/test_bank_settlement_inputs_runtime.py, tests/unit/test_bank_settlement_reads.py, tests/unit/test_bank_settlement_inputs_cli.py
- `integration`：`implemented`；One shared public CLI/native ORM workflow passed both isolated aliases in 24.70s as uid5/su=False/company1. Two new IDs and six extensions: exact-current-root currency-rate correction/date/replay, native technical Float readback, conversion/delete fallback and missing denial; explicit foreign-bank positive/negative paired amount set/clear/replay while legacy omitted shapes remain unchanged; reconciled statement membership/detach retaining native lines, posted moves, financial snapshots and matching graphs; posted unsent invoice bank set/clear with native PDF-link sent denial; posted preferred-method wizard default and Incoterm/location set/clear; a real partially reconciled invoice retaining raw matching IDs/amounts and financial lines. Native configuration roles exist only inside the isolated transaction, never sudo business calls. Fresh tracked fixtures, both companies settings, all defaults, currencies/rates and exact caller/native group memberships roll back. Live companies are independent roots; branch context rejection has unit evidence only. PDF uses synthetic DB-only raw bytes and native linking, not generation or delivery. Wizard defaults do not make payments. All hierarchy/currency/precision/localization/hash/lock paths, fully-paid/CABA invoices, existing foreign-invoice revaluation and concurrent exactly-once are not claimed. Legacy currency.rate.record guard is unchanged. No business DB, native source/addon, configuration, service or external-send changes.；引用：tests/integration/test_accounting_maintenance_batch_live.py, tests/integration/test_bank_settlement_inputs_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-bank-transaction-search"></a>

## bank.transaction.search — 搜索银行流水

- 类型：只读；静态状态：`unconfigured`；handler：`bank_transaction_search`。
- 状态原因：`runtime_context_required` — Optional statement_assignment assigned/unassigned filters the native statement relation before paging; unassigned plus a positive statement_id is rejected.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.bank.statement.line, account.move, account.journal, res.partner, res.currency, account.payment, account.bank.statement；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.bank.statement.line:read, account.move:read, account.journal:read, res.partner:read, res.currency:read, account.payment:read, account.bank.statement:read。
- 请求/响应合同：`schemas/v1/bank.transaction.search.request.schema.json` / `schemas/v1/bank.transaction.search.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read bank.transaction.search --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {}
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"if":{"properties":{"statement_assignment":{"const":"unassigned"}},"required":["statement_assignment"]},"then":{"properties":{"statement_id":{"type":"null"}}}}]} |
| parameters.date_from | string/null | 可选（可能有条件限制） |  | 开始日期 | {"default":null,"format":"date"} |
| parameters.date_to | string/null | 可选（可能有条件限制） |  | 结束日期 | {"default":null,"format":"date"} |
| parameters.journal_id | integer/null | 可选（可能有条件限制） |  | 日记账ID | {"default":null,"minimum":1} |
| parameters.partner_id | integer/null | 可选（可能有条件限制） |  | 合作伙伴ID | {"default":null,"minimum":1} |
| parameters.statement_id | integer/null | 可选（可能有条件限制） |  |  | {"default":null,"minimum":1} |
| parameters.statement_assignment | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["assigned","unassigned"]} |
| parameters.reconciled | boolean/null | 可选（可能有条件限制） |  |  | {"default":null} |
| parameters.query | 组合/开放结构 | 可选（可能有条件限制） |  | 搜索文本 | {"default":null,"oneOf":[{"type":"null"},{"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","type":"string"}]} |
| parameters.query | null | 分支约束 | oneOf[1] | 搜索文本 |  |
| parameters.query | string | 分支约束 | oneOf[2] | 搜索文本 | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |
| parameters | 组合/开放结构 | 分支约束 | allOf[1] |  | {"if":{"properties":{"statement_assignment":{"const":"unassigned"}},"required":["statement_assignment"]},"then":{"properties":{"statement_id":{"type":"null"}}}} |
| parameters | 未限定 | 条件分支 | allOf[1]/then |  |  |
| parameters.statement_id | null | 可选（可能有条件限制） | allOf[1]/then |  |  |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"bank.transaction.list.response.schema.json#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"bank.transaction.search"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"bank.transaction.list.response.schema.json#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"bank.transaction.list.response.schema.json#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","date","payment_date","name","reference","partner","journal","amount","currency","move","reconciled","statement_id"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].payment_date | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | Earliest date among Odoo auto-generated payment_ids, or null when none exists. | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}]} |
| response.data.items[].payment_date | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].payment_date | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.items[].name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | The account.bank.statement.line payment_ref label. | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].name | null | 分支约束 | oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].name | string | 分支约束 | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].reference | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | The inherited account.move ref value. | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].reference | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].reference | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.items[].partner | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/partner"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/journal"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":5,"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].amount | string | 必填（所在对象出现时） | oneOf[2] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].move | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","state"],"resolved_ref":"#/$defs/move"} |
| response.data.items[].move.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].move.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].move.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.items[].reconciled | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].statement_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.has_more | boolean | 必填（所在对象出现时） | oneOf[2] | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | oneOf[2] | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2]/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | oneOf[2]/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | oneOf[2]/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | oneOf[2]/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | oneOf[2]/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | oneOf[2]/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"bank.transaction.list.response.schema.json#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"bank.transaction.list.response.schema.json#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","date","payment_date","name","reference","partner","journal","amount","currency","move","reconciled","statement_id"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].payment_date | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | Earliest date among Odoo auto-generated payment_ids, or null when none exists. | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}]} |
| response.data.items[].payment_date | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].payment_date | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date"} |
| response.data.items[].name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | The account.bank.statement.line payment_ref label. | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].name | null | 分支约束 | allOf[1]/then/oneOf[1] | 名称/行说明 |  |
| response.data.items[].name | string | 分支约束 | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].reference | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | The inherited account.move ref value. | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].reference | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].reference | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.items[].partner | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/partner"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/journal"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":5,"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].amount | string | 必填（所在对象出现时） | allOf[1]/then | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].move | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","state"],"resolved_ref":"#/$defs/move"} |
| response.data.items[].move.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].move.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].move.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.items[].reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].statement_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[1]/then | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[1]/then | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | allOf[1]/then/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_company_scoped_bank_transaction_search
- `verify`：same_transaction_acl_filters_cursor_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Closed typed inputs, schema and target binding; compatible legacy branches remain covered.；引用：tests/unit/test_accounting_workflows_batch.py, tests/unit/test_bank_settlement_write_contract.py, tests/unit/test_bank_settlement_inputs_runtime.py, tests/unit/test_bank_settlement_reads.py, tests/unit/test_bank_settlement_inputs_cli.py
- `integration`：`implemented`；Shared native CLI workflow: both isolated aliases passed32.80s as uid5/su=False/company1. Verified sale/purchase reversal plus draft reissue and replay, native foreign-currency line edits, full/partial matching-group leaf undo and shrinking replay, statement-scoped bank pagination and actual payment bank matches, three company account assignments/clearing/readback and product fallback, purchase self-billing sequence. Native configuration roles and independent bank fixtures exist only in the test transaction. Fresh-cursor objects, caller groups, company settings, defaults and currency/rate rollback checks passed. Bank response additions require synchronized SDK/bridge/schema. No business DB, native source/addon, service, external-send or operation-store changes. Prior-paid reissue, cashbasis/exchange undo workflows, all ancestry/currency/localization/lock/hash branches, all setting consumers and concurrent exactly-once are not claimed.；引用：tests/integration/test_accounting_workflows_batch_live.py, tests/integration/test_bank_settlement_inputs_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-bank-transaction-unmatch"></a>

## bank.transaction.unmatch — 撤销银行流水匹配

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Native undo also restores isolated manual P&L counterparts; default unmatched state replays and existing external match behavior remains unchanged.
- 内部domain：`bank_reconciliation`；来源模型：account.account, account.bank.statement.line, account.full.reconcile, account.move, account.move.line, account.partial.reconcile, account.payment, res.company；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.account:read, account.bank.statement.line:read, account.bank.statement.line:write, account.full.reconcile:read, account.full.reconcile:unlink, account.move.line:create, account.move.line:read, account.move.line:unlink, account.move.line:write, account.move:read, account.move:write, account.partial.reconcile:read, account.partial.reconcile:unlink, account.payment:read, account.payment:unlink。
- 请求/响应合同：`schemas/v1/bank.transaction.unmatch.request.schema.json` / `schemas/v1/bank.transaction.unmatch.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run bank.transaction.unmatch --request "@request.json" --idempotency-key "bank.transaction.unmatch:1" --confirm "bank.transaction.unmatch"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "transaction_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transaction_id"]} |
| parameters.transaction_id | integer | 必填（所在对象出现时） |  | 银行流水记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"bank.transaction.unmatch"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"bank.transaction.unmatch"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_accounting_core_write_action_as_configured_business_user
- `verify`：post_write_same_transaction_reread_and_response_schema_validation
- `idempotency`：native_unmatched_state_and_result_replay
- `reverse`：bank.transaction.match

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request, exact confirmation, fixed native unmatch path, replay, and CLI response contract.；引用：tests/unit/test_payment_bank_writes.py, tests/unit/test_payment_bank_writes_runtime.py, tests/unit/test_payment_bank_write_cli.py, tests/unit/test_bank_settlement_write_contract.py, tests/unit/test_bank_settlement_inputs_runtime.py, tests/unit/test_bank_settlement_reads.py, tests/unit/test_bank_settlement_inputs_cli.py
- `integration`：`implemented`；The shared live smoke verifies execution and rollback in both dedicated isolated database aliases.；引用：tests/integration/test_payment_bank_capability_batch_live.py, tests/integration/test_bank_settlement_inputs_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-bank-transaction-update"></a>

## bank.transaction.update — 更新银行流水

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Optional account_number and partner_name set/clear exact metadata on a default unmatched transaction; matched payment_ref changes remain rejected because native sync resets counterparts.
- 内部domain：`bank_reconciliation`；来源模型：account.bank.statement.line, account.move, account.move.line, res.company, res.currency, res.currency.rate, res.partner；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.bank.statement.line:read, account.bank.statement.line:write, account.move.line:read, account.move.line:write, account.move:read, account.move:write, res.currency.rate:read, res.currency:read, res.partner:read。
- 请求/响应合同：`schemas/v1/bank.transaction.update.request.schema.json` / `schemas/v1/bank.transaction.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run bank.transaction.update --request "@request.json" --idempotency-key "bank.transaction.update:1:41b9144b6f674c03024f8fa0f6815ec4" --confirm "bank.transaction.update"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "transaction_id": 1,
    "changes": {
      "foreign_currency_id": 1,
      "amount_currency": "1"
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transaction_id","changes"]} |
| parameters.transaction_id | integer | 必填（所在对象出现时） |  | 银行流水记录ID | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"allOf":[{"else":{"properties":{"amount_currency":{"maxLength":256,"pattern":"^-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?)$(?![\\s\\S])","type":"string"}}},"if":{"properties":{"foreign_currency_id":{"type":"null"}},"required":["foreign_currency_id"]},"then":{"properties":{"amount_currency":{"const":"0"}}}}],"dependentRequired":{"amount_currency":["foreign_currency_id"],"foreign_currency_id":["amount_currency"]},"minProperties":1} |
| parameters.changes.foreign_currency_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.changes.amount_currency | string | 可选（可能有条件限制） |  | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| parameters.changes.account_number | string/null | 可选（可能有条件限制） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |
| parameters.changes.partner_name | string/null | 可选（可能有条件限制） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |
| parameters.changes.date | string | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.changes.amount | string | 可选（可能有条件限制） |  | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^-?(?:(?:[1-9][0-9]*)(?:\\.[0-9]+)?&#124;0\\.(?=[0-9]*[1-9])[0-9]+)$(?![\\s\\S])"} |
| parameters.changes.payment_ref | string | 可选（可能有条件限制） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |
| parameters.changes.partner_id | integer/null | 可选（可能有条件限制） |  | 合作伙伴ID | {"minimum":1} |
| parameters.changes | 组合/开放结构 | 分支约束 | allOf[1] | 仅提交拟变更字段，非整条记录 | {"else":{"properties":{"amount_currency":{"maxLength":256,"pattern":"^-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?)$(?![\\s\\S])","type":"string"}}},"if":{"properties":{"foreign_currency_id":{"type":"null"}},"required":["foreign_currency_id"]},"then":{"properties":{"amount_currency":{"const":"0"}}}} |
| parameters.changes | 未限定 | 条件分支 | allOf[1]/then | 仅提交拟变更字段，非整条记录 |  |
| parameters.changes.amount_currency | 未限定 | 可选（可能有条件限制） | allOf[1]/then | 外币/交易币数值，非默认公司币金额 | {"const":"0"} |
| parameters.changes | 未限定 | 条件分支 | allOf[1]/else | 仅提交拟变更字段，非整条记录 |  |
| parameters.changes.amount_currency | string | 可选（可能有条件限制） | allOf[1]/else | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?)$(?![\\s\\S])"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"bank.transaction.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"bank.transaction.update"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：native_bank_line_create_or_default_unmatched_write_with_optional_paired_foreign_amount
- `verify`：native_bank_line_amount_currency_pair_reread_and_balanced_posted_entry
- `idempotency`：legacy_omitted_pair_key_unchanged_or_closed_explicit_foreign_target_state_recheck
- `reverse`：bank.transaction.update_with_prior_values

### 已登记测试与证据范围

- `unit`：`implemented`；Focused closed-input, legacy omission/key, company/state/ACL and result binding tests; execution is required before acceptance.；引用：tests/unit/test_accounting_maintenance_batch.py, tests/unit/test_bank_settlement_write_contract.py, tests/unit/test_bank_settlement_inputs_runtime.py, tests/unit/test_bank_settlement_reads.py, tests/unit/test_bank_settlement_inputs_cli.py
- `integration`：`implemented`；One shared public CLI/native ORM workflow passed both isolated aliases in 24.70s as uid5/su=False/company1. Two new IDs and six extensions: exact-current-root currency-rate correction/date/replay, native technical Float readback, conversion/delete fallback and missing denial; explicit foreign-bank positive/negative paired amount set/clear/replay while legacy omitted shapes remain unchanged; reconciled statement membership/detach retaining native lines, posted moves, financial snapshots and matching graphs; posted unsent invoice bank set/clear with native PDF-link sent denial; posted preferred-method wizard default and Incoterm/location set/clear; a real partially reconciled invoice retaining raw matching IDs/amounts and financial lines. Native configuration roles exist only inside the isolated transaction, never sudo business calls. Fresh tracked fixtures, both companies settings, all defaults, currencies/rates and exact caller/native group memberships roll back. Live companies are independent roots; branch context rejection has unit evidence only. PDF uses synthetic DB-only raw bytes and native linking, not generation or delivery. Wizard defaults do not make payments. All hierarchy/currency/precision/localization/hash/lock paths, fully-paid/CABA invoices, existing foreign-invoice revaluation and concurrent exactly-once are not claimed. Legacy currency.rate.record guard is unchanged. No business DB, native source/addon, configuration, service or external-send changes.；引用：tests/integration/test_accounting_maintenance_batch_live.py, tests/integration/test_bank_settlement_inputs_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-company-bank_defaults-assign"></a>

## company.bank_defaults.assign — 设置公司银行默认科目

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Fixed current-company settings are implemented; native company write requires access-rights administration and reference ACLs. Ordinary accountant permission is not implied.
- 内部domain：`accounting_configuration`；来源模型：account.account, ir.default, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：base.group_erp_manager；ACL：account.account:read, ir.default:read, res.company:read, res.company:write。
- 请求/响应合同：`schemas/v1/company.bank_defaults.assign.request.schema.json` / `schemas/v1/company.bank_defaults.assign.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run company.bank_defaults.assign --request "@request.json" --idempotency-key "company.bank_defaults.assign:1:7e6361cfc026a53b7f8875cadbae63cc" --confirm "company.bank_defaults.assign"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "changes": {
      "account_journal_suspense_account_id": 1
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["changes"]} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.account_journal_suspense_account_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.changes.transfer_account_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"company.bank_defaults.assign"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"company.bank_defaults.assign"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：native_res_company_write_with_fixed_operation_fields_as_business_user
- `verify`：same_transaction_native_current_company_setting_readback
- `idempotency`：serial_current_target_setting_recheck_without_operation_store_or_concurrent_exactly_once
- `reverse`：restore_prior_settings_subject_to_native_constraints

### 已登记测试与证据范围

- `unit`：`implemented`；Closed typed inputs, schema and target binding; compatible legacy branches remain covered.；引用：tests/unit/test_accounting_workflows_batch.py
- `integration`：`implemented`；Shared native CLI workflow: both isolated aliases passed32.80s as uid5/su=False/company1. Verified sale/purchase reversal plus draft reissue and replay, native foreign-currency line edits, full/partial matching-group leaf undo and shrinking replay, statement-scoped bank pagination and actual payment bank matches, three company account assignments/clearing/readback and product fallback, purchase self-billing sequence. Native configuration roles and independent bank fixtures exist only in the test transaction. Fresh-cursor objects, caller groups, company settings, defaults and currency/rate rollback checks passed. Bank response additions require synchronized SDK/bridge/schema. No business DB, native source/addon, service, external-send or operation-store changes. Prior-paid reissue, cashbasis/exchange undo workflows, all ancestry/currency/localization/lock/hash branches, all setting consumers and concurrent exactly-once are not claimed.；引用：tests/integration/test_accounting_workflows_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal-bank_account-assign"></a>

## journal.bank_account.assign — 绑定公司银行账户

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires an explicit isolated runtime/company/user configuration.
- 内部domain：`accounting_configuration`；来源模型：account.journal, res.company, res.partner.bank；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.journal:read, account.journal:write, res.partner.bank:read。
- 请求/响应合同：`schemas/v1/journal.bank_account.assign.request.schema.json` / `schemas/v1/journal.bank_account.assign.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run journal.bank_account.assign --request "@request.json" --idempotency-key "journal.bank_account.assign:1:100cedca3ddab7706d647cf11fb03f18" --confirm "journal.bank_account.assign"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "journal_id": 1,
    "partner_bank_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["journal_id","partner_bank_id"]} |
| parameters.journal_id | integer | 必填（所在对象出现时） |  | 日记账ID | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.partner_bank_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"journal.bank_account.assign"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"journal.bank_account.assign"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_company_scoped_native_payment_configuration
- `verify`：same_transaction_native_payload_or_detach_absence_recheck
- `idempotency`：native_current_payload_recheck
- `reverse`：restore_previous_configuration

### 已登记测试与证据范围

- `unit`：`implemented`；Shared batch contract, schema, public CLI, native copy/remove semantics and ACL tests.；引用：tests/unit/test_payment_configuration_batch.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases through the public CLI as uid 5 with su=False: all eight capabilities, five immediate replays, native account reconcile enablement, copy=False account preservation, unused-line deletion, used-line detachment retaining posted payment history, company isolation, and fresh-cursor business-data and temporary-group rollback verification.；引用：tests/integration/test_payment_configuration_batch_live.py
- `golden`：`planned`；Golden examples follow capability coverage.；引用：无
- `e2e`：`planned`；Natural-language routing follows capability coverage.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal-liquidity_configuration-update"></a>

## journal.liquidity_configuration.update — 配置日记账流动性科目

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires an explicit isolated runtime/company/user configuration.
- 内部domain：`accounting_configuration`；来源模型：account.account, account.journal, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.account:read, account.journal:read, account.journal:write。
- 请求/响应合同：`schemas/v1/journal.liquidity_configuration.update.request.schema.json` / `schemas/v1/journal.liquidity_configuration.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run journal.liquidity_configuration.update --request "@request.json" --idempotency-key "journal.liquidity_configuration.update:1:d4380d3476bf96e343a92733108df375" --confirm "journal.liquidity_configuration.update"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "changes": {
      "loss_account_id": 1
    },
    "journal_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["changes","journal_id"]} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.loss_account_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.changes.profit_account_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.changes.suspense_account_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.journal_id | integer | 必填（所在对象出现时） |  | 日记账ID | {"minimum":1,"resolved_ref":"#/$defs/id"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"journal.liquidity_configuration.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"journal.liquidity_configuration.update"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_company_scoped_native_payment_configuration
- `verify`：same_transaction_native_payload_or_detach_absence_recheck
- `idempotency`：native_current_payload_recheck
- `reverse`：restore_previous_configuration

### 已登记测试与证据范围

- `unit`：`implemented`；Shared batch contract, schema, public CLI, native copy/remove semantics and ACL tests.；引用：tests/unit/test_payment_configuration_batch.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases through the public CLI as uid 5 with su=False: all eight capabilities, five immediate replays, native account reconcile enablement, copy=False account preservation, unused-line deletion, used-line detachment retaining posted payment history, company isolation, and fresh-cursor business-data and temporary-group rollback verification.；引用：tests/integration/test_payment_configuration_batch_live.py
- `golden`：`planned`；Golden examples follow capability coverage.；引用：无
- `e2e`：`planned`；Natural-language routing follows capability coverage.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_item-reconciliation-inspect"></a>

## journal_item.reconciliation.inspect — 查看指定分录行核销关系

- 类型：只读；静态状态：`unconfigured`；handler：`journal_item_reconciliation_inspect`。
- 状态原因：`runtime_context_required` — Fixed line-targeted operations are implemented; native accounting, reference and analytic synchronization ACLs apply. Runtime context and native acceptance are not an unrestricted permission claim.
- 内部domain：`journal_item`；来源模型：res.company, account.move.line, account.move, account.partial.reconcile, account.full.reconcile, res.currency；向导：无。
- 必需模块：account, analytic, product, uom；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move.line:read, account.move:read, account.partial.reconcile:read, account.full.reconcile:read, res.currency:read。
- 请求/响应合同：`schemas/v1/journal_item.reconciliation.inspect.request.schema.json` / `schemas/v1/journal_item.reconciliation.inspect.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read journal_item.reconciliation.inspect --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "journal_item_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["journal_item_id"]} |
| parameters.journal_item_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal_item.reconciliation.inspect"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","move_id","company_id","currency_id","company_currency_id","amount_residual","amount_residual_currency","partial_reconcile_ids","reconciled_journal_item_ids","reconciled","matching_number","full_reconcile_id"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.move_id | integer | 必填（所在对象出现时） | oneOf[2] | 会计单据记录ID | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.currency_id | integer | 必填（所在对象出现时） | oneOf[2] | 币种ID | {"minimum":1} |
| response.data.company_currency_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.amount_residual | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.amount_residual_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.partial_reconcile_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.partial_reconcile_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.reconciled_journal_item_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.reconciled_journal_item_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.reconciled | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.matching_number | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.full_reconcile_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","move_id","company_id","currency_id","company_currency_id","amount_residual","amount_residual_currency","partial_reconcile_ids","reconciled_journal_item_ids","reconciled","matching_number","full_reconcile_id"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.move_id | integer | 必填（所在对象出现时） | allOf[1]/then | 会计单据记录ID | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.currency_id | integer | 必填（所在对象出现时） | allOf[1]/then | 币种ID | {"minimum":1} |
| response.data.company_currency_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.amount_residual | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.amount_residual_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.reconciled_journal_item_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.reconciled_journal_item_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.matching_number | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 完整核销关系ID | {"minimum":1} |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：request_schema_validation
- `execute`：fixed_company_line_target_read_as_business_user
- `verify`：typed_target_binding_and_native_keyset_cursor
- `idempotency`：read_only
- `reverse`：not_applicable

### 已登记测试与证据范围

- `unit`：`implemented`；Closed typed parameters, bound parent/line results, shared CLI/schemas/confirmation/keys and target-bound pagination; native behavior is covered separately.；引用：tests/unit/test_journal_item_processing_batch.py
- `integration`：`implemented`；One shared public CLI/real-ORM workflow passed both isolated aliases in21.41s as uid5/su=False/company1: bound line reads, target analytic keyset pages and actual partial/full reconciliation; native atomic draft entry updates preserve IDs and reject imbalance; posted maturity/full analytic replacement/clearing preserve financial fields and replay avoids child recreation; draft product UOM reprices/retaxes natively and purchase deductibility50/0/100 synchronizes native rows. Temporary analytic permission and an admin-created purchase-journal default-account fixture are transaction-local; missing/foreign parent and parent-line mismatch, posted financial writes and draft sales partial-deductibility are rejected. All objects/journal/mail alias and exact groups roll back in fresh cursors. First numeric-conversion and second analytic-sign failures retained, not acceptance; no concurrent exactly-once, receipt, business DB or real external-send claim.；引用：tests/integration/test_journal_item_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-apply"></a>

## reconciliation.apply — 执行部分或完全核销

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.account, account.move.line, account.partial.reconcile, account.full.reconcile, account.move, res.partner；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.account:read, account.move.line:read, account.move.line:write, account.partial.reconcile:read, account.partial.reconcile:create, account.full.reconcile:read, account.move:read, account.move:write, res.partner:read。
- 请求/响应合同：`schemas/v1/reconciliation.apply.request.schema.json` / `schemas/v1/reconciliation.apply.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run reconciliation.apply --request "@request.json" --idempotency-key "reconciliation.apply:1:2" --confirm "reconciliation.apply"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "line_ids": [
      1,
      2
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | 组合/开放结构 | 必填 |  |  | {"oneOf":[{"additionalProperties":false,"properties":{"line_ids":{"items":{"minimum":1,"type":"integer"},"maxItems":2,"minItems":2,"type":"array","uniqueItems":true}},"required":["line_ids"],"type":"object"},{"additionalProperties":false,"properties":{"invoice_id":{"minimum":1,"type":"integer"},"outstanding_line_id":{"minimum":1,"type":"integer"}},"required":["invoice_id","outstanding_line_id"],"type":"object"}]} |
| parameters | object | 分支约束 | oneOf[1] |  | {"additionalProperties":false,"required_in_object":["line_ids"]} |
| parameters.line_ids | array | 必填（所在对象出现时） | oneOf[1] | 行记录ID数组 | {"maxItems":2,"minItems":2,"uniqueItems":true} |
| parameters.line_ids[] | integer | 每个数组元素 | oneOf[1] | 行记录ID数组 | {"minimum":1} |
| parameters | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["invoice_id","outstanding_line_id"]} |
| parameters.invoice_id | integer | 必填（所在对象出现时） | oneOf[2] | 发票/账单记录ID（具体类型按能力定义） | {"minimum":1} |
| parameters.outstanding_line_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"reconciliation.apply"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[1]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[1]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[1]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_invoice_outstanding_assignment_or_line_pair_reconciliation
- `verify`：same_transaction_target_partial_and_invoice_status_validation
- `idempotency`：odoo_persisted_business_marker_and_result_replay
- `reverse`：reconciliation.undo

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request, exact confirmation, fixed bridge action, Odoo-side execution, idempotent replay, and CLI response contract.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_core_write_cli.py
- `integration`：`implemented`；The shared dual-database rollback smoke covers invoice outstanding assignment and replay.；引用：tests/integration/test_core_write_batch_live.py, tests/integration/test_accounting_depth_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-automatic-run"></a>

## reconciliation.automatic.run — 运行自动核销

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.auto.reconcile.wizard, account.account, account.move.line, account.partial.reconcile, account.full.reconcile；向导：account.auto.reconcile.wizard。
- 必需模块：account, account_accountant；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.auto.reconcile.wizard:create, account.account:read, account.move.line:read, account.move.line:write, account.partial.reconcile:read, account.partial.reconcile:create, account.full.reconcile:read。
- 请求/响应合同：`schemas/v1/reconciliation.automatic.run.request.schema.json` / `schemas/v1/reconciliation.automatic.run.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run reconciliation.automatic.run --request "@request.json" --idempotency-key "reconciliation.automatic.run:17f8af97ad4a7f7639a4c9171d5185cb" --confirm "reconciliation.automatic.run"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "line_ids": [
      1,
      2
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  |  |
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["line_ids"]} |
| parameters.line_ids | array | 必填（所在对象出现时） |  | 行记录ID数组 | {"maxItems":200,"minItems":2,"uniqueItems":true} |
| parameters.line_ids[] | integer | 每个数组元素 |  | 行记录ID数组 | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"reconciliation.automatic.run"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"reconciliation.automatic.run"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：native_auto_reconcile_wizard_on_exact_company_scoped_lines
- `verify`：selected_line_reconciliation_graph_and_response_schema_validation
- `idempotency`：odoo_reconciliation_graph_and_exact_line_set_replay
- `reverse`：reconciliation.undo

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the exact line set, reconciliation-graph replay, runtime action, result drift checks, and CLI response.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_core_write_cli.py, tests/unit/test_extended_core_writes.py
- `integration`：`implemented`；The guarded shared live smoke executed the public write contract and immediate replay in both dedicated isolated database aliases, then verified full transaction rollback with a fresh read-only cursor.；引用：tests/integration/test_extended_write_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-candidates-list"></a>

## reconciliation.candidates.list — 列出核销候选项

- 类型：只读；静态状态：`unconfigured`；handler：`reconciliation_candidates_list`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.move.line, account.move, account.account, account.journal, res.partner, res.currency, account.reconcile.model；向导：account.reconcile.wizard。
- 必需模块：account, account_accountant；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move.line:read, account.move:read, account.account:read, account.journal:read, res.partner:read, res.currency:read, account.reconcile.model:read。
- 请求/响应合同：`schemas/v1/reconciliation.candidates.list.request.schema.json` / `schemas/v1/reconciliation.candidates.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read reconciliation.candidates.list --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {}
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"resolved_ref":"#/$defs/parameters"} |
| parameters.date_from | 组合/开放结构 | 可选（可能有条件限制） |  | 开始日期 | {"default":null,"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| parameters.date_from | null | 分支约束 | oneOf[1] | 开始日期 |  |
| parameters.date_from | string | 分支约束 | oneOf[2] | 开始日期 | {"format":"date"} |
| parameters.date_to | 组合/开放结构 | 可选（可能有条件限制） |  | 结束日期 | {"default":null,"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| parameters.date_to | null | 分支约束 | oneOf[1] | 结束日期 |  |
| parameters.date_to | string | 分支约束 | oneOf[2] | 结束日期 | {"format":"date"} |
| parameters.states | array | 可选（可能有条件限制） |  |  | {"default":["posted"],"maxItems":2,"minItems":1,"uniqueItems":true} |
| parameters.states[] | 未限定 | 每个数组元素 |  |  | {"enum":["draft","posted"]} |
| parameters.account_id | integer/null | 可选（可能有条件限制） |  | 会计科目ID | {"default":null,"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.partner_id | integer/null | 可选（可能有条件限制） |  | 合作伙伴ID | {"default":null,"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.journal_id | integer/null | 可选（可能有条件限制） |  | 日记账ID | {"default":null,"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.account_kinds | array | 可选（可能有条件限制） |  |  | {"default":["receivable","payable","other"],"maxItems":3,"minItems":1,"uniqueItems":true} |
| parameters.account_kinds[] | 未限定 | 每个数组元素 |  |  | {"enum":["receivable","payable","other"]} |
| parameters.query | 组合/开放结构 | 可选（可能有条件限制） |  | 搜索文本 | {"default":null,"oneOf":[{"type":"null"},{"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","type":"string"}]} |
| parameters.query | null | 分支约束 | oneOf[1] | 搜索文本 |  |
| parameters.query | string | 分支约束 | oneOf[2] | 搜索文本 | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"reconciliation.candidates.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","date","invoice_date","date_maturity","state","move","label","account","partner","journal","company_id","company_currency","currency","balance","amount_currency","amount_residual","amount_residual_currency","matching_number","reconciliation_model"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].invoice_date | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| response.data.items[].invoice_date | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].invoice_date | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.items[].date_maturity | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| response.data.items[].date_maturity | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].date_maturity | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted"]} |
| response.data.items[].move | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","ref"],"resolved_ref":"#/$defs/move"} |
| response.data.items[].move.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].move.name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].move.name | null | 分支约束 | oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].move.name | string | 分支约束 | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].move.move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["entry","out_invoice","out_refund","in_invoice","in_refund","out_receipt","in_receipt"]} |
| response.data.items[].move.ref | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].move.ref | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].move.ref | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].label | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].label | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].label | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].account | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name","account_type"],"resolved_ref":"#/$defs/account"} |
| response.data.items[].account.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].account.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":64,"minLength":1,"pattern":"^[A-Za-z0-9.]+$(?![\\s\\S])"} |
| response.data.items[].account.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].account.account_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["asset_receivable","asset_cash","asset_current","asset_non_current","asset_prepayments","asset_fixed","liability_payable","liability_credit_card","liability_current","liability_non_current","equity","equity_unaffected","income","income_other","expense","expense_depreciation","expense_direct_cost","expense_other","off_balance"]} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.items[].partner | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/partner"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].partner.name | null | 分支约束 | oneOf[2]/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].partner.name | string | 分支约束 | oneOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name","type"],"resolved_ref":"#/$defs/journal"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":5,"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].journal.type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["sale","purchase","cash","bank","credit","general"]} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].company_currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].company_currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].balance | string | 必填（所在对象出现时） | oneOf[2] | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/money"} |
| response.data.items[].amount_currency | string | 必填（所在对象出现时） | oneOf[2] | 外币/交易币数值，非默认公司币金额 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/money"} |
| response.data.items[].amount_residual | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:(?:[1-9][0-9]*)(?:\\.[0-9]+)?&#124;0\\.(?=[0-9]*[1-9])[0-9]+)$(?![\\s\\S])","resolved_ref":"#/$defs/nonzeroMoney"} |
| response.data.items[].amount_residual_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/money"} |
| response.data.items[].matching_number | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].matching_number | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].matching_number | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].reconciliation_model | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/historicalReconciliationModel"}]} |
| response.data.items[].reconciliation_model | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].reconciliation_model | object | 分支约束 | oneOf[2]/oneOf[2] | The reconciliation rule that historically created this move line; it is not a recommended matching rule. | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/historicalReconciliationModel"} |
| response.data.items[].reconciliation_model.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].reconciliation_model.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.has_more | boolean | 必填（所在对象出现时） | oneOf[2] | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | oneOf[2] | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","date","invoice_date","date_maturity","state","move","label","account","partner","journal","company_id","company_currency","currency","balance","amount_currency","amount_residual","amount_residual_currency","matching_number","reconciliation_model"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].invoice_date | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| response.data.items[].invoice_date | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].invoice_date | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date"} |
| response.data.items[].date_maturity | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| response.data.items[].date_maturity | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].date_maturity | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date"} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted"]} |
| response.data.items[].move | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","ref"],"resolved_ref":"#/$defs/move"} |
| response.data.items[].move.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].move.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].move.name | null | 分支约束 | allOf[1]/then/oneOf[1] | 名称/行说明 |  |
| response.data.items[].move.name | string | 分支约束 | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].move.move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["entry","out_invoice","out_refund","in_invoice","in_refund","out_receipt","in_receipt"]} |
| response.data.items[].move.ref | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].move.ref | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].move.ref | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].label | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].label | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].label | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].account | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name","account_type"],"resolved_ref":"#/$defs/account"} |
| response.data.items[].account.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].account.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":64,"minLength":1,"pattern":"^[A-Za-z0-9.]+$(?![\\s\\S])"} |
| response.data.items[].account.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].account.account_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["asset_receivable","asset_cash","asset_current","asset_non_current","asset_prepayments","asset_fixed","liability_payable","liability_credit_card","liability_current","liability_non_current","equity","equity_unaffected","income","income_other","expense","expense_depreciation","expense_direct_cost","expense_other","off_balance"]} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.items[].partner | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/partner"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].partner.name | null | 分支约束 | allOf[1]/then/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].partner.name | string | 分支约束 | allOf[1]/then/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name","type"],"resolved_ref":"#/$defs/journal"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":5,"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].journal.type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["sale","purchase","cash","bank","credit","general"]} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].company_currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].company_currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].balance | string | 必填（所在对象出现时） | allOf[1]/then | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/money"} |
| response.data.items[].amount_currency | string | 必填（所在对象出现时） | allOf[1]/then | 外币/交易币数值，非默认公司币金额 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/money"} |
| response.data.items[].amount_residual | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:(?:[1-9][0-9]*)(?:\\.[0-9]+)?&#124;0\\.(?=[0-9]*[1-9])[0-9]+)$(?![\\s\\S])","resolved_ref":"#/$defs/nonzeroMoney"} |
| response.data.items[].amount_residual_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/money"} |
| response.data.items[].matching_number | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].matching_number | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].matching_number | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].reconciliation_model | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/historicalReconciliationModel"}]} |
| response.data.items[].reconciliation_model | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].reconciliation_model | object | 分支约束 | allOf[1]/then/oneOf[2] | The reconciliation rule that historically created this move line; it is not a recommended matching rule. | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/historicalReconciliationModel"} |
| response.data.items[].reconciliation_model.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].reconciliation_model.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[1]/then | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[1]/then | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_local_odoo_readonly_composite
- `verify`：same_transaction_acl_result_and_v1_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request and response, stable cursor, fixed bridge action, eight-model ACL gate, company scope, ORM normalization, and control-CLI dispatch.；引用：tests/unit/test_reconciliation_candidates.py, tests/unit/test_reconciliation_candidate_bridge.py, tests/unit/test_reconciliation_candidates_runtime.py, tests/unit/test_reconciliation_candidates_cli.py
- `integration`：`implemented`；The live integration test verifies the fixed reconciliation-candidate read against both dedicated synthetic database aliases and both configured companies, including three-page cursor ordering, exact filters, and cross-company isolation.；引用：tests/integration/test_reconciliation_candidates_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-full-get"></a>

## reconciliation.full.get — 获取全额核销详情

- 类型：只读；静态状态：`unconfigured`；handler：`reconciliation_full_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.full.reconcile, account.partial.reconcile, account.move.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.full.reconcile:read, account.partial.reconcile:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/reconciliation.full.get.request.schema.json` / `schemas/v1/reconciliation.full.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read reconciliation.full.get --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "full_reconcile_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["full_reconcile_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.full_reconcile_id | integer | 必填（所在对象出现时） |  | 完整核销关系ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"reconciliation.full.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"reconciliation.full.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"reconciliation.full.list.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","matching_number","partial_reconcile_ids","reconciled_journal_item_ids"],"resolved_ref":"reconciliation.full.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.matching_number | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.partial_reconcile_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"minItems":1,"uniqueItems":true} |
| response.data.partial_reconcile_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.reconciled_journal_item_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"minItems":1,"uniqueItems":true} |
| response.data.reconciled_journal_item_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"reconciliation.full.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","matching_number","partial_reconcile_ids","reconciled_journal_item_ids"],"resolved_ref":"reconciliation.full.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.matching_number | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"minItems":1,"uniqueItems":true} |
| response.data.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.reconciled_journal_item_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"minItems":1,"uniqueItems":true} |
| response.data.reconciled_journal_item_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_company_scoped_core_object_read_action
- `verify`：same_transaction_acl_result_cursor_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request and response, fixed bridge action, company scope, ACL gates, ORM normalization, pagination where applicable, and CLI dispatch.；引用：tests/unit/test_core_object_reads.py, tests/unit/test_core_object_reads_bridge.py, tests/unit/test_core_object_reads_runtime.py, tests/unit/test_core_object_read_cli.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The shared live read-only smoke verifies the capability against both dedicated isolated database aliases as the ordinary accounting user.；引用：tests/integration/test_payment_reconciliation_read_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-full-list"></a>

## reconciliation.full.list — 列出全额核销

- 类型：只读；静态状态：`unconfigured`；handler：`reconciliation_full_list`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.full.reconcile, account.partial.reconcile, account.move.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.full.reconcile:read, account.partial.reconcile:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/reconciliation.full.list.request.schema.json` / `schemas/v1/reconciliation.full.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read reconciliation.full.list --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {}
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"resolved_ref":"#/$defs/parameters"} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"reconciliation.full.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","matching_number","partial_reconcile_ids","reconciled_journal_item_ids"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].matching_number | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].partial_reconcile_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"minItems":1,"uniqueItems":true} |
| response.data.items[].partial_reconcile_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.items[].reconciled_journal_item_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"minItems":1,"uniqueItems":true} |
| response.data.items[].reconciled_journal_item_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.has_more | boolean | 必填（所在对象出现时） | oneOf[2] | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | oneOf[2] | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2]/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | oneOf[2]/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | oneOf[2]/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | oneOf[2]/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | oneOf[2]/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | oneOf[2]/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","matching_number","partial_reconcile_ids","reconciled_journal_item_ids"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].matching_number | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"minItems":1,"uniqueItems":true} |
| response.data.items[].partial_reconcile_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].reconciled_journal_item_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"minItems":1,"uniqueItems":true} |
| response.data.items[].reconciled_journal_item_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[1]/then | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[1]/then | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | allOf[1]/then/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_company_scoped_core_object_read_action
- `verify`：same_transaction_acl_result_cursor_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request and response, fixed bridge action, company scope, ACL gates, ORM normalization, pagination where applicable, and CLI dispatch.；引用：tests/unit/test_core_object_reads.py, tests/unit/test_core_object_reads_bridge.py, tests/unit/test_core_object_reads_runtime.py, tests/unit/test_core_object_read_cli.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The shared live read-only smoke verifies the capability against both dedicated isolated database aliases as the ordinary accounting user.；引用：tests/integration/test_payment_reconciliation_read_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-model-activity_type-assign"></a>

## reconciliation.model.activity_type.assign — 设置对账规则后续活动类型

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured caller/company and native ACLs. Edits fixed rule fields/lines, not posted journal amounts. Copy uses native copy with new child IDs; usage lists are scoped ORM reads of reconcile_model_id. Follow-up assignment only changes configuration; it schedules no activity. Numeric rule percentages follow native nonzero signed constraints, not an invented 0-100 ceiling. Serial line creation matches one full native payload; ambiguity conflicts. Delete missing targets remain record_not_found, never a fabricated successful replay. Native model deletion cascades rule lines and can clear historical reconcile_model_id links; no bank/provider call, mail delivery, arbitrary methods or caller-sudo.
- 内部domain：`reconciliation`；来源模型：account.reconcile.model, account.reconcile.model.line, mail.activity.type, res.company；向导：无。
- 必需模块：account, base, mail；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.reconcile.model.line:read, account.reconcile.model:read, account.reconcile.model:write, mail.activity.type:read, res.company:read。
- 请求/响应合同：`schemas/v1/reconciliation.model.activity_type.assign.request.schema.json` / `schemas/v1/reconciliation.model.activity_type.assign.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run reconciliation.model.activity_type.assign --request "@request.json" --idempotency-key "reconciliation.model.activity_type.assign:1:ec867b86398cb309e81e0b14d5e203d4" --confirm "reconciliation.model.activity_type.assign"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "activity_type_id": 1,
    "reconciliation_model_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["activity_type_id","reconciliation_model_id"]} |
| parameters.reconciliation_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.activity_type_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"reconciliation.model.activity_type.assign"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"reconciliation.model.activity_type.assign"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_native_rule_fields_copy_or_unlink
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：serial_native_payload_match_or_missing_target_denial
- `reverse`：previous_values_or_native_backup_restore_subject_to_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Closed contracts, fixed CLI/ORM routing, child ownership, native numeric/regex shapes, ACL denial and serial payload replay.；引用：tests/unit/test_reconciliation_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all nine new IDs, two existing setup IDs and eleven immediate replays; native computed partner mapping, signed amounts above 100 percent and regex, native line IDs and complete ordering, tax/analytic configuration copy and clearing, activity configuration without scheduling, scoped usage ID-keyset reads including archived rules, actual child deletion and used-rule cascade/usage-link clearing with posted amounts unchanged. Foreign-company, wrong-parent, incomplete ordering, invalid regex/activity model, changed-source copy conflicts and missing targets denied. Fresh-cursor business-data and temporary-group rollback verified. No actual bank reconciliation, external notification, addon or service changes.；引用：tests/integration/test_reconciliation_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-model-archive"></a>

## reconciliation.model.archive — 停用对账模型

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.reconcile.model；向导：无。
- 必需模块：account, account_accountant, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.reconcile.model:read, account.reconcile.model:write。
- 请求/响应合同：`schemas/v1/reconciliation.model.archive.request.schema.json` / `schemas/v1/reconciliation.model.archive.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run reconciliation.model.archive --request "@request.json" --idempotency-key "reconciliation.model.archive:1" --confirm "reconciliation.model.archive"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "reconciliation_model_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["reconciliation_model_id"]} |
| parameters.reconciliation_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"reconciliation.model.archive"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"reconciliation.model.archive"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_company_reconciliation_model_archive
- `verify`：same_transaction_inactive_state_reread
- `idempotency`：target_inactive_state_recheck_without_operation_store
- `reverse`：reconciliation.model.restore

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed identifier contract, company ownership, manager ACL, target-state replay, schemas, registry metadata, and CLI dispatch.；引用：tests/unit/test_core_writes.py, tests/unit/test_accounting_configuration_write_contracts.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_accounting_configuration_expansion_registry.py
- `integration`：`implemented`；The guarded shared transactional smoke verifies first execution, immediate deterministic replay, and rollback against both dedicated isolated databases.；引用：tests/integration/test_accounting_configuration_expansion_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-model-create"></a>

## reconciliation.model.create — 创建对账模型

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`concurrent_idempotency_limit` — The fixed handler replays an exact company-and-name target, but Odoo provides no request-id uniqueness constraint, so concurrent exactly-once creation is not guaranteed.
- 内部domain：`bank_reconciliation`；来源模型：res.company, res.partner, account.journal, account.reconcile.model；向导：无。
- 必需模块：account, account_accountant, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, res.partner:read, account.journal:read, account.reconcile.model:read, account.reconcile.model:create。
- 请求/响应合同：`schemas/v1/reconciliation.model.create.request.schema.json` / `schemas/v1/reconciliation.model.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run reconciliation.model.create --request "@request.json" --idempotency-key "reconciliation.model.create:1:a765537672930ca4864600e4ee5ebc05" --confirm "reconciliation.model.create"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "name": "Example",
    "sequence": 1,
    "trigger": "manual",
    "match_journal_ids": [],
    "match_partner_ids": [],
    "match_amount": {
      "minimum": null,
      "maximum": "1",
      "operator": "lower"
    },
    "match_label": {
      "operator": "contains",
      "value": "1"
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["name","sequence","trigger","match_journal_ids","match_partner_ids","match_amount","match_label"],"resolved_ref":"#/$defs/model_values"} |
| parameters.name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":256,"minLength":1} |
| parameters.sequence | integer | 必填（所在对象出现时） |  |  | {"minimum":0} |
| parameters.trigger | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["manual","auto_reconcile"]} |
| parameters.match_journal_ids | array | 必填（所在对象出现时） |  |  | {"resolved_ref":"#/$defs/positive_ids","uniqueItems":true} |
| parameters.match_journal_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.match_partner_ids | array | 必填（所在对象出现时） |  |  | {"resolved_ref":"#/$defs/positive_ids","uniqueItems":true} |
| parameters.match_partner_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.match_amount | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"additionalProperties":false,"properties":{"maximum":{"$ref":"#/$defs/nonnegative_decimal"},"minimum":{"type":"null"},"operator":{"const":"lower"}},"required":["operator","minimum","maximum"],"type":"object"},{"additionalProperties":false,"properties":{"maximum":{"type":"null"},"minimum":{"$ref":"#/$defs/nonnegative_decimal"},"operator":{"const":"greater"}},"required":["operator","minimum","maximum"],"type":"object"},{"additionalProperties":false,"properties":{"maximum":{"$ref":"#/$defs/nonnegative_decimal"},"minimum":{"$ref":"#/$defs/nonnegative_decimal"},"operator":{"const":"between"}},"required":["operator","minimum","maximum"],"type":"object"}],"resolved_ref":"#/$defs/match_amount"} |
| parameters.match_amount | null | 分支约束 | oneOf[1] |  |  |
| parameters.match_amount | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["operator","minimum","maximum"]} |
| parameters.match_amount.operator | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":"lower"} |
| parameters.match_amount.minimum | null | 必填（所在对象出现时） | oneOf[2] |  |  |
| parameters.match_amount.maximum | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*&#124;(?:0&#124;[1-9][0-9]*)\\.[0-9]*[1-9])$","resolved_ref":"#/$defs/nonnegative_decimal"} |
| parameters.match_amount | object | 分支约束 | oneOf[3] |  | {"additionalProperties":false,"required_in_object":["operator","minimum","maximum"]} |
| parameters.match_amount.operator | 未限定 | 必填（所在对象出现时） | oneOf[3] |  | {"const":"greater"} |
| parameters.match_amount.minimum | string | 必填（所在对象出现时） | oneOf[3] |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*&#124;(?:0&#124;[1-9][0-9]*)\\.[0-9]*[1-9])$","resolved_ref":"#/$defs/nonnegative_decimal"} |
| parameters.match_amount.maximum | null | 必填（所在对象出现时） | oneOf[3] |  |  |
| parameters.match_amount | object | 分支约束 | oneOf[4] |  | {"additionalProperties":false,"required_in_object":["operator","minimum","maximum"]} |
| parameters.match_amount.operator | 未限定 | 必填（所在对象出现时） | oneOf[4] |  | {"const":"between"} |
| parameters.match_amount.minimum | string | 必填（所在对象出现时） | oneOf[4] |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*&#124;(?:0&#124;[1-9][0-9]*)\\.[0-9]*[1-9])$","resolved_ref":"#/$defs/nonnegative_decimal"} |
| parameters.match_amount.maximum | string | 必填（所在对象出现时） | oneOf[4] |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*&#124;(?:0&#124;[1-9][0-9]*)\\.[0-9]*[1-9])$","resolved_ref":"#/$defs/nonnegative_decimal"} |
| parameters.match_label | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"additionalProperties":false,"properties":{"operator":{"enum":["contains","not_contains","match_regex"]},"value":{"maxLength":500,"minLength":1,"type":"string"}},"required":["operator","value"],"type":"object"}],"resolved_ref":"#/$defs/match_label"} |
| parameters.match_label | null | 分支约束 | oneOf[1] |  |  |
| parameters.match_label | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["operator","value"]} |
| parameters.match_label.operator | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["contains","not_contains","match_regex"]} |
| parameters.match_label.value | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":500,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"reconciliation.model.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"reconciliation.model.create"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_company_reconciliation_model_create_as_configured_business_user
- `verify`：same_transaction_header_match_criteria_and_response_schema_validation
- `idempotency`：company_name_and_full_normalized_target_recheck_without_concurrent_exactly_once_guarantee
- `reverse`：reconciliation.model.archive

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed model contract, company-scoped journal and partner references, match criteria, manager ACL, replay, schemas, registry metadata, and CLI dispatch.；引用：tests/unit/test_core_writes.py, tests/unit/test_accounting_configuration_write_contracts.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_accounting_configuration_expansion_registry.py
- `integration`：`implemented`；The guarded shared transactional smoke verifies first execution, immediate deterministic replay, and rollback against both dedicated isolated databases.；引用：tests/integration/test_accounting_configuration_expansion_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-model-delete"></a>

## reconciliation.model.delete — 删除对账规则

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured caller/company and native ACLs. Edits fixed rule fields/lines, not posted journal amounts. Copy uses native copy with new child IDs; usage lists are scoped ORM reads of reconcile_model_id. Follow-up assignment only changes configuration; it schedules no activity. Numeric rule percentages follow native nonzero signed constraints, not an invented 0-100 ceiling. Serial line creation matches one full native payload; ambiguity conflicts. Delete missing targets remain record_not_found, never a fabricated successful replay. Native model deletion cascades rule lines and can clear historical reconcile_model_id links; no bank/provider call, mail delivery, arbitrary methods or caller-sudo.
- 内部domain：`reconciliation`；来源模型：account.reconcile.model, account.reconcile.model.line, res.company；向导：无。
- 必需模块：account, base, mail；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.reconcile.model.line:read, account.reconcile.model.line:unlink, account.reconcile.model:read, account.reconcile.model:unlink, res.company:read。
- 请求/响应合同：`schemas/v1/reconciliation.model.delete.request.schema.json` / `schemas/v1/reconciliation.model.delete.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run reconciliation.model.delete --request "@request.json" --idempotency-key "reconciliation.model.delete:1:d111d7a84e7b6a288a0fe61343990ec4" --confirm "reconciliation.model.delete"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "reconciliation_model_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["reconciliation_model_id"]} |
| parameters.reconciliation_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"reconciliation.model.delete"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"reconciliation.model.delete"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_native_rule_fields_copy_or_unlink
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：serial_native_payload_match_or_missing_target_denial
- `reverse`：previous_values_or_native_backup_restore_subject_to_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Closed contracts, fixed CLI/ORM routing, child ownership, native numeric/regex shapes, ACL denial and serial payload replay.；引用：tests/unit/test_reconciliation_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all nine new IDs, two existing setup IDs and eleven immediate replays; native computed partner mapping, signed amounts above 100 percent and regex, native line IDs and complete ordering, tax/analytic configuration copy and clearing, activity configuration without scheduling, scoped usage ID-keyset reads including archived rules, actual child deletion and used-rule cascade/usage-link clearing with posted amounts unchanged. Foreign-company, wrong-parent, incomplete ordering, invalid regex/activity model, changed-source copy conflicts and missing targets denied. Fresh-cursor business-data and temporary-group rollback verified. No actual bank reconciliation, external notification, addon or service changes.；引用：tests/integration/test_reconciliation_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-model-duplicate"></a>

## reconciliation.model.duplicate — 复制对账规则

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured caller/company and native ACLs. Edits fixed rule fields/lines, not posted journal amounts. Copy uses native copy with new child IDs; usage lists are scoped ORM reads of reconcile_model_id. Follow-up assignment only changes configuration; it schedules no activity. Numeric rule percentages follow native nonzero signed constraints, not an invented 0-100 ceiling. Serial line creation matches one full native payload; ambiguity conflicts. Delete missing targets remain record_not_found, never a fabricated successful replay. Native model deletion cascades rule lines and can clear historical reconcile_model_id links; no bank/provider call, mail delivery, arbitrary methods or caller-sudo.
- 内部domain：`reconciliation`；来源模型：account.account, account.analytic.account, account.journal, account.reconcile.model, account.reconcile.model.line, account.tax, mail.activity.type, res.company, res.partner；向导：无。
- 必需模块：account, base, mail；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.account:read, account.analytic.account:read, account.journal:read, account.reconcile.model.line:create, account.reconcile.model.line:read, account.reconcile.model:create, account.reconcile.model:read, account.tax:read, mail.activity.type:read, res.company:read, res.partner:read。
- 请求/响应合同：`schemas/v1/reconciliation.model.duplicate.request.schema.json` / `schemas/v1/reconciliation.model.duplicate.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run reconciliation.model.duplicate --request "@request.json" --idempotency-key "reconciliation.model.duplicate:1:fb4a3de12a46937e6d225844e90e2357" --confirm "reconciliation.model.duplicate"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "name": "Example",
    "reconciliation_model_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["name","reconciliation_model_id"]} |
| parameters.reconciliation_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":256,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"reconciliation.model.duplicate"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"reconciliation.model.duplicate"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_native_rule_fields_copy_or_unlink
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：serial_native_payload_match_or_missing_target_denial
- `reverse`：previous_values_or_native_backup_restore_subject_to_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Closed contracts, fixed CLI/ORM routing, child ownership, native numeric/regex shapes, ACL denial and serial payload replay.；引用：tests/unit/test_reconciliation_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all nine new IDs, two existing setup IDs and eleven immediate replays; native computed partner mapping, signed amounts above 100 percent and regex, native line IDs and complete ordering, tax/analytic configuration copy and clearing, activity configuration without scheduling, scoped usage ID-keyset reads including archived rules, actual child deletion and used-rule cascade/usage-link clearing with posted amounts unchanged. Foreign-company, wrong-parent, incomplete ordering, invalid regex/activity model, changed-source copy conflicts and missing targets denied. Fresh-cursor business-data and temporary-group rollback verified. No actual bank reconciliation, external notification, addon or service changes.；引用：tests/integration/test_reconciliation_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-model-get"></a>

## reconciliation.model.get — 获取对账模型详情

- 类型：只读；静态状态：`unconfigured`；handler：`reconciliation_model_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.reconcile.model；向导：无。
- 必需模块：account, account_accountant；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.reconcile.model:read。
- 请求/响应合同：`schemas/v1/reconciliation.model.get.request.schema.json` / `schemas/v1/reconciliation.model.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read reconciliation.model.get --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "reconciliation_model_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["reconciliation_model_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.reconciliation_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"reconciliation.model.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"reconciliation.model.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"reconciliation.model.list.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","sequence","active","company_id","match_amount","match_amount_min","match_amount_max","match_label","match_label_param"],"resolved_ref":"reconciliation.model.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.sequence | integer | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.match_amount | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.match_amount | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.match_amount | string | 分支约束 | oneOf[2]/oneOf[2] |  |  |
| response.data.match_amount_min | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.match_amount_max | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.match_label | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.match_label | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.match_label | string | 分支约束 | oneOf[2]/oneOf[2] |  |  |
| response.data.match_label_param | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.match_label_param | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.match_label_param | string | 分支约束 | oneOf[2]/oneOf[2] |  |  |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"reconciliation.model.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","sequence","active","company_id","match_amount","match_amount_min","match_amount_max","match_label","match_label_param"],"resolved_ref":"reconciliation.model.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.sequence | integer | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.match_amount | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.match_amount | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.match_amount | string | 分支约束 | allOf[1]/then/oneOf[2] |  |  |
| response.data.match_amount_min | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.match_amount_max | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.match_label | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.match_label | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.match_label | string | 分支约束 | allOf[1]/then/oneOf[2] |  |  |
| response.data.match_label_param | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.match_label_param | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.match_label_param | string | 分支约束 | allOf[1]/then/oneOf[2] |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_company_scoped_core_object_read_action
- `verify`：same_transaction_acl_result_cursor_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request and response, fixed bridge action, company scope, ACL gates, ORM normalization, and CLI dispatch.；引用：tests/unit/test_core_object_reads.py, tests/unit/test_core_object_reads_bridge.py, tests/unit/test_core_object_reads_runtime.py, tests/unit/test_core_object_read_cli.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The shared live read-only smoke verifies the capability against both dedicated isolated database aliases as the ordinary accounting user.；引用：tests/integration/test_accounting_configuration_read_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-model-line-create"></a>

## reconciliation.model.line.create — 新增对账规则行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured caller/company and native ACLs. Edits fixed rule fields/lines, not posted journal amounts. Copy uses native copy with new child IDs; usage lists are scoped ORM reads of reconcile_model_id. Follow-up assignment only changes configuration; it schedules no activity. Numeric rule percentages follow native nonzero signed constraints, not an invented 0-100 ceiling. Serial line creation matches one full native payload; ambiguity conflicts. Delete missing targets remain record_not_found, never a fabricated successful replay. Native model deletion cascades rule lines and can clear historical reconcile_model_id links; no bank/provider call, mail delivery, arbitrary methods or caller-sudo.
- 内部domain：`reconciliation`；来源模型：account.account, account.analytic.account, account.reconcile.model, account.reconcile.model.line, account.tax, res.company, res.partner；向导：无。
- 必需模块：account, base, mail；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.account:read, account.analytic.account:read, account.reconcile.model.line:create, account.reconcile.model.line:read, account.reconcile.model:read, account.tax:read, res.company:read, res.partner:read。
- 请求/响应合同：`schemas/v1/reconciliation.model.line.create.request.schema.json` / `schemas/v1/reconciliation.model.line.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run reconciliation.model.line.create --request "@request.json" --idempotency-key "reconciliation.model.line.create:1:53fb53caf6dbc915622e530d721a688a" --confirm "reconciliation.model.line.create"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "line": {
      "account_id": 1,
      "amount_string": "1",
      "amount_type": "fixed",
      "label": "1",
      "partner_id": 1,
      "sequence": 1,
      "tax_ids": []
    },
    "reconciliation_model_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["line","reconciliation_model_id"]} |
| parameters.reconciliation_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.line | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"allOf":[{"if":{"properties":{"amount_type":{"enum":["fixed","percentage","percentage_st_line"]}},"required":["amount_type"]},"then":{"properties":{"amount_string":{"maxLength":256,"pattern":"^(?!-?0(?:\\.0+)?$(?![\\s\\S]))-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","type":"string"}}}}],"required_in_object":["account_id","amount_string","amount_type","label","partner_id","sequence","tax_ids"]} |
| parameters.line.sequence | integer | 必填（所在对象出现时） |  |  | {"maximum":2147483647,"minimum":-2147483648} |
| parameters.line.account_id | integer/null | 必填（所在对象出现时） |  | 会计科目ID | {"minimum":1} |
| parameters.line.partner_id | integer/null | 必填（所在对象出现时） |  | 合作伙伴ID | {"minimum":1} |
| parameters.line.label | string/null | 必填（所在对象出现时） |  |  | {"maxLength":500,"minLength":1} |
| parameters.line.amount_type | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["fixed","percentage","percentage_st_line","regex"]} |
| parameters.line.amount_string | string | 必填（所在对象出现时） |  |  | {"maxLength":500,"minLength":1} |
| parameters.line.tax_ids | array | 必填（所在对象出现时） |  | 应用税ID数组 | {"maxItems":100,"uniqueItems":true} |
| parameters.line.tax_ids[] | integer | 每个数组元素 |  | 应用税ID数组 | {"minimum":1} |
| parameters.line.analytic_distribution | array | 可选（可能有条件限制） |  | 分析分摊映射；写入与读回约束可能不同 | {"maxItems":16} |
| parameters.line.analytic_distribution[] | object | 每个数组元素 |  | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":false,"required_in_object":["analytic_account_ids","percentage"]} |
| parameters.line.analytic_distribution[].analytic_account_ids | array | 必填（所在对象出现时） |  |  | {"maxItems":16,"minItems":1,"uniqueItems":true} |
| parameters.line.analytic_distribution[].analytic_account_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.line.analytic_distribution[].percentage | string | 必填（所在对象出现时） |  |  | {"maxLength":256,"pattern":"^(?:(?:[1-9][0-9]?)(?:\\.[0-9]{1,4})?&#124;0\\.(?=[0-9]*[1-9])[0-9]{1,4}&#124;100(?:\\.0{1,4})?)$(?![\\s\\S])"} |
| parameters.line | 组合/开放结构 | 分支约束 | allOf[1] |  | {"if":{"properties":{"amount_type":{"enum":["fixed","percentage","percentage_st_line"]}},"required":["amount_type"]},"then":{"properties":{"amount_string":{"maxLength":256,"pattern":"^(?!-?0(?:\\.0+)?$(?![\\s\\S]))-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","type":"string"}}}} |
| parameters.line | 未限定 | 条件分支 | allOf[1]/then |  |  |
| parameters.line.amount_string | string | 可选（可能有条件限制） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?!-?0(?:\\.0+)?$(?![\\s\\S]))-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"reconciliation.model.line.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"reconciliation.model.line.create"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_native_rule_fields_copy_or_unlink
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：serial_native_payload_match_or_missing_target_denial
- `reverse`：previous_values_or_native_backup_restore_subject_to_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Closed contracts, fixed CLI/ORM routing, child ownership, native numeric/regex shapes, ACL denial and serial payload replay.；引用：tests/unit/test_reconciliation_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all nine new IDs, two existing setup IDs and eleven immediate replays; native computed partner mapping, signed amounts above 100 percent and regex, native line IDs and complete ordering, tax/analytic configuration copy and clearing, activity configuration without scheduling, scoped usage ID-keyset reads including archived rules, actual child deletion and used-rule cascade/usage-link clearing with posted amounts unchanged. Foreign-company, wrong-parent, incomplete ordering, invalid regex/activity model, changed-source copy conflicts and missing targets denied. Fresh-cursor business-data and temporary-group rollback verified. No actual bank reconciliation, external notification, addon or service changes.；引用：tests/integration/test_reconciliation_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-model-line-delete"></a>

## reconciliation.model.line.delete — 删除对账规则行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured caller/company and native ACLs. Edits fixed rule fields/lines, not posted journal amounts. Copy uses native copy with new child IDs; usage lists are scoped ORM reads of reconcile_model_id. Follow-up assignment only changes configuration; it schedules no activity. Numeric rule percentages follow native nonzero signed constraints, not an invented 0-100 ceiling. Serial line creation matches one full native payload; ambiguity conflicts. Delete missing targets remain record_not_found, never a fabricated successful replay. Native model deletion cascades rule lines and can clear historical reconcile_model_id links; no bank/provider call, mail delivery, arbitrary methods or caller-sudo.
- 内部domain：`reconciliation`；来源模型：account.reconcile.model, account.reconcile.model.line, res.company；向导：无。
- 必需模块：account, base, mail；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.reconcile.model.line:read, account.reconcile.model.line:unlink, account.reconcile.model:read, res.company:read。
- 请求/响应合同：`schemas/v1/reconciliation.model.line.delete.request.schema.json` / `schemas/v1/reconciliation.model.line.delete.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run reconciliation.model.line.delete --request "@request.json" --idempotency-key "reconciliation.model.line.delete:1:705f0962e8da043c5bbbfcfcbf5084d6" --confirm "reconciliation.model.line.delete"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "line_id": 1,
    "reconciliation_model_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["line_id","reconciliation_model_id"]} |
| parameters.reconciliation_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"reconciliation.model.line.delete"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"reconciliation.model.line.delete"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_native_rule_fields_copy_or_unlink
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：serial_native_payload_match_or_missing_target_denial
- `reverse`：previous_values_or_native_backup_restore_subject_to_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Closed contracts, fixed CLI/ORM routing, child ownership, native numeric/regex shapes, ACL denial and serial payload replay.；引用：tests/unit/test_reconciliation_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all nine new IDs, two existing setup IDs and eleven immediate replays; native computed partner mapping, signed amounts above 100 percent and regex, native line IDs and complete ordering, tax/analytic configuration copy and clearing, activity configuration without scheduling, scoped usage ID-keyset reads including archived rules, actual child deletion and used-rule cascade/usage-link clearing with posted amounts unchanged. Foreign-company, wrong-parent, incomplete ordering, invalid regex/activity model, changed-source copy conflicts and missing targets denied. Fresh-cursor business-data and temporary-group rollback verified. No actual bank reconciliation, external notification, addon or service changes.；引用：tests/integration/test_reconciliation_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-model-line-get"></a>

## reconciliation.model.line.get — 获取对账模型行详情

- 类型：只读；静态状态：`unconfigured`；handler：`reconciliation_model_line_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.reconcile.model, account.reconcile.model.line, account.account, res.partner, account.tax, account.analytic.account；向导：无。
- 必需模块：account, account_accountant, analytic；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.reconcile.model:read, account.reconcile.model.line:read, account.account:read, res.partner:read, account.tax:read, account.analytic.account:read。
- 请求/响应合同：`schemas/v1/reconciliation.model.line.get.request.schema.json` / `schemas/v1/reconciliation.model.line.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read reconciliation.model.line.get --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "reconciliation_model_line_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["reconciliation_model_line_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.reconciliation_model_line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"reconciliation.model.line.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"reconciliation.model.line.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"reconciliation.model.line.list.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","sequence","company_id","reconciliation_model","account","partner","label","amount_type","amount","amount_string","taxes","analytic_distribution"],"resolved_ref":"reconciliation.model.line.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.sequence | integer | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.reconciliation_model | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.reconciliation_model.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.reconciliation_model.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.account | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/coded"}]} |
| response.data.account | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.account | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.partner | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.partner | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.partner | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.label | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.amount_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["fixed","percentage","percentage_st_line","regex"]} |
| response.data.amount | string | 必填（所在对象出现时） | oneOf[2] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_string | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.taxes | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.taxes[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.taxes[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.taxes[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.analytic_distribution | array | 必填（所在对象出现时） | oneOf[2] | 分析分摊映射；写入与读回约束可能不同 | {"maxItems":1000,"uniqueItems":true} |
| response.data.analytic_distribution[] | object | 每个数组元素 | oneOf[2] | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":false,"required_in_object":["analytic_accounts","percentage"],"resolved_ref":"#/$defs/analytic_distribution"} |
| response.data.analytic_distribution[].analytic_accounts | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000,"minItems":1,"uniqueItems":true} |
| response.data.analytic_distribution[].analytic_accounts[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.analytic_distribution[].analytic_accounts[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.analytic_distribution[].analytic_accounts[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.analytic_distribution[].percentage | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"reconciliation.model.line.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","sequence","company_id","reconciliation_model","account","partner","label","amount_type","amount","amount_string","taxes","analytic_distribution"],"resolved_ref":"reconciliation.model.line.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.sequence | integer | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.reconciliation_model | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.reconciliation_model.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.reconciliation_model.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.account | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/coded"}]} |
| response.data.account | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.account | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.partner | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.partner | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.label | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.amount_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["fixed","percentage","percentage_st_line","regex"]} |
| response.data.amount | string | 必填（所在对象出现时） | allOf[1]/then | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_string | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.taxes | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.taxes[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.taxes[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.taxes[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.analytic_distribution | array | 必填（所在对象出现时） | allOf[1]/then | 分析分摊映射；写入与读回约束可能不同 | {"maxItems":1000,"uniqueItems":true} |
| response.data.analytic_distribution[] | object | 每个数组元素 | allOf[1]/then | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":false,"required_in_object":["analytic_accounts","percentage"],"resolved_ref":"#/$defs/analytic_distribution"} |
| response.data.analytic_distribution[].analytic_accounts | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000,"minItems":1,"uniqueItems":true} |
| response.data.analytic_distribution[].analytic_accounts[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.analytic_distribution[].analytic_accounts[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.analytic_distribution[].analytic_accounts[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.analytic_distribution[].percentage | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_company_scoped_core_object_read_action
- `verify`：same_transaction_acl_result_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the closed request and response schemas, registry metadata, CLI handler, validator, model, and audit routing.；引用：tests/unit/test_accounting_reference_read_registry.py
- `integration`：`implemented`；The shared live read-only smoke verifies the capability against both dedicated isolated database aliases without database changes.；引用：tests/integration/test_accounting_reference_read_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-model-line-list"></a>

## reconciliation.model.line.list — 列出对账模型行

- 类型：只读；静态状态：`unconfigured`；handler：`reconciliation_model_line_list`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.reconcile.model, account.reconcile.model.line, account.account, res.partner, account.tax, account.analytic.account；向导：无。
- 必需模块：account, account_accountant, analytic；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.reconcile.model:read, account.reconcile.model.line:read, account.account:read, res.partner:read, account.tax:read, account.analytic.account:read。
- 请求/响应合同：`schemas/v1/reconciliation.model.line.list.request.schema.json` / `schemas/v1/reconciliation.model.line.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read reconciliation.model.line.list --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {}
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"resolved_ref":"#/$defs/parameters"} |
| parameters.reconciliation_model_id | integer/null | 可选（可能有条件限制） |  |  | {"default":null,"minimum":1} |
| parameters.account_id | integer/null | 可选（可能有条件限制） |  | 会计科目ID | {"default":null,"minimum":1} |
| parameters.partner_id | integer/null | 可选（可能有条件限制） |  | 合作伙伴ID | {"default":null,"minimum":1} |
| parameters.amount_types | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"default":null,"oneOf":[{"type":"null"},{"items":{"enum":["fixed","percentage","percentage_st_line","regex"]},"maxItems":4,"minItems":1,"type":"array","uniqueItems":true}]} |
| parameters.amount_types | null | 分支约束 | oneOf[1] |  |  |
| parameters.amount_types | array | 分支约束 | oneOf[2] |  | {"maxItems":4,"minItems":1,"uniqueItems":true} |
| parameters.amount_types[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["fixed","percentage","percentage_st_line","regex"]} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"reconciliation.model.line.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","sequence","company_id","reconciliation_model","account","partner","label","amount_type","amount","amount_string","taxes","analytic_distribution"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].sequence | integer | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].reconciliation_model | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].reconciliation_model.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].reconciliation_model.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].account | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/coded"}]} |
| response.data.items[].account | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].account | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.items[].account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].partner | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].label | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].amount_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["fixed","percentage","percentage_st_line","regex"]} |
| response.data.items[].amount | string | 必填（所在对象出现时） | oneOf[2] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_string | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].taxes | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.items[].taxes[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].taxes[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].taxes[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].analytic_distribution | array | 必填（所在对象出现时） | oneOf[2] | 分析分摊映射；写入与读回约束可能不同 | {"maxItems":1000,"uniqueItems":true} |
| response.data.items[].analytic_distribution[] | object | 每个数组元素 | oneOf[2] | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":false,"required_in_object":["analytic_accounts","percentage"],"resolved_ref":"#/$defs/analytic_distribution"} |
| response.data.items[].analytic_distribution[].analytic_accounts | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000,"minItems":1,"uniqueItems":true} |
| response.data.items[].analytic_distribution[].analytic_accounts[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].analytic_distribution[].analytic_accounts[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].analytic_distribution[].analytic_accounts[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].analytic_distribution[].percentage | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.has_more | boolean | 必填（所在对象出现时） | oneOf[2] | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | oneOf[2] | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2]/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | oneOf[2]/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | oneOf[2]/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | oneOf[2]/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | oneOf[2]/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | oneOf[2]/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","sequence","company_id","reconciliation_model","account","partner","label","amount_type","amount","amount_string","taxes","analytic_distribution"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].sequence | integer | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].reconciliation_model | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].reconciliation_model.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].reconciliation_model.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].account | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/coded"}]} |
| response.data.items[].account | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].account | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.items[].account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].partner | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].label | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].amount_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["fixed","percentage","percentage_st_line","regex"]} |
| response.data.items[].amount | string | 必填（所在对象出现时） | allOf[1]/then | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_string | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].taxes | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.items[].taxes[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].taxes[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].taxes[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].analytic_distribution | array | 必填（所在对象出现时） | allOf[1]/then | 分析分摊映射；写入与读回约束可能不同 | {"maxItems":1000,"uniqueItems":true} |
| response.data.items[].analytic_distribution[] | object | 每个数组元素 | allOf[1]/then | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":false,"required_in_object":["analytic_accounts","percentage"],"resolved_ref":"#/$defs/analytic_distribution"} |
| response.data.items[].analytic_distribution[].analytic_accounts | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000,"minItems":1,"uniqueItems":true} |
| response.data.items[].analytic_distribution[].analytic_accounts[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].analytic_distribution[].analytic_accounts[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].analytic_distribution[].analytic_accounts[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].analytic_distribution[].percentage | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[1]/then | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[1]/then | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | allOf[1]/then/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_company_scoped_core_object_read_action
- `verify`：same_transaction_acl_result_cursor_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the closed request and response schemas, registry metadata, CLI handler, validator, model, and audit routing.；引用：tests/unit/test_accounting_reference_read_registry.py
- `integration`：`implemented`；The shared live read-only smoke verifies the capability against both dedicated isolated database aliases without database changes.；引用：tests/integration/test_accounting_reference_read_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-model-line-update"></a>

## reconciliation.model.line.update — 修改对账规则行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured caller/company and native ACLs. Edits fixed rule fields/lines, not posted journal amounts. Copy uses native copy with new child IDs; usage lists are scoped ORM reads of reconcile_model_id. Follow-up assignment only changes configuration; it schedules no activity. Numeric rule percentages follow native nonzero signed constraints, not an invented 0-100 ceiling. Serial line creation matches one full native payload; ambiguity conflicts. Delete missing targets remain record_not_found, never a fabricated successful replay. Native model deletion cascades rule lines and can clear historical reconcile_model_id links; no bank/provider call, mail delivery, arbitrary methods or caller-sudo.
- 内部domain：`reconciliation`；来源模型：account.account, account.analytic.account, account.reconcile.model, account.reconcile.model.line, account.tax, res.company, res.partner；向导：无。
- 必需模块：account, base, mail；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.account:read, account.analytic.account:read, account.reconcile.model.line:read, account.reconcile.model.line:write, account.reconcile.model:read, account.tax:read, res.company:read, res.partner:read。
- 请求/响应合同：`schemas/v1/reconciliation.model.line.update.request.schema.json` / `schemas/v1/reconciliation.model.line.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run reconciliation.model.line.update --request "@request.json" --idempotency-key "reconciliation.model.line.update:1:244e5dba147f0cb33389e1d5c2da1629" --confirm "reconciliation.model.line.update"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "changes": {
      "sequence": 1
    },
    "line_id": 1,
    "reconciliation_model_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["changes","line_id","reconciliation_model_id"]} |
| parameters.reconciliation_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"allOf":[{"if":{"properties":{"amount_type":{"enum":["fixed","percentage","percentage_st_line"]}},"required":["amount_type"]},"then":{"properties":{"amount_string":{"maxLength":256,"pattern":"^(?!-?0(?:\\.0+)?$(?![\\s\\S]))-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","type":"string"}}}}],"minProperties":1,"required_in_object":[]} |
| parameters.changes.sequence | integer | 可选（可能有条件限制） |  |  | {"maximum":2147483647,"minimum":-2147483648} |
| parameters.changes.account_id | integer/null | 可选（可能有条件限制） |  | 会计科目ID | {"minimum":1} |
| parameters.changes.partner_id | integer/null | 可选（可能有条件限制） |  | 合作伙伴ID | {"minimum":1} |
| parameters.changes.label | string/null | 可选（可能有条件限制） |  |  | {"maxLength":500,"minLength":1} |
| parameters.changes.amount_type | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["fixed","percentage","percentage_st_line","regex"]} |
| parameters.changes.amount_string | string | 可选（可能有条件限制） |  |  | {"maxLength":500,"minLength":1} |
| parameters.changes.tax_ids | array | 可选（可能有条件限制） |  | 应用税ID数组 | {"maxItems":100,"uniqueItems":true} |
| parameters.changes.tax_ids[] | integer | 每个数组元素 |  | 应用税ID数组 | {"minimum":1} |
| parameters.changes.analytic_distribution | array | 可选（可能有条件限制） |  | 分析分摊映射；写入与读回约束可能不同 | {"maxItems":16} |
| parameters.changes.analytic_distribution[] | object | 每个数组元素 |  | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":false,"required_in_object":["analytic_account_ids","percentage"]} |
| parameters.changes.analytic_distribution[].analytic_account_ids | array | 必填（所在对象出现时） |  |  | {"maxItems":16,"minItems":1,"uniqueItems":true} |
| parameters.changes.analytic_distribution[].analytic_account_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.changes.analytic_distribution[].percentage | string | 必填（所在对象出现时） |  |  | {"maxLength":256,"pattern":"^(?:(?:[1-9][0-9]?)(?:\\.[0-9]{1,4})?&#124;0\\.(?=[0-9]*[1-9])[0-9]{1,4}&#124;100(?:\\.0{1,4})?)$(?![\\s\\S])"} |
| parameters.changes | 组合/开放结构 | 分支约束 | allOf[1] | 仅提交拟变更字段，非整条记录 | {"if":{"properties":{"amount_type":{"enum":["fixed","percentage","percentage_st_line"]}},"required":["amount_type"]},"then":{"properties":{"amount_string":{"maxLength":256,"pattern":"^(?!-?0(?:\\.0+)?$(?![\\s\\S]))-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","type":"string"}}}} |
| parameters.changes | 未限定 | 条件分支 | allOf[1]/then | 仅提交拟变更字段，非整条记录 |  |
| parameters.changes.amount_string | string | 可选（可能有条件限制） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?!-?0(?:\\.0+)?$(?![\\s\\S]))-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"reconciliation.model.line.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"reconciliation.model.line.update"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_native_rule_fields_copy_or_unlink
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：serial_native_payload_match_or_missing_target_denial
- `reverse`：previous_values_or_native_backup_restore_subject_to_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Closed contracts, fixed CLI/ORM routing, child ownership, native numeric/regex shapes, ACL denial and serial payload replay.；引用：tests/unit/test_reconciliation_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all nine new IDs, two existing setup IDs and eleven immediate replays; native computed partner mapping, signed amounts above 100 percent and regex, native line IDs and complete ordering, tax/analytic configuration copy and clearing, activity configuration without scheduling, scoped usage ID-keyset reads including archived rules, actual child deletion and used-rule cascade/usage-link clearing with posted amounts unchanged. Foreign-company, wrong-parent, incomplete ordering, invalid regex/activity model, changed-source copy conflicts and missing targets denied. Fresh-cursor business-data and temporary-group rollback verified. No actual bank reconciliation, external notification, addon or service changes.；引用：tests/integration/test_reconciliation_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-model-lines-replace"></a>

## reconciliation.model.lines.replace — 替换对账模型行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, model, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, res.partner, account.account, account.tax, account.analytic.account, account.reconcile.model, account.reconcile.model.line；向导：无。
- 必需模块：account, account_accountant, analytic, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, res.partner:read, account.account:read, account.tax:read, account.analytic.account:read, account.reconcile.model:read, account.reconcile.model:write, account.reconcile.model.line:read, account.reconcile.model.line:create, account.reconcile.model.line:write, account.reconcile.model.line:unlink。
- 请求/响应合同：`schemas/v1/reconciliation.model.lines.replace.request.schema.json` / `schemas/v1/reconciliation.model.lines.replace.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run reconciliation.model.lines.replace --request "@request.json" --idempotency-key "reconciliation.model.lines.replace:1:4f53cda18c2baa0c0354bb5f9a3ecbe5" --confirm "reconciliation.model.lines.replace"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "reconciliation_model_id": 1,
    "lines": []
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["reconciliation_model_id","lines"]} |
| parameters.reconciliation_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.lines | array | 必填（所在对象出现时） |  | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":100} |
| parameters.lines[] | object | 每个数组元素 |  | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"allOf":[{"if":{"properties":{"amount_type":{"const":"percentage"}},"required":["amount_type"]},"then":{"properties":{"amount_string":{"$ref":"#/$defs/balance_percentage"}}}},{"if":{"properties":{"amount_type":{"enum":["fixed","percentage_st_line"]}},"required":["amount_type"]},"then":{"properties":{"amount_string":{"$ref":"#/$defs/nonzero_signed_decimal"}}}}],"required_in_object":["sequence","account_id","partner_id","label","amount_type","amount_string","tax_ids"],"resolved_ref":"#/$defs/line"} |
| parameters.lines[].sequence | integer | 必填（所在对象出现时） |  |  | {"minimum":0} |
| parameters.lines[].account_id | integer/null | 必填（所在对象出现时） |  | 会计科目ID | {"minimum":1} |
| parameters.lines[].partner_id | integer/null | 必填（所在对象出现时） |  | 合作伙伴ID | {"minimum":1} |
| parameters.lines[].label | string/null | 必填（所在对象出现时） |  |  | {"maxLength":500,"minLength":1} |
| parameters.lines[].amount_type | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["fixed","percentage","percentage_st_line","regex"]} |
| parameters.lines[].amount_string | string | 必填（所在对象出现时） |  |  | {"maxLength":500,"minLength":1} |
| parameters.lines[].tax_ids | array | 必填（所在对象出现时） |  | 应用税ID数组 | {"uniqueItems":true} |
| parameters.lines[].tax_ids[] | integer | 每个数组元素 |  | 应用税ID数组 | {"minimum":1} |
| parameters.lines[].analytic_distribution | array | 可选（可能有条件限制） |  | 分析分摊映射；写入与读回约束可能不同 | {"maxItems":16,"minItems":1} |
| parameters.lines[].analytic_distribution[] | object | 每个数组元素 |  | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":false,"required_in_object":["analytic_account_ids","percentage"],"resolved_ref":"#/$defs/analytic_entry"} |
| parameters.lines[].analytic_distribution[].analytic_account_ids | array | 必填（所在对象出现时） |  |  | {"maxItems":16,"minItems":1,"uniqueItems":true} |
| parameters.lines[].analytic_distribution[].analytic_account_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.lines[].analytic_distribution[].percentage | string | 必填（所在对象出现时） |  |  | {"maxLength":256,"pattern":"^(?:100&#124;[1-9][0-9]?&#124;(?:0&#124;[1-9][0-9])\\.[0-9]{0,3}[1-9])$"} |
| parameters.lines[] | 组合/开放结构 | 分支约束 | allOf[1] | 行数组；增补/更新/替换语义由能力ID决定 | {"if":{"properties":{"amount_type":{"const":"percentage"}},"required":["amount_type"]},"then":{"properties":{"amount_string":{"$ref":"#/$defs/balance_percentage"}}}} |
| parameters.lines[] | 未限定 | 条件分支 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| parameters.lines[].amount_string | string | 可选（可能有条件限制） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:100&#124;[1-9][0-9]?&#124;(?:0&#124;[1-9][0-9])\\.[0-9]*[1-9])$","resolved_ref":"#/$defs/balance_percentage"} |
| parameters.lines[] | 组合/开放结构 | 分支约束 | allOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"if":{"properties":{"amount_type":{"enum":["fixed","percentage_st_line"]}},"required":["amount_type"]},"then":{"properties":{"amount_string":{"$ref":"#/$defs/nonzero_signed_decimal"}}}} |
| parameters.lines[] | 未限定 | 条件分支 | allOf[2]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| parameters.lines[].amount_string | string | 可选（可能有条件限制） | allOf[2]/then |  | {"maxLength":256,"pattern":"^-?(?:[1-9][0-9]*&#124;(?:0&#124;[1-9][0-9]*)\\.[0-9]*[1-9])$","resolved_ref":"#/$defs/nonzero_signed_decimal"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"reconciliation.model.lines.replace"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"reconciliation.model.lines.replace"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_reconciliation_model_line_one2many_replacement
- `verify`：same_transaction_order_account_partner_amount_tax_and_analytic_reread
- `idempotency`：full_normalized_line_target_recheck_without_operation_store
- `reverse`：repeat_with_previous_reconciliation_model_lines

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed line contract, company-scoped references, amount and analytic normalization, manager ACL, replacement replay, schemas, registry metadata, and CLI dispatch.；引用：tests/unit/test_core_writes.py, tests/unit/test_accounting_configuration_write_contracts.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_accounting_configuration_expansion_registry.py
- `integration`：`implemented`；The guarded shared transactional smoke verifies first execution, immediate deterministic replay, and rollback against both dedicated isolated databases.；引用：tests/integration/test_accounting_configuration_expansion_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-model-lines-resequence"></a>

## reconciliation.model.lines.resequence — 重排对账规则行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured caller/company and native ACLs. Edits fixed rule fields/lines, not posted journal amounts. Copy uses native copy with new child IDs; usage lists are scoped ORM reads of reconcile_model_id. Follow-up assignment only changes configuration; it schedules no activity. Numeric rule percentages follow native nonzero signed constraints, not an invented 0-100 ceiling. Serial line creation matches one full native payload; ambiguity conflicts. Delete missing targets remain record_not_found, never a fabricated successful replay. Native model deletion cascades rule lines and can clear historical reconcile_model_id links; no bank/provider call, mail delivery, arbitrary methods or caller-sudo.
- 内部domain：`reconciliation`；来源模型：account.reconcile.model, account.reconcile.model.line, res.company；向导：无。
- 必需模块：account, base, mail；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.reconcile.model.line:read, account.reconcile.model.line:write, account.reconcile.model:read, res.company:read。
- 请求/响应合同：`schemas/v1/reconciliation.model.lines.resequence.request.schema.json` / `schemas/v1/reconciliation.model.lines.resequence.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run reconciliation.model.lines.resequence --request "@request.json" --idempotency-key "reconciliation.model.lines.resequence:1:cab5d150bf98e69340317f8187f248f3" --confirm "reconciliation.model.lines.resequence"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "line_ids": [],
    "reconciliation_model_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["line_ids","reconciliation_model_id"]} |
| parameters.reconciliation_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.line_ids | array | 必填（所在对象出现时） |  | 行记录ID数组 | {"maxItems":500,"uniqueItems":true} |
| parameters.line_ids[] | integer | 每个数组元素 |  | 行记录ID数组 | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"reconciliation.model.lines.resequence"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"reconciliation.model.lines.resequence"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_native_rule_fields_copy_or_unlink
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：serial_native_payload_match_or_missing_target_denial
- `reverse`：previous_values_or_native_backup_restore_subject_to_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Closed contracts, fixed CLI/ORM routing, child ownership, native numeric/regex shapes, ACL denial and serial payload replay.；引用：tests/unit/test_reconciliation_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all nine new IDs, two existing setup IDs and eleven immediate replays; native computed partner mapping, signed amounts above 100 percent and regex, native line IDs and complete ordering, tax/analytic configuration copy and clearing, activity configuration without scheduling, scoped usage ID-keyset reads including archived rules, actual child deletion and used-rule cascade/usage-link clearing with posted amounts unchanged. Foreign-company, wrong-parent, incomplete ordering, invalid regex/activity model, changed-source copy conflicts and missing targets denied. Fresh-cursor business-data and temporary-group rollback verified. No actual bank reconciliation, external notification, addon or service changes.；引用：tests/integration/test_reconciliation_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-model-list"></a>

## reconciliation.model.list — 列出对账模型

- 类型：只读；静态状态：`unconfigured`；handler：`reconciliation_model_list`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.reconcile.model；向导：无。
- 必需模块：account, account_accountant；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.reconcile.model:read。
- 请求/响应合同：`schemas/v1/reconciliation.model.list.request.schema.json` / `schemas/v1/reconciliation.model.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read reconciliation.model.list --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {}
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"resolved_ref":"#/$defs/parameters"} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"reconciliation.model.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","sequence","active","company_id","match_amount","match_amount_min","match_amount_max","match_label","match_label_param"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].sequence | integer | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].match_amount | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.items[].match_amount | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].match_amount | string | 分支约束 | oneOf[2]/oneOf[2] |  |  |
| response.data.items[].match_amount_min | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].match_amount_max | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].match_label | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.items[].match_label | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].match_label | string | 分支约束 | oneOf[2]/oneOf[2] |  |  |
| response.data.items[].match_label_param | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.items[].match_label_param | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].match_label_param | string | 分支约束 | oneOf[2]/oneOf[2] |  |  |
| response.data.has_more | boolean | 必填（所在对象出现时） | oneOf[2] | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | oneOf[2] | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2]/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | oneOf[2]/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | oneOf[2]/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | oneOf[2]/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | oneOf[2]/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | oneOf[2]/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","sequence","active","company_id","match_amount","match_amount_min","match_amount_max","match_label","match_label_param"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].sequence | integer | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].match_amount | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.items[].match_amount | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].match_amount | string | 分支约束 | allOf[1]/then/oneOf[2] |  |  |
| response.data.items[].match_amount_min | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].match_amount_max | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].match_label | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.items[].match_label | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].match_label | string | 分支约束 | allOf[1]/then/oneOf[2] |  |  |
| response.data.items[].match_label_param | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.items[].match_label_param | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].match_label_param | string | 分支约束 | allOf[1]/then/oneOf[2] |  |  |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[1]/then | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[1]/then | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | allOf[1]/then/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_company_scoped_core_object_read_action
- `verify`：same_transaction_acl_result_cursor_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request and response, cursor binding, fixed bridge action, company scope, ACL gates, ORM normalization, and CLI dispatch.；引用：tests/unit/test_core_object_reads.py, tests/unit/test_core_object_reads_bridge.py, tests/unit/test_core_object_reads_runtime.py, tests/unit/test_core_object_read_cli.py
- `integration`：`implemented`；The shared live read-only smoke verifies the capability against both dedicated isolated database aliases as the ordinary accounting user.；引用：tests/integration/test_core_object_read_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-model-processing_settings-get"></a>

## reconciliation.model.processing_settings.get — 读取对账规则原生处理状态

- 类型：只读；静态状态：`unconfigured`；handler：`reconciliation_model_processing_settings_get`。
- 状态原因：`runtime_context_required` — Requires configured caller/company and native ACLs. Edits fixed rule fields/lines, not posted journal amounts. Copy uses native copy with new child IDs; usage lists are scoped ORM reads of reconcile_model_id. Follow-up assignment only changes configuration; it schedules no activity. Numeric rule percentages follow native nonzero signed constraints, not an invented 0-100 ceiling. Serial line creation matches one full native payload; ambiguity conflicts. Delete missing targets remain record_not_found, never a fabricated successful replay. Native model deletion cascades rule lines and can clear historical reconcile_model_id links; no bank/provider call, mail delivery, arbitrary methods or caller-sudo.
- 内部domain：`reconciliation`；来源模型：res.company, account.reconcile.model, account.reconcile.model.line, res.partner, mail.activity.type；向导：无。
- 必需模块：account, base, mail；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.reconcile.model:read, account.reconcile.model.line:read, res.partner:read, mail.activity.type:read。
- 请求/响应合同：`schemas/v1/reconciliation.model.processing_settings.get.request.schema.json` / `schemas/v1/reconciliation.model.processing_settings.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read reconciliation.model.processing_settings.get --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "reconciliation_model_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["reconciliation_model_id"]} |
| parameters.reconciliation_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"reconciliation.model.processing_settings.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["active","can_be_proposed","company_id","id","line_ids","mapped_partner_id","name","next_activity_type_id","trigger"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 |  |
| response.data.active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.trigger | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["manual","auto_reconcile"]} |
| response.data.can_be_proposed | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.mapped_partner_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.next_activity_type_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.line_ids | array | 必填（所在对象出现时） | oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.line_ids[] | integer | 每个数组元素 | oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["active","can_be_proposed","company_id","id","line_ids","mapped_partner_id","name","next_activity_type_id","trigger"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 |  |
| response.data.active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.trigger | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["manual","auto_reconcile"]} |
| response.data.can_be_proposed | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.mapped_partner_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.next_activity_type_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.line_ids | array | 必填（所在对象出现时） | allOf[1]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.line_ids[] | integer | 每个数组元素 | allOf[1]/then | 行记录ID数组 | {"minimum":1} |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：request_schema_validation
- `execute`：fixed_native_rule_read
- `verify`：closed_response_schema_validation
- `idempotency`：read_only
- `reverse`：not_applicable

### 已登记测试与证据范围

- `unit`：`implemented`；Closed contracts, fixed CLI/ORM routing, child ownership, native numeric/regex shapes, ACL denial and serial payload replay.；引用：tests/unit/test_reconciliation_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all nine new IDs, two existing setup IDs and eleven immediate replays; native computed partner mapping, signed amounts above 100 percent and regex, native line IDs and complete ordering, tax/analytic configuration copy and clearing, activity configuration without scheduling, scoped usage ID-keyset reads including archived rules, actual child deletion and used-rule cascade/usage-link clearing with posted amounts unchanged. Foreign-company, wrong-parent, incomplete ordering, invalid regex/activity model, changed-source copy conflicts and missing targets denied. Fresh-cursor business-data and temporary-group rollback verified. No actual bank reconciliation, external notification, addon or service changes.；引用：tests/integration/test_reconciliation_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-model-restore"></a>

## reconciliation.model.restore — 恢复对账模型

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.reconcile.model；向导：无。
- 必需模块：account, account_accountant, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.reconcile.model:read, account.reconcile.model:write。
- 请求/响应合同：`schemas/v1/reconciliation.model.restore.request.schema.json` / `schemas/v1/reconciliation.model.restore.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run reconciliation.model.restore --request "@request.json" --idempotency-key "reconciliation.model.restore:1" --confirm "reconciliation.model.restore"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "reconciliation_model_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["reconciliation_model_id"]} |
| parameters.reconciliation_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"reconciliation.model.restore"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"reconciliation.model.restore"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_company_reconciliation_model_restore
- `verify`：same_transaction_active_state_reread
- `idempotency`：target_active_state_recheck_without_operation_store
- `reverse`：reconciliation.model.archive

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed identifier contract, company ownership, manager ACL, target-state replay, schemas, registry metadata, and CLI dispatch.；引用：tests/unit/test_core_writes.py, tests/unit/test_accounting_configuration_write_contracts.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_accounting_configuration_expansion_registry.py
- `integration`：`implemented`；The guarded shared transactional smoke verifies first execution, immediate deterministic replay, and rollback against both dedicated isolated databases.；引用：tests/integration/test_accounting_configuration_expansion_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-model-update"></a>

## reconciliation.model.update — 更新对账模型

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, res.partner, account.journal, account.reconcile.model；向导：无。
- 必需模块：account, account_accountant, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, res.partner:read, account.journal:read, account.reconcile.model:read, account.reconcile.model:write。
- 请求/响应合同：`schemas/v1/reconciliation.model.update.request.schema.json` / `schemas/v1/reconciliation.model.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run reconciliation.model.update --request "@request.json" --idempotency-key "reconciliation.model.update:1:663c40c5fc625d44d00a597ae77ce292" --confirm "reconciliation.model.update"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "reconciliation_model_id": 1,
    "changes": {
      "name": "Example"
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["reconciliation_model_id","changes"]} |
| parameters.reconciliation_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.name | string | 可选（可能有条件限制） |  | 名称/行说明 | {"maxLength":256,"minLength":1} |
| parameters.changes.sequence | integer | 可选（可能有条件限制） |  |  | {"minimum":0} |
| parameters.changes.trigger | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["manual","auto_reconcile"]} |
| parameters.changes.match_journal_ids | array | 可选（可能有条件限制） |  |  | {"resolved_ref":"#/$defs/positive_ids","uniqueItems":true} |
| parameters.changes.match_journal_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.changes.match_partner_ids | array | 可选（可能有条件限制） |  |  | {"resolved_ref":"#/$defs/positive_ids","uniqueItems":true} |
| parameters.changes.match_partner_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.changes.match_amount | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"oneOf":[{"type":"null"},{"additionalProperties":false,"properties":{"maximum":{"$ref":"#/$defs/nonnegative_decimal"},"minimum":{"type":"null"},"operator":{"const":"lower"}},"required":["operator","minimum","maximum"],"type":"object"},{"additionalProperties":false,"properties":{"maximum":{"type":"null"},"minimum":{"$ref":"#/$defs/nonnegative_decimal"},"operator":{"const":"greater"}},"required":["operator","minimum","maximum"],"type":"object"},{"additionalProperties":false,"properties":{"maximum":{"$ref":"#/$defs/nonnegative_decimal"},"minimum":{"$ref":"#/$defs/nonnegative_decimal"},"operator":{"const":"between"}},"required":["operator","minimum","maximum"],"type":"object"}],"resolved_ref":"#/$defs/match_amount"} |
| parameters.changes.match_amount | null | 分支约束 | oneOf[1] |  |  |
| parameters.changes.match_amount | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["operator","minimum","maximum"]} |
| parameters.changes.match_amount.operator | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":"lower"} |
| parameters.changes.match_amount.minimum | null | 必填（所在对象出现时） | oneOf[2] |  |  |
| parameters.changes.match_amount.maximum | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*&#124;(?:0&#124;[1-9][0-9]*)\\.[0-9]*[1-9])$","resolved_ref":"#/$defs/nonnegative_decimal"} |
| parameters.changes.match_amount | object | 分支约束 | oneOf[3] |  | {"additionalProperties":false,"required_in_object":["operator","minimum","maximum"]} |
| parameters.changes.match_amount.operator | 未限定 | 必填（所在对象出现时） | oneOf[3] |  | {"const":"greater"} |
| parameters.changes.match_amount.minimum | string | 必填（所在对象出现时） | oneOf[3] |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*&#124;(?:0&#124;[1-9][0-9]*)\\.[0-9]*[1-9])$","resolved_ref":"#/$defs/nonnegative_decimal"} |
| parameters.changes.match_amount.maximum | null | 必填（所在对象出现时） | oneOf[3] |  |  |
| parameters.changes.match_amount | object | 分支约束 | oneOf[4] |  | {"additionalProperties":false,"required_in_object":["operator","minimum","maximum"]} |
| parameters.changes.match_amount.operator | 未限定 | 必填（所在对象出现时） | oneOf[4] |  | {"const":"between"} |
| parameters.changes.match_amount.minimum | string | 必填（所在对象出现时） | oneOf[4] |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*&#124;(?:0&#124;[1-9][0-9]*)\\.[0-9]*[1-9])$","resolved_ref":"#/$defs/nonnegative_decimal"} |
| parameters.changes.match_amount.maximum | string | 必填（所在对象出现时） | oneOf[4] |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*&#124;(?:0&#124;[1-9][0-9]*)\\.[0-9]*[1-9])$","resolved_ref":"#/$defs/nonnegative_decimal"} |
| parameters.changes.match_label | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"oneOf":[{"type":"null"},{"additionalProperties":false,"properties":{"operator":{"enum":["contains","not_contains","match_regex"]},"value":{"maxLength":500,"minLength":1,"type":"string"}},"required":["operator","value"],"type":"object"}],"resolved_ref":"#/$defs/match_label"} |
| parameters.changes.match_label | null | 分支约束 | oneOf[1] |  |  |
| parameters.changes.match_label | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["operator","value"]} |
| parameters.changes.match_label.operator | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["contains","not_contains","match_regex"]} |
| parameters.changes.match_label.value | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":500,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"reconciliation.model.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"reconciliation.model.update"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_company_reconciliation_model_update
- `verify`：same_transaction_header_match_criteria_and_response_schema_validation
- `idempotency`：target_model_state_recheck_without_operation_store
- `reverse`：repeat_update_with_previous_values

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed patch contract, company-scoped references, match criteria, manager ACL, replay, schemas, registry metadata, and CLI dispatch.；引用：tests/unit/test_core_writes.py, tests/unit/test_accounting_configuration_write_contracts.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_accounting_configuration_expansion_registry.py
- `integration`：`implemented`；The guarded shared transactional smoke verifies first execution, immediate deterministic replay, and rollback against both dedicated isolated databases.；引用：tests/integration/test_accounting_configuration_expansion_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-model-usage_lines-list"></a>

## reconciliation.model.usage_lines.list — 查询对账规则使用明细

- 类型：只读；静态状态：`unconfigured`；handler：`reconciliation_model_usage_lines_list`。
- 状态原因：`runtime_context_required` — Requires configured caller/company and native ACLs. Edits fixed rule fields/lines, not posted journal amounts. Copy uses native copy with new child IDs; usage lists are scoped ORM reads of reconcile_model_id. Follow-up assignment only changes configuration; it schedules no activity. Numeric rule percentages follow native nonzero signed constraints, not an invented 0-100 ceiling. Serial line creation matches one full native payload; ambiguity conflicts. Delete missing targets remain record_not_found, never a fabricated successful replay. Native model deletion cascades rule lines and can clear historical reconcile_model_id links; no bank/provider call, mail delivery, arbitrary methods or caller-sudo.
- 内部domain：`reconciliation`；来源模型：res.company, account.reconcile.model, account.move.line, account.move, account.account, res.partner, res.currency；向导：无。
- 必需模块：account, base, mail；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.reconcile.model:read, account.move.line:read, account.move:read, account.account:read, res.partner:read, res.currency:read。
- 请求/响应合同：`schemas/v1/reconciliation.model.usage_lines.list.request.schema.json` / `schemas/v1/reconciliation.model.usage_lines.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read reconciliation.model.usage_lines.list --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "reconciliation_model_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["reconciliation_model_id"]} |
| parameters.reconciliation_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"reconciliation.model.usage_lines.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["account_id","amount_currency","balance","company_id","credit","currency_id","date","debit","id","move_id","name","partner_id","reconcile_model_id"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].reconcile_model_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].move_id | integer | 必填（所在对象出现时） | oneOf[2] | 会计单据记录ID | {"minimum":1} |
| response.data.items[].account_id | integer | 必填（所在对象出现时） | oneOf[2] | 会计科目ID | {"minimum":1} |
| response.data.items[].currency_id | integer | 必填（所在对象出现时） | oneOf[2] | 币种ID | {"minimum":1} |
| response.data.items[].partner_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 合作伙伴ID | {"minimum":1} |
| response.data.items[].name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 |  |
| response.data.items[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].debit | string | 必填（所在对象出现时） | oneOf[2] | 借方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.items[].credit | string | 必填（所在对象出现时） | oneOf[2] | 贷方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.items[].balance | string | 必填（所在对象出现时） | oneOf[2] | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.items[].amount_currency | string | 必填（所在对象出现时） | oneOf[2] | 外币/交易币数值，非默认公司币金额 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.has_more | boolean | 必填（所在对象出现时） | oneOf[2] | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | oneOf[2] | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2]/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | oneOf[2]/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | oneOf[2]/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | oneOf[2]/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | oneOf[2]/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | oneOf[2]/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["account_id","amount_currency","balance","company_id","credit","currency_id","date","debit","id","move_id","name","partner_id","reconcile_model_id"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].reconcile_model_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].move_id | integer | 必填（所在对象出现时） | allOf[1]/then | 会计单据记录ID | {"minimum":1} |
| response.data.items[].account_id | integer | 必填（所在对象出现时） | allOf[1]/then | 会计科目ID | {"minimum":1} |
| response.data.items[].currency_id | integer | 必填（所在对象出现时） | allOf[1]/then | 币种ID | {"minimum":1} |
| response.data.items[].partner_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 合作伙伴ID | {"minimum":1} |
| response.data.items[].name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 |  |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].debit | string | 必填（所在对象出现时） | allOf[1]/then | 借方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.items[].credit | string | 必填（所在对象出现时） | allOf[1]/then | 贷方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.items[].balance | string | 必填（所在对象出现时） | allOf[1]/then | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.items[].amount_currency | string | 必填（所在对象出现时） | allOf[1]/then | 外币/交易币数值，非默认公司币金额 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[1]/then | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[1]/then | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | allOf[1]/then/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：request_schema_validation
- `execute`：fixed_native_rule_read
- `verify`：closed_response_schema_validation
- `idempotency`：read_only
- `reverse`：not_applicable

### 已登记测试与证据范围

- `unit`：`implemented`；Closed contracts, fixed CLI/ORM routing, child ownership, native numeric/regex shapes, ACL denial and serial payload replay.；引用：tests/unit/test_reconciliation_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all nine new IDs, two existing setup IDs and eleven immediate replays; native computed partner mapping, signed amounts above 100 percent and regex, native line IDs and complete ordering, tax/analytic configuration copy and clearing, activity configuration without scheduling, scoped usage ID-keyset reads including archived rules, actual child deletion and used-rule cascade/usage-link clearing with posted amounts unchanged. Foreign-company, wrong-parent, incomplete ordering, invalid regex/activity model, changed-source copy conflicts and missing targets denied. Fresh-cursor business-data and temporary-group rollback verified. No actual bank reconciliation, external notification, addon or service changes.；引用：tests/integration/test_reconciliation_processing_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-partial-get"></a>

## reconciliation.partial.get — 获取部分核销详情

- 类型：只读；静态状态：`unconfigured`；handler：`reconciliation_partial_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.partial.reconcile, account.move.line, account.move, res.currency；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.partial.reconcile:read, account.move.line:read, account.move:read, res.currency:read。
- 请求/响应合同：`schemas/v1/reconciliation.partial.get.request.schema.json` / `schemas/v1/reconciliation.partial.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read reconciliation.partial.get --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "partial_reconcile_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["partial_reconcile_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.partial_reconcile_id | integer | 必填（所在对象出现时） |  | 部分核销关系ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"reconciliation.partial.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"reconciliation.partial.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"reconciliation.partial.list.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","max_date","amount","company_currency","debit_amount_currency","debit_currency","credit_amount_currency","credit_currency","debit_journal_item_id","credit_journal_item_id","full_reconcile_id","exchange_move_id","matching_number"],"resolved_ref":"reconciliation.partial.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.max_date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.amount | string | 必填（所在对象出现时） | oneOf[2] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.company_currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.company_currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.debit_amount_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.debit_currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.debit_currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.debit_currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.credit_amount_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.credit_currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.credit_currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.credit_currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.debit_journal_item_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.credit_journal_item_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.full_reconcile_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.exchange_move_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.matching_number | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"reconciliation.partial.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","max_date","amount","company_currency","debit_amount_currency","debit_currency","credit_amount_currency","credit_currency","debit_journal_item_id","credit_journal_item_id","full_reconcile_id","exchange_move_id","matching_number"],"resolved_ref":"reconciliation.partial.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.max_date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.amount | string | 必填（所在对象出现时） | allOf[1]/then | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.company_currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.company_currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.debit_amount_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.debit_currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.debit_currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.debit_currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.credit_amount_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.credit_currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.credit_currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.credit_currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.debit_journal_item_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.credit_journal_item_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 完整核销关系ID | {"minimum":1} |
| response.data.exchange_move_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.matching_number | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_company_scoped_core_object_read_action
- `verify`：same_transaction_acl_result_cursor_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request and response, fixed bridge action, company scope, ACL gates, ORM normalization, pagination where applicable, and CLI dispatch.；引用：tests/unit/test_core_object_reads.py, tests/unit/test_core_object_reads_bridge.py, tests/unit/test_core_object_reads_runtime.py, tests/unit/test_core_object_read_cli.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The shared live read-only smoke verifies the capability against both dedicated isolated database aliases as the ordinary accounting user.；引用：tests/integration/test_payment_reconciliation_read_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-partial-list"></a>

## reconciliation.partial.list — 列出部分核销

- 类型：只读；静态状态：`unconfigured`；handler：`reconciliation_partial_list`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.partial.reconcile, account.move.line, account.move, res.currency；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.partial.reconcile:read, account.move.line:read, account.move:read, res.currency:read。
- 请求/响应合同：`schemas/v1/reconciliation.partial.list.request.schema.json` / `schemas/v1/reconciliation.partial.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read reconciliation.partial.list --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {}
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"resolved_ref":"#/$defs/parameters"} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"reconciliation.partial.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","max_date","amount","company_currency","debit_amount_currency","debit_currency","credit_amount_currency","credit_currency","debit_journal_item_id","credit_journal_item_id","full_reconcile_id","exchange_move_id","matching_number"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].max_date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].amount | string | 必填（所在对象出现时） | oneOf[2] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].company_currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].company_currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].debit_amount_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].debit_currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].debit_currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].debit_currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].credit_amount_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].credit_currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].credit_currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].credit_currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].debit_journal_item_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].credit_journal_item_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].full_reconcile_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.items[].exchange_move_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].matching_number | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.has_more | boolean | 必填（所在对象出现时） | oneOf[2] | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | oneOf[2] | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2]/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | oneOf[2]/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | oneOf[2]/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | oneOf[2]/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | oneOf[2]/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | oneOf[2]/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","max_date","amount","company_currency","debit_amount_currency","debit_currency","credit_amount_currency","credit_currency","debit_journal_item_id","credit_journal_item_id","full_reconcile_id","exchange_move_id","matching_number"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].max_date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].amount | string | 必填（所在对象出现时） | allOf[1]/then | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].company_currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].company_currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].debit_amount_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].debit_currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].debit_currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].debit_currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].credit_amount_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].credit_currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].credit_currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].credit_currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].debit_journal_item_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].credit_journal_item_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 完整核销关系ID | {"minimum":1} |
| response.data.items[].exchange_move_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].matching_number | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[1]/then | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[1]/then | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | allOf[1]/then/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_company_scoped_core_object_read_action
- `verify`：same_transaction_acl_result_cursor_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request and response, fixed bridge action, company scope, ACL gates, ORM normalization, pagination where applicable, and CLI dispatch.；引用：tests/unit/test_core_object_reads.py, tests/unit/test_core_object_reads_bridge.py, tests/unit/test_core_object_reads_runtime.py, tests/unit/test_core_object_read_cli.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The shared live read-only smoke verifies the capability against both dedicated isolated database aliases as the ordinary accounting user.；引用：tests/integration/test_payment_reconciliation_read_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-undo"></a>

## reconciliation.undo — 反核销会计项目

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：account.account, account.analytic.account, account.analytic.line, account.full.reconcile, account.journal, account.move, account.move.line, account.partial.reconcile, account.payment, account.tax, res.company, res.currency, res.currency.rate, res.partner；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.account:read, account.analytic.account:read, account.analytic.line:create, account.analytic.line:read, account.analytic.line:unlink, account.full.reconcile:create, account.full.reconcile:read, account.full.reconcile:unlink, account.journal:read, account.move.line:create, account.move.line:read, account.move.line:unlink, account.move.line:write, account.move:create, account.move:read, account.move:unlink, account.move:write, account.partial.reconcile:create, account.partial.reconcile:read, account.partial.reconcile:unlink, account.payment:read, account.payment:write, account.tax:read, res.currency.rate:read, res.currency:read, res.partner:read。
- 请求/响应合同：`schemas/v1/reconciliation.undo.request.schema.json` / `schemas/v1/reconciliation.undo.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run reconciliation.undo --request "@request.json" --idempotency-key "reconciliation.undo:1:2" --confirm "reconciliation.undo"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "line_ids": [
      1,
      2
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  |  |
| parameters | 组合/开放结构 | 必填 |  |  | {"oneOf":[{"additionalProperties":false,"properties":{"line_ids":{"items":{"minimum":1,"type":"integer"},"maxItems":2,"minItems":2,"type":"array","uniqueItems":true}},"required":["line_ids"],"type":"object"},{"additionalProperties":false,"properties":{"counterpart_line_id":{"minimum":1,"type":"integer"},"invoice_id":{"minimum":1,"type":"integer"},"invoice_line_id":{"minimum":1,"type":"integer"},"partial_reconcile_id":{"minimum":1,"type":"integer"}},"required":["invoice_id","partial_reconcile_id","invoice_line_id","counterpart_line_id"],"type":"object"},{"additionalProperties":false,"properties":{"line_ids":{"items":{"minimum":1,"type":"integer"},"maxItems":100,"minItems":1,"type":"array","uniqueItems":true},"mode":{"const":"match_group"}},"required":["mode","line_ids"],"type":"object"}]} |
| parameters | object | 分支约束 | oneOf[1] |  | {"additionalProperties":false,"required_in_object":["line_ids"]} |
| parameters.line_ids | array | 必填（所在对象出现时） | oneOf[1] | 行记录ID数组 | {"maxItems":2,"minItems":2,"uniqueItems":true} |
| parameters.line_ids[] | integer | 每个数组元素 | oneOf[1] | 行记录ID数组 | {"minimum":1} |
| parameters | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["invoice_id","partial_reconcile_id","invoice_line_id","counterpart_line_id"]} |
| parameters.invoice_id | integer | 必填（所在对象出现时） | oneOf[2] | 发票/账单记录ID（具体类型按能力定义） | {"minimum":1} |
| parameters.partial_reconcile_id | integer | 必填（所在对象出现时） | oneOf[2] | 部分核销关系ID | {"minimum":1} |
| parameters.invoice_line_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| parameters.counterpart_line_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| parameters | object | 分支约束 | oneOf[3] |  | {"additionalProperties":false,"required_in_object":["mode","line_ids"]} |
| parameters.mode | 未限定 | 必填（所在对象出现时） | oneOf[3] |  | {"const":"match_group"} |
| parameters.line_ids | array | 必填（所在对象出现时） | oneOf[3] | 行记录ID数组 | {"maxItems":100,"minItems":1,"uniqueItems":true} |
| parameters.line_ids[] | integer | 每个数组元素 | oneOf[3] | 行记录ID数组 | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"reconciliation.undo"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"reconciliation.undo"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：native_pair_invoice_or_complete_readable_current_company_matching_group_undo
- `verify`：same_transaction_target_partial_removal_and_outstanding_restore_validation
- `idempotency`：legacy_pair_invoice_recheck_or_match_group_current_state_closure_replay_without_operation_store_or_concurrent_exactly_once
- `reverse`：reconciliation.apply

### 已登记测试与证据范围

- `unit`：`implemented`；Closed typed inputs, schema and target binding; compatible legacy branches remain covered.；引用：tests/unit/test_accounting_workflows_batch.py
- `integration`：`implemented`；Shared native CLI workflow: both isolated aliases passed32.80s as uid5/su=False/company1. Verified sale/purchase reversal plus draft reissue and replay, native foreign-currency line edits, full/partial matching-group leaf undo and shrinking replay, statement-scoped bank pagination and actual payment bank matches, three company account assignments/clearing/readback and product fallback, purchase self-billing sequence. Native configuration roles and independent bank fixtures exist only in the test transaction. Fresh-cursor objects, caller groups, company settings, defaults and currency/rate rollback checks passed. Bank response additions require synchronized SDK/bridge/schema. No business DB, native source/addon, service, external-send or operation-store changes. Prior-paid reissue, cashbasis/exchange undo workflows, all ancestry/currency/localization/lock/hash branches, all setting consumers and concurrent exactly-once are not claimed.；引用：tests/integration/test_accounting_workflows_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-reconciliation-write_off"></a>

## reconciliation.write_off — 核销银行流水差额

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`bank_reconciliation`；来源模型：res.company, account.account, account.bank.statement.line, account.move, account.move.line, account.partial.reconcile, account.full.reconcile；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.account:read, account.bank.statement.line:read, account.bank.statement.line:write, account.move:read, account.move:write, account.move.line:read, account.move.line:create, account.move.line:write, account.move.line:unlink, account.partial.reconcile:read, account.partial.reconcile:create, account.full.reconcile:read。
- 请求/响应合同：`schemas/v1/reconciliation.write_off.request.schema.json` / `schemas/v1/reconciliation.write_off.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run reconciliation.write_off --request "@request.json" --idempotency-key "reconciliation.write_off:1:f73ab70ff8b9b5d5bd6f6251af3f6892" --confirm "reconciliation.write_off"
```

> 合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "transaction_id": 1,
    "write_off_account_id": 1,
    "label": "1",
    "expected_residual_amount": "1"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transaction_id","write_off_account_id","label","expected_residual_amount"]} |
| parameters.transaction_id | integer | 必填（所在对象出现时） |  | 银行流水记录ID | {"minimum":1} |
| parameters.write_off_account_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.label | string | 必填（所在对象出现时） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |
| parameters.expected_residual_amount | string | 必填（所在对象出现时） |  |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"reconciliation.write_off"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
| response | object | 分支约束 | allOf[1] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"],"resolved_ref":"response.schema.json"} |
| response.schema_version | 未限定 | 必填（所在对象出现时） | allOf[1] |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） | allOf[1] |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） | allOf[1] |  |  |
| response.capability | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） | allOf[1] |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings | array | 必填（所在对象出现时） | allOf[1] |  |  |
| response.warnings[] | object | 每个数组元素 | allOf[1] |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） | allOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | allOf[1]/oneOf[1] |  |  |
| response.error | object | 分支约束 | allOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） | allOf[1] | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） | allOf[1] |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） | allOf[1] |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 | allOf[1] |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） | allOf[1] |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） | allOf[1] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/allOf[1]/else |  |  |
| response | 未限定 | 分支约束 | allOf[2] |  |  |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"reconciliation.write_off"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_accounting_core_write_action_as_configured_business_user
- `verify`：expected_residual_then_post_write_same_transaction_reread_and_response_schema_validation
- `idempotency`：requested_reconciliation_state_hash_and_result_replay
- `reverse`：bank.transaction.unmatch

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the residual precondition, closed write-off fields, exact confirmation, fixed reconciliation path, replay, and CLI response contract.；引用：tests/unit/test_payment_bank_writes.py, tests/unit/test_payment_bank_writes_runtime.py, tests/unit/test_payment_bank_write_cli.py
- `integration`：`implemented`；The shared live smoke verifies execution and rollback in both dedicated isolated database aliases.；引用：tests/integration/test_payment_bank_capability_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-bank_reconciliation"></a>

## report.bank_reconciliation — 生成银行对账报告

- 类型：只读；静态状态：`unconfigured`；handler：`report_bank_reconciliation`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, module, journal, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line, res.currency, account.journal, account.bank.statement, account.bank.statement.line；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read, res.currency:read, account.journal:read, account.bank.statement:read, account.bank.statement.line:read。
- 请求/响应合同：`schemas/v1/report.bank_reconciliation.request.schema.json` / `schemas/v1/report.bank_reconciliation.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.bank_reconciliation --request "@request.json"
```

> 合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。

```json
{
  "schema_version": "v1",
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "example.operator",
    "language": "zh_CN",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {
    "journal_id": 1,
    "as_of": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["journal_id","as_of"],"resolved_ref":"#/$defs/parameters"} |
| parameters.journal_id | integer | 必填（所在对象出现时） |  | 日记账ID | {"minimum":1} |
| parameters.as_of | string | 必填（所在对象出现时） |  | 截至日期 | {"format":"date"} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"bank_reconciliation"}}}}}]},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.bank_reconciliation"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"bank_reconciliation"}}}}}]}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2] |  | {"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"bank_reconciliation"}}}}}]} |
| response.data | object | 分支约束 | oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["report","date","currency","basis","columns","lines","has_more","next_cursor"],"resolved_ref":"financial-report.typed-data.schema.json"} |
| response.data.report | object | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["key","name"]} |
| response.data.report.key | string | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"minLength":1} |
| response.data.report.name | string | 必填（所在对象出现时） | oneOf[2]/allOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.date | object | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["from","to"]} |
| response.data.date.from | string | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"format":"date"} |
| response.data.date.to | string | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"format":"date"} |
| response.data.currency | object | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["id","code","decimal_places"]} |
| response.data.currency.id | integer | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"maxLength":3,"minLength":1} |
| response.data.currency.decimal_places | integer | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"minimum":0} |
| response.data.basis | 未限定 | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"const":"posted_entries"} |
| response.data.columns | array | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"maxItems":64,"minItems":1} |
| response.data.columns[] | object | 每个数组元素 | oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["index","label","expression_label","figure_type"],"resolved_ref":"#/$defs/column"} |
| response.data.columns[].index | integer | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"minimum":0} |
| response.data.columns[].label | string | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"minLength":1} |
| response.data.columns[].expression_label | string | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"minLength":1} |
| response.data.columns[].figure_type | 未限定 | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"enum":["monetary","float","percentage","integer","date","string"]} |
| response.data.lines | array | 必填（所在对象出现时） | oneOf[2]/allOf[1] | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":1000} |
| response.data.lines[] | object | 每个数组元素 | oneOf[2]/allOf[1] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","parent_id","name","level","unfoldable","values"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | string | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].parent_id | string/null | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].name | string | 必填（所在对象出现时） | oneOf[2]/allOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].level | integer | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"minimum":0} |
| response.data.lines[].unfoldable | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.lines[].values | array | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"maxItems":64,"minItems":1} |
| response.data.lines[].values[] | string/null | 每个数组元素 | oneOf[2]/allOf[1] |  |  |
| response.data.has_more | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | oneOf[2]/allOf[1] | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 未限定 | 分支约束 | oneOf[2]/allOf[2] |  |  |
| response.data.report | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  |  |
| response.data.report.key | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"bank_reconciliation"} |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"response.schema.json#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"response.schema.json#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"response.schema.json#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"bank_reconciliation"}}}}}]},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then |  | {"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"bank_reconciliation"}}}}}]} |
| response.data | object | 分支约束 | allOf[1]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["report","date","currency","basis","columns","lines","has_more","next_cursor"],"resolved_ref":"financial-report.typed-data.schema.json"} |
| response.data.report | object | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["key","name"]} |
| response.data.report.key | string | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"minLength":1} |
| response.data.report.name | string | 必填（所在对象出现时） | allOf[1]/then/allOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.date | object | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["from","to"]} |
| response.data.date.from | string | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"format":"date"} |
| response.data.date.to | string | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"format":"date"} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["id","code","decimal_places"]} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"maxLength":3,"minLength":1} |
| response.data.currency.decimal_places | integer | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"minimum":0} |
| response.data.basis | 未限定 | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"const":"posted_entries"} |
| response.data.columns | array | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"maxItems":64,"minItems":1} |
| response.data.columns[] | object | 每个数组元素 | allOf[1]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["index","label","expression_label","figure_type"],"resolved_ref":"#/$defs/column"} |
| response.data.columns[].index | integer | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"minimum":0} |
| response.data.columns[].label | string | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"minLength":1} |
| response.data.columns[].expression_label | string | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"minLength":1} |
| response.data.columns[].figure_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"enum":["monetary","float","percentage","integer","date","string"]} |
| response.data.lines | array | 必填（所在对象出现时） | allOf[1]/then/allOf[1] | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":1000} |
| response.data.lines[] | object | 每个数组元素 | allOf[1]/then/allOf[1] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","parent_id","name","level","unfoldable","values"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | string | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].parent_id | string/null | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].name | string | 必填（所在对象出现时） | allOf[1]/then/allOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].level | integer | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"minimum":0} |
| response.data.lines[].unfoldable | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.lines[].values | array | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"maxItems":64,"minItems":1} |
| response.data.lines[].values[] | string/null | 每个数组元素 | allOf[1]/then/allOf[1] |  |  |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[1]/then/allOf[1] | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 未限定 | 分支约束 | allOf[1]/then/allOf[2] |  |  |
| response.data.report | 未限定 | 可选（可能有条件限制） | allOf[1]/then/allOf[2] |  |  |
| response.data.report.key | 未限定 | 可选（可能有条件限制） | allOf[1]/then/allOf[2] |  | {"const":"bank_reconciliation"} |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_odoo_bank_reconciliation_report_readonly_api
- `verify`：typed_report_columns_lines_cursor_journal_scope_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared typed-report contract, fixed journal binding, runtime normalization, cursor binding, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_typed_financial_reports.py, tests/unit/test_typed_financial_report_runtime.py, tests/unit/test_typed_financial_report_cli.py
- `integration`：`implemented`；The shared live read-only smoke verifies the explicitly journal-scoped report against both dedicated isolated database aliases as the ordinary accounting user.；引用：tests/integration/test_core_object_read_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。
