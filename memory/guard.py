# memory/guard.py
from memory.creative import CreativeMemory
import os


def write_creative_memory(
    agent_name: str,
    memory: CreativeMemory,
    content: str,
    chapter_num: int,
    full_text: str,
):
    if agent_name != "MemoryCurator":
        raise PermissionError("Only MemoryCurator can write creative memory")

    # 修改这里：调用带有 chapter_num 的 write_note
    # 这会触发你之前写的带有元数据存储的 ChromaDB 逻辑
    memory.write_note(content, chapter_num)

    # 2. 【核心修改】写入本地文件（存的是正文，用于点击查看）
    if full_text:
        # 创建存档文件夹
        archive_dir = "story_archive"
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)

        file_path = f"{archive_dir}/chapter_{chapter_num}.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_text)
