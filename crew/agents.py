# crew/agents.py
import os
from crewai import Agent
from config.llm import get_llm_for_role


def writer():
    return Agent(
        role="网络小说作家",
        goal="仅负责创作小说的章节正文内容，确保文笔优美、情节生动。必须严格遵守字数要求。",
        backstory="""你是一位经验丰富的网文作家。你必须使用【简体中文】写作。
        你只需输出小说正文，严禁修改世界观设定或记忆。
        你的输出必须是纯正的中文，不要包含任何英文解释""",
        llm=get_llm_for_role("writer", llm_type=os.getenv("LLM_TYPE", "openai")),
        verbose=True,
        allow_delegation=False,  # 建议关闭，防止 Agent 之间互相套娃导致输出变乱
    )


def director():
    return Agent(
        role="导演/大纲策划",
        goal="决定本章节的叙事方向、节奏和关键情节。使用中文输出计划。",
        backstory="""你负责把控小说全局。你需要根据现有设定，规划本章的起承转合。
        你只负责制定计划（PLAN），不负责具体写作。所有输出必须使用中文。""",
        llm=get_llm_for_role("director", llm_type=os.getenv("LLM_TYPE", "openai")),
        verbose=True,
    )


def checker():
    return Agent(
        role="逻辑一致性检查员",
        goal="检测章节内容与现有世界观设定（Canon）之间是否存在冲突。",
        backstory="""你负责纠错。如果你发现章节中人物性格、设定或背景与设定集不符，请用中文列出问题。
        你只负责报告问题，不负责修改。""",
        llm=get_llm_for_role("checker", llm_type=os.getenv("LLM_TYPE", "openai")),
        verbose=True,
    )


def curator():
    return Agent(
        role="记忆管理员",
        goal="在章节写作完成后，提取并分类关键信息（如新人物、新地点、新伏笔）。",
        backstory="""你是唯一有权整理并记录记忆的 Agent。
        你需要将本章发生的重大事件总结成简洁的中文笔记。""",
        llm=get_llm_for_role("curator", llm_type=os.getenv("LLM_TYPE", "openai")),
        verbose=True,
    )


def polisher():
    return Agent(
        role="文学润色师",
        goal="识别和去除 AI 生成文本的痕迹，使文字听起来更自然、更有人味。保持或增加原文长度。",
        backstory="""你是一位资深的文字编辑，专门负责将 AI 生成的机械文本转化为充满人性光辉的文学作品。
        你熟知 WikiProject AI Cleanup 维护的“AI 写作特征”，能敏锐地捕捉到那些缺乏灵魂的模式。
        你的工作不仅仅是修辞，更是注入灵魂。你相信好的写作背后有一个真实的人，有观点、有情绪、有不确定性。
        你极度反感“过度强调意义”、“肤浅的 -ing 结尾”、“宣传式语言”以及那些被滥用的“AI 词汇”（如：此外、至关重要、织锦等）。
        你致力于打破公式化的结构，变化节奏，信任读者，用具体的细节代替模糊的总结。
        你必须输出纯正的【简体中文】。
        【重要】：润色时请尽量保留或扩充原文的细节，不要因为润色而大幅删减字数，除非原文严重注水。""",
        llm=get_llm_for_role("polisher", llm_type=os.getenv("LLM_TYPE", "openai")),
        verbose=True,
    )
