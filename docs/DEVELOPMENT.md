# AI Novel Assistant 开发文档

本文档旨在介绍 AI 小说创作助手（AI Novel Assistant）的技术架构、核心工具链以及核心工作流。

## 🛠️ 核心工具链 (Tech Stack)

本项目采用现代化的 Python AI 应用开发栈，主要组件如下：

1.  **CrewAI**: 多智能体编排框架。
    *   用于构建 `Director` (导演)、`Writer` (作家)、`Polisher` (润色师)、`Checker` (检查员) 等 Agent。
    *   管理 Agent 之间的任务流转（Sequential Process）。
2.  **Streamlit**: 前端交互界面。
    *   提供直观的 Web UI，用于世界观设定、角色管理、章节预览和生成控制。
    *   利用 `st.session_state` 管理会话状态（如缓存的参考资料）。
3.  **ChromaDB**: 向量数据库（RAG）。
    *   存储和检索历史剧情、伏笔、设定。
    *   支持基于语义的上下文召回 (`CreativeMemory`)。
4.  **Qwen / OpenAI**: 大语言模型 (LLM)。
    *   底层推理引擎。支持 Qwen (通义千问) 和 OpenAI 接口模型。
    *   通过 `config/llm.py` 进行多模型路由和参数调优。
5.  **PyPDF2**: 文档处理。
    *   用于解析用户上传的 PDF 参考资料。

---

## 🌊 核心工作流 (Workflow)

本项目通过两个主要的工作流来实现小说的自动化创作：**章节生成流** 和 **风格分析流**。

### 1. 章节生成工作流 (Chapter Generation Flow)

这是一个由 CrewAI 驱动的链式流程，从大纲规划到最终成文。

```ascii
[用户输入/UI触发]
       |
       v
[准备上下文数据] (Canon, RAG, Ref)
       |
       v
+---------------------------------------------------------------+
|                      CrewAI Execution                         |
|                                                               |
|  1. Director (Plan Task)                                      |
|     |                                                         |
|     +---> 生成大纲 (Outline)                                  |
|             |                                                 |
|             v                                                 |
|  2. Writer (Write Task)                                       |
|     |                                                         |
|     +---> 生成初稿 (Draft)                                    |
|             |                                                 |
|             v                                                 |
|  3. Polisher (Polish Task)                                    |
|     |                                                         |
|     +---> 生成润色稿 (Final Text) ----------------------+     |
|             |                                           |     |
|             v                                           |     |
|  4. Checker (Check Task)                                |     |
|     |                                                   |     |
|     +---> 生成逻辑检查报告 (Report)                     |     |
|             |                                           |     |
|             v                                           |     |
|  5. Curator (Memory Task)                               |     |
|     |                                                   |     |
|     +---> 提取记忆信息 (Memory)                         |     |
|                                                         |     |
+---------------------------------------------------------+-----+
                                                          |
       +--------------------------------------------------+
       |
       v
[Streamlit UI 展示结果]
       |
       +---> 用户确认?
               |
               +---> 是: [持久化存储] (JSON, ChromaDB)
               |
               +---> 否: [重写/修改]
```

**流程详解：**

1.  **Director (导演)**: 接收当前章节号和背景信息，制定详细的本章大纲（`PlanTask`）。
2.  **Writer (作家)**: 根据大纲撰写小说初稿（`WriteTask`）。如果注入了**风格档案**，会在此阶段模仿目标风格。
3.  **Polisher (润色师)**: 对初稿进行深度润色（`PolishTask`），去除 AI 味，注入人性化细节（如去连接词、增强感官描写）。这是最终呈现在 UI 上的正文。
4.  **Checker (检查员)**: 审计润色后的文稿（`CheckTask`），检查是否与世界观（Canon）冲突，输出逻辑检查报告。
5.  **Curator (管理员)**: 从文稿中提取关键信息（摘要、新角色、伏笔）（`MemoryTask`），用于更新记忆库。

---

### 2. 风格分析工作流 (Style Analysis Flow)

这是一个独立的辅助流程，用于提取参考文本的写作特征。

```ascii
+-----------------------+
|                       |
|  用户上传参考文本     |
|  (Text / PDF / Input) |
|                       |
+-----------+-----------+
            |
            v
+-----------------------+
|                       |
|  Style Analyzer       |
|  (Director Agent)     |
|                       |
+-----------+-----------+
            | 提取特征 (Tone, Rhythm, Rhetoric...)
            v
+-----------------------+       +------------------------+
|                       |       |                        |
|  生成风格档案 (JSON)  +-----> |  注入 Writer Prompt    |
|                       |       |  (用于下一章生成)      |
+-----------------------+       +------------------------+
```

**流程详解：**

1.  用户在 UI 侧边栏上传或粘贴参考文本。
2.  `style_analyzer.py` 对文本进行分块（防止 Token 溢出）。
3.  调用 `Director` Agent 进行深度阅读，分析其叙事视角、句式特征、修辞偏好等。
4.  输出结构化的 JSON 风格档案（Style Profile）。
5.  该档案被注入到 `Writer` 的 Prompt 中，指导其进行模仿创作。

---

## 📂 项目结构

```
AI-Novel-Workshop/
├── app.py                  # Streamlit 主程序入口
├── engine.py               # 核心引擎，负责初始化 Crew 和 Memory
├── style_analyzer.py       # 风格分析逻辑
├── config/
│   └── llm.py              # LLM 模型配置与路由
├── crew/
│   ├── agents.py           # Agent 定义 (Director, Writer, Polisher...)
│   ├── tasks.py            # Task 定义 (Plan, Write, Polish...)
│   └── crew.py             # Crew 组装逻辑
├── workflow/
│   └── chapter_flow.py     # 章节生成的主控流程
├── memory/                 # 记忆系统 (Canon, Creative/RAG)
└── story_archive/          # 生成的章节存档
```
