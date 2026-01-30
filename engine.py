import os
from datetime import datetime
from memory.system import load_canon, save_canon
from memory.schema.character import CharacterCore, Character, CharacterState
from memory.schema.world import World, WorldRule
from memory.schema.meta import CanonMeta
from memory.canon import CanonMemory
from memory.creative import CreativeMemory
from crew.agents import writer, director, checker, curator
from crew.tasks import plan_task, write_task, check_task, memory_task
from crew.crew import build_crew
from crewai import Crew


# 1. 初始化或加载数据
def get_initialized_memory() -> CanonMemory:
    canon = load_canon()
    if not canon:
        print("未发现存档，正在准备空白世界画布...")

        # 1. 创建真空世界设定（所有字段设为空字符串或空列表）
        empty_world = World(
            genre="",  # 留空，触发 UI 引导
            tech_level="",
            magic_system="",
            rules=[],  # 初始规则列表为空
        )

        # 2. 初始角色字典为空
        empty_characters = {}

        # 3. 组装空内存对象
        canon = CanonMemory(
            world=empty_world,
            characters=empty_characters,
            timeline=[],
            meta=CanonMeta(version=1, last_updated_chapter=0, updated_at=datetime.now()),
        )
    return canon


# 2. 根据当前的 canon 状态构建 Crew
def prepare_crew(canon: CanonMemory) -> Crew:
    # 每次生成新章节都要重新构建任务，因为 canon.read() 的内容变了
    d_agent = director()
    w_agent = writer()
    c_agent = checker()
    m_agent = curator()

    plan = plan_task(d_agent)
    write = write_task(w_agent, plan)
    check = check_task(c_agent, write, canon.read())
    memory = memory_task(m_agent, write)

    return build_crew(
        agents=[d_agent, w_agent, c_agent, m_agent], tasks=[plan, write, check, memory]
    )


# def partial_crew(canon: CanonMemory):
#     d_agent = director()
#     w_agent = writer()
#     c_agent = checker()

#     plan = plan_task(d_agent)
#     write = write_task(w_agent, plan)
#     check = check_task(c_agent, write, canon.read())
#     return build_crew(
#         agents=[d_agent, w_agent, c_agent], tasks=[plan, write, check]
#     )


# def memory_crew(chapter_text):
#     text_length = len(chapter_text)
#     m_agent = curator()
#     if text_length < 500:
#         # 篇幅短：调用简单任务，不强求 JSON，避免模型崩溃
#         memo_task = simple_memory_task(m_agent, partial_result.tasks_output[1])
#     else:
#         # 篇幅长：调用标准结构化任务
#         memo_task = complex_memory_task(m_agent, partial_result.tasks_output[1])
        
#     # 4. 第二阶段：运行记忆提取
#     memory_crew = Crew(agents=[memory_agent], tasks=[memo_task])
#     memo_result = memory_crew.kickoff()
