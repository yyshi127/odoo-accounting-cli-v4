# 客户开票、销售来源开票与贷项通知单

创建客户发票和来源贷项通知单，由销售订单生成发票或预付款发票，配置客户发票编号与可用模板，并检查或加入客户单据发送队列。发票查改和过账使用共用发票场景；贷项通知单不代表已经向客户退现金，发送队列不代表外部邮箱已收到。

[回到总说明书](../../CLI_V4_MANUAL.md) · [新会话使用指南](../USAGE_GUIDE.md)

<a id="cap-customer_credit_note-create"></a>

## customer_credit_note.create — 创建客户贷项通知单

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime. Batch move_ids creates full native refunds for 2-100 posted sources with operation/key markers binding the complete selection. Markers are not concurrency-unique.
- 内部domain：`invoices_and_bills`；来源模型：res.company, res.partner.bank, account.journal, account.move, account.move.reversal, res.partner, product.product, account.account, account.tax, account.move.line, account.analytic.account；向导：account.move.reversal。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：res.partner.bank:read, account.journal:read, account.move:read, account.move:write, account.move:create, account.move.reversal:create, res.partner:read, account.account:read, account.tax:read, account.move.line:read, account.move.line:create, account.move.line:write, account.move.line:unlink。
- 请求/响应合同：`schemas/v1/customer_credit_note.create.request.schema.json` / `schemas/v1/customer_credit_note.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run customer_credit_note.create --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "customer_credit_note.create"
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
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"customer_credit_note.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"core-write-batch-result.schema.json"}]},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"customer_credit_note.create"} |
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
- `reverse`：create_a_new_correcting_invoice

### 已登记测试与证据范围

- `unit`：`implemented`；Existing contracts and explicit native line unit/deductibility inputs covered.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_core_write_cli.py, tests/unit/test_accounting_entry_membership_batch.py, tests/unit/test_invoice_rounds_write_contract.py, tests/unit/test_invoice_rounds_runtime.py, tests/unit/test_invoice_rounds_product_reads.py, tests/unit/test_invoice_rounds_cli.py, tests/unit/test_invoice_line_inputs_contract.py, tests/unit/test_invoice_line_inputs_runtime.py
- `integration`：`implemented`；Shared native smoke passed; full rollback.；引用：tests/integration/test_core_write_batch_live.py, tests/integration/test_accounting_depth_batch_live.py, tests/integration/test_accounting_entry_membership_batch_live.py, tests/integration/test_invoice_rounds_live.py, tests/integration/test_invoice_line_inputs_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-customer_invoice-create"></a>

## customer_invoice.create — 创建草稿客户发票

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`invoices_and_bills`；来源模型：res.company, res.partner, res.partner.bank, account.fiscal.position, res.currency, account.journal, account.account, account.tax, account.move, account.move.line, product.product, account.payment.term, account.analytic.account；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：res.partner:read, res.partner.bank:read, account.fiscal.position:read, res.currency:read, account.journal:read, account.account:read, account.tax:read, account.move:read, account.move:create, account.move.line:read, account.move.line:create。
- 请求/响应合同：`schemas/v1/customer_invoice.create.request.schema.json` / `schemas/v1/customer_invoice.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run customer_invoice.create --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "customer_invoice.create"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"customer_invoice.create"} |
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
- `reverse`：delete_draft_or_customer_credit_note.create_after_posting

### 已登记测试与证据范围

- `unit`：`implemented`；Existing contracts and explicit native line unit/deductibility inputs covered.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_invoice_financial_headers.py, tests/unit/test_invoice_financial_headers_runtime.py, tests/unit/test_core_write_cli.py, tests/unit/test_accounting_entry_membership_batch.py, tests/unit/test_invoice_line_inputs_contract.py, tests/unit/test_invoice_line_inputs_runtime.py
- `integration`：`implemented`；Shared native smoke passed; full rollback.；引用：tests/integration/test_core_write_batch_live.py, tests/integration/test_accounting_depth_batch_live.py, tests/integration/test_invoice_financial_headers_prepayment_batch_live.py, tests/integration/test_accounting_entry_membership_batch_live.py, tests/integration/test_invoice_line_inputs_live.py
- `golden`：`planned`；Deferred.；引用：无
- `e2e`：`planned`；Deferred.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-send"></a>

## invoice.send — 将客户发票、贷项通知单或收据加入 Odoo 发送队列

- 类型：写入；静态状态：`degraded`；handler：`accounting_delivery`。
- 状态原因：`odoo_queue_delivery_only` — The fixed handler verifies its Odoo message marker after invoking the native queue-only delivery path; it does not claim mail-queue persistence or external SMTP delivery.
- 内部domain：`invoices_and_bills`；来源模型：res.company, account.move, res.partner, mail.template, ir.actions.report, mail.message, mail.mail, ir.attachment；向导：account.move.send.wizard。
- 必需模块：account, mail；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：res.company:read, account.move:read, account.move:write, res.partner:read, mail.template:read, ir.actions.report:read, account.move.send.wizard:read, account.move.send.wizard:create, account.move.send.wizard:write, mail.message:read, mail.mail:read, ir.attachment:read。
- 请求/响应合同：`schemas/v1/invoice.send.request.schema.json` / `schemas/v1/invoice.send.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run invoice.send --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "invoice.send"
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
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.send"} |
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
- `execute`：fixed_native_account_move_send_wizard_with_queued_delivery
- `verify`：same_transaction_marked_message_and_response_schema_validation
- `idempotency`：caller_key_marker_serial_replay_without_concurrent_or_external_transport_exactly_once_guarantee
- `reverse`：cancel_pending_mail_outside_this_capability

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover the closed singular-or-batch request, confirmation, idempotency key, result binding, registry metadata, and schemas.；引用：tests/unit/test_accounting_delivery.py, tests/unit/test_accounting_delivery_registry.py
- `integration`：`implemented`；The guarded queue-only smoke passed both isolated aliases as uid 5 with su=False, verifying one native marked message, serial replay, rollback, and no external-delivery claim.；引用：tests/integration/test_accounting_delivery_batch_live.py
- `golden`：`planned`；Golden queued-delivery examples are pending.；引用：无
- `e2e`：`planned`；Natural-language routing evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-invoice-send-inspect"></a>

## invoice.send.inspect — 检查客户发票、贷项通知单或收据发送准备状态

- 类型：只读；静态状态：`unconfigured`；handler：`invoice_send_inspect`。
- 状态原因：`runtime_context_required` — The fixed inspection handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`invoices_and_bills`；来源模型：res.company, account.move, res.partner, mail.template, ir.actions.report, mail.message；向导：account.move.send.wizard。
- 必需模块：account, mail；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_invoice；ACL：res.company:read, account.move:read, res.partner:read, mail.template:read, ir.actions.report:read, mail.message:read, account.move.send.wizard:read, account.move.send.wizard:create, account.move.send.wizard:write。
- 请求/响应合同：`schemas/v1/invoice.send.inspect.request.schema.json` / `schemas/v1/invoice.send.inspect.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read invoice.send.inspect --request "@request.json"
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
| parameters | object | 必填 |  |  | {"additionalProperties":false,"oneOf":[{"required":["move_id"]},{"required":["move_ids"]}]} |
| parameters.move_id | integer | 可选（可能有条件限制） |  | 会计单据记录ID | {"minimum":1} |
| parameters.move_ids | array | 可选（可能有条件限制） |  | 会计单据ID数组 | {"maxItems":100,"minItems":2,"uniqueItems":true} |
| parameters.move_ids[] | integer | 每个数组元素 |  | 会计单据ID数组 | {"minimum":1} |
| parameters | 未限定 | 分支约束 | oneOf[1] |  | {"required_in_object":["move_id"]} |
| parameters | 未限定 | 分支约束 | oneOf[2] |  | {"required_in_object":["move_ids"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"invoice.send.inspect"} |
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
- `execute`：fixed_native_account_move_send_wizard_inspection
- `verify`：rollback_only_recipient_template_report_method_and_warning_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover the closed singular-or-batch request, normalized inspection result, registry metadata, and schemas.；引用：tests/unit/test_accounting_delivery.py, tests/unit/test_accounting_delivery_registry.py
- `integration`：`implemented`；The guarded shared smoke passed both isolated aliases as uid 5 with su=False, using a rollback-only example.invalid fixture to verify native invoice-delivery readiness.；引用：tests/integration/test_accounting_delivery_batch_live.py
- `golden`：`planned`；Golden inspection examples are pending.；引用：无
- `e2e`：`planned`；Natural-language routing evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal-invoice_reference-update"></a>

## journal.invoice_reference.update — 设置发票付款参考格式

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Native advanced journal fields and available invoice-report IDs, not a duplicate of existing basic/liquidity configuration reads. Fixed edits retain company/user/ACLs. Native copy first chooses its name/code, then the copy alone is renamed inside the same savepoint; default accounts, bank references, payment-method lines and aliases retain native copy semantics, not forced source-child sharing. Stable copied configuration is compared; serial code/profile replay is not concurrent exactly-once or copy-provenance proof. Template assignment is limited to native available customer-invoice templates on sale journals; null clears. Account assignment requires an active account containing the current company; null clears. Native unlink may remove method lines, aliases and an exclusively linked bank account, and native journal-entry references still block deletion. Group deletion removes the group, not its journals. No historical sequence repair, posted-entry rewrite, native hashing toggle, arbitrary fields, caller-sudo, external payment or new control framework. Standalone mail-alias creation/deletion and bank-account unlink are not global prerequisites for a journal operation; native parent and applicable child ACLs remain authoritative. An exclusively linked bank account still requires its actual native unlink rights: a denial rolls back journal/method-line removal, and detaching the bank reference does not delete the bank account.
- 内部domain：`accounting_configuration`；来源模型：account.journal, res.company；向导：无。
- 必需模块：account, base, mail；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.journal:read, account.journal:write, res.company:read。
- 请求/响应合同：`schemas/v1/journal.invoice_reference.update.request.schema.json` / `schemas/v1/journal.invoice_reference.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run journal.invoice_reference.update --request "@request.json" --idempotency-key "journal.invoice_reference.update:1:accc886236f82bb302d70d01f00c0c91" --confirm "journal.invoice_reference.update"
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
      "invoice_reference_type": "invoice"
    },
    "journal_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["changes","journal_id"]} |
| parameters.journal_id | integer | 必填（所在对象出现时） |  | 日记账ID | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1,"required_in_object":[]} |
| parameters.changes.invoice_reference_type | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["invoice","partner"]} |
| parameters.changes.invoice_reference_model | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["euro","number","odoo"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"journal.invoice_reference.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"journal.invoice_reference.update"} |
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
- `execute`：fixed_native_journal_copy_unlink_or_settings_write
- `verify`：native_identity_and_requested_configuration_reread_in_one_savepoint
- `idempotency`：serial_journal_code_profile_or_current_requested_fields_with_missing_delete_denial
- `reverse`：previous_configuration_or_backup_subject_to_native_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Closed public CLI/schemas, deterministic keys, native copy rename and state replay, result/company binding, fixed field/reference/access denials and savepoint rollback.；引用：tests/unit/test_journal_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5/su=False/company 1: eight new IDs, six setup IDs and twelve immediate replays per alias. Actual general/sale/bank native copies retain fifteen stable fields, rename only the real copy after native copy_data, preserve sources, use independent identities, honor serial conflict/replay and recreate deleted targets with fresh archived identities. Native copy=False default/bank references are not forced to share; bank copies have fresh native default accounts/method lines and no source bank link. Real native sequence/reference/private-share-account and available customer-invoice-template settings persist and nullable references clear. Foreign/global-group/inapplicable/missing/deleted targets are denied. Native account_move_journal_id_fkey ForeignKeyViolation is verified directly for both draft and posted journal deletion denials, retaining the existing public odoo_write_error/exit-6 mapping. Posted IDs/accounts/journals/maturities/amounts/residuals/tax links remain unchanged. Native group deletion preserves journals. With no standalone bank unlink privilege, linked-bank journal deletion is denied by native ACL and restores journal/method lines/reference in its savepoint; publicly detaching the reference permits journal/method-line unlink while preserving the detached bank record. No added standalone alias/bank prerequisites or broader roles/caller-sudo. Fresh-cursor synthetic business data and temporary manager-group rollback verified; no business DB, addon/source, service or external payment changes.；引用：tests/integration/test_journal_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal-invoice_template-assign"></a>

## journal.invoice_template.assign — 设置可用客户发票模板

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Native advanced journal fields and available invoice-report IDs, not a duplicate of existing basic/liquidity configuration reads. Fixed edits retain company/user/ACLs. Native copy first chooses its name/code, then the copy alone is renamed inside the same savepoint; default accounts, bank references, payment-method lines and aliases retain native copy semantics, not forced source-child sharing. Stable copied configuration is compared; serial code/profile replay is not concurrent exactly-once or copy-provenance proof. Template assignment is limited to native available customer-invoice templates on sale journals; null clears. Account assignment requires an active account containing the current company; null clears. Native unlink may remove method lines, aliases and an exclusively linked bank account, and native journal-entry references still block deletion. Group deletion removes the group, not its journals. No historical sequence repair, posted-entry rewrite, native hashing toggle, arbitrary fields, caller-sudo, external payment or new control framework. Standalone mail-alias creation/deletion and bank-account unlink are not global prerequisites for a journal operation; native parent and applicable child ACLs remain authoritative. An exclusively linked bank account still requires its actual native unlink rights: a denial rolls back journal/method-line removal, and detaching the bank reference does not delete the bank account.
- 内部domain：`accounting_configuration`；来源模型：account.journal, ir.actions.report, res.company；向导：无。
- 必需模块：account, base, mail；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.journal:read, account.journal:write, ir.actions.report:read, res.company:read。
- 请求/响应合同：`schemas/v1/journal.invoice_template.assign.request.schema.json` / `schemas/v1/journal.invoice_template.assign.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run journal.invoice_template.assign --request "@request.json" --idempotency-key "journal.invoice_template.assign:1:b7fc2033906d95e83f3418101f48a907" --confirm "journal.invoice_template.assign"
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
    "report_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["journal_id","report_id"]} |
| parameters.journal_id | integer | 必填（所在对象出现时） |  | 日记账ID | {"minimum":1} |
| parameters.report_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"journal.invoice_template.assign"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"journal.invoice_template.assign"} |
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
- `execute`：fixed_native_journal_copy_unlink_or_settings_write
- `verify`：native_identity_and_requested_configuration_reread_in_one_savepoint
- `idempotency`：serial_journal_code_profile_or_current_requested_fields_with_missing_delete_denial
- `reverse`：previous_configuration_or_backup_subject_to_native_acl

### 已登记测试与证据范围

- `unit`：`implemented`；Closed public CLI/schemas, deterministic keys, native copy rename and state replay, result/company binding, fixed field/reference/access denials and savepoint rollback.；引用：tests/unit/test_journal_processing_batch.py
- `integration`：`implemented`；One shared rollback-only public CLI/real-ORM workflow passed both isolated aliases as uid 5/su=False/company 1: eight new IDs, six setup IDs and twelve immediate replays per alias. Actual general/sale/bank native copies retain fifteen stable fields, rename only the real copy after native copy_data, preserve sources, use independent identities, honor serial conflict/replay and recreate deleted targets with fresh archived identities. Native copy=False default/bank references are not forced to share; bank copies have fresh native default accounts/method lines and no source bank link. Real native sequence/reference/private-share-account and available customer-invoice-template settings persist and nullable references clear. Foreign/global-group/inapplicable/missing/deleted targets are denied. Native account_move_journal_id_fkey ForeignKeyViolation is verified directly for both draft and posted journal deletion denials, retaining the existing public odoo_write_error/exit-6 mapping. Posted IDs/accounts/journals/maturities/amounts/residuals/tax links remain unchanged. Native group deletion preserves journals. With no standalone bank unlink privilege, linked-bank journal deletion is denied by native ACL and restores journal/method lines/reference in its savepoint; publicly detaching the reference permits journal/method-line unlink while preserving the detached bank record. No added standalone alias/bank prerequisites or broader roles/caller-sudo. Fresh-cursor synthetic business data and temporary manager-group rollback verified; no business DB, addon/source, service or external payment changes.；引用：tests/integration/test_journal_processing_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-sale-order-down_payment-create"></a>

## sale.order.down_payment.create — 由销售订单创建预付款发票

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`odoo_move_marker_not_concurrency_unique` — Installed native percentage/fixed down-payment wizard executes as the ordinary configured user; native internal invoice creation semantics are preserved. Native move operation/key markers support sequential replay but are not database-unique for concurrent exactly-once creation.
- 内部domain：`sales_accounting`；来源模型：account.move, account.move.line, account.tax, res.company, sale.advance.payment.inv, sale.order, sale.order.line；向导：sale.advance.payment.inv。
- 必需模块：account, base, sale, sale_stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：sales_team.group_sale_salesman；ACL：account.move.line:read, account.move:create, account.move:read, account.move:write, account.tax:read, res.company:read, sale.advance.payment.inv:create, sale.order.line:create, sale.order.line:read, sale.order.line:write, sale.order:read, sale.order:write。
- 请求/响应合同：`schemas/v1/sale.order.down_payment.create.request.schema.json` / `schemas/v1/sale.order.down_payment.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run sale.order.down_payment.create --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "sale.order.down_payment.create"
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
    "method": "percentage",
    "amount": "1"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  |  |
| parameters | object | 必填 |  |  | {"additionalProperties":false,"if":{"properties":{"method":{"const":"percentage"}},"required":["method"]},"required_in_object":["order_id","method","amount"],"then":{"properties":{"amount":{"pattern":"^(?:100&#124;[1-9][0-9]?(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])"}}}} |
| parameters.order_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.method | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["percentage","fixed"]} |
| parameters.amount | string | 必填（所在对象出现时） |  | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])","resolved_ref":"receivable.payment.register.request.schema.json#/$defs/positive_canonical_decimal"} |
| parameters | 未限定 | 条件分支 | then |  |  |
| parameters.amount | 未限定 | 可选（可能有条件限制） | then | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"pattern":"^(?:100&#124;[1-9][0-9]?(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"sale.order.down_payment.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/down_payment"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/down_payment"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"sale.order.down_payment.create"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/down_payment"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | 组合/开放结构 | 分支约束 | allOf[2]/oneOf[2] |  | {"allOf":[{"$ref":"core-write-result.schema.json"},{"properties":{"result":{"properties":{"id":{"minimum":1,"type":"integer"},"model":{"const":"account.move"},"move_type":{"const":"out_invoice"},"source_id":{"minimum":1,"type":"integer"}}}}}],"resolved_ref":"#/$defs/down_payment"} |
| response.data | object | 分支约束 | allOf[2]/oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2]/allOf[1] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[2]/oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/allOf[1] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2]/allOf[1] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2]/allOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/allOf[1] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2]/allOf[1] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2]/allOf[1] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2]/allOf[1] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2]/allOf[1] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2]/allOf[1] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2]/allOf[1] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2]/allOf[1] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2]/allOf[1] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2]/allOf[1] |  |  |
| response.data | 未限定 | 分支约束 | allOf[2]/oneOf[2]/allOf[2] |  |  |
| response.data.result | 未限定 | 可选（可能有条件限制） | allOf[2]/oneOf[2]/allOf[2] |  |  |
| response.data.result.model | 未限定 | 可选（可能有条件限制） | allOf[2]/oneOf[2]/allOf[2] |  | {"const":"account.move"} |
| response.data.result.id | integer | 可选（可能有条件限制） | allOf[2]/oneOf[2]/allOf[2] |  | {"minimum":1} |
| response.data.result.move_type | 未限定 | 可选（可能有条件限制） | allOf[2]/oneOf[2]/allOf[2] |  | {"const":"out_invoice"} |
| response.data.result.source_id | integer | 可选（可能有条件限制） | allOf[2]/oneOf[2]/allOf[2] |  | {"minimum":1} |
| response | 组合/开放结构 | 分支约束 | allOf[3] |  | {"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/down_payment"},"error":{"type":"null"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[3]/then |  |  |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[3]/then |  | {"const":"verified"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[3]/then |  | {"allOf":[{"$ref":"core-write-result.schema.json"},{"properties":{"result":{"properties":{"id":{"minimum":1,"type":"integer"},"model":{"const":"account.move"},"move_type":{"const":"out_invoice"},"source_id":{"minimum":1,"type":"integer"}}}}}],"resolved_ref":"#/$defs/down_payment"} |
| response.data | object | 分支约束 | allOf[3]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["idempotent_replay","result"],"resolved_ref":"core-write-result.schema.json"} |
| response.data.idempotent_replay | boolean | 必填（所在对象出现时） | allOf[3]/then/allOf[1] | 按本能力规则识别的当前重复，不是全局exactly-once承诺 |  |
| response.data.result | object | 必填（所在对象出现时） | allOf[3]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","id","name","state","company_id","move_type","source_id","line_ids","partial_reconcile_ids","full_reconcile_id","reconciled"]} |
| response.data.result.model | string | 必填（所在对象出现时） | allOf[3]/then/allOf[1] |  | {"minLength":1,"pattern":"\\S"} |
| response.data.result.id | integer/null | 必填（所在对象出现时） | allOf[3]/then/allOf[1] |  | {"minimum":1} |
| response.data.result.name | string/null | 必填（所在对象出现时） | allOf[3]/then/allOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.result.state | string | 必填（所在对象出现时） | allOf[3]/then/allOf[1] | 状态 | {"minLength":1,"pattern":"\\S"} |
| response.data.result.company_id | integer | 必填（所在对象出现时） | allOf[3]/then/allOf[1] | 所选公司ID | {"minimum":1} |
| response.data.result.move_type | string/null | 必填（所在对象出现时） | allOf[3]/then/allOf[1] |  | {"minLength":1} |
| response.data.result.source_id | integer/null | 必填（所在对象出现时） | allOf[3]/then/allOf[1] |  | {"minimum":1} |
| response.data.result.line_ids | array | 必填（所在对象出现时） | allOf[3]/then/allOf[1] | 行记录ID数组 | {"uniqueItems":true} |
| response.data.result.line_ids[] | integer | 每个数组元素 | allOf[3]/then/allOf[1] | 行记录ID数组 | {"minimum":1} |
| response.data.result.partial_reconcile_ids | array | 必填（所在对象出现时） | allOf[3]/then/allOf[1] |  | {"uniqueItems":true} |
| response.data.result.partial_reconcile_ids[] | integer | 每个数组元素 | allOf[3]/then/allOf[1] |  | {"minimum":1} |
| response.data.result.full_reconcile_id | integer/null | 必填（所在对象出现时） | allOf[3]/then/allOf[1] | 完整核销关系ID | {"minimum":1} |
| response.data.result.reconciled | boolean | 必填（所在对象出现时） | allOf[3]/then/allOf[1] |  |  |
| response.data | 未限定 | 分支约束 | allOf[3]/then/allOf[2] |  |  |
| response.data.result | 未限定 | 可选（可能有条件限制） | allOf[3]/then/allOf[2] |  |  |
| response.data.result.model | 未限定 | 可选（可能有条件限制） | allOf[3]/then/allOf[2] |  | {"const":"account.move"} |
| response.data.result.id | integer | 可选（可能有条件限制） | allOf[3]/then/allOf[2] |  | {"minimum":1} |
| response.data.result.move_type | 未限定 | 可选（可能有条件限制） | allOf[3]/then/allOf[2] |  | {"const":"out_invoice"} |
| response.data.result.source_id | integer | 可选（可能有条件限制） | allOf[3]/then/allOf[2] |  | {"minimum":1} |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_native_sale_advance_payment_inv_create_invoices_as_configured_business_user
- `verify`：native_downpayment_amount_tax_line_and_sale_source_graph_reread
- `idempotency`：native_move_operation_and_key_markers_without_concurrent_exactly_once_guarantee
- `reverse`：invoice.cancel_or_customer_credit_note

### 已登记测试与证据范围

- `unit`：`implemented`；Focused native wizard, percentage/fixed amount, graph, replay, company/ACL, schema and CLI contracts.；引用：tests/unit/test_invoice_rounds_write_contract.py, tests/unit/test_invoice_rounds_runtime.py, tests/unit/test_invoice_rounds_product_reads.py, tests/unit/test_invoice_rounds_cli.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；Shared native invoice rounds smoke passed; full rollback.；引用：tests/integration/test_invoice_rounds_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-sale-order-invoice-create"></a>

## sale.order.invoice.create — 由销售订单创建客户发票

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`odoo_linked_invoice_not_concurrency_unique` — The native handler rechecks linked customer invoices for ordinary replay, but Odoo provides no database-unique operation key for concurrent exactly-once creation. The order_ids route creates later native invoiceable rounds with ordinary-user native marker write access and actual native grouping/quantities; legacy order_id replay is retained. Operation markers are not concurrency-unique.
- 内部domain：`sales_accounting`；来源模型：account.move, account.move.line, res.company, sale.order, sale.order.line；向导：无。
- 必需模块：account, base, sale, sale_stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：sales_team.group_sale_salesman；ACL：res.company:read, sale.order:read, sale.order:write, sale.order.line:read, account.move:read, account.move:create, account.move.line:read。
- 请求/响应合同：`schemas/v1/sale.order.invoice.create.request.schema.json` / `schemas/v1/sale.order.invoice.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run sale.order.invoice.create --request "@request.json" --idempotency-key "sale.order.invoice.create:1" --confirm "sale.order.invoice.create"
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
| parameters | object | 必填 |  |  | {"additionalProperties":false,"oneOf":[{"properties":{"consolidated_billing":false,"deduct_down_payments":false,"order_ids":false},"required":["order_id"]},{"properties":{"order_id":false},"required":["order_ids"]}]} |
| parameters.order_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.order_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":100,"minItems":1,"uniqueItems":true} |
| parameters.order_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.consolidated_billing | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.deduct_down_payments | boolean | 可选（可能有条件限制） |  |  |  |
| parameters | 未限定 | 分支约束 | oneOf[1] |  | {"required_in_object":["order_id"]} |
| parameters.order_ids | 禁止 | 可选（可能有条件限制） | oneOf[1] |  | false |
| parameters.consolidated_billing | 禁止 | 可选（可能有条件限制） | oneOf[1] |  | false |
| parameters.deduct_down_payments | 禁止 | 可选（可能有条件限制） | oneOf[1] |  | false |
| parameters | 未限定 | 分支约束 | oneOf[2] |  | {"required_in_object":["order_ids"]} |
| parameters.order_id | 禁止 | 可选（可能有条件限制） | oneOf[2] |  | false |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"sale.order.invoice.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"},{"$ref":"#/$defs/order_invoice_batch"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"oneOf":[{"$ref":"core-write-result.schema.json"},{"$ref":"#/$defs/order_invoice_batch"}]},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"sale.order.invoice.create"} |
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
| response.data.result.items[] | 组合/开放结构 | 每个数组元素 | allOf[2]/oneOf[3] |  | {"allOf":[{"$ref":"core-write-result.schema.json#/properties/result"},{"properties":{"id":{"minimum":1,"type":"integer"},"model":{"const":"account.move"},"move_type":{"enum":["out_invoice","out_refund"]}}}]} |
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
| response.data.result.items[].move_type | 未限定 | 可选（可能有条件限制） | allOf[2]/oneOf[3]/allOf[2] |  | {"enum":["out_invoice","out_refund"]} |
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
| response.data.result.items[] | 组合/开放结构 | 每个数组元素 | allOf[3]/then/oneOf[2] |  | {"allOf":[{"$ref":"core-write-result.schema.json#/properties/result"},{"properties":{"id":{"minimum":1,"type":"integer"},"model":{"const":"account.move"},"move_type":{"enum":["out_invoice","out_refund"]}}}]} |
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
| response.data.result.items[].move_type | 未限定 | 可选（可能有条件限制） | allOf[3]/then/oneOf[2]/allOf[2] |  | {"enum":["out_invoice","out_refund"]} |
| response.data.result.processed_count | integer | 必填（所在对象出现时） | allOf[3]/then/oneOf[2] |  | {"maximum":1000,"minimum":1} |
| response.error | null | 可选（可能有条件限制） | allOf[3]/then |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：exact_capability_confirmation_and_closed_request_validation
- `execute`：fixed_native_sale_order_create_invoices_as_configured_business_user
- `verify`：same_transaction_sale_linked_draft_customer_invoice_reread_and_response_schema_validation
- `idempotency`：linked_customer_invoice_recheck_without_concurrent_exactly_once_guarantee
- `reverse`：invoice.cancel_or_customer_credit_note

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed order contract, native invoice creation path, company and ACL gates, replay, schemas, and CLI dispatch.；引用：tests/unit/test_stock_transfer_writes.py, tests/unit/test_stock_transfer_write_schemas.py, tests/unit/test_stock_transfer_writes_runtime.py, tests/unit/test_stock_transfer_write_cli.py, tests/unit/test_invoice_rounds_write_contract.py, tests/unit/test_invoice_rounds_runtime.py, tests/unit/test_invoice_rounds_product_reads.py, tests/unit/test_invoice_rounds_cli.py
- `integration`：`implemented`；The guarded shared transactional smoke verifies native sales-order invoicing, replay, and rollback in both isolated databases.；引用：tests/integration/test_stock_transfer_write_batch_live.py, tests/integration/test_invoice_rounds_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。
