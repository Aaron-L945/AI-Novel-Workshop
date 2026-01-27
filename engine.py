from dotenv import load_dotenv

load_dotenv()
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
        print("未发现存档，正在初始化全新世界...")
        # 1. 创建世界设定
        initial_world = World(
            genre="东方玄幻",
            tech_level="古代",
            magic_system="境界制：炼气、筑基、金丹",
            rules=[
                WorldRule(
                    name="灵气分布",
                    description="灵气主要集中在名山大川",
                ),
                WorldRule(
                    name="越阶限制",
                    description="跨大境界杀敌极其困难",
                ),
            ],
        )

        # 2. 创建初始角色
        hero = Character(
            core=CharacterCore(
                name="叶辰",
                gender="男",
                personality=["坚韧", "低调", "果断"],
                values=["有恩必报", "追求长生"],
                fears=["家族被灭的悲剧重演"],
            ),
            state=CharacterState(
                location="青云镇", physical_status=["经脉破损"], mental_status=["冷静"]
            ),
            first_appearance_chapter=0,
        )

        canon = CanonMemory(
            world=initial_world,
            characters={"叶辰": hero},
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
    memory = memory_task(m_agent, check)

    return build_crew(
        agents=[d_agent, w_agent, c_agent, m_agent], tasks=[plan, write, check, memory]
    )
