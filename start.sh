#!/bin/bash

# AI Novel Workshop 启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 设置 PYTHONPATH
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# 加载 .env 文件（如果存在）
if [ -f "${SCRIPT_DIR}/.env" ]; then
    export $(grep -v '^#' "${SCRIPT_DIR}/.env" | xargs)
fi

# 激活虚拟环境
if [ -d "${SCRIPT_DIR}/.venv" ]; then
    source "${SCRIPT_DIR}/.venv/bin/activate"
elif [ -d "${HOME}/kortex/.venv" ]; then
    source "${HOME}/kortex/.venv/bin/activate"
fi

# 确保 config 目录是有效的 Python 包
if [ ! -f "${SCRIPT_DIR}/config/__init__.py" ]; then
    touch "${SCRIPT_DIR}/config/__init__.py"
fi

# 启动 Streamlit
cd "${SCRIPT_DIR}"
streamlit run app.py
