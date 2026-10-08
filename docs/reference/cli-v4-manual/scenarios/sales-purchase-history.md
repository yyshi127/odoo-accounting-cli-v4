# 历史销售采购订单、行明细与订单输出

查询销售采购订单、精确行明细及开票状态，管理订单草稿、行替换、确认和取消，生成订单分析汇总，并导出销售订单、采购订单或询价单。历史订单接口不是新增会计发票接口的别名；从订单生成发票、预付款或账单分别在客户和供应商开票场景。

[回到总说明书](../../CLI_V4_MANUAL.md) · [新会话使用指南](../USAGE_GUIDE.md)

<a id="cap-purchase-order-analysis-summary"></a>

## purchase.order.analysis.summary — 汇总分析采购订单

- 类型：只读；静态状态：`unconfigured`；handler：`purchase_order_analysis_summary`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, modules, and ACLs.
- 内部domain：`purchase_accounting`；来源模型：purchase.order, res.company, res.currency, res.partner, res.users；向导：无。
- 必需模块：base, purchase；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：purchase.order:read, res.company:read, res.currency:read, res.partner:read, res.users:read。
- 请求/响应合同：`schemas/v1/purchase.order.analysis.summary.request.schema.json` / `schemas/v1/purchase.order.analysis.summary.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read purchase.order.analysis.summary --request "@request.json"
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
    "date_from": "2026-10-01",
    "date_to": "2026-10-31",
    "group_by": "state"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to","group_by"],"resolved_ref":"#/$defs/parameters"} |
| parameters.date_from | string | 必填（所在对象出现时） |  | 开始日期 | {"format":"date"} |
| parameters.date_to | string | 必填（所在对象出现时） |  | 结束日期 | {"format":"date"} |
| parameters.group_by | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["state","invoice_status","partner","buyer","currency"]} |
| parameters.states | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"oneOf":[{"type":"null"},{"items":{"enum":["draft","sent","to approve","purchase","cancel"]},"maxItems":5,"minItems":1,"type":"array","uniqueItems":true}],"resolved_ref":"#/$defs/nullableStates"} |
| parameters.states | null | 分支约束 | oneOf[1] |  |  |
| parameters.states | array | 分支约束 | oneOf[2] |  | {"maxItems":5,"minItems":1,"uniqueItems":true} |
| parameters.states[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["draft","sent","to approve","purchase","cancel"]} |
| parameters.partner_id | integer/null | 可选（可能有条件限制） |  | 合作伙伴ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.currency_id | integer/null | 可选（可能有条件限制） |  | 币种ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.user_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.payment_term_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.fiscal_position_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.invoice_statuses | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"oneOf":[{"type":"null"},{"items":{"enum":["no","to invoice","invoiced"]},"maxItems":3,"minItems":1,"type":"array","uniqueItems":true}]} |
| parameters.invoice_statuses | null | 分支约束 | oneOf[1] |  |  |
| parameters.invoice_statuses | array | 分支约束 | oneOf[2] |  | {"maxItems":3,"minItems":1,"uniqueItems":true} |
| parameters.invoice_statuses[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["no","to invoice","invoiced"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"purchase.order.analysis.summary"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["company_id","group_by","date_from","date_to","groups","totals_by_currency"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.group_by | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["state","invoice_status","partner","buyer","currency"]} |
| response.data.date_from | string | 必填（所在对象出现时） | oneOf[2] | 开始日期 | {"format":"date"} |
| response.data.date_to | string | 必填（所在对象出现时） | oneOf[2] | 结束日期 | {"format":"date"} |
| response.data.groups | array | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.groups[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["group","currency","order_count","amount_untaxed","amount_tax","amount_total"],"resolved_ref":"#/$defs/groupRow"} |
| response.data.groups[].group | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","value"],"resolved_ref":"#/$defs/group"} |
| response.data.groups[].group.id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.groups[].group.value | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.groups[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.groups[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.groups[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.groups[].order_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.groups[].amount_untaxed | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.groups[].amount_tax | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.groups[].amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.totals_by_currency | array | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.totals_by_currency[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["currency","order_count","amount_untaxed","amount_tax","amount_total"],"resolved_ref":"#/$defs/total"} |
| response.data.totals_by_currency[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.totals_by_currency[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.totals_by_currency[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.totals_by_currency[].order_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.totals_by_currency[].amount_untaxed | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.totals_by_currency[].amount_tax | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.totals_by_currency[].amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["company_id","group_by","date_from","date_to","groups","totals_by_currency"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.group_by | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["state","invoice_status","partner","buyer","currency"]} |
| response.data.date_from | string | 必填（所在对象出现时） | allOf[1]/then | 开始日期 | {"format":"date"} |
| response.data.date_to | string | 必填（所在对象出现时） | allOf[1]/then | 结束日期 | {"format":"date"} |
| response.data.groups | array | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.groups[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["group","currency","order_count","amount_untaxed","amount_tax","amount_total"],"resolved_ref":"#/$defs/groupRow"} |
| response.data.groups[].group | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","value"],"resolved_ref":"#/$defs/group"} |
| response.data.groups[].group.id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.groups[].group.value | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.groups[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.groups[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.groups[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.groups[].order_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.groups[].amount_untaxed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.groups[].amount_tax | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.groups[].amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.totals_by_currency | array | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.totals_by_currency[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["currency","order_count","amount_untaxed","amount_tax","amount_total"],"resolved_ref":"#/$defs/total"} |
| response.data.totals_by_currency[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.totals_by_currency[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.totals_by_currency[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.totals_by_currency[].order_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.totals_by_currency[].amount_untaxed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.totals_by_currency[].amount_tax | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.totals_by_currency[].amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
- `execute`：fixed_company_scoped_purchase_order_read_group
- `verify`：read_only_transaction_acl_grouping_currency_totals_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover fixed groupings, per-currency totals, company and ACL scope, schemas, and CLI dispatch. Native optional projections and explicit accounting filters are covered.；引用：tests/unit/test_order_documents.py, tests/unit/test_order_documents_bridge.py, tests/unit/test_order_documents_runtime.py, tests/unit/test_order_documents_schemas.py, tests/unit/test_order_documents_cli.py, tests/unit/test_capability_registry.py, tests/unit/test_order_accounting_reads_contract.py, tests/unit/test_order_accounting_reads_runtime.py, tests/unit/test_order_accounting_reads_cli.py
- `integration`：`implemented`；The guarded shared smoke exercises sales and purchase order reads in both dedicated isolated databases.；引用：tests/integration/test_order_documents_batch_live.py, tests/integration/test_order_accounting_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-purchase-order-cancel"></a>

## purchase.order.cancel — 取消采购订单

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user. Replay uses a target-state recheck without a persistent operation store, so an old request can become effective after an intervening state change.
- 内部domain：`purchase_accounting`；来源模型：purchase.order, purchase.order.line, res.company；向导：无。
- 必需模块：account, base, purchase, purchase_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：purchase.group_purchase_user；ACL：purchase.order:read, purchase.order:write, purchase.order.line:read, res.company:read。
- 请求/响应合同：`schemas/v1/purchase.order.cancel.request.schema.json` / `schemas/v1/purchase.order.cancel.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run purchase.order.cancel --request "@request.json" --idempotency-key "purchase.order.cancel:1" --confirm "purchase.order.cancel"
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
    "order_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["order_id"],"resolved_ref":"purchase.order.confirm.request.schema.json#/$defs/parameters"} |
| parameters.order_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"purchase.order.cancel"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"purchase.order.cancel"} |
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
- `execute`：fixed_native_purchase_order_button_cancel
- `verify`：same_transaction_cancelled_state_and_response_schema_validation
- `idempotency`：target_cancelled_state_recheck_without_operation_store
- `reverse`：purchase.order.reset_to_draft_when_native_state_allows

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover native cancellation preconditions, exact confirmation, native ACLs, target-state replay, schemas, and CLI dispatch.；引用：tests/unit/test_order_document_writes.py, tests/unit/test_order_document_writes_runtime.py, tests/unit/test_order_document_write_cli.py, tests/unit/test_order_document_write_schemas.py
- `integration`：`implemented`；The guarded shared live smoke verifies native cancellation, replay, and rollback in both dedicated isolated databases.；引用：tests/integration/test_order_document_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-purchase-order-confirm"></a>

## purchase.order.confirm — 确认采购订单

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user. Replay uses a target-state recheck without a persistent operation store, so an old request can become effective after an intervening state change.
- 内部domain：`purchase_accounting`；来源模型：purchase.order, purchase.order.line, res.company；向导：无。
- 必需模块：account, base, purchase, purchase_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：purchase.group_purchase_user；ACL：purchase.order:read, purchase.order:write, purchase.order.line:read, res.company:read。
- 请求/响应合同：`schemas/v1/purchase.order.confirm.request.schema.json` / `schemas/v1/purchase.order.confirm.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run purchase.order.confirm --request "@request.json" --idempotency-key "purchase.order.confirm:1" --confirm "purchase.order.confirm"
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
    "order_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["order_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.order_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"purchase.order.confirm"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"purchase.order.confirm"} |
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
- `execute`：fixed_native_purchase_order_button_confirm
- `verify`：same_transaction_confirmed_state_and_response_schema_validation
- `idempotency`：target_confirmed_state_recheck_without_operation_store
- `reverse`：purchase.order.cancel_when_native_state_allows

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the native confirmation preconditions, exact confirmation, native ACLs, target-state replay, schemas, and CLI dispatch.；引用：tests/unit/test_order_document_writes.py, tests/unit/test_order_document_writes_runtime.py, tests/unit/test_order_document_write_cli.py, tests/unit/test_order_document_write_schemas.py
- `integration`：`implemented`；The guarded shared live smoke verifies native confirmation, replay, and rollback in both dedicated isolated databases.；引用：tests/integration/test_order_document_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-purchase-order-create"></a>

## purchase.order.create — 创建草稿采购订单

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`odoo_order_marker_not_concurrency_unique` — The fixed handler supports ordinary replay with a deterministic visible marker, but Odoo provides no database-unique operation key, so concurrent exactly-once creation is not proven.
- 内部domain：`purchase_accounting`；来源模型：account.incoterms, account.payment.term, account.tax, product.product, purchase.order, purchase.order.line, res.company, res.currency, res.partner, stock.picking.type, uom.uom；向导：无。
- 必需模块：account, base, purchase, purchase_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：purchase.group_purchase_user；ACL：purchase.order:read, purchase.order:create, purchase.order:write, purchase.order.line:read, purchase.order.line:create, purchase.order.line:write, res.company:read。
- 请求/响应合同：`schemas/v1/purchase.order.create.request.schema.json` / `schemas/v1/purchase.order.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run purchase.order.create --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "purchase.order.create"
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
    "partner_id": 1,
    "currency_id": 1,
    "picking_type_id": 1,
    "date_order": "2026-10-03 09:00:00",
    "partner_ref": "1",
    "payment_term_id": 1,
    "incoterm_id": 1,
    "lines": [
      {
        "product_id": 1,
        "name": "Example",
        "quantity": "1",
        "uom_id": 1,
        "price_unit": "1",
        "discount": "1",
        "tax_ids": [],
        "date_planned": "2026-10-03 09:00:00"
      }
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["partner_id","currency_id","picking_type_id","date_order","partner_ref","payment_term_id","incoterm_id","lines"]} |
| parameters.partner_id | integer | 必填（所在对象出现时） |  | 合作伙伴ID | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.currency_id | integer | 必填（所在对象出现时） |  | 币种ID | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.picking_type_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.date_order | string | 必填（所在对象出现时） |  |  | {"pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$","resolved_ref":"#/$defs/datetime"} |
| parameters.partner_ref | string/null | 必填（所在对象出现时） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$","resolved_ref":"#/$defs/nullable_text"} |
| parameters.payment_term_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullable_id"} |
| parameters.incoterm_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullable_id"} |
| parameters.lines | array | 必填（所在对象出现时） |  | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":200,"minItems":1} |
| parameters.lines[] | object | 每个数组元素 |  | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["product_id","name","quantity","uom_id","price_unit","discount","tax_ids","date_planned"],"resolved_ref":"#/$defs/line"} |
| parameters.lines[].product_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.lines[].name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":500,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$"} |
| parameters.lines[].quantity | string | 必填（所在对象出现时） |  | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/positive_decimal"} |
| parameters.lines[].uom_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.lines[].price_unit | string | 必填（所在对象出现时） |  | 单价；币种及符号依单据和合同 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegative_decimal"} |
| parameters.lines[].discount | string | 必填（所在对象出现时） |  | 折扣百分比 | {"maxLength":256,"pattern":"^(?:0&#124;100&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]*[1-9])?)$(?![\\s\\S])","resolved_ref":"#/$defs/percentage_decimal"} |
| parameters.lines[].tax_ids | array | 必填（所在对象出现时） |  | 应用税ID数组 | {"uniqueItems":true} |
| parameters.lines[].tax_ids[] | integer | 每个数组元素 |  | 应用税ID数组 | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.lines[].date_planned | string | 必填（所在对象出现时） |  |  | {"pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$","resolved_ref":"#/$defs/datetime"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"purchase.order.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"purchase.order.create"} |
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
- `execute`：fixed_native_purchase_order_create_as_configured_business_user
- `verify`：same_transaction_company_order_lines_and_response_schema_validation
- `idempotency`：deterministic_visible_marker_and_ordinary_result_replay_without_database_uniqueness
- `reverse`：cancel_or_delete_the_draft_purchase_order

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request, exact confirmation, fixed ORM path, native ACLs, ordinary replay, result validation, schemas, and CLI dispatch.；引用：tests/unit/test_order_document_writes.py, tests/unit/test_order_document_writes_runtime.py, tests/unit/test_order_document_write_cli.py, tests/unit/test_order_document_write_schemas.py
- `integration`：`implemented`；The guarded shared live smoke verifies creation, replay, and rollback in both dedicated isolated databases.；引用：tests/integration/test_order_document_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-purchase-order-get"></a>

## purchase.order.get — 获取采购订单详情

- 类型：只读；静态状态：`unconfigured`；handler：`purchase_order_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, modules, and ACLs.
- 内部domain：`purchase_accounting`；来源模型：account.move, account.move.line, account.tax, product.product, purchase.order, purchase.order.line, res.company, res.currency, res.partner, res.users, stock.location, stock.move, stock.picking, uom.uom；向导：无。
- 必需模块：account, base, purchase, purchase_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.move:read, account.move.line:read, account.tax:read, product.product:read, purchase.order:read, purchase.order.line:read, res.company:read, res.currency:read, res.partner:read, res.users:read, stock.location:read, stock.move:read, stock.picking:read, uom.uom:read。
- 请求/响应合同：`schemas/v1/purchase.order.get.request.schema.json` / `schemas/v1/purchase.order.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read purchase.order.get --request "@request.json"
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
    "order_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["order_id"]} |
| parameters.order_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"purchase.order.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","company","partner","state","date_order","currency","user","invoice_status","amount_untaxed","amount_tax","amount_total","invoice_ids","transfer_ids","line_count","date_approve","partner_ref","origin","receipt_status","lines","invoices","transfers"],"resolved_ref":"#/$defs/data"} |
| response.data.payment_term_id | integer/null | 可选（可能有条件限制） | oneOf[2] |  | {"minimum":1} |
| response.data.fiscal_position_id | integer/null | 可选（可能有条件限制） | oneOf[2] |  | {"minimum":1} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.company | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.company.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.partner | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","sent","to approve","purchase","cancel"]} |
| response.data.date_order | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.user | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.user | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.user | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.user.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.user.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.invoice_status | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["no","to invoice","invoiced"]} |
| response.data.amount_untaxed | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_tax | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.invoice_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.invoice_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.transfer_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.transfer_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.line_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.date_approve | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/utcDateTime"}],"resolved_ref":"#/$defs/nullableUtcDateTime"} |
| response.data.date_approve | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.date_approve | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.partner_ref | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.origin | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.receipt_status | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["pending","partial","full",null]} |
| response.data.lines | array | 必填（所在对象出现时） | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 |  |
| response.data.lines[] | object | 每个数组元素 | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","order","company","partner","state","date_order","sequence","display_type","description","product","uom","ordered_quantity","invoiced_quantity","to_invoice_quantity","unit_price","discount_percent","amount_untaxed","amount_tax","amount_total","currency","taxes","invoice_line_ids","stock_move_ids","received_quantity","to_receive_quantity","date_planned"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].is_downpayment | boolean | 可选（可能有条件限制） | oneOf[2] |  |  |
| response.data.lines[].purchase_method | 未限定 | 可选（可能有条件限制） | oneOf[2] | Native template-shared billing policy, not a company-dependent setting. | {"enum":["purchase","receive",null]} |
| response.data.lines[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].order | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].order.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].order.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].company | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].company.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].company.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].partner | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].partner.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].partner.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","sent","to approve","purchase","cancel"]} |
| response.data.lines[].date_order | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.lines[].sequence | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.lines[].display_type | string/null | 必填（所在对象出现时） | oneOf[2] | 业务行/章节/备注类型 | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.lines[].description | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.lines[].product | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.lines[].product | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].product | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].product.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].product.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].uom | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.lines[].uom | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].uom | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].uom.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].uom.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].ordered_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].invoiced_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].to_invoice_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].received_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].to_receive_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].unit_price | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].discount_percent | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].amount_untaxed | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].amount_tax | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.lines[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.lines[].taxes | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.lines[].taxes[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].taxes[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].taxes[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].invoice_line_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.lines[].invoice_line_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].stock_move_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.lines[].stock_move_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].date_planned | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/utcDateTime"}],"resolved_ref":"#/$defs/nullableUtcDateTime"} |
| response.data.lines[].date_planned | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].date_planned | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.invoices | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.invoices[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","payment_state","amount_total","currency"],"resolved_ref":"#/$defs/invoice"} |
| response.data.invoices[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.invoices[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.invoices[].move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["in_invoice","in_refund","in_receipt"]} |
| response.data.invoices[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.invoices[].payment_state | string/null | 必填（所在对象出现时） | oneOf[2] | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy",null]} |
| response.data.invoices[].amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.invoices[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.invoices[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.invoices[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.transfers | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.transfers[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","state","source_location","destination_location"],"resolved_ref":"#/$defs/transfer"} |
| response.data.transfers[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.transfers[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.transfers[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","waiting","confirmed","assigned","done","cancel"]} |
| response.data.transfers[].source_location | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.transfers[].source_location.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.transfers[].source_location.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.transfers[].destination_location | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.transfers[].destination_location.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.transfers[].destination_location.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","company","partner","state","date_order","currency","user","invoice_status","amount_untaxed","amount_tax","amount_total","invoice_ids","transfer_ids","line_count","date_approve","partner_ref","origin","receipt_status","lines","invoices","transfers"],"resolved_ref":"#/$defs/data"} |
| response.data.payment_term_id | integer/null | 可选（可能有条件限制） | allOf[1]/then |  | {"minimum":1} |
| response.data.fiscal_position_id | integer/null | 可选（可能有条件限制） | allOf[1]/then |  | {"minimum":1} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.company | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.company.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.partner | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","sent","to approve","purchase","cancel"]} |
| response.data.date_order | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.user | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.user | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.user | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.user.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.user.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.invoice_status | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["no","to invoice","invoiced"]} |
| response.data.amount_untaxed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_tax | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.invoice_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.invoice_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.transfer_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.transfer_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.line_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.date_approve | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/utcDateTime"}],"resolved_ref":"#/$defs/nullableUtcDateTime"} |
| response.data.date_approve | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.date_approve | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.partner_ref | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.origin | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.receipt_status | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["pending","partial","full",null]} |
| response.data.lines | array | 必填（所在对象出现时） | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| response.data.lines[] | object | 每个数组元素 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","order","company","partner","state","date_order","sequence","display_type","description","product","uom","ordered_quantity","invoiced_quantity","to_invoice_quantity","unit_price","discount_percent","amount_untaxed","amount_tax","amount_total","currency","taxes","invoice_line_ids","stock_move_ids","received_quantity","to_receive_quantity","date_planned"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].is_downpayment | boolean | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response.data.lines[].purchase_method | 未限定 | 可选（可能有条件限制） | allOf[1]/then | Native template-shared billing policy, not a company-dependent setting. | {"enum":["purchase","receive",null]} |
| response.data.lines[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].order | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].order.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].order.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.lines[].company | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].company.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].company.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.lines[].partner | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].partner.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].partner.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.lines[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","sent","to approve","purchase","cancel"]} |
| response.data.lines[].date_order | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.lines[].sequence | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.lines[].display_type | string/null | 必填（所在对象出现时） | allOf[1]/then | 业务行/章节/备注类型 | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.lines[].description | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.lines[].product | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.lines[].product | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].product | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].product.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].product.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].uom | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.lines[].uom | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].uom | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].uom.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].uom.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].ordered_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].invoiced_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].to_invoice_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].received_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].to_receive_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].unit_price | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].discount_percent | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].amount_untaxed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].amount_tax | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.lines[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.lines[].taxes | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.lines[].taxes[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].taxes[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].taxes[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.lines[].invoice_line_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.lines[].invoice_line_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].stock_move_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.lines[].stock_move_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].date_planned | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/utcDateTime"}],"resolved_ref":"#/$defs/nullableUtcDateTime"} |
| response.data.lines[].date_planned | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].date_planned | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.invoices | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.invoices[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","payment_state","amount_total","currency"],"resolved_ref":"#/$defs/invoice"} |
| response.data.invoices[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.invoices[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.invoices[].move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["in_invoice","in_refund","in_receipt"]} |
| response.data.invoices[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.invoices[].payment_state | string/null | 必填（所在对象出现时） | allOf[1]/then | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy",null]} |
| response.data.invoices[].amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.invoices[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.invoices[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.invoices[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.transfers | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.transfers[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","state","source_location","destination_location"],"resolved_ref":"#/$defs/transfer"} |
| response.data.transfers[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.transfers[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.transfers[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","waiting","confirmed","assigned","done","cancel"]} |
| response.data.transfers[].source_location | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.transfers[].source_location.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.transfers[].source_location.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.transfers[].destination_location | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.transfers[].destination_location.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.transfers[].destination_location.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
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
- `execute`：fixed_company_scoped_purchase_order_get
- `verify`：read_only_transaction_acl_identity_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover exact identity, lines and linked documents, company and ACL scope, schemas, and CLI dispatch. Native optional projections and explicit accounting filters are covered.；引用：tests/unit/test_order_documents.py, tests/unit/test_order_documents_bridge.py, tests/unit/test_order_documents_runtime.py, tests/unit/test_order_documents_schemas.py, tests/unit/test_order_documents_cli.py, tests/unit/test_capability_registry.py, tests/unit/test_order_accounting_reads_contract.py, tests/unit/test_order_accounting_reads_runtime.py, tests/unit/test_order_accounting_reads_cli.py
- `integration`：`implemented`；The guarded shared smoke exercises sales and purchase order reads in both dedicated isolated databases.；引用：tests/integration/test_order_documents_batch_live.py, tests/integration/test_order_accounting_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-purchase-order-line-get"></a>

## purchase.order.line.get — 读取采购订单行

- 类型：只读；静态状态：`unconfigured`；handler：`purchase_order_line_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, modules, and ACLs.
- 内部domain：`purchase_accounting`；来源模型：account.move, account.move.line, account.tax, product.product, purchase.order, purchase.order.line, res.company, res.currency, res.partner, res.users, stock.move, uom.uom；向导：无。
- 必需模块：account, base, purchase, purchase_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.move:read, account.move.line:read, account.tax:read, product.product:read, purchase.order:read, purchase.order.line:read, res.company:read, res.currency:read, res.partner:read, res.users:read, stock.move:read, uom.uom:read。
- 请求/响应合同：`schemas/v1/purchase.order.line.get.request.schema.json` / `schemas/v1/purchase.order.line.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read purchase.order.line.get --request "@request.json"
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
    "line_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  |  |
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["line_id"]} |
| parameters.line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"purchase.order.line.get"},"data":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"purchase.order.line.get"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","order","company","partner","state","date_order","sequence","display_type","description","product","uom","ordered_quantity","invoiced_quantity","to_invoice_quantity","unit_price","discount_percent","amount_untaxed","amount_tax","amount_total","currency","taxes","invoice_line_ids","stock_move_ids","received_quantity","to_receive_quantity","date_planned","invoices"],"resolved_ref":"#/$defs/data"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1,"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/id"} |
| response.data.order | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/order"} |
| response.data.order.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.order.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.company | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/company"} |
| response.data.company.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.company.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.partner | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/partner"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"enum":["draft","sent","to approve","purchase","cancel"],"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/state"} |
| response.data.date_order | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/date_order"} |
| response.data.sequence | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":0,"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/sequence"} |
| response.data.display_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 业务行/章节/备注类型 | {"minLength":1,"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/display_type"} |
| response.data.description | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/description"} |
| response.data.product | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/product"} |
| response.data.product | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.product | object | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.product.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.product.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.uom | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/uom"} |
| response.data.uom | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.uom | object | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.uom.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.uom.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.ordered_quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/ordered_quantity"} |
| response.data.invoiced_quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/invoiced_quantity"} |
| response.data.to_invoice_quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/to_invoice_quantity"} |
| response.data.unit_price | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/unit_price"} |
| response.data.discount_percent | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/discount_percent"} |
| response.data.amount_untaxed | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/amount_untaxed"} |
| response.data.amount_tax | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/amount_tax"} |
| response.data.amount_total | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/amount_total"} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.taxes | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/taxes","uniqueItems":true} |
| response.data.taxes[] | object | 每个数组元素 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.taxes[].id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.taxes[].name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.invoice_line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/invoice_line_ids","uniqueItems":true} |
| response.data.invoice_line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.stock_move_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/stock_move_ids","uniqueItems":true} |
| response.data.stock_move_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.received_quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/received_quantity"} |
| response.data.to_receive_quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/to_receive_quantity"} |
| response.data.date_planned | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/utcDateTime"}],"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/date_planned"} |
| response.data.date_planned | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.date_planned | string | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.is_downpayment | boolean | 可选（可能有条件限制） | allOf[2]/oneOf[2] |  | {"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/is_downpayment"} |
| response.data.purchase_method | 未限定 | 可选（可能有条件限制） | allOf[2]/oneOf[2] | Native template-shared billing policy, not a company-dependent setting. | {"enum":["purchase","receive",null],"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/purchase_method"} |
| response.data.invoices | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.invoices[] | object | 每个数组元素 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","payment_state","amount_total","currency"],"resolved_ref":"purchase.order.get.response.schema.json#/$defs/invoice"} |
| response.data.invoices[].id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.invoices[].name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.invoices[].move_type | 未限定 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"enum":["in_invoice","in_refund","in_receipt"]} |
| response.data.invoices[].state | 未限定 | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.invoices[].payment_state | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy",null]} |
| response.data.invoices[].amount_total | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.invoices[].currency | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.invoices[].currency.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.invoices[].currency.code | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["id","order","company","partner","state","date_order","sequence","display_type","description","product","uom","ordered_quantity","invoiced_quantity","to_invoice_quantity","unit_price","discount_percent","amount_untaxed","amount_tax","amount_total","currency","taxes","invoice_line_ids","stock_move_ids","received_quantity","to_receive_quantity","date_planned","invoices"],"resolved_ref":"#/$defs/data"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1,"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/id"} |
| response.data.order | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/order"} |
| response.data.order.id | integer | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.order.name | string | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.company | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/company"} |
| response.data.company.id | integer | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.company.name | string | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.partner | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/partner"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"enum":["draft","sent","to approve","purchase","cancel"],"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/state"} |
| response.data.date_order | string | 必填（所在对象出现时） | allOf[3]/then |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/date_order"} |
| response.data.sequence | integer | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":0,"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/sequence"} |
| response.data.display_type | string/null | 必填（所在对象出现时） | allOf[3]/then | 业务行/章节/备注类型 | {"minLength":1,"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/display_type"} |
| response.data.description | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/description"} |
| response.data.product | 组合/开放结构 | 必填（所在对象出现时） | allOf[3]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/product"} |
| response.data.product | null | 分支约束 | allOf[3]/then/oneOf[1] |  |  |
| response.data.product | object | 分支约束 | allOf[3]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.product.id | integer | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] |  | {"minimum":1} |
| response.data.product.name | string | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.uom | 组合/开放结构 | 必填（所在对象出现时） | allOf[3]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/uom"} |
| response.data.uom | null | 分支约束 | allOf[3]/then/oneOf[1] |  |  |
| response.data.uom | object | 分支约束 | allOf[3]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.uom.id | integer | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] |  | {"minimum":1} |
| response.data.uom.name | string | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.ordered_quantity | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/ordered_quantity"} |
| response.data.invoiced_quantity | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/invoiced_quantity"} |
| response.data.to_invoice_quantity | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/to_invoice_quantity"} |
| response.data.unit_price | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/unit_price"} |
| response.data.discount_percent | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/discount_percent"} |
| response.data.amount_untaxed | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/amount_untaxed"} |
| response.data.amount_tax | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/amount_tax"} |
| response.data.amount_total | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/amount_total"} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[3]/then |  | {"maxLength":3,"minLength":1} |
| response.data.taxes | array | 必填（所在对象出现时） | allOf[3]/then |  | {"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/taxes","uniqueItems":true} |
| response.data.taxes[] | object | 每个数组元素 | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.taxes[].id | integer | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.taxes[].name | string | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.invoice_line_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/invoice_line_ids","uniqueItems":true} |
| response.data.invoice_line_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.stock_move_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/stock_move_ids","uniqueItems":true} |
| response.data.stock_move_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.received_quantity | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/received_quantity"} |
| response.data.to_receive_quantity | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/to_receive_quantity"} |
| response.data.date_planned | 组合/开放结构 | 必填（所在对象出现时） | allOf[3]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/utcDateTime"}],"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/date_planned"} |
| response.data.date_planned | null | 分支约束 | allOf[3]/then/oneOf[1] |  |  |
| response.data.date_planned | string | 分支约束 | allOf[3]/then/oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.is_downpayment | boolean | 可选（可能有条件限制） | allOf[3]/then |  | {"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/is_downpayment"} |
| response.data.purchase_method | 未限定 | 可选（可能有条件限制） | allOf[3]/then | Native template-shared billing policy, not a company-dependent setting. | {"enum":["purchase","receive",null],"resolved_ref":"purchase.order.line.search.response.schema.json#/$defs/line/properties/purchase_method"} |
| response.data.invoices | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.invoices[] | object | 每个数组元素 | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","payment_state","amount_total","currency"],"resolved_ref":"purchase.order.get.response.schema.json#/$defs/invoice"} |
| response.data.invoices[].id | integer | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.invoices[].name | string | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.invoices[].move_type | 未限定 | 必填（所在对象出现时） | allOf[3]/then |  | {"enum":["in_invoice","in_refund","in_receipt"]} |
| response.data.invoices[].state | 未限定 | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.invoices[].payment_state | string/null | 必填（所在对象出现时） | allOf[3]/then | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy",null]} |
| response.data.invoices[].amount_total | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.invoices[].currency | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.invoices[].currency.id | integer | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.invoices[].currency.code | string | 必填（所在对象出现时） | allOf[3]/then |  | {"maxLength":3,"minLength":1} |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_company_scoped_order_line_get_with_visible_invoice_graph
- `verify`：ordinary_user_acl_exact_line_identity_native_projection_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Fixed exact-line contract, optional native projections, visible invoice graph, ACL and CLI dispatch.；引用：tests/unit/test_order_accounting_reads_contract.py, tests/unit/test_order_accounting_reads_runtime.py, tests/unit/test_order_accounting_reads_cli.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；Shared native order accounting read smoke passed; full rollback.；引用：tests/integration/test_order_accounting_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-purchase-order-line-search"></a>

## purchase.order.line.search — 搜索采购订单行

- 类型：只读；静态状态：`unconfigured`；handler：`purchase_order_line_search`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, modules, and ACLs.
- 内部domain：`purchase_accounting`；来源模型：account.move.line, account.tax, product.product, purchase.order, purchase.order.line, res.company, res.currency, res.partner, res.users, stock.move, uom.uom；向导：无。
- 必需模块：account, base, purchase, purchase_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.move.line:read, account.tax:read, product.product:read, purchase.order:read, purchase.order.line:read, res.company:read, res.currency:read, res.partner:read, res.users:read, stock.move:read, uom.uom:read。
- 请求/响应合同：`schemas/v1/purchase.order.line.search.request.schema.json` / `schemas/v1/purchase.order.line.search.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read purchase.order.line.search --request "@request.json"
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
| parameters | object | 必填 |  |  | {"additionalProperties":false,"not":{"properties":{"negative_to_invoice_only":{"const":true},"to_invoice_only":{"const":true}},"required":["to_invoice_only","negative_to_invoice_only"]},"resolved_ref":"#/$defs/parameters"} |
| parameters.order_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.date_from | 组合/开放结构 | 可选（可能有条件限制） |  | 开始日期 | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| parameters.date_from | null | 分支约束 | oneOf[1] | 开始日期 |  |
| parameters.date_from | string | 分支约束 | oneOf[2] | 开始日期 | {"format":"date"} |
| parameters.date_to | 组合/开放结构 | 可选（可能有条件限制） |  | 结束日期 | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| parameters.date_to | null | 分支约束 | oneOf[1] | 结束日期 |  |
| parameters.date_to | string | 分支约束 | oneOf[2] | 结束日期 | {"format":"date"} |
| parameters.partner_id | integer/null | 可选（可能有条件限制） |  | 合作伙伴ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.product_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.states | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"oneOf":[{"type":"null"},{"items":{"enum":["draft","sent","to approve","purchase","cancel"]},"maxItems":5,"minItems":1,"type":"array","uniqueItems":true}],"resolved_ref":"#/$defs/nullableStates"} |
| parameters.states | null | 分支约束 | oneOf[1] |  |  |
| parameters.states | array | 分支约束 | oneOf[2] |  | {"maxItems":5,"minItems":1,"uniqueItems":true} |
| parameters.states[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["draft","sent","to approve","purchase","cancel"]} |
| parameters.to_receive_only | boolean | 可选（可能有条件限制） |  |  | {"default":false} |
| parameters.to_invoice_only | boolean | 可选（可能有条件限制） |  |  | {"default":false} |
| parameters.is_downpayment | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.negative_to_invoice_only | boolean | 可选（可能有条件限制） |  | Select negative native qty_to_invoice; includes down-payment deductions and does not guarantee a refund. |  |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/page"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"purchase.order.line.search"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/page"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/page"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","order","company","partner","state","date_order","sequence","display_type","description","product","uom","ordered_quantity","invoiced_quantity","to_invoice_quantity","unit_price","discount_percent","amount_untaxed","amount_tax","amount_total","currency","taxes","invoice_line_ids","stock_move_ids","received_quantity","to_receive_quantity","date_planned"],"resolved_ref":"#/$defs/line"} |
| response.data.items[].is_downpayment | boolean | 可选（可能有条件限制） | oneOf[2] |  |  |
| response.data.items[].purchase_method | 未限定 | 可选（可能有条件限制） | oneOf[2] | Native template-shared billing policy, not a company-dependent setting. | {"enum":["purchase","receive",null]} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].order | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].order.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].order.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].company | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].company.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].partner | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","sent","to approve","purchase","cancel"]} |
| response.data.items[].date_order | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.items[].sequence | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.items[].display_type | string/null | 必填（所在对象出现时） | oneOf[2] | 业务行/章节/备注类型 | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].description | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].product | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.items[].product | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].product | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].product.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].product.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].uom | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.items[].uom | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].uom | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].uom.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].uom.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].ordered_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].invoiced_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].to_invoice_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].received_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].to_receive_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].unit_price | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].discount_percent | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_untaxed | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_tax | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].taxes | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.items[].taxes[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].taxes[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].taxes[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].invoice_line_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.items[].invoice_line_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.items[].stock_move_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.items[].stock_move_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.items[].date_planned | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/utcDateTime"}],"resolved_ref":"#/$defs/nullableUtcDateTime"} |
| response.data.items[].date_planned | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].date_planned | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.has_more | boolean | 必填（所在对象出现时） | oneOf[2] | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | oneOf[2] | 下一页不透明游标，无后续时可为空 | {"minLength":1} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/page"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/page"} |
| response.data.items | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","order","company","partner","state","date_order","sequence","display_type","description","product","uom","ordered_quantity","invoiced_quantity","to_invoice_quantity","unit_price","discount_percent","amount_untaxed","amount_tax","amount_total","currency","taxes","invoice_line_ids","stock_move_ids","received_quantity","to_receive_quantity","date_planned"],"resolved_ref":"#/$defs/line"} |
| response.data.items[].is_downpayment | boolean | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response.data.items[].purchase_method | 未限定 | 可选（可能有条件限制） | allOf[1]/then | Native template-shared billing policy, not a company-dependent setting. | {"enum":["purchase","receive",null]} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].order | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].order.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].order.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].company | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].company.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].partner | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","sent","to approve","purchase","cancel"]} |
| response.data.items[].date_order | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.items[].sequence | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.items[].display_type | string/null | 必填（所在对象出现时） | allOf[1]/then | 业务行/章节/备注类型 | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].description | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].product | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.items[].product | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].product | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].product.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].product.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].uom | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.items[].uom | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].uom | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].uom.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].uom.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].ordered_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].invoiced_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].to_invoice_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].received_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].to_receive_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].unit_price | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].discount_percent | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_untaxed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_tax | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].taxes | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.items[].taxes[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].taxes[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].taxes[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].invoice_line_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.items[].invoice_line_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].stock_move_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.items[].stock_move_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].date_planned | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/utcDateTime"}],"resolved_ref":"#/$defs/nullableUtcDateTime"} |
| response.data.items[].date_planned | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].date_planned | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[1]/then | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[1]/then | 下一页不透明游标，无后续时可为空 | {"minLength":1} |
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
- `execute`：fixed_company_scoped_purchase_order_line_search
- `verify`：read_only_transaction_acl_cursor_pending_quantity_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover line filters, non-negative pending quantities, bound ASC cursors, company and ACL scope, schemas, and CLI dispatch. Native optional projections and explicit accounting filters are covered.；引用：tests/unit/test_order_documents.py, tests/unit/test_order_documents_bridge.py, tests/unit/test_order_documents_runtime.py, tests/unit/test_order_documents_schemas.py, tests/unit/test_order_documents_cli.py, tests/unit/test_capability_registry.py, tests/unit/test_order_accounting_reads_contract.py, tests/unit/test_order_accounting_reads_runtime.py, tests/unit/test_order_accounting_reads_cli.py
- `integration`：`implemented`；The guarded shared smoke exercises sales and purchase order reads in both dedicated isolated databases.；引用：tests/integration/test_order_documents_batch_live.py, tests/integration/test_order_accounting_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-purchase-order-lines-replace"></a>

## purchase.order.lines.replace — 替换草稿采购订单行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user. Replay uses a target-payload recheck without a persistent operation store, so an old request can become effective after an intervening state change.
- 内部domain：`purchase_accounting`；来源模型：account.tax, product.product, purchase.order, purchase.order.line, res.company, uom.uom；向导：无。
- 必需模块：account, base, purchase, purchase_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：purchase.group_purchase_user；ACL：purchase.order:read, purchase.order:write, purchase.order.line:read, purchase.order.line:create, purchase.order.line:write, purchase.order.line:unlink, res.company:read。
- 请求/响应合同：`schemas/v1/purchase.order.lines.replace.request.schema.json` / `schemas/v1/purchase.order.lines.replace.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run purchase.order.lines.replace --request "@request.json" --idempotency-key "purchase.order.lines.replace:1:2e1b225e286cf7d1c477c6c80cbee724" --confirm "purchase.order.lines.replace"
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
    "order_id": 1,
    "lines": [
      {
        "product_id": 1,
        "name": "Example",
        "quantity": "1",
        "uom_id": 1,
        "price_unit": "1",
        "discount": "1",
        "tax_ids": [],
        "date_planned": "2026-10-03 09:00:00"
      }
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["order_id","lines"]} |
| parameters.order_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.lines | array | 必填（所在对象出现时） |  | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":200,"minItems":1} |
| parameters.lines[] | object | 每个数组元素 |  | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["product_id","name","quantity","uom_id","price_unit","discount","tax_ids","date_planned"],"resolved_ref":"purchase.order.create.request.schema.json#/$defs/line"} |
| parameters.lines[].product_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.lines[].name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":500,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$"} |
| parameters.lines[].quantity | string | 必填（所在对象出现时） |  | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/positive_decimal"} |
| parameters.lines[].uom_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.lines[].price_unit | string | 必填（所在对象出现时） |  | 单价；币种及符号依单据和合同 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegative_decimal"} |
| parameters.lines[].discount | string | 必填（所在对象出现时） |  | 折扣百分比 | {"maxLength":256,"pattern":"^(?:0&#124;100&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]*[1-9])?)$(?![\\s\\S])","resolved_ref":"#/$defs/percentage_decimal"} |
| parameters.lines[].tax_ids | array | 必填（所在对象出现时） |  | 应用税ID数组 | {"uniqueItems":true} |
| parameters.lines[].tax_ids[] | integer | 每个数组元素 |  | 应用税ID数组 | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.lines[].date_planned | string | 必填（所在对象出现时） |  |  | {"pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$","resolved_ref":"#/$defs/datetime"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"purchase.order.lines.replace"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"purchase.order.lines.replace"} |
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
- `execute`：fixed_native_draft_purchase_order_line_replacement
- `verify`：same_transaction_exact_order_line_payload_and_response_schema_validation
- `idempotency`：target_line_payload_recheck_without_operation_store
- `reverse`：replace_with_the_previous_order_lines

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed line contract, draft-only replacement, exact confirmation, native ACLs, target-payload replay, schemas, and CLI dispatch.；引用：tests/unit/test_order_document_writes.py, tests/unit/test_order_document_writes_runtime.py, tests/unit/test_order_document_write_cli.py, tests/unit/test_order_document_write_schemas.py
- `integration`：`implemented`；The guarded shared live smoke verifies line replacement, replay, and rollback in both dedicated isolated databases.；引用：tests/integration/test_order_document_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-purchase-order-pdf-export"></a>

## purchase.order.pdf.export — 导出采购订单 PDF

- 类型：只读；静态状态：`unconfigured`；handler：`document_purchase_order_pdf_export`。
- 状态原因：`runtime_context_required` — The fixed native PDF handler is installed; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`document_exports`；来源模型：purchase.order, res.company, ir.actions.report；向导：无。
- 必需模块：purchase；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：purchase.group_purchase_user；ACL：purchase.order:read, res.company:read, ir.actions.report:read。
- 请求/响应合同：`schemas/v1/purchase.order.pdf.export.request.schema.json` / `schemas/v1/purchase.order.pdf.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read purchase.order.pdf.export --request "@request.json"
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
    "order_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["order_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.order_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"purchase.order.pdf.export"} |
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
- `execute`：fixed_native_purchase_order_qweb_pdf_action
- `verify`：bound_record_pdf_bytes_hash_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover the fixed action, exact contract, bridge, runtime, CLI routing, registry metadata, and schemas.；引用：tests/unit/test_document_exports.py, tests/unit/test_document_exports_bridge.py, tests/unit/test_document_exports_runtime.py, tests/unit/test_document_export_cli.py, tests/unit/test_document_export_registry.py
- `integration`：`implemented`；The shared read-only live smoke covers the fixed document export batch in both isolated databases.；引用：tests/integration/test_document_export_batch_live.py
- `golden`：`planned`；Golden PDF evidence is pending.；引用：无
- `e2e`：`planned`；End-to-end natural-language routing evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-purchase-order-reset_to_draft"></a>

## purchase.order.reset_to_draft — 将采购订单重置为草稿

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user. Replay uses a target-state recheck without a persistent operation store, so an old request can become effective after an intervening state change.
- 内部domain：`purchase_accounting`；来源模型：purchase.order, purchase.order.line, res.company；向导：无。
- 必需模块：account, base, purchase, purchase_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：purchase.group_purchase_user；ACL：purchase.order:read, purchase.order:write, purchase.order.line:read, res.company:read。
- 请求/响应合同：`schemas/v1/purchase.order.reset_to_draft.request.schema.json` / `schemas/v1/purchase.order.reset_to_draft.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run purchase.order.reset_to_draft --request "@request.json" --idempotency-key "purchase.order.reset_to_draft:1" --confirm "purchase.order.reset_to_draft"
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
    "order_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["order_id"],"resolved_ref":"purchase.order.confirm.request.schema.json#/$defs/parameters"} |
| parameters.order_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"purchase.order.reset_to_draft"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"purchase.order.reset_to_draft"} |
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
- `execute`：fixed_native_purchase_order_button_draft
- `verify`：same_transaction_draft_state_and_response_schema_validation
- `idempotency`：target_draft_state_recheck_without_operation_store
- `reverse`：purchase.order.confirm_when_native_state_allows

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover native reset preconditions, exact confirmation, native ACLs, target-state replay, schemas, and CLI dispatch.；引用：tests/unit/test_order_document_writes.py, tests/unit/test_order_document_writes_runtime.py, tests/unit/test_order_document_write_cli.py, tests/unit/test_order_document_write_schemas.py
- `integration`：`implemented`；The guarded shared live smoke verifies native reset, replay, and rollback in both dedicated isolated databases.；引用：tests/integration/test_order_document_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-purchase-order-search"></a>

## purchase.order.search — 搜索采购订单

- 类型：只读；静态状态：`unconfigured`；handler：`purchase_order_search`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, modules, and ACLs.
- 内部domain：`purchase_accounting`；来源模型：account.move, purchase.order, purchase.order.line, res.company, res.currency, res.partner, res.users, stock.picking；向导：无。
- 必需模块：account, base, purchase, purchase_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.move:read, purchase.order:read, purchase.order.line:read, res.company:read, res.currency:read, res.partner:read, res.users:read, stock.picking:read。
- 请求/响应合同：`schemas/v1/purchase.order.search.request.schema.json` / `schemas/v1/purchase.order.search.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read purchase.order.search --request "@request.json"
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
| parameters.query | string/null | 可选（可能有条件限制） |  | 搜索文本 | {"maxLength":200,"minLength":1} |
| parameters.date_from | 组合/开放结构 | 可选（可能有条件限制） |  | 开始日期 | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| parameters.date_from | null | 分支约束 | oneOf[1] | 开始日期 |  |
| parameters.date_from | string | 分支约束 | oneOf[2] | 开始日期 | {"format":"date"} |
| parameters.date_to | 组合/开放结构 | 可选（可能有条件限制） |  | 结束日期 | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| parameters.date_to | null | 分支约束 | oneOf[1] | 结束日期 |  |
| parameters.date_to | string | 分支约束 | oneOf[2] | 结束日期 | {"format":"date"} |
| parameters.states | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"oneOf":[{"type":"null"},{"items":{"enum":["draft","sent","to approve","purchase","cancel"]},"maxItems":5,"minItems":1,"type":"array","uniqueItems":true}],"resolved_ref":"#/$defs/nullableStates"} |
| parameters.states | null | 分支约束 | oneOf[1] |  |  |
| parameters.states | array | 分支约束 | oneOf[2] |  | {"maxItems":5,"minItems":1,"uniqueItems":true} |
| parameters.states[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["draft","sent","to approve","purchase","cancel"]} |
| parameters.partner_id | integer/null | 可选（可能有条件限制） |  | 合作伙伴ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.currency_id | integer/null | 可选（可能有条件限制） |  | 币种ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.user_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.payment_term_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.fiscal_position_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.invoice_statuses | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"oneOf":[{"type":"null"},{"items":{"enum":["no","to invoice","invoiced"]},"maxItems":3,"minItems":1,"type":"array","uniqueItems":true}],"resolved_ref":"#/$defs/nullableInvoiceStatuses"} |
| parameters.invoice_statuses | null | 分支约束 | oneOf[1] |  |  |
| parameters.invoice_statuses | array | 分支约束 | oneOf[2] |  | {"maxItems":3,"minItems":1,"uniqueItems":true} |
| parameters.invoice_statuses[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["no","to invoice","invoiced"]} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/page"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"purchase.order.search"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/page"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/page"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","company","partner","state","date_order","currency","user","invoice_status","amount_untaxed","amount_tax","amount_total","invoice_ids","transfer_ids","line_count","date_approve","partner_ref","origin","receipt_status"],"resolved_ref":"#/$defs/header"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].company | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].company.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].partner | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","sent","to approve","purchase","cancel"]} |
| response.data.items[].date_order | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.items[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].user | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.items[].user | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].user | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].user.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].user.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].payment_term_id | integer/null | 可选（可能有条件限制） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].fiscal_position_id | integer/null | 可选（可能有条件限制） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].invoice_status | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["no","to invoice","invoiced"]} |
| response.data.items[].amount_untaxed | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_tax | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].invoice_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.items[].invoice_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.items[].transfer_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.items[].transfer_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.items[].line_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.items[].date_approve | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/utcDateTime"}],"resolved_ref":"#/$defs/nullableUtcDateTime"} |
| response.data.items[].date_approve | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].date_approve | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.items[].partner_ref | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].origin | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].receipt_status | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["pending","partial","full",null]} |
| response.data.has_more | boolean | 必填（所在对象出现时） | oneOf[2] | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | oneOf[2] | 下一页不透明游标，无后续时可为空 | {"minLength":1} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/page"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/page"} |
| response.data.items | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","company","partner","state","date_order","currency","user","invoice_status","amount_untaxed","amount_tax","amount_total","invoice_ids","transfer_ids","line_count","date_approve","partner_ref","origin","receipt_status"],"resolved_ref":"#/$defs/header"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].company | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].company.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].partner | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","sent","to approve","purchase","cancel"]} |
| response.data.items[].date_order | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.items[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].user | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.items[].user | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].user | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].user.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].user.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].payment_term_id | integer/null | 可选（可能有条件限制） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].fiscal_position_id | integer/null | 可选（可能有条件限制） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].invoice_status | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["no","to invoice","invoiced"]} |
| response.data.items[].amount_untaxed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_tax | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].invoice_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.items[].invoice_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].transfer_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.items[].transfer_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].line_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.items[].date_approve | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/utcDateTime"}],"resolved_ref":"#/$defs/nullableUtcDateTime"} |
| response.data.items[].date_approve | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].date_approve | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.items[].partner_ref | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].origin | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].receipt_status | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["pending","partial","full",null]} |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[1]/then | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[1]/then | 下一页不透明游标，无后续时可为空 | {"minLength":1} |
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
- `execute`：fixed_company_scoped_purchase_order_search
- `verify`：read_only_transaction_acl_cursor_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover closed filters, bound ASC cursors, company and ACL scope, Odoo mapping, schemas, and CLI dispatch. Native optional projections and explicit accounting filters are covered.；引用：tests/unit/test_order_documents.py, tests/unit/test_order_documents_bridge.py, tests/unit/test_order_documents_runtime.py, tests/unit/test_order_documents_schemas.py, tests/unit/test_order_documents_cli.py, tests/unit/test_capability_registry.py, tests/unit/test_order_accounting_reads_contract.py, tests/unit/test_order_accounting_reads_runtime.py, tests/unit/test_order_accounting_reads_cli.py
- `integration`：`implemented`；The guarded shared smoke exercises sales and purchase order reads in both dedicated isolated databases.；引用：tests/integration/test_order_documents_batch_live.py, tests/integration/test_order_accounting_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-purchase-order-update_draft"></a>

## purchase.order.update_draft — 更新草稿采购订单

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user. Replay uses a target-payload recheck without a persistent operation store, so an old request can become effective after an intervening state change.
- 内部domain：`purchase_accounting`；来源模型：account.incoterms, account.payment.term, purchase.order, purchase.order.line, res.company；向导：无。
- 必需模块：account, base, purchase, purchase_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：purchase.group_purchase_user；ACL：purchase.order:read, purchase.order:write, purchase.order.line:read, res.company:read。
- 请求/响应合同：`schemas/v1/purchase.order.update_draft.request.schema.json` / `schemas/v1/purchase.order.update_draft.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run purchase.order.update_draft --request "@request.json" --idempotency-key "purchase.order.update_draft:1:a20e35cba7b0756e3955cbc3f7cbea03" --confirm "purchase.order.update_draft"
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
    "order_id": 1,
    "changes": {
      "partner_ref": "1"
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["order_id","changes"]} |
| parameters.order_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.partner_ref | string/null | 可选（可能有条件限制） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$","resolved_ref":"purchase.order.create.request.schema.json#/$defs/nullable_text"} |
| parameters.changes.date_order | string | 可选（可能有条件限制） |  |  | {"pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$","resolved_ref":"purchase.order.create.request.schema.json#/$defs/datetime"} |
| parameters.changes.payment_term_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"purchase.order.create.request.schema.json#/$defs/nullable_id"} |
| parameters.changes.incoterm_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"purchase.order.create.request.schema.json#/$defs/nullable_id"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"purchase.order.update_draft"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"purchase.order.update_draft"} |
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
- `execute`：fixed_native_draft_purchase_order_write_action
- `verify`：same_transaction_target_header_payload_and_response_schema_validation
- `idempotency`：target_header_payload_recheck_without_operation_store
- `reverse`：repeat_update_with_previous_header_values

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request, draft-only update, exact confirmation, native ACLs, target-payload replay, schemas, and CLI dispatch.；引用：tests/unit/test_order_document_writes.py, tests/unit/test_order_document_writes_runtime.py, tests/unit/test_order_document_write_cli.py, tests/unit/test_order_document_write_schemas.py
- `integration`：`implemented`；The guarded shared live smoke verifies draft updates, replay, and rollback in both dedicated isolated databases.；引用：tests/integration/test_order_document_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-purchase-rfq-pdf-export"></a>

## purchase.rfq.pdf.export — 导出询价单 PDF

- 类型：只读；静态状态：`unconfigured`；handler：`document_purchase_rfq_pdf_export`。
- 状态原因：`runtime_context_required` — The fixed native PDF handler is installed; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`document_exports`；来源模型：purchase.order, res.company, ir.actions.report；向导：无。
- 必需模块：purchase；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：purchase.group_purchase_user；ACL：purchase.order:read, res.company:read, ir.actions.report:read。
- 请求/响应合同：`schemas/v1/purchase.rfq.pdf.export.request.schema.json` / `schemas/v1/purchase.rfq.pdf.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read purchase.rfq.pdf.export --request "@request.json"
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
    "order_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["order_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.order_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"purchase.rfq.pdf.export"} |
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
- `execute`：fixed_native_purchase_rfq_qweb_pdf_action
- `verify`：bound_record_pdf_bytes_hash_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover the fixed action, exact contract, bridge, runtime, CLI routing, registry metadata, and schemas.；引用：tests/unit/test_document_exports.py, tests/unit/test_document_exports_bridge.py, tests/unit/test_document_exports_runtime.py, tests/unit/test_document_export_cli.py, tests/unit/test_document_export_registry.py
- `integration`：`implemented`；The shared read-only live smoke covers the fixed document export batch in both isolated databases.；引用：tests/integration/test_document_export_batch_live.py
- `golden`：`planned`；Golden PDF evidence is pending.；引用：无
- `e2e`：`planned`；End-to-end natural-language routing evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-sale-order-analysis-summary"></a>

## sale.order.analysis.summary — 汇总分析销售订单

- 类型：只读；静态状态：`unconfigured`；handler：`sale_order_analysis_summary`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, modules, and ACLs.
- 内部domain：`sales_accounting`；来源模型：res.company, res.currency, res.partner, res.users, sale.order；向导：无。
- 必需模块：base, sale；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, res.currency:read, res.partner:read, res.users:read, sale.order:read。
- 请求/响应合同：`schemas/v1/sale.order.analysis.summary.request.schema.json` / `schemas/v1/sale.order.analysis.summary.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read sale.order.analysis.summary --request "@request.json"
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
    "date_from": "2026-10-01",
    "date_to": "2026-10-31",
    "group_by": "state"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to","group_by"],"resolved_ref":"#/$defs/parameters"} |
| parameters.date_from | string | 必填（所在对象出现时） |  | 开始日期 | {"format":"date"} |
| parameters.date_to | string | 必填（所在对象出现时） |  | 结束日期 | {"format":"date"} |
| parameters.group_by | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["state","invoice_status","partner","salesperson","currency"]} |
| parameters.states | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"oneOf":[{"type":"null"},{"items":{"enum":["draft","sent","sale","cancel"]},"maxItems":4,"minItems":1,"type":"array","uniqueItems":true}],"resolved_ref":"#/$defs/nullableStates"} |
| parameters.states | null | 分支约束 | oneOf[1] |  |  |
| parameters.states | array | 分支约束 | oneOf[2] |  | {"maxItems":4,"minItems":1,"uniqueItems":true} |
| parameters.states[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["draft","sent","sale","cancel"]} |
| parameters.partner_id | integer/null | 可选（可能有条件限制） |  | 合作伙伴ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.currency_id | integer/null | 可选（可能有条件限制） |  | 币种ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.user_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.payment_term_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.fiscal_position_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.invoice_statuses | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"oneOf":[{"type":"null"},{"items":{"enum":["upselling","invoiced","to invoice","no"]},"maxItems":4,"minItems":1,"type":"array","uniqueItems":true}]} |
| parameters.invoice_statuses | null | 分支约束 | oneOf[1] |  |  |
| parameters.invoice_statuses | array | 分支约束 | oneOf[2] |  | {"maxItems":4,"minItems":1,"uniqueItems":true} |
| parameters.invoice_statuses[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["upselling","invoiced","to invoice","no"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"sale.order.analysis.summary"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["company_id","group_by","date_from","date_to","groups","totals_by_currency"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.group_by | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["state","invoice_status","partner","salesperson","currency"]} |
| response.data.date_from | string | 必填（所在对象出现时） | oneOf[2] | 开始日期 | {"format":"date"} |
| response.data.date_to | string | 必填（所在对象出现时） | oneOf[2] | 结束日期 | {"format":"date"} |
| response.data.groups | array | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.groups[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["group","currency","order_count","amount_untaxed","amount_tax","amount_total"],"resolved_ref":"#/$defs/groupRow"} |
| response.data.groups[].group | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","value"],"resolved_ref":"#/$defs/group"} |
| response.data.groups[].group.id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.groups[].group.value | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.groups[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.groups[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.groups[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.groups[].order_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.groups[].amount_untaxed | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.groups[].amount_tax | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.groups[].amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.totals_by_currency | array | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.totals_by_currency[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["currency","order_count","amount_untaxed","amount_tax","amount_total"],"resolved_ref":"#/$defs/total"} |
| response.data.totals_by_currency[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.totals_by_currency[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.totals_by_currency[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.totals_by_currency[].order_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.totals_by_currency[].amount_untaxed | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.totals_by_currency[].amount_tax | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.totals_by_currency[].amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["company_id","group_by","date_from","date_to","groups","totals_by_currency"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.group_by | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["state","invoice_status","partner","salesperson","currency"]} |
| response.data.date_from | string | 必填（所在对象出现时） | allOf[1]/then | 开始日期 | {"format":"date"} |
| response.data.date_to | string | 必填（所在对象出现时） | allOf[1]/then | 结束日期 | {"format":"date"} |
| response.data.groups | array | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.groups[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["group","currency","order_count","amount_untaxed","amount_tax","amount_total"],"resolved_ref":"#/$defs/groupRow"} |
| response.data.groups[].group | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","value"],"resolved_ref":"#/$defs/group"} |
| response.data.groups[].group.id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.groups[].group.value | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.groups[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.groups[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.groups[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.groups[].order_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.groups[].amount_untaxed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.groups[].amount_tax | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.groups[].amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.totals_by_currency | array | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.totals_by_currency[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["currency","order_count","amount_untaxed","amount_tax","amount_total"],"resolved_ref":"#/$defs/total"} |
| response.data.totals_by_currency[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.totals_by_currency[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.totals_by_currency[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.totals_by_currency[].order_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.totals_by_currency[].amount_untaxed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.totals_by_currency[].amount_tax | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.totals_by_currency[].amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
- `execute`：fixed_company_scoped_sales_order_read_group
- `verify`：read_only_transaction_acl_grouping_currency_totals_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover fixed groupings, per-currency totals, company and ACL scope, schemas, and CLI dispatch. Native optional projections and explicit accounting filters are covered.；引用：tests/unit/test_order_documents.py, tests/unit/test_order_documents_bridge.py, tests/unit/test_order_documents_runtime.py, tests/unit/test_order_documents_schemas.py, tests/unit/test_order_documents_cli.py, tests/unit/test_capability_registry.py, tests/unit/test_order_accounting_reads_contract.py, tests/unit/test_order_accounting_reads_runtime.py, tests/unit/test_order_accounting_reads_cli.py
- `integration`：`implemented`；The guarded shared smoke exercises sales and purchase order reads in both dedicated isolated databases.；引用：tests/integration/test_order_documents_batch_live.py, tests/integration/test_order_accounting_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-sale-order-cancel"></a>

## sale.order.cancel — 取消销售订单

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user. Replay uses a target-state recheck without a persistent operation store, so an old request can become effective after an intervening state change.
- 内部domain：`sales_accounting`；来源模型：res.company, sale.order, sale.order.line；向导：无。
- 必需模块：account, base, sale, sale_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：sales_team.group_sale_salesman；ACL：res.company:read, sale.order:read, sale.order:write, sale.order.line:read。
- 请求/响应合同：`schemas/v1/sale.order.cancel.request.schema.json` / `schemas/v1/sale.order.cancel.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run sale.order.cancel --request "@request.json" --idempotency-key "sale.order.cancel:1" --confirm "sale.order.cancel"
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
    "order_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["order_id"],"resolved_ref":"sale.order.confirm.request.schema.json#/$defs/parameters"} |
| parameters.order_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"sale.order.cancel"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"sale.order.cancel"} |
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
- `execute`：fixed_native_sale_order_action_cancel
- `verify`：same_transaction_cancelled_state_and_response_schema_validation
- `idempotency`：target_cancelled_state_recheck_without_operation_store
- `reverse`：sale.order.reset_to_draft_when_native_state_allows

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover native cancellation preconditions, exact confirmation, native ACLs, target-state replay, schemas, and CLI dispatch.；引用：tests/unit/test_order_document_writes.py, tests/unit/test_order_document_writes_runtime.py, tests/unit/test_order_document_write_cli.py, tests/unit/test_order_document_write_schemas.py
- `integration`：`implemented`；The guarded shared live smoke verifies native cancellation, replay, and rollback in both dedicated isolated databases.；引用：tests/integration/test_order_document_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-sale-order-confirm"></a>

## sale.order.confirm — 确认销售订单

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user. Replay uses a target-state recheck without a persistent operation store, so an old request can become effective after an intervening state change.
- 内部domain：`sales_accounting`；来源模型：res.company, sale.order, sale.order.line；向导：无。
- 必需模块：account, base, sale, sale_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：sales_team.group_sale_salesman；ACL：res.company:read, sale.order:read, sale.order:write, sale.order.line:read。
- 请求/响应合同：`schemas/v1/sale.order.confirm.request.schema.json` / `schemas/v1/sale.order.confirm.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run sale.order.confirm --request "@request.json" --idempotency-key "sale.order.confirm:1" --confirm "sale.order.confirm"
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
    "order_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["order_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.order_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"sale.order.confirm"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"sale.order.confirm"} |
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
- `execute`：fixed_native_sale_order_action_confirm
- `verify`：same_transaction_confirmed_state_and_response_schema_validation
- `idempotency`：target_confirmed_state_recheck_without_operation_store
- `reverse`：sale.order.cancel_when_native_state_allows

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the native confirmation preconditions, exact confirmation, native ACLs, target-state replay, schemas, and CLI dispatch.；引用：tests/unit/test_order_document_writes.py, tests/unit/test_order_document_writes_runtime.py, tests/unit/test_order_document_write_cli.py, tests/unit/test_order_document_write_schemas.py
- `integration`：`implemented`；The guarded shared live smoke verifies native confirmation, replay, and rollback in both dedicated isolated databases.；引用：tests/integration/test_order_document_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-sale-order-create"></a>

## sale.order.create — 创建草稿销售订单

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`odoo_order_marker_not_concurrency_unique` — The fixed handler supports ordinary replay with a deterministic visible marker, but Odoo provides no database-unique operation key, so concurrent exactly-once creation is not proven.
- 内部domain：`sales_accounting`；来源模型：account.payment.term, account.tax, product.pricelist, product.product, res.company, res.partner, sale.order, sale.order.line, uom.uom；向导：无。
- 必需模块：account, base, sale, sale_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：sales_team.group_sale_salesman；ACL：res.company:read, sale.order:read, sale.order:create, sale.order:write, sale.order.line:read, sale.order.line:create, sale.order.line:write。
- 请求/响应合同：`schemas/v1/sale.order.create.request.schema.json` / `schemas/v1/sale.order.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run sale.order.create --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "sale.order.create"
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
    "partner_id": 1,
    "pricelist_id": 1,
    "date_order": "2026-10-03 09:00:00",
    "client_order_ref": "1",
    "validity_date": "2026-10-31",
    "commitment_date": "2026-10-03 09:00:00",
    "payment_term_id": 1,
    "lines": [
      {
        "product_id": 1,
        "name": "Example",
        "quantity": "1",
        "uom_id": 1,
        "price_unit": "1",
        "discount": "1",
        "tax_ids": []
      }
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["partner_id","pricelist_id","date_order","client_order_ref","validity_date","commitment_date","payment_term_id","lines"]} |
| parameters.partner_id | integer | 必填（所在对象出现时） |  | 合作伙伴ID | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.pricelist_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.date_order | string | 必填（所在对象出现时） |  |  | {"pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$","resolved_ref":"#/$defs/datetime"} |
| parameters.client_order_ref | string/null | 必填（所在对象出现时） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$","resolved_ref":"#/$defs/nullable_text"} |
| parameters.validity_date | string/null | 必填（所在对象出现时） |  |  | {"format":"date"} |
| parameters.commitment_date | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/datetime"}]} |
| parameters.commitment_date | null | 分支约束 | oneOf[1] |  |  |
| parameters.commitment_date | string | 分支约束 | oneOf[2] |  | {"pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$","resolved_ref":"#/$defs/datetime"} |
| parameters.payment_term_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullable_id"} |
| parameters.lines | array | 必填（所在对象出现时） |  | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":200,"minItems":1} |
| parameters.lines[] | object | 每个数组元素 |  | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["product_id","name","quantity","uom_id","price_unit","discount","tax_ids"],"resolved_ref":"#/$defs/line"} |
| parameters.lines[].product_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.lines[].name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":500,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$"} |
| parameters.lines[].quantity | string | 必填（所在对象出现时） |  | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/positive_decimal"} |
| parameters.lines[].uom_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.lines[].price_unit | string | 必填（所在对象出现时） |  | 单价；币种及符号依单据和合同 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegative_decimal"} |
| parameters.lines[].discount | string | 必填（所在对象出现时） |  | 折扣百分比 | {"maxLength":256,"pattern":"^(?:0&#124;100&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]*[1-9])?)$(?![\\s\\S])","resolved_ref":"#/$defs/percentage_decimal"} |
| parameters.lines[].tax_ids | array | 必填（所在对象出现时） |  | 应用税ID数组 | {"uniqueItems":true} |
| parameters.lines[].tax_ids[] | integer | 每个数组元素 |  | 应用税ID数组 | {"minimum":1,"resolved_ref":"#/$defs/id"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"sale.order.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"sale.order.create"} |
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
- `execute`：fixed_native_sale_order_create_as_configured_business_user
- `verify`：same_transaction_company_order_lines_and_response_schema_validation
- `idempotency`：deterministic_visible_marker_and_ordinary_result_replay_without_database_uniqueness
- `reverse`：cancel_or_delete_the_draft_sales_order

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request, exact confirmation, fixed ORM path, native ACLs, ordinary replay, result validation, schemas, and CLI dispatch.；引用：tests/unit/test_order_document_writes.py, tests/unit/test_order_document_writes_runtime.py, tests/unit/test_order_document_write_cli.py, tests/unit/test_order_document_write_schemas.py
- `integration`：`implemented`；The guarded shared live smoke verifies creation, replay, and rollback in both dedicated isolated databases.；引用：tests/integration/test_order_document_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-sale-order-get"></a>

## sale.order.get — 获取销售订单详情

- 类型：只读；静态状态：`unconfigured`；handler：`sale_order_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, modules, and ACLs.
- 内部domain：`sales_accounting`；来源模型：account.move, account.move.line, account.tax, crm.team, product.product, res.company, res.currency, res.partner, res.users, sale.order, sale.order.line, stock.location, stock.move, stock.picking, uom.uom；向导：无。
- 必需模块：account, base, sale, sale_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.move:read, account.move.line:read, account.tax:read, crm.team:read, product.product:read, res.company:read, res.currency:read, res.partner:read, res.users:read, sale.order:read, sale.order.line:read, stock.location:read, stock.move:read, stock.picking:read, uom.uom:read。
- 请求/响应合同：`schemas/v1/sale.order.get.request.schema.json` / `schemas/v1/sale.order.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read sale.order.get --request "@request.json"
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
    "order_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["order_id"]} |
| parameters.order_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"sale.order.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","company","partner","state","date_order","currency","user","invoice_status","amount_untaxed","amount_tax","amount_total","invoice_ids","transfer_ids","line_count","validity_date","client_order_ref","team","delivery_status","lines","invoices","transfers"],"resolved_ref":"#/$defs/data"} |
| response.data.payment_term_id | integer/null | 可选（可能有条件限制） | oneOf[2] |  | {"minimum":1} |
| response.data.fiscal_position_id | integer/null | 可选（可能有条件限制） | oneOf[2] |  | {"minimum":1} |
| response.data.amount_invoiced | 组合/开放结构 | 可选（可能有条件限制） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.amount_invoiced | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.amount_invoiced | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_to_invoice | 组合/开放结构 | 可选（可能有条件限制） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.amount_to_invoice | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.amount_to_invoice | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.company | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.company.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.partner | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","sent","sale","cancel"]} |
| response.data.date_order | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.user | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.user | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.user | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.user.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.user.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.invoice_status | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["upselling","invoiced","to invoice","no"]} |
| response.data.amount_untaxed | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_tax | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.invoice_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.invoice_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.transfer_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.transfer_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.line_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.validity_date | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| response.data.validity_date | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.validity_date | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.client_order_ref | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.team | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.team | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.team | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.team.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.team.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.delivery_status | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["pending","started","partial","full",null]} |
| response.data.lines | array | 必填（所在对象出现时） | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 |  |
| response.data.lines[] | object | 每个数组元素 | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","order","company","partner","state","date_order","sequence","display_type","description","product","uom","ordered_quantity","invoiced_quantity","to_invoice_quantity","unit_price","discount_percent","amount_untaxed","amount_tax","amount_total","currency","taxes","invoice_line_ids","stock_move_ids","delivered_quantity","to_deliver_quantity"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].is_downpayment | boolean | 可选（可能有条件限制） | oneOf[2] |  |  |
| response.data.lines[].invoice_policy | 未限定 | 可选（可能有条件限制） | oneOf[2] | Native template-shared invoicing policy, not a company-dependent setting. | {"enum":["order","delivery",null]} |
| response.data.lines[].invoice_status | 未限定 | 可选（可能有条件限制） | oneOf[2] |  | {"enum":["upselling","invoiced","to invoice","no",null]} |
| response.data.lines[].posted_invoiced_quantity | 组合/开放结构 | 可选（可能有条件限制） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.lines[].posted_invoiced_quantity | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].posted_invoiced_quantity | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].amount_invoiced | 组合/开放结构 | 可选（可能有条件限制） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.lines[].amount_invoiced | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].amount_invoiced | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].amount_to_invoice | 组合/开放结构 | 可选（可能有条件限制） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.lines[].amount_to_invoice | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].amount_to_invoice | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].order | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].order.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].order.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].company | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].company.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].company.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].partner | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].partner.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].partner.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","sent","sale","cancel"]} |
| response.data.lines[].date_order | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.lines[].sequence | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.lines[].display_type | string/null | 必填（所在对象出现时） | oneOf[2] | 业务行/章节/备注类型 | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.lines[].description | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.lines[].product | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.lines[].product | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].product | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].product.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].product.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].uom | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.lines[].uom | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].uom | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].uom.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].uom.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].ordered_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].invoiced_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].to_invoice_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].delivered_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].to_deliver_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].unit_price | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].discount_percent | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].amount_untaxed | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].amount_tax | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.lines[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.lines[].taxes | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.lines[].taxes[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].taxes[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].taxes[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].invoice_line_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.lines[].invoice_line_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].stock_move_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.lines[].stock_move_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.invoices | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.invoices[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","payment_state","amount_total","currency"],"resolved_ref":"#/$defs/invoice"} |
| response.data.invoices[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.invoices[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.invoices[].move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["out_invoice","out_refund","out_receipt"]} |
| response.data.invoices[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.invoices[].payment_state | string/null | 必填（所在对象出现时） | oneOf[2] | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy",null]} |
| response.data.invoices[].amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.invoices[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.invoices[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.invoices[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.transfers | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.transfers[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","state","source_location","destination_location"],"resolved_ref":"#/$defs/transfer"} |
| response.data.transfers[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.transfers[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.transfers[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","waiting","confirmed","assigned","done","cancel"]} |
| response.data.transfers[].source_location | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.transfers[].source_location.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.transfers[].source_location.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.transfers[].destination_location | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.transfers[].destination_location.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.transfers[].destination_location.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","company","partner","state","date_order","currency","user","invoice_status","amount_untaxed","amount_tax","amount_total","invoice_ids","transfer_ids","line_count","validity_date","client_order_ref","team","delivery_status","lines","invoices","transfers"],"resolved_ref":"#/$defs/data"} |
| response.data.payment_term_id | integer/null | 可选（可能有条件限制） | allOf[1]/then |  | {"minimum":1} |
| response.data.fiscal_position_id | integer/null | 可选（可能有条件限制） | allOf[1]/then |  | {"minimum":1} |
| response.data.amount_invoiced | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.amount_invoiced | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.amount_invoiced | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_to_invoice | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.amount_to_invoice | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.amount_to_invoice | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.company | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.company.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.partner | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","sent","sale","cancel"]} |
| response.data.date_order | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.user | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.user | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.user | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.user.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.user.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.invoice_status | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["upselling","invoiced","to invoice","no"]} |
| response.data.amount_untaxed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_tax | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.invoice_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.invoice_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.transfer_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.transfer_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.line_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.validity_date | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| response.data.validity_date | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.validity_date | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date"} |
| response.data.client_order_ref | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.team | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.team | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.team | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.team.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.team.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.delivery_status | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["pending","started","partial","full",null]} |
| response.data.lines | array | 必填（所在对象出现时） | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| response.data.lines[] | object | 每个数组元素 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","order","company","partner","state","date_order","sequence","display_type","description","product","uom","ordered_quantity","invoiced_quantity","to_invoice_quantity","unit_price","discount_percent","amount_untaxed","amount_tax","amount_total","currency","taxes","invoice_line_ids","stock_move_ids","delivered_quantity","to_deliver_quantity"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].is_downpayment | boolean | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response.data.lines[].invoice_policy | 未限定 | 可选（可能有条件限制） | allOf[1]/then | Native template-shared invoicing policy, not a company-dependent setting. | {"enum":["order","delivery",null]} |
| response.data.lines[].invoice_status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"enum":["upselling","invoiced","to invoice","no",null]} |
| response.data.lines[].posted_invoiced_quantity | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.lines[].posted_invoiced_quantity | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].posted_invoiced_quantity | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].amount_invoiced | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.lines[].amount_invoiced | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].amount_invoiced | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].amount_to_invoice | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.lines[].amount_to_invoice | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].amount_to_invoice | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].order | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].order.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].order.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.lines[].company | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].company.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].company.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.lines[].partner | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].partner.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].partner.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.lines[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","sent","sale","cancel"]} |
| response.data.lines[].date_order | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.lines[].sequence | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.lines[].display_type | string/null | 必填（所在对象出现时） | allOf[1]/then | 业务行/章节/备注类型 | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.lines[].description | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.lines[].product | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.lines[].product | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].product | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].product.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].product.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].uom | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.lines[].uom | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].uom | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].uom.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].uom.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].ordered_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].invoiced_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].to_invoice_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].delivered_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].to_deliver_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].unit_price | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].discount_percent | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].amount_untaxed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].amount_tax | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.lines[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.lines[].taxes | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.lines[].taxes[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.lines[].taxes[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].taxes[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.lines[].invoice_line_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.lines[].invoice_line_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].stock_move_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.lines[].stock_move_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.invoices | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.invoices[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","payment_state","amount_total","currency"],"resolved_ref":"#/$defs/invoice"} |
| response.data.invoices[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.invoices[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.invoices[].move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["out_invoice","out_refund","out_receipt"]} |
| response.data.invoices[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.invoices[].payment_state | string/null | 必填（所在对象出现时） | allOf[1]/then | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy",null]} |
| response.data.invoices[].amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.invoices[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.invoices[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.invoices[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.transfers | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.transfers[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","state","source_location","destination_location"],"resolved_ref":"#/$defs/transfer"} |
| response.data.transfers[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.transfers[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.transfers[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","waiting","confirmed","assigned","done","cancel"]} |
| response.data.transfers[].source_location | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.transfers[].source_location.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.transfers[].source_location.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.transfers[].destination_location | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.transfers[].destination_location.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.transfers[].destination_location.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
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
- `execute`：fixed_company_scoped_sales_order_get
- `verify`：read_only_transaction_acl_identity_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover exact identity, lines and linked documents, company and ACL scope, schemas, and CLI dispatch. Native optional projections and explicit accounting filters are covered.；引用：tests/unit/test_order_documents.py, tests/unit/test_order_documents_bridge.py, tests/unit/test_order_documents_runtime.py, tests/unit/test_order_documents_schemas.py, tests/unit/test_order_documents_cli.py, tests/unit/test_capability_registry.py, tests/unit/test_order_accounting_reads_contract.py, tests/unit/test_order_accounting_reads_runtime.py, tests/unit/test_order_accounting_reads_cli.py
- `integration`：`implemented`；The guarded shared smoke exercises sales and purchase order reads in both dedicated isolated databases.；引用：tests/integration/test_order_documents_batch_live.py, tests/integration/test_order_accounting_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-sale-order-line-get"></a>

## sale.order.line.get — 读取销售订单行

- 类型：只读；静态状态：`unconfigured`；handler：`sale_order_line_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, modules, and ACLs.
- 内部domain：`sales_accounting`；来源模型：account.move, account.move.line, account.tax, crm.team, product.product, res.company, res.currency, res.partner, res.users, sale.order, sale.order.line, stock.move, uom.uom；向导：无。
- 必需模块：account, base, sale, sale_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.move:read, account.move.line:read, account.tax:read, crm.team:read, product.product:read, res.company:read, res.currency:read, res.partner:read, res.users:read, sale.order:read, sale.order.line:read, stock.move:read, uom.uom:read。
- 请求/响应合同：`schemas/v1/sale.order.line.get.request.schema.json` / `schemas/v1/sale.order.line.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read sale.order.line.get --request "@request.json"
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
    "line_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  |  |
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["line_id"]} |
| parameters.line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"sale.order.line.get"},"data":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"sale.order.line.get"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","order","company","partner","state","date_order","sequence","display_type","description","product","uom","ordered_quantity","invoiced_quantity","to_invoice_quantity","unit_price","discount_percent","amount_untaxed","amount_tax","amount_total","currency","taxes","invoice_line_ids","stock_move_ids","delivered_quantity","to_deliver_quantity","invoices"],"resolved_ref":"#/$defs/data"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1,"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/id"} |
| response.data.order | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/order"} |
| response.data.order.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.order.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.company | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/company"} |
| response.data.company.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.company.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.partner | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/partner"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"enum":["draft","sent","sale","cancel"],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/state"} |
| response.data.date_order | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/date_order"} |
| response.data.sequence | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":0,"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/sequence"} |
| response.data.display_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 业务行/章节/备注类型 | {"minLength":1,"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/display_type"} |
| response.data.description | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1,"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/description"} |
| response.data.product | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/product"} |
| response.data.product | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.product | object | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.product.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.product.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.uom | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/uom"} |
| response.data.uom | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.uom | object | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.uom.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.uom.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.ordered_quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/ordered_quantity"} |
| response.data.invoiced_quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/invoiced_quantity"} |
| response.data.to_invoice_quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/to_invoice_quantity"} |
| response.data.unit_price | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/unit_price"} |
| response.data.discount_percent | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/discount_percent"} |
| response.data.amount_untaxed | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/amount_untaxed"} |
| response.data.amount_tax | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/amount_tax"} |
| response.data.amount_total | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/amount_total"} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.taxes | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/taxes","uniqueItems":true} |
| response.data.taxes[] | object | 每个数组元素 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.taxes[].id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.taxes[].name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.invoice_line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/invoice_line_ids","uniqueItems":true} |
| response.data.invoice_line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.stock_move_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/stock_move_ids","uniqueItems":true} |
| response.data.stock_move_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.delivered_quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/delivered_quantity"} |
| response.data.to_deliver_quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/to_deliver_quantity"} |
| response.data.is_downpayment | boolean | 可选（可能有条件限制） | allOf[2]/oneOf[2] |  | {"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/is_downpayment"} |
| response.data.invoice_policy | 未限定 | 可选（可能有条件限制） | allOf[2]/oneOf[2] | Native template-shared invoicing policy, not a company-dependent setting. | {"enum":["order","delivery",null],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/invoice_policy"} |
| response.data.invoice_status | 未限定 | 可选（可能有条件限制） | allOf[2]/oneOf[2] |  | {"enum":["upselling","invoiced","to invoice","no",null],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/invoice_status"} |
| response.data.posted_invoiced_quantity | 组合/开放结构 | 可选（可能有条件限制） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/posted_invoiced_quantity"} |
| response.data.posted_invoiced_quantity | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.posted_invoiced_quantity | string | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_invoiced | 组合/开放结构 | 可选（可能有条件限制） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/amount_invoiced"} |
| response.data.amount_invoiced | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.amount_invoiced | string | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_to_invoice | 组合/开放结构 | 可选（可能有条件限制） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/amount_to_invoice"} |
| response.data.amount_to_invoice | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.amount_to_invoice | string | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.invoices | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.invoices[] | object | 每个数组元素 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","payment_state","amount_total","currency"],"resolved_ref":"sale.order.get.response.schema.json#/$defs/invoice"} |
| response.data.invoices[].id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.invoices[].name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.invoices[].move_type | 未限定 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"enum":["out_invoice","out_refund","out_receipt"]} |
| response.data.invoices[].state | 未限定 | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.invoices[].payment_state | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy",null]} |
| response.data.invoices[].amount_total | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.invoices[].currency | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.invoices[].currency.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.invoices[].currency.code | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["id","order","company","partner","state","date_order","sequence","display_type","description","product","uom","ordered_quantity","invoiced_quantity","to_invoice_quantity","unit_price","discount_percent","amount_untaxed","amount_tax","amount_total","currency","taxes","invoice_line_ids","stock_move_ids","delivered_quantity","to_deliver_quantity","invoices"],"resolved_ref":"#/$defs/data"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1,"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/id"} |
| response.data.order | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/order"} |
| response.data.order.id | integer | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.order.name | string | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.company | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/company"} |
| response.data.company.id | integer | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.company.name | string | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.partner | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/partner"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"enum":["draft","sent","sale","cancel"],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/state"} |
| response.data.date_order | string | 必填（所在对象出现时） | allOf[3]/then |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/date_order"} |
| response.data.sequence | integer | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":0,"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/sequence"} |
| response.data.display_type | string/null | 必填（所在对象出现时） | allOf[3]/then | 业务行/章节/备注类型 | {"minLength":1,"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/display_type"} |
| response.data.description | string | 必填（所在对象出现时） | allOf[3]/then |  | {"minLength":1,"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/description"} |
| response.data.product | 组合/开放结构 | 必填（所在对象出现时） | allOf[3]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/product"} |
| response.data.product | null | 分支约束 | allOf[3]/then/oneOf[1] |  |  |
| response.data.product | object | 分支约束 | allOf[3]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.product.id | integer | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] |  | {"minimum":1} |
| response.data.product.name | string | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.uom | 组合/开放结构 | 必填（所在对象出现时） | allOf[3]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/uom"} |
| response.data.uom | null | 分支约束 | allOf[3]/then/oneOf[1] |  |  |
| response.data.uom | object | 分支约束 | allOf[3]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.uom.id | integer | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] |  | {"minimum":1} |
| response.data.uom.name | string | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.ordered_quantity | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/ordered_quantity"} |
| response.data.invoiced_quantity | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/invoiced_quantity"} |
| response.data.to_invoice_quantity | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/to_invoice_quantity"} |
| response.data.unit_price | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/unit_price"} |
| response.data.discount_percent | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/discount_percent"} |
| response.data.amount_untaxed | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/amount_untaxed"} |
| response.data.amount_tax | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/amount_tax"} |
| response.data.amount_total | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/amount_total"} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[3]/then |  | {"maxLength":3,"minLength":1} |
| response.data.taxes | array | 必填（所在对象出现时） | allOf[3]/then |  | {"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/taxes","uniqueItems":true} |
| response.data.taxes[] | object | 每个数组元素 | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.taxes[].id | integer | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.taxes[].name | string | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.invoice_line_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/invoice_line_ids","uniqueItems":true} |
| response.data.invoice_line_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.stock_move_ids | array | 必填（所在对象出现时） | allOf[3]/then |  | {"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/stock_move_ids","uniqueItems":true} |
| response.data.stock_move_ids[] | integer | 每个数组元素 | allOf[3]/then |  | {"minimum":1} |
| response.data.delivered_quantity | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/delivered_quantity"} |
| response.data.to_deliver_quantity | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/to_deliver_quantity"} |
| response.data.is_downpayment | boolean | 可选（可能有条件限制） | allOf[3]/then |  | {"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/is_downpayment"} |
| response.data.invoice_policy | 未限定 | 可选（可能有条件限制） | allOf[3]/then | Native template-shared invoicing policy, not a company-dependent setting. | {"enum":["order","delivery",null],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/invoice_policy"} |
| response.data.invoice_status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"enum":["upselling","invoiced","to invoice","no",null],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/invoice_status"} |
| response.data.posted_invoiced_quantity | 组合/开放结构 | 可选（可能有条件限制） | allOf[3]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/posted_invoiced_quantity"} |
| response.data.posted_invoiced_quantity | null | 分支约束 | allOf[3]/then/oneOf[1] |  |  |
| response.data.posted_invoiced_quantity | string | 分支约束 | allOf[3]/then/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_invoiced | 组合/开放结构 | 可选（可能有条件限制） | allOf[3]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/amount_invoiced"} |
| response.data.amount_invoiced | null | 分支约束 | allOf[3]/then/oneOf[1] |  |  |
| response.data.amount_invoiced | string | 分支约束 | allOf[3]/then/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_to_invoice | 组合/开放结构 | 可选（可能有条件限制） | allOf[3]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}],"resolved_ref":"sale.order.line.search.response.schema.json#/$defs/line/properties/amount_to_invoice"} |
| response.data.amount_to_invoice | null | 分支约束 | allOf[3]/then/oneOf[1] |  |  |
| response.data.amount_to_invoice | string | 分支约束 | allOf[3]/then/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.invoices | array | 必填（所在对象出现时） | allOf[3]/then |  | {"uniqueItems":true} |
| response.data.invoices[] | object | 每个数组元素 | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","payment_state","amount_total","currency"],"resolved_ref":"sale.order.get.response.schema.json#/$defs/invoice"} |
| response.data.invoices[].id | integer | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.invoices[].name | string | 必填（所在对象出现时） | allOf[3]/then | 名称/行说明 | {"minLength":1} |
| response.data.invoices[].move_type | 未限定 | 必填（所在对象出现时） | allOf[3]/then |  | {"enum":["out_invoice","out_refund","out_receipt"]} |
| response.data.invoices[].state | 未限定 | 必填（所在对象出现时） | allOf[3]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.invoices[].payment_state | string/null | 必填（所在对象出现时） | allOf[3]/then | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy",null]} |
| response.data.invoices[].amount_total | string | 必填（所在对象出现时） | allOf[3]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.invoices[].currency | object | 必填（所在对象出现时） | allOf[3]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.invoices[].currency.id | integer | 必填（所在对象出现时） | allOf[3]/then |  | {"minimum":1} |
| response.data.invoices[].currency.code | string | 必填（所在对象出现时） | allOf[3]/then |  | {"maxLength":3,"minLength":1} |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_company_scoped_order_line_get_with_visible_invoice_graph
- `verify`：ordinary_user_acl_exact_line_identity_native_projection_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Fixed exact-line contract, optional native projections, visible invoice graph, ACL and CLI dispatch.；引用：tests/unit/test_order_accounting_reads_contract.py, tests/unit/test_order_accounting_reads_runtime.py, tests/unit/test_order_accounting_reads_cli.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；Shared native order accounting read smoke passed; full rollback.；引用：tests/integration/test_order_accounting_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-sale-order-line-search"></a>

## sale.order.line.search — 搜索销售订单行

- 类型：只读；静态状态：`unconfigured`；handler：`sale_order_line_search`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, modules, and ACLs.
- 内部domain：`sales_accounting`；来源模型：account.move.line, account.tax, crm.team, product.product, res.company, res.currency, res.partner, res.users, sale.order, sale.order.line, stock.move, uom.uom；向导：无。
- 必需模块：account, base, sale, sale_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.move.line:read, account.tax:read, crm.team:read, product.product:read, res.company:read, res.currency:read, res.partner:read, res.users:read, sale.order:read, sale.order.line:read, stock.move:read, uom.uom:read。
- 请求/响应合同：`schemas/v1/sale.order.line.search.request.schema.json` / `schemas/v1/sale.order.line.search.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read sale.order.line.search --request "@request.json"
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
| parameters | object | 必填 |  |  | {"additionalProperties":false,"not":{"properties":{"negative_to_invoice_only":{"const":true},"to_invoice_only":{"const":true}},"required":["to_invoice_only","negative_to_invoice_only"]},"resolved_ref":"#/$defs/parameters"} |
| parameters.order_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.date_from | 组合/开放结构 | 可选（可能有条件限制） |  | 开始日期 | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| parameters.date_from | null | 分支约束 | oneOf[1] | 开始日期 |  |
| parameters.date_from | string | 分支约束 | oneOf[2] | 开始日期 | {"format":"date"} |
| parameters.date_to | 组合/开放结构 | 可选（可能有条件限制） |  | 结束日期 | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| parameters.date_to | null | 分支约束 | oneOf[1] | 结束日期 |  |
| parameters.date_to | string | 分支约束 | oneOf[2] | 结束日期 | {"format":"date"} |
| parameters.partner_id | integer/null | 可选（可能有条件限制） |  | 合作伙伴ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.product_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.states | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"oneOf":[{"type":"null"},{"items":{"enum":["draft","sent","sale","cancel"]},"maxItems":4,"minItems":1,"type":"array","uniqueItems":true}],"resolved_ref":"#/$defs/nullableStates"} |
| parameters.states | null | 分支约束 | oneOf[1] |  |  |
| parameters.states | array | 分支约束 | oneOf[2] |  | {"maxItems":4,"minItems":1,"uniqueItems":true} |
| parameters.states[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["draft","sent","sale","cancel"]} |
| parameters.to_deliver_only | boolean | 可选（可能有条件限制） |  |  | {"default":false} |
| parameters.to_invoice_only | boolean | 可选（可能有条件限制） |  |  | {"default":false} |
| parameters.is_downpayment | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.negative_to_invoice_only | boolean | 可选（可能有条件限制） |  | Select negative native qty_to_invoice; includes down-payment deductions and does not guarantee a refund. |  |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/page"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"sale.order.line.search"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/page"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/page"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","order","company","partner","state","date_order","sequence","display_type","description","product","uom","ordered_quantity","invoiced_quantity","to_invoice_quantity","unit_price","discount_percent","amount_untaxed","amount_tax","amount_total","currency","taxes","invoice_line_ids","stock_move_ids","delivered_quantity","to_deliver_quantity"],"resolved_ref":"#/$defs/line"} |
| response.data.items[].is_downpayment | boolean | 可选（可能有条件限制） | oneOf[2] |  |  |
| response.data.items[].invoice_policy | 未限定 | 可选（可能有条件限制） | oneOf[2] | Native template-shared invoicing policy, not a company-dependent setting. | {"enum":["order","delivery",null]} |
| response.data.items[].invoice_status | 未限定 | 可选（可能有条件限制） | oneOf[2] |  | {"enum":["upselling","invoiced","to invoice","no",null]} |
| response.data.items[].posted_invoiced_quantity | 组合/开放结构 | 可选（可能有条件限制） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.items[].posted_invoiced_quantity | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].posted_invoiced_quantity | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_invoiced | 组合/开放结构 | 可选（可能有条件限制） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.items[].amount_invoiced | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].amount_invoiced | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_to_invoice | 组合/开放结构 | 可选（可能有条件限制） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.items[].amount_to_invoice | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].amount_to_invoice | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].order | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].order.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].order.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].company | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].company.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].partner | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","sent","sale","cancel"]} |
| response.data.items[].date_order | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.items[].sequence | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.items[].display_type | string/null | 必填（所在对象出现时） | oneOf[2] | 业务行/章节/备注类型 | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].description | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].product | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.items[].product | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].product | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].product.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].product.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].uom | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.items[].uom | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].uom | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].uom.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].uom.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].ordered_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].invoiced_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].to_invoice_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].delivered_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].to_deliver_quantity | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].unit_price | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].discount_percent | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_untaxed | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_tax | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].taxes | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.items[].taxes[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].taxes[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].taxes[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].invoice_line_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.items[].invoice_line_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.items[].stock_move_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.items[].stock_move_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.has_more | boolean | 必填（所在对象出现时） | oneOf[2] | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | oneOf[2] | 下一页不透明游标，无后续时可为空 | {"minLength":1} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/page"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/page"} |
| response.data.items | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","order","company","partner","state","date_order","sequence","display_type","description","product","uom","ordered_quantity","invoiced_quantity","to_invoice_quantity","unit_price","discount_percent","amount_untaxed","amount_tax","amount_total","currency","taxes","invoice_line_ids","stock_move_ids","delivered_quantity","to_deliver_quantity"],"resolved_ref":"#/$defs/line"} |
| response.data.items[].is_downpayment | boolean | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response.data.items[].invoice_policy | 未限定 | 可选（可能有条件限制） | allOf[1]/then | Native template-shared invoicing policy, not a company-dependent setting. | {"enum":["order","delivery",null]} |
| response.data.items[].invoice_status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"enum":["upselling","invoiced","to invoice","no",null]} |
| response.data.items[].posted_invoiced_quantity | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.items[].posted_invoiced_quantity | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].posted_invoiced_quantity | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_invoiced | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.items[].amount_invoiced | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].amount_invoiced | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_to_invoice | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.items[].amount_to_invoice | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].amount_to_invoice | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].order | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].order.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].order.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].company | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].company.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].partner | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","sent","sale","cancel"]} |
| response.data.items[].date_order | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.items[].sequence | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.items[].display_type | string/null | 必填（所在对象出现时） | allOf[1]/then | 业务行/章节/备注类型 | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].description | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].product | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.items[].product | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].product | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].product.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].product.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].uom | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.items[].uom | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].uom | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].uom.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].uom.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].ordered_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].invoiced_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].to_invoice_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].delivered_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].to_deliver_quantity | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].unit_price | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].discount_percent | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_untaxed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_tax | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].taxes | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.items[].taxes[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].taxes[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].taxes[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].invoice_line_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.items[].invoice_line_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].stock_move_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.items[].stock_move_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[1]/then | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[1]/then | 下一页不透明游标，无后续时可为空 | {"minLength":1} |
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
- `execute`：fixed_company_scoped_sales_order_line_search
- `verify`：read_only_transaction_acl_cursor_pending_quantity_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover line filters, non-negative pending quantities, bound ASC cursors, company and ACL scope, schemas, and CLI dispatch. Native optional projections and explicit accounting filters are covered.；引用：tests/unit/test_order_documents.py, tests/unit/test_order_documents_bridge.py, tests/unit/test_order_documents_runtime.py, tests/unit/test_order_documents_schemas.py, tests/unit/test_order_documents_cli.py, tests/unit/test_capability_registry.py, tests/unit/test_order_accounting_reads_contract.py, tests/unit/test_order_accounting_reads_runtime.py, tests/unit/test_order_accounting_reads_cli.py
- `integration`：`implemented`；The guarded shared smoke exercises sales and purchase order reads in both dedicated isolated databases.；引用：tests/integration/test_order_documents_batch_live.py, tests/integration/test_order_accounting_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-sale-order-lines-replace"></a>

## sale.order.lines.replace — 替换草稿销售订单行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user. Replay uses a target-payload recheck without a persistent operation store, so an old request can become effective after an intervening state change.
- 内部domain：`sales_accounting`；来源模型：account.tax, product.product, res.company, sale.order, sale.order.line, uom.uom；向导：无。
- 必需模块：account, base, sale, sale_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：sales_team.group_sale_salesman；ACL：res.company:read, sale.order:read, sale.order:write, sale.order.line:read, sale.order.line:create, sale.order.line:write, sale.order.line:unlink。
- 请求/响应合同：`schemas/v1/sale.order.lines.replace.request.schema.json` / `schemas/v1/sale.order.lines.replace.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run sale.order.lines.replace --request "@request.json" --idempotency-key "sale.order.lines.replace:1:5212c25cb1892fcba70b4013a418fa3a" --confirm "sale.order.lines.replace"
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
    "order_id": 1,
    "lines": [
      {
        "product_id": 1,
        "name": "Example",
        "quantity": "1",
        "uom_id": 1,
        "price_unit": "1",
        "discount": "1",
        "tax_ids": []
      }
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["order_id","lines"]} |
| parameters.order_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.lines | array | 必填（所在对象出现时） |  | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":200,"minItems":1} |
| parameters.lines[] | object | 每个数组元素 |  | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["product_id","name","quantity","uom_id","price_unit","discount","tax_ids"],"resolved_ref":"sale.order.create.request.schema.json#/$defs/line"} |
| parameters.lines[].product_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.lines[].name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":500,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$"} |
| parameters.lines[].quantity | string | 必填（所在对象出现时） |  | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/positive_decimal"} |
| parameters.lines[].uom_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.lines[].price_unit | string | 必填（所在对象出现时） |  | 单价；币种及符号依单据和合同 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegative_decimal"} |
| parameters.lines[].discount | string | 必填（所在对象出现时） |  | 折扣百分比 | {"maxLength":256,"pattern":"^(?:0&#124;100&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]*[1-9])?)$(?![\\s\\S])","resolved_ref":"#/$defs/percentage_decimal"} |
| parameters.lines[].tax_ids | array | 必填（所在对象出现时） |  | 应用税ID数组 | {"uniqueItems":true} |
| parameters.lines[].tax_ids[] | integer | 每个数组元素 |  | 应用税ID数组 | {"minimum":1,"resolved_ref":"#/$defs/id"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"sale.order.lines.replace"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"sale.order.lines.replace"} |
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
- `execute`：fixed_native_draft_sale_order_line_replacement
- `verify`：same_transaction_exact_order_line_payload_and_response_schema_validation
- `idempotency`：target_line_payload_recheck_without_operation_store
- `reverse`：replace_with_the_previous_order_lines

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed line contract, draft-only replacement, exact confirmation, native ACLs, target-payload replay, schemas, and CLI dispatch.；引用：tests/unit/test_order_document_writes.py, tests/unit/test_order_document_writes_runtime.py, tests/unit/test_order_document_write_cli.py, tests/unit/test_order_document_write_schemas.py
- `integration`：`implemented`；The guarded shared live smoke verifies line replacement, replay, and rollback in both dedicated isolated databases.；引用：tests/integration/test_order_document_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-sale-order-pdf-export"></a>

## sale.order.pdf.export — 导出销售订单 PDF

- 类型：只读；静态状态：`unconfigured`；handler：`document_sale_order_pdf_export`。
- 状态原因：`runtime_context_required` — The fixed native PDF handler is installed; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`document_exports`；来源模型：sale.order, res.company, ir.actions.report；向导：无。
- 必需模块：sale；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：sales_team.group_sale_salesman；ACL：sale.order:read, res.company:read, ir.actions.report:read。
- 请求/响应合同：`schemas/v1/sale.order.pdf.export.request.schema.json` / `schemas/v1/sale.order.pdf.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read sale.order.pdf.export --request "@request.json"
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
    "order_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["order_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.order_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"sale.order.pdf.export"} |
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
- `execute`：fixed_native_sale_order_qweb_pdf_action
- `verify`：bound_record_pdf_bytes_hash_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover the fixed action, exact contract, bridge, runtime, CLI routing, registry metadata, and schemas.；引用：tests/unit/test_document_exports.py, tests/unit/test_document_exports_bridge.py, tests/unit/test_document_exports_runtime.py, tests/unit/test_document_export_cli.py, tests/unit/test_document_export_registry.py
- `integration`：`implemented`；The shared read-only live smoke covers the fixed document export batch in both isolated databases.；引用：tests/integration/test_document_export_batch_live.py
- `golden`：`planned`；Golden PDF evidence is pending.；引用：无
- `e2e`：`planned`；End-to-end natural-language routing evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-sale-order-reset_to_draft"></a>

## sale.order.reset_to_draft — 将销售订单重置为草稿

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user. Replay uses a target-state recheck without a persistent operation store, so an old request can become effective after an intervening state change.
- 内部domain：`sales_accounting`；来源模型：res.company, sale.order, sale.order.line；向导：无。
- 必需模块：account, base, sale, sale_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：sales_team.group_sale_salesman；ACL：res.company:read, sale.order:read, sale.order:write, sale.order.line:read。
- 请求/响应合同：`schemas/v1/sale.order.reset_to_draft.request.schema.json` / `schemas/v1/sale.order.reset_to_draft.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run sale.order.reset_to_draft --request "@request.json" --idempotency-key "sale.order.reset_to_draft:1" --confirm "sale.order.reset_to_draft"
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
    "order_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["order_id"],"resolved_ref":"sale.order.confirm.request.schema.json#/$defs/parameters"} |
| parameters.order_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"sale.order.reset_to_draft"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"sale.order.reset_to_draft"} |
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
- `execute`：fixed_native_sale_order_action_draft
- `verify`：same_transaction_draft_state_and_response_schema_validation
- `idempotency`：target_draft_state_recheck_without_operation_store
- `reverse`：sale.order.confirm_when_native_state_allows

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover native reset preconditions, exact confirmation, native ACLs, target-state replay, schemas, and CLI dispatch.；引用：tests/unit/test_order_document_writes.py, tests/unit/test_order_document_writes_runtime.py, tests/unit/test_order_document_write_cli.py, tests/unit/test_order_document_write_schemas.py
- `integration`：`implemented`；The guarded shared live smoke verifies native reset, replay, and rollback in both dedicated isolated databases.；引用：tests/integration/test_order_document_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-sale-order-search"></a>

## sale.order.search — 搜索销售订单

- 类型：只读；静态状态：`unconfigured`；handler：`sale_order_search`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, modules, and ACLs.
- 内部domain：`sales_accounting`；来源模型：account.move, crm.team, res.company, res.currency, res.partner, res.users, sale.order, sale.order.line, stock.picking；向导：无。
- 必需模块：account, base, sale, sale_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.move:read, crm.team:read, res.company:read, res.currency:read, res.partner:read, res.users:read, sale.order:read, sale.order.line:read, stock.picking:read。
- 请求/响应合同：`schemas/v1/sale.order.search.request.schema.json` / `schemas/v1/sale.order.search.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read sale.order.search --request "@request.json"
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
| parameters.query | string/null | 可选（可能有条件限制） |  | 搜索文本 | {"maxLength":200,"minLength":1} |
| parameters.date_from | 组合/开放结构 | 可选（可能有条件限制） |  | 开始日期 | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| parameters.date_from | null | 分支约束 | oneOf[1] | 开始日期 |  |
| parameters.date_from | string | 分支约束 | oneOf[2] | 开始日期 | {"format":"date"} |
| parameters.date_to | 组合/开放结构 | 可选（可能有条件限制） |  | 结束日期 | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| parameters.date_to | null | 分支约束 | oneOf[1] | 结束日期 |  |
| parameters.date_to | string | 分支约束 | oneOf[2] | 结束日期 | {"format":"date"} |
| parameters.states | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"oneOf":[{"type":"null"},{"items":{"enum":["draft","sent","sale","cancel"]},"maxItems":4,"minItems":1,"type":"array","uniqueItems":true}],"resolved_ref":"#/$defs/nullableStates"} |
| parameters.states | null | 分支约束 | oneOf[1] |  |  |
| parameters.states | array | 分支约束 | oneOf[2] |  | {"maxItems":4,"minItems":1,"uniqueItems":true} |
| parameters.states[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["draft","sent","sale","cancel"]} |
| parameters.partner_id | integer/null | 可选（可能有条件限制） |  | 合作伙伴ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.currency_id | integer/null | 可选（可能有条件限制） |  | 币种ID | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.user_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.payment_term_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.fiscal_position_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.invoice_statuses | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"oneOf":[{"type":"null"},{"items":{"enum":["upselling","invoiced","to invoice","no"]},"maxItems":4,"minItems":1,"type":"array","uniqueItems":true}],"resolved_ref":"#/$defs/nullableInvoiceStatuses"} |
| parameters.invoice_statuses | null | 分支约束 | oneOf[1] |  |  |
| parameters.invoice_statuses | array | 分支约束 | oneOf[2] |  | {"maxItems":4,"minItems":1,"uniqueItems":true} |
| parameters.invoice_statuses[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["upselling","invoiced","to invoice","no"]} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/page"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"sale.order.search"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/page"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/page"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","company","partner","state","date_order","currency","user","invoice_status","amount_untaxed","amount_tax","amount_total","invoice_ids","transfer_ids","line_count","validity_date","client_order_ref","team","delivery_status"],"resolved_ref":"#/$defs/header"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].company | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].company.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].partner | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","sent","sale","cancel"]} |
| response.data.items[].date_order | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.items[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].user | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.items[].user | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].user | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].user.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].user.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].payment_term_id | integer/null | 可选（可能有条件限制） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].fiscal_position_id | integer/null | 可选（可能有条件限制） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].invoice_status | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["upselling","invoiced","to invoice","no"]} |
| response.data.items[].amount_untaxed | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_tax | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_invoiced | 组合/开放结构 | 可选（可能有条件限制） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.items[].amount_invoiced | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].amount_invoiced | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_to_invoice | 组合/开放结构 | 可选（可能有条件限制） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.items[].amount_to_invoice | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].amount_to_invoice | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].invoice_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.items[].invoice_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.items[].transfer_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.items[].transfer_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.items[].line_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.items[].validity_date | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| response.data.items[].validity_date | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].validity_date | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.items[].client_order_ref | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].team | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.items[].team | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].team | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].team.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].team.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].delivery_status | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["pending","started","partial","full",null]} |
| response.data.has_more | boolean | 必填（所在对象出现时） | oneOf[2] | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | oneOf[2] | 下一页不透明游标，无后续时可为空 | {"minLength":1} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/page"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/page"} |
| response.data.items | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","company","partner","state","date_order","currency","user","invoice_status","amount_untaxed","amount_tax","amount_total","invoice_ids","transfer_ids","line_count","validity_date","client_order_ref","team","delivery_status"],"resolved_ref":"#/$defs/header"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].company | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].company.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].partner | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","sent","sale","cancel"]} |
| response.data.items[].date_order | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","resolved_ref":"#/$defs/utcDateTime"} |
| response.data.items[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].user | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.items[].user | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].user | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].user.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].user.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].payment_term_id | integer/null | 可选（可能有条件限制） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].fiscal_position_id | integer/null | 可选（可能有条件限制） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].invoice_status | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["upselling","invoiced","to invoice","no"]} |
| response.data.items[].amount_untaxed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_tax | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_invoiced | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.items[].amount_invoiced | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].amount_invoiced | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_to_invoice | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.items[].amount_to_invoice | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].amount_to_invoice | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].invoice_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.items[].invoice_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].transfer_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| response.data.items[].transfer_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].line_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.items[].validity_date | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| response.data.items[].validity_date | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].validity_date | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date"} |
| response.data.items[].client_order_ref | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1,"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].team | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/ref"}],"resolved_ref":"#/$defs/nullableRef"} |
| response.data.items[].team | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].team | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/ref"} |
| response.data.items[].team.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].team.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].delivery_status | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["pending","started","partial","full",null]} |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[1]/then | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[1]/then | 下一页不透明游标，无后续时可为空 | {"minLength":1} |
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
- `execute`：fixed_company_scoped_sales_order_search
- `verify`：read_only_transaction_acl_cursor_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover closed filters, bound ASC cursors, company and ACL scope, Odoo mapping, schemas, and CLI dispatch. Native optional projections and explicit accounting filters are covered.；引用：tests/unit/test_order_documents.py, tests/unit/test_order_documents_bridge.py, tests/unit/test_order_documents_runtime.py, tests/unit/test_order_documents_schemas.py, tests/unit/test_order_documents_cli.py, tests/unit/test_capability_registry.py, tests/unit/test_order_accounting_reads_contract.py, tests/unit/test_order_accounting_reads_runtime.py, tests/unit/test_order_accounting_reads_cli.py
- `integration`：`implemented`；The guarded shared smoke exercises sales and purchase order reads in both dedicated isolated databases.；引用：tests/integration/test_order_documents_batch_live.py, tests/integration/test_order_accounting_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-sale-order-update_draft"></a>

## sale.order.update_draft — 更新草稿销售订单

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user. Replay uses a target-payload recheck without a persistent operation store, so an old request can become effective after an intervening state change.
- 内部domain：`sales_accounting`；来源模型：account.payment.term, res.company, sale.order, sale.order.line；向导：无。
- 必需模块：account, base, sale, sale_stock, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：sales_team.group_sale_salesman；ACL：res.company:read, sale.order:read, sale.order:write, sale.order.line:read。
- 请求/响应合同：`schemas/v1/sale.order.update_draft.request.schema.json` / `schemas/v1/sale.order.update_draft.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run sale.order.update_draft --request "@request.json" --idempotency-key "sale.order.update_draft:1:0d520bff47d6b8f0e9489e1b94a3417c" --confirm "sale.order.update_draft"
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
    "order_id": 1,
    "changes": {
      "client_order_ref": "1"
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["order_id","changes"]} |
| parameters.order_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.client_order_ref | string/null | 可选（可能有条件限制） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$","resolved_ref":"sale.order.create.request.schema.json#/$defs/nullable_text"} |
| parameters.changes.validity_date | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.changes.commitment_date | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"oneOf":[{"type":"null"},{"$ref":"sale.order.create.request.schema.json#/$defs/datetime"}]} |
| parameters.changes.commitment_date | null | 分支约束 | oneOf[1] |  |  |
| parameters.changes.commitment_date | string | 分支约束 | oneOf[2] |  | {"pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$","resolved_ref":"sale.order.create.request.schema.json#/$defs/datetime"} |
| parameters.changes.payment_term_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"sale.order.create.request.schema.json#/$defs/nullable_id"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"sale.order.update_draft"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"sale.order.update_draft"} |
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
- `execute`：fixed_native_draft_sale_order_write_action
- `verify`：same_transaction_target_header_payload_and_response_schema_validation
- `idempotency`：target_header_payload_recheck_without_operation_store
- `reverse`：repeat_update_with_previous_header_values

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request, draft-only update, exact confirmation, native ACLs, target-payload replay, schemas, and CLI dispatch.；引用：tests/unit/test_order_document_writes.py, tests/unit/test_order_document_writes_runtime.py, tests/unit/test_order_document_write_cli.py, tests/unit/test_order_document_write_schemas.py
- `integration`：`implemented`；The guarded shared live smoke verifies draft updates, replay, and rollback in both dedicated isolated databases.；引用：tests/integration/test_order_document_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches the target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。
