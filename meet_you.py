#!/usr/bin/env python3
"""
Meet You - 智能相册
一眼是你，满目是你
"""

import face_recognition
import time
from pathlib import Path
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import simpledialog
from threading import Thread
import random
import json
import numpy as np

class MeetYou:
    def __init__(self):
        # 配置
        self.config = {
            "photo_dir": "photos",
            "display_time": 5,
            "window_width": 1024,
            "window_height": 768,
            "face_timeout": 600,
            "match_tolerance": 0.6
        }
        
        # 初始化
        self.temp_faces = {}
        self.person_counter = 0
        self.photo_database = {}
        self.current_viewer = None
        self.current_photos = []
        self.current_photo_index = 0
        self.running = True
        
        # 加载人物名称映射
        self.load_person_names()
        
        # 扫描照片
        self.scan_photos()
        
        # 初始化 UI
        self.setup_ui()
        
        # 启动人脸识别线程（使用图片而非摄像头）
        self.recognition_thread = Thread(target=self.face_recognition_loop, daemon=True)
        self.recognition_thread.start()
        
        # 启动照片轮播
        self.start_slideshow()
    
    def load_person_names(self):
        """加载人物名称映射"""
        try:
            with open("person_names.json", "r", encoding="utf-8") as f:
                self.person_names = json.load(f)
        except FileNotFoundError:
            self.person_names = {}
    
    def save_person_names(self):
        """保存人物名称映射"""
        with open("person_names.json", "w", encoding="utf-8") as f:
            json.dump(self.person_names, f, ensure_ascii=False, indent=2)
    
    def scan_photos(self):
        """扫描照片目录并提取人脸特征"""
        photo_dir = Path(self.config["photo_dir"])
        if not photo_dir.exists():
            photo_dir.mkdir()
            print(f"请将照片放入 {photo_dir} 目录")
            return
        
        print("正在扫描照片...")
        for photo_path in photo_dir.glob("*"):
            if photo_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                try:
                    image = face_recognition.load_image_file(str(photo_path))
                    face_encodings = face_recognition.face_encodings(image)
                    
                    self.photo_database[str(photo_path)] = {
                        "path": photo_path,
                        "faces": face_encodings
                    }
                except Exception as e:
                    print(f"处理照片 {photo_path} 时出错: {e}")
        
        print(f"扫描完成，共 {len(self.photo_database)} 张照片")
    
    def setup_ui(self):
        """设置用户界面"""
        self.root = tk.Tk()
        self.root.title("Meet You - 一眼是你，满目是你")
        self.root.geometry(f"{self.config['window_width']}x{self.config['window_height']}")
        self.root.configure(bg="black")
        
        # 照片显示区域
        self.photo_label = tk.Label(self.root, bg="black")
        self.photo_label.pack(expand=True, fill="both")
        
        # 欢迎信息
        self.info_label = tk.Label(
            self.root,
            text="Meet You\n一眼是你，满目是你",
            font=("Arial", 24),
            fg="white",
            bg="black"
        )
        self.info_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # 绑定退出事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind("<Escape>", lambda e: self.on_closing())
    
    def face_recognition_loop(self):
        """人脸识别循环（简化版，不使用摄像头）"""
        # 这个版本先不做实时识别，只做照片展示
        # 后续可以添加摄像头支持
        pass
    
    def get_photos_for_person(self, person_id):
        """获取包含特定人物的照片"""
        if person_id not in self.temp_faces:
            return []
        
        person_encoding = self.temp_faces[person_id]["encoding"]
        matching_photos = []
        
        for photo_path, photo_data in self.photo_database.items():
            for face_encoding in photo_data["faces"]:
                match = face_recognition.compare_faces(
                    [person_encoding],
                    face_encoding,
                    tolerance=self.config["match_tolerance"]
                )
                if match[0]:
                    matching_photos.append(photo_data["path"])
                    break
        
        return matching_photos
    
    def start_slideshow(self):
        """开始照片轮播"""
        if not self.photo_database:
            return
        
        # 随机选择照片
        all_photos = [data["path"] for data in self.photo_database.values()]
        self.current_photos = random.sample(all_photos, min(len(all_photos), 50))
        self.current_photo_index = 0
        
        self.show_next_photo()
    
    def show_next_photo(self):
        """显示下一张照片"""
        if not self.current_photos or not self.running:
            return
        
        photo_path = self.current_photos[self.current_photo_index]
        
        try:
            # 加载并调整照片大小
            image = Image.open(photo_path)
            
            # 保持宽高比缩放
            img_width, img_height = image.size
            window_width = self.config["window_width"]
            window_height = self.config["window_height"]
            
            scale = min(window_width / img_width, window_height / img_height)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            # 显示照片
            self.photo_label.configure(image=photo)
            self.photo_label.image = photo
            
            # 隐藏欢迎信息
            self.info_label.place_forget()
            
        except Exception as e:
            print(f"显示照片时出错: {e}")
        
        # 下一张
        self.current_photo_index = (self.current_photo_index + 1) % len(self.current_photos)
        
        # 定时切换
        self.root.after(self.config["display_time"] * 1000, self.show_next_photo)
    
    def on_closing(self):
        """关闭窗口"""
        self.running = False
        self.save_person_names()
        self.root.destroy()
    
    def run(self):
        """运行应用"""
        self.root.mainloop()

if __name__ == "__main__":
    app = MeetYou()
    app.run()
