# 供应商账单、采购匹配与供应商退款单

创建供应商账单和来源退款单，由采购订单生成账单，检查、建立或解除采购行匹配，并配置公司快速录入和账单审核选项。账单查改和过账使用共用发票场景；供应商退款单是信用单据，实际收回现金需走应付收付款接口。

[回到总说明书](../../CLI_V4_MANUAL.md) · [新会话使用指南](../USAGE_GUIDE.md)

<a id="cap-company-bill_processing_policy-update"></a>

## company.bill_processing_policy.update — 设置公司快速录入和账单自动审核选项

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Fixed current-company settings are implemented; native company write requires access-rights administration and reference ACLs. Ordinary accountant permission is not implied.
- 内部domain：`accounting_configuration`；来源模型：ir.default, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：base.group_erp_manager；ACL：ir.default:read, res.company:read, res.company:write。
- 请求/响应合同：`schemas/v1/company.bill_processing_policy.update.request.schema.json` / `schemas/v1/company.bill_processing_policy.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run company.bill_processing_policy.update --request "@request.json" --idempotency-key "company.bill_processing_policy.update:1:635933d8ef77d3b65f31c7669c229187" --confirm "company.bill_processing_policy.update"
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
      "autopost_bills": false
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["changes"]} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.autopost_bills | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.changes.quick_edit_mode | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["in_invoices","out_and_in_invoices","out_invoices",null]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"company.bill_processing_policy.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"company.bill_processing_policy.update"} |
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

<a id="cap-purchase-order-bill-create"></a>

## purchase.order.bill.create — 由采购订单生成供应商账单

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`odoo_linked_bill_not_concurrency_unique` — The native handler rechecks linked bills for ordinary replay, but Odoo provides no database-unique operation key for concurrent exactly-once creation. The order_ids route creates later native invoiceable rounds with ordinary-user native marker write access and actual native grouping/quantities; legacy order_id replay is retained. Operation markers are not concurrency-unique.
- 内部domain：`purchase_accounting`；来源模型：purchase.order, purchase.order.line, account.move, account.move.line；向导：无。
- 必需模块：purchase, account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：purchase.order:read, purchase.order:write, purchase.order.line:read, account.move:read, account.move:create, account.move:write, account.move.line:read, account.move.line:create, account.move.line:write。
- 请求/响应合同：`schemas/v1/purchase.order.bill.create.request.schema.json` / `schemas/v1/purchase.order.bill.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run purchase.order.bill.create --request "@request.json" --idempotency-key "purchase.order.bill.create:1" --confirm "purchase.order.bill.create"
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
| parameters | object | 必填 |  |  | {"additionalProperties":false,"oneOf":[{"properties":{"order_ids":false},"required":["order_id"]},{"properties":{"order_id":false},"required":["order_ids"]}]} |
| parameters.order_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.order_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":100,"minItems":1,"uniqueItems":true} |
| parameters.order_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters | 未限定 | 分支约束 | oneOf[1] |  | {"required_in_object":["order_id"]} |
| parameters.order_ids | 禁止 | 可选（可能有条件限制） | oneOf[1] |  | false |
| parameters | 未限定 | 分支约束 | oneOf[2] |  | {"required_in_object":["order_ids"]} |
| parameters.order_id | 禁止 | 可选（可能有条件限制） | oneOf[2] |  | false |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"purchase.order.bill.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"},{"$ref":"#/$defs/order_invoice_batch"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"#/$defs/order_invoice_batch"}]},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"purchase.order.bill.create"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"},{"$ref":"#/$defs/order_invoice_batch"}]} |
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
| response.data | object | 分支约束 | allOf[2]/oneOf[3] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"#/$defs/order_invoice_batch"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[3] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[3] |  | {"additionalProperties":false,"required_in_object":["items","processed_count"]} |
| response.data.result.items | array | 必填（所在对象出现时） | allOf[2]/oneOf[3] |  | {"maxItems":1000,"minItems":1,"uniqueItems":true} |
| response.data.result.items[] | 组合/开放结构 | 每个数组元素 | allOf[2]/oneOf[3] |  | {"allOf":[{"$ref":"core-write-result.schema.json#/properties/result"},{"properties":{"id":{"minimum":1,"type":"integer"},"model":{"const":"account.move"},"move_type":{"enum":["in_invoice","in_refund"]}}}]} |
| response.data.result.items[] | object | 分支约束 | allOf[2]/oneOf[3]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"],"resolved_ref":"core-write-result.schema.json#/properties/result"} |
| response.data.result.items[].model | string | 必填（所在对象出现时） | allOf[2]/oneOf[3]/allOf[1] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[3]/allOf[1] |  | {"minimum":1} |
| response.data.result.items[].name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[3]/allOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.result.items[].state | string | 必填（所在对象出现时） | allOf[2]/oneOf[3]/allOf[1] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[3]/allOf[1] | 所选公司ID | {"minimum":1} |
| response.data.result.items[].move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[3]/allOf[1] |  | {"minLength":1} |
| response.data.result.items[].source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[3]/allOf[1] |  | {"minimum":1} |
| response.data.result.items[].line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[3]/allOf[1] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.items[].line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[3]/allOf[1] | 行记录ID数组 | {"minimum":1} |
| response.data.result.items[].partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[3]/allOf[1] |  | {"uniqueItems":true} |
| response.data.result.items[].partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[3]/allOf[1] |  | {"minimum":1} |
| response.data.result.items[].full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[3]/allOf[1] | 完整核销关系ID | {"minimum":1} |
| response.data.result.items[].reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[3]/allOf[1] |  |  |
| response.data.result.items[] | 未限定 | 分支约束 | allOf[2]/oneOf[3]/allOf[2] |  |  |
| response.data.result.items[].model | 未限定 | 可选（可能有条件限制） | allOf[2]/oneOf[3]/allOf[2] |  | {"const":"account.move"} |
| response.data.result.items[].id | integer | 可选（可能有条件限制） | allOf[2]/oneOf[3]/allOf[2] |  | {"minimum":1} |
| response.data.result.items[].move_type | 未限定 | 可选（可能有条件限制） | allOf[2]/oneOf[3]/allOf[2] |  | {"enum":["in_invoice","in_refund"]} |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | allOf[2]/oneOf[3] |  | {"maximum":1000,"minimum":1} |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"#/$defs/order_invoice_batch"}]},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[3]/then |  | {"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"#/$defs/order_invoice_batch"}]} |
| response.data | object | 分支约束 | allOf[3]/then/oneOf[1] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then/oneOf[1] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then/oneOf[1] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[3]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"#/$defs/order_invoice_batch"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","processed_count"]} |
| response.data.result.items | array | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] |  | {"maxItems":1000,"minItems":1,"uniqueItems":true} |
| response.data.result.items[] | 组合/开放结构 | 每个数组元素 | allOf[3]/then/oneOf[2] |  | {"allOf":[{"$ref":"core-write-result.schema.json#/properties/result"},{"properties":{"id":{"minimum":1,"type":"integer"},"model":{"const":"account.move"},"move_type":{"enum":["in_invoice","in_refund"]}}}]} |
| response.data.result.items[] | object | 分支约束 | allOf[3]/then/oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"],"resolved_ref":"core-write-result.schema.json#/properties/result"} |
| response.data.result.items[].model | string | 必填（所在对象出现时） | allOf[3]/then/oneOf[2]/allOf[1] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].id | integer/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[2]/allOf[1] |  | {"minimum":1} |
| response.data.result.items[].name | string/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[2]/allOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.result.items[].state | string | 必填（所在对象出现时） | allOf[3]/then/oneOf[2]/allOf[1] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].company_id | integer | 必填（所在对象出现时） | allOf[3]/then/oneOf[2]/allOf[1] | 所选公司ID | {"minimum":1} |
| response.data.result.items[].move_type | string/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[2]/allOf[1] |  | {"minLength":1} |
| response.data.result.items[].source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[2]/allOf[1] |  | {"minimum":1} |
| response.data.result.items[].line_ids | array | 必填（所在对象出现时） | allOf[3]/then/oneOf[2]/allOf[1] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.items[].line_ids[] | integer | 每个数组元素 | allOf[3]/then/oneOf[2]/allOf[1] | 行记录ID数组 | {"minimum":1} |
| response.data.result.items[].partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then/oneOf[2]/allOf[1] |  | {"uniqueItems":true} |
| response.data.result.items[].partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then/oneOf[2]/allOf[1] |  | {"minimum":1} |
| response.data.result.items[].full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[2]/allOf[1] | 完整核销关系ID | {"minimum":1} |
| response.data.result.items[].reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then/oneOf[2]/allOf[1] |  |  |
| response.data.result.items[] | 未限定 | 分支约束 | allOf[3]/then/oneOf[2]/allOf[2] |  |  |
| response.data.result.items[].model | 未限定 | 可选（可能有条件限制） | allOf[3]/then/oneOf[2]/allOf[2] |  | {"const":"account.move"} |
| response.data.result.items[].id | integer | 可选（可能有条件限制） | allOf[3]/then/oneOf[2]/allOf[2] |  | {"minimum":1} |
| response.data.result.items[].move_type | 未限定 | 可选（可能有条件限制） | allOf[3]/then/oneOf[2]/allOf[2] |  | {"enum":["in_invoice","in_refund"]} |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] |  | {"maximum":1000,"minimum":1} |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：native_purchase_order_action_create_invoice_as_configured_business_user
- `verify`：same_transaction_purchase_linked_draft_vendor_bill_reread_and_response_schema_validation
- `idempotency`：linked_vendor_bill_recheck_without_concurrent_exactly_once_guarantee
- `reverse`：invoice.cancel_or_supplier_credit_note

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed order contract, native bill creation path, company and ACL gates, replay, schemas, and CLI dispatch.；引用：tests/unit/test_procurement_inventory_writes.py, tests/unit/test_procurement_inventory_writes_runtime.py, tests/unit/test_procurement_inventory_write_schemas.py, tests/unit/test_core_write_cli.py, tests/unit/test_invoice_rounds_write_contract.py, tests/unit/test_invoice_rounds_runtime.py, tests/unit/test_invoice_rounds_product_reads.py, tests/unit/test_invoice_rounds_cli.py
- `integration`：`implemented`；The guarded shared transactional smoke verifies native purchase-to-bill creation and rollback in both isolated databases.；引用：tests/integration/test_accounting_followup_write_batch_live.py, tests/integration/test_invoice_rounds_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-purchase_bill-lines-unmatch"></a>

## purchase_bill.lines.unmatch — 取消供应商账单行的采购匹配

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user.
- 内部domain：`purchase_accounting`；来源模型：purchase.order.line, account.move, account.move.line；向导：无。
- 必需模块：purchase, account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：purchase.order.line:read, account.move:read, account.move:write, account.move.line:read, account.move.line:write。
- 请求/响应合同：`schemas/v1/purchase_bill.lines.unmatch.request.schema.json` / `schemas/v1/purchase_bill.lines.unmatch.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run purchase_bill.lines.unmatch --request "@request.json" --idempotency-key "purchase_bill.lines.unmatch:1:080a9ed428559ef602668b4c00f114f1" --confirm "purchase_bill.lines.unmatch"
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
    "bill_id": 1,
    "bill_line_ids": [
      1
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["bill_id","bill_line_ids"]} |
| parameters.bill_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.bill_line_ids | array | 必填（所在对象出现时） |  |  | {"maxItems":200,"minItems":1,"uniqueItems":true} |
| parameters.bill_line_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"purchase_bill.lines.unmatch"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"purchase_bill.lines.unmatch"} |
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
- `execute`：fixed_draft_vendor_bill_purchase_line_relation_clear_as_configured_business_user
- `verify`：same_transaction_cleared_purchase_line_relation_and_response_schema_validation
- `idempotency`：target_purchase_line_relation_recheck_without_operation_store
- `reverse`：purchase_bill.match

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed bill-line contract, draft and company gates, replay, schemas, and CLI dispatch.；引用：tests/unit/test_procurement_inventory_writes.py, tests/unit/test_procurement_inventory_writes_runtime.py, tests/unit/test_procurement_inventory_write_schemas.py, tests/unit/test_core_write_cli.py
- `integration`：`implemented`；The guarded shared transactional smoke verifies unmatch and rollback in both isolated databases.；引用：tests/integration/test_accounting_followup_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-purchase_bill-match"></a>

## purchase_bill.match — 匹配采购行和供应商账单

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user.
- 内部domain：`purchase_accounting`；来源模型：purchase.bill.line.match, purchase.order.line, account.move, account.move.line；向导：无。
- 必需模块：purchase, account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：purchase.bill.line.match:write, purchase.order.line:read, account.move.line:read, account.move.line:write, account.move:write, account.move:read。
- 请求/响应合同：`schemas/v1/purchase_bill.match.request.schema.json` / `schemas/v1/purchase_bill.match.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run purchase_bill.match --request "@request.json" --idempotency-key "purchase_bill.match:1:b5d01a691a6a5ec8c4094e463f4805c7" --confirm "purchase_bill.match"
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
    "bill_id": 1,
    "pairs": [
      {
        "bill_line_id": 1,
        "purchase_line_id": 1
      }
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["bill_id","pairs"]} |
| parameters.bill_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.pairs | array | 必填（所在对象出现时） |  |  | {"maxItems":200,"minItems":1,"uniqueItems":true} |
| parameters.pairs[] | object | 每个数组元素 |  |  | {"additionalProperties":false,"required_in_object":["bill_line_id","purchase_line_id"],"resolved_ref":"#/$defs/pair"} |
| parameters.pairs[].bill_line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.pairs[].purchase_line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"purchase_bill.match"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"purchase_bill.match"} |
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
- `execute`：fixed_native_purchase_bill_line_pair_matching_as_configured_business_user
- `verify`：same_transaction_persisted_purchase_line_relation_and_response_schema_validation
- `idempotency`：target_purchase_line_relation_recheck_without_operation_store
- `reverse`：purchase_bill.lines.unmatch

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed pair contract, native matching path, ACL and company gates, replay, and schemas.；引用：tests/unit/test_procurement_inventory_writes.py, tests/unit/test_procurement_inventory_writes_runtime.py, tests/unit/test_procurement_inventory_write_schemas.py, tests/unit/test_core_write_cli.py
- `integration`：`implemented`；The guarded shared live smoke verifies native pair matching and rollback in both dedicated isolated databases.；引用：tests/integration/test_accounting_followup_write_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-purchase_bill-matching-inspect"></a>

## purchase_bill.matching.inspect — 检查采购与供应商账单匹配

- 类型：只读；静态状态：`unconfigured`；handler：`purchase_bill_matching_inspect`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`purchase_accounting`；来源模型：purchase.bill.line.match, purchase.order.line, account.move, account.move.line；向导：无。
- 必需模块：purchase, purchase_stock, account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：purchase.bill.line.match:read, purchase.order.line:read, account.move:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/purchase_bill.matching.inspect.request.schema.json` / `schemas/v1/purchase_bill.matching.inspect.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read purchase_bill.matching.inspect --request "@request.json"
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
    "bill_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  |  |
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["bill_id"]} |
| parameters.bill_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"properties":{"capability":{"const":"purchase_bill.matching.inspect"},"data":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]}}}]} |
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
| response | 组合/开放结构 | 分支约束 | allOf[2] |  | {"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}]} |
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"purchase_bill.matching.inspect"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","company_id","partner","currency","is_purchase_matched","purchase_order_ids","lines"],"resolved_ref":"#/$defs/data"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.name | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.name | string | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"enum":["in_invoice","in_refund"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/namedRef"}]} |
| response.data.partner | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.partner | object | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/namedRef"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.is_purchase_matched | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response.data.purchase_order_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.purchase_order_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 |  |
| response.data.lines[] | object | 每个数组元素 | allOf[2]/oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","product","label","quantity","price_subtotal","purchase_line","unmatched_queue"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].product | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/namedRef"}]} |
| response.data.lines[].product | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].product | object | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/namedRef"} |
| response.data.lines[].product.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].product.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].label | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.lines[].label | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].label | string | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.lines[].quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].price_subtotal | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].purchase_line | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/purchaseLine"}]} |
| response.data.lines[].purchase_line | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].purchase_line | object | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","order_id","ordered_quantity","received_quantity","invoiced_quantity","to_invoice_quantity"],"resolved_ref":"#/$defs/purchaseLine"} |
| response.data.lines[].purchase_line.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].purchase_line.order_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].purchase_line.ordered_quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].purchase_line.received_quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].purchase_line.invoiced_quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].purchase_line.to_invoice_quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].unmatched_queue | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[2]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[2]/allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[2]/allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[2]/allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","company_id","partner","currency","is_purchase_matched","purchase_order_ids","lines"],"resolved_ref":"#/$defs/data"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.name | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[1] | 名称/行说明 |  |
| response.data.name | string | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"enum":["in_invoice","in_refund"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/namedRef"}]} |
| response.data.partner | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[1] |  |  |
| response.data.partner | object | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/namedRef"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.is_purchase_matched | boolean | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  |  |
| response.data.purchase_order_ids | array | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"uniqueItems":true} |
| response.data.purchase_order_ids[] | integer | 每个数组元素 | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.lines | array | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| response.data.lines[] | object | 每个数组元素 | allOf[2]/allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","product","label","quantity","price_subtotal","purchase_line","unmatched_queue"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].product | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/namedRef"}]} |
| response.data.lines[].product | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].product | object | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/namedRef"} |
| response.data.lines[].product.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].product.name | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].label | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.lines[].label | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].label | string | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.lines[].quantity | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].price_subtotal | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].purchase_line | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/purchaseLine"}]} |
| response.data.lines[].purchase_line | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].purchase_line | object | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","order_id","ordered_quantity","received_quantity","invoiced_quantity","to_invoice_quantity"],"resolved_ref":"#/$defs/purchaseLine"} |
| response.data.lines[].purchase_line.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].purchase_line.order_id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].purchase_line.ordered_quantity | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].purchase_line.received_quantity | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].purchase_line.invoiced_quantity | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].purchase_line.to_invoice_quantity | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].unmatched_queue | boolean | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[2]/allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[2]/allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[2]/allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[2]/allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"response.schema.json#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[2]/allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[2]/allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：not_applicable_read_only
- `execute`：fixed_company_scoped_inventory_accounting_read
- `verify`：closed_runtime_result_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed contracts, fixed handler dispatch, runtime ACL and result normalization, CLI wiring, and registry metadata.；引用：tests/unit/test_inventory_accounting.py, tests/unit/test_inventory_accounting_bridge.py, tests/unit/test_inventory_accounting_runtime.py, tests/unit/test_inventory_accounting_cli.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The retained shared live smoke passed against both dedicated isolated database aliases as the ordinary accounting user, using read-only operations with no database commits.；引用：tests/integration/test_inventory_accounting_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-vendor_bill-create"></a>

## vendor_bill.create — 创建草稿供应商账单

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`invoices_and_bills`；来源模型：res.company, res.partner, res.partner.bank, account.fiscal.position, res.currency, account.journal, account.account, account.tax, account.move, account.move.line, product.product, account.payment.term, account.analytic.account；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：res.partner:read, res.partner.bank:read, account.fiscal.position:read, res.currency:read, account.journal:read, account.account:read, account.tax:read, account.move:read, account.move:create, account.move.line:read, account.move.line:create。
- 请求/响应合同：`schemas/v1/vendor_bill.create.request.schema.json` / `schemas/v1/vendor_bill.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run vendor_bill.create --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "vendor_bill.create"
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
    "journal_id": 1,
    "invoice_date": "2026-10-31",
    "currency_id": 1,
    "lines": [
      {
        "name": "Example",
        "quantity": "1",
        "tax_ids": [],
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
| parameters | object | 必填 |  |  | {"additionalProperties":false,"not":{"properties":{"invoice_date_due":{"type":"string"},"payment_term_id":{"type":"integer"}},"required":["invoice_date_due","payment_term_id"]},"required_in_object":["partner_id","journal_id","invoice_date","currency_id","lines"]} |
| parameters.partner_id | integer | 必填（所在对象出现时） |  | 合作伙伴ID | {"minimum":1} |
| parameters.journal_id | integer | 必填（所在对象出现时） |  | 日记账ID | {"minimum":1} |
| parameters.invoice_date | string | 必填（所在对象出现时） |  |  | {"format":"date"} |
| parameters.date | string | 可选（可能有条件限制） |  | Optional accounting date. Native Odoo posting and lock-date rules still apply. | {"format":"date"} |
| parameters.invoice_date_due | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.partner_bank_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.fiscal_position_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.payment_term_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.reference | string/null | 可选（可能有条件限制） |  |  | {"maxLength":200,"minLength":1} |
| parameters.payment_reference | string/null | 可选（可能有条件限制） |  |  | {"maxLength":200,"minLength":1} |
| parameters.currency_id | integer | 必填（所在对象出现时） |  | 币种ID | {"minimum":1} |
| parameters.lines | array | 必填（所在对象出现时） |  | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":200,"minItems":1} |
| parameters.lines[] | object | 每个数组元素 |  | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"allOf":[{"if":{"required":["product_uom_id"]},"then":{"properties":{"product_id":{"minimum":1,"type":"integer"}},"required":["product_id"]}}],"dependentRequired":{"deferred_end_date":["deferred_start_date"],"deferred_start_date":["deferred_end_date"]},"oneOf":[{"properties":{"deferred_end_date":{"type":"null"},"deferred_start_date":{"type":"null"}}},{"properties":{"deferred_end_date":{"type":"string"},"deferred_start_date":{"type":"string"}},"required":["deferred_start_date","deferred_end_date"]}],"required_in_object":["name","account_id","quantity","price_unit","tax_ids"]} |
| parameters.lines[].name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":500,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$"} |
| parameters.lines[].account_id | integer | 必填（所在对象出现时） |  | 会计科目ID | {"minimum":1} |
| parameters.lines[].product_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.lines[].product_uom_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.lines[].deductible_amount | string | 可选（可能有条件限制） |  | Native deductibility percentage, not a monetary amount. | {"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])","resolved_ref":"#/$defs/percentage_decimal"} |
| parameters.lines[].quantity | string | 必填（所在对象出现时） |  | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^-?(?:(?:[1-9][0-9]*)(?:\\.[0-9]+)?&#124;0\\.(?=[0-9]*[1-9])[0-9]+)$(?![\\s\\S])","resolved_ref":"#/$defs/nonzero_signed_decimal"} |
| parameters.lines[].price_unit | string | 必填（所在对象出现时） |  | 单价；币种及符号依单据和合同 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| parameters.lines[].discount | string | 可选（可能有条件限制） |  | 折扣百分比 | {"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])","resolved_ref":"#/$defs/percentage_decimal"} |
| parameters.lines[].tax_ids | array | 必填（所在对象出现时） |  | 应用税ID数组 | {"uniqueItems":true} |
| parameters.lines[].tax_ids[] | integer | 每个数组元素 |  | 应用税ID数组 | {"minimum":1} |
| parameters.lines[].analytic_distribution | 组合/开放结构 | 可选（可能有条件限制） |  | 分析分摊映射；写入与读回约束可能不同 | {"oneOf":[{"type":"null"},{"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"},"type":"object"}],"resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/analytic_distribution"} |
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
| parameters.lines[] | 组合/开放结构 | 分支约束 | allOf[1] | 行数组；增补/更新/替换语义由能力ID决定 | {"if":{"required":["product_uom_id"]},"then":{"properties":{"product_id":{"minimum":1,"type":"integer"}},"required":["product_id"]}} |
| parameters.lines[] | 未限定 | 条件分支 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"required_in_object":["product_id"]} |
| parameters.lines[].product_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"vendor_bill.create"} |
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
- `execute`：fixed_accounting_core_write_action_as_configured_business_user
- `verify`：same_transaction_rich_invoice_field_reread_and_schema_validation
- `idempotency`：odoo_persisted_business_marker_and_result_replay
- `reverse`：delete_draft_or_vendor_refund.create_after_posting

### 已登记测试与证据范围

- `unit`：`implemented`；Existing contracts and explicit native line unit/deductibility inputs covered.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_invoice_financial_headers.py, tests/unit/test_invoice_financial_headers_runtime.py, tests/unit/test_core_write_cli.py, tests/unit/test_accounting_entry_membership_batch.py, tests/unit/test_invoice_line_inputs_contract.py, tests/unit/test_invoice_line_inputs_runtime.py
- `integration`：`implemented`；Shared native smoke passed; full rollback.；引用：tests/integration/test_core_write_batch_live.py, tests/integration/test_accounting_depth_batch_live.py, tests/integration/test_invoice_financial_headers_prepayment_batch_live.py, tests/integration/test_accounting_entry_membership_batch_live.py, tests/integration/test_invoice_line_inputs_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-vendor_refund-create"></a>

## vendor_refund.create — 创建供应商退款单

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime. Batch move_ids creates full native refunds for 2-100 posted sources with operation/key markers binding the complete selection. Markers are not concurrency-unique.
- 内部domain：`invoices_and_bills`；来源模型：res.company, res.partner.bank, account.journal, account.move, account.move.reversal, res.partner, product.product, account.account, account.tax, account.move.line, account.analytic.account；向导：account.move.reversal。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：res.partner.bank:read, account.journal:read, account.move:read, account.move:write, account.move:create, account.move.reversal:create, res.partner:read, account.account:read, account.tax:read, account.move.line:read, account.move.line:create, account.move.line:write, account.move.line:unlink。
- 请求/响应合同：`schemas/v1/vendor_refund.create.request.schema.json` / `schemas/v1/vendor_refund.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run vendor_refund.create --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "vendor_refund.create"
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
    "reason": "1",
    "date": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  |  |
| parameters | object | 必填 |  |  | {"additionalProperties":false,"oneOf":[{"properties":{"move_ids":false},"required":["move_id"]},{"properties":{"lines":false,"move_id":false},"required":["move_ids"]}],"required_in_object":["date","reason"]} |
| parameters.move_id | integer | 可选（可能有条件限制） |  | 会计单据记录ID | {"minimum":1} |
| parameters.move_ids | array | 可选（可能有条件限制） |  | 会计单据ID数组 | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| parameters.move_ids[] | integer | 每个数组元素 |  | 会计单据ID数组 | {"minimum":1} |
| parameters.date | string | 必填（所在对象出现时） |  |  | {"format":"date"} |
| parameters.reason | string | 必填（所在对象出现时） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$"} |
| parameters.lines | array | 可选（可能有条件限制） |  | Custom refund lines may include product_uom_id and native deductible_amount percentage; full native batches do not accept custom lines. | {"maxItems":500,"minItems":1} |
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
| parameters | 未限定 | 分支约束 | oneOf[1] |  | {"required_in_object":["move_id"]} |
| parameters.move_ids | 禁止 | 可选（可能有条件限制） | oneOf[1] |  | false |
| parameters | 未限定 | 分支约束 | oneOf[2] |  | {"required_in_object":["move_ids"]} |
| parameters.move_id | 禁止 | 可选（可能有条件限制） | oneOf[2] |  | false |
| parameters.lines | 禁止 | 可选（可能有条件限制） | oneOf[2] |  | false |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"vendor_refund.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"vendor_refund.create"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]} |
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
| response.data | object | 分支约束 | allOf[2]/oneOf[3] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-batch-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[3] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[3] |  | {"additionalProperties":false,"required_in_object":["items","processed_count"]} |
| response.data.result.items | array | 必填（所在对象出现时） | allOf[2]/oneOf[3] |  | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| response.data.result.items[] | object | 每个数组元素 | allOf[2]/oneOf[3] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"],"resolved_ref":"core-write-result.schema.json#/properties/result"} |
| response.data.result.items[].model | string | 必填（所在对象出现时） | allOf[2]/oneOf[3] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[3] |  | {"minimum":1} |
| response.data.result.items[].name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[3] | 名称/行说明 | {"minLength":1} |
| response.data.result.items[].state | string | 必填（所在对象出现时） | allOf[2]/oneOf[3] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[3] | 所选公司ID | {"minimum":1} |
| response.data.result.items[].move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[3] |  | {"minLength":1} |
| response.data.result.items[].source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[3] |  | {"minimum":1} |
| response.data.result.items[].line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[3] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.items[].line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[3] | 行记录ID数组 | {"minimum":1} |
| response.data.result.items[].partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[3] |  | {"uniqueItems":true} |
| response.data.result.items[].partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[3] |  | {"minimum":1} |
| response.data.result.items[].full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[3] | 完整核销关系ID | {"minimum":1} |
| response.data.result.items[].reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[3] |  |  |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | allOf[2]/oneOf[3] |  | {"maximum":100,"minimum":2} |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[3]/then |  | {"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]} |
| response.data | object | 分支约束 | allOf[3]/then/oneOf[1] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then/oneOf[1] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then/oneOf[1] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[3]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-batch-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","processed_count"]} |
| response.data.result.items | array | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] |  | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| response.data.result.items[] | object | 每个数组元素 | allOf[3]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"],"resolved_ref":"core-write-result.schema.json#/properties/result"} |
| response.data.result.items[].model | string | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].id | integer/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] |  | {"minimum":1} |
| response.data.result.items[].name | string/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.result.items[].state | string | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].company_id | integer | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.result.items[].move_type | string/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] |  | {"minLength":1} |
| response.data.result.items[].source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] |  | {"minimum":1} |
| response.data.result.items[].line_ids | array | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.items[].line_ids[] | integer | 每个数组元素 | allOf[3]/then/oneOf[2] | 行记录ID数组 | {"minimum":1} |
| response.data.result.items[].partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.items[].partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then/oneOf[2] |  | {"minimum":1} |
| response.data.result.items[].full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] | 完整核销关系ID | {"minimum":1} |
| response.data.result.items[].reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] |  |  |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] |  | {"maximum":100,"minimum":2} |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_accounting_core_write_action_as_configured_business_user
- `verify`：same_transaction_rich_refund_line_reread_and_schema_validation
- `idempotency`：odoo_persisted_business_marker_and_result_replay
- `reverse`：create_a_new_correcting_bill

### 已登记测试与证据范围

- `unit`：`implemented`；Existing contracts and explicit native line unit/deductibility inputs covered.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_core_write_cli.py, tests/unit/test_accounting_entry_membership_batch.py, tests/unit/test_invoice_rounds_write_contract.py, tests/unit/test_invoice_rounds_runtime.py, tests/unit/test_invoice_rounds_product_reads.py, tests/unit/test_invoice_rounds_cli.py, tests/unit/test_invoice_line_inputs_contract.py, tests/unit/test_invoice_line_inputs_runtime.py
- `integration`：`implemented`；Shared native smoke passed; full rollback.；引用：tests/integration/test_core_write_batch_live.py, tests/integration/test_accounting_depth_batch_live.py, tests/integration/test_accounting_entry_membership_batch_live.py, tests/integration/test_invoice_rounds_live.py, tests/integration/test_invoice_line_inputs_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。
