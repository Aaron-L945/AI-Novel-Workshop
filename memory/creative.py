# memory/creative.py
# class CreativeMemory:
#     def __init__(self):
#         self.archive = []

#     def recall(self, query: str):
#         # 先占位，后面接向量 / MemGPT
#         return self.archive[-5:]

#     def _write(self, content: str):
#         self.archive.append(content)


import chromadb
from sentence_transformers import SentenceTransformer
from datetime import datetime
import os


class CreativeMemory:
    def __init__(self, model_path: str, db_path="./novel_memory", chapter_num = 0):
        """
        model_path: 你从 ModelScope 下载的模型文件夹绝对路径
        """
        # 1. 加载本地模型
        # trust_remote_code=True 是必须的，因为 Nomic 模型包含自定义逻辑
        self.model = SentenceTransformer(model_path, trust_remote_code=True, device="cpu", local_files_only=True)

        # 2. 初始化 ChromaDB
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name="creative_archive")

        # 3. 短期滑动窗口内存
        self.working_context = []
        self.limit = 5

    def _get_embedding(self, text: str, is_query: bool = True):
        """使用本地加载的 nomic-embed-text 生成向量"""
        # Nomic 官方建议在输入前添加特定任务前缀以提升效果
        prefix = "search_query: " if is_query else "search_document: "
        full_text = prefix + text

        # 生成向量并转换为 list 格式供 ChromaDB 使用
        embeddings = self.model.encode([full_text], convert_to_numpy=True)
        return embeddings[0].tolist()

    def write_note(self, content: str, chapter_num):
        """提取的记忆持久化存储"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 存入向量库
        self.collection.add(
            documents=[content],
            embeddings=[self._get_embedding(content, is_query=False)],
            metadatas=[{"chapter": chapter_num, "time": timestamp}],
            ids=[f"ch_{chapter_num}_{datetime.now().timestamp()}"],
        )

        # 更新工作内存
        self.working_context.append(content)
        if len(self.working_context) > self.limit:
            self.working_context.pop(0)

    def recall(self, query: str, n_results: int = 3):
        """语义检索"""
        results = self.collection.query(
            query_embeddings=[self._get_embedding(query, is_query=True)],
            n_results=n_results,
        )

        historical_context = "\n".join(results["documents"][0])
        recent_context = "\n".join(self.working_context)

        return f"【历史相关记录】：\n{historical_context}\n\n【近期情节回顾】：\n{recent_context}"


# --- 使用示例 ---
# LOCAL_MODEL_DIR = "/root/models/nomic-embed-text-v1.5" # 替换为你实际解压的路径
# creative = CreativeMemory(model_path=LOCAL_MODEL_DIR)
