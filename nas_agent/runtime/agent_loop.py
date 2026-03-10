import json
from typing import Any

import ollama

from config.settings import MODEL_NAME
from tools.registry import ToolRegistry


DEBUG_AGENT = True


def _debug(msg: str):
    if DEBUG_AGENT:
        print(f"[agent] {msg}")


def _safe_get_tools(registry: ToolRegistry):
    if hasattr(registry, "list_tools"):
        return registry.list_tools()

    if hasattr(registry, "tools"):
        tools_obj = registry.tools
        if isinstance(tools_obj, dict):
            return list(tools_obj.values())
        if isinstance(tools_obj, list):
            return tools_obj

    return []


def _has_tool(registry: ToolRegistry, tool_name: str) -> bool:
    for tool in _safe_get_tools(registry):
        if getattr(tool, "name", "") == tool_name:
            return True
    return False


def _find_first_tool_by_keywords(registry: ToolRegistry, keywords: list[str]) -> str:
    tools = _safe_get_tools(registry)
    for tool in tools:
        text = " ".join([
            str(getattr(tool, "name", "")),
            str(getattr(tool, "description", "")),
            " ".join(getattr(tool, "keywords", []) or []),
            str(getattr(tool, "command", "")),
        ]).lower()

        if all(k.lower() in text for k in keywords):
            return getattr(tool, "name", "")
    return ""


def _route_by_rules(user_input: str, registry: ToolRegistry) -> dict | None:
    """
    先做轻量规则路由，尽量给小模型减负。
    """
    text = (user_input or "").strip().lower()

    system_hits = [
        "系统信息", "系统状态", "查看系统", "看看系统",
        "cpu", "内存", "磁盘", "硬盘", "显卡", "负载", "资源占用"
    ]

    search_hits = [
        "搜索", "新闻", "最新", "实时", "联网", "最近情况", "局势", "帮我搜", "查新闻"
    ]

    if any(k in text for k in system_hits):
        for candidate in ["system_status", "system_info", "status", "sys_status"]:
            if _has_tool(registry, candidate):
                return {
                    "action": "tool",
                    "tool_name": candidate,
                    "query": user_input.strip()
                }

        maybe = _find_first_tool_by_keywords(registry, ["系统"])
        if maybe:
            return {
                "action": "tool",
                "tool_name": maybe,
                "query": user_input.strip()
            }

    if any(k in text for k in search_hits):
        if _has_tool(registry, "baidu_web_search"):
            return {
                "action": "tool",
                "tool_name": "baidu_web_search",
                "query": user_input.strip()
            }

    if ("查一下" in text or "搜一下" in text or "帮我搜索" in text) and _has_tool(registry, "baidu_web_search"):
        return {
            "action": "tool",
            "tool_name": "baidu_web_search",
            "query": user_input.strip()
        }

    return None


def _extract_model_text(resp) -> str:
    if not resp:
        return ""

    message = resp.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

        thinking = message.get("thinking")
        if isinstance(thinking, str) and thinking.strip():
            return thinking.strip()

    content = resp.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()

    response = resp.get("response")
    if isinstance(response, str) and response.strip():
        return response.strip()

    return ""


def _call_model_chat(messages: list[dict], temperature: float = 0.2, num_predict: int = 128) -> str:
    try:
        resp = ollama.chat(
            model=MODEL_NAME,
            messages=messages,
            stream=False,
            options={
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": num_predict,
            }
        )
        text = _extract_model_text(resp)
        _debug(f"chat 返回长度: {len(text)}")
        return text
    except Exception as e:
        _debug(f"chat 调用异常: {e}")
        return ""


def _call_model_generate(prompt: str, temperature: float = 0.2, num_predict: int = 256) -> str:
    try:
        resp = ollama.generate(
            model=MODEL_NAME,
            prompt=prompt,
            stream=False,
            options={
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": num_predict,
            }
        )
        text = _extract_model_text(resp)
        _debug(f"generate 返回长度: {len(text)}")
        return text
    except Exception as e:
        _debug(f"generate 调用异常: {e}")
        return ""


def _build_small_planner_prompt(user_input: str, registry: ToolRegistry) -> str:
    """
    给小模型的规划任务要极短、极明确。
    输出格式也尽量短。
    """
    tool_names = [getattr(t, "name", "") for t in _safe_get_tools(registry)]
    tool_text = ", ".join([x for x in tool_names if x])

    return f"""你是NAS智能管家。
可用工具：{tool_text}

任务：判断用户是否需要调用工具。

只允许输出以下两种格式之一：
1. TOOL|工具名|查询内容
2. FINAL|直接回答

规则：
- 搜索新闻、最新动态、联网查询 -> 优先 baidu_web_search
- 查看系统状态、系统信息 -> 优先 system_status
- 输出必须只有一行
- 不要解释

用户：{user_input}
"""


def _parse_small_plan(text: str) -> dict[str, str] | None:
    text = (text or "").strip()
    if not text:
        return None

    if text.startswith("TOOL|"):
        parts = text.split("|", 2)
        if len(parts) == 3:
            return {
                "action": "tool",
                "tool_name": parts[1].strip(),
                "query": parts[2].strip()
            }

    if text.startswith("FINAL|"):
        parts = text.split("|", 1)
        if len(parts) == 2:
            return {
                "action": "final",
                "answer": parts[1].strip()
            }

    return None


def _fallback_plain_reply(user_input: str) -> str:
    prompt = f"""你是本地NAS智能管家。
请直接用自然中文简洁回答下面的问题，不要用表格，不要太长。

问题：
{user_input}
"""
    return _call_model_generate(prompt, temperature=0.3, num_predict=160).strip()


def _compress_tool_result(tool_name: str, tool_result: Any) -> str:
    """
    关键优化：
    不把整份 raw JSON 喂给小模型，只喂压缩后的结果。
    """
    if isinstance(tool_result, dict):
        if tool_name == "baidu_web_search":
            query = str(tool_result.get("query", "")).strip()
            refs = tool_result.get("references") or []
            lines = [f"查询：{query}"]

            for i, ref in enumerate(refs[:5], 1):
                title = str(ref.get("title", "")).strip()
                website = str(ref.get("website", "")).strip()
                date = str(ref.get("date", "")).strip()
                snippet = str(ref.get("snippet") or ref.get("content") or "").replace("\n", " ").replace("\r", " ").strip()
                if len(snippet) > 120:
                    snippet = snippet[:120] + "..."

                lines.append(f"{i}. 标题：{title}")
                if website:
                    lines.append(f"   来源：{website}")
                if date:
                    lines.append(f"   时间：{date}")
                if snippet:
                    lines.append(f"   摘要：{snippet}")

            return "\n".join(lines)

        if tool_name in {"system_status", "system_info", "status", "sys_status"}:
            data = tool_result.get("data", {}) or {}
            cpu = data.get("cpu", {}) or {}
            memory = data.get("memory", {}) or {}
            disk = data.get("disk", {}) or {}
            gpu = data.get("gpu", {}) or {}

            lines = [
                f"主机名：{data.get('hostname', '未知')}",
                f"系统：{data.get('system', '未知')} {data.get('release', '')} {data.get('version', '')}".strip(),
                f"CPU占用：{cpu.get('usage_percent', 'N/A')}%",
                f"CPU核心：物理{cpu.get('physical_cores', 'N/A')} / 逻辑{cpu.get('logical_cores', 'N/A')}",
                f"内存：已用 {memory.get('used', 'N/A')} / 总计 {memory.get('total', 'N/A')}（{memory.get('usage_percent', 'N/A')}%）",
            ]

            partitions = disk.get("partitions", []) or []
            for part in partitions[:4]:
                lines.append(
                    f"磁盘 {part.get('mountpoint', '')}：已用 {part.get('used', 'N/A')} / {part.get('total', 'N/A')}（{part.get('usage_percent', 'N/A')}%）"
                )

            if gpu.get("detected"):
                gpus = gpu.get("gpus", []) or []
                if gpus:
                    g = gpus[0]
                    lines.append(
                        f"显卡：{g.get('name', '未知')}，温度 {g.get('temperature_c', 'N/A')}°C，占用 {g.get('utilization_gpu_percent', 'N/A')}%，显存 {g.get('memory_used_mb', 'N/A')} / {g.get('memory_total_mb', 'N/A')} MB"
                    )

            return "\n".join(lines)

        answer = str(tool_result.get("answer", "")).strip()
        if answer:
            return answer

    return str(tool_result)


def _build_summary_prompt(user_input: str, tool_name: str, compact_result: str) -> str:
    """
    给小模型的总结提示要短，而且给固定模板。
    """
    return f"""你是本地NAS智能管家。
请根据下面资料，生成自然、简洁、易读的中文总结。

要求：
1. 第一段先直接说整体情况
2. 再写2到4个重点
3. 不要用表格
4. 不要客服腔
5. 不要编造
6. 最后如果有来源信息，就简单保留“参考来源”

用户问题：
{user_input}

工具：
{tool_name}

资料：
{compact_result}
"""


def _tool_result_to_brief_text(tool_result: Any) -> str:
    if isinstance(tool_result, dict):
        answer = str(tool_result.get("answer", "")).strip()
        if answer:
            return answer

        refs = tool_result.get("references") or []
        if refs:
            lines = ["我查到的几个主要来源："]
            for i, ref in enumerate(refs[:5], 1):
                title = ref.get("title", "无标题")
                url = ref.get("url", "")
                lines.append(f"{i}. {title} {url}")
            return "\n".join(lines)

    return str(tool_result)


def run_agent_with_tools(user_input: str, registry: ToolRegistry, history: list[dict]) -> str:
    # 1. 规则优先
    routed = _route_by_rules(user_input, registry)
    if routed:
        _debug(f"规则路由命中: {routed}")
        decision = routed
    else:
        # 2. 小模型只做极简一行规划
        planner_prompt = _build_small_planner_prompt(user_input, registry)
        planner_text = _call_model_generate(planner_prompt, temperature=0.1, num_predict=48)
        _debug(f"规划输出: {planner_text[:200] if planner_text else '<EMPTY>'}")

        plan = _parse_small_plan(planner_text)

        if plan is None:
            _debug("规划失败，退回普通回答")
            fallback = _fallback_plain_reply(user_input)
            return fallback or "本地模型没有返回内容。"

        decision = plan

    action = str(decision.get("action", "")).strip()
    _debug(f"action = {action}")

    if action == "final":
        answer = str(decision.get("answer", "")).strip()
        if answer:
            return answer

        fallback = _fallback_plain_reply(user_input)
        return fallback or "本地模型没有返回内容。"

    if action == "tool":
        tool_name = str(decision.get("tool_name", "")).strip()
        query = str(decision.get("query", "")).strip() or user_input.strip()

        if not _has_tool(registry, tool_name):
            return f"模型请求了不存在的工具：{tool_name}"

        _debug(f"准备调用工具: {tool_name}, query={query}")

        try:
            tool_result = registry.run(tool_name, query)
        except TypeError:
            tool_result = registry.run(tool_name)
        except Exception as e:
            return f"工具调用失败：{e}"

        compact_result = _compress_tool_result(tool_name, tool_result)
        summary_prompt = _build_summary_prompt(user_input, tool_name, compact_result)

        final_answer = _call_model_generate(summary_prompt, temperature=0.3, num_predict=320).strip()
        _debug(f"最终总结输出: {final_answer[:200] if final_answer else '<EMPTY>'}")

        if final_answer:
            return final_answer

        _debug("最终总结为空，直接返回工具结果摘要")
        return _tool_result_to_brief_text(tool_result)

    fallback = _fallback_plain_reply(user_input)
    return fallback or "模型返回了无法识别的 action。"