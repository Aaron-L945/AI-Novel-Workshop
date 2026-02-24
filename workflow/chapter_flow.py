# workflow/chapter_flow.py
import json
import random

from crewai import Crew

from utils.helpers import parse_tagged_memory
from memory.canon import CanonMemory


def prepare_generation_inputs(
    chapter_num, feedback, canon_memory: CanonMemory, creative_memory, reference_material="", style_profile=None
):
    """
    优化后的 Prompt 输入构建逻辑
    """

    # 1. 动态裁剪 Timeline (滑动窗口：只给最近 3 章的详细记录)
    # 防止 Prompt 随章节增加而无限膨胀
    recent_timeline = (
        canon_memory.timeline[-3:]
        if len(canon_memory.timeline) > 3
        else canon_memory.timeline
    )

    # 2. 核心设定与状态 (只保留最关键的 JSON 部分)
    core_config = {
        "world": canon_memory.world.model_dump(),  # 修复点
        "characters": {
            name: char.model_dump() for name, char in canon_memory.characters.items()
        },  # 修复点
        "recent_history": [event.model_dump() for event in recent_timeline],  # 修复点
    }

    # 3. 语义检索 (利用向量库找回与当前 query 相关的“沉睡伏笔”)
    # 假设 feedback 里包含用户想写的关键词，如果没有，就用前一章的描述去搜
    search_query = (
        feedback
        if feedback
        else (canon_memory.timeline[-1].description if canon_memory.timeline else "")
    )
    historical_recall, _ = creative_memory.recall(search_query, n_results=2)

    # 4. 构建最终 inputs
    styles = [
        "侧重细腻的心理描写",
        "侧重肃杀的环境渲染",
        "侧重激烈的动作细节",
        "侧重冷峻的叙事风格",
    ]
    
    # 5. 处理 Context Instruction，合并参考资料和风格档案
    base_instruction = get_context_instruction(chapter_num)
    
    if style_profile:
        # 如果有风格档案，将其注入到指令中
        base_instruction += f"""
        
### 🎭 目标写作风格（请严格模仿）：
{style_profile}
"""
    # 如果有风格档案，就不再参考原文，避免干扰
    # 只有在没有风格档案，或者参考资料本身不是风格样本时，才加入参考资料
    elif reference_material:
        base_instruction += f"\n\n### 📚 附加参考资料：\n{reference_material}"

    inputs = {
        "chapter_num": chapter_num,
        "feedback": feedback if feedback else "这是本章的初次创作，请保持叙事张力。",
        "canon_context": json.dumps(core_config, ensure_ascii=False),  # 精简后的设定
        "historical_recall": (
            historical_recall if historical_recall != "NO_MATCH" else "无特定相关历史伏笔"
        ),
        "context_instruction": base_instruction,
        "style_preset": random.choice(styles),
    }
    return inputs


def get_context_instruction(chapter_num):
    """指令集解耦，增加写作技巧引导"""
    if chapter_num == 1:
        return """
### 🖋️ 创作指令：黄金开篇
- **环境渲染**：通过视觉/嗅觉/触觉（如“血腥气”、“刺骨寒风”）引出世界观，严禁设定堆砌。
- **核心钩子**：章末制造一个事关生死的选择或突如其来的变故。
- **节奏控制**：前 500 字内必须爆发第一个小冲突。
"""
    else:
        return """
### 🖋️ 创作指令：承上启下
- **逻辑闭环**：精准结算上章末尾的悬念，给出合理的行动代价。
- **人物弧光**：主角在面对当前冲突时，必须展现出性格中的“坚韧”或“果断”。
- **埋线逻辑**：结合提供的【历史相关记录】，在对话或环境中低调呼应之前的伏笔。
"""


def run_chapter(
    crew: Crew,
    canon_memory: CanonMemory,
    creative_memory,
    chapter_num: int,
    feedback: str = None,  # 【新增】接收来自 UI 的反馈或逻辑错误
    reference_material: str = "", # 【新增】接收来自 UI 的参考资料
    style_profile=None, # 【新增】接收来自 UI 的风格档案
):
    # 1. 构造 inputs 字典
    # 注意：这些 key 必须与你 Task description 中的 {chapter_num}, {feedback} 等占位符一致
    inputs = prepare_generation_inputs(
        chapter_num=chapter_num,
        feedback=feedback,
        canon_memory=canon_memory,
        creative_memory=creative_memory,
        reference_material=reference_material,
        style_profile=style_profile,
    )

    # 2. 调用 kickoff 并传入 inputs
    # 这样所有 Task 里的 {feedback} 都会被替换成实际内容
    result = crew.kickoff(inputs=inputs)

    # 3. 获取各阶段输出
    # 优化：通过 Task 名称来获取输出，不再依赖固定的索引
    
    # 建立 Task Name 到 Output 的映射
    # CrewAI 的 result.tasks_output 列表顺序与 crew.tasks 列表一致
    task_output_map = {}
    
    if hasattr(crew, 'tasks') and len(crew.tasks) == len(result.tasks_output):
        for i, task in enumerate(crew.tasks):
            # 获取任务名称，如果未定义 name 属性，则可能为空
            # 我们在定义 Task 时已经加上了 name="WriteTask" 等
            task_name = getattr(task, 'name', None)
            if task_name:
                task_output_map[task_name] = result.tasks_output[i].raw

    # 根据名称获取结果，具有更好的鲁棒性
    # 优先取润色稿，没有则取初稿
    chapter_text = task_output_map.get("PolishTask")
    if not chapter_text:
         chapter_text = task_output_map.get("WriteTask", "")
         
    check_results = task_output_map.get("CheckTask", "未执行检查")
    
    # MemoryTask 输出可能是 JSON 字符串，需要解析
    raw_memo = task_output_map.get("MemoryTask", "{}")

    # debug
    print(f"chapter length: {len(chapter_text)}")

    canon_dict = canon_memory.read()
    # 使用标签解析器
    memory_notes = parse_tagged_memory(raw_memo, canon_data=canon_dict)

    # 将字典转为语义化的纯文本
    formatted_memo = (
        f"第{chapter_num}章剧情提要：{memory_notes['summary']}\n"
        f"角色动态：{memory_notes['char_update']}\n"
        f"场景地点：{memory_notes['locations']}\n"
        f"关键线索：{memory_notes['plot_chain']}"
    )

    # 2. 如果是重写，合并反馈信息
    if feedback:
        formatted_memo = f"【修正版本】基于反馈({feedback})重写：\n{formatted_memo}"

    return chapter_text, check_results, memory_notes, formatted_memo
