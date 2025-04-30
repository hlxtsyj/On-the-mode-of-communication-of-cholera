import numpy as np
import matplotlib.pyplot as plt
from ipywidgets import interact, IntSlider, FloatSlider, Play, VBox, HBox, interactive_output
import ipywidgets as widgets
import math


# 1. 读入背景地图并设置模拟区域


# 读取地图图像 (请使用自己的图片文件名)
# 例如在同级目录放一张名为 london_map.png 的地图
try:
    map_img = plt.imread("london_map.png")
except FileNotFoundError:
    print("未找到地图文件 london_map.png，请检查文件路径或替换其他可用图片。")
    map_img = np.zeros((100,100,3), dtype=float)  # 如果没有图片，使用纯黑背景代替

# 假设将地图像素坐标映射到 [0,100]×[0,100] 的模拟区域
map_height, map_width = map_img.shape[:2]
# extent = (xmin, xmax, ymin, ymax)
extent = (0, 100, 0, 100)

# 网格大小
GRID_SIZE = 50
dx = 100 / GRID_SIZE  # 将[0,100]划分成 GRID_SIZE 等份
dy = 100 / GRID_SIZE

# 2. 定义初始条件

# 人口密度：随机生成 [0,1]，也可以根据历史数据城市布局进行赋值
np.random.seed(42)
population_density = np.random.rand(GRID_SIZE, GRID_SIZE)

# 将水泵位置/受污染水源位置设定在网格上
# 这里为了演示，随机选几个点，也可自行指定如 Broad Street Pump 附近
water_contamination = np.zeros((GRID_SIZE, GRID_SIZE))
pump_locations = [(25, 25), (30, 35)]  # 可以自定义：在(25,25)、(30,35)处放水泵
for (px, py) in pump_locations:
    water_contamination[px, py] = 1

infection_status = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)

infection_init_count = 5
for _ in range(infection_init_count):
    rx, ry = np.random.randint(0, GRID_SIZE, size=2)
    infection_status[rx, ry] = 1

# 3. 定义传播规则

def update_infection(infection_status, base_infection_rate, water_infection_boost,
                     recovery_rate, population_density_factor):
    """
    单步更新感染状态
    """
    new_infection_status = infection_status.copy()
    
    neighbors = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),           (0, 1),
                 (1, -1),  (1, 0),  (1, 1)]
    
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            if infection_status[x, y] == 1:
                # 已感染的个体有一定概率在本轮步进中康复(或死亡)，则不再传染
                if np.random.rand() < recovery_rate:
                    new_infection_status[x, y] = 0
                else:
                    new_infection_status[x, y] = 1
            else:
                # 若此处未感染，检查周围
                infected_neighbors = 0
                for dx, dy in neighbors:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                        if infection_status[nx, ny] == 1:
                            infected_neighbors += 1
                
                if infected_neighbors > 0:
                    prob = (base_infection_rate
                            + water_infection_boost * water_contamination[x, y]
                            + population_density_factor * population_density[x, y])
                    prob *= (1 + 0.1 * infected_neighbors)  # 邻居越多，感染几率越大
                    
                    if np.random.rand() < prob:
                        new_infection_status[x, y] = 1
    return new_infection_status

# 4. 可视化
def plot_map(infection_status, step):
    """
    在背景地图上叠加显示感染状态、标注水泵
    """
    plt.figure(figsize=(8, 8))
    # 绘制地图
    plt.imshow(map_img, extent=extent, origin='upper')  # origin='upper' 视情况可改
    
    # 将网格中感染的坐标提取出来
    infected_x, infected_y = [], []
    healthy_x, healthy_y = [], []
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            if infection_status[x, y] == 1:
                # 映射到 [0,100] 坐标
                infected_x.append((x + 0.5)*dx)
                # 注意：此处将 y 也映射到坐标系
                # 若把 x 作为行号，则在显示时 x->y, y->x, 视实际需要可做转置
                infected_y.append((y + 0.5)*dy)
            else:
                healthy_x.append((x + 0.5)*dx)
                healthy_y.append((y + 0.5)*dy)

    # 绘制健康与感染点
    plt.scatter(healthy_x, healthy_y, c='blue', s=10, alpha=0.3, label='Healthy')
    plt.scatter(infected_x, infected_y, c='red', s=20, alpha=0.8, label='Infected')
    
    # 绘制受污染水源(泵)
    pump_x, pump_y = [], []
    for (px, py) in pump_locations:
        pump_x.append((px + 0.5)*dx)
        pump_y.append((py + 0.5)*dy)
    plt.scatter(pump_x, pump_y, c='black', marker='^', s=80, label='Contaminated Pump')
    
    plt.title(f"John Snow Cholera Simulation - Step {step}")
    plt.xlim([0, 100])
    plt.ylim([0, 100])
    plt.legend(loc='upper right')
    plt.gca().invert_yaxis()  # 若地图本身是自上而下
    plt.show()

# 5. 交互式 UI

base_infection_slider = FloatSlider(value=0.02, min=0.0, max=0.2, step=0.01, description='Base Rate')
water_infection_boost_slider = FloatSlider(value=0.1, min=0.0, max=0.5, step=0.01, description='Water Boost')
recovery_rate_slider = FloatSlider(value=0.05, min=0.0, max=0.5, step=0.01, description='Recovery Rate')
population_density_factor_slider = FloatSlider(value=0.3, min=0.0, max=1.0, step=0.05, description='Pop. Dens. Factor')

play_btn = Play(value=0, min=0, max=50, step=1, interval=600, description="Press Play", disabled=False)
time_slider = IntSlider(min=0, max=50, step=1, description='Time Step')
widgets.jslink((play_btn, 'value'), (time_slider, 'value'))

def run_simulation(step, base_infection_rate, water_infection_boost, recovery_rate, population_density_factor):
    """
    在每个时间步更新感染状态，并绘制。
    如果希望在 step=0 时重置模拟，可在此添加相应逻辑。
    """
    global infection_status
    
    # 更新
    infection_status = update_infection(
        infection_status,
        base_infection_rate,
        water_infection_boost,
        recovery_rate,
        population_density_factor
    )
    # 绘图
    plot_map(infection_status, step)

interactive_out = interactive_output(
    run_simulation,
    {
        'step': time_slider,
        'base_infection_rate': base_infection_slider,
        'water_infection_boost': water_infection_boost_slider,
        'recovery_rate': recovery_rate_slider,
        'population_density_factor': population_density_factor_slider
    }
)

ui = VBox([
    HBox([play_btn, time_slider]),
    base_infection_slider,
    water_infection_boost_slider,
    recovery_rate_slider,
    population_density_factor_slider,
    interactive_out
])

display(ui)
