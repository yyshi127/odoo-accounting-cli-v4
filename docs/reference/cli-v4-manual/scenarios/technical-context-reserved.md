# 公司上下文、权限诊断与预留操作审计

确认可用公司上下文、公司会计配置和处理设置，检查运行环境、用户会计访问以及中国和新加坡本地化配置。operation.audit.get 与 operation.status.get 是禁用预留，不可据此假设存在持久操作审计或统一审批执行；连接配置和通用 CLI 外壳的调用方法见总指南。

[回到总说明书](../../CLI_V4_MANUAL.md) · [新会话使用指南](../USAGE_GUIDE.md)

<a id="cap-company-accounting_configuration-inspect"></a>

## company.accounting_configuration.inspect — 检查公司会计配置

- 类型：只读；静态状态：`unconfigured`；handler：`company_accounting_configuration_inspect`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`accounting_context`；来源模型：res.company, res.currency, res.country, account.account；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, res.currency:read, res.country:read, account.account:read。
- 请求/响应合同：`schemas/v1/company.accounting_configuration.inspect.request.schema.json` / `schemas/v1/company.accounting_configuration.inspect.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read company.accounting_configuration.inspect --request "@request.json"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"company.accounting_configuration.inspect"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["company","currency","country","fiscal_country","chart_template","tax_calculation_rounding_method","fiscal_year_end","anglo_saxon_accounting","account_code_prefixes","suspense_account","pos_receivable_account","opening"],"resolved_ref":"#/$defs/data"} |
| response.data.company | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.company.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.country | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/coded"}]} |
| response.data.country | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.country | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.country.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.country.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.country.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.fiscal_country | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/coded"}]} |
| response.data.fiscal_country | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.fiscal_country | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.fiscal_country.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.fiscal_country.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.fiscal_country.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.chart_template | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.tax_calculation_rounding_method | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["round_per_line","round_globally"]} |
| response.data.fiscal_year_end | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["month","day"]} |
| response.data.fiscal_year_end.month | integer | 必填（所在对象出现时） | oneOf[2] |  | {"maximum":12,"minimum":1} |
| response.data.fiscal_year_end.day | integer | 必填（所在对象出现时） | oneOf[2] |  | {"maximum":31,"minimum":1} |
| response.data.anglo_saxon_accounting | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.account_code_prefixes | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["bank","cash","transfer"]} |
| response.data.account_code_prefixes.bank | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.account_code_prefixes.cash | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.account_code_prefixes.transfer | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.suspense_account | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.suspense_account | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.suspense_account | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.suspense_account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.suspense_account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.suspense_account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.pos_receivable_account | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.pos_receivable_account | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.pos_receivable_account | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.pos_receivable_account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.pos_receivable_account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.pos_receivable_account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.opening | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["date","move_id"]} |
| response.data.opening.date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.opening.move_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 会计单据记录ID | {"minimum":1} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["company","currency","country","fiscal_country","chart_template","tax_calculation_rounding_method","fiscal_year_end","anglo_saxon_accounting","account_code_prefixes","suspense_account","pos_receivable_account","opening"],"resolved_ref":"#/$defs/data"} |
| response.data.company | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.company.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.country | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/coded"}]} |
| response.data.country | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.country | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.country.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.country.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.country.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.fiscal_country | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/coded"}]} |
| response.data.fiscal_country | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.fiscal_country | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.fiscal_country.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.fiscal_country.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.fiscal_country.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.chart_template | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.tax_calculation_rounding_method | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["round_per_line","round_globally"]} |
| response.data.fiscal_year_end | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["month","day"]} |
| response.data.fiscal_year_end.month | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"maximum":12,"minimum":1} |
| response.data.fiscal_year_end.day | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"maximum":31,"minimum":1} |
| response.data.anglo_saxon_accounting | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.account_code_prefixes | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["bank","cash","transfer"]} |
| response.data.account_code_prefixes.bank | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.account_code_prefixes.cash | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.account_code_prefixes.transfer | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.suspense_account | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.suspense_account | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.suspense_account | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.suspense_account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.suspense_account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.suspense_account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.pos_receivable_account | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.pos_receivable_account | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.pos_receivable_account | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.pos_receivable_account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.pos_receivable_account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.pos_receivable_account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.opening | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["date","move_id"]} |
| response.data.opening.date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.opening.move_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 会计单据记录ID | {"minimum":1} |
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
- `execute`：fixed_company_accounting_configuration_inspection
- `verify`：single_read_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The fixed request, bridge action, company configuration fields, validation, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_environment_inspection.py
- `integration`：`implemented`；The fixed company accounting configuration is verified in both synthetic databases and both configured companies.；引用：tests/integration/test_environment_inspection_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-company-accounting_context-list"></a>

## company.accounting_context.list — 列出可用会计公司上下文

- 类型：只读；静态状态：`unconfigured`；handler：`company_accounting_context_list`。
- 状态原因：`runtime_context_required` — The allowlisted read handler is implemented; availability depends on a configured database, company allowlist, active user mapping, installed account module, and runtime ACLs.
- 内部domain：`accounting_context`；来源模型：res.company；向导：无。
- 必需模块：base, account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：base.group_user；ACL：res.company:read, res.currency:read, res.country:read。
- 请求/响应合同：`schemas/v1/company.accounting_context.list.request.schema.json` / `schemas/v1/company.accounting_context.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read company.accounting_context.list --request "@request.json"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"company.accounting_context.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","sequence","active","current","currency","country","fiscal_country","chart_template","tax_calculation_rounding_method","fiscal_year_end"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].sequence | integer | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].current | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","decimal_places"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].currency.decimal_places | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.items[].country | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/country"}]} |
| response.data.items[].country | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].country | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/country"} |
| response.data.items[].country.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].country.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].country.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].fiscal_country | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/country"}]} |
| response.data.items[].fiscal_country | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].fiscal_country | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/country"} |
| response.data.items[].fiscal_country.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].fiscal_country.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].fiscal_country.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].chart_template | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].tax_calculation_rounding_method | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":[null,"round_per_line","round_globally"]} |
| response.data.items[].fiscal_year_end | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["month","day"]} |
| response.data.items[].fiscal_year_end.month | integer | 必填（所在对象出现时） | oneOf[2] |  | {"maximum":12,"minimum":1} |
| response.data.items[].fiscal_year_end.day | integer | 必填（所在对象出现时） | oneOf[2] |  | {"maximum":31,"minimum":1} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","sequence","active","current","currency","country","fiscal_country","chart_template","tax_calculation_rounding_method","fiscal_year_end"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].sequence | integer | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].current | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","decimal_places"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].currency.decimal_places | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.items[].country | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/country"}]} |
| response.data.items[].country | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].country | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/country"} |
| response.data.items[].country.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].country.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].country.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].fiscal_country | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/country"}]} |
| response.data.items[].fiscal_country | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].fiscal_country | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/country"} |
| response.data.items[].fiscal_country.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].fiscal_country.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].fiscal_country.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].chart_template | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].tax_calculation_rounding_method | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":[null,"round_per_line","round_globally"]} |
| response.data.items[].fiscal_year_end | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["month","day"]} |
| response.data.items[].fiscal_year_end.month | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"maximum":12,"minimum":1} |
| response.data.items[].fiscal_year_end.day | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"maximum":31,"minimum":1} |
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
- `execute`：local_read_only_bridge_with_configured_company_allowlist_and_business_user_record_rules
- `verify`：strict_contract_validation_and_real_odoo_integration
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The config allowlist, fixed bridge action, runtime scope, keyset contract, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_config.py, tests/unit/test_master_data_bridge.py, tests/unit/test_master_data_cli.py, tests/unit/test_master_data_lists.py, tests/unit/test_company_context_runtime.py
- `integration`：`implemented`；Live tests verify the configured-company allowlist intersection, business-user visibility, current-company marker, strict schemas, and two-page keyset traversal in both synthetic database aliases.；引用：tests/integration/test_company_accounting_context_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-company-processing_settings-get"></a>

## company.processing_settings.get — 查看公司会计业务设置

- 类型：只读；静态状态：`unconfigured`；handler：`company_processing_settings_get`。
- 状态原因：`runtime_context_required` — The fixed current-company read is implemented; availability requires a configured context, the native read-only accounting group and company read access, not company-write administration.
- 内部domain：`accounting_configuration`；来源模型：res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read。
- 请求/响应合同：`schemas/v1/company.processing_settings.get.request.schema.json` / `schemas/v1/company.processing_settings.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read company.processing_settings.get --request "@request.json"
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
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":[]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"company.processing_settings.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","account_journal_early_pay_discount_gain_account_id","account_journal_early_pay_discount_loss_account_id","account_price_include","account_purchase_tax_id","account_sale_tax_id","account_use_credit_limit","autopost_bills","currency_exchange_journal_id","display_invoice_amount_total_words","display_invoice_tax_company_currency","expense_currency_exchange_account_id","fiscalyear_last_day","fiscalyear_last_month","income_currency_exchange_account_id","link_qr_code","qr_code","quick_edit_mode","tax_calculation_rounding_method","expense_account_id","income_account_id","account_journal_suspense_account_id","transfer_account_id","account_discount_expense_allocation_id","account_discount_income_allocation_id","tax_exigibility","tax_cash_basis_journal_id","account_cash_basis_base_account_id"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.tax_exigibility | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.tax_cash_basis_journal_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.account_cash_basis_base_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.account_journal_early_pay_discount_gain_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.account_journal_early_pay_discount_loss_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.account_price_include | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["tax_excluded","tax_included"]} |
| response.data.account_purchase_tax_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.account_sale_tax_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.account_use_credit_limit | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.autopost_bills | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.currency_exchange_journal_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.display_invoice_amount_total_words | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.display_invoice_tax_company_currency | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.expense_currency_exchange_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.fiscalyear_last_day | integer | 必填（所在对象出现时） | oneOf[2] |  | {"maximum":31,"minimum":1} |
| response.data.fiscalyear_last_month | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["1","10","11","12","2","3","4","5","6","7","8","9"]} |
| response.data.income_currency_exchange_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.link_qr_code | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.qr_code | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.quick_edit_mode | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["in_invoices","out_and_in_invoices","out_invoices",null]} |
| response.data.tax_calculation_rounding_method | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["round_globally","round_per_line"]} |
| response.data.expense_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.income_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.account_journal_suspense_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.transfer_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.account_discount_expense_allocation_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.account_discount_income_allocation_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","account_journal_early_pay_discount_gain_account_id","account_journal_early_pay_discount_loss_account_id","account_price_include","account_purchase_tax_id","account_sale_tax_id","account_use_credit_limit","autopost_bills","currency_exchange_journal_id","display_invoice_amount_total_words","display_invoice_tax_company_currency","expense_currency_exchange_account_id","fiscalyear_last_day","fiscalyear_last_month","income_currency_exchange_account_id","link_qr_code","qr_code","quick_edit_mode","tax_calculation_rounding_method","expense_account_id","income_account_id","account_journal_suspense_account_id","transfer_account_id","account_discount_expense_allocation_id","account_discount_income_allocation_id","tax_exigibility","tax_cash_basis_journal_id","account_cash_basis_base_account_id"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.tax_exigibility | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.tax_cash_basis_journal_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.account_cash_basis_base_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.account_journal_early_pay_discount_gain_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.account_journal_early_pay_discount_loss_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.account_price_include | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["tax_excluded","tax_included"]} |
| response.data.account_purchase_tax_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.account_sale_tax_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.account_use_credit_limit | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.autopost_bills | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.currency_exchange_journal_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.display_invoice_amount_total_words | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.display_invoice_tax_company_currency | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.expense_currency_exchange_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.fiscalyear_last_day | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"maximum":31,"minimum":1} |
| response.data.fiscalyear_last_month | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["1","10","11","12","2","3","4","5","6","7","8","9"]} |
| response.data.income_currency_exchange_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.link_qr_code | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.qr_code | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.quick_edit_mode | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["in_invoices","out_and_in_invoices","out_invoices",null]} |
| response.data.tax_calculation_rounding_method | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["round_globally","round_per_line"]} |
| response.data.expense_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.income_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.account_journal_suspense_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.transfer_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.account_discount_expense_allocation_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.account_discount_income_allocation_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
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
- `execute`：fixed_context_company_field_read
- `verify`：closed_typed_company_singleton_binding
- `idempotency`：read_only
- `reverse`：not_applicable

### 已登记测试与证据范围

- `unit`：`implemented`；Closed typed inputs, legacy request/key compatibility, native scopes and posted nonfinancial boundaries.；引用：tests/unit/test_accounting_setup_batch.py
- `integration`：`implemented`；One shared public CLI/native ORM workflow passed both isolated aliases in 22.30s as uid5/su=False/company1. Two new IDs and six extensions: company cash-basis assign/clear/get/replay; optional advanced tax fields, native grouped-tax invoice computation and transition-account rules; sale/purchase posted reference and narration/user edits including a partially reconciled invoice with raw matching IDs/amounts unchanged; posted entry references; financial/shipping denials; positive/negative/zero/minor-unit native currency-aware cash-rounding computation. Native configuration roles exist only inside the isolated transaction; caller never gains sudo. Fresh fixtures, both companies settings, all defaults, currencies/rates and exact caller/native group memberships roll back. Root cash-basis boolean natively propagates to branches; the live topology uses independent roots, not a tested branch workflow. Company ORM write does not run settings UI onchange or delete cash-basis taxes. Group-to-leaf native write need not clear children; non-group calculation ignores retained children. Actual cash-basis entry lifecycle, all hierarchy/currency/localization/hash/lock paths, PDF regeneration, external sends and concurrent exactly-once are not claimed. No business DB, native source/addon or service changes.；引用：tests/integration/test_accounting_setup_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-diagnostic-accounting_environment-inspect"></a>

## diagnostic.accounting_environment.inspect — 检查会计运行环境

- 类型：只读；静态状态：`unconfigured`；handler：`diagnostic_accounting_environment_inspect`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`diagnostics`；来源模型：ir.module.module, res.company, res.users, ir.model.access；向导：无。
- 必需模块：base, account, account_reports；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：base.group_user；ACL：ir.module.module:read, res.company:read, res.users:read。
- 请求/响应合同：`schemas/v1/diagnostic.accounting_environment.inspect.request.schema.json` / `schemas/v1/diagnostic.accounting_environment.inspect.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read diagnostic.accounting_environment.inspect --request "@request.json"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"diagnostic.accounting_environment.inspect"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["company","user","modules","models","transaction_read_only"],"resolved_ref":"#/$defs/data"} |
| response.data.company | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.company.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.user | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","login"],"resolved_ref":"#/$defs/user"} |
| response.data.user.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.user.login | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.modules | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":3,"minItems":3,"prefixItems":[{"allOf":[{"$ref":"#/$defs/module"},{"properties":{"name":{"const":"account"}}}]},{"allOf":[{"$ref":"#/$defs/module"},{"properties":{"name":{"const":"account_reports"}}}]},{"allOf":[{"$ref":"#/$defs/module"},{"properties":{"name":{"const":"base"}}}]}]} |
| response.data.modules[] | 禁止 | 固定前缀以外的剩余元素 | oneOf[2] |  | false |
| response.data.modules[0] | 组合/开放结构 | 固定位置元素 | oneOf[2] |  | {"allOf":[{"$ref":"#/$defs/module"},{"properties":{"name":{"const":"account"}}}]} |
| response.data.modules[0] | object | 分支约束 | oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["name","state","version"],"resolved_ref":"#/$defs/module"} |
| response.data.modules[0].name | 未限定 | 必填（所在对象出现时） | oneOf[2]/allOf[1] | 名称/行说明 | {"enum":["account","account_reports","base"]} |
| response.data.modules[0].state | string | 必填（所在对象出现时） | oneOf[2]/allOf[1] | 状态 | {"minLength":1} |
| response.data.modules[0].version | string/null | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"minLength":1} |
| response.data.modules[0] | 未限定 | 分支约束 | oneOf[2]/allOf[2] |  |  |
| response.data.modules[0].name | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] | 名称/行说明 | {"const":"account"} |
| response.data.modules[1] | 组合/开放结构 | 固定位置元素 | oneOf[2] |  | {"allOf":[{"$ref":"#/$defs/module"},{"properties":{"name":{"const":"account_reports"}}}]} |
| response.data.modules[1] | object | 分支约束 | oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["name","state","version"],"resolved_ref":"#/$defs/module"} |
| response.data.modules[1].name | 未限定 | 必填（所在对象出现时） | oneOf[2]/allOf[1] | 名称/行说明 | {"enum":["account","account_reports","base"]} |
| response.data.modules[1].state | string | 必填（所在对象出现时） | oneOf[2]/allOf[1] | 状态 | {"minLength":1} |
| response.data.modules[1].version | string/null | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"minLength":1} |
| response.data.modules[1] | 未限定 | 分支约束 | oneOf[2]/allOf[2] |  |  |
| response.data.modules[1].name | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] | 名称/行说明 | {"const":"account_reports"} |
| response.data.modules[2] | 组合/开放结构 | 固定位置元素 | oneOf[2] |  | {"allOf":[{"$ref":"#/$defs/module"},{"properties":{"name":{"const":"base"}}}]} |
| response.data.modules[2] | object | 分支约束 | oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["name","state","version"],"resolved_ref":"#/$defs/module"} |
| response.data.modules[2].name | 未限定 | 必填（所在对象出现时） | oneOf[2]/allOf[1] | 名称/行说明 | {"enum":["account","account_reports","base"]} |
| response.data.modules[2].state | string | 必填（所在对象出现时） | oneOf[2]/allOf[1] | 状态 | {"minLength":1} |
| response.data.modules[2].version | string/null | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"minLength":1} |
| response.data.modules[2] | 未限定 | 分支约束 | oneOf[2]/allOf[2] |  |  |
| response.data.modules[2].name | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] | 名称/行说明 | {"const":"base"} |
| response.data.models | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":9,"minItems":9,"prefixItems":[{"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.account"}}}]},{"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.journal"}}}]},{"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.move"}}}]},{"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.move.line"}}}]},{"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.report"}}}]},{"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.tax"}}}]},{"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"ir.module.module"}}}]},{"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"res.company"}}}]},{"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"res.users"}}}]}]} |
| response.data.models[] | 禁止 | 固定前缀以外的剩余元素 | oneOf[2] |  | false |
| response.data.models[0] | 组合/开放结构 | 固定位置元素 | oneOf[2] |  | {"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.account"}}}]} |
| response.data.models[0] | object | 分支约束 | oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","available","read"],"resolved_ref":"#/$defs/model"} |
| response.data.models[0].model | 未限定 | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax","ir.module.module","res.company","res.users"]} |
| response.data.models[0].available | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.models[0].read | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.models[0] | 未限定 | 分支约束 | oneOf[2]/allOf[2] |  |  |
| response.data.models[0].model | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"account.account"} |
| response.data.models[1] | 组合/开放结构 | 固定位置元素 | oneOf[2] |  | {"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.journal"}}}]} |
| response.data.models[1] | object | 分支约束 | oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","available","read"],"resolved_ref":"#/$defs/model"} |
| response.data.models[1].model | 未限定 | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax","ir.module.module","res.company","res.users"]} |
| response.data.models[1].available | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.models[1].read | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.models[1] | 未限定 | 分支约束 | oneOf[2]/allOf[2] |  |  |
| response.data.models[1].model | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"account.journal"} |
| response.data.models[2] | 组合/开放结构 | 固定位置元素 | oneOf[2] |  | {"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.move"}}}]} |
| response.data.models[2] | object | 分支约束 | oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","available","read"],"resolved_ref":"#/$defs/model"} |
| response.data.models[2].model | 未限定 | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax","ir.module.module","res.company","res.users"]} |
| response.data.models[2].available | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.models[2].read | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.models[2] | 未限定 | 分支约束 | oneOf[2]/allOf[2] |  |  |
| response.data.models[2].model | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"account.move"} |
| response.data.models[3] | 组合/开放结构 | 固定位置元素 | oneOf[2] |  | {"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.move.line"}}}]} |
| response.data.models[3] | object | 分支约束 | oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","available","read"],"resolved_ref":"#/$defs/model"} |
| response.data.models[3].model | 未限定 | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax","ir.module.module","res.company","res.users"]} |
| response.data.models[3].available | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.models[3].read | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.models[3] | 未限定 | 分支约束 | oneOf[2]/allOf[2] |  |  |
| response.data.models[3].model | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"account.move.line"} |
| response.data.models[4] | 组合/开放结构 | 固定位置元素 | oneOf[2] |  | {"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.report"}}}]} |
| response.data.models[4] | object | 分支约束 | oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","available","read"],"resolved_ref":"#/$defs/model"} |
| response.data.models[4].model | 未限定 | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax","ir.module.module","res.company","res.users"]} |
| response.data.models[4].available | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.models[4].read | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.models[4] | 未限定 | 分支约束 | oneOf[2]/allOf[2] |  |  |
| response.data.models[4].model | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"account.report"} |
| response.data.models[5] | 组合/开放结构 | 固定位置元素 | oneOf[2] |  | {"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.tax"}}}]} |
| response.data.models[5] | object | 分支约束 | oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","available","read"],"resolved_ref":"#/$defs/model"} |
| response.data.models[5].model | 未限定 | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax","ir.module.module","res.company","res.users"]} |
| response.data.models[5].available | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.models[5].read | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.models[5] | 未限定 | 分支约束 | oneOf[2]/allOf[2] |  |  |
| response.data.models[5].model | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"account.tax"} |
| response.data.models[6] | 组合/开放结构 | 固定位置元素 | oneOf[2] |  | {"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"ir.module.module"}}}]} |
| response.data.models[6] | object | 分支约束 | oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","available","read"],"resolved_ref":"#/$defs/model"} |
| response.data.models[6].model | 未限定 | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax","ir.module.module","res.company","res.users"]} |
| response.data.models[6].available | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.models[6].read | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.models[6] | 未限定 | 分支约束 | oneOf[2]/allOf[2] |  |  |
| response.data.models[6].model | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"ir.module.module"} |
| response.data.models[7] | 组合/开放结构 | 固定位置元素 | oneOf[2] |  | {"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"res.company"}}}]} |
| response.data.models[7] | object | 分支约束 | oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","available","read"],"resolved_ref":"#/$defs/model"} |
| response.data.models[7].model | 未限定 | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax","ir.module.module","res.company","res.users"]} |
| response.data.models[7].available | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.models[7].read | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.models[7] | 未限定 | 分支约束 | oneOf[2]/allOf[2] |  |  |
| response.data.models[7].model | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"res.company"} |
| response.data.models[8] | 组合/开放结构 | 固定位置元素 | oneOf[2] |  | {"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"res.users"}}}]} |
| response.data.models[8] | object | 分支约束 | oneOf[2]/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","available","read"],"resolved_ref":"#/$defs/model"} |
| response.data.models[8].model | 未限定 | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax","ir.module.module","res.company","res.users"]} |
| response.data.models[8].available | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.models[8].read | boolean | 必填（所在对象出现时） | oneOf[2]/allOf[1] |  |  |
| response.data.models[8] | 未限定 | 分支约束 | oneOf[2]/allOf[2] |  |  |
| response.data.models[8].model | 未限定 | 可选（可能有条件限制） | oneOf[2]/allOf[2] |  | {"const":"res.users"} |
| response.data.transaction_read_only | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":true} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["company","user","modules","models","transaction_read_only"],"resolved_ref":"#/$defs/data"} |
| response.data.company | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.company.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.user | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","login"],"resolved_ref":"#/$defs/user"} |
| response.data.user.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.user.login | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.modules | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":3,"minItems":3,"prefixItems":[{"allOf":[{"$ref":"#/$defs/module"},{"properties":{"name":{"const":"account"}}}]},{"allOf":[{"$ref":"#/$defs/module"},{"properties":{"name":{"const":"account_reports"}}}]},{"allOf":[{"$ref":"#/$defs/module"},{"properties":{"name":{"const":"base"}}}]}]} |
| response.data.modules[] | 禁止 | 固定前缀以外的剩余元素 | allOf[1]/then |  | false |
| response.data.modules[0] | 组合/开放结构 | 固定位置元素 | allOf[1]/then |  | {"allOf":[{"$ref":"#/$defs/module"},{"properties":{"name":{"const":"account"}}}]} |
| response.data.modules[0] | object | 分支约束 | allOf[1]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["name","state","version"],"resolved_ref":"#/$defs/module"} |
| response.data.modules[0].name | 未限定 | 必填（所在对象出现时） | allOf[1]/then/allOf[1] | 名称/行说明 | {"enum":["account","account_reports","base"]} |
| response.data.modules[0].state | string | 必填（所在对象出现时） | allOf[1]/then/allOf[1] | 状态 | {"minLength":1} |
| response.data.modules[0].version | string/null | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"minLength":1} |
| response.data.modules[0] | 未限定 | 分支约束 | allOf[1]/then/allOf[2] |  |  |
| response.data.modules[0].name | 未限定 | 可选（可能有条件限制） | allOf[1]/then/allOf[2] | 名称/行说明 | {"const":"account"} |
| response.data.modules[1] | 组合/开放结构 | 固定位置元素 | allOf[1]/then |  | {"allOf":[{"$ref":"#/$defs/module"},{"properties":{"name":{"const":"account_reports"}}}]} |
| response.data.modules[1] | object | 分支约束 | allOf[1]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["name","state","version"],"resolved_ref":"#/$defs/module"} |
| response.data.modules[1].name | 未限定 | 必填（所在对象出现时） | allOf[1]/then/allOf[1] | 名称/行说明 | {"enum":["account","account_reports","base"]} |
| response.data.modules[1].state | string | 必填（所在对象出现时） | allOf[1]/then/allOf[1] | 状态 | {"minLength":1} |
| response.data.modules[1].version | string/null | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"minLength":1} |
| response.data.modules[1] | 未限定 | 分支约束 | allOf[1]/then/allOf[2] |  |  |
| response.data.modules[1].name | 未限定 | 可选（可能有条件限制） | allOf[1]/then/allOf[2] | 名称/行说明 | {"const":"account_reports"} |
| response.data.modules[2] | 组合/开放结构 | 固定位置元素 | allOf[1]/then |  | {"allOf":[{"$ref":"#/$defs/module"},{"properties":{"name":{"const":"base"}}}]} |
| response.data.modules[2] | object | 分支约束 | allOf[1]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["name","state","version"],"resolved_ref":"#/$defs/module"} |
| response.data.modules[2].name | 未限定 | 必填（所在对象出现时） | allOf[1]/then/allOf[1] | 名称/行说明 | {"enum":["account","account_reports","base"]} |
| response.data.modules[2].state | string | 必填（所在对象出现时） | allOf[1]/then/allOf[1] | 状态 | {"minLength":1} |
| response.data.modules[2].version | string/null | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"minLength":1} |
| response.data.modules[2] | 未限定 | 分支约束 | allOf[1]/then/allOf[2] |  |  |
| response.data.modules[2].name | 未限定 | 可选（可能有条件限制） | allOf[1]/then/allOf[2] | 名称/行说明 | {"const":"base"} |
| response.data.models | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":9,"minItems":9,"prefixItems":[{"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.account"}}}]},{"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.journal"}}}]},{"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.move"}}}]},{"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.move.line"}}}]},{"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.report"}}}]},{"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.tax"}}}]},{"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"ir.module.module"}}}]},{"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"res.company"}}}]},{"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"res.users"}}}]}]} |
| response.data.models[] | 禁止 | 固定前缀以外的剩余元素 | allOf[1]/then |  | false |
| response.data.models[0] | 组合/开放结构 | 固定位置元素 | allOf[1]/then |  | {"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.account"}}}]} |
| response.data.models[0] | object | 分支约束 | allOf[1]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","available","read"],"resolved_ref":"#/$defs/model"} |
| response.data.models[0].model | 未限定 | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax","ir.module.module","res.company","res.users"]} |
| response.data.models[0].available | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.models[0].read | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.models[0] | 未限定 | 分支约束 | allOf[1]/then/allOf[2] |  |  |
| response.data.models[0].model | 未限定 | 可选（可能有条件限制） | allOf[1]/then/allOf[2] |  | {"const":"account.account"} |
| response.data.models[1] | 组合/开放结构 | 固定位置元素 | allOf[1]/then |  | {"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.journal"}}}]} |
| response.data.models[1] | object | 分支约束 | allOf[1]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","available","read"],"resolved_ref":"#/$defs/model"} |
| response.data.models[1].model | 未限定 | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax","ir.module.module","res.company","res.users"]} |
| response.data.models[1].available | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.models[1].read | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.models[1] | 未限定 | 分支约束 | allOf[1]/then/allOf[2] |  |  |
| response.data.models[1].model | 未限定 | 可选（可能有条件限制） | allOf[1]/then/allOf[2] |  | {"const":"account.journal"} |
| response.data.models[2] | 组合/开放结构 | 固定位置元素 | allOf[1]/then |  | {"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.move"}}}]} |
| response.data.models[2] | object | 分支约束 | allOf[1]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","available","read"],"resolved_ref":"#/$defs/model"} |
| response.data.models[2].model | 未限定 | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax","ir.module.module","res.company","res.users"]} |
| response.data.models[2].available | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.models[2].read | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.models[2] | 未限定 | 分支约束 | allOf[1]/then/allOf[2] |  |  |
| response.data.models[2].model | 未限定 | 可选（可能有条件限制） | allOf[1]/then/allOf[2] |  | {"const":"account.move"} |
| response.data.models[3] | 组合/开放结构 | 固定位置元素 | allOf[1]/then |  | {"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.move.line"}}}]} |
| response.data.models[3] | object | 分支约束 | allOf[1]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","available","read"],"resolved_ref":"#/$defs/model"} |
| response.data.models[3].model | 未限定 | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax","ir.module.module","res.company","res.users"]} |
| response.data.models[3].available | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.models[3].read | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.models[3] | 未限定 | 分支约束 | allOf[1]/then/allOf[2] |  |  |
| response.data.models[3].model | 未限定 | 可选（可能有条件限制） | allOf[1]/then/allOf[2] |  | {"const":"account.move.line"} |
| response.data.models[4] | 组合/开放结构 | 固定位置元素 | allOf[1]/then |  | {"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.report"}}}]} |
| response.data.models[4] | object | 分支约束 | allOf[1]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","available","read"],"resolved_ref":"#/$defs/model"} |
| response.data.models[4].model | 未限定 | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax","ir.module.module","res.company","res.users"]} |
| response.data.models[4].available | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.models[4].read | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.models[4] | 未限定 | 分支约束 | allOf[1]/then/allOf[2] |  |  |
| response.data.models[4].model | 未限定 | 可选（可能有条件限制） | allOf[1]/then/allOf[2] |  | {"const":"account.report"} |
| response.data.models[5] | 组合/开放结构 | 固定位置元素 | allOf[1]/then |  | {"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"account.tax"}}}]} |
| response.data.models[5] | object | 分支约束 | allOf[1]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","available","read"],"resolved_ref":"#/$defs/model"} |
| response.data.models[5].model | 未限定 | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax","ir.module.module","res.company","res.users"]} |
| response.data.models[5].available | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.models[5].read | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.models[5] | 未限定 | 分支约束 | allOf[1]/then/allOf[2] |  |  |
| response.data.models[5].model | 未限定 | 可选（可能有条件限制） | allOf[1]/then/allOf[2] |  | {"const":"account.tax"} |
| response.data.models[6] | 组合/开放结构 | 固定位置元素 | allOf[1]/then |  | {"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"ir.module.module"}}}]} |
| response.data.models[6] | object | 分支约束 | allOf[1]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","available","read"],"resolved_ref":"#/$defs/model"} |
| response.data.models[6].model | 未限定 | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax","ir.module.module","res.company","res.users"]} |
| response.data.models[6].available | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.models[6].read | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.models[6] | 未限定 | 分支约束 | allOf[1]/then/allOf[2] |  |  |
| response.data.models[6].model | 未限定 | 可选（可能有条件限制） | allOf[1]/then/allOf[2] |  | {"const":"ir.module.module"} |
| response.data.models[7] | 组合/开放结构 | 固定位置元素 | allOf[1]/then |  | {"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"res.company"}}}]} |
| response.data.models[7] | object | 分支约束 | allOf[1]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","available","read"],"resolved_ref":"#/$defs/model"} |
| response.data.models[7].model | 未限定 | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax","ir.module.module","res.company","res.users"]} |
| response.data.models[7].available | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.models[7].read | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.models[7] | 未限定 | 分支约束 | allOf[1]/then/allOf[2] |  |  |
| response.data.models[7].model | 未限定 | 可选（可能有条件限制） | allOf[1]/then/allOf[2] |  | {"const":"res.company"} |
| response.data.models[8] | 组合/开放结构 | 固定位置元素 | allOf[1]/then |  | {"allOf":[{"$ref":"#/$defs/model"},{"properties":{"model":{"const":"res.users"}}}]} |
| response.data.models[8] | object | 分支约束 | allOf[1]/then/allOf[1] |  | {"additionalProperties":false,"required_in_object":["model","available","read"],"resolved_ref":"#/$defs/model"} |
| response.data.models[8].model | 未限定 | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax","ir.module.module","res.company","res.users"]} |
| response.data.models[8].available | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.models[8].read | boolean | 必填（所在对象出现时） | allOf[1]/then/allOf[1] |  |  |
| response.data.models[8] | 未限定 | 分支约束 | allOf[1]/then/allOf[2] |  |  |
| response.data.models[8].model | 未限定 | 可选（可能有条件限制） | allOf[1]/then/allOf[2] |  | {"const":"res.users"} |
| response.data.transaction_read_only | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"const":true} |
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
- `execute`：fixed_accounting_environment_diagnostic
- `verify`：single_read_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The fixed request, bridge action, module and model matrices, validation, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_environment_inspection.py
- `integration`：`implemented`；The fixed module, model-access, company, user, and transaction-read-only facts are verified in both synthetic databases and both configured companies.；引用：tests/integration/test_environment_inspection_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-localization-china-configuration-inspect"></a>

## localization.china.configuration.inspect — 检查中国会计本地化配置

- 类型：只读；静态状态：`unconfigured`；handler：`localization_china_configuration_inspect`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, modules, and ACLs.
- 内部domain：`localization_china`；来源模型：res.company, res.country, account.account, account.move, account.tax, ir.actions.report, ir.module.module；向导：无。
- 必需模块：account, base, l10n_cn, l10n_cn_oscg；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, res.country:read, account.account:read, account.move:read, account.tax:read, ir.actions.report:read, ir.module.module:read。
- 请求/响应合同：`schemas/v1/localization.china.configuration.inspect.request.schema.json` / `schemas/v1/localization.china.configuration.inspect.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read localization.china.configuration.inspect --request "@request.json"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"localization.china.configuration.inspect"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["company_id","fiscal_country_code","chart_template","modules","account_count","default_sale_tax","default_purchase_tax","fapiao_field_ready","voucher_report_ready","configured","missing"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.fiscal_country_code | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^[A-Z]{2}$"} |
| response.data.chart_template | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.modules | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["l10n_cn","l10n_cn_oscg"]} |
| response.data.modules.l10n_cn | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.modules.l10n_cn_oscg | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.account_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.default_sale_tax | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/tax"}]} |
| response.data.default_sale_tax | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.default_sale_tax | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","rate","type_tax_use"],"resolved_ref":"#/$defs/tax"} |
| response.data.default_sale_tax.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.default_sale_tax.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.default_sale_tax.rate | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.default_sale_tax.type_tax_use | 未限定 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"enum":["sale","purchase"]} |
| response.data.default_purchase_tax | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/tax"}]} |
| response.data.default_purchase_tax | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.default_purchase_tax | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","rate","type_tax_use"],"resolved_ref":"#/$defs/tax"} |
| response.data.default_purchase_tax.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.default_purchase_tax.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.default_purchase_tax.rate | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.default_purchase_tax.type_tax_use | 未限定 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"enum":["sale","purchase"]} |
| response.data.fapiao_field_ready | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.voucher_report_ready | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.configured | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.missing | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.missing[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["fiscal_country","chart_template","l10n_cn","l10n_cn_oscg","accounts","default_sale_tax","default_purchase_tax","fapiao_field","voucher_report"]} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["company_id","fiscal_country_code","chart_template","modules","account_count","default_sale_tax","default_purchase_tax","fapiao_field_ready","voucher_report_ready","configured","missing"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.fiscal_country_code | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^[A-Z]{2}$"} |
| response.data.chart_template | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.modules | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["l10n_cn","l10n_cn_oscg"]} |
| response.data.modules.l10n_cn | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.modules.l10n_cn_oscg | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.account_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.default_sale_tax | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/tax"}]} |
| response.data.default_sale_tax | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.default_sale_tax | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","rate","type_tax_use"],"resolved_ref":"#/$defs/tax"} |
| response.data.default_sale_tax.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.default_sale_tax.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.default_sale_tax.rate | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.default_sale_tax.type_tax_use | 未限定 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"enum":["sale","purchase"]} |
| response.data.default_purchase_tax | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/tax"}]} |
| response.data.default_purchase_tax | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.default_purchase_tax | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","rate","type_tax_use"],"resolved_ref":"#/$defs/tax"} |
| response.data.default_purchase_tax.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.default_purchase_tax.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.default_purchase_tax.rate | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.default_purchase_tax.type_tax_use | 未限定 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"enum":["sale","purchase"]} |
| response.data.fapiao_field_ready | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.voucher_report_ready | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.configured | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.missing | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.missing[] | 未限定 | 每个数组元素 | allOf[1]/then |  | {"enum":["fiscal_country","chart_template","l10n_cn","l10n_cn_oscg","accounts","default_sale_tax","default_purchase_tax","fapiao_field","voucher_report"]} |
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
- `execute`：fixed_company_scoped_china_localization_readiness_inspection
- `verify`：read_only_transaction_modules_template_tax_fapiao_voucher_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request, fixed runtime action, company and ACL scope, readiness semantics, and schemas.；引用：tests/unit/test_localization_configuration.py, tests/unit/test_localization_configuration_runtime.py
- `integration`：`implemented`；The guarded shared smoke verifies China readiness against both dedicated isolated databases.；引用：tests/integration/test_accounting_configuration_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-localization-singapore-configuration-inspect"></a>

## localization.singapore.configuration.inspect — 检查新加坡会计本地化配置

- 类型：只读；静态状态：`unconfigured`；handler：`localization_singapore_configuration_inspect`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, modules, and ACLs.
- 内部domain：`localization_singapore`；来源模型：res.company, res.country, res.currency, res.partner.bank, account.tax, account.report, ir.module.module；向导：无。
- 必需模块：account, base, l10n_sg；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, res.country:read, res.currency:read, res.partner.bank:read, account.tax:read, account.report:read, ir.module.module:read。
- 请求/响应合同：`schemas/v1/localization.singapore.configuration.inspect.request.schema.json` / `schemas/v1/localization.singapore.configuration.inspect.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read localization.singapore.configuration.inspect --request "@request.json"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"localization.singapore.configuration.inspect"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["company_id","fiscal_country_code","chart_template","currency_code","default_sale_tax","default_purchase_tax","tax_report","uen_configured","vat_configured","paynow_configured","configured","missing"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.fiscal_country_code | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^[A-Z]{2}$"} |
| response.data.chart_template | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.currency_code | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"pattern":"^[A-Z]{3}$"} |
| response.data.default_sale_tax | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/tax"}]} |
| response.data.default_sale_tax | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.default_sale_tax | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","rate","type_tax_use"],"resolved_ref":"#/$defs/tax"} |
| response.data.default_sale_tax.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.default_sale_tax.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.default_sale_tax.rate | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.default_sale_tax.type_tax_use | 未限定 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"enum":["sale","purchase"]} |
| response.data.default_purchase_tax | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/tax"}]} |
| response.data.default_purchase_tax | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.default_purchase_tax | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","rate","type_tax_use"],"resolved_ref":"#/$defs/tax"} |
| response.data.default_purchase_tax.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.default_purchase_tax.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.default_purchase_tax.rate | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.default_purchase_tax.type_tax_use | 未限定 | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"enum":["sale","purchase"]} |
| response.data.tax_report | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.tax_report | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.tax_report | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.tax_report.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.tax_report.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.uen_configured | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.vat_configured | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.paynow_configured | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.configured | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.missing | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.missing[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["fiscal_country","chart_template","currency","default_sale_gst","default_purchase_gst","tax_report","uen","vat","paynow"]} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["company_id","fiscal_country_code","chart_template","currency_code","default_sale_tax","default_purchase_tax","tax_report","uen_configured","vat_configured","paynow_configured","configured","missing"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.fiscal_country_code | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^[A-Z]{2}$"} |
| response.data.chart_template | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.currency_code | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"pattern":"^[A-Z]{3}$"} |
| response.data.default_sale_tax | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/tax"}]} |
| response.data.default_sale_tax | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.default_sale_tax | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","rate","type_tax_use"],"resolved_ref":"#/$defs/tax"} |
| response.data.default_sale_tax.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.default_sale_tax.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.default_sale_tax.rate | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.default_sale_tax.type_tax_use | 未限定 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"enum":["sale","purchase"]} |
| response.data.default_purchase_tax | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/tax"}]} |
| response.data.default_purchase_tax | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.default_purchase_tax | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","rate","type_tax_use"],"resolved_ref":"#/$defs/tax"} |
| response.data.default_purchase_tax.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.default_purchase_tax.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.default_purchase_tax.rate | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$"} |
| response.data.default_purchase_tax.type_tax_use | 未限定 | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"enum":["sale","purchase"]} |
| response.data.tax_report | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.tax_report | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.tax_report | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.tax_report.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.tax_report.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.uen_configured | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.vat_configured | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.paynow_configured | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.configured | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.missing | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.missing[] | 未限定 | 每个数组元素 | allOf[1]/then |  | {"enum":["fiscal_country","chart_template","currency","default_sale_gst","default_purchase_gst","tax_report","uen","vat","paynow"]} |
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
- `execute`：fixed_company_scoped_singapore_localization_readiness_inspection
- `verify`：read_only_transaction_template_gst_report_uen_vat_paynow_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request, fixed runtime action, company and ACL scope, readiness semantics, and schemas.；引用：tests/unit/test_localization_configuration.py, tests/unit/test_localization_configuration_runtime.py
- `integration`：`implemented`；The guarded shared smoke verifies Singapore readiness against both dedicated isolated databases.；引用：tests/integration/test_accounting_configuration_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-operation-audit-get"></a>

## operation.audit.get — 读取 V4 操作审计链

- 类型：只读；静态状态：`disabled`；handler：`None`。
- 状态原因：`implementation_pending` — The capability is frozen in the G3 matrix but has no implementation or allowlisted handler.
- 内部domain：`operations`；来源模型：v4.operation.audit；向导：无。
- 必需模块：odoo_accounting_cli_v4；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：base.group_user；ACL：v4.operation.audit:read。
- 请求/响应合同：`schemas/v1/request.schema.json` / `schemas/v1/response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read operation.audit.get --request "@request.json"
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

- `preview`：not_applicable_read_only
- `execute`：implementation_pending
- `verify`：real_odoo_result_reread_and_schema_validation_pending
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`planned`；The unit definition is frozen; implementation evidence is pending.；引用：无
- `integration`：`planned`；The integration definition is frozen; implementation evidence is pending.；引用：无
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-operation-status-get"></a>

## operation.status.get — 读取 V4 操作状态

- 类型：只读；静态状态：`disabled`；handler：`None`。
- 状态原因：`implementation_pending` — The capability is frozen in the G3 matrix but has no implementation or allowlisted handler.
- 内部domain：`operations`；来源模型：v4.operation；向导：无。
- 必需模块：odoo_accounting_cli_v4；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：base.group_user；ACL：v4.operation:read。
- 请求/响应合同：`schemas/v1/request.schema.json` / `schemas/v1/response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read operation.status.get --request "@request.json"
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

- `preview`：not_applicable_read_only
- `execute`：implementation_pending
- `verify`：real_odoo_result_reread_and_schema_validation_pending
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`planned`；The unit definition is frozen; implementation evidence is pending.；引用：无
- `integration`：`planned`；The integration definition is frozen; implementation evidence is pending.；引用：无
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-user-accounting_access-inspect"></a>

## user.accounting_access.inspect — 检查用户会计访问权限

- 类型：只读；静态状态：`unconfigured`；handler：`user_accounting_access_inspect`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`accounting_context`；来源模型：res.users, res.groups, ir.model.access；向导：无。
- 必需模块：base, account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：base.group_user；ACL：res.users:read, res.groups:read, ir.model.access:read。
- 请求/响应合同：`schemas/v1/user.accounting_access.inspect.request.schema.json` / `schemas/v1/user.accounting_access.inspect.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read user.accounting_access.inspect --request "@request.json"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"user.accounting_access.inspect"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["user","company_id","groups","model_acl"],"resolved_ref":"#/$defs/data"} |
| response.data.user | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","login","name","active","company_ids"],"resolved_ref":"#/$defs/user"} |
| response.data.user.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.user.login | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.user.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.user.active | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"const":true} |
| response.data.user.company_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"minItems":1,"uniqueItems":true} |
| response.data.user.company_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.groups | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":5,"minItems":5} |
| response.data.groups[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["xml_id","member"],"resolved_ref":"#/$defs/group"} |
| response.data.groups[].xml_id | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["base.group_user","account.group_account_readonly","account.group_account_invoice","account.group_account_user","account.group_account_manager"]} |
| response.data.groups[].member | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.model_acl | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":6,"minItems":6} |
| response.data.model_acl[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["model","read","create","write","unlink"],"resolved_ref":"#/$defs/model_acl"} |
| response.data.model_acl[].model | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax"]} |
| response.data.model_acl[].read | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.model_acl[].create | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.model_acl[].write | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.model_acl[].unlink | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["user","company_id","groups","model_acl"],"resolved_ref":"#/$defs/data"} |
| response.data.user | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","login","name","active","company_ids"],"resolved_ref":"#/$defs/user"} |
| response.data.user.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.user.login | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.user.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.user.active | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"const":true} |
| response.data.user.company_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"minItems":1,"uniqueItems":true} |
| response.data.user.company_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.groups | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":5,"minItems":5} |
| response.data.groups[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["xml_id","member"],"resolved_ref":"#/$defs/group"} |
| response.data.groups[].xml_id | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["base.group_user","account.group_account_readonly","account.group_account_invoice","account.group_account_user","account.group_account_manager"]} |
| response.data.groups[].member | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.model_acl | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":6,"minItems":6} |
| response.data.model_acl[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["model","read","create","write","unlink"],"resolved_ref":"#/$defs/model_acl"} |
| response.data.model_acl[].model | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["account.account","account.journal","account.move","account.move.line","account.report","account.tax"]} |
| response.data.model_acl[].read | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.model_acl[].create | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.model_acl[].write | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.model_acl[].unlink | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
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
- `execute`：fixed_configured_user_group_and_model_acl_inspection
- `verify`：single_read_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The fixed request, bridge action, group list, model ACL list, validation, and CLI dispatch are covered by unit tests.；引用：tests/unit/test_accounting_access.py
- `integration`：`implemented`；The configured user, accounting groups, and fixed model ACL matrix are verified in both synthetic databases and both configured companies.；引用：tests/integration/test_accounting_access_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。
