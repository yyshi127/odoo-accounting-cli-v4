---
name: odoo-accounting-cli-v4
description: 通过版本化能力注册表安全调用 Odoo 19 会计读写接口；用于会计科目、总账、发票、收付款、核销、资产、汇兑、库存估值、财务报表及中国/新加坡本地化任务。 Use the versioned capability registry to route Odoo 19 accounting work.
---

# Odoo Accounting CLI V4

本 Skill 负责把 Pi 引导到 V4 的能力注册表。不要凭记忆拼接模型名、ORM
方法或旧版命令，也不要把自然语言关键词直接当成最终路由结果。

## 固定路由流程

1. 首次使用或注册表摘要发生变化时执行：

   ```text
   odoo-accounting-cli-v4 capabilities list
   ```

2. 根据用户意图中的会计领域、业务对象、读写动作以及注册表的
   `routing.aliases` / `routing.not_for` 筛选候选能力。
3. 对候选稳定 ID 必须执行：

   ```text
   odoo-accounting-cli-v4 capabilities describe <capability-id>
   ```

4. 按返回的 request schema 补齐 context 和 parameters。缺少必填信息时只询问
   缺少的字段；出现多个合理候选时向用户做最小澄清，不得自行猜测。
5. 读取操作把一个 JSON 请求从 stdin 传入：

   ```text
   odoo-accounting-cli-v4 read <capability-id> --request -
   ```

6. 写操作只能遵循 `write prepare → approve → execute → operations verify`；不得
   绕过预览、审批、幂等键或提交后验证。
7. 只把 stdout 的单个 JSON 文档作为结果，并核对 `schema_version`、
   `request_id`、`capability`、`success`、`status` 和 `error`。stderr 仅是诊断，
   不能当成业务结果。

## 安全边界

- 不得调用任意 Odoo 模型或任意 ORM 方法；只能调用注册表中存在且 CLI
  内部 allowlist 已绑定的 capability ID。
- 数据库、公司和用户必须来自已配置的别名/allowlist；自然语言公司名称不能
  被直接猜成 `company_id`。
- `degraded` 或不可用状态必须向用户如实说明。只有调用成功且返回状态通过
  验证后，才能说明 Odoo 操作成功。
- “列出会计科目”与“查询科目余额、总账明细、试算平衡表”不是同一能力；
  必须遵循注册表中的排除意图和消歧信息。
