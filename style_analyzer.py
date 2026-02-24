from crewai import Agent, Task, Crew
from config.llm import get_llm_for_role
import json

def analyze_style(text_content):
    """
    接收长文本，调用 LLM 进行风格分析，返回结构化的风格档案 (JSON 字符串)。
    """
    
    # 1. 简单的分块逻辑 (避免 token 溢出)
    # 取前 3000 字和后 1000 字作为样本，通常开头和结尾最能体现风格
    if len(text_content) > 4000:
        sample_text = text_content[:3000] + "\n...\n" + text_content[-1000:]
    else:
        sample_text = text_content

    # 2. 定义分析 Agent
    analyst = Agent(
        role="文学风格分析师",
        goal="从文本中提取深层的写作风格特征，生成可复用的风格档案。",
        backstory="""你是一位享誉文坛的文学评论家，擅长解构作家的笔触。
        你能从用词、句式、节奏、修辞等多个维度，精准捕捉文字背后的“指纹”。
        你不仅能分析，还能将这些特征转化为结构化的指导原则，供其他作家模仿。""",
        llm=get_llm_for_role("director", llm_type="openai"), # 复用 director 的配置
        verbose=True,
    )

    # 3. 定义分析任务
    analysis_task = Task(
        description=f"""
请深入分析以下参考文本的写作风格：

【参考文本片段】：
{sample_text}

请从以下维度进行结构化提取：
1. **叙事视角与口吻** (e.g., 冷峻旁观、第一人称沉浸、戏谑调侃)
2. **句式特征** (e.g., 短句为主、长短句交替、复杂的从句结构)
3. **修辞偏好** (e.g., 善用比喻、心理描写细腻、环境渲染浓重)
4. **用词习惯** (e.g., 古风雅致、硬核科幻、市井俚语)
5. **节奏感** (e.g., 紧凑、舒缓、爆发力强)

请输出一个 JSON 格式的风格档案，包含 key: [tone, sentence_structure, rhetoric, vocabulary, rhythm, summary]。
其中 summary 字段用一句话总结这种风格（例如：“这是一种充满黑色幽默的硬汉侦探风格”）。
""",
        expected_output="""
JSON 格式的风格档案。
Example:
{
    "tone": "...",
    "sentence_structure": "...",
    "rhetoric": "...",
    "vocabulary": "...",
    "rhythm": "...",
    "summary": "..."
}
""",
        agent=analyst
    )

    # 4. 执行分析
    crew = Crew(
        agents=[analyst],
        tasks=[analysis_task],
        verbose=True
    )
    
    result = crew.kickoff()
    
    # 5. 结果清理与解析
    raw_output = result.raw
    
    # 去除可能的 markdown 代码块标记
    cleaned_output = raw_output.replace("```json", "").replace("```", "").strip()
    
    # 尝试解析 JSON 以确保格式正确，如果不正确则返回原始文本
    try:
        json_obj = json.loads(cleaned_output)
        # 重新格式化为紧凑的字符串，或者直接返回 dict
        # 这里为了配合后续流程，我们返回 dict 或格式化后的 json string
        return json_obj
    except json.JSONDecodeError:
        # 如果解析失败，可能是因为包含额外文本，尝试简单的提取
        # 这里简单起见，如果解析失败，就直接返回清理后的文本，或者构造一个包含错误的 dict
        print(f"Warning: Failed to parse style analysis JSON. Raw: {raw_output}")
        return {
            "summary": "风格分析结果格式异常，以下是原始分析：",
            "raw_analysis": cleaned_output
        }
