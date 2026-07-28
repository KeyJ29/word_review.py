import streamlit as st
import json
import random
from io import BytesIO

# ========== 云端持久化存储（刷新页面不丢失词库） ==========
if "word_libs" not in st.session_state:
    # 初始化空词库
    st.session_state.word_libs = {}
if "current_lib" not in st.session_state:
    st.session_state.current_lib = None
if "current_word" not in st.session_state:
    st.session_state.current_word = None
if "show_answer" not in st.session_state:
    st.session_state.show_answer = False
if "review_mode" not in st.session_state:
    st.session_state.review_mode = "英译中文"

# ========== 词库操作函数 ==========
def get_all_libs():
    return list(st.session_state.word_libs.keys())

def load_lib(name):
    return st.session_state.word_libs.get(name, [])

def save_lib(name, data):
    st.session_state.word_libs[name] = data

# 加权随机抽取单词（生疏词更容易出现）
def pick_word(word_list):
    if not word_list:
        return None
    weight_list = []
    for w in word_list:
        weight = 3 if w["is_hard"] else 1
        weight_list.extend([w]*weight)
    return random.choice(weight_list)

# ========== 页面布局 ==========
st.set_page_config(page_title="单词抽背工具", layout="wide")
st.title("📖 单词抽背小程序")

# 侧边栏
with st.sidebar:
    st.header("📚 词库管理")
    lib_list = get_all_libs()
    st.session_state.current_lib = st.selectbox("选择词库", lib_list) if lib_list else None

    new_lib_name = st.text_input("新建词库名称")
    if st.button("创建新词库") and new_lib_name.strip():
        if new_lib_name not in get_all_libs():
            save_lib(new_lib_name, [])
            st.success("创建成功！刷新页面")
            st.rerun()

if not st.session_state.current_lib:
    st.info("请先在左侧新建词库！")
    st.stop()

words = load_lib(st.session_state.current_lib)

tab1, tab2, tab3, tab4 = st.tabs(["🎴开始背诵", "➕添加单词", "📥导入/导出", "📊数据统计"])

# 背诵页面
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.review_mode = st.radio("背诵模式", ["英译中文", "中译英文"])

    if st.button("🔀 抽取下一个单词", use_container_width=True):
        st.session_state.current_word = pick_word(words)
        st.session_state.show_answer = False

    word = st.session_state.current_word
    if word is None:
        st.warning("点击上方按钮抽取单词")
    else:
        if st.session_state.review_mode == "英译中文":
            st.subheader(f"【单词】{word['en']}")
        else:
            st.subheader(f"【释义】{word['cn']}")

        if st.button("👁️ 显示/隐藏答案"):
            st.session_state.show_answer = not st.session_state.show_answer

        if st.session_state.show_answer:
            if st.session_state.review_mode == "英译中文":
                st.info(f"释义：{word['cn']}")
            else:
                st.info(f"单词：{word['en']}")

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("✅记住了"):
                word["wrong"] = max(word["wrong"]-1, 0)
                save_lib(st.session_state.current_lib, words)
        with c2:
            if st.button("❌没记住"):
                word["wrong"] += 1
                save_lib(st.session_state.current_lib, words)
        with c3:
            if st.button("⭐切换生疏标记"):
                word["is_hard"] = not word["is_hard"]
                save_lib(st.session_state.current_lib, words)

# 添加单词
with tab2:
    st.subheader("手动录入单词")
    en_text = st.text_input("英文单词")
    cn_text = st.text_input("中文释义")
    if st.button("保存单词"):
        if en_text and cn_text:
            words.append({
                "en": en_text.strip(),
                "cn": cn_text.strip(),
                "is_hard": False,
                "wrong": 0
            })
            save_lib(st.session_state.current_lib, words)
            st.success("添加成功！")
            st.rerun()

# 导入导出
with tab3:
    st.markdown("导入格式：每行 `英文|中文`")
    upload_file = st.file_uploader("上传txt文件")
    if upload_file:
        content = upload_file.read().decode("utf-8")
        lines = content.splitlines()
        cnt = 0
        for line in lines:
            if "|" in line:
                en, cn = line.split("|", 1)
                words.append({"en":en.strip(), "cn":cn.strip(), "is_hard":False, "wrong":0})
                cnt +=1
        save_lib(st.session_state.current_lib, words)
        st.success(f"成功导入{cnt}个单词")

    export_txt = "\n".join([f"{w['en']}|{w['cn']}" for w in words])
    buf = BytesIO(export_txt.encode("utf-8"))
    st.download_button("📤导出全部单词TXT", buf, file_name=f"{st.session_state.current_lib}.txt")

# 统计页面
with tab4:
    hard_list = [w for w in words if w["is_hard"]]
    wrong_list = [w for w in words if w["wrong"] > 0]
    st.write(f"总单词：{len(words)}｜⭐生疏单词：{len(hard_list)}｜❌有错题：{len(wrong_list)}")
    if len(wrong_list) > 0:
        st.subheader("错题列表")
        for item in wrong_list:
            st.write(f"{item['en']} — {item['cn']}  答错次数：{item['wrong']}")
