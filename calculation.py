import math
import ephem
from datetime import datetime, timedelta

# ================= 数据定义 =================
MANDALA_ORDER = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3, 27, 24,
    2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56, 31, 33, 7, 4,
    29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34,
    9, 5, 26, 11, 10, 58, 38, 54, 61, 60
]

# 36条通道定义 (格式: (闸门A, 闸门B): [连接的中心1, 连接的中心2])
CHANNELS_DB = {
    (64, 47): ["Head", "Ajna"], (61, 24): ["Head", "Ajna"], (63, 4): ["Head", "Ajna"],
    (17, 62): ["Ajna", "Throat"], (43, 23): ["Ajna", "Throat"], (11, 56): ["Ajna", "Throat"],
    (16, 48): ["Throat", "Spleen"], (20, 57): ["Throat", "Spleen"], (35, 36): ["Throat", "Solar"],
    (12, 22): ["Throat", "Solar"], (45, 21): ["Throat", "Heart"], (31, 7): ["Throat", "G"],
    (8, 1): ["Throat", "G"], (33, 13): ["Throat", "G"], (10, 20): ["G", "Throat"],
    (10, 34): ["G", "Sacral"], (10, 57): ["G", "Spleen"], (25, 51): ["G", "Heart"],
    (46, 29): ["G", "Sacral"], (15, 5): ["G", "Sacral"], (2, 14): ["G", "Sacral"],
    (26, 44): ["Heart", "Spleen"], (40, 37): ["Heart", "Solar"], (34, 57): ["Sacral", "Spleen"],
    (34, 20): ["Sacral", "Throat"], (50, 27): ["Spleen", "Sacral"], (59, 6): ["Sacral", "Solar"],
    (42, 53): ["Sacral", "Root"], (3, 60): ["Sacral", "Root"], (9, 52): ["Sacral", "Root"],
    (18, 58): ["Spleen", "Root"], (28, 38): ["Spleen", "Root"], (32, 54): ["Spleen", "Root"],
    (19, 49): ["Root", "Solar"], (39, 55): ["Root", "Solar"], (41, 30): ["Root", "Solar"]
}

# 简单的类型判断逻辑
GENERATOR_GATES = [5, 14, 29, 34, 27, 59, 9, 3, 42, 53, 60, 52]

def get_planet_position(body_name, date_utc):
    """
    计算行星在黄道上的绝对经度 (0-360度)
    """
    try:
        planet = None
        # 核心映射表
        if body_name == "Sun": planet = ephem.Sun()
        elif body_name == "Earth": planet = ephem.Sun() # 地球是太阳的对面
        elif body_name == "Moon": planet = ephem.Moon()
        elif body_name == "Mercury": planet = ephem.Mercury()
        elif body_name == "Venus": planet = ephem.Venus()
        elif body_name == "Mars": planet = ephem.Mars()
        elif body_name == "Jupiter": planet = ephem.Jupiter()
        elif body_name == "Saturn": planet = ephem.Saturn()
        elif body_name == "Uranus": planet = ephem.Uranus()
        elif body_name == "Neptune": planet = ephem.Neptune()
        elif body_name == "Pluto": planet = ephem.Pluto()
        
        # 如果找到了对应的星体对象
        if planet:
            planet.compute(date_utc)
            
            # 【核心修复点】
            # PyEphem 的 planet 对象没有 .ecl 属性
            # 必须创建一个 Ecliptic 对象来获取黄道经度
            ecl = ephem.Ecliptic(planet)
            ecl_lon = math.degrees(ecl.lon) 
            
            # 特殊处理：地球的位置永远在太阳对面 (+180度)
            if body_name == "Earth":
                ecl_lon = (ecl_lon + 180) % 360
                
            return ecl_lon
        
        return None
        
    except Exception as e:
        # 在本地调试时打印报错，方便排查
        # print(f"计算出错 {body_name}: {e}")
        return None

def degree_to_gate(degree):
    """将度数转换为闸门"""
    # 如果度数是 None (比如计算失败)，返回 None，不要给 0 (Gate 25)
    if degree is None: 
        return None
        
    degree = degree % 360
    step = 360.0 / 64.0
    index = int(degree / step)
    index = index % 64
    gate = MANDALA_ORDER[index]
    
    rem = degree - (index * step)
    line = int(rem / (step / 6.0)) + 1
    if line > 6: line = 6
    
    return {"gate": gate, "line": line, "text": f"{gate}.{line}"}

def find_design_date(sun_degree_utc, utc_dt):
    # 简化算法：太阳回退 88 天
    return utc_dt - timedelta(days=88)

def get_mechanics(active_gates):
    """计算通道和中心"""
    # 过滤掉 None (计算失败的数据)
    valid_gates = [g for g in active_gates if g is not None]
    
    active_gates_set = set(valid_gates)
    active_channels = []
    defined_centers = set()
    
    for (g1, g2), centers in CHANNELS_DB.items():
        if g1 in active_gates_set and g2 in active_gates_set:
            active_channels.append((g1, g2))
            defined_centers.add(centers[0])
            defined_centers.add(centers[1])
            
    return list(defined_centers), active_channels

def get_chart_data(date_obj, time_obj, lat=None, lon=None):
    """v5.0 主计算函数"""
    local_dt = datetime.combine(date_obj, time_obj)
    # 假设 UTC+8
    utc_dt = local_dt - timedelta(hours=8)

    activations = {}
    gate_list = [] 
    
    # 完整的行星列表
    PLANETS = ["Sun", "Earth", "Moon", "Mercury", "Venus", "Mars", 
               "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]

    # 1. 计算个性 (黑色)
    for body in PLANETS:
        deg = get_planet_position(body, utc_dt)
        if deg is not None:
            data = degree_to_gate(deg)
            activations[f"{body} (个性黑)"] = data
            gate_list.append(data['gate'])
        else:
            # 标记为未知，而不是给 25.1
            activations[f"{body} (个性黑)"] = {"text": "未知"}

    # 2. 计算设计 (红色)
    current_sun = get_planet_position("Sun", utc_dt)
    
    if current_sun is not None:
        design_dt = find_design_date(current_sun, utc_dt)
        
        for body in PLANETS:
            deg = get_planet_position(body, design_dt)
            if deg is not None:
                data = degree_to_gate(deg)
                activations[f"{body} (设计红)"] = data
                gate_list.append(data['gate'])
            else:
                activations[f"{body} (设计红)"] = {"text": "未知"}

    # 3. 结算机制
    defined_centers, active_channels = get_mechanics(gate_list)

    # 简单的类型判断
    my_type = "生产者" if "Sacral" in defined_centers else "显示者 (或投射/反映)"
    
    p_sun = activations.get("Sun (个性黑)", {"text":"?"})
    d_sun = activations.get("Sun (设计红)", {"text":"?"})
    
    # 提取爻线用于显示
    profile = "?/?"
    if "line" in p_sun and "line" in d_sun:
        profile = f"{p_sun['line']} / {d_sun['line']}"

    return {
        "type": my_type,
        "profile": profile,
        "activations": activations,
        "defined_centers": defined_centers,
        "active_channels": active_channels,
        "gate_list": gate_list,     
        "location": {"lat": lat, "lon": lon}
    }
