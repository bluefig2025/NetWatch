import sys
import ctypes
import subprocess
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QDockWidget, QFormLayout, QPushButton, QLineEdit
from PySide6.QtCore import QTimer, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import psutil
from ping3 import ping

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate_for_sniffing():
    subprocess.Popen(
        [sys.executable, __file__, "--sniff"],
        creationflags=subprocess.CREATE_NO_WINDOW
    )

def main():
    app = QApplication(sys.argv)
    window = NetWatch()
    window.show()
    sys.exit(app.exec())

class NetWatch(QMainWindow):
    VERSION = "1.0"
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NetWatch - Network Performance Monitor v1.0")
        self.setGeometry(100, 100, 800, 600)

        self.download_speed_label = QLabel("Download Speed: 0.00 Mbps")
        self.upload_speed_label = QLabel("Upload Speed: 0.00 Mbps")
        self.latency_label = QLabel("Latency: 0.00 ms")

        for label in [self.download_speed_label, self.upload_speed_label, self.latency_label]:
            label.setStyleSheet("font-size: 16px; margin: 5px;")

        stats_layout = QVBoxLayout()
        stats_layout.addWidget(self.download_speed_label)
        stats_layout.addWidget(self.upload_speed_label)
        stats_layout.addWidget(self.latency_label)

        self.graph_figure = Figure()
        self.graph_canvas = FigureCanvas(self.graph_figure)
        self.graph_ax = self.graph_figure.add_subplot(111)
        self.graph_ax.set_title("Network Performance")
        self.graph_ax.set_xlabel("Time (s)")
        self.graph_ax.set_ylabel("Speed (Mbps)")

        self.time_data = []
        self.download_data = []
        self.upload_data = []

        main_layout = QVBoxLayout()
        main_layout.addLayout(stats_layout)
        main_layout.addWidget(self.graph_canvas)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.create_more_panel()

        self.previous_counters = psutil.net_io_counters()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)
        self.elapsed_time = 0

    def create_more_panel(self):
        self.more_dock = QDockWidget("More", self)
        self.more_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable)

        more_widget = QWidget()
        more_layout = QFormLayout()

        self.settings_button = QPushButton("Settings")
        more_layout.addRow(self.settings_button)

        self.ping_button = QPushButton("Ping Server")
        self.ping_button.clicked.connect(self.ping_server)
        more_layout.addRow(self.ping_button)

        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("Enter server address")
        more_layout.addRow("Server:", self.server_input)

        self.ping_result_label = QLabel("Ping Result: ")
        more_layout.addRow(self.ping_result_label)

        more_widget.setLayout(more_layout)
        self.more_dock.setWidget(more_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.more_dock)

    def ping_server(self):
        server = self.server_input.text()
        if not server:
            self.ping_result_label.setText("Ping Result: No server address entered.")
            return

        latency = ping(server, timeout=2)
        if latency is None:
            self.ping_result_label.setText(f"Ping Result: Failed to reach {server}.")
        else:
            self.ping_result_label.setText(f"Ping Result: {latency * 1000:.2f} ms to {server}.")
        self.addDockWidget(Qt.RightDockWidgetArea, self.more_dock)

    def update_stats(self):
        current_counters = psutil.net_io_counters()
        download_bytes = current_counters.bytes_recv - self.previous_counters.bytes_recv
        upload_bytes = current_counters.bytes_sent - self.previous_counters.bytes_sent

        download_speed = (download_bytes * 8) / 1_000_000
        upload_speed = (upload_bytes * 8) / 1_000_000

        latency = ping("8.8.8.8", timeout=1)
        latency = latency * 1000 if latency else -1

        self.previous_counters = current_counters

        self.download_speed_label.setText(f"Download Speed: {download_speed:.2f} Mbps")
        self.upload_speed_label.setText(f"Upload Speed: {upload_speed:.2f} Mbps")
        self.latency_label.setText(f"Latency: {latency:.2f} ms" if latency != -1 else "Latency: N/A")

        self.elapsed_time += 1
        self.time_data.append(self.elapsed_time)
        self.download_data.append(download_speed)
        self.upload_data.append(upload_speed)

        if len(self.time_data) > 60:
            self.time_data.pop(0)
            self.download_data.pop(0)
            self.upload_data.pop(0)

        self.graph_ax.clear()
        self.graph_ax.plot(self.time_data, self.download_data, label="Download Speed (Mbps)", color="blue")
        self.graph_ax.plot(self.time_data, self.upload_data, label="Upload Speed (Mbps)", color="green")
        self.graph_ax.legend()
        self.graph_ax.set_title("Network Performance")
        self.graph_ax.set_xlabel("Time (s)")
        self.graph_ax.set_ylabel("Speed (Mbps)")
        self.graph_canvas.draw()

if __name__ == "__main__":
    main()
