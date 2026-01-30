# memory/guard.py
import os
from memory.creative import CreativeMemory


def write_creative_memory(
    agent_name: str,
    memory: CreativeMemory,
    content: any,  # 可能是 dict (方案B) 或 str
    chapter_num: int,
    full_text: str,
):
    if agent_name != "MemoryCurator":
        raise PermissionError("Only MemoryCurator can write creative memory")

    # 1. 处理 content：将字典转换为适合 Embedding 的描述性字符串
    if isinstance(content, dict):
        # 提取关键字段，并拼接成一段自然语言
        summary = content.get("summary", "无摘要")
        chars = ", ".join(content.get("involved_characters", ["未知角色"]))
        locs = ", ".join(content.get("locations", ["未知地点"]))

        # 这种格式最利于向量检索（语义清晰）
        save_content = (
            f"第 {chapter_num} 章剧情摘要：{summary}。涉及角色：{chars}。地点：{locs}。"
        )
    else:
        # 如果已经是字符串，直接使用
        save_content = str(content)

    # 调用带有 chapter_num 的 write_note 存入 ChromaDB
    # 这里我们传的是格式化后的 save_content
    memory.write_note(save_content, chapter_num)

    # 2. 写入本地文件（存的是正文，用于点击查看）
    if full_text:
        archive_dir = "story_archive"
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)

        file_path = f"{archive_dir}/chapter_{chapter_num}.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_text)
