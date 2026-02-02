import json
import re


def safe_parse_json(raw_output):
    """
    极强鲁棒性的 JSON 解析工具
    支持：Pydantic对象、纯JSON字符串、带Markdown代码块的字符串、带废话的字符串
    """
    # 1. 如果已经是字典或对象，直接处理
    if isinstance(raw_output, dict):
        return raw_output
    if hasattr(raw_output, "model_dump"):
        return raw_output.model_dump()

    # 2. 如果是字符串，开始强力解析
    if isinstance(raw_output, str):
        # 尝试直接解析
        try:
            return json.loads(raw_output)
        except:
            pass

        # 尝试正则提取 {} 之间的内容 (核心逻辑)
        try:
            match = re.search(r"(\{.*\})", raw_output, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except:
            pass

    # 3. 兜底返回空结构，防止程序崩溃
    return {
        "summary": "解析摘要失败",
        "involved_characters": [],
        "locations": [],
        "new_items": [],
        "plot_points": [],
    }


def parse_tagged_memory(raw_text: str, canon_data: dict = None):
    """
    针对当前 JSON 结构设计的解析器。
    如果没有提取到角色，将尝试从 canon_data 的 characters 列表中获取第一个。
    """
    # --- 1. 动态获取兜底角色 ---
    default_actor = "未知角色"
    if canon_data and "characters" in canon_data:
        existing_chars = list(canon_data["characters"].keys())
        if existing_chars:
            default_actor = existing_chars[0]  # 动态获取，比如 "叶辰"

    # 初始化返回结构
    data = {
        "summary": "暂无摘要",
        "involved_characters": [default_actor],
        "locations": "未知地点",
        "items": "无",
        "char_update": "",
        "plot_chain": "",
    }

    if not raw_text:
        return data

    # --- 2. 标签提取 ---
    patterns = {
        "summary": r"\[SUMMARY\](.*?)\[/SUMMARY\]",
        "chars": r"\[CHARS\](.*?)\[/CHARS\]",
        "locs": r"\[LOCS\](.*?)\[/LOCS\]",
        "items": r"\[ITEMS\](.*?)\[/ITEMS\]",
        "char_update": r"\[CHAR_UPDATE\](.*?)\[/CHAR_UPDATE\]",
        "plot_chain": r"\[PLOT_CHAIN\](.*?)\[/PLOT_CHAIN\]",
    }

    results = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, raw_text, re.DOTALL | re.IGNORECASE)
        results[key] = match.group(1).strip() if match else ""

    # --- 3. 数据填充与逻辑合并 ---
    data["summary"] = results.get("summary") or "暂无摘要"
    data["locations"] = results.get("locs") or "未知地点"
    data["items"] = results.get("items") or "无"

    # 填充更新与链条
    data["char_update"] = results.get("char_update") or f"角色动态：{data['summary']}"
    data["plot_chain"] = results.get("plot_chain") or f"因果逻辑：{data['summary']}"

    # 处理涉及角色
    char_str = results.get("chars")
    if char_str:
        # 统一处理中文/英文逗号
        data["involved_characters"] = [
            n.strip() for n in char_str.replace("，", ",").split(",") if n.strip()
        ]
    else:
        # 标签缺失时，使用从 JSON 里读出来的 default_actor
        data["involved_characters"] = [default_actor]

    return data
