<div align="center">
  <h1>🖼️ 序列帧预览器 v2.2 | Image Sequence Previewer v2.2</h1>
  
  <a href="#中文"><img src="https://img.shields.io/badge/🇨🇳_中文-Click_Here-blue?style=for-the-badge" alt="中文版"></a>
  <a href="#english"><img src="https://img.shields.io/badge/🇬🇧_English-Click_Here-blue?style=for-the-badge" alt="English"></a>
  <br><br>

  <h3>点击查看视频简介 / Click to view Video Intro：</h3>
  <a href="https://www.youtube.com/watch?v=sDCH1o2Clfs">
    <img src="https://img.youtube.com/vi/sDCH1o2Clfs/maxresdefault.jpg" width="400" />
  </a>
</div>

<br><br>
## <a href="https://www.creem.io/payment/prod_1P9jWo3dzuXhPZOzIegw9f">Support me on Creem </a><br>thanks<br>

# 中文<br>
一款轻量、优雅且极其迅速的序列帧预览工具，专为动画师和动态图形设计师打造。无需繁琐地打开 After Effects 或 Premiere Pro，拖入即可瞬间流畅回放你的渲染序列！<br>
快去Release中下载体验吧！～！～！～！～！～！～！～！～！～！～！～！～！～
<br><br>

## 界面预览<br>
<img width="957" height="645" alt="Screenshot 2026-06-30 101710" src="https://github.com/user-attachments/assets/86d01ca6-ce44-4e34-8f8a-c6886f40940b" />
<br><br>

### ✨ v2.2 更新日志<br>
✨ EXR 格式支持：全新引入 OpenCV 引擎，支持读取工业级 EXR 序列，自动进行 Gamma 2.2 校正，并完美兼容带 Alpha 透明通道及包含负数极值的渲染图。<br>
✂️ 入点与出点设置：新增专业级出入点功能。按 I / O 键或在时间线上直接拖拽方括号即可设置范围，支持仅在设定范围内进行循环回放与视频导出。<br>
🔽 后台托盘驻留：点击关闭按钮现在会将软件隐藏至系统任务栏托盘，并自动暂停后台播放，实现零额外性能占用。<br>
💡 帮助面板与记忆功能：底部新增“帮助”按钮以随时查看快捷键；软件现在会自动记忆上一次关闭前使用的帧速率设置。<br><br>

✨ v2.1 更新日志<br>
✨ 悬浮帧数显示：时间轴上方新增跟随播放头的气泡提示，实时精准显示原文件名的帧号。<br>
🔄 刷新序列功能：底部控制栏新增“刷新”按钮，支持一键重新加载当前序列文件。<br>
🗑️ 一键清空与重置：新增“清空”按钮，点击即可快速释放占用的内存，并将软件界面恢复至初始状态。<br>
🧠 智能导出命名：优化了导出逻辑，导出文件不再默认命名为“output”，而是自动抓取源文件名作为智能前缀。<br><br>

✨ v2.0 更新日志<br>
沉浸式预览模式： 一键隐藏所有 UI 控件，享受纯粹、无干扰的全屏播放体验（按 ESC 即可恢复）。<br>
强大的导出引擎： 现在你可以将序列帧直接压制导出为 MP4、MOV（完美支持 Alpha 透明通道！）以及 GIF 格式。<br>
全面支持 Apple Silicon： 现已适配 Mac M 系列芯片。<br>
现代高级 UI： 全新重构的深色模式界面。<br><br>

### 🚀 核心功能<br>
极简拖拽： 将序列中的任意一帧拖入窗口，软件将自动读取并加载完整序列。<br>
回放控制： 支持自定义帧速率（10fps ~ 120fps），完美匹配你的工程设置。<br>
背景切换： 支持透明网格、纯黑、纯白、纯绿、红、蓝背景，方便随时检查画面边缘与抠像细节。<br>
智能缩放： 支持自适应窗口大小或指定百分比缩放。<br>
中英双语： UI 一键无缝切换。<br><br>

### 📥 下载与安装<br>
请前往 Releases 页面下载适合你操作系统的最新版本：<br>
Windows (x86_64)<br>
macOS (Apple Silicon)<br>
Mac 用户贴士：作为独立开发者软件，首次打开时可能会遇到苹果的安全拦截。若您遇到拦截，请在终端执行 sudo xattr -rd com.apple.quarantine /Applications/FramePreviewer.app 即可完美解除限制。<br><br>

### 🛠️ 技术栈<br>
Python 3 & PyQt6<br>
FFmpeg（已内置跨平台独立组件，提供极速渲染）<br><br>

### 💬 联系作者<br>
由 舟午YueMoon 开发。<br>
如果你有任何建议、遇到了 BUG，或者单纯想催更，欢迎在B站/Youtube相关视频的评论区告诉我！<br>
博客：http://yuemoon.vip/<br>
GitHub：@YueMoon99<br>
B站：UID223633562<br>
YouTube：@YueMoon99<br><br>

# English<br>
A lightweight, elegant, and blazing-fast image sequence previewer designed for animators and motion graphic designers. Instantly playback your rendered sequences without firing up heavy software like After Effects or Premiere Pro!<br><br>

## UI Preview<br>
<img width="973" height="645" alt="Screenshot 2026-06-30 101717" src="https://github.com/user-attachments/assets/36e3c054-0a2c-4035-beb1-de33aa13d662" />
<br><br>

### ✨ What's New in v2.2<br>
✨ EXR Format Support: Introduced OpenCV engine to support industrial EXR sequences. Features automatic Gamma 2.2 correction and full compatibility with Alpha channels and negative exposure values.<br>
✂️ In/Out Points: Added professional In/Out point functionality. Press I / O or drag the brackets directly on the timeline to set the range. Playback and exports can now be restricted to this designated area.<br>
🔽 System Tray Integration: Clicking the close button now minimizes the application to the system tray and automatically pauses background playback to save system resources.<br><br>
💡 Help Panel & Memory: Added a "Help" button for quick access to shortcuts; the application now automatically remembers your last used FPS setting upon exit.<br><br>

✨ What's New in v2.1<br>
✨ Floating Frame Indicator: Added a dynamic tooltip above the timeline playhead that displays the original file's frame number in real-time.<br>
🔄 Refresh Sequence: Added a "Refresh" button in the control bar to quickly reload the currently loaded image sequence.<br>
🗑️ Clear & Reset: Added a "Clear" button to flush RAM usage and restore the application to its initial default state.<br>
🧠 Smart Export Naming: Exported files now automatically extract and adopt the original sequence's filename prefix instead of defaulting to "output".<br><br>

✨ What's New in v2.0<br>
Immersive Preview Mode: Hide the UI with a single click for a clean, distraction-free playback experience (Press ESC to restore).<br>
Powerful Export Engine: Render your sequences directly into MP4, MOV (with Alpha Channel support for transparency!), or GIF formats.<br>
Apple Silicon Support: Fully optimized for macOS M-series Chips.<br>
Sleek Modern UI: Completely redesigned dark theme with custom typography.<br><br>

### 🚀 Key Features<br>
Drag & Drop: Drop any single frame of your sequence into the window, and it automatically loads the entire sequence.<br>
Playback Controls: Customizable FPS (10 ~ 120fps) to match your project settings.<br>
Background Customization: Switch between Transparent Grid, Solid Black, White, Green, Red, or Blue to check edge details.<br>
Smart Zoom: Fit to window or scale to specific percentages.<br>
Bilingual: Switch seamlessly between English and Chinese.<br><br>

### 📥 Download & Install<br>
Head over to the Releases page to download the latest version for your operating system:<br>
Windows (x86_64)<br>
macOS (Only for Apple Silicon now)<br><br>

Note for macOS users: Since this is an indie-developed app, you might see a security warning on the first launch. Please run sudo xattr -rd com.apple.quarantine /Applications/FramePreviewer.app in your terminal if macOS blocks the app.<br>

### 🛠️ Built With<br>
Python 3 & PyQt6<br>
FFmpeg (Bundled natively for high-speed encoding)<br>
💬 Contact & Support<br>
Created by YueMoon.<br>
If you have any feedback or feature requests, feel free to contact!<br><br>

### 💬 Contact<br>
Blog：http://yuemoon.vip/<br>
GitHub：@YueMoon99<br>
Blibili：UID223633562<br>
YouTube：@YueMoon99<br>
