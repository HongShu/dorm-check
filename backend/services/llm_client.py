"""
Claude API 封装（F-10 LLM 调用失败兜底）

- 超时 10 秒兜底
- 调用失败时抛出异常，由路由层捕获并返回原始结构化数据
"""

import anthropic
from config import settings


PROMPT_TEMPLATE = """你是宿舍查寝管理系统的助手。以下是 {date} 全部楼栋查寝完成后的异常情况：

【应在校但不在寝（疑似失联，需立即核实）】
{missing_section}

【系统显示离校但实际在寝（已返校未报备，需更新状态）】
{return_section}

请生成一段简报给宿管科长，要求：
1. 先讲失联风险类，按辅导员归类，方便联系
2. 再讲已返校待更新类
3. 总字数控制在 300 字以内
4. 直接输出文本，不要 markdown 标题或列表符号
5. 语气专业简洁，像一个工作汇报"""


def build_prompt(date: str, missing: list[str], unreported: list[str]) -> str:
    missing_section = "\n".join(missing) if missing else "无"
    return_section = "\n".join(unreported) if unreported else "无"
    return PROMPT_TEMPLATE.format(
        date=date,
        missing_section=missing_section,
        return_section=return_section,
    )


def generate_report(date: str, missing: list[str], unreported: list[str]) -> str:
    """
    调用 Claude Haiku 生成简报，超时则抛出异常（由路由层兜底）。
    """
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY 未配置")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    prompt = build_prompt(date, missing, unreported)

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=600,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
        timeout=10,
    )
    return response.content[0].text
