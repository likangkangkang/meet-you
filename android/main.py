#!/usr/bin/env python3
"""
Meet You - Android 版
一眼是你，满目是你
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.window import Window
import face_recognition
import cv2
from pathlib import Path
import random
import time

class MeetYouApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.photo_dir = Path("photos")
        self.photo_database = {}
        self.current_photos = []
        self.current_index = 0
        self.camera = None
        self.camera_enabled = False
        self.current_viewer = None
        self.display_time = 5  # 秒
        
    def build(self):
        # 主布局
        self.root = FloatLayout()
        
        # 照片显示区域
        self.photo_image = Image(
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        self.root.add_widget(self.photo_image)
        
        # 欢迎信息
        self.welcome_label = Label(
            text='Meet You\n一眼是你，满目是你',
            font_size='32sp',
            size_hint=(None, None),
            size=(400, 200),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.root.add_widget(self.welcome_label)
        
        # 识别标识（左上角）
        self.viewer_badge = Label(
            text='',
            font_size='16sp',
            size_hint=(None, None),
            size=(200, 50),
            pos_hint={'x': 0.02, 'top': 0.98},
            opacity=0
        )
        self.root.add_widget(self.viewer_badge)
        
        # 控制按钮（右上角）
        self.camera_btn = Button(
            text='开启识别',
            font_size='16sp',
            size_hint=(None, None),
            size=(120, 50),
            pos_hint={'right': 0.98, 'top': 0.98},
            background_color=(0.4, 0.5, 0.9, 1)
        )
        self.camera_btn.bind(on_press=self.toggle_camera)
        self.root.add_widget(self.camera_btn)
        
        # 扫描照片
        self.scan_photos()
        
        # 开始轮播
        if self.photo_database:
            self.current_photos = list(self.photo_database.keys())
            Clock.schedule_once(lambda dt: self.start_slideshow(), 1)
        
        return self.root
    
    def scan_photos(self):
        """扫描照片目录并提取人脸特征"""
        if not self.photo_dir.exists():
            self.photo_dir.mkdir()
            print(f"请将照片放入 {self.photo_dir} 目录")
            return
        
        print("正在扫描照片...")
        for photo_path in self.photo_dir.glob("*"):
            if photo_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                try:
                    image = face_recognition.load_image_file(str(photo_path))
                    face_encodings = face_recognition.face_encodings(image)
                    
                    if face_encodings:
                        self.photo_database[str(photo_path)] = {
                            "path": str(photo_path),
                            "faces": face_encodings
                        }
                except Exception as e:
                    print(f"处理照片 {photo_path} 时出错: {e}")
        
        print(f"扫描完成，共 {len(self.photo_database)} 张包含人脸的照片")
    
    def start_slideshow(self):
        """开始照片轮播"""
        if not self.current_photos:
            return
        
        self.welcome_label.opacity = 0
        self.show_photo(0)
        Clock.schedule_interval(self.next_photo, self.display_time)
    
    def show_photo(self, index):
        """显示指定索引的照片"""
        if not self.current_photos or index >= len(self.current_photos):
            return
        
        photo_path = self.current_photos[index]
        self.photo_image.source = photo_path
        self.current_index = index
    
    def next_photo(self, dt):
        """显示下一张照片"""
        self.current_index = (self.current_index + 1) % len(self.current_photos)
        self.show_photo(self.current_index)
    
    def toggle_camera(self, instance):
        """切换摄像头识别"""
        self.camera_enabled = not self.camera_enabled
        
        if self.camera_enabled:
            self.camera_btn.text = '识别中'
            self.camera_btn.background_color = (0.3, 0.8, 0.3, 1)
            self.start_camera()
        else:
            self.camera_btn.text = '开启识别'
            self.camera_btn.background_color = (0.4, 0.5, 0.9, 1)
            self.stop_camera()
    
    def start_camera(self):
        """启动摄像头识别"""
        try:
            self.camera = cv2.VideoCapture(0)
            Clock.schedule_interval(self.process_camera, 2.0)  # 每2秒识别一次
            print("✅ 摄像头已启动")
 ept Exception as e:
            print(f"❌ 摄像头启动失败: {e}")
            self.camera_enabled = False
    
    def stop_camera(self):
        """停止摄像头识别"""
        Clock.unschedule(self.process_camera)
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.viewer_badge.opacity = 0
        self.current_viewer = None
        self.current_photos = list(self.photo_database.keys())
        print("⏸️  摄像头已停止")
    
    def process_camera(self, dt):
        """处理摄像头帧"""
        if not self.camera or not self.camera.isOpened():
            return
              ret, frame = self.camera.read()
        if not ret:
            return
        
        # 缩小图像以加快处理速度
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # 检测人脸
        face_encodings = face_recognition.face_encodings(rgb_small_frame)
        
        if not face_encodings:
            if self.current_viewer is not None:
                self.current_viewer = None
                self.viewer_badge.opacity = 0
                self.current_photos = list(self.photo_database.keys())
            return
        
        # 使用第一个检测到的人脸
        viewer_encoding = face_encodings[0]
        
        # 查找匹配的照片
        matching_photos = []
        for photo_path, photo_data in self.photo_database.items():
            for face_encoding in photo_data["faces"]:
                matches = face_recognition.compare_faces(
                    [face_encoding],
                    viewer_encoding,
                    tolerance=0.6
                )
                if matches[0]:
                    matching_photos.append(photo_path)
                    break
        
        # 更新当前观看者
        if matching_photos:
            viewer_id = viewer_encoding.tobytes()
            if self.current_viewer != viewer_id:
                self.current_viewer = viewer_id
                self.current_photos = matching_photos
                
                self.viewer_badge.text = f'✓ 访客 {len(matching_photos)} 张照片'
                self.viewer_badge.opacity = 1
                
                print(f"✅ 检测到观看者，匹配到 {len(matching_photos)} 张照片")
    
    def on_stop(self):
        """应用关闭时清理资源"""
        if self.camera:
            self.camera.release()

if __name__ == '__main__':
    MeetYouApp().run()
