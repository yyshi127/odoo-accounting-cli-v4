# 手工凭证、分录行、冲销与凭证检查

创建、读取、编辑、过账、冲销或删除手工会计凭证，原子维护分录行，查看会计分录行及通用会计凭证的自动过账、复核和来源关联，检查序列完整性并渲染中国会计凭证。通用 accounting_move 和 journal_item 读取也可能针对发票、支付等来源凭证，不只限于手工分录；核销和分析分摊分别见对应场景。

[回到总说明书](../../CLI_V4_MANUAL.md) · [新会话使用指南](../USAGE_GUIDE.md)

<a id="cap-accounting_move-autopost-configure"></a>

## accounting_move.autopost.configure — 设置分录自动过账计划

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires explicit runtime company/user scope and native ACLs. Currency/rounding/term/method/schedule changes require draft moves; review uses the native posted-only method. Auto-post configuration schedules native future work but never runs a cron or posts a move in this command. No arbitrary field/method calls or external delivery.
- 内部domain：`accounting_documents`；来源模型：account.move, account.move.line, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.move.line:read, account.move:read, account.move:write。
- 请求/响应合同：`schemas/v1/accounting_move.autopost.configure.request.schema.json` / `schemas/v1/accounting_move.autopost.configure.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run accounting_move.autopost.configure --request "@request.json" --idempotency-key "accounting_move.autopost.configure:1:455b09bc1b381769d30d7bf0dfdab392" --confirm "accounting_move.autopost.configure"
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
    "auto_post": "at_date",
    "auto_post_until": null,
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"if":{"properties":{"auto_post":{"enum":["no","at_date"]}}},"then":{"properties":{"auto_post_until":{"type":"null"}}}}],"required_in_object":["auto_post","auto_post_until","move_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.auto_post | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["at_date","monthly","no","quarterly","yearly"]} |
| parameters.auto_post_until | string/null | 必填（所在对象出现时） |  |  | {"format":"date","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}$(?![\\s\\S])"} |
| parameters | 组合/开放结构 | 分支约束 | allOf[1] |  | {"if":{"properties":{"auto_post":{"enum":["no","at_date"]}}},"then":{"properties":{"auto_post_until":{"type":"null"}}}} |
| parameters | 未限定 | 条件分支 | allOf[1]/then |  |  |
| parameters.auto_post_until | null | 可选（可能有条件限制） | allOf[1]/then |  |  |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"accounting_move.autopost.configure"} |
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

<a id="cap-accounting_move-origin_links-inspect"></a>

## accounting_move.origin_links.inspect — 查看凭证来源关联

- 类型：只读；静态状态：`unconfigured`；handler：`accounting_move_origin_links_inspect`。
- 状态原因：`runtime_context_required` — Fixed invoice preparation and product accounting operations are implemented; runtime company, ordinary-user ACL and native accounting recomputation apply.
- 内部domain：`journal_entry`；来源模型：res.company, account.move；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move:read。
- 请求/响应合同：`schemas/v1/accounting_move.origin_links.inspect.request.schema.json` / `schemas/v1/accounting_move.origin_links.inspect.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read accounting_move.origin_links.inspect --request "@request.json"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"accounting_move.origin_links.inspect"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","move_type","state","reversed_entry","tax_cash_basis_origin_move","reversal_moves","tax_cash_basis_created_moves","adjusting_entry_origin_moves","adjusting_entries_moves"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.reversed_entry | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"additionalProperties":false,"properties":{"date":{"format":"date","type":"string"},"id":{"minimum":1,"type":"integer"},"move_type":{"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]},"name":{"minLength":1,"type":["string","null"]},"state":{"enum":["draft","posted","cancel"]}},"required":["id","name","move_type","state","date"],"type":"object"}]} |
| response.data.reversed_entry | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.reversed_entry | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","date"]} |
| response.data.reversed_entry.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.reversed_entry.name | string/null | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.reversed_entry.move_type | 未限定 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.reversed_entry.state | 未限定 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.reversed_entry.date | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.tax_cash_basis_origin_move | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"additionalProperties":false,"properties":{"date":{"format":"date","type":"string"},"id":{"minimum":1,"type":"integer"},"move_type":{"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]},"name":{"minLength":1,"type":["string","null"]},"state":{"enum":["draft","posted","cancel"]}},"required":["id","name","move_type","state","date"],"type":"object"}]} |
| response.data.tax_cash_basis_origin_move | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.tax_cash_basis_origin_move | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","date"]} |
| response.data.tax_cash_basis_origin_move.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.tax_cash_basis_origin_move.name | string/null | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.tax_cash_basis_origin_move.move_type | 未限定 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.tax_cash_basis_origin_move.state | 未限定 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.tax_cash_basis_origin_move.date | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.reversal_moves | array | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.reversal_moves[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","date"]} |
| response.data.reversal_moves[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.reversal_moves[].name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.reversal_moves[].move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.reversal_moves[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.reversal_moves[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.tax_cash_basis_created_moves | array | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.tax_cash_basis_created_moves[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","date"]} |
| response.data.tax_cash_basis_created_moves[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.tax_cash_basis_created_moves[].name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.tax_cash_basis_created_moves[].move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.tax_cash_basis_created_moves[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.tax_cash_basis_created_moves[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.adjusting_entry_origin_moves | array | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.adjusting_entry_origin_moves[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","date"]} |
| response.data.adjusting_entry_origin_moves[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.adjusting_entry_origin_moves[].name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.adjusting_entry_origin_moves[].move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.adjusting_entry_origin_moves[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.adjusting_entry_origin_moves[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.adjusting_entries_moves | array | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.adjusting_entries_moves[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","date"]} |
| response.data.adjusting_entries_moves[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.adjusting_entries_moves[].name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.adjusting_entries_moves[].move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.adjusting_entries_moves[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.adjusting_entries_moves[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","move_type","state","reversed_entry","tax_cash_basis_origin_move","reversal_moves","tax_cash_basis_created_moves","adjusting_entry_origin_moves","adjusting_entries_moves"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.reversed_entry | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"additionalProperties":false,"properties":{"date":{"format":"date","type":"string"},"id":{"minimum":1,"type":"integer"},"move_type":{"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]},"name":{"minLength":1,"type":["string","null"]},"state":{"enum":["draft","posted","cancel"]}},"required":["id","name","move_type","state","date"],"type":"object"}]} |
| response.data.reversed_entry | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.reversed_entry | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","date"]} |
| response.data.reversed_entry.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.reversed_entry.name | string/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.reversed_entry.move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.reversed_entry.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.reversed_entry.date | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"format":"date"} |
| response.data.tax_cash_basis_origin_move | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"additionalProperties":false,"properties":{"date":{"format":"date","type":"string"},"id":{"minimum":1,"type":"integer"},"move_type":{"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]},"name":{"minLength":1,"type":["string","null"]},"state":{"enum":["draft","posted","cancel"]}},"required":["id","name","move_type","state","date"],"type":"object"}]} |
| response.data.tax_cash_basis_origin_move | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.tax_cash_basis_origin_move | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","date"]} |
| response.data.tax_cash_basis_origin_move.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.tax_cash_basis_origin_move.name | string/null | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.tax_cash_basis_origin_move.move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.tax_cash_basis_origin_move.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.tax_cash_basis_origin_move.date | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"format":"date"} |
| response.data.reversal_moves | array | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.reversal_moves[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","date"]} |
| response.data.reversal_moves[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.reversal_moves[].name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.reversal_moves[].move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.reversal_moves[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.reversal_moves[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.tax_cash_basis_created_moves | array | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.tax_cash_basis_created_moves[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","date"]} |
| response.data.tax_cash_basis_created_moves[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.tax_cash_basis_created_moves[].name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.tax_cash_basis_created_moves[].move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.tax_cash_basis_created_moves[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.tax_cash_basis_created_moves[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.adjusting_entry_origin_moves | array | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.adjusting_entry_origin_moves[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","date"]} |
| response.data.adjusting_entry_origin_moves[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.adjusting_entry_origin_moves[].name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.adjusting_entry_origin_moves[].move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.adjusting_entry_origin_moves[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.adjusting_entry_origin_moves[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.adjusting_entries_moves | array | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.adjusting_entries_moves[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","date"]} |
| response.data.adjusting_entries_moves[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.adjusting_entries_moves[].name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.adjusting_entries_moves[].move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.adjusting_entries_moves[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.adjusting_entries_moves[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
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

<a id="cap-accounting_move-processing_settings-get"></a>

## accounting_move.processing_settings.get — 读取发票分录处理设置

- 类型：只读；静态状态：`unconfigured`；handler：`accounting_move_processing_settings_get`。
- 状态原因：`runtime_context_required` — Requires explicit runtime company/user scope and native ACLs. Currency/rounding/term/method/schedule changes require draft moves; review uses the native posted-only method. Auto-post configuration schedules native future work but never runs a cron or posts a move in this command. No arbitrary field/method calls or external delivery.
- 内部domain：`accounting_documents`；来源模型：res.company, account.move, res.currency, account.cash.rounding, account.incoterms, account.payment.method.line；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move:read, res.currency:read, account.cash.rounding:read, account.incoterms:read, account.payment.method.line:read。
- 请求/响应合同：`schemas/v1/accounting_move.processing_settings.get.request.schema.json` / `schemas/v1/accounting_move.processing_settings.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read accounting_move.processing_settings.get --request "@request.json"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"accounting_move.processing_settings.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["auto_post","auto_post_origin_id","auto_post_until","checked","company_currency_id","company_id","currency_id","date","expected_currency_rate","id","incoterm_location","invoice_cash_rounding_id","invoice_currency_rate","invoice_incoterm_id","move_type","name","payment_state","preferred_payment_method_line_id","state"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}$(?![\\s\\S])"} |
| response.data.currency_id | integer | 必填（所在对象出现时） | oneOf[2] | 币种ID | {"minimum":1} |
| response.data.company_currency_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.invoice_currency_rate | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.expected_currency_rate | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.invoice_cash_rounding_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.invoice_incoterm_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.incoterm_location | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.preferred_payment_method_line_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.auto_post | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["at_date","monthly","no","quarterly","yearly"]} |
| response.data.auto_post_until | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}$(?![\\s\\S])"} |
| response.data.auto_post_origin_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.checked | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.payment_state | string/null | 必填（所在对象出现时） | oneOf[2] | 原生付款结算状态 | {"minLength":1} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["auto_post","auto_post_origin_id","auto_post_until","checked","company_currency_id","company_id","currency_id","date","expected_currency_rate","id","incoterm_location","invoice_cash_rounding_id","invoice_currency_rate","invoice_incoterm_id","move_type","name","payment_state","preferred_payment_method_line_id","state"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["entry","in_invoice","in_receipt","in_refund","out_invoice","out_receipt","out_refund"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}$(?![\\s\\S])"} |
| response.data.currency_id | integer | 必填（所在对象出现时） | allOf[1]/then | 币种ID | {"minimum":1} |
| response.data.company_currency_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.invoice_currency_rate | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.expected_currency_rate | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.invoice_cash_rounding_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.invoice_incoterm_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.incoterm_location | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.preferred_payment_method_line_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.auto_post | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["at_date","monthly","no","quarterly","yearly"]} |
| response.data.auto_post_until | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}$(?![\\s\\S])"} |
| response.data.auto_post_origin_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.checked | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.payment_state | string/null | 必填（所在对象出现时） | allOf[1]/then | 原生付款结算状态 | {"minLength":1} |
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
- `execute`：fixed_native_move_processing_settings_read
- `verify`：closed_response_schema_validation
- `idempotency`：read_only
- `reverse`：not_applicable

### 已登记测试与证据范围

- `unit`：`implemented`；Shared closed contracts, native methods, fixed public/runtime/schema and company/user boundaries.；引用：tests/unit/test_move_processing_batch.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases through the public CLI as uid 5 with su=False: all nine new capabilities, eight immediate replays, actual foreign-currency balance recomputation and native rate refresh, native cash-rounding line, incoterm and invoice method, native payment block/unblock and posted review, a saved unposted recurring schedule, direction/state/company denial, and fresh-cursor business-data, currency/rate fixture and temporary-group rollback verification. No cron, external delivery or service changes.；引用：tests/integration/test_move_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-accounting_move-review-set"></a>

## accounting_move.review.set — 设置分录复核状态

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Requires explicit runtime company/user scope and native ACLs. Currency/rounding/term/method/schedule changes require draft moves; review uses the native posted-only method. Auto-post configuration schedules native future work but never runs a cron or posts a move in this command. No arbitrary field/method calls or external delivery.
- 内部domain：`accounting_documents`；来源模型：account.move, account.move.line, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.move.line:read, account.move:read, account.move:write。
- 请求/响应合同：`schemas/v1/accounting_move.review.set.request.schema.json` / `schemas/v1/accounting_move.review.set.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run accounting_move.review.set --request "@request.json" --idempotency-key "accounting_move.review.set:1:139e8a0dd2b14e410a85d8c81611264c" --confirm "accounting_move.review.set"
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
    "checked": false,
    "move_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["checked","move_id"]} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |
| parameters.checked | boolean | 必填（所在对象出现时） |  |  |  |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"accounting_move.review.set"} |
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

<a id="cap-diagnostic-journal_integrity-inspect"></a>

## diagnostic.journal_integrity.inspect — 检查日记账完整性

- 类型：只读；静态状态：`unconfigured`；handler：`diagnostic_journal_integrity_inspect`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`diagnostics`；来源模型：res.company, account.journal, account.move；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：res.company:read, account.journal:read, account.move:read。
- 请求/响应合同：`schemas/v1/diagnostic.journal_integrity.inspect.request.schema.json` / `schemas/v1/diagnostic.journal_integrity.inspect.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read diagnostic.journal_integrity.inspect --request "@request.json"
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
| parameters | object | 必填 |  |  | {"additionalProperties":false,"maxProperties":0} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"diagnostic.journal_integrity.inspect"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["company_id","printing_date","results"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.printing_date | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.results | array | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.results[] | 组合/开放结构 | 每个数组元素 | oneOf[2] |  | {"oneOf":[{"$ref":"#/$defs/basic_result"},{"$ref":"#/$defs/verified_result"}],"resolved_ref":"#/$defs/result"} |
| response.data.results[] | object | 分支约束 | oneOf[2]/oneOf[1] |  | {"additionalProperties":false,"required_in_object":["journal_name","restricted_by_hash_table","status","msg_cover"],"resolved_ref":"#/$defs/basic_result"} |
| response.data.results[].journal_name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[1] |  | {"minLength":1} |
| response.data.results[].restricted_by_hash_table | 未限定 | 必填（所在对象出现时） | oneOf[2]/oneOf[1] |  | {"enum":["V","X"],"resolved_ref":"#/$defs/restricted_flag"} |
| response.data.results[].status | 未限定 | 必填（所在对象出现时） | oneOf[2]/oneOf[1] |  | {"enum":["no_data","corrupted"]} |
| response.data.results[].msg_cover | string | 必填（所在对象出现时） | oneOf[2]/oneOf[1] |  | {"minLength":1} |
| response.data.results[] | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["journal_name","restricted_by_hash_table","status","msg_cover","first_move_name","first_hash","first_move_date","last_move_name","last_hash","last_move_date"],"resolved_ref":"#/$defs/verified_result"} |
| response.data.results[].journal_name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.results[].restricted_by_hash_table | 未限定 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"enum":["V","X"],"resolved_ref":"#/$defs/restricted_flag"} |
| response.data.results[].status | 未限定 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"const":"verified"} |
| response.data.results[].msg_cover | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.results[].first_move_name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.results[].first_hash | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.results[].first_move_date | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.results[].last_move_name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.results[].last_hash | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.results[].last_move_date | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["company_id","printing_date","results"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.printing_date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.results | array | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.results[] | 组合/开放结构 | 每个数组元素 | allOf[1]/then |  | {"oneOf":[{"$ref":"#/$defs/basic_result"},{"$ref":"#/$defs/verified_result"}],"resolved_ref":"#/$defs/result"} |
| response.data.results[] | object | 分支约束 | allOf[1]/then/oneOf[1] |  | {"additionalProperties":false,"required_in_object":["journal_name","restricted_by_hash_table","status","msg_cover"],"resolved_ref":"#/$defs/basic_result"} |
| response.data.results[].journal_name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"minLength":1} |
| response.data.results[].restricted_by_hash_table | 未限定 | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"enum":["V","X"],"resolved_ref":"#/$defs/restricted_flag"} |
| response.data.results[].status | 未限定 | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"enum":["no_data","corrupted"]} |
| response.data.results[].msg_cover | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[1] |  | {"minLength":1} |
| response.data.results[] | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["journal_name","restricted_by_hash_table","status","msg_cover","first_move_name","first_hash","first_move_date","last_move_name","last_hash","last_move_date"],"resolved_ref":"#/$defs/verified_result"} |
| response.data.results[].journal_name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.results[].restricted_by_hash_table | 未限定 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"enum":["V","X"],"resolved_ref":"#/$defs/restricted_flag"} |
| response.data.results[].status | 未限定 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"const":"verified"} |
| response.data.results[].msg_cover | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.results[].first_move_name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.results[].first_hash | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.results[].first_move_date | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.results[].last_move_name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.results[].last_hash | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.results[].last_move_date | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
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
- `execute`：fixed_native_journal_hash_integrity_inspection
- `verify`：native_hash_integrity_result_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The closed request and native result validation, fixed bridge action, read-only runtime dispatch, and CLI routing are covered by unit tests.；引用：tests/unit/test_journal_integrity.py, tests/unit/test_journal_integrity_bridge.py, tests/unit/test_remaining_read_batch_runtime.py, tests/unit/test_remaining_read_batch_cli.py
- `integration`：`implemented`；The shared live integration test verifies the native journal integrity inspection against both dedicated synthetic database aliases without committing database changes.；引用：tests/integration/test_remaining_read_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal-sequence_irregularity-list"></a>

## journal.sequence_irregularity.list — 列出日记账序列异常

- 类型：只读；静态状态：`unconfigured`；handler：`journal_sequence_irregularity_list`。
- 状态原因：`runtime_context_required` — The fixed read handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`journals`；来源模型：res.company, account.journal, account.move；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.journal:read, account.move:read。
- 请求/响应合同：`schemas/v1/journal.sequence_irregularity.list.request.schema.json` / `schemas/v1/journal.sequence_irregularity.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read journal.sequence_irregularity.list --request "@request.json"
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
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal.sequence_irregularity.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","name","date","state","move_type","journal","sequence_prefix","sequence_number","made_sequence_gap"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.items[].move_type | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].sequence_prefix | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].sequence_number | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.items[].made_sequence_gap | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":true} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","name","date","state","move_type","journal","sequence_prefix","sequence_number","made_sequence_gap"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.items[].move_type | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].sequence_prefix | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].sequence_number | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.items[].made_sequence_gap | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"const":true} |
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
- `execute`：fixed_company_scoped_journal_sequence_irregularity_list
- `verify`：same_transaction_acl_cursor_lock_boundary_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared focused test covers registry metadata, fixed CLI routing, model mapping, and exclusion of inventory capabilities.；引用：tests/unit/test_accounting_operational_reads_registry_cli.py
- `integration`：`implemented`；The shared ordinary-accounting-user read-only smoke passed for all twelve capabilities on both dedicated isolated database aliases.；引用：tests/integration/test_accounting_operational_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_entry-cancel"></a>

## journal_entry.cancel — 原子取消单笔或 2–100 笔普通日记账分录

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`general_ledger`；来源模型：res.company, account.move, account.move.line, account.analytic.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.move:read, account.move:write, account.move.line:read。
- 请求/响应合同：`schemas/v1/journal_entry.cancel.request.schema.json` / `schemas/v1/journal_entry.cancel.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run journal_entry.cancel --request "@request.json" --idempotency-key "journal_entry.cancel:1" --confirm "journal_entry.cancel"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal_entry.cancel"} |
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
- `execute`：full_batch_record_scope_company_general_entry_type_and_state_preflight_then_single_transaction_all_or_nothing_native_cancel
- `verify`：explicit_batch_result_with_exact_normalized_record_ids_target_states_same_transaction_reread_and_response_schema_validation
- `idempotency`：capability_company_and_full_normalized_sorted_record_id_set_key_with_serial_target_state_replay
- `reverse`：journal_entry.reset_to_draft_when_native_state_allows

### 已登记测试与证据范围

- `unit`：`implemented`；The existing unit tests continue to cover the singular request and native runtime behavior; the batch contract unit test covers batch-request normalization, full normalized-ID-set idempotency keys, bridge and capability contracts, explicit batch results, and CLI verification.；引用：tests/unit/test_document_lifecycle_writes.py, tests/unit/test_document_lifecycle_writes_runtime.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_write_cli.py, tests/unit/test_document_lifecycle_write_cli.py, tests/unit/test_lifecycle_batch_contract.py
- `integration`：`implemented`；The existing integration smoke continues to cover singular native execution; the new live smoke covers dual-database batch execution, immediate replay, and rollback, plus a representative whole-batch invalid-ID no-op for invoice.post.；引用：tests/integration/test_document_lifecycle_write_batch_live.py, tests/integration/test_batch_lifecycle_write_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_entry-create"></a>

## journal_entry.create — 创建草稿总账分录

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`general_ledger`；来源模型：res.company, res.partner, account.journal, account.account, account.move, account.move.line, res.currency, account.analytic.account, account.tax, account.tax.repartition.line, account.account.tag；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：res.partner:read, account.journal:read, account.account:read, account.move:read, account.move:create, account.move.line:read, account.move.line:create, account.tax:read, account.tax.repartition.line:read, account.account.tag:read。
- 请求/响应合同：`schemas/v1/journal_entry.create.request.schema.json` / `schemas/v1/journal_entry.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run journal_entry.create --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "journal_entry.create"
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
    "lines": [
      {
        "name": "Example",
        "account_id": 1,
        "partner_id": 1,
        "debit": "100",
        "credit": "0"
      },
      {
        "name": "Example",
        "account_id": 2,
        "partner_id": 2,
        "debit": "0",
        "credit": "100"
      }
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["journal_id","date","lines"]} |
| parameters.journal_id | integer | 必填（所在对象出现时） |  | 日记账ID | {"minimum":1} |
| parameters.date | string | 必填（所在对象出现时） |  |  | {"format":"date"} |
| parameters.reference | string/null | 可选（可能有条件限制） |  |  | {"maxLength":200,"minLength":1} |
| parameters.lines | array | 必填（所在对象出现时） |  | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":500,"minItems":2} |
| parameters.lines[] | object | 每个数组元素 |  | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"allOf":[{"if":{"properties":{"currency_id":{"type":"null"}},"required":["currency_id"]},"then":{"properties":{"amount_currency":{"type":"null"}}}},{"if":{"properties":{"amount_currency":{"type":"null"}},"required":["amount_currency"]},"then":{"properties":{"currency_id":{"type":"null"}}}}],"dependentRequired":{"amount_currency":["currency_id"],"currency_id":["amount_currency"]},"required_in_object":["name","account_id","partner_id","debit","credit"]} |
| parameters.lines[].name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":500,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$"} |
| parameters.lines[].account_id | integer | 必填（所在对象出现时） |  | 会计科目ID | {"minimum":1} |
| parameters.lines[].partner_id | integer/null | 必填（所在对象出现时） |  | 合作伙伴ID | {"minimum":1} |
| parameters.lines[].date_maturity | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.lines[].debit | string | 必填（所在对象出现时） |  | 借方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| parameters.lines[].credit | string | 必填（所在对象出现时） |  | 贷方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| parameters.lines[].currency_id | integer/null | 可选（可能有条件限制） |  | 币种ID | {"minimum":1} |
| parameters.lines[].amount_currency | 组合/开放结构 | 可选（可能有条件限制） |  | 外币/交易币数值，非默认公司币金额 | {"oneOf":[{"$ref":"#/$defs/nonzero_signed_decimal"},{"type":"null"}]} |
| parameters.lines[].amount_currency | string | 分支约束 | oneOf[1] | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:(?:[1-9][0-9]*)(?:\\.[0-9]+)?&#124;0\\.(?=[0-9]*[1-9])[0-9]+)$(?![\\s\\S])","resolved_ref":"#/$defs/nonzero_signed_decimal"} |
| parameters.lines[].amount_currency | null | 分支约束 | oneOf[2] | 外币/交易币数值，非默认公司币金额 |  |
| parameters.lines[].tax_ids | array | 可选（可能有条件限制） |  | 应用税ID数组 | {"maxItems":100,"uniqueItems":true} |
| parameters.lines[].tax_ids[] | integer | 每个数组元素 |  | 应用税ID数组 | {"minimum":1} |
| parameters.lines[].tax_tag_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":100,"uniqueItems":true} |
| parameters.lines[].tax_tag_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.lines[].tax_repartition_line_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.lines[].tax_base_amount | string | 可选（可能有条件限制） |  |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| parameters.lines[].analytic_distribution | 组合/开放结构 | 可选（可能有条件限制） |  | 分析分摊映射；写入与读回约束可能不同 | {"oneOf":[{"type":"null"},{"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"},"type":"object"}],"resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/analytic_distribution"} |
| parameters.lines[].analytic_distribution | null | 分支约束 | oneOf[1] | 分析分摊映射；写入与读回约束可能不同 |  |
| parameters.lines[].analytic_distribution | object | 分支约束 | oneOf[2] | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"}} |
| parameters.lines[].analytic_distribution{其他键} | string | 动态键值 | oneOf[2] |  | {"maxLength":8,"pattern":"^(?:100&#124;(?:[1-9][0-9]?)(?:\\.[0-9]{0,3}[1-9])?&#124;0\\.[0-9]{0,3}[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/analytic_percentage"} |
| parameters.lines[] | 组合/开放结构 | 分支约束 | allOf[1] | 行数组；增补/更新/替换语义由能力ID决定 | {"if":{"properties":{"currency_id":{"type":"null"}},"required":["currency_id"]},"then":{"properties":{"amount_currency":{"type":"null"}}}} |
| parameters.lines[] | 未限定 | 条件分支 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| parameters.lines[].amount_currency | null | 可选（可能有条件限制） | allOf[1]/then | 外币/交易币数值，非默认公司币金额 |  |
| parameters.lines[] | 组合/开放结构 | 分支约束 | allOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"if":{"properties":{"amount_currency":{"type":"null"}},"required":["amount_currency"]},"then":{"properties":{"currency_id":{"type":"null"}}}} |
| parameters.lines[] | 未限定 | 条件分支 | allOf[2]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| parameters.lines[].currency_id | null | 可选（可能有条件限制） | allOf[2]/then | 币种ID |  |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal_entry.create"} |
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
- `verify`：same_transaction_rich_journal_field_reread_and_schema_validation
- `idempotency`：odoo_persisted_business_marker_and_result_replay
- `reverse`：delete_draft_or_reverse_after_posting

### 已登记测试与证据范围

- `unit`：`implemented`；Existing contracts and explicit payment/tax input extensions are covered.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_core_write_cli.py, tests/unit/test_accounting_payment_tax_inputs_batch.py, tests/unit/test_entry_payment_explicit_inputs_contract.py, tests/unit/test_journal_item_tax_projection_contract.py, tests/unit/test_payment_tax_input_runtime.py
- `integration`：`implemented`；Shared native payment/tax smoke passed; full rollback.；引用：tests/integration/test_core_write_batch_live.py, tests/integration/test_accounting_depth_batch_live.py, tests/integration/test_accounting_payment_tax_inputs_batch_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_entry-delete"></a>

## journal_entry.delete — 删除从未过账的普通草稿总账分录

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`deleted_record_tombstone_unavailable` — The handler verifies journal-entry and line absence after deletion, but keeps no persistent tombstone, so a later retry cannot distinguish its prior deletion from an unrelated disappearance.
- 内部domain：`general_ledger`；来源模型：res.company, account.journal, account.move, account.move.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.journal:read, account.move:read, account.move:unlink, account.move.line:read, account.move.line:unlink。
- 请求/响应合同：`schemas/v1/journal_entry.delete.request.schema.json` / `schemas/v1/journal_entry.delete.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run journal_entry.delete --request "@request.json" --idempotency-key "journal_entry.delete:1" --confirm "journal_entry.delete"
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
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"journal_entry.delete"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"journal_entry.delete"} |
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
- `execute`：fixed_native_never_posted_ordinary_draft_journal_entry_unlink
- `verify`：same_transaction_account_move_and_lines_absence_and_response_schema_validation
- `idempotency`：record_absence_recheck_without_operation_store_or_persistent_tombstone
- `reverse`：not_reversible_deleted_journal_entry_must_be_recreated

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover confirmation, ordinary-entry and never-posted-draft boundaries, generated-entry exclusion, native unlink, move-and-line absence verification, result binding, registry descriptor, and schemas.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_draft_document_maintenance_runtime.py, tests/unit/test_draft_document_maintenance_schemas.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases through the public CLI as uid 5 with su=False, exercising all six draft-maintenance commands, five immediate replays, and fresh-cursor business-data and temporary-group rollback verification.；引用：tests/integration/test_draft_document_maintenance_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_entry-duplicate"></a>

## journal_entry.duplicate — 复制普通总账分录为新草稿

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`concurrent_idempotency_limit` — The handler persists source-bound idempotency markers and rechecks a matching draft duplicate, but Odoo provides no database uniqueness constraint for concurrent exactly-once duplication.
- 内部domain：`general_ledger`；来源模型：res.company, account.journal, account.move, account.move.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.journal:read, account.move:read, account.move:create, account.move:write, account.move.line:read, account.move.line:create。
- 请求/响应合同：`schemas/v1/journal_entry.duplicate.request.schema.json` / `schemas/v1/journal_entry.duplicate.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run journal_entry.duplicate --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "journal_entry.duplicate"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal_entry.duplicate"} |
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
- `execute`：fixed_native_ordinary_journal_entry_copy_as_draft_with_persistent_source_marker
- `verify`：same_transaction_new_draft_general_entry_source_binding_marker_lines_and_response_schema_validation
- `idempotency`：stable_source_and_operation_marker_lookup_without_database_uniqueness_or_concurrent_exactly_once_guarantee
- `reverse`：journal_entry.delete

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the closed source request, generated-entry exclusion, native copy, persistent source-bound marker replay, line preservation, result binding, registry descriptor, and schemas.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_draft_document_maintenance_runtime.py, tests/unit/test_draft_document_maintenance_schemas.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases through the public CLI as uid 5 with su=False, exercising all six draft-maintenance commands, five immediate replays, and fresh-cursor business-data and temporary-group rollback verification.；引用：tests/integration/test_draft_document_maintenance_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_entry-get"></a>

## journal_entry.get — 读取总账分录明细

- 类型：只读；静态状态：`unconfigured`；handler：`journal_entry_get`。
- 状态原因：`runtime_context_required` — Static registry metadata does not declare target-specific runtime availability; availability is evaluated for each configured database, company, and user.
- 内部domain：`general_ledger`；来源模型：account.move, account.move.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move:read, account.move.line:read, account.journal:read, account.account:read, res.currency:read, res.partner:read。
- 请求/响应合同：`schemas/v1/journal_entry.get.request.schema.json` / `schemas/v1/journal_entry.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read journal_entry.get --request "@request.json"
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
    "entry_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["entry_id"]} |
| parameters.entry_id | integer | 必填（所在对象出现时） |  | 分录记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal_entry.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","date","state","ref","journal","company_id","currency","partner","lines","totals"],"resolved_ref":"#/$defs/data"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.ref | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}]} |
| response.data.ref | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.ref | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/journal"} |
| response.data.journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":5,"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.partner | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.partner | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.partner | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/partner"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines | array | 必填（所在对象出现时） | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 |  |
| response.data.lines[] | object | 每个数组元素 | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"allOf":[{"else":{"properties":{"account":{"$ref":"#/$defs/account"}}},"if":{"properties":{"display_type":{"enum":["line_section","line_subsection","line_note"]}},"required":["display_type"]},"then":{"properties":{"account":{"type":"null"}}}}],"required_in_object":["id","sequence","display_type","name","account","partner","debit","credit","balance","company_currency","amount_currency","currency","date_maturity","reconciled","matching_number","analytic_distribution"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].sequence | integer | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.lines[].display_type | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | 业务行/章节/备注类型 | {"oneOf":[{"type":"null"},{"enum":["product","cogs","tax","discount","rounding","payment_term","line_section","line_subsection","line_note","epd","non_deductible_product_total","non_deductible_product","non_deductible_tax"]}]} |
| response.data.lines[].display_type | null | 分支约束 | oneOf[2]/oneOf[1] | 业务行/章节/备注类型 |  |
| response.data.lines[].display_type | 未限定 | 分支约束 | oneOf[2]/oneOf[2] | 业务行/章节/备注类型 | {"enum":["product","cogs","tax","discount","rounding","payment_term","line_section","line_subsection","line_note","epd","non_deductible_product_total","non_deductible_product","non_deductible_tax"]} |
| response.data.lines[].name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].account | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.lines[].account | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].account | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.lines[].account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.lines[].account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].partner | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.lines[].partner | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].partner | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/partner"} |
| response.data.lines[].partner.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].partner.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].debit | string | 必填（所在对象出现时） | oneOf[2] | 借方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.lines[].credit | string | 必填（所在对象出现时） | oneOf[2] | 贷方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.lines[].balance | string | 必填（所在对象出现时） | oneOf[2] | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.lines[].company_currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.lines[].company_currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.lines[].company_currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.lines[].amount_currency | string | 必填（所在对象出现时） | oneOf[2] | 外币/交易币数值，非默认公司币金额 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.lines[].currency | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/currency"}]} |
| response.data.lines[].currency | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].currency | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.lines[].currency.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].currency.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.lines[].date_maturity | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.lines[].reconciled | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.lines[].matching_number | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}]} |
| response.data.lines[].matching_number | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].matching_number | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1} |
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
| response.data.totals | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["debit","credit","balance"],"resolved_ref":"#/$defs/totals"} |
| response.data.totals.debit | string | 必填（所在对象出现时） | oneOf[2] | 借方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.totals.credit | string | 必填（所在对象出现时） | oneOf[2] | 贷方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.totals.balance | string | 必填（所在对象出现时） | oneOf[2] | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","date","state","ref","journal","company_id","currency","partner","lines","totals"],"resolved_ref":"#/$defs/data"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.ref | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}]} |
| response.data.ref | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.ref | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/journal"} |
| response.data.journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":5,"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.partner | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.partner | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/partner"} |
| response.data.partner.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines | array | 必填（所在对象出现时） | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| response.data.lines[] | object | 每个数组元素 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"allOf":[{"else":{"properties":{"account":{"$ref":"#/$defs/account"}}},"if":{"properties":{"display_type":{"enum":["line_section","line_subsection","line_note"]}},"required":["display_type"]},"then":{"properties":{"account":{"type":"null"}}}}],"required_in_object":["id","sequence","display_type","name","account","partner","debit","credit","balance","company_currency","amount_currency","currency","date_maturity","reconciled","matching_number","analytic_distribution"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].sequence | integer | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.lines[].display_type | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | 业务行/章节/备注类型 | {"oneOf":[{"type":"null"},{"enum":["product","cogs","tax","discount","rounding","payment_term","line_section","line_subsection","line_note","epd","non_deductible_product_total","non_deductible_product","non_deductible_tax"]}]} |
| response.data.lines[].display_type | null | 分支约束 | allOf[1]/then/oneOf[1] | 业务行/章节/备注类型 |  |
| response.data.lines[].display_type | 未限定 | 分支约束 | allOf[1]/then/oneOf[2] | 业务行/章节/备注类型 | {"enum":["product","cogs","tax","discount","rounding","payment_term","line_section","line_subsection","line_note","epd","non_deductible_product_total","non_deductible_product","non_deductible_tax"]} |
| response.data.lines[].name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.lines[].account | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.lines[].account | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].account | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.lines[].account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.lines[].account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/partner"}]} |
| response.data.lines[].partner | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].partner | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/partner"} |
| response.data.lines[].partner.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].partner.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].debit | string | 必填（所在对象出现时） | allOf[1]/then | 借方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.lines[].credit | string | 必填（所在对象出现时） | allOf[1]/then | 贷方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.lines[].balance | string | 必填（所在对象出现时） | allOf[1]/then | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.lines[].company_currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.lines[].company_currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].company_currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.lines[].amount_currency | string | 必填（所在对象出现时） | allOf[1]/then | 外币/交易币数值，非默认公司币金额 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.lines[].currency | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/currency"}]} |
| response.data.lines[].currency | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].currency | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.lines[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.lines[].date_maturity | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.lines[].reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.lines[].matching_number | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}]} |
| response.data.lines[].matching_number | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].matching_number | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
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
| response.data.totals | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["debit","credit","balance"],"resolved_ref":"#/$defs/totals"} |
| response.data.totals.debit | string | 必填（所在对象出现时） | allOf[1]/then | 借方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.totals.credit | string | 必填（所在对象出现时） | allOf[1]/then | 贷方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.totals.balance | string | 必填（所在对象出现时） | allOf[1]/then | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
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

- `unit`：`implemented`；Unit tests cover the closed request, response, cursor, bridge, and fixed Odoo runtime contracts.；引用：tests/unit/test_journal_entries.py, tests/unit/test_journal_entry_bridge.py, tests/unit/test_journal_entry_runtime.py, tests/unit/test_journal_entry_cli.py
- `integration`：`implemented`；Live tests verify both fixed journal-entry reads against both dedicated synthetic databases and both configured companies.；引用：tests/integration/test_journal_entries_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_entry-lines-add"></a>

## journal_entry.lines.add — 保留其他行 ID，追加草稿手工分录行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Runtime required; serial target replay is not concurrent exactly-once.
- 内部domain：`general_ledger`；来源模型：account.account, account.analytic.account, account.analytic.line, account.analytic.plan, account.journal, account.move, account.move.line, res.company, res.currency, res.currency.rate, res.partner, account.tax, account.tax.repartition.line, account.account.tag；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.account:read, account.analytic.account:read, account.analytic.line:create, account.analytic.line:read, account.analytic.line:unlink, account.analytic.plan:read, account.journal:read, account.move.line:create, account.move.line:read, account.move:read, account.move:write, res.company:read, res.currency.rate:read, res.currency:read, res.partner:read, account.tax:read, account.tax.repartition.line:read, account.account.tag:read。
- 请求/响应合同：`schemas/v1/journal_entry.lines.add.request.schema.json` / `schemas/v1/journal_entry.lines.add.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run journal_entry.lines.add --request "@request.json" --idempotency-key "journal_entry.lines.add:1:9e40d12606e58f17803f87f6f38a1c55" --confirm "journal_entry.lines.add"
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
        "account_id": 1,
        "partner_id": 1,
        "debit": "100",
        "credit": "0"
      },
      {
        "name": "Example",
        "account_id": 2,
        "partner_id": 2,
        "debit": "0",
        "credit": "100"
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
| parameters.expected_line_ids | array | 必填（所在对象出现时） |  |  | {"maxItems":500,"minItems":0,"uniqueItems":true} |
| parameters.expected_line_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.lines | array | 必填（所在对象出现时） |  | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":500,"minItems":2,"resolved_ref":"journal_entry.lines.replace.request.schema.json#/properties/parameters/properties/lines"} |
| parameters.lines[] | object | 每个数组元素 |  | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"allOf":[{"if":{"properties":{"currency_id":{"type":"null"}},"required":["currency_id"]},"then":{"properties":{"amount_currency":{"type":"null"}}}},{"if":{"properties":{"amount_currency":{"type":"null"}},"required":["amount_currency"]},"then":{"properties":{"currency_id":{"type":"null"}}}}],"dependentRequired":{"amount_currency":["currency_id"],"currency_id":["amount_currency"]},"required_in_object":["name","account_id","partner_id","debit","credit"]} |
| parameters.lines[].name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":500,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$"} |
| parameters.lines[].account_id | integer | 必填（所在对象出现时） |  | 会计科目ID | {"minimum":1} |
| parameters.lines[].partner_id | integer/null | 必填（所在对象出现时） |  | 合作伙伴ID | {"minimum":1} |
| parameters.lines[].date_maturity | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.lines[].debit | string | 必填（所在对象出现时） |  | 借方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| parameters.lines[].credit | string | 必填（所在对象出现时） |  | 贷方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| parameters.lines[].currency_id | integer/null | 可选（可能有条件限制） |  | 币种ID | {"minimum":1} |
| parameters.lines[].amount_currency | 组合/开放结构 | 可选（可能有条件限制） |  | 外币/交易币数值，非默认公司币金额 | {"oneOf":[{"$ref":"#/$defs/nonzero_signed_decimal"},{"type":"null"}]} |
| parameters.lines[].amount_currency | string | 分支约束 | oneOf[1] | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:(?:[1-9][0-9]*)(?:\\.[0-9]+)?&#124;0\\.(?=[0-9]*[1-9])[0-9]+)$(?![\\s\\S])","resolved_ref":"#/$defs/nonzero_signed_decimal"} |
| parameters.lines[].amount_currency | null | 分支约束 | oneOf[2] | 外币/交易币数值，非默认公司币金额 |  |
| parameters.lines[].tax_ids | array | 可选（可能有条件限制） |  | 应用税ID数组 | {"maxItems":100,"uniqueItems":true} |
| parameters.lines[].tax_ids[] | integer | 每个数组元素 |  | 应用税ID数组 | {"minimum":1} |
| parameters.lines[].tax_tag_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":100,"uniqueItems":true} |
| parameters.lines[].tax_tag_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.lines[].tax_repartition_line_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.lines[].tax_base_amount | string | 可选（可能有条件限制） |  |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| parameters.lines[].analytic_distribution | 组合/开放结构 | 可选（可能有条件限制） |  | 分析分摊映射；写入与读回约束可能不同 | {"oneOf":[{"type":"null"},{"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"},"type":"object"}],"resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/analytic_distribution"} |
| parameters.lines[].analytic_distribution | null | 分支约束 | oneOf[1] | 分析分摊映射；写入与读回约束可能不同 |  |
| parameters.lines[].analytic_distribution | object | 分支约束 | oneOf[2] | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"}} |
| parameters.lines[].analytic_distribution{其他键} | string | 动态键值 | oneOf[2] |  | {"maxLength":8,"pattern":"^(?:100&#124;(?:[1-9][0-9]?)(?:\\.[0-9]{0,3}[1-9])?&#124;0\\.[0-9]{0,3}[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/analytic_percentage"} |
| parameters.lines[] | 组合/开放结构 | 分支约束 | allOf[1] | 行数组；增补/更新/替换语义由能力ID决定 | {"if":{"properties":{"currency_id":{"type":"null"}},"required":["currency_id"]},"then":{"properties":{"amount_currency":{"type":"null"}}}} |
| parameters.lines[] | 未限定 | 条件分支 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| parameters.lines[].amount_currency | null | 可选（可能有条件限制） | allOf[1]/then | 外币/交易币数值，非默认公司币金额 |  |
| parameters.lines[] | 组合/开放结构 | 分支约束 | allOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"if":{"properties":{"amount_currency":{"type":"null"}},"required":["amount_currency"]},"then":{"properties":{"currency_id":{"type":"null"}}}} |
| parameters.lines[] | 未限定 | 条件分支 | allOf[2]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| parameters.lines[].currency_id | null | 可选（可能有条件限制） | allOf[2]/then | 币种ID |  |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal_entry.lines.add"} |
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
- `execute`：native_parent_create_commands_with_balance_check
- `verify`：same_transaction_membership_and_preserved_rows
- `idempotency`：serial_expected_ids_and_added_row_match
- `reverse`：remove_added_rows

### 已登记测试与证据范围

- `unit`：`implemented`；Existing contracts and explicit payment/tax input extensions are covered.；引用：tests/unit/test_accounting_entry_membership_batch.py, tests/unit/test_capability_registry.py, tests/unit/test_accounting_payment_tax_inputs_batch.py, tests/unit/test_entry_payment_explicit_inputs_contract.py, tests/unit/test_journal_item_tax_projection_contract.py, tests/unit/test_payment_tax_input_runtime.py
- `integration`：`implemented`；Shared native payment/tax smoke passed; full rollback.；引用：tests/integration/test_accounting_entry_membership_batch_live.py, tests/integration/test_accounting_payment_tax_inputs_batch_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_entry-lines-remove"></a>

## journal_entry.lines.remove — 保留其他行 ID，删除指定草稿手工分录行

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`deleted_record_tombstone_unavailable` — Absent rows reject: no persistent deletion-attribution tombstone.
- 内部domain：`general_ledger`；来源模型：account.account, account.analytic.line, account.journal, account.move, account.move.line, res.company；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.account:read, account.analytic.line:read, account.analytic.line:unlink, account.journal:read, account.move.line:read, account.move.line:unlink, account.move:read, account.move:write, res.company:read。
- 请求/响应合同：`schemas/v1/journal_entry.lines.remove.request.schema.json` / `schemas/v1/journal_entry.lines.remove.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run journal_entry.lines.remove --request "@request.json" --idempotency-key "journal_entry.lines.remove:1:5de2ffcced6cd634927b39bfad7d193f" --confirm "journal_entry.lines.remove"
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
| parameters.line_ids | array | 必填（所在对象出现时） |  | 行记录ID数组 | {"maxItems":500,"minItems":1,"uniqueItems":true} |
| parameters.line_ids[] | integer | 每个数组元素 |  | 行记录ID数组 | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal_entry.lines.remove"} |
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
- `execute`：native_parent_delete_commands_with_balance_check
- `verify`：same_transaction_membership_and_preserved_rows
- `idempotency`：missing_rows_reject_without_tombstone
- `reverse`：recreate_rows_with_new_ids

### 已登记测试与证据范围

- `unit`：`implemented`；Contract, native writes, preservation and replay.；引用：tests/unit/test_accounting_entry_membership_batch.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；Shared native smoke passed; full rollback.；引用：tests/integration/test_accounting_entry_membership_batch_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_entry-lines-replace"></a>

## journal_entry.lines.replace — 替换草稿总账分录的全部行

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`general_ledger`；来源模型：res.company, res.partner, account.account, account.move, account.move.line, res.currency, account.analytic.account, account.tax, account.tax.repartition.line, account.account.tag；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：res.partner:read, account.account:read, account.move:read, account.move:write, account.move.line:read, account.move.line:create, account.move.line:write, account.move.line:unlink, account.tax:read, account.tax.repartition.line:read, account.account.tag:read。
- 请求/响应合同：`schemas/v1/journal_entry.lines.replace.request.schema.json` / `schemas/v1/journal_entry.lines.replace.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run journal_entry.lines.replace --request "@request.json" --idempotency-key "journal_entry.lines.replace:1:309c743320954645829be5bc3c40304c" --confirm "journal_entry.lines.replace"
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
        "account_id": 1,
        "partner_id": 1,
        "debit": "100",
        "credit": "0"
      },
      {
        "name": "Example",
        "account_id": 2,
        "partner_id": 1,
        "debit": "0",
        "credit": "100"
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
| parameters.lines[] | object | 每个数组元素 |  | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"allOf":[{"if":{"properties":{"currency_id":{"type":"null"}},"required":["currency_id"]},"then":{"properties":{"amount_currency":{"type":"null"}}}},{"if":{"properties":{"amount_currency":{"type":"null"}},"required":["amount_currency"]},"then":{"properties":{"currency_id":{"type":"null"}}}}],"dependentRequired":{"amount_currency":["currency_id"],"currency_id":["amount_currency"]},"required_in_object":["name","account_id","partner_id","debit","credit"]} |
| parameters.lines[].name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":500,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$"} |
| parameters.lines[].account_id | integer | 必填（所在对象出现时） |  | 会计科目ID | {"minimum":1} |
| parameters.lines[].partner_id | integer/null | 必填（所在对象出现时） |  | 合作伙伴ID | {"minimum":1} |
| parameters.lines[].date_maturity | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.lines[].debit | string | 必填（所在对象出现时） |  | 借方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| parameters.lines[].credit | string | 必填（所在对象出现时） |  | 贷方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| parameters.lines[].currency_id | integer/null | 可选（可能有条件限制） |  | 币种ID | {"minimum":1} |
| parameters.lines[].amount_currency | 组合/开放结构 | 可选（可能有条件限制） |  | 外币/交易币数值，非默认公司币金额 | {"oneOf":[{"$ref":"#/$defs/nonzero_signed_decimal"},{"type":"null"}]} |
| parameters.lines[].amount_currency | string | 分支约束 | oneOf[1] | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:(?:[1-9][0-9]*)(?:\\.[0-9]+)?&#124;0\\.(?=[0-9]*[1-9])[0-9]+)$(?![\\s\\S])","resolved_ref":"#/$defs/nonzero_signed_decimal"} |
| parameters.lines[].amount_currency | null | 分支约束 | oneOf[2] | 外币/交易币数值，非默认公司币金额 |  |
| parameters.lines[].tax_ids | array | 可选（可能有条件限制） |  | 应用税ID数组 | {"maxItems":100,"uniqueItems":true} |
| parameters.lines[].tax_ids[] | integer | 每个数组元素 |  | 应用税ID数组 | {"minimum":1} |
| parameters.lines[].tax_tag_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":100,"uniqueItems":true} |
| parameters.lines[].tax_tag_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.lines[].tax_repartition_line_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.lines[].tax_base_amount | string | 可选（可能有条件限制） |  |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| parameters.lines[].analytic_distribution | 组合/开放结构 | 可选（可能有条件限制） |  | 分析分摊映射；写入与读回约束可能不同 | {"oneOf":[{"type":"null"},{"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"},"type":"object"}],"resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/analytic_distribution"} |
| parameters.lines[].analytic_distribution | null | 分支约束 | oneOf[1] | 分析分摊映射；写入与读回约束可能不同 |  |
| parameters.lines[].analytic_distribution | object | 分支约束 | oneOf[2] | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"}} |
| parameters.lines[].analytic_distribution{其他键} | string | 动态键值 | oneOf[2] |  | {"maxLength":8,"pattern":"^(?:100&#124;(?:[1-9][0-9]?)(?:\\.[0-9]{0,3}[1-9])?&#124;0\\.[0-9]{0,3}[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/analytic_percentage"} |
| parameters.lines[] | 组合/开放结构 | 分支约束 | allOf[1] | 行数组；增补/更新/替换语义由能力ID决定 | {"if":{"properties":{"currency_id":{"type":"null"}},"required":["currency_id"]},"then":{"properties":{"amount_currency":{"type":"null"}}}} |
| parameters.lines[] | 未限定 | 条件分支 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| parameters.lines[].amount_currency | null | 可选（可能有条件限制） | allOf[1]/then | 外币/交易币数值，非默认公司币金额 |  |
| parameters.lines[] | 组合/开放结构 | 分支约束 | allOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"if":{"properties":{"amount_currency":{"type":"null"}},"required":["amount_currency"]},"then":{"properties":{"currency_id":{"type":"null"}}}} |
| parameters.lines[] | 未限定 | 条件分支 | allOf[2]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| parameters.lines[].currency_id | null | 可选（可能有条件限制） | allOf[2]/then | 币种ID |  |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal_entry.lines.replace"} |
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
- `verify`：same_transaction_exact_rich_journal_line_reread_and_schema_validation
- `idempotency`：target_line_payload_state_check_before_native_write
- `reverse`：repeat_replace_with_previous_journal_lines

### 已登记测试与证据范围

- `unit`：`implemented`；Existing contracts and explicit payment/tax input extensions are covered.；引用：tests/unit/test_document_lifecycle_writes.py, tests/unit/test_document_lifecycle_writes_runtime.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_write_cli.py, tests/unit/test_document_lifecycle_write_cli.py, tests/unit/test_accounting_payment_tax_inputs_batch.py, tests/unit/test_entry_payment_explicit_inputs_contract.py, tests/unit/test_journal_item_tax_projection_contract.py, tests/unit/test_payment_tax_input_runtime.py
- `integration`：`implemented`；Shared native payment/tax smoke passed; full rollback.；引用：tests/integration/test_document_lifecycle_write_batch_live.py, tests/integration/test_accounting_depth_batch_live.py, tests/integration/test_accounting_payment_tax_inputs_batch_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_entry-lines-update"></a>

## journal_entry.lines.update — 保留行标识批量修改草稿分录

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Fixed line-targeted operations are implemented; native accounting, reference and analytic synchronization ACLs apply. Runtime context and native acceptance are not an unrestricted permission claim.
- 内部domain：`journal_entry`；来源模型：account.account, account.analytic.account, account.analytic.line, account.analytic.plan, account.journal, account.move, account.move.line, res.company, res.currency, res.currency.rate, res.partner, account.tax, account.tax.repartition.line, account.account.tag；向导：无。
- 必需模块：account, analytic, product, uom；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.account:read, account.analytic.account:read, account.analytic.line:create, account.analytic.line:read, account.analytic.line:unlink, account.analytic.plan:read, account.journal:read, account.move.line:read, account.move.line:write, account.move:read, account.move:write, res.company:read, res.currency.rate:read, res.currency:read, res.partner:read, account.tax:read, account.tax.repartition.line:read, account.account.tag:read。
- 请求/响应合同：`schemas/v1/journal_entry.lines.update.request.schema.json` / `schemas/v1/journal_entry.lines.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run journal_entry.lines.update --request "@request.json" --idempotency-key "journal_entry.lines.update:1:b75dd8aa72353d85969d646e006de239" --confirm "journal_entry.lines.update"
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
| parameters.lines | array | 必填（所在对象出现时） |  | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":100,"minItems":1} |
| parameters.lines[] | object | 每个数组元素 |  | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["line_id","changes"]} |
| parameters.lines[].line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.lines[].changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"dependentRequired":{"currency_id":["amount_currency"]},"minProperties":1} |
| parameters.lines[].changes.name | string | 可选（可能有条件限制） |  | 名称/行说明 | {"maxLength":256,"minLength":1} |
| parameters.lines[].changes.account_id | integer | 可选（可能有条件限制） |  | 会计科目ID | {"minimum":1} |
| parameters.lines[].changes.partner_id | integer/null | 可选（可能有条件限制） |  | 合作伙伴ID | {"minimum":1} |
| parameters.lines[].changes.debit | string | 可选（可能有条件限制） |  | 借方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| parameters.lines[].changes.credit | string | 可选（可能有条件限制） |  | 贷方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| parameters.lines[].changes.date_maturity | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.lines[].changes.tax_ids | array | 可选（可能有条件限制） |  | 应用税ID数组 | {"maxItems":100,"uniqueItems":true} |
| parameters.lines[].changes.tax_ids[] | integer | 每个数组元素 |  | 应用税ID数组 | {"minimum":1} |
| parameters.lines[].changes.tax_tag_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":100,"uniqueItems":true} |
| parameters.lines[].changes.tax_tag_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.lines[].changes.tax_repartition_line_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.lines[].changes.tax_base_amount | string | 可选（可能有条件限制） |  |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| parameters.lines[].changes.analytic_distribution | 组合/开放结构 | 可选（可能有条件限制） |  | 分析分摊映射；写入与读回约束可能不同 | {"oneOf":[{"type":"null"},{"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"},"type":"object"}],"resolved_ref":"invoice.lines.replace.request.schema.json#/$defs/invoice_line/properties/analytic_distribution"} |
| parameters.lines[].changes.analytic_distribution | null | 分支约束 | oneOf[1] | 分析分摊映射；写入与读回约束可能不同 |  |
| parameters.lines[].changes.analytic_distribution | object | 分支约束 | oneOf[2] | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":{"$ref":"#/$defs/analytic_percentage"},"maxProperties":16,"minProperties":1,"propertyNames":{"pattern":"^[1-9][0-9]*(?:,[1-9][0-9]*)*$(?![\\s\\S])"}} |
| parameters.lines[].changes.analytic_distribution{其他键} | string | 动态键值 | oneOf[2] |  | {"maxLength":8,"pattern":"^(?:100&#124;(?:[1-9][0-9]?)(?:\\.[0-9]{0,3}[1-9])?&#124;0\\.[0-9]{0,3}[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/analytic_percentage"} |
| parameters.lines[].changes.currency_id | integer | 可选（可能有条件限制） |  | 币种ID | {"minimum":1} |
| parameters.lines[].changes.amount_currency | string | 可选（可能有条件限制） |  | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal_entry.lines.update"} |
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

- `unit`：`implemented`；Existing contracts and explicit payment/tax input extensions are covered.；引用：tests/unit/test_accounting_workflows_batch.py, tests/unit/test_accounting_payment_tax_inputs_batch.py, tests/unit/test_entry_payment_explicit_inputs_contract.py, tests/unit/test_journal_item_tax_projection_contract.py, tests/unit/test_payment_tax_input_runtime.py
- `integration`：`implemented`；Shared native payment/tax smoke passed; full rollback.；引用：tests/integration/test_accounting_workflows_batch_live.py, tests/integration/test_accounting_payment_tax_inputs_batch_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_entry-post"></a>

## journal_entry.post — 原子过账单笔或 2–100 笔普通日记账分录

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`general_ledger`；来源模型：res.company, account.move, account.move.line, account.analytic.account, account.analytic.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.move:read, account.move:write, account.move.line:read。
- 请求/响应合同：`schemas/v1/journal_entry.post.request.schema.json` / `schemas/v1/journal_entry.post.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run journal_entry.post --request "@request.json" --idempotency-key "journal_entry.post:1" --confirm "journal_entry.post"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal_entry.post"} |
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
- `execute`：full_batch_record_scope_company_general_entry_type_and_state_preflight_then_single_transaction_all_or_nothing_native_post
- `verify`：explicit_batch_result_with_exact_normalized_record_ids_target_states_same_transaction_reread_and_response_schema_validation
- `idempotency`：capability_company_and_full_normalized_sorted_record_id_set_key_with_serial_target_state_replay
- `reverse`：journal_entry.reverse

### 已登记测试与证据范围

- `unit`：`implemented`；The existing unit tests continue to cover the singular request and native runtime behavior; the batch contract unit test covers batch-request normalization, full normalized-ID-set idempotency keys, bridge and capability contracts, explicit batch results, and CLI verification.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_core_write_cli.py, tests/unit/test_lifecycle_batch_contract.py
- `integration`：`implemented`；The existing integration smoke continues to cover singular native execution; the new live smoke covers dual-database batch execution, immediate replay, and rollback, plus a representative whole-batch invalid-ID no-op for invoice.post.；引用：tests/integration/test_core_write_batch_live.py, tests/integration/test_batch_lifecycle_write_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_entry-reset_to_draft"></a>

## journal_entry.reset_to_draft — 原子将单笔或 2–100 笔普通日记账分录重置为草稿

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`general_ledger`；来源模型：res.company, account.move, account.move.line, account.analytic.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.move:read, account.move:write, account.move.line:read。
- 请求/响应合同：`schemas/v1/journal_entry.reset_to_draft.request.schema.json` / `schemas/v1/journal_entry.reset_to_draft.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run journal_entry.reset_to_draft --request "@request.json" --idempotency-key "journal_entry.reset_to_draft:1" --confirm "journal_entry.reset_to_draft"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal_entry.reset_to_draft"} |
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
- `execute`：full_batch_record_scope_company_general_entry_type_and_state_preflight_then_single_transaction_all_or_nothing_native_reset_to_draft
- `verify`：explicit_batch_result_with_exact_normalized_record_ids_target_states_same_transaction_reread_and_response_schema_validation
- `idempotency`：capability_company_and_full_normalized_sorted_record_id_set_key_with_serial_target_state_replay
- `reverse`：journal_entry.post_when_business_intent_requires_reposting

### 已登记测试与证据范围

- `unit`：`implemented`；The existing unit tests continue to cover the singular request and native runtime behavior; the batch contract unit test covers batch-request normalization, full normalized-ID-set idempotency keys, bridge and capability contracts, explicit batch results, and CLI verification.；引用：tests/unit/test_document_lifecycle_writes.py, tests/unit/test_document_lifecycle_writes_runtime.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_write_cli.py, tests/unit/test_document_lifecycle_write_cli.py, tests/unit/test_lifecycle_batch_contract.py
- `integration`：`implemented`；The existing integration smoke continues to cover singular native execution; the new live smoke covers dual-database batch execution, immediate replay, and rollback, plus a representative whole-batch invalid-ID no-op for invoice.post.；引用：tests/integration/test_document_lifecycle_write_batch_live.py, tests/integration/test_batch_lifecycle_write_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_entry-reverse"></a>

## journal_entry.reverse — 冲销已过账分录

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`general_ledger`；来源模型：res.company, res.partner.bank, account.journal, account.move, account.move.line, account.analytic.account, account.analytic.line, account.move.reversal；向导：account.move.reversal。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：res.partner.bank:read, account.journal:read, account.move:read, account.move:write, account.move:create, account.move.line:read, account.move.line:create, account.move.reversal:create。
- 请求/响应合同：`schemas/v1/journal_entry.reverse.request.schema.json` / `schemas/v1/journal_entry.reverse.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run journal_entry.reverse --request "@request.json" --idempotency-key "journal_entry.reverse:1" --confirm "journal_entry.reverse"
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
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal_entry.reverse"} |
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
- `verify`：post_write_same_transaction_reread_and_response_schema_validation
- `idempotency`：odoo_persisted_business_marker_and_result_replay
- `reverse`：reverse_the_reversal_with_a_new_business_entry

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request, exact confirmation, fixed bridge action, Odoo-side execution, idempotent replay, and CLI response contract.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_core_write_cli.py
- `integration`：`implemented`；The guarded live write smoke verified first execution and immediate idempotent replay against both dedicated isolated database aliases.；引用：tests/integration/test_core_write_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_entry-search"></a>

## journal_entry.search — 搜索总账分录

- 类型：只读；静态状态：`unconfigured`；handler：`journal_entry_search`。
- 状态原因：`runtime_context_required` — Static registry metadata does not declare target-specific runtime availability; availability is evaluated for each configured database, company, and user.
- 内部domain：`general_ledger`；来源模型：account.move, account.move.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move:read, account.move.line:read, account.journal:read, res.currency:read, res.partner:read。
- 请求/响应合同：`schemas/v1/journal_entry.search.request.schema.json` / `schemas/v1/journal_entry.search.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read journal_entry.search --request "@request.json"
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
| parameters.currency_id | integer | 可选（可能有条件限制） |  | 币种ID | {"minimum":1} |
| parameters.account_id | integer | 可选（可能有条件限制） |  | 会计科目ID | {"minimum":1} |
| parameters.tax_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.line_query | string/null | 可选（可能有条件限制） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |
| parameters.states | array | 可选（可能有条件限制） |  |  | {"maxItems":3,"minItems":1,"uniqueItems":true} |
| parameters.states[] | 未限定 | 每个数组元素 |  |  | {"enum":["draft","posted","cancel"]} |
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal_entry.search"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","date","state","ref","journal","company_id","currency","partner","debit","credit","balance"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.items[].ref | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}]} |
| response.data.items[].ref | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].ref | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1} |
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
| response.data.items[].debit | string | 必填（所在对象出现时） | oneOf[2] | 借方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.items[].credit | string | 必填（所在对象出现时） | oneOf[2] | 贷方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.items[].balance | string | 必填（所在对象出现时） | oneOf[2] | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","date","state","ref","journal","company_id","currency","partner","debit","credit","balance"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.items[].ref | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}]} |
| response.data.items[].ref | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].ref | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
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
| response.data.items[].debit | string | 必填（所在对象出现时） | allOf[1]/then | 借方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.items[].credit | string | 必填（所在对象出现时） | allOf[1]/then | 贷方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.items[].balance | string | 必填（所在对象出现时） | allOf[1]/then | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
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

- `unit`：`implemented`；Existing contracts and optional native same-line/header search filters covered.；引用：tests/unit/test_journal_entries.py, tests/unit/test_journal_entry_bridge.py, tests/unit/test_journal_entry_runtime.py, tests/unit/test_journal_entry_cli.py, tests/unit/test_document_search_batch_contract.py, tests/unit/test_document_search_batch_runtime.py, tests/unit/test_document_search_header_runtime.py, tests/unit/test_document_search_batch_cli.py, tests/unit/test_invoice_business_line_filters_contract.py, tests/unit/test_document_business_filters_runtime.py, tests/unit/test_business_line_search_remove_cli.py
- `integration`：`implemented`；Shared native business-line search and bulk deletion smoke passed; full rollback.；引用：tests/integration/test_journal_entries_live.py, tests/integration/test_document_search_bulk_lines_live.py, tests/integration/test_business_line_search_remove_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_entry-update"></a>

## journal_entry.update — 更新草稿总账分录表头

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`general_ledger`；来源模型：res.company, account.journal, account.move；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.journal:read, account.move:read, account.move:write。
- 请求/响应合同：`schemas/v1/journal_entry.update.request.schema.json` / `schemas/v1/journal_entry.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run journal_entry.update --request "@request.json" --idempotency-key "journal_entry.update:1:2757de2acaa2fd8599a790c7442961bd" --confirm "journal_entry.update"
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
      "date": "2026-10-31"
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
| parameters.changes.date | string | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.changes.journal_id | integer | 可选（可能有条件限制） |  | 日记账ID | {"minimum":1} |
| parameters.changes.reference | string/null | 可选（可能有条件限制） |  |  | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal_entry.update"} |
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
- `execute`：native_draft_header_write_or_posted_existing_reference_fields_only
- `verify`：same_transaction_target_header_payload_reread_and_response_schema_validation
- `idempotency`：target_header_payload_state_check_before_native_write
- `reverse`：repeat_update_with_previous_header_values

### 已登记测试与证据范围

- `unit`：`implemented`；Closed typed inputs, legacy request/key compatibility, native scopes and posted nonfinancial boundaries.；引用：tests/unit/test_accounting_setup_batch.py
- `integration`：`implemented`；One shared public CLI/native ORM workflow passed both isolated aliases in 22.30s as uid5/su=False/company1. Two new IDs and six extensions: company cash-basis assign/clear/get/replay; optional advanced tax fields, native grouped-tax invoice computation and transition-account rules; sale/purchase posted reference and narration/user edits including a partially reconciled invoice with raw matching IDs/amounts unchanged; posted entry references; financial/shipping denials; positive/negative/zero/minor-unit native currency-aware cash-rounding computation. Native configuration roles exist only inside the isolated transaction; caller never gains sudo. Fresh fixtures, both companies settings, all defaults, currencies/rates and exact caller/native group memberships roll back. Root cash-basis boolean natively propagates to branches; the live topology uses independent roots, not a tested branch workflow. Company ORM write does not run settings UI onchange or delete cash-basis taxes. Group-to-leaf native write need not clear children; non-group calculation ignores retained children. Actual cash-basis entry lifecycle, all hierarchy/currency/localization/hash/lock paths, PDF regeneration, external sends and concurrent exactly-once are not claimed. No business DB, native source/addon or service changes.；引用：tests/integration/test_accounting_setup_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_item-get"></a>

## journal_item.get — 获取会计分录行详情

- 类型：只读；静态状态：`unconfigured`；handler：`journal_item_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`general_ledger`；来源模型：res.company, account.move.line, account.move, account.account, account.journal, res.partner, res.currency；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move.line:read, account.move:read, account.account:read, account.journal:read, res.partner:read, res.currency:read。
- 请求/响应合同：`schemas/v1/journal_item.get.request.schema.json` / `schemas/v1/journal_item.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read journal_item.get --request "@request.json"
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
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["line_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.line_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"journal_item.search.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal_item.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"journal_item.search.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","date","date_maturity","move","account","partner","journal","name","reference","debit","credit","balance","amount_currency","currency","reconciled","matching_number","analytic_distribution","tax_line_id","tax_ids","tax_base_amount"],"resolved_ref":"journal_item.search.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.date_maturity | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}]} |
| response.data.date_maturity | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.date_maturity | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.move | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","state","move_type"]} |
| response.data.move.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.move.name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.move.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.move.move_type | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.account | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.account.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.account.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.account.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.partner | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"additionalProperties":false,"properties":{"id":{"minimum":1,"type":"integer"},"name":{"minLength":1,"type":"string"}},"required":["id","name"],"type":"object"}]} |
| response.data.partner | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.partner | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"]} |
| response.data.partner.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 |  |
| response.data.reference | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.reference | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.reference | string | 分支约束 | oneOf[2]/oneOf[2] |  |  |
| response.data.debit | string | 必填（所在对象出现时） | oneOf[2] | 借方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.credit | string | 必填（所在对象出现时） | oneOf[2] | 贷方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.balance | string | 必填（所在对象出现时） | oneOf[2] | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_currency | string | 必填（所在对象出现时） | oneOf[2] | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"]} |
| response.data.currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.reconciled | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.matching_number | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.matching_number | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.matching_number | string | 分支约束 | oneOf[2]/oneOf[2] |  |  |
| response.data.analytic_distribution | object | 必填（所在对象出现时） | oneOf[2] | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":{"pattern":"^(?:0&#124;-?(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9]))(?![\\s\\S])","type":"string"},"propertyNames":{"minLength":1,"type":"string"},"resolved_ref":"#/$defs/analytic_distribution"} |
| response.data.analytic_distribution{其他键} | string | 动态键值 | oneOf[2] |  | {"pattern":"^(?:0&#124;-?(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9]))(?![\\s\\S])"} |
| response.data.tax_line_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.tax_ids | array | 必填（所在对象出现时） | oneOf[2] | 应用税ID数组 | {"uniqueItems":true} |
| response.data.tax_ids[] | integer | 每个数组元素 | oneOf[2] | 应用税ID数组 | {"minimum":1} |
| response.data.tax_tag_ids | array | 可选（可能有条件限制） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.tax_tag_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.tax_repartition_line_id | integer/null | 可选（可能有条件限制） | oneOf[2] |  | {"minimum":1} |
| response.data.tax_base_amount | string | 必填（所在对象出现时） | oneOf[2] | Tax base in the journal item's company currency. | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"journal_item.search.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","date","date_maturity","move","account","partner","journal","name","reference","debit","credit","balance","amount_currency","currency","reconciled","matching_number","analytic_distribution","tax_line_id","tax_ids","tax_base_amount"],"resolved_ref":"journal_item.search.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.date_maturity | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}]} |
| response.data.date_maturity | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.date_maturity | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date"} |
| response.data.move | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","state","move_type"]} |
| response.data.move.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.move.name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.move.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.move.move_type | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.account | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.account.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.account.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.account.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"additionalProperties":false,"properties":{"id":{"minimum":1,"type":"integer"},"name":{"minLength":1,"type":"string"}},"required":["id","name"],"type":"object"}]} |
| response.data.partner | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.partner | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"]} |
| response.data.partner.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.partner.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 |  |
| response.data.reference | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.reference | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.reference | string | 分支约束 | allOf[1]/then/oneOf[2] |  |  |
| response.data.debit | string | 必填（所在对象出现时） | allOf[1]/then | 借方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.credit | string | 必填（所在对象出现时） | allOf[1]/then | 贷方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.balance | string | 必填（所在对象出现时） | allOf[1]/then | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.amount_currency | string | 必填（所在对象出现时） | allOf[1]/then | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"]} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.matching_number | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.matching_number | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.matching_number | string | 分支约束 | allOf[1]/then/oneOf[2] |  |  |
| response.data.analytic_distribution | object | 必填（所在对象出现时） | allOf[1]/then | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":{"pattern":"^(?:0&#124;-?(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9]))(?![\\s\\S])","type":"string"},"propertyNames":{"minLength":1,"type":"string"},"resolved_ref":"#/$defs/analytic_distribution"} |
| response.data.analytic_distribution{其他键} | string | 动态键值 | allOf[1]/then |  | {"pattern":"^(?:0&#124;-?(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9]))(?![\\s\\S])"} |
| response.data.tax_line_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.tax_ids | array | 必填（所在对象出现时） | allOf[1]/then | 应用税ID数组 | {"uniqueItems":true} |
| response.data.tax_ids[] | integer | 每个数组元素 | allOf[1]/then | 应用税ID数组 | {"minimum":1} |
| response.data.tax_tag_ids | array | 可选（可能有条件限制） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.tax_tag_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.tax_repartition_line_id | integer/null | 可选（可能有条件限制） | allOf[1]/then |  | {"minimum":1} |
| response.data.tax_base_amount | string | 必填（所在对象出现时） | allOf[1]/then | Tax base in the journal item's company currency. | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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

- `unit`：`implemented`；Existing contracts and explicit payment/tax input extensions are covered.；引用：tests/unit/test_core_object_reads.py, tests/unit/test_core_object_reads_bridge.py, tests/unit/test_core_object_reads_runtime.py, tests/unit/test_core_object_read_cli.py, tests/unit/test_journal_item_tax_links.py, tests/unit/test_accounting_payment_tax_inputs_batch.py, tests/unit/test_journal_item_tax_projection_contract.py
- `integration`：`implemented`；Shared native payment/tax smoke passed; full rollback.；引用：tests/integration/test_core_object_read_batch_live.py, tests/integration/test_invoice_tax_flow_batch_live.py, tests/integration/test_accounting_payment_tax_inputs_batch_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_item-processing_details-get"></a>

## journal_item.processing_details.get — 查看分录行处理详情

- 类型：只读；静态状态：`unconfigured`；handler：`journal_item_processing_details_get`。
- 状态原因：`runtime_context_required` — Fixed line-targeted operations are implemented; native accounting, reference and analytic synchronization ACLs apply. Runtime context and native acceptance are not an unrestricted permission claim.
- 内部domain：`journal_item`；来源模型：res.company, account.move.line, account.move, account.account, product.product, uom.uom, account.payment, account.bank.statement.line, res.currency；向导：无。
- 必需模块：account, analytic, product, uom；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move.line:read, account.move:read, account.account:read, product.product:read, uom.uom:read, account.payment:read, account.bank.statement.line:read, res.currency:read。
- 请求/响应合同：`schemas/v1/journal_item.processing_details.get.request.schema.json` / `schemas/v1/journal_item.processing_details.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read journal_item.processing_details.get --request "@request.json"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal_item.processing_details.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","move_id","company_id","currency_id","company_currency_id","account_id","product_id","product_uom_id","payment_id","statement_line_id","date_maturity","discount_date","amount_residual","amount_residual_currency","discount_amount_currency","parent_state","move_type","display_type","deductible_amount","no_followup"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.move_id | integer | 必填（所在对象出现时） | oneOf[2] | 会计单据记录ID | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.currency_id | integer | 必填（所在对象出现时） | oneOf[2] | 币种ID | {"minimum":1} |
| response.data.company_currency_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.account_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 会计科目ID | {"minimum":1} |
| response.data.product_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.product_uom_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.payment_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 付款/收款记录ID | {"minimum":1} |
| response.data.statement_line_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.date_maturity | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.discount_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.amount_residual | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.amount_residual_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.discount_amount_currency | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.parent_state | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["draft","posted","cancel"]} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["entry","out_invoice","in_invoice","out_refund","in_refund","out_receipt","in_receipt"]} |
| response.data.display_type | string | 必填（所在对象出现时） | oneOf[2] | 业务行/章节/备注类型 | {"minLength":1} |
| response.data.deductible_amount | string | 必填（所在对象出现时） | oneOf[2] | 可抵扣百分比，不是可抵扣货币金额 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.tax_ids | array | 可选（可能有条件限制） | oneOf[2] | 应用税ID数组 | {"uniqueItems":true} |
| response.data.tax_ids[] | integer | 每个数组元素 | oneOf[2] | 应用税ID数组 | {"minimum":1} |
| response.data.tax_tag_ids | array | 可选（可能有条件限制） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.tax_tag_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.tax_repartition_line_id | integer/null | 可选（可能有条件限制） | oneOf[2] |  | {"minimum":1} |
| response.data.tax_base_amount | string | 可选（可能有条件限制） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.tax_line_id | integer/null | 可选（可能有条件限制） | oneOf[2] |  | {"minimum":1} |
| response.data.no_followup | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","move_id","company_id","currency_id","company_currency_id","account_id","product_id","product_uom_id","payment_id","statement_line_id","date_maturity","discount_date","amount_residual","amount_residual_currency","discount_amount_currency","parent_state","move_type","display_type","deductible_amount","no_followup"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.move_id | integer | 必填（所在对象出现时） | allOf[1]/then | 会计单据记录ID | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.currency_id | integer | 必填（所在对象出现时） | allOf[1]/then | 币种ID | {"minimum":1} |
| response.data.company_currency_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 会计科目ID | {"minimum":1} |
| response.data.product_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.product_uom_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.payment_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 付款/收款记录ID | {"minimum":1} |
| response.data.statement_line_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.date_maturity | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.discount_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.amount_residual | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.amount_residual_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.discount_amount_currency | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.parent_state | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["draft","posted","cancel"]} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["entry","out_invoice","in_invoice","out_refund","in_refund","out_receipt","in_receipt"]} |
| response.data.display_type | string | 必填（所在对象出现时） | allOf[1]/then | 业务行/章节/备注类型 | {"minLength":1} |
| response.data.deductible_amount | string | 必填（所在对象出现时） | allOf[1]/then | 可抵扣百分比，不是可抵扣货币金额 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.tax_ids | array | 可选（可能有条件限制） | allOf[1]/then | 应用税ID数组 | {"uniqueItems":true} |
| response.data.tax_ids[] | integer | 每个数组元素 | allOf[1]/then | 应用税ID数组 | {"minimum":1} |
| response.data.tax_tag_ids | array | 可选（可能有条件限制） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.tax_tag_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.tax_repartition_line_id | integer/null | 可选（可能有条件限制） | allOf[1]/then |  | {"minimum":1} |
| response.data.tax_base_amount | string | 可选（可能有条件限制） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])"} |
| response.data.tax_line_id | integer/null | 可选（可能有条件限制） | allOf[1]/then |  | {"minimum":1} |
| response.data.no_followup | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
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

- `unit`：`implemented`；Existing contracts and explicit payment/tax input extensions are covered.；引用：tests/unit/test_journal_item_processing_batch.py, tests/unit/test_accounting_payment_tax_inputs_batch.py, tests/unit/test_journal_item_tax_projection_contract.py
- `integration`：`implemented`；Shared native payment/tax smoke passed; full rollback.；引用：tests/integration/test_journal_item_processing_batch_live.py, tests/integration/test_accounting_payment_tax_inputs_batch_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal_item-search"></a>

## journal_item.search — 搜索会计分录行

- 类型：只读；静态状态：`unconfigured`；handler：`journal_item_search`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`general_ledger`；来源模型：res.company, account.move.line, account.move, account.account, account.journal, res.partner, res.currency；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move.line:read, account.move:read, account.account:read, account.journal:read, res.partner:read, res.currency:read。
- 请求/响应合同：`schemas/v1/journal_item.search.request.schema.json` / `schemas/v1/journal_item.search.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read journal_item.search --request "@request.json"
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
| parameters.date_from | string/null | 可选（可能有条件限制） |  | 开始日期 | {"format":"date"} |
| parameters.date_to | string/null | 可选（可能有条件限制） |  | 结束日期 | {"format":"date"} |
| parameters.move_id | integer/null | 可选（可能有条件限制） |  | 会计单据记录ID | {"minimum":1} |
| parameters.account_id | integer/null | 可选（可能有条件限制） |  | 会计科目ID | {"minimum":1} |
| parameters.partner_id | integer/null | 可选（可能有条件限制） |  | 合作伙伴ID | {"minimum":1} |
| parameters.journal_id | integer/null | 可选（可能有条件限制） |  | 日记账ID | {"minimum":1} |
| parameters.posted_only | boolean | 可选（可能有条件限制） |  |  | {"default":false} |
| parameters.currency_id | integer | 可选（可能有条件限制） |  | 币种ID | {"minimum":1} |
| parameters.product_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.tax_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.due_date_from | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.due_date_to | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.reconciled | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.move_types | array | 可选（可能有条件限制） |  |  | {"maxItems":7,"minItems":1,"uniqueItems":true} |
| parameters.move_types[] | 未限定 | 每个数组元素 |  |  | {"enum":["entry","out_invoice","out_refund","in_invoice","in_refund","out_receipt","in_receipt"]} |
| parameters.query | string/null | 可选（可能有条件限制） |  | 搜索文本 | {"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal_item.search"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","date","date_maturity","move","account","partner","journal","name","reference","debit","credit","balance","amount_currency","currency","reconciled","matching_number","analytic_distribution","tax_line_id","tax_ids","tax_base_amount"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].date_maturity | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}]} |
| response.data.items[].date_maturity | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].date_maturity | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.items[].move | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","state","move_type"]} |
| response.data.items[].move.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].move.name | string/null | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].move.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.items[].move.move_type | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].account | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.items[].account.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].account.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].account.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"additionalProperties":false,"properties":{"id":{"minimum":1,"type":"integer"},"name":{"minLength":1,"type":"string"}},"required":["id","name"],"type":"object"}]} |
| response.data.items[].partner | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"]} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 |  |
| response.data.items[].reference | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.items[].reference | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].reference | string | 分支约束 | oneOf[2]/oneOf[2] |  |  |
| response.data.items[].debit | string | 必填（所在对象出现时） | oneOf[2] | 借方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].credit | string | 必填（所在对象出现时） | oneOf[2] | 贷方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].balance | string | 必填（所在对象出现时） | oneOf[2] | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_currency | string | 必填（所在对象出现时） | oneOf[2] | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"]} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].reconciled | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].matching_number | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.items[].matching_number | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].matching_number | string | 分支约束 | oneOf[2]/oneOf[2] |  |  |
| response.data.items[].analytic_distribution | object | 必填（所在对象出现时） | oneOf[2] | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":{"pattern":"^(?:0&#124;-?(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9]))(?![\\s\\S])","type":"string"},"propertyNames":{"minLength":1,"type":"string"},"resolved_ref":"#/$defs/analytic_distribution"} |
| response.data.items[].analytic_distribution{其他键} | string | 动态键值 | oneOf[2] |  | {"pattern":"^(?:0&#124;-?(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9]))(?![\\s\\S])"} |
| response.data.items[].tax_line_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].tax_ids | array | 必填（所在对象出现时） | oneOf[2] | 应用税ID数组 | {"uniqueItems":true} |
| response.data.items[].tax_ids[] | integer | 每个数组元素 | oneOf[2] | 应用税ID数组 | {"minimum":1} |
| response.data.items[].tax_tag_ids | array | 可选（可能有条件限制） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.items[].tax_tag_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.items[].tax_repartition_line_id | integer/null | 可选（可能有条件限制） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].tax_base_amount | string | 必填（所在对象出现时） | oneOf[2] | Tax base in the journal item's company currency. | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","date","date_maturity","move","account","partner","journal","name","reference","debit","credit","balance","amount_currency","currency","reconciled","matching_number","analytic_distribution","tax_line_id","tax_ids","tax_base_amount"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].date_maturity | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"format":"date","type":"string"}]} |
| response.data.items[].date_maturity | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].date_maturity | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date"} |
| response.data.items[].move | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","state","move_type"]} |
| response.data.items[].move.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].move.name | string/null | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].move.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.items[].move.move_type | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].account | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.items[].account.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].account.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].account.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].partner | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"additionalProperties":false,"properties":{"id":{"minimum":1,"type":"integer"},"name":{"minLength":1,"type":"string"}},"required":["id","name"],"type":"object"}]} |
| response.data.items[].partner | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].partner | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"]} |
| response.data.items[].partner.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].partner.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"]} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 |  |
| response.data.items[].reference | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.items[].reference | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].reference | string | 分支约束 | allOf[1]/then/oneOf[2] |  |  |
| response.data.items[].debit | string | 必填（所在对象出现时） | allOf[1]/then | 借方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].credit | string | 必填（所在对象出现时） | allOf[1]/then | 贷方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].balance | string | 必填（所在对象出现时） | allOf[1]/then | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].amount_currency | string | 必填（所在对象出现时） | allOf[1]/then | 外币/交易币数值，非默认公司币金额 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"]} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].reconciled | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].matching_number | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"type":"string"}]} |
| response.data.items[].matching_number | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].matching_number | string | 分支约束 | allOf[1]/then/oneOf[2] |  |  |
| response.data.items[].analytic_distribution | object | 必填（所在对象出现时） | allOf[1]/then | 分析分摊映射；写入与读回约束可能不同 | {"additionalProperties":{"pattern":"^(?:0&#124;-?(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9]))(?![\\s\\S])","type":"string"},"propertyNames":{"minLength":1,"type":"string"},"resolved_ref":"#/$defs/analytic_distribution"} |
| response.data.items[].analytic_distribution{其他键} | string | 动态键值 | allOf[1]/then |  | {"pattern":"^(?:0&#124;-?(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9]))(?![\\s\\S])"} |
| response.data.items[].tax_line_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].tax_ids | array | 必填（所在对象出现时） | allOf[1]/then | 应用税ID数组 | {"uniqueItems":true} |
| response.data.items[].tax_ids[] | integer | 每个数组元素 | allOf[1]/then | 应用税ID数组 | {"minimum":1} |
| response.data.items[].tax_tag_ids | array | 可选（可能有条件限制） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.items[].tax_tag_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].tax_repartition_line_id | integer/null | 可选（可能有条件限制） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].tax_base_amount | string | 必填（所在对象出现时） | allOf[1]/then | Tax base in the journal item's company currency. | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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

- `unit`：`implemented`；Existing contracts and optional native same-line/header search filters covered.；引用：tests/unit/test_core_object_reads.py, tests/unit/test_core_object_reads_bridge.py, tests/unit/test_core_object_reads_runtime.py, tests/unit/test_core_object_read_cli.py, tests/unit/test_journal_item_tax_links.py, tests/unit/test_accounting_payment_tax_inputs_batch.py, tests/unit/test_journal_item_tax_projection_contract.py, tests/unit/test_document_search_batch_contract.py, tests/unit/test_document_search_batch_runtime.py, tests/unit/test_document_search_header_runtime.py, tests/unit/test_document_search_batch_cli.py, tests/unit/test_invoice_business_line_filters_contract.py, tests/unit/test_document_business_filters_runtime.py, tests/unit/test_business_line_search_remove_cli.py
- `integration`：`implemented`；Shared native business-line search and bulk deletion smoke passed; full rollback.；引用：tests/integration/test_core_object_read_batch_live.py, tests/integration/test_invoice_tax_flow_batch_live.py, tests/integration/test_accounting_payment_tax_inputs_batch_live.py, tests/integration/test_document_search_bulk_lines_live.py, tests/integration/test_business_line_search_remove_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-localization-china-voucher-render"></a>

## localization.china.voucher.render — 导出中国会计凭证 PDF

- 类型：只读；静态状态：`unconfigured`；handler：`document_localization_china_voucher_render`。
- 状态原因：`runtime_context_required` — The fixed l10n_cn_reports action_report_account_move_print handler avoids the legacy cn2an-dependent voucher template; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`localization_china`；来源模型：account.move, res.company, res.country, ir.actions.report；向导：无。
- 必需模块：l10n_cn_reports；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.move:read, res.company:read, res.country:read, ir.actions.report:read。
- 请求/响应合同：`schemas/v1/localization.china.voucher.render.request.schema.json` / `schemas/v1/localization.china.voucher.render.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read localization.china.voucher.render --request "@request.json"
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
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["move_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.move_id | integer | 必填（所在对象出现时） |  | 会计单据记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"localization.china.voucher.render"} |
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
- `execute`：fixed_l10n_cn_reports_action_report_account_move_print
- `verify`：bound_record_pdf_bytes_hash_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover the fixed action, exact contract, bridge, runtime, CLI routing, registry metadata, and schemas.；引用：tests/unit/test_document_exports.py, tests/unit/test_document_exports_bridge.py, tests/unit/test_document_exports_runtime.py, tests/unit/test_document_export_cli.py, tests/unit/test_document_export_registry.py
- `integration`：`implemented`；The shared read-only live smoke covers the fixed document export batch in both isolated databases.；引用：tests/integration/test_document_export_batch_live.py
- `golden`：`planned`；Golden PDF evidence is pending.；引用：无
- `e2e`：`planned`；End-to-end natural-language routing evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-recurring-journal_entry-get"></a>

## recurring.journal_entry.get — 读取自动过账和周期分录

- 类型：只读；静态状态：`unconfigured`；handler：`recurring_journal_entry_get`。
- 状态原因：`runtime_context_required` — The fixed read handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`general_ledger`；来源模型：res.company, account.move, account.journal, res.partner, res.currency；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move:read, account.journal:read, res.partner:read, res.currency:read。
- 请求/响应合同：`schemas/v1/recurring.journal_entry.get.request.schema.json` / `schemas/v1/recurring.journal_entry.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read recurring.journal_entry.get --request "@request.json"
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
    "entry_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["entry_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.entry_id | integer | 必填（所在对象出现时） |  | 分录记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"recurring.journal_entry.search.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"recurring.journal_entry.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"recurring.journal_entry.search.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","name","date","state","journal","reference","auto_post","auto_post_until","auto_post_origin"],"resolved_ref":"recurring.journal_entry.search.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.reference | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.auto_post | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["at_date","monthly","quarterly","yearly"]} |
| response.data.auto_post_until | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.auto_post_origin | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.auto_post_origin | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.auto_post_origin | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.auto_post_origin.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.auto_post_origin.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"recurring.journal_entry.search.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","name","date","state","journal","reference","auto_post","auto_post_until","auto_post_origin"],"resolved_ref":"recurring.journal_entry.search.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.reference | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.auto_post | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["at_date","monthly","quarterly","yearly"]} |
| response.data.auto_post_until | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.auto_post_origin | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.auto_post_origin | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.auto_post_origin | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.auto_post_origin.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.auto_post_origin.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
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
- `execute`：fixed_company_scoped_recurring_journal_entry_get
- `verify`：same_transaction_acl_company_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared focused test covers registry metadata, fixed CLI routing, model mapping, and exclusion of inventory capabilities.；引用：tests/unit/test_accounting_operational_reads_registry_cli.py
- `integration`：`implemented`；The shared ordinary-accounting-user read-only smoke passed for all twelve capabilities on both dedicated isolated database aliases.；引用：tests/integration/test_accounting_operational_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-recurring-journal_entry-search"></a>

## recurring.journal_entry.search — 搜索自动过账和周期分录

- 类型：只读；静态状态：`unconfigured`；handler：`recurring_journal_entry_search`。
- 状态原因：`runtime_context_required` — The fixed read handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`general_ledger`；来源模型：res.company, account.move, account.journal, res.partner, res.currency；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move:read, account.journal:read, res.partner:read, res.currency:read。
- 请求/响应合同：`schemas/v1/recurring.journal_entry.search.request.schema.json` / `schemas/v1/recurring.journal_entry.search.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read recurring.journal_entry.search --request "@request.json"
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
| parameters.states | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"default":null,"oneOf":[{"type":"null"},{"items":{"enum":["draft","posted","cancel"]},"maxItems":3,"minItems":1,"type":"array","uniqueItems":true}]} |
| parameters.states | null | 分支约束 | oneOf[1] |  |  |
| parameters.states | array | 分支约束 | oneOf[2] |  | {"maxItems":3,"minItems":1,"uniqueItems":true} |
| parameters.states[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["draft","posted","cancel"]} |
| parameters.auto_post_types | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"default":null,"oneOf":[{"type":"null"},{"items":{"enum":["at_date","monthly","quarterly","yearly"]},"maxItems":4,"minItems":1,"type":"array","uniqueItems":true}]} |
| parameters.auto_post_types | null | 分支约束 | oneOf[1] |  |  |
| parameters.auto_post_types | array | 分支约束 | oneOf[2] |  | {"maxItems":4,"minItems":1,"uniqueItems":true} |
| parameters.auto_post_types[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["at_date","monthly","quarterly","yearly"]} |
| parameters.date_from | string/null | 可选（可能有条件限制） |  | 开始日期 | {"default":null,"format":"date"} |
| parameters.date_to | string/null | 可选（可能有条件限制） |  | 结束日期 | {"default":null,"format":"date"} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"recurring.journal_entry.search"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","name","date","state","journal","reference","auto_post","auto_post_until","auto_post_origin"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.items[].journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].reference | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].auto_post | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["at_date","monthly","quarterly","yearly"]} |
| response.data.items[].auto_post_until | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].auto_post_origin | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].auto_post_origin | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].auto_post_origin | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].auto_post_origin.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].auto_post_origin.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","name","date","state","journal","reference","auto_post","auto_post_until","auto_post_origin"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.items[].journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].reference | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].auto_post | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["at_date","monthly","quarterly","yearly"]} |
| response.data.items[].auto_post_until | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].auto_post_origin | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].auto_post_origin | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].auto_post_origin | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].auto_post_origin.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].auto_post_origin.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
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
- `execute`：fixed_company_scoped_recurring_journal_entry_search
- `verify`：same_transaction_acl_cursor_company_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared focused test covers registry metadata, fixed CLI routing, model mapping, and exclusion of inventory capabilities.；引用：tests/unit/test_accounting_operational_reads_registry_cli.py
- `integration`：`implemented`；The shared ordinary-accounting-user read-only smoke passed for all twelve capabilities on both dedicated isolated database aliases.；引用：tests/integration/test_accounting_operational_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-validation-journal_entry-check"></a>

## validation.journal_entry.check — 验证总账分录就绪状态

- 类型：只读；静态状态：`unconfigured`；handler：`validation_journal_entry_check`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`validation`；来源模型：account.move, account.move.line；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.move:read, account.move.line:read, account.journal:read, account.account:read, res.currency:read, res.partner:read。
- 请求/响应合同：`schemas/v1/validation.journal_entry.check.request.schema.json` / `schemas/v1/validation.journal_entry.check.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read validation.journal_entry.check --request "@request.json"
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
    "entry_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["entry_id"]} |
| parameters.entry_id | integer | 必填（所在对象出现时） |  | 分录记录ID | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"validation.journal_entry.check"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["entry_id","company_id","state","ready","checks","line_count","accountable_line_count","totals"],"resolved_ref":"#/$defs/data"} |
| response.data.entry_id | integer | 必填（所在对象出现时） | oneOf[2] | 分录记录ID | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.ready | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.checks | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["company_matches","state_is_draft","debits_equal_credits","line_items_valid"],"resolved_ref":"#/$defs/checks"} |
| response.data.checks.company_matches | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":true} |
| response.data.checks.state_is_draft | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.checks.debits_equal_credits | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.checks.line_items_valid | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.line_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.accountable_line_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.totals | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["debit","credit","balance"],"resolved_ref":"#/$defs/totals"} |
| response.data.totals.debit | string | 必填（所在对象出现时） | oneOf[2] | 借方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.totals.credit | string | 必填（所在对象出现时） | oneOf[2] | 贷方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.totals.balance | string | 必填（所在对象出现时） | oneOf[2] | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["entry_id","company_id","state","ready","checks","line_count","accountable_line_count","totals"],"resolved_ref":"#/$defs/data"} |
| response.data.entry_id | integer | 必填（所在对象出现时） | allOf[1]/then | 分录记录ID | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.ready | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.checks | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["company_matches","state_is_draft","debits_equal_credits","line_items_valid"],"resolved_ref":"#/$defs/checks"} |
| response.data.checks.company_matches | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"const":true} |
| response.data.checks.state_is_draft | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.checks.debits_equal_credits | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.checks.line_items_valid | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.line_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.accountable_line_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.totals | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["debit","credit","balance"],"resolved_ref":"#/$defs/totals"} |
| response.data.totals.debit | string | 必填（所在对象出现时） | allOf[1]/then | 借方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.totals.credit | string | 必填（所在对象出现时） | allOf[1]/then | 贷方值；不得丢弃原生storno符号 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
| response.data.totals.balance | string | 必填（所在对象出现时） | allOf[1]/then | 余额；币种与范围取决于本对象 | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/money"} |
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
- `execute`：fixed_journal_entry_readiness_check
- `verify`：same_transaction_entry_totals_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request, fixed journal-entry read reuse, balance and line checks, and CLI dispatch.；引用：tests/unit/test_journal_entry_validation.py, tests/unit/test_journal_entry_validation_bridge.py, tests/unit/test_capability_batch_cli.py
- `integration`：`implemented`；The shared live integration test verifies the capability against both dedicated synthetic database aliases without committing database changes.；引用：tests/integration/test_read_capability_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。
