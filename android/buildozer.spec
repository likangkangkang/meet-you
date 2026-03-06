[app]

# 应用名称
title = Meet You

# 包名
package.name = meetyou

# 包域名
package.domain = com.meetyou

# 源代码目录
source.dir = .

# 源代码包含的文件
source.include_exts = py,png,jpg,kv,atlas

# 版本号
version = 1.0.0

# 版本代码
version.code = 1

# 应用需要的权限
android.permissions = CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# 支持的 Android API 级别
android.api = 31
android.minapi = 21

# Android NDK 版本
android.ndk = 25b

# 是否接受 Android SDK 许可
android.accept_sdk_license = True

# 应用图标
#icon.filename = %(source.dir)s/data/icon.png

# 启动画面
#presplash.filename = %(source.dir)s/data/presplash.png

# 方向（landscape, portrait, all）
orientation = portrait

# 全屏模式
fullscreen = 0

# Python 依赖
requirements = python3,kivy,kivymd,pillow,opencv-python,face-recognition,numpy

# Android 架构
android.archs = arm64-v8a,armeabi-v7a

# 日志级别
log_level = 2

# 是否使用 Android 的 wakelock
android.wakelock = False

[buildozer]

# 日志级别
log_level = 2

# 警告级别
warn_on_root = 1
