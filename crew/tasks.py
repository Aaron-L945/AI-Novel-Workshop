# crew/tasks.py
# from crewai import Task
from typing import List
from pydantic import BaseModel
from crewai import Task, Agent

# from crewai.agents.agent import Agent


def plan_task(agent: Agent) -> Task:
    return Task(
        name="PlanTask",
        description="""
你现在是【导演 Agent】。正在规划第 {chapter_num} 章。
{context_instruction}

### 2. 任务背景(Canon):
{canon_context}

### 3. 本章大纲规划：
请基于背景，制定本章的叙事节奏。
【重要】：为了支撑用户设定的字数要求（{target_word_count}字），你必须将本章拆解为 **4-6 个具体的关键情节节点 (Plot Beats)**。
每个节点必须包含：
- **场景地点**：具体发生在哪里？
- **核心动作**：发生了什么具体的事件或对话？
- **情感/冲突升级**：角色的情绪如何变化？
- **预计字数分配**：预估该部分需要的篇幅。
""",
        expected_output="""
返回结构化的章节计划：
- **上章收尾方案**：简述如何处理上章末尾的遗留冲突。
- **时间/空间转场**：明确交代本章从何时、何地开始。
- **核心情节拆解 (4-6个节点)**：详细描述每个 Plot Beat，确保内容足够支撑用户设定的字数要求。
- **角色调度**：记录涉及角色及其出现在场景中的逻辑理由（登场动机）。
- **呼应伏笔**：本章将利用哪些已有的道具或线索？
""",
        agent=agent,
    )


def write_task(agent: Agent, plan_task_instance: Task) -> Task:
    return Task(
        name="WriteTask",
        description="""
你现在是顶级【网络小说作家 Agent】。

### 💡 创作风格要求：
{context_instruction}

### 🏷️ 核心要求：
1. **章节标题**：请为本章起一个引人入胜的标题。
   - 格式要求：第一行必须是“第{chapter_num}章：[章节名称]”，然后换行开始正文。
2. **纯文本创作（硬性指标）**：
   - **禁止出现任何 Markdown 符号**：严禁使用 **粗体**、## 标题、*斜体*、- 列表或 > 引用。
   - 仅允许使用中文字符、标点符号和段落换行。
   - 这是一个“非格式化”任务，请像在记事本里写作一样输出。
3. **字数控制技巧**：
   - 如果目标字数较多：请通过环境描写（光线、气味）、心理活动（焦虑、回忆）、动作分解（微动作）来充实内容。
   - 如果目标字数较少：请加快叙事节奏，减少不必要的铺垫，直奔核心冲突。

### 🚀 补救任务：
专家评审反馈：{feedback}
*任务：必须在前 10% 篇幅内补全剧情真空期，实现丝滑衔接。*

### 创作准则：
- **世界观对齐**：参考以下设定，禁止“吃书”：
  {canon_context}
- **细节呼应**：检查记忆库中的道具、伤势或角色动态，确保逻辑连贯。
""",
        expected_output="""
一份完全去除 Markdown 标记的纯文本章节。
1. 第一行是章节标题（格式：第X章：名称）。
2. 全文没有任何星号、井号或特殊格式符。
3. 段落分明，叙事流畅，逻辑闭环。
4. **严格遵守字数要求**。
""",
        agent=agent,
        context=[plan_task_instance],
        max_retries=3,
    )


def polish_task(agent: Agent, write_task_instance: Task) -> Task:
    return Task(
        name="PolishTask",
        description="""
你现在是【文学润色师 Agent】。

### 核心任务：
请阅读 Context 中的小说初稿，应用《AI 写作特征去除指南》进行深度重写。
你的目标是**消除所有 AI 生成的痕迹**，注入真实的人性与灵魂，使文字读起来像是由一位有观点、有情绪的人类作家写出的。

### 🚫 必须消除的 AI 模式（见到必删）：
1. **过度强调意义**：删除所有“标志着……的关键时刻”、“不仅……而且……”、“作为……的证明”等宏大叙事。
2. **机械连接词**：严禁使用“此外”、“然而”、“值得注意的是”、“总之”、“综上所述”。
3. **肤浅的分析**：删除句末的“-ing”式总结（如“……凸显了……”、“……象征着……”）。
4. **宣传式语言**：删除“令人叹为观止的”、“充满活力的”、“无缝的”等空洞形容词。
5. **公式化结构**：打破“三段式”列举，打破“虽然……但是……”的二元对比。
6. **AI 词汇黑名单**：严禁出现【织锦、交响曲、挂毯、见证、基石、催化剂、领域、格局、至关重要、深入探讨】。

### ✨ 注入灵魂指南：
1. **要有观点**：不要中立报道。通过角色的感官和心理，对事件做出主观反应（“这让人不安”、“我不知道该怎么看”）。
2. **变化节奏**：使用短促有力的句子。混合长短句。不要让每个段落长度都一样。
3. **具体细节**：用“凌晨三点的机器轰鸣声”代替“令人担忧的噪音”。信任读者，直接陈述事实，不要解释隐喻。
4. **允许不完美**：真实的对话和心理活动是混乱的、跳跃的，不要写得像教科书一样逻辑完美。
5. **系动词回归**：多用简单的“是”、“有”，少用“作为”、“充当”、“设有”。

### 格式要求：
- 保持原有的章节标题格式（第X章：名称）。
- 直接输出润色后的正文，不要包含任何“润色说明”、“改写前/改写后”对比或总结。
- 使用标准的中文标点符号和段落格式。
""",
        expected_output="""
一份经过深度润色、去AI味的小说正文。
1. 第一行是章节标题。
2. 内容流畅自然，文笔优美。
3. 没有任何多余的解释性文字。
""",
        agent=agent,
        context=[write_task_instance],
        max_retries=3,
    )


def check_task(agent: Agent, write_task_instance: Task, canon: dict) -> Task:
    # 瘦身：只取最关键的 3 条规则和最近 2 条时间线
    minimal_canon = {
        "rules": canon["world"]["rules"][:3],
        "recent_events": canon["timeline"][-2:],
    }

    return Task(
        name="CheckTask",
        description=f"""
你现在是【首席逻辑官】。请审计 Context 中的正文是否存在以下断裂：
1. **转场**：开头是否有时间交代（如“三日后”）？
2. **动机**：角色登场（如赵明轩）是否合理？
3. **立场**: 针对本章出现的【所有角色】，对比其性格标签（Personality）和历史立场。
4. **冲突**: 检查正文是否违反了世界观中的核心规则（如：原本灵气枯竭的人突然发大招）

核心约束：{minimal_canon}
""",
        expected_output="发现的问题列表。若无问题，返回‘未发现逻辑冲突’。",
        agent=agent,
        context=[write_task_instance],  # 这里的正文已经很长了， description 必须短
        max_retries=3,
    )


def memory_task(agent: Agent, write_task_instance: Task):
    return Task(
        name="MemoryTask",
        description="""
        你现在是【首席速记员】。请仔细阅读 Context 中的小说正文，提取关键信息。
        请严格按照以下格式输出，不要包含任何 Markdown 代码块或多余解释：

        [SUMMARY]
        一句话总结本章剧情核心。
        [/SUMMARY]

        [CHARS]
        本章实际出场或产生的角色姓名，用逗号隔开。
        [/CHARS]

        [LOCS]
        本章发生的具体小地名。
        [/LOCS]

        [ITEMS]
        本章新出现的关键道具、功法名词或重要的伏笔。
        [/ITEMS]

        [CHAR_UPDATE]
        角色名：当前的心境或关键动作（例如：叶辰：重伤苏醒，心境愈发冷冽）。
        [/CHAR_UPDATE]

        [PLOT_CHAIN]
        起因 -> 经过 -> 结果（例如：雾锁林遇袭 -> 药力耗尽 -> 险些被影杀门俘虏）。
        [/PLOT_CHAIN]
        """,
        expected_output="包含 [SUMMARY], [CHARS], [LOCS], [ITEMS], [CHAR_UPDATE], [PLOT_CHAIN]标签的结构化文本。",
        agent=agent,
        context=[write_task_instance],
        max_retries=5,
    )
