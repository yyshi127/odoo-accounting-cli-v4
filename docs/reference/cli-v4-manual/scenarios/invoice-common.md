# 发票和账单共用查询、编辑、过账与导出

读取和筛选客户发票、贷项通知单、供应商账单及退款单，维护表头、业务行、税额、单位、扣除比例、布局和显示设置，执行过账、撤销到草稿、取消、复制、删除或冲销重开，并导出单据。单行和多行接口的源关联、草稿、成员集合及重放限制以各条合同为准；支付、催款和外币汇率有独立场景。

[回到总说明书](../../CLI_V4_MANUAL.md) · [新会话使用指南](../USAGE_GUIDE.md)

<a id="cap-cash_rounding-compute"></a>

## cash_rounding.compute — 计算现金舍入金额与差额

- 类型：只读；静态状态：`unconfigured`；handler：`cash_rounding_compute`。
- 状态原因：`runtime_context_required` — Fixed handler implemented; runtime checks configured database, native caller permissions and company context.
- 内部domain：`accounting_master_data`；来源模型：res.company, account.cash.rounding, res.currency；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.cash.rounding:read, res.currency:read。
- 请求/响应合同：`schemas/v1/cash_rounding.compute.request.schema.json` / `schemas/v1/cash_rounding.compute.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read cash_rounding.compute --request "@request.json"
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
    "cash_rounding_id": 1,
    "currency_id": 1,
    "amount": "1"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["cash_rounding_id","currency_id","amount"]} |
| parameters.cash_rounding_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.currency_id | integer | 必填（所在对象出现时） |  | 币种ID | {"minimum":1} |
| parameters.amount | string | 必填（所在对象出现时） |  | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"cash_rounding.compute"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","currency_id","amount","base_amount","rounded_amount","difference"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.currency_id | integer | 必填（所在对象出现时） | oneOf[2] | 币种ID | {"minimum":1} |
| response.data.amount | string | 必填（所在对象出现时） | oneOf[2] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.base_amount | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.rounded_amount | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.difference | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","currency_id","amount","base_amount","rounded_amount","difference"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.currency_id | integer | 必填（所在对象出现时） | allOf[1]/then | 币种ID | {"minimum":1} |
| response.data.amount | string | 必填（所在对象出现时） | allOf[1]/then | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.base_amount | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.rounded_amount | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.difference | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
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
- `execute`：native_currency_round_and_cash_rounding_compute_difference_as_business_user
- `verify`：closed_result_bound_to_rule_currency_company_and_original_canonical_amount
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Closed typed inputs, legacy request/key compatibility, native scopes and posted nonfinancial boundaries.；引用：tests/unit/test_accounting_setup_batch.py
- `integration`：`implemented`；One shared public CLI/native ORM workflow passed both isolated aliases in 22.30s as uid5/su=False/company1. Two new IDs and six extensions: company cash-basis assign/clear/get/replay; optional advanced tax fields, native grouped-tax invoice computation and transition-account rules; sale/purchase posted reference and narration/user edits including a partially reconciled invoice with raw matching IDs/amounts unchanged; posted entry references; financial/shipping denials; positive/negative/zero/minor-unit native currency-aware cash-rounding computation. Native configuration roles exist only inside the isolated transaction; caller never gains sudo. Fresh fixtures, both companies settings, all defaults, currencies/rates and exact caller/native group memberships roll back. Root cash-basis boolean natively propagates to branches; the live topology uses independent roots, not a tested branch workflow. Company ORM write does not run settings UI onchange or delete cash-basis taxes. Group-to-leaf native write need not clear children; non-group calculation ignores retained children. Actual cash-basis entry lifecycle, all hierarchy/currency/localization/hash/lock paths, PDF regeneration, external sends and concurrent exactly-once are not claimed. No business DB, native source/addon or service changes.；引用：tests/integration/test_accounting_setup_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-cash_rounding-create"></a>

## cash_rounding.create — 创建现金舍入规则

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`database_global_record_scope` — Cash-rounding records are database-global while profit and loss accounts are company-dependent; the fixed handler binds account values to the selected company but global fields can affect other companies.
- 内部domain：`accounting_master_data`；来源模型：res.company, account.cash.rounding, account.account；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.account:read, account.cash.rounding:read, account.cash.rounding:create。
- 请求/响应合同：`schemas/v1/cash_rounding.create.request.schema.json` / `schemas/v1/cash_rounding.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run cash_rounding.create --request "@request.json" --idempotency-key "cash_rounding.create:1:8bab25a4597106833350d0a8606af35f" --confirm "cash_rounding.create"
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
    "rounding": "1",
    "strategy": "biggest_tax",
    "rounding_method": "UP",
    "profit_account_id": null,
    "loss_account_id": null
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"if":{"properties":{"strategy":{"const":"biggest_tax"}},"required":["strategy"]},"then":{"properties":{"loss_account_id":{"type":"null"},"profit_account_id":{"type":"null"}}}},{"if":{"properties":{"strategy":{"const":"add_invoice_line"}},"required":["strategy"]},"then":{"properties":{"loss_account_id":{"minimum":1,"type":"integer"},"profit_account_id":{"minimum":1,"type":"integer"}}}}],"required_in_object":["name","rounding","strategy","rounding_method","profit_account_id","loss_account_id"]} |
| parameters.name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":256,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$","resolved_ref":"#/$defs/text"} |
| parameters.rounding | string | 必填（所在对象出现时） |  |  | {"maxLength":256,"pattern":"^(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$","resolved_ref":"#/$defs/positiveDecimal"} |
| parameters.strategy | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["biggest_tax","add_invoice_line"]} |
| parameters.rounding_method | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["UP","DOWN","HALF-UP"]} |
| parameters.profit_account_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.loss_account_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters | 组合/开放结构 | 分支约束 | allOf[1] |  | {"if":{"properties":{"strategy":{"const":"biggest_tax"}},"required":["strategy"]},"then":{"properties":{"loss_account_id":{"type":"null"},"profit_account_id":{"type":"null"}}}} |
| parameters | 未限定 | 条件分支 | allOf[1]/then |  |  |
| parameters.profit_account_id | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| parameters.loss_account_id | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| parameters | 组合/开放结构 | 分支约束 | allOf[2] |  | {"if":{"properties":{"strategy":{"const":"add_invoice_line"}},"required":["strategy"]},"then":{"properties":{"loss_account_id":{"minimum":1,"type":"integer"},"profit_account_id":{"minimum":1,"type":"integer"}}}} |
| parameters | 未限定 | 条件分支 | allOf[2]/then |  |  |
| parameters.profit_account_id | integer | 可选（可能有条件限制） | allOf[2]/then |  | {"minimum":1} |
| parameters.loss_account_id | integer | 可选（可能有条件限制） | allOf[2]/then |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"cash_rounding.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"cash_rounding.create"} |
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
- `execute`：fixed_company_context_cash_rounding_create_as_configured_business_user
- `verify`：same_transaction_rounding_strategy_method_and_company_dependent_accounts_reread
- `idempotency`：global_name_natural_key_and_full_company_context_target_recheck_without_concurrent_exactly_once_guarantee
- `reverse`：manual_reconfiguration_or_remove_if_unused

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed cash-rounding contract, conditional account invariants, company context, manager ACL, natural-key replay, schemas, registry metadata, and CLI dispatch.；引用：tests/unit/test_core_writes.py, tests/unit/test_accounting_master_data_completion_contracts.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_accounting_master_data_completion_registry.py
- `integration`：`implemented`；The guarded shared dual-database transactional smoke verifies first execution, immediate replay, readback, and rollback in both isolated database aliases.；引用：tests/integration/test_accounting_master_data_completion_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-cash_rounding-get"></a>

## cash_rounding.get — 获取现金舍入规则详情

- 类型：只读；静态状态：`unconfigured`；handler：`cash_rounding_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`accounting_master_data`；来源模型：res.company, account.cash.rounding, account.account；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.cash.rounding:read, account.account:read。
- 请求/响应合同：`schemas/v1/cash_rounding.get.request.schema.json` / `schemas/v1/cash_rounding.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read cash_rounding.get --request "@request.json"
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
    "cash_rounding_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["cash_rounding_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.cash_rounding_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"cash_rounding.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"cash_rounding.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"cash_rounding.list.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","rounding","strategy","rounding_method","profit_account","loss_account"],"resolved_ref":"cash_rounding.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.rounding | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.strategy | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["biggest_tax","add_invoice_line"]} |
| response.data.rounding_method | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["UP","DOWN","HALF-UP"]} |
| response.data.profit_account | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/coded"}]} |
| response.data.profit_account | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.profit_account | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.profit_account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.profit_account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.profit_account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.loss_account | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/coded"}]} |
| response.data.loss_account | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.loss_account | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.loss_account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.loss_account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.loss_account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"cash_rounding.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","rounding","strategy","rounding_method","profit_account","loss_account"],"resolved_ref":"cash_rounding.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.rounding | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.strategy | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["biggest_tax","add_invoice_line"]} |
| response.data.rounding_method | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["UP","DOWN","HALF-UP"]} |
| response.data.profit_account | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/coded"}]} |
| response.data.profit_account | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.profit_account | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.profit_account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.profit_account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.profit_account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.loss_account | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/coded"}]} |
| response.data.loss_account | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.loss_account | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.loss_account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.loss_account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.loss_account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
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

- `unit`：`implemented`；Unit tests cover the closed request and response, fixed bridge action, company context, ACL gates, ORM normalization, and CLI dispatch.；引用：tests/unit/test_core_object_reads.py, tests/unit/test_core_object_reads_bridge.py, tests/unit/test_core_object_reads_runtime.py, tests/unit/test_core_object_read_cli.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The shared live read-only smoke verifies the capability against both dedicated isolated database aliases as the ordinary accounting user.；引用：tests/integration/test_accounting_configuration_read_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-cash_rounding-list"></a>

## cash_rounding.list — 列出现金舍入规则

- 类型：只读；静态状态：`unconfigured`；handler：`cash_rounding_list`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`accounting_master_data`；来源模型：res.company, account.cash.rounding, account.account；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.cash.rounding:read, account.account:read。
- 请求/响应合同：`schemas/v1/cash_rounding.list.request.schema.json` / `schemas/v1/cash_rounding.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read cash_rounding.list --request "@request.json"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"cash_rounding.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","rounding","strategy","rounding_method","profit_account","loss_account"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].rounding | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].strategy | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["biggest_tax","add_invoice_line"]} |
| response.data.items[].rounding_method | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["UP","DOWN","HALF-UP"]} |
| response.data.items[].profit_account | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/coded"}]} |
| response.data.items[].profit_account | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].profit_account | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].profit_account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].profit_account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.items[].profit_account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].loss_account | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/coded"}]} |
| response.data.items[].loss_account | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].loss_account | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].loss_account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].loss_account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.items[].loss_account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","rounding","strategy","rounding_method","profit_account","loss_account"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].rounding | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].strategy | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["biggest_tax","add_invoice_line"]} |
| response.data.items[].rounding_method | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["UP","DOWN","HALF-UP"]} |
| response.data.items[].profit_account | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/coded"}]} |
| response.data.items[].profit_account | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].profit_account | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].profit_account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].profit_account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.items[].profit_account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].loss_account | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/coded"}]} |
| response.data.items[].loss_account | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].loss_account | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].loss_account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].loss_account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.items[].loss_account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
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

- `unit`：`implemented`；Unit tests cover the closed request and response, cursor binding, fixed bridge action, company context, ACL gates, ORM normalization, and CLI dispatch.；引用：tests/unit/test_core_object_reads.py, tests/unit/test_core_object_reads_bridge.py, tests/unit/test_core_object_reads_runtime.py, tests/unit/test_core_object_read_cli.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The shared live read-only smoke verifies the capability against both dedicated isolated database aliases as the ordinary accounting user.；引用：tests/integration/test_accounting_configuration_read_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-cash_rounding-update"></a>

## cash_rounding.update — 更新现金舍入规则

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`database_global_record_scope` — Cash-rounding records are database-global while profit and loss accounts are company-dependent; the fixed handler binds account values to the selected company but global fields can affect other companies.
- 内部domain：`accounting_master_data`；来源模型：res.company, account.cash.rounding, account.account；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.account:read, account.cash.rounding:read, account.cash.rounding:write。
- 请求/响应合同：`schemas/v1/cash_rounding.update.request.schema.json` / `schemas/v1/cash_rounding.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run cash_rounding.update --request "@request.json" --idempotency-key "cash_rounding.update:1:663c40c5fc625d44d00a597ae77ce292" --confirm "cash_rounding.update"
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
    "cash_rounding_id": 1,
    "changes": {
      "name": "Example"
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["cash_rounding_id","changes"]} |
| parameters.cash_rounding_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"allOf":[{"if":{"properties":{"strategy":{"const":"biggest_tax"}},"required":["strategy"]},"then":{"properties":{"loss_account_id":{"type":"null"},"profit_account_id":{"type":"null"}}}},{"if":{"properties":{"strategy":{"const":"add_invoice_line"}},"required":["strategy"]},"then":{"properties":{"loss_account_id":{"minimum":1,"type":"integer"},"profit_account_id":{"minimum":1,"type":"integer"}}}},{"if":{"required":["profit_account_id","loss_account_id"]},"then":{"oneOf":[{"properties":{"loss_account_id":{"type":"null"},"profit_account_id":{"type":"null"}}},{"properties":{"loss_account_id":{"minimum":1,"type":"integer"},"profit_account_id":{"minimum":1,"type":"integer"}}}]}}],"minProperties":1} |
| parameters.changes.name | string | 可选（可能有条件限制） |  | 名称/行说明 | {"maxLength":256,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$","resolved_ref":"#/$defs/text"} |
| parameters.changes.rounding | string | 可选（可能有条件限制） |  |  | {"maxLength":256,"pattern":"^(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$","resolved_ref":"#/$defs/positiveDecimal"} |
| parameters.changes.strategy | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["biggest_tax","add_invoice_line"]} |
| parameters.changes.rounding_method | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["UP","DOWN","HALF-UP"]} |
| parameters.changes.profit_account_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.changes.loss_account_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.changes | 组合/开放结构 | 分支约束 | allOf[1] | 仅提交拟变更字段，非整条记录 | {"if":{"properties":{"strategy":{"const":"biggest_tax"}},"required":["strategy"]},"then":{"properties":{"loss_account_id":{"type":"null"},"profit_account_id":{"type":"null"}}}} |
| parameters.changes | 未限定 | 条件分支 | allOf[1]/then | 仅提交拟变更字段，非整条记录 |  |
| parameters.changes.profit_account_id | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| parameters.changes.loss_account_id | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| parameters.changes | 组合/开放结构 | 分支约束 | allOf[2] | 仅提交拟变更字段，非整条记录 | {"if":{"properties":{"strategy":{"const":"add_invoice_line"}},"required":["strategy"]},"then":{"properties":{"loss_account_id":{"minimum":1,"type":"integer"},"profit_account_id":{"minimum":1,"type":"integer"}}}} |
| parameters.changes | 未限定 | 条件分支 | allOf[2]/then | 仅提交拟变更字段，非整条记录 |  |
| parameters.changes.profit_account_id | integer | 可选（可能有条件限制） | allOf[2]/then |  | {"minimum":1} |
| parameters.changes.loss_account_id | integer | 可选（可能有条件限制） | allOf[2]/then |  | {"minimum":1} |
| parameters.changes | 组合/开放结构 | 分支约束 | allOf[3] | 仅提交拟变更字段，非整条记录 | {"if":{"required":["profit_account_id","loss_account_id"]},"then":{"oneOf":[{"properties":{"loss_account_id":{"type":"null"},"profit_account_id":{"type":"null"}}},{"properties":{"loss_account_id":{"minimum":1,"type":"integer"},"profit_account_id":{"minimum":1,"type":"integer"}}}]}} |
| parameters.changes | 组合/开放结构 | 条件分支 | allOf[3]/then | 仅提交拟变更字段，非整条记录 | {"oneOf":[{"properties":{"loss_account_id":{"type":"null"},"profit_account_id":{"type":"null"}}},{"properties":{"loss_account_id":{"minimum":1,"type":"integer"},"profit_account_id":{"minimum":1,"type":"integer"}}}]} |
| parameters.changes | 未限定 | 分支约束 | allOf[3]/then/oneOf[1] | 仅提交拟变更字段，非整条记录 |  |
| parameters.changes.profit_account_id | null | 可选（可能有条件限制） | allOf[3]/then/oneOf[1] |  |  |
| parameters.changes.loss_account_id | null | 可选（可能有条件限制） | allOf[3]/then/oneOf[1] |  |  |
| parameters.changes | 未限定 | 分支约束 | allOf[3]/then/oneOf[2] | 仅提交拟变更字段，非整条记录 |  |
| parameters.changes.profit_account_id | integer | 可选（可能有条件限制） | allOf[3]/then/oneOf[2] |  | {"minimum":1} |
| parameters.changes.loss_account_id | integer | 可选（可能有条件限制） | allOf[3]/then/oneOf[2] |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"cash_rounding.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"cash_rounding.update"} |
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
- `execute`：fixed_company_context_cash_rounding_update
- `verify`：same_transaction_rounding_strategy_method_and_company_dependent_accounts_reread
- `idempotency`：full_company_context_target_state_recheck_without_operation_store
- `reverse`：repeat_update_with_previous_values

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed patch contract, conditional account invariants, company context, manager ACL, target-state replay, schemas, registry metadata, and CLI dispatch.；引用：tests/unit/test_core_writes.py, tests/unit/test_accounting_master_data_completion_contracts.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_accounting_master_data_completion_registry.py
- `integration`：`implemented`；The guarded shared dual-database transactional smoke verifies first execution, immediate replay, readback, and rollback in both isolated database aliases.；引用：tests/integration/test_accounting_master_data_completion_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-company-discount_allocation_accounts-assign"></a>

## company.discount_allocation_accounts.assign — 设置发票折扣分摊科目

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Fixed current-company settings are implemented; native company write requires access-rights administration and reference ACLs. Ordinary accountant permission is not implied.
- 内部domain：`accounting_configuration`；来源模型：account.account, ir.default, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：base.group_erp_manager；ACL：account.account:read, ir.default:read, res.company:read, res.company:write。
- 请求/响应合同：`schemas/v1/company.discount_allocation_accounts.assign.request.schema.json` / `schemas/v1/company.discount_allocation_accounts.assign.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run company.discount_allocation_accounts.assign --request "@request.json" --idempotency-key "company.discount_allocation_accounts.assign:1:fee3127c67c7d0bda07f603e9a2ab66f" --confirm "company.discount_allocation_accounts.assign"
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
      "account_discount_expense_allocation_id": 1
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["changes"]} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.account_discount_expense_allocation_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.changes.account_discount_income_allocation_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"company.discount_allocation_accounts.assign"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"company.discount_allocation_accounts.assign"} |
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

<a id="cap-company-invoice_display-update"></a>

## company.invoice_display.update — 修改公司发票显示选项

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Fixed current-company settings are implemented; native company write requires access-rights administration and reference ACLs. Ordinary accountant permission is not implied.
- 内部domain：`accounting_configuration`；来源模型：ir.default, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：base.group_erp_manager；ACL：ir.default:read, res.company:read, res.company:write。
- 请求/响应合同：`schemas/v1/company.invoice_display.update.request.schema.json` / `schemas/v1/company.invoice_display.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run company.invoice_display.update --request "@request.json" --idempotency-key "company.invoice_display.update:1:b37225d8ed2803e354fbee9712ede80c" --confirm "company.invoice_display.update"
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
      "display_invoice_amount_total_words": false
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["changes"]} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.display_invoice_amount_total_words | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.changes.display_invoice_tax_company_currency | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.changes.link_qr_code | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.changes.qr_code | boolean | 可选（可能有条件限制） |  |  |  |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"company.invoice_display.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"company.invoice_display.update"} |
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
- `verify`：same_savepoint_configuration_reread_with_native_constraints
- `idempotency`：serial_current_target_setting_recheck_without_operation_store_or_concurrent_exactly_once
- `reverse`：restore_prior_settings_subject_to_native_constraints

### 已登记测试与证据范围

- `unit`：`implemented`；Closed operation-specific settings, native typed choices and null clearing, public CLI/schemas/confirmation, deterministic keys and contextual company/result binding. Real ORM behavior belongs to the shared integration workflow.；引用：tests/unit/test_company_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5/su=False/company 1: eight new IDs and two reused journal-entry setup IDs; fourteen setting replays plus one posting replay per alias. Ordinary business-user settings read succeeds and native company write is denied before a transaction-local ERP-access group grant. All seven fixed native company writes persist and serial target-state replay is verified. Native April31 fiscal-end validation and existing-accounting price-method denial return the actual ValidationError/business_rule_error and restore all partial changes; February29 is natively accepted. Current-company reads, relation null clearing, all three quick-edit choices and disabled null mode are checked. All seven relation fields reject foreign and missing references; exchange journal selection rejects non-general sale journals. Posted entry identities/accounts/amounts/residuals/taxes, the other company and non-target lock/audit/chart/currency/prefix configuration are unchanged. Actual product-category default values match native company accounts after company.write; fresh cursors prove existing company settings, all ir.default rows, exact groups and synthetic objects roll back, including before rethrow on failure. The test loads the actual immutable CLI registry once per worker but retains real request/response validation and native ACLs. No concurrent exactly-once, child-company native scenario, real invoice rendering/delivery, automatic bill posting or credit-limit amount mutation claim. No business DB, installed addon/source or service/configuration changes; no ERP grant persisted.；引用：tests/integration/test_company_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-alerts-inspect"></a>

## invoice.alerts.inspect — 查看发票原生提醒

- 类型：只读；静态状态：`unconfigured`；handler：`invoice_alerts_inspect`。
- 状态原因：`runtime_context_required` — Fixed invoice preparation and product accounting operations are implemented; runtime company, ordinary-user ACL and native accounting recomputation apply.
- 内部domain：`invoice`；来源模型：res.company, account.move, account.move.line, account.journal, res.partner, res.currency；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move:read, account.move.line:read, account.journal:read, res.partner:read, res.currency:read。
- 请求/响应合同：`schemas/v1/invoice.alerts.inspect.request.schema.json` / `schemas/v1/invoice.alerts.inspect.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read invoice.alerts.inspect --request "@request.json"
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
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.alerts.inspect"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","move_type","state","alerts"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["in_invoice","in_refund","out_invoice","out_refund"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.alerts | array | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.alerts[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["key","level","message","action_label"]} |
| response.data.alerts[].key | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.alerts[].level | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.alerts[].message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.alerts[].action_label | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","move_type","state","alerts"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["in_invoice","in_refund","out_invoice","out_refund"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.alerts | array | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.alerts[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["key","level","message","action_label"]} |
| response.data.alerts[].key | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.alerts[].level | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.alerts[].message | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.alerts[].action_label | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
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
- `execute`：fixed_target_native_accounting_read_as_business_user
- `verify`：typed_target_and_optional_fiscal_position_binding
- `idempotency`：read_only
- `reverse`：not_applicable

### 已登记测试与证据范围

- `unit`：`implemented`；Closed parameters and typed target binding, schemas and public CLI; native behavior is tested separately.；引用：tests/unit/test_invoice_preparation_batch.py
- `integration`：`implemented`；One shared public CLI/real ORM workflow passed both isolated aliases in 20.08s as uid5/su=False/company1: native service-date set/clear and replay; sanitized zero-purchase-line alerts without executing actions; actual reversal and transaction-local direct cashbasis/adjusting relation inspection; category/product defaults, native tax filtering and fiscal-position account mapping; sale/purchase existing tax-group minor-unit inverse adjustments, balance and payment-term readback, replay and unchanged other tax rows. Posted, missing, foreign and invalid-target denials are exercised. Fixtures, exact groups, company settings and defaults roll back in fresh cursors. Direct relation fixtures are not full cashbasis/deferral workflow acceptance; current company topology does not prove every ancestry/localization/currency branch. No business DB, service/addon change, actual send or concurrent exactly-once claim.；引用：tests/integration/test_invoice_preparation_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-cancel"></a>

## invoice.cancel — 原子取消单张或 2–100 张发票或账单

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`invoices_and_bills`；来源模型：res.company, account.move, account.move.line, account.analytic.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.move:read, account.move:write, account.move.line:read。
- 请求/响应合同：`schemas/v1/invoice.cancel.request.schema.json` / `schemas/v1/invoice.cancel.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.cancel --request "@request.json" --idempotency-key "invoice.cancel:1" --confirm "invoice.cancel"
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
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"oneOf":[{"required":["move_id"]},{"required":["move_ids"]}]} |
| parameters.move_id | integer | 可选（可能有条件限制） |  | 会计单据记录ID | {"minimum":1} |
| parameters.move_ids | array | 可选（可能有条件限制） |  | 会计单据ID数组 | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| parameters.move_ids[] | integer | 每个数组元素 |  | 会计单据ID数组 | {"minimum":1} |
| parameters | 未限定 | 分支约束 | oneOf[1] |  | {"required_in_object":["move_id"]} |
| parameters | 未限定 | 分支约束 | oneOf[2] |  | {"required_in_object":["move_ids"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.cancel"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]} |
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
| response.data | object | 分支约束 | oneOf[3] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-batch-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | oneOf[3] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | oneOf[3] |  | {"additionalProperties":false,"required_in_object":["items","processed_count"]} |
| response.data.result.items | array | 必填（所在对象出现时） | oneOf[3] |  | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| response.data.result.items[] | object | 每个数组元素 | oneOf[3] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"],"resolved_ref":"core-write-result.schema.json#/properties/result"} |
| response.data.result.items[].model | string | 必填（所在对象出现时） | oneOf[3] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].id | integer/null | 必填（所在对象出现时） | oneOf[3] |  | {"minimum":1} |
| response.data.result.items[].name | string/null | 必填（所在对象出现时） | oneOf[3] | 名称/行说明 | {"minLength":1} |
| response.data.result.items[].state | string | 必填（所在对象出现时） | oneOf[3] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].company_id | integer | 必填（所在对象出现时） | oneOf[3] | 所选公司ID | {"minimum":1} |
| response.data.result.items[].move_type | string/null | 必填（所在对象出现时） | oneOf[3] |  | {"minLength":1} |
| response.data.result.items[].source_id | integer/null | 必填（所在对象出现时） | oneOf[3] |  | {"minimum":1} |
| response.data.result.items[].line_ids | array | 必填（所在对象出现时） | oneOf[3] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.items[].line_ids[] | integer | 每个数组元素 | oneOf[3] | 行记录ID数组 | {"minimum":1} |
| response.data.result.items[].partial_reconcile_ids | array | 必填（所在对象出现时） | oneOf[3] |  | {"uniqueItems":true} |
| response.data.result.items[].partial_reconcile_ids[] | integer | 每个数组元素 | oneOf[3] |  | {"minimum":1} |
| response.data.result.items[].full_reconcile_id | integer/null | 必填（所在对象出现时） | oneOf[3] | 完整核销关系ID | {"minimum":1} |
| response.data.result.items[].reconciled | boolean | 必填（所在对象出现时） | oneOf[3] |  |  |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | oneOf[3] |  | {"maximum":100,"minimum":2} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then |  | {"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]} |
| response.data | object | 分支约束 | allOf[1]/then/oneOf[1] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[1]/then/oneOf[1] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[1]/then/oneOf[1] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-batch-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","processed_count"]} |
| response.data.result.items | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| response.data.result.items[] | object | 每个数组元素 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"],"resolved_ref":"core-write-result.schema.json#/properties/result"} |
| response.data.result.items[].model | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.result.items[].name | string/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.items[].state | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.items[].move_type | string/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.result.items[].source_id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.result.items[].line_ids | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.items[].line_ids[] | integer | 每个数组元素 | allOf[1]/then/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.items[].partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.items[].partial_reconcile_ids[] | integer | 每个数组元素 | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.result.items[].full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.items[].reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  |  |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"maximum":100,"minimum":2} |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：singular_or_2_to_100_distinct_ids_closed_validation_normalized_sorted_and_exact_capability_confirmation
- `execute`：full_batch_record_scope_company_invoice_type_and_state_preflight_then_single_transaction_all_or_nothing_native_cancel
- `verify`：explicit_batch_result_with_exact_normalized_record_ids_target_states_same_transaction_reread_and_response_schema_validation
- `idempotency`：capability_company_and_full_normalized_sorted_record_id_set_key_with_serial_target_state_replay
- `reverse`：invoice.reset_to_draft_when_native_state_allows

### 已登记测试与证据范围

- `unit`：`implemented`；The existing unit tests continue to cover the singular request and native runtime behavior; the batch contract unit test covers batch-request normalization, full normalized-ID-set idempotency keys, bridge and capability contracts, explicit batch results, and CLI verification.；引用：tests/unit/test_document_lifecycle_writes.py, tests/unit/test_document_lifecycle_writes_runtime.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_write_cli.py, tests/unit/test_document_lifecycle_write_cli.py, tests/unit/test_lifecycle_batch_contract.py
- `integration`：`implemented`；The existing integration smoke continues to cover singular native execution; the new live smoke covers dual-database batch execution, immediate replay, and rollback, plus a representative whole-batch invalid-ID no-op for invoice.post.；引用：tests/integration/test_document_lifecycle_write_batch_live.py, tests/integration/test_batch_lifecycle_write_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-cash_rounding-assign"></a>

## invoice.cash_rounding.assign — 设置发票现金舍入方式

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires explicit runtime company/user scope and native ACLs. Currency/rounding/term/method/schedule changes require draft moves; review uses the native posted-only method. Auto-post configuration schedules native future work but never runs a cron or posts a move in this command. No arbitrary field/method calls or external delivery.
- 内部domain：`accounting_documents`；来源模型：account.account, account.cash.rounding, account.move, account.move.line, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.account:read, account.cash.rounding:read, account.move.line:create, account.move.line:read, account.move.line:unlink, account.move.line:write, account.move:read, account.move:write。
- 请求/响应合同：`schemas/v1/invoice.cash_rounding.assign.request.schema.json` / `schemas/v1/invoice.cash_rounding.assign.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.cash_rounding.assign --request "@request.json" --idempotency-key "invoice.cash_rounding.assign:1:a4b0fa34c05f9103b427ab63df2f0439" --confirm "invoice.cash_rounding.assign"
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
    "cash_rounding_id": 1,
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["cash_rounding_id","move_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.cash_rounding_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.cash_rounding.assign"} |
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
- `execute`：fixed_native_move_field_patch_or_native_action
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：native_current_payload_recheck
- `reverse`：restore_previous_setting_subject_to_native_state_and_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Shared closed contracts, native methods, fixed public/runtime/schema and company/user boundaries.；引用：tests/unit/test_move_processing_batch.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases through the public CLI as uid 5 with su=False: all nine new capabilities, eight immediate replays, actual foreign-currency balance recomputation and native rate refresh, native cash-rounding line, incoterm and invoice method, native payment block/unblock and posted review, a saved unposted recurring schedule, direction/state/company denial, and fresh-cursor business-data, currency/rate fixture and temporary-group rollback verification. No cron, external delivery or service changes.；引用：tests/integration/test_move_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-delete"></a>

## invoice.delete — 删除从未过账的草稿发票或账单

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`deleted_record_tombstone_unavailable` — The handler verifies invoice-or-bill and line absence after deletion, but keeps no persistent tombstone, so a later retry cannot distinguish its prior deletion from an unrelated disappearance.
- 内部domain：`invoices_and_bills`；来源模型：res.company, account.move, account.move.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.move:read, account.move:unlink, account.move.line:read, account.move.line:unlink。
- 请求/响应合同：`schemas/v1/invoice.delete.request.schema.json` / `schemas/v1/invoice.delete.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.delete --request "@request.json" --idempotency-key "invoice.delete:1" --confirm "invoice.delete"
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
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"invoice.delete"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"invoice.delete"} |
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
- `execute`：fixed_native_never_posted_draft_invoice_or_bill_unlink
- `verify`：same_transaction_account_move_and_lines_absence_and_response_schema_validation
- `idempotency`：record_absence_recheck_without_operation_store_or_persistent_tombstone
- `reverse`：not_reversible_deleted_invoice_or_bill_must_be_recreated

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover confirmation, invoice-family and never-posted-draft boundaries, native unlink, move-and-line absence verification, result binding, registry descriptor, and schemas.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_draft_document_maintenance_runtime.py, tests/unit/test_draft_document_maintenance_schemas.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases through the public CLI as uid 5 with su=False, exercising all six draft-maintenance commands, five immediate replays, and fresh-cursor business-data and temporary-group rollback verification.；引用：tests/integration/test_draft_document_maintenance_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-duplicate"></a>

## invoice.duplicate — 复制发票或账单为新草稿

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`invoices_and_bills`；来源模型：res.company, account.move, account.move.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.move:read, account.move:create, account.move:write, account.move.line:read, account.move.line:create。
- 请求/响应合同：`schemas/v1/invoice.duplicate.request.schema.json` / `schemas/v1/invoice.duplicate.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.duplicate --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "invoice.duplicate"
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
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.duplicate"} |
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
- `execute`：fixed_native_account_move_copy_as_draft
- `verify`：same_transaction_new_draft_source_binding_and_response_schema_validation
- `idempotency`：caller_chosen_operation_key_and_source_parameter_marker_allow_distinct_duplicates_and_same_key_replay
- `reverse`：invoice.cancel_or_delete_draft_outside_this_capability

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the generic core-write path, closed request, caller-selected operation key and source-bound draft result.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_core_write_cli.py, tests/unit/test_invoice_copy_type_contract.py, tests/unit/test_invoice_copy_type_runtime.py
- `integration`：`implemented`；The guarded live smoke verifies native draft duplication, type switching and rollback.；引用：tests/integration/test_invoice_duplicate_type_switch_batch_live.py
- `golden`：`planned`；Golden examples are deferred.；引用：无
- `e2e`：`planned`；Natural-language routing is deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-duplicate_candidates-list"></a>

## invoice.duplicate_candidates.list — 列出发票潜在重复项

- 类型：只读；静态状态：`unconfigured`；handler：`invoice_duplicate_candidates_list`。
- 状态原因：`runtime_context_required` — The fixed read handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`invoices_and_bills`；来源模型：res.company, account.move, res.partner, res.currency；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move:read, res.partner:read, res.currency:read。
- 请求/响应合同：`schemas/v1/invoice.duplicate_candidates.list.request.schema.json` / `schemas/v1/invoice.duplicate_candidates.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read invoice.duplicate_candidates.list --request "@request.json"
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
    "invoice_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["invoice_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.invoice_id | integer | 必填（所在对象出现时） |  | 发票/账单记录ID（具体类型按能力定义） | {"minimum":1} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.duplicate_candidates.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","name","move_type","state","invoice_date","reference","partner","currency","amount_total"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["out_invoice","out_refund","in_invoice","in_refund"]} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.items[].invoice_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].reference | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].partner | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","name","move_type","state","invoice_date","reference","partner","currency","amount_total"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["out_invoice","out_refund","in_invoice","in_refund"]} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.items[].invoice_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].reference | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].partner | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
- `execute`：fixed_company_scoped_native_duplicate_invoice_candidate_list
- `verify`：same_transaction_acl_company_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared focused test covers registry metadata, fixed CLI routing, model mapping, and exclusion of inventory capabilities.；引用：tests/unit/test_accounting_operational_reads_registry_cli.py
- `integration`：`implemented`；The shared ordinary-accounting-user read-only smoke passed for all twelve capabilities on both dedicated isolated database aliases.；引用：tests/integration/test_accounting_operational_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-fiscal_position-refresh"></a>

## invoice.fiscal_position.refresh — 重算发票财税规则

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured caller/company scope and native ACLs. Writes require a draft invoice or receipt. Terms use native HTML sanitization. Sections/subsections/notes are non-accountable native lines; layout deletion never deletes product, tax or payment-term lines. Resequencing requires all native invoice lines and only changes sequence. Fiscal refresh calls the native price/tax/account recomputation and may overwrite manual financial values. No external delivery, cron or caller-sudo.
- 内部domain：`accounting_documents`；来源模型：account.account, account.fiscal.position, account.move, account.move.line, account.tax, product.product, product.template, res.company, res.currency；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.account:read, account.fiscal.position:read, account.move.line:create, account.move.line:read, account.move.line:unlink, account.move.line:write, account.move:read, account.move:write, account.tax:read, product.product:read, product.template:read, res.company:read, res.currency:read。
- 请求/响应合同：`schemas/v1/invoice.fiscal_position.refresh.request.schema.json` / `schemas/v1/invoice.fiscal_position.refresh.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.fiscal_position.refresh --request "@request.json" --idempotency-key "invoice.fiscal_position.refresh:1:cf502a7b8946f37ee6cdff9476a06ca9" --confirm "invoice.fiscal_position.refresh"
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
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.fiscal_position.refresh"} |
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
- `execute`：fixed_native_invoice_fields_or_fiscal_action
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：native_current_payload_recheck_missing_deleted_line_is_not_found
- `reverse`：restore_previous_values_subject_to_native_state_and_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Shared closed schemas, public/runtime contracts, native layout and fiscal actions, replay and scope boundaries.；引用：tests/unit/test_invoice_presentation_batch.py
- `integration`：`implemented`；The shared rollback-only public CLI/real-ORM smoke passed both isolated aliases as uid 5 with su=False: all eight new IDs and seven immediate replays; native sanitized terms, shipping/responsible settings; sections, subsections, notes, native zero-accounting/parent/order and scoped keyset pagination; existing empty/long native labels; layout edits preserve totals; native fiscal price/tax/account recomputation with native balance and dynamic-sync guards; product-line deletion, incomplete ordering, posted and foreign-company denial; fresh-cursor business-record and temporary-group rollback. No external delivery, cron, addon modification or service changes.；引用：tests/integration/test_invoice_presentation_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-get"></a>

## invoice.get — 读取发票或账单明细

- 类型：只读；静态状态：`unconfigured`；handler：`invoice_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`invoices_and_bills`；来源模型：account.move, account.move.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move:read, account.move.line:read, account.journal:read, account.account:read, account.tax:read, product.product:read, res.currency:read, res.partner:read。
- 请求/响应合同：`schemas/v1/invoice.get.request.schema.json` / `schemas/v1/invoice.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read invoice.get --request "@request.json"
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
    "invoice_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["invoice_id"]} |
| parameters.invoice_id | integer | 必填（所在对象出现时） |  | 发票/账单记录ID（具体类型按能力定义） | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","date","invoice_date","invoice_date_due","ref","payment_reference","invoice_origin","journal","company_id","currency","partner","partner_bank_id","fiscal_position_id","amount_untaxed","amount_tax","amount_total","amount_residual","payment_state","lines"],"resolved_ref":"#/$defs/data"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1,"resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/id"} |
| response.data.name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/name"} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["out_invoice","out_refund","in_invoice","in_refund"],"resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/move_type"} |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"],"resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/state"} |
| response.data.date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date","resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/date"} |
| response.data.invoice_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date","resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/invoice_date"} |
| response.data.invoice_date_due | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date","resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/invoice_date_due"} |
| response.data.ref | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1,"resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/ref"} |
| response.data.payment_reference | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1,"resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/payment_reference"} |
| response.data.invoice_origin | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1,"resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/invoice_origin"} |
| response.data.journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"invoice.search.response.schema.json#/$defs/journal"} |
| response.data.journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":5,"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1,"resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/company_id"} |
| response.data.currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"invoice.search.response.schema.json#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.partner | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"invoice.search.response.schema.json#/$defs/partner"}]} |
| response.data.partner | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.partner | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"invoice.search.response.schema.json#/$defs/partner"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.partner_bank_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.fiscal_position_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.amount_untaxed | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.amount_tax | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.amount_residual | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.payment_state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy"],"resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/payment_state"} |
| response.data.lines | array | 必填（所在对象出现时） | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 |  |
| response.data.lines[] | object | 每个数组元素 | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"allOf":[{"else":{"properties":{"account":{"$ref":"#/$defs/account"}}},"if":{"properties":{"display_type":{"enum":["line_section","line_subsection","line_note"]}},"required":["display_type"]},"then":{"properties":{"account":{"type":"null"}}}}],"required_in_object":["id","sequence","display_type","name","product","account","quantity","price_unit","discount","price_subtotal","price_total","deferred_start_date","deferred_end_date","taxes","analytic_distribution"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].sequence | integer | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.lines[].display_type | 未限定 | 必填（所在对象出现时） | oneOf[2] | 业务行/章节/备注类型 | {"enum":["product","line_section","line_subsection","line_note"]} |
| response.data.lines[].name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].product | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named_ref"}]} |
| response.data.lines[].product | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].product | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named_ref"} |
| response.data.lines[].product.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].product.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].product_uom_id | integer/null | 可选（可能有条件限制） | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].deductible_amount | string | 可选（可能有条件限制） | oneOf[2] | Native deductible percentage, not a monetary amount; omitted when the field is unavailable. | {"pattern":"^(?:100(?:\\.0+)?&#124;(?:0&#124;[1-9][0-9]?)(?:\\.[0-9]+)?)$(?![\\s\\S])"} |
| response.data.lines[].account | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.lines[].account | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].account | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.lines[].account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.lines[].account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].quantity | string | 必填（所在对象出现时） | oneOf[2] | 数量；单位、符号和精度依具体接口 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.lines[].price_unit | string | 必填（所在对象出现时） | oneOf[2] | 单价；币种及符号依单据和合同 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.lines[].discount | string | 必填（所在对象出现时） | oneOf[2] | 折扣百分比 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.lines[].price_subtotal | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.lines[].price_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.lines[].deferred_start_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.lines[].deferred_end_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.lines[].taxes | array | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.lines[].taxes[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","type_tax_use","amount_type","amount","price_include"],"resolved_ref":"#/$defs/tax"} |
| response.data.lines[].taxes[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].taxes[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].taxes[].type_tax_use | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["sale","purchase","none"]} |
| response.data.lines[].taxes[].amount_type | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.lines[].taxes[].amount | string | 必填（所在对象出现时） | oneOf[2] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.lines[].taxes[].price_include | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.lines[].analytic_distribution | object | 必填（所在对象出现时） | oneOf[2] | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":{"pattern":"^(?:0&#124;-?(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9]))(?![\\s\\S])","type":"string"},"propertyNames":{"minLength":1,"type":"string"},"resolved_ref":"journal_item.search.response.schema.json#/$defs/analytic_distribution"} |
| response.data.lines[].analytic_distribution{其他键} | string | 动态键值 | oneOf[2] |  | {"pattern":"^(?:0&#124;-?(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9]))(?![\\s\\S])"} |
| response.data.lines[] | 组合/开放结构 | 分支约束 | oneOf[2]/allOf[1] | 行数组；增补/更新/替换语义由能力ID决定 | {"else":{"properties":{"account":{"$ref":"#/$defs/account"}}},"if":{"properties":{"display_type":{"enum":["line_section","line_subsection","line_note"]}},"required":["display_type"]},"then":{"properties":{"account":{"type":"null"}}}} |
| response.data.lines[] | 未限定 | 条件分支 | oneOf[2]/allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| response.data.lines[].account | null | 可选（可能有条件限制） | oneOf[2]/allOf[1]/then |  |  |
| response.data.lines[] | 未限定 | 条件分支 | oneOf[2]/allOf[1]/else | 行数组；增补/更新/替换语义由能力ID决定 |  |
| response.data.lines[].account | object | 可选（可能有条件限制） | oneOf[2]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.lines[].account.id | integer | 必填（所在对象出现时） | oneOf[2]/allOf[1]/else |  | {"minimum":1} |
| response.data.lines[].account.code | string | 必填（所在对象出现时） | oneOf[2]/allOf[1]/else |  | {"minLength":1} |
| response.data.lines[].account.name | string | 必填（所在对象出现时） | oneOf[2]/allOf[1]/else | 名称/行说明 | {"minLength":1} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","date","invoice_date","invoice_date_due","ref","payment_reference","invoice_origin","journal","company_id","currency","partner","partner_bank_id","fiscal_position_id","amount_untaxed","amount_tax","amount_total","amount_residual","payment_state","lines"],"resolved_ref":"#/$defs/data"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1,"resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/id"} |
| response.data.name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1,"resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/name"} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["out_invoice","out_refund","in_invoice","in_refund"],"resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/move_type"} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"],"resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/state"} |
| response.data.date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date","resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/date"} |
| response.data.invoice_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date","resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/invoice_date"} |
| response.data.invoice_date_due | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date","resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/invoice_date_due"} |
| response.data.ref | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1,"resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/ref"} |
| response.data.payment_reference | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1,"resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/payment_reference"} |
| response.data.invoice_origin | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1,"resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/invoice_origin"} |
| response.data.journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"invoice.search.response.schema.json#/$defs/journal"} |
| response.data.journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":5,"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1,"resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/company_id"} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"invoice.search.response.schema.json#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"invoice.search.response.schema.json#/$defs/partner"}]} |
| response.data.partner | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.partner | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"invoice.search.response.schema.json#/$defs/partner"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.partner_bank_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.fiscal_position_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.amount_untaxed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.amount_tax | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.amount_residual | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.payment_state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy"],"resolved_ref":"invoice.search.response.schema.json#/$defs/item/properties/payment_state"} |
| response.data.lines | array | 必填（所在对象出现时） | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| response.data.lines[] | object | 每个数组元素 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"allOf":[{"else":{"properties":{"account":{"$ref":"#/$defs/account"}}},"if":{"properties":{"display_type":{"enum":["line_section","line_subsection","line_note"]}},"required":["display_type"]},"then":{"properties":{"account":{"type":"null"}}}}],"required_in_object":["id","sequence","display_type","name","product","account","quantity","price_unit","discount","price_subtotal","price_total","deferred_start_date","deferred_end_date","taxes","analytic_distribution"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].sequence | integer | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.lines[].display_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 业务行/章节/备注类型 | {"enum":["product","line_section","line_subsection","line_note"]} |
| response.data.lines[].name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.lines[].product | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named_ref"}]} |
| response.data.lines[].product | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].product | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named_ref"} |
| response.data.lines[].product.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].product.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].product_uom_id | integer/null | 可选（可能有条件限制） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].deductible_amount | string | 可选（可能有条件限制） | allOf[1]/then | Native deductible percentage, not a monetary amount; omitted when the field is unavailable. | {"pattern":"^(?:100(?:\\.0+)?&#124;(?:0&#124;[1-9][0-9]?)(?:\\.[0-9]+)?)$(?![\\s\\S])"} |
| response.data.lines[].account | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.lines[].account | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].account | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.lines[].account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.lines[].account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].quantity | string | 必填（所在对象出现时） | allOf[1]/then | 数量；单位、符号和精度依具体接口 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.lines[].price_unit | string | 必填（所在对象出现时） | allOf[1]/then | 单价；币种及符号依单据和合同 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.lines[].discount | string | 必填（所在对象出现时） | allOf[1]/then | 折扣百分比 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.lines[].price_subtotal | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.lines[].price_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.lines[].deferred_start_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.lines[].deferred_end_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.lines[].taxes | array | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.lines[].taxes[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","type_tax_use","amount_type","amount","price_include"],"resolved_ref":"#/$defs/tax"} |
| response.data.lines[].taxes[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].taxes[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.lines[].taxes[].type_tax_use | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["sale","purchase","none"]} |
| response.data.lines[].taxes[].amount_type | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.lines[].taxes[].amount | string | 必填（所在对象出现时） | allOf[1]/then | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.lines[].taxes[].price_include | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.lines[].analytic_distribution | object | 必填（所在对象出现时） | allOf[1]/then | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":{"pattern":"^(?:0&#124;-?(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9]))(?![\\s\\S])","type":"string"},"propertyNames":{"minLength":1,"type":"string"},"resolved_ref":"journal_item.search.response.schema.json#/$defs/analytic_distribution"} |
| response.data.lines[].analytic_distribution{其他键} | string | 动态键值 | allOf[1]/then |  | {"pattern":"^(?:0&#124;-?(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9]))(?![\\s\\S])"} |
| response.data.lines[] | 组合/开放结构 | 分支约束 | allOf[1]/then/allOf[1] | 行数组；增补/更新/替换语义由能力ID决定 | {"else":{"properties":{"account":{"$ref":"#/$defs/account"}}},"if":{"properties":{"display_type":{"enum":["line_section","line_subsection","line_note"]}},"required":["display_type"]},"then":{"properties":{"account":{"type":"null"}}}} |
| response.data.lines[] | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| response.data.lines[].account | null | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/then |  |  |
| response.data.lines[] | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/else | 行数组；增补/更新/替换语义由能力ID决定 |  |
| response.data.lines[].account | object | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.lines[].account.id | integer | 必填（所在对象出现时） | allOf[1]/then/allOf[1]/else |  | {"minimum":1} |
| response.data.lines[].account.code | string | 必填（所在对象出现时） | allOf[1]/then/allOf[1]/else |  | {"minLength":1} |
| response.data.lines[].account.name | string | 必填（所在对象出现时） | allOf[1]/then/allOf[1]/else | 名称/行说明 | {"minLength":1} |
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
- `verify`：same_transaction_result_and_v1_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Existing contracts and explicit native line unit/deductibility inputs covered.；引用：tests/unit/test_invoices.py, tests/unit/test_invoice_bridge.py, tests/unit/test_invoice_runtime.py, tests/unit/test_invoice_cli.py, tests/unit/test_invoice_line_inputs_reads.py
- `integration`：`implemented`；Live tests verify the fixed invoice reads against both dedicated synthetic databases and both configured companies.；引用：tests/integration/test_invoices_live.py, tests/integration/test_invoice_line_inputs_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-incoterm-update"></a>

## invoice.incoterm.update — 修改发票贸易术语

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires explicit runtime company/user scope and native ACLs. Currency/rounding/term/method/schedule changes require draft moves; review uses the native posted-only method. Auto-post configuration schedules native future work but never runs a cron or posts a move in this command. No arbitrary field/method calls or external delivery.
- 内部domain：`accounting_documents`；来源模型：account.incoterms, account.move, account.move.line, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.incoterms:read, account.move.line:read, account.move:read, account.move:write。
- 请求/响应合同：`schemas/v1/invoice.incoterm.update.request.schema.json` / `schemas/v1/invoice.incoterm.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.incoterm.update --request "@request.json" --idempotency-key "invoice.incoterm.update:1:4c6620256796888aa692672aa4fd5189" --confirm "invoice.incoterm.update"
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
      "incoterm_id": 1
    },
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["changes","move_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.incoterm_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.changes.incoterm_location | string/null | 可选（可能有条件限制） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.incoterm.update"} |
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
- `execute`：native_draft_or_posted_invoice_incoterm_metadata_write
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：native_current_payload_recheck
- `reverse`：restore_previous_setting_subject_to_native_state_and_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Focused closed-input, legacy omission/key, company/state/ACL and result binding tests; execution is required before acceptance.；引用：tests/unit/test_accounting_maintenance_batch.py
- `integration`：`implemented`；One shared public CLI/native ORM workflow passed both isolated aliases in 24.70s as uid5/su=False/company1. Two new IDs and six extensions: exact-current-root currency-rate correction/date/replay, native technical Float readback, conversion/delete fallback and missing denial; explicit foreign-bank positive/negative paired amount set/clear/replay while legacy omitted shapes remain unchanged; reconciled statement membership/detach retaining native lines, posted moves, financial snapshots and matching graphs; posted unsent invoice bank set/clear with native PDF-link sent denial; posted preferred-method wizard default and Incoterm/location set/clear; a real partially reconciled invoice retaining raw matching IDs/amounts and financial lines. Native configuration roles exist only inside the isolated transaction, never sudo business calls. Fresh tracked fixtures, both companies settings, all defaults, currencies/rates and exact caller/native group memberships roll back. Live companies are independent roots; branch context rejection has unit evidence only. PDF uses synthetic DB-only raw bytes and native linking, not generation or delivery. Wizard defaults do not make payments. All hierarchy/currency/precision/localization/hash/lock paths, fully-paid/CABA invoices, existing foreign-invoice revaluation and concurrent exactly-once are not claimed. Legacy currency.rate.record guard is unchanged. No business DB, native source/addon, configuration, service or external-send changes.；引用：tests/integration/test_accounting_maintenance_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-layout_line-create"></a>

## invoice.layout_line.create — 添加发票章节和备注行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured caller/company scope and native ACLs. Writes require a draft invoice or receipt. Terms use native HTML sanitization. Sections/subsections/notes are non-accountable native lines; layout deletion never deletes product, tax or payment-term lines. Resequencing requires all native invoice lines and only changes sequence. Fiscal refresh calls the native price/tax/account recomputation and may overwrite manual financial values. No external delivery, cron or caller-sudo.
- 内部domain：`accounting_documents`；来源模型：account.move, account.move.line, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.move.line:create, account.move.line:read, account.move:read, account.move:write。
- 请求/响应合同：`schemas/v1/invoice.layout_line.create.request.schema.json` / `schemas/v1/invoice.layout_line.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.layout_line.create --request "@request.json" --idempotency-key "invoice.layout_line.create:1:5595bc92d8747f6cdc573eb1abed21fc" --confirm "invoice.layout_line.create"
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
      "collapse_composition": false,
      "collapse_prices": false,
      "display_type": "line_note",
      "name": "Example",
      "sequence": 1
    },
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["line","move_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.line | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["collapse_composition","collapse_prices","display_type","name","sequence"]} |
| parameters.line.display_type | 未限定 | 必填（所在对象出现时） |  | 业务行/章节/备注类型 | {"enum":["line_note","line_section","line_subsection"]} |
| parameters.line.name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":500,"minLength":1,"pattern":"\\S"} |
| parameters.line.sequence | integer | 必填（所在对象出现时） |  |  | {"maximum":2147483647,"minimum":-2147483648} |
| parameters.line.collapse_prices | boolean | 必填（所在对象出现时） |  |  |  |
| parameters.line.collapse_composition | boolean | 必填（所在对象出现时） |  |  |  |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.layout_line.create"} |
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
- `execute`：fixed_native_invoice_fields_or_fiscal_action
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：native_current_payload_recheck_missing_deleted_line_is_not_found
- `reverse`：restore_previous_values_subject_to_native_state_and_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Shared closed schemas, public/runtime contracts, native layout and fiscal actions, replay and scope boundaries.；引用：tests/unit/test_invoice_presentation_batch.py
- `integration`：`implemented`；The shared rollback-only public CLI/real-ORM smoke passed both isolated aliases as uid 5 with su=False: all eight new IDs and seven immediate replays; native sanitized terms, shipping/responsible settings; sections, subsections, notes, native zero-accounting/parent/order and scoped keyset pagination; existing empty/long native labels; layout edits preserve totals; native fiscal price/tax/account recomputation with native balance and dynamic-sync guards; product-line deletion, incomplete ordering, posted and foreign-company denial; fresh-cursor business-record and temporary-group rollback. No external delivery, cron, addon modification or service changes.；引用：tests/integration/test_invoice_presentation_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-layout_line-delete"></a>

## invoice.layout_line.delete — 删除发票章节和备注行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured caller/company scope and native ACLs. Writes require a draft invoice or receipt. Terms use native HTML sanitization. Sections/subsections/notes are non-accountable native lines; layout deletion never deletes product, tax or payment-term lines. Resequencing requires all native invoice lines and only changes sequence. Fiscal refresh calls the native price/tax/account recomputation and may overwrite manual financial values. No external delivery, cron or caller-sudo.
- 内部domain：`accounting_documents`；来源模型：account.move, account.move.line, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.move.line:read, account.move.line:unlink, account.move:read, account.move:write。
- 请求/响应合同：`schemas/v1/invoice.layout_line.delete.request.schema.json` / `schemas/v1/invoice.layout_line.delete.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.layout_line.delete --request "@request.json" --idempotency-key "invoice.layout_line.delete:1:b38b8ec62e4d767389ac061f3dff904d" --confirm "invoice.layout_line.delete"
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
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["line_id","move_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.layout_line.delete"} |
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
- `execute`：fixed_native_invoice_fields_or_fiscal_action
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：native_current_payload_recheck_missing_deleted_line_is_not_found
- `reverse`：recreate_layout_line_explicitly_with_new_native_identifier

### 已登记测试与证据范围

- `unit`：`implemented`；Shared closed schemas, public/runtime contracts, native layout and fiscal actions, replay and scope boundaries.；引用：tests/unit/test_invoice_presentation_batch.py
- `integration`：`implemented`；The shared rollback-only public CLI/real-ORM smoke passed both isolated aliases as uid 5 with su=False: all eight new IDs and seven immediate replays; native sanitized terms, shipping/responsible settings; sections, subsections, notes, native zero-accounting/parent/order and scoped keyset pagination; existing empty/long native labels; layout edits preserve totals; native fiscal price/tax/account recomputation with native balance and dynamic-sync guards; product-line deletion, incomplete ordering, posted and foreign-company denial; fresh-cursor business-record and temporary-group rollback. No external delivery, cron, addon modification or service changes.；引用：tests/integration/test_invoice_presentation_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-layout_line-list"></a>

## invoice.layout_line.list — 查询发票章节和备注行

- 类型：只读；静态状态：`unconfigured`；handler：`invoice_layout_line_list`。
- 状态原因：`runtime_context_required` — Requires configured caller/company scope and native ACLs. Writes require a draft invoice or receipt. Terms use native HTML sanitization. Sections/subsections/notes are non-accountable native lines; layout deletion never deletes product, tax or payment-term lines. Resequencing requires all native invoice lines and only changes sequence. Fiscal refresh calls the native price/tax/account recomputation and may overwrite manual financial values. No external delivery, cron or caller-sudo.
- 内部domain：`accounting_documents`；来源模型：res.company, account.move, account.move.line；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/invoice.layout_line.list.request.schema.json` / `schemas/v1/invoice.layout_line.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read invoice.layout_line.list --request "@request.json"
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
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.layout_line.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["collapse_composition","collapse_prices","company_id","display_type","id","move_id","name","parent_id","sequence"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].move_id | integer | 必填（所在对象出现时） | oneOf[2] | 会计单据记录ID | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].display_type | 未限定 | 必填（所在对象出现时） | oneOf[2] | 业务行/章节/备注类型 | {"enum":["line_note","line_section","line_subsection"]} |
| response.data.items[].name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 |  |
| response.data.items[].sequence | integer | 必填（所在对象出现时） | oneOf[2] |  | {"maximum":2147483647,"minimum":-2147483648} |
| response.data.items[].collapse_prices | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].collapse_composition | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].parent_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["collapse_composition","collapse_prices","company_id","display_type","id","move_id","name","parent_id","sequence"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].move_id | integer | 必填（所在对象出现时） | allOf[1]/then | 会计单据记录ID | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].display_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 业务行/章节/备注类型 | {"enum":["line_note","line_section","line_subsection"]} |
| response.data.items[].name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 |  |
| response.data.items[].sequence | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"maximum":2147483647,"minimum":-2147483648} |
| response.data.items[].collapse_prices | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].collapse_composition | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].parent_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
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
- `execute`：fixed_native_invoice_presentation_read
- `verify`：closed_response_schema_validation
- `idempotency`：read_only
- `reverse`：not_applicable

### 已登记测试与证据范围

- `unit`：`implemented`；Shared closed schemas, public/runtime contracts, native layout and fiscal actions, replay and scope boundaries.；引用：tests/unit/test_invoice_presentation_batch.py
- `integration`：`implemented`；The shared rollback-only public CLI/real-ORM smoke passed both isolated aliases as uid 5 with su=False: all eight new IDs and seven immediate replays; native sanitized terms, shipping/responsible settings; sections, subsections, notes, native zero-accounting/parent/order and scoped keyset pagination; existing empty/long native labels; layout edits preserve totals; native fiscal price/tax/account recomputation with native balance and dynamic-sync guards; product-line deletion, incomplete ordering, posted and foreign-company denial; fresh-cursor business-record and temporary-group rollback. No external delivery, cron, addon modification or service changes.；引用：tests/integration/test_invoice_presentation_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-layout_line-update"></a>

## invoice.layout_line.update — 修改发票章节和备注行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured caller/company scope and native ACLs. Writes require a draft invoice or receipt. Terms use native HTML sanitization. Sections/subsections/notes are non-accountable native lines; layout deletion never deletes product, tax or payment-term lines. Resequencing requires all native invoice lines and only changes sequence. Fiscal refresh calls the native price/tax/account recomputation and may overwrite manual financial values. No external delivery, cron or caller-sudo.
- 内部domain：`accounting_documents`；来源模型：account.move, account.move.line, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.move.line:read, account.move.line:write, account.move:read, account.move:write。
- 请求/响应合同：`schemas/v1/invoice.layout_line.update.request.schema.json` / `schemas/v1/invoice.layout_line.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.layout_line.update --request "@request.json" --idempotency-key "invoice.layout_line.update:1:b69272a62b30ad9aed89039428a25ff8" --confirm "invoice.layout_line.update"
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
      "display_type": "line_note"
    },
    "line_id": 1,
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["changes","line_id","move_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1,"required_in_object":[]} |
| parameters.changes.display_type | 未限定 | 可选（可能有条件限制） |  | 业务行/章节/备注类型 | {"enum":["line_note","line_section","line_subsection"]} |
| parameters.changes.name | string | 可选（可能有条件限制） |  | 名称/行说明 | {"maxLength":500,"minLength":1,"pattern":"\\S"} |
| parameters.changes.sequence | integer | 可选（可能有条件限制） |  |  | {"maximum":2147483647,"minimum":-2147483648} |
| parameters.changes.collapse_prices | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.changes.collapse_composition | boolean | 可选（可能有条件限制） |  |  |  |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.layout_line.update"} |
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
- `execute`：fixed_native_invoice_fields_or_fiscal_action
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：native_current_payload_recheck_missing_deleted_line_is_not_found
- `reverse`：restore_previous_values_subject_to_native_state_and_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Shared closed schemas, public/runtime contracts, native layout and fiscal actions, replay and scope boundaries.；引用：tests/unit/test_invoice_presentation_batch.py
- `integration`：`implemented`；The shared rollback-only public CLI/real-ORM smoke passed both isolated aliases as uid 5 with su=False: all eight new IDs and seven immediate replays; native sanitized terms, shipping/responsible settings; sections, subsections, notes, native zero-accounting/parent/order and scoped keyset pagination; existing empty/long native labels; layout edits preserve totals; native fiscal price/tax/account recomputation with native balance and dynamic-sync guards; product-line deletion, incomplete ordering, posted and foreign-company denial; fresh-cursor business-record and temporary-group rollback. No external delivery, cron, addon modification or service changes.；引用：tests/integration/test_invoice_presentation_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-line-create"></a>

## invoice.line.create — 新增草稿发票或账单业务行

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`concurrent_idempotency_limit` — The handler rechecks the natural rich-line payload before creation, but Odoo provides no database uniqueness constraint for concurrent exactly-once business-line creation.
- 内部domain：`invoices_and_bills`；来源模型：res.company, res.partner, product.product, account.account, account.tax, account.move, account.move.line, account.analytic.account；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：res.partner:read, product.product:read, account.account:read, account.tax:read, account.analytic.account:read, account.move:read, account.move:write, account.move.line:read, account.move.line:create, account.move.line:write, account.move.line:unlink。
- 请求/响应合同：`schemas/v1/invoice.line.create.request.schema.json` / `schemas/v1/invoice.line.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.line.create --request "@request.json" --idempotency-key "invoice.line.create:1:79174efe1bdee81a061a97c84f327dfe" --confirm "invoice.line.create"
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
    "move_id": 1,
    "line": {
      "name": "Example",
      "quantity": "1",
      "discount": "1",
      "tax_ids": [],
      "product_id": 1,
      "account_id": 1,
      "price_unit": "1"
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id","line"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.line | object | 必填（所在对象出现时） |  | Optional product_uom_id requires a product-backed line; deductible_amount is a native percentage, not money. | {"additionalProperties":false,"allOf":[{"if":{"required":["product_uom_id"]},"then":{"properties":{"product_id":{"minimum":1,"type":"integer"}}}}],"dependentRequired":{"deferred_end_date":["deferred_start_date"],"deferred_start_date":["deferred_end_date"]},"oneOf":[{"properties":{"deferred_end_date":{"type":"null"},"deferred_start_date":{"type":"null"}}},{"properties":{"deferred_end_date":{"type":"string"},"deferred_start_date":{"type":"string"}},"required":["deferred_start_date","deferred_end_date"]}],"required_in_object":["name","product_id","account_id","quantity","price_unit","discount","tax_ids"],"resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line"} |
| parameters.line.name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":500,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$"} |
| parameters.line.product_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.line.product_uom_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.line.deductible_amount | string | 可选（可能有条件限制） |  | Native deductibility percentage, not a monetary amount. | {"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])","resolved_ref":"#/$defs/percentage_decimal"} |
| parameters.line.account_id | integer | 必填（所在对象出现时） |  | 会计科目ID | {"minimum":1} |
| parameters.line.quantity | string | 必填（所在对象出现时） |  | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/signed_decimal"} |
| parameters.line.price_unit | string | 必填（所在对象出现时） |  | 单价；币种及符号依单据和合同 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/signed_decimal"} |
| parameters.line.discount | string | 必填（所在对象出现时） |  | 折扣百分比 | {"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])","resolved_ref":"#/$defs/percentage_decimal"} |
| parameters.line.tax_ids | array | 必填（所在对象出现时） |  | 应用税ID数组 | {"uniqueItems":true} |
| parameters.line.tax_ids[] | integer | 每个数组元素 |  | 应用税ID数组 | {"minimum":1} |
| parameters.line.analytic_distribution | 组合/开放结构 | 可选（可能有条件限制） |  | 分析分摊映射；写入与读回约束可能不同 | {"oneOf":[{"type":"null"},{"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"},"type":"object"}],"resolved_ref":"#/$defs/analytic_distribution"} |
| parameters.line.analytic_distribution | null | 分支约束 | oneOf[1] | 分析分摊映射；写入与读回约束可能不同 |  |
| parameters.line.analytic_distribution | object | 分支约束 | oneOf[2] | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"}} |
| parameters.line.analytic_distribution{其他键} | string | 动态键值 | oneOf[2] |  | {"maxLength":8,"pattern":"^(?:100&#124;(?:[1-9][0-9]?)(?:\\.[0-9]{0,3}[1-9])?&#124;0\\.[0-9]{0,3}[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/analytic_percentage"} |
| parameters.line.deferred_start_date | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.line.deferred_end_date | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.line | 未限定 | 分支约束 | oneOf[1] |  |  |
| parameters.line.deferred_start_date | null | 可选（可能有条件限制） | oneOf[1] |  |  |
| parameters.line.deferred_end_date | null | 可选（可能有条件限制） | oneOf[1] |  |  |
| parameters.line | 未限定 | 分支约束 | oneOf[2] |  | {"required_in_object":["deferred_start_date","deferred_end_date"]} |
| parameters.line.deferred_start_date | string | 必填（所在对象出现时） | oneOf[2] |  |  |
| parameters.line.deferred_end_date | string | 必填（所在对象出现时） | oneOf[2] |  |  |
| parameters.line | 组合/开放结构 | 分支约束 | allOf[1] |  | {"if":{"required":["product_uom_id"]},"then":{"properties":{"product_id":{"minimum":1,"type":"integer"}}}} |
| parameters.line | 未限定 | 条件分支 | allOf[1]/then |  |  |
| parameters.line.product_id | integer | 可选（可能有条件限制） | allOf[1]/then |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.line.create"} |
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
- `execute`：fixed_native_draft_invoice_business_line_create
- `verify`：same_transaction_created_business_line_identity_payload_parent_totals_and_response_schema_validation
- `idempotency`：natural_line_payload_recheck_without_database_uniqueness_or_concurrent_exactly_once_guarantee
- `reverse`：invoice.line.delete

### 已登记测试与证据范围

- `unit`：`implemented`；Existing contracts and explicit native line unit/deductibility inputs covered.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_draft_document_maintenance_runtime.py, tests/unit/test_draft_document_maintenance_schemas.py, tests/unit/test_capability_registry.py, tests/unit/test_accounting_entry_membership_batch.py, tests/unit/test_invoice_line_inputs_contract.py, tests/unit/test_invoice_line_inputs_runtime.py
- `integration`：`implemented`；Shared native smoke passed; full rollback.；引用：tests/integration/test_draft_document_maintenance_live.py, tests/integration/test_accounting_entry_membership_batch_live.py, tests/integration/test_invoice_line_inputs_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-line-deductibility-update"></a>

## invoice.line.deductibility.update — 修改草稿账单行抵扣比例

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Fixed line-targeted operations are implemented; native accounting, reference and analytic synchronization ACLs apply. Runtime context and native acceptance are not an unrestricted permission claim.
- 内部domain：`invoice`；来源模型：account.account, account.fiscal.position, account.journal, account.move, account.move.line, account.tax, product.product, product.template, res.company, res.currency；向导：无。
- 必需模块：account, analytic, product, uom；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.account:read, account.fiscal.position:read, account.journal:read, account.move.line:create, account.move.line:read, account.move.line:unlink, account.move.line:write, account.move:read, account.move:write, account.tax:read, product.product:read, product.template:read, res.company:read, res.currency:read。
- 请求/响应合同：`schemas/v1/invoice.line.deductibility.update.request.schema.json` / `schemas/v1/invoice.line.deductibility.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.line.deductibility.update --request "@request.json" --idempotency-key "invoice.line.deductibility.update:1:414d45b1d5381ee15ecff0d0e97719d4" --confirm "invoice.line.deductibility.update"
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
    "move_id": 1,
    "line_id": 1,
    "deductible_amount": "1"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id","line_id","deductible_amount"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.deductible_amount | string | 必填（所在对象出现时） |  | 可抵扣百分比，不是可抵扣货币金额 | {"pattern":"^(?:100&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]{1,2})?)$"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.line.deductibility.update"} |
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
- `execute`：native_line_or_atomic_parent_write_with_closed_existing_targets_as_business_user
- `verify`：same_transaction_parent_line_readback_with_native_constraints_and_recomputation
- `idempotency`：serial_current_target_recheck_without_operation_store_or_concurrent_exactly_once
- `reverse`：restore_prior_values_subject_to_native_constraints

### 已登记测试与证据范围

- `unit`：`implemented`；Closed typed parameters, bound parent/line results, shared CLI/schemas/confirmation/keys and target-bound pagination; native behavior is covered separately.；引用：tests/unit/test_journal_item_processing_batch.py
- `integration`：`implemented`；One shared public CLI/real-ORM workflow passed both isolated aliases in21.41s as uid5/su=False/company1: bound line reads, target analytic keyset pages and actual partial/full reconciliation; native atomic draft entry updates preserve IDs and reject imbalance; posted maturity/full analytic replacement/clearing preserve financial fields and replay avoids child recreation; draft product UOM reprices/retaxes natively and purchase deductibility50/0/100 synchronizes native rows. Temporary analytic permission and an admin-created purchase-journal default-account fixture are transaction-local; missing/foreign parent and parent-line mismatch, posted financial writes and draft sales partial-deductibility are rejected. All objects/journal/mail alias and exact groups roll back in fresh cursors. First numeric-conversion and second analytic-sign failures retained, not acceptance; no concurrent exactly-once, receipt, business DB or real external-send claim.；引用：tests/integration/test_journal_item_processing_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-line-delete"></a>

## invoice.line.delete — 删除草稿发票或账单业务行

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`deleted_record_tombstone_unavailable` — The handler verifies business-line absence and the synchronized parent invoice after deletion, but keeps no persistent tombstone for later retry attribution.
- 内部domain：`invoices_and_bills`；来源模型：res.company, account.move, account.move.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.move:read, account.move:write, account.move.line:read, account.move.line:create, account.move.line:write, account.move.line:unlink。
- 请求/响应合同：`schemas/v1/invoice.line.delete.request.schema.json` / `schemas/v1/invoice.line.delete.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.line.delete --request "@request.json" --idempotency-key "invoice.line.delete:1:1" --confirm "invoice.line.delete"
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
    "move_id": 1,
    "line_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id","line_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.line.delete"} |
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
- `execute`：fixed_native_draft_invoice_business_line_unlink
- `verify`：same_transaction_target_line_absence_parent_dynamic_lines_totals_and_response_schema_validation
- `idempotency`：record_absence_recheck_without_operation_store_or_persistent_tombstone
- `reverse`：recreate_the_deleted_business_line_outside_this_capability

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover confirmation, draft and business-line boundaries, source-preserving native unlink, dynamic-line synchronization, absence verification, result binding, registry descriptor, and schemas.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_draft_document_maintenance_runtime.py, tests/unit/test_draft_document_maintenance_schemas.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases through the public CLI as uid 5 with su=False, exercising all six draft-maintenance commands, five immediate replays, and fresh-cursor business-data and temporary-group rollback verification.；引用：tests/integration/test_draft_document_maintenance_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-line-unit-assign"></a>

## invoice.line.unit.assign — 设置草稿发票行计量单位

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Fixed line-targeted operations are implemented; native accounting, reference and analytic synchronization ACLs apply. Runtime context and native acceptance are not an unrestricted permission claim.
- 内部domain：`invoice`；来源模型：account.account, account.fiscal.position, account.journal, account.move, account.move.line, account.tax, product.product, product.template, res.company, res.currency, uom.uom；向导：无。
- 必需模块：account, analytic, product, uom；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.account:read, account.fiscal.position:read, account.journal:read, account.move.line:create, account.move.line:read, account.move.line:unlink, account.move.line:write, account.move:read, account.move:write, account.tax:read, product.product:read, product.template:read, res.company:read, res.currency:read, uom.uom:read。
- 请求/响应合同：`schemas/v1/invoice.line.unit.assign.request.schema.json` / `schemas/v1/invoice.line.unit.assign.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.line.unit.assign --request "@request.json" --idempotency-key "invoice.line.unit.assign:1:6c3b9c7a0adb6844e40275b084e54833" --confirm "invoice.line.unit.assign"
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
    "move_id": 1,
    "line_id": 1,
    "product_uom_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id","line_id","product_uom_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.product_uom_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.line.unit.assign"} |
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
- `execute`：native_line_or_atomic_parent_write_with_closed_existing_targets_as_business_user
- `verify`：same_transaction_parent_line_readback_with_native_constraints_and_recomputation
- `idempotency`：serial_current_target_recheck_without_operation_store_or_concurrent_exactly_once
- `reverse`：restore_prior_values_subject_to_native_constraints

### 已登记测试与证据范围

- `unit`：`implemented`；Closed typed parameters, bound parent/line results, shared CLI/schemas/confirmation/keys and target-bound pagination; native behavior is covered separately.；引用：tests/unit/test_journal_item_processing_batch.py
- `integration`：`implemented`；One shared public CLI/real-ORM workflow passed both isolated aliases in21.41s as uid5/su=False/company1: bound line reads, target analytic keyset pages and actual partial/full reconciliation; native atomic draft entry updates preserve IDs and reject imbalance; posted maturity/full analytic replacement/clearing preserve financial fields and replay avoids child recreation; draft product UOM reprices/retaxes natively and purchase deductibility50/0/100 synchronizes native rows. Temporary analytic permission and an admin-created purchase-journal default-account fixture are transaction-local; missing/foreign parent and parent-line mismatch, posted financial writes and draft sales partial-deductibility are rejected. All objects/journal/mail alias and exact groups roll back in fresh cursors. First numeric-conversion and second analytic-sign failures retained, not acceptance; no concurrent exactly-once, receipt, business DB or real external-send claim.；引用：tests/integration/test_journal_item_processing_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-line-update"></a>

## invoice.line.update — 更新草稿发票或账单业务行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`invoices_and_bills`；来源模型：res.company, res.partner, product.product, account.account, account.tax, account.move, account.move.line, account.analytic.account；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：res.partner:read, product.product:read, account.account:read, account.tax:read, account.analytic.account:read, account.move:read, account.move:write, account.move.line:read, account.move.line:create, account.move.line:write, account.move.line:unlink。
- 请求/响应合同：`schemas/v1/invoice.line.update.request.schema.json` / `schemas/v1/invoice.line.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.line.update --request "@request.json" --idempotency-key "invoice.line.update:1:1:663c40c5fc625d44d00a597ae77ce292" --confirm "invoice.line.update"
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
    "move_id": 1,
    "line_id": 1,
    "changes": {
      "name": "Example"
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id","line_id","changes"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"allOf":[{"if":{"properties":{"deferred_start_date":{"type":"null"}},"required":["deferred_start_date"]},"then":{"properties":{"deferred_end_date":{"type":"null"}}}},{"if":{"properties":{"deferred_end_date":{"type":"null"}},"required":["deferred_end_date"]},"then":{"properties":{"deferred_start_date":{"type":"null"}}}},{"if":{"required":["product_uom_id","product_id"]},"then":{"properties":{"product_id":{"minimum":1,"type":"integer"}}}}],"dependentRequired":{"deferred_end_date":["deferred_start_date"],"deferred_start_date":["deferred_end_date"]},"minProperties":1} |
| parameters.changes.name | string | 可选（可能有条件限制） |  | 名称/行说明 | {"maxLength":500,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$","resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/name"} |
| parameters.changes.product_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/product_id"} |
| parameters.changes.product_uom_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/product_uom_id"} |
| parameters.changes.deductible_amount | string | 可选（可能有条件限制） |  | Native deductibility percentage, not a monetary amount. | {"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])","resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/deductible_amount"} |
| parameters.changes.account_id | integer | 可选（可能有条件限制） |  | 会计科目ID | {"minimum":1,"resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/account_id"} |
| parameters.changes.quantity | string | 可选（可能有条件限制） |  | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/quantity"} |
| parameters.changes.price_unit | string | 可选（可能有条件限制） |  | 单价；币种及符号依单据和合同 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/price_unit"} |
| parameters.changes.discount | string | 可选（可能有条件限制） |  | 折扣百分比 | {"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])","resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/discount"} |
| parameters.changes.tax_ids | array | 可选（可能有条件限制） |  | 应用税ID数组 | {"resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/tax_ids","uniqueItems":true} |
| parameters.changes.tax_ids[] | integer | 每个数组元素 |  | 应用税ID数组 | {"minimum":1} |
| parameters.changes.analytic_distribution | 组合/开放结构 | 可选（可能有条件限制） |  | 分析分摊映射；写入与读回约束可能不同 | {"oneOf":[{"type":"null"},{"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"},"type":"object"}],"resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/analytic_distribution"} |
| parameters.changes.analytic_distribution | null | 分支约束 | oneOf[1] | 分析分摊映射；写入与读回约束可能不同 |  |
| parameters.changes.analytic_distribution | object | 分支约束 | oneOf[2] | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"}} |
| parameters.changes.analytic_distribution{其他键} | string | 动态键值 | oneOf[2] |  | {"maxLength":8,"pattern":"^(?:100&#124;(?:[1-9][0-9]?)(?:\\.[0-9]{0,3}[1-9])?&#124;0\\.[0-9]{0,3}[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/analytic_percentage"} |
| parameters.changes.deferred_start_date | string/null | 可选（可能有条件限制） |  |  | {"format":"date","resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/deferred_start_date"} |
| parameters.changes.deferred_end_date | string/null | 可选（可能有条件限制） |  |  | {"format":"date","resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/deferred_end_date"} |
| parameters.changes | 组合/开放结构 | 分支约束 | allOf[1] | 仅提交拟变更字段，非整条记录 | {"if":{"properties":{"deferred_start_date":{"type":"null"}},"required":["deferred_start_date"]},"then":{"properties":{"deferred_end_date":{"type":"null"}}}} |
| parameters.changes | 未限定 | 条件分支 | allOf[1]/then | 仅提交拟变更字段，非整条记录 |  |
| parameters.changes.deferred_end_date | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| parameters.changes | 组合/开放结构 | 分支约束 | allOf[2] | 仅提交拟变更字段，非整条记录 | {"if":{"properties":{"deferred_end_date":{"type":"null"}},"required":["deferred_end_date"]},"then":{"properties":{"deferred_start_date":{"type":"null"}}}} |
| parameters.changes | 未限定 | 条件分支 | allOf[2]/then | 仅提交拟变更字段，非整条记录 |  |
| parameters.changes.deferred_start_date | null | 可选（可能有条件限制） | allOf[2]/then |  |  |
| parameters.changes | 组合/开放结构 | 分支约束 | allOf[3] | 仅提交拟变更字段，非整条记录 | {"if":{"required":["product_uom_id","product_id"]},"then":{"properties":{"product_id":{"minimum":1,"type":"integer"}}}} |
| parameters.changes | 未限定 | 条件分支 | allOf[3]/then | 仅提交拟变更字段，非整条记录 |  |
| parameters.changes.product_id | integer | 可选（可能有条件限制） | allOf[3]/then |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.line.update"} |
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
- `execute`：fixed_native_draft_invoice_business_line_update
- `verify`：same_transaction_target_business_line_payload_parent_totals_and_response_schema_validation
- `idempotency`：target_line_payload_state_check_before_native_write
- `reverse`：repeat_update_with_previous_business_line_values

### 已登记测试与证据范围

- `unit`：`implemented`；Existing contracts and explicit native line unit/deductibility inputs covered.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_draft_document_maintenance_runtime.py, tests/unit/test_draft_document_maintenance_schemas.py, tests/unit/test_capability_registry.py, tests/unit/test_accounting_entry_membership_batch.py, tests/unit/test_invoice_line_inputs_contract.py, tests/unit/test_invoice_line_inputs_runtime.py
- `integration`：`implemented`；Shared native smoke passed; full rollback.；引用：tests/integration/test_draft_document_maintenance_live.py, tests/integration/test_accounting_entry_membership_batch_live.py, tests/integration/test_invoice_line_inputs_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-lines-add"></a>

## invoice.lines.add — 保留既有行，批量追加草稿发票或账单业务行

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`serial_state_replay_only` — Serial expected membership replay; not concurrent exactly-once.
- 内部domain：`invoices_and_bills`；来源模型：res.company, res.partner, product.product, account.account, account.tax, account.move, account.move.line, account.analytic.account；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：res.partner:read, product.product:read, account.account:read, account.tax:read, account.analytic.account:read, account.move:read, account.move:write, account.move.line:read, account.move.line:create, account.move.line:write, account.move.line:unlink。
- 请求/响应合同：`schemas/v1/invoice.lines.add.request.schema.json` / `schemas/v1/invoice.lines.add.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.lines.add --request "@request.json" --idempotency-key "invoice.lines.add:1:99e847429ed07d6d3abd35d40ea40b87" --confirm "invoice.lines.add"
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
    "move_id": 1,
    "expected_line_ids": [],
    "lines": [
      {
        "name": "Example",
        "quantity": "1",
        "discount": "1",
        "tax_ids": [],
        "product_id": 1,
        "account_id": 1,
        "price_unit": "1"
      }
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id","expected_line_ids","lines"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.expected_line_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| parameters.expected_line_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.lines | array | 必填（所在对象出现时） |  | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":200,"minItems":1} |
| parameters.lines[] | object | 每个数组元素 |  | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"allOf":[{"if":{"required":["product_uom_id"]},"then":{"properties":{"product_id":{"minimum":1,"type":"integer"}}}}],"dependentRequired":{"deferred_end_date":["deferred_start_date"],"deferred_start_date":["deferred_end_date"]},"oneOf":[{"properties":{"deferred_end_date":{"type":"null"},"deferred_start_date":{"type":"null"}}},{"properties":{"deferred_end_date":{"type":"string"},"deferred_start_date":{"type":"string"}},"required":["deferred_start_date","deferred_end_date"]}],"required_in_object":["name","product_id","account_id","quantity","price_unit","discount","tax_ids"],"resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line"} |
| parameters.lines[].name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":500,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$"} |
| parameters.lines[].product_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.lines[].product_uom_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.lines[].deductible_amount | string | 可选（可能有条件限制） |  | Native deductibility percentage, not a monetary amount. | {"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])","resolved_ref":"#/$defs/percentage_decimal"} |
| parameters.lines[].account_id | integer | 必填（所在对象出现时） |  | 会计科目ID | {"minimum":1} |
| parameters.lines[].quantity | string | 必填（所在对象出现时） |  | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/signed_decimal"} |
| parameters.lines[].price_unit | string | 必填（所在对象出现时） |  | 单价；币种及符号依单据和合同 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/signed_decimal"} |
| parameters.lines[].discount | string | 必填（所在对象出现时） |  | 折扣百分比 | {"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])","resolved_ref":"#/$defs/percentage_decimal"} |
| parameters.lines[].tax_ids | array | 必填（所在对象出现时） |  | 应用税ID数组 | {"uniqueItems":true} |
| parameters.lines[].tax_ids[] | integer | 每个数组元素 |  | 应用税ID数组 | {"minimum":1} |
| parameters.lines[].analytic_distribution | 组合/开放结构 | 可选（可能有条件限制） |  | 分析分摊映射；写入与读回约束可能不同 | {"oneOf":[{"type":"null"},{"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"},"type":"object"}],"resolved_ref":"#/$defs/analytic_distribution"} |
| parameters.lines[].analytic_distribution | null | 分支约束 | oneOf[1] | 分析分摊映射；写入与读回约束可能不同 |  |
| parameters.lines[].analytic_distribution | object | 分支约束 | oneOf[2] | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"}} |
| parameters.lines[].analytic_distribution{其他键} | string | 动态键值 | oneOf[2] |  | {"maxLength":8,"pattern":"^(?:100&#124;(?:[1-9][0-9]?)(?:\\.[0-9]{0,3}[1-9])?&#124;0\\.[0-9]{0,3}[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/analytic_percentage"} |
| parameters.lines[].deferred_start_date | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.lines[].deferred_end_date | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.lines[] | 未限定 | 分支约束 | oneOf[1] | 行数组；增补/更新/替换语义由能力ID决定 |  |
| parameters.lines[].deferred_start_date | null | 可选（可能有条件限制） | oneOf[1] |  |  |
| parameters.lines[].deferred_end_date | null | 可选（可能有条件限制） | oneOf[1] |  |  |
| parameters.lines[] | 未限定 | 分支约束 | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"required_in_object":["deferred_start_date","deferred_end_date"]} |
| parameters.lines[].deferred_start_date | string | 必填（所在对象出现时） | oneOf[2] |  |  |
| parameters.lines[].deferred_end_date | string | 必填（所在对象出现时） | oneOf[2] |  |  |
| parameters.lines[] | 组合/开放结构 | 分支约束 | allOf[1] | 行数组；增补/更新/替换语义由能力ID决定 | {"if":{"required":["product_uom_id"]},"then":{"properties":{"product_id":{"minimum":1,"type":"integer"}}}} |
| parameters.lines[] | 未限定 | 条件分支 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| parameters.lines[].product_id | integer | 可选（可能有条件限制） | allOf[1]/then |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.lines.add"} |
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

- `preview`：exact_confirmation_closed_contract
- `execute`：single_native_parent_business_line_commands
- `verify`：business_layout_membership_and_explicit_values_with_native_dynamic_sync
- `idempotency`：serial_expected_business_ids_and_added_payload_multiset
- `reverse`：delete_appended_business_rows

### 已登记测试与证据范围

- `unit`：`implemented`；Bulk closed contracts, native parent writes and business row membership covered.；引用：tests/unit/test_invoice_bulk_lines_contract.py, tests/unit/test_invoice_bulk_lines_runtime.py, tests/unit/test_document_search_batch_cli.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；Shared native document search and invoice bulk smoke passed; full rollback.；引用：tests/integration/test_document_search_bulk_lines_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-lines-remove"></a>

## invoice.lines.remove — 保留其余行，批量删除草稿发票或账单业务行

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`deleted_record_tombstone_unavailable` — No deletion tombstone; missing targets reject retries instead of claiming attributable replay.
- 内部domain：`invoices_and_bills`；来源模型：res.company, account.move, account.move.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.move:read, account.move:write, account.move.line:read, account.move.line:create, account.move.line:write, account.move.line:unlink。
- 请求/响应合同：`schemas/v1/invoice.lines.remove.request.schema.json` / `schemas/v1/invoice.lines.remove.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.lines.remove --request "@request.json" --idempotency-key "invoice.lines.remove:1:5de2ffcced6cd634927b39bfad7d193f" --confirm "invoice.lines.remove"
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
    "move_id": 1,
    "line_ids": [
      1
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id","line_ids"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.line_ids | array | 必填（所在对象出现时） |  | 行记录ID数组 | {"maxItems":200,"minItems":1,"uniqueItems":true} |
| parameters.line_ids[] | integer | 每个数组元素 |  | 行记录ID数组 | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.lines.remove"} |
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

- `preview`：exact_confirmation_closed_contract
- `execute`：single_native_parent_business_line_delete_commands
- `verify`：deleted_targets_absent_survivor_inputs_ids_sources_native_dynamic_sync
- `idempotency`：content_key_missing_targets_rejected_no_tombstone
- `reverse`：recreate_deleted_business_rows_outside_this_capability

### 已登记测试与证据范围

- `unit`：`implemented`；Closed bulk deletion contract, one parent write, survivor preservation and absence rejection covered.；引用：tests/unit/test_invoice_lines_remove_contract.py, tests/unit/test_invoice_lines_remove_runtime.py, tests/unit/test_business_line_search_remove_cli.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；Shared native business-line search and bulk deletion smoke passed; full rollback.；引用：tests/integration/test_business_line_search_remove_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-lines-replace"></a>

## invoice.lines.replace — 替换草稿发票或账单的全部业务行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`invoices_and_bills`；来源模型：res.company, res.partner, product.product, account.account, account.tax, account.move, account.move.line, account.analytic.account；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：res.partner:read, product.product:read, account.account:read, account.tax:read, account.move:read, account.move:write, account.move.line:read, account.move.line:create, account.move.line:write, account.move.line:unlink。
- 请求/响应合同：`schemas/v1/invoice.lines.replace.request.schema.json` / `schemas/v1/invoice.lines.replace.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.lines.replace --request "@request.json" --idempotency-key "invoice.lines.replace:1:8658557eb261f83db602358b6fbb05d6" --confirm "invoice.lines.replace"
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
    "move_id": 1,
    "lines": [
      {
        "name": "Example",
        "quantity": "1",
        "discount": "1",
        "tax_ids": [],
        "product_id": 1,
        "account_id": 1,
        "price_unit": "1"
      }
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id","lines"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.lines | array | 必填（所在对象出现时） |  | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":500,"minItems":1} |
| parameters.lines[] | object | 每个数组元素 |  | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"allOf":[{"if":{"required":["product_uom_id"]},"then":{"properties":{"product_id":{"minimum":1,"type":"integer"}}}}],"dependentRequired":{"deferred_end_date":["deferred_start_date"],"deferred_start_date":["deferred_end_date"]},"oneOf":[{"properties":{"deferred_end_date":{"type":"null"},"deferred_start_date":{"type":"null"}}},{"properties":{"deferred_end_date":{"type":"string"},"deferred_start_date":{"type":"string"}},"required":["deferred_start_date","deferred_end_date"]}],"required_in_object":["name","product_id","account_id","quantity","price_unit","discount","tax_ids"]} |
| parameters.lines[].name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":500,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$"} |
| parameters.lines[].product_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.lines[].product_uom_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.lines[].deductible_amount | string | 可选（可能有条件限制） |  | Native deductibility percentage, not a monetary amount. | {"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])","resolved_ref":"#/$defs/percentage_decimal"} |
| parameters.lines[].account_id | integer | 必填（所在对象出现时） |  | 会计科目ID | {"minimum":1} |
| parameters.lines[].quantity | string | 必填（所在对象出现时） |  | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/signed_decimal"} |
| parameters.lines[].price_unit | string | 必填（所在对象出现时） |  | 单价；币种及符号依单据和合同 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/signed_decimal"} |
| parameters.lines[].discount | string | 必填（所在对象出现时） |  | 折扣百分比 | {"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])","resolved_ref":"#/$defs/percentage_decimal"} |
| parameters.lines[].tax_ids | array | 必填（所在对象出现时） |  | 应用税ID数组 | {"uniqueItems":true} |
| parameters.lines[].tax_ids[] | integer | 每个数组元素 |  | 应用税ID数组 | {"minimum":1} |
| parameters.lines[].analytic_distribution | 组合/开放结构 | 可选（可能有条件限制） |  | 分析分摊映射；写入与读回约束可能不同 | {"oneOf":[{"type":"null"},{"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"},"type":"object"}],"resolved_ref":"#/$defs/analytic_distribution"} |
| parameters.lines[].analytic_distribution | null | 分支约束 | oneOf[1] | 分析分摊映射；写入与读回约束可能不同 |  |
| parameters.lines[].analytic_distribution | object | 分支约束 | oneOf[2] | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"}} |
| parameters.lines[].analytic_distribution{其他键} | string | 动态键值 | oneOf[2] |  | {"maxLength":8,"pattern":"^(?:100&#124;(?:[1-9][0-9]?)(?:\\.[0-9]{0,3}[1-9])?&#124;0\\.[0-9]{0,3}[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/analytic_percentage"} |
| parameters.lines[].deferred_start_date | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.lines[].deferred_end_date | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.lines[] | 未限定 | 分支约束 | oneOf[1] | 行数组；增补/更新/替换语义由能力ID决定 |  |
| parameters.lines[].deferred_start_date | null | 可选（可能有条件限制） | oneOf[1] |  |  |
| parameters.lines[].deferred_end_date | null | 可选（可能有条件限制） | oneOf[1] |  |  |
| parameters.lines[] | 未限定 | 分支约束 | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"required_in_object":["deferred_start_date","deferred_end_date"]} |
| parameters.lines[].deferred_start_date | string | 必填（所在对象出现时） | oneOf[2] |  |  |
| parameters.lines[].deferred_end_date | string | 必填（所在对象出现时） | oneOf[2] |  |  |
| parameters.lines[] | 组合/开放结构 | 分支约束 | allOf[1] | 行数组；增补/更新/替换语义由能力ID决定 | {"if":{"required":["product_uom_id"]},"then":{"properties":{"product_id":{"minimum":1,"type":"integer"}}}} |
| parameters.lines[] | 未限定 | 条件分支 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| parameters.lines[].product_id | integer | 可选（可能有条件限制） | allOf[1]/then |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.lines.replace"} |
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
- `execute`：fixed_native_draft_account_move_line_replacement_write_action
- `verify`：same_transaction_exact_rich_business_line_reread_and_schema_validation
- `idempotency`：target_line_payload_state_check_before_native_write
- `reverse`：repeat_replace_with_previous_business_lines

### 已登记测试与证据范围

- `unit`：`implemented`；Existing contracts and explicit native line unit/deductibility inputs covered.；引用：tests/unit/test_document_lifecycle_writes.py, tests/unit/test_document_lifecycle_writes_runtime.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_write_cli.py, tests/unit/test_document_lifecycle_write_cli.py, tests/unit/test_accounting_entry_membership_batch.py, tests/unit/test_invoice_line_inputs_contract.py, tests/unit/test_invoice_line_inputs_runtime.py
- `integration`：`implemented`；Shared native smoke passed; full rollback.；引用：tests/integration/test_document_lifecycle_write_batch_live.py, tests/integration/test_accounting_depth_batch_live.py, tests/integration/test_accounting_entry_membership_batch_live.py, tests/integration/test_invoice_line_inputs_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-lines-resequence"></a>

## invoice.lines.resequence — 调整发票展示行顺序

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured caller/company scope and native ACLs. Writes require a draft invoice or receipt. Terms use native HTML sanitization. Sections/subsections/notes are non-accountable native lines; layout deletion never deletes product, tax or payment-term lines. Resequencing requires all native invoice lines and only changes sequence. Fiscal refresh calls the native price/tax/account recomputation and may overwrite manual financial values. No external delivery, cron or caller-sudo.
- 内部domain：`accounting_documents`；来源模型：account.move, account.move.line, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.move.line:read, account.move.line:write, account.move:read, account.move:write。
- 请求/响应合同：`schemas/v1/invoice.lines.resequence.request.schema.json` / `schemas/v1/invoice.lines.resequence.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.lines.resequence --request "@request.json" --idempotency-key "invoice.lines.resequence:1:5de2ffcced6cd634927b39bfad7d193f" --confirm "invoice.lines.resequence"
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
      1
    ],
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["line_ids","move_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.line_ids | array | 必填（所在对象出现时） |  | 行记录ID数组 | {"maxItems":500,"minItems":1,"uniqueItems":true} |
| parameters.line_ids[] | integer | 每个数组元素 |  | 行记录ID数组 | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.lines.resequence"} |
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
- `execute`：fixed_native_invoice_fields_or_fiscal_action
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：native_current_payload_recheck_missing_deleted_line_is_not_found
- `reverse`：restore_previous_values_subject_to_native_state_and_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Shared closed schemas, public/runtime contracts, native layout and fiscal actions, replay and scope boundaries.；引用：tests/unit/test_invoice_presentation_batch.py
- `integration`：`implemented`；The shared rollback-only public CLI/real-ORM smoke passed both isolated aliases as uid 5 with su=False: all eight new IDs and seven immediate replays; native sanitized terms, shipping/responsible settings; sections, subsections, notes, native zero-accounting/parent/order and scoped keyset pagination; existing empty/long native labels; layout edits preserve totals; native fiscal price/tax/account recomputation with native balance and dynamic-sync guards; product-line deletion, incomplete ordering, posted and foreign-company denial; fresh-cursor business-record and temporary-group rollback. No external delivery, cron, addon modification or service changes.；引用：tests/integration/test_invoice_presentation_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-lines-update"></a>

## invoice.lines.update — 保留编号，批量修改草稿发票或账单业务行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`invoices_and_bills`；来源模型：res.company, res.partner, product.product, account.account, account.tax, account.move, account.move.line, account.analytic.account；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：res.partner:read, product.product:read, account.account:read, account.tax:read, account.analytic.account:read, account.move:read, account.move:write, account.move.line:read, account.move.line:create, account.move.line:write, account.move.line:unlink。
- 请求/响应合同：`schemas/v1/invoice.lines.update.request.schema.json` / `schemas/v1/invoice.lines.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.lines.update --request "@request.json" --idempotency-key "invoice.lines.update:1:b75dd8aa72353d85969d646e006de239" --confirm "invoice.lines.update"
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
    "move_id": 1,
    "lines": [
      {
        "line_id": 1,
        "changes": {
          "name": "Example"
        }
      }
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id","lines"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.lines | array | 必填（所在对象出现时） |  | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":200,"minItems":1} |
| parameters.lines[] | object | 每个数组元素 |  | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["line_id","changes"]} |
| parameters.lines[].line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.lines[].changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"allOf":[{"if":{"properties":{"deferred_start_date":{"type":"null"}},"required":["deferred_start_date"]},"then":{"properties":{"deferred_end_date":{"type":"null"}}}},{"if":{"properties":{"deferred_end_date":{"type":"null"}},"required":["deferred_end_date"]},"then":{"properties":{"deferred_start_date":{"type":"null"}}}},{"if":{"required":["product_uom_id","product_id"]},"then":{"properties":{"product_id":{"minimum":1,"type":"integer"}}}}],"dependentRequired":{"deferred_end_date":["deferred_start_date"],"deferred_start_date":["deferred_end_date"]},"minProperties":1,"resolved_ref":"invoice.line.update.request.schema.json#/properties/parameters/properties/changes"} |
| parameters.lines[].changes.name | string | 可选（可能有条件限制） |  | 名称/行说明 | {"maxLength":500,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$","resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/name"} |
| parameters.lines[].changes.product_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/product_id"} |
| parameters.lines[].changes.product_uom_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/product_uom_id"} |
| parameters.lines[].changes.deductible_amount | string | 可选（可能有条件限制） |  | Native deductibility percentage, not a monetary amount. | {"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])","resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/deductible_amount"} |
| parameters.lines[].changes.account_id | integer | 可选（可能有条件限制） |  | 会计科目ID | {"minimum":1,"resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/account_id"} |
| parameters.lines[].changes.quantity | string | 可选（可能有条件限制） |  | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/quantity"} |
| parameters.lines[].changes.price_unit | string | 可选（可能有条件限制） |  | 单价；币种及符号依单据和合同 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/price_unit"} |
| parameters.lines[].changes.discount | string | 可选（可能有条件限制） |  | 折扣百分比 | {"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])","resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/discount"} |
| parameters.lines[].changes.tax_ids | array | 可选（可能有条件限制） |  | 应用税ID数组 | {"resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/tax_ids","uniqueItems":true} |
| parameters.lines[].changes.tax_ids[] | integer | 每个数组元素 |  | 应用税ID数组 | {"minimum":1} |
| parameters.lines[].changes.analytic_distribution | 组合/开放结构 | 可选（可能有条件限制） |  | 分析分摊映射；写入与读回约束可能不同 | {"oneOf":[{"type":"null"},{"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"},"type":"object"}],"resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/analytic_distribution"} |
| parameters.lines[].changes.analytic_distribution | null | 分支约束 | oneOf[1] | 分析分摊映射；写入与读回约束可能不同 |  |
| parameters.lines[].changes.analytic_distribution | object | 分支约束 | oneOf[2] | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"}} |
| parameters.lines[].changes.analytic_distribution{其他键} | string | 动态键值 | oneOf[2] |  | {"maxLength":8,"pattern":"^(?:100&#124;(?:[1-9][0-9]?)(?:\\.[0-9]{0,3}[1-9])?&#124;0\\.[0-9]{0,3}[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/analytic_percentage"} |
| parameters.lines[].changes.deferred_start_date | string/null | 可选（可能有条件限制） |  |  | {"format":"date","resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/deferred_start_date"} |
| parameters.lines[].changes.deferred_end_date | string/null | 可选（可能有条件限制） |  |  | {"format":"date","resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/deferred_end_date"} |
| parameters.lines[].changes | 组合/开放结构 | 分支约束 | allOf[1] | 仅提交拟变更字段，非整条记录 | {"if":{"properties":{"deferred_start_date":{"type":"null"}},"required":["deferred_start_date"]},"then":{"properties":{"deferred_end_date":{"type":"null"}}}} |
| parameters.lines[].changes | 未限定 | 条件分支 | allOf[1]/then | 仅提交拟变更字段，非整条记录 |  |
| parameters.lines[].changes.deferred_end_date | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| parameters.lines[].changes | 组合/开放结构 | 分支约束 | allOf[2] | 仅提交拟变更字段，非整条记录 | {"if":{"properties":{"deferred_end_date":{"type":"null"}},"required":["deferred_end_date"]},"then":{"properties":{"deferred_start_date":{"type":"null"}}}} |
| parameters.lines[].changes | 未限定 | 条件分支 | allOf[2]/then | 仅提交拟变更字段，非整条记录 |  |
| parameters.lines[].changes.deferred_start_date | null | 可选（可能有条件限制） | allOf[2]/then |  |  |
| parameters.lines[].changes | 组合/开放结构 | 分支约束 | allOf[3] | 仅提交拟变更字段，非整条记录 | {"if":{"required":["product_uom_id","product_id"]},"then":{"properties":{"product_id":{"minimum":1,"type":"integer"}}}} |
| parameters.lines[].changes | 未限定 | 条件分支 | allOf[3]/then | 仅提交拟变更字段，非整条记录 |  |
| parameters.lines[].changes.product_id | integer | 可选（可能有条件限制） | allOf[3]/then |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.lines.update"} |
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

- `preview`：exact_confirmation_closed_contract
- `execute`：single_native_parent_business_line_commands
- `verify`：business_layout_membership_and_explicit_values_with_native_dynamic_sync
- `idempotency`：explicit_target_state_replay
- `reverse`：restore_previous_values

### 已登记测试与证据范围

- `unit`：`implemented`；Bulk closed contracts, native parent writes and business row membership covered.；引用：tests/unit/test_invoice_bulk_lines_contract.py, tests/unit/test_invoice_bulk_lines_runtime.py, tests/unit/test_document_search_batch_cli.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；Shared native document search and invoice bulk smoke passed; full rollback.；引用：tests/integration/test_document_search_bulk_lines_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-pdf-export"></a>

## invoice.pdf.export — 导出发票 PDF

- 类型：只读；静态状态：`unconfigured`；handler：`document_invoice_pdf_export`。
- 状态原因：`runtime_context_required` — The fixed native PDF handler is installed; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`document_exports`；来源模型：account.move, res.company, ir.actions.report；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.move:read, res.company:read, ir.actions.report:read。
- 请求/响应合同：`schemas/v1/invoice.pdf.export.request.schema.json` / `schemas/v1/invoice.pdf.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read invoice.pdf.export --request "@request.json"
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
    "move_id": 1,
    "layout": "with_payments"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id","layout"],"resolved_ref":"#/$defs/parameters"} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.layout | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["with_payments","without_payments"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.pdf.export"} |
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
- `execute`：fixed_native_invoice_qweb_pdf_action_selected_by_layout
- `verify`：bound_record_pdf_bytes_hash_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover the fixed actions, exact contract, bridge, runtime, CLI routing, registry metadata, and schemas.；引用：tests/unit/test_document_exports.py, tests/unit/test_document_exports_bridge.py, tests/unit/test_document_exports_runtime.py, tests/unit/test_document_export_cli.py, tests/unit/test_document_export_registry.py
- `integration`：`implemented`；The shared read-only live smoke covers the fixed document export batch in both isolated databases.；引用：tests/integration/test_document_export_batch_live.py
- `golden`：`planned`；Golden PDF evidence is pending.；引用：无
- `e2e`：`planned`；End-to-end natural-language routing evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-post"></a>

## invoice.post — 原子过账单张或 2–100 张发票或账单

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`invoices_and_bills`；来源模型：res.company, account.move, account.move.line, account.analytic.account, account.analytic.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.move:read, account.move:write, account.move.line:read。
- 请求/响应合同：`schemas/v1/invoice.post.request.schema.json` / `schemas/v1/invoice.post.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.post --request "@request.json" --idempotency-key "invoice.post:1" --confirm "invoice.post"
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
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"oneOf":[{"required":["move_id"]},{"required":["move_ids"]}]} |
| parameters.move_id | integer | 可选（可能有条件限制） |  | 会计单据记录ID | {"minimum":1} |
| parameters.move_ids | array | 可选（可能有条件限制） |  | 会计单据ID数组 | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| parameters.move_ids[] | integer | 每个数组元素 |  | 会计单据ID数组 | {"minimum":1} |
| parameters | 未限定 | 分支约束 | oneOf[1] |  | {"required_in_object":["move_id"]} |
| parameters | 未限定 | 分支约束 | oneOf[2] |  | {"required_in_object":["move_ids"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.post"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]} |
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
| response.data | object | 分支约束 | oneOf[3] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-batch-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | oneOf[3] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | oneOf[3] |  | {"additionalProperties":false,"required_in_object":["items","processed_count"]} |
| response.data.result.items | array | 必填（所在对象出现时） | oneOf[3] |  | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| response.data.result.items[] | object | 每个数组元素 | oneOf[3] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"],"resolved_ref":"core-write-result.schema.json#/properties/result"} |
| response.data.result.items[].model | string | 必填（所在对象出现时） | oneOf[3] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].id | integer/null | 必填（所在对象出现时） | oneOf[3] |  | {"minimum":1} |
| response.data.result.items[].name | string/null | 必填（所在对象出现时） | oneOf[3] | 名称/行说明 | {"minLength":1} |
| response.data.result.items[].state | string | 必填（所在对象出现时） | oneOf[3] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].company_id | integer | 必填（所在对象出现时） | oneOf[3] | 所选公司ID | {"minimum":1} |
| response.data.result.items[].move_type | string/null | 必填（所在对象出现时） | oneOf[3] |  | {"minLength":1} |
| response.data.result.items[].source_id | integer/null | 必填（所在对象出现时） | oneOf[3] |  | {"minimum":1} |
| response.data.result.items[].line_ids | array | 必填（所在对象出现时） | oneOf[3] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.items[].line_ids[] | integer | 每个数组元素 | oneOf[3] | 行记录ID数组 | {"minimum":1} |
| response.data.result.items[].partial_reconcile_ids | array | 必填（所在对象出现时） | oneOf[3] |  | {"uniqueItems":true} |
| response.data.result.items[].partial_reconcile_ids[] | integer | 每个数组元素 | oneOf[3] |  | {"minimum":1} |
| response.data.result.items[].full_reconcile_id | integer/null | 必填（所在对象出现时） | oneOf[3] | 完整核销关系ID | {"minimum":1} |
| response.data.result.items[].reconciled | boolean | 必填（所在对象出现时） | oneOf[3] |  |  |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | oneOf[3] |  | {"maximum":100,"minimum":2} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then |  | {"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]} |
| response.data | object | 分支约束 | allOf[1]/then/oneOf[1] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[1]/then/oneOf[1] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[1]/then/oneOf[1] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-batch-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","processed_count"]} |
| response.data.result.items | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| response.data.result.items[] | object | 每个数组元素 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"],"resolved_ref":"core-write-result.schema.json#/properties/result"} |
| response.data.result.items[].model | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.result.items[].name | string/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.items[].state | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.items[].move_type | string/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.result.items[].source_id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.result.items[].line_ids | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.items[].line_ids[] | integer | 每个数组元素 | allOf[1]/then/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.items[].partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.items[].partial_reconcile_ids[] | integer | 每个数组元素 | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.result.items[].full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.items[].reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  |  |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"maximum":100,"minimum":2} |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：singular_or_2_to_100_distinct_ids_closed_validation_normalized_sorted_and_exact_capability_confirmation
- `execute`：full_batch_record_scope_company_invoice_type_and_state_preflight_then_single_transaction_all_or_nothing_native_post
- `verify`：explicit_batch_result_with_exact_normalized_record_ids_target_states_same_transaction_reread_and_response_schema_validation
- `idempotency`：capability_company_and_full_normalized_sorted_record_id_set_key_with_serial_target_state_replay
- `reverse`：customer_credit_note.create_or_vendor_refund.create

### 已登记测试与证据范围

- `unit`：`implemented`；The existing unit tests continue to cover the singular request and native runtime behavior; the batch contract unit test covers batch-request normalization, full normalized-ID-set idempotency keys, bridge and capability contracts, explicit batch results, and CLI verification.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_core_write_cli.py, tests/unit/test_lifecycle_batch_contract.py
- `integration`：`implemented`；The existing integration smoke continues to cover singular native execution; the new live smoke covers dual-database batch execution, immediate replay, and rollback, plus a representative whole-batch invalid-ID no-op for invoice.post.；引用：tests/integration/test_core_write_batch_live.py, tests/integration/test_batch_lifecycle_write_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-presentation_settings-get"></a>

## invoice.presentation_settings.get — 读取发票展示设置

- 类型：只读；静态状态：`unconfigured`；handler：`invoice_presentation_settings_get`。
- 状态原因：`runtime_context_required` — Requires configured caller/company scope and native ACLs. Writes require a draft invoice or receipt. Terms use native HTML sanitization. Sections/subsections/notes are non-accountable native lines; layout deletion never deletes product, tax or payment-term lines. Resequencing requires all native invoice lines and only changes sequence. Fiscal refresh calls the native price/tax/account recomputation and may overwrite manual financial values. No external delivery, cron or caller-sudo.
- 内部domain：`accounting_documents`；来源模型：res.company, account.move, res.partner, res.users；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move:read, res.partner:read, res.users:read。
- 请求/响应合同：`schemas/v1/invoice.presentation_settings.get.request.schema.json` / `schemas/v1/invoice.presentation_settings.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read invoice.presentation_settings.get --request "@request.json"
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
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.presentation_settings.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["company_id","fiscal_position_id","id","invoice_user_id","move_type","name","narration","partner_id","partner_shipping_id","state"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 |  |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.partner_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 合作伙伴ID | {"minimum":1} |
| response.data.partner_shipping_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.invoice_user_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.fiscal_position_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.narration | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["company_id","fiscal_position_id","id","invoice_user_id","move_type","name","narration","partner_id","partner_shipping_id","state"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 |  |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.partner_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 合作伙伴ID | {"minimum":1} |
| response.data.partner_shipping_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.invoice_user_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.fiscal_position_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.narration | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
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
- `execute`：fixed_native_invoice_presentation_read
- `verify`：closed_response_schema_validation
- `idempotency`：read_only
- `reverse`：not_applicable

### 已登记测试与证据范围

- `unit`：`implemented`；Shared closed schemas, public/runtime contracts, native layout and fiscal actions, replay and scope boundaries.；引用：tests/unit/test_invoice_presentation_batch.py
- `integration`：`implemented`；The shared rollback-only public CLI/real-ORM smoke passed both isolated aliases as uid 5 with su=False: all eight new IDs and seven immediate replays; native sanitized terms, shipping/responsible settings; sections, subsections, notes, native zero-accounting/parent/order and scoped keyset pagination; existing empty/long native labels; layout edits preserve totals; native fiscal price/tax/account recomputation with native balance and dynamic-sync guards; product-line deletion, incomplete ordering, posted and foreign-company denial; fresh-cursor business-record and temporary-group rollback. No external delivery, cron, addon modification or service changes.；引用：tests/integration/test_invoice_presentation_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-presentation_settings-update"></a>

## invoice.presentation_settings.update — 修改发票展示设置

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured caller/company scope and native ACLs. Writes require a draft invoice or receipt. Terms use native HTML sanitization. Sections/subsections/notes are non-accountable native lines; layout deletion never deletes product, tax or payment-term lines. Resequencing requires all native invoice lines and only changes sequence. Fiscal refresh calls the native price/tax/account recomputation and may overwrite manual financial values. No external delivery, cron or caller-sudo.
- 内部domain：`accounting_documents`；来源模型：account.move, account.move.line, res.company, res.partner, res.users；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.move.line:read, account.move:read, account.move:write, res.partner:read, res.users:read。
- 请求/响应合同：`schemas/v1/invoice.presentation_settings.update.request.schema.json` / `schemas/v1/invoice.presentation_settings.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.presentation_settings.update --request "@request.json" --idempotency-key "invoice.presentation_settings.update:1:fcc70c6c36b2680d2e54a5879bc47948" --confirm "invoice.presentation_settings.update"
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
      "partner_shipping_id": 1
    },
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["changes","move_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1,"required_in_object":[]} |
| parameters.changes.partner_shipping_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.changes.invoice_user_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.changes.narration | string/null | 可选（可能有条件限制） |  |  | {"maxLength":20000,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.presentation_settings.update"} |
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
- `execute`：native_draft_presentation_or_posted_narration_salesperson_only_no_pdf_regeneration
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：native_current_payload_recheck_missing_deleted_line_is_not_found
- `reverse`：restore_previous_values_subject_to_native_state_and_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Closed typed inputs, legacy request/key compatibility, native scopes and posted nonfinancial boundaries.；引用：tests/unit/test_accounting_setup_batch.py
- `integration`：`implemented`；One shared public CLI/native ORM workflow passed both isolated aliases in 22.30s as uid5/su=False/company1. Two new IDs and six extensions: company cash-basis assign/clear/get/replay; optional advanced tax fields, native grouped-tax invoice computation and transition-account rules; sale/purchase posted reference and narration/user edits including a partially reconciled invoice with raw matching IDs/amounts unchanged; posted entry references; financial/shipping denials; positive/negative/zero/minor-unit native currency-aware cash-rounding computation. Native configuration roles exist only inside the isolated transaction; caller never gains sudo. Fresh fixtures, both companies settings, all defaults, currencies/rates and exact caller/native group memberships roll back. Root cash-basis boolean natively propagates to branches; the live topology uses independent roots, not a tested branch workflow. Company ORM write does not run settings UI onchange or delete cash-basis taxes. Group-to-leaf native write need not clear children; non-group calculation ignores retained children. Actual cash-basis entry lifecycle, all hierarchy/currency/localization/hash/lock paths, PDF regeneration, external sends and concurrent exactly-once are not claimed. No business DB, native source/addon or service changes.；引用：tests/integration/test_accounting_setup_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-reset_to_draft"></a>

## invoice.reset_to_draft — 原子将单张或 2–100 张发票或账单重置为草稿

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`invoices_and_bills`；来源模型：res.company, account.move, account.move.line, account.analytic.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.move:read, account.move:write, account.move.line:read。
- 请求/响应合同：`schemas/v1/invoice.reset_to_draft.request.schema.json` / `schemas/v1/invoice.reset_to_draft.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.reset_to_draft --request "@request.json" --idempotency-key "invoice.reset_to_draft:1" --confirm "invoice.reset_to_draft"
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
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"oneOf":[{"required":["move_id"]},{"required":["move_ids"]}]} |
| parameters.move_id | integer | 可选（可能有条件限制） |  | 会计单据记录ID | {"minimum":1} |
| parameters.move_ids | array | 可选（可能有条件限制） |  | 会计单据ID数组 | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| parameters.move_ids[] | integer | 每个数组元素 |  | 会计单据ID数组 | {"minimum":1} |
| parameters | 未限定 | 分支约束 | oneOf[1] |  | {"required_in_object":["move_id"]} |
| parameters | 未限定 | 分支约束 | oneOf[2] |  | {"required_in_object":["move_ids"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.reset_to_draft"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]} |
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
| response.data | object | 分支约束 | oneOf[3] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-batch-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | oneOf[3] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | oneOf[3] |  | {"additionalProperties":false,"required_in_object":["items","processed_count"]} |
| response.data.result.items | array | 必填（所在对象出现时） | oneOf[3] |  | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| response.data.result.items[] | object | 每个数组元素 | oneOf[3] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"],"resolved_ref":"core-write-result.schema.json#/properties/result"} |
| response.data.result.items[].model | string | 必填（所在对象出现时） | oneOf[3] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].id | integer/null | 必填（所在对象出现时） | oneOf[3] |  | {"minimum":1} |
| response.data.result.items[].name | string/null | 必填（所在对象出现时） | oneOf[3] | 名称/行说明 | {"minLength":1} |
| response.data.result.items[].state | string | 必填（所在对象出现时） | oneOf[3] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].company_id | integer | 必填（所在对象出现时） | oneOf[3] | 所选公司ID | {"minimum":1} |
| response.data.result.items[].move_type | string/null | 必填（所在对象出现时） | oneOf[3] |  | {"minLength":1} |
| response.data.result.items[].source_id | integer/null | 必填（所在对象出现时） | oneOf[3] |  | {"minimum":1} |
| response.data.result.items[].line_ids | array | 必填（所在对象出现时） | oneOf[3] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.items[].line_ids[] | integer | 每个数组元素 | oneOf[3] | 行记录ID数组 | {"minimum":1} |
| response.data.result.items[].partial_reconcile_ids | array | 必填（所在对象出现时） | oneOf[3] |  | {"uniqueItems":true} |
| response.data.result.items[].partial_reconcile_ids[] | integer | 每个数组元素 | oneOf[3] |  | {"minimum":1} |
| response.data.result.items[].full_reconcile_id | integer/null | 必填（所在对象出现时） | oneOf[3] | 完整核销关系ID | {"minimum":1} |
| response.data.result.items[].reconciled | boolean | 必填（所在对象出现时） | oneOf[3] |  |  |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | oneOf[3] |  | {"maximum":100,"minimum":2} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then |  | {"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]} |
| response.data | object | 分支约束 | allOf[1]/then/oneOf[1] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[1]/then/oneOf[1] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[1]/then/oneOf[1] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-batch-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","processed_count"]} |
| response.data.result.items | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| response.data.result.items[] | object | 每个数组元素 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"],"resolved_ref":"core-write-result.schema.json#/properties/result"} |
| response.data.result.items[].model | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.result.items[].name | string/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.items[].state | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.items[].move_type | string/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.result.items[].source_id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.result.items[].line_ids | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.items[].line_ids[] | integer | 每个数组元素 | allOf[1]/then/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.items[].partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.items[].partial_reconcile_ids[] | integer | 每个数组元素 | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.result.items[].full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.items[].reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  |  |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"maximum":100,"minimum":2} |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：singular_or_2_to_100_distinct_ids_closed_validation_normalized_sorted_and_exact_capability_confirmation
- `execute`：full_batch_record_scope_company_invoice_type_and_state_preflight_then_single_transaction_all_or_nothing_native_reset_to_draft
- `verify`：explicit_batch_result_with_exact_normalized_record_ids_target_states_same_transaction_reread_and_response_schema_validation
- `idempotency`：capability_company_and_full_normalized_sorted_record_id_set_key_with_serial_target_state_replay
- `reverse`：invoice.post_when_business_intent_requires_reposting

### 已登记测试与证据范围

- `unit`：`implemented`；The existing unit tests continue to cover the singular request and native runtime behavior; the batch contract unit test covers batch-request normalization, full normalized-ID-set idempotency keys, bridge and capability contracts, explicit batch results, and CLI verification.；引用：tests/unit/test_document_lifecycle_writes.py, tests/unit/test_document_lifecycle_writes_runtime.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_write_cli.py, tests/unit/test_document_lifecycle_write_cli.py, tests/unit/test_lifecycle_batch_contract.py
- `integration`：`implemented`；The existing integration smoke continues to cover singular native execution; the new live smoke covers dual-database batch execution, immediate replay, and rollback, plus a representative whole-batch invalid-ID no-op for invoice.post.；引用：tests/integration/test_document_lifecycle_write_batch_live.py, tests/integration/test_batch_lifecycle_write_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-reverse_and_reissue"></a>

## invoice.reverse_and_reissue — 冲销并重新开票

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`invoices_and_bills`；来源模型：account.account, account.analytic.account, account.analytic.line, account.full.reconcile, account.journal, account.move, account.move.line, account.move.reversal, account.partial.reconcile, account.payment, account.tax, product.product, res.company, res.currency, res.currency.rate, res.partner, res.partner.bank；向导：account.move.reversal。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.account:read, account.analytic.account:read, account.analytic.line:create, account.analytic.line:read, account.analytic.line:unlink, account.full.reconcile:create, account.full.reconcile:read, account.full.reconcile:unlink, account.journal:read, account.move.line:create, account.move.line:read, account.move.line:unlink, account.move.line:write, account.move.reversal:create, account.move:create, account.move:read, account.move:unlink, account.move:write, account.partial.reconcile:create, account.partial.reconcile:read, account.partial.reconcile:unlink, account.payment:read, account.payment:write, account.tax:read, res.currency.rate:read, res.currency:read, res.partner.bank:read, res.partner:read。
- 请求/响应合同：`schemas/v1/invoice.reverse_and_reissue.request.schema.json` / `schemas/v1/invoice.reverse_and_reissue.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.reverse_and_reissue --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "invoice.reverse_and_reissue"
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
    "move_id": 1,
    "date": "2026-10-31",
    "reason": "1"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id","date","reason"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.date | string | 必填（所在对象出现时） |  |  | {"format":"date"} |
| parameters.reason | string | 必填（所在对象出现时） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-batch-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.reverse_and_reissue"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-batch-result.schema.json"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-batch-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","processed_count"]} |
| response.data.result.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| response.data.result.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"],"resolved_ref":"core-write-result.schema.json#/properties/result"} |
| response.data.result.items[].model | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.result.items[].name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.items[].state | string | 必填（所在对象出现时） | oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.items[].move_type | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.result.items[].source_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.result.items[].line_ids | array | 必填（所在对象出现时） | oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.items[].line_ids[] | integer | 每个数组元素 | oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.items[].partial_reconcile_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.items[].partial_reconcile_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.result.items[].full_reconcile_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.items[].reconciled | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"maximum":100,"minimum":2} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-batch-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-batch-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[1]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["items","processed_count"]} |
| response.data.result.items | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| response.data.result.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"],"resolved_ref":"core-write-result.schema.json#/properties/result"} |
| response.data.result.items[].model | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.result.items[].name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.result.items[].state | string | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.result.items[].move_type | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.result.items[].source_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.result.items[].line_ids | array | 必填（所在对象出现时） | allOf[1]/then | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.items[].line_ids[] | integer | 每个数组元素 | allOf[1]/then | 行记录ID数组 | {"minimum":1} |
| response.data.result.items[].partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.result.items[].partial_reconcile_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.result.items[].full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 完整核销关系ID | {"minimum":1} |
| response.data.result.items[].reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"maximum":100,"minimum":2} |
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
- `execute`：native_modify_moves_as_ordinary_caller_today_or_past_posted_invoice
- `verify`：same_transaction_posted_refund_and_same_direction_draft_replacement
- `idempotency`：native_marked_pair_current_target_recheck_without_operation_store
- `reverse`：native_compensating_workflow_subject_to_accounting_constraints

### 已登记测试与证据范围

- `unit`：`implemented`；Closed typed inputs, schema and target binding; compatible legacy branches remain covered.；引用：tests/unit/test_accounting_workflows_batch.py
- `integration`：`implemented`；Shared native CLI workflow: both isolated aliases passed32.80s as uid5/su=False/company1. Verified sale/purchase reversal plus draft reissue and replay, native foreign-currency line edits, full/partial matching-group leaf undo and shrinking replay, statement-scoped bank pagination and actual payment bank matches, three company account assignments/clearing/readback and product fallback, purchase self-billing sequence. Native configuration roles and independent bank fixtures exist only in the test transaction. Fresh-cursor objects, caller groups, company settings, defaults and currency/rate rollback checks passed. Bank response additions require synchronized SDK/bridge/schema. No business DB, native source/addon, service, external-send or operation-store changes. Prior-paid reissue, cashbasis/exchange undo workflows, all ancestry/currency/localization/lock/hash branches, all setting consumers and concurrent exactly-once are not claimed.；引用：tests/integration/test_accounting_workflows_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-search"></a>

## invoice.search — 搜索客户发票和供应商账单

- 类型：只读；静态状态：`unconfigured`；handler：`invoice_search`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`invoices_and_bills`；来源模型：account.move, account.move.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move:read, account.move.line:read, account.journal:read, res.currency:read, res.partner:read。
- 请求/响应合同：`schemas/v1/invoice.search.request.schema.json` / `schemas/v1/invoice.search.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read invoice.search --request "@request.json"
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
| parameters.date_from | string/null | 可选（可能有条件限制） |  | 开始日期 | {"default":null,"format":"date"} |
| parameters.date_to | string/null | 可选（可能有条件限制） |  | 结束日期 | {"default":null,"format":"date"} |
| parameters.invoice_date_from | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.invoice_date_to | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.due_date_from | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.due_date_to | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.currency_id | integer | 可选（可能有条件限制） |  | 币种ID | {"minimum":1} |
| parameters.invoice_user_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.payment_term_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.fiscal_position_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.product_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.account_id | integer | 可选（可能有条件限制） |  | 会计科目ID | {"minimum":1} |
| parameters.tax_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.document_types | array | 可选（可能有条件限制） |  |  | {"maxItems":4,"minItems":1,"uniqueItems":true} |
| parameters.document_types[] | 未限定 | 每个数组元素 |  |  | {"enum":["out_invoice","out_refund","in_invoice","in_refund"]} |
| parameters.states | array | 可选（可能有条件限制） |  |  | {"maxItems":3,"minItems":1,"uniqueItems":true} |
| parameters.states[] | 未限定 | 每个数组元素 |  |  | {"enum":["draft","posted","cancel"]} |
| parameters.payment_states | array | 可选（可能有条件限制） |  |  | {"maxItems":7,"minItems":1,"uniqueItems":true} |
| parameters.payment_states[] | 未限定 | 每个数组元素 |  |  | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy"]} |
| parameters.journal_id | integer/null | 可选（可能有条件限制） |  | 日记账ID | {"default":null,"minimum":1} |
| parameters.partner_id | integer/null | 可选（可能有条件限制） |  | 合作伙伴ID | {"default":null,"minimum":1} |
| parameters.query | string/null | 可选（可能有条件限制） |  | 搜索文本 | {"default":null,"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.search"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","date","invoice_date","invoice_date_due","ref","payment_reference","invoice_origin","journal","company_id","currency","partner","amount_untaxed","amount_tax","amount_total","amount_residual","payment_state"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["out_invoice","out_refund","in_invoice","in_refund"]} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.items[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].invoice_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].invoice_date_due | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].ref | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].payment_reference | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].invoice_origin | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/journal"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":5,"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.items[].partner | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/partner"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].amount_untaxed | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.items[].amount_tax | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.items[].amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.items[].amount_residual | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.items[].payment_state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy"]} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","date","invoice_date","invoice_date_due","ref","payment_reference","invoice_origin","journal","company_id","currency","partner","amount_untaxed","amount_tax","amount_total","amount_residual","payment_state"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["out_invoice","out_refund","in_invoice","in_refund"]} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].invoice_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].invoice_date_due | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].ref | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].payment_reference | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].invoice_origin | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/journal"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":5,"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.items[].partner | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/partner"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].amount_untaxed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.items[].amount_tax | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.items[].amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.items[].amount_residual | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.items[].payment_state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy"]} |
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
- `verify`：same_transaction_result_and_v1_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Existing contracts and optional native same-line/header search filters covered.；引用：tests/unit/test_invoices.py, tests/unit/test_invoice_bridge.py, tests/unit/test_invoice_runtime.py, tests/unit/test_invoice_cli.py, tests/unit/test_document_search_batch_contract.py, tests/unit/test_document_search_batch_runtime.py, tests/unit/test_document_search_header_runtime.py, tests/unit/test_document_search_batch_cli.py, tests/unit/test_invoice_business_line_filters_contract.py, tests/unit/test_document_business_filters_runtime.py, tests/unit/test_business_line_search_remove_cli.py
- `integration`：`implemented`；Shared native business-line search and bulk deletion smoke passed; full rollback.；引用：tests/integration/test_invoices_live.py, tests/integration/test_document_search_bulk_lines_live.py, tests/integration/test_business_line_search_remove_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-service_dates-get"></a>

## invoice.service_dates.get — 查看发票业务日期

- 类型：只读；静态状态：`unconfigured`；handler：`invoice_service_dates_get`。
- 状态原因：`runtime_context_required` — Fixed invoice preparation and product accounting operations are implemented; runtime company, ordinary-user ACL and native accounting recomputation apply.
- 内部domain：`invoice`；来源模型：res.company, account.move；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move:read。
- 请求/响应合同：`schemas/v1/invoice.service_dates.get.request.schema.json` / `schemas/v1/invoice.service_dates.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read invoice.service_dates.get --request "@request.json"
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
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.service_dates.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","move_type","state","date","invoice_date","delivery_date","taxable_supply_date","show_delivery_date","show_taxable_supply_date"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["in_invoice","in_refund","out_invoice","out_refund"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.invoice_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.delivery_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.taxable_supply_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.show_delivery_date | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.show_taxable_supply_date | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","move_type","state","date","invoice_date","delivery_date","taxable_supply_date","show_delivery_date","show_taxable_supply_date"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["in_invoice","in_refund","out_invoice","out_refund"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.invoice_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.delivery_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.taxable_supply_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.show_delivery_date | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.show_taxable_supply_date | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
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
- `execute`：fixed_target_native_accounting_read_as_business_user
- `verify`：typed_target_and_optional_fiscal_position_binding
- `idempotency`：read_only
- `reverse`：not_applicable

### 已登记测试与证据范围

- `unit`：`implemented`；Closed parameters and typed target binding, schemas and public CLI; native behavior is tested separately.；引用：tests/unit/test_invoice_preparation_batch.py
- `integration`：`implemented`；One shared public CLI/real ORM workflow passed both isolated aliases in 20.08s as uid5/su=False/company1: native service-date set/clear and replay; sanitized zero-purchase-line alerts without executing actions; actual reversal and transaction-local direct cashbasis/adjusting relation inspection; category/product defaults, native tax filtering and fiscal-position account mapping; sale/purchase existing tax-group minor-unit inverse adjustments, balance and payment-term readback, replay and unchanged other tax rows. Posted, missing, foreign and invalid-target denials are exercised. Fixtures, exact groups, company settings and defaults roll back in fresh cursors. Direct relation fixtures are not full cashbasis/deferral workflow acceptance; current company topology does not prove every ancestry/localization/currency branch. No business DB, service/addon change, actual send or concurrent exactly-once claim.；引用：tests/integration/test_invoice_preparation_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-service_dates-update"></a>

## invoice.service_dates.update — 修改草稿发票业务日期

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Fixed invoice preparation and product accounting operations are implemented; runtime company, ordinary-user ACL and native accounting recomputation apply.
- 内部domain：`invoice`；来源模型：account.account, account.move, account.move.line, account.tax, res.company, res.currency, res.currency.rate；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.account:read, account.move.line:create, account.move.line:read, account.move.line:unlink, account.move.line:write, account.move:read, account.move:write, account.tax:read, res.company:read, res.currency.rate:read, res.currency:read。
- 请求/响应合同：`schemas/v1/invoice.service_dates.update.request.schema.json` / `schemas/v1/invoice.service_dates.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.service_dates.update --request "@request.json" --idempotency-key "invoice.service_dates.update:1:3ce73cb13e27059459afddb570d0c0a9" --confirm "invoice.service_dates.update"
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
    "move_id": 1,
    "changes": {
      "delivery_date": "2026-10-31"
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id","changes"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.delivery_date | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.changes.taxable_supply_date | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.service_dates.update"} |
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
- `execute`：native_draft_invoice_write_and_recomputation_as_business_user
- `verify`：same_transaction_native_date_or_computed_tax_group_readback
- `idempotency`：serial_current_target_recheck_without_operation_store_or_concurrent_exactly_once
- `reverse`：restore_prior_values_subject_to_native_constraints

### 已登记测试与证据范围

- `unit`：`implemented`；Closed parameters and typed target binding, schemas and public CLI; native behavior is tested separately.；引用：tests/unit/test_invoice_preparation_batch.py
- `integration`：`implemented`；One shared public CLI/real ORM workflow passed both isolated aliases in 20.08s as uid5/su=False/company1: native service-date set/clear and replay; sanitized zero-purchase-line alerts without executing actions; actual reversal and transaction-local direct cashbasis/adjusting relation inspection; category/product defaults, native tax filtering and fiscal-position account mapping; sale/purchase existing tax-group minor-unit inverse adjustments, balance and payment-term readback, replay and unchanged other tax rows. Posted, missing, foreign and invalid-target denials are exercised. Fixtures, exact groups, company settings and defaults roll back in fresh cursors. Direct relation fixtures are not full cashbasis/deferral workflow acceptance; current company topology does not prove every ancestry/localization/currency branch. No business DB, service/addon change, actual send or concurrent exactly-once claim.；引用：tests/integration/test_invoice_preparation_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-tax_breakdown-inspect"></a>

## invoice.tax_breakdown.inspect — 检查发票税额明细

- 类型：只读；静态状态：`unconfigured`；handler：`invoice_tax_breakdown_inspect`。
- 状态原因：`runtime_context_required` — The fixed read handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`invoices_and_bills`；来源模型：res.company, account.move, account.move.line, account.tax, account.tax.repartition.line, res.currency；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move:read, account.move.line:read, account.tax:read, account.tax.repartition.line:read, res.currency:read。
- 请求/响应合同：`schemas/v1/invoice.tax_breakdown.inspect.request.schema.json` / `schemas/v1/invoice.tax_breakdown.inspect.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read invoice.tax_breakdown.inspect --request "@request.json"
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
    "invoice_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["invoice_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.invoice_id | integer | 必填（所在对象出现时） |  | 发票/账单记录ID（具体类型按能力定义） | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.tax_breakdown.inspect"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","invoice","company_id","currency","amount_untaxed","amount_tax","amount_total","has_tax_groups","subtotals"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.invoice | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state"],"resolved_ref":"#/$defs/invoice"} |
| response.data.invoice.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.invoice.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.invoice.move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["out_invoice","out_refund","in_invoice","in_refund"]} |
| response.data.invoice.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.amount_untaxed | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_tax | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.has_tax_groups | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.subtotals | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.subtotals[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["name","base_amount","tax_amount","tax_groups"],"resolved_ref":"#/$defs/subtotal"} |
| response.data.subtotals[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.subtotals[].base_amount | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.subtotals[].tax_amount | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.subtotals[].tax_groups | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.subtotals[].tax_groups[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","base_amount","tax_amount"],"resolved_ref":"#/$defs/tax_group"} |
| response.data.subtotals[].tax_groups[].id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.subtotals[].tax_groups[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.subtotals[].tax_groups[].base_amount | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.subtotals[].tax_groups[].tax_amount | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","invoice","company_id","currency","amount_untaxed","amount_tax","amount_total","has_tax_groups","subtotals"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.invoice | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state"],"resolved_ref":"#/$defs/invoice"} |
| response.data.invoice.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.invoice.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.invoice.move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["out_invoice","out_refund","in_invoice","in_refund"]} |
| response.data.invoice.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.amount_untaxed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_tax | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.has_tax_groups | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.subtotals | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.subtotals[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["name","base_amount","tax_amount","tax_groups"],"resolved_ref":"#/$defs/subtotal"} |
| response.data.subtotals[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.subtotals[].base_amount | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.subtotals[].tax_amount | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.subtotals[].tax_groups | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.subtotals[].tax_groups[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","base_amount","tax_amount"],"resolved_ref":"#/$defs/tax_group"} |
| response.data.subtotals[].tax_groups[].id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.subtotals[].tax_groups[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.subtotals[].tax_groups[].base_amount | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.subtotals[].tax_groups[].tax_amount | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
- `execute`：fixed_company_scoped_invoice_tax_breakdown_inspection
- `verify`：same_transaction_acl_company_tax_total_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared focused test covers registry metadata, fixed CLI routing, model mapping, and exclusion of inventory capabilities.；引用：tests/unit/test_accounting_operational_reads_registry_cli.py
- `integration`：`implemented`；The shared ordinary-accounting-user read-only smoke passed for all twelve capabilities on both dedicated isolated database aliases.；引用：tests/integration/test_accounting_operational_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-tax_totals-adjust"></a>

## invoice.tax_totals.adjust — 调整草稿发票税组金额

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Fixed invoice preparation and product accounting operations are implemented; runtime company, ordinary-user ACL and native accounting recomputation apply.
- 内部domain：`invoice`；来源模型：account.account, account.move, account.move.line, account.tax, res.company, res.currency；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.account:read, account.move.line:create, account.move.line:read, account.move.line:unlink, account.move.line:write, account.move:read, account.move:write, account.tax:read, res.company:read, res.currency:read。
- 请求/响应合同：`schemas/v1/invoice.tax_totals.adjust.request.schema.json` / `schemas/v1/invoice.tax_totals.adjust.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.tax_totals.adjust --request "@request.json" --idempotency-key "invoice.tax_totals.adjust:1:3a02c6e86a239fde79c21964049bb969" --confirm "invoice.tax_totals.adjust"
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
    "move_id": 1,
    "groups": [
      {
        "tax_group_id": 1,
        "tax_amount": "1"
      }
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id","groups"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.groups | array | 必填（所在对象出现时） |  |  | {"maxItems":64,"minItems":1} |
| parameters.groups[] | object | 每个数组元素 |  |  | {"additionalProperties":false,"required_in_object":["tax_group_id","tax_amount"]} |
| parameters.groups[].tax_group_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.groups[].tax_amount | string | 必填（所在对象出现时） |  |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.tax_totals.adjust"} |
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
- `execute`：native_draft_invoice_write_and_recomputation_as_business_user
- `verify`：same_transaction_native_date_or_computed_tax_group_readback
- `idempotency`：serial_current_target_recheck_without_operation_store_or_concurrent_exactly_once
- `reverse`：restore_prior_values_subject_to_native_constraints

### 已登记测试与证据范围

- `unit`：`implemented`；Closed parameters and typed target binding, schemas and public CLI; native behavior is tested separately.；引用：tests/unit/test_invoice_preparation_batch.py
- `integration`：`implemented`；One shared public CLI/real ORM workflow passed both isolated aliases in 20.08s as uid5/su=False/company1: native service-date set/clear and replay; sanitized zero-purchase-line alerts without executing actions; actual reversal and transaction-local direct cashbasis/adjusting relation inspection; category/product defaults, native tax filtering and fiscal-position account mapping; sale/purchase existing tax-group minor-unit inverse adjustments, balance and payment-term readback, replay and unchanged other tax rows. Posted, missing, foreign and invalid-target denials are exercised. Fixtures, exact groups, company settings and defaults roll back in fresh cursors. Direct relation fixtures are not full cashbasis/deferral workflow acceptance; current company topology does not prove every ancestry/localization/currency branch. No business DB, service/addon change, actual send or concurrent exactly-once claim.；引用：tests/integration/test_invoice_preparation_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-type-switch"></a>

## invoice.type.switch — 切换草稿发票或账单的发票退款类型

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`invoices_and_bills`；来源模型：res.company, account.move, account.move.line, account.tax；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.move:read, account.move:write, account.move.line:read, account.move.line:write, account.tax:read。
- 请求/响应合同：`schemas/v1/invoice.type.switch.request.schema.json` / `schemas/v1/invoice.type.switch.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.type.switch --request "@request.json" --idempotency-key "invoice.type.switch:1:out_invoice" --confirm "invoice.type.switch"
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
    "move_id": 1,
    "target_move_type": "out_invoice"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id","target_move_type"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.target_move_type | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["out_invoice","out_refund","in_invoice","in_refund"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.type.switch"} |
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
- `execute`：fixed_same_business_family_draft_move_type_switch
- `verify`：same_transaction_target_type_draft_state_and_response_schema_validation
- `idempotency`：move_and_target_type_deterministic_key_with_target_state_replay
- `reverse`：invoice.type.switch_to_original_type

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the generic core-write path, closed target enum, deterministic key and exact draft result binding.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_core_write_cli.py, tests/unit/test_invoice_copy_type_contract.py, tests/unit/test_invoice_copy_type_runtime.py
- `integration`：`implemented`；The guarded live smoke verifies native draft duplication, type switching and rollback.；引用：tests/integration/test_invoice_duplicate_type_switch_batch_live.py
- `golden`：`planned`；Golden examples are deferred.；引用：无
- `e2e`：`planned`；Natural-language routing is deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-update"></a>

## invoice.update — 更新草稿发票或账单表头

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`invoices_and_bills`；来源模型：account.fiscal.position, account.journal, account.move, account.payment.term, res.company, res.currency, res.partner, res.partner.bank；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.fiscal.position:read, account.journal:read, account.move:read, account.move:write, account.payment.term:read, res.currency:read, res.partner.bank:read, res.partner:read。
- 请求/响应合同：`schemas/v1/invoice.update.request.schema.json` / `schemas/v1/invoice.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.update --request "@request.json" --idempotency-key "invoice.update:1:0dab72ac511abe674c7aa19954f4c0ac" --confirm "invoice.update"
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
    "move_id": 1,
    "changes": {
      "partner_id": 1
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id","changes"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1,"not":{"required":["invoice_date_due","payment_term_id"]}} |
| parameters.changes.partner_id | integer | 可选（可能有条件限制） |  | 合作伙伴ID | {"minimum":1} |
| parameters.changes.journal_id | integer | 可选（可能有条件限制） |  | 日记账ID | {"minimum":1} |
| parameters.changes.currency_id | integer | 可选（可能有条件限制） |  | 币种ID | {"minimum":1} |
| parameters.changes.invoice_date | string | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.changes.date | string | 可选（可能有条件限制） |  | Accounting date for a draft invoice, bill, or refund. Native Odoo posting and lock-date rules still apply. | {"format":"date"} |
| parameters.changes.invoice_date_due | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.changes.partner_bank_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.changes.fiscal_position_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.changes.payment_term_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.changes.reference | string/null | 可选（可能有条件限制） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$"} |
| parameters.changes.payment_reference | string/null | 可选（可能有条件限制） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.update"} |
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
- `execute`：native_draft_header_or_posted_reference_fields_and_unsent_partner_bank_only
- `verify`：same_transaction_target_header_payload_reread_and_response_schema_validation
- `idempotency`：target_header_payload_state_check_before_native_write
- `reverse`：repeat_update_with_previous_header_values

### 已登记测试与证据范围

- `unit`：`implemented`；Focused closed-input, legacy omission/key, company/state/ACL and result binding tests; execution is required before acceptance.；引用：tests/unit/test_accounting_maintenance_batch.py
- `integration`：`implemented`；One shared public CLI/native ORM workflow passed both isolated aliases in 24.70s as uid5/su=False/company1. Two new IDs and six extensions: exact-current-root currency-rate correction/date/replay, native technical Float readback, conversion/delete fallback and missing denial; explicit foreign-bank positive/negative paired amount set/clear/replay while legacy omitted shapes remain unchanged; reconciled statement membership/detach retaining native lines, posted moves, financial snapshots and matching graphs; posted unsent invoice bank set/clear with native PDF-link sent denial; posted preferred-method wizard default and Incoterm/location set/clear; a real partially reconciled invoice retaining raw matching IDs/amounts and financial lines. Native configuration roles exist only inside the isolated transaction, never sudo business calls. Fresh tracked fixtures, both companies settings, all defaults, currencies/rates and exact caller/native group memberships roll back. Live companies are independent roots; branch context rejection has unit evidence only. PDF uses synthetic DB-only raw bytes and native linking, not generation or delivery. Wizard defaults do not make payments. All hierarchy/currency/precision/localization/hash/lock paths, fully-paid/CABA invoices, existing foreign-invoice revaluation and concurrent exactly-once are not claimed. Legacy currency.rate.record guard is unchanged. No business DB, native source/addon, configuration, service or external-send changes.；引用：tests/integration/test_accounting_maintenance_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。
