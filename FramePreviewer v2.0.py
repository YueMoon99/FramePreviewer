import sys
import os
import re
import ctypes
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGraphicsView, QGraphicsScene, 
                             QComboBox, QLabel, QPushButton, QGraphicsItem, QMessageBox,
                             QSizeGrip, QFileDialog, QProgressDialog)
from PyQt6.QtCore import (Qt, QTimer, QThread, pyqtSignal, QPointF, QRectF, QSettings)
from PyQt6.QtGui import (QPixmap, QImage, QIcon, QPainter, QColor, QPen, QBrush, 
                         QTransform, QKeySequence, QShortcut, QPolygonF)

# 字典
LANG = {
    'cn': {
        'title': '序列帧预览器 v2.0 By 舟午YueMoon',
        'fps': '帧速率:',
        'bg': '背景:',
        'zoom': '缩放:',
        'fit': '适应窗口',
        'bg_grid': '透明网格',
        'bg_black': '纯黑',
        'bg_white': '纯白',
        'bg_green': '纯绿',
        'bg_red': '纯红',
        'bg_blue': '纯蓝',
        'lang_btn': 'English', 
        'hide_btn': '隐藏UI（按ESC恢复）',
        'export_btn': '导出',
        'hint': '拖入序列的任意一帧即可',
        'warn_empty': '请先拖入序列帧！',
        'exp_title': '导出设置',
        'exp_format': '导出格式:',
        'exp_res': '分辨率:',
        'exp_fps': '帧速率:',
        'exp_bitrate': '码率 (kbps):',
        'exp_alpha': '保留 Alpha 透明通道',
        'exp_colors': 'GIF 颜色数:',
        'exp_cancel': '取消',
        'exp_start': '导出',
        'exp_err_res': '分辨率格式错误，请使用 宽*高 的格式，例如 1920*1080',
        'msg_exporting': '正在导出，请稍候...',
        'msg_exp_success': '导出完成！',
        'msg_exp_fail': '导出失败，请检查是否已安装 FFmpeg 并加入环境变量。',
        'msg_exporting': '正在渲染...',
    },
    'en': {
        'title': 'Image Sequence Previewer v2.0 By 舟午YueMoon',
        'fps': 'FPS:',
        'bg': 'Background:',
        'zoom': 'Zoom:',
        'fit': 'Fit Window',
        'bg_grid': 'Grid',
        'bg_black': 'Black',
        'bg_white': 'White',
        'bg_green': 'Green',
        'bg_red': 'Red',
        'bg_blue': 'Blue',
        'lang_btn': '中文',
        'hide_btn': 'Hide UI (ESC to restore)',
        'export_btn': 'Export',
        'hint': 'Drop any frame of the sequence here',
        'warn_empty': 'Please load a sequence first!',
        'exp_title': 'Export Settings',
        'exp_format': 'Format:',
        'exp_res': 'Resolution:',
        'exp_fps': 'FPS:',
        'exp_bitrate': 'Bitrate (kbps):',
        'exp_alpha': 'Export with Alpha Channel',
        'exp_colors': 'GIF Colors:',
        'exp_cancel': 'Cancel',
        'exp_start': 'Export',
        'exp_err_res': 'Invalid resolution. Use W*H format (e.g., 1920*1080)',
        'msg_exporting': 'Exporting in progress...',
        'msg_exp_success': 'Export completed successfully!',
        'msg_exp_fail': 'Export failed. Ensure FFmpeg is installed and in PATH.', 
        'msg_exporting': 'Rendering...',
    }
}

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

class CacheWorker(QThread):
    progress = pyqtSignal(int)
    frame_loaded = pyqtSignal(int, QImage)
    finished_caching = pyqtSignal()

    def __init__(self, file_list):
        super().__init__()
        self.file_list = file_list
        self.is_running = True

    def run(self):
        for i, file_path in enumerate(self.file_list):
            if not self.is_running:
                break
            img = QImage(file_path)
            self.frame_loaded.emit(i, img)
            self.progress.emit(i + 1)
        self.finished_caching.emit()

    def stop(self):
        self.is_running = False

class TimelineBar(QWidget):
    seek_frame = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setFixedHeight(12)
        self.total_frames = 1
        self.cached_frames = 0
        self.current_frame = 0

    def set_data(self, total, cached, current):
        self.total_frames = max(1, total)
        self.cached_frames = cached
        self.current_frame = current
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width = self.width()
        height = self.height()
        painter.fillRect(0, 0, width, height, QColor(60, 60, 60))
        cache_width = int((self.cached_frames / self.total_frames) * width)
        painter.fillRect(0, 0, cache_width, height, QColor(0, 200, 0))
        playhead_x = (self.current_frame / self.total_frames) * width
        painter.setPen(QPen(QColor(255, 50, 50), 1.5))
        painter.drawLine(int(playhead_x), 0, int(playhead_x), height)
        painter.setBrush(QBrush(QColor(255, 50, 50)))
        painter.setPen(Qt.PenStyle.NoPen)
        triangle = QPolygonF([
            QPointF(playhead_x - 5, 0),
            QPointF(playhead_x + 5, 0),
            QPointF(playhead_x, 6)
        ])
        painter.drawPolygon(triangle)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._update_frame_from_mouse(event.pos().x())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._update_frame_from_mouse(event.pos().x())

    def _update_frame_from_mouse(self, x):
        if self.total_frames <= 1:
            return
        frame_idx = int((x / self.width()) * self.total_frames)
        frame_idx = max(0, min(frame_idx, self.total_frames - 1))
        self.seek_frame.emit(frame_idx)


class PreviewView(QGraphicsView):
    files_dropped = pyqtSignal(str)
    toggle_play = pyqtSignal()
    zoom_changed = pyqtSignal(float)

    def __init__(self, scene):
        super().__init__(scene)
        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.bg_mode = 'grid'
        self._press_pos = None
        self._drag_start_global = None
        self._window_start_pos = None
        self.show_hint = True 
        self.hint_text = ""
        self.grid_brush = self._create_grid_brush()
    
    def _create_grid_brush(self):
        pixmap = QPixmap(20, 20)
        painter = QPainter(pixmap)
        painter.fillRect(0, 0, 10, 10, QColor(200, 200, 200))
        painter.fillRect(10, 10, 10, 10, QColor(200, 200, 200))
        painter.fillRect(10, 0, 10, 10, QColor(255, 255, 255))
        painter.fillRect(0, 10, 10, 10, QColor(255, 255, 255))
        painter.end()
        return QBrush(pixmap)

    def drawBackground(self, painter, rect):
        if self.bg_mode == 'transparent':
            painter.save()
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            painter.restore()
            return  
        if self.bg_mode == 'grid':
            painter.fillRect(rect, self.grid_brush)
        else:
            colors = {
                'black': QColor(0, 0, 0), 'white': QColor(255, 255, 255),
                'green': QColor(0, 255, 0), 'red': QColor(255, 0, 0), 'blue': QColor(0, 0, 255)
            }
            painter.fillRect(rect, colors.get(self.bg_mode, QColor(0,0,0)))

    def drawForeground(self, painter, rect):
        if self.show_hint:
            painter.setTransform(QTransform())
            painter.setPen(QColor(150, 150, 150))
            font = painter.font()
            font.setPointSize(14)
            painter.setFont(font)
            painter.drawText(self.viewport().rect(), Qt.AlignmentFlag.AlignCenter, self.hint_text)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.files_dropped.emit(file_path)

    def wheelEvent(self, event):
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        self.scale(zoom_factor, zoom_factor)
        current_scale = self.transform().m11()
        self.zoom_changed.emit(current_scale * 100)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.pos()
            
            window = self.window()
            if getattr(window, 'is_ui_hidden', False):
                self._drag_start_global = event.globalPosition().toPoint()
                self._window_start_pos = window.pos()
                
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        window = self.window()
        if getattr(window, 'is_ui_hidden', False) and self._drag_start_global is not None:
            if event.buttons() & Qt.MouseButton.LeftButton:
                delta = event.globalPosition().toPoint() - self._drag_start_global
                window.move(self._window_start_pos + delta)
                return 
                
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._press_pos is not None:
            if (event.pos() - self._press_pos).manhattanLength() < 5:
                self.toggle_play.emit()
            self._drag_start_global = None
        super().mouseReleaseEvent(event)

import subprocess
from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QCheckBox

class ExportWorker(QThread):
    finished = pyqtSignal(bool, str)
    progress_update = pyqtSignal(int)

    def __init__(self, file_list, out_path, params):
        super().__init__()
        self.file_list = file_list
        self.out_path = out_path
        self.params = params
        self.is_cancelled = False
        self.process = None

    def cancel(self):
        self.is_cancelled = True
        if self.process:
            self.process.terminate()

    def run(self):
        try:
            first_file = self.file_list[0]
            dir_name = os.path.dirname(first_file)
            base_name = os.path.basename(first_file)
            match = re.match(r'^(.*?)(\d+)(\.[a-zA-Z0-9]+)$', base_name)
            
            if not match:
                self.finished.emit(False, "文件命名不符合序列帧规范")
                return
                
            prefix, num_str, ext = match.groups()
            padding = len(num_str)
            start_num = int(num_str)
            input_pattern = os.path.join(dir_name, f"{prefix}%0{padding}d{ext}")
            total_frames = len(self.file_list)

            fmt = self.params['format']
            w, h = self.params['res'].split('*')
            fps = self.params['fps']
            
            is_mac = sys.platform == 'darwin'
            h264_enc = "h264_videotoolbox" if is_mac else "h264_nvenc"

            ffmpeg_name = 'ffmpeg' if is_mac else 'ffmpeg.exe'
            ffmpeg_path = resource_path(ffmpeg_name)
            
            if not os.path.isfile(ffmpeg_path):
                self.finished.emit(False, f"找不到 FFmpeg 组件！\n路径: {ffmpeg_path}")
                return
            
            cmd = [
                ffmpeg_path, '-y', 
                '-progress', 'pipe:1',
                '-framerate', str(fps), 
                '-start_number', str(start_num), 
                '-i', input_pattern
            ]

            if fmt == 'MP4':
                bitrate = self.params['bitrate']
                cmd.extend(['-c:v', h264_enc, '-b:v', f"{bitrate}k", '-s', f"{w}x{h}", '-pix_fmt', 'yuv420p', self.out_path])
            elif fmt == 'MOV':
                bitrate = self.params.get('bitrate', '8000')
                if self.params.get('alpha', False):
                    prores_enc = "prores_videotoolbox" if is_mac else "prores_ks"
                    cmd.extend(['-c:v', prores_enc, '-profile:v', '4444', '-pix_fmt', 'yuva444p10le' if not is_mac else 'yuva422p10le', '-s', f"{w}x{h}", self.out_path])
                else:
                    cmd.extend(['-c:v', h264_enc, '-b:v', f"{bitrate}k", '-s', f"{w}x{h}", '-pix_fmt', 'yuv420p', self.out_path])
            elif fmt == 'GIF':
                colors = self.params['colors']
                vf_filter = f"scale={w}:{h}:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors={colors}[p];[s1][p]paletteuse"
                cmd.extend(['-vf', vf_filter, self.out_path])

            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=creationflags)
            
            while True:
                if self.is_cancelled:
                    break
                    
                line = self.process.stdout.readline()
                if not line and self.process.poll() is not None:
                    break
                    
                if line.startswith('frame='):
                    try:
                        current_frame = int(line.split('=')[1].strip())
                        percent = int((current_frame / total_frames) * 100)
                        self.progress_update.emit(min(percent, 100))
                    except:
                        pass
                        
            stdout, stderr = self.process.communicate()

            if self.is_cancelled:
                self.finished.emit(False, "User Cancelled")
            elif self.process.returncode == 0:
                self.progress_update.emit(100)
                self.finished.emit(True, "")
            else:
                self.finished.emit(False, stderr)
                
        except Exception as e:
            self.finished.emit(False, str(e))


class ExportDialog(QDialog):
    def __init__(self, parent, lang, orig_w, orig_h, current_fps):
        super().__init__(parent)
        self.lang = lang
        self.t = LANG[lang]
        self.orig_w = orig_w
        self.orig_h = orig_h
        
        self.setWindowTitle(self.t['exp_title'])
        self.setFixedWidth(350)
        
        self.setStyleSheet(parent.styleSheet() + " QDialog { background-color: #303030; }")
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.cb_format = QComboBox()
        self.cb_format.addItems(['MP4', 'MOV', 'GIF'])
        self.cb_format.currentTextChanged.connect(self.on_format_changed)
        form_layout.addRow(self.t['exp_format'], self.cb_format)
        
        res_layout = QHBoxLayout()
        self.le_res = QLineEdit(f"{orig_w}*{orig_h}")
        self.btn_res_mul = QPushButton("×2")
        self.btn_res_div = QPushButton("÷2")
        self.btn_res_mul.clicked.connect(lambda: self.modify_res(2.0))
        self.btn_res_div.clicked.connect(lambda: self.modify_res(0.5))
        
        self.le_res.setStyleSheet("background-color: #404040; color: #e0e0e0; border: 1px solid #555555; border-radius: 3px; padding: 2px 5px;")
        
        res_layout.addWidget(self.le_res)
        res_layout.addWidget(self.btn_res_mul)
        res_layout.addWidget(self.btn_res_div)
        form_layout.addRow(self.t['exp_res'], res_layout)
        
        self.le_fps = QLineEdit(str(current_fps))
        self.le_fps.setStyleSheet(self.le_res.styleSheet())
        form_layout.addRow(self.t['exp_fps'], self.le_fps)
        
        self.lbl_bitrate = QLabel(self.t['exp_bitrate'])
        self.le_bitrate = QLineEdit("8000")
        self.le_bitrate.setStyleSheet(self.le_res.styleSheet())
        form_layout.addRow(self.lbl_bitrate, self.le_bitrate)
        
        self.cb_alpha = QCheckBox(self.t['exp_alpha'])
        self.cb_alpha.setStyleSheet("color: #e0e0e0;")
        form_layout.addRow("", self.cb_alpha)
        self.cb_alpha.hide()
        
        self.lbl_colors = QLabel(self.t['exp_colors'])
        self.cb_colors = QComboBox()
        self.cb_colors.addItems(['2', '4', '8', '16', '32', '64', '128', '256'])
        self.cb_colors.setCurrentText('128')
        form_layout.addRow(self.lbl_colors, self.cb_colors)
        self.lbl_colors.hide()
        self.cb_colors.hide()
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_cancel = QPushButton(self.t['exp_cancel'])
        self.btn_export = QPushButton(self.t['exp_start'])
        self.btn_export.setStyleSheet("background-color: #0078D7; color: white;") # 给导出按钮一个醒目的强调色
        
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_export.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_export)
        layout.addLayout(btn_layout)

    def modify_res(self, factor):
        try:
            txt = self.le_res.text()
            w, h = map(int, txt.split('*'))
            new_w, new_h = round(w * factor), round(h * factor)
            self.le_res.setText(f"{new_w}*{new_h}")
        except:
            QMessageBox.warning(self, "Error", self.t['exp_err_res'])

    def on_format_changed(self, fmt):
        is_video = fmt in ['MP4', 'MOV']
        self.lbl_bitrate.setVisible(is_video)
        self.le_bitrate.setVisible(is_video)
        
        self.cb_alpha.setVisible(fmt == 'MOV')
        
        is_gif = fmt == 'GIF'
        self.lbl_colors.setVisible(is_gif)
        self.cb_colors.setVisible(is_gif)
        
    def get_params(self):
        return {
            'format': self.cb_format.currentText(),
            'res': self.le_res.text(),
            'fps': self.le_fps.text(),
            'bitrate': self.le_bitrate.text(),
            'alpha': self.cb_alpha.isChecked(),
            'colors': self.cb_colors.currentText()
        }

class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(30)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        self.setObjectName("TitleBar")
        self.setStyleSheet("""
            QWidget#TitleBar {
                background-color: #252525;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        
        self.title_label = QLabel()
        self.title_label.setStyleSheet("color: #e0e0e0; background-color: #252525; font-size: 14px;")

        # ====== 核心跨平台逻辑：判断当前操作系统 ======
        is_mac = sys.platform == 'darwin'
        
        if is_mac:
            # -------------------------------------
            # macOS 专属样式：左侧 12px 圆形“红绿灯”
            # -------------------------------------
            layout.setSpacing(8)
            
            # 核心修改1：直接在按钮初始化时填入对应的字符（乘号、减号、加号）
            self.btn_close = QPushButton("×")
            self.btn_min = QPushButton("-")
            self.btn_max = QPushButton("+")
            
            for btn in (self.btn_close, self.btn_min, self.btn_max):
                btn.setFixedSize(12, 12)
            
            # 核心修改2：设置字体样式，并让 color 默认为 transparent（透明隐藏）
            mac_btn_style = """
                QPushButton { 
                    border: none; 
                    border-radius: 6px; 
                    color: transparent;  /* 默认隐藏内部符号 */
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
                    font-size: 12px;
                    font-weight: 900;
                    padding: 0px;        
                }
            """
            
            # 核心修改3：在 :hover 状态下，不仅背景变暗，color(文字颜色) 也会变成深色显示出来
            self.btn_close.setStyleSheet(mac_btn_style + "QPushButton { background-color: #FF5F56; } QPushButton:hover { background-color: #E0443E; color: #4d0000; }")
            self.btn_min.setStyleSheet(mac_btn_style + "QPushButton { background-color: #FFBD2E; } QPushButton:hover { background-color: #DEA127; color: #5a4000; }")
            self.btn_max.setStyleSheet(mac_btn_style + "QPushButton { background-color: #27C93F; } QPushButton:hover { background-color: #1AAB29; color: #004d00; }")
            
            layout.addWidget(self.btn_close)
            layout.addWidget(self.btn_min)
            layout.addWidget(self.btn_max)
            layout.addSpacing(10)
            layout.addWidget(self.title_label)
            layout.addStretch()
            
        else:
            # -------------------------------------
            # Windows 专属样式：右侧矩形控制键
            # -------------------------------------
            layout.setSpacing(0)
            
            # Win 排版顺序：标题 -> 弹簧挤压 -> 最小化 -> 最大化 -> 关闭
            layout.addWidget(self.title_label)
            layout.addStretch()
            
            btn_style = """
                QPushButton { 
                    background-color: transparent; border: none; color: #e0e0e0; 
                    font-size: 15px; font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; 
                }
                QPushButton:hover { background-color: #404040; }
            """
            close_style = """
                QPushButton { 
                    background-color: transparent; border: none; color: #e0e0e0; 
                    font-size: 15px; font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; 
                    border-top-right-radius: 8px; 
                }
                QPushButton:hover { background-color: #e81123; }
            """
            
            self.btn_min = QPushButton("─")
            self.btn_max = QPushButton("□")
            self.btn_close = QPushButton("✕")
            
            for btn, style in [(self.btn_min, btn_style), (self.btn_max, btn_style), (self.btn_close, close_style)]:
                btn.setFixedSize(45, 30)
                btn.setStyleSheet(style)
                layout.addWidget(btn)
                
        # ============================================

        # 信号绑定（跨平台通用，底层行为是一致的）
        self.btn_min.clicked.connect(self.parent.showMinimized)
        self.btn_max.clicked.connect(self.toggle_max)
        self.btn_close.clicked.connect(self.parent.close)
        
        self._is_tracking = False
        self._start_pos = None

    def update_title(self, text):
        self.title_label.setText(text)

    def toggle_max(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_tracking = True
            self._start_pos = event.globalPosition().toPoint()
            self._window_pos = self.parent.pos()

    def mouseMoveEvent(self, event):
        if self._is_tracking and self._start_pos:
            delta = event.globalPosition().toPoint() - self._start_pos
            self.parent.move(self._window_pos + delta)

    def mouseReleaseEvent(self, event):
        self._is_tracking = False
        
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_max()
# =========================================================


class SequenceViewer(QMainWindow):
    from PyQt6.QtWidgets import QFileDialog

    def open_export_dialog(self):
        if not self.file_list:
            QMessageBox.warning(self, "Warning", LANG[self.lang]['warn_empty'])
            return
            
        img = self.frames_ram[0].toImage() if self.frames_ram[0] else QImage(self.file_list[0])
        orig_w, orig_h = img.width(), img.height()
        current_fps = self.cb_fps.currentText()
        
        dialog = ExportDialog(self, self.lang, orig_w, orig_h, current_fps)
        if dialog.exec():
            params = dialog.get_params()
            fmt = params['format']
            ext_map = {'MP4': '.mp4', 'MOV': '.mov', 'GIF': '.gif'}
            default_ext = ext_map[fmt]
            
            out_path, _ = QFileDialog.getSaveFileName(
                self, 
                "保存文件" if self.lang == 'cn' else "Save File", 
                f"output{default_ext}", 
                f"{fmt} Files (*{default_ext})"
            )
            
            if out_path:
                self.start_export(out_path, params)

    def start_export(self, out_path, params):
        self.btn_export.setEnabled(False) 
        
        self.progress_dialog = QProgressDialog(LANG[self.lang]['msg_exporting'], LANG[self.lang]['exp_cancel'], 0, 100, self)
        self.progress_dialog.setWindowTitle(LANG[self.lang]['exp_title'])
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setStyleSheet(self.styleSheet() + " QDialog { background-color: #303030; }")
        self.progress_dialog.setMinimumDuration(500)
        self.progress_dialog.setValue(0)
        
        self.export_thread = ExportWorker(self.file_list, out_path, params)
        self.export_thread.progress_update.connect(self.progress_dialog.setValue)
        self.export_thread.finished.connect(self.on_export_finished)
        self.progress_dialog.canceled.connect(self.cancel_export)
        
        self.export_thread.start()

    def cancel_export(self):
        if hasattr(self, 'export_thread') and self.export_thread.isRunning():
            self.export_thread.cancel()

    def on_export_finished(self, success, error_msg):
        self.btn_export.setEnabled(True)
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        
        if error_msg == "User Cancelled":
            QMessageBox.information(self, "取消", "导出已取消" if self.lang == 'cn' else "Export Cancelled")
        elif success:
            QMessageBox.information(self, "Success", LANG[self.lang]['msg_exp_success'])
        else:
            QMessageBox.critical(self, "Error", f"{LANG[self.lang]['msg_exp_fail']}\n\nLog: {error_msg}")

    def __init__(self):
        super().__init__()
        self.lang = 'cn'
        self.settings = QSettings("YueMoon", "FramePreviewer")
        self.lang = self.settings.value("language", "cn")
        self.file_list = []
        self.current_index = 0
        self.is_playing = False
        self.cache_worker = None
        self.is_ui_hidden = False
        
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        self.init_ui()
        self.init_timer()
        self.update_language()
        icon_path = resource_path("favicon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def setup_dark_theme(self):
        self.main_widget.setStyleSheet("""
            QWidget#MainWidget {
                background-color: #303030;
                border: 1px solid #252525;
                border-radius: 8px;
            }
        """)
        
        import tempfile
        pixmap = QPixmap(14, 14)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#e0e0e0"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawLine(3, 5, 7, 9)
        painter.drawLine(7, 9, 11, 5)
        painter.end()
        
        arrow_path = os.path.join(tempfile.gettempdir(), "seq_arrow_icon.png").replace("\\", "/")
        pixmap.save(arrow_path, "PNG")

        style = """
            QWidget#BottomWidget {
                background-color: #252525;
                border-top: 1px solid #3d3d3d;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            QLabel {
                color: #e0e0e0;
                font-family: 'Segoe UI', 'Microsoft YaHei';
            }

            QComboBox {
                background-color: #404040;
                color: #e0e0e0;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px 28px 4px 8px; 
            }
            
            QComboBox QLineEdit {
                background: transparent;
                border: none;
                padding: 0px;
            }
            
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left-width: 1px;
                border-left-color: #555555;
                border-left-style: solid;
            }
            
            QComboBox::down-arrow {
                image: url("ARROW_PATH");
                width: 14px;
                height: 14px;
            }
            
            QComboBox QAbstractItemView, QComboBox QListView {
                color: #e0e0e0;
                background-color: #353535;
                selection-background-color: #505050;
                selection-color: #ffffff;
                outline: none;
                border: 1px solid #555555;
            }
                           
            QPushButton {
                background-color: #454545;
                color: #e0e0e0;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
                           
            QMessageBox {
                background-color: #303030;
            }
            QMessageBox QLabel {
                color: #e0e0e0;
                background-color: transparent;
            }
        """.replace("ARROW_PATH", arrow_path)
        
        self.setStyleSheet(style)

    def init_ui(self):
        self.setWindowTitle("序列帧预览器")
        self.resize(800, 600)
        
        self.main_widget = QWidget()
        self.main_widget.setObjectName("MainWidget")
        self.setCentralWidget(self.main_widget)
        layout = QVBoxLayout(self.main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.title_bar = CustomTitleBar(self)
        layout.addWidget(self.title_bar)
        
        self.scene = QGraphicsScene()
        self.view = PreviewView(self.scene)
        self.view.files_dropped.connect(self.load_sequence)
        self.view.toggle_play.connect(self.toggle_playback)
        self.view.zoom_changed.connect(self.on_view_zoomed)
        self.pixmap_item = self.scene.addPixmap(QPixmap())
        self.pixmap_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        layout.addWidget(self.view)
        
        self.bottom_widget = QWidget()
        self.bottom_widget.setObjectName("BottomWidget")
        bottom_layout = QVBoxLayout(self.bottom_widget)
        bottom_layout.setContentsMargins(5, 5, 5, 5)
        self.timeline = TimelineBar()
        self.timeline.seek_frame.connect(self.seek_to_frame)
        bottom_layout.addWidget(self.timeline)
        
        control_layout = QHBoxLayout()
        self.lbl_fps = QLabel()
        self.cb_fps = QComboBox()
        self.cb_fps.setFixedWidth(100)
        self.cb_fps.addItems(['10', '24', '25', '29.97', '30', '60', '90', '120'])
        self.cb_fps.setCurrentText('25')
        self.cb_fps.currentTextChanged.connect(self.update_timer_interval)
        control_layout.addWidget(self.lbl_fps)
        control_layout.addWidget(self.cb_fps)
        
        self.lbl_bg = QLabel()
        self.cb_bg = QComboBox()
        self.cb_bg.setFixedWidth(130)
        self.cb_bg.currentIndexChanged.connect(self.change_background)
        control_layout.addWidget(self.lbl_bg)
        control_layout.addWidget(self.cb_bg)
        
        self.lbl_zoom = QLabel()
        self.cb_zoom = QComboBox()
        self.cb_zoom.setEditable(True)
        self.cb_zoom.setFixedWidth(140)
        self.cb_zoom.lineEdit().returnPressed.connect(self.apply_manual_zoom)
        self.cb_zoom.activated.connect(self.apply_manual_zoom)
        self.cb_zoom.setCurrentText(LANG[self.lang]['fit'])
        control_layout.addWidget(self.lbl_zoom)
        control_layout.addWidget(self.cb_zoom)
        
        self.btn_hide_ui = QPushButton()
        self.btn_hide_ui.clicked.connect(self.toggle_ui_visibility)
        control_layout.addWidget(self.btn_hide_ui)

        self.btn_export = QPushButton()
        self.btn_export.clicked.connect(self.open_export_dialog)
        control_layout.addWidget(self.btn_export)
        
        control_layout.addStretch()
        self.btn_lang = QPushButton()
        self.btn_lang.clicked.connect(self.switch_language)
        control_layout.addWidget(self.btn_lang)
        
        self.size_grip = QSizeGrip(self)
        control_layout.addWidget(self.size_grip)
        
        bottom_layout.addLayout(control_layout)
        layout.addWidget(self.bottom_widget)
        
        self.setup_dark_theme()
        
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self.toggle_playback)
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self.prev_frame)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self.next_frame)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self.restore_ui_visibility)

    def init_timer(self):
        self.timer = QTimer()
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self.next_frame)
        self.update_timer_interval()

    def update_timer_interval(self):
        try:
            fps = float(self.cb_fps.currentText())
            self.timer.setInterval(int(1000 / fps))
        except ValueError:
            pass

    def update_language(self):
        t = LANG[self.lang]
        self.setWindowTitle(t['title'])
        self.title_bar.update_title(t['title'])
        self.lbl_fps.setText(t['fps'])
        self.lbl_bg.setText(t['bg'])
        self.lbl_zoom.setText(t['zoom'])
        self.btn_lang.setText(t['lang_btn'])
        self.btn_hide_ui.setText(t['hide_btn'])
        self.btn_export.setText(t['export_btn'])
        
        bg_idx = self.cb_bg.currentIndex()
        self.cb_bg.blockSignals(True)
        self.cb_bg.clear()
        self.cb_bg.addItems([t['bg_grid'], t['bg_black'], t['bg_white'], t['bg_green'], t['bg_red'], t['bg_blue']])
        self.cb_bg.setCurrentIndex(max(0, bg_idx))
        self.cb_bg.blockSignals(False)
        self.view.hint_text = t['hint']
        self.view.viewport().update()
        
        zoom_text = self.cb_zoom.currentText()
        self.cb_zoom.blockSignals(True)
        self.cb_zoom.clear()
        self.cb_zoom.addItems(['10%', '25%', '50%', '75%', '100%', '150%', '200%', t['fit']])
        if zoom_text in [LANG['cn']['fit'], LANG['en']['fit']]:
            self.cb_zoom.setCurrentText(t['fit'])
        else:
            self.cb_zoom.setCurrentText(zoom_text)
        self.cb_zoom.blockSignals(False)

    def switch_language(self):
        self.lang = 'en' if self.lang == 'cn' else 'cn'
        self.settings.setValue("language", self.lang)
        self.update_language()

    def change_background(self):
        idx = self.cb_bg.currentIndex()
        modes = ['grid', 'black', 'white', 'green', 'red', 'blue']
        self.view.bg_mode = modes[idx]
        self.view.scene().invalidate()

    def on_view_zoomed(self, percentage):
        self.cb_zoom.blockSignals(True)
        self.cb_zoom.setCurrentText(f"{percentage:.1f}%")
        self.cb_zoom.blockSignals(False)

    def apply_manual_zoom(self):
        text = self.cb_zoom.currentText()
        t = LANG[self.lang]
        if text == t['fit']:
            self.fit_to_window()
        else:
            try:
                val = float(text.replace('%', ''))
                scale_factor = val / 100.0
                self.view.setTransform(QTransform().scale(scale_factor, scale_factor))
            except ValueError:
                pass

    def fit_to_window(self):
        if self.pixmap_item.pixmap().isNull():
            return
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        current_scale = self.view.transform().m11() * 100
        self.cb_zoom.blockSignals(True)
        self.cb_zoom.setCurrentText(LANG[self.lang]['fit'])
        self.cb_zoom.blockSignals(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.cb_zoom.currentText() in [LANG['cn']['fit'], LANG['en']['fit']]:
            self.fit_to_window()

    def load_sequence(self, file_path):
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        match = re.match(r'^(.*?)(\d+)(\.[a-zA-Z0-9]+)$', filename)
        
        if match:
            prefix, _, ext = match.groups()
            escaped_prefix = re.escape(prefix)
            escaped_ext = re.escape(ext)
            pattern = re.compile(rf'^{escaped_prefix}(\d+){escaped_ext}$')
            
            files = []
            for f in os.listdir(directory):
                if pattern.match(f):
                    files.append(os.path.join(directory, f))
            
            files.sort(key=lambda x: int(re.search(r'(\d+)(?=\.[^.]+$)', x).group(1)))
        else:
            files = [file_path]
            
        self.file_list = files
        self.frames_ram = [None] * len(files)
        self.current_index = 0
        self.is_playing = False
        self.timer.stop()
        self.view.show_hint = False
        self.pixmap_item.setPos(0, 0)
        self.fit_to_window()
        self.timeline.set_data(len(self.file_list), 1, 0)
        
        if self.cache_worker and self.cache_worker.isRunning():
            self.cache_worker.stop()
            self.cache_worker.wait()
            
        first_img = QImage(self.file_list[0])
        first_pixmap = QPixmap.fromImage(first_img)
        self.frames_ram[0] = first_pixmap
        self.show_frame(0)
        img_w, img_h = first_pixmap.width(), first_pixmap.height()
        self.scene.setSceneRect(0, 0, img_w, img_h)
        self.timeline.set_data(len(self.file_list), 1, 0)
        self.pixmap_item.setPos(0, 0)
        self.fit_to_window()
        
        if len(self.file_list) > 1:
            self.cache_worker = CacheWorker(self.file_list)
            self.cache_worker.frame_loaded.connect(self.on_frame_cached)
            self.cache_worker.progress.connect(self.update_cache_progress)
            self.cache_worker.start()

    def toggle_ui_visibility(self):
        if not self.file_list:
            QMessageBox.warning(self, "提示" if self.lang == 'cn' else "Warning", LANG[self.lang]['warn_empty'])
            return
            
        self.is_ui_hidden = True
        
        self.title_bar.hide()
        self.bottom_widget.hide()
        
        self.view.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.main_widget.setStyleSheet("QWidget#MainWidget { background: transparent; border: none; }")
        self.view.setStyleSheet("background: transparent; border: none;")
        
        self.original_bg_mode = self.view.bg_mode
        self.view.bg_mode = 'transparent'
        
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.view.scene().invalidate()
        self.view.viewport().update()

    def restore_ui_visibility(self):
        if getattr(self, 'is_ui_hidden', False):
            self.is_ui_hidden = False
            
            self.title_bar.show()
            self.bottom_widget.show()
            
            self.view.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.setup_dark_theme()
            
            self.view.setStyleSheet("background-color: transparent; border: none;")
            self.view.bg_mode = getattr(self, 'original_bg_mode', 'grid')
            
            self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.view.scene().invalidate()
            self.view.viewport().update()

    def on_frame_cached(self, index, qimage):
        if index < len(self.frames_ram):
            self.frames_ram[index] = QPixmap.fromImage(qimage)

    def update_cache_progress(self, cached_count):
        self.timeline.set_data(len(self.file_list), cached_count, self.current_index)

    def toggle_playback(self):
        if not self.file_list: return
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.timer.start()
        else:
            self.timer.stop()

    def next_frame(self):
        if not self.file_list: return
        self.current_index = (self.current_index + 1) % len(self.file_list)
        self.show_frame(self.current_index)

    def prev_frame(self):
        if not self.file_list: return
        self.current_index = (self.current_index - 1) % len(self.file_list)
        self.show_frame(self.current_index)

    def show_frame(self, index):
        pixmap = self.frames_ram[index]
        if pixmap:
            self.pixmap_item.setPixmap(pixmap)
        else:
            self.pixmap_item.setPixmap(QPixmap(self.file_list[index]))
        self.timeline.set_data(len(self.file_list), self.timeline.cached_frames, index)

    def seek_to_frame(self, index):
        if not self.file_list: return
        self.current_index = index
        self.show_frame(self.current_index)


if __name__ == '__main__':
    try:
        myappid = 'sequenceviewer.1.1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    viewer = SequenceViewer()
    viewer.show()
    sys.exit(app.exec())