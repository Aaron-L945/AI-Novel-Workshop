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



def parse_tagged_memory(raw_text: str):
    """
    升级版：提取所有细分维度，不再只靠 SUMMARY 填充
    """
    data = {
        "summary": "暂无摘要",
        "involved_characters": ["叶辰"],
        "locations": "未知地点",
        "items": "无",
        "char_update": "", # 新增：专门存角色动态
        "plot_chain": ""   # 新增：专门存剧情演化
    }
    
    if not raw_text:
        return data

    # 1. 定义更丰富的提取规则
    patterns = {
        "summary": r"\[SUMMARY\](.*?)\[/SUMMARY\]",
        "chars": r"\[CHARS\](.*?)\[/CHARS\]",
        "locs": r"\[LOCS\](.*?)\[/LOCS\]",
        "items": r"\[ITEMS\](.*?)\[/ITEMS\]",
        "char_update": r"\[CHAR_UPDATE\](.*?)\[/CHAR_UPDATE\]", # 匹配新标签
        "plot_chain": r"\[PLOT_CHAIN\](.*?)\[/PLOT_CHAIN\]"     # 匹配新标签
    }

    results = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, raw_text, re.DOTALL | re.IGNORECASE)
        results[key] = match.group(1).strip() if match else ""

    # 2. 填充数据
    data["summary"] = results.get("summary") or "暂无摘要"
    data["locations"] = results.get("locs") or "未知地点"
    data["items"] = results.get("items") or "无"
    
    # 3. 核心改进：优先使用专用标签，没有再用 summary 兜底
    data["char_update"] = results.get("char_update") or f"角色状态更新：{data['summary']}"
    data["plot_chain"] = results.get("plot_chain") or f"剧情演进：{data['summary']}"
    
    # 角色列表处理
    char_str = results.get("chars") or "叶辰"
    data["involved_characters"] = [n.strip() for n in char_str.replace("，", ",").split(",") if n.strip()]
    
    return data
