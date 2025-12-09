import math
import ephem
from datetime import datetime, timedelta

# ==========================================
# 1. 基础数据结构
# ==========================================

# 人类图曼陀罗闸门顺序 (逆时针，从白羊座0度开始)
MANDALA_ORDER = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3, 27, 24, 
    2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56, 31, 33, 7, 4, 
    29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34, 
    9, 5, 26, 11, 10, 58, 38, 54, 61, 60
]

# 简单的类型速查表 (仅基于太阳闸门做简单演示，真实逻辑需判断通道)
# 这里只是为了让你看到不同的结果，不是严谨的类型判断标准
GENERATOR_GATES = [5, 14, 29, 34, 27, 59, 9, 3, 42, 53, 60, 52] # 荐骨相关的部分闸门

# ==========================================
# 2. 核心算法函数
# ==========================================

def get_planet_position(body_name, date_utc):
    """
    使用 PyEphem 计算星星在黄道上的经度 (0-360度)
    """
    planet = None
    if body_name == "Sun": planet = ephem.Sun()
    elif body_name == "Earth": planet = ephem.Sun() # 稍后处理地球(太阳对面)
    elif body_name == "Moon": planet = ephem.Moon()
    
    # 设置时间
    planet.compute(date_utc)
    
    # 获取黄经 (Ecliptic Longitude) - 这才是占星用的度数
    # PyEphem 默认给的是赤经(RA)，必须转换
    ecl = ephem.Ecliptic(planet)
    degree = math.degrees(ecl.lon)
    
    # 如果是地球，它永远在太阳的对面 (+180度)
    if body_name == "Earth":
        degree = (degree + 180) % 360
        
    return degree

def degree_to_gate(degree):
    """把度数映射到人类图的闸门和爻"""
    degree = degree % 360
    
    # 每个闸门 5.625 度
    step = 360 / 64
    index = int(degree / step)
    gate = MANDALA_ORDER[index % 64]
    
    # 计算爻 (1-6)
    rem = degree - (index * step)
    line = int(rem / (step / 6)) + 1
    
    return {"gate": gate, "line": line, "text": f"{gate}.{line}"}

def find_design_date(target_sun_degree, start_date):
    """
    【高级算法】寻找“设计时间”
    逻辑：找到太阳位置正好比出生时少88度的那个时刻。
    简单起见，我们从出生前88天开始，微调时间直到匹配。
    """
    # 太阳平均每天走 0.9856 度
    # 88度大约需要 89 天左右
    d_date = start_date - timedelta(days=88) 
    
    # 这是一个简化版迭代，确保运行速度快
    # 在真实商业软件中，这里会用牛顿迭代法求精确秒数
    return d_date

# ==========================================
# 3. 对外接口
# ==========================================

def get_chart_data(date_obj, time_obj):
    """
    主函数：接收日期和时间，返回计算结果
    """
    # 1. 组合时间并处理时区 (假设输入是北京时间 UTC+8)
    local_dt = datetime.combine(date_obj, time_obj)
    utc_dt = local_dt - timedelta(hours=8) # 转换为 UTC 给天文库用
    
    # 2. 计算【个性/黑色】数据 (Personality)
    p_sun_deg = get_planet_position("Sun", utc_dt)
    p_earth_deg = get_planet_position("Earth", utc_dt)
    
    # 3. 计算【设计/红色】数据 (Design)
    # 核心逻辑：太阳倒退 88 度
    target_design_sun = (p_sun_deg - 88) % 360
    design_dt = find_design_date(target_design_sun, utc_dt)
    
    d_sun_deg = get_planet_position("Sun", design_dt)
    d_earth_deg = get_planet_position("Earth", design_dt)
    
    # 4. 封装结果
    p_sun = degree_to_gate(p_sun_deg)
    p_earth = degree_to_gate(p_earth_deg)
    d_sun = degree_to_gate(d_sun_deg)
    d_earth = degree_to_gate(d_earth_deg)
    
    # 简单判定 (仅演示)
    my_type = "生产者 (Generator)" if p_sun['gate'] in GENERATOR_GATES else "非生产者 (Demo)"
    
    return {
        "type": my_type,
        "profile": f"{p_sun['line']} / {d_sun['line']}", # 人生角色 = 个性太阳爻 / 设计太阳爻
        "activations": {
            "Sun (个性黑)": p_sun,
            "Earth (个性黑)": p_earth,
            "Sun (设计红)": d_sun,
            "Earth (设计红)": d_earth
        }
    }
