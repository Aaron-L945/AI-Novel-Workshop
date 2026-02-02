import os
import shutil
import json

from memory.creative import CreativeMemory
from memory.canon import CanonMemory


def save_canon(canon: CanonMemory, path="canon_storage.json"):
    """兼容 Pydantic V2 的 JSON 保存模式"""
    # 1. 先使用 model_dump 将模型转换为原生 Python 字典
    # mode='json' 会确保 datetime 等对象被转为字符串
    canon_dict = canon.model_dump(mode="json")

    # 2. 使用标准的 json.dumps 进行格式化保存
    with open(path, "w", encoding="utf-8") as f:
        json.dump(canon_dict, f, ensure_ascii=False, indent=4)


def load_canon(path="canon_storage.json"):
    """兼容 Pydantic V2 的 JSON 读取模式"""
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # V2 使用 model_validate 代替 parse_obj
            return CanonMemory.model_validate(data)
    return None


def reset_all_data(creative_memory: CreativeMemory):
    # 1. 清空向量库
    try:
        collection_name = creative_memory.collection.name

        # 假设你的 collection 名字叫 'novel_events'
        creative_memory.client.delete_collection(name=collection_name)
        # 然后重新创建一个同名的空集合
        creative_memory.collection = creative_memory.client.create_collection(
            name=collection_name
        )
        print("向量库已彻底重置")
    except Exception as e:
        print(f"重置失败: {e}")

    # 2. 删除正文存档
    if os.path.exists("story_archive"):
        shutil.rmtree("story_archive")

    # 3. 删除 JSON 存档 (注意这里后缀改成了 .json)
    if os.path.exists("canon_storage.json"):
        os.remove("canon_storage.json")
