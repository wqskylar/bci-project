# bci-project
## 项目描述
一个基于Qt开发可视化界面，Python实现逻辑功能的程序。是脑电采集分析设备的配套软件。软件可以检测软硬件设备的通信状态，采集阻抗数据，采集脑电信号数据。设计数字滤波器并滤波。去噪，变换频谱图。

## 项目要点
1. **使用Python的QtDesigner配合Qt相关库pyside2编写好应用的可视化界面框架。并做好事件绑定。** 整个应用继承一个QWidget，图表统一使用pyqtgraph。预先准备好QButton，Combox等控件的绑定事件，并准备好触发的信号和槽。
2. **连接串口，并检测通信状态。** 使用Serial模块，根据设定好的串口号，波特率，比特数，是否校验等参数初始化串口。上位机发送信息等待回应，确保通信状态良好。之后及时检测阻抗数据。检测过程继承QThread,利用多线程防止界面卡顿。
3. **确保串口通信状态良好，预先设定采集方式和数量，并采集多组脑电数据以供后续分析。**
4. **设计数字滤波器。** 支持巴特沃夫，切比雪夫Ⅰ，Ⅱ型滤波器，椭圆滤波。允许选择高通，低通，带通，带阻等多种滤波方式，可以设定通带最大衰减，阻带最小衰减，通带最大波纹和阻带最大波纹这四个参数。之后会使用使用scipy的singal模块完成数字滤波器的阶数，参数多项式的设计，并提供幅频响应曲线。
5. **根据设计好的数字滤波器完成数字滤波。** 首先程序会根据之前选定的滤波器类型，滤波器阶数：self.order 和滤波器极限频率：self.cutoffFrequence 得到滤波器的 second-order 部分：sos。使用函数scipy.signal.sosfilt(sos, x, axis=- 1, zi=None)完成数字滤波。
6. **使用pywt模块完成小波去噪。** 首先根据传入的参数名称读取对应的小波基函数，之后求最大分解级别，然后进行循环处理。再对源数据进行分段处理。之后输出小波去噪的数据。
7. **实现FFT算法，完成变换频谱图功能。** 使用 scipy 模块的 fftpack 子模块对滤波前后的数据进行 FFT（快速傅里叶变换）得到源数据和滤波后数据的频谱图。之后使用 numpy 模块将数据处理成可以使用的格式。

## 项目展示
### 阻抗检测页面，可以检测串口的通信状况，并采集硬件设备和开发板的阻抗数据。
![image](https://user-images.githubusercontent.com/115355943/210690522-34757375-26d5-44fc-b65e-d0e5207bdba3.png)
### 采集储存页面，可以采集脑电数据（脑电数据是头皮某一个位置的电位和基极的电位差，因此一组脑电数据是一组离散点数据）,一次可以采集四组数据，支持定时采集和定量采集。
![image](https://user-images.githubusercontent.com/115355943/210691753-bbbf2747-4146-47b5-926e-338813c2dade.png)
采集脑电数据展示
![image](https://user-images.githubusercontent.com/115355943/210756434-a0feb406-3abc-428e-b2b2-354f723ab9e5.png)
采集到的离散脑电数据文件
![image](https://user-images.githubusercontent.com/115355943/210756722-63023cb2-fc6c-4d6b-9f1e-eed51e17ea2f.png)
### 数字滤波器设计
- 巴特沃夫低通  
![image](https://user-images.githubusercontent.com/115355943/210756897-a7912ddc-cf8b-420a-8ee0-2f1fa2d0c136.png)
- 切比雪夫Ⅰ高通   
![image](https://user-images.githubusercontent.com/115355943/210757933-893a33d3-19b8-4239-858b-9756bcb5667f.png)
### 选定小波基函数，完成滤波，降噪，变换频谱图
在下图的左上角图像是源数据波形。左下角的图象是滤波后波形。右上角图像是源数据的频谱图，右下角是滤波后数据的频谱图。
![image](https://user-images.githubusercontent.com/115355943/210757251-5e826146-fd07-4efa-8073-84863a7ff4da.png)
