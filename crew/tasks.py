# crew/tasks.py
# from crewai import Task
from typing import List
from pydantic import BaseModel
from crewai import Task, Agent

# from crewai.agents.agent import Agent


def plan_task(agent: Agent) -> Task:
    return Task(
        description="""
你现在是【导演 Agent】。正在规划第 {chapter_num} 章。
{context_instruction}

### 2. 任务背景(Canon):
{canon_context}

### 3. 本章大纲规划：
请基于背景，制定本章的叙事节奏。
""",
        expected_output="""
返回结构化的章节计划：
- **上章收尾方案**：简述如何处理上章末尾的遗留冲突。
- **时间/空间转场**：明确交代本章从何时、何地开始。
- **核心情节拆解**：分段描述本章的 Plot Beats。
- **角色调度**：记录涉及角色及其出现在场景中的逻辑理由（登场动机）。
- **呼应伏笔**：本章将利用哪些已有的道具或线索？
""",
        agent=agent,
    )


def write_task(agent: Agent, plan_task_instance: Task) -> Task:
    return Task(
        description="""
你现在是顶级【网络小说作家 Agent】。

### 💡 创作风格要求：
- 本次重写请特别【{style_preset}】。
- 禁止复读之前的措辞，请重新组织语言，在保持逻辑一致的前提下提供新鲜的阅读感。

### 🏷️ 核心要求：
1. **章节标题**：请为本章起一个引人入胜的标题。
   - 格式要求：第一行必须是“第{chapter_num}章：[章节名称]”，然后换行开始正文。
2. **纯文本创作（硬性指标）**：
   - **禁止出现任何 Markdown 符号**：严禁使用 **粗体**、## 标题、*斜体*、- 列表或 > 引用。
   - 仅允许使用中文字符、标点符号和段落换行。
   - 这是一个“非格式化”任务，请像在记事本里写作一样输出。

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
""",
        agent=agent,
        context=[plan_task_instance],
        max_retries=3,
    )


def check_task(agent: Agent, write_task_instance: Task, canon: dict) -> Task:
    # 瘦身：只取最关键的 3 条规则和最近 2 条时间线
    minimal_canon = {
        "rules": canon["world"]["rules"][:3],
        "recent_events": canon["timeline"][-2:],
    }

    return Task(
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
