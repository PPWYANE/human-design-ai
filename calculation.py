import math
import ephem
from datetime import datetime, timedelta

# 人类图曼陀罗闸门顺序
MANDALA_ORDER = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3, 27, 24,
    2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56, 31, 33, 7, 4,
    29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34,
    9, 5, 26, 11, 10, 58, 38, 54, 61, 60
]

# 简单的类型判断逻辑 (仅供演示)
GENERATOR_GATES = [5, 14, 29, 34, 27, 59, 9, 3, 42, 53, 60, 52]

def get_planet_position(body_name, date_utc):
    """使用 PyEphem 计算星星在黄道上的经度"""
    planet = None
    if body_name == "Sun": planet = ephem.Sun()
    elif body_name == "Earth": planet = ephem.Sun()
    elif body_name == "Moon": planet = ephem.Moon()
    
    planet.compute(date_utc)
    ecl = ephem.Ecliptic(planet)
    degree = math.degrees(ecl.lon)
    
    if body_name == "Earth":
        degree = (degree + 180) % 360
    return degree

def degree_to_gate(degree):
    """把度数映射到人类图的闸门和爻"""
    degree = degree % 360
    step = 360 / 64
    index = int(degree / step)
    gate = MANDALA_ORDER[index % 64]
    
    rem = degree - (index * step)
    line = int(rem / (step / 6)) + 1
    
    return {"gate": gate, "line": line, "text": f"{gate}.{line}"}

def find_design_date(target_sun_degree, start_date):
    """寻找设计时间（太阳回退88度）"""
    d_date = start_date - timedelta(days=88)
    return d_date

def get_chart_data(date_obj, time_obj, lat=None, lon=None):
    """主函数"""
    local_dt = datetime.combine(date_obj, time_obj)
    # 简单假设 UTC+8，真实环境可引入 pytz
    utc_dt = local_dt - timedelta(hours=8)
    
    # 个性（黑）
    p_sun_deg = get_planet_position("Sun", utc_dt)
    p_earth_deg = get_planet_position("Earth", utc_dt)
    
    # 设计（红）
    target_design_sun = (p_sun_deg - 88) % 360
    design_dt = find_design_date(target_design_sun, utc_dt)
    d_sun_deg = get_planet_position("Sun", design_dt)
    d_earth_deg = get_planet_position("Earth", design_dt)
    
    p_sun = degree_to_gate(p_sun_deg)
    p_earth = degree_to_gate(p_earth_deg)
    d_sun = degree_to_gate(d_sun_deg)
    d_earth = degree_to_gate(d_earth_deg)
    
    my_type = "生产者 (Generator)" if p_sun['gate'] in GENERATOR_GATES else "非生产者 (Projector/Other)"
    
    return {
        "type": my_type,
        "profile": f"{p_sun['line']} / {d_sun['line']}",
        "activations": {
            "Sun (个性黑)": p_sun,
            "Earth (个性黑)": p_earth,
            "Sun (设计红)": d_sun,
            "Earth (设计红)": d_earth
        },
        "location": {
            "lat": lat,
            "lon": lon
        }
    }
