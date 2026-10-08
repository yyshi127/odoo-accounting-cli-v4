#!/usr/bin/env python3
"""Generate the complete Chinese manual from local public contracts, without Odoo."""

from __future__ import annotations

import argparse
import copy
import hashlib
import html
import importlib.util
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urldefrag

from jsonschema import Draft202012Validator

from odoo_accounting_cli_v4.registry import load_registry

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/reference/cli-v4-manual"
CONTEXT = {"database": "v4-dev", "company_id": 1, "user_login": "example.operator",
           "language": "zh_CN", "timezone": "Asia/Shanghai"}
UUID = "11111111-1111-4111-8111-111111111111"
BOUND_KEYS = ("const", "enum", "format", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
              "multipleOf", "minLength", "maxLength", "pattern", "minItems", "maxItems", "uniqueItems",
              "minProperties", "maxProperties", "additionalProperties", "propertyNames", "prefixItems", "default")
RULE_KEYS = ("oneOf", "anyOf", "allOf", "if", "then", "else", "not", "dependentRequired", "dependentSchemas", "contains")
LABELS = {"limit": "每页数量", "cursor": "不透明分页游标；新查询先省略，后续原样使用返回值",
          "move_id": "会计单据记录ID", "move_ids": "会计单据ID数组", "payment_id": "付款/收款记录ID",
          "company_id": "所选公司ID", "partner_id": "合作伙伴ID", "journal_id": "日记账ID",
          "account_id": "会计科目ID", "tax_ids": "应用税ID数组", "line_ids": "行记录ID数组",
          "date_from": "开始日期", "date_to": "结束日期", "as_of": "截至日期",
          "currency_id": "币种ID", "amount": "十进制数值；金额、固定税额或税率按所在业务对象解释",
          "changes": "仅提交拟变更字段，非整条记录", "lines": "行数组；增补/更新/替换语义由能力ID决定",
          "query": "搜索文本", "format": "输出格式", "state": "状态", "name": "名称/行说明",
          "analytic_distribution": "分析分摊映射；写入与读回约束可能不同",
          "invoice_id": "发票/账单记录ID（具体类型按能力定义）", "entry_id": "分录记录ID",
          "transaction_id": "银行流水记录ID", "bank_statement_id": "银行对账单ID",
          "partial_reconcile_id": "部分核销关系ID", "full_reconcile_id": "完整核销关系ID",
          "quantity": "数量；单位、符号和精度依具体接口", "price_unit": "单价；币种及符号依单据和合同",
          "debit": "借方值；不得丢弃原生storno符号", "credit": "贷方值；不得丢弃原生storno符号",
          "balance": "余额；币种与范围取决于本对象", "amount_currency": "外币/交易币数值，非默认公司币金额",
          "display_type": "业务行/章节/备注类型", "discount": "折扣百分比",
          "deductible_amount": "可抵扣百分比，不是可抵扣货币金额", "payment_state": "原生付款结算状态",
          "has_more": "是否仍有后续页", "next_cursor": "下一页不透明游标，无后续时可为空",
          "idempotent_replay": "按本能力规则识别的当前重复，不是全局exactly-once承诺"}


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(data):
    return hashlib.sha256(data).hexdigest()


class Schemas:
    def __init__(self):
        self.files = {f"schemas/v1/{path.name}": json.loads(path.read_text(encoding="utf-8"))
                      for path in sorted((ROOT / "schemas/v1").glob("*.json"))}
        self.ids = {value["$id"]: path for path, value in self.files.items()}

    def resolve(self, node, document, seen=()):
        if not isinstance(node, dict) or "$ref" not in node:
            return node, document
        ref = node["$ref"]
        base, pointer = urldefrag(ref)
        target = self.ids.get(base) if base.startswith("https://") else f"schemas/v1/{Path(base).name}" if base else document
        if target not in self.files or (target, pointer) in seen:
            raise ValueError(f"Unresolved or recursive local reference: {ref}")
        value = self.files[target]
        for part in unquote(pointer).split("/")[1:]:
            value = value[part.replace("~1", "/").replace("~0", "~")]
        value, resolved_document = self.resolve(value, target, (*seen, (target, pointer)))
        merged = {**value, **{key: item for key, item in node.items() if key != "$ref"}}
        # Schema siblings here are descriptions/constraints, never a replacement object tree.
        for key in ("properties", "required", "oneOf", "anyOf", "allOf"):
            if key in node and key in value and node[key] != value[key]:
                raise ValueError(f"Nontrivial reference sibling needs explicit handling: {ref}")
        return merged, resolved_document

    def rows(self, node, document, path, required="必填", branch="", depth=0):
        if depth > 32:
            raise ValueError("Schema nesting exceeds documentation traversal limit")
        raw_ref = node.get("$ref") if isinstance(node, dict) else None
        node, document = self.resolve(node, document)
        if not isinstance(node, dict):
            return [(path, "任意" if node else "禁止", required, branch, "", dump(node))]
        kind = node.get("type", "组合/开放结构" if any(k in node for k in RULE_KEYS) else "未限定")
        kind = "/".join(kind) if isinstance(kind, list) else kind
        bounds = {key: node[key] for key in BOUND_KEYS if key in node}
        if "required" in node:
            bounds["required_in_object"] = node["required"]
        rules = {key: node[key] for key in RULE_KEYS if key in node}
        if raw_ref:
            bounds["resolved_ref"] = raw_ref
        meaning = node.get("description") or LABELS.get(path.rsplit(".", 1)[-1].replace("[]", ""), "")
        rows = [(path, kind, required, branch, meaning, dump({**bounds, **rules}) if bounds or rules else "")]
        needed = node.get("required", [])
        for key, value in node.get("properties", {}).items():
            rows.extend(self.rows(value, document, f"{path}.{key}",
                                  "必填（所在对象出现时）" if key in needed else "可选（可能有条件限制）", branch, depth+1))
        if isinstance(node.get("items"), (dict, bool)):
            item_scope = "固定前缀以外的剩余元素" if node.get("prefixItems") else "每个数组元素"
            rows.extend(self.rows(node["items"], document, path+"[]", item_scope, branch, depth+1))
        for index, value in enumerate(node.get("prefixItems", [])):
            rows.extend(self.rows(value, document, f"{path}[{index}]", "固定位置元素", branch, depth+1))
        for pattern, value in node.get("patternProperties", {}).items():
            rows.extend(self.rows(value, document, path+"{匹配:"+pattern+"}", "动态键", branch, depth+1))
        if isinstance(node.get("additionalProperties"), dict):
            rows.extend(self.rows(node["additionalProperties"], document, path+"{其他键}", "动态键值", branch, depth+1))
        for keyword in ("oneOf", "anyOf", "allOf"):
            for index, value in enumerate(node.get(keyword, []), 1):
                rows.extend(self.rows(value, document, path, "分支约束", f"{branch}/{keyword}[{index}]".strip("/"), depth+1))
        for keyword in ("then", "else"):
            if keyword in node:
                rows.extend(self.rows(node[keyword], document, path, "条件分支", f"{branch}/{keyword}".strip("/"), depth+1))
        return rows

    def property_nodes(self, schema, document, name):
        schema, document = self.resolve(schema, document)
        result = [(schema["properties"][name], document)] if name in schema.get("properties", {}) else []
        for branch in schema.get("allOf", []):
            result.extend(self.property_nodes(branch, document, name))
        return result

    def sample(self, node, document, name="", index=0):
        node, document = self.resolve(node, document)
        if "const" in node:
            return copy.deepcopy(node["const"])
        if "enum" in node:
            if name == "repartition_type":
                return "base" if index == 0 else "tax"
            return copy.deepcopy(next((v for v in node["enum"] if v is not None), node["enum"][0]))
        for keyword in ("oneOf", "anyOf"):
            for branch in node.get(keyword, []):
                candidate, _ = self.resolve(branch, document)
                if candidate.get("type") != "null":
                    merged = {**{k: v for k, v in node.items() if k != keyword}, **candidate}
                    for key in ("properties",):
                        if key in node and key in candidate:
                            merged[key] = {**node[key], **candidate[key]}
                    if "required" in node or "required" in candidate:
                        merged["required"] = list(set(node.get("required", []) + candidate.get("required", [])))
                    return self.sample(merged, document, name, index)
        kind = node.get("type", "object" if "properties" in node else "string")
        if isinstance(kind, list):
            kind = next((item for item in kind if item != "null"), "null")
        if kind == "object":
            properties = node.get("properties", {})
            needed = list(node.get("required", []))
            for branch in node.get("allOf", []):
                needed.extend(branch.get("required", []))
            needed = list(dict.fromkeys(needed))
            for key in properties:
                if len(needed) >= node.get("minProperties", 0):
                    break
                if key not in needed:
                    needed.append(key)
            for key in tuple(needed):
                needed.extend(other for other in node.get("dependentRequired", {}).get(key, []) if other not in needed)
            if not properties and node.get("minProperties", 0):
                return {"1": "100"}
            result = {key: self.sample(properties[key], document, key, index) for key in needed if key in properties}
            for branch in node.get("allOf", []):
                if "if" not in branch:
                    continue
                constraint = branch.get("then" if Draft202012Validator(branch["if"]).is_valid(result) else "else", {})
                for key in constraint.get("required", []):
                    if key not in result and key in properties:
                        result[key] = self.sample(properties[key], document, key, index)
                for key, value in constraint.get("properties", {}).items():
                    if key in result:
                        result[key] = self.sample({**properties.get(key, {}), **value}, document, key, index)
            return result
        if kind == "array":
            return [self.sample(node["items"], document, name, i) for i in range(node.get("minItems", 0))]
        if kind == "integer":
            return max(int(node.get("minimum", 1)), index+1)
        if kind == "number":
            return max(node.get("minimum", 1), index+1)
        if kind == "boolean":
            return False
        if kind == "null":
            return None
        if node.get("format") == "date":
            if name == "reversal_date":
                return "2026-11-01"
            return "2026-10-01" if "from" in name or "start" in name else "2026-10-31"
        if node.get("format") == "uuid":
            return UUID
        if node.get("format") == "date-time":
            return "2026-10-03T00:00:00Z"
        if node.get("format") == "email":
            return "example@example.invalid"
        choices = ["1", "100", "0", "0.2", "USD", "1000", "Example", "EXAMPLE", "example@example.invalid", "example.operator", "2026-10-03 09:00:00"]
        if name in {"name", "query", "reference", "payment_ref"}:
            choices.insert(0, "Example")
        if name in {"value_amount", "factor_percent", "original_value"}:
            choices.insert(0, "100")
        if name in {"debit", "credit", "salvage_value"}:
            choices.insert(0, "0")
        for candidate in choices:
            if len(candidate) < node.get("minLength", 0) or len(candidate) > node.get("maxLength", 99999):
                continue
            if "pattern" not in node or re.search(node["pattern"], candidate):
                return candidate
        raise ValueError(f"No honest schema sample for {name}: {dump(node)}")


def field_table(rows):
    text = "| 字段路径 | 类型 | 必填性/作用域 | 分支 | 含义 | 约束/默认值 |\n|---|---|---|---|---|---|\n"
    for row in rows:
        cells = [str(value).replace("|", "&#124;").replace("\n", "<br>") for value in row]
        text += "| " + " | ".join(cells) + " |\n"
    return text


def markdown_html(text, prefix="guide"):
    """Render our small authored Markdown subset, keeping code and tables literal."""
    blocks, code, table = [], None, False
    def inline(value):
        escaped = html.escape(value).replace("&amp;#124;", "&#124;")
        escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
        escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
        def link(match):
            title, target = match.groups()
            if target.endswith(("CLI_V4_MANUAL.md", "USAGE_GUIDE.md")):
                target = "#quickstart"
            elif target.endswith("request_key.py"):
                target = "#request-key"
            elif "/schemas/v1/" in target:
                target = "#schema-"+Path(target).stem
            elif not target.startswith("#"):
                return f'<span title="仓库参考：{target}">{title}</span>'
            return f'<a href="{target}">{title}</a>'
        return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, escaped)
    for line in text.splitlines():
        if line.startswith("```"):
            if code is None:
                code = []
            else:
                blocks.append("<pre><code>"+html.escape("\n".join(code))+"</code></pre>")
                code = None
            continue
        if code is not None:
            code.append(line)
            continue
        if line.startswith('<a id="'):
            continue  # Markdown chapter anchor; the HTML details already owns this ID.
        if line.startswith("|"):
            if re.fullmatch(r"[| :\-]+", line):
                continue
            if not table:
                blocks.append('<div class="table-wrap"><table>')
                table = True
            blocks.append("<tr>"+"".join("<td>"+inline(v.strip())+"</td>" for v in line.strip("|").split("|"))+"</tr>")
            continue
        if table:
            blocks.append("</table></div>")
            table = False
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            level = min(len(line)-len(line.lstrip("#")), 4)
            blocks.append(f'<h{level} id="{prefix}-heading-{len(blocks)}">'+inline(title)+f"</h{level}>")
        elif line.startswith("> "):
            blocks.append('<aside class="note">'+inline(line[2:])+"</aside>")
        elif line:
            blocks.append("<p>"+inline(line)+"</p>")
    if table:
        blocks.append("</table></div>")
    return "\n".join(blocks)


def build(html_path):
    schemas = Schemas()
    registry = load_registry()
    groups = json.loads((DOCS / "SCENARIOS.json").read_text(encoding="utf-8"))
    ordered = [cap for group in groups for cap in group["capabilities"]]
    assert len(ordered) == len(set(ordered)) and set(ordered) == set(registry.ids())
    spec = importlib.util.spec_from_file_location("manual_request_key", DOCS / "request_key.py")
    keys = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(keys)
    guide = (DOCS / "USAGE_GUIDE.md").read_text(encoding="utf-8")
    guide_body = guide.split("\n", 1)[1]
    sha = digest((ROOT / "capabilities/v1/registry.json").read_bytes())
    descriptors = {cap: registry.describe(cap) for cap in registry.ids()}
    counts = {"registered": len(ordered), "implemented": sum(bool(v["handler_key"]) for v in descriptors.values()),
              "registered_access": dict(Counter(v["access"] for v in descriptors.values())),
              "implemented_access": dict(Counter(v["access"] for v in descriptors.values() if v["handler_key"])),
              "status": dict(Counter(v["status"]["value"] for v in descriptors.values()))}
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    intro = f"""# CLI V4 全部命令与 JSON 接口说明书\n\n快照日期：2026-10-03（Asia/Shanghai）。版本：0.0.0/bootstrap，非生产发布。\n\n本书覆盖当前全部 **{len(ordered)}** 个注册能力，其中 **{counts['implemented']}** 个有实现，**{counts['status'].get('disabled', 0)}** 个禁用/预留。已实现包括{counts['implemented_access']['read']}个读取、{counts['implemented_access']['write']}个写入；注册总数还包括禁用项。注册状态是环境无关的静态声明，不等于所选用户有权限或每个接口已经完成真实全流程测试。\n\n依据：当前本地注册表、所有请求/响应 Schema、CLI路由和纯参数校验器。源码基线：{commit}；registry canonical SHA-256：{registry.digest}；文件 SHA-256：{sha}。不依赖 Pi，不建立新审批/服务，不执行 Odoo 业务操作。\n\n> 新会话先读下方快速上手，再到业务场景选能力ID。不能把本书中的合成ID、示例幂等键或`verified`字段当成真实执行证据。每次写入须先确认授权/对象/精确参数，再为实际请求重新计算幂等键。\n\n"""
    index_guide = guide_body.replace("../../../", "../../").replace("../../execution/", "../execution/")
    index_guide = index_guide.replace("](../CLI_V4_MANUAL.md)", "](CLI_V4_MANUAL.md)").replace("](request_key.py)", "](cli-v4-manual/request_key.py)")
    index = intro + index_guide + "\n\n## 全量业务场景目录\n\n"
    nav, articles, cases = [], [], []
    for group in groups:
        slug, title = group["slug"], group["title"]
        caps = group["capabilities"]
        index += f"### {title}（{len(caps)}项）\n\n{group['description']}\n\n[打开本场景完整接口章节](cli-v4-manual/scenarios/{slug}.md)\n\n"
        index += "| 能力ID | 用途 | 读写 | 状态 |\n|---|---|---|---|\n"
        chapter = f"# {title}\n\n{group['description']}\n\n[回到总说明书](../../CLI_V4_MANUAL.md) · [新会话使用指南](../USAGE_GUIDE.md)\n\n"
        cards = []
        nav.append(f'<a href="#scenario-{slug}">{html.escape(title)} <span>{len(caps)}</span></a>')
        for cap in caps:
            desc = descriptors[cap]
            req_path, res_path = desc["schemas"]["request"], desc["schemas"]["response"]
            request = schemas.files[req_path]
            parameter_nodes = schemas.property_nodes(request, req_path, "parameters")
            assert parameter_nodes, f"Missing parameter contract: {cap}"
            parameters, parameter_document = max(parameter_nodes, key=lambda item:
                len(schemas.resolve(*item)[0].get("properties", {})) +
                100 * len(schemas.resolve(*item)[0].get("oneOf", [])))
            example = None
            note = "禁用项：此ID不能执行。"
            key = None
            try:
                example = {"schema_version": "v1", "request_id": UUID, "context": CONTEXT,
                           "parameters": schemas.sample(parameters, parameter_document)}
                if cap in {"journal_entry.create", "journal_entry.lines.replace", "journal_entry.lines.add"}:
                    lines = example["parameters"]["lines"]
                    if len(lines) == 1:
                        lines.append(copy.deepcopy(lines[0]))
                        lines[1]["account_id"] = 2
                    for i, line in enumerate(lines):
                        line.update(debit="100" if i == 0 else "0", credit="100" if i == 1 else "0")
                if cap == "fiscal_position.account_mapping.create":
                    example["parameters"]["destination_account_id"] = 2
                if cap == "stock.transfer.create":
                    example["parameters"]["location_dest_id"] = 2
                registry.validate_instance(req_path, example)
                note = "合成示例仅验证请求Schema；不证明记录存在、权限/配置满足或业务执行成功。"
                if desc["access"] == "write" and desc["handler_key"]:
                    try:
                        key = keys.derive_key(cap, example, "doc-example-operation-001")
                        note = "合成示例通过请求Schema和当前纯写入参数校验；展示键由当前代码计算，无Odoo执行。真实ID和参数变更后必须重算。"
                    except Exception as error:  # noqa: BLE001 - report unavailable synthetic examples honestly
                        note += f" 此最小结构仍可能被业务参数校验拒绝（{type(error).__name__}）；按完整字段表补齐实际请求后用request_key.py离线校验。"
            except Exception as error:  # noqa: BLE001 - schema failure must never produce an unvalidated example
                example = None
                note = f"未提供未经验证的请求示例：{type(error).__name__}。按下方精确字段及原始Schema构造。"
            if not desc["handler_key"]:
                note = "禁用/预留ID，不能调用。若展示请求结构，仅说明占位合同，不表示实现已存在。"
            command = f'odoo-accounting-cli-v4 read {cap} --request "@request.json"' if desc["access"] == "read" else f'odoo-accounting-cli-v4 write run {cap} --request "@request.json" --idempotency-key "{key or "RECOMPUTE_FOR_ACTUAL_REQUEST"}" --confirm "{cap}"'
            rows_req = [row for node, document in parameter_nodes for row in schemas.rows(node, document, "parameters")]
            # Full response includes success/failure alternatives and nullable envelope fields.
            rows_res = schemas.rows(schemas.files[res_path], res_path, "response")
            access = "只读" if desc["access"] == "read" else "写入"
            status = desc["status"]["value"]
            anchor = "cap-"+cap.replace(".", "-")
            item = f'<a id="{anchor}"></a>\n\n'+f"## {cap} — {desc['summary']['zh_CN']}\n\n"
            item += f"- 类型：{access}；静态状态：`{status}`；handler：`{desc['handler_key']}`。\n"
            item += f"- 状态原因：`{desc['status']['reason_code']}` — {desc['status']['reason']}\n"
            item += f"- 内部domain：`{desc['domain']}`；来源模型：{', '.join(desc['source']['models']) or '无'}；向导：{', '.join(desc['source']['wizards']) or '无'}。\n"
            item += f"- 必需模块：{', '.join(desc['requirements']['modules']) or '无'}；配置项：{', '.join(desc['requirements']['configuration']) or '无'}；公司条件：`{desc['requirements']['company']}`。\n"
            item += f"- 权限组：{', '.join(desc['requirements']['groups']) or '未声明'}；ACL：{', '.join(desc['requirements']['acl']) or '未声明'}。\n"
            item += f"- 请求/响应合同：`{req_path}` / `{res_path}`。\n\n"
            item += "### 调用方式\n\n```bash\n"+command+"\n```\n\n> "+note+"\n\n"
            if example is not None:
                item += "```json\n"+json.dumps(example, ensure_ascii=False, indent=2)+"\n```\n\n"
            item += "### 请求参数（公共context与信封见总指南）\n\n"+field_table(rows_req)
            item += "\n### 返回字段（包含成功/失败条件分支）\n\n"+field_table(rows_res)
            item += "\n### 执行、验证、幂等与逆向边界\n\n"
            for strategy, value in desc["strategies"].items():
                item += f"- `{strategy}`：{value}\n"
            item += "\n### 已登记测试与证据范围\n\n"
            for kind, record in desc["tests"].items():
                item += f"- `{kind}`：`{record['status']}`；{record['reason']}；引用：{', '.join(record['references']) or '无'}\n"
            item += "\n登记为implemented不等于本次重新跑过，也不等于全部配置/全部接口真实E2E通过。\n\n"
            chapter += item
            index += f"| [{cap}](cli-v4-manual/scenarios/{slug}.md#{anchor}) | {desc['summary']['zh_CN']} | {access} | {status} |\n"
            search = html.escape(f"{cap} {desc['summary']['zh_CN']} {desc['summary']['en_US']} {title} {access} {status}", quote=True)
            cards.append(f'<details class="capability" id="{anchor}" data-search="{search}"><summary><code>{cap}</code> {html.escape(desc["summary"]["zh_CN"])} <span class="badge">{access} · {status}</span></summary>'+markdown_html(item, anchor)+f'<p>精确原始合同：<a href="#schema-{Path(req_path).stem}">请求Schema</a> · <a href="#schema-{Path(res_path).stem}">响应Schema</a></p></details>')
            cases.append({"id": cap, "scenario": slug, "handler_key": desc["handler_key"],
                          "request_schema": req_path, "response_schema": res_path,
                          "request_rows": len(rows_req), "response_rows": len(rows_res),
                          "has_schema_validated_example": example is not None,
                          "has_normalized_write_key_example": key is not None})
        destination = DOCS / "scenarios" / f"{slug}.md"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(chapter.rstrip() + "\n", encoding="utf-8", newline="\n")
        articles.append(f'<section class="scenario" id="scenario-{slug}"><h2 id="scenario-{slug}-title">{html.escape(title)}</h2><p>{html.escape(group["description"])}</p>'+"".join(cards)+"</section>")
    (ROOT / "docs/reference/CLI_V4_MANUAL.md").write_text(index, encoding="utf-8", newline="\n")
    schema_section = '<section id="request-key"><h2 id="request-key-title">附录：离线幂等键计算示例完整源码</h2><p>仅本0.0.0快照的源码辅助示例，不是新增业务命令；须在当前CLI Python环境运行。将下面代码保存为request_key.py，按快速上手的格式调用。示例只进行合同/纯参数校验和键计算，绝不建立Odoo端口。第三个参数只用于需调用者明确选择的operation key；不能用它覆盖内容绑定的预期键。</p><pre><code>'+html.escape((DOCS/'request_key.py').read_text(encoding='utf-8'))+'</code></pre></section>'
    schema_section += '<section id="schema-appendix"><h2 id="schema-appendix-title">附录：全部精确原始JSON Schema</h2><p>引用均指向本地合同，无需联网；下列文件是本快照的完整原文结构。</p>'
    for path, value in schemas.files.items():
        schema_section += f'<details id="schema-{Path(path).stem}"><summary>{html.escape(path)}</summary><pre><code>'+html.escape(json.dumps(value, ensure_ascii=False, indent=2))+"</code></pre></details>"
    schema_section += "</section>"
    style = (DOCS / "manual_style.css").read_text(encoding="utf-8")
    behavior = (DOCS / "manual_ui.js").read_text(encoding="utf-8")
    page = '<!doctype html><html lang="zh-CN" dir="ltr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CLI V4 命令接口说明书 · 业务场景版</title><style>'+style+'</style></head><body><header><div>ODOO ACCOUNTING CLI V4</div><p>命令与JSON接口说明书 · 2026-10-03 · 559项全量快照</p></header><div class="layout"><nav data-od-id="nav"><h2>按业务场景查找</h2><a href="#quickstart">新会话快速上手</a><label for="search">搜索命令ID / 中文用途</label><input id="search" type="search" placeholder="例如：发票、payment、核销"><div id="search-status" role="status" aria-live="polite">559个接口</div>'+"".join(nav)+'<a href="#schema-appendix">全部原始Schema</a></nav><main data-od-id="article"><section id="quickstart">'+markdown_html(intro+guide)+'</section>'+"".join(articles)+schema_section+'</main><aside class="toc" data-od-id="toc"><h2>阅读提示</h2><p>先读快速上手 → 选业务场景 → 展开精确ID → 填真实请求 → 检查返回。</p><p>写入必须重算幂等键，并显式确认。禁用项不可执行。</p><a href="#quickstart">快速上手</a><a href="#schema-appendix">精确Schema</a><button id="expand-visible" type="button">展开当前匹配接口</button><button id="collapse-all" type="button">收起接口</button><p>本文件可离线独立浏览；无需Pi或网络。</p></aside></div><script>'+behavior+'</script></body></html>'
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(page, encoding="utf-8", newline="\n")
    manifest = {"snapshot_date": "2026-10-03", "source_commit": commit, "registry_canonical_sha256": registry.digest,
                "registry_file_sha256": sha, "counts": counts, "scenarios": len(groups),
                "schema_sha256": {path: digest((ROOT/path).read_bytes()) for path in schemas.files},
                "coverage": cases, "html_sha256": digest(page.encode()), "html_bytes": len(page.encode()),
                "browser_preview": "not_verified_browser_start_blocked_by_environment_policy",
                "guide_sha256": digest(guide.encode()),
                "generator_sha256": digest(Path(__file__).read_bytes()),
                "request_key_example_sha256": digest((DOCS/'request_key.py').read_bytes())}
    (DOCS / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(dump({"success": True, "counts": counts, "scenarios": len(groups), "schemas": len(schemas.files),
                "schema_examples": sum(item["has_schema_validated_example"] for item in cases),
                "write_key_examples": sum(item["has_normalized_write_key_example"] for item in cases),
                "html_bytes": len(page.encode()), "html": str(html_path)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", required=True, type=Path, help="Standalone generated artifact path, outside public Git tree")
    args = parser.parse_args()
    build(args.html.resolve())


if __name__ == "__main__":
    main()
