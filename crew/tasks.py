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

### 🚀 补救任务（最高优先级）：
专家评审指出当前存在以下问题：
{feedback}
*任务：你必须在本章前 10% 的篇幅内，通过倒叙、回忆或直接描写，补全上一章结尾到本章开头之间的“剧情真空期”。*

### 创作目标：
1. **章节序号**：第 {chapter_num} 章。
2. **大纲执行**：严格执行 Context 中的计划，尤其是其中的【上章收尾方案】。
3. **世界观对齐**：参考以下设定，禁止“吃书”：
   {canon_context}

### 创作准则：
- **丝滑过渡**：章节开头禁止直接瞬移。必须有环境渲染或角色内心独白来衔接上一章的紧张感。
- **动机闭环**：新角色（如赵明轩）登场必须在前文有侧面描写或本章有因果交代。
- **细节呼应**：检查记忆库中的道具（如玉佩、伤势），在本章中必须有所体现。
""",
        expected_output="""
小说正文 Markdown。
要求：
1. **过渡补完**：成功修复了“紧急冲突未收尾”的问题，让读者感到因果连续。
2. **逻辑密度**：每一个角色的立场转变都有心理支撑。
3. **篇幅完整**：确保从冲突结算到本章高潮，最后到余韵收尾，逻辑闭环。
""",
        agent=agent,
        context=[plan_task_instance],
        # 建议针对作家角色设置较高的 retry，因为 30B 容易在长文生成时断线
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


def memory_task(agent: Agent, write_task_instance: Task) -> Task:
    return Task(
        description="""
你现在是【档案记录官】。请审阅《Context》中的正文，挖掘本章节产生的**所有实质性变化**。

### 核心挖掘目标：
1. **时空定位**：本章故事发生的具体地点是什么？时间流逝了多久？（必须根据原文给出模糊或精确的时间，如“深夜”、“三日后”）。
2. **角色动态**：本章出现了哪些角色？他们现在的身体状况（如：经脉受损）、心理状态（如：由恨生怜）以及出现的直接原因。
3. **关键转折**：发生了哪几件不可逆转的事？（如：某人吐血、某人决定逃跑）。
4. **情报收集**：文中提到的新功法、新地名、或未解释的怪异细节。

### 📝 记录原则：
- **拒绝留空**：严禁回答“无”。即便情节平淡，也要记录角色当下的“静止状态”作为存档。
- **忠于原文**：不脑补，但要捕捉字里行间的细节。
- **即时输出**：跳出深度思考，直接将提取到的事实列在下方。
""",
        expected_output="""
请按以下结构输出（中文）：

### 📍 时空坐标
- [位置] | [时间节点]

### 👥 角色更新
- **姓名**：[状态/伤势] | [立场/心态变化] | [行动动机]

### ⚡ 剧情链条
1. [事件A] -> 导致 [结果B]
2. [事件C] -> 产生 [后果D]

### 🔍 伏笔与名词
- 名词：...
- 伏笔：...
""",
        agent=agent,
        context=[write_task_instance],
        max_retries=3,
    )
