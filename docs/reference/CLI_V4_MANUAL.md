# CLI V4 全部命令与 JSON 接口说明书

快照日期：2026-10-03（Asia/Shanghai）。版本：0.0.0/bootstrap，非生产发布。

本书覆盖当前全部 **559** 个注册能力，其中 **544** 个有实现，**15** 个禁用/预留。已实现包括253个读取、291个写入；注册总数还包括禁用项。注册状态是环境无关的静态声明，不等于所选用户有权限或每个接口已经完成真实全流程测试。

依据：当前本地注册表、所有请求/响应 Schema、CLI路由和纯参数校验器。源码基线：067404fb2cfc13cf87c263ef95ab8faed6de1bde；registry canonical SHA-256：182788e5679566370f436aede47beb356d3304dae3f94ffd59ce03b256123fc1；文件 SHA-256：9746e25f3350f95a3f408f50fffe4bd442430ea96256173500a0a41ddfc58d83。不依赖 Pi，不建立新审批/服务，不执行 Odoo 业务操作。

> 新会话先读下方快速上手，再到业务场景选能力ID。不能把本书中的合成ID、示例幂等键或`verified`字段当成真实执行证据。每次写入须先确认授权/对象/精确参数，再为实际请求重新计算幂等键。


文档快照：2026-10-03；对应当前 `0.0.0` / `bootstrap` 接口。全量业务分类、每个能力的参数与返回字段见[说明书主入口](CLI_V4_MANUAL.md)。本文说明怎样正确调用，不表示全部能力已经在当前用户、公司或生产环境验收。

## 新会话快速上手／复制这段给 Agent

> 1. 先运行本地 `version`、`capabilities list`；选准确 ID 后 `capabilities describe <ID>`，按当前契约填参数，不猜旧接口。
>
> 2. 沿用已有 `ODOO_ACCOUNTING_CLI_V4_CONFIG`（未设置则默认路径）；只用获准的 alias/company/user，不读取或输出秘密配置，不把 Pi 当必需组件。
>
> 3. 使用完整 v1 request envelope；读取走 `read <ID> --request @文件` 或 `--request -` 加 stdin，不传裸 parameters。完整例子见下方。
>
> 4. 先读取选择可见真实 ID。写前取得用户对具体变更的许可；只用 `write run`，`--confirm` 精确等于 ID，不自行批准、加权限或改原生插件。
>
> 5. 写键通过离线 `request_key.py` 取得；特殊操作键由用户明确指定。不猜 hash，不以 `request_id` 代替；参数变动重新校验。
>
> 6. 超时或回执不明先读回，不换键盲重试。`doctor`、分阶段审批、`operations` 未实现，不能用它们获取审批或收据。
>
> 7. 这是当前 `0.0.0` 快照；注册表及 fixture 验收不等于全部 544 个处理器外部 E2E 或生产可用，资产/多期递延等未完成边界必须保留。

下面是完整的只读例子。**所有上下文值都是合成示例**：执行前将 `v4-dev`、公司 `1`、`synthetic-accountant`、语言和时区改成已有配置及 Odoo 中允许的值，不新建账号或改配置来迎合示例。它只读取科目，不会创建会计业务。

先核对本地元数据；这三条不连接 Odoo：

```text
odoo-accounting-cli-v4 version
odoo-accounting-cli-v4 capabilities list
odoo-accounting-cli-v4 capabilities describe account.account.list
```

Linux / Bash，完整 stdin 调用：

```bash
odoo-accounting-cli-v4 read account.account.list --request - <<'JSON'
{
  "schema_version": "v1",
  "request_id": "12345678-1234-4234-8234-123456789abc",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "synthetic-accountant",
    "language": "en_US",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {"limit": 20, "cursor": null}
}
JSON
```

Windows / PowerShell，完整 stdin 调用：

```powershell
@'
{
  "schema_version": "v1",
  "request_id": "12345678-1234-4234-8234-123456789abc",
  "context": {
    "database": "v4-dev",
    "company_id": 1,
    "user_login": "synthetic-accountant",
    "language": "en_US",
    "timezone": "Asia/Shanghai"
  },
  "parameters": {"limit": 20, "cursor": null}
}
'@ | odoo-accounting-cli-v4 read account.account.list --request -
$LASTEXITCODE
```

也可以把同一个 JSON 用编辑器保存为 UTF-8、无 BOM 的 `requests/accounts.json`，然后调用：

```text
odoo-accounting-cli-v4 read account.account.list --request @requests/accounts.json
```

含空格的路径要把整个 `@路径` 作为一个参数，例如 `--request "@requests/account list.json"`。`account.account.list` 当前只接受 `limit`、`cursor`；不要给它添加猜测的 `query` 或科目类型筛选。

上面的 stdin 示例为 ASCII 字符，不依赖中文管道编码。中文参数优先使用无 BOM 的 UTF-8 `@文件`；旧 PowerShell 默认管道编码可能损坏中文。自动化若按 UTF-8 解析 stdout，可在当前进程设置 `$env:PYTHONUTF8 = '1'`，中文 stdin 管道同时将 `$OutputEncoding` 设为 `[System.Text.UTF8Encoding]::new($false)`；接收端也按 UTF-8 解码。这是 Python/终端编码前提，不是新的 CLI 配置开关。

若没有运行配置，业务调用会返回 `unconfigured`，进程退出码 `4`；配置存在但示例别名、公司或用户不在允许范围内，会分别被拒绝。不要把此结果误解为科目能力未实现。

## 1. 程序入口与运行环境

### 1.1 优先使用已安装入口

公开可执行名是 `odoo-accounting-cli-v4`；同一 Python 环境也可用：

```text
python -m odoo_accounting_cli_v4 --help
```

当前包要求 Python `>=3.12,<3.13`，运行依赖以 `pyproject.toml` 为准。安装 CLI 不等于安装 Odoo、配置桥接或授权业务用户；不要为解决配置错误随意安装 addon、重启服务或修改账套。

源码尚未安装时，且依赖已经在当前 Python 环境中准备好，可在仓库根目录使用模块入口。PowerShell：

```powershell
$env:PYTHONPATH = (Resolve-Path ./src).Path
python -m odoo_accounting_cli_v4 read account.account.list --request @requests/accounts.json
```

Linux / Bash：

```bash
PYTHONPATH=src python3 -m odoo_accounting_cli_v4 read account.account.list --request @requests/accounts.json
```

这些源码命令仍需上面的完整请求文件和已批准的桥接配置；`PYTHONPATH` 不是配置、登录或权限的替代。已安装包的发布校验应避免源码回退，不能用这组开发入口证明离线安装完整性。

### 1.2 配置路径和桥接边界

公开 CLI 读取环境变量 `ODOO_ACCOUNTING_CLI_V4_CONFIG`。未设置或为空时，默认读 `/etc/odoo-accounting-cli-v4/runtime.json`。**没有公开的 `--config`、`--database`、`--company` 或 `--sudo` 开关**；请求上下文不能越过配置 allowlist。

新会话应先确认当前进程是否继承了这个环境变量，以及配置文件是否为已批准的现有文件；不要在日志、聊天或文档里粘贴配置正文、Odoo 密钥或连接秘密。环境变量未设置不必然表示未配置：默认文件仍可能有效。不要未经授权覆盖默认文件。

运行配置是严格 JSON，顶层仅有 `config_schema_version`、`bridge`、`aliases`：

| 配置位置 | 当前规则及作用 |
| --- | --- |
| `config_schema_version` | 精确为 `v1`。 |
| `bridge.argv` | 非空字符串数组，第一个是绝对可执行文件路径；以 `shell=False` 启动既有桥接程序，不是任意 shell 命令文本。 |
| `bridge.timeout_seconds` | 整数 `1..300`，桥接子进程超时。 |
| `aliases.<别名>.database` | 当前代码仅允许隔离库 `odoo_cli_v4_dev`、`odoo_cli_v4_e2e`；不是任意生产数据库连接器。 |
| `aliases.<别名>.companies` | 规范正整数的字符串公司键，对应非空、无重复的允许登录名列表。 |

`context.database` 填**别名**，不是自行指定真实数据库名；别名不必固定叫 `v4-dev`。业务执行使用配置中允许的 Odoo 用户，并受其实际公司、ACL 和 record rules 限制。原生方法自己的内部行为仍由 Odoo 决定，不能把 CLI 的普通用户边界解释为所有原生 helper 都没有内部提权。

桥接部署中的 `--runtime-config`、`--odoo-config`、`--odoo-source` 是桥接启动参数，不是公开 CLI 参数。正常调用者只沿用管理员已准备的配置；Pi 可以是另行集成的入口，但不是本 CLI 的运行前提。

## 2. 所有顶层命令及实现状态

下表中的 `CAP_ID` 是准确注册 ID，`SOURCE` 仅为 `@FILE` 或 `-`。每个命令还可以追加 `--help`；帮助输出是普通文本，不是 JSON 回执。

| 命令语法 | 当前行为 |
| --- | --- |
| `--help`、各子命令 `--help` | 本地帮助，退出 `0`；列出语法不代表对应业务已实现。 |
| `version` | 本地单行 JSON，当前为 `{"product":"odoo-accounting-cli-v4","status":"bootstrap","version":"0.0.0"}`；不是通用响应 envelope，也不是生产发布承诺。 |
| `capabilities list` | 本地注册表清单、摘要、访问类型、状态、required slots 和注册表 digest。 |
| `capabilities describe CAP_ID` | 本地描述符、完整 request/response schema、权限/模块前提、策略及测试元数据。未知 ID 返回不可用。 |
| `read CAP_ID --request SOURCE` | 执行绑定的读取处理器，校验请求、原生用户范围和返回契约。写能力不能走此入口。 |
| `write run CAP_ID --request SOURCE --idempotency-key KEY --confirm CAP_ID` | 执行固定白名单写能力；成功的桥接事务提交，**不是预览或 dry-run**。读取能力不能走此入口。 |
| `doctor` | 命令入口保留，当前 `command_unavailable`，退出 `4`；不能拿它检查现有部署健康。 |
| `write prepare CAP_ID --request SOURCE --idempotency-key KEY` | 分阶段入口尚未实现，`command_unavailable` / `4`。 |
| `write approve OPERATION_ID --approval APPROVAL_SOURCE` | 同上；当前没有实现的审批存储或自批准通道。 |
| `write execute OPERATION_ID` | 同上；不是 `write run` 的替代调用方式。 |
| `operations get OPERATION_ID` | 同上；不能依赖它查询丢失写回执。 |
| `operations verify OPERATION_ID` | 同上；没有实现的统一操作验真服务。 |
| `operations reverse OPERATION_ID --request SOURCE` | 同上；撤销应查找该业务已实现的具体反向能力，不能通用回滚已提交事务。 |

当前快照有 **559 个注册 ID**，其中 **544 个绑定处理器**（读取 253、写入 291）；其余 15 个无处理器。全部注册 ID 的访问类型合计是读取 260、写入 299，两个计数口径不能混用。

当前静态状态为 465 `unconfigured`、79 `degraded`、15 `disabled`。`unconfigured` 通常表示按请求的数据库、公司、用户评估，不是静态判定该能力不能用；`degraded` 要阅读其 `reason_code`、幂等/反向策略和成功时的 `warnings`；`disabled` 不可执行。描述符中 `tests.*.status=implemented` 只是证据索引，不是当前用户可用性、全外部 E2E 或全部业务分支验收。

## 3. 通用请求：先 envelope，再能力参数

每个请求都要有以下四个顶层键，不能省略 `context` 或把参数放在顶层：

| 字段 | 规则 |
| --- | --- |
| `schema_version` | 精确字符串 `v1`。 |
| `request_id` | UUID 字符串，按 schema 使用规范 UUID 形式；用于关联请求，不是写操作幂等键。 |
| `context.database` | 已配置的数据库别名。 |
| `context.company_id` | 正整数公司 ID，不接受布尔值。 |
| `context.user_login` | 已配置且可用的 Odoo 登录名，不是密码、OS 用户或任意 UID。 |
| `context.language` | Odoo 中有效且启用的语言代码；不是中文命令别名。 |
| `context.timezone` | 有效时区名称。 |
| `parameters` | 能力专用对象。只接受该能力 schema 及校验器规定的字段、类型、枚举、互斥关系。 |

同名对象键重复、无效 JSON、非对象根节点、未知字段会被拒绝。请求最大为 1 MiB；文件来源必须可读取且为普通文件。`--request '{"parameters":...}'` 这种内联 JSON 参数不受支持，必须经 stdin 或 `@文件`。

常见参数不能跨能力类推：

- 很多金额和数量使用十进制**字符串**，不是 JSON 浮点数；正负、非零、精度限制分别看具体 schema。例如当前 `customer_invoice.create` 的行数量允许非零有符号值，不能泛化成“所有数量必须正数”。
- 日期一般为 `YYYY-MM-DD`；ID 为正整数；枚举必须精确匹配。不要把标签名称当作 ID，也不要把 `false` 写成字符串 `"false"`。
- 省略、`null`、`false`、空数组并不通用等价：有的字段允许 `null` 表示不筛或清空，有的显式 `null` 会拒绝，有的 `false` 本身是有效筛选条件。按当前能力定义填写。
- 不存在一个通用 `filters` 包装、任意 ORM `domain`、`model/method` 或 `sudo` 入口；需要的能力不在注册表时应报告缺口，不能绕过固定路由。

### 字段表与组合约束怎么读

每条能力的字段表展开了数组元素、嵌套对象与本地 `$ref`。字段路径的 `[]` 表示每个数组元素；“必填（所在对象出现时）”不表示这个父对象无条件必填。带 `oneOf[n]`、`then`、`else` 的行只在相应分支中解释，必须同时检查父级规则，不能把所有分支字段都一并塞进请求。

`oneOf` 要恰好符合一个分支；`anyOf` 要符合至少一个；`allOf` 要同时符合全部约束。`if/then/else` 是条件校验，`not` 是禁止条件，`dependentRequired` 表示提供某字段时必须同时提供关联字段。`additionalProperties=false` 禁止额外键。`enum`、`const`、数值/长度范围与正则都要遵守；`default` 是合同中的默认值声明，不代表 JSON Schema 会替调用者自动填值。省略与 `null` 的区别仍以具体校验器为准。

无法从字段名称确定业务含义时，保留“不确定”并查该能力的描述、来源模型和精确 Schema，不能把税率当金额、把报告行标识当业务记录 ID，或猜测删除/替换的范围。

### 3.1 分页

对于返回 `data.items`、`data.has_more`、`data.next_cursor` 的读取：首请求不带有效 cursor 或填 `null`；后续将返回的 `next_cursor` 原样写入下一份请求。保留上下文和绑定筛选，不自行解码、拼接或伪造 cursor。筛选改变后从第一页开始；改筛选沿用旧 cursor 可能返回 `invalid_cursor`。

上述三项位于对应能力的 `data` 对象，不是响应 envelope 顶层。不同能力的返回结构可能是单对象、汇总数组或其他专用结构，不能强行按分页处理。第一页为空也不自动说明记录不存在：需要区分权限、公司、筛选和确实无数据。

### 3.2 读取 ID 参数不要猜

这些精确名称可作为后续读回导航；实际 ID 必须来自当前普通用户可见的查询或写结果：

| 读取能力 | `parameters` 的目标 ID 键 |
| --- | --- |
| `invoice.get`、`invoice.payment_status.inspect` | `invoice_id` |
| `payment.get` | `payment_id` |
| `journal_entry.get` | `entry_id` |
| `bank.statement.get` | `bank_statement_id`，不是 `statement_id` |
| `bank.transaction.get`、`bank.transaction.reconciliation.get` | `transaction_id` |
| `journal_item.reconciliation.inspect` | `journal_item_id` |
| `reconciliation.partial.get` | `partial_reconcile_id` |
| `reconciliation.full.get` | `full_reconcile_id` |
| `sale.order.get`、`purchase.order.get` | `order_id` |
| `asset.get` | `asset_id` |

这张表不表示其他更新/删除能力也使用同一键；例如写入中的 `move_id` 与上述 `invoice_id` 不应互换。

## 4. 通用响应、错误与退出码

除 `--help` 和 `version` 例外，正常命令结果在 stdout 输出**一个物理行的 JSON**；不要把 stderr 合并到 JSON 输入解析，也不要将 JSON 美化后误认为 CLI 原始回执。严重注册表或内部失败可能另在 stderr 输出简短提示。

| 顶层字段 | 含义 |
| --- | --- |
| `schema_version`、`request_id` | 契约版本与可取得的请求 ID；元数据命令或请求尚未通过校验时 ID 可为 `null`。 |
| `success`、`status` | 成功布尔值与本次执行状态；成功通常为 `verified`，不是注册表静态状态。 |
| `capability` | 本次准确能力 ID；CLI/注册表级错误可能是相应命令标识。 |
| `data` | 成功时为该能力规定的对象；失败时为 `null`。不能统一假设有 `result.id` 或 `items`。 |
| `warnings` | 警告数组；成功也可能有 `capability_degraded`，不可丢弃。 |
| `error` | 成功为 `null`；失败含 `code`、`message`、`details`、`retryable`。 |
| `odoo` | `database`、`company_id`、`user_id`、`model`、`record_ids`；没有完成身份核实时可为空，不是额外授权。 |
| `audit` | `operation_id`、`idempotency_key`、`verification`；可能为 `null`，不是已实现审批或持久操作账本的证明。 |

退出码在进程层取得：PowerShell 查看 `$LASTEXITCODE`，Bash 在调用后立即查看 `$?`。`error` 对象没有通用 `exit_code` 字段。

| 退出码 | 状态 / 典型原因 | 调用者处理 |
| --- | --- | --- |
| `0` | 命令成功或帮助输出。 | 业务结果仍需检查 `success`、警告及实际读回。 |
| `2` | `invalid`：参数、请求、cursor、确认或幂等键无效。 | 按具体 schema/错误修正，不能猜下一组字段反复试写。 |
| `3` | `denied`：访问类型、公司、用户、实际权限等拒绝。 | 报告所需权限，不自行加组或 sudo。 |
| `4` | `unavailable`：未配置、未知/禁用能力、未实现命令、别名不存在等。 | 区分缺配置与缺能力；记录依赖，不扩展到生产库。 |
| `5` | `conflict`：目标状态或幂等意图冲突。 | 先读回并重新确认目标，不换键绕过状态冲突。 |
| `6` | `failed`：映射的业务执行失败。 | 保留错误及相关读回，核实原生规则和前提。 |
| `7` | `failed`：桥接、配置格式、超时、协议或内部运行失败。 | 不输出秘密诊断；写调用回执不明时先核实是否已提交。 |
| `8` | `failed_validation`：注册表或结果契约验证失败。 | 不信任不合约的结果；停止继续业务串联并报告。 |

例如未配置时的**结构示意**如下，非一次真实 Odoo 执行记录；程序实际输出为单行：

```json
{
  "schema_version": "v1",
  "request_id": "12345678-1234-4234-8234-123456789abc",
  "success": false,
  "capability": "account.account.list",
  "status": "unavailable",
  "data": null,
  "warnings": [],
  "error": {
    "code": "unconfigured",
    "message": "No matching Odoo bridge configuration is active.",
    "details": {},
    "retryable": false
  },
  "odoo": {"database": null, "company_id": null, "user_id": null, "model": null, "record_ids": []},
  "audit": {"operation_id": null, "idempotency_key": null, "verification": null}
}
```

## 5. 写入、确认、幂等和回执不明

### 5.1 写前最低约定

先 `describe` 获取精确契约，再读当前目标及引用 ID，向用户说明具体变更、公司、金额/日期与风险。仅在得到该变更的授权后才运行 `write run`。`--confirm CAP_ID` 必须精确等于正在执行的 ID；这是防误调用校验，**不是权限提升、审批系统或 Agent 自批准依据**。

业务写入不是测试 fixture：成功的桥接事务会提交。CLI 没有通用 dry-run 开关；各能力的 `strategies.preview` 也不能被误读为当前存在 `write prepare`。读路由一般为只读事务；少数原生报告或 inspect 需要临时计算/向导，以 rollback-only 事务执行，不应宣称所有读取都是完全没有临时 ORM 写入。

### 5.2 从实际代码获取键，不手写算法

写入键语法为 8–128 个安全字符：首字符为字母或数字，其后可为字母、数字、`.`、`_`、`:`、`-`。仅满足语法不表示键符合该能力的语义。

固定核心写入有两类：一类必须精确匹配当前 SDK 对**归一化参数**计算的预期键；另一类使用调用者显式操作键以区分业务轮次。重复创建、部分款、批次基线等差异由能力代码决定，不能统一使用随机 UUID、原始 JSON hash、`request_id` 或 `capability:record_id`。

本说明书提供[离线请求键助手](cli-v4-manual/request_key.py)，在仓库根目录使用已有 Python 环境：

```text
python docs/reference/cli-v4-manual/request_key.py CAP_ID request.json [USER_OPERATION_KEY]
```

`CAP_ID`、文件名和方括号内参数是语法占位，不是可直接执行的业务例子。确定性键无需第三参数；助手要求调用者键时，第三参数必须来自用户认可的独立操作意图。助手只加载本地 registry/schema 和校验/键函数，不创建端口、不连接 Odoo、不写业务；失败时 stderr 提示且退出非零，成功 stdout 只有键。

取得键后必须检查助手退出码，再与人工批准的请求一同使用：PowerShell 可用 `$key = (& python docs/reference/cli-v4-manual/request_key.py $cap $requestFile)`，立即检查 `$LASTEXITCODE -ne 0` 并停止；Bash 可用 `key=$(python docs/reference/cli-v4-manual/request_key.py "$cap" "$request_file") || exit $?`。**这不是写命令，也不是获得批准**；该能力需要调用者操作键时提供第三参数，失败不能擅自猜键绕过。

助手使用私有源码 API，仅为本 `0.0.0` 快照的文档示例，不是额外注册的 CLI 命令。升级包、修改参数或改变有意义的业务基线后重新校验键；先阅读主说明书对应能力的键规则。实际写语法见第 2 节，本指南不提供可误粘贴执行的合成业务写入请求。

### 5.3 幂等不是无条件 exactly-once

- 成功数据里的 `idempotent_replay` 表示该能力按自身规则识别了当前可证明的重复；不表示有统一持久 operation store、全局事务收据或数据库级并发唯一保证。
- 同一个键不得移作另一业务意图。目标已被其他人修改、来源关系改变或显式参数漂移时，原键也可能冲突；不能强行恢复历史中间状态。
- 删除没有通用 tombstone。重试时记录不存在，不能仅凭“不存在”证明前次删成功。新增多行的基线匹配也不是持久事务标记。
- 超时、断连、CLI 结果验证失败或输出丢失可能发生在桥接提交之后。`success=false`、非零退出码或 `retryable` 单项都不足以证明没有写入。
- 回执不明时保留请求、键、时间和错误，使用已有读取/关联检查核实目标图；无法确认则明确报告“回执未知”并请求人工处理，不新建键重做，不调用尚未实现的 `operations get` 假装找到了收据。
- 撤销必须使用适合当前状态的准确能力，如 `reconciliation.undo`、`bank.transaction.unmatch`、`journal_entry.reverse`；取消、重置草稿、现金退款与会计冲销不是同一业务动作。

## 6. 八类典型业务流程导航

以下是**调用顺序与核对点**，不是自动执行脚本。每一步都先 `describe`，用该步骤的专用参数；写入须单独获得相应授权。所有记录 ID 由实际可见数据提供，不能把示例数字照搬到业务。

### 6.1 发现账号、账套及必要基础资料

先读 `user.accounting_access.inspect`、`company.accounting_context.list`、`company.accounting_configuration.inspect`、`diagnostic.accounting_environment.inspect`；再按需求选 `account.account.list`、`journal.list`、`partner.accounting.search`、`tax.list`、`payment_term.list`、`fiscal_position.resolve`、`product.accounting_profile.get`。

核对当前用户、公司、可见资料及必要日记账/默认科目，不将“能写分录”推成“能维护会计配置”。`account.account.create`、`journal.create`、`tax.create` 等配置维护需要各自权限及明确授权。报缺配置时应说明前提，不偷偷补权限或改默认银行账户。

### 6.2 客户开票、应收、部分收款与结清

普通链路：`customer_invoice.create` → 草稿读取 `invoice.get` → 需要时 `invoice.update` / `invoice.line.update` / `invoice.lines.update` → `invoice.post` → `receivable.payment.register` → `payment.get`、`invoice.payment_status.inspect`、`receivable.open_items.list`。

草稿批量行维护另有 `invoice.lines.add`、`invoice.lines.remove`；`invoice.lines.replace` 是重建业务行的替换，不是保留 ID 的稀疏 patch。来源销售行的修改限制仍保留。由订单开票可导航 `sale.order.invoice.create` 和 `sale.order.line.get`，不要把订单所有数量、历史发票或草稿/已过账数量混为一谈。

核对币种、税、到期日、原生总额/残余、实际付款和核销图。部分付款或分期不应被断言为所有选中发票都结清；原生分组决定单付款或逐期付款。登记收款不等于实际银行转账，付款的辅助发票关联也不能代替真实 partial/full 核销图。

### 6.3 供应商账单、应付与付款

普通链路：`vendor_bill.create` → `invoice.get` / 草稿编辑 → `invoice.post` → `payable.payment.register` → `payment.get`、`invoice.payment_status.inspect`、`payable.open_items.list`。来源采购可用 `purchase.order.get`、`purchase.order.line.get`、`purchase.order.bill.create`、`purchase_bill.matching.inspect` 核对会计单据关系。

核对应付方向、科目、原生可开票数量、税及币种；不能仅看采购单订购数量推出可开票全部数量。行单位和可抵扣百分比按该能力合同与原生产品单位检查，不能假设可抵扣率变化必然降低账单总税额。多期自动递延受阻的采购场景不得因普通账单付款通过而记为完成。

### 6.4 财务贷项、退款与付款差额

来源单据读取后，根据业务使用 `customer_credit_note.create` 或 `vendor_refund.create`；之后读取原单与新单的 `invoice.get`，按授权过账、核销或登记现金退款，检查余额、来源关联及实际付款方向。客户退款常涉及 outbound、供应商退款常涉及 inbound，具体由原生单据方向决定。

未收付单的财务贷项与已收付单的现金退款不同；贷项不代表实物退货。发票/账单少付差额通过 `receivable.payment.register` / `payable.payment.register` 的 `payment_difference_handling`、`writeoff_account_id` 等精确合同处理；`reconciliation.write_off` 是银行流水差额能力，不能替代前者。读回差额账户、实际金额、平衡及残余，不能只看操作成功。

### 6.5 手工凭证、纠错与普通期间调整

`journal_entry.create` → `journal_entry.get` → `journal_entry.update` / `journal_entry.lines.update` / `journal_entry.lines.replace` → `validation.journal_entry.check` → `journal_entry.post`。需要冲销时使用 `journal_entry.reverse`，再读取源单和冲销单、`journal_item.search`。

核对分录平衡、日期、公司、科目、外币与反向来源。启用 storno 时原生借贷总额可能为负，不能一律按正数验证冲销金额。草稿生命周期按各能力允许状态处理，不能修改已过账单据来回避锁账或哈希规则。

普通期间调整可以是正常调整凭证，但这不等于精确 ID `period.adjustment.create` 已实现，也不等于最终锁期。`company.lock_dates.inspect` 可读取边界；`period.lock.change`、`validation.period_close.check` 当前无处理器。

### 6.6 银行流水、对账单与实际核销图

先读 `journal.get` 和必要配置；合规记录流水用 `bank.transaction.record`，归组可用 `bank.statement.create` / `bank.statement.update`，读回 `bank.statement.get`、`bank.transaction.search`。实际匹配前读 `bank.transaction.match_candidates.list` 和 `bank.transaction.reconciliation.get`；授权后 `bank.transaction.match`，再读 `payment.get` 及银行关系。撤销用 `bank.transaction.unmatch` 并核对关系和残余恢复。

会计核销链：`reconciliation.candidates.list` → `reconciliation.apply` 或 `reconciliation.automatic.run` → `journal_item.reconciliation.inspect`、`reconciliation.partial.get`、`reconciliation.full.get`；需要时 `reconciliation.undo`，读回全部受影响成员。

核销涉及真实财务行的余额及完整匹配组，不能仅凭 memo 或候选列表认定匹配完成。必要 liquidity/outstanding/suspense 配置必须先已适用；事务内合成银行正例不证明现有业务银行配置合适。不要顺手发送支付、接银行网络或重配账套。

### 6.7 账簿、财务报表、导出与分析

账簿可选 `report.trial_balance`、`report.general_ledger`、`report.partner_ledger`、`report.journal`；财报可选 `report.balance_sheet`、`report.profit_and_loss`、`report.cash_flow`；未结分析可选 `report.aged_receivable`、`report.aged_payable`、`report.tax`。使用确实存在的对应 `.export` ID，如 `report.trial_balance.export`；不是所有报告都可凭名称自动加 `.export`。

业务分析有 `invoice.analysis.search` / `invoice.analysis.summary`、`journal_item.analysis.summary`、`analytic.line.search` / `analytic.line.summary`。分页与 summary、单据币和公司币分别按合同；不要把汇总结果当作实际未结应收或现金到账。

核对期间、公司、科目/日记账等过滤、金额与返回文件的实际字段。报表有数据、导出文件格式/hash 有效、XLSX 金额核对、PDF 页面金额核对是不同证据。财报导出不等于法定申报；`invoice.send`、`report.customer_statement.send`、`report.followup.send` 等外发写能力需另外获得明确发送授权，导出不得自动串联外发。

### 6.8 固定资产、递延、币种及期末：明确未完成边界

可导航 `asset.search`、`asset.get`、`asset.depreciation_schedule.get`、`report.asset`；递延可导航 `invoice.service_dates.get`、`report.deferred_expense`、`report.deferred_revenue`、`deferred_expense.generate_entries`、`deferred_revenue.generate_entries`；币种可导航 `currency.rate.list`、`currency.convert`、`report.multicurrency_revaluation`、`multicurrency.revaluation.generate_entries`。

已知边界必须保留：`asset.validate` 有原生失败记录，`asset.modify`、`asset.resume` 禁用；非零资产完整折旧/处置链未完成。单期手动递延正例不代表多期自动 `invoice.post` 链完成；原生多期失败及未到达的供应商/退款分支仍受阻。普通期末调整、应计/结转能力不证明最终锁期、现金制税完整链、report-bound 税结账或税局送达。

另有 `period.accrual.generate`、`period.transfer.run`、`localization.china.period_transfer.run` 的有界能力；执行前仍需当前原生前提、普通用户权限及授权。借项单 addon 未安装的已知依赖不能用贷项单代替宣布通过。完整范围与历史证据见[核心验收及收尾边界](../execution/ACCOUNTING_ACCEPTANCE.md)，状态以最新记录为准；不得擅自安装原生 addon 或修复生产插件。

## 7. 新会话交接与证据口径

交接至少记录：实际安装版本及 registry digest、准确能力 ID、批准的 alias/company/user 范围、请求 ID、请求参数与写入键、用户授权范围、退出码、完整 JSON 警告/错误、读回所核对的金额/状态/关系。只保留必要业务证据，秘密配置和真实私有日志不贴进公共文档。

把以下情况分开写：已实现接口、当前可用、已验证场景、模拟/fixture 正例、规划/disabled、原生依赖受阻、回执未知。日常核心共享隔离验收并不覆盖所有命令、生产银行配置、真实外发、并发 exactly-once 或全部资产/递延/税务流程。文档中的合成请求是教学数据，不是执行结果。

本次文档只依据本地代码/schema 和离线帮助/元数据核对，没有连接 Odoo、读取真实配置或密钥、执行业务读写、重新运行 native smoke 或修改服务。总目标的暂停状态不因说明书新增而改变。

## 8. 事实来源与更新方式

接口变动时先更新代码和 schema，再重新生成目录/字段并复核指南；历史 README、能力名称、描述符测试状态或此前聊天均不能替代当前合同。

- [CLI 语法、请求加载、分发、错误和未实现入口](../../src/odoo_accounting_cli_v4/cli.py)：`_parser`、`_load_request`、`_status_for_exit`、`_configured_port_factory`、`main`。
- [运行配置](../../src/odoo_accounting_cli_v4/config.py)：`load_runtime_config`、`RuntimeConfig.resolve`、隔离数据库 allowlist。
- [通用响应](../../src/odoo_accounting_cli_v4/contracts.py)、[请求 envelope schema](../../schemas/v1/request.schema.json)、[响应 envelope schema](../../schemas/v1/response.schema.json)。
- [科目读取请求](../../schemas/v1/account.account.list.request.schema.json)及[读取校验器](../../src/odoo_accounting_cli_v4/capabilities/account_account_list.py)：本文完整只读例子的字段和分页规则。
- [固定核心写入合同与键](../../src/odoo_accounting_cli_v4/capabilities/core_writes.py)：`validate_core_write_request`、`_expected_idempotency_key`、`execute_core_write`；[发送类写入校验](../../src/odoo_accounting_cli_v4/capabilities/accounting_delivery.py)。
- [桥接子进程](../../src/odoo_accounting_cli_v4/bridge/client.py)及[原生事务/用户范围](../../src/odoo_accounting_cli_v4/bridge/runtime.py)：固定 action、普通用户环境、读取回滚与写入提交边界。
- [完整注册表](../../capabilities/v1/registry.json)、[包版本及 Python 范围](../../pyproject.toml)、[主说明书](CLI_V4_MANUAL.md)：全量 ID、schema、状态及业务分类导航。

本指南不补实现缺口、不授权执行写入，也不把已安装 `0.0.0` 包描述为完成生产发布。详细参数与键配方以主说明书和当次 `capabilities describe` 为准。


## 全量业务场景目录

### 会计科目、日记账与公司基础配置（42项）

建立和维护科目、科目组、会计标签、日记账及其组，配置公司默认收入费用科目、日记账序列和私人分摊科目。银行流动性、税务、汇兑、账单处理等专项设置按用途放入对应场景；基础配置不替代运行上下文和用户权限检查。

[打开本场景完整接口章节](cli-v4-manual/scenarios/accounting-foundation.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [account.account.archive](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-account-archive) | 停用会计科目 | 写入 | unconfigured |
| [account.account.create](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-account-create) | 创建会计科目 | 写入 | degraded |
| [account.account.default_taxes.assign](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-account-default_taxes-assign) | 设置科目默认税种 | 写入 | unconfigured |
| [account.account.delete](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-account-delete) | 删除未被原生引用阻止的科目 | 写入 | unconfigured |
| [account.account.duplicate](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-account-duplicate) | 复制会计科目配置 | 写入 | unconfigured |
| [account.account.get](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-account-get) | 获取会计科目详情 | 只读 | unconfigured |
| [account.account.list](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-account-list) | 列出当前用户可访问的指定公司会计科目 | 只读 | unconfigured |
| [account.account.non_trade.set](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-account-non_trade-set) | 设置科目非贸易标记 | 写入 | unconfigured |
| [account.account.notes.update](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-account-notes-update) | 更新科目说明和内部备注 | 写入 | unconfigured |
| [account.account.processing_settings.get](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-account-processing_settings-get) | 查看科目高级设置及原生余额 | 只读 | unconfigured |
| [account.account.restore](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-account-restore) | 恢复会计科目 | 写入 | unconfigured |
| [account.account.tags.assign](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-account-tags-assign) | 设置科目报表标签 | 写入 | unconfigured |
| [account.account.update](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-account-update) | 更新会计科目 | 写入 | unconfigured |
| [account.group.create](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-group-create) | 创建会计科目组 | 写入 | degraded |
| [account.group.delete](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-group-delete) | 删除科目组并原生调整子组 | 写入 | unconfigured |
| [account.group.get](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-group-get) | 获取会计科目组详情 | 只读 | unconfigured |
| [account.group.list](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-group-list) | 列出会计科目组 | 只读 | unconfigured |
| [account.group.update](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-group-update) | 更新会计科目组 | 写入 | unconfigured |
| [account.tag.archive](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-tag-archive) | 停用会计标签 | 写入 | degraded |
| [account.tag.create](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-tag-create) | 创建会计标签 | 写入 | degraded |
| [account.tag.get](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-tag-get) | 获取会计标签详情 | 只读 | unconfigured |
| [account.tag.list](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-tag-list) | 列出会计标签 | 只读 | unconfigured |
| [account.tag.restore](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-tag-restore) | 恢复会计标签 | 写入 | degraded |
| [account.tag.update](cli-v4-manual/scenarios/accounting-foundation.md#cap-account-tag-update) | 更新会计标签 | 写入 | degraded |
| [company.default_accounts.assign](cli-v4-manual/scenarios/accounting-foundation.md#cap-company-default_accounts-assign) | 设置公司默认收入费用科目 | 写入 | unconfigured |
| [journal.archive](cli-v4-manual/scenarios/accounting-foundation.md#cap-journal-archive) | 停用会计日记账 | 写入 | unconfigured |
| [journal.configuration.inspect](cli-v4-manual/scenarios/accounting-foundation.md#cap-journal-configuration-inspect) | 检查日记账会计配置 | 只读 | unconfigured |
| [journal.create](cli-v4-manual/scenarios/accounting-foundation.md#cap-journal-create) | 创建会计日记账 | 写入 | unconfigured |
| [journal.delete](cli-v4-manual/scenarios/accounting-foundation.md#cap-journal-delete) | 原生删除日记账 | 写入 | unconfigured |
| [journal.duplicate](cli-v4-manual/scenarios/accounting-foundation.md#cap-journal-duplicate) | 原生复制日记账 | 写入 | unconfigured |
| [journal.get](cli-v4-manual/scenarios/accounting-foundation.md#cap-journal-get) | 获取会计日记账详情 | 只读 | unconfigured |
| [journal.group.create](cli-v4-manual/scenarios/accounting-foundation.md#cap-journal-group-create) | 创建日记账组 | 写入 | unconfigured |
| [journal.group.delete](cli-v4-manual/scenarios/accounting-foundation.md#cap-journal-group-delete) | 删除日记账组 | 写入 | unconfigured |
| [journal.group.get](cli-v4-manual/scenarios/accounting-foundation.md#cap-journal-group-get) | 获取日记账组详情 | 只读 | unconfigured |
| [journal.group.list](cli-v4-manual/scenarios/accounting-foundation.md#cap-journal-group-list) | 列出日记账组 | 只读 | unconfigured |
| [journal.group.update](cli-v4-manual/scenarios/accounting-foundation.md#cap-journal-group-update) | 更新日记账组 | 写入 | unconfigured |
| [journal.list](cli-v4-manual/scenarios/accounting-foundation.md#cap-journal-list) | 列出会计日记账 | 只读 | unconfigured |
| [journal.non_deductible_account.assign](cli-v4-manual/scenarios/accounting-foundation.md#cap-journal-non_deductible_account-assign) | 设置私人分摊科目 | 写入 | unconfigured |
| [journal.processing_settings.get](cli-v4-manual/scenarios/accounting-foundation.md#cap-journal-processing_settings-get) | 查看日记账高级设置和可用发票模板 | 只读 | unconfigured |
| [journal.restore](cli-v4-manual/scenarios/accounting-foundation.md#cap-journal-restore) | 恢复会计日记账 | 写入 | unconfigured |
| [journal.sequence_policy.update](cli-v4-manual/scenarios/accounting-foundation.md#cap-journal-sequence_policy-update) | 设置专用贷项和付款序列 | 写入 | unconfigured |
| [journal.update](cli-v4-manual/scenarios/accounting-foundation.md#cap-journal-update) | 更新会计日记账 | 写入 | unconfigured |
### 客户、供应商、银行账户与往来偏好（27项）

查找和维护往来单位、应收应付科目与会计属性、伙伴银行账户，以及开票交付、账单校验、收付偏好和信用限额。伙伴会计属性和偏好设置不是创建发票、执行支付或实际发送邮件；查询信用暴露可用于判断往来风险。

[打开本场景完整接口章节](cli-v4-manual/scenarios/partners.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [bank.get](cli-v4-manual/scenarios/partners.md#cap-bank-get) | 获取银行主数据详情 | 只读 | unconfigured |
| [bank.list](cli-v4-manual/scenarios/partners.md#cap-bank-list) | 列出银行主数据 | 只读 | unconfigured |
| [company.credit_policy.update](cli-v4-manual/scenarios/partners.md#cap-company-credit_policy-update) | 设置公司信用限额启用选项 | 写入 | unconfigured |
| [partner.accounting.get](cli-v4-manual/scenarios/partners.md#cap-partner-accounting-get) | 获取会计合作伙伴详情 | 只读 | unconfigured |
| [partner.accounting.search](cli-v4-manual/scenarios/partners.md#cap-partner-accounting-search) | 搜索会计合作伙伴 | 只读 | unconfigured |
| [partner.accounting.update](cli-v4-manual/scenarios/partners.md#cap-partner-accounting-update) | 更新伙伴会计属性 | 写入 | unconfigured |
| [partner.archive](cli-v4-manual/scenarios/partners.md#cap-partner-archive) | 归档伙伴 | 写入 | unconfigured |
| [partner.bank_account.archive](cli-v4-manual/scenarios/partners.md#cap-partner-bank_account-archive) | 归档伙伴银行账户 | 写入 | unconfigured |
| [partner.bank_account.create](cli-v4-manual/scenarios/partners.md#cap-partner-bank_account-create) | 创建伙伴银行账户 | 写入 | unconfigured |
| [partner.bank_account.get](cli-v4-manual/scenarios/partners.md#cap-partner-bank_account-get) | 获取合作伙伴银行账户详情 | 只读 | unconfigured |
| [partner.bank_account.restore](cli-v4-manual/scenarios/partners.md#cap-partner-bank_account-restore) | 恢复伙伴银行账户 | 写入 | unconfigured |
| [partner.bank_account.search](cli-v4-manual/scenarios/partners.md#cap-partner-bank_account-search) | 搜索合作伙伴银行账户 | 只读 | unconfigured |
| [partner.bank_account.update](cli-v4-manual/scenarios/partners.md#cap-partner-bank_account-update) | 更新伙伴银行账户 | 写入 | unconfigured |
| [partner.bill_validation_preferences.get](cli-v4-manual/scenarios/partners.md#cap-partner-bill_validation_preferences-get) | 读取供应商账单校验偏好 | 只读 | unconfigured |
| [partner.bill_validation_preferences.update](cli-v4-manual/scenarios/partners.md#cap-partner-bill_validation_preferences-update) | 修改供应商账单校验偏好 | 写入 | degraded |
| [partner.create](cli-v4-manual/scenarios/partners.md#cap-partner-create) | 创建伙伴 | 写入 | degraded |
| [partner.credit_exposure.inspect](cli-v4-manual/scenarios/partners.md#cap-partner-credit_exposure-inspect) | 检查往来单位信用暴露 | 只读 | unconfigured |
| [partner.credit_limit.reset](cli-v4-manual/scenarios/partners.md#cap-partner-credit_limit-reset) | 恢复客户公司默认信用额度 | 写入 | unconfigured |
| [partner.credit_limit.update](cli-v4-manual/scenarios/partners.md#cap-partner-credit_limit-update) | 设置客户信用额度 | 写入 | unconfigured |
| [partner.get](cli-v4-manual/scenarios/partners.md#cap-partner-get) | 获取伙伴详情 | 只读 | unconfigured |
| [partner.invoice_delivery_preferences.get](cli-v4-manual/scenarios/partners.md#cap-partner-invoice_delivery_preferences-get) | 读取客户发票交付偏好 | 只读 | unconfigured |
| [partner.invoice_delivery_preferences.update](cli-v4-manual/scenarios/partners.md#cap-partner-invoice_delivery_preferences-update) | 修改客户发票交付偏好 | 写入 | degraded |
| [partner.payment_preferences.get](cli-v4-manual/scenarios/partners.md#cap-partner-payment_preferences-get) | 读取客户供应商付款偏好 | 只读 | unconfigured |
| [partner.payment_preferences.update](cli-v4-manual/scenarios/partners.md#cap-partner-payment_preferences-update) | 修改客户供应商付款偏好 | 写入 | unconfigured |
| [partner.restore](cli-v4-manual/scenarios/partners.md#cap-partner-restore) | 恢复伙伴 | 写入 | unconfigured |
| [partner.search](cli-v4-manual/scenarios/partners.md#cap-partner-search) | 搜索伙伴 | 只读 | unconfigured |
| [partner.update](cli-v4-manual/scenarios/partners.md#cap-partner-update) | 更新伙伴 | 写入 | unconfigured |
### 产品、类别与会计默认值（17项）

维护产品及类别，查看和设置收入费用科目、默认销售采购税、成本和开票政策，解析实际适用科目，并查阅贸易术语。产品会计配置不是库存数量调整；模板共享政策及多变体限制须按单条接口说明核对。

[打开本场景完整接口章节](cli-v4-manual/scenarios/products.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [incoterm.get](cli-v4-manual/scenarios/products.md#cap-incoterm-get) | 获取国际贸易术语详情 | 只读 | unconfigured |
| [incoterm.list](cli-v4-manual/scenarios/products.md#cap-incoterm-list) | 列出国际贸易术语 | 只读 | unconfigured |
| [product.accounting_profile.get](cli-v4-manual/scenarios/products.md#cap-product-accounting_profile-get) | 读取产品会计配置 | 只读 | unconfigured |
| [product.accounting_profile.update](cli-v4-manual/scenarios/products.md#cap-product-accounting_profile-update) | 更新产品会计配置 | 写入 | unconfigured |
| [product.accounts.resolve](cli-v4-manual/scenarios/products.md#cap-product-accounts-resolve) | 解析产品实际会计科目 | 只读 | unconfigured |
| [product.archive](cli-v4-manual/scenarios/products.md#cap-product-archive) | 归档产品 | 写入 | unconfigured |
| [product.category.accounting_profile.get](cli-v4-manual/scenarios/products.md#cap-product-category-accounting_profile-get) | 查看产品分类会计科目 | 只读 | unconfigured |
| [product.category.accounting_profile.update](cli-v4-manual/scenarios/products.md#cap-product-category-accounting_profile-update) | 更新产品类别会计配置 | 写入 | unconfigured |
| [product.category.list](cli-v4-manual/scenarios/products.md#cap-product-category-list) | 列出产品类别 | 只读 | unconfigured |
| [product.cost.update](cli-v4-manual/scenarios/products.md#cap-product-cost-update) | 更新产品成本 | 写入 | unconfigured |
| [product.create](cli-v4-manual/scenarios/products.md#cap-product-create) | 创建产品 | 写入 | degraded |
| [product.duplicate](cli-v4-manual/scenarios/products.md#cap-product-duplicate) | 复制产品 | 写入 | degraded |
| [product.get](cli-v4-manual/scenarios/products.md#cap-product-get) | 获取产品详情 | 只读 | unconfigured |
| [product.restore](cli-v4-manual/scenarios/products.md#cap-product-restore) | 恢复产品 | 写入 | unconfigured |
| [product.search](cli-v4-manual/scenarios/products.md#cap-product-search) | 搜索产品 | 只读 | unconfigured |
| [product.tax_profile.get](cli-v4-manual/scenarios/products.md#cap-product-tax_profile-get) | 查看产品默认税与会计标签 | 只读 | unconfigured |
| [product.update](cli-v4-manual/scenarios/products.md#cap-product-update) | 更新产品 | 写入 | unconfigured |
### 客户开票、销售来源开票与贷项通知单（8项）

创建客户发票和来源贷项通知单，由销售订单生成发票或预付款发票，配置客户发票编号与可用模板，并检查或加入客户单据发送队列。发票查改和过账使用共用发票场景；贷项通知单不代表已经向客户退现金，发送队列不代表外部邮箱已收到。

[打开本场景完整接口章节](cli-v4-manual/scenarios/customer-invoices.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [customer_credit_note.create](cli-v4-manual/scenarios/customer-invoices.md#cap-customer_credit_note-create) | 创建客户贷项通知单 | 写入 | unconfigured |
| [customer_invoice.create](cli-v4-manual/scenarios/customer-invoices.md#cap-customer_invoice-create) | 创建草稿客户发票 | 写入 | unconfigured |
| [invoice.send](cli-v4-manual/scenarios/customer-invoices.md#cap-invoice-send) | 将客户发票、贷项通知单或收据加入 Odoo 发送队列 | 写入 | degraded |
| [invoice.send.inspect](cli-v4-manual/scenarios/customer-invoices.md#cap-invoice-send-inspect) | 检查客户发票、贷项通知单或收据发送准备状态 | 只读 | unconfigured |
| [journal.invoice_reference.update](cli-v4-manual/scenarios/customer-invoices.md#cap-journal-invoice_reference-update) | 设置发票付款参考格式 | 写入 | unconfigured |
| [journal.invoice_template.assign](cli-v4-manual/scenarios/customer-invoices.md#cap-journal-invoice_template-assign) | 设置可用客户发票模板 | 写入 | unconfigured |
| [sale.order.down_payment.create](cli-v4-manual/scenarios/customer-invoices.md#cap-sale-order-down_payment-create) | 由销售订单创建预付款发票 | 写入 | degraded |
| [sale.order.invoice.create](cli-v4-manual/scenarios/customer-invoices.md#cap-sale-order-invoice-create) | 由销售订单创建客户发票 | 写入 | degraded |
### 供应商账单、采购匹配与供应商退款单（7项）

创建供应商账单和来源退款单，由采购订单生成账单，检查、建立或解除采购行匹配，并配置公司快速录入和账单审核选项。账单查改和过账使用共用发票场景；供应商退款单是信用单据，实际收回现金需走应付收付款接口。

[打开本场景完整接口章节](cli-v4-manual/scenarios/vendor-bills.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [company.bill_processing_policy.update](cli-v4-manual/scenarios/vendor-bills.md#cap-company-bill_processing_policy-update) | 设置公司快速录入和账单自动审核选项 | 写入 | unconfigured |
| [purchase.order.bill.create](cli-v4-manual/scenarios/vendor-bills.md#cap-purchase-order-bill-create) | 由采购订单生成供应商账单 | 写入 | degraded |
| [purchase_bill.lines.unmatch](cli-v4-manual/scenarios/vendor-bills.md#cap-purchase_bill-lines-unmatch) | 取消供应商账单行的采购匹配 | 写入 | unconfigured |
| [purchase_bill.match](cli-v4-manual/scenarios/vendor-bills.md#cap-purchase_bill-match) | 匹配采购行和供应商账单 | 写入 | unconfigured |
| [purchase_bill.matching.inspect](cli-v4-manual/scenarios/vendor-bills.md#cap-purchase_bill-matching-inspect) | 检查采购与供应商账单匹配 | 只读 | unconfigured |
| [vendor_bill.create](cli-v4-manual/scenarios/vendor-bills.md#cap-vendor_bill-create) | 创建草稿供应商账单 | 写入 | unconfigured |
| [vendor_refund.create](cli-v4-manual/scenarios/vendor-bills.md#cap-vendor_refund-create) | 创建供应商退款单 | 写入 | unconfigured |
### 发票和账单共用查询、编辑、过账与导出（43项）

读取和筛选客户发票、贷项通知单、供应商账单及退款单，维护表头、业务行、税额、单位、扣除比例、布局和显示设置，执行过账、撤销到草稿、取消、复制、删除或冲销重开，并导出单据。单行和多行接口的源关联、草稿、成员集合及重放限制以各条合同为准；支付、催款和外币汇率有独立场景。

[打开本场景完整接口章节](cli-v4-manual/scenarios/invoice-common.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [cash_rounding.compute](cli-v4-manual/scenarios/invoice-common.md#cap-cash_rounding-compute) | 计算现金舍入金额与差额 | 只读 | unconfigured |
| [cash_rounding.create](cli-v4-manual/scenarios/invoice-common.md#cap-cash_rounding-create) | 创建现金舍入规则 | 写入 | degraded |
| [cash_rounding.get](cli-v4-manual/scenarios/invoice-common.md#cap-cash_rounding-get) | 获取现金舍入规则详情 | 只读 | unconfigured |
| [cash_rounding.list](cli-v4-manual/scenarios/invoice-common.md#cap-cash_rounding-list) | 列出现金舍入规则 | 只读 | unconfigured |
| [cash_rounding.update](cli-v4-manual/scenarios/invoice-common.md#cap-cash_rounding-update) | 更新现金舍入规则 | 写入 | degraded |
| [company.discount_allocation_accounts.assign](cli-v4-manual/scenarios/invoice-common.md#cap-company-discount_allocation_accounts-assign) | 设置发票折扣分摊科目 | 写入 | unconfigured |
| [company.invoice_display.update](cli-v4-manual/scenarios/invoice-common.md#cap-company-invoice_display-update) | 修改公司发票显示选项 | 写入 | unconfigured |
| [invoice.alerts.inspect](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-alerts-inspect) | 查看发票原生提醒 | 只读 | unconfigured |
| [invoice.cancel](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-cancel) | 原子取消单张或 2–100 张发票或账单 | 写入 | unconfigured |
| [invoice.cash_rounding.assign](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-cash_rounding-assign) | 设置发票现金舍入方式 | 写入 | unconfigured |
| [invoice.delete](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-delete) | 删除从未过账的草稿发票或账单 | 写入 | degraded |
| [invoice.duplicate](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-duplicate) | 复制发票或账单为新草稿 | 写入 | unconfigured |
| [invoice.duplicate_candidates.list](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-duplicate_candidates-list) | 列出发票潜在重复项 | 只读 | unconfigured |
| [invoice.fiscal_position.refresh](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-fiscal_position-refresh) | 重算发票财税规则 | 写入 | unconfigured |
| [invoice.get](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-get) | 读取发票或账单明细 | 只读 | unconfigured |
| [invoice.incoterm.update](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-incoterm-update) | 修改发票贸易术语 | 写入 | unconfigured |
| [invoice.layout_line.create](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-layout_line-create) | 添加发票章节和备注行 | 写入 | unconfigured |
| [invoice.layout_line.delete](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-layout_line-delete) | 删除发票章节和备注行 | 写入 | unconfigured |
| [invoice.layout_line.list](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-layout_line-list) | 查询发票章节和备注行 | 只读 | unconfigured |
| [invoice.layout_line.update](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-layout_line-update) | 修改发票章节和备注行 | 写入 | unconfigured |
| [invoice.line.create](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-line-create) | 新增草稿发票或账单业务行 | 写入 | degraded |
| [invoice.line.deductibility.update](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-line-deductibility-update) | 修改草稿账单行抵扣比例 | 写入 | unconfigured |
| [invoice.line.delete](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-line-delete) | 删除草稿发票或账单业务行 | 写入 | degraded |
| [invoice.line.unit.assign](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-line-unit-assign) | 设置草稿发票行计量单位 | 写入 | unconfigured |
| [invoice.line.update](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-line-update) | 更新草稿发票或账单业务行 | 写入 | unconfigured |
| [invoice.lines.add](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-lines-add) | 保留既有行，批量追加草稿发票或账单业务行 | 写入 | degraded |
| [invoice.lines.remove](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-lines-remove) | 保留其余行，批量删除草稿发票或账单业务行 | 写入 | degraded |
| [invoice.lines.replace](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-lines-replace) | 替换草稿发票或账单的全部业务行 | 写入 | unconfigured |
| [invoice.lines.resequence](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-lines-resequence) | 调整发票展示行顺序 | 写入 | unconfigured |
| [invoice.lines.update](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-lines-update) | 保留编号，批量修改草稿发票或账单业务行 | 写入 | unconfigured |
| [invoice.pdf.export](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-pdf-export) | 导出发票 PDF | 只读 | unconfigured |
| [invoice.post](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-post) | 原子过账单张或 2–100 张发票或账单 | 写入 | unconfigured |
| [invoice.presentation_settings.get](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-presentation_settings-get) | 读取发票展示设置 | 只读 | unconfigured |
| [invoice.presentation_settings.update](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-presentation_settings-update) | 修改发票展示设置 | 写入 | unconfigured |
| [invoice.reset_to_draft](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-reset_to_draft) | 原子将单张或 2–100 张发票或账单重置为草稿 | 写入 | unconfigured |
| [invoice.reverse_and_reissue](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-reverse_and_reissue) | 冲销并重新开票 | 写入 | unconfigured |
| [invoice.search](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-search) | 搜索客户发票和供应商账单 | 只读 | unconfigured |
| [invoice.service_dates.get](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-service_dates-get) | 查看发票业务日期 | 只读 | unconfigured |
| [invoice.service_dates.update](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-service_dates-update) | 修改草稿发票业务日期 | 写入 | unconfigured |
| [invoice.tax_breakdown.inspect](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-tax_breakdown-inspect) | 检查发票税额明细 | 只读 | unconfigured |
| [invoice.tax_totals.adjust](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-tax_totals-adjust) | 调整草稿发票税组金额 | 写入 | unconfigured |
| [invoice.type.switch](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-type-switch) | 切换草稿发票或账单的发票退款类型 | 写入 | unconfigured |
| [invoice.update](cli-v4-manual/scenarios/invoice-common.md#cap-invoice-update) | 更新草稿发票或账单表头 | 写入 | unconfigured |
### 应收应付、收付款、现金退款与催款（64项）

查看未结项、付款计划、付款状态和账龄，登记客户收款、客户现金退款、供应商付款或供应商现金退款，维护支付单、日记账付款方式及付款条款，处理到期日、付款暂停和催款排除，并输出或发送收款凭证、客户对账单及催款资料。应收与应付入口按原单类型确定收付方向；支付核销和差额还需结合核销场景。

[打开本场景完整接口章节](cli-v4-manual/scenarios/payments-open-items.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [company.cash_discount_accounts.assign](cli-v4-manual/scenarios/payments-open-items.md#cap-company-cash_discount_accounts-assign) | 设置公司现金折扣损益科目 | 写入 | unconfigured |
| [invoice.followup.update](cli-v4-manual/scenarios/payments-open-items.md#cap-invoice-followup-update) | 更新发票或账单催款排除状态 | 写入 | unconfigured |
| [invoice.payment_block.set](cli-v4-manual/scenarios/payments-open-items.md#cap-invoice-payment_block-set) | 设置发票付款阻止状态 | 写入 | unconfigured |
| [invoice.payment_method.assign](cli-v4-manual/scenarios/payments-open-items.md#cap-invoice-payment_method-assign) | 设置发票付款方式 | 写入 | unconfigured |
| [invoice.payment_schedule.inspect](cli-v4-manual/scenarios/payments-open-items.md#cap-invoice-payment_schedule-inspect) | 查看发票原生分期到期计划 | 只读 | unconfigured |
| [invoice.payment_status.inspect](cli-v4-manual/scenarios/payments-open-items.md#cap-invoice-payment_status-inspect) | 检查发票付款状态和余额 | 只读 | unconfigured |
| [journal_item.date_maturity.update](cli-v4-manual/scenarios/payments-open-items.md#cap-journal_item-date_maturity-update) | 修改分录行到期日 | 写入 | unconfigured |
| [payable.open_items.list](cli-v4-manual/scenarios/payments-open-items.md#cap-payable-open_items-list) | 列出应付未清项 | 只读 | unconfigured |
| [payable.payment.register](cli-v4-manual/scenarios/payments-open-items.md#cap-payable-payment-register) | 登记供应商账单付款（支持多账单合并）或供应商退款收款 | 写入 | unconfigured |
| [payment.bank_account.assign](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-bank_account-assign) | 指定付款银行账户 | 写入 | unconfigured |
| [payment.bank_account_candidates.list](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-bank_account_candidates-list) | 查询付款可选银行账户 | 只读 | unconfigured |
| [payment.cancel](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-cancel) | 原子取消并补偿单笔或 2–100 笔会计付款 | 写入 | unconfigured |
| [payment.create](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-create) | 创建草稿会计付款 | 写入 | unconfigured |
| [payment.delete](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-delete) | 删除未核销的草稿或已取消付款 | 写入 | degraded |
| [payment.destination_account.assign](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-destination_account-assign) | 指定草稿付款对方科目 | 写入 | unconfigured |
| [payment.duplicate](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-duplicate) | 复制会计付款为新草稿 | 写入 | degraded |
| [payment.duplicate_candidates.list](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-duplicate_candidates-list) | 查询付款重复候选 | 只读 | unconfigured |
| [payment.get](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-get) | 读取付款及关联单据 | 只读 | unconfigured |
| [payment.method.get](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-method-get) | 获取付款方式详情 | 只读 | unconfigured |
| [payment.method.list](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-method-list) | 列出付款方式 | 只读 | unconfigured |
| [payment.method_definition.get](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-method_definition-get) | 读取付款方式定义 | 只读 | unconfigured |
| [payment.method_definition.list](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-method_definition-list) | 列出付款方式定义 | 只读 | unconfigured |
| [payment.method_line.create](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-method_line-create) | 创建日记账付款方式行 | 写入 | degraded |
| [payment.method_line.duplicate](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-method_line-duplicate) | 复制日记账付款方式行 | 写入 | degraded |
| [payment.method_line.remove](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-method_line-remove) | 移除日记账付款方式行 | 写入 | degraded |
| [payment.method_line.update](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-method_line-update) | 修改日记账付款方式行 | 写入 | unconfigured |
| [payment.post](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-post) | 原子过账单笔或 2–100 笔会计付款 | 写入 | unconfigured |
| [payment.processing_settings.get](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-processing_settings-get) | 读取付款处理设置 | 只读 | unconfigured |
| [payment.receipt.pdf.export](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-receipt-pdf-export) | 导出付款收据 PDF | 只读 | unconfigured |
| [payment.receipt.send](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-receipt-send) | 将付款收据加入 Odoo 发送队列 | 写入 | degraded |
| [payment.receipt.send.inspect](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-receipt-send-inspect) | 检查付款收据发送准备状态 | 只读 | unconfigured |
| [payment.reject](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-reject) | 拒绝已发送付款 | 写入 | unconfigured |
| [payment.reset_to_draft](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-reset_to_draft) | 原子将单笔或 2–100 笔会计付款重置为草稿 | 写入 | unconfigured |
| [payment.search](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-search) | 搜索会计付款 | 只读 | unconfigured |
| [payment.sent_status.set](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-sent_status-set) | 设置付款已发送标记 | 写入 | unconfigured |
| [payment.update_draft](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-update_draft) | 更新草稿会计付款 | 写入 | unconfigured |
| [payment.validate](cli-v4-manual/scenarios/payments-open-items.md#cap-payment-validate) | 确认无分录付款完成 | 写入 | unconfigured |
| [payment_term.archive](cli-v4-manual/scenarios/payments-open-items.md#cap-payment_term-archive) | 停用付款条件 | 写入 | unconfigured |
| [payment_term.compute](cli-v4-manual/scenarios/payments-open-items.md#cap-payment_term-compute) | 试算付款期限及提前付款折扣 | 只读 | unconfigured |
| [payment_term.create](cli-v4-manual/scenarios/payments-open-items.md#cap-payment_term-create) | 创建付款条件 | 写入 | degraded |
| [payment_term.delete](cli-v4-manual/scenarios/payments-open-items.md#cap-payment_term-delete) | 删除未被单据引用的付款条件 | 写入 | unconfigured |
| [payment_term.duplicate](cli-v4-manual/scenarios/payments-open-items.md#cap-payment_term-duplicate) | 复制付款条件和分期行 | 写入 | unconfigured |
| [payment_term.get](cli-v4-manual/scenarios/payments-open-items.md#cap-payment_term-get) | 获取付款条件详情 | 只读 | unconfigured |
| [payment_term.line.create](cli-v4-manual/scenarios/payments-open-items.md#cap-payment_term-line-create) | 新增付款条件分期行 | 写入 | unconfigured |
| [payment_term.line.delete](cli-v4-manual/scenarios/payments-open-items.md#cap-payment_term-line-delete) | 删除付款条件分期行 | 写入 | unconfigured |
| [payment_term.line.update](cli-v4-manual/scenarios/payments-open-items.md#cap-payment_term-line-update) | 修改付款条件分期行 | 写入 | unconfigured |
| [payment_term.lines.replace](cli-v4-manual/scenarios/payments-open-items.md#cap-payment_term-lines-replace) | 替换付款条件行 | 写入 | unconfigured |
| [payment_term.lines.update](cli-v4-manual/scenarios/payments-open-items.md#cap-payment_term-lines-update) | 成组修改付款条件分期行 | 写入 | unconfigured |
| [payment_term.list](cli-v4-manual/scenarios/payments-open-items.md#cap-payment_term-list) | 列出付款条件 | 只读 | unconfigured |
| [payment_term.restore](cli-v4-manual/scenarios/payments-open-items.md#cap-payment_term-restore) | 恢复付款条件 | 写入 | unconfigured |
| [payment_term.update](cli-v4-manual/scenarios/payments-open-items.md#cap-payment_term-update) | 更新付款条件 | 写入 | unconfigured |
| [payment_term.usage_moves.list](cli-v4-manual/scenarios/payments-open-items.md#cap-payment_term-usage_moves-list) | 查询付款条件使用单据 | 只读 | unconfigured |
| [receivable.open_items.list](cli-v4-manual/scenarios/payments-open-items.md#cap-receivable-open_items-list) | 列出应收未清项 | 只读 | unconfigured |
| [receivable.payment.register](cli-v4-manual/scenarios/payments-open-items.md#cap-receivable-payment-register) | 登记客户发票收款（支持多发票合并）或退款 | 写入 | unconfigured |
| [report.aged_payable](cli-v4-manual/scenarios/payments-open-items.md#cap-report-aged_payable) | 生成应付账龄报告 | 只读 | unconfigured |
| [report.aged_payable.export](cli-v4-manual/scenarios/payments-open-items.md#cap-report-aged_payable-export) | 导出应付账龄报告 | 只读 | unconfigured |
| [report.aged_receivable](cli-v4-manual/scenarios/payments-open-items.md#cap-report-aged_receivable) | 生成应收账龄报告 | 只读 | unconfigured |
| [report.aged_receivable.export](cli-v4-manual/scenarios/payments-open-items.md#cap-report-aged_receivable-export) | 导出应收账龄报告 | 只读 | unconfigured |
| [report.customer_statement](cli-v4-manual/scenarios/payments-open-items.md#cap-report-customer_statement) | 生成客户对账单 | 只读 | unconfigured |
| [report.customer_statement.export](cli-v4-manual/scenarios/payments-open-items.md#cap-report-customer_statement-export) | 导出客户对账单 | 只读 | unconfigured |
| [report.customer_statement.send](cli-v4-manual/scenarios/payments-open-items.md#cap-report-customer_statement-send) | 将客户对账单加入 Odoo 发送队列 | 写入 | degraded |
| [report.followup](cli-v4-manual/scenarios/payments-open-items.md#cap-report-followup) | 生成应收催款报告 | 只读 | unconfigured |
| [report.followup.export](cli-v4-manual/scenarios/payments-open-items.md#cap-report-followup-export) | 导出应收催款报告 | 只读 | unconfigured |
| [report.followup.send](cli-v4-manual/scenarios/payments-open-items.md#cap-report-followup-send) | 将应收催款报告加入 Odoo 发送队列 | 写入 | degraded |
### 银行流水、对账单、核销及核销差额（49项）

录入和维护银行流水、对账单，配置银行默认科目和日记账流动性，查找匹配候选，建立或撤销银行匹配、部分或全额核销，维护对账模型及其行，并查看银行对账报告。核销与实际现金收付是不同操作；reconciliation.write_off 针对银行流水，支付登记差额由相应支付接口参数控制。

[打开本场景完整接口章节](cli-v4-manual/scenarios/bank-reconciliation.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [bank.statement.create](cli-v4-manual/scenarios/bank-reconciliation.md#cap-bank-statement-create) | 创建含期初与期末余额的银行对账单 | 写入 | degraded |
| [bank.statement.delete](cli-v4-manual/scenarios/bank-reconciliation.md#cap-bank-statement-delete) | 删除银行对账单并保留银行流水 | 写入 | degraded |
| [bank.statement.get](cli-v4-manual/scenarios/bank-reconciliation.md#cap-bank-statement-get) | 获取银行对账单详情 | 只读 | unconfigured |
| [bank.statement.pdf.export](cli-v4-manual/scenarios/bank-reconciliation.md#cap-bank-statement-pdf-export) | 导出银行对账单 PDF | 只读 | unconfigured |
| [bank.statement.search](cli-v4-manual/scenarios/bank-reconciliation.md#cap-bank-statement-search) | 搜索银行对账单 | 只读 | unconfigured |
| [bank.statement.update](cli-v4-manual/scenarios/bank-reconciliation.md#cap-bank-statement-update) | 维护银行对账单期初期末余额及流水归组 | 写入 | unconfigured |
| [bank.transaction.counterparts.replace](cli-v4-manual/scenarios/bank-reconciliation.md#cap-bank-transaction-counterparts-replace) | 拆分或重新分类银行流水损益分录 | 写入 | unconfigured |
| [bank.transaction.delete](cli-v4-manual/scenarios/bank-reconciliation.md#cap-bank-transaction-delete) | 删除未分组且未匹配的银行流水 | 写入 | degraded |
| [bank.transaction.get](cli-v4-manual/scenarios/bank-reconciliation.md#cap-bank-transaction-get) | 获取银行流水详情 | 只读 | unconfigured |
| [bank.transaction.list](cli-v4-manual/scenarios/bank-reconciliation.md#cap-bank-transaction-list) | 列出银行流水 | 只读 | unconfigured |
| [bank.transaction.match](cli-v4-manual/scenarios/bank-reconciliation.md#cap-bank-transaction-match) | 匹配银行流水 | 写入 | unconfigured |
| [bank.transaction.match_candidates.list](cli-v4-manual/scenarios/bank-reconciliation.md#cap-bank-transaction-match_candidates-list) | 列出银行流水匹配候选项 | 只读 | unconfigured |
| [bank.transaction.reconciliation.get](cli-v4-manual/scenarios/bank-reconciliation.md#cap-bank-transaction-reconciliation-get) | 获取银行流水核销详情 | 只读 | unconfigured |
| [bank.transaction.record](cli-v4-manual/scenarios/bank-reconciliation.md#cap-bank-transaction-record) | 记录银行流水 | 写入 | unconfigured |
| [bank.transaction.search](cli-v4-manual/scenarios/bank-reconciliation.md#cap-bank-transaction-search) | 搜索银行流水 | 只读 | unconfigured |
| [bank.transaction.unmatch](cli-v4-manual/scenarios/bank-reconciliation.md#cap-bank-transaction-unmatch) | 撤销银行流水匹配 | 写入 | unconfigured |
| [bank.transaction.update](cli-v4-manual/scenarios/bank-reconciliation.md#cap-bank-transaction-update) | 更新银行流水 | 写入 | unconfigured |
| [company.bank_defaults.assign](cli-v4-manual/scenarios/bank-reconciliation.md#cap-company-bank_defaults-assign) | 设置公司银行默认科目 | 写入 | unconfigured |
| [journal.bank_account.assign](cli-v4-manual/scenarios/bank-reconciliation.md#cap-journal-bank_account-assign) | 绑定公司银行账户 | 写入 | unconfigured |
| [journal.liquidity_configuration.update](cli-v4-manual/scenarios/bank-reconciliation.md#cap-journal-liquidity_configuration-update) | 配置日记账流动性科目 | 写入 | unconfigured |
| [journal_item.reconciliation.inspect](cli-v4-manual/scenarios/bank-reconciliation.md#cap-journal_item-reconciliation-inspect) | 查看指定分录行核销关系 | 只读 | unconfigured |
| [reconciliation.apply](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-apply) | 执行部分或完全核销 | 写入 | unconfigured |
| [reconciliation.automatic.run](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-automatic-run) | 运行自动核销 | 写入 | unconfigured |
| [reconciliation.candidates.list](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-candidates-list) | 列出核销候选项 | 只读 | unconfigured |
| [reconciliation.full.get](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-full-get) | 获取全额核销详情 | 只读 | unconfigured |
| [reconciliation.full.list](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-full-list) | 列出全额核销 | 只读 | unconfigured |
| [reconciliation.model.activity_type.assign](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-model-activity_type-assign) | 设置对账规则后续活动类型 | 写入 | unconfigured |
| [reconciliation.model.archive](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-model-archive) | 停用对账模型 | 写入 | unconfigured |
| [reconciliation.model.create](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-model-create) | 创建对账模型 | 写入 | degraded |
| [reconciliation.model.delete](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-model-delete) | 删除对账规则 | 写入 | unconfigured |
| [reconciliation.model.duplicate](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-model-duplicate) | 复制对账规则 | 写入 | unconfigured |
| [reconciliation.model.get](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-model-get) | 获取对账模型详情 | 只读 | unconfigured |
| [reconciliation.model.line.create](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-model-line-create) | 新增对账规则行 | 写入 | unconfigured |
| [reconciliation.model.line.delete](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-model-line-delete) | 删除对账规则行 | 写入 | unconfigured |
| [reconciliation.model.line.get](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-model-line-get) | 获取对账模型行详情 | 只读 | unconfigured |
| [reconciliation.model.line.list](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-model-line-list) | 列出对账模型行 | 只读 | unconfigured |
| [reconciliation.model.line.update](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-model-line-update) | 修改对账规则行 | 写入 | unconfigured |
| [reconciliation.model.lines.replace](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-model-lines-replace) | 替换对账模型行 | 写入 | unconfigured |
| [reconciliation.model.lines.resequence](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-model-lines-resequence) | 重排对账规则行 | 写入 | unconfigured |
| [reconciliation.model.list](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-model-list) | 列出对账模型 | 只读 | unconfigured |
| [reconciliation.model.processing_settings.get](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-model-processing_settings-get) | 读取对账规则原生处理状态 | 只读 | unconfigured |
| [reconciliation.model.restore](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-model-restore) | 恢复对账模型 | 写入 | unconfigured |
| [reconciliation.model.update](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-model-update) | 更新对账模型 | 写入 | unconfigured |
| [reconciliation.model.usage_lines.list](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-model-usage_lines-list) | 查询对账规则使用明细 | 只读 | unconfigured |
| [reconciliation.partial.get](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-partial-get) | 获取部分核销详情 | 只读 | unconfigured |
| [reconciliation.partial.list](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-partial-list) | 列出部分核销 | 只读 | unconfigured |
| [reconciliation.undo](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-undo) | 反核销会计项目 | 写入 | unconfigured |
| [reconciliation.write_off](cli-v4-manual/scenarios/bank-reconciliation.md#cap-reconciliation-write_off) | 核销银行流水差额 | 写入 | unconfigured |
| [report.bank_reconciliation](cli-v4-manual/scenarios/bank-reconciliation.md#cap-report-bank_reconciliation) | 生成银行对账报告 | 只读 | unconfigured |
### 手工凭证、分录行、冲销与凭证检查（27项）

创建、读取、编辑、过账、冲销或删除手工会计凭证，原子维护分录行，查看会计分录行及通用会计凭证的自动过账、复核和来源关联，检查序列完整性并渲染中国会计凭证。通用 accounting_move 和 journal_item 读取也可能针对发票、支付等来源凭证，不只限于手工分录；核销和分析分摊分别见对应场景。

[打开本场景完整接口章节](cli-v4-manual/scenarios/journal-entries.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [accounting_move.autopost.configure](cli-v4-manual/scenarios/journal-entries.md#cap-accounting_move-autopost-configure) | 设置分录自动过账计划 | 写入 | unconfigured |
| [accounting_move.origin_links.inspect](cli-v4-manual/scenarios/journal-entries.md#cap-accounting_move-origin_links-inspect) | 查看凭证来源关联 | 只读 | unconfigured |
| [accounting_move.processing_settings.get](cli-v4-manual/scenarios/journal-entries.md#cap-accounting_move-processing_settings-get) | 读取发票分录处理设置 | 只读 | unconfigured |
| [accounting_move.review.set](cli-v4-manual/scenarios/journal-entries.md#cap-accounting_move-review-set) | 设置分录复核状态 | 写入 | unconfigured |
| [diagnostic.journal_integrity.inspect](cli-v4-manual/scenarios/journal-entries.md#cap-diagnostic-journal_integrity-inspect) | 检查日记账完整性 | 只读 | unconfigured |
| [journal.sequence_irregularity.list](cli-v4-manual/scenarios/journal-entries.md#cap-journal-sequence_irregularity-list) | 列出日记账序列异常 | 只读 | unconfigured |
| [journal_entry.cancel](cli-v4-manual/scenarios/journal-entries.md#cap-journal_entry-cancel) | 原子取消单笔或 2–100 笔普通日记账分录 | 写入 | unconfigured |
| [journal_entry.create](cli-v4-manual/scenarios/journal-entries.md#cap-journal_entry-create) | 创建草稿总账分录 | 写入 | unconfigured |
| [journal_entry.delete](cli-v4-manual/scenarios/journal-entries.md#cap-journal_entry-delete) | 删除从未过账的普通草稿总账分录 | 写入 | degraded |
| [journal_entry.duplicate](cli-v4-manual/scenarios/journal-entries.md#cap-journal_entry-duplicate) | 复制普通总账分录为新草稿 | 写入 | degraded |
| [journal_entry.get](cli-v4-manual/scenarios/journal-entries.md#cap-journal_entry-get) | 读取总账分录明细 | 只读 | unconfigured |
| [journal_entry.lines.add](cli-v4-manual/scenarios/journal-entries.md#cap-journal_entry-lines-add) | 保留其他行 ID，追加草稿手工分录行 | 写入 | unconfigured |
| [journal_entry.lines.remove](cli-v4-manual/scenarios/journal-entries.md#cap-journal_entry-lines-remove) | 保留其他行 ID，删除指定草稿手工分录行 | 写入 | degraded |
| [journal_entry.lines.replace](cli-v4-manual/scenarios/journal-entries.md#cap-journal_entry-lines-replace) | 替换草稿总账分录的全部行 | 写入 | unconfigured |
| [journal_entry.lines.update](cli-v4-manual/scenarios/journal-entries.md#cap-journal_entry-lines-update) | 保留行标识批量修改草稿分录 | 写入 | unconfigured |
| [journal_entry.post](cli-v4-manual/scenarios/journal-entries.md#cap-journal_entry-post) | 原子过账单笔或 2–100 笔普通日记账分录 | 写入 | unconfigured |
| [journal_entry.reset_to_draft](cli-v4-manual/scenarios/journal-entries.md#cap-journal_entry-reset_to_draft) | 原子将单笔或 2–100 笔普通日记账分录重置为草稿 | 写入 | unconfigured |
| [journal_entry.reverse](cli-v4-manual/scenarios/journal-entries.md#cap-journal_entry-reverse) | 冲销已过账分录 | 写入 | unconfigured |
| [journal_entry.search](cli-v4-manual/scenarios/journal-entries.md#cap-journal_entry-search) | 搜索总账分录 | 只读 | unconfigured |
| [journal_entry.update](cli-v4-manual/scenarios/journal-entries.md#cap-journal_entry-update) | 更新草稿总账分录表头 | 写入 | unconfigured |
| [journal_item.get](cli-v4-manual/scenarios/journal-entries.md#cap-journal_item-get) | 获取会计分录行详情 | 只读 | unconfigured |
| [journal_item.processing_details.get](cli-v4-manual/scenarios/journal-entries.md#cap-journal_item-processing_details-get) | 查看分录行处理详情 | 只读 | unconfigured |
| [journal_item.search](cli-v4-manual/scenarios/journal-entries.md#cap-journal_item-search) | 搜索会计分录行 | 只读 | unconfigured |
| [localization.china.voucher.render](cli-v4-manual/scenarios/journal-entries.md#cap-localization-china-voucher-render) | 导出中国会计凭证 PDF | 只读 | unconfigured |
| [recurring.journal_entry.get](cli-v4-manual/scenarios/journal-entries.md#cap-recurring-journal_entry-get) | 读取自动过账和周期分录 | 只读 | unconfigured |
| [recurring.journal_entry.search](cli-v4-manual/scenarios/journal-entries.md#cap-recurring-journal_entry-search) | 搜索自动过账和周期分录 | 只读 | unconfigured |
| [validation.journal_entry.check](cli-v4-manual/scenarios/journal-entries.md#cap-validation-journal_entry-check) | 验证总账分录就绪状态 | 只读 | unconfigured |
### 总账、往来账簿与财务报表（26项）

生成和导出总账、日记账、伙伴分类账、试算平衡、资产负债表、利润表、现金流量表、执行摘要和中国本地化财务报表，并查阅报表目录与外部值。报表选项、公司币口径、期间和输出格式按接口合同使用；账龄、税、预算、资产、递延、外币和库存估值报表按业务目的列于其他场景。

[打开本场景完整接口章节](cli-v4-manual/scenarios/ledgers-financial-reports.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [report.balance_sheet](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-balance_sheet) | 生成资产负债表 | 只读 | unconfigured |
| [report.balance_sheet.export](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-balance_sheet-export) | 导出资产负债表 | 只读 | unconfigured |
| [report.cash_flow](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-cash_flow) | 生成现金流量表 | 只读 | unconfigured |
| [report.cash_flow.export](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-cash_flow-export) | 导出现金流量表 | 只读 | unconfigured |
| [report.catalog.get](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-catalog-get) | 获取会计报表定义详情 | 只读 | unconfigured |
| [report.catalog.list](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-catalog-list) | 列出可用会计报表目录 | 只读 | unconfigured |
| [report.china.balance_sheet](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-china-balance_sheet) | 生成中国资产负债表 | 只读 | unconfigured |
| [report.china.balance_sheet.export](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-china-balance_sheet-export) | 导出中国资产负债表 | 只读 | unconfigured |
| [report.china.cash_flow](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-china-cash_flow) | 生成中国现金流量表 | 只读 | unconfigured |
| [report.china.cash_flow.export](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-china-cash_flow-export) | 导出中国现金流量表 | 只读 | unconfigured |
| [report.china.profit_and_loss](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-china-profit_and_loss) | 生成中国利润表 | 只读 | unconfigured |
| [report.china.profit_and_loss.export](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-china-profit_and_loss-export) | 导出中国利润表 | 只读 | unconfigured |
| [report.executive_summary](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-executive_summary) | 生成财务执行摘要 | 只读 | unconfigured |
| [report.executive_summary.export](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-executive_summary-export) | 导出财务执行摘要 | 只读 | unconfigured |
| [report.external_value.get](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-external_value-get) | 读取财务报表外部值 | 只读 | unconfigured |
| [report.external_value.search](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-external_value-search) | 搜索财务报表外部值 | 只读 | unconfigured |
| [report.general_ledger](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-general_ledger) | 生成总账报告 | 只读 | unconfigured |
| [report.general_ledger.export](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-general_ledger-export) | 导出总账报告 | 只读 | unconfigured |
| [report.journal](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-journal) | 生成日记账报告 | 只读 | unconfigured |
| [report.journal.export](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-journal-export) | 导出日记账报告 | 只读 | unconfigured |
| [report.partner_ledger](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-partner_ledger) | 生成合作伙伴分类账 | 只读 | unconfigured |
| [report.partner_ledger.export](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-partner_ledger-export) | 导出合作伙伴分类账 | 只读 | unconfigured |
| [report.profit_and_loss](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-profit_and_loss) | 生成利润表 | 只读 | unconfigured |
| [report.profit_and_loss.export](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-profit_and_loss-export) | 导出利润表 | 只读 | unconfigured |
| [report.trial_balance](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-trial_balance) | 生成试算平衡表 | 只读 | unconfigured |
| [report.trial_balance.export](cli-v4-manual/scenarios/ledgers-financial-reports.md#cap-report-trial_balance-export) | 导出试算平衡表 | 只读 | unconfigured |
### 分析会计、预算与经营分析（61项）

维护分析计划、分析账户、适用规则、分摊模型、分析分录和分录行分析分摊，检查分析账户余额及发票使用，管理预算生命周期、预算行、报表预算定义和期间总额，并查询发票及会计分录行分析汇总。分析币种与分组口径按原生报告合同读取；销售采购订单统计见历史订单场景。

[打开本场景完整接口章节](cli-v4-manual/scenarios/analytic-budget-management.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [analytic.account.archive](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-account-archive) | 停用分析账户 | 写入 | unconfigured |
| [analytic.account.balance.inspect](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-account-balance-inspect) | 查看指定期间原生分析借贷和余额 | 只读 | unconfigured |
| [analytic.account.create](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-account-create) | 创建分析账户 | 写入 | degraded |
| [analytic.account.delete](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-account-delete) | 原生删除公司分析账户 | 写入 | unconfigured |
| [analytic.account.duplicate](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-account-duplicate) | 原生复制公司分析账户 | 写入 | degraded |
| [analytic.account.get](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-account-get) | 获取分析账户详情 | 只读 | unconfigured |
| [analytic.account.invoice_usage.inspect](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-account-invoice_usage-inspect) | 查看原生发票和账单分析计数 | 只读 | unconfigured |
| [analytic.account.restore](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-account-restore) | 恢复分析账户 | 写入 | unconfigured |
| [analytic.account.search](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-account-search) | 搜索分析账户 | 只读 | unconfigured |
| [analytic.account.update](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-account-update) | 更新分析账户 | 写入 | unconfigured |
| [analytic.applicability.create](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-applicability-create) | 创建分析适用性规则 | 写入 | degraded |
| [analytic.applicability.delete](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-applicability-delete) | 删除公司分析适用性规则 | 写入 | unconfigured |
| [analytic.applicability.get](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-applicability-get) | 获取分析适用性规则详情 | 只读 | unconfigured |
| [analytic.applicability.list](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-applicability-list) | 列出分析适用性规则 | 只读 | unconfigured |
| [analytic.applicability.resolve](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-applicability-resolve) | 解析原生分析适用性 | 只读 | unconfigured |
| [analytic.applicability.update](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-applicability-update) | 更新分析适用性规则 | 写入 | unconfigured |
| [analytic.distribution.resolve](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-distribution-resolve) | 解析原生自动分析分配 | 只读 | unconfigured |
| [analytic.distribution_model.create](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-distribution_model-create) | 创建分析分配模型 | 写入 | degraded |
| [analytic.distribution_model.delete](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-distribution_model-delete) | 删除公司分析分配模型 | 写入 | unconfigured |
| [analytic.distribution_model.get](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-distribution_model-get) | 获取分析分摊模型详情 | 只读 | unconfigured |
| [analytic.distribution_model.list](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-distribution_model-list) | 列出分析分摊模型 | 只读 | unconfigured |
| [analytic.distribution_model.update](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-distribution_model-update) | 更新分析分配模型 | 写入 | unconfigured |
| [analytic.line.create](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-line-create) | 创建手工分析分录 | 写入 | degraded |
| [analytic.line.delete](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-line-delete) | 删除手工分析分录 | 写入 | degraded |
| [analytic.line.get](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-line-get) | 获取分析分录详情 | 只读 | unconfigured |
| [analytic.line.search](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-line-search) | 搜索分析分录 | 只读 | unconfigured |
| [analytic.line.summary](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-line-summary) | 按分析账户汇总分析分录 | 只读 | unconfigured |
| [analytic.line.update](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-line-update) | 更新手工分析分录 | 写入 | unconfigured |
| [analytic.plan.create](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-plan-create) | 创建分析子计划 | 写入 | degraded |
| [analytic.plan.get](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-plan-get) | 获取分析计划详情 | 只读 | unconfigured |
| [analytic.plan.list](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-plan-list) | 列出分析计划 | 只读 | unconfigured |
| [analytic.plan.update](cli-v4-manual/scenarios/analytic-budget-management.md#cap-analytic-plan-update) | 更新分析子计划 | 写入 | degraded |
| [budget.cancel](cli-v4-manual/scenarios/analytic-budget-management.md#cap-budget-cancel) | 取消预算 | 写入 | unconfigured |
| [budget.confirm](cli-v4-manual/scenarios/analytic-budget-management.md#cap-budget-confirm) | 确认预算 | 写入 | unconfigured |
| [budget.create](cli-v4-manual/scenarios/analytic-budget-management.md#cap-budget-create) | 创建草稿预算 | 写入 | degraded |
| [budget.get](cli-v4-manual/scenarios/analytic-budget-management.md#cap-budget-get) | 获取预算详情 | 只读 | unconfigured |
| [budget.line.get](cli-v4-manual/scenarios/analytic-budget-management.md#cap-budget-line-get) | 获取预算行详情 | 只读 | unconfigured |
| [budget.line.list](cli-v4-manual/scenarios/analytic-budget-management.md#cap-budget-line-list) | 列出预算行 | 只读 | unconfigured |
| [budget.lines.replace](cli-v4-manual/scenarios/analytic-budget-management.md#cap-budget-lines-replace) | 替换预算行 | 写入 | unconfigured |
| [budget.mark_done](cli-v4-manual/scenarios/analytic-budget-management.md#cap-budget-mark_done) | 将预算标记为已完成 | 写入 | unconfigured |
| [budget.reset_to_draft](cli-v4-manual/scenarios/analytic-budget-management.md#cap-budget-reset_to_draft) | 将预算重置为草稿 | 写入 | unconfigured |
| [budget.search](cli-v4-manual/scenarios/analytic-budget-management.md#cap-budget-search) | 搜索预算 | 只读 | unconfigured |
| [budget.update_draft](cli-v4-manual/scenarios/analytic-budget-management.md#cap-budget-update_draft) | 更新草稿预算 | 写入 | unconfigured |
| [invoice.analysis.search](cli-v4-manual/scenarios/analytic-budget-management.md#cap-invoice-analysis-search) | 搜索发票分析明细 | 只读 | unconfigured |
| [invoice.analysis.summary](cli-v4-manual/scenarios/analytic-budget-management.md#cap-invoice-analysis-summary) | 汇总发票分析 | 只读 | unconfigured |
| [journal_item.analysis.summary](cli-v4-manual/scenarios/analytic-budget-management.md#cap-journal_item-analysis-summary) | 汇总期间分录行活动 | 只读 | unconfigured |
| [journal_item.analytic_distribution.replace](cli-v4-manual/scenarios/analytic-budget-management.md#cap-journal_item-analytic_distribution-replace) | 替换分录行分析分配 | 写入 | unconfigured |
| [journal_item.analytic_lines.list](cli-v4-manual/scenarios/analytic-budget-management.md#cap-journal_item-analytic_lines-list) | 列出指定分录行的分析分录 | 只读 | unconfigured |
| [report.budget](cli-v4-manual/scenarios/analytic-budget-management.md#cap-report-budget) | 生成预算报告 | 只读 | unconfigured |
| [report.budget_account_period.set_total](cli-v4-manual/scenarios/analytic-budget-management.md#cap-report-budget_account_period-set_total) | 设置科目期间预算总额并按月分配 | 写入 | unconfigured |
| [report.budget_definition.create](cli-v4-manual/scenarios/analytic-budget-management.md#cap-report-budget_definition-create) | 创建财务报表预算 | 写入 | degraded |
| [report.budget_definition.delete](cli-v4-manual/scenarios/analytic-budget-management.md#cap-report-budget_definition-delete) | 删除财务报表预算及预算项 | 写入 | degraded |
| [report.budget_definition.duplicate](cli-v4-manual/scenarios/analytic-budget-management.md#cap-report-budget_definition-duplicate) | 复制财务报表预算及预算项 | 写入 | degraded |
| [report.budget_definition.get](cli-v4-manual/scenarios/analytic-budget-management.md#cap-report-budget_definition-get) | 读取财务报表预算定义 | 只读 | unconfigured |
| [report.budget_definition.search](cli-v4-manual/scenarios/analytic-budget-management.md#cap-report-budget_definition-search) | 搜索财务报表预算定义 | 只读 | unconfigured |
| [report.budget_definition.update](cli-v4-manual/scenarios/analytic-budget-management.md#cap-report-budget_definition-update) | 更新财务报表预算 | 写入 | unconfigured |
| [report.budget_item.create](cli-v4-manual/scenarios/analytic-budget-management.md#cap-report-budget_item-create) | 创建财务报表预算项 | 写入 | degraded |
| [report.budget_item.delete](cli-v4-manual/scenarios/analytic-budget-management.md#cap-report-budget_item-delete) | 删除财务报表预算项 | 写入 | degraded |
| [report.budget_item.get](cli-v4-manual/scenarios/analytic-budget-management.md#cap-report-budget_item-get) | 读取财务报表预算项 | 只读 | unconfigured |
| [report.budget_item.search](cli-v4-manual/scenarios/analytic-budget-management.md#cap-report-budget_item-search) | 搜索财务报表预算项 | 只读 | unconfigured |
| [report.budget_item.update](cli-v4-manual/scenarios/analytic-budget-management.md#cap-report-budget_item-update) | 更新财务报表预算项 | 写入 | unconfigured |
### 税率、税务映射、税务报告与本地化合规预留（55项）

维护税、税组、税务分摊行和税务单元，解析财务位置及科目和税映射，配置公司默认税和现金收付制税，并查看或导出税务及新加坡 GST 报告。新加坡合规评估、申报和 PINT 导出仍按单条状态识别预留接口，纳入目录不代表已可执行；会计申报内部工作流见期末场景。

[打开本场景完整接口章节](cli-v4-manual/scenarios/taxes-fiscal-position.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [company.cash_basis_configuration.update](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-company-cash_basis_configuration-update) | 设置现金收付制会计配置 | 写入 | unconfigured |
| [company.tax_policy.update](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-company-tax_policy-update) | 修改公司默认税和计算方式 | 写入 | unconfigured |
| [compliance.singapore.assessment.run](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-compliance-singapore-assessment-run) | 运行新加坡合规评估 | 写入 | disabled |
| [compliance.singapore.filing.list](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-compliance-singapore-filing-list) | 列出新加坡申报任务 | 只读 | disabled |
| [compliance.singapore.filing.prepare](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-compliance-singapore-filing-prepare) | 准备新加坡合规申报 | 写入 | disabled |
| [compliance.singapore.filing.submit](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-compliance-singapore-filing-submit) | 提交新加坡合规申报 | 写入 | disabled |
| [compliance.singapore.findings.list](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-compliance-singapore-findings-list) | 列出新加坡合规发现 | 只读 | disabled |
| [compliance.singapore.registration.verify](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-compliance-singapore-registration-verify) | 验证新加坡登记证据 | 只读 | disabled |
| [fiscal_position.account_mapping.create](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-fiscal_position-account_mapping-create) | 新增财政状况科目映射 | 写入 | degraded |
| [fiscal_position.account_mapping.delete](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-fiscal_position-account_mapping-delete) | 删除财政状况科目映射 | 写入 | degraded |
| [fiscal_position.account_mapping.list](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-fiscal_position-account_mapping-list) | 列出财政状况科目映射 | 只读 | unconfigured |
| [fiscal_position.account_mapping.update](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-fiscal_position-account_mapping-update) | 修改财政状况科目映射 | 写入 | unconfigured |
| [fiscal_position.account_mappings.replace](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-fiscal_position-account_mappings-replace) | 替换财政状况科目映射 | 写入 | unconfigured |
| [fiscal_position.archive](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-fiscal_position-archive) | 停用财政状况 | 写入 | unconfigured |
| [fiscal_position.create](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-fiscal_position-create) | 创建财政状况 | 写入 | degraded |
| [fiscal_position.delete](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-fiscal_position-delete) | 删除财政状况 | 写入 | degraded |
| [fiscal_position.duplicate](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-fiscal_position-duplicate) | 复制财政状况 | 写入 | degraded |
| [fiscal_position.get](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-fiscal_position-get) | 获取财务位置详情 | 只读 | unconfigured |
| [fiscal_position.resolve](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-fiscal_position-resolve) | 解析财务位置映射 | 只读 | unconfigured |
| [fiscal_position.restore](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-fiscal_position-restore) | 恢复财政状况 | 写入 | unconfigured |
| [fiscal_position.search](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-fiscal_position-search) | 搜索财务位置 | 只读 | unconfigured |
| [fiscal_position.tax_mapping.list](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-fiscal_position-tax_mapping-list) | 列出财政状况税映射 | 只读 | unconfigured |
| [fiscal_position.taxes.replace](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-fiscal_position-taxes-replace) | 替换财政状况税集合 | 写入 | unconfigured |
| [fiscal_position.update](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-fiscal_position-update) | 更新财政状况 | 写入 | unconfigured |
| [invoice.singapore.pint.export](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-invoice-singapore-pint-export) | 导出新加坡 PINT 电子发票 | 只读 | disabled |
| [report.singapore.gst](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-report-singapore-gst) | 生成新加坡 GST 报告 | 只读 | unconfigured |
| [report.singapore.gst.export](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-report-singapore-gst-export) | 导出新加坡 GST 报告 | 只读 | unconfigured |
| [report.tax](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-report-tax) | 生成税务报告 | 只读 | unconfigured |
| [report.tax.export](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-report-tax-export) | 导出税务报告 | 只读 | unconfigured |
| [tax.archive](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-archive) | 停用税 | 写入 | unconfigured |
| [tax.compute](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-compute) | 试算原生税额 | 只读 | unconfigured |
| [tax.create](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-create) | 创建税 | 写入 | degraded |
| [tax.delete](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-delete) | 删除未被原生引用阻止的税种 | 写入 | unconfigured |
| [tax.duplicate](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-duplicate) | 复制税 | 写入 | degraded |
| [tax.get](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-get) | 获取会计税详情 | 只读 | unconfigured |
| [tax.group.create](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-group-create) | 创建含税款结算科目的税组 | 写入 | degraded |
| [tax.group.get](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-group-get) | 读取税组及税款结算科目 | 只读 | unconfigured |
| [tax.group.list](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-group-list) | 列出税组及税款结算科目 | 只读 | unconfigured |
| [tax.group.update](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-group-update) | 维护税组及税款结算科目 | 写入 | unconfigured |
| [tax.list](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-list) | 列出会计税 | 只读 | unconfigured |
| [tax.original_taxes.replace](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-original_taxes-replace) | 替换税的来源税集合 | 写入 | unconfigured |
| [tax.processing_settings.get](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-processing_settings-get) | 查看税种原生处理设置 | 只读 | unconfigured |
| [tax.repartition_line.get](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-repartition_line-get) | 获取税收重分配行详情 | 只读 | unconfigured |
| [tax.repartition_line.list](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-repartition_line-list) | 列出税收重分配行 | 只读 | unconfigured |
| [tax.repartition_line.update](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-repartition_line-update) | 修改税务分摊行 | 写入 | unconfigured |
| [tax.repartition_lines.replace](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-repartition_lines-replace) | 替换税金重分配行 | 写入 | unconfigured |
| [tax.repartition_lines.resequence](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-repartition_lines-resequence) | 调整两侧税务分摊行顺序 | 写入 | unconfigured |
| [tax.repartition_lines.update](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-repartition_lines-update) | 原子修改现有税务分摊行 | 写入 | unconfigured |
| [tax.repartition_pair.create](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-repartition_pair-create) | 成对新增发票退款税务分摊行 | 写入 | unconfigured |
| [tax.repartition_pair.delete](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-repartition_pair-delete) | 成对删除发票退款税务分摊行 | 写入 | unconfigured |
| [tax.restore](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-restore) | 恢复税 | 写入 | unconfigured |
| [tax.unit.get](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-unit-get) | 读取税务单元 | 只读 | unconfigured |
| [tax.unit.search](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-unit-search) | 搜索税务单元 | 只读 | unconfigured |
| [tax.update](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-update) | 更新税 | 写入 | unconfigured |
| [tax.usage_lines.list](cli-v4-manual/scenarios/taxes-fiscal-position.md#cap-tax-usage_lines-list) | 查询税种使用的分录行 | 只读 | unconfigured |
### 财政年度、期末处理、锁期与会计申报（42项）

解析和维护财政年度，查看公司锁定日期及锁期例外，解析允许的会计日期，管理转结模型，生成预提或期末转结，执行期末校验，并维护会计申报、检查结果和账户状态。部分调整和锁期修改为禁用预留；account.return.mark_submitted 只改变 Odoo 内部状态，不向外部税务机关申报。

[打开本场景完整接口章节](cli-v4-manual/scenarios/period-close-returns.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [account.lock_exception.get](cli-v4-manual/scenarios/period-close-returns.md#cap-account-lock_exception-get) | 读取会计锁定日期例外 | 只读 | unconfigured |
| [account.lock_exception.search](cli-v4-manual/scenarios/period-close-returns.md#cap-account-lock_exception-search) | 搜索会计锁定日期例外 | 只读 | unconfigured |
| [account.return.account_status.get](cli-v4-manual/scenarios/period-close-returns.md#cap-account-return-account_status-get) | 读取申报表科目审计状态 | 只读 | unconfigured |
| [account.return.account_status.search](cli-v4-manual/scenarios/period-close-returns.md#cap-account-return-account_status-search) | 搜索申报表科目审计状态 | 只读 | unconfigured |
| [account.return.archive](cli-v4-manual/scenarios/period-close-returns.md#cap-account-return-archive) | 归档会计申报 | 写入 | unconfigured |
| [account.return.check.get](cli-v4-manual/scenarios/period-close-returns.md#cap-account-return-check-get) | 获取会计申报检查项 | 只读 | unconfigured |
| [account.return.check.list](cli-v4-manual/scenarios/period-close-returns.md#cap-account-return-check-list) | 列出会计申报检查项 | 只读 | unconfigured |
| [account.return.check.result.update](cli-v4-manual/scenarios/period-close-returns.md#cap-account-return-check-result-update) | 更新会计申报检查结果 | 写入 | unconfigured |
| [account.return.checks.refresh](cli-v4-manual/scenarios/period-close-returns.md#cap-account-return-checks-refresh) | 刷新会计申报检查项 | 写入 | unconfigured |
| [account.return.create](cli-v4-manual/scenarios/period-close-returns.md#cap-account-return-create) | 创建会计申报 | 写入 | degraded |
| [account.return.delete](cli-v4-manual/scenarios/period-close-returns.md#cap-account-return-delete) | 删除手工会计申报 | 写入 | degraded |
| [account.return.get](cli-v4-manual/scenarios/period-close-returns.md#cap-account-return-get) | 获取会计申报 | 只读 | unconfigured |
| [account.return.mark_submitted](cli-v4-manual/scenarios/period-close-returns.md#cap-account-return-mark_submitted) | 在 Odoo 内标记会计申报为已提交 | 写入 | unconfigured |
| [account.return.restore](cli-v4-manual/scenarios/period-close-returns.md#cap-account-return-restore) | 恢复已归档会计申报 | 写入 | unconfigured |
| [account.return.search](cli-v4-manual/scenarios/period-close-returns.md#cap-account-return-search) | 搜索会计申报 | 只读 | unconfigured |
| [account.return.summary](cli-v4-manual/scenarios/period-close-returns.md#cap-account-return-summary) | 汇总会计申报到期状态 | 只读 | unconfigured |
| [account.return.type.list](cli-v4-manual/scenarios/period-close-returns.md#cap-account-return-type-list) | 列出会计申报类型 | 只读 | unconfigured |
| [account.return.validate](cli-v4-manual/scenarios/period-close-returns.md#cap-account-return-validate) | 校验会计申报 | 写入 | unconfigured |
| [account.transfer_model.archive](cli-v4-manual/scenarios/period-close-returns.md#cap-account-transfer_model-archive) | 归档科目转结模型 | 写入 | unconfigured |
| [account.transfer_model.create](cli-v4-manual/scenarios/period-close-returns.md#cap-account-transfer_model-create) | 创建科目转结模型 | 写入 | degraded |
| [account.transfer_model.delete](cli-v4-manual/scenarios/period-close-returns.md#cap-account-transfer_model-delete) | 删除未运行的科目转结模型 | 写入 | degraded |
| [account.transfer_model.disable](cli-v4-manual/scenarios/period-close-returns.md#cap-account-transfer_model-disable) | 停用科目转结模型 | 写入 | unconfigured |
| [account.transfer_model.duplicate](cli-v4-manual/scenarios/period-close-returns.md#cap-account-transfer_model-duplicate) | 复制科目转结模型 | 写入 | degraded |
| [account.transfer_model.enable](cli-v4-manual/scenarios/period-close-returns.md#cap-account-transfer_model-enable) | 启用科目转结模型 | 写入 | unconfigured |
| [account.transfer_model.get](cli-v4-manual/scenarios/period-close-returns.md#cap-account-transfer_model-get) | 读取会计科目转结模型 | 只读 | unconfigured |
| [account.transfer_model.restore](cli-v4-manual/scenarios/period-close-returns.md#cap-account-transfer_model-restore) | 恢复科目转结模型 | 写入 | unconfigured |
| [account.transfer_model.search](cli-v4-manual/scenarios/period-close-returns.md#cap-account-transfer_model-search) | 搜索会计科目转结模型 | 只读 | unconfigured |
| [account.transfer_model.update](cli-v4-manual/scenarios/period-close-returns.md#cap-account-transfer_model-update) | 更新科目转结模型 | 写入 | unconfigured |
| [company.fiscal_year.resolve](cli-v4-manual/scenarios/period-close-returns.md#cap-company-fiscal_year-resolve) | 解析公司财政年度 | 只读 | unconfigured |
| [company.fiscal_year_end.update](cli-v4-manual/scenarios/period-close-returns.md#cap-company-fiscal_year_end-update) | 修改公司会计年度结束日 | 写入 | unconfigured |
| [company.lock_dates.inspect](cli-v4-manual/scenarios/period-close-returns.md#cap-company-lock_dates-inspect) | 检查公司会计锁定日期 | 只读 | unconfigured |
| [fiscal_year.create](cli-v4-manual/scenarios/period-close-returns.md#cap-fiscal_year-create) | 创建会计年度 | 写入 | degraded |
| [fiscal_year.get](cli-v4-manual/scenarios/period-close-returns.md#cap-fiscal_year-get) | 获取财政年度详情 | 只读 | unconfigured |
| [fiscal_year.search](cli-v4-manual/scenarios/period-close-returns.md#cap-fiscal_year-search) | 搜索财政年度 | 只读 | unconfigured |
| [fiscal_year.update](cli-v4-manual/scenarios/period-close-returns.md#cap-fiscal_year-update) | 更新会计年度 | 写入 | unconfigured |
| [journal.accounting_date.resolve](cli-v4-manual/scenarios/period-close-returns.md#cap-journal-accounting_date-resolve) | 解析日记账实际入账日期 | 只读 | unconfigured |
| [localization.china.period_transfer.run](cli-v4-manual/scenarios/period-close-returns.md#cap-localization-china-period_transfer-run) | 运行中国月末损益结转 | 写入 | degraded |
| [period.accrual.generate](cli-v4-manual/scenarios/period-close-returns.md#cap-period-accrual-generate) | 生成采购或销售预提分录 | 写入 | degraded |
| [period.adjustment.create](cli-v4-manual/scenarios/period-close-returns.md#cap-period-adjustment-create) | 创建期末调整分录 | 写入 | disabled |
| [period.lock.change](cli-v4-manual/scenarios/period-close-returns.md#cap-period-lock-change) | 变更会计锁定日期 | 写入 | disabled |
| [period.transfer.run](cli-v4-manual/scenarios/period-close-returns.md#cap-period-transfer-run) | 运行期间科目结转 | 写入 | degraded |
| [validation.period_close.check](cli-v4-manual/scenarios/period-close-returns.md#cap-validation-period_close-check) | 验证期间结账就绪状态 | 只读 | disabled |
### 币种、汇率、发票汇率与汇兑重估（13项）

查询币种、维护汇率和换算金额，更新或刷新发票汇率，配置公司汇兑损益科目与日记账，并生成多币种重估分录及相关报表。汇率日期、发票状态和原生重算约束按接口使用；报表公司币金额不应误读为单据外币金额。

[打开本场景完整接口章节](cli-v4-manual/scenarios/foreign-currency.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [company.exchange_configuration.update](cli-v4-manual/scenarios/foreign-currency.md#cap-company-exchange_configuration-update) | 修改公司汇兑损益配置 | 写入 | unconfigured |
| [currency.convert](cli-v4-manual/scenarios/foreign-currency.md#cap-currency-convert) | 按会计日期换算币种 | 只读 | unconfigured |
| [currency.get](cli-v4-manual/scenarios/foreign-currency.md#cap-currency-get) | 获取会计币种详情 | 只读 | unconfigured |
| [currency.list](cli-v4-manual/scenarios/foreign-currency.md#cap-currency-list) | 列出会计币种 | 只读 | unconfigured |
| [currency.rate.delete](cli-v4-manual/scenarios/foreign-currency.md#cap-currency-rate-delete) | 删除根公司历史汇率 | 写入 | degraded |
| [currency.rate.list](cli-v4-manual/scenarios/foreign-currency.md#cap-currency-rate-list) | 列出公司汇率 | 只读 | unconfigured |
| [currency.rate.record](cli-v4-manual/scenarios/foreign-currency.md#cap-currency-rate-record) | 记录公司汇率 | 写入 | unconfigured |
| [currency.rate.update](cli-v4-manual/scenarios/foreign-currency.md#cap-currency-rate-update) | 更正根公司历史汇率 | 写入 | unconfigured |
| [invoice.currency_rate.refresh](cli-v4-manual/scenarios/foreign-currency.md#cap-invoice-currency_rate-refresh) | 恢复发票原生默认汇率 | 写入 | unconfigured |
| [invoice.currency_rate.update](cli-v4-manual/scenarios/foreign-currency.md#cap-invoice-currency_rate-update) | 设置发票手工汇率 | 写入 | unconfigured |
| [multicurrency.revaluation.generate_entries](cli-v4-manual/scenarios/foreign-currency.md#cap-multicurrency-revaluation-generate_entries) | 生成汇兑重估分录 | 写入 | degraded |
| [report.multicurrency_revaluation](cli-v4-manual/scenarios/foreign-currency.md#cap-report-multicurrency_revaluation) | 生成多币种汇兑重估报告 | 只读 | unconfigured |
| [report.multicurrency_revaluation.export](cli-v4-manual/scenarios/foreign-currency.md#cap-report-multicurrency_revaluation-export) | 导出多币种汇兑重估报告 | 只读 | unconfigured |
### 固定资产、折旧、处置与资产报表（14项）

查找资产和资产组，创建、验证、暂停、取消或处置资产，读取折旧计划并生成或导出资产报表。修改折旧参数和恢复折旧等接口须先核对状态；目录中的禁用预留不代表资产修改流程已经实现。

[打开本场景完整接口章节](cli-v4-manual/scenarios/fixed-assets.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [asset.cancel](cli-v4-manual/scenarios/fixed-assets.md#cap-asset-cancel) | 取消固定资产并冲销折旧 | 写入 | unconfigured |
| [asset.create](cli-v4-manual/scenarios/fixed-assets.md#cap-asset-create) | 创建草稿固定资产 | 写入 | degraded |
| [asset.depreciation_schedule.get](cli-v4-manual/scenarios/fixed-assets.md#cap-asset-depreciation_schedule-get) | 读取固定资产折旧计划 | 只读 | unconfigured |
| [asset.dispose](cli-v4-manual/scenarios/fixed-assets.md#cap-asset-dispose) | 处置或出售固定资产 | 写入 | unconfigured |
| [asset.get](cli-v4-manual/scenarios/fixed-assets.md#cap-asset-get) | 读取固定资产明细 | 只读 | unconfigured |
| [asset.group.get](cli-v4-manual/scenarios/fixed-assets.md#cap-asset-group-get) | 读取资产组 | 只读 | unconfigured |
| [asset.group.search](cli-v4-manual/scenarios/fixed-assets.md#cap-asset-group-search) | 搜索资产组 | 只读 | unconfigured |
| [asset.modify](cli-v4-manual/scenarios/fixed-assets.md#cap-asset-modify) | 修改固定资产折旧参数 | 写入 | disabled |
| [asset.pause](cli-v4-manual/scenarios/fixed-assets.md#cap-asset-pause) | 暂停固定资产折旧 | 写入 | degraded |
| [asset.resume](cli-v4-manual/scenarios/fixed-assets.md#cap-asset-resume) | 恢复固定资产折旧 | 写入 | disabled |
| [asset.search](cli-v4-manual/scenarios/fixed-assets.md#cap-asset-search) | 搜索固定资产 | 只读 | unconfigured |
| [asset.validate](cli-v4-manual/scenarios/fixed-assets.md#cap-asset-validate) | 验证并启用固定资产 | 写入 | degraded |
| [report.asset](cli-v4-manual/scenarios/fixed-assets.md#cap-report-asset) | 生成固定资产报告 | 只读 | unconfigured |
| [report.asset.export](cli-v4-manual/scenarios/fixed-assets.md#cap-report-asset-export) | 导出固定资产报告 | 只读 | unconfigured |
### 递延收入、递延费用与摊销报表（6项）

按原生递延工作流生成收入或费用递延分录，读取并导出递延收入和费用报告。业务日期、科目及原单配置是原生生成条件；这些接口不代表可任意编辑所有摊销模型，也不取代原始发票核对。

[打开本场景完整接口章节](cli-v4-manual/scenarios/deferrals.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [deferred_expense.generate_entries](cli-v4-manual/scenarios/deferrals.md#cap-deferred_expense-generate_entries) | 生成递延费用分录 | 写入 | degraded |
| [deferred_revenue.generate_entries](cli-v4-manual/scenarios/deferrals.md#cap-deferred_revenue-generate_entries) | 生成递延收入分录 | 写入 | degraded |
| [report.deferred_expense](cli-v4-manual/scenarios/deferrals.md#cap-report-deferred_expense) | 生成递延费用报告 | 只读 | unconfigured |
| [report.deferred_expense.export](cli-v4-manual/scenarios/deferrals.md#cap-report-deferred_expense-export) | 导出递延费用报告 | 只读 | unconfigured |
| [report.deferred_revenue](cli-v4-manual/scenarios/deferrals.md#cap-report-deferred_revenue) | 生成递延收入报告 | 只读 | unconfigured |
| [report.deferred_revenue.export](cli-v4-manual/scenarios/deferrals.md#cap-report-deferred_revenue-export) | 导出递延收入报告 | 只读 | unconfigured |
### 库存估值、销售成本与库存会计衔接（5项）

查询库存关联会计分录、销售成本分录和销售发票到库存会计的关联，读取库存估值报告，并辨识库存估值调整的预留接口。该场景关注会计金额和来源衔接，不执行出入库、拣货、预留或实物退货；估值调整纳入索引不代表当前可用。

[打开本场景完整接口章节](cli-v4-manual/scenarios/inventory-accounting.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [cogs.entries.list](cli-v4-manual/scenarios/inventory-accounting.md#cap-cogs-entries-list) | 列出销售成本会计分录 | 只读 | unconfigured |
| [inventory.accounting_entries.list](cli-v4-manual/scenarios/inventory-accounting.md#cap-inventory-accounting_entries-list) | 列出库存关联会计分录 | 只读 | unconfigured |
| [inventory.valuation.adjust](cli-v4-manual/scenarios/inventory-accounting.md#cap-inventory-valuation-adjust) | 调整库存会计估值 | 写入 | disabled |
| [report.inventory_valuation](cli-v4-manual/scenarios/inventory-accounting.md#cap-report-inventory_valuation) | 生成库存估值报告 | 只读 | unconfigured |
| [sale_invoice.stock_link.inspect](cli-v4-manual/scenarios/inventory-accounting.md#cap-sale_invoice-stock_link-inspect) | 检查销售发票与库存会计衔接 | 只读 | unconfigured |
### 历史销售采购订单、行明细与订单输出（25项）

查询销售采购订单、精确行明细及开票状态，管理订单草稿、行替换、确认和取消，生成订单分析汇总，并导出销售订单、采购订单或询价单。历史订单接口不是新增会计发票接口的别名；从订单生成发票、预付款或账单分别在客户和供应商开票场景。

[打开本场景完整接口章节](cli-v4-manual/scenarios/sales-purchase-history.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [purchase.order.analysis.summary](cli-v4-manual/scenarios/sales-purchase-history.md#cap-purchase-order-analysis-summary) | 汇总分析采购订单 | 只读 | unconfigured |
| [purchase.order.cancel](cli-v4-manual/scenarios/sales-purchase-history.md#cap-purchase-order-cancel) | 取消采购订单 | 写入 | unconfigured |
| [purchase.order.confirm](cli-v4-manual/scenarios/sales-purchase-history.md#cap-purchase-order-confirm) | 确认采购订单 | 写入 | unconfigured |
| [purchase.order.create](cli-v4-manual/scenarios/sales-purchase-history.md#cap-purchase-order-create) | 创建草稿采购订单 | 写入 | degraded |
| [purchase.order.get](cli-v4-manual/scenarios/sales-purchase-history.md#cap-purchase-order-get) | 获取采购订单详情 | 只读 | unconfigured |
| [purchase.order.line.get](cli-v4-manual/scenarios/sales-purchase-history.md#cap-purchase-order-line-get) | 读取采购订单行 | 只读 | unconfigured |
| [purchase.order.line.search](cli-v4-manual/scenarios/sales-purchase-history.md#cap-purchase-order-line-search) | 搜索采购订单行 | 只读 | unconfigured |
| [purchase.order.lines.replace](cli-v4-manual/scenarios/sales-purchase-history.md#cap-purchase-order-lines-replace) | 替换草稿采购订单行 | 写入 | unconfigured |
| [purchase.order.pdf.export](cli-v4-manual/scenarios/sales-purchase-history.md#cap-purchase-order-pdf-export) | 导出采购订单 PDF | 只读 | unconfigured |
| [purchase.order.reset_to_draft](cli-v4-manual/scenarios/sales-purchase-history.md#cap-purchase-order-reset_to_draft) | 将采购订单重置为草稿 | 写入 | unconfigured |
| [purchase.order.search](cli-v4-manual/scenarios/sales-purchase-history.md#cap-purchase-order-search) | 搜索采购订单 | 只读 | unconfigured |
| [purchase.order.update_draft](cli-v4-manual/scenarios/sales-purchase-history.md#cap-purchase-order-update_draft) | 更新草稿采购订单 | 写入 | unconfigured |
| [purchase.rfq.pdf.export](cli-v4-manual/scenarios/sales-purchase-history.md#cap-purchase-rfq-pdf-export) | 导出询价单 PDF | 只读 | unconfigured |
| [sale.order.analysis.summary](cli-v4-manual/scenarios/sales-purchase-history.md#cap-sale-order-analysis-summary) | 汇总分析销售订单 | 只读 | unconfigured |
| [sale.order.cancel](cli-v4-manual/scenarios/sales-purchase-history.md#cap-sale-order-cancel) | 取消销售订单 | 写入 | unconfigured |
| [sale.order.confirm](cli-v4-manual/scenarios/sales-purchase-history.md#cap-sale-order-confirm) | 确认销售订单 | 写入 | unconfigured |
| [sale.order.create](cli-v4-manual/scenarios/sales-purchase-history.md#cap-sale-order-create) | 创建草稿销售订单 | 写入 | degraded |
| [sale.order.get](cli-v4-manual/scenarios/sales-purchase-history.md#cap-sale-order-get) | 获取销售订单详情 | 只读 | unconfigured |
| [sale.order.line.get](cli-v4-manual/scenarios/sales-purchase-history.md#cap-sale-order-line-get) | 读取销售订单行 | 只读 | unconfigured |
| [sale.order.line.search](cli-v4-manual/scenarios/sales-purchase-history.md#cap-sale-order-line-search) | 搜索销售订单行 | 只读 | unconfigured |
| [sale.order.lines.replace](cli-v4-manual/scenarios/sales-purchase-history.md#cap-sale-order-lines-replace) | 替换草稿销售订单行 | 写入 | unconfigured |
| [sale.order.pdf.export](cli-v4-manual/scenarios/sales-purchase-history.md#cap-sale-order-pdf-export) | 导出销售订单 PDF | 只读 | unconfigured |
| [sale.order.reset_to_draft](cli-v4-manual/scenarios/sales-purchase-history.md#cap-sale-order-reset_to_draft) | 将销售订单重置为草稿 | 写入 | unconfigured |
| [sale.order.search](cli-v4-manual/scenarios/sales-purchase-history.md#cap-sale-order-search) | 搜索销售订单 | 只读 | unconfigured |
| [sale.order.update_draft](cli-v4-manual/scenarios/sales-purchase-history.md#cap-sale-order-update_draft) | 更新草稿销售订单 | 写入 | unconfigured |
### 历史库存物流、可用量、拣货与实物退货（19项）

查阅仓库、库位、操作类型和路线，查询现有库存、产品可用量、库存移动及调拨，创建、确认、预留、设定数量、取消或验证调拨，并导出送货单、拣货操作单和实物退货单。这里是物流与历史库存能力，不是会计核心核销或贷项现金退款；会计估值和分录在库存会计场景。

[打开本场景完整接口章节](cli-v4-manual/scenarios/stock-logistics-history.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [inventory.availability.inspect](cli-v4-manual/scenarios/stock-logistics-history.md#cap-inventory-availability-inspect) | 检查产品可用量 | 只读 | unconfigured |
| [inventory.on_hand.summary](cli-v4-manual/scenarios/stock-logistics-history.md#cap-inventory-on_hand-summary) | 汇总现有库存 | 只读 | unconfigured |
| [stock.delivery_slip.pdf.export](cli-v4-manual/scenarios/stock-logistics-history.md#cap-stock-delivery_slip-pdf-export) | 导出送货单 PDF | 只读 | unconfigured |
| [stock.location.list](cli-v4-manual/scenarios/stock-logistics-history.md#cap-stock-location-list) | 列出库存库位 | 只读 | unconfigured |
| [stock.move.search](cli-v4-manual/scenarios/stock-logistics-history.md#cap-stock-move-search) | 搜索库存移动 | 只读 | unconfigured |
| [stock.operation_type.list](cli-v4-manual/scenarios/stock-logistics-history.md#cap-stock-operation_type-list) | 列出库存作业类型 | 只读 | unconfigured |
| [stock.picking_operations.pdf.export](cli-v4-manual/scenarios/stock-logistics-history.md#cap-stock-picking_operations-pdf-export) | 导出调拨操作单 PDF | 只读 | unconfigured |
| [stock.return_slip.pdf.export](cli-v4-manual/scenarios/stock-logistics-history.md#cap-stock-return_slip-pdf-export) | 导出退货单 PDF | 只读 | unconfigured |
| [stock.route.list](cli-v4-manual/scenarios/stock-logistics-history.md#cap-stock-route-list) | 列出库存路线 | 只读 | unconfigured |
| [stock.transfer.assign](cli-v4-manual/scenarios/stock-logistics-history.md#cap-stock-transfer-assign) | 为库存调拨保留库存 | 写入 | unconfigured |
| [stock.transfer.cancel](cli-v4-manual/scenarios/stock-logistics-history.md#cap-stock-transfer-cancel) | 取消库存调拨 | 写入 | unconfigured |
| [stock.transfer.confirm](cli-v4-manual/scenarios/stock-logistics-history.md#cap-stock-transfer-confirm) | 确认库存调拨 | 写入 | unconfigured |
| [stock.transfer.create](cli-v4-manual/scenarios/stock-logistics-history.md#cap-stock-transfer-create) | 创建库存调拨 | 写入 | degraded |
| [stock.transfer.get](cli-v4-manual/scenarios/stock-logistics-history.md#cap-stock-transfer-get) | 获取库存调拨 | 只读 | unconfigured |
| [stock.transfer.quantities.set](cli-v4-manual/scenarios/stock-logistics-history.md#cap-stock-transfer-quantities-set) | 设置库存调拨完成数量 | 写入 | unconfigured |
| [stock.transfer.search](cli-v4-manual/scenarios/stock-logistics-history.md#cap-stock-transfer-search) | 搜索库存调拨 | 只读 | unconfigured |
| [stock.transfer.unreserve](cli-v4-manual/scenarios/stock-logistics-history.md#cap-stock-transfer-unreserve) | 取消库存调拨保留 | 写入 | unconfigured |
| [stock.transfer.validate](cli-v4-manual/scenarios/stock-logistics-history.md#cap-stock-transfer-validate) | 完成库存调拨 | 写入 | unconfigured |
| [warehouse.list](cli-v4-manual/scenarios/stock-logistics-history.md#cap-warehouse-list) | 列出仓库 | 只读 | unconfigured |
### 公司上下文、权限诊断与预留操作审计（9项）

确认可用公司上下文、公司会计配置和处理设置，检查运行环境、用户会计访问以及中国和新加坡本地化配置。operation.audit.get 与 operation.status.get 是禁用预留，不可据此假设存在持久操作审计或统一审批执行；连接配置和通用 CLI 外壳的调用方法见总指南。

[打开本场景完整接口章节](cli-v4-manual/scenarios/technical-context-reserved.md)

| 能力ID | 用途 | 读写 | 状态 |
|---|---|---|---|
| [company.accounting_configuration.inspect](cli-v4-manual/scenarios/technical-context-reserved.md#cap-company-accounting_configuration-inspect) | 检查公司会计配置 | 只读 | unconfigured |
| [company.accounting_context.list](cli-v4-manual/scenarios/technical-context-reserved.md#cap-company-accounting_context-list) | 列出可用会计公司上下文 | 只读 | unconfigured |
| [company.processing_settings.get](cli-v4-manual/scenarios/technical-context-reserved.md#cap-company-processing_settings-get) | 查看公司会计业务设置 | 只读 | unconfigured |
| [diagnostic.accounting_environment.inspect](cli-v4-manual/scenarios/technical-context-reserved.md#cap-diagnostic-accounting_environment-inspect) | 检查会计运行环境 | 只读 | unconfigured |
| [localization.china.configuration.inspect](cli-v4-manual/scenarios/technical-context-reserved.md#cap-localization-china-configuration-inspect) | 检查中国会计本地化配置 | 只读 | unconfigured |
| [localization.singapore.configuration.inspect](cli-v4-manual/scenarios/technical-context-reserved.md#cap-localization-singapore-configuration-inspect) | 检查新加坡会计本地化配置 | 只读 | unconfigured |
| [operation.audit.get](cli-v4-manual/scenarios/technical-context-reserved.md#cap-operation-audit-get) | 读取 V4 操作审计链 | 只读 | disabled |
| [operation.status.get](cli-v4-manual/scenarios/technical-context-reserved.md#cap-operation-status-get) | 读取 V4 操作状态 | 只读 | disabled |
| [user.accounting_access.inspect](cli-v4-manual/scenarios/technical-context-reserved.md#cap-user-accounting_access-inspect) | 检查用户会计访问权限 | 只读 | unconfigured |
