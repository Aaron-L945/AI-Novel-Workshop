# workflow/chapter_flow.py
from memory.guard import write_creative_memory


def run_chapter(
    crew,
    canon_memory,
    creative_memory,
    chapter_num: int,
    feedback: str = None,  # 【新增】接收来自 UI 的反馈或逻辑错误
):
    # 1. 构造 inputs 字典
    # 注意：这些 key 必须与你 Task description 中的 {chapter_num}, {feedback} 等占位符一致
    inputs = {
        "chapter_num": chapter_num,
        "feedback": (
            feedback if feedback else "这是本章的初次创作，请根据大纲和设定自由发挥。"
        ),
        "canon_context": canon_memory.model_dump_json(),  # 将当前的设定集转为文本给 AI 参考
        "context_instruction": (
            """
### 1. 开篇设定（黄金三章准则）：
- **世界观切入**：不要堆砌设定，通过主角的遭遇自然引出。
- **核心钩子**：本章末尾必须制造一个巨大的悬念或危机（Hook），吸引读者点开下一章。
- **身份定位**：明确交代主角当前的处境、社会地位及核心矛盾。
"""
            if chapter_num == 1
            else """
### 1. 冲突结算与衔接：
- **上章收尾**：必须先交代上一章末尾危机的结果。
- **时间锚点**：明确本章与上章的时间间隔（如“三日后”）。
"""
        ),     # 初始章节与后续章节的指令差异

    }

    # 2. 调用 kickoff 并传入 inputs
    # 这样所有 Task 里的 {feedback} 都会被替换成实际内容
    result = crew.kickoff(inputs=inputs)

    # 3. 获取各阶段输出
    # 注意：如果你的 Crew 结构变了，索引可能需要调整；
    # 建议使用任务名称获取更稳妥，例如：result.extract_output_from_task("WriteTask")
    chapter_text = result.tasks_output[1].raw
    check_results = result.tasks_output[2].raw
    memory_notes = result.tasks_output[3].raw

    # 4. 存入向量数据库
    # 如果是重写，我们可以在 content 里标注一下是修正后的记忆
    save_content = memory_notes
    if feedback:
        save_content = f"【修正重写】基于反馈：{feedback}\n新记忆点：{memory_notes}"

    write_creative_memory(
        agent_name="MemoryCurator",
        memory=creative_memory,
        content=save_content,
        chapter_num=chapter_num,
        full_text=chapter_text,
    )

    return chapter_text, check_results, memory_notes
