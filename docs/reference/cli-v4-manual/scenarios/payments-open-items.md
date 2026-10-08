# 应收应付、收付款、现金退款与催款

查看未结项、付款计划、付款状态和账龄，登记客户收款、客户现金退款、供应商付款或供应商现金退款，维护支付单、日记账付款方式及付款条款，处理到期日、付款暂停和催款排除，并输出或发送收款凭证、客户对账单及催款资料。应收与应付入口按原单类型确定收付方向；支付核销和差额还需结合核销场景。

[回到总说明书](../../CLI_V4_MANUAL.md) · [新会话使用指南](../USAGE_GUIDE.md)

<a id="cap-company-cash_discount_accounts-assign"></a>

## company.cash_discount_accounts.assign — 设置公司现金折扣损益科目

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Fixed current-company settings are implemented; native company write requires access-rights administration and reference ACLs. Ordinary accountant permission is not implied.
- 内部domain：`accounting_configuration`；来源模型：account.account, ir.default, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：base.group_erp_manager；ACL：account.account:read, ir.default:read, res.company:read, res.company:write。
- 请求/响应合同：`schemas/v1/company.cash_discount_accounts.assign.request.schema.json` / `schemas/v1/company.cash_discount_accounts.assign.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run company.cash_discount_accounts.assign --request "@request.json" --idempotency-key "company.cash_discount_accounts.assign:1:d939ada469f992f9f01899db72032b76" --confirm "company.cash_discount_accounts.assign"
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
      "account_journal_early_pay_discount_gain_account_id": 1
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["changes"]} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.account_journal_early_pay_discount_gain_account_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.changes.account_journal_early_pay_discount_loss_account_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"company.cash_discount_accounts.assign"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"company.cash_discount_accounts.assign"} |
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

<a id="cap-invoice-followup-update"></a>

## invoice.followup.update — 更新发票或账单催款排除状态

- 类型：写入；静态状态：`unconfigured`；handler：`accounting_delivery`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`receivables_payables`；来源模型：res.company, account.move, account.move.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：res.company:read, account.move:read, account.move:write, account.move.line:read, account.move.line:write。
- 请求/响应合同：`schemas/v1/invoice.followup.update.request.schema.json` / `schemas/v1/invoice.followup.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.followup.update --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "invoice.followup.update"
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
    "no_followup": false
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id","no_followup"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.no_followup | boolean | 必填（所在对象出现时） |  |  |  |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.followup.update"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"#/$defs/data"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["record_id","no_followup"]} |
| response.data.result.record_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.result.no_followup | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"#/$defs/data"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[1]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["record_id","no_followup"]} |
| response.data.result.record_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.result.no_followup | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
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
- `execute`：fixed_account_move_no_followup_write
- `verify`：same_transaction_target_state_reread_and_response_schema_validation
- `idempotency`：target_value_replay_without_operation_store
- `reverse`：repeat_with_the_previous_no_followup_value

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover the closed boolean update, confirmation, result binding, registry metadata, and schemas.；引用：tests/unit/test_accounting_delivery.py, tests/unit/test_accounting_delivery_registry.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases as uid 5 with su=False, verifying invoice and receivable-line no_followup propagation, immediate replay, and rollback.；引用：tests/integration/test_accounting_delivery_batch_live.py
- `golden`：`planned`；Golden update examples are pending.；引用：无
- `e2e`：`planned`；Natural-language routing evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-payment_block-set"></a>

## invoice.payment_block.set — 设置发票付款阻止状态

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires explicit runtime company/user scope and native ACLs. Currency/rounding/term/method/schedule changes require draft moves; review uses the native posted-only method. Auto-post configuration schedules native future work but never runs a cron or posts a move in this command. No arbitrary field/method calls or external delivery.
- 内部domain：`accounting_documents`；来源模型：account.move, account.move.line, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.move.line:read, account.move:read, account.move:write。
- 请求/响应合同：`schemas/v1/invoice.payment_block.set.request.schema.json` / `schemas/v1/invoice.payment_block.set.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.payment_block.set --request "@request.json" --idempotency-key "invoice.payment_block.set:1:090d10a6f0dc713eff3e0e17e70a7469" --confirm "invoice.payment_block.set"
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
    "blocked": false,
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["blocked","move_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.blocked | boolean | 必填（所在对象出现时） |  |  |  |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.payment_block.set"} |
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

<a id="cap-invoice-payment_method-assign"></a>

## invoice.payment_method.assign — 设置发票付款方式

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires explicit runtime company/user scope and native ACLs. Currency/rounding/term/method/schedule changes require draft moves; review uses the native posted-only method. Auto-post configuration schedules native future work but never runs a cron or posts a move in this command. No arbitrary field/method calls or external delivery.
- 内部domain：`accounting_documents`；来源模型：account.journal, account.move, account.move.line, account.payment.method.line, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.journal:read, account.move.line:read, account.move:read, account.move:write, account.payment.method.line:read。
- 请求/响应合同：`schemas/v1/invoice.payment_method.assign.request.schema.json` / `schemas/v1/invoice.payment_method.assign.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.payment_method.assign --request "@request.json" --idempotency-key "invoice.payment_method.assign:1:f67597a755e686c092ad999c397caee0" --confirm "invoice.payment_method.assign"
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
    "payment_method_line_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id","payment_method_line_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.payment_method_line_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.payment_method.assign"} |
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
- `execute`：native_draft_or_posted_invoice_preferred_method_write_for_later_payment_registration
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：native_current_payload_recheck
- `reverse`：restore_previous_setting_subject_to_native_state_and_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Focused closed-input, legacy omission/key, company/state/ACL and result binding tests; execution is required before acceptance.；引用：tests/unit/test_accounting_maintenance_batch.py
- `integration`：`implemented`；One shared public CLI/native ORM workflow passed both isolated aliases in 24.70s as uid5/su=False/company1. Two new IDs and six extensions: exact-current-root currency-rate correction/date/replay, native technical Float readback, conversion/delete fallback and missing denial; explicit foreign-bank positive/negative paired amount set/clear/replay while legacy omitted shapes remain unchanged; reconciled statement membership/detach retaining native lines, posted moves, financial snapshots and matching graphs; posted unsent invoice bank set/clear with native PDF-link sent denial; posted preferred-method wizard default and Incoterm/location set/clear; a real partially reconciled invoice retaining raw matching IDs/amounts and financial lines. Native configuration roles exist only inside the isolated transaction, never sudo business calls. Fresh tracked fixtures, both companies settings, all defaults, currencies/rates and exact caller/native group memberships roll back. Live companies are independent roots; branch context rejection has unit evidence only. PDF uses synthetic DB-only raw bytes and native linking, not generation or delivery. Wizard defaults do not make payments. All hierarchy/currency/precision/localization/hash/lock paths, fully-paid/CABA invoices, existing foreign-invoice revaluation and concurrent exactly-once are not claimed. Legacy currency.rate.record guard is unchanged. No business DB, native source/addon, configuration, service or external-send changes.；引用：tests/integration/test_accounting_maintenance_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-payment_schedule-inspect"></a>

## invoice.payment_schedule.inspect — 查看发票原生分期到期计划

- 类型：只读；静态状态：`unconfigured`；handler：`invoice_payment_schedule_inspect`。
- 状态原因：`runtime_context_required` — Requires configured user/company and native ACLs. Reads actual invoice needed_terms including native currencies, maturity/discount dates and amounts; this is a computed plan, not actual payment or residual proof. Usage is scoped to visible shared/own terms and same-company documents. Mutations only target owned terms; duplicate may read a shared term and create an independent company-owned copy. Child writes use one parent write and native savepoint, preserving IDs/order and native total/early-discount constraints; fixed amounts and days follow native signed semantics. Native final line is the residual regardless of its amount type; there is no invented sequence/order field. Referenced-term deletion and missing targets remain native errors, not fake replay. No posted-entry rewrite, external delivery, arbitrary fields/methods or caller-sudo.
- 内部domain：`invoices_and_bills`；来源模型：res.company, account.move, account.move.line, account.payment.term, account.payment.term.line, res.currency, account.cash.rounding, account.tax；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move:read, account.move.line:read, account.payment.term:read, account.payment.term.line:read, res.currency:read, account.cash.rounding:read, account.tax:read。
- 请求/响应合同：`schemas/v1/invoice.payment_schedule.inspect.request.schema.json` / `schemas/v1/invoice.payment_schedule.inspect.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read invoice.payment_schedule.inspect --request "@request.json"
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
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.payment_schedule.inspect"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["company_currency_id","company_id","currency_id","id","lines","move_type","payment_term_id","state"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.currency_id | integer | 必填（所在对象出现时） | oneOf[2] | 币种ID | {"minimum":1} |
| response.data.company_currency_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.payment_term_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.lines | array | 必填（所在对象出现时） | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":100000} |
| response.data.lines[] | object | 每个数组元素 | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["amount_currency","balance","date_maturity","discount_amount_currency","discount_balance","discount_date"]} |
| response.data.lines[].date_maturity | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.lines[].discount_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.lines[].balance | string | 必填（所在对象出现时） | oneOf[2] | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.lines[].amount_currency | string | 必填（所在对象出现时） | oneOf[2] | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.lines[].discount_balance | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.lines[].discount_amount_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["company_currency_id","company_id","currency_id","id","lines","move_type","payment_term_id","state"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.currency_id | integer | 必填（所在对象出现时） | allOf[1]/then | 币种ID | {"minimum":1} |
| response.data.company_currency_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.payment_term_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines | array | 必填（所在对象出现时） | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":100000} |
| response.data.lines[] | object | 每个数组元素 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["amount_currency","balance","date_maturity","discount_amount_currency","discount_balance","discount_date"]} |
| response.data.lines[].date_maturity | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.lines[].discount_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.lines[].balance | string | 必填（所在对象出现时） | allOf[1]/then | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.lines[].amount_currency | string | 必填（所在对象出现时） | allOf[1]/then | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.lines[].discount_balance | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.lines[].discount_amount_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
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
- `execute`：fixed_native_needed_terms_or_scoped_usage_read
- `verify`：closed_response_schema_validation
- `idempotency`：read_only
- `reverse`：not_applicable

### 已登记测试与证据范围

- `unit`：`implemented`；Closed request/result ownership, native line shapes, atomic ID-preserving updates, fixed routing, schemas, access denials and actual invoice schedule normalization.；引用：tests/unit/test_payment_term_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all eight new IDs, five existing setup IDs and six immediate replays; native owned/shared term copies with independent child IDs, individual and atomic line edits preserving IDs, native failed percentage/early-discount mutations rolled back per call, actual taxed foreign-currency installment and early-discount schedules, posted entries unchanged by configuration changes, scoped ID-keyset usage reads including archived terms, unused-term deletion/cascade and native referenced-term deletion denial. Wrong-parent/company, shared-term mutation, changed-source copy and missing targets denied. Fresh-cursor business-data and temporary-group rollback verified. No payment, external delivery, addon or service changes.；引用：tests/integration/test_payment_term_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-payment_status-inspect"></a>

## invoice.payment_status.inspect — 检查发票付款状态和余额

- 类型：只读；静态状态：`unconfigured`；handler：`invoice_payment_status_inspect`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`receivables_payables`；来源模型：account.move, account.move.line, account.partial.reconcile, account.payment, account.payment.method, account.payment.method.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move:read, account.move.line:read, account.journal:read, account.account:read, account.partial.reconcile:read, account.payment:read, account.payment.method:read, account.payment.method.line:read, res.currency:read, res.partner:read。
- 请求/响应合同：`schemas/v1/invoice.payment_status.inspect.request.schema.json` / `schemas/v1/invoice.payment_status.inspect.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read invoice.payment_status.inspect --request "@request.json"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.payment_status.inspect"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","payment_state","company_id","currency","company_currency","amount_total","amount_residual","receivable_payable_lines","reconciliations","payments","outstanding_items"],"resolved_ref":"#/$defs/data"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["out_invoice","out_refund","in_invoice","in_refund"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.payment_state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy"]} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"invoice.search.response.schema.json#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.company_currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"invoice.search.response.schema.json#/$defs/currency"} |
| response.data.company_currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.amount_residual | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.receivable_payable_lines | array | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.receivable_payable_lines[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","account","date_maturity","balance","amount_currency","amount_residual","amount_residual_currency","currency","reconciled","matching_number"],"resolved_ref":"#/$defs/receivable_payable_line"} |
| response.data.receivable_payable_lines[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.receivable_payable_lines[].account | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name","account_type"],"resolved_ref":"#/$defs/account"} |
| response.data.receivable_payable_lines[].account.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.receivable_payable_lines[].account.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.receivable_payable_lines[].account.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.receivable_payable_lines[].account.account_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["asset_receivable","liability_payable"]} |
| response.data.receivable_payable_lines[].date_maturity | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.receivable_payable_lines[].balance | string | 必填（所在对象出现时） | oneOf[2] | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.receivable_payable_lines[].amount_currency | string | 必填（所在对象出现时） | oneOf[2] | 外币/交易币数值，非默认公司币金额 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.receivable_payable_lines[].amount_residual | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.receivable_payable_lines[].amount_residual_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.receivable_payable_lines[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"invoice.search.response.schema.json#/$defs/currency"} |
| response.data.receivable_payable_lines[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.receivable_payable_lines[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.receivable_payable_lines[].reconciled | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.receivable_payable_lines[].matching_number | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.reconciliations | array | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.reconciliations[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","date","amount","company_amount","currency","company_currency","invoice_line_id","counterpart_line_id","counterpart_move","payment_id","exchange_move_id"],"resolved_ref":"#/$defs/reconciliation"} |
| response.data.reconciliations[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.reconciliations[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.reconciliations[].amount | string | 必填（所在对象出现时） | oneOf[2] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.reconciliations[].company_amount | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.reconciliations[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"invoice.search.response.schema.json#/$defs/currency"} |
| response.data.reconciliations[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.reconciliations[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.reconciliations[].company_currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"invoice.search.response.schema.json#/$defs/currency"} |
| response.data.reconciliations[].company_currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.reconciliations[].company_currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.reconciliations[].invoice_line_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.reconciliations[].counterpart_line_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.reconciliations[].counterpart_move | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","date"],"resolved_ref":"#/$defs/counterpart_move"} |
| response.data.reconciliations[].counterpart_move.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.reconciliations[].counterpart_move.name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.reconciliations[].counterpart_move.move_type | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.reconciliations[].counterpart_move.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.reconciliations[].counterpart_move.date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.reconciliations[].payment_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 付款/收款记录ID | {"minimum":1} |
| response.data.reconciliations[].exchange_move_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.payments | array | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.payments[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","state","date","payment_type","partner_type","amount","currency","journal","payment_method","move_id","is_reconciled","is_matched"],"resolved_ref":"#/$defs/payment"} |
| response.data.payments[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.payments[].name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.payments[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","in_process","paid","canceled","rejected"]} |
| response.data.payments[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.payments[].payment_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["inbound","outbound"]} |
| response.data.payments[].partner_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["customer","supplier"]} |
| response.data.payments[].amount | string | 必填（所在对象出现时） | oneOf[2] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.payments[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"invoice.search.response.schema.json#/$defs/currency"} |
| response.data.payments[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.payments[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.payments[].journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"invoice.search.response.schema.json#/$defs/journal"} |
| response.data.payments[].journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.payments[].journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":5,"minLength":1} |
| response.data.payments[].journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.payments[].payment_method | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/payment_method"} |
| response.data.payments[].payment_method.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.payments[].payment_method.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.payments[].payment_method.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.payments[].move_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 会计单据记录ID | {"minimum":1} |
| response.data.payments[].is_reconciled | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.payments[].is_matched | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.outstanding_items | array | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.outstanding_items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["line_id","move_id","payment_id","date","label","amount","currency"],"resolved_ref":"#/$defs/outstanding_item"} |
| response.data.outstanding_items[].line_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.outstanding_items[].move_id | integer | 必填（所在对象出现时） | oneOf[2] | 会计单据记录ID | {"minimum":1} |
| response.data.outstanding_items[].payment_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 付款/收款记录ID | {"minimum":1} |
| response.data.outstanding_items[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.outstanding_items[].label | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.outstanding_items[].amount | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"allOf":[{"$ref":"invoice.search.response.schema.json#/$defs/money"},{"pattern":"^(?:0\\.[0-9]*[1-9][0-9]*&#124;[1-9][0-9]*(?:\\.[0-9]+)?)$"}]} |
| response.data.outstanding_items[].amount | string | 分支约束 | oneOf[2]/allOf[1] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.outstanding_items[].amount | 未限定 | 分支约束 | oneOf[2]/allOf[2] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"pattern":"^(?:0\\.[0-9]*[1-9][0-9]*&#124;[1-9][0-9]*(?:\\.[0-9]+)?)$"} |
| response.data.outstanding_items[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"invoice.search.response.schema.json#/$defs/currency"} |
| response.data.outstanding_items[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.outstanding_items[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","payment_state","company_id","currency","company_currency","amount_total","amount_residual","receivable_payable_lines","reconciliations","payments","outstanding_items"],"resolved_ref":"#/$defs/data"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["out_invoice","out_refund","in_invoice","in_refund"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.payment_state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy"]} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"invoice.search.response.schema.json#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.company_currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"invoice.search.response.schema.json#/$defs/currency"} |
| response.data.company_currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.amount_residual | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.receivable_payable_lines | array | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.receivable_payable_lines[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","account","date_maturity","balance","amount_currency","amount_residual","amount_residual_currency","currency","reconciled","matching_number"],"resolved_ref":"#/$defs/receivable_payable_line"} |
| response.data.receivable_payable_lines[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.receivable_payable_lines[].account | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name","account_type"],"resolved_ref":"#/$defs/account"} |
| response.data.receivable_payable_lines[].account.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.receivable_payable_lines[].account.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.receivable_payable_lines[].account.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.receivable_payable_lines[].account.account_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["asset_receivable","liability_payable"]} |
| response.data.receivable_payable_lines[].date_maturity | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.receivable_payable_lines[].balance | string | 必填（所在对象出现时） | allOf[1]/then | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.receivable_payable_lines[].amount_currency | string | 必填（所在对象出现时） | allOf[1]/then | 外币/交易币数值，非默认公司币金额 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.receivable_payable_lines[].amount_residual | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.receivable_payable_lines[].amount_residual_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.receivable_payable_lines[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"invoice.search.response.schema.json#/$defs/currency"} |
| response.data.receivable_payable_lines[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.receivable_payable_lines[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.receivable_payable_lines[].reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.receivable_payable_lines[].matching_number | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.reconciliations | array | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.reconciliations[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","date","amount","company_amount","currency","company_currency","invoice_line_id","counterpart_line_id","counterpart_move","payment_id","exchange_move_id"],"resolved_ref":"#/$defs/reconciliation"} |
| response.data.reconciliations[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.reconciliations[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.reconciliations[].amount | string | 必填（所在对象出现时） | allOf[1]/then | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.reconciliations[].company_amount | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.reconciliations[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"invoice.search.response.schema.json#/$defs/currency"} |
| response.data.reconciliations[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.reconciliations[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.reconciliations[].company_currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"invoice.search.response.schema.json#/$defs/currency"} |
| response.data.reconciliations[].company_currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.reconciliations[].company_currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.reconciliations[].invoice_line_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.reconciliations[].counterpart_line_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.reconciliations[].counterpart_move | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","date"],"resolved_ref":"#/$defs/counterpart_move"} |
| response.data.reconciliations[].counterpart_move.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.reconciliations[].counterpart_move.name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.reconciliations[].counterpart_move.move_type | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.reconciliations[].counterpart_move.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.reconciliations[].counterpart_move.date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.reconciliations[].payment_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 付款/收款记录ID | {"minimum":1} |
| response.data.reconciliations[].exchange_move_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.payments | array | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.payments[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","state","date","payment_type","partner_type","amount","currency","journal","payment_method","move_id","is_reconciled","is_matched"],"resolved_ref":"#/$defs/payment"} |
| response.data.payments[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.payments[].name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.payments[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","in_process","paid","canceled","rejected"]} |
| response.data.payments[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.payments[].payment_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["inbound","outbound"]} |
| response.data.payments[].partner_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["customer","supplier"]} |
| response.data.payments[].amount | string | 必填（所在对象出现时） | allOf[1]/then | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.payments[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"invoice.search.response.schema.json#/$defs/currency"} |
| response.data.payments[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.payments[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.payments[].journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"invoice.search.response.schema.json#/$defs/journal"} |
| response.data.payments[].journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.payments[].journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":5,"minLength":1} |
| response.data.payments[].journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.payments[].payment_method | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/payment_method"} |
| response.data.payments[].payment_method.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.payments[].payment_method.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.payments[].payment_method.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.payments[].move_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 会计单据记录ID | {"minimum":1} |
| response.data.payments[].is_reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.payments[].is_matched | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.outstanding_items | array | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.outstanding_items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["line_id","move_id","payment_id","date","label","amount","currency"],"resolved_ref":"#/$defs/outstanding_item"} |
| response.data.outstanding_items[].line_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.outstanding_items[].move_id | integer | 必填（所在对象出现时） | allOf[1]/then | 会计单据记录ID | {"minimum":1} |
| response.data.outstanding_items[].payment_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 付款/收款记录ID | {"minimum":1} |
| response.data.outstanding_items[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.outstanding_items[].label | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.outstanding_items[].amount | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"allOf":[{"$ref":"invoice.search.response.schema.json#/$defs/money"},{"pattern":"^(?:0\\.[0-9]*[1-9][0-9]*&#124;[1-9][0-9]*(?:\\.[0-9]+)?)$"}]} |
| response.data.outstanding_items[].amount | string | 分支约束 | allOf[1]/then/allOf[1] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"invoice.search.response.schema.json#/$defs/money"} |
| response.data.outstanding_items[].amount | 未限定 | 分支约束 | allOf[1]/then/allOf[2] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"pattern":"^(?:0\\.[0-9]*[1-9][0-9]*&#124;[1-9][0-9]*(?:\\.[0-9]+)?)$"} |
| response.data.outstanding_items[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"invoice.search.response.schema.json#/$defs/currency"} |
| response.data.outstanding_items[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.outstanding_items[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
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
- `execute`：fixed_invoice_payment_graph_and_outstanding_read
- `verify`：same_transaction_outstanding_and_reconciliation_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request, response, bridge, fixed Odoo runtime, and control-CLI contracts.；引用：tests/unit/test_invoices.py, tests/unit/test_invoice_bridge.py, tests/unit/test_invoice_runtime.py, tests/unit/test_invoice_cli.py
- `integration`：`implemented`；The shared dual-database rollback smoke covers outstanding items and applied or undone partials.；引用：tests/integration/test_invoices_live.py, tests/integration/test_accounting_depth_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_item-date_maturity-update"></a>

## journal_item.date_maturity.update — 修改分录行到期日

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Fixed line-targeted operations are implemented; native accounting, reference and analytic synchronization ACLs apply. Runtime context and native acceptance are not an unrestricted permission claim.
- 内部domain：`journal_item`；来源模型：account.account, account.move, account.move.line, res.company；向导：无。
- 必需模块：account, analytic, product, uom；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.account:read, account.move.line:read, account.move.line:write, account.move:read, res.company:read。
- 请求/响应合同：`schemas/v1/journal_item.date_maturity.update.request.schema.json` / `schemas/v1/journal_item.date_maturity.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run journal_item.date_maturity.update --request "@request.json" --idempotency-key "journal_item.date_maturity.update:1:3e0fa9178458e321f8fa31b6c9cd7218" --confirm "journal_item.date_maturity.update"
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
    "date_maturity": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id","line_id","date_maturity"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.date_maturity | string/null | 必填（所在对象出现时） |  |  | {"format":"date"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal_item.date_maturity.update"} |
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

<a id="cap-payable-open_items-list"></a>

## payable.open_items.list — 列出应付未清项

- 类型：只读；静态状态：`unconfigured`；handler：`payable_open_items_list`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`receivables_payables`；来源模型：account.move.line, account.move, account.account, account.journal, res.partner, res.currency；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move.line:read, account.move:read, account.account:read, account.journal:read, res.partner:read, res.currency:read。
- 请求/响应合同：`schemas/v1/payable.open_items.list.request.schema.json` / `schemas/v1/payable.open_items.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read payable.open_items.list --request "@request.json"
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
| parameters.due_date_from | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"default":null,"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| parameters.due_date_from | null | 分支约束 | oneOf[1] |  |  |
| parameters.due_date_from | string | 分支约束 | oneOf[2] |  | {"format":"date"} |
| parameters.due_date_to | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"default":null,"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| parameters.due_date_to | null | 分支约束 | oneOf[1] |  |  |
| parameters.due_date_to | string | 分支约束 | oneOf[2] |  | {"format":"date"} |
| parameters.partner_id | integer/null | 可选（可能有条件限制） |  | 合作伙伴ID | {"default":null,"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.account_id | integer/null | 可选（可能有条件限制） |  | 会计科目ID | {"default":null,"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.journal_id | integer/null | 可选（可能有条件限制） |  | 日记账ID | {"default":null,"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.currency_id | integer/null | 可选（可能有条件限制） |  | 币种ID | {"default":null,"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.move_id | integer | 可选（可能有条件限制） |  | 会计单据记录ID | {"minimum":1} |
| parameters.invoice_user_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.payment_term_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.fiscal_position_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.move_types | array | 可选（可能有条件限制） |  |  | {"maxItems":7,"minItems":1,"uniqueItems":true} |
| parameters.move_types[] | 未限定 | 每个数组元素 |  |  | {"enum":["entry","out_invoice","out_refund","in_invoice","in_refund","out_receipt","in_receipt"]} |
| parameters.query | 组合/开放结构 | 可选（可能有条件限制） |  | 搜索文本 | {"default":null,"oneOf":[{"type":"null"},{"allOf":[{"not":{"pattern":"^\\s"}},{"not":{"pattern":"\\s$"}}],"maxLength":200,"minLength":1,"type":"string"}]} |
| parameters.query | null | 分支约束 | oneOf[1] | 搜索文本 |  |
| parameters.query | string | 分支约束 | oneOf[2] | 搜索文本 | {"allOf":[{"not":{"pattern":"^\\s"}},{"not":{"pattern":"\\s$"}}],"maxLength":200,"minLength":1} |
| parameters.query | 组合/开放结构 | 分支约束 | oneOf[2]/allOf[1] | 搜索文本 | {"not":{"pattern":"^\\s"}} |
| parameters.query | 组合/开放结构 | 分支约束 | oneOf[2]/allOf[2] | 搜索文本 | {"not":{"pattern":"\\s$"}} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payable.open_items.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","side","date","due_date","name","ref","move","journal","company_id","partner","account","currency","company_currency","debit","credit","balance","amount_currency","amount_residual","amount_residual_currency","reconciled","matching_number"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].side | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":"payable"} |
| response.data.items[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].due_date | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}]} |
| response.data.items[].due_date | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].due_date | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.items[].name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].name | null | 分支约束 | oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].name | string | 分支约束 | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].ref | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].ref | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].ref | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.items[].move | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state"],"resolved_ref":"#/$defs/move"} |
| response.data.items[].move.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].move.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].move.move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["entry","out_invoice","out_refund","in_invoice","in_refund","out_receipt","in_receipt"]} |
| response.data.items[].move.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"const":"posted"} |
| response.data.items[].journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/journal"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":5,"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.items[].partner | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","reference"],"resolved_ref":"#/$defs/partner"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].partner.name | null | 分支约束 | oneOf[2]/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].partner.name | string | 分支约束 | oneOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].partner.reference | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].partner.reference | null | 分支约束 | oneOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.items[].partner.reference | string | 分支约束 | oneOf[2]/oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.items[].account | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name","account_type","non_trade"],"resolved_ref":"#/$defs/account"} |
| response.data.items[].account.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].account.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].account.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].account.account_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":"liability_payable"} |
| response.data.items[].account.non_trade | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].company_currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].company_currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].debit | string | 必填（所在对象出现时） | oneOf[2] | 借方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].credit | string | 必填（所在对象出现时） | oneOf[2] | 贷方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].balance | string | 必填（所在对象出现时） | oneOf[2] | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_currency | string | 必填（所在对象出现时） | oneOf[2] | 外币/交易币数值，非默认公司币金额 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_residual | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_residual_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].reconciled | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":false} |
| response.data.items[].matching_number | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].matching_number | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].matching_number | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","side","date","due_date","name","ref","move","journal","company_id","partner","account","currency","company_currency","debit","credit","balance","amount_currency","amount_residual","amount_residual_currency","reconciled","matching_number"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].side | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"const":"payable"} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].due_date | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}]} |
| response.data.items[].due_date | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].due_date | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date"} |
| response.data.items[].name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].name | null | 分支约束 | allOf[1]/then/oneOf[1] | 名称/行说明 |  |
| response.data.items[].name | string | 分支约束 | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].ref | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].ref | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].ref | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.items[].move | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state"],"resolved_ref":"#/$defs/move"} |
| response.data.items[].move.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].move.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].move.move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["entry","out_invoice","out_refund","in_invoice","in_refund","out_receipt","in_receipt"]} |
| response.data.items[].move.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"const":"posted"} |
| response.data.items[].journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/journal"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":5,"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.items[].partner | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","reference"],"resolved_ref":"#/$defs/partner"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].partner.name | null | 分支约束 | allOf[1]/then/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].partner.name | string | 分支约束 | allOf[1]/then/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].partner.reference | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].partner.reference | null | 分支约束 | allOf[1]/then/oneOf[2]/oneOf[1] |  |  |
| response.data.items[].partner.reference | string | 分支约束 | allOf[1]/then/oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.items[].account | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name","account_type","non_trade"],"resolved_ref":"#/$defs/account"} |
| response.data.items[].account.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].account.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].account.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].account.account_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"const":"liability_payable"} |
| response.data.items[].account.non_trade | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].company_currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].company_currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].debit | string | 必填（所在对象出现时） | allOf[1]/then | 借方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].credit | string | 必填（所在对象出现时） | allOf[1]/then | 贷方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].balance | string | 必填（所在对象出现时） | allOf[1]/then | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_currency | string | 必填（所在对象出现时） | allOf[1]/then | 外币/交易币数值，非默认公司币金额 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_residual | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_residual_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].reconciled | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"const":false} |
| response.data.items[].matching_number | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].matching_number | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].matching_number | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
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

- `unit`：`implemented`；Existing contracts and optional native same-line/header search filters covered.；引用：tests/unit/test_open_items.py, tests/unit/test_open_items_bridge.py, tests/unit/test_open_items_cli.py, tests/unit/test_open_items_runtime.py, tests/unit/test_document_search_batch_contract.py, tests/unit/test_document_search_batch_runtime.py, tests/unit/test_document_search_header_runtime.py, tests/unit/test_document_search_batch_cli.py, tests/unit/test_invoice_business_line_filters_contract.py, tests/unit/test_document_business_filters_runtime.py, tests/unit/test_business_line_search_remove_cli.py
- `integration`：`implemented`；Shared native business-line search and bulk deletion smoke passed; full rollback.；引用：tests/integration/test_open_items_live.py, tests/integration/test_document_search_bulk_lines_live.py, tests/integration/test_business_line_search_remove_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payable-payment-register"></a>

## payable.payment.register — 登记供应商账单付款（支持多账单合并）或供应商退款收款

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime. Explicit installment/group options use native next/overdue/before-date/full amounts and actual payment graphs; editable grouped batches support partial amounts. Operation markers distinguish sequential rounds but are not concurrency-unique.
- 内部domain：`payments`；来源模型：res.company, account.account, account.journal, account.move, account.move.line, account.payment, account.payment.register, account.partial.reconcile, account.full.reconcile, account.payment.method.line, res.partner.bank；向导：account.payment.register。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.account:read, account.journal:read, account.move:read, account.move.line:read, account.payment:read, account.payment:create, account.payment.register:create, account.move.line:write, account.partial.reconcile:read, account.partial.reconcile:create, account.full.reconcile:read, account.payment.method.line:read, res.partner.bank:read。
- 请求/响应合同：`schemas/v1/payable.payment.register.request.schema.json` / `schemas/v1/payable.payment.register.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payable.payment.register --request "@request.json" --idempotency-key "payable.payment.register:1" --confirm "payable.payment.register"
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
    "journal_id": 1,
    "payment_date": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"installment_cutoff_date":false}},"if":{"properties":{"installments_mode":{"const":"before_date"}},"required":["installments_mode"]},"then":{"required":["installment_cutoff_date"]}},{"if":{"properties":{"group_payment":{"const":false}},"required":["group_payment"]},"then":{"properties":{"amount":false}}}],"else":{"properties":{"writeoff_account_id":false,"writeoff_label":false}},"if":{"properties":{"payment_difference_handling":{"const":"reconcile"}},"required":["payment_difference_handling"]},"oneOf":[{"properties":{"move_ids":false},"required":["move_id"]},{"properties":{"move_id":false},"required":["move_ids"]}],"required_in_object":["journal_id","payment_date"],"then":{"required":["amount","writeoff_account_id"]}} |
| parameters.move_id | integer | 可选（可能有条件限制） |  | 会计单据记录ID | {"minimum":1} |
| parameters.move_ids | array | 可选（可能有条件限制） |  | 会计单据ID数组 | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| parameters.move_ids[] | integer | 每个数组元素 |  | 会计单据ID数组 | {"minimum":1} |
| parameters.journal_id | integer | 必填（所在对象出现时） |  | 日记账ID | {"minimum":1} |
| parameters.payment_method_line_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.partner_bank_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.payment_date | string | 必填（所在对象出现时） |  |  | {"format":"date"} |
| parameters.installments_mode | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["full","next","overdue","before_date"]} |
| parameters.group_payment | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.installment_cutoff_date | string | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.amount | string | 可选（可能有条件限制） |  | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/positive_canonical_decimal"} |
| parameters.payment_difference_handling | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["open","reconcile"]} |
| parameters.writeoff_account_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.writeoff_label | string | 可选（可能有条件限制） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |
| parameters | 未限定 | 分支约束 | oneOf[1] |  | {"required_in_object":["move_id"]} |
| parameters.move_ids | 禁止 | 可选（可能有条件限制） | oneOf[1] |  | false |
| parameters | 未限定 | 分支约束 | oneOf[2] |  | {"required_in_object":["move_ids"]} |
| parameters.move_id | 禁止 | 可选（可能有条件限制） | oneOf[2] |  | false |
| parameters | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"installment_cutoff_date":false}},"if":{"properties":{"installments_mode":{"const":"before_date"}},"required":["installments_mode"]},"then":{"required":["installment_cutoff_date"]}} |
| parameters | 未限定 | 条件分支 | allOf[1]/then |  | {"required_in_object":["installment_cutoff_date"]} |
| parameters | 未限定 | 条件分支 | allOf[1]/else |  |  |
| parameters.installment_cutoff_date | 禁止 | 可选（可能有条件限制） | allOf[1]/else |  | false |
| parameters | 组合/开放结构 | 分支约束 | allOf[2] |  | {"if":{"properties":{"group_payment":{"const":false}},"required":["group_payment"]},"then":{"properties":{"amount":false}}} |
| parameters | 未限定 | 条件分支 | allOf[2]/then |  |  |
| parameters.amount | 禁止 | 可选（可能有条件限制） | allOf[2]/then |  | false |
| parameters | 未限定 | 条件分支 | then |  | {"required_in_object":["amount","writeoff_account_id"]} |
| parameters | 未限定 | 条件分支 | else |  |  |
| parameters.writeoff_account_id | 禁止 | 可选（可能有条件限制） | else |  | false |
| parameters.writeoff_label | 禁止 | 可选（可能有条件限制） | else |  | false |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"#/$defs/payment_batch"}]},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payable.payment.register"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"},{"$ref":"#/$defs/payment_batch"}]} |
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
| response.data | object | 分支约束 | oneOf[3] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"#/$defs/payment_batch"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | oneOf[3] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | oneOf[3] |  | {"additionalProperties":false,"required_in_object":["items","processed_count"]} |
| response.data.result.items | array | 必填（所在对象出现时） | oneOf[3] |  | {"maxItems":1000,"minItems":1,"uniqueItems":true} |
| response.data.result.items[] | 组合/开放结构 | 每个数组元素 | oneOf[3] |  | {"allOf":[{"$ref":"core-write-result.schema.json#/properties/result"},{"properties":{"id":{"minimum":1,"type":"integer"},"model":{"const":"account.payment"},"move_type":{"type":"null"}}}]} |
| response.data.result.items[] | object | 分支约束 | oneOf[3]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"],"resolved_ref":"core-write-result.schema.json#/properties/result"} |
| response.data.result.items[].model | string | 必填（所在对象出现时） | oneOf[3]/allOf[1] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].id | integer/null | 必填（所在对象出现时） | oneOf[3]/allOf[1] |  | {"minimum":1} |
| response.data.result.items[].name | string/null | 必填（所在对象出现时） | oneOf[3]/allOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.result.items[].state | string | 必填（所在对象出现时） | oneOf[3]/allOf[1] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].company_id | integer | 必填（所在对象出现时） | oneOf[3]/allOf[1] | 所选公司ID | {"minimum":1} |
| response.data.result.items[].move_type | string/null | 必填（所在对象出现时） | oneOf[3]/allOf[1] |  | {"minLength":1} |
| response.data.result.items[].source_id | integer/null | 必填（所在对象出现时） | oneOf[3]/allOf[1] |  | {"minimum":1} |
| response.data.result.items[].line_ids | array | 必填（所在对象出现时） | oneOf[3]/allOf[1] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.items[].line_ids[] | integer | 每个数组元素 | oneOf[3]/allOf[1] | 行记录ID数组 | {"minimum":1} |
| response.data.result.items[].partial_reconcile_ids | array | 必填（所在对象出现时） | oneOf[3]/allOf[1] |  | {"uniqueItems":true} |
| response.data.result.items[].partial_reconcile_ids[] | integer | 每个数组元素 | oneOf[3]/allOf[1] |  | {"minimum":1} |
| response.data.result.items[].full_reconcile_id | integer/null | 必填（所在对象出现时） | oneOf[3]/allOf[1] | 完整核销关系ID | {"minimum":1} |
| response.data.result.items[].reconciled | boolean | 必填（所在对象出现时） | oneOf[3]/allOf[1] |  |  |
| response.data.result.items[] | 未限定 | 分支约束 | oneOf[3]/allOf[2] |  |  |
| response.data.result.items[].model | 未限定 | 可选（可能有条件限制） | oneOf[3]/allOf[2] |  | {"const":"account.payment"} |
| response.data.result.items[].id | integer | 可选（可能有条件限制） | oneOf[3]/allOf[2] |  | {"minimum":1} |
| response.data.result.items[].move_type | null | 可选（可能有条件限制） | oneOf[3]/allOf[2] |  |  |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | oneOf[3] |  | {"maximum":1000,"minimum":1} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"#/$defs/payment_batch"}]},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then |  | {"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"#/$defs/payment_batch"}]} |
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
| response.data | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"#/$defs/payment_batch"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","processed_count"]} |
| response.data.result.items | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"maxItems":1000,"minItems":1,"uniqueItems":true} |
| response.data.result.items[] | 组合/开放结构 | 每个数组元素 | allOf[1]/then/oneOf[2] |  | {"allOf":[{"$ref":"core-write-result.schema.json#/properties/result"},{"properties":{"id":{"minimum":1,"type":"integer"},"model":{"const":"account.payment"},"move_type":{"type":"null"}}}]} |
| response.data.result.items[] | object | 分支约束 | allOf[1]/then/oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"],"resolved_ref":"core-write-result.schema.json#/properties/result"} |
| response.data.result.items[].model | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] |  | {"minimum":1} |
| response.data.result.items[].name | string/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.result.items[].state | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] | 所选公司ID | {"minimum":1} |
| response.data.result.items[].move_type | string/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] |  | {"minLength":1} |
| response.data.result.items[].source_id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] |  | {"minimum":1} |
| response.data.result.items[].line_ids | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.items[].line_ids[] | integer | 每个数组元素 | allOf[1]/then/oneOf[2]/allOf[1] | 行记录ID数组 | {"minimum":1} |
| response.data.result.items[].partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] |  | {"uniqueItems":true} |
| response.data.result.items[].partial_reconcile_ids[] | integer | 每个数组元素 | allOf[1]/then/oneOf[2]/allOf[1] |  | {"minimum":1} |
| response.data.result.items[].full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] | 完整核销关系ID | {"minimum":1} |
| response.data.result.items[].reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] |  |  |
| response.data.result.items[] | 未限定 | 分支约束 | allOf[1]/then/oneOf[2]/allOf[2] |  |  |
| response.data.result.items[].model | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[2]/allOf[2] |  | {"const":"account.payment"} |
| response.data.result.items[].id | integer | 可选（可能有条件限制） | allOf[1]/then/oneOf[2]/allOf[2] |  | {"minimum":1} |
| response.data.result.items[].move_type | null | 可选（可能有条件限制） | allOf[1]/then/oneOf[2]/allOf[2] |  |  |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"maximum":1000,"minimum":1} |
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
- `execute`：fixed_single_or_full_grouped_invoice_payment_registration_as_configured_business_user
- `verify`：same_transaction_single_or_grouped_residual_and_replay_validation
- `idempotency`：single_document_legacy_key_or_company_and_normalized_batch_digest_with_odoo_persisted_business_marker_and_result_replay
- `reverse`：payment.cancel

### 已登记测试与证据范围

- `unit`：`implemented`；Existing contracts and explicit payment/tax input extensions are covered.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_payment_register_writeoff_runtime.py, tests/unit/test_payment_register_many_contract.py, tests/unit/test_payment_register_many_runtime.py, tests/unit/test_core_write_cli.py, tests/unit/test_accounting_payment_tax_inputs_batch.py, tests/unit/test_entry_payment_explicit_inputs_contract.py, tests/unit/test_payment_tax_input_runtime.py, tests/unit/test_invoice_rounds_write_contract.py, tests/unit/test_invoice_rounds_runtime.py, tests/unit/test_invoice_rounds_product_reads.py, tests/unit/test_invoice_rounds_cli.py
- `integration`：`implemented`；Shared native payment/tax smoke passed; full rollback.；引用：tests/integration/test_core_write_batch_live.py, tests/integration/test_accounting_depth_batch_live.py, tests/integration/test_invoice_cash_refund_batch_live.py, tests/integration/test_payment_register_many_batch_live.py, tests/integration/test_accounting_payment_tax_inputs_batch_live.py, tests/integration/test_invoice_rounds_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-bank_account-assign"></a>

## payment.bank_account.assign — 指定付款银行账户

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured caller/company and native ACLs. Bank assignment uses native eligible recipient/company accounts without changing trust. Accounting destination changes require draft payment and entry. Sent-status actions require in-process manual method. Manual validation is only for no-entry payments; journal-backed settlement uses reconciliation. Rejection requires in-process sent payment. Native duplicate warnings are candidates, not proof of duplication; they may include different currencies. No external transfer, bank submission, receipt send or caller-sudo.
- 内部domain：`payments`；来源模型：account.move, account.move.line, account.payment, res.company, res.partner.bank；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.move.line:create, account.move.line:read, account.move.line:unlink, account.move.line:write, account.move:read, account.move:write, account.payment:read, account.payment:write, res.company:read, res.partner.bank:read。
- 请求/响应合同：`schemas/v1/payment.bank_account.assign.request.schema.json` / `schemas/v1/payment.bank_account.assign.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment.bank_account.assign --request "@request.json" --idempotency-key "payment.bank_account.assign:1:67fbbd6b7368ea491e2540eae10e16a4" --confirm "payment.bank_account.assign"
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
    "partner_bank_id": 1,
    "payment_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["partner_bank_id","payment_id"]} |
| parameters.payment_id | integer | 必填（所在对象出现时） |  | 付款/收款记录ID | {"minimum":1} |
| parameters.partner_bank_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment.bank_account.assign"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment.bank_account.assign"} |
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
- `execute`：fixed_native_payment_fields_or_state_action
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：native_desired_payload_or_state_recheck
- `reverse`：native_previous_assignment_or_existing_payment_reset_subject_to_acl_and_state

### 已登记测试与证据范围

- `unit`：`implemented`；Closed schemas, fixed CLI/ORM dispatch, native eligibility and state boundaries, deterministic keys and read/write scope.；引用：tests/unit/test_payment_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all eight new IDs, three existing setup/recovery IDs and eleven immediate replays; native recipient/company bank eligibility, scoped keyset duplicate warnings, unchanged bank trust, actual destination account in the posted balanced entry, native sent/unset and rejected/reset lifecycle, truthful posted bank change without rewriting its entry, and native no-entry validation. Invalid state, journal-backed validation, foreign company and ineligible bank denied; fresh-cursor business-data and temporary-group rollback verified. No bank/provider submission, external receipt delivery, addon or service changes.；引用：tests/integration/test_payment_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-bank_account_candidates-list"></a>

## payment.bank_account_candidates.list — 查询付款可选银行账户

- 类型：只读；静态状态：`unconfigured`；handler：`payment_bank_account_candidates_list`。
- 状态原因：`runtime_context_required` — Requires configured caller/company and native ACLs. Bank assignment uses native eligible recipient/company accounts without changing trust. Accounting destination changes require draft payment and entry. Sent-status actions require in-process manual method. Manual validation is only for no-entry payments; journal-backed settlement uses reconciliation. Rejection requires in-process sent payment. Native duplicate warnings are candidates, not proof of duplication; they may include different currencies. No external transfer, bank submission, receipt send or caller-sudo.
- 内部domain：`payments`；来源模型：res.company, account.payment, res.partner.bank；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.payment:read, res.partner.bank:read。
- 请求/响应合同：`schemas/v1/payment.bank_account_candidates.list.request.schema.json` / `schemas/v1/payment.bank_account_candidates.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read payment.bank_account_candidates.list --request "@request.json"
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
    "payment_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_id"]} |
| parameters.payment_id | integer | 必填（所在对象出现时） |  | 付款/收款记录ID | {"minimum":1} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payment.bank_account_candidates.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["acc_number","active","allow_out_payment","bank_id","company_id","currency_id","id","partner_id","payment_id"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].payment_id | integer | 必填（所在对象出现时） | oneOf[2] | 付款/收款记录ID | {"minimum":1} |
| response.data.items[].company_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].partner_id | integer | 必填（所在对象出现时） | oneOf[2] | 合作伙伴ID | {"minimum":1} |
| response.data.items[].acc_number | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].bank_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].currency_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 币种ID | {"minimum":1} |
| response.data.items[].active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].allow_out_payment | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["acc_number","active","allow_out_payment","bank_id","company_id","currency_id","id","partner_id","payment_id"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].payment_id | integer | 必填（所在对象出现时） | allOf[1]/then | 付款/收款记录ID | {"minimum":1} |
| response.data.items[].company_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].partner_id | integer | 必填（所在对象出现时） | allOf[1]/then | 合作伙伴ID | {"minimum":1} |
| response.data.items[].acc_number | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].bank_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].currency_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 币种ID | {"minimum":1} |
| response.data.items[].active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].allow_out_payment | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
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
- `execute`：fixed_native_payment_read
- `verify`：closed_response_schema_validation
- `idempotency`：read_only
- `reverse`：not_applicable

### 已登记测试与证据范围

- `unit`：`implemented`；Closed schemas, fixed CLI/ORM dispatch, native eligibility and state boundaries, deterministic keys and read/write scope.；引用：tests/unit/test_payment_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all eight new IDs, three existing setup/recovery IDs and eleven immediate replays; native recipient/company bank eligibility, scoped keyset duplicate warnings, unchanged bank trust, actual destination account in the posted balanced entry, native sent/unset and rejected/reset lifecycle, truthful posted bank change without rewriting its entry, and native no-entry validation. Invalid state, journal-backed validation, foreign company and ineligible bank denied; fresh-cursor business-data and temporary-group rollback verified. No bank/provider submission, external receipt delivery, addon or service changes.；引用：tests/integration/test_payment_processing_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-cancel"></a>

## payment.cancel — 原子取消并补偿单笔或 2–100 笔会计付款

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`payments`；来源模型：res.company, account.move, account.payment；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.payment:read, account.payment:write, account.move:read。
- 请求/响应合同：`schemas/v1/payment.cancel.request.schema.json` / `schemas/v1/payment.cancel.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment.cancel --request "@request.json" --idempotency-key "payment.cancel:1" --confirm "payment.cancel"
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
    "payment_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"oneOf":[{"required":["payment_id"]},{"required":["payment_ids"]}]} |
| parameters.payment_id | integer | 可选（可能有条件限制） |  | 付款/收款记录ID | {"minimum":1} |
| parameters.payment_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| parameters.payment_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters | 未限定 | 分支约束 | oneOf[1] |  | {"required_in_object":["payment_id"]} |
| parameters | 未限定 | 分支约束 | oneOf[2] |  | {"required_in_object":["payment_ids"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payment.cancel"} |
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
- `execute`：full_batch_record_scope_company_payment_type_and_state_preflight_then_single_transaction_all_or_nothing_native_cancel
- `verify`：explicit_batch_result_with_exact_normalized_record_ids_target_states_same_transaction_reread_and_response_schema_validation
- `idempotency`：capability_company_and_full_normalized_sorted_record_id_set_key_with_serial_target_state_replay
- `reverse`：register_a_new_correcting_payment

### 已登记测试与证据范围

- `unit`：`implemented`；The existing unit tests continue to cover the singular request and native runtime behavior; the batch contract unit test covers batch-request normalization, full normalized-ID-set idempotency keys, bridge and capability contracts, explicit batch results, and CLI verification.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_core_write_cli.py, tests/unit/test_lifecycle_batch_contract.py
- `integration`：`implemented`；The existing integration smoke continues to cover singular native execution; the new live smoke covers dual-database batch execution, immediate replay, and rollback, plus a representative whole-batch invalid-ID no-op for invoice.post.；引用：tests/integration/test_core_write_batch_live.py, tests/integration/test_batch_lifecycle_write_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-create"></a>

## payment.create — 创建草稿会计付款

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`payments`；来源模型：res.company, res.partner, res.currency, account.journal, account.account, account.payment.method, account.payment.method.line, account.payment, account.move, account.move.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：res.partner:read, res.currency:read, account.journal:read, account.account:read, account.payment.method:read, account.payment.method.line:read, account.payment:read, account.payment:create, account.move:read, account.move:create, account.move.line:read, account.move.line:create。
- 请求/响应合同：`schemas/v1/payment.create.request.schema.json` / `schemas/v1/payment.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment.create --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "payment.create"
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
    "payment_type": "inbound",
    "partner_type": "customer",
    "partner_id": 1,
    "amount": "1",
    "currency_id": 1,
    "journal_id": 1,
    "payment_method_line_id": 1,
    "date": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_type","partner_type","partner_id","amount","currency_id","journal_id","payment_method_line_id","date"]} |
| parameters.payment_type | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["inbound","outbound"]} |
| parameters.partner_type | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["customer","supplier"]} |
| parameters.partner_id | integer | 必填（所在对象出现时） |  | 合作伙伴ID | {"minimum":1} |
| parameters.amount | string | 必填（所在对象出现时） |  | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^(?=[0-9.]*[1-9])(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/positiveAmount"} |
| parameters.currency_id | integer | 必填（所在对象出现时） |  | 币种ID | {"minimum":1} |
| parameters.journal_id | integer | 必填（所在对象出现时） |  | 日记账ID | {"minimum":1} |
| parameters.payment_method_line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.date | string | 必填（所在对象出现时） |  |  | {"format":"date"} |
| parameters.payment_reference | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"oneOf":[{"type":"null"},{"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| parameters.payment_reference | null | 分支约束 | oneOf[1] |  |  |
| parameters.payment_reference | string | 分支约束 | oneOf[2] |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment.create"} |
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
- `idempotency`：odoo_persisted_business_marker_and_result_replay
- `reverse`：delete_draft_or_payment.cancel_after_posting

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed payment fields, exact confirmation, fixed bridge action, Odoo-side execution, replay, and CLI response contract.；引用：tests/unit/test_payment_bank_writes.py, tests/unit/test_payment_bank_writes_runtime.py, tests/unit/test_payment_bank_write_cli.py
- `integration`：`implemented`；The shared live smoke verifies execution and rollback in both dedicated isolated database aliases.；引用：tests/integration/test_payment_bank_capability_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-delete"></a>

## payment.delete — 删除未核销的草稿或已取消付款

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`deleted_record_tombstone_unavailable` — The handler verifies payment and journal-entry absence after deleting an unreconciled draft or canceled payment, but keeps no persistent tombstone for later retry attribution.
- 内部domain：`payments`；来源模型：res.company, account.payment, account.move, account.move.line, account.partial.reconcile, account.full.reconcile；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.payment:read, account.payment:unlink, account.move:read, account.move:write, account.move:unlink, account.move.line:read, account.partial.reconcile:read, account.full.reconcile:read。
- 请求/响应合同：`schemas/v1/payment.delete.request.schema.json` / `schemas/v1/payment.delete.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment.delete --request "@request.json" --idempotency-key "payment.delete:1" --confirm "payment.delete"
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
    "payment_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_id"]} |
| parameters.payment_id | integer | 必填（所在对象出现时） |  | 付款/收款记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment.delete"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment.delete"} |
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
- `execute`：fixed_company_scoped_unreconciled_draft_or_canceled_payment_unlink
- `verify`：same_transaction_payment_and_journal_entry_absence_and_response_schema_validation
- `idempotency`：record_absence_recheck_without_operation_store_or_persistent_tombstone
- `reverse`：not_reversible_deleted_payment_must_be_recreated

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover confirmation, runtime result contract, CLI dispatch, registry descriptor, deletion boundary, and schemas.；引用：tests/unit/test_bank_statement_payment_maintenance_public.py, tests/unit/test_bank_statement_payment_maintenance_runtime.py, tests/unit/test_core_writes.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases through the public CLI as uid 5 with su=False, exercising all six bank/payment-maintenance commands, three immediate replays, native statement/payment readbacks, and fresh-cursor rollback verification.；引用：tests/integration/test_bank_statement_payment_maintenance_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-destination_account-assign"></a>

## payment.destination_account.assign — 指定草稿付款对方科目

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured caller/company and native ACLs. Bank assignment uses native eligible recipient/company accounts without changing trust. Accounting destination changes require draft payment and entry. Sent-status actions require in-process manual method. Manual validation is only for no-entry payments; journal-backed settlement uses reconciliation. Rejection requires in-process sent payment. Native duplicate warnings are candidates, not proof of duplication; they may include different currencies. No external transfer, bank submission, receipt send or caller-sudo.
- 内部domain：`payments`；来源模型：account.account, account.move, account.move.line, account.payment, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.account:read, account.move.line:create, account.move.line:read, account.move.line:unlink, account.move.line:write, account.move:read, account.move:write, account.payment:read, account.payment:write, res.company:read。
- 请求/响应合同：`schemas/v1/payment.destination_account.assign.request.schema.json` / `schemas/v1/payment.destination_account.assign.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment.destination_account.assign --request "@request.json" --idempotency-key "payment.destination_account.assign:1:c4eb54335279bddaee16a8ffdd87bc8e" --confirm "payment.destination_account.assign"
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
    "account_id": 1,
    "payment_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["account_id","payment_id"]} |
| parameters.payment_id | integer | 必填（所在对象出现时） |  | 付款/收款记录ID | {"minimum":1} |
| parameters.account_id | integer | 必填（所在对象出现时） |  | 会计科目ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment.destination_account.assign"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment.destination_account.assign"} |
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
- `execute`：fixed_native_payment_fields_or_state_action
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：native_desired_payload_or_state_recheck
- `reverse`：native_previous_assignment_or_existing_payment_reset_subject_to_acl_and_state

### 已登记测试与证据范围

- `unit`：`implemented`；Closed schemas, fixed CLI/ORM dispatch, native eligibility and state boundaries, deterministic keys and read/write scope.；引用：tests/unit/test_payment_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all eight new IDs, three existing setup/recovery IDs and eleven immediate replays; native recipient/company bank eligibility, scoped keyset duplicate warnings, unchanged bank trust, actual destination account in the posted balanced entry, native sent/unset and rejected/reset lifecycle, truthful posted bank change without rewriting its entry, and native no-entry validation. Invalid state, journal-backed validation, foreign company and ineligible bank denied; fresh-cursor business-data and temporary-group rollback verified. No bank/provider submission, external receipt delivery, addon or service changes.；引用：tests/integration/test_payment_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-duplicate"></a>

## payment.duplicate — 复制会计付款为新草稿

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`concurrent_idempotency_limit` — The handler preserves the source memo as a visible prefix, appends a stable source-specific marker, and rejects retries after source changes, but Odoo provides no matching uniqueness constraint for concurrent exactly-once duplication.
- 内部domain：`payments`；来源模型：res.company, account.payment, account.move, account.move.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.payment:read, account.payment:create, account.payment:write, account.move:read, account.move:create, account.move.line:read, account.move.line:create。
- 请求/响应合同：`schemas/v1/payment.duplicate.request.schema.json` / `schemas/v1/payment.duplicate.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment.duplicate --request "@request.json" --idempotency-key "payment.duplicate:1" --confirm "payment.duplicate"
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
    "payment_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_id"]} |
| parameters.payment_id | integer | 必填（所在对象出现时） |  | 付款/收款记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment.duplicate"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment.duplicate"} |
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
- `execute`：fixed_company_scoped_payment_copy_as_draft_with_source_memo_prefix
- `verify`：same_transaction_new_draft_payment_source_values_and_appended_marker_reread_and_response_schema_validation
- `idempotency`：stable_source_key_suffix_lookup_and_current_source_memo_recheck_without_concurrent_exactly_once_guarantee
- `reverse`：payment.delete

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the closed request, exact confirmation, stable marker lookup, preserved source memo prefix, source-linked draft result, CLI dispatch, registry descriptor, and schemas.；引用：tests/unit/test_bank_statement_payment_maintenance_public.py, tests/unit/test_bank_statement_payment_maintenance_runtime.py, tests/unit/test_core_writes.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases through the public CLI as uid 5 with su=False, exercising all six bank/payment-maintenance commands, three immediate replays, native statement/payment readbacks, and fresh-cursor rollback verification.；引用：tests/integration/test_bank_statement_payment_maintenance_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-duplicate_candidates-list"></a>

## payment.duplicate_candidates.list — 查询付款重复候选

- 类型：只读；静态状态：`unconfigured`；handler：`payment_duplicate_candidates_list`。
- 状态原因：`runtime_context_required` — Requires configured caller/company and native ACLs. Bank assignment uses native eligible recipient/company accounts without changing trust. Accounting destination changes require draft payment and entry. Sent-status actions require in-process manual method. Manual validation is only for no-entry payments; journal-backed settlement uses reconciliation. Rejection requires in-process sent payment. Native duplicate warnings are candidates, not proof of duplication; they may include different currencies. No external transfer, bank submission, receipt send or caller-sudo.
- 内部domain：`payments`；来源模型：res.company, account.payment；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.payment:read。
- 请求/响应合同：`schemas/v1/payment.duplicate_candidates.list.request.schema.json` / `schemas/v1/payment.duplicate_candidates.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read payment.duplicate_candidates.list --request "@request.json"
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
    "payment_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_id"]} |
| parameters.payment_id | integer | 必填（所在对象出现时） |  | 付款/收款记录ID | {"minimum":1} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payment.duplicate_candidates.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["amount","company_id","currency_id","date","id","name","partner_id","partner_type","payment_id","payment_type","state"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 |  |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["canceled","draft","in_process","paid","rejected"]} |
| response.data.items[].payment_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["inbound","outbound"]} |
| response.data.items[].partner_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["customer","supplier"]} |
| response.data.items[].partner_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 合作伙伴ID | {"minimum":1} |
| response.data.items[].payment_id | integer | 必填（所在对象出现时） | oneOf[2] | 付款/收款记录ID | {"minimum":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].currency_id | integer | 必填（所在对象出现时） | oneOf[2] | 币种ID | {"minimum":1} |
| response.data.items[].amount | string | 必填（所在对象出现时） | oneOf[2] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["amount","company_id","currency_id","date","id","name","partner_id","partner_type","payment_id","payment_type","state"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 |  |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["canceled","draft","in_process","paid","rejected"]} |
| response.data.items[].payment_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["inbound","outbound"]} |
| response.data.items[].partner_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["customer","supplier"]} |
| response.data.items[].partner_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 合作伙伴ID | {"minimum":1} |
| response.data.items[].payment_id | integer | 必填（所在对象出现时） | allOf[1]/then | 付款/收款记录ID | {"minimum":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].currency_id | integer | 必填（所在对象出现时） | allOf[1]/then | 币种ID | {"minimum":1} |
| response.data.items[].amount | string | 必填（所在对象出现时） | allOf[1]/then | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
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
- `execute`：fixed_native_payment_read
- `verify`：closed_response_schema_validation
- `idempotency`：read_only
- `reverse`：not_applicable

### 已登记测试与证据范围

- `unit`：`implemented`；Closed schemas, fixed CLI/ORM dispatch, native eligibility and state boundaries, deterministic keys and read/write scope.；引用：tests/unit/test_payment_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all eight new IDs, three existing setup/recovery IDs and eleven immediate replays; native recipient/company bank eligibility, scoped keyset duplicate warnings, unchanged bank trust, actual destination account in the posted balanced entry, native sent/unset and rejected/reset lifecycle, truthful posted bank change without rewriting its entry, and native no-entry validation. Invalid state, journal-backed validation, foreign company and ineligible bank denied; fresh-cursor business-data and temporary-group rollback verified. No bank/provider submission, external receipt delivery, addon or service changes.；引用：tests/integration/test_payment_processing_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-get"></a>

## payment.get — 读取付款及关联单据

- 类型：只读；静态状态：`unconfigured`；handler：`payment_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`payments`；来源模型：res.company, account.payment, account.payment.method, account.payment.method.line, res.currency, res.partner, account.journal, account.move, account.move.line, account.account, account.partial.reconcile, account.bank.statement.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.payment:read, account.payment.method:read, account.payment.method.line:read, res.currency:read, res.partner:read, account.journal:read, account.move:read, account.move.line:read, account.account:read, account.partial.reconcile:read, account.bank.statement.line:read。
- 请求/响应合同：`schemas/v1/payment.get.request.schema.json` / `schemas/v1/payment.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read payment.get --request "@request.json"
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
    "payment_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_id"]} |
| parameters.payment_id | integer | 必填（所在对象出现时） |  | 付款/收款记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payment.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","date","state","payment_type","partner_type","amount","amount_signed","amount_company_currency_signed","currency","company_currency","company_id","partner","journal","memo","payment_reference","payment_method_line","payment_method","move_id","is_reconciled","is_matched","journal_entry","invoice_ids","reconciled_invoices","reconciled_bills","reconciled_bank_transactions"],"resolved_ref":"#/$defs/data"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"payment.search.response.schema.json#/$defs/nullableText"} |
| response.data.name | null | 分支约束 | oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.name | string | 分支约束 | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","in_process","paid","canceled","rejected"]} |
| response.data.payment_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["inbound","outbound"]} |
| response.data.partner_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["customer","supplier"]} |
| response.data.amount | string | 必填（所在对象出现时） | oneOf[2] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"payment.search.response.schema.json#/$defs/nonnegativeMoney"} |
| response.data.amount_signed | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"payment.search.response.schema.json#/$defs/money"} |
| response.data.amount_company_currency_signed | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"payment.search.response.schema.json#/$defs/money"} |
| response.data.currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"payment.search.response.schema.json#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.company_currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"payment.search.response.schema.json#/$defs/currency"} |
| response.data.company_currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.partner | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"payment.search.response.schema.json#/$defs/partner"}]} |
| response.data.partner | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.partner | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"payment.search.response.schema.json#/$defs/partner"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.partner.name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.partner.name | null | 分支约束 | oneOf[2]/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.partner.name | string | 分支约束 | oneOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"payment.search.response.schema.json#/$defs/journal"} |
| response.data.journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":5,"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.memo | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"payment.search.response.schema.json#/$defs/nullableText"} |
| response.data.memo | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.memo | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.payment_reference | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"payment.search.response.schema.json#/$defs/nullableText"} |
| response.data.payment_reference | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.payment_reference | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.payment_method_line | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","journal_id"],"resolved_ref":"payment.search.response.schema.json#/$defs/paymentMethodLine"} |
| response.data.payment_method_line.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.payment_method_line.name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.payment_method_line.name | null | 分支约束 | oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.payment_method_line.name | string | 分支约束 | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.payment_method_line.journal_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 日记账ID | {"minimum":1} |
| response.data.payment_method | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name","payment_type"],"resolved_ref":"payment.search.response.schema.json#/$defs/paymentMethod"} |
| response.data.payment_method.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.payment_method.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.payment_method.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.payment_method.payment_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["inbound","outbound"]} |
| response.data.move_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 会计单据记录ID | {"minimum":1} |
| response.data.is_reconciled | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.is_matched | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.journal_entry | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/journalEntry"}]} |
| response.data.journal_entry | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.journal_entry | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","state","date"],"resolved_ref":"#/$defs/journalEntry"} |
| response.data.journal_entry.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.journal_entry.name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"payment.search.response.schema.json#/$defs/nullableText"} |
| response.data.journal_entry.name | null | 分支约束 | oneOf[2]/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.journal_entry.name | string | 分支约束 | oneOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.journal_entry.state | 未限定 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.journal_entry.date | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.invoice_ids | array | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.invoice_ids[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","payment_state","company_id"],"resolved_ref":"#/$defs/document"} |
| response.data.invoice_ids[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.invoice_ids[].name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"payment.search.response.schema.json#/$defs/nullableText"} |
| response.data.invoice_ids[].name | null | 分支约束 | oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.invoice_ids[].name | string | 分支约束 | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.invoice_ids[].move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["out_invoice","out_refund","out_receipt","in_invoice","in_refund","in_receipt"]} |
| response.data.invoice_ids[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.invoice_ids[].payment_state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy"]} |
| response.data.invoice_ids[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.reconciled_invoices | array | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.reconciled_invoices[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","payment_state","company_id"],"resolved_ref":"#/$defs/document"} |
| response.data.reconciled_invoices[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.reconciled_invoices[].name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"payment.search.response.schema.json#/$defs/nullableText"} |
| response.data.reconciled_invoices[].name | null | 分支约束 | oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.reconciled_invoices[].name | string | 分支约束 | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.reconciled_invoices[].move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["out_invoice","out_refund","out_receipt","in_invoice","in_refund","in_receipt"]} |
| response.data.reconciled_invoices[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.reconciled_invoices[].payment_state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy"]} |
| response.data.reconciled_invoices[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.reconciled_bills | array | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.reconciled_bills[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","payment_state","company_id"],"resolved_ref":"#/$defs/document"} |
| response.data.reconciled_bills[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.reconciled_bills[].name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"payment.search.response.schema.json#/$defs/nullableText"} |
| response.data.reconciled_bills[].name | null | 分支约束 | oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.reconciled_bills[].name | string | 分支约束 | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.reconciled_bills[].move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["out_invoice","out_refund","out_receipt","in_invoice","in_refund","in_receipt"]} |
| response.data.reconciled_bills[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.reconciled_bills[].payment_state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy"]} |
| response.data.reconciled_bills[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.reconciled_bank_transactions | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.reconciled_bank_transactions[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id"]} |
| response.data.reconciled_bank_transactions[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.reconciled_bank_transactions[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","date","state","payment_type","partner_type","amount","amount_signed","amount_company_currency_signed","currency","company_currency","company_id","partner","journal","memo","payment_reference","payment_method_line","payment_method","move_id","is_reconciled","is_matched","journal_entry","invoice_ids","reconciled_invoices","reconciled_bills","reconciled_bank_transactions"],"resolved_ref":"#/$defs/data"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"payment.search.response.schema.json#/$defs/nullableText"} |
| response.data.name | null | 分支约束 | allOf[1]/then/oneOf[1] | 名称/行说明 |  |
| response.data.name | string | 分支约束 | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","in_process","paid","canceled","rejected"]} |
| response.data.payment_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["inbound","outbound"]} |
| response.data.partner_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["customer","supplier"]} |
| response.data.amount | string | 必填（所在对象出现时） | allOf[1]/then | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"payment.search.response.schema.json#/$defs/nonnegativeMoney"} |
| response.data.amount_signed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"payment.search.response.schema.json#/$defs/money"} |
| response.data.amount_company_currency_signed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"payment.search.response.schema.json#/$defs/money"} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"payment.search.response.schema.json#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.company_currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"payment.search.response.schema.json#/$defs/currency"} |
| response.data.company_currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"payment.search.response.schema.json#/$defs/partner"}]} |
| response.data.partner | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.partner | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"payment.search.response.schema.json#/$defs/partner"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.partner.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.partner.name | null | 分支约束 | allOf[1]/then/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.partner.name | string | 分支约束 | allOf[1]/then/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"payment.search.response.schema.json#/$defs/journal"} |
| response.data.journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":5,"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.memo | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"payment.search.response.schema.json#/$defs/nullableText"} |
| response.data.memo | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.memo | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.payment_reference | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"payment.search.response.schema.json#/$defs/nullableText"} |
| response.data.payment_reference | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.payment_reference | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.payment_method_line | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","journal_id"],"resolved_ref":"payment.search.response.schema.json#/$defs/paymentMethodLine"} |
| response.data.payment_method_line.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.payment_method_line.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.payment_method_line.name | null | 分支约束 | allOf[1]/then/oneOf[1] | 名称/行说明 |  |
| response.data.payment_method_line.name | string | 分支约束 | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.payment_method_line.journal_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 日记账ID | {"minimum":1} |
| response.data.payment_method | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name","payment_type"],"resolved_ref":"payment.search.response.schema.json#/$defs/paymentMethod"} |
| response.data.payment_method.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.payment_method.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.payment_method.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.payment_method.payment_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["inbound","outbound"]} |
| response.data.move_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 会计单据记录ID | {"minimum":1} |
| response.data.is_reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.is_matched | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.journal_entry | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/journalEntry"}]} |
| response.data.journal_entry | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.journal_entry | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","state","date"],"resolved_ref":"#/$defs/journalEntry"} |
| response.data.journal_entry.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.journal_entry.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"payment.search.response.schema.json#/$defs/nullableText"} |
| response.data.journal_entry.name | null | 分支约束 | allOf[1]/then/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.journal_entry.name | string | 分支约束 | allOf[1]/then/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.journal_entry.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.journal_entry.date | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"format":"date"} |
| response.data.invoice_ids | array | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.invoice_ids[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","payment_state","company_id"],"resolved_ref":"#/$defs/document"} |
| response.data.invoice_ids[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.invoice_ids[].name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"payment.search.response.schema.json#/$defs/nullableText"} |
| response.data.invoice_ids[].name | null | 分支约束 | allOf[1]/then/oneOf[1] | 名称/行说明 |  |
| response.data.invoice_ids[].name | string | 分支约束 | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.invoice_ids[].move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["out_invoice","out_refund","out_receipt","in_invoice","in_refund","in_receipt"]} |
| response.data.invoice_ids[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.invoice_ids[].payment_state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy"]} |
| response.data.invoice_ids[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.reconciled_invoices | array | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.reconciled_invoices[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","payment_state","company_id"],"resolved_ref":"#/$defs/document"} |
| response.data.reconciled_invoices[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.reconciled_invoices[].name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"payment.search.response.schema.json#/$defs/nullableText"} |
| response.data.reconciled_invoices[].name | null | 分支约束 | allOf[1]/then/oneOf[1] | 名称/行说明 |  |
| response.data.reconciled_invoices[].name | string | 分支约束 | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.reconciled_invoices[].move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["out_invoice","out_refund","out_receipt","in_invoice","in_refund","in_receipt"]} |
| response.data.reconciled_invoices[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.reconciled_invoices[].payment_state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy"]} |
| response.data.reconciled_invoices[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.reconciled_bills | array | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.reconciled_bills[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","payment_state","company_id"],"resolved_ref":"#/$defs/document"} |
| response.data.reconciled_bills[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.reconciled_bills[].name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"payment.search.response.schema.json#/$defs/nullableText"} |
| response.data.reconciled_bills[].name | null | 分支约束 | allOf[1]/then/oneOf[1] | 名称/行说明 |  |
| response.data.reconciled_bills[].name | string | 分支约束 | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.reconciled_bills[].move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["out_invoice","out_refund","out_receipt","in_invoice","in_refund","in_receipt"]} |
| response.data.reconciled_bills[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.reconciled_bills[].payment_state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 原生付款结算状态 | {"enum":["not_paid","in_payment","paid","partial","reversed","blocked","invoicing_legacy"]} |
| response.data.reconciled_bills[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.reconciled_bank_transactions | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.reconciled_bank_transactions[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id"]} |
| response.data.reconciled_bank_transactions[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.reconciled_bank_transactions[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
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

- `unit`：`implemented`；Closed typed inputs, schema and target binding; compatible legacy branches remain covered.；引用：tests/unit/test_accounting_workflows_batch.py
- `integration`：`implemented`；Shared native CLI workflow: both isolated aliases passed32.80s as uid5/su=False/company1. Verified sale/purchase reversal plus draft reissue and replay, native foreign-currency line edits, full/partial matching-group leaf undo and shrinking replay, statement-scoped bank pagination and actual payment bank matches, three company account assignments/clearing/readback and product fallback, purchase self-billing sequence. Native configuration roles and independent bank fixtures exist only in the test transaction. Fresh-cursor objects, caller groups, company settings, defaults and currency/rate rollback checks passed. Bank response additions require synchronized SDK/bridge/schema. No business DB, native source/addon, service, external-send or operation-store changes. Prior-paid reissue, cashbasis/exchange undo workflows, all ancestry/currency/localization/lock/hash branches, all setting consumers and concurrent exactly-once are not claimed.；引用：tests/integration/test_accounting_workflows_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-method-get"></a>

## payment.method.get — 获取付款方式详情

- 类型：只读；静态状态：`unconfigured`；handler：`payment_method_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`payments`；来源模型：res.company, account.payment.method.line, account.payment.method, account.journal, account.account；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.payment.method.line:read, account.payment.method:read, account.journal:read, account.account:read。
- 请求/响应合同：`schemas/v1/payment.method.get.request.schema.json` / `schemas/v1/payment.method.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read payment.method.get --request "@request.json"
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
    "payment_method_line_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_method_line_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.payment_method_line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"payment.method.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payment.method.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"payment.method.list.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","payment_type","sequence","company_id","payment_method","journal","payment_account"],"resolved_ref":"payment.method.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.payment_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["inbound","outbound"]} |
| response.data.sequence | integer | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.payment_method | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.payment_method.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.payment_method.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.payment_method.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.payment_account | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"additionalProperties":false,"properties":{"code":{"minLength":1,"type":"string"},"id":{"minimum":1,"type":"integer"},"name":{"minLength":1,"type":"string"}},"required":["id","code","name"],"type":"object"}]} |
| response.data.payment_account | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.payment_account | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.payment_account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.payment_account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.payment_account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"payment.method.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","payment_type","sequence","company_id","payment_method","journal","payment_account"],"resolved_ref":"payment.method.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.payment_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["inbound","outbound"]} |
| response.data.sequence | integer | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.payment_method | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.payment_method.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.payment_method.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.payment_method.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.payment_account | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"additionalProperties":false,"properties":{"code":{"minLength":1,"type":"string"},"id":{"minimum":1,"type":"integer"},"name":{"minLength":1,"type":"string"}},"required":["id","code","name"],"type":"object"}]} |
| response.data.payment_account | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.payment_account | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.payment_account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.payment_account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.payment_account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
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

<a id="cap-payment-method-list"></a>

## payment.method.list — 列出付款方式

- 类型：只读；静态状态：`unconfigured`；handler：`payment_method_list`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`payments`；来源模型：res.company, account.payment.method.line, account.payment.method, account.journal, account.account；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.payment.method.line:read, account.payment.method:read, account.journal:read, account.account:read。
- 请求/响应合同：`schemas/v1/payment.method.list.request.schema.json` / `schemas/v1/payment.method.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read payment.method.list --request "@request.json"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payment.method.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","payment_type","sequence","company_id","payment_method","journal","payment_account"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].payment_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["inbound","outbound"]} |
| response.data.items[].sequence | integer | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].payment_method | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.items[].payment_method.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].payment_method.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].payment_method.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].payment_account | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"additionalProperties":false,"properties":{"code":{"minLength":1,"type":"string"},"id":{"minimum":1,"type":"integer"},"name":{"minLength":1,"type":"string"}},"required":["id","code","name"],"type":"object"}]} |
| response.data.items[].payment_account | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].payment_account | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.items[].payment_account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].payment_account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.items[].payment_account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","payment_type","sequence","company_id","payment_method","journal","payment_account"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].payment_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["inbound","outbound"]} |
| response.data.items[].sequence | integer | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].payment_method | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.items[].payment_method.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].payment_method.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].payment_method.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].payment_account | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"additionalProperties":false,"properties":{"code":{"minLength":1,"type":"string"},"id":{"minimum":1,"type":"integer"},"name":{"minLength":1,"type":"string"}},"required":["id","code","name"],"type":"object"}]} |
| response.data.items[].payment_account | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].payment_account | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.items[].payment_account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].payment_account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.items[].payment_account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
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

<a id="cap-payment-method_definition-get"></a>

## payment.method_definition.get — 读取付款方式定义

- 类型：只读；静态状态：`unconfigured`；handler：`payment_method_definition_get`。
- 状态原因：`runtime_context_required` — Requires an explicit isolated runtime/company/user configuration.
- 内部domain：`accounting_configuration`；来源模型：res.company, account.payment.method；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.payment.method:read。
- 请求/响应合同：`schemas/v1/payment.method_definition.get.request.schema.json` / `schemas/v1/payment.method_definition.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read payment.method_definition.get --request "@request.json"
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
    "payment_method_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_method_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.payment_method_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"payment.method_definition.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payment.method_definition.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"payment.method_definition.list.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","code","payment_type"],"resolved_ref":"payment.method_definition.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.payment_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["inbound","outbound"]} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"payment.method_definition.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","code","payment_type"],"resolved_ref":"payment.method_definition.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.payment_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["inbound","outbound"]} |
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
- `execute`：fixed_native_payment_method_definition_read
- `verify`：response_schema_validation
- `idempotency`：read_only
- `reverse`：not_applicable

### 已登记测试与证据范围

- `unit`：`implemented`；Shared batch contract, schema, public CLI, native copy/remove semantics and ACL tests.；引用：tests/unit/test_payment_configuration_batch.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases through the public CLI as uid 5 with su=False: all eight capabilities, five immediate replays, native account reconcile enablement, copy=False account preservation, unused-line deletion, used-line detachment retaining posted payment history, company isolation, and fresh-cursor business-data and temporary-group rollback verification.；引用：tests/integration/test_payment_configuration_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-method_definition-list"></a>

## payment.method_definition.list — 列出付款方式定义

- 类型：只读；静态状态：`unconfigured`；handler：`payment_method_definition_list`。
- 状态原因：`runtime_context_required` — Requires an explicit isolated runtime/company/user configuration.
- 内部domain：`accounting_configuration`；来源模型：res.company, account.payment.method；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.payment.method:read。
- 请求/响应合同：`schemas/v1/payment.method_definition.list.request.schema.json` / `schemas/v1/payment.method_definition.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read payment.method_definition.list --request "@request.json"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payment.method_definition.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","code","payment_type"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].payment_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["inbound","outbound"]} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","code","payment_type"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].payment_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["inbound","outbound"]} |
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
- `execute`：fixed_native_payment_method_definition_read
- `verify`：response_schema_validation
- `idempotency`：read_only
- `reverse`：not_applicable

### 已登记测试与证据范围

- `unit`：`implemented`；Shared batch contract, schema, public CLI, native copy/remove semantics and ACL tests.；引用：tests/unit/test_payment_configuration_batch.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases through the public CLI as uid 5 with su=False: all eight capabilities, five immediate replays, native account reconcile enablement, copy=False account preservation, unused-line deletion, used-line detachment retaining posted payment history, company isolation, and fresh-cursor business-data and temporary-group rollback verification.；引用：tests/integration/test_payment_configuration_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-method_line-create"></a>

## payment.method_line.create — 创建日记账付款方式行

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`natural_key_replay_attribution_limit` — Natural-key replay attribution and concurrent exactly-once execution are not proven.
- 内部domain：`accounting_configuration`；来源模型：account.account, account.journal, account.payment.method, account.payment.method.line, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.account:read, account.account:write, account.journal:read, account.payment.method.line:create, account.payment.method.line:read, account.payment.method:read。
- 请求/响应合同：`schemas/v1/payment.method_line.create.request.schema.json` / `schemas/v1/payment.method_line.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment.method_line.create --request "@request.json" --idempotency-key "payment.method_line.create:1:36fee78f7357a4d663187c2b351a0fca" --confirm "payment.method_line.create"
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
    "name": "Example",
    "payment_account_id": 1,
    "payment_method_id": 1,
    "sequence": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["journal_id","name","payment_account_id","payment_method_id","sequence"]} |
| parameters.journal_id | integer | 必填（所在对象出现时） |  | 日记账ID | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":256,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","resolved_ref":"#/$defs/name"} |
| parameters.payment_account_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.payment_method_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.sequence | integer | 必填（所在对象出现时） |  |  | {"maximum":2147483647,"minimum":0} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment.method_line.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment.method_line.create"} |
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
- `idempotency`：natural_key_payload_recheck_without_operation_store
- `reverse`：restore_previous_configuration

### 已登记测试与证据范围

- `unit`：`implemented`；Shared batch contract, schema, public CLI, native copy/remove semantics and ACL tests.；引用：tests/unit/test_payment_configuration_batch.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases through the public CLI as uid 5 with su=False: all eight capabilities, five immediate replays, native account reconcile enablement, copy=False account preservation, unused-line deletion, used-line detachment retaining posted payment history, company isolation, and fresh-cursor business-data and temporary-group rollback verification.；引用：tests/integration/test_payment_configuration_batch_live.py
- `golden`：`planned`；Golden examples follow capability coverage.；引用：无
- `e2e`：`planned`；Natural-language routing follows capability coverage.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-method_line-duplicate"></a>

## payment.method_line.duplicate — 复制日记账付款方式行

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`natural_key_replay_attribution_limit` — Natural-key replay attribution and concurrent exactly-once execution are not proven.
- 内部domain：`accounting_configuration`；来源模型：account.account, account.journal, account.payment.method, account.payment.method.line, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.account:read, account.account:write, account.journal:read, account.payment.method.line:create, account.payment.method.line:read, account.payment.method:read。
- 请求/响应合同：`schemas/v1/payment.method_line.duplicate.request.schema.json` / `schemas/v1/payment.method_line.duplicate.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment.method_line.duplicate --request "@request.json" --idempotency-key "payment.method_line.duplicate:1:738e24d4e0e29c63059f232f52ec8bb9" --confirm "payment.method_line.duplicate"
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
    "payment_method_line_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["name","payment_method_line_id"]} |
| parameters.name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":256,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","resolved_ref":"#/$defs/name"} |
| parameters.payment_method_line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment.method_line.duplicate"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment.method_line.duplicate"} |
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
- `idempotency`：natural_key_payload_recheck_without_operation_store
- `reverse`：restore_previous_configuration

### 已登记测试与证据范围

- `unit`：`implemented`；Shared batch contract, schema, public CLI, native copy/remove semantics and ACL tests.；引用：tests/unit/test_payment_configuration_batch.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases through the public CLI as uid 5 with su=False: all eight capabilities, five immediate replays, native account reconcile enablement, copy=False account preservation, unused-line deletion, used-line detachment retaining posted payment history, company isolation, and fresh-cursor business-data and temporary-group rollback verification.；引用：tests/integration/test_payment_configuration_batch_live.py
- `golden`：`planned`；Golden examples follow capability coverage.；引用：无
- `e2e`：`planned`；Natural-language routing follows capability coverage.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-method_line-remove"></a>

## payment.method_line.remove — 移除日记账付款方式行

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`deleted_record_tombstone_unavailable` — Used lines are natively detached, unused lines deleted; no persistent tombstone or automatic reversal.
- 内部domain：`accounting_configuration`；来源模型：account.account, account.journal, account.payment.method, account.payment.method.line, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.account:read, account.journal:read, account.payment.method.line:read, account.payment.method.line:unlink, account.payment.method.line:write, account.payment.method:read。
- 请求/响应合同：`schemas/v1/payment.method_line.remove.request.schema.json` / `schemas/v1/payment.method_line.remove.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment.method_line.remove --request "@request.json" --idempotency-key "payment.method_line.remove:1:b1e9a34b5512e32c79279fd630dfb404" --confirm "payment.method_line.remove"
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
    "payment_method_line_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_method_line_id"]} |
| parameters.payment_method_line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment.method_line.remove"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment.method_line.remove"} |
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
- `idempotency`：target_lookup_without_persistent_tombstone
- `reverse`：not_reversible

### 已登记测试与证据范围

- `unit`：`implemented`；Shared batch contract, schema, public CLI, native copy/remove semantics and ACL tests.；引用：tests/unit/test_payment_configuration_batch.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases through the public CLI as uid 5 with su=False: all eight capabilities, five immediate replays, native account reconcile enablement, copy=False account preservation, unused-line deletion, used-line detachment retaining posted payment history, company isolation, and fresh-cursor business-data and temporary-group rollback verification.；引用：tests/integration/test_payment_configuration_batch_live.py
- `golden`：`planned`；Golden examples follow capability coverage.；引用：无
- `e2e`：`planned`；Natural-language routing follows capability coverage.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-method_line-update"></a>

## payment.method_line.update — 修改日记账付款方式行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires an explicit isolated runtime/company/user configuration.
- 内部domain：`accounting_configuration`；来源模型：account.account, account.journal, account.payment.method, account.payment.method.line, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.account:read, account.account:write, account.journal:read, account.payment.method.line:read, account.payment.method.line:write, account.payment.method:read。
- 请求/响应合同：`schemas/v1/payment.method_line.update.request.schema.json` / `schemas/v1/payment.method_line.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment.method_line.update --request "@request.json" --idempotency-key "payment.method_line.update:1:33ac7b585d44533f3110fa752dcd22fd" --confirm "payment.method_line.update"
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
      "name": "Example"
    },
    "payment_method_line_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["changes","payment_method_line_id"]} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.name | string | 可选（可能有条件限制） |  | 名称/行说明 | {"maxLength":256,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","resolved_ref":"#/$defs/name"} |
| parameters.changes.payment_account_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.changes.sequence | integer | 可选（可能有条件限制） |  |  | {"maximum":2147483647,"minimum":0} |
| parameters.payment_method_line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment.method_line.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment.method_line.update"} |
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

<a id="cap-payment-post"></a>

## payment.post — 原子过账单笔或 2–100 笔会计付款

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`payments`；来源模型：res.company, account.move, account.payment；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.payment:read, account.payment:write, account.move:read, account.move:write。
- 请求/响应合同：`schemas/v1/payment.post.request.schema.json` / `schemas/v1/payment.post.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment.post --request "@request.json" --idempotency-key "payment.post:1" --confirm "payment.post"
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
    "payment_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  |  |
| parameters | object | 必填 |  |  | {"additionalProperties":false,"oneOf":[{"required":["payment_id"]},{"required":["payment_ids"]}]} |
| parameters.payment_id | integer | 可选（可能有条件限制） |  | 付款/收款记录ID | {"minimum":1} |
| parameters.payment_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| parameters.payment_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters | 未限定 | 分支约束 | oneOf[1] |  | {"required_in_object":["payment_id"]} |
| parameters | 未限定 | 分支约束 | oneOf[2] |  | {"required_in_object":["payment_ids"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment.post"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment.post"} |
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

- `preview`：singular_or_2_to_100_distinct_ids_closed_validation_normalized_sorted_and_exact_capability_confirmation
- `execute`：full_batch_record_scope_company_payment_type_and_state_preflight_then_single_transaction_all_or_nothing_native_post
- `verify`：explicit_batch_result_with_exact_normalized_record_ids_target_states_same_transaction_reread_and_response_schema_validation
- `idempotency`：capability_company_and_full_normalized_sorted_record_id_set_key_with_serial_target_state_replay
- `reverse`：payment.cancel

### 已登记测试与证据范围

- `unit`：`implemented`；The existing unit tests continue to cover the singular request and native runtime behavior; the batch contract unit test covers batch-request normalization, full normalized-ID-set idempotency keys, bridge and capability contracts, explicit batch results, and CLI verification.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_core_write_cli.py, tests/unit/test_lifecycle_batch_contract.py
- `integration`：`implemented`；The existing integration smoke continues to cover singular native execution; the new live smoke covers dual-database batch execution, immediate replay, and rollback, plus a representative whole-batch invalid-ID no-op for invoice.post.；引用：tests/integration/test_core_write_batch_live.py, tests/integration/test_batch_lifecycle_write_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-processing_settings-get"></a>

## payment.processing_settings.get — 读取付款处理设置

- 类型：只读；静态状态：`unconfigured`；handler：`payment_processing_settings_get`。
- 状态原因：`runtime_context_required` — Requires configured caller/company and native ACLs. Bank assignment uses native eligible recipient/company accounts without changing trust. Accounting destination changes require draft payment and entry. Sent-status actions require in-process manual method. Manual validation is only for no-entry payments; journal-backed settlement uses reconciliation. Rejection requires in-process sent payment. Native duplicate warnings are candidates, not proof of duplication; they may include different currencies. No external transfer, bank submission, receipt send or caller-sudo.
- 内部domain：`payments`；来源模型：res.company, account.payment, res.partner.bank, account.account, account.move；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.payment:read, res.partner.bank:read, account.account:read, account.move:read。
- 请求/响应合同：`schemas/v1/payment.processing_settings.get.request.schema.json` / `schemas/v1/payment.processing_settings.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read payment.processing_settings.get --request "@request.json"
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
    "payment_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_id"]} |
| parameters.payment_id | integer | 必填（所在对象出现时） |  | 付款/收款记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payment.processing_settings.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["company_id","destination_account_id","id","is_matched","is_reconciled","is_sent","move_id","name","outstanding_account_id","partner_bank_id","partner_id","partner_type","payment_method_code","payment_type","require_partner_bank_account","show_partner_bank_account","state"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 |  |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["canceled","draft","in_process","paid","rejected"]} |
| response.data.payment_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["inbound","outbound"]} |
| response.data.partner_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["customer","supplier"]} |
| response.data.partner_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 合作伙伴ID | {"minimum":1} |
| response.data.partner_bank_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.destination_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.outstanding_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.move_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 会计单据记录ID | {"minimum":1} |
| response.data.payment_method_code | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.is_sent | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.is_reconciled | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.is_matched | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.show_partner_bank_account | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.require_partner_bank_account | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["company_id","destination_account_id","id","is_matched","is_reconciled","is_sent","move_id","name","outstanding_account_id","partner_bank_id","partner_id","partner_type","payment_method_code","payment_type","require_partner_bank_account","show_partner_bank_account","state"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 |  |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["canceled","draft","in_process","paid","rejected"]} |
| response.data.payment_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["inbound","outbound"]} |
| response.data.partner_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["customer","supplier"]} |
| response.data.partner_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 合作伙伴ID | {"minimum":1} |
| response.data.partner_bank_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.destination_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.outstanding_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.move_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 会计单据记录ID | {"minimum":1} |
| response.data.payment_method_code | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.is_sent | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.is_reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.is_matched | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.show_partner_bank_account | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.require_partner_bank_account | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
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
- `execute`：fixed_native_payment_read
- `verify`：closed_response_schema_validation
- `idempotency`：read_only
- `reverse`：not_applicable

### 已登记测试与证据范围

- `unit`：`implemented`；Closed schemas, fixed CLI/ORM dispatch, native eligibility and state boundaries, deterministic keys and read/write scope.；引用：tests/unit/test_payment_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all eight new IDs, three existing setup/recovery IDs and eleven immediate replays; native recipient/company bank eligibility, scoped keyset duplicate warnings, unchanged bank trust, actual destination account in the posted balanced entry, native sent/unset and rejected/reset lifecycle, truthful posted bank change without rewriting its entry, and native no-entry validation. Invalid state, journal-backed validation, foreign company and ineligible bank denied; fresh-cursor business-data and temporary-group rollback verified. No bank/provider submission, external receipt delivery, addon or service changes.；引用：tests/integration/test_payment_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-receipt-pdf-export"></a>

## payment.receipt.pdf.export — 导出付款收据 PDF

- 类型：只读；静态状态：`unconfigured`；handler：`document_payment_receipt_pdf_export`。
- 状态原因：`runtime_context_required` — The fixed native PDF handler is installed; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`document_exports`；来源模型：account.payment, res.company, ir.actions.report；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.payment:read, res.company:read, ir.actions.report:read。
- 请求/响应合同：`schemas/v1/payment.receipt.pdf.export.request.schema.json` / `schemas/v1/payment.receipt.pdf.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read payment.receipt.pdf.export --request "@request.json"
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
    "payment_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.payment_id | integer | 必填（所在对象出现时） |  | 付款/收款记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payment.receipt.pdf.export"} |
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
- `execute`：fixed_native_payment_receipt_qweb_pdf_action
- `verify`：bound_record_pdf_bytes_hash_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover the fixed action, exact contract, bridge, runtime, CLI routing, registry metadata, and schemas.；引用：tests/unit/test_document_exports.py, tests/unit/test_document_exports_bridge.py, tests/unit/test_document_exports_runtime.py, tests/unit/test_document_export_cli.py, tests/unit/test_document_export_registry.py
- `integration`：`implemented`；The shared read-only live smoke covers the fixed document export batch in both isolated databases.；引用：tests/integration/test_document_export_batch_live.py
- `golden`：`planned`；Golden PDF evidence is pending.；引用：无
- `e2e`：`planned`；End-to-end natural-language routing evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-receipt-send"></a>

## payment.receipt.send — 将付款收据加入 Odoo 发送队列

- 类型：写入；静态状态：`degraded`；handler：`accounting_delivery`。
- 状态原因：`odoo_queue_delivery_only` — The fixed handler verifies its Odoo message marker after invoking the native queue-only delivery path; it does not claim mail-queue persistence or external SMTP delivery.
- 内部domain：`payments`；来源模型：res.company, account.payment, res.partner, mail.template, ir.actions.report, mail.message, mail.mail, ir.attachment；向导：mail.compose.message。
- 必需模块：account, mail；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：res.company:read, account.payment:read, account.payment:write, res.partner:read, mail.template:read, ir.actions.report:read, mail.compose.message:read, mail.compose.message:create, mail.compose.message:write, mail.message:read, mail.mail:read, ir.attachment:read。
- 请求/响应合同：`schemas/v1/payment.receipt.send.request.schema.json` / `schemas/v1/payment.receipt.send.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment.receipt.send --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "payment.receipt.send"
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
    "payment_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"oneOf":[{"required":["payment_id"]},{"required":["payment_ids"]}]} |
| parameters.payment_id | integer | 可选（可能有条件限制） |  | 付款/收款记录ID | {"minimum":1} |
| parameters.payment_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| parameters.payment_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters | 未限定 | 分支约束 | oneOf[1] |  | {"required_in_object":["payment_id"]} |
| parameters | 未限定 | 分支约束 | oneOf[2] |  | {"required_in_object":["payment_ids"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payment.receipt.send"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"#/$defs/data"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["record_ids","processed_count"],"resolved_ref":"#/$defs/send_result"} |
| response.data.result.record_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":100,"minItems":1,"uniqueItems":true} |
| response.data.result.record_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"maximum":100,"minimum":1} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"#/$defs/data"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[1]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["record_ids","processed_count"],"resolved_ref":"#/$defs/send_result"} |
| response.data.result.record_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":100,"minItems":1,"uniqueItems":true} |
| response.data.result.record_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"maximum":100,"minimum":1} |
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
- `execute`：fixed_native_payment_receipt_mail_composer_with_queued_delivery
- `verify`：same_transaction_marked_message_and_response_schema_validation
- `idempotency`：caller_key_marker_serial_replay_without_concurrent_or_external_transport_exactly_once_guarantee
- `reverse`：cancel_pending_mail_outside_this_capability

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover the closed singular-or-batch request, confirmation, idempotency key, result binding, registry metadata, and schemas.；引用：tests/unit/test_accounting_delivery.py, tests/unit/test_accounting_delivery_registry.py
- `integration`：`implemented`；The guarded queue-only smoke passed both isolated aliases as uid 5 with su=False, verifying one native marked message, serial replay, rollback, and no external-delivery claim.；引用：tests/integration/test_accounting_delivery_batch_live.py
- `golden`：`planned`；Golden queued-delivery examples are pending.；引用：无
- `e2e`：`planned`；Natural-language routing evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-receipt-send-inspect"></a>

## payment.receipt.send.inspect — 检查付款收据发送准备状态

- 类型：只读；静态状态：`unconfigured`；handler：`payment_receipt_send_inspect`。
- 状态原因：`runtime_context_required` — The fixed inspection handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`payments`；来源模型：res.company, account.payment, res.partner, mail.template, ir.actions.report, mail.message；向导：mail.compose.message。
- 必需模块：account, mail；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：res.company:read, account.payment:read, res.partner:read, mail.template:read, ir.actions.report:read, mail.message:read, mail.compose.message:read, mail.compose.message:create, mail.compose.message:write。
- 请求/响应合同：`schemas/v1/payment.receipt.send.inspect.request.schema.json` / `schemas/v1/payment.receipt.send.inspect.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read payment.receipt.send.inspect --request "@request.json"
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
    "payment_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"oneOf":[{"required":["payment_id"]},{"required":["payment_ids"]}]} |
| parameters.payment_id | integer | 可选（可能有条件限制） |  | 付款/收款记录ID | {"minimum":1} |
| parameters.payment_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| parameters.payment_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters | 未限定 | 分支约束 | oneOf[1] |  | {"required_in_object":["payment_id"]} |
| parameters | 未限定 | 分支约束 | oneOf[2] |  | {"required_in_object":["payment_ids"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payment.receipt.send.inspect"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"#/$defs/data"} |
| response.data.idempotent_replay | 未限定 | 必填（所在对象出现时） | oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 | {"const":false} |
| response.data.result | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["records"],"resolved_ref":"#/$defs/inspection_result"} |
| response.data.result.records | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":100,"minItems":1,"uniqueItems":true} |
| response.data.result.records[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["record_id","partner_id","recipient_emails","template_id","report_id","sending_methods","warnings","sendable"],"resolved_ref":"#/$defs/inspection_record"} |
| response.data.result.records[].record_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.result.records[].partner_id | integer | 必填（所在对象出现时） | oneOf[2] | 合作伙伴ID | {"minimum":1} |
| response.data.result.records[].recipient_emails | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.records[].recipient_emails[] | string | 每个数组元素 | oneOf[2] |  | {"minLength":1} |
| response.data.result.records[].template_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.result.records[].report_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.result.records[].sending_methods | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.records[].sending_methods[] | string | 每个数组元素 | oneOf[2] |  | {"minLength":1} |
| response.data.result.records[].warnings | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.result.records[].warnings[] | string | 每个数组元素 | oneOf[2] |  | {"minLength":1} |
| response.data.result.records[].sendable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"#/$defs/data"} |
| response.data.idempotent_replay | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 | {"const":false} |
| response.data.result | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["records"],"resolved_ref":"#/$defs/inspection_result"} |
| response.data.result.records | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":100,"minItems":1,"uniqueItems":true} |
| response.data.result.records[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["record_id","partner_id","recipient_emails","template_id","report_id","sending_methods","warnings","sendable"],"resolved_ref":"#/$defs/inspection_record"} |
| response.data.result.records[].record_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.result.records[].partner_id | integer | 必填（所在对象出现时） | allOf[1]/then | 合作伙伴ID | {"minimum":1} |
| response.data.result.records[].recipient_emails | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.result.records[].recipient_emails[] | string | 每个数组元素 | allOf[1]/then |  | {"minLength":1} |
| response.data.result.records[].template_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.result.records[].report_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.result.records[].sending_methods | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.result.records[].sending_methods[] | string | 每个数组元素 | allOf[1]/then |  | {"minLength":1} |
| response.data.result.records[].warnings | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.result.records[].warnings[] | string | 每个数组元素 | allOf[1]/then |  | {"minLength":1} |
| response.data.result.records[].sendable | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
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
- `execute`：fixed_payment_receipt_template_and_composer_inspection
- `verify`：rollback_only_recipient_template_report_method_and_warning_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover the closed singular-or-batch request, normalized inspection result, registry metadata, and schemas.；引用：tests/unit/test_accounting_delivery.py, tests/unit/test_accounting_delivery_registry.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases as uid 5 with su=False, using a rollback-only example.invalid fixture to verify native payment-receipt readiness.；引用：tests/integration/test_accounting_delivery_batch_live.py
- `golden`：`planned`；Golden inspection examples are pending.；引用：无
- `e2e`：`planned`；Natural-language routing evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-reject"></a>

## payment.reject — 拒绝已发送付款

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured caller/company and native ACLs. Bank assignment uses native eligible recipient/company accounts without changing trust. Accounting destination changes require draft payment and entry. Sent-status actions require in-process manual method. Manual validation is only for no-entry payments; journal-backed settlement uses reconciliation. Rejection requires in-process sent payment. Native duplicate warnings are candidates, not proof of duplication; they may include different currencies. No external transfer, bank submission, receipt send or caller-sudo.
- 内部domain：`payments`；来源模型：account.move, account.move.line, account.payment, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.move.line:read, account.move:read, account.payment:read, account.payment:write, res.company:read。
- 请求/响应合同：`schemas/v1/payment.reject.request.schema.json` / `schemas/v1/payment.reject.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment.reject --request "@request.json" --idempotency-key "payment.reject:1:f0c8de7167ff8d9ffb4c486ead6bbdd4" --confirm "payment.reject"
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
    "payment_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_id"]} |
| parameters.payment_id | integer | 必填（所在对象出现时） |  | 付款/收款记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment.reject"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment.reject"} |
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
- `execute`：fixed_native_payment_fields_or_state_action
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：native_desired_payload_or_state_recheck
- `reverse`：native_previous_assignment_or_existing_payment_reset_subject_to_acl_and_state

### 已登记测试与证据范围

- `unit`：`implemented`；Closed schemas, fixed CLI/ORM dispatch, native eligibility and state boundaries, deterministic keys and read/write scope.；引用：tests/unit/test_payment_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all eight new IDs, three existing setup/recovery IDs and eleven immediate replays; native recipient/company bank eligibility, scoped keyset duplicate warnings, unchanged bank trust, actual destination account in the posted balanced entry, native sent/unset and rejected/reset lifecycle, truthful posted bank change without rewriting its entry, and native no-entry validation. Invalid state, journal-backed validation, foreign company and ineligible bank denied; fresh-cursor business-data and temporary-group rollback verified. No bank/provider submission, external receipt delivery, addon or service changes.；引用：tests/integration/test_payment_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-reset_to_draft"></a>

## payment.reset_to_draft — 原子将单笔或 2–100 笔会计付款重置为草稿

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`payments`；来源模型：res.company, account.payment, account.move；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.payment:read, account.payment:write, account.move:read, account.move:write。
- 请求/响应合同：`schemas/v1/payment.reset_to_draft.request.schema.json` / `schemas/v1/payment.reset_to_draft.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment.reset_to_draft --request "@request.json" --idempotency-key "payment.reset_to_draft:1" --confirm "payment.reset_to_draft"
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
    "payment_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"oneOf":[{"required":["payment_id"]},{"required":["payment_ids"]}]} |
| parameters.payment_id | integer | 可选（可能有条件限制） |  | 付款/收款记录ID | {"minimum":1} |
| parameters.payment_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| parameters.payment_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters | 未限定 | 分支约束 | oneOf[1] |  | {"required_in_object":["payment_id"]} |
| parameters | 未限定 | 分支约束 | oneOf[2] |  | {"required_in_object":["payment_ids"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment.reset_to_draft"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment.reset_to_draft"} |
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

- `preview`：singular_or_2_to_100_distinct_ids_closed_validation_normalized_sorted_and_exact_capability_confirmation
- `execute`：full_batch_record_scope_company_payment_type_and_state_preflight_then_single_transaction_all_or_nothing_native_reset_to_draft
- `verify`：explicit_batch_result_with_exact_normalized_record_ids_target_states_same_transaction_reread_and_response_schema_validation
- `idempotency`：capability_company_and_full_normalized_sorted_record_id_set_key_with_serial_target_state_replay
- `reverse`：payment.post

### 已登记测试与证据范围

- `unit`：`implemented`；The existing unit tests continue to cover the singular request and native runtime behavior; the batch contract unit test covers batch-request normalization, full normalized-ID-set idempotency keys, bridge and capability contracts, explicit batch results, and CLI verification.；引用：tests/unit/test_payment_bank_writes.py, tests/unit/test_payment_bank_writes_runtime.py, tests/unit/test_payment_bank_write_cli.py, tests/unit/test_lifecycle_batch_contract.py
- `integration`：`implemented`；The existing integration smoke continues to cover singular native execution; the new live smoke covers dual-database batch execution, immediate replay, and rollback, plus a representative whole-batch invalid-ID no-op for invoice.post.；引用：tests/integration/test_payment_bank_capability_batch_live.py, tests/integration/test_batch_lifecycle_write_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-search"></a>

## payment.search — 搜索会计付款

- 类型：只读；静态状态：`unconfigured`；handler：`payment_search`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`payments`；来源模型：res.company, account.payment, account.payment.method, account.payment.method.line, res.currency, res.partner, account.journal, account.move；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.payment:read, account.payment.method:read, account.payment.method.line:read, res.currency:read, res.partner:read, account.journal:read, account.move:read。
- 请求/响应合同：`schemas/v1/payment.search.request.schema.json` / `schemas/v1/payment.search.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read payment.search --request "@request.json"
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
| parameters.states | array | 可选（可能有条件限制） |  |  | {"maxItems":5,"minItems":1,"uniqueItems":true} |
| parameters.states[] | 未限定 | 每个数组元素 |  |  | {"enum":["draft","in_process","paid","canceled","rejected"]} |
| parameters.payment_types | array | 可选（可能有条件限制） |  |  | {"maxItems":2,"minItems":1,"uniqueItems":true} |
| parameters.payment_types[] | 未限定 | 每个数组元素 |  |  | {"enum":["inbound","outbound"]} |
| parameters.partner_types | array | 可选（可能有条件限制） |  |  | {"maxItems":2,"minItems":1,"uniqueItems":true} |
| parameters.partner_types[] | 未限定 | 每个数组元素 |  |  | {"enum":["customer","supplier"]} |
| parameters.journal_id | integer/null | 可选（可能有条件限制） |  | 日记账ID | {"default":null,"minimum":1} |
| parameters.partner_id | integer/null | 可选（可能有条件限制） |  | 合作伙伴ID | {"default":null,"minimum":1} |
| parameters.currency_id | integer/null | 可选（可能有条件限制） |  | 币种ID | {"default":null,"minimum":1} |
| parameters.query | 组合/开放结构 | 可选（可能有条件限制） |  | 搜索文本 | {"default":null,"oneOf":[{"type":"null"},{"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","type":"string"}]} |
| parameters.query | null | 分支约束 | oneOf[1] | 搜索文本 |  |
| parameters.query | string | 分支约束 | oneOf[2] | 搜索文本 | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payment.search"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","date","state","payment_type","partner_type","amount","amount_signed","amount_company_currency_signed","currency","company_currency","company_id","partner","journal","memo","payment_reference","payment_method_line","payment_method","move_id","is_reconciled","is_matched"],"resolved_ref":"#/$defs/payment"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].name | null | 分支约束 | oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].name | string | 分支约束 | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","in_process","paid","canceled","rejected"]} |
| response.data.items[].payment_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["inbound","outbound"]} |
| response.data.items[].partner_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["customer","supplier"]} |
| response.data.items[].amount | string | 必填（所在对象出现时） | oneOf[2] | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegativeMoney"} |
| response.data.items[].amount_signed | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/money"} |
| response.data.items[].amount_company_currency_signed | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/money"} |
| response.data.items[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].company_currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].company_currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.items[].partner | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/partner"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].partner.name | null | 分支约束 | oneOf[2]/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].partner.name | string | 分支约束 | oneOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/journal"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":5,"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].memo | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].memo | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].memo | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].payment_reference | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].payment_reference | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].payment_reference | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].payment_method_line | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","journal_id"],"resolved_ref":"#/$defs/paymentMethodLine"} |
| response.data.items[].payment_method_line.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].payment_method_line.name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].payment_method_line.name | null | 分支约束 | oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].payment_method_line.name | string | 分支约束 | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].payment_method_line.journal_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 日记账ID | {"minimum":1} |
| response.data.items[].payment_method | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name","payment_type"],"resolved_ref":"#/$defs/paymentMethod"} |
| response.data.items[].payment_method.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].payment_method.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].payment_method.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].payment_method.payment_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["inbound","outbound"]} |
| response.data.items[].move_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 会计单据记录ID | {"minimum":1} |
| response.data.items[].is_reconciled | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].is_matched | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","date","state","payment_type","partner_type","amount","amount_signed","amount_company_currency_signed","currency","company_currency","company_id","partner","journal","memo","payment_reference","payment_method_line","payment_method","move_id","is_reconciled","is_matched"],"resolved_ref":"#/$defs/payment"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].name | null | 分支约束 | allOf[1]/then/oneOf[1] | 名称/行说明 |  |
| response.data.items[].name | string | 分支约束 | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","in_process","paid","canceled","rejected"]} |
| response.data.items[].payment_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["inbound","outbound"]} |
| response.data.items[].partner_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["customer","supplier"]} |
| response.data.items[].amount | string | 必填（所在对象出现时） | allOf[1]/then | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegativeMoney"} |
| response.data.items[].amount_signed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/money"} |
| response.data.items[].amount_company_currency_signed | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/money"} |
| response.data.items[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].company_currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].company_currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.items[].partner | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/partner"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].partner.name | null | 分支约束 | allOf[1]/then/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].partner.name | string | 分支约束 | allOf[1]/then/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/journal"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":5,"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].memo | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].memo | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].memo | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].payment_reference | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].payment_reference | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].payment_reference | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].payment_method_line | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","journal_id"],"resolved_ref":"#/$defs/paymentMethodLine"} |
| response.data.items[].payment_method_line.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].payment_method_line.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/text"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].payment_method_line.name | null | 分支约束 | allOf[1]/then/oneOf[1] | 名称/行说明 |  |
| response.data.items[].payment_method_line.name | string | 分支约束 | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].payment_method_line.journal_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 日记账ID | {"minimum":1} |
| response.data.items[].payment_method | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name","payment_type"],"resolved_ref":"#/$defs/paymentMethod"} |
| response.data.items[].payment_method.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].payment_method.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].payment_method.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1,"resolved_ref":"#/$defs/text"} |
| response.data.items[].payment_method.payment_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["inbound","outbound"]} |
| response.data.items[].move_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 会计单据记录ID | {"minimum":1} |
| response.data.items[].is_reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].is_matched | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
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

- `unit`：`implemented`；Unit tests cover the closed request and response, cursor, bridge, fixed ORM, scope, ACL, and control-CLI contracts.；引用：tests/unit/test_payments.py, tests/unit/test_payment_bridge.py, tests/unit/test_payment_runtime.py, tests/unit/test_payment_cli.py
- `integration`：`implemented`；The live integration test verifies payment search, exact-get details, all available search filters, and company isolation across both dedicated synthetic database aliases and both configured companies.；引用：tests/integration/test_payments_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-sent_status-set"></a>

## payment.sent_status.set — 设置付款已发送标记

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured caller/company and native ACLs. Bank assignment uses native eligible recipient/company accounts without changing trust. Accounting destination changes require draft payment and entry. Sent-status actions require in-process manual method. Manual validation is only for no-entry payments; journal-backed settlement uses reconciliation. Rejection requires in-process sent payment. Native duplicate warnings are candidates, not proof of duplication; they may include different currencies. No external transfer, bank submission, receipt send or caller-sudo.
- 内部domain：`payments`；来源模型：account.move, account.move.line, account.payment, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.move.line:read, account.move:read, account.payment:read, account.payment:write, res.company:read。
- 请求/响应合同：`schemas/v1/payment.sent_status.set.request.schema.json` / `schemas/v1/payment.sent_status.set.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment.sent_status.set --request "@request.json" --idempotency-key "payment.sent_status.set:1:b6fe601d8cef488ea74a55bb2febe8db" --confirm "payment.sent_status.set"
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
    "payment_id": 1,
    "sent": false
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_id","sent"]} |
| parameters.payment_id | integer | 必填（所在对象出现时） |  | 付款/收款记录ID | {"minimum":1} |
| parameters.sent | boolean | 必填（所在对象出现时） |  |  |  |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment.sent_status.set"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment.sent_status.set"} |
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
- `execute`：fixed_native_payment_fields_or_state_action
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：native_desired_payload_or_state_recheck
- `reverse`：native_previous_assignment_or_existing_payment_reset_subject_to_acl_and_state

### 已登记测试与证据范围

- `unit`：`implemented`；Closed schemas, fixed CLI/ORM dispatch, native eligibility and state boundaries, deterministic keys and read/write scope.；引用：tests/unit/test_payment_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all eight new IDs, three existing setup/recovery IDs and eleven immediate replays; native recipient/company bank eligibility, scoped keyset duplicate warnings, unchanged bank trust, actual destination account in the posted balanced entry, native sent/unset and rejected/reset lifecycle, truthful posted bank change without rewriting its entry, and native no-entry validation. Invalid state, journal-backed validation, foreign company and ineligible bank denied; fresh-cursor business-data and temporary-group rollback verified. No bank/provider submission, external receipt delivery, addon or service changes.；引用：tests/integration/test_payment_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-update_draft"></a>

## payment.update_draft — 更新草稿会计付款

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`payments`；来源模型：res.company, res.partner, res.currency, account.journal, account.account, account.payment.method, account.payment.method.line, account.payment, account.move, account.move.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：res.partner:read, res.currency:read, account.journal:read, account.account:read, account.payment.method:read, account.payment.method.line:read, account.payment:read, account.payment:write, account.move:read, account.move:write, account.move.line:read, account.move.line:write。
- 请求/响应合同：`schemas/v1/payment.update_draft.request.schema.json` / `schemas/v1/payment.update_draft.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment.update_draft --request "@request.json" --idempotency-key "payment.update_draft:1:5f584ec21a856311a118df8d9b253ad9" --confirm "payment.update_draft"
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
    "payment_id": 1,
    "changes": {
      "payment_type": "inbound"
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_id","changes"]} |
| parameters.payment_id | integer | 必填（所在对象出现时） |  | 付款/收款记录ID | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.payment_type | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["inbound","outbound"]} |
| parameters.changes.partner_type | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["customer","supplier"]} |
| parameters.changes.partner_id | integer | 可选（可能有条件限制） |  | 合作伙伴ID | {"minimum":1} |
| parameters.changes.amount | string | 可选（可能有条件限制） |  | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^(?=[0-9.]*[1-9])(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/positiveAmount"} |
| parameters.changes.currency_id | integer | 可选（可能有条件限制） |  | 币种ID | {"minimum":1} |
| parameters.changes.journal_id | integer | 可选（可能有条件限制） |  | 日记账ID | {"minimum":1} |
| parameters.changes.payment_method_line_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.changes.date | string | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.changes.payment_reference | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"oneOf":[{"type":"null"},{"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| parameters.changes.payment_reference | null | 分支约束 | oneOf[1] |  |  |
| parameters.changes.payment_reference | string | 分支约束 | oneOf[2] |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment.update_draft"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment.update_draft"} |
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
- `idempotency`：requested_target_state_hash_and_result_replay
- `reverse`：payment.update_draft_with_prior_values

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the non-empty changes, draft-only mutation, exact confirmation, fixed bridge action, replay, and CLI response contract.；引用：tests/unit/test_payment_bank_writes.py, tests/unit/test_payment_bank_writes_runtime.py, tests/unit/test_payment_bank_write_cli.py
- `integration`：`implemented`；The shared live smoke verifies execution and rollback in both dedicated isolated database aliases.；引用：tests/integration/test_payment_bank_capability_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment-validate"></a>

## payment.validate — 确认无分录付款完成

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured caller/company and native ACLs. Bank assignment uses native eligible recipient/company accounts without changing trust. Accounting destination changes require draft payment and entry. Sent-status actions require in-process manual method. Manual validation is only for no-entry payments; journal-backed settlement uses reconciliation. Rejection requires in-process sent payment. Native duplicate warnings are candidates, not proof of duplication; they may include different currencies. No external transfer, bank submission, receipt send or caller-sudo.
- 内部domain：`payments`；来源模型：account.move, account.move.line, account.payment, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.move.line:create, account.move.line:read, account.move.line:write, account.move:create, account.move:read, account.move:write, account.payment:read, account.payment:write, res.company:read。
- 请求/响应合同：`schemas/v1/payment.validate.request.schema.json` / `schemas/v1/payment.validate.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment.validate --request "@request.json" --idempotency-key "payment.validate:1:f0c8de7167ff8d9ffb4c486ead6bbdd4" --confirm "payment.validate"
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
    "payment_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_id"]} |
| parameters.payment_id | integer | 必填（所在对象出现时） |  | 付款/收款记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment.validate"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment.validate"} |
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
- `execute`：fixed_native_payment_fields_or_state_action
- `verify`：same_transaction_native_payload_recheck
- `idempotency`：native_desired_payload_or_state_recheck
- `reverse`：native_previous_assignment_or_existing_payment_reset_subject_to_acl_and_state

### 已登记测试与证据范围

- `unit`：`implemented`；Closed schemas, fixed CLI/ORM dispatch, native eligibility and state boundaries, deterministic keys and read/write scope.；引用：tests/unit/test_payment_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all eight new IDs, three existing setup/recovery IDs and eleven immediate replays; native recipient/company bank eligibility, scoped keyset duplicate warnings, unchanged bank trust, actual destination account in the posted balanced entry, native sent/unset and rejected/reset lifecycle, truthful posted bank change without rewriting its entry, and native no-entry validation. Invalid state, journal-backed validation, foreign company and ineligible bank denied; fresh-cursor business-data and temporary-group rollback verified. No bank/provider submission, external receipt delivery, addon or service changes.；引用：tests/integration/test_payment_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment_term-archive"></a>

## payment_term.archive — 停用付款条件

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user.
- 内部domain：`accounting_configuration`；来源模型：res.company, account.payment.term；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.payment.term:read, account.payment.term:write。
- 请求/响应合同：`schemas/v1/payment_term.archive.request.schema.json` / `schemas/v1/payment_term.archive.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment_term.archive --request "@request.json" --idempotency-key "payment_term.archive:1" --confirm "payment_term.archive"
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
    "payment_term_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_term_id"]} |
| parameters.payment_term_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment_term.archive"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment_term.archive"} |
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
- `execute`：fixed_payment_term_archive_as_configured_business_user
- `verify`：same_transaction_inactive_state_reread_and_response_schema_validation
- `idempotency`：target_active_state_recheck_without_operation_store
- `reverse`：payment_term.restore

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed target contract, company and manager gates, replay, schemas, and CLI dispatch.；引用：tests/unit/test_procurement_inventory_writes.py, tests/unit/test_payment_term_accrual_writes_runtime.py, tests/unit/test_payment_term_accrual_write_schemas.py, tests/unit/test_core_write_cli.py
- `integration`：`implemented`；The guarded shared transactional smoke verifies archive and rollback in both isolated databases.；引用：tests/integration/test_accounting_followup_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment_term-compute"></a>

## payment_term.compute — 试算付款期限及提前付款折扣

- 类型：只读；静态状态：`unconfigured`；handler：`payment_term_compute`。
- 状态原因：`runtime_context_required` — Fixed read-only native calculation; configured database, ordinary caller permissions and company context are required.
- 内部domain：`accounting_master_data`；来源模型：account.cash.rounding, account.payment.term, account.payment.term.line, res.company, res.currency；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.cash.rounding:read, account.payment.term.line:read, account.payment.term:read, res.company:read, res.currency:read。
- 请求/响应合同：`schemas/v1/payment_term.compute.request.schema.json` / `schemas/v1/payment_term.compute.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read payment_term.compute --request "@request.json"
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
    "payment_term_id": 1,
    "date_ref": "2026-10-31",
    "currency_id": 1,
    "tax_amount": "1",
    "tax_amount_currency": "1",
    "untaxed_amount": "1",
    "untaxed_amount_currency": "1"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_term_id","date_ref","currency_id","tax_amount","tax_amount_currency","untaxed_amount","untaxed_amount_currency"]} |
| parameters.payment_term_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.date_ref | string | 必填（所在对象出现时） |  |  | {"format":"date","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}$(?![\\s\\S])"} |
| parameters.currency_id | integer | 必填（所在对象出现时） |  | 币种ID | {"minimum":1} |
| parameters.tax_amount | string | 必填（所在对象出现时） |  |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| parameters.tax_amount_currency | string | 必填（所在对象出现时） |  |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| parameters.untaxed_amount | string | 必填（所在对象出现时） |  |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| parameters.untaxed_amount_currency | string | 必填（所在对象出现时） |  |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| parameters.sign | integer | 可选（可能有条件限制） |  |  | {"enum":[-1,1]} |
| parameters.cash_rounding_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payment_term.compute"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","currency_id","company_currency_id","input","total_amount","discount_percentage","discount_date","discount_balance","discount_amount_currency","line_ids"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.currency_id | integer | 必填（所在对象出现时） | oneOf[2] | 币种ID | {"minimum":1} |
| response.data.company_currency_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.input | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["payment_term_id","date_ref","currency_id","tax_amount","tax_amount_currency","untaxed_amount","untaxed_amount_currency","sign","cash_rounding_id"]} |
| response.data.input.payment_term_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.input.date_ref | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}$(?![\\s\\S])"} |
| response.data.input.currency_id | integer | 必填（所在对象出现时） | oneOf[2] | 币种ID | {"minimum":1} |
| response.data.input.tax_amount | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.input.tax_amount_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.input.untaxed_amount | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.input.untaxed_amount_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.input.sign | integer | 必填（所在对象出现时） | oneOf[2] |  | {"enum":[-1,1]} |
| response.data.input.cash_rounding_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.total_amount | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.discount_percentage | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?)$(?![\\s\\S])"} |
| response.data.discount_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}$(?![\\s\\S])"} |
| response.data.discount_balance | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.discount_amount_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.line_ids | array | 必填（所在对象出现时） | oneOf[2] | 行记录ID数组 |  |
| response.data.line_ids[] | object | 每个数组元素 | oneOf[2] | 行记录ID数组 | {"additionalProperties":false,"required_in_object":["date","company_amount","foreign_amount"]} |
| response.data.line_ids[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}$(?![\\s\\S])"} |
| response.data.line_ids[].company_amount | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.line_ids[].foreign_amount | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","currency_id","company_currency_id","input","total_amount","discount_percentage","discount_date","discount_balance","discount_amount_currency","line_ids"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.currency_id | integer | 必填（所在对象出现时） | allOf[1]/then | 币种ID | {"minimum":1} |
| response.data.company_currency_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.input | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["payment_term_id","date_ref","currency_id","tax_amount","tax_amount_currency","untaxed_amount","untaxed_amount_currency","sign","cash_rounding_id"]} |
| response.data.input.payment_term_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.input.date_ref | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}$(?![\\s\\S])"} |
| response.data.input.currency_id | integer | 必填（所在对象出现时） | allOf[1]/then | 币种ID | {"minimum":1} |
| response.data.input.tax_amount | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.input.tax_amount_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.input.untaxed_amount | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.input.untaxed_amount_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.input.sign | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":[-1,1]} |
| response.data.input.cash_rounding_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.total_amount | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.discount_percentage | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?)$(?![\\s\\S])"} |
| response.data.discount_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}$(?![\\s\\S])"} |
| response.data.discount_balance | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.discount_amount_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.line_ids | array | 必填（所在对象出现时） | allOf[1]/then | 行记录ID数组 |  |
| response.data.line_ids[] | object | 每个数组元素 | allOf[1]/then | 行记录ID数组 | {"additionalProperties":false,"required_in_object":["date","company_amount","foreign_amount"]} |
| response.data.line_ids[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}$(?![\\s\\S])"} |
| response.data.line_ids[].company_amount | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
| response.data.line_ids[].foreign_amount | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;-?(?:0\\.[0-9]*[1-9]&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$(?![\\s\\S])"} |
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
- `execute`：native_payment_term_compute_terms_with_explicit_signed_company_and_foreign_totals
- `verify`：closed_native_result_identity_company_currency_and_complete_normalized_input_echo
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Focused closed preview inputs/results, native scopes, optional field normalization and unchanged legacy omission/key tests; execution is required before acceptance.；引用：tests/unit/test_accounting_settlement_batch.py
- `integration`：`implemented`；Shared public CLI/native ORM workflow passed both isolated aliases in 21.89s as uid5/su=False/company1. Tax/invoice and installment/schedule consumers, signed nonzero discount cash rounding, nullable tax-group accounts, statement start/end/replay, foreign denials, preserved financial graphs and full fresh rollback verified. Callers supply both currencies and already-cash-rounded totals; native Float residuals stay unchanged. Transaction-only roles, no sudo business calls. Tax-closing/CABA posting, all hierarchy/localization/precision paths, automatic FX, sends and concurrent exactly-once are not claimed. Details: docs/execution/STATUS.md.；引用：tests/integration/test_accounting_settlement_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment_term-create"></a>

## payment_term.create — 创建付款条件

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`odoo_payment_term_name_not_concurrency_unique` — The handler rechecks company and name for ordinary replay, but Odoo provides no database-unique operation key for concurrent exactly-once creation.
- 内部domain：`accounting_configuration`；来源模型：res.company, account.payment.term, account.payment.term.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.payment.term:read, account.payment.term:create, account.payment.term.line:read, account.payment.term.line:create。
- 请求/响应合同：`schemas/v1/payment_term.create.request.schema.json` / `schemas/v1/payment_term.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment_term.create --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "payment_term.create"
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
    "company_id": 1,
    "lines": [
      {
        "value": "percent",
        "value_amount": "100",
        "delay_type": "days_after",
        "nb_days": 1
      }
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"if":{"properties":{"early_discount":{"const":true}},"required":["early_discount"]},"then":{"properties":{"discount_days":{"minimum":1,"type":"integer"},"discount_percentage":{"$ref":"#/$defs/positive_percentage_decimal"},"lines":{"items":{"allOf":[{"$ref":"#/$defs/line"},{"properties":{"value":{"const":"percent"},"value_amount":{"const":"100"}}}]},"maxItems":1}},"required":["discount_percentage","discount_days"]}}],"required_in_object":["name","company_id","lines"]} |
| parameters.name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","resolved_ref":"#/$defs/name"} |
| parameters.company_id | integer | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| parameters.sequence | integer | 可选（可能有条件限制） |  |  | {"minimum":0} |
| parameters.note | string/null | 可选（可能有条件限制） |  |  | {"maxLength":5000,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","resolved_ref":"#/$defs/note"} |
| parameters.display_on_invoice | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.early_discount | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.discount_percentage | string | 可选（可能有条件限制） |  |  | {"maxLength":256,"pattern":"^(?:0&#124;100&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]*[1-9])?)$(?![\\s\\S])","resolved_ref":"#/$defs/percentage_decimal"} |
| parameters.discount_days | integer | 可选（可能有条件限制） |  |  | {"minimum":0} |
| parameters.early_pay_discount_computation | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["included","excluded","mixed"]} |
| parameters.lines | array | 必填（所在对象出现时） |  | 行数组；增补/更新/替换语义由能力ID决定 | {"minItems":1} |
| parameters.lines[] | object | 每个数组元素 |  | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"allOf":[{"if":{"properties":{"value":{"const":"percent"}},"required":["value"]},"then":{"properties":{"value_amount":{"$ref":"#/$defs/percentage_decimal"}}}}],"required_in_object":["value","value_amount","delay_type","nb_days"],"resolved_ref":"#/$defs/line"} |
| parameters.lines[].value | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["percent","fixed"]} |
| parameters.lines[].value_amount | string | 必填（所在对象出现时） |  |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegative_decimal"} |
| parameters.lines[].delay_type | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["days_after","days_after_end_of_month","days_after_end_of_next_month","days_end_of_month_on_the"]} |
| parameters.lines[].nb_days | integer | 必填（所在对象出现时） |  |  | {"minimum":0} |
| parameters.lines[].days_next_month | integer | 可选（可能有条件限制） |  |  | {"maximum":31,"minimum":0} |
| parameters.lines[] | 组合/开放结构 | 分支约束 | allOf[1] | 行数组；增补/更新/替换语义由能力ID决定 | {"if":{"properties":{"value":{"const":"percent"}},"required":["value"]},"then":{"properties":{"value_amount":{"$ref":"#/$defs/percentage_decimal"}}}} |
| parameters.lines[] | 未限定 | 条件分支 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| parameters.lines[].value_amount | string | 可选（可能有条件限制） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;100&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]*[1-9])?)$(?![\\s\\S])","resolved_ref":"#/$defs/percentage_decimal"} |
| parameters | 组合/开放结构 | 分支约束 | allOf[1] |  | {"if":{"properties":{"early_discount":{"const":true}},"required":["early_discount"]},"then":{"properties":{"discount_days":{"minimum":1,"type":"integer"},"discount_percentage":{"$ref":"#/$defs/positive_percentage_decimal"},"lines":{"items":{"allOf":[{"$ref":"#/$defs/line"},{"properties":{"value":{"const":"percent"},"value_amount":{"const":"100"}}}]},"maxItems":1}},"required":["discount_percentage","discount_days"]}} |
| parameters | 未限定 | 条件分支 | allOf[1]/then |  | {"required_in_object":["discount_percentage","discount_days"]} |
| parameters.discount_percentage | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:100&#124;(?:[1-9]&#124;[1-9][0-9])(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/positive_percentage_decimal"} |
| parameters.discount_days | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| parameters.lines | 未限定 | 可选（可能有条件限制） | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":1} |
| parameters.lines[] | 组合/开放结构 | 每个数组元素 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"allOf":[{"$ref":"#/$defs/line"},{"properties":{"value":{"const":"percent"},"value_amount":{"const":"100"}}}]} |
| parameters.lines[] | object | 分支约束 | allOf[1]/then/allOf[1] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"allOf":[{"if":{"properties":{"value":{"const":"percent"}},"required":["value"]},"then":{"properties":{"value_amount":{"$ref":"#/$defs/percentage_decimal"}}}}],"required_in_object":["value","value_amount","delay_type","nb_days"],"resolved_ref":"#/$defs/line"} |
| parameters.lines[].value | 未限定 | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"enum":["percent","fixed"]} |
| parameters.lines[].value_amount | string | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegative_decimal"} |
| parameters.lines[].delay_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"enum":["days_after","days_after_end_of_month","days_after_end_of_next_month","days_end_of_month_on_the"]} |
| parameters.lines[].nb_days | integer | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"minimum":0} |
| parameters.lines[].days_next_month | integer | 可选（可能有条件限制） | allOf[1]/then/allOf[1] |  | {"maximum":31,"minimum":0} |
| parameters.lines[] | 组合/开放结构 | 分支约束 | allOf[1]/then/allOf[1]/allOf[1] | 行数组；增补/更新/替换语义由能力ID决定 | {"if":{"properties":{"value":{"const":"percent"}},"required":["value"]},"then":{"properties":{"value_amount":{"$ref":"#/$defs/percentage_decimal"}}}} |
| parameters.lines[] | 未限定 | 条件分支 | allOf[1]/then/allOf[1]/allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| parameters.lines[].value_amount | string | 可选（可能有条件限制） | allOf[1]/then/allOf[1]/allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;100&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]*[1-9])?)$(?![\\s\\S])","resolved_ref":"#/$defs/percentage_decimal"} |
| parameters.lines[] | 未限定 | 分支约束 | allOf[1]/then/allOf[2] | 行数组；增补/更新/替换语义由能力ID决定 |  |
| parameters.lines[].value | 未限定 | 可选（可能有条件限制） | allOf[1]/then/allOf[2] |  | {"const":"percent"} |
| parameters.lines[].value_amount | 未限定 | 可选（可能有条件限制） | allOf[1]/then/allOf[2] |  | {"const":"100"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment_term.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment_term.create"} |
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
- `execute`：fixed_company_payment_term_create_as_configured_business_user
- `verify`：same_transaction_header_lines_and_response_schema_validation
- `idempotency`：company_and_name_natural_key_recheck_without_database_uniqueness
- `reverse`：payment_term.archive

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed header and line contract, company and manager gates, replay, schemas, and CLI dispatch.；引用：tests/unit/test_procurement_inventory_writes.py, tests/unit/test_payment_term_accrual_writes_runtime.py, tests/unit/test_payment_term_accrual_write_schemas.py, tests/unit/test_core_write_cli.py
- `integration`：`implemented`；The guarded shared transactional smoke verifies payment-term creation and rollback in both isolated databases.；引用：tests/integration/test_accounting_followup_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment_term-delete"></a>

## payment_term.delete — 删除未被单据引用的付款条件

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured user/company and native ACLs. Reads actual invoice needed_terms including native currencies, maturity/discount dates and amounts; this is a computed plan, not actual payment or residual proof. Usage is scoped to visible shared/own terms and same-company documents. Mutations only target owned terms; duplicate may read a shared term and create an independent company-owned copy. Child writes use one parent write and native savepoint, preserving IDs/order and native total/early-discount constraints; fixed amounts and days follow native signed semantics. Native final line is the residual regardless of its amount type; there is no invented sequence/order field. Referenced-term deletion and missing targets remain native errors, not fake replay. No posted-entry rewrite, external delivery, arbitrary fields/methods or caller-sudo.
- 内部domain：`accounting_configuration`；来源模型：account.move, account.payment.term, account.payment.term.line, res.company；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.move:read, account.payment.term.line:read, account.payment.term.line:unlink, account.payment.term:read, account.payment.term:unlink, res.company:read。
- 请求/响应合同：`schemas/v1/payment_term.delete.request.schema.json` / `schemas/v1/payment_term.delete.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment_term.delete --request "@request.json" --idempotency-key "payment_term.delete:1:e0012d95cd059b2312abdcb60085693d" --confirm "payment_term.delete"
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
    "payment_term_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_term_id"]} |
| parameters.payment_term_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment_term.delete"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment_term.delete"} |
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
- `execute`：fixed_native_term_copy_or_atomic_parent_line_commands
- `verify`：native_payload_reread_in_one_savepoint
- `idempotency`：serial_native_payload_matching_with_ambiguous_or_missing_target_denial
- `reverse`：previous_configuration_or_backup_subject_to_native_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Closed request/result ownership, native line shapes, atomic ID-preserving updates, fixed routing, schemas, access denials and actual invoice schedule normalization.；引用：tests/unit/test_payment_term_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all eight new IDs, five existing setup IDs and six immediate replays; native owned/shared term copies with independent child IDs, individual and atomic line edits preserving IDs, native failed percentage/early-discount mutations rolled back per call, actual taxed foreign-currency installment and early-discount schedules, posted entries unchanged by configuration changes, scoped ID-keyset usage reads including archived terms, unused-term deletion/cascade and native referenced-term deletion denial. Wrong-parent/company, shared-term mutation, changed-source copy and missing targets denied. Fresh-cursor business-data and temporary-group rollback verified. No payment, external delivery, addon or service changes.；引用：tests/integration/test_payment_term_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment_term-duplicate"></a>

## payment_term.duplicate — 复制付款条件和分期行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured user/company and native ACLs. Reads actual invoice needed_terms including native currencies, maturity/discount dates and amounts; this is a computed plan, not actual payment or residual proof. Usage is scoped to visible shared/own terms and same-company documents. Mutations only target owned terms; duplicate may read a shared term and create an independent company-owned copy. Child writes use one parent write and native savepoint, preserving IDs/order and native total/early-discount constraints; fixed amounts and days follow native signed semantics. Native final line is the residual regardless of its amount type; there is no invented sequence/order field. Referenced-term deletion and missing targets remain native errors, not fake replay. No posted-entry rewrite, external delivery, arbitrary fields/methods or caller-sudo.
- 内部domain：`accounting_configuration`；来源模型：account.payment.term, account.payment.term.line, res.company；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.payment.term.line:create, account.payment.term.line:read, account.payment.term:create, account.payment.term:read, account.payment.term:write, res.company:read。
- 请求/响应合同：`schemas/v1/payment_term.duplicate.request.schema.json` / `schemas/v1/payment_term.duplicate.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment_term.duplicate --request "@request.json" --idempotency-key "payment_term.duplicate:1:81c82e1437627106d4fce64dde640266" --confirm "payment_term.duplicate"
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
    "payment_term_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["name","payment_term_id"]} |
| parameters.payment_term_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":256,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment_term.duplicate"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment_term.duplicate"} |
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
- `execute`：fixed_native_term_copy_or_atomic_parent_line_commands
- `verify`：native_payload_reread_in_one_savepoint
- `idempotency`：serial_native_payload_matching_with_ambiguous_or_missing_target_denial
- `reverse`：previous_configuration_or_backup_subject_to_native_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Closed request/result ownership, native line shapes, atomic ID-preserving updates, fixed routing, schemas, access denials and actual invoice schedule normalization.；引用：tests/unit/test_payment_term_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all eight new IDs, five existing setup IDs and six immediate replays; native owned/shared term copies with independent child IDs, individual and atomic line edits preserving IDs, native failed percentage/early-discount mutations rolled back per call, actual taxed foreign-currency installment and early-discount schedules, posted entries unchanged by configuration changes, scoped ID-keyset usage reads including archived terms, unused-term deletion/cascade and native referenced-term deletion denial. Wrong-parent/company, shared-term mutation, changed-source copy and missing targets denied. Fresh-cursor business-data and temporary-group rollback verified. No payment, external delivery, addon or service changes.；引用：tests/integration/test_payment_term_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment_term-get"></a>

## payment_term.get — 获取付款条件详情

- 类型：只读；静态状态：`unconfigured`；handler：`payment_term_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`payment_terms`；来源模型：res.company, account.payment.term, account.payment.term.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.payment.term:read, account.payment.term.line:read。
- 请求/响应合同：`schemas/v1/payment_term.get.request.schema.json` / `schemas/v1/payment_term.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read payment_term.get --request "@request.json"
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
    "payment_term_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_term_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.payment_term_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"payment_term.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payment_term.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"payment_term.list.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","sequence","name","active","company_id","display_on_invoice","early_discount","discount_percentage","discount_days","early_pay_discount_computation","lines"],"resolved_ref":"payment_term.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.sequence | integer | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.company_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.display_on_invoice | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.early_discount | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.discount_percentage | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.discount_days | integer | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.early_pay_discount_computation | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["included","excluded","mixed"]} |
| response.data.lines | array | 必填（所在对象出现时） | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"minItems":1} |
| response.data.lines[] | object | 每个数组元素 | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","value","value_amount","delay_type","nb_days","days_next_month"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].value | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["percent","fixed"]} |
| response.data.lines[].value_amount | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].delay_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["days_after","days_after_end_of_month","days_after_end_of_next_month","days_end_of_month_on_the"]} |
| response.data.lines[].nb_days | integer | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.lines[].days_next_month | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"pattern":"^(?:[0-9]&#124;[12][0-9]&#124;3[01])$","type":"string"}]} |
| response.data.lines[].days_next_month | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].days_next_month | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"pattern":"^(?:[0-9]&#124;[12][0-9]&#124;3[01])$"} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"payment_term.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","sequence","name","active","company_id","display_on_invoice","early_discount","discount_percentage","discount_days","early_pay_discount_computation","lines"],"resolved_ref":"payment_term.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.sequence | integer | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.company_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.display_on_invoice | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.early_discount | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.discount_percentage | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.discount_days | integer | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.early_pay_discount_computation | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["included","excluded","mixed"]} |
| response.data.lines | array | 必填（所在对象出现时） | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"minItems":1} |
| response.data.lines[] | object | 每个数组元素 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","value","value_amount","delay_type","nb_days","days_next_month"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].value | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["percent","fixed"]} |
| response.data.lines[].value_amount | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].delay_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["days_after","days_after_end_of_month","days_after_end_of_next_month","days_end_of_month_on_the"]} |
| response.data.lines[].nb_days | integer | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.lines[].days_next_month | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"pattern":"^(?:[0-9]&#124;[12][0-9]&#124;3[01])$","type":"string"}]} |
| response.data.lines[].days_next_month | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].days_next_month | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"pattern":"^(?:[0-9]&#124;[12][0-9]&#124;3[01])$"} |
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

<a id="cap-payment_term-line-create"></a>

## payment_term.line.create — 新增付款条件分期行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured user/company and native ACLs. Reads actual invoice needed_terms including native currencies, maturity/discount dates and amounts; this is a computed plan, not actual payment or residual proof. Usage is scoped to visible shared/own terms and same-company documents. Mutations only target owned terms; duplicate may read a shared term and create an independent company-owned copy. Child writes use one parent write and native savepoint, preserving IDs/order and native total/early-discount constraints; fixed amounts and days follow native signed semantics. Native final line is the residual regardless of its amount type; there is no invented sequence/order field. Referenced-term deletion and missing targets remain native errors, not fake replay. No posted-entry rewrite, external delivery, arbitrary fields/methods or caller-sudo.
- 内部domain：`accounting_configuration`；来源模型：account.payment.term, account.payment.term.line, res.company；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.payment.term.line:create, account.payment.term.line:read, account.payment.term:read, account.payment.term:write, res.company:read。
- 请求/响应合同：`schemas/v1/payment_term.line.create.request.schema.json` / `schemas/v1/payment_term.line.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment_term.line.create --request "@request.json" --idempotency-key "payment_term.line.create:1:f56d8941b01def98919ca180204749a1" --confirm "payment_term.line.create"
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
      "days_next_month": 1,
      "delay_type": "days_after",
      "nb_days": 1,
      "value": "percent",
      "value_amount": "100"
    },
    "payment_term_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["line","payment_term_id"]} |
| parameters.payment_term_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.line | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"allOf":[{"if":{"properties":{"value":{"const":"percent"}},"required":["value"]},"then":{"properties":{"value_amount":{"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])","type":"string"}}}}],"required_in_object":["days_next_month","delay_type","nb_days","value","value_amount"]} |
| parameters.line.value | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["percent","fixed"]} |
| parameters.line.value_amount | string | 必填（所在对象出现时） |  |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| parameters.line.delay_type | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["days_after","days_after_end_of_month","days_after_end_of_next_month","days_end_of_month_on_the"]} |
| parameters.line.nb_days | integer | 必填（所在对象出现时） |  |  | {"maximum":2147483647,"minimum":-2147483648} |
| parameters.line.days_next_month | integer | 必填（所在对象出现时） |  |  | {"maximum":31,"minimum":0} |
| parameters.line | 组合/开放结构 | 分支约束 | allOf[1] |  | {"if":{"properties":{"value":{"const":"percent"}},"required":["value"]},"then":{"properties":{"value_amount":{"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])","type":"string"}}}} |
| parameters.line | 未限定 | 条件分支 | allOf[1]/then |  |  |
| parameters.line.value_amount | string | 可选（可能有条件限制） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment_term.line.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment_term.line.create"} |
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
- `execute`：fixed_native_term_copy_or_atomic_parent_line_commands
- `verify`：native_payload_reread_in_one_savepoint
- `idempotency`：serial_native_payload_matching_with_ambiguous_or_missing_target_denial
- `reverse`：previous_configuration_or_backup_subject_to_native_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Closed request/result ownership, native line shapes, atomic ID-preserving updates, fixed routing, schemas, access denials and actual invoice schedule normalization.；引用：tests/unit/test_payment_term_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all eight new IDs, five existing setup IDs and six immediate replays; native owned/shared term copies with independent child IDs, individual and atomic line edits preserving IDs, native failed percentage/early-discount mutations rolled back per call, actual taxed foreign-currency installment and early-discount schedules, posted entries unchanged by configuration changes, scoped ID-keyset usage reads including archived terms, unused-term deletion/cascade and native referenced-term deletion denial. Wrong-parent/company, shared-term mutation, changed-source copy and missing targets denied. Fresh-cursor business-data and temporary-group rollback verified. No payment, external delivery, addon or service changes.；引用：tests/integration/test_payment_term_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment_term-line-delete"></a>

## payment_term.line.delete — 删除付款条件分期行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured user/company and native ACLs. Reads actual invoice needed_terms including native currencies, maturity/discount dates and amounts; this is a computed plan, not actual payment or residual proof. Usage is scoped to visible shared/own terms and same-company documents. Mutations only target owned terms; duplicate may read a shared term and create an independent company-owned copy. Child writes use one parent write and native savepoint, preserving IDs/order and native total/early-discount constraints; fixed amounts and days follow native signed semantics. Native final line is the residual regardless of its amount type; there is no invented sequence/order field. Referenced-term deletion and missing targets remain native errors, not fake replay. No posted-entry rewrite, external delivery, arbitrary fields/methods or caller-sudo.
- 内部domain：`accounting_configuration`；来源模型：account.payment.term, account.payment.term.line, res.company；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.payment.term.line:read, account.payment.term.line:unlink, account.payment.term:read, account.payment.term:write, res.company:read。
- 请求/响应合同：`schemas/v1/payment_term.line.delete.request.schema.json` / `schemas/v1/payment_term.line.delete.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment_term.line.delete --request "@request.json" --idempotency-key "payment_term.line.delete:1:fa9cb0395d0342f2043dfe6a231217cd" --confirm "payment_term.line.delete"
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
    "payment_term_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["line_id","payment_term_id"]} |
| parameters.payment_term_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment_term.line.delete"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment_term.line.delete"} |
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
- `execute`：fixed_native_term_copy_or_atomic_parent_line_commands
- `verify`：native_payload_reread_in_one_savepoint
- `idempotency`：serial_native_payload_matching_with_ambiguous_or_missing_target_denial
- `reverse`：previous_configuration_or_backup_subject_to_native_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Closed request/result ownership, native line shapes, atomic ID-preserving updates, fixed routing, schemas, access denials and actual invoice schedule normalization.；引用：tests/unit/test_payment_term_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all eight new IDs, five existing setup IDs and six immediate replays; native owned/shared term copies with independent child IDs, individual and atomic line edits preserving IDs, native failed percentage/early-discount mutations rolled back per call, actual taxed foreign-currency installment and early-discount schedules, posted entries unchanged by configuration changes, scoped ID-keyset usage reads including archived terms, unused-term deletion/cascade and native referenced-term deletion denial. Wrong-parent/company, shared-term mutation, changed-source copy and missing targets denied. Fresh-cursor business-data and temporary-group rollback verified. No payment, external delivery, addon or service changes.；引用：tests/integration/test_payment_term_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment_term-line-update"></a>

## payment_term.line.update — 修改付款条件分期行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured user/company and native ACLs. Reads actual invoice needed_terms including native currencies, maturity/discount dates and amounts; this is a computed plan, not actual payment or residual proof. Usage is scoped to visible shared/own terms and same-company documents. Mutations only target owned terms; duplicate may read a shared term and create an independent company-owned copy. Child writes use one parent write and native savepoint, preserving IDs/order and native total/early-discount constraints; fixed amounts and days follow native signed semantics. Native final line is the residual regardless of its amount type; there is no invented sequence/order field. Referenced-term deletion and missing targets remain native errors, not fake replay. No posted-entry rewrite, external delivery, arbitrary fields/methods or caller-sudo.
- 内部domain：`accounting_configuration`；来源模型：account.payment.term, account.payment.term.line, res.company；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.payment.term.line:read, account.payment.term.line:write, account.payment.term:read, account.payment.term:write, res.company:read。
- 请求/响应合同：`schemas/v1/payment_term.line.update.request.schema.json` / `schemas/v1/payment_term.line.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment_term.line.update --request "@request.json" --idempotency-key "payment_term.line.update:1:715da3a7bfaba45249d4c1d55755fea4" --confirm "payment_term.line.update"
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
      "value": "percent"
    },
    "line_id": 1,
    "payment_term_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["changes","line_id","payment_term_id"]} |
| parameters.payment_term_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"allOf":[{"if":{"properties":{"value":{"const":"percent"}},"required":["value"]},"then":{"properties":{"value_amount":{"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])","type":"string"}}}}],"minProperties":1,"required_in_object":[]} |
| parameters.changes.value | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["percent","fixed"]} |
| parameters.changes.value_amount | string | 可选（可能有条件限制） |  |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| parameters.changes.delay_type | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["days_after","days_after_end_of_month","days_after_end_of_next_month","days_end_of_month_on_the"]} |
| parameters.changes.nb_days | integer | 可选（可能有条件限制） |  |  | {"maximum":2147483647,"minimum":-2147483648} |
| parameters.changes.days_next_month | integer | 可选（可能有条件限制） |  |  | {"maximum":31,"minimum":0} |
| parameters.changes | 组合/开放结构 | 分支约束 | allOf[1] | 仅提交拟变更字段，非整条记录 | {"if":{"properties":{"value":{"const":"percent"}},"required":["value"]},"then":{"properties":{"value_amount":{"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])","type":"string"}}}} |
| parameters.changes | 未限定 | 条件分支 | allOf[1]/then | 仅提交拟变更字段，非整条记录 |  |
| parameters.changes.value_amount | string | 可选（可能有条件限制） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment_term.line.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment_term.line.update"} |
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
- `execute`：fixed_native_term_copy_or_atomic_parent_line_commands
- `verify`：native_payload_reread_in_one_savepoint
- `idempotency`：serial_native_payload_matching_with_ambiguous_or_missing_target_denial
- `reverse`：previous_configuration_or_backup_subject_to_native_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Closed request/result ownership, native line shapes, atomic ID-preserving updates, fixed routing, schemas, access denials and actual invoice schedule normalization.；引用：tests/unit/test_payment_term_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all eight new IDs, five existing setup IDs and six immediate replays; native owned/shared term copies with independent child IDs, individual and atomic line edits preserving IDs, native failed percentage/early-discount mutations rolled back per call, actual taxed foreign-currency installment and early-discount schedules, posted entries unchanged by configuration changes, scoped ID-keyset usage reads including archived terms, unused-term deletion/cascade and native referenced-term deletion denial. Wrong-parent/company, shared-term mutation, changed-source copy and missing targets denied. Fresh-cursor business-data and temporary-group rollback verified. No payment, external delivery, addon or service changes.；引用：tests/integration/test_payment_term_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment_term-lines-replace"></a>

## payment_term.lines.replace — 替换付款条件行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user.
- 内部domain：`accounting_configuration`；来源模型：res.company, account.payment.term, account.payment.term.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.payment.term:read, account.payment.term:write, account.payment.term.line:read, account.payment.term.line:create, account.payment.term.line:write, account.payment.term.line:unlink。
- 请求/响应合同：`schemas/v1/payment_term.lines.replace.request.schema.json` / `schemas/v1/payment_term.lines.replace.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment_term.lines.replace --request "@request.json" --idempotency-key "payment_term.lines.replace:1:7c43ac6004452446704762d96555927c" --confirm "payment_term.lines.replace"
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
    "payment_term_id": 1,
    "lines": [
      {
        "value": "percent",
        "value_amount": "100",
        "delay_type": "days_after",
        "nb_days": 1
      }
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_term_id","lines"]} |
| parameters.payment_term_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.lines | array | 必填（所在对象出现时） |  | 行数组；增补/更新/替换语义由能力ID决定 | {"minItems":1} |
| parameters.lines[] | object | 每个数组元素 |  | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"allOf":[{"if":{"properties":{"value":{"const":"percent"}},"required":["value"]},"then":{"properties":{"value_amount":{"$ref":"#/$defs/percentage_decimal"}}}}],"required_in_object":["value","value_amount","delay_type","nb_days"],"resolved_ref":"#/$defs/line"} |
| parameters.lines[].value | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["percent","fixed"]} |
| parameters.lines[].value_amount | string | 必填（所在对象出现时） |  |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegative_decimal"} |
| parameters.lines[].delay_type | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["days_after","days_after_end_of_month","days_after_end_of_next_month","days_end_of_month_on_the"]} |
| parameters.lines[].nb_days | integer | 必填（所在对象出现时） |  |  | {"minimum":0} |
| parameters.lines[].days_next_month | integer | 可选（可能有条件限制） |  |  | {"maximum":31,"minimum":0} |
| parameters.lines[] | 组合/开放结构 | 分支约束 | allOf[1] | 行数组；增补/更新/替换语义由能力ID决定 | {"if":{"properties":{"value":{"const":"percent"}},"required":["value"]},"then":{"properties":{"value_amount":{"$ref":"#/$defs/percentage_decimal"}}}} |
| parameters.lines[] | 未限定 | 条件分支 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| parameters.lines[].value_amount | string | 可选（可能有条件限制） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;100&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]*[1-9])?)$(?![\\s\\S])","resolved_ref":"#/$defs/percentage_decimal"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment_term.lines.replace"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment_term.lines.replace"} |
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
- `execute`：fixed_payment_term_line_replacement_as_configured_business_user
- `verify`：same_transaction_exact_lines_reread_and_response_schema_validation
- `idempotency`：target_line_state_recheck_without_operation_store
- `reverse`：replace_with_previous_payment_term_lines

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover percent totals, early-discount constraints, native delay types, company gates, replay, schemas, and CLI dispatch.；引用：tests/unit/test_procurement_inventory_writes.py, tests/unit/test_payment_term_accrual_writes_runtime.py, tests/unit/test_payment_term_accrual_write_schemas.py, tests/unit/test_core_write_cli.py
- `integration`：`implemented`；The guarded shared transactional smoke verifies line replacement and rollback in both isolated databases.；引用：tests/integration/test_accounting_followup_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment_term-lines-update"></a>

## payment_term.lines.update — 成组修改付款条件分期行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires configured user/company and native ACLs. Reads actual invoice needed_terms including native currencies, maturity/discount dates and amounts; this is a computed plan, not actual payment or residual proof. Usage is scoped to visible shared/own terms and same-company documents. Mutations only target owned terms; duplicate may read a shared term and create an independent company-owned copy. Child writes use one parent write and native savepoint, preserving IDs/order and native total/early-discount constraints; fixed amounts and days follow native signed semantics. Native final line is the residual regardless of its amount type; there is no invented sequence/order field. Referenced-term deletion and missing targets remain native errors, not fake replay. No posted-entry rewrite, external delivery, arbitrary fields/methods or caller-sudo.
- 内部domain：`accounting_configuration`；来源模型：account.payment.term, account.payment.term.line, res.company；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.payment.term.line:read, account.payment.term.line:write, account.payment.term:read, account.payment.term:write, res.company:read。
- 请求/响应合同：`schemas/v1/payment_term.lines.update.request.schema.json` / `schemas/v1/payment_term.lines.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment_term.lines.update --request "@request.json" --idempotency-key "payment_term.lines.update:1:c4ab21493613e76a14de520d75bc4c4c" --confirm "payment_term.lines.update"
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
    "lines": [
      {
        "changes": {
          "value": "percent"
        },
        "line_id": 1
      },
      {
        "changes": {
          "value": "percent"
        },
        "line_id": 2
      }
    ],
    "payment_term_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["lines","payment_term_id"]} |
| parameters.payment_term_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.lines | array | 必填（所在对象出现时） |  | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":100,"minItems":2} |
| parameters.lines[] | object | 每个数组元素 |  | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["changes","line_id"]} |
| parameters.lines[].line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.lines[].changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"allOf":[{"if":{"properties":{"value":{"const":"percent"}},"required":["value"]},"then":{"properties":{"value_amount":{"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])","type":"string"}}}}],"minProperties":1,"required_in_object":[]} |
| parameters.lines[].changes.value | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["percent","fixed"]} |
| parameters.lines[].changes.value_amount | string | 可选（可能有条件限制） |  |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| parameters.lines[].changes.delay_type | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["days_after","days_after_end_of_month","days_after_end_of_next_month","days_end_of_month_on_the"]} |
| parameters.lines[].changes.nb_days | integer | 可选（可能有条件限制） |  |  | {"maximum":2147483647,"minimum":-2147483648} |
| parameters.lines[].changes.days_next_month | integer | 可选（可能有条件限制） |  |  | {"maximum":31,"minimum":0} |
| parameters.lines[].changes | 组合/开放结构 | 分支约束 | allOf[1] | 仅提交拟变更字段，非整条记录 | {"if":{"properties":{"value":{"const":"percent"}},"required":["value"]},"then":{"properties":{"value_amount":{"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])","type":"string"}}}} |
| parameters.lines[].changes | 未限定 | 条件分支 | allOf[1]/then | 仅提交拟变更字段，非整条记录 |  |
| parameters.lines[].changes.value_amount | string | 可选（可能有条件限制） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:100(?:\\.0+)?&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]+)?)$(?![\\s\\S])"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment_term.lines.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment_term.lines.update"} |
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
- `execute`：fixed_native_term_copy_or_atomic_parent_line_commands
- `verify`：native_payload_reread_in_one_savepoint
- `idempotency`：serial_native_payload_matching_with_ambiguous_or_missing_target_denial
- `reverse`：previous_configuration_or_backup_subject_to_native_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Closed request/result ownership, native line shapes, atomic ID-preserving updates, fixed routing, schemas, access denials and actual invoice schedule normalization.；引用：tests/unit/test_payment_term_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all eight new IDs, five existing setup IDs and six immediate replays; native owned/shared term copies with independent child IDs, individual and atomic line edits preserving IDs, native failed percentage/early-discount mutations rolled back per call, actual taxed foreign-currency installment and early-discount schedules, posted entries unchanged by configuration changes, scoped ID-keyset usage reads including archived terms, unused-term deletion/cascade and native referenced-term deletion denial. Wrong-parent/company, shared-term mutation, changed-source copy and missing targets denied. Fresh-cursor business-data and temporary-group rollback verified. No payment, external delivery, addon or service changes.；引用：tests/integration/test_payment_term_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment_term-list"></a>

## payment_term.list — 列出付款条件

- 类型：只读；静态状态：`unconfigured`；handler：`payment_term_list`。
- 状态原因：`runtime_context_required` — Static registry metadata does not declare target-specific runtime availability; availability is evaluated for each configured database, company, and user.
- 内部domain：`payment_terms`；来源模型：account.payment.term, account.payment.term.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.payment.term:read, account.payment.term.line:read。
- 请求/响应合同：`schemas/v1/payment_term.list.request.schema.json` / `schemas/v1/payment_term.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read payment_term.list --request "@request.json"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payment_term.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","sequence","name","active","company_id","display_on_invoice","early_discount","discount_percentage","discount_days","early_pay_discount_computation","lines"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].sequence | integer | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].company_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].display_on_invoice | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].early_discount | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].discount_percentage | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].discount_days | integer | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].early_pay_discount_computation | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["included","excluded","mixed"]} |
| response.data.items[].lines | array | 必填（所在对象出现时） | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"minItems":1} |
| response.data.items[].lines[] | object | 每个数组元素 | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","value","value_amount","delay_type","nb_days","days_next_month"],"resolved_ref":"#/$defs/line"} |
| response.data.items[].lines[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].lines[].value | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["percent","fixed"]} |
| response.data.items[].lines[].value_amount | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].lines[].delay_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["days_after","days_after_end_of_month","days_after_end_of_next_month","days_end_of_month_on_the"]} |
| response.data.items[].lines[].nb_days | integer | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].lines[].days_next_month | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"pattern":"^(?:[0-9]&#124;[12][0-9]&#124;3[01])$","type":"string"}]} |
| response.data.items[].lines[].days_next_month | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].lines[].days_next_month | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"pattern":"^(?:[0-9]&#124;[12][0-9]&#124;3[01])$"} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","sequence","name","active","company_id","display_on_invoice","early_discount","discount_percentage","discount_days","early_pay_discount_computation","lines"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].sequence | integer | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].company_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].display_on_invoice | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].early_discount | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].discount_percentage | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].discount_days | integer | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].early_pay_discount_computation | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["included","excluded","mixed"]} |
| response.data.items[].lines | array | 必填（所在对象出现时） | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"minItems":1} |
| response.data.items[].lines[] | object | 每个数组元素 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","value","value_amount","delay_type","nb_days","days_next_month"],"resolved_ref":"#/$defs/line"} |
| response.data.items[].lines[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].lines[].value | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["percent","fixed"]} |
| response.data.items[].lines[].value_amount | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].lines[].delay_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["days_after","days_after_end_of_month","days_after_end_of_next_month","days_end_of_month_on_the"]} |
| response.data.items[].lines[].nb_days | integer | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].lines[].days_next_month | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"pattern":"^(?:[0-9]&#124;[12][0-9]&#124;3[01])$","type":"string"}]} |
| response.data.items[].lines[].days_next_month | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].lines[].days_next_month | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"pattern":"^(?:[0-9]&#124;[12][0-9]&#124;3[01])$"} |
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
- `execute`：local_read_only_odoo_bridge
- `verify`：same_transaction_acl_result_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the strict cursor, fixed bridge action, Odoo row normalization, and response contract.；引用：tests/unit/test_master_data_lists.py, tests/unit/test_master_data_bridge.py, tests/unit/test_master_data_runtime.py
- `integration`：`implemented`；The live integration test verifies the real local read-only Odoo bridge against both dedicated synthetic database aliases, including strict schema validation and two-page cursor ordering without overlap.；引用：tests/integration/test_master_data_lists_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment_term-restore"></a>

## payment_term.restore — 恢复付款条件

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user.
- 内部domain：`accounting_configuration`；来源模型：res.company, account.payment.term；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.payment.term:read, account.payment.term:write。
- 请求/响应合同：`schemas/v1/payment_term.restore.request.schema.json` / `schemas/v1/payment_term.restore.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment_term.restore --request "@request.json" --idempotency-key "payment_term.restore:1" --confirm "payment_term.restore"
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
    "payment_term_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_term_id"]} |
| parameters.payment_term_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment_term.restore"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment_term.restore"} |
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
- `execute`：fixed_payment_term_restore_as_configured_business_user
- `verify`：same_transaction_active_state_reread_and_response_schema_validation
- `idempotency`：target_active_state_recheck_without_operation_store
- `reverse`：payment_term.archive

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed target contract, company and manager gates, replay, schemas, and CLI dispatch.；引用：tests/unit/test_procurement_inventory_writes.py, tests/unit/test_payment_term_accrual_writes_runtime.py, tests/unit/test_payment_term_accrual_write_schemas.py, tests/unit/test_core_write_cli.py
- `integration`：`implemented`；The guarded shared transactional smoke verifies restore and rollback in both isolated databases.；引用：tests/integration/test_accounting_followup_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment_term-update"></a>

## payment_term.update — 更新付款条件

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user.
- 内部domain：`accounting_configuration`；来源模型：res.company, account.payment.term；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.payment.term:read, account.payment.term:write。
- 请求/响应合同：`schemas/v1/payment_term.update.request.schema.json` / `schemas/v1/payment_term.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run payment_term.update --request "@request.json" --idempotency-key "payment_term.update:1:603ff4b70ceeeda2a87631465b1a7089" --confirm "payment_term.update"
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
    "payment_term_id": 1,
    "sequence": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"if":{"properties":{"early_discount":{"const":true}},"required":["early_discount"]},"then":{"properties":{"discount_days":{"minimum":1,"type":"integer"},"discount_percentage":{"$ref":"#/$defs/positive_percentage_decimal"}},"required":["discount_percentage","discount_days"]}}],"minProperties":2,"required_in_object":["payment_term_id"]} |
| parameters.payment_term_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.sequence | integer | 可选（可能有条件限制） |  |  | {"minimum":0} |
| parameters.note | string/null | 可选（可能有条件限制） |  |  | {"maxLength":5000,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","resolved_ref":"#/$defs/note"} |
| parameters.display_on_invoice | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.early_discount | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.discount_percentage | string | 可选（可能有条件限制） |  |  | {"maxLength":256,"pattern":"^(?:0&#124;100&#124;(?:[0-9]&#124;[1-9][0-9])(?:\\.[0-9]*[1-9])?)$(?![\\s\\S])","resolved_ref":"#/$defs/percentage_decimal"} |
| parameters.discount_days | integer | 可选（可能有条件限制） |  |  | {"minimum":0} |
| parameters.early_pay_discount_computation | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["included","excluded","mixed"]} |
| parameters | 组合/开放结构 | 分支约束 | allOf[1] |  | {"if":{"properties":{"early_discount":{"const":true}},"required":["early_discount"]},"then":{"properties":{"discount_days":{"minimum":1,"type":"integer"},"discount_percentage":{"$ref":"#/$defs/positive_percentage_decimal"}},"required":["discount_percentage","discount_days"]}} |
| parameters | 未限定 | 条件分支 | allOf[1]/then |  | {"required_in_object":["discount_percentage","discount_days"]} |
| parameters.discount_percentage | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:100&#124;(?:[1-9]&#124;[1-9][0-9])(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/positive_percentage_decimal"} |
| parameters.discount_days | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"payment_term.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"payment_term.update"} |
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
- `execute`：fixed_company_payment_term_header_update_as_configured_business_user
- `verify`：same_transaction_header_reread_and_response_schema_validation
- `idempotency`：target_header_state_recheck_without_operation_store
- `reverse`：payment_term.update_with_prior_values

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed header patch contract, company and manager gates, replay, schemas, and CLI dispatch.；引用：tests/unit/test_procurement_inventory_writes.py, tests/unit/test_payment_term_accrual_writes_runtime.py, tests/unit/test_payment_term_accrual_write_schemas.py, tests/unit/test_core_write_cli.py
- `integration`：`implemented`；The guarded shared transactional smoke verifies payment-term update and rollback in both isolated databases.；引用：tests/integration/test_accounting_followup_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-payment_term-usage_moves-list"></a>

## payment_term.usage_moves.list — 查询付款条件使用单据

- 类型：只读；静态状态：`unconfigured`；handler：`payment_term_usage_moves_list`。
- 状态原因：`runtime_context_required` — Requires configured user/company and native ACLs. Reads actual invoice needed_terms including native currencies, maturity/discount dates and amounts; this is a computed plan, not actual payment or residual proof. Usage is scoped to visible shared/own terms and same-company documents. Mutations only target owned terms; duplicate may read a shared term and create an independent company-owned copy. Child writes use one parent write and native savepoint, preserving IDs/order and native total/early-discount constraints; fixed amounts and days follow native signed semantics. Native final line is the residual regardless of its amount type; there is no invented sequence/order field. Referenced-term deletion and missing targets remain native errors, not fake replay. No posted-entry rewrite, external delivery, arbitrary fields/methods or caller-sudo.
- 内部domain：`accounting_configuration`；来源模型：res.company, account.payment.term, account.move, res.partner, res.currency；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.payment.term:read, account.move:read, res.partner:read, res.currency:read。
- 请求/响应合同：`schemas/v1/payment_term.usage_moves.list.request.schema.json` / `schemas/v1/payment_term.usage_moves.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read payment_term.usage_moves.list --request "@request.json"
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
    "payment_term_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["payment_term_id"]} |
| parameters.payment_term_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"payment_term.usage_moves.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["amount_residual","amount_total","company_id","currency_id","date","id","invoice_date","invoice_payment_term_id","move_type","name","partner_id","state"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].invoice_payment_term_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.items[].name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 |  |
| response.data.items[].partner_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 合作伙伴ID | {"minimum":1} |
| response.data.items[].currency_id | integer | 必填（所在对象出现时） | oneOf[2] | 币种ID | {"minimum":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].invoice_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].amount_total | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.items[].amount_residual | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["amount_residual","amount_total","company_id","currency_id","date","id","invoice_date","invoice_payment_term_id","move_type","name","partner_id","state"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].invoice_payment_term_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.items[].name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 |  |
| response.data.items[].partner_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 合作伙伴ID | {"minimum":1} |
| response.data.items[].currency_id | integer | 必填（所在对象出现时） | allOf[1]/then | 币种ID | {"minimum":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].invoice_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].amount_total | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.items[].amount_residual | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
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
- `execute`：fixed_native_needed_terms_or_scoped_usage_read
- `verify`：closed_response_schema_validation
- `idempotency`：read_only
- `reverse`：not_applicable

### 已登记测试与证据范围

- `unit`：`implemented`；Closed request/result ownership, native line shapes, atomic ID-preserving updates, fixed routing, schemas, access denials and actual invoice schedule normalization.；引用：tests/unit/test_payment_term_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5 with su=False: all eight new IDs, five existing setup IDs and six immediate replays; native owned/shared term copies with independent child IDs, individual and atomic line edits preserving IDs, native failed percentage/early-discount mutations rolled back per call, actual taxed foreign-currency installment and early-discount schedules, posted entries unchanged by configuration changes, scoped ID-keyset usage reads including archived terms, unused-term deletion/cascade and native referenced-term deletion denial. Wrong-parent/company, shared-term mutation, changed-source copy and missing targets denied. Fresh-cursor business-data and temporary-group rollback verified. No payment, external delivery, addon or service changes.；引用：tests/integration/test_payment_term_processing_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-receivable-open_items-list"></a>

## receivable.open_items.list — 列出应收未清项

- 类型：只读；静态状态：`unconfigured`；handler：`receivable_open_items_list`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`receivables_payables`；来源模型：account.move.line, account.move, account.account, account.journal, res.partner, res.currency；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move.line:read, account.move:read, account.account:read, account.journal:read, res.partner:read, res.currency:read。
- 请求/响应合同：`schemas/v1/receivable.open_items.list.request.schema.json` / `schemas/v1/receivable.open_items.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read receivable.open_items.list --request "@request.json"
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
| parameters.due_date_from | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"default":null,"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| parameters.due_date_from | null | 分支约束 | oneOf[1] |  |  |
| parameters.due_date_from | string | 分支约束 | oneOf[2] |  | {"format":"date"} |
| parameters.due_date_to | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"default":null,"oneOf":[{"type":"null"},{"format":"date","type":"string"}],"resolved_ref":"#/$defs/nullableDate"} |
| parameters.due_date_to | null | 分支约束 | oneOf[1] |  |  |
| parameters.due_date_to | string | 分支约束 | oneOf[2] |  | {"format":"date"} |
| parameters.partner_id | integer/null | 可选（可能有条件限制） |  | 合作伙伴ID | {"default":null,"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.account_id | integer/null | 可选（可能有条件限制） |  | 会计科目ID | {"default":null,"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.journal_id | integer/null | 可选（可能有条件限制） |  | 日记账ID | {"default":null,"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.currency_id | integer/null | 可选（可能有条件限制） |  | 币种ID | {"default":null,"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.move_id | integer | 可选（可能有条件限制） |  | 会计单据记录ID | {"minimum":1} |
| parameters.invoice_user_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.payment_term_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.fiscal_position_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.move_types | array | 可选（可能有条件限制） |  |  | {"maxItems":7,"minItems":1,"uniqueItems":true} |
| parameters.move_types[] | 未限定 | 每个数组元素 |  |  | {"enum":["entry","out_invoice","out_refund","in_invoice","in_refund","out_receipt","in_receipt"]} |
| parameters.query | 组合/开放结构 | 可选（可能有条件限制） |  | 搜索文本 | {"default":null,"oneOf":[{"type":"null"},{"allOf":[{"not":{"pattern":"^\\s"}},{"not":{"pattern":"\\s$"}}],"maxLength":200,"minLength":1,"type":"string"}]} |
| parameters.query | null | 分支约束 | oneOf[1] | 搜索文本 |  |
| parameters.query | string | 分支约束 | oneOf[2] | 搜索文本 | {"allOf":[{"not":{"pattern":"^\\s"}},{"not":{"pattern":"\\s$"}}],"maxLength":200,"minLength":1} |
| parameters.query | 组合/开放结构 | 分支约束 | oneOf[2]/allOf[1] | 搜索文本 | {"not":{"pattern":"^\\s"}} |
| parameters.query | 组合/开放结构 | 分支约束 | oneOf[2]/allOf[2] | 搜索文本 | {"not":{"pattern":"\\s$"}} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"receivable.open_items.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","side","date","due_date","name","ref","move","journal","company_id","partner","account","currency","company_currency","debit","credit","balance","amount_currency","amount_residual","amount_residual_currency","reconciled","matching_number"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].side | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":"receivable"} |
| response.data.items[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].due_date | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}]} |
| response.data.items[].due_date | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].due_date | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.items[].name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].name | null | 分支约束 | oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].name | string | 分支约束 | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].ref | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].ref | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].ref | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.items[].move | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state"],"resolved_ref":"#/$defs/move"} |
| response.data.items[].move.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].move.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].move.move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["entry","out_invoice","out_refund","in_invoice","in_refund","out_receipt","in_receipt"]} |
| response.data.items[].move.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"const":"posted"} |
| response.data.items[].journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/journal"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":5,"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.items[].partner | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","reference"],"resolved_ref":"#/$defs/partner"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].partner.name | null | 分支约束 | oneOf[2]/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].partner.name | string | 分支约束 | oneOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].partner.reference | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].partner.reference | null | 分支约束 | oneOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.items[].partner.reference | string | 分支约束 | oneOf[2]/oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.items[].account | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name","account_type","non_trade"],"resolved_ref":"#/$defs/account"} |
| response.data.items[].account.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].account.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].account.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].account.account_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":"asset_receivable"} |
| response.data.items[].account.non_trade | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].company_currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].company_currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].debit | string | 必填（所在对象出现时） | oneOf[2] | 借方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].credit | string | 必填（所在对象出现时） | oneOf[2] | 贷方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].balance | string | 必填（所在对象出现时） | oneOf[2] | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_currency | string | 必填（所在对象出现时） | oneOf[2] | 外币/交易币数值，非默认公司币金额 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_residual | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_residual_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].reconciled | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":false} |
| response.data.items[].matching_number | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].matching_number | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].matching_number | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","side","date","due_date","name","ref","move","journal","company_id","partner","account","currency","company_currency","debit","credit","balance","amount_currency","amount_residual","amount_residual_currency","reconciled","matching_number"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].side | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"const":"receivable"} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].due_date | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}]} |
| response.data.items[].due_date | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].due_date | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date"} |
| response.data.items[].name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].name | null | 分支约束 | allOf[1]/then/oneOf[1] | 名称/行说明 |  |
| response.data.items[].name | string | 分支约束 | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].ref | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].ref | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].ref | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.items[].move | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state"],"resolved_ref":"#/$defs/move"} |
| response.data.items[].move.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].move.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].move.move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["entry","out_invoice","out_refund","in_invoice","in_refund","out_receipt","in_receipt"]} |
| response.data.items[].move.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"const":"posted"} |
| response.data.items[].journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/journal"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":5,"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.items[].partner | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","reference"],"resolved_ref":"#/$defs/partner"} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].partner.name | null | 分支约束 | allOf[1]/then/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].partner.name | string | 分支约束 | allOf[1]/then/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].partner.reference | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].partner.reference | null | 分支约束 | allOf[1]/then/oneOf[2]/oneOf[1] |  |  |
| response.data.items[].partner.reference | string | 分支约束 | allOf[1]/then/oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.items[].account | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name","account_type","non_trade"],"resolved_ref":"#/$defs/account"} |
| response.data.items[].account.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].account.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].account.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].account.account_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"const":"asset_receivable"} |
| response.data.items[].account.non_trade | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].company_currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].company_currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].debit | string | 必填（所在对象出现时） | allOf[1]/then | 借方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].credit | string | 必填（所在对象出现时） | allOf[1]/then | 贷方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].balance | string | 必填（所在对象出现时） | allOf[1]/then | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_currency | string | 必填（所在对象出现时） | allOf[1]/then | 外币/交易币数值，非默认公司币金额 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_residual | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_residual_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].reconciled | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"const":false} |
| response.data.items[].matching_number | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].matching_number | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].matching_number | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
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

- `unit`：`implemented`；Existing contracts and optional native same-line/header search filters covered.；引用：tests/unit/test_open_items.py, tests/unit/test_open_items_bridge.py, tests/unit/test_open_items_cli.py, tests/unit/test_open_items_runtime.py, tests/unit/test_document_search_batch_contract.py, tests/unit/test_document_search_batch_runtime.py, tests/unit/test_document_search_header_runtime.py, tests/unit/test_document_search_batch_cli.py, tests/unit/test_invoice_business_line_filters_contract.py, tests/unit/test_document_business_filters_runtime.py, tests/unit/test_business_line_search_remove_cli.py
- `integration`：`implemented`；Shared native business-line search and bulk deletion smoke passed; full rollback.；引用：tests/integration/test_open_items_live.py, tests/integration/test_document_search_bulk_lines_live.py, tests/integration/test_business_line_search_remove_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-receivable-payment-register"></a>

## receivable.payment.register — 登记客户发票收款（支持多发票合并）或退款

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime. Explicit installment/group options use native next/overdue/before-date/full amounts and actual payment graphs; editable grouped batches support partial amounts. Operation markers distinguish sequential rounds but are not concurrency-unique.
- 内部domain：`payments`；来源模型：res.company, account.account, account.journal, account.move, account.move.line, account.payment, account.payment.register, account.partial.reconcile, account.full.reconcile, account.payment.method.line, res.partner.bank；向导：account.payment.register。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：account.account:read, account.journal:read, account.move:read, account.move.line:read, account.payment:read, account.payment:create, account.payment.register:create, account.move.line:write, account.partial.reconcile:read, account.partial.reconcile:create, account.full.reconcile:read, account.payment.method.line:read, res.partner.bank:read。
- 请求/响应合同：`schemas/v1/receivable.payment.register.request.schema.json` / `schemas/v1/receivable.payment.register.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run receivable.payment.register --request "@request.json" --idempotency-key "receivable.payment.register:1" --confirm "receivable.payment.register"
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
    "journal_id": 1,
    "payment_date": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"installment_cutoff_date":false}},"if":{"properties":{"installments_mode":{"const":"before_date"}},"required":["installments_mode"]},"then":{"required":["installment_cutoff_date"]}},{"if":{"properties":{"group_payment":{"const":false}},"required":["group_payment"]},"then":{"properties":{"amount":false}}}],"else":{"properties":{"writeoff_account_id":false,"writeoff_label":false}},"if":{"properties":{"payment_difference_handling":{"const":"reconcile"}},"required":["payment_difference_handling"]},"oneOf":[{"properties":{"move_ids":false},"required":["move_id"]},{"properties":{"move_id":false},"required":["move_ids"]}],"required_in_object":["journal_id","payment_date"],"then":{"required":["amount","writeoff_account_id"]}} |
| parameters.move_id | integer | 可选（可能有条件限制） |  | 会计单据记录ID | {"minimum":1} |
| parameters.move_ids | array | 可选（可能有条件限制） |  | 会计单据ID数组 | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| parameters.move_ids[] | integer | 每个数组元素 |  | 会计单据ID数组 | {"minimum":1} |
| parameters.journal_id | integer | 必填（所在对象出现时） |  | 日记账ID | {"minimum":1} |
| parameters.payment_method_line_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.partner_bank_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.payment_date | string | 必填（所在对象出现时） |  |  | {"format":"date"} |
| parameters.installments_mode | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["full","next","overdue","before_date"]} |
| parameters.group_payment | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.installment_cutoff_date | string | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.amount | string | 可选（可能有条件限制） |  | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/positive_canonical_decimal"} |
| parameters.payment_difference_handling | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["open","reconcile"]} |
| parameters.writeoff_account_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.writeoff_label | string | 可选（可能有条件限制） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |
| parameters | 未限定 | 分支约束 | oneOf[1] |  | {"required_in_object":["move_id"]} |
| parameters.move_ids | 禁止 | 可选（可能有条件限制） | oneOf[1] |  | false |
| parameters | 未限定 | 分支约束 | oneOf[2] |  | {"required_in_object":["move_ids"]} |
| parameters.move_id | 禁止 | 可选（可能有条件限制） | oneOf[2] |  | false |
| parameters | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"installment_cutoff_date":false}},"if":{"properties":{"installments_mode":{"const":"before_date"}},"required":["installments_mode"]},"then":{"required":["installment_cutoff_date"]}} |
| parameters | 未限定 | 条件分支 | allOf[1]/then |  | {"required_in_object":["installment_cutoff_date"]} |
| parameters | 未限定 | 条件分支 | allOf[1]/else |  |  |
| parameters.installment_cutoff_date | 禁止 | 可选（可能有条件限制） | allOf[1]/else |  | false |
| parameters | 组合/开放结构 | 分支约束 | allOf[2] |  | {"if":{"properties":{"group_payment":{"const":false}},"required":["group_payment"]},"then":{"properties":{"amount":false}}} |
| parameters | 未限定 | 条件分支 | allOf[2]/then |  |  |
| parameters.amount | 禁止 | 可选（可能有条件限制） | allOf[2]/then |  | false |
| parameters | 未限定 | 条件分支 | then |  | {"required_in_object":["amount","writeoff_account_id"]} |
| parameters | 未限定 | 条件分支 | else |  |  |
| parameters.writeoff_account_id | 禁止 | 可选（可能有条件限制） | else |  | false |
| parameters.writeoff_label | 禁止 | 可选（可能有条件限制） | else |  | false |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"#/$defs/payment_batch"}]},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"receivable.payment.register"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"},{"$ref":"#/$defs/payment_batch"}]} |
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
| response.data | object | 分支约束 | oneOf[3] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"#/$defs/payment_batch"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | oneOf[3] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | oneOf[3] |  | {"additionalProperties":false,"required_in_object":["items","processed_count"]} |
| response.data.result.items | array | 必填（所在对象出现时） | oneOf[3] |  | {"maxItems":1000,"minItems":1,"uniqueItems":true} |
| response.data.result.items[] | 组合/开放结构 | 每个数组元素 | oneOf[3] |  | {"allOf":[{"$ref":"core-write-result.schema.json#/properties/result"},{"properties":{"id":{"minimum":1,"type":"integer"},"model":{"const":"account.payment"},"move_type":{"type":"null"}}}]} |
| response.data.result.items[] | object | 分支约束 | oneOf[3]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"],"resolved_ref":"core-write-result.schema.json#/properties/result"} |
| response.data.result.items[].model | string | 必填（所在对象出现时） | oneOf[3]/allOf[1] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].id | integer/null | 必填（所在对象出现时） | oneOf[3]/allOf[1] |  | {"minimum":1} |
| response.data.result.items[].name | string/null | 必填（所在对象出现时） | oneOf[3]/allOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.result.items[].state | string | 必填（所在对象出现时） | oneOf[3]/allOf[1] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].company_id | integer | 必填（所在对象出现时） | oneOf[3]/allOf[1] | 所选公司ID | {"minimum":1} |
| response.data.result.items[].move_type | string/null | 必填（所在对象出现时） | oneOf[3]/allOf[1] |  | {"minLength":1} |
| response.data.result.items[].source_id | integer/null | 必填（所在对象出现时） | oneOf[3]/allOf[1] |  | {"minimum":1} |
| response.data.result.items[].line_ids | array | 必填（所在对象出现时） | oneOf[3]/allOf[1] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.items[].line_ids[] | integer | 每个数组元素 | oneOf[3]/allOf[1] | 行记录ID数组 | {"minimum":1} |
| response.data.result.items[].partial_reconcile_ids | array | 必填（所在对象出现时） | oneOf[3]/allOf[1] |  | {"uniqueItems":true} |
| response.data.result.items[].partial_reconcile_ids[] | integer | 每个数组元素 | oneOf[3]/allOf[1] |  | {"minimum":1} |
| response.data.result.items[].full_reconcile_id | integer/null | 必填（所在对象出现时） | oneOf[3]/allOf[1] | 完整核销关系ID | {"minimum":1} |
| response.data.result.items[].reconciled | boolean | 必填（所在对象出现时） | oneOf[3]/allOf[1] |  |  |
| response.data.result.items[] | 未限定 | 分支约束 | oneOf[3]/allOf[2] |  |  |
| response.data.result.items[].model | 未限定 | 可选（可能有条件限制） | oneOf[3]/allOf[2] |  | {"const":"account.payment"} |
| response.data.result.items[].id | integer | 可选（可能有条件限制） | oneOf[3]/allOf[2] |  | {"minimum":1} |
| response.data.result.items[].move_type | null | 可选（可能有条件限制） | oneOf[3]/allOf[2] |  |  |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | oneOf[3] |  | {"maximum":1000,"minimum":1} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"#/$defs/payment_batch"}]},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then |  | {"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"#/$defs/payment_batch"}]} |
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
| response.data | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"#/$defs/payment_batch"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","processed_count"]} |
| response.data.result.items | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"maxItems":1000,"minItems":1,"uniqueItems":true} |
| response.data.result.items[] | 组合/开放结构 | 每个数组元素 | allOf[1]/then/oneOf[2] |  | {"allOf":[{"$ref":"core-write-result.schema.json#/properties/result"},{"properties":{"id":{"minimum":1,"type":"integer"},"model":{"const":"account.payment"},"move_type":{"type":"null"}}}]} |
| response.data.result.items[] | object | 分支约束 | allOf[1]/then/oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"],"resolved_ref":"core-write-result.schema.json#/properties/result"} |
| response.data.result.items[].model | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] |  | {"minimum":1} |
| response.data.result.items[].name | string/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.result.items[].state | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] | 所选公司ID | {"minimum":1} |
| response.data.result.items[].move_type | string/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] |  | {"minLength":1} |
| response.data.result.items[].source_id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] |  | {"minimum":1} |
| response.data.result.items[].line_ids | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.items[].line_ids[] | integer | 每个数组元素 | allOf[1]/then/oneOf[2]/allOf[1] | 行记录ID数组 | {"minimum":1} |
| response.data.result.items[].partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] |  | {"uniqueItems":true} |
| response.data.result.items[].partial_reconcile_ids[] | integer | 每个数组元素 | allOf[1]/then/oneOf[2]/allOf[1] |  | {"minimum":1} |
| response.data.result.items[].full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] | 完整核销关系ID | {"minimum":1} |
| response.data.result.items[].reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then/oneOf[2]/allOf[1] |  |  |
| response.data.result.items[] | 未限定 | 分支约束 | allOf[1]/then/oneOf[2]/allOf[2] |  |  |
| response.data.result.items[].model | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[2]/allOf[2] |  | {"const":"account.payment"} |
| response.data.result.items[].id | integer | 可选（可能有条件限制） | allOf[1]/then/oneOf[2]/allOf[2] |  | {"minimum":1} |
| response.data.result.items[].move_type | null | 可选（可能有条件限制） | allOf[1]/then/oneOf[2]/allOf[2] |  |  |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"maximum":1000,"minimum":1} |
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
- `execute`：fixed_single_or_full_grouped_invoice_payment_registration_as_configured_business_user
- `verify`：same_transaction_single_or_grouped_residual_and_replay_validation
- `idempotency`：single_document_legacy_key_or_company_and_normalized_batch_digest_with_odoo_persisted_business_marker_and_result_replay
- `reverse`：payment.cancel

### 已登记测试与证据范围

- `unit`：`implemented`；Existing contracts and explicit payment/tax input extensions are covered.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_payment_register_writeoff_runtime.py, tests/unit/test_payment_register_many_contract.py, tests/unit/test_payment_register_many_runtime.py, tests/unit/test_core_write_cli.py, tests/unit/test_accounting_payment_tax_inputs_batch.py, tests/unit/test_entry_payment_explicit_inputs_contract.py, tests/unit/test_payment_tax_input_runtime.py, tests/unit/test_invoice_rounds_write_contract.py, tests/unit/test_invoice_rounds_runtime.py, tests/unit/test_invoice_rounds_product_reads.py, tests/unit/test_invoice_rounds_cli.py
- `integration`：`implemented`；Shared native payment/tax smoke passed; full rollback.；引用：tests/integration/test_core_write_batch_live.py, tests/integration/test_accounting_depth_batch_live.py, tests/integration/test_invoice_cash_refund_batch_live.py, tests/integration/test_payment_register_many_batch_live.py, tests/integration/test_accounting_payment_tax_inputs_batch_live.py, tests/integration/test_invoice_rounds_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-aged_payable"></a>

## report.aged_payable — 生成应付账龄报告

- 类型：只读；静态状态：`unconfigured`；handler：`report_aged_payable`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line, res.partner；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read, res.partner:read。
- 请求/响应合同：`schemas/v1/report.aged_payable.request.schema.json` / `schemas/v1/report.aged_payable.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.aged_payable --request "@request.json"
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
    "as_of": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["as_of"],"resolved_ref":"#/$defs/parameters"} |
| parameters.as_of | string | 必填（所在对象出现时） |  | 截至日期 | {"format":"date"} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.aged_payable"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"aged_payable"}}}}}]}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2] |  | {"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"aged_payable"}}}}}]} |
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
| response.data.report.key | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"aged_payable"} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  |  |
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
- `execute`：fixed_odoo_aged_payable_report_handler
- `verify`：rollback_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared typed-report contract, runtime normalization, cursor binding, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_typed_financial_reports.py, tests/unit/test_typed_financial_report_runtime.py, tests/unit/test_typed_financial_report_cli.py
- `integration`：`implemented`；The shared live integration test verifies the capability against both dedicated synthetic database aliases without committing database changes.；引用：tests/integration/test_read_capability_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-aged_payable-export"></a>

## report.aged_payable.export — 导出应付账龄报告

- 类型：只读；静态状态：`unconfigured`；handler：`report_aged_payable_export`。
- 状态原因：`runtime_context_required` — The fixed native export handler is installed; availability depends on the selected database, company, user, module, configuration, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line, res.partner；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read, res.partner:read。
- 请求/响应合同：`schemas/v1/report.aged_payable.export.request.schema.json` / `schemas/v1/report.aged_payable.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.aged_payable.export --request "@request.json"
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
    "as_of": "2026-10-31",
    "format": "pdf"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["as_of","format"],"resolved_ref":"#/$defs/parameters"} |
| parameters.as_of | string | 必填（所在对象出现时） |  | 截至日期 | {"format":"date"} |
| parameters.format | 未限定 | 必填（所在对象出现时） |  | 输出格式 | {"enum":["pdf","xlsx"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.aged_payable.export"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["filename","format","mimetype","byte_count","sha256","content_base64"],"resolved_ref":"#/$defs/data"} |
| response.data.filename | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":255,"minLength":1} |
| response.data.format | 未限定 | 必填（所在对象出现时） | oneOf[2] | 输出格式 | {"enum":["pdf","xlsx"]} |
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
| response.data.format | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 输出格式 | {"enum":["pdf","xlsx"]} |
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
- `execute`：fixed_native_odoo_export_via_account.report.fixed_export
- `verify`：posted_entries_read_only_export_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover the fixed contract, bridge, Odoo runtime, CLI routing, registry metadata, and schemas.；引用：tests/unit/test_financial_report_exports.py, tests/unit/test_financial_report_export_bridge.py, tests/unit/test_financial_report_exports_runtime.py, tests/unit/test_financial_report_export_cli.py, tests/unit/test_financial_report_export_registry.py
- `integration`：`implemented`；One shared read-only live smoke covers both isolated aliases and both native export formats.；引用：tests/integration/test_financial_report_export_batch_live.py
- `golden`：`planned`；Golden export evidence is pending.；引用：无
- `e2e`：`planned`；End-to-end export evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-aged_receivable"></a>

## report.aged_receivable — 生成应收账龄报告

- 类型：只读；静态状态：`unconfigured`；handler：`report_aged_receivable`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line, res.partner；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read, res.partner:read。
- 请求/响应合同：`schemas/v1/report.aged_receivable.request.schema.json` / `schemas/v1/report.aged_receivable.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.aged_receivable --request "@request.json"
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
    "as_of": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["as_of"],"resolved_ref":"#/$defs/parameters"} |
| parameters.as_of | string | 必填（所在对象出现时） |  | 截至日期 | {"format":"date"} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.aged_receivable"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"aged_receivable"}}}}}]}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2] |  | {"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"aged_receivable"}}}}}]} |
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
| response.data.report.key | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"aged_receivable"} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  |  |
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
- `execute`：fixed_odoo_aged_receivable_report_handler
- `verify`：rollback_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared typed-report contract, runtime normalization, cursor binding, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_typed_financial_reports.py, tests/unit/test_typed_financial_report_runtime.py, tests/unit/test_typed_financial_report_cli.py
- `integration`：`implemented`；The shared live integration test verifies the capability against both dedicated synthetic database aliases without committing database changes.；引用：tests/integration/test_read_capability_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-aged_receivable-export"></a>

## report.aged_receivable.export — 导出应收账龄报告

- 类型：只读；静态状态：`unconfigured`；handler：`report_aged_receivable_export`。
- 状态原因：`runtime_context_required` — The fixed native export handler is installed; availability depends on the selected database, company, user, module, configuration, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line, res.partner；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read, res.partner:read。
- 请求/响应合同：`schemas/v1/report.aged_receivable.export.request.schema.json` / `schemas/v1/report.aged_receivable.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.aged_receivable.export --request "@request.json"
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
    "as_of": "2026-10-31",
    "format": "pdf"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["as_of","format"],"resolved_ref":"#/$defs/parameters"} |
| parameters.as_of | string | 必填（所在对象出现时） |  | 截至日期 | {"format":"date"} |
| parameters.format | 未限定 | 必填（所在对象出现时） |  | 输出格式 | {"enum":["pdf","xlsx"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.aged_receivable.export"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["filename","format","mimetype","byte_count","sha256","content_base64"],"resolved_ref":"#/$defs/data"} |
| response.data.filename | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":255,"minLength":1} |
| response.data.format | 未限定 | 必填（所在对象出现时） | oneOf[2] | 输出格式 | {"enum":["pdf","xlsx"]} |
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
| response.data.format | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 输出格式 | {"enum":["pdf","xlsx"]} |
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
- `execute`：fixed_native_odoo_export_via_account.report.fixed_export
- `verify`：posted_entries_read_only_export_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover the fixed contract, bridge, Odoo runtime, CLI routing, registry metadata, and schemas.；引用：tests/unit/test_financial_report_exports.py, tests/unit/test_financial_report_export_bridge.py, tests/unit/test_financial_report_exports_runtime.py, tests/unit/test_financial_report_export_cli.py, tests/unit/test_financial_report_export_registry.py
- `integration`：`implemented`；One shared read-only live smoke covers both isolated aliases and both native export formats.；引用：tests/integration/test_financial_report_export_batch_live.py
- `golden`：`planned`；Golden export evidence is pending.；引用：无
- `e2e`：`planned`；End-to-end export evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-customer_statement"></a>

## report.customer_statement — 生成客户对账单

- 类型：只读；静态状态：`unconfigured`；handler：`report_customer_statement`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line, res.partner；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read, res.partner:read。
- 请求/响应合同：`schemas/v1/report.customer_statement.request.schema.json` / `schemas/v1/report.customer_statement.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.customer_statement --request "@request.json"
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
    "partner_id": 1,
    "date_from": "2026-10-01",
    "date_to": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["partner_id","date_from","date_to"]} |
| parameters.partner_id | integer | 必填（所在对象出现时） |  | 合作伙伴ID | {"minimum":1} |
| parameters.date_from | string | 必填（所在对象出现时） |  | 开始日期 | {"format":"date"} |
| parameters.date_to | string | 必填（所在对象出现时） |  | 结束日期 | {"format":"date"} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.customer_statement"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"customer_statement"}}}}}]}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2] |  | {"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"customer_statement"}}}}}]} |
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
| response.data.report.key | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"customer_statement"} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  |  |
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
- `execute`：fixed_single_partner_customer_statement_report_handler
- `verify`：rollback_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared typed-report contract, fixed partner scope, runtime normalization, cursor binding, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_typed_financial_reports.py, tests/unit/test_typed_financial_report_runtime.py, tests/unit/test_typed_financial_report_cli.py
- `integration`：`implemented`；The shared read-only smoke verifies the official customer statement in both dedicated isolated database aliases.；引用：tests/integration/test_management_reporting_period_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-customer_statement-export"></a>

## report.customer_statement.export — 导出客户对账单

- 类型：只读；静态状态：`unconfigured`；handler：`report_customer_statement_export`。
- 状态原因：`runtime_context_required` — The fixed native export handler is installed; availability depends on the selected database, company, user, module, configuration, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line, res.currency, res.partner；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read, res.currency:read, res.partner:read。
- 请求/响应合同：`schemas/v1/report.customer_statement.export.request.schema.json` / `schemas/v1/report.customer_statement.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.customer_statement.export --request "@request.json"
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
    "partner_id": 1,
    "date_from": "2026-10-01",
    "date_to": "2026-10-31",
    "format": "pdf"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["partner_id","date_from","date_to","format"]} |
| parameters.partner_id | integer | 必填（所在对象出现时） |  | 合作伙伴ID | {"minimum":1} |
| parameters.date_from | string | 必填（所在对象出现时） |  | 开始日期 | {"format":"date"} |
| parameters.date_to | string | 必填（所在对象出现时） |  | 结束日期 | {"format":"date"} |
| parameters.format | 未限定 | 必填（所在对象出现时） |  | 输出格式 | {"enum":["pdf","xlsx"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.customer_statement.export"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["filename","format","mimetype","byte_count","sha256","content_base64"],"resolved_ref":"#/$defs/data"} |
| response.data.filename | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":255,"minLength":1} |
| response.data.format | 未限定 | 必填（所在对象出现时） | oneOf[2] | 输出格式 | {"enum":["pdf","xlsx"]} |
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
| response.data.format | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 输出格式 | {"enum":["pdf","xlsx"]} |
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
- `execute`：fixed_native_odoo_export_via_account.report.fixed_export
- `verify`：posted_entries_read_only_export_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover the partner-scoped export contract, bridge, runtime, registry metadata, and schemas.；引用：tests/unit/test_financial_report_exports.py, tests/unit/test_financial_report_export_bridge.py, tests/unit/test_financial_report_exports_runtime.py, tests/unit/test_financial_report_export_registry.py, tests/unit/test_accounting_delivery_registry.py
- `integration`：`implemented`；The guarded shared smoke exported and validated a customer-statement PDF on both isolated aliases as uid 5 with su=False and rollback verification.；引用：tests/integration/test_accounting_delivery_batch_live.py
- `golden`：`planned`；Golden export evidence is pending.；引用：无
- `e2e`：`planned`；End-to-end export evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-customer_statement-send"></a>

## report.customer_statement.send — 将客户对账单加入 Odoo 发送队列

- 类型：写入；静态状态：`degraded`；handler：`accounting_delivery`。
- 状态原因：`odoo_queue_delivery_only` — The fixed handler verifies its Odoo message marker after invoking the native queue-only delivery path; it does not claim mail-queue persistence or external SMTP delivery.
- 内部domain：`financial_reports`；来源模型：res.company, res.partner, account.report, account.move.line, mail.template, mail.message, mail.mail, ir.attachment；向导：account.report.send。
- 必需模块：account_reports, account, mail；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：res.company:read, res.partner:read, res.partner:write, account.report:read, account.move.line:read, mail.template:read, account.report.send:read, account.report.send:create, account.report.send:write, mail.message:read, mail.mail:read, ir.attachment:read。
- 请求/响应合同：`schemas/v1/report.customer_statement.send.request.schema.json` / `schemas/v1/report.customer_statement.send.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run report.customer_statement.send --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "report.customer_statement.send"
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
    "date_from": "2026-10-01",
    "date_to": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"oneOf":[{"required":["partner_id"]},{"required":["partner_ids"]}],"required_in_object":["date_from","date_to"]} |
| parameters.partner_id | integer | 可选（可能有条件限制） |  | 合作伙伴ID | {"minimum":1} |
| parameters.partner_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| parameters.partner_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.date_from | string | 必填（所在对象出现时） |  | 开始日期 | {"format":"date"} |
| parameters.date_to | string | 必填（所在对象出现时） |  | 结束日期 | {"format":"date"} |
| parameters | 未限定 | 分支约束 | oneOf[1] |  | {"required_in_object":["partner_id"]} |
| parameters | 未限定 | 分支约束 | oneOf[2] |  | {"required_in_object":["partner_ids"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.customer_statement.send"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"#/$defs/data"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["record_ids","processed_count"],"resolved_ref":"#/$defs/send_result"} |
| response.data.result.record_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":100,"minItems":1,"uniqueItems":true} |
| response.data.result.record_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"maximum":100,"minimum":1} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"#/$defs/data"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[1]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["record_ids","processed_count"],"resolved_ref":"#/$defs/send_result"} |
| response.data.result.record_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":100,"minItems":1,"uniqueItems":true} |
| response.data.result.record_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"maximum":100,"minimum":1} |
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
- `execute`：fixed_native_customer_statement_report_send_with_queued_delivery
- `verify`：same_transaction_marked_message_and_response_schema_validation
- `idempotency`：caller_key_marker_serial_replay_without_concurrent_or_external_transport_exactly_once_guarantee
- `reverse`：cancel_pending_mail_outside_this_capability

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover partner selection, closed date range, confirmation, result binding, registry metadata, and schemas.；引用：tests/unit/test_accounting_delivery.py, tests/unit/test_accounting_delivery_registry.py
- `integration`：`planned`；The shared dual-alias smoke verified a clean unauthorized response because configured uid 5 lacks res.partner:write; positive native report delivery remains pending for an eligible ordinary user.；引用：tests/integration/test_accounting_delivery_batch_live.py
- `golden`：`planned`；Golden queued-delivery examples are pending.；引用：无
- `e2e`：`planned`；Natural-language routing evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-followup"></a>

## report.followup — 生成应收催款报告

- 类型：只读；静态状态：`unconfigured`；handler：`report_followup`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line, res.partner；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read, res.partner:read。
- 请求/响应合同：`schemas/v1/report.followup.request.schema.json` / `schemas/v1/report.followup.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.followup --request "@request.json"
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
    "partner_id": 1,
    "as_of": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["partner_id","as_of"]} |
| parameters.partner_id | integer | 必填（所在对象出现时） |  | 合作伙伴ID | {"minimum":1} |
| parameters.as_of | string | 必填（所在对象出现时） |  | 截至日期 | {"format":"date"} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.followup"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"followup"}}}}}]}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2] |  | {"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"followup"}}}}}]} |
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
| response.data.report.key | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"followup"} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  |  |
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
- `execute`：fixed_single_partner_followup_report_handler
- `verify`：rollback_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared typed-report contract, fixed partner scope, runtime normalization, cursor binding, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_typed_financial_reports.py, tests/unit/test_typed_financial_report_runtime.py, tests/unit/test_typed_financial_report_cli.py
- `integration`：`implemented`；The shared read-only smoke verifies the official follow-up report in both dedicated isolated database aliases.；引用：tests/integration/test_management_reporting_period_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-followup-export"></a>

## report.followup.export — 导出应收催款报告

- 类型：只读；静态状态：`unconfigured`；handler：`report_followup_export`。
- 状态原因：`runtime_context_required` — The fixed native export handler is installed; availability depends on the selected database, company, user, module, configuration, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line, res.currency, res.partner；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read, res.currency:read, res.partner:read。
- 请求/响应合同：`schemas/v1/report.followup.export.request.schema.json` / `schemas/v1/report.followup.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.followup.export --request "@request.json"
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
    "partner_id": 1,
    "as_of": "2026-10-31",
    "format": "pdf"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["partner_id","as_of","format"]} |
| parameters.partner_id | integer | 必填（所在对象出现时） |  | 合作伙伴ID | {"minimum":1} |
| parameters.as_of | string | 必填（所在对象出现时） |  | 截至日期 | {"format":"date"} |
| parameters.format | 未限定 | 必填（所在对象出现时） |  | 输出格式 | {"enum":["pdf","xlsx"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.followup.export"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["filename","format","mimetype","byte_count","sha256","content_base64"],"resolved_ref":"#/$defs/data"} |
| response.data.filename | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":255,"minLength":1} |
| response.data.format | 未限定 | 必填（所在对象出现时） | oneOf[2] | 输出格式 | {"enum":["pdf","xlsx"]} |
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
| response.data.format | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 输出格式 | {"enum":["pdf","xlsx"]} |
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
- `execute`：fixed_native_odoo_export_via_account.report.fixed_export
- `verify`：posted_entries_read_only_export_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover the partner-scoped export contract, bridge, runtime, registry metadata, and schemas.；引用：tests/unit/test_financial_report_exports.py, tests/unit/test_financial_report_export_bridge.py, tests/unit/test_financial_report_exports_runtime.py, tests/unit/test_financial_report_export_registry.py, tests/unit/test_accounting_delivery_registry.py
- `integration`：`implemented`；The guarded shared smoke exported and validated a follow-up PDF on both isolated aliases as uid 5 with su=False and rollback verification.；引用：tests/integration/test_accounting_delivery_batch_live.py
- `golden`：`planned`；Golden export evidence is pending.；引用：无
- `e2e`：`planned`；End-to-end export evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-followup-send"></a>

## report.followup.send — 将应收催款报告加入 Odoo 发送队列

- 类型：写入；静态状态：`degraded`；handler：`accounting_delivery`。
- 状态原因：`odoo_queue_delivery_only` — The fixed handler verifies its Odoo message marker after invoking the native queue-only delivery path; it does not claim mail-queue persistence or external SMTP delivery.
- 内部domain：`financial_reports`；来源模型：res.company, res.partner, account.report, account.move.line, mail.template, mail.message, mail.mail, ir.attachment；向导：account.report.send。
- 必需模块：account_reports, account, mail；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：res.company:read, res.partner:read, res.partner:write, account.report:read, account.move.line:read, mail.template:read, account.report.send:read, account.report.send:create, account.report.send:write, mail.message:read, mail.mail:read, ir.attachment:read。
- 请求/响应合同：`schemas/v1/report.followup.send.request.schema.json` / `schemas/v1/report.followup.send.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run report.followup.send --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "report.followup.send"
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
    "as_of": "2026-10-31",
    "partner_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"oneOf":[{"required":["partner_id"]},{"required":["partner_ids"]}],"required_in_object":["as_of"]} |
| parameters.partner_id | integer | 可选（可能有条件限制） |  | 合作伙伴ID | {"minimum":1} |
| parameters.partner_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| parameters.partner_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.as_of | string | 必填（所在对象出现时） |  | 截至日期 | {"format":"date"} |
| parameters | 未限定 | 分支约束 | oneOf[1] |  | {"required_in_object":["partner_id"]} |
| parameters | 未限定 | 分支约束 | oneOf[2] |  | {"required_in_object":["partner_ids"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.followup.send"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"#/$defs/data"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | oneOf[2] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["record_ids","processed_count"],"resolved_ref":"#/$defs/send_result"} |
| response.data.result.record_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":100,"minItems":1,"uniqueItems":true} |
| response.data.result.record_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"maximum":100,"minimum":1} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"#/$defs/data"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[1]/then | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["record_ids","processed_count"],"resolved_ref":"#/$defs/send_result"} |
| response.data.result.record_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":100,"minItems":1,"uniqueItems":true} |
| response.data.result.record_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"maximum":100,"minimum":1} |
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
- `execute`：fixed_native_followup_report_send_with_queued_delivery
- `verify`：same_transaction_marked_message_and_response_schema_validation
- `idempotency`：caller_key_marker_serial_replay_without_concurrent_or_external_transport_exactly_once_guarantee
- `reverse`：cancel_pending_mail_outside_this_capability

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover partner selection, closed as-of date, confirmation, result binding, registry metadata, and schemas.；引用：tests/unit/test_accounting_delivery.py, tests/unit/test_accounting_delivery_registry.py
- `integration`：`planned`；The shared dual-alias smoke verified a clean unauthorized response because configured uid 5 lacks res.partner:write; positive native report delivery remains pending for an eligible ordinary user.；引用：tests/integration/test_accounting_delivery_batch_live.py
- `golden`：`planned`；Golden queued-delivery examples are pending.；引用：无
- `e2e`：`planned`；Natural-language routing evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。
