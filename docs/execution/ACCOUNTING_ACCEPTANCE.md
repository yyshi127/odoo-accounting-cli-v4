# CLI V4 日常核心验收与收尾清单

更新：2026-10-02，Asia/Shanghai。能力代码基线：`3700271`。

本文回答“做到什么程度算完成”，不是更改目标或宣布完成。
用户已确认第一阶段先验收日常核心流程；非零固定资产完整流程、
多期自动递延、最终锁期和法定税结账单列后续未完成。
既有缺失、原生故障和后续阶段工作不得因这份清单被删除或改记为完成。

## 1. 结束依据

第一阶段以 Agent 能完成实际会计工作为依据，不以命令数量为依据。
按下面八类流程和第 6 节固定场景逐项验证；全部必需场景通过后，
结束第一阶段的无边界能力扩充。后续新增筛选字段、模型、国家包或边缘组合，
需要说明对应业务需求，不自动增加这一阶段的验收分母。

第一阶段验收通过不等于整个目标完成，更不等于生产发布完成。
统一审批、审计、证据封存、离线交付和发布门禁仍是原目标中的后续阶段，
不能提前省略，也不应为每个命令分别建设大型控制体系。

本次收尾按第 6 节固定的 12 个连贯场景登记，不能按字段、命令或重复调用计数。
目前尚未按这份清单完成逐项最终验收，因此不从历史元数据换算通过比例。
该比例即使达到 100%，也仅代表日常核心第一阶段，不是整个会计模块或总目标。

## 2. 本轮已核实的事实

- 本地和服务器注册表一致：559 个注册 ID、544 个已绑定处理器，
  其中读取 253、写入 291；1094 个 schema。
- 544 个处理器都存在对应的 CLI 读取分发或固定写入白名单，
  请求/响应 schema 存在，注册表完整加载通过，测试引用文件存在。
  这是结构检查，不是 544 个业务场景全部验收通过。
- 注册表有 15 个 disabled ID；其余状态为 465 unconfigured、79 degraded。
  unconfigured 表示按调用上下文评估，不能直接解释为 465 个都不可用；
  degraded 的具体并发幂等、删除重试等限制必须保留。
- 集成元数据为 541 implemented、2 planned、1 failed。
  implemented 是历史记录，不能据此计算业务完成率或当前用户可用率。
- 当前配置账号的既有只读权限测试在两隔离库、公司 1/2 通过：
  4 passed，59.58 秒。账号 UID 5 不是会计 manager；科目、日记账、税、
  报表模型的配置写权限不能从分录写权限推导出来。
- 上一批 29 个部署文件、六个审计原生文件及服务 PID/重启计数 fresh 核对一致。
  本轮没有新增能力、运行写 fixture、修改 ACL、业务账套、原生插件或服务。
- 历史财报导出的原始 focused/native/public-CLI 证据在服务器仍存在，
  三个 SHA-256 与既有记录一致。它们仍是历史证据，不是本轮全量重测。

## 3. 八类核心流程及现有证据

下表列代表性准确 ID，不是完整命令清单。代码、schema 或单元测试存在，
不能单独证明业务闭环。真实 smoke 的测试范围和权限前提必须一起阅读。

| 流程 | 现有命令及读回 | 当前证据与待核实边界 |
| --- | --- | --- |
| 基础资料与必要配置 | `account.account.create`、`account.account.update`、`account.account.get`；`journal.create`、`journal.get`；`tax.create`、`tax.compute`；`payment_term.compute`；`fiscal_position.resolve`；`company.processing_settings.get` | 配置维护、税/分期消费者、公司默认账户与读回有双库正例。部分配置正例临时补齐普通用户角色并回滚，不代表当前 UID 5 已获权限。需确定实际 accountant/manager 角色及必需配置。 |
| 客户发票、收款与退款 | `customer_invoice.create`、`invoice.update`、`invoice.post`、`receivable.payment.register`、`customer_credit_note.create`；`invoice.get`、`invoice.payment_status.inspect`、`payment.get` | 有创建、过账、分期/部分收款、已收款来源的贷项与现金退款链式正例；现金退款方向 outbound 已核对。财务贷项不等于退货物流，登记付款不等于银行真实转账。 |
| 供应商账单、付款与退款 | `vendor_bill.create`、`invoice.post`、`payable.payment.register`、`vendor_refund.create`；同上读回 | 有双库付款、分期/部分付款、供应商退款 inbound 正例。不能将多期自动递延受阻的供应商场景记为通过。 |
| 手工凭证及冲销 | `journal_entry.create`、`journal_entry.update`、`journal_entry.lines.replace`、`journal_entry.lines.update`、`journal_entry.post`、`journal_entry.reverse`；`journal_entry.get`、`journal_item.search` | 普通分录生命周期、平衡、外币金额修改、手工税消费者有正例。非法金额、已过账修改及全批次预检有测试；不据此覆盖所有锁账、哈希、国家包分支。 |
| 银行流水与对账 | `bank.transaction.record`、`bank.transaction.search`、`bank.transaction.match`、`bank.transaction.unmatch`、`bank.transaction.counterparts.replace`；`bank.statement.create`、`bank.statement.get`、`payment.get` | 已有实际付款 outstanding 行与流水匹配、payment 原生银行引用读回、对账单归组分页正例。使用独立合成银行配置；不证明既有银行 journal 的 suspense/outstanding 设置已经适用。 |
| 核销、撤销及差额 | `reconciliation.apply`、`reconciliation.automatic.run`、`reconciliation.undo`、`reconciliation.write_off`；`receivable.payment.register`、`payable.payment.register`；`journal_item.reconciliation.inspect`、`reconciliation.partial.get`、`reconciliation.full.get` | 部分/全额/完整匹配组撤销和余额恢复有双库正例。发票/账单少付款差额用收付款的 payment_difference_handling=reconcile 和 writeoff_account_id；reconciliation.write_off 仅处理银行流水差额，两者不能混同。现金制税/汇兑差额撤销、已付款重开等分支尚不能宣称验收；应先判断是否为本阶段必需需求。 |
| 账簿、财报与导出 | `report.trial_balance`、`report.general_ledger`、`report.partner_ledger`、`report.balance_sheet`、`report.profit_and_loss`、`report.cash_flow`、`report.tax`、`report.aged_receivable`、`report.aged_payable`；对应 `.export` ID | 历史双库 PDF/XLSX 导出、两项外部 CLI 导出证据已 fresh 核对保留。日记账筛选和非空 XLSX/native 金额对照有记录；PDF 文件结构/hash 成功不是 PDF 数值内容核对，更不是法定申报覆盖。 |
| 常用期末处理 | `period.accrual.generate`、`period.transfer.run`、`localization.china.period_transfer.run`、`multicurrency.revaluation.generate_entries`、`company.lock_dates.inspect` | 已有应计、结转等有界正例；普通期末调整可用 `journal_entry.create`/`journal_entry.post`。最终锁期尚无处理器；资产、多期递延、报表绑定税结账及非空期末报告还不能整体宣称闭环。 |

现有分析读取、预算、币种汇率和会计库存估值能力仍保留。
历史销售、采购、拣货和物理退货命令不计入当前会计核心完成率；
这不排除会计端的销购单据关联、成本及估值需求。

## 4. 有限收尾事项：缺能力、缺证据和依赖分别记录

| 项目 | 已确认状态 | 下一步及权限边界 |
| --- | --- | --- |
| 目标角色与银行前提 | 当前 accountant 权限已复核；117 个描述符声明会计 manager 组要求，这不是 117 个失败结果。部分测试角色及配置仅事务内存在。 | 列清哪些日常操作由 accountant 执行、哪些配置由普通 manager 执行；检查必需银行配置。不得偷偷加组、sudo 或重配既有业务银行。 |
| 核心流程连贯验收及 JSON 入口 | 近期链式正例多为 in-process CLI + real ORM；历史外部 CLI/bridge 正例存在，但不构成所有当前命令逐项外部 E2E。 | 固定必需场景，复用共享 smoke 和必要的外部 CLI/JSON 入口抽样，不为 544 个命令分别造门禁；仅在两隔离库写验证并完整回滚。 |
| 最终锁期及结账检查 | `period.lock.change`、`validation.period_close.check` 无处理器。`period.adjustment.create` 也无处理器，但普通调整分录已有业务替代。 | 明确“常用期末”是否必须含最终锁期、原生自动调整向导和结账检查；如为必需则补齐，不能将替代业务命令冒充精确 ID 已实现。 |
| 固定资产 | `asset.validate` 原生失败；`asset.modify`、`asset.resume` 无处理器。零值 cancel/dispose 正例不能证明非零折旧及处置损益闭环。 | 原生插件修复需另获授权；先保留故障与缺失，不用零值场景绕过后宣布完成。 |
| 多期自动递延与期末金额 | 历史多期 `invoice.post` 失败；单期 `deferred_expense.generate_entries`/`deferred_revenue.generate_entries` 成功不能替代它。部分期末报告只有空结果证据。 | 保留 supplier/refund 未到达及非空报告核对缺口。自动多期插件修复需另获授权；已有原始失败日志及插件文件 hash 本轮核对未变。 |
| 税结账与申报 | 通用非空税账务报告有正例；现金制税首次付款到 CABA 分录的完整消费者链尚缺验收。`account.return.validate`、`account.return.mark_submitted` 的 manual/reportless 工作流不证明 report-bound tax closing 或税局送达。 | 确定目标公司的法定税务流程；没有明确需求与原生支持证据，不把所有国家申报自动加入第一阶段，也不宣称它们完成。 |
| 借项单原生依赖 | 既有记录确认借项单 addon 未安装，安装未获授权；不能把贷项/退款能力当成借项单正例。 | 明确借项单是否为第一阶段必需业务；如必需，先获得安装及隔离验收范围的授权，不擅自改原生环境。 |
| 客户对账单与催款外发 | `report.customer_statement.send`、`report.followup.send` 正向验收待补；历史验证了权限拒绝。导出成功不能推导发送成功。 | 需要适当普通用户权限和明确外发授权；不得擅自发真实邮件。 |
| 历史 disabled 边界 | 合规国家包、PINT、估值调整及审计/操作状态等仍有 disabled ID。 | 完整列在下节；分别决定必需、后续阶段或不在当前业务需求内。在用户批准前不能自行删除范围或改记完成。 |

上一轮候选 8 EXT / 0 NEW（业务输入投影、分析筛选）尚未实现或部署。
它们不是本轮发现的必需缺口清单，不应仅为凑批次数优先于收尾验收。
旧 G3 的 52 个扩展和 9 个边界决策是历史审查记录，不是当前精确剩余数量，
也不构成无限补字段的依据。

## 5. 当前 15 个无处理器 ID：不能漏记

- 资产：`asset.modify`、`asset.resume`。
- 期末：`period.adjustment.create`、`period.lock.change`、`validation.period_close.check`。
- 会计估值：`inventory.valuation.adjust`。
- 新加坡：`compliance.singapore.assessment.run`、`compliance.singapore.filing.list`、
  `compliance.singapore.filing.prepare`、`compliance.singapore.filing.submit`、
  `compliance.singapore.findings.list`、`compliance.singapore.registration.verify`、
  `invoice.singapore.pint.export`。
- 后续控制：`operation.audit.get`、`operation.status.get`。

15 不是“还差 15 个就完成”的分母：其中有后续阶段项及待确定业务边界，
已有处理器也可能仍缺真实正例或受到环境限制。

## 6. 已确认收尾方向下的固定场景与停止规则

以下是执行清单，不是新增命令清单。历史正例作为起点，最终复核应注明
源码版本、实际普通用户/公司、fixture 前提及真实结果，不能默认为全部通过。

| 场景 | 连贯操作及核对结果 |
| --- | --- |
| S01 发现与基础读取 | 从 CLI/JSON 读取公司、用户权限、科目、日记账、伙伴、税和付款条款；选用可访问的真实 ID，区分当前用户权限与事务内 fixture 配置。 |
| S02 客户开票收款 | 创建并编辑含税客户发票，过账，部分收款后结清；读回金额、状态、应收未结和付款关联。 |
| S03 供应商账单付款 | 创建并编辑含税供应商账单，过账，部分付款后结清；读回金额、状态、应付未结和付款关联。 |
| S04 客户贷项与现金退款 | 对未收款来源做部分财务贷项并核销；对已收款来源做现金退款；核对原单/贷项余额及 outbound 方向。 |
| S05 供应商贷项与现金退款 | 对未付款来源做部分供应商退款单并核销；对已付款来源做现金退款；核对余额及 inbound 方向。 |
| S06 手工凭证与冲销 | 创建、编辑、过账平衡凭证，再冲销；读回源单和冲销单的日期、关联、反向金额及平衡结果。 |
| S07 银行流水与实际匹配 | 记录流水、归组对账单、分页读取；匹配实际付款 outstanding 行后读回银行引用，撤销匹配后核对关系及余额恢复。 |
| S08 部分/全额核销与撤销 | 对可核销项目进行部分和全额核销，撤销指定关系/完整匹配组；读回残余、partial/full 图及来源财务行未被意外改写。 |
| S09 发票与账单付款差额 | 两方向分别做 100 应收/应付、99 实付、1 差额；读回差额账户、符号、付款金额、平衡结果及残余零。 |
| S10 非空账簿与报表 | 从合成业务读取试算、总账、伙伴账、资产负债、损益、现金流、通用税及账龄结果；核对原生范围/金额和公司币语义，验证相关分析读取。不是法定税申报验收。 |
| S11 导出与共享入口 | 验证 PDF/XLSX 合同、文件类型/hash和非空 XLSX 金额；共享 CLI stdin/stdout JSON 与 bridge 入口抽样，不为每个命令各建门禁。 |
| S12 日常纠错与期间调整 | 验证草稿取消/恢复/行维护以及普通期间调整凭证的日期和报表读回；检查已过账、不平衡、错误公司/父记录、无效确认和键冲突拒绝。不是最终锁期验收。 |

十二个场景共享现有框架、必要测试及隔离回滚方案，不建设新的验收平台。
没有收尾需求的可选字段不自动增加场景；新增必需业务须先说明并更新范围。

1. 按用户已确认的日常核心方向执行上述固定清单；先核对实际普通用户角色
   及必要配置，不擅自赋权或 sudo。未确认的其他边界不默认为已完成。
2. 每个必需场景可通过既有 CLI/统一 JSON 合同调用，完成操作后读取核对
   单据状态、余额/核销关系或报表金额；有相应真实 Odoo 证据，不能只靠 registry。
3. 写操作保持原生 ACL、公司/用户范围、明确确认及诚实的幂等限制。
   现有 delete 无 tombstone、并发 exactly-once 等限制不因验收被隐去。
4. 新增或修复按相关小批共享测试，不重跑已接受的历史句柄冒充新证据。
   所有写验证限两隔离库；不动业务账套、原生插件和既有服务链路。
5. 必需缺口全部解决且验收通过，才宣布第一阶段完成。
   必需项受阻则仍为未完成；只有用户明确批准后续处理，才可移入下一阶段。
6. 此后停止主动寻找无穷字段缺口；按新业务需求或原目标的统一控制/交付阶段推进。

完成日期应在固定清单的实际缺口及外部依赖核对后估算。
当前不能负责任地给出剩余天数；外部授权等待与可实施工作应分开排期。

## 7. 可复查的证据入口

- [当前计数及批次状态](STATUS.md)、[历史工作流与限制](HANDOFF.md)、
  [未缩减的目标摘要](GOAL_SUMMARY.md)、[历史 G3 范围校准](G3.md)。
- 当前账号只读权限：[test_accounting_access_live.py](../../tests/integration/test_accounting_access_live.py)。
- 发票/退款/分期：[test_invoice_rounds_live.py](../../tests/integration/test_invoice_rounds_live.py)。
- 重开、核销组撤销、银行实际匹配：[test_accounting_workflows_batch_live.py](../../tests/integration/test_accounting_workflows_batch_live.py)。
- 外部 CLI JSON 写入口的历史测试：[test_core_write_batch_live.py](../../tests/integration/test_core_write_batch_live.py)。
  其现存旧脚本没有总事务/fresh-cursor 回滚验证，不能为补入口证据直接重跑；
  若需要新验证，应使用受控的隔离回滚方案，不能省略当前安全边界。
- 非空税消费者：[test_accounting_payment_tax_inputs_batch_live.py](../../tests/integration/test_accounting_payment_tax_inputs_batch_live.py)。
- 财报导出：[test_financial_report_export_batch_live.py](../../tests/integration/test_financial_report_export_batch_live.py)。
- 受阻递延：[test_deferred_invoice_lines_live.py](../../tests/integration/test_deferred_invoice_lines_live.py)。

私有核对结果保留在本轮忽略目录，原始环境日志不发布到公共 Git 仓库。
本轮不宣布完整会计覆盖、不更改 goal 状态，也不宣称全测试套件或生产发布通过。
用户的阶段选择不授权修改原生插件、真实外发或变更业务账套。
