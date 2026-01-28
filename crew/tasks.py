# crew/tasks.py
# from crewai import Task

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
### 提取任务：
1. **时空**：主角目前身处哪个具体小地名？（如：林家后山、破庙内）
2. **角色**：本章除了主角，还出现了谁？（必须提取出姓名，如：赵明轩）
3. **关键事件**：本章发生了什么推动剧情的事？（用一句话概括，严禁写“无”）
4. **新设定**：文中是否提到了新的道具、功法或地名？

### ⚠️ 警告：
严禁输出“未明确”、“无变化”等空洞回复。如果文中提到了，必须抓取出来！
""",
        expected_output="""
必须包含以下格式：
### 📍 时空坐标
- [具体地点] | [时间交代]
### 👥 角色更新
- [角色姓名]：[当前状态/位置]
### ⚡ 剧情链条
1. [事件A] -> [影响]
### 🔍 伏笔与名词
- 名词：[新出现的专业术语]
""",
        agent=agent,
        context=[write_task_instance],
        max_retries=3,
    )
