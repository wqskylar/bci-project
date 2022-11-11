# 通信检测功能
import struct
import time

import serial

# 串口相关函数功能
from PySide2.QtCore import *
from PySide2.QtWidgets import QFileDialog


class Serial_interface(QObject):
    signal1 = Signal(str)

    def __init__(self):
        super(Serial_interface, self).__init__()
        port = 'com4'  # 串口
        baudrate = 921600  # 波特率
        bytesize = 8  # 比特数
        parity = 'N'  # 校验
        stopbits = 1
        try:
            global ser
            ser = serial.Serial(port, baudrate, bytesize, parity, stopbits, timeout=2)
            while ser.isOpen():
                print('串口打开成功！')
                break
        except Exception as e:
            print("串口打开失败！", e)

    def try_detect(self):
        try:
            send_data = "40\r\n"
            ser.write(str(send_data).encode('ISO-8859-1'))
            print("已发送数据：", send_data)
        except Exception as e:
            self.signal1.emit('命令发送失败!')

        while 1:

            if ser.inWaiting():  # 直到有数据
                data = ser.read(1).decode('ISO-8859-1')  # ASCII
                print("收到的命令是：", data)
                if data == 'o':
                    self.signal1.emit("通信连接成功！")
                    break
                else:
                    self.signal1.emit("通信连接失败！")
                    break


# 选择一个文件
def select_a_file(stats):
    # 该语句的返回值类型是一个元组，第一个元素是文件路径，第二个是文件类型
    file_path, its_type = QFileDialog.getOpenFileName(
        stats,  # 父窗口对象
        "选择你要上传的文本",  # 标题
        r"d:\\data",  # 起始目录
        "文本类型(All Flies(*)) "  # 选择类型过滤项，过滤内容在括号中
    )
    temp_tip = file_path
    return temp_tip


# 阻抗检测，开始检测函数
class Detect(QThread):
    signal1 = Signal(float)

    def __init__(self):
        super(Detect, self).__init__()
        self.i = 0

    def run(self):
        send_data = "3060\r\n"
        ser.write(str(send_data).encode('utf-8'))
        print("已发送数据：", send_data)
        while 1:
            if ser.inWaiting():
                data = ser.read(4).decode('ISO-8859-1')
                a = bytes(data, encoding='ISO-8859-1').hex()
                b = float(struct.unpack('>f', bytes.fromhex(a))[0])
                self.signal1.emit(b)
                self.i += 1
            if self.i >= 60:
                self.i = 0
                break


# 第一页重新检测按钮
def re_start_check(my_software):
    my_software.i = 0
    my_software.rs_time = 0
    my_software.rs_times.clear()
    my_software.rs_data.clear()
    print("开始重新检测")


def data_storage(file_path, data):
    try:
        with open(str(file_path), 'w') as file_object:
            file_object.write(str(data))
        print("存储成功！")
    except:
        print("存储失败！请重新检测！")


class data_collection(QThread):
    signal5 = Signal(list)  # 采集到的数据进行绘图的信号

    def __init__(self, method, quantity):
        super(data_collection, self).__init__()

        self.time2 = 0  # 采集次数
        self.t = 0  # 时间

        self.datasheet1 = []
        self.datasheet2 = []
        self.datasheet3 = []
        self.datasheet4 = []
        self.datasheet5 = []
        self.datasheet6 = []
        self.datasheet7 = []
        self.datasheet8 = []
        self.lists = [self.datasheet1, self.datasheet2, self.datasheet3, self.datasheet4, self.datasheet5,
                      self.datasheet6, self.datasheet7, self.datasheet8]

        self.error_times = 0
        self.method = method
        self.quantity = quantity

    def run(self):
        collected_quantity = self.quantity
        if self.method == '定量采集':
            self.send_order = 10

        elif self.method == '定时采集':
            self.send_order = 20

        send_message = str(self.send_order) + str(collected_quantity) + '\r\n'
        ser.write(send_message.encode('utf-8'))
        print('发送的命令为:' + send_message)
        print(type(send_message))
        print(send_message.encode('US-ASCII'))

        timer1 = time.time()
        self.lists = [self.datasheet1, self.datasheet2, self.datasheet3, self.datasheet4, self.datasheet5,
                      self.datasheet6, self.datasheet7, self.datasheet8]

        while 1:
            if ser.inWaiting():
                timer3 = time.time()
                data = ser.read(58).decode('ISO-8859-1')
                a = bytes(data, encoding='ISO-8859-1').hex()
                # print('a的值为：',a)
                timer5 = time.time()

                for list in self.lists:
                    try:
                        b1, b2 = a.split('0d0a', 1)
                        b1 = b1[-8:]
                        d = float(struct.unpack('>f', bytes.fromhex(b1))[0])
                        list.append(d)
                        a = b2

                        if len(a) == 14:
                            self.time2 += 1
                            b1 = a[2:10]
                            d = float(struct.unpack('>f', bytes.fromhex(b1))[0])
                            self.lists[-1].append(d)

                            self.signal5.emit(self.lists)

                            self.datasheet1.clear()
                            self.datasheet2.clear()
                            self.datasheet3.clear()
                            self.datasheet4.clear()
                            self.datasheet5.clear()
                            self.datasheet6.clear()
                            self.datasheet7.clear()
                            self.datasheet8.clear()
                            timer4 = time.time()
                            break

                    except:
                        # 先将每个数组清零
                        self.datasheet1.clear()
                        self.datasheet2.clear()
                        self.datasheet3.clear()
                        self.datasheet4.clear()
                        self.datasheet5.clear()
                        self.datasheet6.clear()
                        self.datasheet7.clear()
                        self.datasheet8.clear()
                        self.time2 += 1
                        self.error_times += 1
                        break

            if self.time2 >= collected_quantity:
                timer2 = time.time()
                print("总耗时为：" + str(timer2 - timer1))
                self.time2 = 0
                self.datasheet1.clear()
                self.datasheet2.clear()
                self.datasheet3.clear()
                self.datasheet4.clear()
                self.datasheet5.clear()
                self.datasheet6.clear()
                self.datasheet7.clear()
                self.datasheet8.clear()

                print("失败次数为：" + str(self.error_times))
                self.error_times = 0
                print("数据传输完成！")
                break
