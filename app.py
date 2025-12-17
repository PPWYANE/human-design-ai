import streamlit as st
import calculation      # 你的计算逻辑 (v4.1)
import drawer_pil       # 👈 【修正】必须引用这个 PIL 叠图引擎！
import city_data        # 离线城市库
from openai import OpenAI
from geopy.geocoders import Nominatim
from datetime import date

# ==========================================
# 0. 页面配置 & 样式
# ==========================================
st.set_page_config(page_title="天命人类图AI+", page_icon="🔮", layout="centered")

# 隐藏右上角菜单和页脚，并调整图片间距
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
div[data-testid="stImage"] {
    margin-top: 20px;
    margin-bottom: 20px;
}
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
        geolocator = Nominatim(user_agent="my_hd_app_v16_pil", timeout=5)
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
        with st.spinner('正在连接宇宙能量库，绘制灵魂蓝图...'):
            # 1. 获取经纬度
            lat, lon = get_coordinates(city)
            if lat is None:
                st.warning(f"⚠️ 找不到城市 '{city}'，已使用默认坐标 (北京)。")
                lat, lon = 39.9042, 116.4074
            
            # 2. 计算人类图 (调用 calculation.py)
            chart_data = calculation.get_chart_data(birth_date, birth_time, lat, lon)
            
            # 3. 构建 System Prompt
            st.session_state.system_prompt_content = f"""
# 角色
你叫“活活”，资深人类图分析师。
# 核心指令
**必须掌握对话主动权**。每次回复最后必须抛出一个引导性反问句。
# 回复逻辑
## 第一阶段：深度首秀
直接输出 600字 综合解读：
1. 能量致意（连接 {city}）。
2. 核心画像（{chart_data['type']} + {chart_data['profile']} 的比喻）。
3. 光之天赋（意识太阳 {chart_data['activations'].get('Sun (个性黑)', {}).get('text', '未知')}）。
4. 暗之动力（潜意识太阳 {chart_data['activations'].get('Sun (设计红)', {}).get('text', '未知')}）。
5. 灵魂拷问。
## 第二阶段：后续互动
短小精悍，结合生活场景追问。
---
# 用户数据
姓名：{name}
城市：{city}
类型：{chart_data['type']}
人生角色：{chart_data['profile']}
定义中心：{', '.join(chart_data['defined_centers'])}
"""
            # 4. 更新状态
            st.session_state.chart_calculated = True
            st.session_state.current_chart = chart_data
            st.session_state.messages = [] # 重置对话

            # 5. 主动触发第一次 AI 解读
            first_trigger_msg = [
                {"role": "system", "content": st.session_state.system_prompt_content},
                {"role": "user", "content": "请基于我的数据，给我一份完整、深度的整体解读报告。"}
            ]
            
            # --- C. 处理 AI 流式响应 ---
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
            st.rerun() # 强制刷新

# --- 结果展示区 (PIL 图片版 + 详细数据版) ---
if st.session_state.chart_calculated:
    d = st.session_state.current_chart
    loc_str = ""
    if d.get('location') and d['location'].get('lat'):
        loc_str = f"📍 {d['location']['lat']:.2f}, {d['location']['lon']:.2f}"

    st.markdown("---")
    st.subheader("📊 你的能量蓝图")
    
    col_img, col_info = st.columns([1.2, 1.8])
    
    with col_img:
        # === 核心修正：调用 drawer_pil 生成图片 ===
        pil_image = drawer_pil.create_chart_image(d)
        
        if pil_image:
            st.image(pil_image, caption=f"{name} 的人类图", use_container_width=True)
        else:
            st.error("❌ 无法生成图片，请检查 images 文件夹及素材")
            
    with col_info:
        # 1. 核心大标题
        st.success(f"✨ **{name}** | {d['type']} | {d['profile']}")
        
        # 2. 基础数据
        st.write(f"🌍 **坐标**: {city} ({loc_str})")
        st.write(f"⚡ **定义中心**: {len(d['defined_centers'])} 个")
        
        # 3. 通道列表
        if d['active_channels']:
            with st.expander(f"🔗 接通通道 ({len(d['active_channels'])}条)", expanded=True):
                for ch in d['active_channels']:
                    st.write(f"**{ch[0]} - {ch[1]}**")
        else:
            st.info("🔗 无接通通道")

        st.divider()
        
        # 4. 行星数据列表 (修复：从 calculation.py 获取的数据显示出来)
        c_black, c_red = st.columns(2)
        
        with c_black:
            st.markdown("#### ⚫ 个性")
            for k, v in d['activations'].items():
                if "黑" in k:
                    # 简化显示：只取行星名
                    planet_name = k.split(" ")[0] 
                    st.write(f"{planet_name}: **{v['text']}**")
                    
        with c_red:
            st.markdown("#### 🔴 设计")
            for k, v in d['activations'].items():
                if "红" in k:
                    planet_name = k.split(" ")[0]
                    st.write(f"{planet_name}: **{v['text']}**")

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
