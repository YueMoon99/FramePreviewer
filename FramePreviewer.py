import sys
import os
import re
import glob
import ctypes
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGraphicsView, QGraphicsScene, 
                             QComboBox, QLabel, QPushButton, QFileDialog, QGraphicsItem)
from PyQt6.QtCore import (Qt, QTimer, QThread, pyqtSignal, QPointF, QRectF, QEvent)
from PyQt6.QtGui import (QPixmap, QImage, QIcon, QPainter, QColor, QPen, QBrush, 
                         QTransform, QKeySequence, QShortcut, QPolygonF)

# 字典
LANG = {
    'cn': {
        'title': '序列帧预览器',
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
        'hint': '拖入序列的任意一帧即可'
    },
    'en': {
        'title': 'Image Sequence Previewer',
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
        'hint': 'Drop any frame of the sequence here'
    }
}

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._press_pos is not None:
            if (event.pos() - self._press_pos).manhattanLength() < 5:
                self.toggle_play.emit()
        super().mouseReleaseEvent(event)


class SequenceViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang = 'cn'
        self.frames_ram = []
        self.file_list = []
        self.current_index = 0
        self.is_playing = False
        self.cache_worker = None
        self.init_ui()
        self.init_timer()
        self.update_language()
        icon_path = resource_path("favicon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def init_ui(self):
        self.setWindowTitle("序列帧预览器")
        self.resize(800, 600)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.scene = QGraphicsScene()
        self.view = PreviewView(self.scene)
        self.view.files_dropped.connect(self.load_sequence)
        self.view.toggle_play.connect(self.toggle_playback)
        self.view.zoom_changed.connect(self.on_view_zoomed)
        self.pixmap_item = self.scene.addPixmap(QPixmap())
        self.pixmap_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        layout.addWidget(self.view)
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(5, 5, 5, 5)
        self.timeline = TimelineBar()
        self.timeline.seek_frame.connect(self.seek_to_frame)
        bottom_layout.addWidget(self.timeline)
        control_layout = QHBoxLayout()
        self.lbl_fps = QLabel()
        self.cb_fps = QComboBox()
        self.cb_fps.addItems(['10', '24', '25', '29.97', '30', '60', '90', '120'])
        self.cb_fps.setCurrentText('25')
        self.cb_fps.currentTextChanged.connect(self.update_timer_interval)
        control_layout.addWidget(self.lbl_fps)
        control_layout.addWidget(self.cb_fps)
        self.lbl_bg = QLabel()
        self.cb_bg = QComboBox()
        self.cb_bg.currentIndexChanged.connect(self.change_background)
        control_layout.addWidget(self.lbl_bg)
        control_layout.addWidget(self.cb_bg)
        self.lbl_zoom = QLabel()
        self.cb_zoom = QComboBox()
        self.cb_zoom.setEditable(True)
        self.cb_zoom.lineEdit().returnPressed.connect(self.apply_manual_zoom)
        self.cb_zoom.activated.connect(self.apply_manual_zoom)
        self.cb_zoom.setCurrentText(LANG[self.lang]['fit'])
        control_layout.addWidget(self.lbl_zoom)
        control_layout.addWidget(self.cb_zoom)
        control_layout.addStretch()
        self.btn_lang = QPushButton()
        self.btn_lang.clicked.connect(self.switch_language)
        control_layout.addWidget(self.btn_lang)
        bottom_layout.addLayout(control_layout)
        layout.addWidget(bottom_widget)
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self.toggle_playback)
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self.prev_frame)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self.next_frame)

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
        self.lbl_fps.setText(t['fps'])
        self.lbl_bg.setText(t['bg'])
        self.lbl_zoom.setText(t['zoom'])
        self.btn_lang.setText(t['lang_btn'])
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
            pattern = os.path.join(directory, f"{prefix}*{ext}")
            files = glob.glob(pattern)
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
        self.timeline.set_data(len(self.file_list), 1, 0)
        if len(self.file_list) > 1:
            self.cache_worker = CacheWorker(self.file_list)
            self.cache_worker.frame_loaded.connect(self.on_frame_cached)
            self.cache_worker.progress.connect(self.update_cache_progress)
            self.cache_worker.start()

    def on_frame_cached(self, index, qimage):
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
        myappid = 'sequenceviewer.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    viewer = SequenceViewer()
    viewer.show()
    sys.exit(app.exec())