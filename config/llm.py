import os
from crewai import LLM
from dashscope import Generation  # Qwen 官方 SDK


def get_llm_for_role(role="writer", llm_type=None):
    """
    返回一个可调用对象，模拟 LLM(**params) 的行为，
    内部使用 Qwen SDK Generation.call 完成请求。
    """
    if llm_type is None:
        llm_type = os.getenv("LLM_TYPE", "claude")
    # 基础共享配置 (超时与重试)
    common_params = {
        "timeout": 600,
        "max_retries": 5,
    }

    if llm_type == "claude":
        # Claude API 配置
        base_claude_config = {
            "provider": "anthropic",
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
        }

        # 角色特定配置
        role_configs = {
            "writer": {
                "model": "claude-sonnet-4-6",
                "temperature": 0.85,
                "top_p": 1.0,
                "max_tokens": 12000,
            },
            "director": {
                "model": "claude-sonnet-4-6",
                "temperature": 0.7,
                "top_p": 1.0,
                "max_tokens": 4096,
            },
            "checker": {
                "model": "claude-sonnet-4-6",
                "temperature": 0.2,
                "top_p": 1.0,
                "max_tokens": 4096,
            },
            "curator": {
                "model": "claude-sonnet-4-6",
                "temperature": 0.5,
                "top_p": 1.0,
                "max_tokens": 4096,
            },
            "polisher": {
                "model": "claude-sonnet-4-6",
                "temperature": 0.6,
                "top_p": 1.0,
                "max_tokens": 12000,
            },
        }

        specific_config = role_configs.get(
            role,
            {
                "model": "claude-sonnet-4-6",
                "temperature": 0.7,
                "top_p": 1.0,
                "max_tokens": 2048,
            },
        )

        target_config = {**base_claude_config, **specific_config}
    elif llm_type == "openai":
        # 默认基础配置
        base_openai_config = {
            "model": os.getenv("OPENAI_MODEL_NAME"),
            "base_url": os.getenv("OPENAI_API_BASE"),
            "api_key": os.getenv("OPENAI_API_KEY"),
        }

        # 角色特定配置
        role_configs = {
            "writer": {
                "temperature": 0.85,
                "top_p": 1.0,
                "max_tokens": 12000,
                "presence_penalty": 0.0,
            },
            "director": {
                "temperature": 0.7,
                "top_p": 1.0,
                "max_tokens": 4096,
                "presence_penalty": 0.0,
            },
            "checker": {
                "temperature": 0.2,
                "top_p": 1.0,
                "max_tokens": 4096,
                "presence_penalty": 0.1,
            },
            "curator": {
                "temperature": 0.5,
                "top_p": 1.0,
                "max_tokens": 4096,
                "presence_penalty": 0.0,
            },
            "polisher": {
                "temperature": 0.6,
                "top_p": 1.0,
                "max_tokens": 12000,
                "presence_penalty": 0.1,
            },
        }

        specific_config = role_configs.get(
            role,
            {
                "temperature": 0.7,
                "top_p": 1.0,
                "max_tokens": 2048,
                "presence_penalty": 0.0,
            },
        )

        target_config = {**base_openai_config, **specific_config}

    else:  # 默认为 qwen
        # 区分模式
        if role in ["writer", "checker", "polisher"]:
            # 深度推理模式
            target_config = {
                "model": os.getenv("QWEN_MODEL_2"),
                "base_url": os.getenv("QWEN_BASE_URL"),
                "api_key": os.getenv("QWEN_API_KEY"),
                "temperature": 0.85 if role == "writer" else 0.1,
                "top_p": 0.92 if role == "writer" else 0.1,
                "max_tokens": 12000 if role in ["writer", "polisher"] else 4096, # 统一增加输出上限
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
