from dotenv import load_dotenv

load_dotenv()
import streamlit as st
import os
import uuid
import html
import re
import json
import streamlit.components.v1 as components

from workflow.chapter_flow import run_chapter
from engine import get_initialized_memory, prepare_crew
from memory.system import reset_all_data, save_canon
from memory.schema.timeline import CanonEvent
from memory.schema.world import WorldRule
from memory.creative import CreativeMemory


@st.cache_resource
def get_creative_memory():
    return CreativeMemory(model_path=os.getenv("LOCAL_MODEL_DIR"))


def setup_page():
    st.set_page_config(page_title="AI 小说创作助手", layout="wide")
    st.title("✍️ AI Novel Editor")
    st.caption("基于 CrewAI + Qwen-Thinking 本地模型")


def init_memory():
    if "canon" not in st.session_state:
        st.session_state.canon = get_initialized_memory()

    if "creative" not in st.session_state:
        st.session_state.creative = get_creative_memory()

    if "crew" not in st.session_state:
        st.session_state.crew = prepare_crew(st.session_state.canon)


def render_sidebar_world():
    canon = st.session_state.canon

    with st.sidebar:
        st.header("🌍 世界观设定")
        if st.button("刷新设定数据"):
            st.rerun()

        st.subheader("类型 & 规则")
        st.write(f"**题材:** {canon.world.genre}")
        st.write(f"**科技水平:** {canon.world.tech_level}")

        if canon.world.rules:
            st.info(
                "\n\n".join(f"• {r.name}: {r.description}" for r in canon.world.rules)
            )
        else:
            st.caption("尚未定义世界运行规则")

        st.subheader("核心角色")
        for name, char in canon.characters.items():
            with st.popover(f"👤 {name}"):
                st.write(f"**性格:** {', '.join(char.core.personality)}")
                st.write(f"**动机:** {char.core.values}")
                st.write(
                    f"**状态:** {char.state.location} | {'存活' if char.state.alive else '死亡'}"
                )


def render_sidebar_search():
    creative = st.session_state.creative
    with st.sidebar:
        st.divider()
        st.header("🔍 剧情百科检索")

        # 1. 快速检索按钮放在上面（或者在下方点击后更新 state）
        st.caption("快速快捷键：")
        c1, c2, c3 = st.columns(3)

        # 定义一个简单的点击回调逻辑
        preset_query = ""
        if c1.button("📍 地点"):
            preset_query = "时空坐标"
        if c2.button("👥 角色"):
            preset_query = "角色更新"
        if c3.button("🔍 伏笔"):
            preset_query = "伏笔与名词"

        # 2. 搜索框：如果有预设值，则填入预设值
        # 注意：这里我们通过 key 手动触发，或者利用 value 绑定
        query = st.text_input(
            "搜索历史伏笔或细节",
            value=preset_query,  # 这里绑定了按钮触发的值
            key="wiki_search_input",
            placeholder="例如：黑雾谷",
        )

        # 3. 执行检索
        if query:
            hist, recent = creative.recall(query)

            if hist == "NO_MATCH":
                st.warning(f"🔍 库中没有关于 '{query}' 的确切记录")
                # 依然显示近期动态，方便用户参考
                with st.expander("🕒 查看近期参考", expanded=False):
                    st.write(recent)
            else:
                st.success(f"✅ 找到与 '{query}' 相关的线索")
                st.info(hist)


def render_main_editor():
    col1, col2 = st.columns([3, 1])

    with col2:
        # 放创作按钮、控制面板
        render_control_panel()
        # 在中控台下方插入世界观编辑器
        render_world_editor_below_control()
        # 角色管理器
        render_character_manager_below_control()

    with col1:
        render_story_flow()


def render_control_panel():
    st.subheader("⚙️ 创作中控台")

    canon = st.session_state.canon
    is_world_ready = bool(canon.world.genre.strip())
    is_hero_ready = len(canon.characters) > 0

    # 只保留这一个按钮逻辑
    if st.button(
        "🚀 开始创作下一章",
        type="primary",
        use_container_width=True,
        disabled=not (is_world_ready and is_hero_ready),
    ):
        # 显式开启创作开关
        st.session_state.trigger_generation = True
        st.rerun()  # 立即触发重绘以进入生成流程


def render_story_flow():
    canon = st.session_state.canon
    creative = st.session_state.creative
    crew = st.session_state.crew

    pending_feedback = st.session_state.get("pending_feedback")
    is_ready = canon.world.genre and canon.characters

    if not is_ready:
        st.warning("### 🌌 混沌初开，世界尚未定义")
        return

    # 修改判断逻辑：使用 trigger_generation 替代 start_btn
    should_run = st.session_state.get("trigger_generation") or st.session_state.get(
        "need_auto_run"
    )

    if should_run:
        # 【关键】立即关闭开关，防止同步数据后的下一次 rerun 再次进入此逻辑
        st.session_state.trigger_generation = False
        st.session_state.need_auto_run = False

        run_generation(canon, creative, crew, pending_feedback)
        st.rerun()  # 生成结束后刷新页面显示结果

    render_preview_and_actions()


def run_generation(canon, creative, crew, pending_feedback):
    current_chapter = canon.meta.last_updated_chapter + 1

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

        chapter_text, check_results, memory_notes = run_chapter(
            crew,
            canon,
            creative,
            current_chapter,
            feedback=pending_feedback,
        )

        chapter_text = clean_story_text_for_display(chapter_text)

        st.session_state.temp_creation_result = {
            "chapter": current_chapter,
            "text": chapter_text,
            "check": check_results,
            "memory": memory_notes,
            "is_rewrite": bool(pending_feedback),
        }

        st.session_state.pending_feedback = None

        status.update(
            label=f"✅ 第 {current_chapter} 章生成完毕！",
            state="complete",
            expanded=False,
        )


def clean_story_text_for_display(text: str) -> str:
    """
    用于 UI 展示的轻度清洗
    """
    # 去掉行首 Markdown 标题符
    text = re.sub(r"^\s*#+\s*", "", text, flags=re.MULTILINE)

    # 去除粗体 / 斜体标记
    text = re.sub(r"[*_]", "", text)

    # 压缩过多空行
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def render_preview_and_actions():
    res = st.session_state.get("temp_creation_result")
    if not res:
        return

    st.subheader(f"📖 第 {res['chapter']} 章内容预览")

    if res.get("is_rewrite"):
        st.info("✨ 这是根据逻辑反馈重写后的版本")

    st.write(res["text"])

    has_conflict = "未检测到设定冲突" not in res["check"]
    with st.expander("🔍 逻辑一致性检查报告", expanded=has_conflict):
        if has_conflict:
            st.warning(res["check"])
        else:
            st.success("检测通过：未发现明显逻辑冲突。")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 确认并同步到时间线", type="primary", use_container_width=True):
            confirm_chapter_to_canon(res)

    with col2:
        if st.button("🔄 自动针对错误重写", use_container_width=True):
            st.session_state.pending_feedback = res["check"]
            st.session_state.need_auto_run = True
            st.rerun()


def confirm_chapter_to_canon(res):
    canon = st.session_state.canon

    # 假设 res["memory"] 现在是 ChapterSummary 实例或对应的 dict
    memory_data = res["memory"]

    # 如果 memory_data 是字符串（AI 有时会返回字符串），则需要 json.loads
    if isinstance(memory_data, str):
        try:
            memory_data = json.loads(memory_data)
        except:
            # 兜底：如果解析失败，退回到之前的模糊匹配
            memory_data = {"summary": memory_data, "involved_characters": [""]}

    # 提取解析出的数据
    involved = memory_data.get("involved_characters", [""])

    char_status = (
        memory_data.get("char_update")
        or f"{', '.join(memory_data.get('involved_characters'))}：经历了本章事件"
    )
    plot_flow = memory_data.get("plot_chain") or f"发生事件：{memory_data.get('summary')}"

    rich_description = (
        f"### 📍 时空坐标\n"
        f"- {memory_data.get('locations')} | 章节时间点\n\n"
        f"### 👥 角色更新\n"
        f"- {char_status}\n\n"
        f"### ⚡ 剧情链条\n"
        f"1. {plot_flow}\n\n"
        f"### 🔍 伏笔与名词\n"
        f"- 名词：{memory_data.get('items')}"
    )

    # 创建正式的事件对象
    new_event = CanonEvent(
        chapter=res["chapter"],
        description=rich_description,  # 存入纯文本摘要
        involved_characters=involved,
        event_type="plot",
    )

    # 更新时间线
    canon.timeline = [e for e in canon.timeline if e.chapter != res["chapter"]]
    canon.timeline.append(new_event)
    canon.meta.last_updated_chapter = res["chapter"]

    # --- 进阶：自动更新角色位置 ---
    current_loc = memory_data.get("locations", [])
    if current_loc:
        for char_name in involved:
            if char_name in canon.characters:
                canon.characters[char_name].state.location = current_loc[0]

    save_canon(canon)

    # 状态清理
    st.session_state.temp_creation_result = None
    st.session_state.trigger_generation = False
    st.session_state.need_auto_run = False

    st.toast(f"✅ 同步成功！涉及角色：{', '.join(involved)}")
    st.rerun()


def render_timeline():
    st.divider()
    st.subheader("📜 故事时间线")

    canon = st.session_state.canon

    for event in reversed(canon.timeline):
        render_timeline_item(event)


def render_timeline_item(event):
    canon = st.session_state.canon

    archive_path = f"story_archive/chapter_{event.chapter}.txt"
    chapter_title = f"第 {event.chapter} 章"
    full_text = ""

    if os.path.exists(archive_path):
        with open(archive_path, "r", encoding="utf-8") as f:
            lines = strip_leading_blank_lines(f.readlines())
            if lines:
                potential_title = lines[0].strip()
                if "第" in potential_title and "章" in potential_title:
                    chapter_title = potential_title
                full_text = "".join(lines)

    with st.expander(f"📖 {chapter_title}"):
        st.caption(
            f"📅 类型: {event.event_type} | 👥 角色: {', '.join(event.involved_characters)}"
        )

        if full_text:
            col_l, col_r = st.columns([5, 1])
            with col_l:
                st.markdown("#### 📄 章节原文")
            with col_r:
                copy_button(full_text)

            st.text_area(
                "内容预览",
                value=full_text,
                height=350,
                key=f"area_{event.chapter}",
            )

            with st.popover("🧠 查看记忆审计详情"):
                st.write(event.description)
        else:
            st.warning("未找到正文存档。")
            st.info(event.description)


def strip_leading_blank_lines(lines: list[str]) -> list[str]:
    """
    仅移除文件开头的空行（含只有 \\n / 空白的行）
    """
    for i, line in enumerate(lines):
        if line.strip():
            return lines[i:]
    return []


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

            btn.innerHTML = "✔ 已复制";
            btn.style.backgroundColor = "#2ecc71";
            btn.style.color = "white";
            btn.disabled = true;
        }}
        </script>
        """,
        height=42,
    )


def render_system_panel():
    with st.sidebar:
        st.divider()
        with st.popover("🛠️ 系统管理"):
            render_reset_buttons()


def render_reset_buttons():
    creative = st.session_state.creative

    if st.button("♻️ 重置故事进度 (保留设定)", use_container_width=True):
        # 1. 物理清空 timeline
        st.session_state.canon.timeline = []

        # 2. 重置元数据
        st.session_state.canon.meta.last_updated_chapter = 0

        # 3. 如果你的 CanonMemory 类有专门的重置方法，调用它
        # st.session_state.canon.reset()

        # 4. 清除后端数据（向量库等）
        reset_all_data(creative)

        # 5. 立即持久化这个“空状态”到文件
        save_canon(st.session_state.canon)

        # 6. 清理所有临时的 session 变量
        keys_to_clear = [
            "temp_creation_result",
            "current_chapter_text",
            "last_check_result",
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]

        st.toast("故事已重置，世界观与角色已保留", icon="♻️")

        # 7. 强制 Streamlit 重新运行整个 script
        st.rerun()

    st.write("---")

    confirm = st.checkbox("确认清空所有数据（不可恢复）")
    if st.button(
        "🔥 彻底全清",
        disabled=not confirm,
        use_container_width=True,
        type="secondary",
    ):
        reset_all_data(creative)
        st.session_state.clear()
        st.toast("存档已彻底清空！", icon="✅")
        st.rerun()


def render_world_editor_below_control():
    """
    世界观编辑器，自动折叠逻辑：
    如果有题材和至少一个角色，则默认折叠
    """
    canon = st.session_state.canon

    # 判断是否折叠
    has_world = bool(canon.world.genre.strip())
    has_char = len(canon.characters) > 0
    should_collapse = has_world and has_char

    with st.expander("🌍 世界观设定", expanded=not should_collapse):
        # ---------- 基础设定 ----------
        canon.world.genre = st.text_input(
            "题材", value=canon.world.genre, key="world_genre"
        )

        tech_options = ["凡俗", "低武", "修真", "高武", "仙侠"]
        current_tech = canon.world.tech_level
        if current_tech not in tech_options:
            current_tech = tech_options[0]

        canon.world.tech_level = st.selectbox(
            "科技 / 修真水平",
            tech_options,
            index=tech_options.index(current_tech),
            key="world_tech",
        )

        # ---------- 世界规则 ----------
        st.markdown("**世界规则**")
        if not canon.world.rules:
            st.caption("尚未定义世界运行规则")

        for i, rule in enumerate(canon.world.rules):
            with st.container():  # 这里用 container 替代 expander
                st.text_input("规则名", value=rule.name, key=f"rule_name_{i}")
                st.text_area(
                    "描述", value=rule.description, key=f"rule_desc_{i}", height=80
                )

        if st.button("➕ 添加规则", use_container_width=True):
            from memory.schema.world import WorldRule

            canon.world.rules.append(WorldRule(name="", description=""))
            st.rerun()


def render_character_manager_below_control():
    """
    角色管理器，自动折叠逻辑：
    如果有题材和至少一个角色，则默认折叠
    """
    canon = st.session_state.canon

    has_world = bool(canon.world.genre.strip())
    has_char = len(canon.characters) > 0
    should_collapse = has_world and has_char

    with st.expander("👤 角色管理器", expanded=not should_collapse):
        char_names = list(canon.characters.keys())
        main_char = char_names[0] if char_names else None  # 默认第一个为主角

        if not char_names:
            st.caption("当前没有角色，请添加新角色")
            selected_name = None
        else:
            selected_name = st.selectbox(
                "选择要编辑的角色", char_names, key="selected_char"
            )

        # 编辑表单
        if selected_name:
            char = canon.characters[selected_name]

            st.text_input("姓名", value=char.core.name, key="char_name")
            st.selectbox(
                "性别",
                options=["男", "女", "不明"],
                index=["男", "女", "不明"].index(char.core.gender),
                key="char_gender",
            )
            st.text_area(
                "性格标签 (逗号隔开)",
                value=",".join(char.core.personality),
                key="char_personality",
            )
            st.text_area(
                "价值观/动机 (逗号隔开)",
                value=",".join(char.core.values),
                key="char_values",
            )
            st.text_area(
                "内心恐惧 (逗号隔开)", value=",".join(char.core.fears), key="char_fears"
            )
            st.text_input("当前位置", value=char.state.location, key="char_location")
            st.checkbox("存活", value=char.state.alive, key="char_alive")

            # 保存角色
            if st.button("💾 保存角色修改", use_container_width=True):
                from memory.schema.character import (
                    Character,
                    CharacterCore,
                    CharacterState,
                )

                updated_char = Character(
                    core=CharacterCore(
                        name=st.session_state.char_name,
                        gender=st.session_state.char_gender,
                        personality=[
                            p.strip()
                            for p in st.session_state.char_personality.split(",")
                            if p
                        ],
                        values=[
                            v.strip()
                            for v in st.session_state.char_values.split(",")
                            if v
                        ],
                        fears=[
                            f.strip() for f in st.session_state.char_fears.split(",") if f
                        ],
                    ),
                    state=CharacterState(
                        location=st.session_state.char_location,
                        alive=st.session_state.char_alive,
                        physical_status=["完好"],
                        mental_status=["冷静"],
                    ),
                    first_appearance_chapter=canon.meta.last_updated_chapter,
                )

                canon.characters[updated_char.core.name] = updated_char
                st.session_state.canon = canon
                from memory.system import save_canon

                save_canon(canon)
                st.success(f"角色 {updated_char.core.name} 已保存")
                st.rerun()

            # 删除配角
            if selected_name != main_char:
                if st.button(f"🗑 删除角色 {selected_name}", use_container_width=True):
                    del canon.characters[selected_name]
                    st.session_state.canon = canon
                    from memory.system import save_canon

                    save_canon(canon)
                    st.success(f"角色 {selected_name} 已删除")
                    st.rerun()
            else:
                st.info("⭐ 主角无法删除")

        # 添加新角色
        st.markdown("---")
        st.info("添加新角色")
        new_name = st.text_input("新角色姓名", key="new_char_name")
        if st.button("➕ 添加角色"):
            if not new_name.strip():
                st.warning("姓名不能为空")
            elif new_name in canon.characters:
                st.warning("该角色已存在")
            else:
                from memory.schema.character import (
                    Character,
                    CharacterCore,
                    CharacterState,
                )

                canon.characters[new_name] = Character(
                    core=CharacterCore(
                        name=new_name,
                        gender="男",
                        personality=[],
                        values=[],
                        fears=[],
                    ),
                    state=CharacterState(
                        location="起始点",
                        alive=True,
                        physical_status=["完好"],
                        mental_status=["冷静"],
                    ),
                    first_appearance_chapter=canon.meta.last_updated_chapter,
                )
                st.session_state.canon = canon
                from memory.system import save_canon

                save_canon(canon)
                st.success(f"角色 {new_name} 已添加")
                st.rerun()


def main():
    setup_page()
    init_memory()

    # 页面布局
    render_sidebar_world()
    render_sidebar_search()
    render_main_editor()

    render_timeline()
    render_system_panel()


if __name__ == "__main__":
    main()
