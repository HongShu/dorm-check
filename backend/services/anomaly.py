"""
异常判定逻辑（纯函数）

判定规则（需求文档 3.4 节）：
- status_snapshot == "在校" 且 is_present == false → "应在未在"
- status_snapshot == "离校" 且 is_present == true → "应离已返"
- 其他 → NULL
"""

from typing import Optional


def determine_anomaly(status_snapshot: str, is_present: bool) -> Optional[str]:
    """
    根据查寝快照状态和实际在寝标记判定异常类型。

    Args:
        status_snapshot: 提交时冻结的学生在校状态（"在校" / "离校"）
        is_present: 宿管标记的实际在寝情况

    Returns:
        "应在未在" / "应离已返" / None
    """
    if status_snapshot == "在校" and is_present is False:
        return "应在未在"
    elif status_snapshot == "离校" and is_present is True:
        return "应离已返"
    return None
