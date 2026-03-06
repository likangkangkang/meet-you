# Meet You - 智能相册

一眼是你，满目是你

## 功能特性

- 📷 摄像头人脸识别
- 🖼️ 智能照片匹配
- 🎨 优雅的照片轮播
- 📱 支持 Web 和 Android

## Web 版使用

```bash
cd meet-you
python3 app.py
```

访问 http://127.0.0.1:5002

## Android 版打包

使用 GitHub Actions 自动打包：

1. 推送代码到 GitHub
2. 进入 Actions 标签页
3. 运行 "Build Android APK" workflow
4. 下载生成的 APK

## 照片准备

将照片放入 `photos` 目录，支持 JPG、PNG 格式。

## 技术栈

- **Web 版**: Flask + Socket.IO + face_recognition
- **Android 版**: Kivy + KivyMD + OpenCV
- **人脸识别**: face_recognition (基于 dlib)

## 许可证

MIT License
