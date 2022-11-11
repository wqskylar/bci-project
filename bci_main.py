import pywt
from PySide2.QtWidgets import *
from PySide2.QtUiTools import QUiLoader

from PySide2.QtCore import QObject, Signal, Slot
import pyqtgraph as pg

from scipy import signal
from scipy.fftpack import fft

import numpy as np

import details

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'black')


class MySignal(QObject):
    signal1 = Signal(str)  # 通信检测信号
    signal4 = Signal(str, int)  # 采集方式信号

    signal7 = Signal(str)  # 通道1选择
    signal8 = Signal(str)  # 通道1选择
    signal9 = Signal(str)  # 通道1选择
    signal10 = Signal(str)  # 通道1选择


class My_software(QWidget):

    def __init__(self):
        super(My_software, self).__init__()

        loader = QUiLoader()
        loader.registerCustomWidget(pg.PlotWidget)
        self.ui = loader.load('bci_ui.ui')

        # 串口实例化，并初始化连接
        self.serial_interface = details.Serial_interface()
        self.serial_interface.signal1.connect(self.showMessage11)
        # 初始时刻的变量创建
        self.i = 0
        self.t = 0

        # # 阻抗检测相关初始参数
        self.detect = None  # 开始检测对象
        self.rs_time = 0
        self.rs_times = []
        self.rs_data = []

        # 数据采集
        self.acquisitionState = 0  # 采集方式  标识符
        self.detection = None  # 开始采集对象
        self.method = ''  # 采集方式
        self.quantity = ''  # 采集数量
        self.times = []  # 采集时间

        # 采集数据相关参数
        # 频道
        self.channel1 = []
        self.channel2 = []
        self.channel3 = []
        self.channel4 = []
        self.channel5 = []
        self.channel6 = []
        self.channel7 = []
        self.channel8 = []

        # 频道列表
        self.channels = [self.channel1, self.channel2, self.channel3, self.channel4, self.channel5, self.channel6,
                         self.channel7, self.channel8]

        # 第四页单选按钮初始设定， 为 “无”
        self.type = None

        # 第五页 频道
        self.ch1 = []
        self.ch2 = []
        self.ch3 = []
        self.ch4 = []
        self.channelMark = []

        self.ms = MySignal()

        # 第一页
        # 按钮
        self.ui.p1b1.clicked.connect(self.handleCalc11)  # 通信检测
        self.ui.p1b2.clicked.connect(self.handleCalc12)  # 阻抗数据存储路径
        self.ui.p1b3.clicked.connect(self.handleCalc13)  # 开始检测
        self.ui.p1b4.clicked.connect(self.handleCalc14)  # 重新检测
        self.ui.p1b5.clicked.connect(self.handleCalc15)  # 存储阻抗数据

        # 图表
        self.ui.p1_huitu1.addLegend()
        self.curve_rs = self.ui.p1_huitu1.plot(pen='blue', name='阻抗')
        self.ui.p1_huitu1.setLabel("left", '欧姆(Ω)')
        self.ui.p1_huitu1.setLabel('bottom', '时间(s)')
        self.ui.p1_huitu1.showGrid(x=True, y=True)
        self.ui.p1_huitu1.setTitle('阻抗波形')

        # 第二页
        # 按钮
        self.ui.p2b1.clicked.connect(self.handleCalc21)  # 脑电数据存储路径选择
        self.ui.c_box.currentIndexChanged.connect(self.methodChange)  # 组合文本框改变选项时
        self.ui.p2b2.clicked.connect(self.handleCalc22)  # 参数确认
        self.ui.p2b3.clicked.connect(self.handleCalc23)  # 开始采集
        self.ui.p2b4.clicked.connect(self.handleCalc24)  # 重新采集
        self.ui.p2b5.clicked.connect(self.handleCalc25)  # 存储采集数据

        # 文本框相关
        self.ui.p2t2.setEnabled(True)
        self.ui.p2t3.setEnabled(False)
        self.ui.p2t4.setEnabled(False)
        self.ui.p2t2.editingFinished.connect(self.acquisition_parameters)
        self.ui.p2t3.editingFinished.connect(self.acquisition_parameters)
        self.ms.signal4.connect(self.parameters_conduction)  # 传递采集参数的信号

        # 图表
        self.ui.p2_huitu1.addLegend()
        self.curve1 = self.ui.p2_huitu1.plot(pen='red', name='频道1')
        self.curve2 = self.ui.p2_huitu1.plot(pen='yellow', name='频道2')
        self.curve3 = self.ui.p2_huitu1.plot(pen='blue', name='频道3')
        self.curve4 = self.ui.p2_huitu1.plot(pen='green', name='频道4')

        self.ui.p2_huitu1.setLabel("left", '伏特（V）')
        self.ui.p2_huitu1.setLabel("bottom", "毫秒（ms）")
        self.ui.p2_huitu1.showGrid(x=True, y=True)
        self.ui.p2_huitu1.setTitle('数据采集')

        # 第三页
        self.ui.p3b1.clicked.connect(self.handleCalc31)  # 显示数据
        self.ui.p3b2.clicked.connect(self.handleCalc32)  # 数据清除

        # 第四页
        self.ui.c_box2.currentIndexChanged.connect(self.filter_type)  # 滤波器类型

        # 单选按钮组状态改变时
        self.ui.radioButton1.toggled.connect(self.typeSelection)
        self.ui.radioButton2.toggled.connect(self.typeSelection)
        self.ui.radioButton3.toggled.connect(self.typeSelection)
        self.ui.radioButton4.toggled.connect(self.typeSelection)

        self.ui.p4b1.clicked.connect(self.amplitude_frequency)  # 幅频响应
        # 图表 幅频响应
        self.ui.p4_huitu1.addLegend()
        self.ui.p4_huitu1.setLabel("left", '增益（dB）')
        self.ui.p4_huitu1.setLabel("bottom", "频率（Hz）")
        self.ui.p4_huitu1.setTitle('幅频响应')
        self.response = self.ui.p4_huitu1.plot(pen="red", name='响应')

        # 第五页
        self.ui.p5b1.clicked.connect(self.handleCalc51)  # 数据路径
        self.ui.p5b2.clicked.connect(self.handleCalc52)  # 数据处理
        self.ui.p5b3.clicked.connect(self.handleCalc53)  # 滤波存储数据路径
        self.ui.p5b4.clicked.connect(self.handleCalc54)  # 数据储存

        self.ms.signal7.connect(self.data_plot)
        self.ms.signal8.connect(self.data_plot)
        self.ms.signal9.connect(self.data_plot)
        self.ms.signal10.connect(self.data_plot)

        self.ui.checkBox.stateChanged.connect(self.ch1Emit)
        self.ui.checkBox_2.stateChanged.connect(self.ch2Emit)
        self.ui.checkBox_3.stateChanged.connect(self.ch3Emit)
        self.ui.checkBox_4.stateChanged.connect(self.ch4Emit)

        # 图1
        self.ui.p5_huitu1.addLegend()
        self.ui.p5_huitu1.setLabel("left", '幅值(μV)')
        self.ui.p5_huitu1.setLabel('bottom', '时间(s)')
        self.ui.p5_huitu1.showGrid(x=True, y=True)
        self.ui.p5_huitu1.setTitle('源数据波形')

        # 图2
        self.ui.p5_huitu2.addLegend()
        self.ui.p5_huitu2.setLabel("left", '归一化幅值(μV)')
        self.ui.p5_huitu2.setLabel('bottom', '频率(Hz)')
        self.ui.p5_huitu2.showGrid(x=True, y=True)
        self.ui.p5_huitu2.setTitle('源数据频谱')

        # 图三
        self.ui.p5_huitu3.addLegend()
        self.ui.p5_huitu3.setLabel("left", '归一化幅值(μV)')
        self.ui.p5_huitu3.setLabel('bottom', '频率(Hz)')
        self.ui.p5_huitu3.showGrid(x=True, y=True)
        self.ui.p5_huitu3.setTitle('滤波后频谱')

        # 图四
        self.ui.p5_huitu4.addLegend()
        self.ui.p5_huitu4.setLabel("left", '幅值(μV)')
        self.ui.p5_huitu4.setLabel('bottom', '时间(s)')
        self.ui.p5_huitu4.showGrid(x=True, y=True)
        self.ui.p5_huitu4.setTitle('滤波后波形')

        # 源数据
        self.source_curve1 = self.ui.p5_huitu1.getPlotItem().plot(pen=pg.mkPen('r', width=1), name='channel1')
        self.source_curve2 = self.ui.p5_huitu1.getPlotItem().plot(pen=pg.mkPen('b', width=1), name='channel2')
        self.source_curve3 = self.ui.p5_huitu1.getPlotItem().plot(pen=pg.mkPen('g', width=1), name='channel3')
        self.source_curve4 = self.ui.p5_huitu1.getPlotItem().plot(pen=pg.mkPen('y', width=1), name='channel4')
        # 源数据频谱
        self.wp_curve1 = self.ui.p5_huitu2.getPlotItem().plot(pen=pg.mkPen('r', width=1), name='channel1')
        self.wp_curve2 = self.ui.p5_huitu2.getPlotItem().plot(pen=pg.mkPen('b', width=1), name='channel2')
        self.wp_curve3 = self.ui.p5_huitu2.getPlotItem().plot(pen=pg.mkPen('g', width=1), name='channel3')
        self.wp_curve4 = self.ui.p5_huitu2.getPlotItem().plot(pen=pg.mkPen('y', width=1), name='channel4')
        self.wpCurve = [self.wp_curve1, self.wp_curve2, self.wp_curve3, self.wp_curve4]
        # 滤波后频谱图
        self.fft_curve1 = self.ui.p5_huitu3.getPlotItem().plot(pen=pg.mkPen('r', width=1), name='channel1')
        self.fft_curve2 = self.ui.p5_huitu3.getPlotItem().plot(pen=pg.mkPen('b', width=1), name='channel2')
        self.fft_curve3 = self.ui.p5_huitu3.getPlotItem().plot(pen=pg.mkPen('g', width=1), name='channel3')
        self.fft_curve4 = self.ui.p5_huitu3.getPlotItem().plot(pen=pg.mkPen('y', width=1), name='channel4')
        # 滤波后波形
        self.filter_curve1 = self.ui.p5_huitu4.getPlotItem().plot(pen=pg.mkPen('r', width=1), name='channel1')
        self.filter_curve2 = self.ui.p5_huitu4.getPlotItem().plot(pen=pg.mkPen('b', width=1), name='channel2')
        self.filter_curve3 = self.ui.p5_huitu4.getPlotItem().plot(pen=pg.mkPen('g', width=1), name='channel3')
        self.filter_curve4 = self.ui.p5_huitu4.getPlotItem().plot(pen=pg.mkPen('y', width=1), name='channel4')

    # 按钮点击功能函数
    # 第一页
    # 通信检测按钮
    def handleCalc11(self):
        self.serial_interface.try_detect()

    def showMessage11(self, a):
        self.ui.p1t1.setText(a)

    # 阻抗数据存储路径按钮
    def handleCalc12(self):
        self.ui.p1t2.setText(details.select_a_file(self.ui))

    # 阻抗检测的开始检测按钮
    def handleCalc13(self):
        self.detect = details.Detect()
        self.detect.signal1.connect(self.rs_detect)
        self.detect.start()

    def rs_detect(self, data):
        self.rs_time += 0.5
        self.rs_data.append(data)
        self.rs_times.append(self.rs_time - 0.5)
        print('获取了一组阻抗数据', self.rs_time - 0.5, data)
        self.curve_rs.setData(self.rs_times, self.rs_data)

    # 重新检测按钮
    def handleCalc14(self):
        details.re_start_check(self)

    # 存储数据按钮
    def handleCalc15(self):
        details.data_storage(self.ui.p1t2.text(), self.rs_data)

    # 第二页
    def handleCalc21(self):
        self.ui.p2t1.setText(details.select_a_file(self.ui))

    def handleCalc22(self):
        pass

    def methodChange(self):
        text = self.ui.c_box.currentText()
        if text == '定量采集':
            self.ui.p2t3.setEnabled(False)
            self.ui.p2t2.setEnabled(True)
            self.ui.p2t3.clear()
            self.ui.p2t2.clear()
            self.acquisitionState = 1
        elif text == '定时采集':
            self.ui.p2t3.setEnabled(True)
            self.ui.p2t2.setEnabled(False)
            self.ui.p2t3.clear()
            self.ui.p2t2.clear()
            self.acquisitionState = 2

    def acquisition_parameters(self):
        if self.acquisitionState == 0:
            print("请先输入采集参数")
        else:
            if self.acquisitionState == 1:
                quantity = self.ui.p2t2.text()
                self.ms.signal4.emit('定量采集', int(quantity))
            elif self.acquisitionState == 2:
                time = self.ui.p2t3.text()
                self.ms.signal4.emit('定时采集', int(time))
            elif self.acquisitionState == 3:
                pass

    def parameters_conduction(self, method, quantity):


        print('参数传递完成', method, quantity)
        text = '参数传递完成\r' + method + '\r' + str(quantity)
        self.ui.p2t4.setText(text)
        self.detection = details.data_collection(method, quantity)
        self.detection.signal5.connect(self.plot_collect_data)


    def plot_collect_data(self, datas):
        try:
            i = 0
            for a in datas:
                self.channels[i].append(a[0])
                i += 1
        except:
            print("数据错误")
        self.i += 1
        self.t += 2
        self.times.append(self.t - 2)

        try:
            self.curve1.setData(self.times, self.channel1)
            self.curve2.setData(self.times, self.channel2)
            self.curve3.setData(self.times, self.channel3)
            self.curve4.setData(self.times, self.channel4)

        except:
            print("绘图错误！")

    def handleCalc23(self):
        if self.detection is None:
            print("请先输入参数再开始采集")
        else:
            print('检测开始')
            self.detection.start()

    def handleCalc24(self):
        self.ui.c_box.setCurrentIndex(0)
        self.i = 0
        self.t = 0
        self.times.clear()
        self.channel1 = []
        self.channel2 = []
        self.channel3 = []
        self.channel4 = []
        self.channel5 = []
        self.channel6 = []
        self.channel7 = []
        self.channel8 = []
        self.channels = [self.channel1, self.channel2, self.channel3, self.channel4, self.channel5, self.channel6,
                         self.channel7, self.channel8]

        self.ui.p2t2.setText("")
        self.ui.p2t3.setText("")
        self.ui.p2t4.setText("采集参数已清空")

    def handleCalc25(self):
        with open(str(self.ui.p2t1.text()), 'w') as file_object1:
            file_object1.write(str(self.channel1))
            file_object1.write(str('0d0a') + str(self.channel2))
            file_object1.write(str('0d0a') + str(self.channel3))
            file_object1.write(str('0d0a') + str(self.channel4))

        self.ui.p2t4.setText("已完成采集数据储存")

    # 第三页
    def handleCalc31(self):
        try:
            with open(str(self.ui.p2t1.text()), 'r') as file:
                data = file.read()
            self.ui.p3t3.setPlainText("数据为：\r\n" + data)
            self.ui.p3t1.setText("文件读取成功")
        except FileNotFoundError:
            self.ui.p3t1.setText("文件读取失败")

    def handleCalc32(self):
        self.ui.p3t3.clear()
        self.ui.p3t2.setText("数据清除成功")

    # 第四页
    def filter_type(self):
        filter_type = self.ui.c_box2.currentText()

        if filter_type == '巴特沃夫':
            self.ui.p4t7.setEnabled(False)
            self.ui.p4t8.setEnabled(False)
        if filter_type == '切比雪夫-I':
            self.ui.p4t8.setEnabled(False)
            self.ui.p4t7.setEnabled(True)
        if filter_type == '切比雪夫-II':
            self.ui.p4t8.setEnabled(True)
            self.ui.p4t7.setEnabled(False)
        if filter_type == '椭圆':
            self.ui.p4t8.setEnabled(True)
            self.ui.p4t7.setEnabled(True)

    def typeSelection(self):
        type = self.sender()  # 获取调用此函数的控件对象
        if type.isChecked():
            if type.text() == '低通':
                self.type = 'lowpass'
                self.ui.p4t2.setEnabled(False)
                self.ui.p4t3.setEnabled(False)
                self.ui.p4t7.setEnabled(False)
                self.ui.p4t8.setEnabled(False)

            if type.text() == '高通':
                self.type = 'highpass'
                self.ui.p4t2.setEnabled(False)
                self.ui.p4t3.setEnabled(False)
                self.ui.p4t7.setEnabled(False)
                self.ui.p4t8.setEnabled(False)

            if type.text() == '带通':
                self.type = 'bandpass'
                self.ui.p4t2.setEnabled(True)
                self.ui.p4t7.setEnabled(False)
                self.ui.p4t3.setEnabled(True)
            if type.text() == '带阻':
                self.type = 'bandstop'
                self.ui.p4t2.setEnabled(True)
                self.ui.p4t3.setEnabled(True)
        print(self.type)

    def amplitude_frequency(self):
        global Wn
        global N

        # print(self.type)
        # print(type(self.type))

        if self.ui.c_box2.currentText() == '巴特沃夫':

            if self.type == 'bandpass' or self.type == 'bandstop':
                wp_up = int(self.ui.p4t1.text())  # 通带上边缘
                wp_down = int(self.ui.p4t2.text())  # 通带下边缘
                ws_up = int(self.ui.p4t3.text())  # 阻带上边缘
                ws_down = int(self.ui.p4t4.text())  # 阻带下边缘
                gpass = int(self.ui.p4t5.text())  # 通带最大损耗
                gstop = int(self.ui.p4t6.text())  # 阻带最小损耗

                # Return the order of the lowest order digital or analog Butterworth filter that loses no more than
                # gpass dB in the passband and has at least gstop dB attenuation in the stopband.

                """  N, Wn = signal.buttord([20, 50], [14, 60], 3, 40, True)"""
                N, Wn = signal.buttord([2 * np.pi * wp_down, 2 * np.pi * wp_up],
                                       [2 * np.pi * ws_down, 2 * np.pi * ws_up],
                                       gpass, gstop, analog=True)

                b, a = signal.butter(N, Wn, btype=self.type, analog=True)

                w, h = signal.freqs(b, a)
                self.response.setData(w / (2 * np.pi), 20 * np.log10(abs(h)))
                # print('这里被执行了')

            if self.type == 'lowpass' or self.type == 'highpass':
                wp_up = int(self.ui.p4t1.text())
                ws_down = int(self.ui.p4t4.text())
                gpass = int(self.ui.p4t5.text())
                gstop = int(self.ui.p4t6.text())

                N, Wn = signal.buttord(2 * np.pi * wp_up, 2 * np.pi * ws_down, gpass, gstop, analog=True)
                b, a = signal.butter(N, Wn, btype=self.type, analog=True)
                w, h = signal.freqs(b, a)
                self.response.setData(w / (2 * np.pi), 20 * np.log10(abs(h)))

        if self.ui.c_box2.currentText() == '切比雪夫-I':
            if self.type == 'bandpass' or self.type == 'bandstop':
                wp_up = int(self.ui.p4t1.text())
                wp_down = int(self.ui.p4t2.text())
                ws_up = int(self.ui.p4t3.text())
                ws_down = int(self.ui.p4t4.text())
                gpass = int(self.ui.p4t5.text())
                gstop = int(self.ui.p4t6.text())
                rp = int(self.ui.p4t7.text())

                N, Wn = signal.cheb1ord([2 * np.pi * wp_down, 2 * np.pi * wp_up],
                                        [2 * np.pi * ws_down, 2 * np.pi * ws_up], gpass, gstop, analog=True)
                b, a = signal.cheby1(N, rp, Wn, btype=self.type, analog=True)
                w, h = signal.freqs(b, a)
                self.response.setData(w / (2 * np.pi), 20 * np.log10(abs(h)))
            if self.type == 'lowpass' or self.type == 'highpass':
                wp_up = int(self.ui.p4t1.text())
                ws_down = int(self.ui.p4t4.text())
                gpass = int(self.ui.p4t5.text())
                gstop = int(self.ui.p4t6.text())
                rp = int(self.ui.p4t7.text())

                N, Wn = signal.cheb1ord(2 * np.pi * wp_up, 2 * np.pi * ws_down, gpass, gstop, analog=True)
                b, a = signal.cheby1(N, rp, Wn, btype=self.type, analog=True)
                w, h = signal.freqs(b, a)
                self.response.setData(w / (2 * np.pi), 20 * np.log10(abs(h)))

        if self.ui.c_box.currentText() == '切比雪夫-II':
            if self.type == 'bandpass' or self.type == 'bandstop':
                wp_up = int(self.ui.p4t1.text())
                wp_down = int(self.ui.p4t2.text())
                ws_up = int(self.ui.p4t3.text())
                ws_down = int(self.ui.p4t4.text())
                gpass = int(self.ui.p4t5.text())
                gstop = int(self.ui.p4t6.text())
                rs = int(self.ui.p4t8.text())

                N, Wn = signal.cheb2ord([2 * np.pi * wp_down, 2 * np.pi * wp_up],
                                        [2 * np.pi * ws_down, 2 * np.pi * ws_up], gpass, gstop, analog=True)
                b, a = signal.cheby2(N, rs, Wn, btype=self.type, analog=True)
                w, h = signal.freqs(b, a)
                self.response.setData(w / (2 * np.pi), 20 * np.log10(abs(h)))
            if self.type == 'lowpass' or self.type == 'highpass':
                wp_up = int(self.ui.p4t1.text())
                ws_down = int(self.ui.p4t4.text())
                gpass = int(self.ui.p4t5.text())
                gstop = int(self.ui.p4t6.text())
                rs = int(self.ui.p4t8.text())

                N, Wn = signal.cheb2ord(2 * np.pi * wp_up, 2 * np.pi * ws_down, gpass, gstop, analog=True)
                b, a = signal.cheby2(N, rs, Wn, btype=self.type, analog=True)
                w, h = signal.freqs(b, a)
                self.response.setData(w / (2 * np.pi), 20 * np.log10(abs(h)))

        if self.ui.c_box2.currentText() == '椭圆':
            if self.type == 'bandpass' or self.type == 'bandstop':
                wp_up = int(self.ui.p4t1.text())
                wp_down = int(self.ui.p4t2.text())
                ws_up = int(self.ui.p4t3.text())
                ws_down = int(self.ui.p4t4.text())
                gpass = int(self.ui.p4t5.text())
                gstop = int(self.ui.p4t6.text())
                rs = int(self.ui.p4t8.text())
                rp = int(self.ui.p4t7.text())

                N, Wn = signal.ellipord([2 * np.pi * wp_down, 2 * np.pi * wp_up],
                                        [2 * np.pi * ws_down, 2 * np.pi * ws_up], gpass, gstop, analog=True)
                b, a = signal.ellip(N, rp, rs, Wn, btype=self.type, analog=True)
                w, h = signal.freqs(b, a)
                self.response.setData(w / (2 * np.pi), 20 * np.log10(abs(h)))
            if self.type == 'lowpass' or self.type == 'highpass':
                wp_up = int(self.ui.p4t1.text())
                ws_down = int(self.ui.p4t4.text())
                gpass = int(self.ui.p4t5.text())
                gstop = int(self.ui.p4t6.text())
                rs = int(self.ui.p4t8.text())
                rp = int(self.ui.p4t7.text())



                N, Wn = signal.ellipord(2 * np.pi * wp_up, 2 * np.pi * ws_down, gpass, gstop, analog=True)

                b, a = signal.ellip(N, rp, rs, Wn, btype=self.type, analog=True)
                w, h = signal.freqs(b, a)
                self.response.setData(w / (2 * np.pi), 20 * np.log10(abs(h)))

        self.order = N
        self.cutoffFrequence = Wn

    # 第五页
    def handleCalc51(self):
        self.ui.p5t1.setText(details.select_a_file(self))

    def handleCalc52(self):
        global sig
        global sos
        global t
        global number

        self.sorce_channel1 = []
        self.sorce_channel2 = []
        self.sorce_channel3 = []
        self.sorce_channel4 = []
        source_channels = [self.sorce_channel1, self.sorce_channel2, self.sorce_channel3, self.sorce_channel4]

        waveletBaseFunction = self.ui.p4t9.text()  # 小波基函数
        waveletThresholdValue = float(self.ui.p4t10.text())  # 阈值
        waveletThresholdMode = self.ui.c_box3.currentText()  # 阈值模式

        print("类型：", type(waveletThresholdMode), "模式：", waveletThresholdMode)
        self.ui.p5t3.setText('计算中！')

        try:
            with open(str(self.ui.p5t1.text()), 'r') as file:
                data = file.read()
            sig = data

        except FileNotFoundError:
            print('文件读取失败！')
        print("数据类型为：", type(sig))

        # 读出4个通道的数据
        for channel in source_channels:
            b1, b2 = sig.split('0d0a', 1)
            b1 = b1[1:-1]
            cout = b1.count(',', 0, len(b1))
            for i in range(cout):
                c1, c2 = b1.split(',', 1)
                channel.append(float(c1))
                b1 = c2
                if i + 1 == cout:
                    channel.append(float(c2))

            sig = b2
            if b2.count('0d0a', 0, len(b2)) == 0:  # 最后一个通道数据
                b2 = b2[1:-1]
                cout = b2.count(',', 0, len(b2))
                for i in range(cout):
                    c1, c2 = b2.split(',', 1)
                    self.sorce_channel4.append(float(c1))
                    b2 = c2
                    if i + 1 == cout:
                        self.sorce_channel4.append(float(c2))
                break

        if self.ui.c_box2.currentText() == '巴特沃夫':
            sos = signal.butter(self.order, self.cutoffFrequence / (2 * np.pi), btype=self.type, analog=False,
                                output='sos', fs=500)
        elif self.ui.c_box2.currentText() == '切比雪夫-I':
            sos = signal.cheby1(self.order, int(self.ui.p4t7.text()), self.cutoffFrequence / (2 * np.pi),
                                btype=self.type, analog=False, output='sos',
                                fs=500)
        elif self.ui.c_box2.currentText() == '切比雪夫-II':
            sos = signal.cheby2(self.order, int(self.ui.p4t8.text()), self.cutoffFrequence / (2 * np.pi),
                                btype=self.type, analog=False, output='sos',
                                fs=500)
        elif self.ui.c_box2.currentText() == '椭圆':
            sos = signal.ellip(self.order, int(self.ui.p4t7.text()), int(self.ui.p4t8.text()),
                               self.cutoffFrequence / (2 * np.pi), btype=self.type, analog=False, output='sos',
                               fs=500)

        data_length = len(self.sorce_channel1)  # 每通道数据长度
        self.label_t = np.linspace(0, data_length / 500, data_length)  # 时间轴坐标

        x = np.arange(data_length)
        label_x = x[range(int(data_length))] / (data_length / 500)

        # 源数据快速傅里叶变换
        self.sorce_channel1_fft = self.fftChannel(self.sorce_channel1, data_length)
        self.sorce_channel2_fft = self.fftChannel(self.sorce_channel2, data_length)
        self.sorce_channel3_fft = self.fftChannel(self.sorce_channel3, data_length)
        self.sorce_channel4_fft = self.fftChannel(self.sorce_channel4, data_length)

        # 滤波
        self.filter_data1 = signal.sosfilt(sos, self.sorce_channel1)
        self.filter_data2 = signal.sosfilt(sos, self.sorce_channel2)
        self.filter_data3 = signal.sosfilt(sos, self.sorce_channel3)
        self.filter_data4 = signal.sosfilt(sos, self.sorce_channel4)

        # 小波去噪
        self.waveletDenoisingCh1 = self.waveletDenoising(self.filter_data1, waveletBaseFunction, waveletThresholdValue,
                                                         waveletThresholdMode)
        self.waveletDenoisingCh2 = self.waveletDenoising(self.filter_data2, waveletBaseFunction, waveletThresholdValue,
                                                         waveletThresholdMode)
        self.waveletDenoisingCh3 = self.waveletDenoising(self.filter_data3, waveletBaseFunction, waveletThresholdValue,
                                                         waveletThresholdMode)
        self.waveletDenoisingCh4 = self.waveletDenoising(self.filter_data4, waveletBaseFunction, waveletThresholdValue,
                                                         waveletThresholdMode)

        # 归一化横坐标
        self.normalization_x = label_x[range(int(data_length / 2))]

        # 滤波、去噪后数据的FFT
        self.fftCh1 = self.fftChannel(self.waveletDenoisingCh1, data_length)
        self.fftCh2 = self.fftChannel(self.waveletDenoisingCh2, data_length)
        self.fftCh3 = self.fftChannel(self.waveletDenoisingCh3, data_length)
        self.fftCh4 = self.fftChannel(self.waveletDenoisingCh4, data_length)

        self.ui.p5t3_2.setText('计算完成！')
        self.ui.p5t3.setText('计算结束，请点击通道显示波形')

    # 小波去噪
    def waveletDenoising(self, data, function, threshold, mode):
        wave = pywt.Wavelet(function)
        maxlev = pywt.dwt_max_level(len(data), wave.dec_len)
        coeffs = pywt.wavedec(data, function, level=maxlev)
        for i in range(1, len(coeffs)):
            coeffs[i] = pywt.threshold(data=coeffs[i], value=threshold * max(coeffs[i]), mode=mode, substitute=0)
        waverec = pywt.waverec(coeffs, function)
        return waverec

    # 快速傅里叶变换
    def fftChannel(self, data, dataLength):
        fftData = fft(data)
        ampNormalization = np.abs(fftData) / dataLength
        return ampNormalization[range(int(dataLength / 2))]

    def handleCalc53(self):
        self.ui.p5t2.setText(details.select_a_file(self))

    def handleCalc54(self):
        try:
            if self.ui.checkBox.checkState() == 2:  # 通道1
                details.data_storage(str(self.ui.p5t2.text()), self.filter_data1)
            elif self.ui.checkBox_2.checkState() == 2:  # 通道3
                details.data_storage(str(self.ui.p5t2.text()), self.filter_data2)
            elif self.ui.checkBox_3.checkState() == 2:  # 通道3
                details.data_storage(str(self.ui.p5t2.text()), self.filter_data3)
            elif self.ui.checkBox_4.checkState() == 2:  # 通道3
                details.data_storage(str(self.ui.p5t2.text()), self.filter_data4)
            print("滤波数据存储已完成！")
        except:
            print("数据存储出错！")
        pass

    def data_plot(self, cb):
        if cb == 'CH1':
            if self.ui.checkBox.checkState() == 2:  # 画通道1的数据图
                # 通道1的四个图
                print('通道1画图')
                self.channelMark.append(0)
                self.dataPlot(self.waveletDenoisingCh1, self.fftCh1, self.filter_curve1, self.fft_curve1)
                self.dataPlot(self.sorce_channel1, self.sorce_channel1_fft, self.source_curve1, self.wp_curve1)
            else:  # 清除通道1的数据图
                self.channelMark.remove(0)
                self.source_curve1.clear()
                self.fft_curve1.clear()
                self.wp_curve1.clear()
                self.filter_curve1.clear()
        elif cb == "CH2":
            if self.ui.checkBox_2.checkState() == 2:  # 画通道2的数据图
                # 通道2的四个图
                print('通道2画图')
                self.channelMark.append(1)
                self.dataPlot(self.waveletDenoisingCh2, self.fftCh2, self.filter_curve2, self.fft_curve2)
                self.dataPlot(self.sorce_channel2, self.sorce_channel2_fft, self.source_curve2, self.wp_curve2)
            else:  # 清除通道2的数据图
                self.channelMark.remove(1)
                self.source_curve2.clear()
                self.fft_curve2.clear()
                self.wp_curve2.clear()
                self.filter_curve2.clear()
        elif cb == "CH3":
            if self.ui.checkBox_3.checkState() == 2:  # 画通道3的数据图
                # 通道3的四个图
                print('通道3画图')
                self.channelMark.append(2)
                self.dataPlot(self.waveletDenoisingCh3, self.fftCh3, self.filter_curve3, self.fft_curve3)
                self.dataPlot(self.sorce_channel3, self.sorce_channel3_fft, self.source_curve3, self.wp_curve3)
            else:  # 清除通道3的数据图
                self.channelMark.remove(2)
                self.source_curve3.clear()
                self.fft_curve3.clear()
                self.wp_curve3.clear()
                self.filter_curve3.clear()
        elif cb == "CH4":
            if self.ui.checkBox_4.checkState() == 2:  # 画通道4的数据图
                # 通道4的四个图
                print('通道4画图')
                self.channelMark.append(3)
                self.dataPlot(self.waveletDenoisingCh4, self.fftCh4, self.filter_curve4, self.fft_curve4)
                self.dataPlot(self.sorce_channel4, self.sorce_channel4_fft, self.source_curve4, self.wp_curve4)
            else:  # 清除通道4的数据图
                self.channelMark.remove(3)
                self.source_curve4.clear()
                self.fft_curve4.clear()
                self.wp_curve4.clear()
                self.filter_curve4.clear()

    def dataPlot(self, source_data, fft_data, source_curve, fft_curve):
        sd = [(1000 / 1.1) * i for i in source_data]
        fd = [i / (max(fft_data)) for i in fft_data]
        source_curve.setData(self.label_t, sd)
        fft_curve.setData(self.normalization_x, fd)

    def ch1Emit(self):
        # if self.ui.checkBox.checkState() ==2:
        self.ms.signal7.emit("CH1")

    def ch2Emit(self):
        # if self.ui.checkBox_2.checkState() == 2:
        self.ms.signal8.emit("CH2")

    def ch3Emit(self):
        # if self.ui.checkBox_3.checkState() == 2:
        self.ms.signal9.emit("CH3")

    def ch4Emit(self):
        # if self.ui.checkBox_4.checkState() == 2:
        self.ms.signal10.emit("CH4")


class Window(QWidget):

    def __init__(self):
        super(Window, self).__init__()

        loader = QUiLoader()
        self.ui = loader.load('window.ui')
        self.ui.B1.clicked.connect(self.onLogin)
        self.ui.B2.clicked.connect(self.check)

    def onLogin(self):
        global main_win
        # 实例化另外一个窗口
        main_win = My_software()
        # 显示新窗口
        main_win.ui.show()
        # 关闭自己
        self.ui.close()

    def check(self):
        global register
        # 实例化另外一个窗口
        register = Register()
        # 显示新窗口
        register.ui.show()
        # 关闭自己
        self.ui.close()

class Register(QWidget):

    def __init__(self):
        super(Register, self).__init__()

        loader = QUiLoader()
        self.ui = loader.load('login.ui')
        self.ui.B1.clicked.connect(self.finish)


    def finish(self):
        global win
        # 实例化另外一个窗口
        win = Window()
        # 显示新窗口
        win.ui.show()
        # 关闭自己
        self.ui.close()



"""app = QApplication([])
my_software = My_software()
my_software.ui.show()
app.exec_()"""

app = QApplication([])
window = Window()
window.ui.show()
app.exec_()