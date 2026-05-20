# workflow/chapter_flow.py
import json
import random
import re

from crewai import Crew

from utils.helpers import parse_tagged_memory
from memory.canon import CanonMemory


def prepare_generation_inputs(
    chapter_num, feedback, canon_memory: CanonMemory, creative_memory, reference_material="", style_profile=None, target_word_count=3000
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

    # 3.1 情节重复检测
    # 使用 search_query 在向量库中搜索，如果存在相似度极高（距离很小）的记录，说明该情节可能已经写过
    # 注意：creative_memory.recall 返回的是 (hist_text, recent_text)
    # 我们需要通过 creative_memory 的底层方法或者稍微修改 recall 来获取距离信息
    # 这里我们直接调用 creative_memory.collection.query 来获取距离
    
    # 构造查询向量
    query_emb = creative_memory._get_embedding(search_query, is_query=True)
    
    # 查询最相似的 1 条记录
    duplication_check = creative_memory.collection.query(
        query_embeddings=[query_emb],
        n_results=1
    )
    
    # 检查距离
    # 这里的阈值需要根据实际模型调整，nomic-embed-text-v1.5 归一化后，相似内容的距离通常小于 0.3
    # 如果距离小于阈值，说明库里已经有非常相似的内容
    if duplication_check["ids"] and duplication_check["distances"][0]:
        min_dist = duplication_check["distances"][0][0]
        # 设定一个严格的阈值，比如 0.25，表示高度重复
        if min_dist < 0.25:
            existing_content = duplication_check["documents"][0][0]
            # 只有当 feedback 存在（即用户有明确意图）时，才提示重复
            # 如果是自动生成的 search_query（基于上一章），则不需要查重
            if feedback:
                 base_instruction_warning = f"""
⚠️ **警告：情节重复检测**
检测到您提供的构思与历史情节高度雷同！
【历史相似片段】：{existing_content}
请务必**更换情节走向**，或者从完全不同的角度进行描写，避免读者产生疲劳感。
"""
                 # 将警告插入到 feedback 中，强制 AI 注意
                 feedback += f"\n\n{base_instruction_warning}"

    # 4. 构建最终 inputs
    styles = [
        "侧重细腻的心理描写",
        "侧重肃杀的环境渲染",
        "侧重激烈的动作细节",
        "侧重冷峻的叙事风格",
    ]
    
    # 5. 处理 Context Instruction，合并参考资料和风格档案
    base_instruction = get_context_instruction(chapter_num)
    
    # 注入字数限制指令
    base_instruction += f"\n\n### 📏 字数要求：\n请将本章正文长度控制在 **{target_word_count}** 字左右（允许上下浮动 10%）。内容必须充实，拒绝注水。"
    
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
        "target_word_count": target_word_count, # 【修复】添加 target_word_count 到 inputs 字典
    }
    return inputs


def strip_think_content(text: str) -> str:
    """
    去除文本中的 <think>... 思考过程标记
    以及 Final Answer: 等 AI 输出前缀
    """
    if not text:
        return text
    import re
    
    # ========================================
    # 【新增】第一步：智能提取正文部分
    # ========================================
    
    # 策略1：查找"第X章："作为正文的起始点，删除之前的所有内容
    chapter_match = re.search(r"第\s*\d+\s*章[：:]\s*[^\n]*\n", text)
    if chapter_match:
        # 如果发现"第X章"前面有大量分析内容，说明需要截断
        if chapter_match.start() > 200:
            # 保留从"第X章"开始的内容
            text = text[chapter_match.start():]
    
    # 策略2：查找"润色后的文本"标记，删除之前的所有内容
    polish_marker = re.search(r"润色后的?文本[：:]", text)
    if polish_marker:
        text = text[polish_marker.end():]
    
    # 策略3：查找"原文"标记后的正式内容（区分分析用的"原文"和正文）
    # 如果"原文"后面紧跟正文段落，则从那里开始
    original_marker = re.search(r"原文[：:]\s*\n", text)
    if original_marker:
        # 检查原文标记后是否是长段落（超过100字）
        rest = text[original_marker.end():]
        next_newline = rest.find("\n")
        if next_newline > 50:  # 原文内容超过50字，可能是正文
            # 但这可能是分析段落，需要继续检查是否有"润色后"
            pass
    
    # ========================================
    # 第二步：去除各种 AI 输出标记
    # ========================================
    
    # 去除 XML 注释形式 <!-- ... -->
    text = re.sub(r"<!--[\s\S]*?-->", "", text)
    
    # 去除 <think>... 形式（最外层包裹）
    text = re.sub(r"<think>[\s\S]*?", "", text, flags=re.IGNORECASE)
    
    # 去除 <think>... 形式（未闭合的）
    text = re.sub(r"<think>[\s\S]*?$", "", text, flags=re.IGNORECASE)
    
    # 去除 Final Answer: 之后的所有内容（仅保留 Final Answer 部分）
    # 这对 Qwen-Thinking 模式的输出特别有效
    final_answer_match = re.search(r"Final\s+Answer\s*[:：]\s*", text, re.IGNORECASE)
    if final_answer_match:
        # 提取 Final Answer: 之后的内容
        after_final = text[final_answer_match.end():]
        # 如果 Final Answer 部分很短（几百字以内），认为是正常输出
        if len(after_final.strip()) < 500:
            text = after_final.strip()
    
    # 去除 Agent: XXX 这样的前缀行
    text = re.sub(r"^(Agent|角色|任务)[\s:：]+.*$", "", text, flags=re.MULTILINE)
    
    # 去除 【】 方括号包裹的标签
    text = re.sub(r"【[^】]*】", "", text)
    
    # 去除 ** 包裹的标题
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    
    # ========================================
    # 【新增】第三步：去除分析说明段落
    # ========================================
    
    # 去除"用户要求我"、"让我先分析"、"根据润色要求"等分析性开头
    analysis_patterns = [
        r"用户要求我作为.*?开始润色[，，]?\s*",
        r"让我先分析.*?\n",
        r"根据润色要求[：:].*?\n",
        r"问题[：:]\s*\d+[.、].*?\n",
        r"让我开始润色[，，]?逐段处理[：:]\s*",
        r"节点一[：:].*?\n",
        r"原文[：:]\s*\n",  # 分析中引用的原文
    ]
    for pattern in analysis_patterns:
        text = re.sub(pattern, "", text, flags=re.MULTILINE | re.IGNORECASE)
    
    # 去除"这是分析过程"的典型特征行
    lines = text.split('\n')
    clean_lines = []
    skip_mode = False
    for line in lines:
        # 检测是否为分析说明段落（短行 + 分析性词汇）
        stripped = line.strip()
        if len(stripped) < 100:  # 短行可能是说明
            if any(kw in stripped for kw in ['分析', '润色', '问题', '规则', '要求', '根据']):
                if not re.search(r"第\s*\d+\s*章", stripped):  # 但章节标题要保留
                    continue  # 跳过这行
        clean_lines.append(line)
    text = '\n'.join(clean_lines)
    
    return text.strip()


def extract_final_answer_only(text: str) -> str:
    """
    专门用于从 Qwen-Thinking 模式中提取干净的 Final Answer
    如果 Final Answer 部分过长（包含原文），则返回空字符串让调用方使用备用逻辑
    """
    if not text:
        return text
    
    import re
    
    # 查找 Final Answer: 或 Final Answer\n 的位置
    match = re.search(r"(?:Final\s+Answer|最终答案)[\s:：]*\n?", text, re.IGNORECASE)
    
    if match:
        content = text[match.end():]
        # 如果内容超过 2000 字，很可能是把原文也输出了（检查报告不应该这么长）
        if len(content.strip()) > 2000:
            return ""  # 返回空，让调用方使用备用逻辑
        return content.strip()
    
    # 如果没有找到 Final Answer，尝试查找章节标题（说明输出的是原文）
    # 如果文本以 "第X章" 开头，说明是小说正文，不是检查报告
    if re.match(r"第\s*\d+\s*章", text.strip()):
        return ""  # 返回空
    
    # 其他情况，返回原始文本（但仍去除 think 标签）
    return strip_think_content(text)


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
    target_word_count: int = 1000, # 【新增】目标字数
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
        target_word_count=target_word_count,
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
    
    # 【关键】去除 AI 思考过程标记，防止 thinking 过程泄露到最终输出
    chapter_text = strip_think_content(chapter_text)
         
    check_results = task_output_map.get("CheckTask", "未执行检查")
    # 对检查结果应用 Final Answer 提取逻辑（用于 Qwen-Thinking 模式）
    extracted_check = extract_final_answer_only(check_results)
    if extracted_check:
        check_results = extracted_check
    else:
        # 如果提取失败（可能输出的是原文），则仅去除 think 标签，保留格式
        check_results = re.sub(r"<think>.*?</think>", "", check_results, flags=re.DOTALL)
        # 如果处理后的内容过长（超过 2000 字），说明 AI 把原文输出了
        if len(check_results) > 2000:
            check_results = "⚠️ 检查任务输出异常，AI 可能将原文内容输出为检查报告，请人工审核章节逻辑。"
    
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
