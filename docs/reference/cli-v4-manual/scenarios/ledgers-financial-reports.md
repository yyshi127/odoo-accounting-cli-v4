# 总账、往来账簿与财务报表

生成和导出总账、日记账、伙伴分类账、试算平衡、资产负债表、利润表、现金流量表、执行摘要和中国本地化财务报表，并查阅报表目录与外部值。报表选项、公司币口径、期间和输出格式按接口合同使用；账龄、税、预算、资产、递延、外币和库存估值报表按业务目的列于其他场景。

[回到总说明书](../../CLI_V4_MANUAL.md) · [新会话使用指南](../USAGE_GUIDE.md)

<a id="cap-report-balance_sheet"></a>

## report.balance_sheet — 生成资产负债表

- 类型：只读；静态状态：`unconfigured`；handler：`report_balance_sheet`。
- 状态原因：`runtime_context_required` — The implementation is installed; availability depends on the selected database, company, user, modules, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/report.balance_sheet.request.schema.json` / `schemas/v1/report.balance_sheet.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.balance_sheet --request "@request.json"
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
| parameters.journal_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":1000,"minItems":1,"uniqueItems":true} |
| parameters.journal_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.balance_sheet"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["report","date","currency","basis","columns","lines","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.report | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["key","name"],"resolved_ref":"#/$defs/report"} |
| response.data.report.key | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":"balance_sheet"} |
| response.data.report.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.date | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["from","to"],"resolved_ref":"#/$defs/date"} |
| response.data.date.from | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.date.to | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","decimal_places"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.currency.decimal_places | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.basis | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":"posted_entries"} |
| response.data.columns | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":64,"minItems":1} |
| response.data.columns[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["index","label","expression_label"],"resolved_ref":"#/$defs/column"} |
| response.data.columns[].index | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.columns[].label | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.columns[].expression_label | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.lines | array | 必填（所在对象出现时） | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":1000} |
| response.data.lines[] | object | 每个数组元素 | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","parent_id","name","level","unfoldable","values"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].parent_id | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].level | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.lines[].unfoldable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.lines[].values | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":64,"minItems":1} |
| response.data.lines[].values[] | 组合/开放结构 | 每个数组元素 | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.lines[].values[] | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].values[] | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"pattern":"^-?(0&#124;[1-9][0-9]*)(\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["report","date","currency","basis","columns","lines","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.report | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["key","name"],"resolved_ref":"#/$defs/report"} |
| response.data.report.key | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"const":"balance_sheet"} |
| response.data.report.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.date | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["from","to"],"resolved_ref":"#/$defs/date"} |
| response.data.date.from | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.date.to | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","decimal_places"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.currency.decimal_places | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.basis | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"const":"posted_entries"} |
| response.data.columns | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":64,"minItems":1} |
| response.data.columns[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["index","label","expression_label"],"resolved_ref":"#/$defs/column"} |
| response.data.columns[].index | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.columns[].label | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.columns[].expression_label | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.lines | array | 必填（所在对象出现时） | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":1000} |
| response.data.lines[] | object | 每个数组元素 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","parent_id","name","level","unfoldable","values"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].parent_id | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.lines[].level | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.lines[].unfoldable | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.lines[].values | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":64,"minItems":1} |
| response.data.lines[].values[] | 组合/开放结构 | 每个数组元素 | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.lines[].values[] | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].values[] | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"pattern":"^-?(0&#124;[1-9][0-9]*)(\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
- `execute`：fixed_read_only_odoo_balance_sheet_handler
- `verify`：single_read_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The fixed report contract, runtime normalization, cursor binding, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_balance_sheet.py, tests/unit/test_balance_sheet_runtime.py, tests/unit/test_balance_sheet_cli.py
- `integration`：`implemented`；The fixed report handler is verified in both synthetic databases and both configured companies.；引用：tests/integration/test_balance_sheet_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-balance_sheet-export"></a>

## report.balance_sheet.export — 导出资产负债表

- 类型：只读；静态状态：`unconfigured`；handler：`report_balance_sheet_export`。
- 状态原因：`runtime_context_required` — The fixed native export handler is installed; availability depends on the selected database, company, user, module, configuration, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/report.balance_sheet.export.request.schema.json` / `schemas/v1/report.balance_sheet.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.balance_sheet.export --request "@request.json"
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
| parameters.journal_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":1000,"minItems":1,"uniqueItems":true} |
| parameters.journal_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.format | 未限定 | 必填（所在对象出现时） |  | 输出格式 | {"enum":["pdf","xlsx"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.balance_sheet.export"} |
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

<a id="cap-report-cash_flow"></a>

## report.cash_flow — 生成现金流量表

- 类型：只读；静态状态：`unconfigured`；handler：`report_cash_flow`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/report.cash_flow.request.schema.json` / `schemas/v1/report.cash_flow.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.cash_flow --request "@request.json"
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
    "date_to": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to"],"resolved_ref":"#/$defs/parameters"} |
| parameters.date_from | string | 必填（所在对象出现时） |  | 开始日期 | {"format":"date"} |
| parameters.date_to | string | 必填（所在对象出现时） |  | 结束日期 | {"format":"date"} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.cash_flow"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["report","date","currency","basis","columns","lines","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.report | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["key","name"],"resolved_ref":"#/$defs/report"} |
| response.data.report.key | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":"cash_flow"} |
| response.data.report.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.date | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["from","to"],"resolved_ref":"#/$defs/date"} |
| response.data.date.from | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.date.to | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","decimal_places"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.currency.decimal_places | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.basis | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":"posted_entries"} |
| response.data.columns | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":64,"minItems":1} |
| response.data.columns[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["index","label","expression_label"],"resolved_ref":"#/$defs/column"} |
| response.data.columns[].index | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.columns[].label | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.columns[].expression_label | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.lines | array | 必填（所在对象出现时） | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":1000} |
| response.data.lines[] | object | 每个数组元素 | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","parent_id","name","level","unfoldable","values"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].parent_id | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].level | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.lines[].unfoldable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.lines[].values | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":64,"minItems":1} |
| response.data.lines[].values[] | 组合/开放结构 | 每个数组元素 | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.lines[].values[] | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].values[] | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"pattern":"^-?(0&#124;[1-9][0-9]*)(\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["report","date","currency","basis","columns","lines","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.report | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["key","name"],"resolved_ref":"#/$defs/report"} |
| response.data.report.key | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"const":"cash_flow"} |
| response.data.report.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.date | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["from","to"],"resolved_ref":"#/$defs/date"} |
| response.data.date.from | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.date.to | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","decimal_places"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.currency.decimal_places | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.basis | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"const":"posted_entries"} |
| response.data.columns | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":64,"minItems":1} |
| response.data.columns[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["index","label","expression_label"],"resolved_ref":"#/$defs/column"} |
| response.data.columns[].index | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.columns[].label | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.columns[].expression_label | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.lines | array | 必填（所在对象出现时） | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":1000} |
| response.data.lines[] | object | 每个数组元素 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","parent_id","name","level","unfoldable","values"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].parent_id | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.lines[].level | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.lines[].unfoldable | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.lines[].values | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":64,"minItems":1} |
| response.data.lines[].values[] | 组合/开放结构 | 每个数组元素 | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.lines[].values[] | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].values[] | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"pattern":"^-?(0&#124;[1-9][0-9]*)(\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
- `execute`：fixed_read_only_odoo_cash_flow_report
- `verify`：single_read_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The fixed report contract, runtime normalization, cursor binding, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_cash_flow.py
- `integration`：`implemented`；The fixed report is verified in both synthetic databases and both configured companies.；引用：tests/integration/test_cash_flow_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-cash_flow-export"></a>

## report.cash_flow.export — 导出现金流量表

- 类型：只读；静态状态：`unconfigured`；handler：`report_cash_flow_export`。
- 状态原因：`runtime_context_required` — The fixed native export handler is installed; availability depends on the selected database, company, user, module, configuration, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/report.cash_flow.export.request.schema.json` / `schemas/v1/report.cash_flow.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.cash_flow.export --request "@request.json"
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
    "format": "pdf"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to","format"],"resolved_ref":"#/$defs/parameters"} |
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.cash_flow.export"} |
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

<a id="cap-report-catalog-get"></a>

## report.catalog.get — 获取会计报表定义详情

- 类型：只读；静态状态：`unconfigured`；handler：`report_catalog_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`financial_reports`；来源模型：res.company, account.report, account.report.column, res.country；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.report:read, account.report.column:read, res.country:read。
- 请求/响应合同：`schemas/v1/report.catalog.get.request.schema.json` / `schemas/v1/report.catalog.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.catalog.get --request "@request.json"
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
    "report_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["report_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.report_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"report.catalog.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.catalog.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"report.catalog.list.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","active","root_report","country","availability_condition","variants","sections","columns","filters"],"resolved_ref":"report.catalog.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.root_report | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.root_report | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.root_report | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.root_report.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.root_report.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.country | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.country | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.country | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.country.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.country.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.availability_condition | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["country","coa","always"]} |
| response.data.variants | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.variants[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.variants[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.variants[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.sections | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.sections[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.sections[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.sections[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.columns | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.columns[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","expression_label","figure_type","sortable","blank_if_zero"],"resolved_ref":"#/$defs/column"} |
| response.data.columns[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.columns[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.columns[].expression_label | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.columns[].figure_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["monetary","percentage","integer","float","date","datetime","boolean","string"]} |
| response.data.columns[].sortable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.columns[].blank_if_zero | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.filters | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["multi_company","date_range","show_draft","unreconciled","unfold_all","journals","analytic","partner"],"resolved_ref":"#/$defs/filters"} |
| response.data.filters.multi_company | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":[null,"selector","tax_units"]} |
| response.data.filters.date_range | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.filters.show_draft | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.filters.unreconciled | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.filters.unfold_all | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.filters.journals | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.filters.analytic | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.filters.partner | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"report.catalog.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","active","root_report","country","availability_condition","variants","sections","columns","filters"],"resolved_ref":"report.catalog.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.root_report | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.root_report | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.root_report | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.root_report.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.root_report.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.country | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.country | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.country | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.country.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.country.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.availability_condition | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["country","coa","always"]} |
| response.data.variants | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.variants[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.variants[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.variants[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.sections | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.sections[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.sections[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.sections[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.columns | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.columns[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","expression_label","figure_type","sortable","blank_if_zero"],"resolved_ref":"#/$defs/column"} |
| response.data.columns[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.columns[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.columns[].expression_label | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.columns[].figure_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["monetary","percentage","integer","float","date","datetime","boolean","string"]} |
| response.data.columns[].sortable | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.columns[].blank_if_zero | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.filters | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["multi_company","date_range","show_draft","unreconciled","unfold_all","journals","analytic","partner"],"resolved_ref":"#/$defs/filters"} |
| response.data.filters.multi_company | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":[null,"selector","tax_units"]} |
| response.data.filters.date_range | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.filters.show_draft | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.filters.unreconciled | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.filters.unfold_all | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.filters.journals | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.filters.analytic | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.filters.partner | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
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
- `execute`：fixed_company_context_core_object_read_action
- `verify`：same_transaction_acl_result_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the closed request and response schemas, registry metadata, CLI handler, validator, model, and audit routing.；引用：tests/unit/test_accounting_reference_read_registry.py
- `integration`：`implemented`；The shared live read-only smoke verifies the capability against both dedicated isolated database aliases without database changes.；引用：tests/integration/test_accounting_reference_read_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-catalog-list"></a>

## report.catalog.list — 列出可用会计报表目录

- 类型：只读；静态状态：`unconfigured`；handler：`report_catalog_list`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`financial_reports`；来源模型：res.company, account.report, account.report.column, res.country；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.report:read, account.report.column:read, res.country:read。
- 请求/响应合同：`schemas/v1/report.catalog.list.request.schema.json` / `schemas/v1/report.catalog.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.catalog.list --request "@request.json"
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
| parameters.country_id | integer/null | 可选（可能有条件限制） |  |  | {"default":null,"minimum":1} |
| parameters.root_report_id | integer/null | 可选（可能有条件限制） |  |  | {"default":null,"minimum":1} |
| parameters.availability_conditions | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"default":null,"oneOf":[{"type":"null"},{"items":{"enum":["country","coa","always"]},"maxItems":3,"minItems":1,"type":"array","uniqueItems":true}]} |
| parameters.availability_conditions | null | 分支约束 | oneOf[1] |  |  |
| parameters.availability_conditions | array | 分支约束 | oneOf[2] |  | {"maxItems":3,"minItems":1,"uniqueItems":true} |
| parameters.availability_conditions[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["country","coa","always"]} |
| parameters.active | boolean/null | 可选（可能有条件限制） |  |  | {"default":null} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.catalog.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","active","root_report","country","availability_condition","variants","sections","columns","filters"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].root_report | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].root_report | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].root_report | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].root_report.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].root_report.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].country | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].country | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].country | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].country.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].country.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].availability_condition | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["country","coa","always"]} |
| response.data.items[].variants | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.items[].variants[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].variants[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].variants[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].sections | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.items[].sections[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].sections[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].sections[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].columns | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.items[].columns[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","expression_label","figure_type","sortable","blank_if_zero"],"resolved_ref":"#/$defs/column"} |
| response.data.items[].columns[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].columns[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].columns[].expression_label | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].columns[].figure_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["monetary","percentage","integer","float","date","datetime","boolean","string"]} |
| response.data.items[].columns[].sortable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].columns[].blank_if_zero | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].filters | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["multi_company","date_range","show_draft","unreconciled","unfold_all","journals","analytic","partner"],"resolved_ref":"#/$defs/filters"} |
| response.data.items[].filters.multi_company | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":[null,"selector","tax_units"]} |
| response.data.items[].filters.date_range | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].filters.show_draft | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].filters.unreconciled | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].filters.unfold_all | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].filters.journals | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].filters.analytic | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].filters.partner | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","active","root_report","country","availability_condition","variants","sections","columns","filters"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].root_report | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].root_report | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].root_report | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].root_report.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].root_report.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].country | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].country | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].country | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].country.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].country.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].availability_condition | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["country","coa","always"]} |
| response.data.items[].variants | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.items[].variants[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].variants[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].variants[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].sections | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.items[].sections[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].sections[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].sections[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].columns | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.items[].columns[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","expression_label","figure_type","sortable","blank_if_zero"],"resolved_ref":"#/$defs/column"} |
| response.data.items[].columns[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].columns[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].columns[].expression_label | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].columns[].figure_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["monetary","percentage","integer","float","date","datetime","boolean","string"]} |
| response.data.items[].columns[].sortable | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].columns[].blank_if_zero | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].filters | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["multi_company","date_range","show_draft","unreconciled","unfold_all","journals","analytic","partner"],"resolved_ref":"#/$defs/filters"} |
| response.data.items[].filters.multi_company | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":[null,"selector","tax_units"]} |
| response.data.items[].filters.date_range | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].filters.show_draft | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].filters.unreconciled | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].filters.unfold_all | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].filters.journals | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].filters.analytic | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].filters.partner | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
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
- `execute`：fixed_company_context_core_object_read_action
- `verify`：same_transaction_acl_result_cursor_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the closed request and response schemas, registry metadata, CLI handler, validator, model, and audit routing.；引用：tests/unit/test_accounting_reference_read_registry.py
- `integration`：`implemented`；The shared live read-only smoke verifies the capability against both dedicated isolated database aliases without database changes.；引用：tests/integration/test_accounting_reference_read_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-china-balance_sheet"></a>

## report.china.balance_sheet — 生成中国资产负债表

- 类型：只读；静态状态：`unconfigured`；handler：`report_china_balance_sheet`。
- 状态原因：`runtime_context_required` — The fixed localized report handler is implemented; availability depends on the selected database, company, user, localization, modules, and ACLs.
- 内部domain：`localization_china`；来源模型：account.report, account.move.line, res.currency, res.country；向导：无。
- 必需模块：l10n_cn_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read, res.currency:read, res.country:read。
- 请求/响应合同：`schemas/v1/report.china.balance_sheet.request.schema.json` / `schemas/v1/report.china.balance_sheet.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.china.balance_sheet --request "@request.json"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.china.balance_sheet"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"china_balance_sheet"}}}}}]}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2] |  | {"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"china_balance_sheet"}}}}}]} |
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
| response.data.report.key | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"china_balance_sheet"} |
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
- `execute`：fixed_odoo_localized_financial_report_handler
- `verify`：rollback_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared typed-report contract, runtime normalization, cursor binding, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_typed_financial_reports.py, tests/unit/test_typed_financial_report_runtime.py, tests/unit/test_typed_financial_report_cli.py
- `integration`：`implemented`；The retained live integration test verifies the localized report against both dedicated isolated database aliases as the ordinary accounting user without committing database changes.；引用：tests/integration/test_remaining_read_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-china-balance_sheet-export"></a>

## report.china.balance_sheet.export — 导出中国资产负债表

- 类型：只读；静态状态：`unconfigured`；handler：`report_china_balance_sheet_export`。
- 状态原因：`runtime_context_required` — The fixed native export handler is installed; availability depends on the selected database, company, user, module, configuration, and ACLs.
- 内部domain：`localization_china`；来源模型：account.report, account.move.line, res.currency, res.country；向导：无。
- 必需模块：l10n_cn_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read, res.currency:read, res.country:read。
- 请求/响应合同：`schemas/v1/report.china.balance_sheet.export.request.schema.json` / `schemas/v1/report.china.balance_sheet.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.china.balance_sheet.export --request "@request.json"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.china.balance_sheet.export"} |
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

<a id="cap-report-china-cash_flow"></a>

## report.china.cash_flow — 生成中国现金流量表

- 类型：只读；静态状态：`unconfigured`；handler：`report_china_cash_flow`。
- 状态原因：`runtime_context_required` — The fixed localized report handler is implemented; availability depends on the selected database, company, user, localization, modules, and ACLs.
- 内部domain：`localization_china`；来源模型：account.report, account.move.line, account.cash.flow.line, res.currency, res.country；向导：无。
- 必需模块：l10n_cn_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read, account.cash.flow.line:read, res.currency:read, res.country:read。
- 请求/响应合同：`schemas/v1/report.china.cash_flow.request.schema.json` / `schemas/v1/report.china.cash_flow.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.china.cash_flow --request "@request.json"
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
    "date_to": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to"],"resolved_ref":"#/$defs/parameters"} |
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.china.cash_flow"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"china_cash_flow"}}}}}]}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2] |  | {"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"china_cash_flow"}}}}}]} |
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
| response.data.report.key | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"china_cash_flow"} |
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
- `execute`：fixed_odoo_localized_financial_report_handler
- `verify`：rollback_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared typed-report contract, runtime normalization, cursor binding, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_typed_financial_reports.py, tests/unit/test_typed_financial_report_runtime.py, tests/unit/test_typed_financial_report_cli.py
- `integration`：`implemented`；The retained live integration test verifies the localized report against both dedicated isolated database aliases as the ordinary accounting user without committing database changes.；引用：tests/integration/test_remaining_read_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-china-cash_flow-export"></a>

## report.china.cash_flow.export — 导出中国现金流量表

- 类型：只读；静态状态：`unconfigured`；handler：`report_china_cash_flow_export`。
- 状态原因：`runtime_context_required` — The fixed native export handler is installed; availability depends on the selected database, company, user, module, configuration, and ACLs.
- 内部domain：`localization_china`；来源模型：account.report, account.move.line, account.cash.flow.line, res.currency, res.country；向导：无。
- 必需模块：l10n_cn_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read, account.cash.flow.line:read, res.currency:read, res.country:read。
- 请求/响应合同：`schemas/v1/report.china.cash_flow.export.request.schema.json` / `schemas/v1/report.china.cash_flow.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.china.cash_flow.export --request "@request.json"
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
    "format": "pdf"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to","format"],"resolved_ref":"#/$defs/parameters"} |
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.china.cash_flow.export"} |
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

<a id="cap-report-china-profit_and_loss"></a>

## report.china.profit_and_loss — 生成中国利润表

- 类型：只读；静态状态：`unconfigured`；handler：`report_china_profit_and_loss`。
- 状态原因：`runtime_context_required` — The fixed localized report handler is implemented; availability depends on the selected database, company, user, localization, modules, and ACLs.
- 内部domain：`localization_china`；来源模型：account.report, account.move.line, res.currency, res.country；向导：无。
- 必需模块：l10n_cn_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read, res.currency:read, res.country:read。
- 请求/响应合同：`schemas/v1/report.china.profit_and_loss.request.schema.json` / `schemas/v1/report.china.profit_and_loss.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.china.profit_and_loss --request "@request.json"
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
    "date_to": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to"],"resolved_ref":"#/$defs/parameters"} |
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.china.profit_and_loss"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"china_profit_and_loss"}}}}}]}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2] |  | {"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"china_profit_and_loss"}}}}}]} |
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
| response.data.report.key | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"china_profit_and_loss"} |
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
- `execute`：fixed_odoo_localized_financial_report_handler
- `verify`：rollback_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared typed-report contract, runtime normalization, cursor binding, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_typed_financial_reports.py, tests/unit/test_typed_financial_report_runtime.py, tests/unit/test_typed_financial_report_cli.py
- `integration`：`implemented`；The retained live integration test verifies the localized report against both dedicated isolated database aliases as the ordinary accounting user without committing database changes.；引用：tests/integration/test_remaining_read_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-china-profit_and_loss-export"></a>

## report.china.profit_and_loss.export — 导出中国利润表

- 类型：只读；静态状态：`unconfigured`；handler：`report_china_profit_and_loss_export`。
- 状态原因：`runtime_context_required` — The fixed native export handler is installed; availability depends on the selected database, company, user, module, configuration, and ACLs.
- 内部domain：`localization_china`；来源模型：account.report, account.move.line, res.currency, res.country；向导：无。
- 必需模块：l10n_cn_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read, res.currency:read, res.country:read。
- 请求/响应合同：`schemas/v1/report.china.profit_and_loss.export.request.schema.json` / `schemas/v1/report.china.profit_and_loss.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.china.profit_and_loss.export --request "@request.json"
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
    "format": "pdf"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to","format"],"resolved_ref":"#/$defs/parameters"} |
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.china.profit_and_loss.export"} |
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

<a id="cap-report-executive_summary"></a>

## report.executive_summary — 生成财务执行摘要

- 类型：只读；静态状态：`unconfigured`；handler：`report_executive_summary`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/report.executive_summary.request.schema.json` / `schemas/v1/report.executive_summary.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.executive_summary --request "@request.json"
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
    "date_to": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to"],"resolved_ref":"#/$defs/parameters"} |
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.executive_summary"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"executive_summary"}}}}}]}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2] |  | {"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"executive_summary"}}}}}]} |
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
| response.data.report.key | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"executive_summary"} |
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
- `execute`：fixed_odoo_executive_summary_report
- `verify`：rollback_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared typed-report contract, runtime normalization, cursor binding, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_typed_financial_reports.py, tests/unit/test_typed_financial_report_runtime.py, tests/unit/test_typed_financial_report_cli.py
- `integration`：`implemented`；The shared live integration test verifies the capability against both dedicated synthetic database aliases without committing database changes.；引用：tests/integration/test_read_capability_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-executive_summary-export"></a>

## report.executive_summary.export — 导出财务执行摘要

- 类型：只读；静态状态：`unconfigured`；handler：`report_executive_summary_export`。
- 状态原因：`runtime_context_required` — The fixed native export handler is installed; availability depends on the selected database, company, user, module, configuration, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/report.executive_summary.export.request.schema.json` / `schemas/v1/report.executive_summary.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.executive_summary.export --request "@request.json"
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
    "format": "pdf"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to","format"],"resolved_ref":"#/$defs/parameters"} |
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.executive_summary.export"} |
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

<a id="cap-report-external_value-get"></a>

## report.external_value.get — 读取财务报表外部值

- 类型：只读；静态状态：`unconfigured`；handler：`report_external_value_get`。
- 状态原因：`runtime_context_required` — The fixed read handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`financial_reports`；来源模型：res.company, account.report.external.value, account.report.expression, account.report.line, account.report；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.report.external.value:read, account.report.expression:read, account.report.line:read, account.report:read。
- 请求/响应合同：`schemas/v1/report.external_value.get.request.schema.json` / `schemas/v1/report.external_value.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.external_value.get --request "@request.json"
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
    "external_value_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["external_value_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.external_value_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"report.external_value.search.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.external_value.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"report.external_value.search.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","name","date","value","text_value","report","report_line","expression","carryover_origin_line","carryover_origin_expression_label"],"resolved_ref":"report.external_value.search.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.value | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.text_value | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.report | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.report | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.report | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.report.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.report.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.report_line | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","code"],"resolved_ref":"#/$defs/report_line"} |
| response.data.report_line.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.report_line.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.report_line.code | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.expression | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","label"],"resolved_ref":"#/$defs/expression"} |
| response.data.expression.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.expression.label | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.carryover_origin_line | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.carryover_origin_line | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.carryover_origin_line | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.carryover_origin_line.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.carryover_origin_line.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.carryover_origin_expression_label | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"report.external_value.search.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","name","date","value","text_value","report","report_line","expression","carryover_origin_line","carryover_origin_expression_label"],"resolved_ref":"report.external_value.search.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.value | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.text_value | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.report | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.report | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.report | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.report.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.report.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.report_line | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","code"],"resolved_ref":"#/$defs/report_line"} |
| response.data.report_line.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.report_line.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.report_line.code | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.expression | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","label"],"resolved_ref":"#/$defs/expression"} |
| response.data.expression.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.expression.label | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.carryover_origin_line | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.carryover_origin_line | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.carryover_origin_line | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.carryover_origin_line.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.carryover_origin_line.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.carryover_origin_expression_label | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
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
- `execute`：fixed_company_scoped_report_external_value_get
- `verify`：same_transaction_acl_company_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared focused test covers registry metadata, fixed CLI routing, model mapping, and exclusion of inventory capabilities.；引用：tests/unit/test_accounting_operational_reads_registry_cli.py
- `integration`：`implemented`；The shared ordinary-accounting-user read-only smoke passed for all twelve capabilities on both dedicated isolated database aliases.；引用：tests/integration/test_accounting_operational_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-external_value-search"></a>

## report.external_value.search — 搜索财务报表外部值

- 类型：只读；静态状态：`unconfigured`；handler：`report_external_value_search`。
- 状态原因：`runtime_context_required` — The fixed read handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`financial_reports`；来源模型：res.company, account.report.external.value, account.report.expression, account.report.line, account.report；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.report.external.value:read, account.report.expression:read, account.report.line:read, account.report:read。
- 请求/响应合同：`schemas/v1/report.external_value.search.request.schema.json` / `schemas/v1/report.external_value.search.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.external_value.search --request "@request.json"
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
| parameters.report_id | integer/null | 可选（可能有条件限制） |  |  | {"default":null,"minimum":1} |
| parameters.expression_id | integer/null | 可选（可能有条件限制） |  |  | {"default":null,"minimum":1} |
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.external_value.search"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","name","date","value","text_value","report","report_line","expression","carryover_origin_line","carryover_origin_expression_label"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].value | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].text_value | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].report | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].report | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].report | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].report.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].report.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].report_line | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","code"],"resolved_ref":"#/$defs/report_line"} |
| response.data.items[].report_line.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].report_line.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].report_line.code | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].expression | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","label"],"resolved_ref":"#/$defs/expression"} |
| response.data.items[].expression.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].expression.label | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].carryover_origin_line | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].carryover_origin_line | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].carryover_origin_line | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].carryover_origin_line.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].carryover_origin_line.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].carryover_origin_expression_label | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","name","date","value","text_value","report","report_line","expression","carryover_origin_line","carryover_origin_expression_label"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].value | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].text_value | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].report | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].report | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].report | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].report.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].report.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].report_line | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","code"],"resolved_ref":"#/$defs/report_line"} |
| response.data.items[].report_line.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].report_line.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].report_line.code | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].expression | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","label"],"resolved_ref":"#/$defs/expression"} |
| response.data.items[].expression.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].expression.label | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].carryover_origin_line | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].carryover_origin_line | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].carryover_origin_line | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].carryover_origin_line.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].carryover_origin_line.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].carryover_origin_expression_label | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
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
- `execute`：fixed_company_scoped_report_external_value_search
- `verify`：same_transaction_acl_cursor_company_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared focused test covers registry metadata, fixed CLI routing, model mapping, and exclusion of inventory capabilities.；引用：tests/unit/test_accounting_operational_reads_registry_cli.py
- `integration`：`implemented`；The shared ordinary-accounting-user read-only smoke passed for all twelve capabilities on both dedicated isolated database aliases.；引用：tests/integration/test_accounting_operational_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-general_ledger"></a>

## report.general_ledger — 生成总账报告

- 类型：只读；静态状态：`unconfigured`；handler：`report_general_ledger`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/report.general_ledger.request.schema.json` / `schemas/v1/report.general_ledger.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.general_ledger --request "@request.json"
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
    "date_to": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to"],"resolved_ref":"#/$defs/parameters"} |
| parameters.date_from | string | 必填（所在对象出现时） |  | 开始日期 | {"format":"date"} |
| parameters.date_to | string | 必填（所在对象出现时） |  | 结束日期 | {"format":"date"} |
| parameters.journal_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":1000,"minItems":1,"uniqueItems":true} |
| parameters.journal_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"type":"object"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.general_ledger"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"general_ledger"}}}}}]}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2] |  | {"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"general_ledger"}}}}}]} |
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
| response.data.report.key | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"general_ledger"} |
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
- `execute`：fixed_odoo_general_ledger_report_handler
- `verify`：rollback_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared typed-report contract, runtime normalization, cursor binding, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_typed_financial_reports.py, tests/unit/test_typed_financial_report_runtime.py, tests/unit/test_typed_financial_report_cli.py
- `integration`：`implemented`；The shared live integration test verifies the capability against both dedicated synthetic database aliases without committing database changes.；引用：tests/integration/test_read_capability_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-general_ledger-export"></a>

## report.general_ledger.export — 导出总账报告

- 类型：只读；静态状态：`unconfigured`；handler：`report_general_ledger_export`。
- 状态原因：`runtime_context_required` — The fixed native export handler is installed; availability depends on the selected database, company, user, module, configuration, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/report.general_ledger.export.request.schema.json` / `schemas/v1/report.general_ledger.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.general_ledger.export --request "@request.json"
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
    "format": "pdf"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to","format"],"resolved_ref":"#/$defs/parameters"} |
| parameters.date_from | string | 必填（所在对象出现时） |  | 开始日期 | {"format":"date"} |
| parameters.date_to | string | 必填（所在对象出现时） |  | 结束日期 | {"format":"date"} |
| parameters.journal_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":1000,"minItems":1,"uniqueItems":true} |
| parameters.journal_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.format | 未限定 | 必填（所在对象出现时） |  | 输出格式 | {"enum":["pdf","xlsx"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.general_ledger.export"} |
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

<a id="cap-report-journal"></a>

## report.journal — 生成日记账报告

- 类型：只读；静态状态：`unconfigured`；handler：`report_journal`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move, account.move.line, res.currency；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move:read, account.move.line:read, res.currency:read。
- 请求/响应合同：`schemas/v1/report.journal.request.schema.json` / `schemas/v1/report.journal.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.journal --request "@request.json"
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
    "date_to": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to"],"resolved_ref":"#/$defs/parameters"} |
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.journal"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"journal"}}}}}]}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2] |  | {"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"journal"}}}}}]} |
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
| response.data.report.key | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"journal"} |
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
- `execute`：fixed_odoo_journal_report_handler
- `verify`：rollback_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared typed-report contract, runtime normalization, cursor binding, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_typed_financial_reports.py, tests/unit/test_typed_financial_report_runtime.py, tests/unit/test_typed_financial_report_cli.py
- `integration`：`implemented`；The shared live integration test verifies the capability against both dedicated synthetic database aliases without committing database changes.；引用：tests/integration/test_read_capability_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-journal-export"></a>

## report.journal.export — 导出日记账报告

- 类型：只读；静态状态：`unconfigured`；handler：`report_journal_export`。
- 状态原因：`runtime_context_required` — The fixed native export handler is installed; availability depends on the selected database, company, user, module, configuration, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move, account.move.line, res.currency；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move:read, account.move.line:read, res.currency:read。
- 请求/响应合同：`schemas/v1/report.journal.export.request.schema.json` / `schemas/v1/report.journal.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.journal.export --request "@request.json"
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
    "format": "pdf"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to","format"],"resolved_ref":"#/$defs/parameters"} |
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.journal.export"} |
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

<a id="cap-report-partner_ledger"></a>

## report.partner_ledger — 生成合作伙伴分类账

- 类型：只读；静态状态：`unconfigured`；handler：`report_partner_ledger`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line, res.partner；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read, res.partner:read。
- 请求/响应合同：`schemas/v1/report.partner_ledger.request.schema.json` / `schemas/v1/report.partner_ledger.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.partner_ledger --request "@request.json"
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
    "date_to": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to"],"resolved_ref":"#/$defs/parameters"} |
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.partner_ledger"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"partner_ledger"}}}}}]}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | 组合/开放结构 | 分支约束 | oneOf[2] |  | {"allOf":[{"$ref":"financial-report.typed-data.schema.json"},{"properties":{"report":{"properties":{"key":{"const":"partner_ledger"}}}}}]} |
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
| response.data.report.key | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"partner_ledger"} |
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
- `execute`：fixed_odoo_partner_ledger_report_handler
- `verify`：rollback_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared typed-report contract, runtime normalization, cursor binding, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_typed_financial_reports.py, tests/unit/test_typed_financial_report_runtime.py, tests/unit/test_typed_financial_report_cli.py
- `integration`：`implemented`；The shared live integration test verifies the capability against both dedicated synthetic database aliases without committing database changes.；引用：tests/integration/test_read_capability_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-partner_ledger-export"></a>

## report.partner_ledger.export — 导出合作伙伴分类账

- 类型：只读；静态状态：`unconfigured`；handler：`report_partner_ledger_export`。
- 状态原因：`runtime_context_required` — The fixed native export handler is installed; availability depends on the selected database, company, user, module, configuration, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line, res.partner；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read, res.partner:read。
- 请求/响应合同：`schemas/v1/report.partner_ledger.export.request.schema.json` / `schemas/v1/report.partner_ledger.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.partner_ledger.export --request "@request.json"
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
    "format": "pdf"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to","format"],"resolved_ref":"#/$defs/parameters"} |
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.partner_ledger.export"} |
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

<a id="cap-report-profit_and_loss"></a>

## report.profit_and_loss — 生成利润表

- 类型：只读；静态状态：`unconfigured`；handler：`report_profit_and_loss`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/report.profit_and_loss.request.schema.json` / `schemas/v1/report.profit_and_loss.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.profit_and_loss --request "@request.json"
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
    "date_to": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to"],"resolved_ref":"#/$defs/parameters"} |
| parameters.date_from | string | 必填（所在对象出现时） |  | 开始日期 | {"format":"date"} |
| parameters.date_to | string | 必填（所在对象出现时） |  | 结束日期 | {"format":"date"} |
| parameters.journal_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":1000,"minItems":1,"uniqueItems":true} |
| parameters.journal_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.profit_and_loss"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["report","date","currency","basis","columns","lines","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.report | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["key","name"],"resolved_ref":"#/$defs/report"} |
| response.data.report.key | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":"profit_and_loss"} |
| response.data.report.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.date | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["from","to"],"resolved_ref":"#/$defs/date"} |
| response.data.date.from | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.date.to | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","decimal_places"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.currency.decimal_places | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.basis | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":"posted_entries"} |
| response.data.columns | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":64,"minItems":1} |
| response.data.columns[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["index","label","expression_label"],"resolved_ref":"#/$defs/column"} |
| response.data.columns[].index | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.columns[].label | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.columns[].expression_label | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.lines | array | 必填（所在对象出现时） | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":1000} |
| response.data.lines[] | object | 每个数组元素 | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","parent_id","name","level","unfoldable","values"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].parent_id | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].level | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.lines[].unfoldable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.lines[].values | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":64,"minItems":1} |
| response.data.lines[].values[] | 组合/开放结构 | 每个数组元素 | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.lines[].values[] | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].values[] | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"pattern":"^-?(0&#124;[1-9][0-9]*)(\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["report","date","currency","basis","columns","lines","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.report | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["key","name"],"resolved_ref":"#/$defs/report"} |
| response.data.report.key | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"const":"profit_and_loss"} |
| response.data.report.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.date | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["from","to"],"resolved_ref":"#/$defs/date"} |
| response.data.date.from | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.date.to | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","decimal_places"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.currency.decimal_places | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.basis | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"const":"posted_entries"} |
| response.data.columns | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":64,"minItems":1} |
| response.data.columns[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["index","label","expression_label"],"resolved_ref":"#/$defs/column"} |
| response.data.columns[].index | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.columns[].label | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.columns[].expression_label | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.lines | array | 必填（所在对象出现时） | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":1000} |
| response.data.lines[] | object | 每个数组元素 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","parent_id","name","level","unfoldable","values"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].parent_id | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.lines[].level | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.lines[].unfoldable | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.lines[].values | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":64,"minItems":1} |
| response.data.lines[].values[] | 组合/开放结构 | 每个数组元素 | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.lines[].values[] | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].values[] | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"pattern":"^-?(0&#124;[1-9][0-9]*)(\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
- `execute`：fixed_read_only_odoo_profit_and_loss_report
- `verify`：single_read_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The fixed report contract, runtime normalization, cursor binding, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_profit_and_loss.py
- `integration`：`implemented`；The fixed report is verified in both synthetic databases and both configured companies.；引用：tests/integration/test_profit_and_loss_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-profit_and_loss-export"></a>

## report.profit_and_loss.export — 导出利润表

- 类型：只读；静态状态：`unconfigured`；handler：`report_profit_and_loss_export`。
- 状态原因：`runtime_context_required` — The fixed native export handler is installed; availability depends on the selected database, company, user, module, configuration, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/report.profit_and_loss.export.request.schema.json` / `schemas/v1/report.profit_and_loss.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.profit_and_loss.export --request "@request.json"
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
    "format": "pdf"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to","format"],"resolved_ref":"#/$defs/parameters"} |
| parameters.date_from | string | 必填（所在对象出现时） |  | 开始日期 | {"format":"date"} |
| parameters.date_to | string | 必填（所在对象出现时） |  | 结束日期 | {"format":"date"} |
| parameters.journal_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":1000,"minItems":1,"uniqueItems":true} |
| parameters.journal_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.format | 未限定 | 必填（所在对象出现时） |  | 输出格式 | {"enum":["pdf","xlsx"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.profit_and_loss.export"} |
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

<a id="cap-report-trial_balance"></a>

## report.trial_balance — 生成试算平衡表

- 类型：只读；静态状态：`unconfigured`；handler：`report_trial_balance`。
- 状态原因：`runtime_context_required` — The implementation is installed; availability depends on the selected database, company, user, modules, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/report.trial_balance.request.schema.json` / `schemas/v1/report.trial_balance.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.trial_balance --request "@request.json"
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
    "date_to": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to"],"resolved_ref":"#/$defs/parameters"} |
| parameters.date_from | string | 必填（所在对象出现时） |  | 开始日期 | {"format":"date"} |
| parameters.date_to | string | 必填（所在对象出现时） |  | 结束日期 | {"format":"date"} |
| parameters.journal_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":1000,"minItems":1,"uniqueItems":true} |
| parameters.journal_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.trial_balance"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["report","date","currency","basis","columns","lines","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.report | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["key","name"],"resolved_ref":"#/$defs/report"} |
| response.data.report.key | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":"trial_balance"} |
| response.data.report.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.date | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["from","to"],"resolved_ref":"#/$defs/date"} |
| response.data.date.from | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.date.to | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","decimal_places"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.currency.decimal_places | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.basis | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":"posted_entries"} |
| response.data.columns | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":64,"minItems":1} |
| response.data.columns[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["index","label","expression_label"],"resolved_ref":"#/$defs/column"} |
| response.data.columns[].index | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.columns[].label | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.columns[].expression_label | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.lines | array | 必填（所在对象出现时） | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":1000} |
| response.data.lines[] | object | 每个数组元素 | oneOf[2] | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","parent_id","name","level","unfoldable","values"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].parent_id | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.lines[].level | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.lines[].unfoldable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.lines[].values | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":64,"minItems":1} |
| response.data.lines[].values[] | 组合/开放结构 | 每个数组元素 | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.lines[].values[] | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.lines[].values[] | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"pattern":"^-?(0&#124;[1-9][0-9]*)(\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["report","date","currency","basis","columns","lines","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.report | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["key","name"],"resolved_ref":"#/$defs/report"} |
| response.data.report.key | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"const":"trial_balance"} |
| response.data.report.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.date | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["from","to"],"resolved_ref":"#/$defs/date"} |
| response.data.date.from | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.date.to | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","decimal_places"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.currency.decimal_places | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.basis | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"const":"posted_entries"} |
| response.data.columns | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":64,"minItems":1} |
| response.data.columns[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["index","label","expression_label"],"resolved_ref":"#/$defs/column"} |
| response.data.columns[].index | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.columns[].label | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.columns[].expression_label | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.lines | array | 必填（所在对象出现时） | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"maxItems":1000} |
| response.data.lines[] | object | 每个数组元素 | allOf[1]/then | 行数组；增补/更新/替换语义由能力ID决定 | {"additionalProperties":false,"required_in_object":["id","parent_id","name","level","unfoldable","values"],"resolved_ref":"#/$defs/line"} |
| response.data.lines[].id | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].parent_id | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":4096,"minLength":1} |
| response.data.lines[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.lines[].level | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.lines[].unfoldable | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.lines[].values | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":64,"minItems":1} |
| response.data.lines[].values[] | 组合/开放结构 | 每个数组元素 | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/decimal"}]} |
| response.data.lines[].values[] | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.lines[].values[] | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"pattern":"^-?(0&#124;[1-9][0-9]*)(\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
- `execute`：fixed_read_only_odoo_trial_balance_handler
- `verify`：single_read_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The fixed report contract, runtime normalization, cursor binding, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_trial_balance.py, tests/unit/test_trial_balance_runtime.py, tests/unit/test_trial_balance_cli.py
- `integration`：`implemented`；The fixed report handler is verified in both synthetic databases and both configured companies.；引用：tests/integration/test_trial_balance_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-report-trial_balance-export"></a>

## report.trial_balance.export — 导出试算平衡表

- 类型：只读；静态状态：`unconfigured`；handler：`report_trial_balance_export`。
- 状态原因：`runtime_context_required` — The fixed native export handler is installed; availability depends on the selected database, company, user, module, configuration, and ACLs.
- 内部domain：`financial_reports`；来源模型：account.report, account.move.line；向导：无。
- 必需模块：account_reports；配置项：database_alias, company_allowlist, user_mapping, account_report_options；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.report:read, account.move.line:read。
- 请求/响应合同：`schemas/v1/report.trial_balance.export.request.schema.json` / `schemas/v1/report.trial_balance.export.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read report.trial_balance.export --request "@request.json"
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
    "format": "pdf"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date_from","date_to","format"],"resolved_ref":"#/$defs/parameters"} |
| parameters.date_from | string | 必填（所在对象出现时） |  | 开始日期 | {"format":"date"} |
| parameters.date_to | string | 必填（所在对象出现时） |  | 结束日期 | {"format":"date"} |
| parameters.journal_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":1000,"minItems":1,"uniqueItems":true} |
| parameters.journal_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.format | 未限定 | 必填（所在对象出现时） |  | 输出格式 | {"enum":["pdf","xlsx"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"report.trial_balance.export"} |
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
