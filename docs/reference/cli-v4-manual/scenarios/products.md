# 产品、类别与会计默认值

维护产品及类别，查看和设置收入费用科目、默认销售采购税、成本和开票政策，解析实际适用科目，并查阅贸易术语。产品会计配置不是库存数量调整；模板共享政策及多变体限制须按单条接口说明核对。

[回到总说明书](../../CLI_V4_MANUAL.md) · [新会话使用指南](../USAGE_GUIDE.md)

<a id="cap-incoterm-get"></a>

## incoterm.get — 获取国际贸易术语详情

- 类型：只读；静态状态：`unconfigured`；handler：`incoterm_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`accounting_master_data`；来源模型：res.company, account.incoterms；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.incoterms:read。
- 请求/响应合同：`schemas/v1/incoterm.get.request.schema.json` / `schemas/v1/incoterm.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read incoterm.get --request "@request.json"
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
    "incoterm_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["incoterm_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.incoterm_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"incoterm.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"incoterm.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"incoterm.list.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name","active"],"resolved_ref":"incoterm.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"incoterm.list.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name","active"],"resolved_ref":"incoterm.list.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
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

<a id="cap-incoterm-list"></a>

## incoterm.list — 列出国际贸易术语

- 类型：只读；静态状态：`unconfigured`；handler：`incoterm_list`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`accounting_master_data`；来源模型：res.company, account.incoterms；向导：无。
- 必需模块：account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, account.incoterms:read。
- 请求/响应合同：`schemas/v1/incoterm.list.request.schema.json` / `schemas/v1/incoterm.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read incoterm.list --request "@request.json"
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"incoterm.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name","active"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code","name","active"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
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

<a id="cap-product-accounting_profile-get"></a>

## product.accounting_profile.get — 读取产品会计配置

- 类型：只读；静态状态：`unconfigured`；handler：`product_accounting_profile_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime. Optional invoice_policy and purchase_method are native template-shared policies affecting every variant and company, not company-dependent properties. Absent native addon fields project null on get and reject only explicit policy writes; policy-only updates accept visible shared/multi-variant templates.
- 内部domain：`accounting_master_data`；来源模型：res.company, product.product, product.template, product.category, account.account；向导：无。
- 必需模块：product；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：base.group_user；ACL：res.company:read, product.product:read, product.template:read, product.category:read, account.account:read。
- 请求/响应合同：`schemas/v1/product.accounting_profile.get.request.schema.json` / `schemas/v1/product.accounting_profile.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read product.accounting_profile.get --request "@request.json"
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
    "product_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["product_id"]} |
| parameters.product_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"product.accounting_profile.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["company_id","product","template","category","modules","accounts","valuation","cost_method"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.product | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","default_code","active","company_id","template_id"],"resolved_ref":"#/$defs/product"} |
| response.data.product.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.product.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.product.default_code | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}]} |
| response.data.product.default_code | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.product.default_code | string | 分支约束 | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.product.active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.product.company_id | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"oneOf":[{"type":"null"},{"minimum":1,"type":"integer"}],"resolved_ref":"#/$defs/nullable_company_id"} |
| response.data.product.company_id | null | 分支约束 | oneOf[2]/oneOf[1] | 所选公司ID |  |
| response.data.product.company_id | integer | 分支约束 | oneOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.product.template_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.template | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","company_id","category_id"],"resolved_ref":"#/$defs/template"} |
| response.data.template.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.template.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.template.company_id | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"oneOf":[{"type":"null"},{"minimum":1,"type":"integer"}],"resolved_ref":"#/$defs/nullable_company_id"} |
| response.data.template.company_id | null | 分支约束 | oneOf[2]/oneOf[1] | 所选公司ID |  |
| response.data.template.company_id | integer | 分支约束 | oneOf[2]/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.template.category_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.category | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","complete_name"],"resolved_ref":"#/$defs/category"} |
| response.data.category.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.category.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.category.complete_name | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
| response.data.modules | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["account","stock_account"],"resolved_ref":"#/$defs/modules"} |
| response.data.modules.account | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.modules.stock_account | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.accounts | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["income","expense","stock_valuation","stock_input","stock_output"],"resolved_ref":"#/$defs/accounts"} |
| response.data.accounts.income | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"oneOf":[{"properties":{"account":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]},"available":{"const":true},"reason_code":{"type":"null"}}},{"properties":{"account":{"type":"null"},"available":{"const":false},"reason_code":{"$ref":"#/$defs/unavailable_reason"}}}],"required_in_object":["available","reason_code","account"],"resolved_ref":"#/$defs/account_slot"} |
| response.data.accounts.income.available | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.accounts.income.reason_code | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/unavailable_reason"}]} |
| response.data.accounts.income.reason_code | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.income.reason_code | 未限定 | 分支约束 | oneOf[2]/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.income.account | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.income.account | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.income.account | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.income.account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.income.account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.income.account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.income | 未限定 | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.income.available | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  | {"const":true} |
| response.data.accounts.income.reason_code | null | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.income.account | 组合/开放结构 | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.income.account | null | 分支约束 | oneOf[2]/oneOf[1]/oneOf[1] |  |  |
| response.data.accounts.income.account | object | 分支约束 | oneOf[2]/oneOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.income.account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[1]/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.income.account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[1]/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.income.account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[1]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.income | 未限定 | 分支约束 | oneOf[2]/oneOf[2] |  |  |
| response.data.accounts.income.available | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  | {"const":false} |
| response.data.accounts.income.reason_code | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.income.account | null | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  |  |
| response.data.accounts.expense | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"oneOf":[{"properties":{"account":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]},"available":{"const":true},"reason_code":{"type":"null"}}},{"properties":{"account":{"type":"null"},"available":{"const":false},"reason_code":{"$ref":"#/$defs/unavailable_reason"}}}],"required_in_object":["available","reason_code","account"],"resolved_ref":"#/$defs/account_slot"} |
| response.data.accounts.expense.available | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.accounts.expense.reason_code | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/unavailable_reason"}]} |
| response.data.accounts.expense.reason_code | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.expense.reason_code | 未限定 | 分支约束 | oneOf[2]/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.expense.account | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.expense.account | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.expense.account | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.expense.account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.expense.account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.expense.account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.expense | 未限定 | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.expense.available | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  | {"const":true} |
| response.data.accounts.expense.reason_code | null | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.expense.account | 组合/开放结构 | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.expense.account | null | 分支约束 | oneOf[2]/oneOf[1]/oneOf[1] |  |  |
| response.data.accounts.expense.account | object | 分支约束 | oneOf[2]/oneOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.expense.account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[1]/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.expense.account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[1]/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.expense.account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[1]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.expense | 未限定 | 分支约束 | oneOf[2]/oneOf[2] |  |  |
| response.data.accounts.expense.available | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  | {"const":false} |
| response.data.accounts.expense.reason_code | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.expense.account | null | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  |  |
| response.data.accounts.stock_valuation | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"oneOf":[{"properties":{"account":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]},"available":{"const":true},"reason_code":{"type":"null"}}},{"properties":{"account":{"type":"null"},"available":{"const":false},"reason_code":{"$ref":"#/$defs/unavailable_reason"}}}],"required_in_object":["available","reason_code","account"],"resolved_ref":"#/$defs/account_slot"} |
| response.data.accounts.stock_valuation.available | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.accounts.stock_valuation.reason_code | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/unavailable_reason"}]} |
| response.data.accounts.stock_valuation.reason_code | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.stock_valuation.reason_code | 未限定 | 分支约束 | oneOf[2]/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.stock_valuation.account | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.stock_valuation.account | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.stock_valuation.account | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.stock_valuation.account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.stock_valuation.account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.stock_valuation.account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.stock_valuation | 未限定 | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.stock_valuation.available | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  | {"const":true} |
| response.data.accounts.stock_valuation.reason_code | null | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.stock_valuation.account | 组合/开放结构 | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.stock_valuation.account | null | 分支约束 | oneOf[2]/oneOf[1]/oneOf[1] |  |  |
| response.data.accounts.stock_valuation.account | object | 分支约束 | oneOf[2]/oneOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.stock_valuation.account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[1]/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.stock_valuation.account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[1]/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.stock_valuation.account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[1]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.stock_valuation | 未限定 | 分支约束 | oneOf[2]/oneOf[2] |  |  |
| response.data.accounts.stock_valuation.available | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  | {"const":false} |
| response.data.accounts.stock_valuation.reason_code | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.stock_valuation.account | null | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  |  |
| response.data.accounts.stock_input | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"oneOf":[{"properties":{"account":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]},"available":{"const":true},"reason_code":{"type":"null"}}},{"properties":{"account":{"type":"null"},"available":{"const":false},"reason_code":{"$ref":"#/$defs/unavailable_reason"}}}],"required_in_object":["available","reason_code","account"],"resolved_ref":"#/$defs/account_slot"} |
| response.data.accounts.stock_input.available | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.accounts.stock_input.reason_code | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/unavailable_reason"}]} |
| response.data.accounts.stock_input.reason_code | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.stock_input.reason_code | 未限定 | 分支约束 | oneOf[2]/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.stock_input.account | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.stock_input.account | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.stock_input.account | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.stock_input.account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.stock_input.account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.stock_input.account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.stock_input | 未限定 | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.stock_input.available | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  | {"const":true} |
| response.data.accounts.stock_input.reason_code | null | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.stock_input.account | 组合/开放结构 | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.stock_input.account | null | 分支约束 | oneOf[2]/oneOf[1]/oneOf[1] |  |  |
| response.data.accounts.stock_input.account | object | 分支约束 | oneOf[2]/oneOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.stock_input.account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[1]/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.stock_input.account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[1]/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.stock_input.account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[1]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.stock_input | 未限定 | 分支约束 | oneOf[2]/oneOf[2] |  |  |
| response.data.accounts.stock_input.available | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  | {"const":false} |
| response.data.accounts.stock_input.reason_code | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.stock_input.account | null | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  |  |
| response.data.accounts.stock_output | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"oneOf":[{"properties":{"account":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]},"available":{"const":true},"reason_code":{"type":"null"}}},{"properties":{"account":{"type":"null"},"available":{"const":false},"reason_code":{"$ref":"#/$defs/unavailable_reason"}}}],"required_in_object":["available","reason_code","account"],"resolved_ref":"#/$defs/account_slot"} |
| response.data.accounts.stock_output.available | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.accounts.stock_output.reason_code | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/unavailable_reason"}]} |
| response.data.accounts.stock_output.reason_code | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.stock_output.reason_code | 未限定 | 分支约束 | oneOf[2]/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.stock_output.account | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.stock_output.account | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.stock_output.account | object | 分支约束 | oneOf[2]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.stock_output.account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.stock_output.account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.stock_output.account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.stock_output | 未限定 | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.stock_output.available | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  | {"const":true} |
| response.data.accounts.stock_output.reason_code | null | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  |  |
| response.data.accounts.stock_output.account | 组合/开放结构 | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.stock_output.account | null | 分支约束 | oneOf[2]/oneOf[1]/oneOf[1] |  |  |
| response.data.accounts.stock_output.account | object | 分支约束 | oneOf[2]/oneOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.stock_output.account.id | integer | 必填（所在对象出现时） | oneOf[2]/oneOf[1]/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.stock_output.account.code | string | 必填（所在对象出现时） | oneOf[2]/oneOf[1]/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.stock_output.account.name | string | 必填（所在对象出现时） | oneOf[2]/oneOf[1]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.stock_output | 未限定 | 分支约束 | oneOf[2]/oneOf[2] |  |  |
| response.data.accounts.stock_output.available | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  | {"const":false} |
| response.data.accounts.stock_output.reason_code | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.stock_output.account | null | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  |  |
| response.data.valuation | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"oneOf":[{"properties":{"available":{"const":true},"reason_code":{"type":"null"},"value":{"enum":["periodic","real_time"]}}},{"properties":{"available":{"const":false},"reason_code":{"$ref":"#/$defs/unavailable_reason"},"value":{"type":"null"}}}],"required_in_object":["available","reason_code","value"],"resolved_ref":"#/$defs/valuation"} |
| response.data.valuation.available | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.valuation.reason_code | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/unavailable_reason"}]} |
| response.data.valuation.reason_code | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.valuation.reason_code | 未限定 | 分支约束 | oneOf[2]/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.valuation.value | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"enum":["periodic","real_time"]}]} |
| response.data.valuation.value | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.valuation.value | 未限定 | 分支约束 | oneOf[2]/oneOf[2] |  | {"enum":["periodic","real_time"]} |
| response.data.valuation | 未限定 | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.valuation.available | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  | {"const":true} |
| response.data.valuation.reason_code | null | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  |  |
| response.data.valuation.value | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  | {"enum":["periodic","real_time"]} |
| response.data.valuation | 未限定 | 分支约束 | oneOf[2]/oneOf[2] |  |  |
| response.data.valuation.available | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  | {"const":false} |
| response.data.valuation.reason_code | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.valuation.value | null | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  |  |
| response.data.cost_method | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"oneOf":[{"properties":{"available":{"const":true},"reason_code":{"type":"null"},"value":{"enum":["standard","fifo","average"]}}},{"properties":{"available":{"const":false},"reason_code":{"$ref":"#/$defs/unavailable_reason"},"value":{"type":"null"}}}],"required_in_object":["available","reason_code","value"],"resolved_ref":"#/$defs/cost_method"} |
| response.data.cost_method.available | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.cost_method.reason_code | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/unavailable_reason"}]} |
| response.data.cost_method.reason_code | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.cost_method.reason_code | 未限定 | 分支约束 | oneOf[2]/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.cost_method.value | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"oneOf":[{"type":"null"},{"enum":["standard","fifo","average"]}]} |
| response.data.cost_method.value | null | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.cost_method.value | 未限定 | 分支约束 | oneOf[2]/oneOf[2] |  | {"enum":["standard","fifo","average"]} |
| response.data.cost_method | 未限定 | 分支约束 | oneOf[2]/oneOf[1] |  |  |
| response.data.cost_method.available | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  | {"const":true} |
| response.data.cost_method.reason_code | null | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  |  |
| response.data.cost_method.value | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[1] |  | {"enum":["standard","fifo","average"]} |
| response.data.cost_method | 未限定 | 分支约束 | oneOf[2]/oneOf[2] |  |  |
| response.data.cost_method.available | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  | {"const":false} |
| response.data.cost_method.reason_code | 未限定 | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.cost_method.value | null | 可选（可能有条件限制） | oneOf[2]/oneOf[2] |  |  |
| response.data.invoice_policy | 未限定 | 可选（可能有条件限制） | oneOf[2] | Native template-shared sales invoicing policy; affects every variant and company, not a company-dependent property. Null when the native field is unavailable. | {"enum":[null,"order","delivery"]} |
| response.data.purchase_method | 未限定 | 可选（可能有条件限制） | oneOf[2] | Native template-shared purchase billing policy; affects every variant and company, not a company-dependent property. Null when the native field is unavailable. | {"enum":[null,"purchase","receive"]} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["company_id","product","template","category","modules","accounts","valuation","cost_method"],"resolved_ref":"#/$defs/data"} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.product | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","default_code","active","company_id","template_id"],"resolved_ref":"#/$defs/product"} |
| response.data.product.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.product.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.product.default_code | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"minLength":1,"type":"string"}]} |
| response.data.product.default_code | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.product.default_code | string | 分支约束 | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.product.active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.product.company_id | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"oneOf":[{"type":"null"},{"minimum":1,"type":"integer"}],"resolved_ref":"#/$defs/nullable_company_id"} |
| response.data.product.company_id | null | 分支约束 | allOf[1]/then/oneOf[1] | 所选公司ID |  |
| response.data.product.company_id | integer | 分支约束 | allOf[1]/then/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.product.template_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.template | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","company_id","category_id"],"resolved_ref":"#/$defs/template"} |
| response.data.template.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.template.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.template.company_id | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"oneOf":[{"type":"null"},{"minimum":1,"type":"integer"}],"resolved_ref":"#/$defs/nullable_company_id"} |
| response.data.template.company_id | null | 分支约束 | allOf[1]/then/oneOf[1] | 所选公司ID |  |
| response.data.template.company_id | integer | 分支约束 | allOf[1]/then/oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.template.category_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.category | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","complete_name"],"resolved_ref":"#/$defs/category"} |
| response.data.category.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.category.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.category.complete_name | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
| response.data.modules | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["account","stock_account"],"resolved_ref":"#/$defs/modules"} |
| response.data.modules.account | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.modules.stock_account | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.accounts | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["income","expense","stock_valuation","stock_input","stock_output"],"resolved_ref":"#/$defs/accounts"} |
| response.data.accounts.income | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"oneOf":[{"properties":{"account":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]},"available":{"const":true},"reason_code":{"type":"null"}}},{"properties":{"account":{"type":"null"},"available":{"const":false},"reason_code":{"$ref":"#/$defs/unavailable_reason"}}}],"required_in_object":["available","reason_code","account"],"resolved_ref":"#/$defs/account_slot"} |
| response.data.accounts.income.available | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.accounts.income.reason_code | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/unavailable_reason"}]} |
| response.data.accounts.income.reason_code | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.income.reason_code | 未限定 | 分支约束 | allOf[1]/then/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.income.account | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.income.account | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.income.account | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.income.account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.income.account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.income.account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.income | 未限定 | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.income.available | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  | {"const":true} |
| response.data.accounts.income.reason_code | null | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.income.account | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.income.account | null | 分支约束 | allOf[1]/then/oneOf[1]/oneOf[1] |  |  |
| response.data.accounts.income.account | object | 分支约束 | allOf[1]/then/oneOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.income.account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[1]/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.income.account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[1]/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.income.account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[1]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.income | 未限定 | 分支约束 | allOf[1]/then/oneOf[2] |  |  |
| response.data.accounts.income.available | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  | {"const":false} |
| response.data.accounts.income.reason_code | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.income.account | null | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  |  |
| response.data.accounts.expense | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"oneOf":[{"properties":{"account":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]},"available":{"const":true},"reason_code":{"type":"null"}}},{"properties":{"account":{"type":"null"},"available":{"const":false},"reason_code":{"$ref":"#/$defs/unavailable_reason"}}}],"required_in_object":["available","reason_code","account"],"resolved_ref":"#/$defs/account_slot"} |
| response.data.accounts.expense.available | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.accounts.expense.reason_code | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/unavailable_reason"}]} |
| response.data.accounts.expense.reason_code | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.expense.reason_code | 未限定 | 分支约束 | allOf[1]/then/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.expense.account | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.expense.account | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.expense.account | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.expense.account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.expense.account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.expense.account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.expense | 未限定 | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.expense.available | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  | {"const":true} |
| response.data.accounts.expense.reason_code | null | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.expense.account | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.expense.account | null | 分支约束 | allOf[1]/then/oneOf[1]/oneOf[1] |  |  |
| response.data.accounts.expense.account | object | 分支约束 | allOf[1]/then/oneOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.expense.account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[1]/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.expense.account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[1]/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.expense.account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[1]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.expense | 未限定 | 分支约束 | allOf[1]/then/oneOf[2] |  |  |
| response.data.accounts.expense.available | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  | {"const":false} |
| response.data.accounts.expense.reason_code | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.expense.account | null | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  |  |
| response.data.accounts.stock_valuation | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"oneOf":[{"properties":{"account":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]},"available":{"const":true},"reason_code":{"type":"null"}}},{"properties":{"account":{"type":"null"},"available":{"const":false},"reason_code":{"$ref":"#/$defs/unavailable_reason"}}}],"required_in_object":["available","reason_code","account"],"resolved_ref":"#/$defs/account_slot"} |
| response.data.accounts.stock_valuation.available | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.accounts.stock_valuation.reason_code | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/unavailable_reason"}]} |
| response.data.accounts.stock_valuation.reason_code | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.stock_valuation.reason_code | 未限定 | 分支约束 | allOf[1]/then/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.stock_valuation.account | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.stock_valuation.account | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.stock_valuation.account | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.stock_valuation.account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.stock_valuation.account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.stock_valuation.account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.stock_valuation | 未限定 | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.stock_valuation.available | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  | {"const":true} |
| response.data.accounts.stock_valuation.reason_code | null | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.stock_valuation.account | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.stock_valuation.account | null | 分支约束 | allOf[1]/then/oneOf[1]/oneOf[1] |  |  |
| response.data.accounts.stock_valuation.account | object | 分支约束 | allOf[1]/then/oneOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.stock_valuation.account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[1]/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.stock_valuation.account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[1]/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.stock_valuation.account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[1]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.stock_valuation | 未限定 | 分支约束 | allOf[1]/then/oneOf[2] |  |  |
| response.data.accounts.stock_valuation.available | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  | {"const":false} |
| response.data.accounts.stock_valuation.reason_code | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.stock_valuation.account | null | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  |  |
| response.data.accounts.stock_input | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"oneOf":[{"properties":{"account":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]},"available":{"const":true},"reason_code":{"type":"null"}}},{"properties":{"account":{"type":"null"},"available":{"const":false},"reason_code":{"$ref":"#/$defs/unavailable_reason"}}}],"required_in_object":["available","reason_code","account"],"resolved_ref":"#/$defs/account_slot"} |
| response.data.accounts.stock_input.available | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.accounts.stock_input.reason_code | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/unavailable_reason"}]} |
| response.data.accounts.stock_input.reason_code | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.stock_input.reason_code | 未限定 | 分支约束 | allOf[1]/then/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.stock_input.account | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.stock_input.account | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.stock_input.account | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.stock_input.account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.stock_input.account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.stock_input.account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.stock_input | 未限定 | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.stock_input.available | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  | {"const":true} |
| response.data.accounts.stock_input.reason_code | null | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.stock_input.account | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.stock_input.account | null | 分支约束 | allOf[1]/then/oneOf[1]/oneOf[1] |  |  |
| response.data.accounts.stock_input.account | object | 分支约束 | allOf[1]/then/oneOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.stock_input.account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[1]/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.stock_input.account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[1]/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.stock_input.account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[1]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.stock_input | 未限定 | 分支约束 | allOf[1]/then/oneOf[2] |  |  |
| response.data.accounts.stock_input.available | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  | {"const":false} |
| response.data.accounts.stock_input.reason_code | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.stock_input.account | null | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  |  |
| response.data.accounts.stock_output | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"oneOf":[{"properties":{"account":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]},"available":{"const":true},"reason_code":{"type":"null"}}},{"properties":{"account":{"type":"null"},"available":{"const":false},"reason_code":{"$ref":"#/$defs/unavailable_reason"}}}],"required_in_object":["available","reason_code","account"],"resolved_ref":"#/$defs/account_slot"} |
| response.data.accounts.stock_output.available | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.accounts.stock_output.reason_code | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/unavailable_reason"}]} |
| response.data.accounts.stock_output.reason_code | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.stock_output.reason_code | 未限定 | 分支约束 | allOf[1]/then/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.stock_output.account | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.stock_output.account | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.stock_output.account | object | 分支约束 | allOf[1]/then/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.stock_output.account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.stock_output.account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.stock_output.account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.stock_output | 未限定 | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.stock_output.available | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  | {"const":true} |
| response.data.accounts.stock_output.reason_code | null | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  |  |
| response.data.accounts.stock_output.account | 组合/开放结构 | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/account"}]} |
| response.data.accounts.stock_output.account | null | 分支约束 | allOf[1]/then/oneOf[1]/oneOf[1] |  |  |
| response.data.accounts.stock_output.account | object | 分支约束 | allOf[1]/then/oneOf[1]/oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code","name"],"resolved_ref":"#/$defs/account"} |
| response.data.accounts.stock_output.account.id | integer | 必填（所在对象出现时） | allOf[1]/then/oneOf[1]/oneOf[2] |  | {"minimum":1} |
| response.data.accounts.stock_output.account.code | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[1]/oneOf[2] |  | {"minLength":1} |
| response.data.accounts.stock_output.account.name | string | 必填（所在对象出现时） | allOf[1]/then/oneOf[1]/oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.accounts.stock_output | 未限定 | 分支约束 | allOf[1]/then/oneOf[2] |  |  |
| response.data.accounts.stock_output.available | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  | {"const":false} |
| response.data.accounts.stock_output.reason_code | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.accounts.stock_output.account | null | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  |  |
| response.data.valuation | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"oneOf":[{"properties":{"available":{"const":true},"reason_code":{"type":"null"},"value":{"enum":["periodic","real_time"]}}},{"properties":{"available":{"const":false},"reason_code":{"$ref":"#/$defs/unavailable_reason"},"value":{"type":"null"}}}],"required_in_object":["available","reason_code","value"],"resolved_ref":"#/$defs/valuation"} |
| response.data.valuation.available | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.valuation.reason_code | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/unavailable_reason"}]} |
| response.data.valuation.reason_code | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.valuation.reason_code | 未限定 | 分支约束 | allOf[1]/then/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.valuation.value | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"enum":["periodic","real_time"]}]} |
| response.data.valuation.value | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.valuation.value | 未限定 | 分支约束 | allOf[1]/then/oneOf[2] |  | {"enum":["periodic","real_time"]} |
| response.data.valuation | 未限定 | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.valuation.available | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  | {"const":true} |
| response.data.valuation.reason_code | null | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  |  |
| response.data.valuation.value | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  | {"enum":["periodic","real_time"]} |
| response.data.valuation | 未限定 | 分支约束 | allOf[1]/then/oneOf[2] |  |  |
| response.data.valuation.available | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  | {"const":false} |
| response.data.valuation.reason_code | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.valuation.value | null | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  |  |
| response.data.cost_method | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"oneOf":[{"properties":{"available":{"const":true},"reason_code":{"type":"null"},"value":{"enum":["standard","fifo","average"]}}},{"properties":{"available":{"const":false},"reason_code":{"$ref":"#/$defs/unavailable_reason"},"value":{"type":"null"}}}],"required_in_object":["available","reason_code","value"],"resolved_ref":"#/$defs/cost_method"} |
| response.data.cost_method.available | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.cost_method.reason_code | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/unavailable_reason"}]} |
| response.data.cost_method.reason_code | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.cost_method.reason_code | 未限定 | 分支约束 | allOf[1]/then/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.cost_method.value | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"oneOf":[{"type":"null"},{"enum":["standard","fifo","average"]}]} |
| response.data.cost_method.value | null | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.cost_method.value | 未限定 | 分支约束 | allOf[1]/then/oneOf[2] |  | {"enum":["standard","fifo","average"]} |
| response.data.cost_method | 未限定 | 分支约束 | allOf[1]/then/oneOf[1] |  |  |
| response.data.cost_method.available | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  | {"const":true} |
| response.data.cost_method.reason_code | null | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  |  |
| response.data.cost_method.value | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[1] |  | {"enum":["standard","fifo","average"]} |
| response.data.cost_method | 未限定 | 分支约束 | allOf[1]/then/oneOf[2] |  |  |
| response.data.cost_method.available | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  | {"const":false} |
| response.data.cost_method.reason_code | 未限定 | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  | {"enum":["module_uninstalled","field_unavailable"],"resolved_ref":"#/$defs/unavailable_reason"} |
| response.data.cost_method.value | null | 可选（可能有条件限制） | allOf[1]/then/oneOf[2] |  |  |
| response.data.invoice_policy | 未限定 | 可选（可能有条件限制） | allOf[1]/then | Native template-shared sales invoicing policy; affects every variant and company, not a company-dependent property. Null when the native field is unavailable. | {"enum":[null,"order","delivery"]} |
| response.data.purchase_method | 未限定 | 可选（可能有条件限制） | allOf[1]/then | Native template-shared purchase billing policy; affects every variant and company, not a company-dependent property. Null when the native field is unavailable. | {"enum":[null,"purchase","receive"]} |
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
- `execute`：fixed_company_relative_product_accounting_profile
- `verify`：final_odoo_account_mapping_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed request and response, optional module slots, final company-relative account mapping, and CLI dispatch.；引用：tests/unit/test_product_accounting_profile.py, tests/unit/test_product_accounting_profile_bridge.py, tests/unit/test_capability_batch_runtime.py, tests/unit/test_capability_batch_cli.py, tests/unit/test_invoice_rounds_write_contract.py, tests/unit/test_invoice_rounds_runtime.py, tests/unit/test_invoice_rounds_product_reads.py, tests/unit/test_invoice_rounds_cli.py
- `integration`：`implemented`；Existing native product-accounting write workflow already positively verified category fallback/product overrides. Current shared line-processing workflow also reads a synthetic company-specific product and category as ordinary uid5/su=False before temporary analytic permissions in both isolated aliases. Full fresh-cursor fixture/group rollback verified; unavailable legacy stock slots remain explicit, not invented.；引用：tests/integration/test_product_accounting_write_batch_live.py, tests/integration/test_journal_item_processing_batch_live.py, tests/integration/test_invoice_rounds_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-product-accounting_profile-update"></a>

## product.accounting_profile.update — 更新产品会计配置

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is registered; availability depends on runtime configuration, company-scoped product data, and product-manager access. Optional invoice_policy and purchase_method are native template-shared policies affecting every variant and company, not company-dependent properties. Absent native addon fields project null on get and reject only explicit policy writes; policy-only updates accept visible shared/multi-variant templates.
- 内部domain：`accounting_master_data`；来源模型：res.company, account.account, account.tax, product.template, product.product；向导：无。
- 必需模块：base, product, account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：product.group_product_manager；ACL：res.company:read, account.account:read, account.tax:read, product.template:read, product.template:write, product.product:read。
- 请求/响应合同：`schemas/v1/product.accounting_profile.update.request.schema.json` / `schemas/v1/product.accounting_profile.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run product.accounting_profile.update --request "@request.json" --idempotency-key "product.accounting_profile.update:1:2e3d1d65a31733cc449a97f0601f4e73" --confirm "product.accounting_profile.update"
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
    "product_id": 1,
    "changes": {
      "income_account_id": 1
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["product_id","changes"]} |
| parameters.product_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.income_account_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.changes.expense_account_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1,"resolved_ref":"#/$defs/nullableId"} |
| parameters.changes.sale_tax_ids | array | 可选（可能有条件限制） |  | Unique positive IDs are normalized to ascending order. | {"resolved_ref":"#/$defs/sortedUniqueIds","uniqueItems":true} |
| parameters.changes.sale_tax_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.changes.purchase_tax_ids | array | 可选（可能有条件限制） |  | Unique positive IDs are normalized to ascending order. | {"resolved_ref":"#/$defs/sortedUniqueIds","uniqueItems":true} |
| parameters.changes.purchase_tax_ids[] | integer | 每个数组元素 |  |  | {"minimum":1} |
| parameters.changes.invoice_policy | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["order","delivery"]} |
| parameters.changes.purchase_method | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["purchase","receive"]} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"product.accounting_profile.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"product.accounting_profile.update"} |
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
- `execute`：fixed_company_specific_single_variant_account_tax_update_or_visible_template_shared_global_policy_only_update
- `verify`：same_transaction_company_relative_product_reread_and_response_schema_validation
- `idempotency`：deterministic_product_target_and_changes_digest32_request_key_with_current_target_state_recheck_without_operation_store_or_intermediate_change_protection
- `reverse`：product.accounting_profile.update_with_prior_values

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the closed public contract, fixed company and single-variant runtime scope, result validation, registry schemas, and CLI dispatch.；引用：tests/unit/test_product_accounting_write_public.py, tests/unit/test_product_accounting_writes_runtime.py, tests/unit/test_invoice_rounds_write_contract.py, tests/unit/test_invoice_rounds_runtime.py, tests/unit/test_invoice_rounds_product_reads.py, tests/unit/test_invoice_rounds_cli.py
- `integration`：`implemented`；The guarded shared transactional smoke passed both isolated database aliases as uid 5 with su=False, verifying execution and immediate replay for all eight writes plus rollback of business data and temporary product-manager/stock-manager grants.；引用：tests/integration/test_product_accounting_write_batch_live.py, tests/integration/test_invoice_rounds_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-product-accounts-resolve"></a>

## product.accounts.resolve — 解析产品实际会计科目

- 类型：只读；静态状态：`unconfigured`；handler：`product_accounts_resolve`。
- 状态原因：`runtime_context_required` — Fixed invoice preparation and product accounting operations are implemented; runtime company, ordinary-user ACL and native accounting recomputation apply.
- 内部domain：`product`；来源模型：res.company, product.product, product.template, product.category, account.fiscal.position, account.fiscal.position.account, account.account, account.journal；向导：无。
- 必需模块：account, product；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, product.product:read, product.template:read, product.category:read, account.fiscal.position:read, account.fiscal.position.account:read, account.account:read, account.journal:read。
- 请求/响应合同：`schemas/v1/product.accounts.resolve.request.schema.json` / `schemas/v1/product.accounts.resolve.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read product.accounts.resolve --request "@request.json"
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
    "product_id": 1,
    "fiscal_position_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["product_id","fiscal_position_id"]} |
| parameters.product_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.fiscal_position_id | integer/null | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"product.accounts.resolve"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","template_id","fiscal_position_id","income_account_id","expense_account_id","stock_valuation_account_id","stock_variation_account_id","stock_journal_id"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.template_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.fiscal_position_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.income_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.expense_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.stock_valuation_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.stock_variation_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.stock_journal_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","template_id","fiscal_position_id","income_account_id","expense_account_id","stock_valuation_account_id","stock_variation_account_id","stock_journal_id"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.template_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.fiscal_position_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.income_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.expense_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.stock_valuation_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.stock_variation_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.stock_journal_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
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

<a id="cap-product-archive"></a>

## product.archive — 归档产品

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is registered; Odoo's stock extension reads and writes warehouse orderpoints during product archiving, so availability additionally depends on stock being installed and the configured user holding both product-manager and stock-manager access.
- 内部domain：`accounting_master_data`；来源模型：res.company, product.template, product.product, stock.warehouse.orderpoint；向导：无。
- 必需模块：base, product, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：product.group_product_manager, stock.group_stock_manager；ACL：res.company:read, product.template:read, product.template:write, product.product:read, product.product:write, stock.warehouse.orderpoint:read, stock.warehouse.orderpoint:write。
- 请求/响应合同：`schemas/v1/product.archive.request.schema.json` / `schemas/v1/product.archive.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run product.archive --request "@request.json" --idempotency-key "product.archive:1" --confirm "product.archive"
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
    "product_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["product_id"]} |
| parameters.product_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"product.archive"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"product.archive"} |
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
- `execute`：fixed_company_specific_single_variant_product_archive
- `verify`：same_transaction_archived_product_reread_and_response_schema_validation
- `idempotency`：deterministic_product_target_request_key_with_current_archived_state_recheck_without_operation_store
- `reverse`：product.restore

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the closed public contract, fixed company and single-variant runtime scope, result validation, registry schemas, and CLI dispatch.；引用：tests/unit/test_product_accounting_write_public.py, tests/unit/test_product_accounting_writes_runtime.py
- `integration`：`implemented`；The guarded shared transactional smoke passed both isolated database aliases as uid 5 with su=False, verifying execution and immediate replay for all eight writes, including an attached orderpoint during archive/restore, plus rollback of business data and temporary product-manager/stock-manager grants.；引用：tests/integration/test_product_accounting_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-product-category-accounting_profile-get"></a>

## product.category.accounting_profile.get — 查看产品分类会计科目

- 类型：只读；静态状态：`unconfigured`；handler：`product_category_accounting_profile_get`。
- 状态原因：`runtime_context_required` — Fixed invoice preparation and product accounting operations are implemented; runtime company, ordinary-user ACL and native accounting recomputation apply.
- 内部domain：`product`；来源模型：res.company, product.category, account.account；向导：无。
- 必需模块：account, product；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, product.category:read, account.account:read。
- 请求/响应合同：`schemas/v1/product.category.accounting_profile.get.request.schema.json` / `schemas/v1/product.category.accounting_profile.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read product.category.accounting_profile.get --request "@request.json"
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
    "category_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["category_id"]} |
| parameters.category_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"product.category.accounting_profile.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","income_account_id","expense_account_id","company_income_account_id","company_expense_account_id"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.income_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.expense_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_income_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_expense_account_id | integer/null | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","income_account_id","expense_account_id","company_income_account_id","company_expense_account_id"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.income_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.expense_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_income_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_expense_account_id | integer/null | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
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

<a id="cap-product-category-accounting_profile-update"></a>

## product.category.accounting_profile.update — 更新产品类别会计配置

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is registered; availability depends on runtime configuration, company-relative category data, and product-manager access.
- 内部domain：`accounting_master_data`；来源模型：res.company, account.account, product.category；向导：无。
- 必需模块：base, product, account；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：product.group_product_manager；ACL：res.company:read, account.account:read, product.category:read, product.category:write。
- 请求/响应合同：`schemas/v1/product.category.accounting_profile.update.request.schema.json` / `schemas/v1/product.category.accounting_profile.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run product.category.accounting_profile.update --request "@request.json" --idempotency-key "product.category.accounting_profile.update:1:1:2e3d1d65a31733cc449a97f0601f4e73" --confirm "product.category.accounting_profile.update"
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
    "category_id": 1,
    "changes": {
      "income_account_id": 1
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["category_id","changes"]} |
| parameters.category_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.income_account_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.changes.expense_account_id | integer/null | 可选（可能有条件限制） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"product.category.accounting_profile.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"product.category.accounting_profile.update"} |
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
- `execute`：fixed_company_specific_product_category_accounting_profile_update
- `verify`：same_transaction_company_relative_category_reread_and_response_schema_validation
- `idempotency`：deterministic_company_category_target_and_changes_digest32_request_key_with_current_target_state_recheck_without_operation_store_or_intermediate_change_protection
- `reverse`：product.category.accounting_profile.update_with_prior_values

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the closed public contract, fixed company-relative runtime scope, result validation, registry schemas, and CLI dispatch.；引用：tests/unit/test_product_accounting_write_public.py, tests/unit/test_product_accounting_writes_runtime.py
- `integration`：`implemented`；The guarded shared transactional smoke passed both isolated database aliases as uid 5 with su=False, verifying execution and immediate replay for all eight writes plus rollback of business data and temporary product-manager/stock-manager grants.；引用：tests/integration/test_product_accounting_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-product-category-list"></a>

## product.category.list — 列出产品类别

- 类型：只读；静态状态：`unconfigured`；handler：`product_category_list`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability depends on the selected database, company, user, module, and ACLs.
- 内部domain：`inventory`；来源模型：res.company, product.category；向导：无。
- 必需模块：base, product；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, product.category:read。
- 请求/响应合同：`schemas/v1/product.category.list.request.schema.json` / `schemas/v1/product.category.list.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read product.category.list --request "@request.json"
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
| parameters.parent_id | integer/null | 可选（可能有条件限制） |  |  | {"default":null,"minimum":1} |
| parameters.limit | integer | 可选（可能有条件限制） |  | 每页数量 | {"default":100,"maximum":1000,"minimum":1} |
| parameters.cursor | string/null | 可选（可能有条件限制） |  | 不透明分页游标；新查询先省略，后续原样使用返回值 | {"default":null,"maxLength":4096,"minLength":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/data"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"product.category.list"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","complete_name","parent_id"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].complete_name | string | 必填（所在对象出现时） | oneOf[2] |  | {"minLength":1} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","complete_name","parent_id"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].complete_name | string | 必填（所在对象出现时） | allOf[1]/then |  | {"minLength":1} |
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

- `preview`：not_applicable_read_only
- `execute`：fixed_company_context_inventory_master_read
- `verify`：read_only_transaction_acl_cursor_and_response_schema_validation
- `idempotency`：not_applicable_read_only
- `reverse`：not_applicable_read_only

### 已登记测试与证据范围

- `unit`：`implemented`；Unit tests cover the closed filters, cursor binding, fixed bridge action, ACL gate, Odoo mapping, schemas, registry metadata, and CLI dispatch.；引用：tests/unit/test_inventory_master.py, tests/unit/test_inventory_master_bridge.py, tests/unit/test_inventory_master_runtime.py, tests/unit/test_inventory_master_schemas.py, tests/unit/test_inventory_read_cli.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The guarded shared smoke reads inventory master data as the ordinary accounting user in both dedicated isolated databases and verifies rollback residue.；引用：tests/integration/test_inventory_read_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-product-cost-update"></a>

## product.cost.update — 更新产品成本

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is registered; availability depends on runtime configuration, company-specific cost data, and product-manager access.
- 内部domain：`accounting_master_data`；来源模型：res.company, product.template, product.product；向导：无。
- 必需模块：base, product；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：product.group_product_manager；ACL：res.company:read, product.template:read, product.product:read, product.product:write。
- 请求/响应合同：`schemas/v1/product.cost.update.request.schema.json` / `schemas/v1/product.cost.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run product.cost.update --request "@request.json" --idempotency-key "product.cost.update:1:3cff04bfd4328ebe694bd67bd246b11a" --confirm "product.cost.update"
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
    "product_id": 1,
    "standard_price": "1"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["product_id","standard_price"]} |
| parameters.product_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.standard_price | string | 必填（所在对象出现时） |  |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]*[1-9])?$(?![\\s\\S])"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"product.cost.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"product.cost.update"} |
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
- `execute`：fixed_company_specific_single_variant_standard_price_update
- `verify`：same_transaction_company_relative_product_cost_reread_and_response_schema_validation
- `idempotency`：deterministic_product_target_and_standard_price_digest32_request_key_with_current_target_state_recheck_without_operation_store_or_intermediate_change_protection
- `reverse`：product.cost.update_with_prior_value

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover canonical decimal input, fixed company and single-variant runtime scope, result validation, registry schemas, and CLI dispatch.；引用：tests/unit/test_product_accounting_write_public.py, tests/unit/test_product_accounting_writes_runtime.py
- `integration`：`implemented`；The guarded shared transactional smoke passed both isolated database aliases as uid 5 with su=False, verifying execution and immediate replay for all eight writes plus rollback of business data and temporary product-manager/stock-manager grants.；引用：tests/integration/test_product_accounting_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-product-create"></a>

## product.create — 创建产品

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`natural_key_replay_attribution_limit` — An exact pre-existing company product code and field match is treated as a serial replay because Odoo exposes neither a request marker nor a matching request uniqueness constraint; unrelated exact matches and concurrent creates cannot be distinguished.
- 内部domain：`accounting_master_data`；来源模型：res.company, product.category, uom.uom, product.template, product.product；向导：无。
- 必需模块：base, product, uom；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：product.group_product_manager；ACL：res.company:read, product.category:read, uom.uom:read, product.template:read, product.template:create, product.product:read, product.product:create。
- 请求/响应合同：`schemas/v1/product.create.request.schema.json` / `schemas/v1/product.create.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run product.create --request "@request.json" --idempotency-key "product.create:1:e018c0b8123554e8e9d56880fb32bf93" --confirm "product.create"
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
    "default_code": "1",
    "product_type": "consu",
    "category_id": 1,
    "uom_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["name","default_code","product_type","category_id","uom_id"]} |
| parameters.name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":256,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","resolved_ref":"#/$defs/text256"} |
| parameters.default_code | string | 必填（所在对象出现时） |  |  | {"maxLength":64,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","resolved_ref":"#/$defs/text64"} |
| parameters.product_type | 未限定 | 必填（所在对象出现时） |  |  | {"enum":["consu","service"]} |
| parameters.category_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.uom_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.barcode | string/null | 可选（可能有条件限制） |  |  | {"default":null,"maxLength":64,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","resolved_ref":"#/$defs/nullableText64"} |
| parameters.sale_ok | boolean | 可选（可能有条件限制） |  |  | {"default":true} |
| parameters.purchase_ok | boolean | 可选（可能有条件限制） |  |  | {"default":true} |
| parameters.list_price | string | 可选（可能有条件限制） |  |  | {"default":"0","maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]*[1-9])?$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegativeDecimal"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"product.create"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"product.create"} |
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
- `execute`：fixed_company_specific_single_variant_product_create
- `verify`：same_transaction_created_variant_and_template_reread_and_response_schema_validation
- `idempotency`：full_normalized_parameters_digest32_request_key_and_company_code_natural_key_recheck_with_preexisting_exact_match_attribution_and_concurrent_uniqueness_limits
- `reverse`：product.archive

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the closed normalized create contract, fixed company and single-variant runtime scope, result validation, registry schemas, and CLI dispatch.；引用：tests/unit/test_product_accounting_write_public.py, tests/unit/test_product_accounting_writes_runtime.py
- `integration`：`implemented`；The guarded shared transactional smoke passed both isolated database aliases as uid 5 with su=False, verifying execution and immediate replay for all eight writes plus rollback of business data and temporary product-manager/stock-manager grants.；引用：tests/integration/test_product_accounting_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-product-duplicate"></a>

## product.duplicate — 复制产品

- 类型：写入；静态状态：`degraded`；handler：`core_write`。
- 状态原因：`natural_key_replay_attribution_limit` — An exact pre-existing company product code and copied-field match is treated as a serial replay because Odoo exposes neither a request marker nor a matching request uniqueness constraint; unrelated exact matches and concurrent copies cannot be distinguished.
- 内部domain：`accounting_master_data`；来源模型：res.company, product.category, uom.uom, product.template, product.product；向导：无。
- 必需模块：base, product, uom；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：product.group_product_manager；ACL：res.company:read, product.category:read, uom.uom:read, product.template:read, product.template:create, product.product:read, product.product:create。
- 请求/响应合同：`schemas/v1/product.duplicate.request.schema.json` / `schemas/v1/product.duplicate.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run product.duplicate --request "@request.json" --idempotency-key "product.duplicate:1:de16d4c139b2cf6cf2995c563882e8a0" --confirm "product.duplicate"
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
    "product_id": 1,
    "name": "Example",
    "default_code": "1"
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["product_id","name","default_code"]} |
| parameters.product_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.name | string | 必填（所在对象出现时） |  | 名称/行说明 | {"maxLength":256,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |
| parameters.default_code | string | 必填（所在对象出现时） |  |  | {"maxLength":64,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"product.duplicate"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"product.duplicate"} |
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
- `execute`：fixed_company_specific_single_variant_product_duplicate
- `verify`：same_transaction_duplicated_variant_and_template_reread_and_response_schema_validation
- `idempotency`：source_and_parameters_digest32_request_key_and_company_code_natural_key_recheck_with_preexisting_exact_match_attribution_and_concurrent_uniqueness_limits
- `reverse`：product.archive

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the exact duplicate contract, fixed company and single-variant runtime scope, result validation, registry schemas, and CLI dispatch.；引用：tests/unit/test_product_accounting_write_public.py, tests/unit/test_product_accounting_writes_runtime.py
- `integration`：`implemented`；The guarded shared transactional smoke passed both isolated database aliases as uid 5 with su=False, verifying execution and immediate replay for all eight writes plus rollback of business data and temporary product-manager/stock-manager grants.；引用：tests/integration/test_product_accounting_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-product-get"></a>

## product.get — 获取产品详情

- 类型：只读；静态状态：`unconfigured`；handler：`product_get`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`accounting_master_data`；来源模型：res.company, product.product, product.template, product.category, uom.uom, res.currency；向导：无。
- 必需模块：base, product, uom, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, product.product:read, product.template:read, product.category:read, uom.uom:read, res.currency:read。
- 请求/响应合同：`schemas/v1/product.get.request.schema.json` / `schemas/v1/product.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read product.get --request "@request.json"
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
    "product_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["product_id"],"resolved_ref":"#/$defs/parameters"} |
| parameters.product_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"product.search.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"product.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"product.search.response.schema.json#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","default_code","active","product_type","is_storable","template","category","uom","company_id","currency","standard_price","list_price"],"resolved_ref":"product.search.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.default_code | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.product_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["consu","service","combo"]} |
| response.data.is_storable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.template | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.template.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.template.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.category | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"anyOf":[{"$ref":"#/$defs/named"},{"type":"null"}]} |
| response.data.category | object | 分支约束 | oneOf[2]/anyOf[1] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.category.id | integer | 必填（所在对象出现时） | oneOf[2]/anyOf[1] |  | {"minimum":1} |
| response.data.category.name | string | 必填（所在对象出现时） | oneOf[2]/anyOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.category | null | 分支约束 | oneOf[2]/anyOf[2] |  |  |
| response.data.uom | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.uom.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.uom.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.company_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.standard_price | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.list_price | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
| response | 组合/开放结构 | 分支约束 | allOf[1] |  | {"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"product.search.response.schema.json#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}} |
| response | 未限定 | 条件分支 | allOf[1]/then |  |  |
| response.request_id | string | 可选（可能有条件限制） | allOf[1]/then |  | {"format":"uuid"} |
| response.status | 未限定 | 可选（可能有条件限制） | allOf[1]/then |  | {"const":"verified"} |
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","default_code","active","product_type","is_storable","template","category","uom","company_id","currency","standard_price","list_price"],"resolved_ref":"product.search.response.schema.json#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.default_code | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.product_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["consu","service","combo"]} |
| response.data.is_storable | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.template | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.template.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.template.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.category | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"anyOf":[{"$ref":"#/$defs/named"},{"type":"null"}]} |
| response.data.category | object | 分支约束 | allOf[1]/then/anyOf[1] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.category.id | integer | 必填（所在对象出现时） | allOf[1]/then/anyOf[1] |  | {"minimum":1} |
| response.data.category.name | string | 必填（所在对象出现时） | allOf[1]/then/anyOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.category | null | 分支约束 | allOf[1]/then/anyOf[2] |  |  |
| response.data.uom | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.uom.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.uom.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.company_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.standard_price | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.list_price | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
- `integration`：`implemented`；The shared live read-only smoke verifies the capability against both dedicated isolated database aliases as the ordinary accounting user.；引用：tests/integration/test_reference_object_read_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-product-restore"></a>

## product.restore — 恢复产品

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is registered; Odoo's stock extension reads and writes warehouse orderpoints during product restoration, so availability additionally depends on stock being installed and the configured user holding both product-manager and stock-manager access.
- 内部domain：`accounting_master_data`；来源模型：res.company, product.template, product.product, stock.warehouse.orderpoint；向导：无。
- 必需模块：base, product, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：product.group_product_manager, stock.group_stock_manager；ACL：res.company:read, product.template:read, product.template:write, product.product:read, product.product:write, stock.warehouse.orderpoint:read, stock.warehouse.orderpoint:write。
- 请求/响应合同：`schemas/v1/product.restore.request.schema.json` / `schemas/v1/product.restore.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run product.restore --request "@request.json" --idempotency-key "product.restore:1" --confirm "product.restore"
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
    "product_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["product_id"]} |
| parameters.product_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"product.restore"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"product.restore"} |
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
- `execute`：fixed_company_specific_single_variant_product_restore
- `verify`：same_transaction_active_product_reread_and_response_schema_validation
- `idempotency`：deterministic_product_target_request_key_with_current_active_state_recheck_without_operation_store
- `reverse`：product.archive

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the closed public contract, fixed company and single-variant runtime scope, result validation, registry schemas, and CLI dispatch.；引用：tests/unit/test_product_accounting_write_public.py, tests/unit/test_product_accounting_writes_runtime.py
- `integration`：`implemented`；The guarded shared transactional smoke passed both isolated database aliases as uid 5 with su=False, verifying execution and immediate replay for all eight writes, including an attached orderpoint during archive/restore, plus rollback of business data and temporary product-manager/stock-manager grants.；引用：tests/integration/test_product_accounting_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-product-search"></a>

## product.search — 搜索产品

- 类型：只读；静态状态：`unconfigured`；handler：`product_search`。
- 状态原因：`runtime_context_required` — The fixed handler is implemented; availability is evaluated for each configured database, company, and user at runtime.
- 内部domain：`accounting_master_data`；来源模型：res.company, product.product, product.template, product.category, uom.uom, res.currency；向导：无。
- 必需模块：base, product, uom, stock；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, product.product:read, product.template:read, product.category:read, uom.uom:read, res.currency:read。
- 请求/响应合同：`schemas/v1/product.search.request.schema.json` / `schemas/v1/product.search.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read product.search --request "@request.json"
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
| parameters.query | string/null | 可选（可能有条件限制） |  | 搜索文本 | {"default":null,"maxLength":200} |
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
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"product.search"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/data"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"next_cursor":{"type":"null"}}},"if":{"properties":{"has_more":{"const":true}},"required":["has_more"]},"then":{"properties":{"items":{"minItems":1,"type":"array"},"next_cursor":{"type":"string"}}}}],"required_in_object":["items","has_more","next_cursor"],"resolved_ref":"#/$defs/data"} |
| response.data.items | array | 必填（所在对象出现时） | oneOf[2] |  | {"maxItems":1000} |
| response.data.items[] | object | 每个数组元素 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name","default_code","active","product_type","is_storable","template","category","uom","company_id","currency","standard_price","list_price"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].default_code | string/null | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].active | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].product_type | 未限定 | 必填（所在对象出现时） | oneOf[2] |  | {"enum":["consu","service","combo"]} |
| response.data.items[].is_storable | boolean | 必填（所在对象出现时） | oneOf[2] |  |  |
| response.data.items[].template | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].template.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].template.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].category | 组合/开放结构 | 必填（所在对象出现时） | oneOf[2] |  | {"anyOf":[{"$ref":"#/$defs/named"},{"type":"null"}]} |
| response.data.items[].category | object | 分支约束 | oneOf[2]/anyOf[1] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].category.id | integer | 必填（所在对象出现时） | oneOf[2]/anyOf[1] |  | {"minimum":1} |
| response.data.items[].category.name | string | 必填（所在对象出现时） | oneOf[2]/anyOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.items[].category | null | 分支约束 | oneOf[2]/anyOf[2] |  |  |
| response.data.items[].uom | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].uom.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].uom.name | string | 必填（所在对象出现时） | oneOf[2] | 名称/行说明 | {"minLength":1} |
| response.data.items[].company_id | integer/null | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.items[].currency | object | 必填（所在对象出现时） | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":3,"minLength":1} |
| response.data.items[].standard_price | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].list_price | string | 必填（所在对象出现时） | oneOf[2] |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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
| response.data.items[] | object | 每个数组元素 | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name","default_code","active","product_type","is_storable","template","category","uom","company_id","currency","standard_price","list_price"],"resolved_ref":"#/$defs/item"} |
| response.data.items[].id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].default_code | string/null | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].active | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].product_type | 未限定 | 必填（所在对象出现时） | allOf[1]/then |  | {"enum":["consu","service","combo"]} |
| response.data.items[].is_storable | boolean | 必填（所在对象出现时） | allOf[1]/then |  |  |
| response.data.items[].template | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].template.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].template.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].category | 组合/开放结构 | 必填（所在对象出现时） | allOf[1]/then |  | {"anyOf":[{"$ref":"#/$defs/named"},{"type":"null"}]} |
| response.data.items[].category | object | 分支约束 | allOf[1]/then/anyOf[1] |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].category.id | integer | 必填（所在对象出现时） | allOf[1]/then/anyOf[1] |  | {"minimum":1} |
| response.data.items[].category.name | string | 必填（所在对象出现时） | allOf[1]/then/anyOf[1] | 名称/行说明 | {"minLength":1} |
| response.data.items[].category | null | 分支约束 | allOf[1]/then/anyOf[2] |  |  |
| response.data.items[].uom | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","name"],"resolved_ref":"#/$defs/named"} |
| response.data.items[].uom.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].uom.name | string | 必填（所在对象出现时） | allOf[1]/then | 名称/行说明 | {"minLength":1} |
| response.data.items[].company_id | integer/null | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.items[].currency | object | 必填（所在对象出现时） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","code"],"resolved_ref":"#/$defs/currency"} |
| response.data.items[].currency.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.items[].currency.code | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":3,"minLength":1} |
| response.data.items[].standard_price | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
| response.data.items[].list_price | string | 必填（所在对象出现时） | allOf[1]/then |  | {"maxLength":256,"pattern":"^-?(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]+)?$","resolved_ref":"#/$defs/decimal"} |
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

- `unit`：`implemented`；Unit tests cover the closed request and response, fixed bridge action, company scope, ACL gates, ORM normalization, cursor pagination, and CLI dispatch.；引用：tests/unit/test_core_object_reads.py, tests/unit/test_core_object_reads_bridge.py, tests/unit/test_core_object_reads_runtime.py, tests/unit/test_core_object_read_cli.py, tests/unit/test_capability_registry.py
- `integration`：`implemented`；The shared live read-only smoke verifies the capability against both dedicated isolated database aliases as the ordinary accounting user.；引用：tests/integration/test_reference_object_read_batch_live.py
- `golden`：`planned`；The golden definition is frozen; implementation evidence is pending.；引用：无
- `e2e`：`planned`；The e2e definition is frozen; implementation evidence is pending.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。

<a id="cap-product-tax_profile-get"></a>

## product.tax_profile.get — 查看产品默认税与会计标签

- 类型：只读；静态状态：`unconfigured`；handler：`product_tax_profile_get`。
- 状态原因：`runtime_context_required` — Fixed invoice preparation and product accounting operations are implemented; runtime company, ordinary-user ACL and native accounting recomputation apply.
- 内部domain：`product`；来源模型：res.company, product.product, product.template, account.tax, account.account.tag；向导：无。
- 必需模块：account, product；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：account.group_account_readonly；ACL：res.company:read, product.product:read, product.template:read, account.tax:read, account.account.tag:read。
- 请求/响应合同：`schemas/v1/product.tax_profile.get.request.schema.json` / `schemas/v1/product.tax_profile.get.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 read product.tax_profile.get --request "@request.json"
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
    "product_id": 1
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["product_id"]} |
| parameters.product_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"additionalProperties":false,"allOf":[{"else":{"properties":{"data":{"type":"null"},"error":{"$ref":"response.schema.json#/$defs/error"}}},"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"#/$defs/item"},"error":{"type":"null"},"request_id":{"format":"uuid","type":"string"},"status":{"const":"verified"}}}}],"required_in_object":["schema_version","request_id","success","capability","status","data","warnings","error","odoo","audit"]} |
| response.schema_version | 未限定 | 必填（所在对象出现时） |  |  | {"const":"v1"} |
| response.request_id | string/null | 必填（所在对象出现时） |  |  | {"format":"uuid"} |
| response.success | boolean | 必填（所在对象出现时） |  |  |  |
| response.capability | 未限定 | 必填（所在对象出现时） |  |  | {"const":"product.tax_profile.get"} |
| response.status | string | 必填（所在对象出现时） |  |  | {"minLength":1} |
| response.data | 组合/开放结构 | 必填（所在对象出现时） |  |  | {"oneOf":[{"type":"null"},{"$ref":"#/$defs/item"}]} |
| response.data | null | 分支约束 | oneOf[1] |  |  |
| response.data | object | 分支约束 | oneOf[2] |  | {"additionalProperties":false,"required_in_object":["id","company_id","template_id","sale_tax_ids","purchase_tax_ids","account_tag_ids"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | oneOf[2] | 所选公司ID | {"minimum":1} |
| response.data.template_id | integer | 必填（所在对象出现时） | oneOf[2] |  | {"minimum":1} |
| response.data.sale_tax_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.sale_tax_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.purchase_tax_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.purchase_tax_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
| response.data.account_tag_ids | array | 必填（所在对象出现时） | oneOf[2] |  | {"uniqueItems":true} |
| response.data.account_tag_ids[] | integer | 每个数组元素 | oneOf[2] |  | {"minimum":1} |
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
| response.data | object | 可选（可能有条件限制） | allOf[1]/then |  | {"additionalProperties":false,"required_in_object":["id","company_id","template_id","sale_tax_ids","purchase_tax_ids","account_tag_ids"],"resolved_ref":"#/$defs/item"} |
| response.data.id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.company_id | integer | 必填（所在对象出现时） | allOf[1]/then | 所选公司ID | {"minimum":1} |
| response.data.template_id | integer | 必填（所在对象出现时） | allOf[1]/then |  | {"minimum":1} |
| response.data.sale_tax_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.sale_tax_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.purchase_tax_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.purchase_tax_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
| response.data.account_tag_ids | array | 必填（所在对象出现时） | allOf[1]/then |  | {"uniqueItems":true} |
| response.data.account_tag_ids[] | integer | 每个数组元素 | allOf[1]/then |  | {"minimum":1} |
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

<a id="cap-product-update"></a>

## product.update — 更新产品

- 类型：写入；静态状态：`unconfigured`；handler：`core_write`。
- 状态原因：`runtime_context_required` — The fixed handler is registered; availability depends on runtime configuration, company-scoped product data, and product-manager access.
- 内部domain：`accounting_master_data`；来源模型：res.company, product.category, uom.uom, product.template, product.product；向导：无。
- 必需模块：base, product, uom；配置项：database_alias, company_allowlist, user_mapping；公司条件：`required`。
- 权限组：product.group_product_manager；ACL：res.company:read, product.category:read, uom.uom:read, product.template:read, product.template:write, product.product:read, product.product:write。
- 请求/响应合同：`schemas/v1/product.update.request.schema.json` / `schemas/v1/product.update.response.schema.json`。

### 调用方式

```bash
odoo-accounting-cli-v4 write run product.update --request "@request.json" --idempotency-key "product.update:1:663c40c5fc625d44d00a597ae77ce292" --confirm "product.update"
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
    "product_id": 1,
    "changes": {
      "name": "Example"
    }
  }
}
```

### 请求参数（公共context与信封见总指南）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| parameters | object | 必填 |  |  | {"additionalProperties":false,"required_in_object":["product_id","changes"]} |
| parameters.product_id | integer | 必填（所在对象出现时） |  |  | {"minimum":1} |
| parameters.changes | object | 必填（所在对象出现时） |  | 仅提交拟变更字段，非整条记录 | {"additionalProperties":false,"minProperties":1} |
| parameters.changes.name | string | 可选（可能有条件限制） |  | 名称/行说明 | {"maxLength":256,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","resolved_ref":"#/$defs/text256"} |
| parameters.changes.default_code | string | 可选（可能有条件限制） |  |  | {"maxLength":64,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","resolved_ref":"#/$defs/text64"} |
| parameters.changes.product_type | 未限定 | 可选（可能有条件限制） |  |  | {"enum":["consu","service"]} |
| parameters.changes.category_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.changes.uom_id | integer | 可选（可能有条件限制） |  |  | {"minimum":1} |
| parameters.changes.barcode | string/null | 可选（可能有条件限制） |  |  | {"maxLength":64,"minLength":1,"pattern":"^(?:\\S&#124;\\S[\\s\\S]*\\S)$(?![\\s\\S])","resolved_ref":"#/$defs/nullableText64"} |
| parameters.changes.sale_ok | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.changes.purchase_ok | boolean | 可选（可能有条件限制） |  |  |  |
| parameters.changes.list_price | string | 可选（可能有条件限制） |  |  | {"maxLength":256,"pattern":"^(?:0&#124;[1-9][0-9]*)(?:\\.[0-9]*[1-9])?$(?![\\s\\S])","resolved_ref":"#/$defs/nonnegativeDecimal"} |

### 返回字段（包含成功/失败条件分支）

| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |
|---|---|---|---|---|---|
| response | object | 必填 |  |  | {"allOf":[{"$ref":"response.schema.json"},{"properties":{"capability":{"const":"product.update"},"data":{"oneOf":[{"type":"null"},{"$ref":"core-write-result.schema.json"}]}}},{"if":{"properties":{"success":{"const":true}},"required":["success"]},"then":{"properties":{"data":{"$ref":"core-write-result.schema.json"},"error":{"type":"null"},"status":{"const":"verified"}}}}]} |
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
| response.capability | 未限定 | 可选（可能有条件限制） | allOf[2] |  | {"const":"product.update"} |
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
- `execute`：fixed_company_specific_single_variant_product_update
- `verify`：same_transaction_updated_variant_and_template_reread_and_response_schema_validation
- `idempotency`：deterministic_product_target_and_changes_digest32_request_key_with_current_target_state_recheck_without_operation_store_or_intermediate_change_protection
- `reverse`：product.update_with_prior_values

### 已登记测试与证据范围

- `unit`：`implemented`；Focused tests cover the nonempty basic-field update contract, fixed company and single-variant runtime scope, result validation, registry schemas, and CLI dispatch.；引用：tests/unit/test_product_accounting_write_public.py, tests/unit/test_product_accounting_writes_runtime.py
- `integration`：`implemented`；The guarded shared transactional smoke passed both isolated database aliases as uid 5 with su=False, verifying execution and immediate replay for all eight writes plus rollback of business data and temporary product-manager/stock-manager grants.；引用：tests/integration/test_product_accounting_write_batch_live.py
- `golden`：`planned`；Golden examples are deferred until the capability library reaches target coverage.；引用：无
- `e2e`：`planned`；Natural-language routing is outside this capability batch.；引用：无

登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。
