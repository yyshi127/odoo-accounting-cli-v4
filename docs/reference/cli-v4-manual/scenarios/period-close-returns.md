# 财政年度、期末处理、锁期与会计申报

解析和维护财政年度，查看公司锁定日期及锁期例外，解析允许的会计日期，管理转结模型，生成预提或期末转结，执行期末校验，并维护会计申报、检查结果和账户状态。部分调整和锁期修改为禁用预留；account.return.mark_submitted 只改变 Odoo 内部状态，不向外部税务机关申报。

[回到总说明书](../../CLI_V4_MANUAL.md) · [新会话使用指南](../USAGE_GUIDE.md)

<a id="cap-account-lock_exception-get"></a>

## account.lock_exception.get — 读取会计锁定日期例外

- 类型：只读；静态状态：`unconfigured`；handler：`account_lock_exception_get`。
- 状态原因：`runtime_context_required` — The fixed read handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`period_close`；来源模型：res.company, res.users, account.lock_exception；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, res.users:read, account.lock_exception:read。
- 请求/响应合同：`schemas/v1/account.lock_exception.get.request.schema.json` / `schemas/v1/account.lock_exception.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read account.lock_exception.get --request "@request.json"
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
    "lock_exception_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["lock_exception_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.lock_exception_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"account.lock_exception.search.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"account.lock_exception.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"account.lock_exception.search.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","user","reason","end_datetime","state","active","lock_date_field","lock_date","company_lock_date"],"resolved_ref":"account.lock_exception.search.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.user | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.user | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.user | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.user.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.user.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.reason | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.end_datetime | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","type":"string"}]} |
| response.data.end_datetime | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.end_datetime | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"} |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["active","revoked","expired"]} |
| response.data.active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.lock_date_field | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["fiscalyear_lock_date","tax_lock_date","sale_lock_date","purchase_lock_date"]} |
| response.data.lock_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.company_lock_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"account.lock_exception.search.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","user","reason","end_datetime","state","active","lock_date_field","lock_date","company_lock_date"],"resolved_ref":"account.lock_exception.search.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.user | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.user | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.user | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.user.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.user.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.reason | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.end_datetime | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","type":"string"}]} |
| response.data.end_datetime | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.end_datetime | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["active","revoked","expired"]} |
| response.data.active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.lock_date_field | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["fiscalyear_lock_date","tax_lock_date","sale_lock_date","purchase_lock_date"]} |
| response.data.lock_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.company_lock_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
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
- `execute`：fixed_company_scoped_account_lock_exception_get
- `verify`：same_transaction_acl_company_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared focused test covers registry metadata, fixed CLI routing, model mapping, and exclusion of inventory capabilities.；引用：tests/unit/test_accounting_operational_reads_registry_cli.py
- `integration`：`implemented`；The shared ordinary-accounting-user read-only smoke passed for all twelve capabilities on both dedicated isolated database aliases.；引用：tests/integration/test_accounting_operational_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-lock_exception-search"></a>

## account.lock_exception.search — 搜索会计锁定日期例外

- 类型：只读；静态状态：`unconfigured`；handler：`account_lock_exception_search`。
- 状态原因：`runtime_context_required` — The fixed read handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`period_close`；来源模型：res.company, res.users, account.lock_exception；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, res.users:read, account.lock_exception:read。
- 请求/响应合同：`schemas/v1/account.lock_exception.search.request.schema.json` / `schemas/v1/account.lock_exception.search.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read account.lock_exception.search --request "@request.json"
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
| parameters.states | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"default":null,"oneOf":[{"type":"null"},{"items":{"enum":["active","revoked","expired"]},"maxItems":3,"minItems":1,"type":"array","uniqueItems":true}]} |
| parameters.states | null | 分支约束 | oneOf[1] |  |  |
| parameters.states | array | 分支约束 | oneOf[2] |  | {"maxItems":3,"minItems":1,"uniqueItems":true} |
| parameters.states[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["active","revoked","expired"]} |
| parameters.user_id | integer/null | 可选（可能有条件限制） |  |  | {"default":null,"minimum":1} |
| parameters.lock_date_fields | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"default":null,"oneOf":[{"type":"null"},{"items":{"enum":["fiscalyear_lock_date","tax_lock_date","sale_lock_date","purchase_lock_date"]},"maxItems":4,"minItems":1,"type":"array","uniqueItems":true}]} |
| parameters.lock_date_fields | null | 分支约束 | oneOf[1] |  |  |
| parameters.lock_date_fields | array | 分支约束 | oneOf[2] |  | {"maxItems":4,"minItems":1,"uniqueItems":true} |
| parameters.lock_date_fields[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["fiscalyear_lock_date","tax_lock_date","sale_lock_date","purchase_lock_date"]} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"account.lock_exception.search"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","user","reason","end_datetime","state","active","lock_date_field","lock_date","company_lock_date"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].user | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].user | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].user | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].user.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].user.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].reason | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].end_datetime | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","type":"string"}]} |
| response.data.items[].end_datetime | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].end_datetime | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["active","revoked","expired"]} |
| response.data.items[].active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].lock_date_field | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["fiscalyear_lock_date","tax_lock_date","sale_lock_date","purchase_lock_date"]} |
| response.data.items[].lock_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].company_lock_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","user","reason","end_datetime","state","active","lock_date_field","lock_date","company_lock_date"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].user | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].user | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].user | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].user.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].user.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].reason | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].end_datetime | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$","type":"string"}]} |
| response.data.items[].end_datetime | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].end_datetime | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"format":"date-time","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["active","revoked","expired"]} |
| response.data.items[].active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].lock_date_field | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["fiscalyear_lock_date","tax_lock_date","sale_lock_date","purchase_lock_date"]} |
| response.data.items[].lock_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].company_lock_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
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
- `execute`：fixed_company_scoped_account_lock_exception_search
- `verify`：same_transaction_acl_cursor_company_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared focused test covers registry metadata, fixed CLI routing, model mapping, and exclusion of inventory capabilities.；引用：tests/unit/test_accounting_operational_reads_registry_cli.py
- `integration`：`implemented`；The shared ordinary-accounting-user read-only smoke passed for all twelve capabilities on both dedicated isolated database aliases.；引用：tests/integration/test_accounting_operational_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-return-account_status-get"></a>

## account.return.account_status.get — 读取申报表科目审计状态

- 类型：只读；静态状态：`unconfigured`；handler：`account_return_account_status_get`。
- 状态原因：`runtime_context_required` — Availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`period_close`；来源模型：res.company, account.return, account.audit.account.status, account.account；向导：无。
- 必需模块：account_reports, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.return:read, account.audit.account.status:read, account.account:read。
- 请求/响应合同：`schemas/v1/account.return.account_status.get.request.schema.json` / `schemas/v1/account.return.account_status.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read account.return.account_status.get --request "@request.json"
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
    "account_status_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["account_status_id"]} |
| parameters.account_status_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"account.return.account_status.search.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"account.return.account_status.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"account.return.account_status.search.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","return","account","status"],"resolved_ref":"account.return.account_status.search.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.return | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.return.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.return.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.account | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.account.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.account.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.account.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.status | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":[null,"todo","reviewed","supervised","anomaly"]} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"account.return.account_status.search.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","return","account","status"],"resolved_ref":"account.return.account_status.search.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.return | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.return.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.return.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.account | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.account.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.account.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.account.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.status | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":[null,"todo","reviewed","supervised","anomaly"]} |
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
- `execute`：fixed_company_scoped_account_return_account_status_get
- `verify`：same_transaction_acl_company_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The focused test covers registry metadata, fixed CLI routing, and model mapping.；引用：tests/unit/test_accounting_supporting_object_reads_registry_cli.py
- `integration`：`implemented`；The shared uid-5 read-only smoke passed on both isolated databases, verifying model/field availability, ACL, empty pages, and missing-record errors; populated-row and computed-field live evidence remains pending.；引用：tests/integration/test_accounting_supporting_object_reads_live.py
- `golden`：`planned`；Golden examples are deferred until target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-return-account_status-search"></a>

## account.return.account_status.search — 搜索申报表科目审计状态

- 类型：只读；静态状态：`unconfigured`；handler：`account_return_account_status_search`。
- 状态原因：`runtime_context_required` — Availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`period_close`；来源模型：res.company, account.return, account.audit.account.status, account.account；向导：无。
- 必需模块：account_reports, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.return:read, account.audit.account.status:read, account.account:read。
- 请求/响应合同：`schemas/v1/account.return.account_status.search.request.schema.json` / `schemas/v1/account.return.account_status.search.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read account.return.account_status.search --request "@request.json"
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
| parameters.return_id | integer/null | 可选（可能有条件限制） |  |  | {"default":null,"minimum":1} |
| parameters.account_id | integer/null | 可选（可能有条件限制） |  | 会计科目ID | {"default":null,"minimum":1} |
| parameters.statuses | 组合/开放结构 | 可选（可能有条件限制） |  |  | {"default":null,"oneOf":[{"type":"null"},{"items":{"enum":["todo","reviewed","supervised","anomaly"]},"maxItems":4,"minItems":1,"type":"array","uniqueItems":true}]} |
| parameters.statuses | null | 分支约束 | oneOf[1] |  |  |
| parameters.statuses | array | 分支约束 | oneOf[2] |  | {"maxItems":4,"minItems":1,"uniqueItems":true} |
| parameters.statuses[] | 未限定 | 每个数组元素 | oneOf[2] |  | {"enum":["todo","reviewed","supervised","anomaly"]} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"account.return.account_status.search"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","return","account","status"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].return | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].return.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].return.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].account | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].account.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].account.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].account.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].status | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":[null,"todo","reviewed","supervised","anomaly"]} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","return","account","status"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].return | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].return.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].return.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].account | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].account.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].account.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].account.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].status | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":[null,"todo","reviewed","supervised","anomaly"]} |
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
- `execute`：fixed_company_scoped_account_return_account_status_search
- `verify`：same_transaction_acl_cursor_company_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The focused test covers registry metadata, fixed CLI routing, and model mapping.；引用：tests/unit/test_accounting_supporting_object_reads_registry_cli.py
- `integration`：`implemented`；The shared uid-5 read-only smoke passed on both isolated databases, verifying model/field availability, ACL, empty pages, and missing-record errors; populated-row and computed-field live evidence remains pending.；引用：tests/integration/test_accounting_supporting_object_reads_live.py
- `golden`：`planned`；Golden examples are deferred until target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-return-archive"></a>

## account.return.archive — 归档会计申报

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, user, module, return state, and ACL set.
- 内部domain：`period_close`；来源模型：res.company, account.return.type, account.return；向导：无。
- 必需模块：account_reports, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：res.company:read, account.return.type:read, account.return:read, account.return:write。
- 请求/响应合同：`schemas/v1/account.return.archive.request.schema.json` / `schemas/v1/account.return.archive.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run account.return.archive --request "@request.json" --idempotency-key "account.return.archive:1" --confirm "account.return.archive"
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
    "return_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["return_id"]} |
| parameters.return_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"account.return.archive"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"account.return.archive"} |
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
- `execute`：fixed_company_scoped_native_account_return_action_archive
- `verify`：same_transaction_inactive_state_reread_and_response_schema_validation
- `idempotency`：target_inactive_state_recheck_without_operation_store_or_protection_from_intermediate_changes
- `reverse`：account.return.restore

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover confirmation, company and new-state scope, native archive behavior, replay, result validation, and CLI dispatch.；引用：tests/unit/test_account_returns.py, tests/unit/test_account_return_writes_runtime.py, tests/unit/test_return_journal_analysis_cli.py
- `integration`：`implemented`；The shared guarded transactional smoke verifies archive, replay, restore, and rollback in both isolated database aliases.；引用：tests/integration/test_return_journal_analysis_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-return-check-get"></a>

## account.return.check.get — 获取会计申报检查项

- 类型：只读；静态状态：`unconfigured`；handler：`account_return_check_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`period_close`；来源模型：account.return, account.return.check, res.company；向导：无。
- 必需模块：account_reports, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.return:read, account.return.check:read, res.company:read。
- 请求/响应合同：`schemas/v1/account.return.check.get.request.schema.json` / `schemas/v1/account.return.check.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read account.return.check.get --request "@request.json"
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
    "check_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["check_id"]} |
| parameters.check_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"account.return.check.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"account.return.check.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"account.return.check.list.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","return","code","type","name","message","state","result","records_count"],"resolved_ref":"account.return.check.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.return | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.return.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.return.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["check","file"]} |
| response.data.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.message | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["new","reviewed","submitted","paid"]} |
| response.data.result | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["todo","reviewed","supervised","anomaly"]} |
| response.data.records_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"account.return.check.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","return","code","type","name","message","state","result","records_count"],"resolved_ref":"account.return.check.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.return | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.return.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.return.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["check","file"]} |
| response.data.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.message | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["new","reviewed","submitted","paid"]} |
| response.data.result | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["todo","reviewed","supervised","anomaly"]} |
| response.data.records_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
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
- `execute`：fixed_visible_return_check_get
- `verify`：read_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover exact check identity, parent-return company scope, omitted dynamic actions and attachments, schemas, and CLI dispatch.；引用：tests/unit/test_account_returns.py, tests/unit/test_account_returns_runtime.py, tests/unit/test_account_return_schemas.py, tests/unit/test_return_journal_analysis_cli.py
- `integration`：`implemented`；The shared guarded smoke reads one scoped check as uid 5 in both isolated databases and verifies rollback.；引用：tests/integration/test_return_journal_analysis_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-return-check-list"></a>

## account.return.check.list — 列出会计申报检查项

- 类型：只读；静态状态：`unconfigured`；handler：`account_return_check_list`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`period_close`；来源模型：account.return, account.return.check, res.company；向导：无。
- 必需模块：account_reports, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.return:read, account.return.check:read, res.company:read。
- 请求/响应合同：`schemas/v1/account.return.check.list.request.schema.json` / `schemas/v1/account.return.check.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read account.return.check.list --request "@request.json"
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
    "return_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["return_id"]} |
| parameters.return_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.result | string/null | 可选（可能有条件限制） |  |  | {"default":null,"enum":["todo","reviewed","supervised","anomaly",null]} |
| parameters.type | string/null | 可选（可能有条件限制） |  |  | {"default":null,"enum":["check","file",null]} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"account.return.check.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","return","code","type","name","message","state","result","records_count"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].return | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].return.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].return.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["check","file"]} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].message | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["new","reviewed","submitted","paid"]} |
| response.data.items[].result | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["todo","reviewed","supervised","anomaly"]} |
| response.data.items[].records_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","return","code","type","name","message","state","result","records_count"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].return | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].return.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].return.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["check","file"]} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].message | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["new","reviewed","submitted","paid"]} |
| response.data.items[].result | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["todo","reviewed","supervised","anomaly"]} |
| response.data.items[].records_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
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
- `execute`：fixed_visible_return_check_list
- `verify`：read_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover parent-return company scope, fixed filters, cursor binding, sanitized rows, schemas, and CLI dispatch.；引用：tests/unit/test_account_returns.py, tests/unit/test_account_returns_runtime.py, tests/unit/test_account_return_schemas.py, tests/unit/test_return_journal_analysis_cli.py
- `integration`：`implemented`；The shared guarded smoke reads a transaction-local check as uid 5 in both isolated databases and verifies rollback.；引用：tests/integration/test_return_journal_analysis_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-return-check-result-update"></a>

## account.return.check.result.update — 更新会计申报检查结果

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, user, module, return state, and ACL set.
- 内部domain：`period_close`；来源模型：res.company, account.return.type, account.return, account.return.check；向导：无。
- 必需模块：account_reports, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：res.company:read, account.return.type:read, account.return:read, account.return.check:read, account.return.check:write。
- 请求/响应合同：`schemas/v1/account.return.check.result.update.request.schema.json` / `schemas/v1/account.return.check.result.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run account.return.check.result.update --request "@request.json" --idempotency-key "account.return.check.result.update:1:todo" --confirm "account.return.check.result.update"
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
    "check_id": 1,
    "result": "todo"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["check_id","result"]} |
| parameters.check_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.result | string | 必填（所在对象出现时） |  |  | {"enum":["todo","reviewed"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"account.return.check.result.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"account.return.check.result.update"} |
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
- `execute`：fixed_company_scoped_account_return_check_result_write
- `verify`：same_transaction_check_result_reread_and_response_schema_validation
- `idempotency`：target_result_recheck_without_operation_store_or_protection_from_intermediate_changes
- `reverse`：repeat_with_previous_todo_or_reviewed_result

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the todo-or-reviewed enum, confirmation, parent-return company and new-state scope, target replay, result validation, and CLI dispatch.；引用：tests/unit/test_account_returns.py, tests/unit/test_account_return_writes_runtime.py, tests/unit/test_return_journal_analysis_cli.py
- `integration`：`implemented`；The shared guarded transactional smoke verifies check-result update, replay, and rollback in both isolated database aliases.；引用：tests/integration/test_return_journal_analysis_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-return-checks-refresh"></a>

## account.return.checks.refresh — 刷新会计申报检查项

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, user, module, return state, and ACL set.
- 内部domain：`period_close`；来源模型：res.company, account.return.type, account.return, account.return.check；向导：无。
- 必需模块：account_reports, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：res.company:read, account.return.type:read, account.return:read, account.return.check:read, account.return.check:create, account.return.check:write。
- 请求/响应合同：`schemas/v1/account.return.checks.refresh.request.schema.json` / `schemas/v1/account.return.checks.refresh.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run account.return.checks.refresh --request "@request.json" --idempotency-key "account.return.checks.refresh:1" --confirm "account.return.checks.refresh"
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
    "return_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["return_id"]} |
| parameters.return_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"account.return.checks.refresh"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"account.return.checks.refresh"} |
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
- `execute`：fixed_company_scoped_native_account_return_refresh_checks
- `verify`：same_transaction_return_and_check_state_reread_and_response_schema_validation
- `idempotency`：current_return_and_check_state_recheck_without_operation_store_or_concurrent_exactly_once_guarantee
- `reverse`：not_reversible_check_evaluation

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the closed request, confirmation, new-state and company scope, native check refresh, result validation, and CLI dispatch.；引用：tests/unit/test_account_returns.py, tests/unit/test_account_return_writes_runtime.py, tests/unit/test_return_journal_analysis_cli.py
- `integration`：`implemented`；The shared guarded transactional smoke verifies native check refresh and rollback in both isolated database aliases.；引用：tests/integration/test_return_journal_analysis_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-return-create"></a>

## account.return.create — 创建会计申报

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`concurrent_idempotency_limit` — The handler supports only a standalone root company and a date range equal to exactly one native Odoo return period; it rechecks the company, return type, and date-range natural key, but Odoo has no matching request-id uniqueness constraint for concurrent exactly-once creation.
- 内部domain：`period_close`；来源模型：res.company, account.return.type, account.return, account.return.check, account.return.creation.wizard；向导：account.return.creation.wizard。
- 必需模块：account_reports, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：res.company:read, account.return.type:read, account.return:read, account.return:create, account.return.check:read, account.return.check:create, account.return.check:write, account.return.creation.wizard:create。
- 请求/响应合同：`schemas/v1/account.return.create.request.schema.json` / `schemas/v1/account.return.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run account.return.create --request "@request.json" --idempotency-key "account.return.create:1:50493b922be4bacdf521aad933178c0d" --confirm "account.return.create"
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
    "return_type_id": 1,
    "date_from": "2026-10-01",
    "date_to": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["return_type_id","date_from","date_to"]} |
| parameters.return_type_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.date_from | string | 必填（所在对象出现时） |  | The first day of exactly one native Odoo return period for the selected standalone root company. | {"format":"date"} |
| parameters.date_to | string | 必填（所在对象出现时） |  | The last day of the same native Odoo return period; the range must not span multiple periods. | {"format":"date"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"account.return.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"account.return.create"} |
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
- `execute`：fixed_standalone_root_company_single_native_return_period_creation_wizard
- `verify`：same_transaction_created_return_reread_and_response_schema_validation
- `idempotency`：company_return_type_and_date_range_natural_key_recheck_without_operation_store_or_concurrent_exactly_once_guarantee
- `reverse`：account.return.delete_when_still_manual_and_new

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the closed create contract, confirmation, company and type scope, native creation flow, replay limits, result validation, and CLI dispatch.；引用：tests/unit/test_account_returns.py, tests/unit/test_account_return_writes_runtime.py, tests/unit/test_return_journal_analysis_cli.py
- `integration`：`implemented`；The shared guarded transactional smoke verifies manual return creation, immediate replay, and rollback in both isolated database aliases.；引用：tests/integration/test_return_journal_analysis_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-return-delete"></a>

## account.return.delete — 删除手工会计申报

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`deleted_record_tombstone_unavailable` — The handler verifies record absence but keeps no persistent tombstone, so a later retry cannot distinguish its prior deletion from an unrelated disappearance.
- 内部domain：`period_close`；来源模型：res.company, account.return.type, account.return；向导：无。
- 必需模块：account_reports, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：res.company:read, account.return.type:read, account.return:read, account.return:unlink。
- 请求/响应合同：`schemas/v1/account.return.delete.request.schema.json` / `schemas/v1/account.return.delete.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run account.return.delete --request "@request.json" --idempotency-key "account.return.delete:1" --confirm "account.return.delete"
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
    "return_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["return_id"]} |
| parameters.return_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"account.return.delete"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"account.return.delete"} |
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
- `execute`：fixed_company_scoped_native_account_return_action_delete
- `verify`：same_transaction_record_absence_and_response_schema_validation
- `idempotency`：record_absence_recheck_without_operation_store_or_persistent_tombstone
- `reverse`：not_reversible_deleted_return_must_be_recreated

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover confirmation, company and manual-new guardrails, native deletion, absence verification, tombstone limits, result validation, and CLI dispatch.；引用：tests/unit/test_account_returns.py, tests/unit/test_account_return_writes_runtime.py, tests/unit/test_return_journal_analysis_cli.py
- `integration`：`implemented`；The shared guarded transactional smoke verifies deletion of a manual new return and rollback in both isolated database aliases.；引用：tests/integration/test_return_journal_analysis_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-return-get"></a>

## account.return.get — 获取会计申报

- 类型：只读；静态状态：`unconfigured`；handler：`account_return_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`period_close`；来源模型：account.return, account.return.type, account.return.check, account.tax.unit, res.company；向导：无。
- 必需模块：account_reports, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.return:read, account.return.type:read, account.return.check:read, account.tax.unit:read, res.company:read。
- 请求/响应合同：`schemas/v1/account.return.get.request.schema.json` / `schemas/v1/account.return.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read account.return.get --request "@request.json"
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
    "return_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["return_id"]} |
| parameters.return_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"account.return.search.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"account.return.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"account.return.search.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","active","date_from","date_to","date_deadline","date_submission","date_lock","type","state","next_state","is_completed","company_id","tax_unit_id","manually_created","check_counts"],"resolved_ref":"account.return.search.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.date_from | string | 必填（所在对象出现时） | oneOf[2] | 开始日期 | {"format":"date"} |
| response.data.date_to | string | 必填（所在对象出现时） | oneOf[2] | 结束日期 | {"format":"date"} |
| response.data.date_deadline | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.date_submission | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.date_lock | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.type | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","category"],"resolved_ref":"#/$defs/return_type"} |
| response.data.type.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.type.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.type.category | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["account_return","audit"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["new","reviewed","submitted","paid"]} |
| response.data.next_state | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["new","reviewed","submitted","paid",null]} |
| response.data.is_completed | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.tax_unit_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.manually_created | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.check_counts | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["total","unresolved","resolved"],"resolved_ref":"#/$defs/check_counts"} |
| response.data.check_counts.total | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.check_counts.unresolved | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.check_counts.resolved | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"account.return.search.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","active","date_from","date_to","date_deadline","date_submission","date_lock","type","state","next_state","is_completed","company_id","tax_unit_id","manually_created","check_counts"],"resolved_ref":"account.return.search.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.date_from | string | 必填（所在对象出现时） | allOf[1]/then | 开始日期 | {"format":"date"} |
| response.data.date_to | string | 必填（所在对象出现时） | allOf[1]/then | 结束日期 | {"format":"date"} |
| response.data.date_deadline | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.date_submission | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.date_lock | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.type | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","category"],"resolved_ref":"#/$defs/return_type"} |
| response.data.type.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.type.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.type.category | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["account_return","audit"]} |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["new","reviewed","submitted","paid"]} |
| response.data.next_state | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["new","reviewed","submitted","paid",null]} |
| response.data.is_completed | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.tax_unit_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.manually_created | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.check_counts | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["total","unresolved","resolved"],"resolved_ref":"#/$defs/check_counts"} |
| response.data.check_counts.total | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.check_counts.unresolved | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.check_counts.resolved | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
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
- `execute`：fixed_company_scoped_account_return_get
- `verify`：read_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover exact-ID and company scope, closed response mapping, schemas, and CLI dispatch.；引用：tests/unit/test_account_returns.py, tests/unit/test_account_returns_bridge.py, tests/unit/test_account_returns_runtime.py, tests/unit/test_account_return_schemas.py, tests/unit/test_return_journal_analysis_cli.py
- `integration`：`implemented`；The shared guarded smoke reads one transaction-local return as uid 5 in both isolated databases and verifies rollback.；引用：tests/integration/test_return_journal_analysis_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-return-mark_submitted"></a>

## account.return.mark_submitted — 在 Odoo 内标记会计申报为已提交

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler only advances Odoo's internal return state; availability depends on the configured database, company, user, workflow, checks, and ACLs, and no external tax-authority filing is performed.
- 内部domain：`period_close`；来源模型：res.company, account.return.type, account.return, account.return.check；向导：无。
- 必需模块：account_reports, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：res.company:read, account.return.type:read, account.return:read, account.return:write, account.return.check:read。
- 请求/响应合同：`schemas/v1/account.return.mark_submitted.request.schema.json` / `schemas/v1/account.return.mark_submitted.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run account.return.mark_submitted --request "@request.json" --idempotency-key "account.return.mark_submitted:1" --confirm "account.return.mark_submitted"
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
    "return_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["return_id"]} |
| parameters.return_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"account.return.mark_submitted"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"account.return.mark_submitted"} |
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
- `execute`：fixed_company_scoped_native_account_return_action_submit_internal_state_only
- `verify`：same_transaction_submitted_state_and_submission_date_reread_and_response_schema_validation
- `idempotency`：target_submitted_state_recheck_without_operation_store_or_protection_from_intermediate_changes
- `reverse`：native_reset_actions_not_exposed_in_this_batch

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover confirmation, company and workflow scope, internal Odoo submission-state transition, replay, result validation, and CLI dispatch.；引用：tests/unit/test_account_returns.py, tests/unit/test_account_return_writes_runtime.py, tests/unit/test_return_journal_analysis_cli.py
- `integration`：`implemented`；The shared guarded transactional smoke verifies the internal submitted-state transition and rollback in both isolated database aliases; it does not contact an external tax authority.；引用：tests/integration/test_return_journal_analysis_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-return-restore"></a>

## account.return.restore — 恢复已归档会计申报

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, user, module, archived record, and ACL set.
- 内部domain：`period_close`；来源模型：res.company, account.return.type, account.return；向导：无。
- 必需模块：account_reports, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：res.company:read, account.return.type:read, account.return:read, account.return:write。
- 请求/响应合同：`schemas/v1/account.return.restore.request.schema.json` / `schemas/v1/account.return.restore.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run account.return.restore --request "@request.json" --idempotency-key "account.return.restore:1" --confirm "account.return.restore"
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
    "return_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["return_id"]} |
| parameters.return_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"account.return.restore"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"account.return.restore"} |
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
- `execute`：fixed_company_scoped_account_return_active_restore
- `verify`：same_transaction_active_state_reread_and_response_schema_validation
- `idempotency`：target_active_state_recheck_without_operation_store_or_protection_from_intermediate_changes
- `reverse`：account.return.archive

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover confirmation, archived-record company scope, active-state restore, replay, result validation, and CLI dispatch.；引用：tests/unit/test_account_returns.py, tests/unit/test_account_return_writes_runtime.py, tests/unit/test_return_journal_analysis_cli.py
- `integration`：`implemented`；The shared guarded transactional smoke verifies archive, restore, replay, and rollback in both isolated database aliases.；引用：tests/integration/test_return_journal_analysis_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-return-search"></a>

## account.return.search — 搜索会计申报

- 类型：只读；静态状态：`unconfigured`；handler：`account_return_search`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`period_close`；来源模型：account.return, account.return.type, account.return.check, account.tax.unit, res.company；向导：无。
- 必需模块：account_reports, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.return:read, account.return.type:read, account.return.check:read, account.tax.unit:read, res.company:read。
- 请求/响应合同：`schemas/v1/account.return.search.request.schema.json` / `schemas/v1/account.return.search.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read account.return.search --request "@request.json"
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
| parameters.type_id | integer/null | 可选（可能有条件限制） |  |  | {"default":null,"minimum":1} |
| parameters.state | string/null | 可选（可能有条件限制） |  | 状态 | {"default":null,"enum":["new","reviewed","submitted","paid",null]} |
| parameters.completed | boolean/null | 可选（可能有条件限制） |  |  | {"default":null} |
| parameters.deadline_from | string/null | 可选（可能有条件限制） |  |  | {"default":null,"format":"date"} |
| parameters.deadline_to | string/null | 可选（可能有条件限制） |  |  | {"default":null,"format":"date"} |
| parameters.active | boolean/null | 可选（可能有条件限制） |  |  | {"default":true} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"account.return.search"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","active","date_from","date_to","date_deadline","date_submission","date_lock","type","state","next_state","is_completed","company_id","tax_unit_id","manually_created","check_counts"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].date_from | string | 必填（所在对象出现时） | oneOf[2] | 开始日期 | {"format":"date"} |
| response.data.items[].date_to | string | 必填（所在对象出现时） | oneOf[2] | 结束日期 | {"format":"date"} |
| response.data.items[].date_deadline | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].date_submission | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].date_lock | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].type | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","category"],"resolved_ref":"#/$defs/return_type"} |
| response.data.items[].type.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].type.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].type.category | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["account_return","audit"]} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["new","reviewed","submitted","paid"]} |
| response.data.items[].next_state | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["new","reviewed","submitted","paid",null]} |
| response.data.items[].is_completed | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].tax_unit_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].manually_created | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].check_counts | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["total","unresolved","resolved"],"resolved_ref":"#/$defs/check_counts"} |
| response.data.items[].check_counts.total | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.items[].check_counts.unresolved | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.items[].check_counts.resolved | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","active","date_from","date_to","date_deadline","date_submission","date_lock","type","state","next_state","is_completed","company_id","tax_unit_id","manually_created","check_counts"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].date_from | string | 必填（所在对象出现时） | allOf[1]/then | 开始日期 | {"format":"date"} |
| response.data.items[].date_to | string | 必填（所在对象出现时） | allOf[1]/then | 结束日期 | {"format":"date"} |
| response.data.items[].date_deadline | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].date_submission | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].date_lock | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].type | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","category"],"resolved_ref":"#/$defs/return_type"} |
| response.data.items[].type.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].type.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].type.category | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["account_return","audit"]} |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["new","reviewed","submitted","paid"]} |
| response.data.items[].next_state | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["new","reviewed","submitted","paid",null]} |
| response.data.items[].is_completed | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].tax_unit_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].manually_created | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].check_counts | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["total","unresolved","resolved"],"resolved_ref":"#/$defs/check_counts"} |
| response.data.items[].check_counts.total | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.items[].check_counts.unresolved | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.items[].check_counts.resolved | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
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
- `execute`：fixed_company_scoped_account_return_search
- `verify`：read_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover fixed filters, company scope, cursor binding, bridge validation, runtime mapping, schemas, and CLI dispatch.；引用：tests/unit/test_account_returns.py, tests/unit/test_account_returns_bridge.py, tests/unit/test_account_returns_runtime.py, tests/unit/test_account_return_schemas.py, tests/unit/test_return_journal_analysis_cli.py
- `integration`：`implemented`；The shared guarded smoke verifies the native return search in both isolated databases and rolls back its fixture.；引用：tests/integration/test_return_journal_analysis_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-return-summary"></a>

## account.return.summary — 汇总会计申报到期状态

- 类型：只读；静态状态：`unconfigured`；handler：`account_return_summary`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`period_close`；来源模型：account.return, res.company；向导：无。
- 必需模块：account_reports, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.return:read, res.company:read。
- 请求/响应合同：`schemas/v1/account.return.summary.request.schema.json` / `schemas/v1/account.return.summary.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read account.return.summary --request "@request.json"
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
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["as_of"]} |
| parameters.as_of | string | 必填（所在对象出现时） |  | 截至日期 | {"format":"date"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"account.return.summary"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["company_id","as_of","counts"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.as_of | string | 必填（所在对象出现时） | oneOf[2] | 截至日期 | {"format":"date"} |
| response.data.counts | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["total","open","completed","overdue","due_today","due_next_30_days","later"],"resolved_ref":"#/$defs/counts"} |
| response.data.counts.total | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.counts.open | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.counts.completed | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.counts.overdue | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.counts.due_today | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.counts.due_next_30_days | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.counts.later | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["company_id","as_of","counts"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.as_of | string | 必填（所在对象出现时） | allOf[1]/then | 截至日期 | {"format":"date"} |
| response.data.counts | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["total","open","completed","overdue","due_today","due_next_30_days","later"],"resolved_ref":"#/$defs/counts"} |
| response.data.counts.total | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.counts.open | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.counts.completed | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.counts.overdue | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.counts.due_today | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.counts.due_next_30_days | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.counts.later | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
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
- `execute`：fixed_company_scoped_account_return_deadline_counts
- `verify`：read_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the fixed as-of buckets, company scope, count invariants, schemas, and CLI dispatch.；引用：tests/unit/test_account_returns.py, tests/unit/test_account_returns_runtime.py, tests/unit/test_account_return_schemas.py, tests/unit/test_return_journal_analysis_cli.py
- `integration`：`implemented`；The shared guarded smoke verifies native company-scoped return counts in both isolated databases.；引用：tests/integration/test_return_journal_analysis_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-return-type-list"></a>

## account.return.type.list — 列出会计申报类型

- 类型：只读；静态状态：`unconfigured`；handler：`account_return_type_list`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`period_close`；来源模型：account.return.type, account.report, res.country, res.company；向导：无。
- 必需模块：account_reports, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.return.type:read, account.report:read, res.country:read, res.company:read。
- 请求/响应合同：`schemas/v1/account.return.type.list.request.schema.json` / `schemas/v1/account.return.type.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read account.return.type.list --request "@request.json"
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
| parameters.category | string/null | 可选（可能有条件限制） |  |  | {"default":null,"enum":["account_return","audit",null]} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"account.return.type.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","company_id","category","report","country","auto_generate","states_workflow","deadline_periodicity","deadline_start_date","deadline_days_delay"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].category | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["account_return","audit"]} |
| response.data.items[].report | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].report | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].report | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].report.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].report.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].country | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].country | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.items[].country | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].country.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.items[].country.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].auto_generate | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].states_workflow | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["generic_state_review","generic_state_review_submit","generic_state_tax_report","generic_state_only_pay"]} |
| response.data.items[].deadline_periodicity | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["monthly","2_months","trimester","4_months","semester","year",null]} |
| response.data.items[].deadline_start_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].deadline_days_delay | integer | 必填（所在对象出现时） | oneOf[2] |  |  |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","company_id","category","report","country","auto_generate","states_workflow","deadline_periodicity","deadline_start_date","deadline_days_delay"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].category | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["account_return","audit"]} |
| response.data.items[].report | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].report | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].report | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].report.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].report.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].country | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/named"}]} |
| response.data.items[].country | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.items[].country | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].country.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.items[].country.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].auto_generate | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].states_workflow | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["generic_state_review","generic_state_review_submit","generic_state_tax_report","generic_state_only_pay"]} |
| response.data.items[].deadline_periodicity | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["monthly","2_months","trimester","4_months","semester","year",null]} |
| response.data.items[].deadline_start_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].deadline_days_delay | integer | 必填（所在对象出现时） | allOf[1]/then |  |  |
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
- `execute`：fixed_company_context_return_type_list
- `verify`：read_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover category filters, company-dependent values, pagination, schemas, and CLI dispatch.；引用：tests/unit/test_account_returns.py, tests/unit/test_account_returns_runtime.py, tests/unit/test_account_return_schemas.py, tests/unit/test_return_journal_analysis_cli.py
- `integration`：`implemented`；The shared guarded smoke reads installed return types through the requested company context in both isolated databases.；引用：tests/integration/test_return_journal_analysis_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-return-validate"></a>

## account.return.validate — 校验会计申报

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, user, module, return workflow, checks, and ACL set.
- 内部domain：`period_close`；来源模型：res.company, account.return.type, account.return, account.return.check；向导：无。
- 必需模块：account_reports, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：res.company:read, account.return.type:read, account.return:read, account.return:write, account.return.check:read, account.return.check:create, account.return.check:write。
- 请求/响应合同：`schemas/v1/account.return.validate.request.schema.json` / `schemas/v1/account.return.validate.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run account.return.validate --request "@request.json" --idempotency-key "account.return.validate:1" --confirm "account.return.validate"
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
    "return_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["return_id"]} |
| parameters.return_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"account.return.validate"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"account.return.validate"} |
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
- `execute`：fixed_company_scoped_native_account_return_action_validate
- `verify`：same_transaction_reviewed_state_reread_and_response_schema_validation
- `idempotency`：target_reviewed_state_recheck_without_operation_store_or_protection_from_intermediate_changes
- `reverse`：native_reset_actions_not_exposed_in_this_batch

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover confirmation, company and workflow scope, native validation, failing-check guardrails, replay, result validation, and CLI dispatch.；引用：tests/unit/test_account_returns.py, tests/unit/test_account_return_writes_runtime.py, tests/unit/test_return_journal_analysis_cli.py
- `integration`：`implemented`；The shared guarded transactional smoke verifies native return validation, replay, and rollback in both isolated database aliases.；引用：tests/integration/test_return_journal_analysis_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-transfer_model-archive"></a>

## account.transfer_model.archive — 归档科目转结模型

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed native action_archive handler is registered; availability depends on runtime configuration, company-scoped transfer data, state, and accounting-manager access.
- 内部domain：`period_close`；来源模型：res.company, account.journal, account.account, account.transfer.model, account.transfer.model.line；向导：无。
- 必需模块：account_transfer, account_accountant, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.journal:read, account.account:read, account.transfer.model:read, account.transfer.model:write, account.transfer.model.line:read。
- 请求/响应合同：`schemas/v1/account.transfer_model.archive.request.schema.json` / `schemas/v1/account.transfer_model.archive.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run account.transfer_model.archive --request "@request.json" --idempotency-key "account.transfer_model.archive:1" --confirm "account.transfer_model.archive"
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
    "transfer_model_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transfer_model_id"]} |
| parameters.transfer_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"account.transfer_model.archive"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"account.transfer_model.archive"} |
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
- `execute`：fixed_company_scoped_native_account_transfer_model_action_archive
- `verify`：same_transaction_inactive_disabled_state_reread_and_response_schema_validation
- `idempotency`：target_archived_state_recheck_without_operation_store
- `reverse`：account.transfer_model.restore

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover confirmation, company scope, native disable-before-archive behavior, replay, result validation, registry schemas, and CLI dispatch.；引用：tests/unit/test_account_transfer_model_writes_public.py, tests/unit/test_account_transfer_model_writes_runtime.py
- `integration`：`implemented`；Guarded shared live smoke passed both isolated aliases as uid 5 with su=False, exercising this command and its immediate replay except delete; outer rollback plus a fresh cursor proved model, line, move, and temporary group residue absent.；引用：tests/integration/test_account_transfer_model_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-transfer_model-create"></a>

## account.transfer_model.create — 创建科目转结模型

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`concurrent_idempotency_limit` — The handler can recheck an exact company-scoped natural-key match, but Odoo provides no matching request-id uniqueness constraint for concurrent exactly-once creation.
- 内部domain：`period_close`；来源模型：res.company, account.journal, account.account, account.transfer.model, account.transfer.model.line；向导：无。
- 必需模块：account_transfer, account_accountant, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.journal:read, account.account:read, account.transfer.model:read, account.transfer.model:create, account.transfer.model.line:read, account.transfer.model.line:create。
- 请求/响应合同：`schemas/v1/account.transfer_model.create.request.schema.json` / `schemas/v1/account.transfer_model.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run account.transfer_model.create --request "@request.json" --idempotency-key "account.transfer_model.create:1:796c261fe023720deb75bb1b9501d792" --confirm "account.transfer_model.create"
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
    "journal_id": 1,
    "date_start": "2026-10-01",
    "date_stop": "2026-10-31",
    "frequency": "month",
    "origin_account_ids": [
      1
    ],
    "destination_lines": [
      {
        "account_id": 1,
        "percentage": "1"
      }
    ]
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["name","journal_id","date_start","date_stop","frequency","origin_account_ids","destination_lines"]} |
| parameters.name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":256,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","resolved_ref":"#/$defs/text256"} |
| parameters.journal_id | integer | 必填（所在对象出现时） |  | 日记账ID | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.date_start | string | 必填（所在对象出现时） |  |  | {"format":"date"} |
| parameters.date_stop | string/null | 必填（所在对象出现时） |  |  | {"format":"date"} |
| parameters.frequency | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["month","quarter","year"]} |
| parameters.origin_account_ids | array | 必填（所在对象出现时） |  |  | {"maxItems":1000,"minItems":1,"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| parameters.origin_account_ids[] | integer | 每个数组元素 |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.destination_lines | array | 必填（所在对象出现时） |  |  | {"maxItems":1000,"minItems":1,"resolved_ref":"#/$defs/destinationLines","uniqueItems":true} |
| parameters.destination_lines[] | object | 每个数组元素 |  |  | {"additionalProperties":false,"required_in_object":["account_id","percentage"],"resolved_ref":"#/$defs/destinationLine"} |
| parameters.destination_lines[].account_id | integer | 必填（所在对象出现时） |  | 会计科目ID | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.destination_lines[].percentage | string | 必填（所在对象出现时） |  |  | {"maxLength":9,"pattern":"^(?:100&#124;(?:[1-9]&#124;[1-9][0-9])(?:\\.[0-9]{0,5}[1-9])?&#124;0\\.[0-9]{0,5}[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/positivePercentage"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"account.transfer_model.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"account.transfer_model.create"} |
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
- `execute`：fixed_company_scoped_account_transfer_model_create
- `verify`：same_transaction_created_model_lines_and_state_reread_and_response_schema_validation
- `idempotency`：company_name_and_full_normalized_parameters_natural_key_recheck_without_concurrent_exactly_once_guarantee
- `reverse`：account.transfer_model.delete_when_never_run

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the closed normalized create contract, company-scoped references, result validation, registry schemas, and CLI dispatch.；引用：tests/unit/test_account_transfer_model_writes_public.py, tests/unit/test_account_transfer_model_writes_runtime.py
- `integration`：`implemented`；Guarded shared live smoke passed both isolated aliases as uid 5 with su=False, exercising this command and its immediate replay except delete; outer rollback plus a fresh cursor proved model, line, move, and temporary group residue absent.；引用：tests/integration/test_account_transfer_model_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-transfer_model-delete"></a>

## account.transfer_model.delete — 删除未运行的科目转结模型

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`deleted_record_tombstone_unavailable` — The handler verifies absence after deleting an active, disabled, never-run model, but keeps no persistent tombstone, so a later retry cannot distinguish its prior deletion from an unrelated disappearance.
- 内部domain：`period_close`；来源模型：res.company, account.journal, account.account, account.transfer.model, account.transfer.model.line, account.move；向导：无。
- 必需模块：account_transfer, account_accountant, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.journal:read, account.account:read, account.transfer.model:read, account.transfer.model:unlink, account.transfer.model.line:read, account.move:read。
- 请求/响应合同：`schemas/v1/account.transfer_model.delete.request.schema.json` / `schemas/v1/account.transfer_model.delete.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run account.transfer_model.delete --request "@request.json" --idempotency-key "account.transfer_model.delete:1" --confirm "account.transfer_model.delete"
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
    "transfer_model_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transfer_model_id"]} |
| parameters.transfer_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"account.transfer_model.delete"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"account.transfer_model.delete"} |
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
- `execute`：fixed_company_scoped_never_run_account_transfer_model_unlink
- `verify`：same_transaction_record_absence_and_response_schema_validation
- `idempotency`：record_absence_recheck_without_operation_store_or_persistent_tombstone
- `reverse`：not_reversible_deleted_transfer_model_must_be_recreated

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover confirmation, company and never-run guardrails, native unlink rejection for generated moves, absence verification, tombstone limits, registry schemas, and CLI dispatch.；引用：tests/unit/test_account_transfer_model_writes_public.py, tests/unit/test_account_transfer_model_writes_runtime.py
- `integration`：`implemented`；Guarded shared live smoke passed both isolated aliases as uid 5 with su=False, exercising this command and its immediate replay except delete; outer rollback plus a fresh cursor proved model, line, move, and temporary group residue absent.；引用：tests/integration/test_account_transfer_model_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-transfer_model-disable"></a>

## account.transfer_model.disable — 停用科目转结模型

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed native action_disable handler is registered; availability depends on runtime configuration, company-scoped transfer data, state, and accounting-manager access.
- 内部domain：`period_close`；来源模型：res.company, account.journal, account.account, account.transfer.model, account.transfer.model.line；向导：无。
- 必需模块：account_transfer, account_accountant, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.journal:read, account.account:read, account.transfer.model:read, account.transfer.model:write, account.transfer.model.line:read。
- 请求/响应合同：`schemas/v1/account.transfer_model.disable.request.schema.json` / `schemas/v1/account.transfer_model.disable.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run account.transfer_model.disable --request "@request.json" --idempotency-key "account.transfer_model.disable:1" --confirm "account.transfer_model.disable"
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
    "transfer_model_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transfer_model_id"]} |
| parameters.transfer_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"account.transfer_model.disable"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"account.transfer_model.disable"} |
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
- `execute`：fixed_company_scoped_native_account_transfer_model_action_disable
- `verify`：same_transaction_active_disabled_state_reread_and_response_schema_validation
- `idempotency`：target_disabled_state_recheck_without_operation_store
- `reverse`：account.transfer_model.enable

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover confirmation, company scope, native action_disable behavior, replay, result validation, registry schemas, and CLI dispatch.；引用：tests/unit/test_account_transfer_model_writes_public.py, tests/unit/test_account_transfer_model_writes_runtime.py
- `integration`：`implemented`；Guarded shared live smoke passed both isolated aliases as uid 5 with su=False, exercising this command and its immediate replay except delete; outer rollback plus a fresh cursor proved model, line, move, and temporary group residue absent.；引用：tests/integration/test_account_transfer_model_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-transfer_model-duplicate"></a>

## account.transfer_model.duplicate — 复制科目转结模型

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`concurrent_idempotency_limit` — The handler can recheck an exact company-scoped named copy, but Odoo provides no matching request-id uniqueness constraint for concurrent exactly-once duplication.
- 内部domain：`period_close`；来源模型：res.company, account.journal, account.account, account.transfer.model, account.transfer.model.line；向导：无。
- 必需模块：account_transfer, account_accountant, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.journal:read, account.account:read, account.transfer.model:read, account.transfer.model:create, account.transfer.model:write, account.transfer.model.line:read, account.transfer.model.line:create。
- 请求/响应合同：`schemas/v1/account.transfer_model.duplicate.request.schema.json` / `schemas/v1/account.transfer_model.duplicate.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run account.transfer_model.duplicate --request "@request.json" --idempotency-key "account.transfer_model.duplicate:1:0ce111a2b08b7f397746d80f4419fdc0" --confirm "account.transfer_model.duplicate"
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
    "transfer_model_id": 1,
    "name": "Example"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transfer_model_id","name"]} |
| parameters.transfer_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":256,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"account.transfer_model.duplicate"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"account.transfer_model.duplicate"} |
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
- `execute`：fixed_company_scoped_native_account_transfer_model_copy
- `verify`：same_transaction_distinct_disabled_copy_and_lines_reread_and_response_schema_validation
- `idempotency`：source_name_and_copied_configuration_natural_key_recheck_without_concurrent_exactly_once_guarantee
- `reverse`：account.transfer_model.delete_when_never_run

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the exact duplicate contract, native copy boundary, source attribution, result validation, registry schemas, and CLI dispatch.；引用：tests/unit/test_account_transfer_model_writes_public.py, tests/unit/test_account_transfer_model_writes_runtime.py
- `integration`：`implemented`；Guarded shared live smoke passed both isolated aliases as uid 5 with su=False, exercising this command and its immediate replay except delete; outer rollback plus a fresh cursor proved model, line, move, and temporary group residue absent.；引用：tests/integration/test_account_transfer_model_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-transfer_model-enable"></a>

## account.transfer_model.enable — 启用科目转结模型

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed native action_enable handler is registered; availability depends on runtime configuration, company scope, a complete active model, and accounting-manager access.
- 内部domain：`period_close`；来源模型：res.company, account.journal, account.account, account.transfer.model, account.transfer.model.line；向导：无。
- 必需模块：account_transfer, account_accountant, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.journal:read, account.account:read, account.transfer.model:read, account.transfer.model:write, account.transfer.model.line:read。
- 请求/响应合同：`schemas/v1/account.transfer_model.enable.request.schema.json` / `schemas/v1/account.transfer_model.enable.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run account.transfer_model.enable --request "@request.json" --idempotency-key "account.transfer_model.enable:1" --confirm "account.transfer_model.enable"
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
    "transfer_model_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transfer_model_id"]} |
| parameters.transfer_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"account.transfer_model.enable"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"account.transfer_model.enable"} |
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
- `execute`：fixed_company_scoped_native_account_transfer_model_action_enable
- `verify`：same_transaction_active_in_progress_state_reread_and_response_schema_validation
- `idempotency`：target_in_progress_state_recheck_without_operation_store
- `reverse`：account.transfer_model.disable

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover confirmation, company scope, complete-model guardrails, native action_enable behavior, replay, result validation, registry schemas, and CLI dispatch.；引用：tests/unit/test_account_transfer_model_writes_public.py, tests/unit/test_account_transfer_model_writes_runtime.py
- `integration`：`implemented`；Guarded shared live smoke passed both isolated aliases as uid 5 with su=False, exercising this command and its immediate replay except delete; outer rollback plus a fresh cursor proved model, line, move, and temporary group residue absent.；引用：tests/integration/test_account_transfer_model_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-transfer_model-get"></a>

## account.transfer_model.get — 读取会计科目转结模型

- 类型：只读；静态状态：`unconfigured`；handler：`account_transfer_model_get`。
- 状态原因：`runtime_context_required` — The fixed read handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`period_close`；来源模型：res.company, account.transfer.model, account.transfer.model.line, account.journal, account.account, account.move；向导：无。
- 必需模块：account_transfer, account_accountant, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.transfer.model:read, account.transfer.model.line:read, account.journal:read, account.account:read, account.move:read。
- 请求/响应合同：`schemas/v1/account.transfer_model.get.request.schema.json` / `schemas/v1/account.transfer_model.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read account.transfer_model.get --request "@request.json"
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
    "transfer_model_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transfer_model_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.transfer_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"account.transfer_model.search.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"account.transfer_model.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"account.transfer_model.search.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","active","state","company_id","journal","date_start","date_stop","frequency","origin_accounts","destination_lines","move_ids_count","has_draft_moves","total_percent"],"resolved_ref":"account.transfer_model.search.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["disabled","in_progress"]} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.date_start | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.date_stop | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.frequency | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["month","quarter","year"]} |
| response.data.origin_accounts | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.origin_accounts[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.origin_accounts[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.origin_accounts[].code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.origin_accounts[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.destination_lines | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.destination_lines[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","sequence","account","percentage"],"resolved_ref":"#/$defs/destination_line"} |
| response.data.destination_lines[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.destination_lines[].sequence | integer | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.destination_lines[].account | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.destination_lines[].account.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.destination_lines[].account.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.destination_lines[].account.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.destination_lines[].percentage | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.move_ids_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.has_draft_moves | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.total_percent | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"account.transfer_model.search.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","active","state","company_id","journal","date_start","date_stop","frequency","origin_accounts","destination_lines","move_ids_count","has_draft_moves","total_percent"],"resolved_ref":"account.transfer_model.search.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["disabled","in_progress"]} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.date_start | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.date_stop | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.frequency | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["month","quarter","year"]} |
| response.data.origin_accounts | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.origin_accounts[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.origin_accounts[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.origin_accounts[].code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.origin_accounts[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.destination_lines | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.destination_lines[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","sequence","account","percentage"],"resolved_ref":"#/$defs/destination_line"} |
| response.data.destination_lines[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.destination_lines[].sequence | integer | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.destination_lines[].account | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.destination_lines[].account.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.destination_lines[].account.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.destination_lines[].account.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.destination_lines[].percentage | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.move_ids_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.has_draft_moves | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.total_percent | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
- `execute`：fixed_company_scoped_account_transfer_model_get
- `verify`：same_transaction_acl_company_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared focused test covers registry metadata, fixed CLI routing, model mapping, and exclusion of inventory capabilities.；引用：tests/unit/test_accounting_operational_reads_registry_cli.py
- `integration`：`implemented`；The shared ordinary-accounting-user read-only smoke passed for all twelve capabilities on both dedicated isolated database aliases.；引用：tests/integration/test_accounting_operational_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-transfer_model-restore"></a>

## account.transfer_model.restore — 恢复科目转结模型

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed native action_unarchive handler is registered; availability depends on runtime configuration, company-scoped transfer data, archived state, and accounting-manager access.
- 内部domain：`period_close`；来源模型：res.company, account.journal, account.account, account.transfer.model, account.transfer.model.line；向导：无。
- 必需模块：account_transfer, account_accountant, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.journal:read, account.account:read, account.transfer.model:read, account.transfer.model:write, account.transfer.model.line:read。
- 请求/响应合同：`schemas/v1/account.transfer_model.restore.request.schema.json` / `schemas/v1/account.transfer_model.restore.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run account.transfer_model.restore --request "@request.json" --idempotency-key "account.transfer_model.restore:1" --confirm "account.transfer_model.restore"
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
    "transfer_model_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transfer_model_id"]} |
| parameters.transfer_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"account.transfer_model.restore"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"account.transfer_model.restore"} |
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
- `execute`：fixed_company_scoped_native_account_transfer_model_action_unarchive
- `verify`：same_transaction_active_disabled_state_reread_and_response_schema_validation
- `idempotency`：target_restored_disabled_state_recheck_without_operation_store
- `reverse`：account.transfer_model.archive

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover confirmation, company scope, native action_unarchive behavior, disabled restored state, replay, result validation, registry schemas, and CLI dispatch.；引用：tests/unit/test_account_transfer_model_writes_public.py, tests/unit/test_account_transfer_model_writes_runtime.py
- `integration`：`implemented`；Guarded shared live smoke passed both isolated aliases as uid 5 with su=False, exercising this command and its immediate replay except delete; outer rollback plus a fresh cursor proved model, line, move, and temporary group residue absent.；引用：tests/integration/test_account_transfer_model_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-transfer_model-search"></a>

## account.transfer_model.search — 搜索会计科目转结模型

- 类型：只读；静态状态：`unconfigured`；handler：`account_transfer_model_search`。
- 状态原因：`runtime_context_required` — The fixed read handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`period_close`；来源模型：res.company, account.transfer.model, account.transfer.model.line, account.journal, account.account, account.move；向导：无。
- 必需模块：account_transfer, account_accountant, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.transfer.model:read, account.transfer.model.line:read, account.journal:read, account.account:read, account.move:read。
- 请求/响应合同：`schemas/v1/account.transfer_model.search.request.schema.json` / `schemas/v1/account.transfer_model.search.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read account.transfer_model.search --request "@request.json"
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
| parameters.query | string/null | 可选（可能有条件限制） |  | 搜索文本 | {"default":null,"maxLength":200,"minLength":1,"pattern":"^(?:\\S&#124;\\S(?:.&#124;\\n)*\\S)$"} |
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"account.transfer_model.search"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","active","state","company_id","journal","date_start","date_stop","frequency","origin_accounts","destination_lines","move_ids_count","has_draft_moves","total_percent"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | oneOf[2] | 状态 | {"enum":["disabled","in_progress"]} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].date_start | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].date_stop | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.items[].frequency | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["month","quarter","year"]} |
| response.data.items[].origin_accounts | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.items[].origin_accounts[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].origin_accounts[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].origin_accounts[].code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].origin_accounts[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].destination_lines | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[].destination_lines[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","sequence","account","percentage"],"resolved_ref":"#/$defs/destination_line"} |
| response.data.items[].destination_lines[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].destination_lines[].sequence | integer | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].destination_lines[].account | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].destination_lines[].account.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].destination_lines[].account.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.items[].destination_lines[].account.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].destination_lines[].percentage | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].move_ids_count | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":0} |
| response.data.items[].has_draft_moves | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].total_percent | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","active","state","company_id","journal","date_start","date_stop","frequency","origin_accounts","destination_lines","move_ids_count","has_draft_moves","total_percent"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].state | 未限定 | 必填（所在对象出现时） | allOf[1]/then | 状态 | {"enum":["disabled","in_progress"]} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].date_start | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].date_stop | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.items[].frequency | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["month","quarter","year"]} |
| response.data.items[].origin_accounts | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000,"uniqueItems":true} |
| response.data.items[].origin_accounts[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].origin_accounts[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].origin_accounts[].code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].origin_accounts[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].destination_lines | array | 必填（所在对象出现时） | allOf[1]/then |  | {"maxItems":1000} |
| response.data.items[].destination_lines[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","sequence","account","percentage"],"resolved_ref":"#/$defs/destination_line"} |
| response.data.items[].destination_lines[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].destination_lines[].sequence | integer | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].destination_lines[].account | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/coded"} |
| response.data.items[].destination_lines[].account.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].destination_lines[].account.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.items[].destination_lines[].account.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].destination_lines[].percentage | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].move_ids_count | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":0} |
| response.data.items[].has_draft_moves | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].total_percent | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
- `execute`：fixed_company_scoped_account_transfer_model_search
- `verify`：same_transaction_acl_cursor_company_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；The shared focused test covers registry metadata, fixed CLI routing, model mapping, and exclusion of inventory capabilities.；引用：tests/unit/test_accounting_operational_reads_registry_cli.py
- `integration`：`implemented`；The shared ordinary-accounting-user read-only smoke passed for all twelve capabilities on both dedicated isolated database aliases.；引用：tests/integration/test_accounting_operational_reads_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-account-transfer_model-update"></a>

## account.transfer_model.update — 更新科目转结模型

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is registered; availability depends on runtime configuration, company-scoped transfer data, disabled state, and accounting-manager access.
- 内部domain：`period_close`；来源模型：res.company, account.journal, account.account, account.transfer.model, account.transfer.model.line；向导：无。
- 必需模块：account_transfer, account_accountant, account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.journal:read, account.account:read, account.transfer.model:read, account.transfer.model:write, account.transfer.model.line:read, account.transfer.model.line:create, account.transfer.model.line:write, account.transfer.model.line:unlink。
- 请求/响应合同：`schemas/v1/account.transfer_model.update.request.schema.json` / `schemas/v1/account.transfer_model.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run account.transfer_model.update --request "@request.json" --idempotency-key "account.transfer_model.update:1:663c40c5fc625d44d00a597ae77ce292" --confirm "account.transfer_model.update"
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
    "transfer_model_id": 1,
    "changes": {
      "name": "Example"
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transfer_model_id","changes"]} |
| parameters.transfer_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.name | string | 可选（可能有条件限制） |  | 名称/行说明 | {"maxLength":256,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","resolved_ref":"#/$defs/text256"} |
| parameters.changes.journal_id | integer | 可选（可能有条件限制） |  | 日记账ID | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.changes.date_start | string | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.changes.date_stop | string/null | 可选（可能有条件限制） |  |  | {"format":"date"} |
| parameters.changes.frequency | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["month","quarter","year"]} |
| parameters.changes.origin_account_ids | array | 可选（可能有条件限制） |  |  | {"maxItems":1000,"minItems":1,"resolved_ref":"#/$defs/idList","uniqueItems":true} |
| parameters.changes.origin_account_ids[] | integer | 每个数组元素 |  |  | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.changes.destination_lines | array | 可选（可能有条件限制） |  |  | {"maxItems":1000,"minItems":1,"resolved_ref":"#/$defs/destinationLines","uniqueItems":true} |
| parameters.changes.destination_lines[] | object | 每个数组元素 |  |  | {"additionalProperties":false,"required_in_object":["account_id","percentage"],"resolved_ref":"#/$defs/destinationLine"} |
| parameters.changes.destination_lines[].account_id | integer | 必填（所在对象出现时） |  | 会计科目ID | {"minimum":1,"resolved_ref":"#/$defs/id"} |
| parameters.changes.destination_lines[].percentage | string | 必填（所在对象出现时） |  |  | {"maxLength":9,"pattern":"^(?:100&#124;(?:[1-9]&#124;[1-9][0-9])(?:\\.[0-9]{0,5}[1-9])?&#124;0\\.[0-9]{0,5}[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/positivePercentage"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"account.transfer_model.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"account.transfer_model.update"} |
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
- `execute`：fixed_company_scoped_disabled_account_transfer_model_update
- `verify`：same_transaction_updated_model_lines_and_state_reread_and_response_schema_validation
- `idempotency`：target_state_recheck_without_operation_store_or_protection_from_intermediate_changes
- `reverse`：account.transfer_model.update_with_prior_values

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the nonempty changes contract, company-scoped references and disabled-state guard, result validation, registry schemas, and CLI dispatch.；引用：tests/unit/test_account_transfer_model_writes_public.py, tests/unit/test_account_transfer_model_writes_runtime.py
- `integration`：`implemented`；Guarded shared live smoke passed both isolated aliases as uid 5 with su=False, exercising this command and its immediate replay except delete; outer rollback plus a fresh cursor proved model, line, move, and temporary group residue absent.；引用：tests/integration/test_account_transfer_model_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-company-fiscal_year-resolve"></a>

## company.fiscal_year.resolve — 解析公司财政年度

- 类型：只读；静态状态：`unconfigured`；handler：`company_fiscal_year_resolve`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`accounting_context`；来源模型：res.company, account.fiscal.year；向导：无。
- 必需模块：account, account_accountant；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.fiscal.year:read。
- 请求/响应合同：`schemas/v1/company.fiscal_year.resolve.request.schema.json` / `schemas/v1/company.fiscal_year.resolve.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read company.fiscal_year.resolve --request "@request.json"
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
    "date": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["date"]} |
| parameters.date | string | 必填（所在对象出现时） |  |  | {"format":"date"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"company.fiscal_year.resolve"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["company_id","date","date_from","date_to","fiscal_year"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.date_from | string | 必填（所在对象出现时） | oneOf[2] | 开始日期 | {"format":"date"} |
| response.data.date_to | string | 必填（所在对象出现时） | oneOf[2] | 结束日期 | {"format":"date"} |
| response.data.fiscal_year | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/fiscal_year"}]} |
| response.data.fiscal_year | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.fiscal_year | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/fiscal_year"} |
| response.data.fiscal_year.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.fiscal_year.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["company_id","date","date_from","date_to","fiscal_year"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.date_from | string | 必填（所在对象出现时） | allOf[1]/then | 开始日期 | {"format":"date"} |
| response.data.date_to | string | 必填（所在对象出现时） | allOf[1]/then | 结束日期 | {"format":"date"} |
| response.data.fiscal_year | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/fiscal_year"}]} |
| response.data.fiscal_year | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.fiscal_year | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/fiscal_year"} |
| response.data.fiscal_year.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.fiscal_year.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
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
- `execute`：fixed_native_company_fiscal_year_resolution
- `verify`：same_transaction_acl_result_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed date request, native fiscal-year resolution, company scope, and bridge response.；引用：tests/unit/test_period_context.py, tests/unit/test_period_context_runtime.py
- `integration`：`implemented`；The shared read-only smoke verifies the capability in both dedicated isolated database aliases.；引用：tests/integration/test_management_reporting_period_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-company-fiscal_year_end-update"></a>

## company.fiscal_year_end.update — 修改公司会计年度结束日

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — Fixed current-company settings are implemented; native company write requires access-rights administration and reference ACLs. Ordinary accountant permission is not implied.
- 内部domain：`accounting_configuration`；来源模型：ir.default, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：base.group_erp_manager；ACL：ir.default:read, res.company:read, res.company:write。
- 请求/响应合同：`schemas/v1/company.fiscal_year_end.update.request.schema.json` / `schemas/v1/company.fiscal_year_end.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run company.fiscal_year_end.update --request "@request.json" --idempotency-key "company.fiscal_year_end.update:1:51fe7b6d3297add7fd1ab266302d6ac7" --confirm "company.fiscal_year_end.update"
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
      "fiscalyear_last_day": 1
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["changes"]} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.fiscalyear_last_day | integer | 可选（可能有条件限制） |  |  | {"maximum":31,"minimum":1} |
| parameters.changes.fiscalyear_last_month | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["1","10","11","12","2","3","4","5","6","7","8","9"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"company.fiscal_year_end.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"company.fiscal_year_end.update"} |
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

<a id="cap-company-lock_dates-inspect"></a>

## company.lock_dates.inspect — 检查公司会计锁定日期

- 类型：只读；静态状态：`unconfigured`；handler：`company_lock_dates_inspect`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`accounting_context`；来源模型：res.company；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read。
- 请求/响应合同：`schemas/v1/company.lock_dates.inspect.request.schema.json` / `schemas/v1/company.lock_dates.inspect.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read company.lock_dates.inspect --request "@request.json"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"company.lock_dates.inspect"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["company_id","configured","effective"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.configured | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["fiscalyear_lock_date","tax_lock_date","sale_lock_date","purchase_lock_date","hard_lock_date"],"resolved_ref":"#/$defs/locks"} |
| response.data.configured.fiscalyear_lock_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.configured.tax_lock_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.configured.sale_lock_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.configured.purchase_lock_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.configured.hard_lock_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.effective | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["fiscalyear_lock_date","tax_lock_date","sale_lock_date","purchase_lock_date","hard_lock_date"],"resolved_ref":"#/$defs/locks"} |
| response.data.effective.fiscalyear_lock_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.effective.tax_lock_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.effective.sale_lock_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.effective.purchase_lock_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.effective.hard_lock_date | string/null | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["company_id","configured","effective"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.configured | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["fiscalyear_lock_date","tax_lock_date","sale_lock_date","purchase_lock_date","hard_lock_date"],"resolved_ref":"#/$defs/locks"} |
| response.data.configured.fiscalyear_lock_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.configured.tax_lock_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.configured.sale_lock_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.configured.purchase_lock_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.configured.hard_lock_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.effective | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["fiscalyear_lock_date","tax_lock_date","sale_lock_date","purchase_lock_date","hard_lock_date"],"resolved_ref":"#/$defs/locks"} |
| response.data.effective.fiscalyear_lock_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.effective.tax_lock_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.effective.sale_lock_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.effective.purchase_lock_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.effective.hard_lock_date | string/null | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
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
- `execute`：fixed_company_scoped_native_lock_date_inspection
- `verify`：same_transaction_acl_result_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request, company scope, ACL gates, date normalization, and bridge response.；引用：tests/unit/test_period_context.py, tests/unit/test_period_context_runtime.py
- `integration`：`implemented`；The shared read-only smoke verifies the capability in both dedicated isolated database aliases.；引用：tests/integration/test_management_reporting_period_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-fiscal_year-create"></a>

## fiscal_year.create — 创建会计年度

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`concurrent_idempotency_limit` — The handler replays the company-and-date-range natural key, but Odoo has no matching database uniqueness constraint for concurrent exactly-once creation.
- 内部domain：`accounting_context`；来源模型：res.company, account.fiscal.year；向导：无。
- 必需模块：account_accountant；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.fiscal.year:read, account.fiscal.year:create。
- 请求/响应合同：`schemas/v1/fiscal_year.create.request.schema.json` / `schemas/v1/fiscal_year.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run fiscal_year.create --request "@request.json" --idempotency-key "fiscal_year.create:1:be31044791c600d1e5d2bf0cb06b4ee7" --confirm "fiscal_year.create"
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
    "date_from": "2026-10-01",
    "date_to": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["name","date_from","date_to"]} |
| parameters.name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":256,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$","resolved_ref":"#/$defs/text"} |
| parameters.date_from | string | 必填（所在对象出现时） |  | 开始日期 | {"format":"date"} |
| parameters.date_to | string | 必填（所在对象出现时） |  | 结束日期 | {"format":"date"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"fiscal_year.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"fiscal_year.create"} |
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
- `execute`：fixed_company_scoped_fiscal_year_create
- `verify`：same_transaction_record_reread_and_response_schema_validation
- `idempotency`：company_and_exact_date_range_natural_key_recheck_without_concurrent_exactly_once_guarantee
- `reverse`：not_exposed_in_this_batch

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover the closed contract, company scope, source constraints, replay, runtime dispatch, schemas, and registry metadata.；引用：tests/unit/test_core_writes.py, tests/unit/test_accounting_rules_fiscal_year_contracts.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_accounting_rules_fiscal_year_registry.py
- `integration`：`implemented`；The guarded shared transactional smoke passed on both dedicated isolated database aliases with first execution, immediate replay, API/ORM readback, and transaction/temporary-group rollback verification.；引用：tests/integration/test_accounting_rules_fiscal_year_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-fiscal_year-get"></a>

## fiscal_year.get — 获取财政年度详情

- 类型：只读；静态状态：`unconfigured`；handler：`fiscal_year_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`accounting_context`；来源模型：res.company, account.fiscal.year；向导：无。
- 必需模块：account_accountant；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.fiscal.year:read。
- 请求/响应合同：`schemas/v1/fiscal_year.get.request.schema.json` / `schemas/v1/fiscal_year.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read fiscal_year.get --request "@request.json"
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
    "fiscal_year_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["fiscal_year_id"]} |
| parameters.fiscal_year_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"fiscal_year.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","company_id","date_from","date_to"],"resolved_ref":"#/$defs/data"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.date_from | string | 必填（所在对象出现时） | oneOf[2] | 开始日期 | {"format":"date"} |
| response.data.date_to | string | 必填（所在对象出现时） | oneOf[2] | 结束日期 | {"format":"date"} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","company_id","date_from","date_to"],"resolved_ref":"#/$defs/data"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.date_from | string | 必填（所在对象出现时） | allOf[1]/then | 开始日期 | {"format":"date"} |
| response.data.date_to | string | 必填（所在对象出现时） | allOf[1]/then | 结束日期 | {"format":"date"} |
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
- `execute`：fixed_company_scoped_fiscal_year_get
- `verify`：same_transaction_acl_result_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed identifier request, explicit company scope, ACL gates, and normalization.；引用：tests/unit/test_period_context.py, tests/unit/test_period_context_runtime.py
- `integration`：`implemented`；The shared rollback smoke verifies company-scoped fiscal-year reads in both dedicated isolated database aliases.；引用：tests/integration/test_management_reporting_period_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-fiscal_year-search"></a>

## fiscal_year.search — 搜索财政年度

- 类型：只读；静态状态：`unconfigured`；handler：`fiscal_year_search`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`accounting_context`；来源模型：res.company, account.fiscal.year；向导：无。
- 必需模块：account_accountant；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.fiscal.year:read。
- 请求/响应合同：`schemas/v1/fiscal_year.search.request.schema.json` / `schemas/v1/fiscal_year.search.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read fiscal_year.search --request "@request.json"
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
| parameters.contains_date | string/null | 可选（可能有条件限制） |  |  | {"default":null,"format":"date"} |
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"fiscal_year.search"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","company_id","date_from","date_to"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].date_from | string | 必填（所在对象出现时） | oneOf[2] | 开始日期 | {"format":"date"} |
| response.data.items[].date_to | string | 必填（所在对象出现时） | oneOf[2] | 结束日期 | {"format":"date"} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","company_id","date_from","date_to"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].date_from | string | 必填（所在对象出现时） | allOf[1]/then | 开始日期 | {"format":"date"} |
| response.data.items[].date_to | string | 必填（所在对象出现时） | allOf[1]/then | 结束日期 | {"format":"date"} |
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
- `execute`：fixed_company_scoped_fiscal_year_search
- `verify`：same_transaction_acl_result_cursor_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover closed filters, explicit company scope, keyset pagination, ACL gates, and normalization.；引用：tests/unit/test_period_context.py, tests/unit/test_period_context_runtime.py
- `integration`：`implemented`；The shared rollback smoke verifies company-scoped fiscal-year reads in both dedicated isolated database aliases.；引用：tests/integration/test_management_reporting_period_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-fiscal_year-update"></a>

## fiscal_year.update — 更新会计年度

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`accounting_context`；来源模型：res.company, account.fiscal.year；向导：无。
- 必需模块：account_accountant；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:read, account.fiscal.year:read, account.fiscal.year:write。
- 请求/响应合同：`schemas/v1/fiscal_year.update.request.schema.json` / `schemas/v1/fiscal_year.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run fiscal_year.update --request "@request.json" --idempotency-key "fiscal_year.update:1:663c40c5fc625d44d00a597ae77ce292" --confirm "fiscal_year.update"
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
    "id": 1,
    "changes": {
      "name": "Example"
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["id","changes"]} |
| parameters.id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.name | string | 可选（可能有条件限制） |  | 名称/行说明 | {"maxLength":256,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$","resolved_ref":"#/$defs/text"} |
| parameters.changes.date_from | string | 可选（可能有条件限制） |  | 开始日期 | {"format":"date"} |
| parameters.changes.date_to | string | 可选（可能有条件限制） |  | 结束日期 | {"format":"date"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"fiscal_year.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"fiscal_year.update"} |
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
- `execute`：fixed_company_scoped_fiscal_year_update
- `verify`：same_transaction_record_reread_and_response_schema_validation
- `idempotency`：target_state_recheck_without_operation_store
- `reverse`：update_with_previous_values

### 已登记测试与证据范围

- `unit`：`implemented`；Focused unit tests cover the closed contract, company scope, source constraints, replay, runtime dispatch, schemas, and registry metadata.；引用：tests/unit/test_core_writes.py, tests/unit/test_accounting_rules_fiscal_year_contracts.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_accounting_rules_fiscal_year_registry.py
- `integration`：`implemented`；The guarded shared transactional smoke passed on both dedicated isolated database aliases with first execution, immediate replay, API/ORM readback, and transaction/temporary-group rollback verification.；引用：tests/integration/test_accounting_rules_fiscal_year_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-journal-accounting_date-resolve"></a>

## journal.accounting_date.resolve — 解析日记账实际入账日期

- 类型：只读；静态状态：`unconfigured`；handler：`journal_accounting_date_resolve`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`period_close`；来源模型：account.journal, res.company；向导：无。
- 必需模块：account, base；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：account.journal:read, res.company:read。
- 请求/响应合同：`schemas/v1/journal.accounting_date.resolve.request.schema.json` / `schemas/v1/journal.accounting_date.resolve.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read journal.accounting_date.resolve --request "@request.json"
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
    "date": "2026-10-31",
    "has_tax": false
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["journal_id","date","has_tax"]} |
| parameters.journal_id | integer | 必填（所在对象出现时） |  | 日记账ID | {"minimum":1} |
| parameters.date | string | 必填（所在对象出现时） |  |  | {"format":"date"} |
| parameters.has_tax | boolean | 必填（所在对象出现时） |  |  |  |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"journal.accounting_date.resolve"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["company_id","journal","requested_date","has_tax","accounting_date","adjusted"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.journal | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/journal"} |
| response.data.journal.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.requested_date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.has_tax | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.accounting_date | string | 必填（所在对象出现时） | oneOf[2] |  | {"format":"date"} |
| response.data.adjusted | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["company_id","journal","requested_date","has_tax","accounting_date","adjusted"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.journal | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/journal"} |
| response.data.journal.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.journal.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.journal.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.requested_date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.has_tax | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.accounting_date | string | 必填（所在对象出现时） | allOf[1]/then |  | {"format":"date"} |
| response.data.adjusted | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
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
- `execute`：native_company_scoped_journal_accounting_date_compute
- `verify`：read_only_transaction_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the fixed journal/date/tax context, native computed field mapping, company scope, schema, and CLI dispatch.；引用：tests/unit/test_journal_analysis.py, tests/unit/test_journal_analysis_runtime.py, tests/unit/test_return_journal_analysis_cli.py
- `integration`：`implemented`；The shared guarded smoke compares the capability with the native journal accounting-date field in both isolated databases.；引用：tests/integration/test_return_journal_analysis_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-localization-china-period_transfer-run"></a>

## localization.china.period_transfer.run — 运行中国月末损益结转

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`odoo_transfer_marker_not_concurrency_unique` — The command is implemented with a visible deterministic move marker, but Odoo has no native unique operation key for concurrent transfer execution.
- 内部domain：`localization_china`；来源模型：res.company, res.country, account.transfer.model, account.transfer.model.line, account.move, account.move.line；向导：无。
- 必需模块：l10n_cn_reports, account_transfer；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：res.country:read, account.transfer.model:read, account.transfer.model.line:read, account.move:read, account.move:create, account.move:write, account.move.line:read, account.move.line:create, account.move.line:write, account.move.line:unlink。
- 请求/响应合同：`schemas/v1/localization.china.period_transfer.run.request.schema.json` / `schemas/v1/localization.china.period_transfer.run.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run localization.china.period_transfer.run --request "@request.json" --idempotency-key "localization.china.period_transfer.run:1:2026-10-31" --confirm "localization.china.period_transfer.run"
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
    "run_date": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  |  |
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["run_date"]} |
| parameters.run_date | string | 必填（所在对象出现时） |  |  | {"format":"date"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"localization.china.period_transfer.run"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"localization.china.period_transfer.run"} |
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
- `execute`：native_fixed_china_monthly_transfer_action_as_configured_business_user
- `verify`：generated_move_marker_balance_and_response_schema_validation
- `idempotency`：visible_odoo_move_marker_and_exact_parameter_replay
- `reverse`：journal_entry.reverse

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the fixed China transfer model and run date, marker replay, runtime action, result drift checks, and CLI response.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_core_write_cli.py, tests/unit/test_extended_core_writes.py
- `integration`：`implemented`；The guarded shared live smoke executed the public write contract and immediate replay in both dedicated isolated database aliases, then verified full transaction rollback with a fresh read-only cursor.；引用：tests/integration/test_extended_write_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-period-accrual-generate"></a>

## period.accrual.generate — 生成采购或销售预提分录

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`odoo_accrual_pair_not_concurrency_unique` — The native wizard path is implemented, but Odoo provides no database-unique operation key for concurrent exactly-once generation.
- 内部domain：`period_close`；来源模型：sale.order, purchase.order, account.journal, account.account, account.move, account.move.line；向导：account.accrued.orders.wizard。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：sale.order:read, purchase.order:read, account.accrued.orders.wizard:create, account.journal:read, account.account:read, account.move:create, account.move:read, account.move:write, account.move.line:read, account.move.line:create, account.move.line:write。
- 请求/响应合同：`schemas/v1/period.accrual.generate.request.schema.json` / `schemas/v1/period.accrual.generate.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run period.accrual.generate --request "@request.json" --idempotency-key "doc-example-operation-001" --confirm "period.accrual.generate"
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
    "source_model": "sale.order",
    "order_ids": [
      1
    ],
    "date": "2026-10-31",
    "reversal_date": "2026-11-01",
    "journal_id": 1,
    "accrual_account_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"if":{"required":["amount"]},"then":{"properties":{"order_ids":{"maxItems":1}}}}],"required_in_object":["source_model","order_ids","date","reversal_date","journal_id","accrual_account_id"]} |
| parameters.source_model | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["sale.order","purchase.order"]} |
| parameters.order_ids | array | 必填（所在对象出现时） |  |  | {"minItems":1,"uniqueItems":true} |
| parameters.order_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.date | string | 必填（所在对象出现时） |  |  | {"format":"date"} |
| parameters.reversal_date | string | 必填（所在对象出现时） |  |  | {"format":"date"} |
| parameters.journal_id | integer | 必填（所在对象出现时） |  | 日记账ID | {"minimum":1} |
| parameters.accrual_account_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.amount | string | 可选（可能有条件限制） |  | 十进制数值；金额、固定税额或税率按所在业务对象解释 | {"maxLength":256,"pattern":"^(?:[1-9][0-9]*(?:\\.[0-9]*[1-9])?&#124;0\\.[0-9]*[1-9])$(?![\\s\\S])","resolved_ref":"#/$defs/positive_decimal"} |
| parameters | 组合/开放结构 | 分支约束 | allOf[1] |  | {"if":{"required":["amount"]},"then":{"properties":{"order_ids":{"maxItems":1}}}} |
| parameters | 未限定 | 条件分支 | allOf[1]/then |  |  |
| parameters.order_ids | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"maxItems":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"period.accrual.generate"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"period.accrual.generate"} |
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
- `execute`：native_accrued_orders_wizard_as_configured_business_user
- `verify`：same_transaction_accrual_and_reversal_move_reread_and_response_schema_validation
- `idempotency`：deterministic_request_key_and_generated_move_pair_reread_without_database_uniqueness
- `reverse`：journal_entry.reverse

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed accrual contract, native wizard runtime, schemas, and CLI dispatch.；引用：tests/unit/test_procurement_inventory_writes.py, tests/unit/test_payment_term_accrual_writes_runtime.py, tests/unit/test_payment_term_accrual_write_schemas.py, tests/unit/test_core_write_cli.py
- `integration`：`implemented`；The guarded shared transactional smoke verifies native accrual generation and rollback in both isolated databases.；引用：tests/integration/test_accounting_followup_write_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-period-adjustment-create"></a>

## period.adjustment.create — 创建期末调整分录

- 类型：写入；静态状态：`disabled`；handler：`None`。
- 状态原因：`implementation_pending` — The capability is frozen in the G3 matrix but has no implementation or allowlisted handler.
- 内部domain：`period_close`；来源模型：account.move, account.move.line；向导：account.automatic.entry.wizard。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping, write_approval_policy, audit_store；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.automatic.entry.wizard:create, account.move:create, account.move:read。
- 请求/响应合同：`schemas/v1/request.schema.json` / `schemas/v1/response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run period.adjustment.create --request "@request.json" --idempotency-key "RECOMPUTE_FOR_ACTUAL_REQUEST" --confirm "period.adjustment.create"
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
- `reverse`：journal_entry.reverse

### 已登记测试与证据范围

- `unit`：`planned`；The unit definition is frozen; implementation evidence is pending.；引用：无
- `integration`：`planned`；The integration definition is frozen; implementation evidence is pending.；引用：无
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-period-lock-change"></a>

## period.lock.change — 变更会计锁定日期

- 类型：写入；静态状态：`disabled`；handler：`None`。
- 状态原因：`implementation_pending` — The capability is frozen in the G3 matrix but has no implementation or allowlisted handler.
- 内部domain：`period_close`；来源模型：res.company, account.lock_exception；向导：account.change.lock.date。
- 必需模块：account_accountant, account_reports；配置项：database_alias, company_allowlist, user_mapping, write_approval_policy, audit_store；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：res.company:write, res.company:read, account.lock_exception:create。
- 请求/响应合同：`schemas/v1/request.schema.json` / `schemas/v1/response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run period.lock.change --request "@request.json" --idempotency-key "RECOMPUTE_FOR_ACTUAL_REQUEST" --confirm "period.lock.change"
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
- `reverse`：change_lock_date_with_a_new_approved_plan

### 已登记测试与证据范围

- `unit`：`planned`；The unit definition is frozen; implementation evidence is pending.；引用：无
- `integration`：`planned`；The integration definition is frozen; implementation evidence is pending.；引用：无
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-period-transfer-run"></a>

## period.transfer.run — 运行期间科目结转

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`odoo_transfer_marker_not_concurrency_unique` — The command is implemented with a visible deterministic move marker, but Odoo has no native unique operation key for concurrent transfer execution.
- 内部domain：`period_close`；来源模型：res.company, account.transfer.model, account.transfer.model.line, account.move, account.move.line；向导：无。
- 必需模块：account_transfer；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_user；ACL：account.transfer.model:read, account.transfer.model.line:read, account.move:read, account.move:create, account.move:write, account.move.line:read, account.move.line:create, account.move.line:write, account.move.line:unlink。
- 请求/响应合同：`schemas/v1/period.transfer.run.request.schema.json` / `schemas/v1/period.transfer.run.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run period.transfer.run --request "@request.json" --idempotency-key "period.transfer.run:1:2026-10-31" --confirm "period.transfer.run"
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
    "transfer_model_id": 1,
    "run_date": "2026-10-31"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  |  |
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["transfer_model_id","run_date"]} |
| parameters.transfer_model_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.run_date | string | 必填（所在对象出现时） |  |  | {"format":"date"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"period.transfer.run"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"period.transfer.run"} |
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
- `execute`：native_account_transfer_model_action_as_configured_business_user
- `verify`：generated_move_marker_balance_and_response_schema_validation
- `idempotency`：visible_odoo_move_marker_and_exact_parameter_replay
- `reverse`：journal_entry.reverse

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the exact transfer model and run date, marker replay, runtime action, result drift checks, and CLI response.；引用：tests/unit/test_core_writes.py, tests/unit/test_core_writes_bridge.py, tests/unit/test_core_writes_runtime.py, tests/unit/test_core_write_cli.py, tests/unit/test_extended_core_writes.py
- `integration`：`implemented`；The guarded shared live smoke executed the public write contract and immediate replay in both dedicated isolated database aliases, then verified full transaction rollback with a fresh read-only cursor.；引用：tests/integration/test_extended_write_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-validation-period_close-check"></a>

## validation.period_close.check — 验证期间结账就绪状态

- 类型：只读；静态状态：`disabled`；handler：`None`。
- 状态原因：`implementation_pending` — The capability is frozen in the G3 matrix but has no implementation or allowlisted handler.
- 内部domain：`validation`；来源模型：account.move, account.move.line, account.bank.statement.line, account.asset, res.company；向导：无。
- 必需模块：account, account_accountant, account_reports, account_asset；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_manager；ACL：account.move:read, account.move.line:read, account.bank.statement.line:read, account.asset:read, res.company:read。
- 请求/响应合同：`schemas/v1/request.schema.json` / `schemas/v1/response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read validation.period_close.check --request "@request.json"
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
