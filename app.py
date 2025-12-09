import streamlit as st
import calculation
from openai import OpenAI
import uuid
from geopy.geocoders import Nominatim
import city_data
from datetime import date # 👈 【新增】引入日期库

# ==========================================
# 0. 页面配置 & 隐藏菜单
# ==========================================
st.set_page_config(page_title="天命人类图AI+", page_icon="🔮")

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ==========================================
# 1. 配置 DeepSeek API
# ==========================================
try:
    api_key = st.secrets["DEEPSEEK_API_KEY"]
except (FileNotFoundError, KeyError):
    st.warning("⚠️ 未检测到密钥配置，请在 .streamlit/secrets.toml 中配置 DEEPSEEK_API_KEY")
    st.stop()

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# ==========================================
# 2. 定义功能函数
# ==========================================
def chat_with_deepseek(messages):
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=messages,
            stream=True,
            temperature=1.3 
        )
        return response
    except Exception as e:
        st.error(f"连接 AI 出错: {e}")
        return None

def get_coordinates(city_name):
    clean_name = city_name.strip().lower()
    if clean_name in city_data.CHINA_CITIES:
        return city_data.CHINA_CITIES[clean_name]

    try:
        geolocator = Nominatim(user_agent="my_hd_app_v13_datefix", timeout=5)
        location = geolocator.geocode(city_name)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except Exception:
        return None, None

# ==========================================
# 3. 初始化状态
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chart_calculated" not in st.session_state:
    st.session_state.chart_calculated = False

if "system_prompt_content" not in st.session_state:
    st.session_state.system_prompt_content = ""

# ==========================================
# 4. 网页界面布局
# ==========================================
st.title("🔮 天命人类图AI+")

# --- A. 先展示历史聊天记录 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- B. 输入区域 ---
with st.expander("📝 输入/修改 出生信息", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("你的名字", "Wanye")
        
        # 👈 【修改点】设置日期范围
        # min_value: 允许最早选到 1900年
        # max_value: 最晚选到今天
        # value: 默认显示 1995年 (方便用户调节)
        birth_date = st.date_input(
            "出生日期", 
            value=date(1995, 1, 1), 
            min_value=date(1900, 1, 1), 
            max_value=date.today()
        )
        
    with col2:
        city = st.text_input("出生城市 (中文/拼音)", "北京")
        birth_time = st.time_input("出生时间")

    # 点击按钮触发逻辑
    if st.button("🚀 生成盘面并深度解读", type="primary"):
        with st.spinner('正在连接宇宙能量库，生成深度报告...'):
            # 1. 获取经纬度
            lat, lon = get_coordinates(city)
            if lat is None:
                st.warning(f"⚠️ 找不到城市 '{city}'，已使用默认坐标 (北京)。")
                lat, lon = 39.9042, 116.4074

            # 2. 计算人类图
            chart_data = calculation.get_chart_data(birth_date, birth_time, lat, lon)

            # 3. 构建 System Prompt
            st.session_state.system_prompt_content = f"""
# 角色 (Role)
你叫“活活 (Huohuo)”，一位资深且温暖的人类图分析师。
你的特长是将冰冷的参数转化为直击灵魂的生命故事。

# 核心指令 (Core Instruction)
**你必须掌握对话的主动权。**
在每次回复的最后，**必须**抛出一个具有引导性的**反问句**，诱导用户继续深入探索，绝不让对话在你的回合结束。

# 回复逻辑 (Workflow)
## 第一阶段：深度首秀 (The Grand Opening)
**当对话开始时**，直接输出一份 **600字左右** 的综合解读，包含：
1.  **能量致意**：呼唤名字，连接 {city} 的出生地能量场。
2.  **核心画像（类型+人生角色）**：用比喻将两者结合。
3.  **光之天赋（意识太阳）**：解析【意识太阳闸门】的最强天赋。
4.  **暗之动力（潜意识太阳）**：点出内在驱动力。
5.  **灵魂拷问**：抛出一个直击痛点的反思问题。

## 第二阶段：后续互动
* 保持短小精悍，每次必须追问具体生活场景。

---
# 用户实时数据
- 姓名：{name}
- 城市：{city}
- 类型：{chart_data['type']}
- 人生角色：{chart_data['profile']}
- 意识太阳：{chart_data['activations']['Sun (个性黑)']['text']}
- 意识地球：{chart_data['activations']['Earth (个性黑)']['text']}
- 潜意识太阳：{chart_data['activations']['Sun (设计红)']['text']}
            """

            # 4. 更新状态
            st.session_state.chart_calculated = True
            st.session_state.current_chart = chart_data
            st.session_state.messages = [] 

            # 5. 主动触发第一次 AI 解读
            first_trigger_msg = [{"role": "system", "content": st.session_state.system_prompt_content}, 
                                 {"role": "user", "content": "请基于我的数据，给我一份完整、深度的整体解读报告。"}]
            
            # --- C. 处理新生成的流式消息 ---
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                
                stream = chat_with_deepseek(first_trigger_msg)
                
                if stream:
                    for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_response += content
                            response_placeholder.markdown(full_response + "▌")
                    
                    response_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

# --- 结果展示区 ---
if st.session_state.chart_calculated:
    d = st.session_state.current_chart
    loc_str = ""
    if d.get('location') and d['location'].get('lat'):
         loc_str = f"📍 {d['location']['lat']:.2f}, {d['location']['lon']:.2f}"
    
    st.info(f"✨ {name} | {d['type']} | {d['profile']} | {loc_str}")

# --- D. 聊天输入框 ---
if prompt := st.chat_input("和活活继续深入探讨..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    api_messages = [{"role": "system", "content": st.session_state.system_prompt_content}]
    for msg in st.session_state.messages:
        api_messages.append(msg)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        stream = chat_with_deepseek(api_messages)

        if stream:
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
