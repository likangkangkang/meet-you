#!/usr/bin/env python3
"""
摄像头权限测试和授权
"""

import cv2
import sys

print("正在请求摄像头权限...")
print("如果弹出权限对话框，请点击'允许'\n")

camera = cv2.VideoCapture(0)

if camera.isOpened():
    print("✅ 摄像头权限已授权！")
    ret, frame = camera.read()
    if ret:
        print(f"✅ 摄像头工作正常，分辨率: {frame.shape[1]}x{frame.shape[0]}")
    camera.release()
    sys.exit(0)
else:
    print("❌ 无法打开摄像头")
    print("\n请手动授权：")
    print("1. 打开 系统设置 > 隐私与安全性 > 摄像头")
    print("2. 找到 'Python' 或 'Terminal'")
    print("3. 勾选允许访问摄像头")
    print("4. 重新运行此脚本")
    sys.exit(1)
