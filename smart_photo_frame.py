#!/usr/bin/env python3
"""
智能电子相册 - 根据观看者展示个性化照片
"""

import cv2
import face_recognition
import os
import time
from pathlib import Path
from PIL import Image, ImageTk
import tkinter as tk
from threading import Thread
import random

class SmartPhotoFrame:
    def __init__(self):
        # 配置
        self.config = {
            "photo_dir": "photos",
            "faces_dir": "known_faces",
            "display_time": 5,
            "window_width": 1024,
            "window_height": 768,
            "camera_index": 0
        }
        
        # 初始化
        self.known_faces = {}
        self.photo_database = {}
        self.current_viewer = None
        self.current_photos = []
        self.current_photo_index = 0
        self.running = True
        
        # 加载已知人脸
        self.load_known_faces()
        
        # 扫描照片
        self.scan_photos()
        
        # 初始化 UI
        self.setup_ui()
        
        # 启动人脸识别线程
        self.recognition_thread = Thread(target=self.face_recognition_loop, daemon=True)
        self.recognition_thread.start()
        
        # 启动照片轮播线程
        self.slideshow_thread = Thread(target=self.slideshow_loop, daemon=True)
        self.slideshow_thread.start()
    
    def load_known_faces(self):
        """加载已知人脸"""
        faces_dir = Path(self.config["faces_dir"])
        if not faces_dir.exists():
            faces_dir.mkdir(parents=True)
            print(f"请在 {faces_dir} 目录下放置家庭成员照片")
            print("文件名格式：爸爸.jpg, 妈妈.jpg, 孩子.jpg")
            return
        
        for face_file in faces_dir.glob("*.jpg"):
            name = face_file.stem
            try:
                image = face_recognition.load_image_file(str(face_file))
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    self.known_faces[name] = encodings[0]
                    print(f"✓ 加载人脸: {name}")
                else:
                    print(f"✗ 未检测到人脸: {name}")
            except Exception as e:
                print(f"✗ 加载失败 {name}: {e}")
        
        if not self.known_faces:
            print("⚠️  未找到已知人脸，将展示所有照片")
    
    def scan_photos(self):
        """扫描照片目录"""
        photo_dir = Path(self.config["photo_dir"])
        if not photo_dir.exists():
            photo_dir.mkdir(parents=True)
            print(f"请在 {photo_dir} 目录下放置照片")
            return
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        
        for photo_file in photo_dir.rglob("*"):
            if photo_file.suffix.lower() in image_extensions:
                people = self.extract_people_from_path(photo_file)
                
                self.photo_database[str(photo_file)] = {
                    "people": people,
                    "path": str(photo_file),
                    "name": photo_file.name
                }
        
        print(f"✓ 扫描到 {len(self.photo_database)} 张照片")
    
    def extract_people_from_path(self, photo_path):
        """从文件路径提取关联的人"""
        people = []
        path_str = str(photo_path)
        
        for name in self.known_faces.keys():
            if name in path_str:
                people.append(name)
        
        return people if people else ["所有人"]
    
    def setup_ui(self):
        """设置 UI"""
        self.root = tk.Tk()
        self.root.title("智能电子相册")
        self.root.geometry(f"{self.config['window_width']}x{self.config['window_height']}")
        self.root.configure(bg='black')
        
        # 照片显示区域
        self.photo_label = tk.Label(self.root, bg='black')
        self.photo_label.pack(expand=True, fill='both')
        
        # 信息显示区域
        self.info_label = tk.Label(
            self.root, 
            text="正在识别观看者...", 
            font=("Arial", 16),
            fg='white',
            bg='black'
        )
        self.info_label.pack(side='bottom', pady=10)
        
        # 绑定键盘事件
        self.root.bind('<Escape>', lambda e: self.quit())
        self.root.bind('<space>', lambda e: self.next_photo())
        self.root.bind('<Left>', lambda e: self.prev_photo())
        self.root.bind('<Right>', lambda e: self.next_photo())
    
    def face_recognition_loop(self):
        """人脸识别循环"""
        video_capture = cv2.VideoCapture(self.config["camera_index"])
        
        if not video_capture.isOpened():
            print("⚠️  无法打开摄像头，将展示所有照片")
            self.current_viewer = "所有人"
            self.update_photo_list()
            return
        
        print("✓ 摄像头已启动")
        
        frame_count = 0
        while self.running:
            ret, frame = video_capture.read()
            if not ret:
                break
            
            frame_count += 1
            if frame_count % 30 != 0:
                continue
            
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            if face_encodings:
                face_encoding = face_encodings[0]
                
                matches = face_recognition.compare_faces(
                    list(self.known_faces.values()), 
                    face_encoding,
                    tolerance=0.6
                )
                
                name = "未知访客"
                if True in matches:
                    match_index = matches.index(True)
                    name = list(self.known_faces.keys())[match_index]
                
                if name != self.current_viewer:
                    self.current_viewer = name
                    self.update_photo_list()
                    print(f"👤 检测到: {name}")
            else:
                if self.current_viewer != "所有人":
                    self.current_viewer = "所有人"
                    self.update_photo_list()
            
            time.sleep(0.1)
        
        video_capture.release()
    
    def update_photo_list(self):
        """更新照片列表"""
        if not self.current_viewer:
            self.current_photos = list(self.photo_database.keys())
        else:
            self.current_photos = [
                photo_path for photo_path, info in self.photo_database.items()
                if self.current_viewer in info["people"] or "所有人" in info["people"]
            ]
            
            if not self.current_photos:
                self.current_photos = list(self.photo_database.keys())
        
        random.shuffle(self.current_photos)
        self.current_photo_index = 0
        
        print(f"📸 为 {self.current_viewer} 准备了 {len(self.current_photos)} 张照片")
    
    def slideshow_loop(self):
        """照片轮播循环"""
        while self.running:
            if self.current_photos:
                self.show_current_photo()
            time.sleep(self.config["display_time"])
            self.next_photo()
    
    def show_current_photo(self):
        """显示当前照片"""
        if not self.current_photos:
            return
        
        photo_path = self.current_photos[self.current_photo_index]
        photo_info = self.photo_database[photo_path]
        
        try:
            image = Image.open(photo_path)
            image.thumbnail(
                (self.config["window_width"], self.config["window_height"] - 100),
                Image.Resampling.LANCZOS
            )
            
            photo = ImageTk.PhotoImage(image)
            
            self.photo_label.config(image=photo)
            self.photo_label.image = photo
            
            info_text = f"👤 {self.current_viewer} 正在观看  |  📸 {self.current_photo_index + 1}/{len(self.current_photos)}  |  {photo_info['name']}"
            self.info_label.config(text=info_text)
            
        except Exception as e:
            print(f"✗ 加载照片失败 {photo_path}: {e}")
    
    def next_photo(self):
        """下一张照片"""
        if self.current_photos:
            self.current_photo_index = (self.current_photo_index + 1) % len(self.current_photos)
    
    def prev_photo(self):
        """上一张照片"""
        if self.current_photos:
            self.current_photo_index = (self.current_photo_index - 1) % len(self.current_photos)
    
    def quit(self):
        """退出程序"""
        self.running = False
        self.root.quit()
    
    def run(self):
        """运行相册"""
        print("\n" + "="*50)
        print("🖼️  智能电子相册已启动")
        print("="*50)
        print("\n快捷键:")
        print("  空格 / 右箭头: 下一张")
        print("  左箭头: 上一张")
        print("  ESC: 退出")
        print("\n" + "="*50 + "\n")
        
        self.root.mainloop()

def main():
    """主函数"""
    print("🖼️  智能电子相册 v1.0")
    print("="*50)
    
    frame = SmartPhotoFrame()
    frame.run()

if __name__ == "__main__":
    main()
