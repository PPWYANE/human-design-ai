import os
import streamlit as st
from PIL import Image

# === 配置区域 ===
# 图片素材文件夹名称
IMG_DIR = "images"

# 默认画布大小 (当找不到 base.png 时使用这个尺寸)
# 建议和你 PS 里的画布大小保持一致
DEFAULT_SIZE = (1000, 1000)

# 9大中心的文件名映射
CENTER_FILES = {
    "Head": "center_head",
    "Ajna": "center_ajna",
    "Throat": "center_throat",
    "G": "center_g",
    "Heart": "center_heart",
    "Sacral": "center_sacral",
    "Spleen": "center_spleen",
    "Solar": "center_solar",
    "Root": "center_root"
}

def load_layer(layer_name):
    """
    加载一张图层，如果文件不存在则返回 None
    """
    # 确保文件夹存在
    if not os.path.exists(IMG_DIR):
        st.error(f"❌ 严重错误：找不到 '{IMG_DIR}' 文件夹！请在项目根目录新建它。")
        return None

    path = os.path.join(IMG_DIR, f"{layer_name}.png")
    if os.path.exists(path):
        return Image.open(path).convert("RGBA")
    else:
        # 这里不报错，只是静默返回 None，方便后续统计缺失文件
        return None

def get_gate_color(gate_num, chart_data):
    """
    判断一个闸门应该是 红、黑 还是 斑马纹
    """
    red_gates = set()
    black_gates = set()
    
    activations = chart_data.get('activations', {})
    
    for planet_name, data in activations.items():
        g = data['gate']
        if "设计红" in planet_name:
            red_gates.add(g)
        elif "个性黑" in planet_name:
            black_gates.add(g)
            
    is_red = gate_num in red_gates
    is_black = gate_num in black_gates
    
    if is_red and is_black:
        return "mix"
    elif is_red:
        return "red"
    elif is_black:
        return "black"
    else:
        return None

def create_chart_image(chart_data):
    """
    宽容版叠图函数：缺图不报错，只显示有的
    """
    missing_assets = [] # 用于记录缺了什么图
    
    # ===============================
    # 第 1 层：BASE (底图)
    # ===============================
    base_img = load_layer("base")
    
    if base_img is None:
        # 【关键修改】如果没有底图，创建一个空的透明画布
        missing_assets.append("base.png (底图)")
        canvas = Image.new("RGBA", DEFAULT_SIZE, (255, 255, 255, 0))
    else:
        canvas = base_img.copy()

    # ===============================
    # 第 2 层：CENTERS (中心)
    # ===============================
    defined_centers = chart_data.get('defined_centers', [])
    for center_name in defined_centers:
        file_name = CENTER_FILES.get(center_name)
        if file_name:
            center_layer = load_layer(file_name)
            if center_layer:
                canvas = Image.alpha_composite(canvas, center_layer)
            else:
                missing_assets.append(f"{file_name}.png")

    # ===============================
    # 第 3 层：GATES (闸门)
    # ===============================
    all_active_gates = chart_data.get('gate_list', [])
    all_active_gates = set(all_active_gates)
    
    for gate in all_active_gates:
        color = get_gate_color(gate, chart_data)
        if color:
            file_name = f"gate_{gate}_{color}"
            gate_layer = load_layer(file_name)
            
            if gate_layer:
                canvas = Image.alpha_composite(canvas, gate_layer)
            else:
                # 记录缺失的闸门图
                missing_assets.append(f"{file_name}.png")

    # ===============================
    # 第 4 层：NUMBERS (数字)
    # ===============================
    numbers_layer = load_layer("numbers")
    if numbers_layer:
        canvas = Image.alpha_composite(canvas, numbers_layer)
    else:
        missing_assets.append("numbers.png (数字层)")

    # ===============================
    # 反馈：告诉用户缺了什么 (仅在测试时显示)
    # ===============================
    if missing_assets:
        with st.expander("⚠️ 缺少部分素材 (但不影响预览)", expanded=False):
            st.write("以下图片未找到，因此未显示在图中：")
            st.write(missing_assets)
            st.caption("提示：请检查 images 文件夹，确保文件名完全一致。")
        
    return canvas
