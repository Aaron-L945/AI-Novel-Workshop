from dotenv import load_dotenv

load_dotenv()
import streamlit as st
import os
import uuid
import html
import re
import streamlit.components.v1 as components

from workflow.chapter_flow import run_chapter
from engine import get_initialized_memory, prepare_crew
from memory.creative import CreativeMemory
from memory.system import reset_all_data, save_canon
from memory.canon import CanonMemory
from memory.schema.timeline import CanonEvent


def remove_leading_newlines(text_list):
    """
    去掉列表开头连续的换行符或空字符串
    """
    i = 0
    while i < len(text_list) and text_list[i].strip() == "":
        i += 1
    return text_list[i:]


def clean_story_text(text: str) -> str:
    # 1. 去除 Markdown 标题符 (###)
    text = re.sub(r"#+\s?", "", text)
    # 2. 去除粗体和斜体 (* 或 _)
    text = re.sub(r"[*_]", "", text)
    # 3. 去除多余的空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


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


def update_character(old_name, new_data):
    """更新角色信息"""
    for i, char in enumerate(st.session_state.canon.characters):
        if char.name == old_name:
            st.session_state.canon.characters[i] = new_data
            break
    save_canon(st.session_state.canon)


def delete_character_logic(name):
    """从字典中彻底删除角色并存档"""
    if name in st.session_state.canon.characters:
        # 1. 从内存删除
        st.session_state.canon.characters.pop(name)
        # 2. 同步到硬盘
        save_canon(st.session_state.canon)
        return True
    return False


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
    # 增加判断，防止 rules 为空
    if canon.world.rules:
        st.info("\n\n".join([f"• {r.name}: {r.description}" for r in canon.world.rules]))
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
    st.subheader("⚙️ 创作中控台")

    # --- 基础状态检查 ---
    is_world_ready = bool(canon.world.genre.strip())
    is_hero_ready = len(canon.characters) > 0

    # --- 1. 核心控制按钮 ---
    start_btn = st.button(
        "🚀 开始创作下一章",
        type="primary",
        use_container_width=True,
        disabled=not (is_world_ready and is_hero_ready),
    )
    if not (is_world_ready and is_hero_ready):
        st.caption("⚠️ 需完善下方 [世界观] 与 [主人翁] 设定以激活")

    st.divider()

    with st.expander("🌍 世界观架构", expanded=not is_world_ready):
        # 使用 session_state 预存表单值，避免刷新丢失
        with st.form("world_settings_form"):
            # 绑定 key，Streamlit 会自动处理缓存
            c_genre = st.text_input(
                "故事题材",
                value=canon.world.genre,
                key="input_genre",
                placeholder="如：凡人流仙侠...",
            )
            c_tech = st.text_input(
                "科技/文明等级", value=canon.world.tech_level, key="input_tech"
            )
            c_magic = st.text_area(
                "力量体系", value=canon.world.magic_system, key="input_magic"
            )

            # 规则列表同理
            existing_rules = "\n".join(
                [f"{r.name}:{r.description}" for r in canon.world.rules]
            )
            c_rules_raw = st.text_area(
                "规则列表(格式<名称：描述>)", value=existing_rules, key="input_rules"
            )

            if st.form_submit_button("💾 保存设定"):
                # 这里的逻辑保持不变，点击后持久化到 canon.json
                from memory.schema.world import WorldRule

                canon.world.genre = c_genre
                canon.world.tech_level = c_tech
                canon.world.magic_system = c_magic

                # 解析规则
                new_rules = []
                for line in c_rules_raw.split("\n"):
                    if ":" in line:
                        name, desc = line.split(":", 1)
                        new_rules.append(
                            WorldRule(name=name.strip(), description=desc.strip())
                        )
                    else:
                        st.toast("规则格式错误！")
                canon.world.rules = new_rules
                st.session_state.canon = canon
                save_canon(canon)
                st.toast("存档成功！", icon="💾")

    with st.expander("👤 角色库全域管理", expanded=is_world_ready and not is_hero_ready):
        # --- 第一部分：角色资产清单 (只读展示 + 删除) ---
        if canon.characters:
            st.markdown("##### 当前角色清单")
            for name, char in list(canon.characters.items()):
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 3, 1])
                    with c1:
                        st.markdown(f"**{name}**")
                        # 📍 不换行处理
                        st.markdown(f'<div style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:0.8rem;color:gray;">📍 {char.state.location}</div>', unsafe_allow_html=True)
                    with c2:
                        tags = char.core.personality[:3]
                        st.markdown(" ".join([f"`{t}`" for t in tags]))
                    with c3:
                        if list(canon.characters.keys()).index(name) != 0:
                            if st.button("🗑️", key=f"del_{name}"):
                                delete_character_logic(name)
                                st.rerun()
                        else:
                            st.caption("⭐主角")

        st.divider()

        # --- 第二部分：角色操作表单 (新增 & 修改合一) ---
        st.markdown("##### 角色编辑器")
        mode = st.radio("当前动作", ["加入新角色", "修改已有角色"], horizontal=True, key="char_mode_v2")

        char_names = list(canon.characters.keys())

        # 统一使用这一个表单
        with st.form("char_mgmt_form_unified", clear_on_submit=True):
            if mode == "修改已有角色" and char_names:
                selected_name = st.selectbox("选择要修改的角色", char_names)
                target_char = canon.characters[selected_name]
                
                # 初始值绑定已有数据
                t_name = selected_name
                t_per = ",".join(target_char.core.personality)
                t_val = ",".join(target_char.core.values)
                t_fear = ",".join(target_char.core.fears)
                t_loc = target_char.state.location
                t_gender = target_char.core.gender
            else:
                # 新增模式初始值
                t_name = st.text_input("角色姓名*", placeholder="例如：赵明轩")
                t_per = ""
                t_val = ""
                t_fear = ""
                t_loc = "起始点"
                t_gender = "男"

            # 共有编辑输入区
            c_per = st.text_input("性格标签 (逗号隔开)", value=t_per)
            c_val = st.text_input("价值观/动机", value=t_val)
            c_fear = st.text_input("内心恐惧", value=t_fear)
            
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                c_gender = st.selectbox("性别", ["男", "女", "不明"], 
                                      index=(["男", "女", "不明"].index(t_gender) if mode == "修改已有角色" else 0))
            with f_col2:
                c_loc = st.text_input("当前位置", value=t_loc)

            # 唯一的提交按钮
            if st.form_submit_button("🔥 同步并存入记忆", use_container_width=True):
                if not t_name:
                    st.error("姓名是必填项")
                else:
                    from memory.schema.character import Character, CharacterCore, CharacterState
                    new_char = Character(
                        core=CharacterCore(
                            name=t_name,
                            gender=c_gender,
                            personality=[p.strip() for p in c_per.split(",") if p],
                            values=[v.strip() for v in c_val.split(",") if v],
                            fears=[f.strip() for f in c_fear.split(",") if f],
                        ),
                        state=CharacterState(location=c_loc, physical_status=["完好"], mental_status=["冷静"]),
                        first_appearance_chapter=canon.meta.last_updated_chapter
                    )
                    st.session_state.canon.characters[t_name] = new_char
                    save_canon(st.session_state.canon)
                    st.success(f"角色 {t_name} 数据已同步")
                    st.rerun()



with col1:
    # --- 1. 初始化反馈变量 ---
    # 检查是否有待处理的重写反馈
    pending_feedback = st.session_state.get("pending_feedback", None)

    # 检查世界观是否已定义，且是否至少有一个角色
    is_world_ready = bool(canon.world.genre.strip())
    is_hero_ready = len(canon.characters) > 0

    if not is_world_ready or not is_hero_ready:
        # with col1:
        st.warning("### 🌌 混沌初开，世界尚未定义")
        st.info(
            "请在右侧面板完成以下操作以开启故事：\n1. 确立世界观题材 \n2. 创造你的主人翁"
        )
    else:
        # 正常显示创作按钮和正文预览
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

                # 正文清洗
                chapter_text = clean_story_text(chapter_text)

                st.write("正在临时存档...")

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
                f"当前故事进度：\n\t已完成 {st.session_state.canon.meta.last_updated_chapter} 章。\n\t准备开始：第 {next_ch} 章。"
            )


# --- 底部：历史记录 ---
st.divider()
st.subheader("📜 故事时间线 (点击章节标题查看正文)")

# 倒序显示，最新章节在最上面
for event in reversed(canon.timeline):
    # 1. 尝试从文件获取真实标题
    archive_path = f"story_archive/chapter_{event.chapter}.txt"
    chapter_title = f"第 {event.chapter} 章"  # 默认名
    full_text = ""

    if os.path.exists(archive_path):
        with open(archive_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                # 检查第一行是否是标题格式
                lines = remove_leading_newlines(lines)
                potential_title = lines[0].strip()
                if potential_title:
                    if "第" in potential_title and "章" in potential_title:
                        chapter_title = potential_title
                full_text = "".join(lines)

    # 2. 【核心】这里是唯一的 expander 层级
    with st.expander(f"📖 {chapter_title}"):

        # 显示元数据
        st.caption(
            f"📅 类型: {event.event_type} | 👥 角色: {', '.join(event.involved_characters)}"
        )

        if full_text:
            # 按钮区
            col_left, col_right = st.columns([5, 1])
            with col_left:
                st.markdown("#### 📄 章节原文")
            with col_right:
                copy_button(full_text)

            # 正文区
            st.text_area(
                label="内容预览", value=full_text, height=350, key=f"area_{event.chapter}"
            )

            # --- 关键修改：用 Popover 或 Divider 替换 Expander ---
            # 方案：使用 popover（这不会触发嵌套异常）
            with st.popover("🧠 查看记忆审计详情"):
                st.markdown("##### 本章结构化提取结果")
                st.write(event.description)
        else:
            # 兜底：无文件时显示
            st.warning("未找到正文存档。")
            st.info(f"**记忆笔记：**\n\n{event.description}")

with st.sidebar:
    st.divider()
    with st.popover("🛠️ 系统管理"):
        # --- 选项 A：软重置（保留世界观） ---
        if st.button("♻️ 重置故事进度 (保留设定)", use_container_width=True):
            # 1. 只清空剧情相关的部分
            st.session_state.canon.timeline = []  # 清空时间线
            st.session_state.canon.meta.last_updated_chapter = 0  # 章节归零

            # 2. 清空向量库（建议执行，否则旧剧情的伏笔会被检索出来干扰新剧情）
            reset_all_data(creative)  # 这里的具体方法取决于你 CreativeMemory 的实现

            # 3. 保存到硬盘
            save_canon(st.session_state.canon)

            # 4. 清除预览缓存
            if "temp_creation_result" in st.session_state:
                del st.session_state.temp_creation_result

            st.toast("故事已重置，世界观与角色已保留", icon="♻️")
            st.rerun()

        st.write("---")

        # --- 选项 B：硬重置（彻底删档） ---
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
            import time

            time.sleep(1)
            st.rerun()
