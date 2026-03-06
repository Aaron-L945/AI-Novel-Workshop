# 🤖 AI Novel Assistant - 智能小说创作助手

一个基于多智能体协作的AI小说创作平台，通过CrewAI框架协调多个AI智能体，帮助作者高效创作逻辑严谨、风格统一的长篇小说。

## 🌟 核心功能

### ✍️ 智能章节生成
- **多智能体协作**：导演、作家、润色师、检查员四个AI智能体协同工作
- **上下文感知**：自动检索历史剧情和角色设定，确保故事连贯性
- **逻辑一致性检查**：每章生成后自动检查与世界观的一致性
- **风格模仿**：支持上传参考文本，AI将模仿其写作风格

### 🌍 世界观管理
- **可视化设定**：直观的界面管理题材、科技水平、世界规则
- **角色档案**：详细记录每个角色的性格、动机、状态变化
- **时间线追踪**：自动维护故事发展时间线，方便回顾剧情
- **向量记忆库**：基于ChromaDB的剧情百科，支持语义搜索

### 📚 参考资料集成
- **多格式支持**：支持文本粘贴和PDF文件上传
- **风格分析**：自动分析参考文本的写作特征
- **临时参考**：为单次创作提供临时背景资料
- **智能检索**：快速查找历史伏笔和设定细节

## 🚀 快速开始

### 方式一：Docker 一键部署（推荐）

1. **配置环境变量**
   在项目根目录下创建 `.env` 文件，并根据您选择的 LLM 类型进行配置：

   **使用阿里云通义千问 (Qwen)**
   ```bash
   export QWEN_API_KEY=""
   export QWEN_MODEL=qwen-long # long is a think model
   export QWEN_MODEL_2=qwen-flash # flash is a quick model
   export LLM_TYPE=qwen
   ```

   **使用 OpenAI API**
   ```bash
   export OPENAI_API_BASE=""
   export OPENAI_MODEL_NAME=""
   export OPENAI_API_KEY=""
   export LLM_TYPE=openai
   ```

2. **启动服务**
   ```bash
   docker-compose up -d
   ```

3. **访问应用**
   浏览器访问：`http://localhost:8501`

### 方式二：本地源码部署

### 环境要求
- Python 3.8+
- 8GB+ 内存（建议16GB）
- 10GB+ 可用磁盘空间

### 安装步骤

1. **克隆项目**
```bash
git clone <项目地址>
cd AI-Novel-Workshop
```

2. **创建虚拟环境**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置API密钥**
编辑 `.env` 文件，根据您选择的 LLM 类型添加您的API密钥：

**使用阿里云通义千问（推荐）**
```bash
export QWEN_API_KEY=your_qwen_api_key_here
export LLM_TYPE=qwen
```

**使用 OpenAI API**
```bash
export OPENAI_API_KEY=your_openai_api_key_here
export LLM_TYPE=openai
```

5. **启动应用**
```bash
streamlit run app.py
```

6. **访问应用**
打开浏览器访问：`http://localhost:8501`

## 页面预览
### 左边栏
<img width="411" height="897" alt="image" src="https://github.com/user-attachments/assets/dda1537c-e389-4f97-b70a-07598267c51c" />
<img width="429" height="900" alt="eefbdbd74d960ab13e52f6142d78c40d" src="https://github.com/user-attachments/assets/7018b921-9fe4-4ef9-935f-14a39737713b" />

### 中部区域
<img width="966" height="579" alt="9a3d3df656a948b449e18b12158b8568" src="https://github.com/user-attachments/assets/b8d2b272-23a0-47d4-bcae-9a3ab04ef0f6" />
<img width="987" height="327" alt="8dd210027cc762dcf0ab15b656bcd8c6" src="https://github.com/user-attachments/assets/ac72b0bc-90a4-4355-aa1a-d07375c6938f" />
<img width="573" height="764" alt="image" src="https://github.com/user-attachments/assets/4e24c81f-35c9-4c69-bc21-de7cd26f6eb8" />

### 右边栏
<img width="372" height="567" alt="067c30bf59bc6675fe280864117be165" src="https://github.com/user-attachments/assets/f6989d07-68da-4729-a5e5-78ec81f27c6a" />


## 📖 使用指南

### 第一步：设定世界观
1. 在右侧"世界观设定"面板中：
   - 选择题材（仙侠、科幻、玄幻等）
   - 设定科技/修真水平
   - 添加世界运行规则

### 第二步：创建角色
1. 在"角色管理器"中添加主要角色：
   - 设定姓名、性别、性格特征
   - 定义价值观和内心恐惧
   - 设置初始位置和状态

### 第三步：开始创作
1. 点击"开始创作下一章"按钮
2. 等待AI智能体协作完成（约1-3分钟）
3. 预览生成的章节内容
4. 查看逻辑一致性检查报告
5. 确认无误后点击"同步到时间线"

### 进阶功能 (左边栏)
- **风格模仿**：上传参考文本，AI将学习其写作风格
- **剧情检索**：使用"剧情百科检索"查找历史细节
- **重写功能**：如发现逻辑问题，可自动重写章节
- **参考资料**：为特定章节添加临时背景资料

## 🛠️ 技术架构

### 核心组件
- **CrewAI**: 多智能体编排框架
- **Streamlit**: 用户界面框架
- **ChromaDB**: 向量数据库用于记忆存储
- **Qwen/OpenAI**: 大语言模型提供推理能力
- **Sentence Transformers**: 文本嵌入模型 (使用 nomic-ai/nomic-embed-text-v1.5)

### 智能体分工
- **导演(Director)**: 制定章节大纲，规划剧情发展
- **作家(Writer)**: 根据大纲撰写初稿，可模仿指定风格
- **润色师(Polisher)**: 深度润色，去除AI痕迹，增强文学性
- **检查员(Checker)**: 检查逻辑一致性，确保世界观统一
- **管理员(Curator)**: 提取关键信息，更新记忆库

## 💡 使用技巧

### 获得更好效果
1. **详细的世界观设定**：越详细的世界规则，AI越容易保持一致性
2. **丰富的角色档案**：完整的角色设定让AI创作更生动
3. **合理的章节长度**：建议每章1000-2000字，过长可能影响质量
4. **及时检查反馈**：每次生成后检查逻辑报告，及时修正问题

### 风格模仿
- 上传与目标风格相似的文本片段（1000字以上效果最佳）
- 可以上传多个不同风格的文本，AI会综合学习
- 风格档案会在后续章节中持续应用，直到重新分析

### 记忆管理
- 向量记忆库会自动积累剧情信息
- 使用"剧情百科检索"快速查找历史细节
- 定期检查和清理不需要的记忆条目

## 🔧 常见问题

### Q: 生成速度很慢怎么办？
A: 这是正常现象，因为需要多个AI智能体协作。可以尝试：
- 使用更快的模型（如qwen-flash）
- 减少参考资料的长度
- 在`.env`中切换到更快的API端点

### Q: 生成的内容不符合预期？
A: 建议：
- 检查世界观设定是否完整
- 确认角色设定是否详细
- 尝试添加更多参考资料
- 使用风格分析功能指定写作风格

### Q: 如何保存创作进度？
A: 系统会自动保存：
- 世界观设定到`canon_storage.json`
- 章节内容到`story_archive/`目录
- 记忆向量到`novel_memory/`目录

## 📄 项目结构
```
AI-Novel-Workshop/
├── app.py                  # 主程序入口
├── engine.py               # 核心引擎
├── style_analyzer.py       # 风格分析
├── requirements.txt        # 依赖列表
├── .env                    # 环境配置
├── config/
│   └── llm.py             # 模型配置
├── crew/                   # 智能体定义
│   ├── agents.py          # 智能体角色
│   ├── tasks.py           # 任务定义
│   └── crew.py            # 智能体编排
├── workflow/               # 工作流
│   └── chapter_flow.py    # 章节生成流程
├── memory/                 # 记忆系统
│   ├── canon.py           # 世界观记忆
│   ├── creative.py        # 创作记忆
│   └── schema/            # 数据结构定义
├── story_archive/          # 章节存档
├── novel_memory/           # 向量记忆库
└── models/                 # 本地模型

```

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- CrewAI团队提供的优秀多智能体框架
- 通义千问团队提供的强大语言模型
- Streamlit团队提供的简洁UI框架

## 联系作者：
- Email： lxybecomerich@163.com
- VX:     lxybecomerich
---

**Happy Writing! 🎉 让AI成为你创作路上的得力助手！**
