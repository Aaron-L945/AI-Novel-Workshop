import os
from crewai import LLM
import os
from dashscope import Generation  # Qwen 官方 SDK


def get_llm_for_role(role="writer"):
    """
    返回一个可调用对象，模拟 LLM(**params) 的行为，
    内部使用 Qwen SDK Generation.call 完成请求。
    """
    # 基础共享配置 (超时与重试)
    common_params = {
        "timeout": 600,
        "max_retries": 5,
    }

    # 区分模式
    if role in ["writer", "checker"]:
        # 深度推理模式
        target_config = {
            "model": os.getenv("QWEN_MODEL_2"),
            "base_url": os.getenv("QWEN_BASE_URL"),
            "api_key": os.getenv("QWEN_API_KEY"),
            "temperature": 0.85 if role == "writer" else 0.1,
            "top_p": 0.92 if role == "writer" else 0.1,
            "max_tokens": 8192 if role == "writer" else 3000,
            "presence_penalty": 0.3 if role == "writer" else 0.0,
        }
    else:
        # 极速模式
        target_config = {
            "model": os.getenv("QWEN_MODEL_2"),
            "base_url": os.getenv("QWEN_BASE_URL"),
            "api_key": os.getenv("QWEN_API_KEY"),
            "temperature": 0.2,
            "max_tokens": 1500,
        }

    # 合并参数
    final_params = {**common_params, **target_config}
    return LLM(**final_params)
