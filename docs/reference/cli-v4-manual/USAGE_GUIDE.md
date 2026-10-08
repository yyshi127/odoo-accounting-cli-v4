# CLI V4 中文总使用指南

文档快照：2026-10-03；对应当前 `0.0.0` / `bootstrap` 接口。全量业务分类、每个能力的参数与返回字段见[说明书主入口](../CLI_V4_MANUAL.md)。本文说明怎样正确调用，不表示全部能力已经在当前用户、公司或生产环境验收。

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

本说明书提供[离线请求键助手](request_key.py)，在仓库根目录使用已有 Python 环境：

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

另有 `period.accrual.generate`、`period.transfer.run`、`localization.china.period_transfer.run` 的有界能力；执行前仍需当前原生前提、普通用户权限及授权。借项单 addon 未安装的已知依赖不能用贷项单代替宣布通过。完整范围与历史证据见[核心验收及收尾边界](../../execution/ACCOUNTING_ACCEPTANCE.md)，状态以最新记录为准；不得擅自安装原生 addon 或修复生产插件。

## 7. 新会话交接与证据口径

交接至少记录：实际安装版本及 registry digest、准确能力 ID、批准的 alias/company/user 范围、请求 ID、请求参数与写入键、用户授权范围、退出码、完整 JSON 警告/错误、读回所核对的金额/状态/关系。只保留必要业务证据，秘密配置和真实私有日志不贴进公共文档。

把以下情况分开写：已实现接口、当前可用、已验证场景、模拟/fixture 正例、规划/disabled、原生依赖受阻、回执未知。日常核心共享隔离验收并不覆盖所有命令、生产银行配置、真实外发、并发 exactly-once 或全部资产/递延/税务流程。文档中的合成请求是教学数据，不是执行结果。

本次文档只依据本地代码/schema 和离线帮助/元数据核对，没有连接 Odoo、读取真实配置或密钥、执行业务读写、重新运行 native smoke 或修改服务。总目标的暂停状态不因说明书新增而改变。

## 8. 事实来源与更新方式

接口变动时先更新代码和 schema，再重新生成目录/字段并复核指南；历史 README、能力名称、描述符测试状态或此前聊天均不能替代当前合同。

- [CLI 语法、请求加载、分发、错误和未实现入口](../../../src/odoo_accounting_cli_v4/cli.py)：`_parser`、`_load_request`、`_status_for_exit`、`_configured_port_factory`、`main`。
- [运行配置](../../../src/odoo_accounting_cli_v4/config.py)：`load_runtime_config`、`RuntimeConfig.resolve`、隔离数据库 allowlist。
- [通用响应](../../../src/odoo_accounting_cli_v4/contracts.py)、[请求 envelope schema](../../../schemas/v1/request.schema.json)、[响应 envelope schema](../../../schemas/v1/response.schema.json)。
- [科目读取请求](../../../schemas/v1/account.account.list.request.schema.json)及[读取校验器](../../../src/odoo_accounting_cli_v4/capabilities/account_account_list.py)：本文完整只读例子的字段和分页规则。
- [固定核心写入合同与键](../../../src/odoo_accounting_cli_v4/capabilities/core_writes.py)：`validate_core_write_request`、`_expected_idempotency_key`、`execute_core_write`；[发送类写入校验](../../../src/odoo_accounting_cli_v4/capabilities/accounting_delivery.py)。
- [桥接子进程](../../../src/odoo_accounting_cli_v4/bridge/client.py)及[原生事务/用户范围](../../../src/odoo_accounting_cli_v4/bridge/runtime.py)：固定 action、普通用户环境、读取回滚与写入提交边界。
- [完整注册表](../../../capabilities/v1/registry.json)、[包版本及 Python 范围](../../../pyproject.toml)、[主说明书](../CLI_V4_MANUAL.md)：全量 ID、schema、状态及业务分类导航。

本指南不补实现缺口、不授权执行写入，也不把已安装 `0.0.0` 包描述为完成生产发布。详细参数与键配方以主说明书和当次 `capabilities describe` 为准。
