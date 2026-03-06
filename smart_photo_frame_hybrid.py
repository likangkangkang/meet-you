#!/usr/bin/env python3
"""
Meet You - 智能相册
一眼是你，满目是你
"""

import cv2
import face_recognition
import time
from pathlib import Path
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import simpledialog
from threading import Thread
import random
import json

class SmartPhotoFrame:
    def __init__(self):
        # 配置
        self.config = {
            "photo_dir": "photos",
            "display_time": 5,
            "window_width": 1024,
            "window_height": 768,
            "camera_index": 0,
            "face_timeout": 600,  # 10分钟未出现则移除
            "match_tolerance": 0.6  # 人脸匹配容差
        }
        
        # 初始化
        self.temp_faces = {}  # 临时人脸库 {person_id: {"encoding": [], "name": "", "last_seen": time}}
        self.person_counter = 0  # 人物计数器
        self.photo_database = {}
        self.current_viewer = None
        self.current_photos = []
        self.current_photo_index = 0
        self.running = True
        
        # 加载人物名称映射（如果存在）
        self.load_person_names()
        
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
        
        # 启动清理线程
        self.cleanup_thread = Thread(target=self.cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def load_person_names(self):
        """加载人物名称映射"""
        names_file = Path("person_names.json")
        if names_file.exists():
            try:
                with open(names_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 恢复临时人脸库
                    for person_id, info in data.items():
                        self.temp_faces[person_id] = {
                            "encoding": info["encoding"],
                            "name": info["name"],
                            "last_seen": time.time()
                        }
                    self.person_counter = len(self.temp_faces)
                print(f"✓ 加载了 {len(self.temp_faces)} 个已识别人物")
            except Exception as e:
                print(f"✗ 加载人物名称失败: {e}")
    
    def save_person_names(self):
        """保存人物名称映射"""
        try:
            data = {}
            for person_id, info in self.temp_faces.items():
                data[person_id] = {
                    "encoding": info["encoding"].tolist(),
                    "name": info["name"]
                }
            
            with open("person_names.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("✓ 保存人物名称成功")
        except Exception as e:
            print(f"✗ 保存人物名称失败: {e}")
    
    def scan_photos(self):
        """扫描照片目录"""
        photo_dir = Path(self.config["photo_dir"])
        if not photo_dir.exists():
            photo_dir.mkdir(parents=True)
            print(f"请在 {photo_dir} 目录下放置照片")
            print("照片可以按人物分类，例如：photos/康康/photo1.jpg")
            return
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        
        for photo_file in photo_dir.rglob("*"):
            if photo_file.suffix.lower() in image_extensions:
                # 从路径提取可能的人物标签
                tags = self.extract_tags_from_path(photo_file)
                
                self.photo_database[str(photo_file)] = {
                    "tags": tags,
                    "path": str(photo_file),
                    "name": photo_file.name
                }
        
        print(f"✓ 扫描到 {len(self.photo_database)} 张照片")
    
    def extract_tags_from_path(self, photo_path):
        """从文件路径提取标签"""
        tags = []
        path_parts = photo_path.parts
        
        # 提取目录名作为标签
        for part in path_parts:
            if part != self.config["photo_dir"] and part != photo_path.name:
                tags.append(part)
        
        return tags if tags else ["所有人"]
    
    def setup_ui(self):
        """设置 UI"""
        self.root = tk.Tk()
        self.root.title("智能电子相册 - 混合识别")
        self.root.geometry(f"{self.config['window_width']}x{self.config['window_height']}")
        self.root.configure(bg='black')
        
        # 照片显示区域
        self.photo_label = tk.Label(self.root, bg='black')
        self.photo_label.pack(expand=True, fill='both')
        
        # 信息显示区域
        self.info_frame = tk.Frame(self.root, bg='black')
        self.info_frame.pack(side='bottom', fill='x', pady=10)
        
        self.info_label = tk.Label(
            self.info_frame,
            text="正在识别观看者...",
            font=("Arial", 16),
            fg='white',
            bg='black'
        )
        self.info_label.pack(side='left', padx=20)
        
        # 命名按钮
        self.name_button = tk.Button(
            self.info_frame,
            text="给当前观看者命名",
            command=self.name_current_viewer,
            font=("Arial", 12),
            bg='#667eea',
            fg='white',
            relief='flat',
            padx=15,
            pady=5
        )
        self.name_button.pack(side='right', padx=20)
        
        # 绑定键盘事件
        self.root.bind('<Escape>', lambda e: self.quit())
        self.root.bind('<space>', lambda e: self.next_photo())
        self.root.bind('<Left>', lambda e: self.prev_photo())
        self.root.bind('<Right>', lambda e: self.next_photo())
        self.root.bind('<n>', lambda e: self.name_current_viewer())
    
    def face_recognition_loop(self):
        """人脸识别循环"""
        video_capture = cv2.VideoCapture(self.config["camera_index"])
        
        if not video_capture.isOpened():
            print("⚠️  无法打开摄像头，将展示所有照片")
            self.current_viewer = "所有人"
            self.update_photo_list()
            return
        
        print("✓ 摄像头已启动")
        print("💡 提示：识别到新人后，按 'N' 键可以给TA命名")
        
        frame_count = 0
        while self.running:
            ret, frame = video_capture.read()
            if not ret:
                break
            
            frame_count += 1
            if frame_count % 30 != 0:  # 每30帧识别一次
                continue
            
            # 缩小图像提高速度
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # 检测人脸
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            if face_encodings:
                face_encoding = face_encodings[0]
                
                # 与临时人脸库比对
                person_id = self.match_or_create_person(face_encoding)
                person_info = self.temp_faces[person_id]
                
                # 更新最后出现时间
                person_info["last_seen"] = time.time()
                
                # 获取显示名称
                display_name = person_info["name"] if person_info["name"] else f"访客{person_id}"
                
                # 更新当前观看者
                if display_name != self.current_viewer:
                    self.current_viewer = display_name
                    self.update_photo_list()
                    print(f"👤 检测到: {display_name}")
            else:
                # 没有检测到人脸
                if self.current_viewer != "所有人":
                    self.current_viewer = "所有人"
                    self.update_photo_list()
            
            time.sleep(0.1)
        
        video_capture.release()
    
    def match_or_create_person(self, face_encoding):
        """匹配或创建新人物"""
        # 与已知人脸比对
        for person_id, info in self.temp_faces.items():
            known_encoding = info["encoding"]
            match = face_recognition.compare_faces(
                [known_encoding],
                face_encoding,
                tolerance=self.config["match_tolerance"]
            )[0]
            
            if match:
                return person_id
        
        # 未匹配到，创建新人物
        self.person_counter += 1
        person_id = str(self.person_counter)
        
        self.temp_faces[person_id] = {
            "encoding": face_encoding,
            "name": "",  # 未命名
            "last_seen": time.time()
        }
        
        print(f"✨ 检测到新人物: 访客{person_id}")
        return person_id
    
    def name_current_viewer(self):
        """给当前观看者命名"""
        if not self.current_viewer or self.current_viewer == "所有人":
            print("⚠️看者")
            return
        
        # 查找当前观看者的 person_id
        person_id = None
        for pid, info in self.temp_faces.items():
            display_name = info["name"] if info["name"] else f"访客{pid}"
            if display_name == self.current_viewer:
                person_id = pid
                break
        
        if not person_id:
            return
        
        # 弹出对话框输入名字
        name = simpledialog.askstring(
            "命名",
            f"请为 {self.current_viewer} 输入名字：",
            parent=self.root
        )
        
        if name and name.strip():
            self.temp_faces[person_id]["name"] = name.strip()
            self.current_viewer = name.strip()
            self.save_person_names()
            self.update_photo_list()
            print(f"✓ 已命名: {name.strip()}")
    
    def cleanup_loop(self):
        """清理长时间未出现的人脸"""
        while self.running:
            time.sleep(60)  # 每分钟检查一次
            
            current_time = time.time()
            to_remove = []
            
            for person_id, info in self.temp_faces.items():
                if current_time - info["last_seen"] > self.config["face_timeout"]:
                    to_remove.append(person_id)
            
            for person_id in to_remove:
                name = self.temp_faces[person_id]["name"] or f"访客{person_id}"
                del self.temp_faces[person_id]
                print(f"🗑️  移除长时间未出现的人物: {name}")
    
    def update_photo_list(self):
        """更新照片列表"""
        if not self.current_viewer or self.current_viewer == "所有人":
            self.current_photos = list(self.photo_database.keys())
        else:
            # 筛选包含当前观看者标签的照片
            self.current_photos = [
                photo_path for photo_path, info in self.photo_database.items()
                if self.current_viewer in info["tags"] or "所有人" in info["tags"]
            ]
            
            # 如果没有相关照片，展示所有照片
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
            
            # 显示识别的人数
            active_count = len([p for p in self.temp_faces.values() 
                              if time.time() - p["last_seen"] < 60])
            
            info_text = f"👤 {self.current_viewer}  |  📸 {self.current_photo_index + 1}/{len(self.current_photos)}  |  👥 已识别 {len(self.temp_faces)} 人 (活跃 {active_count})"
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
        print("\n💾 保存人物信息...")
        self.save_person_names()
        self.running = False
        self.root.quit()
    
    def run(self):
        """运行相册"""
        print("\n" + "="*60)
        print("🖼️  智能电子相册 - 混合识别模式")
        print("="*60)
        print("\n特性:")
        print("  ✨ 无需预先录入人脸")
        print("  🎯 自动识别并记住新人")
        print("  📝 可以给识别的人命名")
        print("  🔄 自动清理长时间未出现的人")
        print("\n快捷键:")
        print("  空格 / 右箭头: 下一张")
        print("  左箭头: 上一张")
        print("  N: 给当前观看者命名")
        print("  ESC: 退出")
        print("\n" + "="*60 + "\n")
        
        self.root.mainloop()

def main():
    """主函数"""
    print("🖼️  智能电子相册 v2.0 - 混合识别")
    print("="*60)
    
    frame = SmartPhotoFrame()
    frame.run()

if __name__ == "__main__":
    main()
