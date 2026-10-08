# 库存估值、销售成本与库存会计衔接

查询库存关联会计分录、销售成本分录和销售发票到库存会计的关联，读取库存估值报告，并辨识库存估值调整的预留接口。该场景关注会计金额和来源衔接，不执行出入库、拣货、预留或实物退货；估值调整纳入索引不代表当前可用。

[回到总说明书](../../CLI_V4_MANUAL.md) · [新会话使用指南](../USAGE_GUIDE.md)

<a id="cap-cogs-entries-list"></a>

## cogs.entries.list — 列出销售成本会计分录

- 类型：只读；静态状态：`unconfigured`；handler：`cogs_entries_list`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`inventory_accounting`；来源模型：stock.move, account.move, account.move.line, sale.order.line；向导：无。
- 必需模块：stock_account, sale_stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：stock.move:read, account.move:read, account.move.line:read, sale.order.line:read。
- 请求/响应合同：`schemas/v1/cogs.entries.list.request.schema.json` / `schemas/v1/cogs.entries.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read cogs.entries.list --request "@request.json"
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
| parameters | object | 必填 |  |  |  |
| parameters | object | 必填 |  |  | {"additionalProperties":false} |
| parameters.date_from | string/null | 可选（可能有条件限制） |  | 开始日期 | {"default":null,"format":"date"} |
| parameters.date_to | string/null | 可选（可能有条件限制） |  | 结束日期 | {"default":null,"format":"date"} |
| parameters.invoice_id | integer/null | 可选（可能有条件限制） |  | 发票/账单记录ID（具体类型按能力定义） | {"default":null,"minimum":1} |
| parameters.product_id | integer/null | 可选（可能有条件限制） |  |  | {"default":null,"minimum":1} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"properties":{"capability":{"const":"cogs.entries.list"},"data":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"cogs.entries.list"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","date","company_id","invoice","origin_invoice_line_id","account","product","label","quantity","debit","credit","balance","company_currency","sale_order_line_ids","stock_move_ids"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].invoice | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state"],"resolved_ref":"#/$defs/invoice"} |
| response.data.items[].invoice.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].invoice.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].invoice.name | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].invoice.name | string | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].invoice.move_type | 未限定 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"enum":["out_invoice","out_refund"]} |
| response.data.items[].invoice.state | 未限定 | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"const":"posted"} |
| response.data.items[].origin_invoice_line_id | integer/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].account | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.items[].account.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].account.code | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.items[].account.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].product | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/namedRef"}]} |
| response.data.items[].product | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.items[].product | object | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/namedRef"} |
| response.data.items[].product.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].product.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].label | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].label | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.items[].label | string | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.items[].quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].debit | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 借方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].credit | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 贷方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].balance | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].company_currency | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].company_currency.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_currency.code | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].sale_order_line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.items[].sale_order_line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].stock_move_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.items[].stock_move_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | allOf[2]/oneOf[2]/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | allOf[2]/oneOf[2]/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | allOf[2]/oneOf[2]/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | allOf[2]/oneOf[2]/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | allOf[2]/oneOf[2]/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | allOf[2]/oneOf[2]/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
| response | 组合/开放结构 | 分支约束 | allOf[2]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[2]/allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[2]/allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[2]/allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","date","company_id","invoice","origin_invoice_line_id","account","product","label","quantity","debit","credit","balance","company_currency","sale_order_line_ids","stock_move_ids"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"format":"date"} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].invoice | object | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state"],"resolved_ref":"#/$defs/invoice"} |
| response.data.items[].invoice.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.items[].invoice.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].invoice.name | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[1] | 名称/行说明 |  |
| response.data.items[].invoice.name | string | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].invoice.move_type | 未限定 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"enum":["out_invoice","out_refund"]} |
| response.data.items[].invoice.state | 未限定 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 状态 | {"const":"posted"} |
| response.data.items[].origin_invoice_line_id | integer/null | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.items[].account | object | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.items[].account.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.items[].account.code | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minLength":1} |
| response.data.items[].account.name | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].product | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/namedRef"}]} |
| response.data.items[].product | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].product | object | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/namedRef"} |
| response.data.items[].product.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].product.name | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].label | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].label | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].label | string | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.items[].quantity | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].debit | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 借方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].credit | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 贷方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].balance | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].company_currency | object | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].company_currency.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_currency.code | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].sale_order_line_ids | array | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"uniqueItems":true} |
| response.data.items[].sale_order_line_ids[] | integer | 每个数组元素 | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.items[].stock_move_ids | array | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"uniqueItems":true} |
| response.data.items[].stock_move_ids[] | integer | 每个数组元素 | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | allOf[2]/allOf[1]/then/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | allOf[2]/allOf[1]/then/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | allOf[2]/allOf[1]/then/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | allOf[2]/allOf[1]/then/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | allOf[2]/allOf[1]/then/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | allOf[2]/allOf[1]/then/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
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

<a id="cap-inventory-accounting_entries-list"></a>

## inventory.accounting_entries.list — 列出库存关联会计分录

- 类型：只读；静态状态：`unconfigured`；handler：`inventory_accounting_entries_list`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`inventory_accounting`；来源模型：stock.move, account.move, account.move.line；向导：无。
- 必需模块：stock_account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：stock.move:read, account.move:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/inventory.accounting_entries.list.request.schema.json` / `schemas/v1/inventory.accounting_entries.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read inventory.accounting_entries.list --request "@request.json"
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
| parameters | object | 必填 |  |  |  |
| parameters | object | 必填 |  |  | {"additionalProperties":false} |
| parameters.date_from | string/null | 可选（可能有条件限制） |  | 开始日期 | {"default":null,"format":"date"} |
| parameters.date_to | string/null | 可选（可能有条件限制） |  | 结束日期 | {"default":null,"format":"date"} |
| parameters.product_id | integer/null | 可选（可能有条件限制） |  |  | {"default":null,"minimum":1} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"properties":{"capability":{"const":"inventory.accounting_entries.list"},"data":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"inventory.accounting_entries.list"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","date","company_id","reference","state","product","quantity","uom","value","is_in","is_out","account_move","lines","company_currency"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].reference | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].reference | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.items[].reference | string | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"const":"done"} |
| response.data.items[].product | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/namedRef"} |
| response.data.items[].product.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].product.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].uom | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/namedRef"} |
| response.data.items[].uom.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].uom.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].value | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].is_in | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response.data.items[].is_out | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response.data.items[].account_move | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","date","state","journal"],"resolved_ref":"#/$defs/accountMove"} |
| response.data.items[].account_move.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].account_move.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].account_move.name | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.items[].account_move.name | string | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].account_move.date | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.items[].account_move.state | 未限定 | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"const":"posted"} |
| response.data.items[].account_move.journal | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/journal"} |
| response.data.items[].account_move.journal.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].account_move.journal.code | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":5,"minLength":1} |
| response.data.items[].account_move.journal.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].lines | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"minItems":1} |
| response.data.items[].lines[] | object | 每个数组元素 | allOf[2]/oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","account","debit","credit","balance"],"resolved_ref":"#/$defs/accountingLine"} |
| response.data.items[].lines[].id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].lines[].account | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.items[].lines[].account.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].lines[].account.code | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.items[].lines[].account.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].lines[].debit | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 借方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegativeDecimal"} |
| response.data.items[].lines[].credit | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 贷方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegativeDecimal"} |
| response.data.items[].lines[].balance | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].company_currency | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].company_currency.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_currency.code | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | allOf[2]/oneOf[2]/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | allOf[2]/oneOf[2]/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | allOf[2]/oneOf[2]/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | allOf[2]/oneOf[2]/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | allOf[2]/oneOf[2]/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | allOf[2]/oneOf[2]/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
| response | 组合/开放结构 | 分支约束 | allOf[2]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[2]/allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[2]/allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[2]/allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","date","company_id","reference","state","product","quantity","uom","value","is_in","is_out","account_move","lines","company_currency"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].reference | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].reference | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].reference | string | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 状态 | {"const":"done"} |
| response.data.items[].product | object | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/namedRef"} |
| response.data.items[].product.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.items[].product.name | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].quantity | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].uom | object | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/namedRef"} |
| response.data.items[].uom.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.items[].uom.name | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].value | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].is_in | boolean | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  |  |
| response.data.items[].is_out | boolean | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  |  |
| response.data.items[].account_move | object | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","date","state","journal"],"resolved_ref":"#/$defs/accountMove"} |
| response.data.items[].account_move.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.items[].account_move.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.items[].account_move.name | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[1] | 名称/行说明 |  |
| response.data.items[].account_move.name | string | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].account_move.date | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"format":"date"} |
| response.data.items[].account_move.state | 未限定 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 状态 | {"const":"posted"} |
| response.data.items[].account_move.journal | object | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/journal"} |
| response.data.items[].account_move.journal.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.items[].account_move.journal.code | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"maxLength":5,"minLength":1} |
| response.data.items[].account_move.journal.name | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].lines | array | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"minItems":1} |
| response.data.items[].lines[] | object | 每个数组元素 | allOf[2]/allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","account","debit","credit","balance"],"resolved_ref":"#/$defs/accountingLine"} |
| response.data.items[].lines[].id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.items[].lines[].account | object | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.items[].lines[].account.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.items[].lines[].account.code | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minLength":1} |
| response.data.items[].lines[].account.name | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].lines[].debit | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 借方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegativeDecimal"} |
| response.data.items[].lines[].credit | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 贷方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegativeDecimal"} |
| response.data.items[].lines[].balance | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].company_currency | object | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].company_currency.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_currency.code | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.has_more | boolean | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 是否仍有后续页 |  |
| response.data.next_cursor | string/null | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 下一页不透明游标，无后续时可为空 | {"maxLength":4096,"minLength":1} |
| response.data | 组合/开放结构 | 分支约束 | allOf[2]/allOf[1]/then/allOf[1] |  | {"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}} |
| response.data | 未限定 | 条件分支 | allOf[2]/allOf[1]/then/allOf[1]/then |  |  |
| response.data.items | array | 可选（可能有条件限制） | allOf[2]/allOf[1]/then/allOf[1]/then |  | {"minItems":1} |
| response.data.next_cursor | string | 可选（可能有条件限制） | allOf[2]/allOf[1]/then/allOf[1]/then | 下一页不透明游标，无后续时可为空 |  |
| response.data | 未限定 | 条件分支 | allOf[2]/allOf[1]/then/allOf[1]/else |  |  |
| response.data.next_cursor | null | 可选（可能有条件限制） | allOf[2]/allOf[1]/then/allOf[1]/else | 下一页不透明游标，无后续时可为空 |  |
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

<a id="cap-inventory-valuation-adjust"></a>

## inventory.valuation.adjust — 调整库存会计估值

- 类型：写入；静态状态：`disabled`；handler：`None`。
- 状态原因：`implementation_pending` — The capability is frozen in the G3 matrix but has no implementation or allowlisted handler.
- 内部domain：`inventory_accounting`；来源模型：product.value, stock.move, account.move；向导：无。
- 必需模块：stock_account；配置项：database_alias, company_allowlist, user_mapping, write_approval_policy, audit_store；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：product.value:create, product.value:read, stock.move:read, account.move:read。
- 请求/响应合同：`schemas/v1/request.schema.json` / `schemas/v1/response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run inventory.valuation.adjust --request "@request.json" --idempotency-key "RECOMPUTE_FOR_ACTUAL_REQUEST" --confirm "inventory.valuation.adjust"
```

> 禁用/预留ID，不能调用。若展示请求结构，仅说明占位合同，不表示实现已存在。

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
| parameters | object | 必填 |  |  |  |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | object/null | 必填（所在对象出现时） |  |  |  |
| response.warnings | array | 必填（所在对象出现时） |  |  |  |
| response.warnings[] | object | 每个数组元素 |  |  |  |
| response.error | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/error"}]} |
| response.error | null | 分支约束 | oneOf[1] |  |  |
| response.error | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.odoo | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["database","company_id","user_id","model","record_ids"],"resolved_ref":"#/$defs/odoo"} |
| response.odoo.database | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.company_id | integer/null | 必填（所在对象出现时） |  | 所选公司ID | {"minimum":1} |
| response.odoo.user_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |
| response.odoo.model | string/null | 必填（所在对象出现时） |  |  |  |
| response.odoo.record_ids | array | 必填（所在对象出现时） |  |  | {"uniqueItems":true} |
| response.odoo.record_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| response.audit | object | 必填（所在对象出现时） |  |  | {"additionalProperties":false,"required_in_object":["operation_id","idempotency_key","verification"],"resolved_ref":"#/$defs/audit"} |
| response.audit.operation_id | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.idempotency_key | string/null | 必填（所在对象出现时） |  |  |  |
| response.audit.verification | object/null | 必填（所在对象出现时） |  |  |  |
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response.error | null | 可选（可能有条件限制） | allOf[1]/then |  |  |
| response | 未限定 | 条件分支 | allOf[1]/else |  |  |
| response.data | null | 可选（可能有条件限制） | allOf[1]/else |  |  |
| response.error | object | 可选（可能有条件限制） | allOf[1]/else |  | {"additionalProperties":false,"required_in_object":["code","message","details","retryable"],"resolved_ref":"#/$defs/error"} |
| response.error.code | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.message | string | 必填（所在对象出现时） | allOf[1]/else |  | {"minLength":1} |
| response.error.details | object | 必填（所在对象出现时） | allOf[1]/else |  |  |
| response.error.retryable | boolean | 必填（所在对象出现时） | allOf[1]/else |  |  |

### 执行、验证、幂等与逆向边界

- `preview`：prepare_immutable_plan_before_approval
- `execute`：implementation_pending
- `verify`：post_commit_business_state_reread_pending
- `idempotency`：persistent_idempotency_key_required
- `reverse`：record_a_new_correcting_valuation_adjustment

### 已登记测试与证据范围

- `unit`：`planned`；The unit definition is frozen; implementation evidence is pending.；引用：无
- `integration`：`planned`；The integration definition is frozen; implementation evidence is pending.；引用：无
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-inventory_valuation"></a>

## report.inventory_valuation — 生成库存估值报告

- 类型：只读；静态状态：`unconfigured`；handler：`report_inventory_valuation`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`inventory_accounting`；来源模型：stock_account.stock.valuation.report, stock.move, account.move.line；向导：无。
- 必需模块：stock_account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：stock.move:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/report.inventory_valuation.request.schema.json` / `schemas/v1/report.inventory_valuation.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.inventory_valuation --request "@request.json"
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
| parameters | object | 必填 |  |  |  |
| parameters | object | 必填 |  |  | {"additionalProperties":false} |
| parameters.date | string/null | 可选（可能有条件限制） |  |  | {"default":null,"format":"date"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"properties":{"capability":{"const":"report.inventory_valuation"},"data":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"report.inventory_valuation"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["as_of_date","company","currency","initial_balance","ending_stock","stock_variation","inventory_loss","not_invoiced_delivered_goods","not_invoiced_received_goods","cost_of_production","accounts"],"resolved_ref":"#/$defs/data"} |
| response.data.as_of_date | string/null | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.company | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/namedRef"} |
| response.data.company.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.company.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.initial_balance | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.ending_stock | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.stock_variation | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.inventory_loss | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}],"resolved_ref":"#/$defs/nullableDecimal"} |
| response.data.inventory_loss | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.inventory_loss | string | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.not_invoiced_delivered_goods | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}],"resolved_ref":"#/$defs/nullableDecimal"} |
| response.data.not_invoiced_delivered_goods | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.not_invoiced_delivered_goods | string | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.not_invoiced_received_goods | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}],"resolved_ref":"#/$defs/nullableDecimal"} |
| response.data.not_invoiced_received_goods | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.not_invoiced_received_goods | string | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.cost_of_production | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}],"resolved_ref":"#/$defs/nullableDecimal"} |
| response.data.cost_of_production | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.cost_of_production | string | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.accounts | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response.data.accounts[] | object | 每个数组元素 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["account","initial_balance","ending_stock","variation_debit","variation_credit"],"resolved_ref":"#/$defs/accountItem"} |
| response.data.accounts[].account | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts[].account.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.accounts[].account.code | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.accounts[].account.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts[].initial_balance | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.accounts[].ending_stock | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.accounts[].variation_debit | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegativeDecimal"} |
| response.data.accounts[].variation_credit | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegativeDecimal"} |
| response | 组合/开放结构 | 分支约束 | allOf[2]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[2]/allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[2]/allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[2]/allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["as_of_date","company","currency","initial_balance","ending_stock","stock_variation","inventory_loss","not_invoiced_delivered_goods","not_invoiced_received_goods","cost_of_production","accounts"],"resolved_ref":"#/$defs/data"} |
| response.data.as_of_date | string/null | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"format":"date"} |
| response.data.company | object | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/namedRef"} |
| response.data.company.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.company.name | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.initial_balance | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.ending_stock | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.stock_variation | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.inventory_loss | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}],"resolved_ref":"#/$defs/nullableDecimal"} |
| response.data.inventory_loss | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[1] |  |  |
| response.data.inventory_loss | string | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.not_invoiced_delivered_goods | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}],"resolved_ref":"#/$defs/nullableDecimal"} |
| response.data.not_invoiced_delivered_goods | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[1] |  |  |
| response.data.not_invoiced_delivered_goods | string | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.not_invoiced_received_goods | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}],"resolved_ref":"#/$defs/nullableDecimal"} |
| response.data.not_invoiced_received_goods | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[1] |  |  |
| response.data.not_invoiced_received_goods | string | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.cost_of_production | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}],"resolved_ref":"#/$defs/nullableDecimal"} |
| response.data.cost_of_production | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[1] |  |  |
| response.data.cost_of_production | string | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.accounts | array | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  |  |
| response.data.accounts[] | object | 每个数组元素 | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["account","initial_balance","ending_stock","variation_debit","variation_credit"],"resolved_ref":"#/$defs/accountItem"} |
| response.data.accounts[].account | object | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts[].account.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.accounts[].account.code | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minLength":1} |
| response.data.accounts[].account.name | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.accounts[].initial_balance | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.accounts[].ending_stock | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.accounts[].variation_debit | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegativeDecimal"} |
| response.data.accounts[].variation_credit | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegativeDecimal"} |
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

<a id="cap-sale_invoice-stock_link-inspect"></a>

## sale_invoice.stock_link.inspect — 检查销售发票与库存会计衔接

- 类型：只读；静态状态：`unconfigured`；handler：`sale_invoice_stock_link_inspect`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`sales_accounting`；来源模型：sale.order.line, stock.move, account.move, account.move.line；向导：无。
- 必需模块：sale, sale_stock, stock_account, account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：sale.order.line:read, stock.move:read, account.move:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/sale_invoice.stock_link.inspect.request.schema.json` / `schemas/v1/sale_invoice.stock_link.inspect.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read sale_invoice.stock_link.inspect --request "@request.json"
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
| parameters | object | 必填 |  |  |  |
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["invoice_id"]} |
| parameters.invoice_id | integer | 必填（所在对象出现时） |  | 发票/账单记录ID（具体类型按能力定义） | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"properties":{"capability":{"const":"sale_invoice.stock_link.inspect"},"data":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"sale_invoice.stock_link.inspect"} |
| response.data | 组合/开放结构 | 可选（可能有条件限制） | allOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | allOf[2]/oneOf[1] |  |  |
| response.data | object | 分支约束 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","company_id","lines","stock_move_ids","account_move_ids"],"resolved_ref":"#/$defs/data"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.name | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.name | string | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"enum":["out_invoice","out_refund"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.lines | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 |  |
| response.data.lines[] | object | 每个数组元素 | allOf[2]/oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","product","quantity","sale_order_line_ids","stock_moves"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].product | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/namedRef"}]} |
| response.data.lines[].product | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].product | object | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/namedRef"} |
| response.data.lines[].product.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].product.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].sale_order_line_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.lines[].sale_order_line_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].stock_moves | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  |  |
| response.data.lines[].stock_moves[] | object | 每个数组元素 | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","date","state","reference","product","quantity","uom","value","accounting_entry"],"resolved_ref":"#/$defs/stockMove"} |
| response.data.lines[].stock_moves[].id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].stock_moves[].date | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"} |
| response.data.lines[].stock_moves[].state | 未限定 | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 状态 | {"const":"done"} |
| response.data.lines[].stock_moves[].reference | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.lines[].stock_moves[].reference | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].stock_moves[].reference | string | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.lines[].stock_moves[].product | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/namedRef"} |
| response.data.lines[].stock_moves[].product.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].stock_moves[].product.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].stock_moves[].quantity | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].stock_moves[].uom | object | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/namedRef"} |
| response.data.lines[].stock_moves[].uom.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].stock_moves[].uom.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].stock_moves[].value | string | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].stock_moves[].accounting_entry | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/accountingEntry"}]} |
| response.data.lines[].stock_moves[].accounting_entry | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].stock_moves[].accounting_entry | object | 分支约束 | allOf[2]/oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","date","state","lines"],"resolved_ref":"#/$defs/accountingEntry"} |
| response.data.lines[].stock_moves[].accounting_entry.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].stock_moves[].accounting_entry.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.lines[].stock_moves[].accounting_entry.name | null | 分支约束 | allOf[2]/oneOf[2]/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.lines[].stock_moves[].accounting_entry.name | string | 分支约束 | allOf[2]/oneOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].stock_moves[].accounting_entry.date | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"format":"date"} |
| response.data.lines[].stock_moves[].accounting_entry.state | 未限定 | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] | 状态 | {"const":"posted"} |
| response.data.lines[].stock_moves[].accounting_entry.lines | array | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"minItems":1} |
| response.data.lines[].stock_moves[].accounting_entry.lines[] | object | 每个数组元素 | allOf[2]/oneOf[2]/oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","account","debit","credit","balance"],"resolved_ref":"#/$defs/accountingLine"} |
| response.data.lines[].stock_moves[].accounting_entry.lines[].id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].stock_moves[].accounting_entry.lines[].account | object | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.lines[].stock_moves[].accounting_entry.lines[].account.id | integer | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].stock_moves[].accounting_entry.lines[].account.code | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.lines[].stock_moves[].accounting_entry.lines[].account.name | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].stock_moves[].accounting_entry.lines[].debit | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] | 借方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegativeDecimal"} |
| response.data.lines[].stock_moves[].accounting_entry.lines[].credit | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] | 贷方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegativeDecimal"} |
| response.data.lines[].stock_moves[].accounting_entry.lines[].balance | string | 必填（所在对象出现时） | allOf[2]/oneOf[2]/oneOf[2] | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.stock_move_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.stock_move_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.account_move_ids | array | 必填（所在对象出现时） | allOf[2]/oneOf[2] |  | {"uniqueItems":true} |
| response.data.account_move_ids[] | integer | 每个数组元素 | allOf[2]/oneOf[2] |  | {"minimum":1} |
| response | 组合/开放结构 | 分支约束 | allOf[2]/allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[2]/allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[2]/allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[2]/allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","move_type","state","company_id","lines","stock_move_ids","account_move_ids"],"resolved_ref":"#/$defs/data"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.name | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[1] | 名称/行说明 |  |
| response.data.name | string | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.move_type | 未限定 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"enum":["out_invoice","out_refund"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 状态 | {"enum":["draft","posted","cancel"]} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.lines | array | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 |  |
| response.data.lines[] | object | 每个数组元素 | allOf[2]/allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","product","quantity","sale_order_line_ids","stock_moves"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].product | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/namedRef"}]} |
| response.data.lines[].product | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].product | object | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/namedRef"} |
| response.data.lines[].product.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].product.name | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].quantity | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].sale_order_line_ids | array | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"uniqueItems":true} |
| response.data.lines[].sale_order_line_ids[] | integer | 每个数组元素 | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].stock_moves | array | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  |  |
| response.data.lines[].stock_moves[] | object | 每个数组元素 | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","date","state","reference","product","quantity","uom","value","accounting_entry"],"resolved_ref":"#/$defs/stockMove"} |
| response.data.lines[].stock_moves[].id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].stock_moves[].date | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"} |
| response.data.lines[].stock_moves[].state | 未限定 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 状态 | {"const":"done"} |
| response.data.lines[].stock_moves[].reference | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.lines[].stock_moves[].reference | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].stock_moves[].reference | string | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.lines[].stock_moves[].product | object | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/namedRef"} |
| response.data.lines[].stock_moves[].product.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].stock_moves[].product.name | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.lines[].stock_moves[].quantity | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 数量；单位、符号和精度依具体接口 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].stock_moves[].uom | object | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/namedRef"} |
| response.data.lines[].stock_moves[].uom.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.lines[].stock_moves[].uom.name | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.lines[].stock_moves[].value | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.lines[].stock_moves[].accounting_entry | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/accountingEntry"}]} |
| response.data.lines[].stock_moves[].accounting_entry | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].stock_moves[].accounting_entry | object | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","date","state","lines"],"resolved_ref":"#/$defs/accountingEntry"} |
| response.data.lines[].stock_moves[].accounting_entry.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].stock_moves[].accounting_entry.name | 组合/开放结构 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] | 名称/行说明 | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}],"resolved_ref":"#/$defs/nullableText"} |
| response.data.lines[].stock_moves[].accounting_entry.name | null | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2]/oneOf[1] | 名称/行说明 |  |
| response.data.lines[].stock_moves[].accounting_entry.name | string | 分支约束 | allOf[2]/allOf[1]/then/oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].stock_moves[].accounting_entry.date | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] |  | {"format":"date"} |
| response.data.lines[].stock_moves[].accounting_entry.state | 未限定 | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] | 状态 | {"const":"posted"} |
| response.data.lines[].stock_moves[].accounting_entry.lines | array | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"minItems":1} |
| response.data.lines[].stock_moves[].accounting_entry.lines[] | object | 每个数组元素 | allOf[2]/allOf[1]/then/oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","account","debit","credit","balance"],"resolved_ref":"#/$defs/accountingLine"} |
| response.data.lines[].stock_moves[].accounting_entry.lines[].id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].stock_moves[].accounting_entry.lines[].account | object | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.lines[].stock_moves[].accounting_entry.lines[].account.id | integer | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.lines[].stock_moves[].accounting_entry.lines[].account.code | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.lines[].stock_moves[].accounting_entry.lines[].account.name | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].stock_moves[].accounting_entry.lines[].debit | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] | 借方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegativeDecimal"} |
| response.data.lines[].stock_moves[].accounting_entry.lines[].credit | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] | 贷方值；不得丢弃原生storno符号 | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegativeDecimal"} |
| response.data.lines[].stock_moves[].accounting_entry.lines[].balance | string | 必填（所在对象出现时） | allOf[2]/allOf[1]/then/oneOf[2] | 余额；币种与范围取决于本对象 | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$(?![\\s\\S])","resolved_ref":"#/$defs/decimal"} |
| response.data.stock_move_ids | array | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"uniqueItems":true} |
| response.data.stock_move_ids[] | integer | 每个数组元素 | allOf[2]/allOf[1]/then |  | {"minimum":1} |
| response.data.account_move_ids | array | 必填（所在对象出现时） | allOf[2]/allOf[1]/then |  | {"uniqueItems":true} |
| response.data.account_move_ids[] | integer | 每个数组元素 | allOf[2]/allOf[1]/then |  | {"minimum":1} |
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
