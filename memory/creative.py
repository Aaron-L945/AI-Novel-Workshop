import os
import numpy as np
import chromadb
from sentence_transformers import SentenceTransformer
from datetime import datetime


class CreativeMemory:
    def __init__(self, model_path: str, db_path="novel_memory"):
        # 1. 加载模型 (允许从 HuggingFace 下载)
        self.model = SentenceTransformer(
            model_path, trust_remote_code=True, device="cpu", local_files_only=False
        )

        # 2. 初始化 ChromaDB
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name="creative_archive")

        # 3. 短期滑动窗口内存
        self.working_context = []
        self.limit = 5

    def _get_embedding(self, text: str, is_query: bool = True):
        """生成并归一化向量，返回 1D 列表 [float, ...]"""
        prefix = "search_query: " if is_query else "search_document: "
        full_text = prefix + text

        # encode 返回的是 numpy 数组
        # 注意：这里传入的是 [full_text]，encode 返回 [[...]]，我们取 [0] 变成 1D
        embedding = self.model.encode([full_text], convert_to_numpy=True)[0]

        # L2 归一化：解决距离数值过大（300+）的问题，使其缩放到 0-2 之间
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding.tolist()

    def write_note(self, content: str, chapter_num: int):
        """存入记忆"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 获取 1D 向量
        emb = self._get_embedding(content, is_query=False)

        # 存入向量库：embeddings 参数要求是 [[...]]，所以包装一层 [emb]
        self.collection.add(
            documents=[content],
            embeddings=[emb],
            metadatas=[{"chapter": chapter_num, "time": timestamp}],
            ids=[f"ch_{chapter_num}_{datetime.now().timestamp()}"],
        )

        # 更新工作内存
        self.working_context.append(content)
        if len(self.working_context) > self.limit:
            self.working_context.pop(0)

    def recall(self, query: str, n_results: int = 3):
        """语义检索 + 阈值过滤"""
        count = self.collection.count()
        if count == 0:
            return "NO_MATCH", "\n".join(self.working_context)

        # 获取查询向量 (1D 列表)
        query_emb = self._get_embedding(query, is_query=True)

        # 向量库查询
        results = self.collection.query(
            query_embeddings=[query_emb],
            n_results=min(n_results, count),
        )

        valid_docs = []
        docs = results["documents"][0]
        distances = results["distances"][0]

        # 💡 核心优化：由于做了归一化，L2距离现在很小
        # 0.0 - 0.4: 极度相关 | 0.4 - 0.6: 比较相关 | > 0.8: 不相关
        threshold = 0.7

        for doc, dist in zip(docs, distances):
            has_keyword = query.lower() in doc.lower()
            # 只有满足关键词命中，或者距离足够近才通过
            if has_keyword or dist < threshold:
                valid_docs.append(doc)

        # 格式化输出
        hist_text = "\n\n".join(valid_docs) if valid_docs else "NO_MATCH"
        recent_text = "\n".join(self.working_context)

        return hist_text, recent_text
