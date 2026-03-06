#!/usr/bin/env python3
"""
Meet You - 智能相册（使用 imagesnap 调用摄像头）
一眼是你，满目是你
"""

from flask import Flask, render_template, send_from_directory, jsonify
from flask_socketio import SocketIO
from pathlib import Path
import json
import webbrowser
from threading import Timer, Thread
import face_recognition
import subprocess
import time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'meet-you-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# 配置
PHOTO_DIR = Path("photos")
DISPLAY_TIME = 5  # 秒
TEMP_SNAPSHOT = Path("temp_snapshot.jpg")

# 全局状态
photo_database = {}
current_viewer = None
current_viewer_name = None
camera_running = False

def scan_photos():
    """扫描照片目录并提取人脸特征"""
    global photo_database
    
    if not PHOTO_DIR.exists():
        PHOTO_DIR.mkdir()
        print(f"请将照片放入 {PHOTO_DIR} 目录")
        return
    
    print("正在扫描照片...")
    photo_database = {}
    
    for photo_path in PHOTO_DIR.glob("*"):
        if photo_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            try:
                image = face_recognition.load_image_file(str(photo_path))
                face_encodings = face_recognition.face_encodings(image)
                
                if face_encodings:
                    photo_database[str(photo_path)] = {
                        "path": str(photo_path),
                        "name": photo_path.name,
                        "faces": face_encodings
                    }
            except Exception as e:
                print(f"处理照片 {photo_path} 时出错: {e}")
    
    print(f"扫描完成，共 {len(photo_database)} 张包含人脸的照片")

def check_imagesnap():
    """检查 imagesnap 是否安装"""
    try:
        result = subprocess.run(['which', 'imagesnap'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def install_imagesnap():
    """安装 imagesnap"""
    print("正在安装 imagesnap...")
    try:
        subprocess.run(['brew', 'install', 'imagesnap'], check=True)
        return True
    except:
        print("❌ 安装失败，请手动运行: brew install imagesnap")
        return False

def capture_snapshot():
    """使用 imagesnap 捕获照片"""
    try:
        # 使用 imagesnap 捕获照片（不显示预览窗口）
        result = subprocess.run(
            ['imagesnap', '-w', '0.5', str(TEMP_SNAPSHOT)],
            capture_output=True,
            timeout=3
        )
        return result.returncode == 0 and TEMP_SNAPSHOT.exists()
    except Exception as e:
        print(f"捕获照片失败: {e}")
        return False

def camera_loop():
    """摄像头循环（使用 imagesnap）"""
    global camera_running, current_viewer, current_viewer_name
    
    time.sleep(2)
    
    # 检查 imagesnap
    if not check_imagesnap():
        print("未找到 imagesnap，正在安装...")
        if not install_imagesnap():
            print("❌ 无法使用摄像头功能")
            return
    
    print("✅ 摄像头已启动（使用 imagesnap）")
    camera_running = True
    detection_interval = 2.0  # 每2秒检测一次
    
    while camera_running:
        try:
            # 捕获照片
            if not capture_snapshot():
                time.sleep(detection_interval)
                continue
            
            # 加载并分析照片
            image = face_recognition.load_image_file(str(TEMP_SNAPSHOT))
            face_encodings = face_recognition.face_encodings(image)
            
            # 清理临时文件
            if TEMP_SNAPSHOT.exists():
                TEMP_SNAPSHOT.unlink()
            
            if not face_encodings:
                if current_viewer is not None:
                    current_viewer = None
                    current_viewer_name = None
                    socketio.emit('viewer_changed', {'viewer': None})
                time.sleep(detection_interval)
                continue
            
            # 使用第一个检测到的人脸
            viewer_encoding = face_encodings[0]
            
            # 查找匹配的照片
            matching_photos = []
            for photo_path, photo_data in photo_database.items():
                for face_encoding in photo_data["faces"]:
                    matches = face_recognition.compare_faces(
                        [face_encoding],
                        viewer_encoding,
                        tolerance=0.6
                    )
                    if matches[0]:
                        matching_photos.append(photo_data["name"])
                        break
            
            # 更新当前观看者
            if matching_photos:
                viewer_id = viewer_encoding.tobytes()
                if current_viewer != viewer_id:
                    current_viewer = viewer_id
                    current_viewer_name = f"访客 {len(matching_photos)} 张照片"
                    
                    socketio.emit('viewer_changed', {
                        'viewer': current_viewer_name,
                        'photos': matching_photos
                    })
                    print(f"✅ 检测到观看者，匹配到 {len(matching_photos)} 张照片")
            
            time.sleep(detection_interval)
            
        except Exception as e:
            print(f"识别出错: {e}")
            time.sleep(detection_interval)
    
    print("摄像头已关闭")

@app.route('/')
def index():
    """主页"""
    return render_template('index.html', display_time=DISPLAY_TIME)

@app.route('/api/photos')
def get_photos():
    """获取表"""
    photos = [data["name"] for data in photo_database.values()]
    return jsonify(photos)

@app.route('/photos/<path:filename>')
def serve_photo(filename):
    """提供照片文件"""
    return send_from_directory(PHOTO_DIR, filename)

@socketio.on('start_camera')
def handle_start_camera():
    """启动摄像头"""
    global camera_running
    if not camera_running:
        camera_running = True
        camera_thread = Thread(target=camera_loop, daemon=True)
        camera_thread.start()
        print("✅ 摄像头已启动")

@socketio.on('stop_camera')
def handle_stop_camera():
    """停止摄像头"""
    global camera_running, current_viewer, current_viewer_name
    camera_running = False
    current_viewer = None
    current_viewer_name = None
    socketio.emit('viewer_changed', {'viewer': None})
    print("⏸️  摄像头已停止")

def open_browser():
    """自动打开浏览器"""
    webbrowser.open('http://127.0.0.1:5002')

if __name__ == '__main__':
    # 扫描照片
    scan_photos()
    
    # 不自动启动摄像头，等待用户点击按钮
    # camera_thread = Thread(target=camera_loop, daemon=True)
    # camera_thread.start()
    
    # 1.5秒后自动打开浏览器
    Timer(1.5, open_browser).start()
    
    print("Meet You 正在启动...")
    print("浏览器将自动打开，如果没有，请访问: http://127.0.0.1:5002")
    print("点击右上角按钮开启人脸识别")
    print("按 Ctrl+C 停止\n")
    
    try:
        socketio.run(app, debug=False, host='127.0.0.1', port=5002, allow_unsafe_werkzeug=True)
    finally:
        camera_running = False
        if TEMP_SNAPSHOT.exists():
            TEMP_SNAPSHOT.unlink()
