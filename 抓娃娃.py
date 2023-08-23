# 导入必要的库
import cv2 # 用于图像处理
import serial # 用于串口通信
import numpy as np # 用于数学运算

# 定义抓娃娃机的参数
claw_width = 10 # 爪子的宽度，单位为厘米
claw_height = 15 # 爪子的高度，单位为厘米
claw_depth = 20 # 爪子的深度，单位为厘米
claw_speed = 5 # 爪子的移动速度，单位为厘米/秒
claw_force = 50 # 爪子的夹力，单位为牛顿

# 定义摄像头的参数
camera_width = 640 # 摄像头的水平分辨率，单位为像素
camera_height = 480 # 摄像头的垂直分辨率，单位为像素
camera_fov = 60 # 摄像头的视场角，单位为度

# 定义串口的参数
port_name = "COM1" # 串口的名称
baud_rate = 9600 # 串口的波特率

# 打开串口
ser = serial.Serial(port_name, baud_rate)

# 打开摄像头
cap = cv2.VideoCapture(0)

# 定义一个函数，用于计算物体在摄像头中的位置和大小
def detect_object(image):
    # 这里可以使用一些图像处理算法，例如边缘检测、轮廓提取、颜色分割等，来识别物体并返回其位置和大小
    # 这里只是简单地使用一个阈值来分割物体和背景，并返回最大连通区域的位置和大小
    _, mask = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY) # 使用128作为阈值进行二值化
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # 寻找轮廓
    if len(contours) > 0: # 如果有轮廓存在
        max_contour = max(contours, key=cv2.contourArea) # 找到最大的轮廓
        x, y, w, h = cv2.boundingRect(max_contour) # 计算最大轮廓的外接矩形
        return x, y, w, h # 返回位置和大小
    else: # 如果没有轮廓存在
        return None, None, None, None # 返回空值

# 定义一个函数，用于计算物体在真实世界中的位置和大小
def calculate_position_and_size(x, y, w, h):
    # 根据摄像头的参数和物体在摄像头中的位置和大小，计算物体在真实世界中的位置和大小
    # 这里假设摄像头是水平放置的，并且与抓娃娃机的平面平行，并且与抓娃娃机的中心对齐
    camera_angle = camera_fov / 2 # 计算摄像头的半视场角，单位为弧度
    camera_distance = camera_width / (2 * np.tan(camera_angle)) # 计算摄像头到抓娃娃机平面的距离，单位为厘米
    object_x = (x + w / 2 - camera_width / 2) * camera_distance / camera_width # 计算物体在水平方向上的位置，单位为厘米
    object_y = camera_distance - (y + h / 2 - camera_height / 2) * camera_distance / camera_height # 计算物体在垂直方向上的位置，单位为厘米
    object_w = w * camera_distance / camera_width # 计算物体在水平方向上的大小，单位为厘米
    object_h = h * camera_distance / camera_height # 计算物体在垂直方向上的大小，单位为厘米
    return object_x, object_y, object_w, object_h # 返回位置和大小

# 定义一个函数，用于控制爪子的移动和夹取
def control_claw(x, y, w, h):
    # 根据物体在真实世界中的位置和大小，控制爪子的移动和夹取
    # 这里假设爪子的初始位置是在抓娃娃机的中心，并且与物体的深度相同
    claw_x = 0 # 爪子在水平方向上的位置，单位为厘米
    claw_y = claw_depth # 爪子在垂直方向上的位置，单位为厘米
    claw_open = True # 爪子是否打开
    claw_grab = False # 爪子是否抓住物体
    while True: # 循环执行以下步骤，直到抓住物体或者超时
        if claw_open: # 如果爪子是打开的
            if abs(claw_x - x) < 1 and abs(claw_y - y) < 1: # 如果爪子的位置和物体的位置接近
                claw_open = False # 关闭爪子
                if w < claw_width and h < claw_height: # 如果物体的大小小于爪子的大小
                    claw_grab = True # 抓住物体
                    break # 跳出循环
                else: # 如果物体的大小大于爪子的大小
                    break # 跳出循环
            else: # 如果爪子的位置和物体的位置不接近
                if claw_x < x: # 如果爪子在水平方向上落后于物体
                    claw_x += claw_speed # 爪子向右移动一定距离
                elif claw_x > x: # 如果爪子在水平方向上超过了物体
                    claw_x -= claw_speed # 爪子向左移动一定距离
                if claw_y < y: # 如果爪子在垂直方向上落后于物体
                    claw_y += claw_speed # 爪子向上移动一定距离
                elif claw_y > y: # 如果爪子在垂直方向上超过了物体
                    claw_y -= claw_speed # 爪子向下移动一定距离
        else: # 如果爪子是关闭的
            break # 跳出循环

        # 通过串口发送爪子的位置和状态给抓娃娃机
        data = "{},{},{},{}".format(claw_x, claw_y, int(claw_open), int(claw_grab)) # 将数据格式化为字符串，用逗号分隔
        data = data.encode() # 将字符串转换为字节串
        ser.write(data) # 通过串口发送数据

    return claw_grab # 返回是否抓住物体

# 主循环，不断地从摄像头获取图像，并进行处理和控制
while True:
    ret, frame = cap.read() # 从摄像头读取一帧图像
    if ret: # 如果读取成功
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # 将图像转换为灰度图像
        x, y, w, h = detect_object(gray) # 检测物体在图像中的位置和大小
        if x is not None and y is not None and w is not None and h is not None: # 如果检测到了物体
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2) # 在图像上绘制物体的外接矩形，颜色为绿色，线宽为2像素
            object_x, object_y, object_w, object_h = calculate_position_and_size(x, y, w, h) # 计算物体在真实世界
