#!/usr/bin/env python3
"""
Meet You - Android 版（简化版）
一眼是你，满目是你
"""

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.clock import Clock
from pathlib import Path
import random

class MeetYouApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.photo_dir = Path("photos")
        self.current_photos = []
        self.current_index = 0
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
        
        # 扫描照片
        self.scan_photos()
        
        # 开始轮播
        if self.current_photos:
            Clock.schedule_once(lambda dt: self.start_slideshow(), 1)
        
        return self.root
    
    def scan_photos(self):
        """扫描照片目录"""
        if not self.photo_dir.exists():
            self.photo_dir.mkdir()
            print(f"请将照片放入 {self.photo_dir} 目录")
            return
        
        print("正在扫描照片...")
        for photo_path in self.photo_dir.glob("*"):
            if photo_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                self.current_photos.append(str(photo_path))
        
        print(f"扫描完成，共 {len(self.current_photos)} 张照片")
    
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

if __name__ == '__main__':
    MeetYouApp().run()
