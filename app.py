import streamlit as st
import calculation  # 你的计算逻辑文件
import time
import requests     # 新增：用于发送网络请求
import json         # 新增：用于处理返回的数据

# ==========================================
# 1. 配置 Coze API 信息
# ==========================================
# 🛡️ 安全模式：从云端密钥库读取，不再直接写死在代码里
# 如果你在本地运行报错，请看教程最后的“本地如何运行”说明
try:
    COZE_API_TOKEN = st.secrets["COZE_API_TOKEN"]
    COZE_BOT_ID = st.secrets["COZE_BOT_ID"]
except FileNotFoundError:
    st.error("密钥未配置！请在 Streamlit Cloud 的 Secrets 里配置，或者在本地创建 .streamlit/secrets.toml 文件。")
    st.stop()

USER_ID = "user_123"

# ==========================================
# 2. 定义与 Coze 对话的函数
# ==========================================
def chat_with_coze(prompt_text):
    """
    发送 prompt 给 Coze，并获取流式回复
    """
    # 如果是国内版 Coze (扣子)，域名可能是 api.coze.cn
    # 如果是国际版，用 api.coze.com
    url = "https://api.coze.cn/open_api/v2/chat" 
    
    headers = {
        "Authorization": f"Bearer {COZE_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Host": "api.coze.cn", 
        "Connection": "keep-alive"
    }
    
    data = {
        "conversation_id": "123",
        "bot_id": COZE_BOT_ID,
        "user": USER_ID,
        "query": prompt_text,
        "stream": True # 开启流式输出
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, stream=True)
        if response.status_code == 200:
            return response
        else:
            st.error(f"连接 AI 失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"网络请求出错: {e}")
        return None

# ==========================================
# 3. 网页界面布局 (前端)
# ==========================================
st.title("🔮 人类图 AI 解读系统")
st.write("输入你的出生信息，获取专属的人类图解析。")

# --- 输入区域 ---
col_input1, col_input2 = st.columns(2)
with col_input1:
    name = st.text_input("你的名字", "Wanye")
    birth_date = st.date_input("出生日期")
with col_input2:
    city = st.text_input("出生城市", "Beijing")
    birth_time = st.time_input("出生时间")

# --- 核心按钮逻辑 ---
if st.button("🚀 生成并解读", type="primary"):
    
    # === 第一部分：计算人类图数据 ===
    with st.spinner('正在排盘中...'):
        time.sleep(0.5) # 增加一点仪式感
        
        # 调用 calculation.py 进行真实天文计算
        chart_data = calculation.get_chart_data(birth_date, birth_time)
        
        st.success("排盘完成！")
        
        # 显示基础结果
        c1, c2 = st.columns(2)
        with c1:
            st.metric("类型", chart_data['type'])
            st.metric("人生角色", chart_data['profile'])
        with c2:
            st.write("**核心激活点：**")
            st.write(f"☀️ 意识太阳: {chart_data['activations']['Sun (个性黑)']['text']}")
            st.write(f"🌍 意识地球: {chart_data['activations']['Earth (个性黑)']['text']}")
            st.write(f"☀️ 潜意识太阳: {chart_data['activations']['Sun (设计红)']['text']}")

    # === 第二部分：生成 AI 提示词 ===
    prompt_for_ai = f"""
    用户数据如下：
    - 类型：{chart_data['type']}
    - 人生角色：{chart_data['profile']}
    - 意识太阳闸门：{chart_data['activations']['Sun (个性黑)']['text']}
    - 潜意识太阳闸门：{chart_data['activations']['Sun (设计红)']['text']}
    
    请根据以上人类图数据，用专业且富有洞察力的口吻，为用户提供一段简短的人生策略建议和天赋解读。
    """
    
    # 这一行用来调试，确认数据没问题 (不想看可以注释掉)
    with st.expander("查看发送给 AI 的数据包"):
        st.code(prompt_for_ai)

    # === 第三部分：召唤 Coze AI ===
    st.divider()
    st.subheader("🤖 活活智能体正在解读...")
    
    # 创建占位符，准备实时显示文字
    response_placeholder = st.empty()
    full_response = ""
    
    # 调用函数
    api_response = chat_with_coze(prompt_for_ai)
    
    # 处理流式回复
    # === 处理流式回复 (调试版) ===
    # ... (上面的代码不用动) ...
    
    # 3. 召唤 Coze AI (确保这一行缩进正确)
    api_response = chat_with_coze(prompt_for_ai)
    
    # === 👇 请完全覆盖替换下面这一段 👇 ===
    
    # 创建占位符，准备实时显示文字
    response_placeholder = st.empty()
    full_response = ""
    
    # 处理流式回复
    if api_response:
        for line in api_response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                
                # 识别以 "data:" 开头的数据行
                if decoded_line.startswith('data:'):
                    json_str = decoded_line[5:] # 去掉前面的 "data:"
                    try:
                        data_packet = json.loads(json_str)
                        
                        # 核心逻辑：提取 'message' 里的 'content'
                        # 只有当 type 是 answer 时，才是 AI 给用户的回答
                        if ('message' in data_packet and 
                            data_packet['message']['type'] == 'answer' and
                            'content' in data_packet['message']):
                            
                            content = data_packet['message']['content']
                            
                            # 只有内容不为空时才更新（避免开头没字的时候闪烁）
                            if content:
                                full_response += content
                                # 实时刷新显示 (加上光标 ▌ 增加科技感)
                                response_placeholder.markdown(full_response + "▌")
                                
                    except Exception as e:
                        # 如果有一行解析失败，忽略它，继续下一行
                        pass
        
        # 循环结束后，显示最终完整文本（去掉光标）
        response_placeholder.markdown(full_response)
        st.success("✅ 解读完毕")
