import os
from crewai import LLM


def get_llm_for_role(role="writer"):
    # 基础共享配置
    base_config = {
        "model": f"openai/{os.getenv('MODEL')}",
        "base_url": os.getenv("OPENAI_API_BASE"),
        "api_key": os.getenv("OPENAI_API_KEY"),
        "timeout": 600,  # 30B模型推理慢，10分钟超时是合理的
        "max_retries": 3,
    }

    # 针对 30B 级别本地模型的底层优化参数
    # num_ctx 必须覆盖：Prompt内容 + Thinking过程 + 最终回答
    local_server_config = {
        "num_ctx": 16384,  # 调大到16k，防止Thinking过程把窗口撑爆
        "num_predict": 8192,  # 对应 max_tokens 的底层映射
        "temperature": 0.0,  # 默认基准
    }

    # 差异化参数映射表
    role_settings = {
        "writer": {
            "temperature": 0.85,
            "top_p": 0.92,
            "max_tokens": 8192,  # 极大扩容：Thinking 4k + 正文 4k
            "presence_penalty": 0.3,  # 额外：减少网文常用词重复
        },
        "director": {"temperature": 0.5, "top_p": 0.85, "max_tokens": 3000},
        "checker": {"temperature": 0.1, "top_p": 0.1, "max_tokens": 2000},
        "curator": {
            "temperature": 0.0,
            "max_tokens": 2000,
            "extra_headers": (
                {"X-Reasoning-Effort": "low"}
                if "thinking" in base_config["model"].lower()
                else {}
            ),
        },
    }

    params = role_settings.get(role, role_settings["writer"])

    # 注入全局环境屏蔽监控（解决报错干扰）
    os.environ["OTEL_SDK_DISABLED"] = "true"

    return LLM(
        **base_config, **params, config=local_server_config  # 统一应用底层窗口配置
    )
