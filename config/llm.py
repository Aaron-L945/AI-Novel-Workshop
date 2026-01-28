import os
from crewai import LLM


def get_llm_for_role(role="writer"):
    # 基础共享配置
    base_config = {
        "model": f"openai/{os.getenv('MODEL')}",
        "base_url": os.getenv("OPENAI_API_BASE"),
        "api_key": os.getenv("OPENAI_API_KEY"),
        "timeout": 600,
        "max_retries": 5,  # 增加重试次数，提高稳定性
    }

    # 1. 差异化参数设置
    if role in ["writer", "checker"]:
        # --- 【深度推理模式】 ---
        # 适用于需要处理复杂因果、纠正逻辑、文学润色的角色
        mode_params = {
            "temperature": 0.85 if role == "writer" else 0.1,
            "top_p": 0.92 if role == "writer" else 0.1,
            "max_tokens": 8192 if role == "writer" else 3000,
            "presence_penalty": 0.3 if role == "writer" else 0.0,
            "config": {
                "num_ctx": 16384,  # 16k 窗口：装得下思考过程
                "num_predict": 8192,
            },
        }
    else:
        # --- 【极速/直出模式】 ---
        # 适用于导演规划、记忆提取。强制模型“别想了，直接出结果”
        mode_params = {
            "temperature": 0.1,  # 强制最高确定性
            "max_tokens": 2000,
            "extra_headers": {
                # 某些后端通过 header 降低推理强度，或强制跳过 reasoning parser
                "X-Reasoning-Effort": "low",
            },
            "config": {
                "num_ctx": 8192,  # 缩小窗口，加快响应并减少显存占用
                "stop": ["</think>", "\n\n###"],  # 强制截断思考，或者遇到标题直接返回
            },
        }

    # 2. 合并配置
    final_params = {**base_config, **mode_params}

    # 注入全局环境屏蔽监控
    os.environ["OTEL_SDK_DISABLED"] = "true"

    return LLM(**final_params)
