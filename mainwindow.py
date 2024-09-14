from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton,QLineEdit,QWidget,QMessageBox
import zmq
import struct
import sys
import subprocess
import datetime
import random
import string

class VideoPlayer:
    def __init__(self):
        self.ffplay_process = None

    def start_player(self, width, height, type):
        if self.ffplay_process is not None:
            return

        random_string = self.generate_random_string()

        if type == 1 or type == 0:
            self.ffplay_process = subprocess.Popen(
                ['ffplay', '-window_title', 'raw_' + random_string, '-f', 'rawvideo', '-pixel_format', 'nv12', '-video_size', f'{width}x{height}', '-i', '-'],
                stdin=subprocess.PIPE
            )
        else:
            self.ffplay_process = subprocess.Popen(
                ['ffplay', '-window_title', 'encode_hevc_' + str(type),  '-codec:v', 'hevc', '-i', '-'],
                stdin=subprocess.PIPE
            )

    def stop_player(self):
        if self.ffplay_process is not None:
            self.ffplay_process.terminate()  # 发送终止信号
            self.ffplay_process.wait()  # 等待进程结束
            self.ffplay_process = None

    def show(self, image_data):
        if self.ffplay_process is None:
            return
        self.ffplay_process.stdin.write(image_data)
        self.ffplay_process.stdin.flush()

    def generate_random_string(self, length=3):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for _ in range(length))

class ZmqService(QThread):

    def __init__(self, zmq_host: str, zmq_port: str):
        super().__init__()
        self.zmq_host = zmq_host
        self.zmq_port = zmq_port
        self.context = zmq.Context()
        self.stop_flag = False
        self.record_flag = False
        self.video_file = None
        self.video_player = None
    def run(self):
        print('start')
        self.stop_flag = False
        self.zmq_socket = self.context.socket(zmq.SUB)
        self.zmq_socket.connect('tcp://{}:{}'.format(self.zmq_host, self.zmq_port))
        self.zmq_socket.setsockopt_string(zmq.SUBSCRIBE, '')
        self.video_player = VideoPlayer()
        try:
            while not self.stop_flag:
                try:
                    data = self.zmq_socket.recv(flags=zmq.NOBLOCK)
                    type, height, width, size_byte = struct.unpack('IIII', data[:16])
                    image_data = data[16:16+size_byte]
                    current_time = datetime.datetime.now().strftime("%H:%M:%S")
                    print(f'{current_time} Type: {type}, Height: {height}, Width: {width}, Size: {size_byte}')
                    self.video_player.start_player(width, height, type)
                    self.video_player.show(image_data)
                    if self.record_flag:
                        if not self.video_file:
                            filename = f"{type}_{height}.raw"
                            self.video_file = open(filename, "wb")#覆盖，'ab'追加
                        self.video_file.write(image_data)
                except zmq.Again:
                    self.sleep(0.001)
        finally:
            print('Cleaning up ZmqService...')
            self.zmq_socket.close()
            self.context.term()

    def stop(self):
        self.stop_flag = True
        self.quit()
        self.video_player.stop_player()
        self.record_flag = False
        if self.video_file:
            self.video_file.close()
            self.video_file = None


    def set_record(self,flag):
        if flag and not self.record_flag:
            # Start recording
            self.record_flag = flag
        elif not flag and self.record_flag:
            # Stop recording
            self.record_flag = flag
            if self.video_file:
                self.video_file.close()
                self.video_file = None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZeroMQ NV12 Image Receiver")
        self.is_record = False

        # GUI布局
        layout = QVBoxLayout()

        # IP地址输入
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter ZeroMQ Server IP")
        self.ip_input.setText("10.3.1.32") #默认值
        layout.addWidget(self.ip_input)

        # 原图端口输入
        self.port_raw_input = QLineEdit()
        self.port_raw_input.setPlaceholderText("Enter ZeroMQ Server Raw Port")
        self.port_raw_input.setText("6000") #统一值
        layout.addWidget(self.port_raw_input)

        # 原图端口输入1
        self.port_raw_input1 = QLineEdit()
        self.port_raw_input1.setPlaceholderText("Enter ZeroMQ Server Raw1 Port")
        self.port_raw_input1.setText("6001")  #统一值
        layout.addWidget(self.port_raw_input1)

        # 编码图端口输入
        self.port_encode_input = QLineEdit()
        self.port_encode_input.setPlaceholderText("Enter ZeroMQ Server Encode Port")
        self.port_encode_input.setText("6002")  #统一值
        layout.addWidget(self.port_encode_input)

        # 编码图1端口输入
        self.port_encode1_input = QLineEdit()
        self.port_encode1_input.setPlaceholderText("Enter ZeroMQ Server Encode1 Port")
        self.port_encode1_input.setText("6003") #统一值
        layout.addWidget(self.port_encode1_input)

        # 编码图2端口输入
        self.port_encode2_input = QLineEdit()
        self.port_encode2_input.setPlaceholderText("Enter ZeroMQ Server Encode2 Port")
        self.port_encode2_input.setText("6004")  #统一值
        layout.addWidget(self.port_encode2_input)

        # 编码图3端口输入
        self.port_encode3_input = QLineEdit()
        self.port_encode3_input.setPlaceholderText("Enter ZeroMQ Server Encode3 Port")
        self.port_encode3_input.setText("6005")  #统一值
        layout.addWidget(self.port_encode3_input)

        # 编码图4端口输
        self.port_encode4_input = QLineEdit()
        self.port_encode4_input.setPlaceholderText("Enter ZeroMQ Server Encode4 Port")
        self.port_encode4_input.setText("6006")  #统一值
        layout.addWidget(self.port_encode4_input)

        # 开始按钮
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_receiving)
        layout.addWidget(self.start_button)

        # 停止按钮
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_receiving)
        layout.addWidget(self.stop_button)

        # 录制
        self.recode_button = QPushButton("开始录制")
        self.recode_button.clicked.connect(self.record_button_click)
        layout.addWidget(self.recode_button)

        # 设置中央Widget和布局
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.zmq_service_raw = None
        self.zmq_service_raw1 = None
        self.zmq_service_encode = None
        self.zmq_service_encode1 = None
        self.zmq_service_encode2 = None
        self.zmq_service_encode3 = None
        self.zmq_service_encode4 = None

    def is_valid_ip(self, ip: str) -> bool:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            if not part.isdigit() or not 0 <= int(part) <= 255:
                return False
        return True

    def record_button_click(self):
        if self.is_record:#停止
            self.is_record = False
            self.recode_button.setText("开始录制")
            self.recode_button.setStyleSheet('')
            self.zmq_service_raw.set_record(False)
            self.zmq_service_raw1.set_record(False)
            self.zmq_service_encode.set_record(False)
            self.zmq_service_encode1.set_record(False)
            self.zmq_service_encode2.set_record(False)
            self.zmq_service_encode3.set_record(False)
            self.zmq_service_encode4.set_record(False)
        else:#开始
            self.is_record = True
            self.recode_button.setText("停止录制")
            self.recode_button.setStyleSheet('background-color: red')
            self.zmq_service_raw.set_record(True)
            self.zmq_service_raw1.set_record(True)
            self.zmq_service_encode.set_record(True)
            self.zmq_service_encode1.set_record(True)
            self.zmq_service_encode2.set_record(True)
            self.zmq_service_encode3.set_record(True)
            self.zmq_service_encode4.set_record(True)

    def start_receiving(self):
        zmq_host = self.ip_input.text()
        if not zmq_host or not self.is_valid_ip(zmq_host):
            QMessageBox.warning(self, "Error", "Invalid ZeroMQ server IP address.")
            return

        zmq_port_raw = self.port_raw_input.text()
        if self.zmq_service_raw is None and zmq_port_raw != '':
            self.zmq_service_raw = ZmqService(zmq_host, zmq_port_raw)
            self.zmq_service_raw.start()

        zmq_port_raw1 = self.port_raw_input1.text()
        if self.zmq_service_raw1 is None and zmq_port_raw1 != '':
            self.zmq_service_raw1 = ZmqService(zmq_host, zmq_port_raw1)
            self.zmq_service_raw1.start()

        zmq_port_encode = self.port_encode_input.text()
        print(zmq_port_encode)
        if self.zmq_service_encode is None and zmq_port_encode != '':
            self.zmq_service_encode = ZmqService(zmq_host, zmq_port_encode)
            self.zmq_service_encode.start()

        zmq_port_encode1 = self.port_encode1_input.text()
        if self.zmq_service_encode1 is None and zmq_port_encode1 != '':
            self.zmq_service_encode1 = ZmqService(zmq_host, zmq_port_encode1)
            self.zmq_service_encode1.start()

        zmq_port_encode2 = self.port_encode2_input.text()
        if self.zmq_service_encode2 is None and zmq_port_encode2 != '':
            self.zmq_service_encode2 = ZmqService(zmq_host, zmq_port_encode2)
            self.zmq_service_encode2.start()

        zmq_port_encode3 = self.port_encode3_input.text()
        if self.zmq_service_encode3 is None and zmq_port_encode3 != '':
            self.zmq_service_encode3 = ZmqService(zmq_host, zmq_port_encode3)
            self.zmq_service_encode3.start()

        zmq_port_encode4 = self.port_encode4_input.text()
        if self.zmq_service_encode4 is None and zmq_port_encode4 != '':
            self.zmq_service_encode4 = ZmqService(zmq_host, zmq_port_encode4)
            self.zmq_service_encode4.start()

    def stop_receiving(self):
        if self.is_record:
            self.record_button_click()  # 停止录制

        if self.zmq_service_raw is not None:
            self.zmq_service_raw.stop()
            self.zmq_service_raw.wait()
            self.zmq_service_raw = None

        if self.zmq_service_raw1 is not None:
            self.zmq_service_raw1.stop()
            self.zmq_service_raw1.wait()
            self.zmq_service_raw1 = None

        if self.zmq_service_encode is not None:
            self.zmq_service_encode.stop()
            self.zmq_service_encode.wait()
            self.zmq_service_encode = None

        if self.zmq_service_encode1 is not None:
            self.zmq_service_encode1.stop()
            self.zmq_service_encode1.wait()
            self.zmq_service_encode1 = None

        if self.zmq_service_encode2 is not None:
            self.zmq_service_encode2.stop()
            self.zmq_service_encode2.wait()
            self.zmq_service_encode2 = None

        if self.zmq_service_encode3 is not None:
            self.zmq_service_encode3.stop()
            self.zmq_service_encode3.wait()
            self.zmq_service_encode3 = None

        if self.zmq_service_encode4 is not None:
            self.zmq_service_encode4.stop()
            self.zmq_service_encode4.wait()
            self.zmq_service_encode4 = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
