import streamlit as st
import datetime
import os
import uuid
import html
import streamlit.components.v1 as components


# from your_main_logic import run_chapter, canon, creative  # 导入你的逻辑
from workflow.chapter_flow import run_chapter
from engine import get_initialized_memory, prepare_crew
from memory.creative import CreativeMemory
from memory.system import reset_all_data, save_canon
from memory.canon import CanonMemory
from memory.schema.timeline import CanonEvent


def copy_button(text: str, label: str = "📋 复制"):
    uid = f"copy_{uuid.uuid4().hex}"
    safe_text = html.escape(text)

    components.html(
        f"""
        <textarea id="{uid}" style="position:absolute; left:-9999px;">
        {safe_text}
        </textarea>

        <button
            id="btn_{uid}"
            onclick="copy_{uid}()"
            style="
                padding:6px 10px;
                font-size:14px;
                border-radius:6px;
                border:1px solid #ccc;
                cursor:pointer;
                background-color:#f9f9f9;
                transition: all 0.2s ease;
            "
        >
            {label}
        </button>

        <script>
        function copy_{uid}() {{
            var text = document.getElementById("{uid}");
            var btn = document.getElementById("btn_{uid}");

            text.select();
            document.execCommand("copy");

            // 成功态
            btn.innerHTML = "✔ 已复制";
            btn.style.backgroundColor = "#2ecc71";
            btn.style.borderColor = "#27ae60";
            btn.style.color = "white";
            btn.disabled = true;
        }}
        </script>
        """,
        height=42,
    )


# --- 页面配置 ---
st.set_page_config(page_title="AI 小说创作助手", layout="wide")

st.title("✍️ AI Novel Editor")
st.caption("基于 CrewAI + Qwen-Thinking 本地模型")


# --- 初始化持久化对象 ---
# 使用 st.cache_resource 确保 creative 模型只加载一次
@st.cache_resource
def get_creative_memory():
    return CreativeMemory(model_path=os.getenv("LOCAL_MODEL_DIR"))


creative = get_creative_memory()
# 每次运行 app.py 都会尝试加载最新的 canon

if "canon" not in st.session_state:
    st.session_state.canon = get_initialized_memory()

canon = st.session_state.canon
crew = prepare_crew(canon)


# --- 侧边栏：显示世界观设定 (Canon) ---
with st.sidebar:
    st.header("🌍 世界观设定")
    if st.button("刷新设定数据"):
        st.rerun()

    st.subheader("类型 & 规则")
    st.write(f"**题材:** {canon.world.genre}")
    st.write(f"**科技水平:** {canon.world.tech_level}")
    st.info("\n\n".join([f"• {r.name}: {r.description}" for r in canon.world.rules]))
    st.subheader("核心角色")
    for name, char in canon.characters.items():
        with st.expander(f"👤 {name}"):
            st.write(f"**性格:** {', '.join(char.core.personality)}")
            st.write(f"**动机:** {char.core.values}")
            st.write(
                f"**状态:** {char.state.location} | {'存活' if char.state.alive else '死亡'}"
            )

# --- 侧边栏：历史搜索功能 (添加在侧边栏底部) ---
with st.sidebar:
    st.divider()
    st.header("🔍 剧情百科检索")
    st.caption("基于 Nomic 向量模型检索深层记忆")

    # 搜索输入框
    search_query = st.text_input(
        "搜索历史伏笔或细节", placeholder="例如：某人的身世、那把断剑..."
    )

    if search_query:
        with st.spinner("正在翻阅记忆库..."):
            # 1. 调用你之前定义的 recall 方法
            # 如果你之前修改过 recall 让它返回元数据，这里可以按列表展示
            # 这里先按你最基础的 recall 返回字符串逻辑处理
            results = creative.recall(search_query, n_results=3)

            st.markdown("### 匹配的记忆片段")

            # 2. 这里的处理逻辑取决于你 recall 返回的格式
            # 建议将结果展示在 info 框或 expander 中
            if "【历史相关记录】" in results:
                # 提取历史记录部分（去除近期回顾，避免重复显示）
                history_part = (
                    results.split("【近期情节回顾】")[0]
                    .replace("【历史相关记录】：", "")
                    .strip()
                )

                if history_part:
                    st.info(history_part)
                else:
                    st.warning("未找到高度相关的历史记录。")
            else:
                st.warning("没有匹配到对应记录！")
                st.write(results)  # 兜底直接打印

    # 3. 记忆库统计信息（小组件）
    st.divider()
    if st.checkbox("查看记忆库状态"):
        try:
            count = creative.collection.count()
            st.write(f"📊 向量库碎片: {count} 条")
            st.write(f"🏠 短期窗口条数: {len(creative.working_context)}")
        except Exception as e:
            st.error("无法读取向量库状态")

# --- 主界面：创作控制 ---
col1, col2 = st.columns([3, 1])

with col2:
    st.subheader("操作面板")
    num_chapters = st.number_input("连续创作章节数", min_value=1, max_value=5, value=1)
    start_btn = st.button("开始创作下一章", type="primary")


with col1:
    # --- 1. 初始化反馈变量 ---
    # 检查是否有待处理的重写反馈
    pending_feedback = st.session_state.get("pending_feedback", None)

    # 触发条件：点击了开始按钮 OR 处于自动重写状态
    if start_btn or st.session_state.get("need_auto_run"):
        # 如果是自动重写，重置标志位
        if st.session_state.get("need_auto_run"):
            st.session_state.need_auto_run = False

        canon: CanonMemory = st.session_state.canon
        # 如果是重写，章节号不变；如果是新创作，章节号 +1
        current_chapter = (
            canon.meta.last_updated_chapter + 1
            if pending_feedback
            else (canon.meta.last_updated_chapter + 1)
        )

        status_label = (
            f"🔄 正在重写第 {current_chapter} 章..."
            if pending_feedback
            else f"🚀 正在创作第 {current_chapter} 章..."
        )

        with st.status(status_label, expanded=True) as status:
            st.write(
                "正在检索历史背景并注入反馈..."
                if pending_feedback
                else "正在检索历史背景与角色设定..."
            )

            # 调用修改后的 run_chapter，传入反馈
            chapter_text, check_results, memory_notes = run_chapter(
                crew, canon, creative, current_chapter, feedback=pending_feedback
            )

            st.write("正在临时存档...")

            # 物理存档（仅存正文文本，对象更新留到确认按钮）

            # 注意：这里我们先不更新 canon 的元数据，等用户点击“确认加载”再更新
            # 但为了预览，我们需要把结果存入临时状态
            st.session_state.temp_creation_result = {
                "chapter": current_chapter,
                "text": chapter_text,
                "check": check_results,
                "memory": memory_notes,
                "is_rewrite": True if pending_feedback else False,
            }

            # 清除已使用的反馈
            st.session_state.pending_feedback = None

            status.update(
                label=f"✅ 第 {current_chapter} 章生成完毕！",
                state="complete",
                expanded=False,
            )
        with st.expander("🧠 本章核心记忆点"):
            st.info(memory_notes)

    # --- 2. 结果展示与重写控制区 ---
    if (
        "temp_creation_result" in st.session_state
        and st.session_state.temp_creation_result
    ):
        res = st.session_state.temp_creation_result

        st.subheader(f"📖 第 {res['chapter']} 章内容预览")
        if res.get("is_rewrite"):
            st.info("✨ 这是根据逻辑反馈重写后的版本")

        st.write(res["text"])

        # 7. 展示本章提取的记忆笔记


        # 逻辑检查报告展示
        has_conflict = "未检测到设定冲突" not in res["check"]
        with st.expander("🔍 逻辑一致性检查报告", expanded=has_conflict):
            if has_conflict:
                st.warning(res["check"])
            else:
                st.success("检测通过：未发现明显逻辑冲突。")

        # 操作按钮
        c1, c2 = st.columns(2)
        with c1:
            if st.button(
                "📥 确认并同步到时间线", type="primary", use_container_width=True
            ):
                # 只有点确认时，才正式更新 canon 对象
                new_event = CanonEvent(
                    chapter=res["chapter"],
                    description=res["memory"],
                    involved_characters=["叶辰"],  # 建议后续从 res['memory'] 动态解析
                    event_type="plot",
                )
                # 如果是重写，先删除旧的同章节事件（如果有）
                st.session_state.canon.timeline = [
                    e
                    for e in st.session_state.canon.timeline
                    if e.chapter != res["chapter"]
                ]

                st.session_state.canon.timeline.append(new_event)
                st.session_state.canon.meta.last_updated_chapter = res["chapter"]
                save_canon(st.session_state.canon)

                st.session_state.temp_creation_result = None
                st.toast("数据已同步！")
                st.rerun()

        with c2:
            if st.button(
                "🔄 自动针对错误重写", type="secondary", use_container_width=True
            ):
                st.session_state.pending_feedback = res["check"]  # 把报错喂给下一次
                st.session_state.need_auto_run = True  # 开启自动运行标志
                st.rerun()

    # --- C. 初始状态提示 ---
    elif not start_btn:
        next_ch = st.session_state.canon.meta.last_updated_chapter + 1
        st.info(
            f"当前故事进度：已完成 {st.session_state.canon.meta.last_updated_chapter} 章。准备开始：第 {next_ch} 章。"
        )


# --- 底部：历史记录 ---
st.divider()
st.subheader("📜 故事时间线 (点击章节标题查看正文)")

# 倒序显示，最新章节在最上面
for event in reversed(canon.timeline):
    # 使用 expander 创建可点击的折叠块
    with st.expander(f"第 {event.chapter} 章: {event.description[:40]}..."):

        # 布局：左侧显示元数据，右侧显示操作
        col_info, col_action = st.columns([3, 1])

        with col_info:
            st.caption(
                f"📅 类型: {event.event_type} | 👥 角色: {', '.join(event.involved_characters)}"
            )

        # 尝试读取本地正文存档
        archive_path = f"story_archive/chapter_{event.chapter}.txt"

        if os.path.exists(archive_path):
            with open(archive_path, "r", encoding="utf-8") as f:
                saved_full_text = f.read()

            # 按钮布局
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown("#### 📖 章节原文")

            with c2:
                copy_button(saved_full_text)
            # 原文展示（保留）
            # st.code(saved_full_text)

            st.text_area(
                "内容预览", saved_full_text, height=300, key=f"txt_{event.chapter}"
            )
        else:
            # 如果没有全文，则展示提取的笔记（兜底逻辑）
            st.warning("未找到该章节的正文存档，显示记忆笔记：")
            st.info(event.description)

        # 也可以顺便显示向量库里的笔记
        # notes = creative.get_content_by_chapter(event.chapter) # 如果你写了这个方法


with st.sidebar:
    st.divider()
    with st.expander("🛠️ 系统管理"):
        confirm = st.checkbox("确认清空所有章节和记忆")
        if st.button("🔥 彻底删档", disabled=not confirm, use_container_width=True):
            try:
                # 执行清理逻辑
                reset_all_data(creative)

                # 清除 Session 状态
                st.session_state.clear()

                # 成功提示：绿色勾选图标，文字会自动变绿/正常色（取决于主题）
                st.toast("存档已彻底清空！", icon="✅")

                # 稍微延迟一下，让用户看清提示再刷新（可选，0.5-1秒）
                import time

                time.sleep(1)

                # 强制刷新
                st.rerun()

            except Exception as e:
                # 失败提示：红色警告图标
                st.toast(f"清除失败：{str(e)}", icon="🚨")
