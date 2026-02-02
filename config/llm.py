import os
from crewai import LLM


def get_llm_for_role(role="writer"):
    # 基础共享配置 (超时与重试)
    common_params = {
        "timeout": 600,
        "max_retries": 5,
    }

    # 1. 差异化模型与 API 地址配置
    if role in ["writer", "checker"]:
        # --- 【深度推理模式】：使用主模型 MODEL (通常是强推理模型) ---
        target_config = {
            "model": f"openai/{os.getenv('MODEL')}",
            "base_url": os.getenv("OPENAI_API_BASE"),
            "api_key": os.getenv("OPENAI_API_KEY"),
            "temperature": 0.85 if role == "writer" else 0.1,
            "top_p": 0.92 if role == "writer" else 0.1,
            "max_tokens": 8192 if role == "writer" else 3000,
            "presence_penalty": 0.3 if role == "writer" else 0.0,
            "config": {
                "num_ctx": 16384,
                "num_predict": 8192,
            },
        }
    else:
        # --- 【极速/直出模式】：使用次模型 MODEL_2 (通常是快模型，如 Curator/Director) ---
        target_config = {
            "model": f"openai/{os.getenv('MODEL_2')}",
            "base_url": os.getenv("OPENAI_API_BASE_2"),
            "api_key": os.getenv("OPENAI_API_KEY_2"),  # 允许共用或独立 API Key
            "temperature": 0.2,
            "max_tokens": 1500,
            "config": {
                "num_ctx": 8192,
            },
        }

    # 2. 合并配置
    final_params = {**common_params, **target_config}

    # 屏蔽 OpenTelemetry 监控
    os.environ["OTEL_SDK_DISABLED"] = "true"

    return LLM(**final_params)
