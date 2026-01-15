"""
Multi-camera grid viewer - FINAL PyQt5 RPi version
✅ FIXED: CAP_PROP_BUFFERSIZE + 0 FPS + USB detection
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QThread, QTimer
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence
import sys
import cv2
import time 
import traceback
import glob
import atexit
import signal

# SAFE IMPORTS
try:
    import qdarkstyle
    DARKSTYLE_AVAILABLE = True
except:
    DARKSTYLE_AVAILABLE = False

# 🔥 FIXED CAMERA THREAD - NO MORE AttributeError
class CaptureWorker(QThread):
    frame_ready = pyqtSignal(object)
    status_changed = pyqtSignal(bool)

    def __init__(self, stream_link, parent=None):
        super().__init__(parent)
        self.stream_link = stream_link
        self._running = True
        self._cap = None

    def run(self):
        print(f"🎥 Camera {self.stream_link} thread starting...")
        
        # TEST BACKENDS
        backends = [
            (cv2.CAP_V4L2, "V4L2"), 
            (cv2.CAP_ANY, "ANY"), 
            (0, "DEFAULT")
        ]
        
        for backend_id, name in backends:
            print(f"   Testing {name}...")
            cap = cv2.VideoCapture(self.stream_link, backend_id)
            
            if cap.isOpened():
                # 🔥 FIXED: Use CAP_PROP_BUFFERSIZE
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                ret, test_frame = cap.read()
                if ret and test_frame is not None:
                    print(f"✅ [{name}] Camera {self.stream_link}: {test_frame.shape}")
                    
                    # RPi optimizations
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    cap.set(cv2.CAP_PROP_FPS, 20)
                    
                    self._cap = cap
                    self.status_changed.emit(True)
                    break
                cap.release()
        
        if not self._cap:
            print(f"❌ Camera {self.stream_link} failed")
            return

        # MAIN LOOP
        frame_count = 0
        while self._running:
            try:
                ret, frame = self._cap.read()
                if ret and frame is not None:
                    frame_count += 1
                    self.frame_ready.emit(frame)
                    
                    if frame_count % 30 == 0:
                        print(f"📸 Camera {self.stream_link} running...")
                
                else:
                    self.status_changed.emit(False)
                    time.sleep(0.1)
                
                time.sleep(0.05)  # 20 FPS
                
            except Exception as e:
                print(f"Thread error {self.stream_link}: {e}")
                time.sleep(0.5)

    def stop(self):
        self._running = False
        if self._cap:
            self._cap.release()

# CAMERA WIDGET - SIMPLIFIED
class CameraWidget(QtWidgets.QWidget):
    hold_threshold_ms = 400

    def __init__(self, width, height, stream_link=0, parent=None):
        super().__init__(parent)
        print(f"Creating camera {stream_link} widget")
        
        self.stream_link = stream_link
        self.widget_id = f"cam{stream_link}_{id(self)}"
        self.is_fullscreen = False
        self.grid_position = None
        
        self.normal_style = "border: 2px solid #555; background: black;"
        self.swap_style = "border: 4px solid yellow; background: black;"
        self.setStyleSheet(self.normal_style)
        
        self.video_label = QtWidgets.QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setScaledContents(True)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.video_label)
        
        self.frame_count = 0
        self.prev_time = time.time()

        # Start worker
        self.worker = CaptureWorker(stream_link, self)
        self.worker.frame_ready.connect(self.on_frame)
        self.worker.status_changed.connect(self.on_status_changed)
        self.worker.start()
        
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._print_fps)
        self.ui_timer.start(1000)
        
        self.installEventFilter(self)
        self.video_label.installEventFilter(self)

    @pyqtSlot(object)
    def on_frame(self, frame):
        try:
            if frame is None:
                return
            
            # FAST BGR->RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            
            bytes_per_line = 3 * w
            img = QtGui.QImage(rgb.tobytes(), w, h, bytes_per_line, 
                             QtGui.QImage.Format_RGB888)
            pixmap = QtGui.QPixmap.fromImage(img)
            self.video_label.setPixmap(pixmap)
            self.frame_count += 1
            
        except:
            pass

    @pyqtSlot(bool)
    def on_status_changed(self, online):
        if online:
            self.setStyleSheet(self.normal_style)
        else:
            self.video_label.clear()

    def _print_fps(self):
        try:
            now = time.time()
            fps = self.frame_count / (now - self.prev_time)
            if fps > 0:
                print(f"FPS {self.widget_id}: {fps:.1f}")
            self.frame_count = 0
            self.prev_time = now
        except:
            pass

    # Mouse controls (simplified)
    def eventFilter(self, obj, event):
        if obj not in (self, self.video_label):
            return super().eventFilter(obj, event)
        
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                self.toggle_fullscreen()
            elif event.button() == Qt.RightButton:
                self.toggle_fullscreen()
            return True
        return super().eventFilter(obj, event)

    def toggle_fullscreen(self):
        print(f"Fullscreen toggle {self.widget_id}")
        # Simplified - just print for now

    def cleanup(self):
        try:
            self.worker.quit()
            self.worker.wait(2000)
        except:
            pass

# INDUSTRIAL CAMERA DETECTION - FIXED
def find_working_cameras():
    working = []
    print("\n" + "="*50)
    print("🔍 COMPREHENSIVE CAMERA SCAN")
    print("="*50)
    
    devices = glob.glob('/dev/video*')
    print(f"📹 Found: {devices}")
    
    for device in devices:
        try:
            i = int(device[10:])
            print(f"\nTesting {device} (#{i})")
            
            cap = cv2.VideoCapture(i, cv2.CAP_ANY)
            if cap.isOpened():
                # 🔥 FIXED PROP NAME
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                ret, frame = cap.read()
                cap.release()
                
                if ret and frame is not None:
                    print(f"✅ #{i} OK ({frame.shape})")
                    working.append(i)
                else:
                    print(f"⚠️  #{i} no frames")
            else:
                print(f"❌ #{i} can't open")
        except Exception as e:
            print(f"❌ {device}: {e}")
    
    print(f"\n🎯 RESULT: {len(working)} cameras: {working}")
    return working

def get_smart_grid(n):
    if n <= 1: return 1, 1
    if n == 2: return 1, 2
    if n == 3: return 1, 3
    if n == 4: return 2, 2
    return 2, 3

def safe_cleanup(widgets):
    print("🧹 Cleaning...")
    for w in widgets:
        try:
            w.cleanup()
        except:
            pass

# MAIN
def main():
    print("🚀 RPi Camera Grid - FIXED VERSION")
    app = QtWidgets.QApplication(sys.argv)
    camera_widgets = []

    signal.signal(signal.SIGINT, lambda s,f: sys.exit(0))
    atexit.register(lambda: safe_cleanup(camera_widgets))

    if DARKSTYLE_AVAILABLE:
        try:
            app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        except:
            app.setStyle("Fusion")
    else:
        app.setStyle("Fusion")

    mw = QtWidgets.QMainWindow()
    mw.setWindowFlags(Qt.FramelessWindowHint)
    central = QtWidgets.QWidget()
    mw.setCentralWidget(central)
    mw.showFullScreen()

    screen = app.primaryScreen().availableGeometry()
    cameras = find_working_cameras()
    
    layout = QtWidgets.QGridLayout(central)
    layout.setContentsMargins(10,10,10,10)
    layout.setSpacing(10)

    if cameras:
        rows, cols = get_smart_grid(len(cameras))
        w, h = screen.width() // cols, screen.height() // rows
        
        for i, cam_id in enumerate(cameras[:9]):
            widget = CameraWidget(w, h, cam_id, central)
            camera_widgets.append(widget)
            row, col = divmod(i, cols)
            widget.grid_position = (row, col)
            layout.addWidget(widget, row, col)
    else:
        label = QtWidgets.QLabel("NO CAMERAS FOUND\n\nPlug USB cameras\n\nsudo usermod -a -G video $USER")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 32px; color: #ff6666;")
        layout.addWidget(label)

    QShortcut(QKeySequence('Ctrl+Q'), mw, app.quit)
    
    print("\n🎮 Short-click = Fullscreen | Ctrl+Q = Quit")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
