# encoding=utf-8
import datetime
import os.path
import os
import socket
import socketserver
import threading
import serial
import asyncio
import sqlite3
# import winreg
import uuid

import pickle
import sys
import copy

class CONSTVALUES():
    """单线单向 （虎石台， 上海）"""
    LINE_MODE_1L1D = 1
    """单线双向 （可门）"""
    LINE_MODE_1L2D = 2
    """双线单向 （杨柳青）"""
    LINE_MODE_2L1D = 3
    """双线双向 （暂无）"""
    LINE_MODE_2L2D = 4

    """正向"""
    LINE_FORWARD = 10
    """反向"""
    LINE_BACKWARD = 11

    """文件模式"""
    PIC_MODE_FILE = 20
    """SOCKET模式"""
    PIC_MODE_SOCKET = 21

    """无循环"""
    LOOP_MODE_NO = 30
    """有循环"""
    LOOP_MODE_YES = 31

    DEST_GQPICS_ROOT = os.path.join('e:\\', 'gqpics')
    DEST_ZXGQPICS_ROOT = os.path.join('e:\\', 'ZXGQPics')

    PRIORITY_SOCKET = 41
    PRIORITY_PIC = 42

    INDEX_MODE_NORMAL = 51
    INDEX_MODE_MISS = 52

    DATA_TYPE_CASE = 61
    DATA_TYPE_TRAIN = 62
    DATA_TYPE_CARRIAGE = 63

    _s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    _s.connect(('8.8.8.8', 0))
    LOCAL_IP = _s.getsockname()[0]
    _s.close()

class UTIL():
    @staticmethod
    def _get_pic_info(file_name):
        import PIL.Image
        img = PIL.Image.open(file_name)
        return img.size[0], img.size[1], os.path.getsize(file_name)


    @staticmethod
    def getTime(_time=None, _type='socket'):
        """
        获取特定格式的日期时间字符串
        """
        t = None
        if _time is None:
            t = datetime.datetime.now()
        elif isinstance(_time, datetime.datetime):
            t = _time
        else:
            return None

        if _type == 'socket':
            return t.strftime("%Y-%m-%d %H:%M:%S")
        elif _type == 'file':
            return t.strftime("%Y%m%d%H%M%S")
        else:
            return None

    @staticmethod
    def getSpeed(_l, _s=0, _t=0):
        _r = 0
        t = float(_t)
        l = float(_l)
        s = float(_s)
        if _s == 0:
            _r = l * 0.001 / t * 0.00028
        elif _t == 0:
            S = s * 1000 / 3600
            _r = l / S
        return _r

    @staticmethod
    def getCode(_kind, _index):
        if _kind[0] == 'J' and _index == 0:
            _no = '0001'
            _code = '%s%s00AH00000000' % (
                ('%4s' % (_kind[::-1],))[::-1],
                ('%4s' % (_no[::-1],))[::-1]
            )
        elif _kind[0] == 'K':
            _no = str(1000000 + _index)
            _code = '%s%s0000000' % (
                ('%6s' % (_kind[::-1],))[::-1],
                ('%7s' % (_no[::-1],))[::-1]
            )
        else:
            _no = str(2000000 + _index)
            _code = 'T%s%s000000' % (
                ('%6s' % (_kind[::-1],))[::-1],
                ('%7s' % (_no[::-1],))[::-1]
            )
        return _code

class Scenario():
    def __init__(
            self,
            _name=None,
            _sx_datas=None,
            _xx_datas=None,
            _sx_direction='forward',
            _xx_direction='forward'
    ):
        self.name = _name
        self.sx = _sx_datas
        self.xx = _xx_datas
        self.sx_direction = _sx_direction
        self.xx_direction = _xx_direction

    def setLineInfo(self, _line, _info):
        if _line == 'sx':
            self.sx_info = _info
        else:
            self.xx_info = _info

    def setTrains(self, _line, _trains):
        if _line == 'sx':
            self.sx = _trains
        else:
            self.xx = _trains

    def setName(self, _name):
        self.name = _name

    def setDelay(self, _line, _delay):
        if _line == 'sx':
            self.sx_delay = _delay
        if _line == 'xx':
            self.xx_delay = _delay

    def setDirection(self, _line, _direction):
        if _line == 'sx':
            self.sx_direction = _direction
        if _line == 'xx':
            self.xx_direction = _direction

class Carriage():
    def __init__(
            self,
            _id=uuid.uuid1(),
            _kind_name=None,
            _l_pic=None,
            _r_pic=None,
            _l_z_pic=None,
            _r_z_pic=None,
            _length=15,
            _socket_priority=True):
        self.kind = _kind_name
        self.no = None
        self.length = _length
        self.speed = 60
        self._index = 0
        self.Priority = _socket_priority
        self.L_src = _l_pic
        self.R_src = _r_pic
        self.ZL_src = _l_z_pic
        self.ZR_src = _r_z_pic
        self.L_width = 0
        self.R_width = 0
        self.ZL_width = 0
        self.ZR_width = 0
        self.code = None
        self.id = _id
        self.warningCount = 0
        self.L_warning = None
        self.R_warning = None
        self.ZR_warning = None
        self.ZL_warning = None

        self.getWidth()
        self.store()

    def save(self):
        pass

    def store(self):
        if os.path.exists(self.L_src):
            self.L_src = self._getData(self.L_src)
        if os.path.exists(self.R_src):
            self.R_src = self._getData(self.R_src)
        if os.path.exists(self.ZL_src):
            self.ZL_src = self._getData(self.ZL_src)
        if os.path.exists(self.ZR_src):
            self.ZR_src = self._getData(self.ZR_src)

    def _getData(self, _filepath):
        bList = list()
        with open(_filepath, 'rb') as f:
            while 1:
                fd = f.read(1024)
                if not fd:
                    break
                bList.append(fd)
        return bList

    def getWarningInfo(self):
        pass

    def getWidth(self):
        self.L_width, self.R_width, self.ZL_width, self.ZR_width = [UTIL._get_pic_info(img)[0] for img in [self.L_src, self.R_src, self.ZL_src, self.ZR_src]]

    def setCode(self, _code):
        self.code = _code

    def setSpeed(self, _speed):
        self.speed = _speed

    def setPriority(self, _priority):
        self.Priority = _priority

#废弃
class Train():
    def __init__(self, _name, _car, _indexMode=CONSTVALUES.INDEX_MODE_NORMAL):
        self.car = _car
        self.name = _name
        self.indexMode = _indexMode
        # self.startDelay = _startDelay
        self.SERIAL = None
        self.INDEX = None
        self.time = datetime.datetime.now()
        # self.data_init()
        self.get_index()

    def data_init(self):
        for i in range(len(self.car)):
            self.car[i].setIndex(i)
            self.car[i].generateCode()

    def updateTime(self):
        self.time = datetime.datetime.now()

    def get_index(self):
        #   生成index文件内容
        index = ['0\n', ]
        for i in range(len(self.car)):
            index.append("%s\t%s\t%s\t%s\n" % (
                str(i + 1),
                str(int(float(self.car[i].speed) * 10)),
                self.car[i].L_width,
                self.car[i].code
            ))
        self.INDEX = index

    def get_serial(self, index):
        #   生成串口数据
        _serial = []
        _serial.append('D' + str(int(float(self.car[index].speed) * 10)))
        if index == 0:
            _serial.append('J')
            _serial.append('N' + self.car[index].code)
        else:
            _serial.append('N' + self.car[index].code)
        _serial.append('C' + str(index + 1).zfill(3))
        return _serial

    def setName(self, _name):
        self.name = _name

    # def setStartDelay(self, _delay):
    #     self.startDelay = _delay

    def setIndexMode(self, _mode):
        self.indexMode = _mode



#废弃
# class UI(QtWidgets.QMainWindow):
#     def setupUi(self, MainWindow):
#         MainWindow.setObjectName("MainWindow")
#         MainWindow.resize(609, 543)
#         MainWindow.setMinimumSize(QtCore.QSize(609, 543))
#         MainWindow.setMaximumSize(QtCore.QSize(609, 543))
#         self.centralwidget = QtWidgets.QWidget(MainWindow)
#         self.centralwidget.setObjectName("centralwidget")
#         self.tab_all = QtWidgets.QTabWidget(self.centralwidget)
#         self.tab_all.setGeometry(QtCore.QRect(10, 10, 591, 511))
#         self.tab_all.setObjectName("tab_all")
#         self.tab_monitor = QtWidgets.QWidget()
#         self.tab_monitor.setObjectName("tab_monitor")
#         # self.openGLWidget = QtWidgets.QOpenGLWidget(self.tab_monitor)
#         # self.openGLWidget.setGeometry(QtCore.QRect(10, 10, 561, 281))
#         # self.openGLWidget.setObjectName("openGLWidget")
#         # self.progressBar = QtWidgets.QProgressBar(self.tab_monitor)
#         # self.progressBar.setGeometry(QtCore.QRect(10, 460, 561, 23))
#         # self.progressBar.setProperty("value", 24)
#         # self.progressBar.setObjectName("progressBar")
#         self.listView_3 = QtWidgets.QListWidget(self.tab_monitor)
#         self.listView_3.setGeometry(QtCore.QRect(10, 10, 561, 455))
#         # self.listView_3.setGeometry(QtCore.QRect(10, 300, 561, 151))
#         self.listView_3.setObjectName("listView_3")
#         self.tab_all.addTab(self.tab_monitor, "")
#         self.tab_do = QtWidgets.QWidget()
#         self.tab_do.setObjectName("tab_do")
#         self.cb_line_mode = QtWidgets.QComboBox(self.tab_do)
#         self.cb_line_mode.setGeometry(QtCore.QRect(120, 10, 191, 22))
#         self.cb_line_mode.setObjectName("cb_line_mode")
#         self.cb_line_mode.addItem("")
#         self.cb_line_mode.addItem("")
#         self.cb_line_mode.addItem("")
#         self.label = QtWidgets.QLabel(self.tab_do)
#         self.label.setGeometry(QtCore.QRect(50, 11, 61, 20))
#         self.label.setObjectName("label")
#         self.cb_loop_mode = QtWidgets.QComboBox(self.tab_do)
#         self.cb_loop_mode.setGeometry(QtCore.QRect(120, 40, 191, 22))
#         self.cb_loop_mode.setObjectName("cb_loop_mode")
#         self.cb_loop_mode.addItem("")
#         self.cb_loop_mode.addItem("")
#         self.label_2 = QtWidgets.QLabel(self.tab_do)
#         self.label_2.setGeometry(QtCore.QRect(50, 43, 61, 16))
#         self.label_2.setObjectName("label_2")
#         self.cb_pic_mode = QtWidgets.QComboBox(self.tab_do)
#         self.cb_pic_mode.setGeometry(QtCore.QRect(120, 70, 191, 22))
#         self.cb_pic_mode.setObjectName("cb_pic_mode")
#         self.cb_pic_mode.addItem("")
#         self.cb_pic_mode.addItem("")
#         self.label_3 = QtWidgets.QLabel(self.tab_do)
#         self.label_3.setGeometry(QtCore.QRect(50, 73, 61, 16))
#         self.label_3.setObjectName("label_3")
#         self.lst_case = QtWidgets.QListWidget(self.tab_do)
#         self.lst_case.setGeometry(QtCore.QRect(120, 100, 431, 341))
#         self.lst_case.setObjectName("lst_case")
#         self.label_11 = QtWidgets.QLabel(self.tab_do)
#         self.label_11.setGeometry(QtCore.QRect(50, 100, 61, 16))
#         self.label_11.setObjectName("label_11")
#         self.verticalScrollBar = QtWidgets.QScrollBar(self.tab_do)
#         self.verticalScrollBar.setGeometry(QtCore.QRect(551, 100, 16, 341))
#         self.verticalScrollBar.setOrientation(QtCore.Qt.Vertical)
#         self.verticalScrollBar.setObjectName("verticalScrollBar")
#         self.horizontalLayoutWidget_2 = QtWidgets.QWidget(self.tab_do)
#         self.horizontalLayoutWidget_2.setGeometry(QtCore.QRect(0, 450, 581, 31))
#         self.horizontalLayoutWidget_2.setObjectName("horizontalLayoutWidget_2")
#         self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_2)
#         self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
#         self.horizontalLayout_2.setObjectName("horizontalLayout_2")
#         self.btn_start_case = QtWidgets.QPushButton(self.horizontalLayoutWidget_2)
#         self.btn_start_case.setObjectName("btn_start_case")
#         self.btn_start_case.clicked.connect(self.go)
#         self.horizontalLayout_2.addWidget(self.btn_start_case)
#         self.tab_all.addTab(self.tab_do, "")
#         self.tab_new_case = QtWidgets.QWidget()
#         self.tab_new_case.setObjectName("tab_new_case")
#         self.horizontalLayoutWidget_3 = QtWidgets.QWidget(self.tab_new_case)
#         self.horizontalLayoutWidget_3.setGeometry(QtCore.QRect(10, 60, 571, 291))
#         self.horizontalLayoutWidget_3.setObjectName("horizontalLayoutWidget_3")
#         self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_3)
#         self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
#         self.horizontalLayout_3.setObjectName("horizontalLayout_3")
#         self.tr_new_case_sx = QtWidgets.QTreeWidget(self.horizontalLayoutWidget_3)
#         self.tr_new_case_sx.setObjectName("tr_new_case_sx")
#         self.tr_new_case_sx.setHeaderLabels([u'列车', u'总长（节）'])
#         self.horizontalLayout_3.addWidget(self.tr_new_case_sx)
#         self.vsb_new_case_sx = QtWidgets.QScrollBar(self.horizontalLayoutWidget_3)
#         self.vsb_new_case_sx.setOrientation(QtCore.Qt.Vertical)
#         self.vsb_new_case_sx.setObjectName("vsb_new_case_sx")
#         self.horizontalLayout_3.addWidget(self.vsb_new_case_sx)
#         self.tr_new_case_xx = QtWidgets.QTreeWidget(self.horizontalLayoutWidget_3)
#         self.tr_new_case_xx.setObjectName("tr_new_case_xx")
#         self.tr_new_case_xx.setHeaderLabels([u'列车', u'总长（节）'])
#         self.horizontalLayout_3.addWidget(self.tr_new_case_xx)
#         self.vsb_new_case_xx = QtWidgets.QScrollBar(self.horizontalLayoutWidget_3)
#         self.vsb_new_case_xx.setOrientation(QtCore.Qt.Vertical)
#         self.vsb_new_case_xx.setObjectName("vsb_new_case_xx")
#         self.horizontalLayout_3.addWidget(self.vsb_new_case_xx)
#         self.cb_new_line_mode = QtWidgets.QComboBox(self.tab_new_case)
#         self.cb_new_line_mode.setGeometry(QtCore.QRect(80, 9, 211, 22))
#         self.cb_new_line_mode.setObjectName("cb_new_line_mode")
#         self.cb_new_line_mode.addItem("")
#         self.cb_new_line_mode.addItem("")
#         self.cb_new_line_mode.addItem("")
#         self.label_12 = QtWidgets.QLabel(self.tab_new_case)
#         self.label_12.setGeometry(QtCore.QRect(10, 10, 61, 20))
#         self.label_12.setObjectName("label_12")
#         self.label_13 = QtWidgets.QLabel(self.tab_new_case)
#         self.label_13.setGeometry(QtCore.QRect(124, 36, 31, 20))
#         self.label_13.setObjectName("label_13")
#         self.label_14 = QtWidgets.QLabel(self.tab_new_case)
#         self.label_14.setGeometry(QtCore.QRect(414, 36, 31, 20))
#         self.label_14.setObjectName("label_14")
#         self.tb_case_name = QtWidgets.QLineEdit(self.tab_new_case)
#         self.tb_case_name.setGeometry(QtCore.QRect(370, 10, 211, 20))
#         self.tb_case_name.setObjectName("tb_case_name")
#         self.label_15 = QtWidgets.QLabel(self.tab_new_case)
#         self.label_15.setGeometry(QtCore.QRect(300, 11, 61, 16))
#         self.label_15.setScaledContents(False)
#         self.label_15.setWordWrap(False)
#         self.label_15.setObjectName("label_15")
#         self.horizontalLayoutWidget_4 = QtWidgets.QWidget(self.tab_new_case)
#         self.horizontalLayoutWidget_4.setGeometry(QtCore.QRect(0, 450, 581, 31))
#         self.horizontalLayoutWidget_4.setObjectName("horizontalLayoutWidget_4")
#         self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_4)
#         self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
#         self.horizontalLayout_4.setObjectName("horizontalLayout_4")
#         self.btn_new_case = QtWidgets.QPushButton(self.horizontalLayoutWidget_4)
#         self.btn_new_case.setObjectName("btn_new_case")
#         self.horizontalLayout_4.addWidget(self.btn_new_case)
#         self.label_19 = QtWidgets.QLabel(self.tab_new_case)
#         self.label_19.setGeometry(QtCore.QRect(10, 390, 61, 16))
#         self.label_19.setScaledContents(False)
#         self.label_19.setWordWrap(False)
#         self.label_19.setObjectName("label_19")
#         self.tb_new_case_sx_delay = QtWidgets.QLineEdit(self.tab_new_case)
#         self.tb_new_case_sx_delay.setGeometry(QtCore.QRect(80, 389, 191, 20))
#         self.tb_new_case_sx_delay.setObjectName("tb_new_case_sx_delay")
#         self.label_20 = QtWidgets.QLabel(self.tab_new_case)
#         self.label_20.setGeometry(QtCore.QRect(10, 420, 61, 20))
#         self.label_20.setObjectName("label_20")
#         self.cb_new_case_sx_index = QtWidgets.QComboBox(self.tab_new_case)
#         self.cb_new_case_sx_index.setGeometry(QtCore.QRect(80, 419, 211, 22))
#         self.cb_new_case_sx_index.setObjectName("cb_new_case_sx_index")
#         self.cb_new_case_sx_index.addItem("")
#         self.cb_new_case_sx_index.addItem("")
#         self.tb_new_case_xx_delay = QtWidgets.QLineEdit(self.tab_new_case)
#         self.tb_new_case_xx_delay.setGeometry(QtCore.QRect(370, 388, 191, 20))
#         self.tb_new_case_xx_delay.setObjectName("tb_new_case_xx_delay")
#         self.label_21 = QtWidgets.QLabel(self.tab_new_case)
#         self.label_21.setGeometry(QtCore.QRect(300, 391, 61, 16))
#         self.label_21.setScaledContents(False)
#         self.label_21.setWordWrap(False)
#         self.label_21.setObjectName("label_21")
#         self.cb_new_case_xx_index = QtWidgets.QComboBox(self.tab_new_case)
#         self.cb_new_case_xx_index.setGeometry(QtCore.QRect(370, 419, 211, 22))
#         self.cb_new_case_xx_index.setObjectName("cb_new_case_xx_index")
#         self.cb_new_case_xx_index.addItem("")
#         self.cb_new_case_xx_index.addItem("")
#         self.label_22 = QtWidgets.QLabel(self.tab_new_case)
#         self.label_22.setGeometry(QtCore.QRect(300, 420, 61, 20))
#         self.label_22.setObjectName("label_22")
#         self.label_23 = QtWidgets.QLabel(self.tab_new_case)
#         self.label_23.setGeometry(QtCore.QRect(280, 391, 16, 16))
#         self.label_23.setScaledContents(False)
#         self.label_23.setWordWrap(False)
#         self.label_23.setObjectName("label_23")
#         self.label_24 = QtWidgets.QLabel(self.tab_new_case)
#         self.label_24.setGeometry(QtCore.QRect(570, 390, 16, 16))
#         self.label_24.setScaledContents(False)
#         self.label_24.setWordWrap(False)
#         self.label_24.setObjectName("label_24")
#         self.label_33 = QtWidgets.QLabel(self.tab_new_case)
#         self.label_33.setGeometry(QtCore.QRect(10, 360, 61, 20))
#         self.label_33.setObjectName("label_33")
#         self.cb_new_case_sx_direction = QtWidgets.QComboBox(self.tab_new_case)
#         self.cb_new_case_sx_direction.setGeometry(QtCore.QRect(80, 359, 211, 22))
#         self.cb_new_case_sx_direction.setObjectName("cb_new_case_sx_direction")
#         self.cb_new_case_sx_direction.addItem("")
#         self.cb_new_case_sx_direction.addItem("")
#         self.label_34 = QtWidgets.QLabel(self.tab_new_case)
#         self.label_34.setGeometry(QtCore.QRect(300, 360, 61, 20))
#         self.label_34.setObjectName("label_34")
#         self.cb_new_case_xx_direction = QtWidgets.QComboBox(self.tab_new_case)
#         self.cb_new_case_xx_direction.setGeometry(QtCore.QRect(370, 359, 211, 22))
#         self.cb_new_case_xx_direction.setObjectName("cb_new_case_xx_direction")
#         self.cb_new_case_xx_direction.addItem("")
#         self.cb_new_case_xx_direction.addItem("")
#         self.tab_all.addTab(self.tab_new_case, "")
#         self.tab_new_train = QtWidgets.QWidget()
#         self.tab_new_train.setObjectName("tab_new_train")
#         self.label_16 = QtWidgets.QLabel(self.tab_new_train)
#         self.label_16.setGeometry(QtCore.QRect(50, 11, 61, 16))
#         self.label_16.setScaledContents(False)
#         self.label_16.setWordWrap(False)
#         self.label_16.setObjectName("label_16")
#         self.tb_new_train_name = QtWidgets.QLineEdit(self.tab_new_train)
#         self.tb_new_train_name.setGeometry(QtCore.QRect(120, 10, 221, 20))
#         self.tb_new_train_name.setObjectName("tb_new_train_name")
#         # self.label_17 = QtWidgets.QLabel(self.tab_new_train)
#         # self.label_17.setGeometry(QtCore.QRect(50, 41, 61, 16))
#         # self.label_17.setScaledContents(False)
#         # self.label_17.setWordWrap(False)
#         # self.label_17.setObjectName("label_17")
#         # self.tb_new_train_speed = QtWidgets.QLineEdit(self.tab_new_train)
#         # self.tb_new_train_speed.setGeometry(QtCore.QRect(120, 40, 161, 20))
#         # self.tb_new_train_speed.setObjectName("tb_new_train_speed")
#         self.verticalScrollBar_2 = QtWidgets.QScrollBar(self.tab_new_train)
#         self.verticalScrollBar_2.setGeometry(QtCore.QRect(551, 70, 16, 361))
#         self.verticalScrollBar_2.setOrientation(QtCore.Qt.Vertical)
#         self.verticalScrollBar_2.setObjectName("verticalScrollBar_2")
#         self.label_18 = QtWidgets.QLabel(self.tab_new_train)
#         self.label_18.setGeometry(QtCore.QRect(50, 41, 61, 16))
#         self.label_18.setObjectName("label_18")
#         self.tr_new_train = QtWidgets.QTreeWidget(self.tab_new_train)
#         self.tr_new_train.setGeometry(QtCore.QRect(120, 40, 431, 361))
#         self.tr_new_train.setObjectName("tr_new_train")
#         self.tr_new_train.setHeaderLabels([u'车型', u'车长（米）', u'时速（公里/小时）', u'编码', u'SOCKET优先', u'备注'])
#         self.horizontalLayoutWidget_5 = QtWidgets.QWidget(self.tab_new_train)
#         self.horizontalLayoutWidget_5.setGeometry(QtCore.QRect(0, 450, 581, 31))
#         self.horizontalLayoutWidget_5.setObjectName("horizontalLayoutWidget_5")
#         self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_5)
#         self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
#         self.horizontalLayout_5.setObjectName("horizontalLayout_5")
#         self.btn_new_train = QtWidgets.QPushButton(self.horizontalLayoutWidget_5)
#         self.btn_new_train.setObjectName("btn_new_train")
#         self.horizontalLayout_5.addWidget(self.btn_new_train)
#         # self.label_35 = QtWidgets.QLabel(self.tab_new_train)
#         # self.label_35.setGeometry(QtCore.QRect(290, 43, 61, 16))
#         # self.label_35.setScaledContents(False)
#         # self.label_35.setWordWrap(False)
#         # self.label_35.setObjectName("label_35")
#         self.tab_all.addTab(self.tab_new_train, "")
#         self.tab_new_car = QtWidgets.QWidget()
#         self.tab_new_car.setObjectName("tab_new_car")
#         self.label_4 = QtWidgets.QLabel(self.tab_new_car)
#         self.label_4.setGeometry(QtCore.QRect(10, 20, 41, 16))
#         self.label_4.setScaledContents(False)
#         self.label_4.setWordWrap(False)
#         self.label_4.setObjectName("label_4")
#         self.tb_new_car_kind = QtWidgets.QLineEdit(self.tab_new_car)
#         self.tb_new_car_kind.setGeometry(QtCore.QRect(110, 19, 381, 20))
#         self.tb_new_car_kind.setObjectName("tb_new_car_kind")
#         self.tb_new_car_lpic = QtWidgets.QLineEdit(self.tab_new_car)
#         self.tb_new_car_lpic.setGeometry(QtCore.QRect(110, 49, 381, 20))
#         self.tb_new_car_lpic.setObjectName("tb_new_car_lpic")
#         self.label_5 = QtWidgets.QLabel(self.tab_new_car)
#         self.label_5.setGeometry(QtCore.QRect(10, 50, 81, 16))
#         self.label_5.setScaledContents(False)
#         self.label_5.setWordWrap(False)
#         self.label_5.setObjectName("label_5")
#         self.tb_new_car_rpic = QtWidgets.QLineEdit(self.tab_new_car)
#         self.tb_new_car_rpic.setGeometry(QtCore.QRect(110, 79, 381, 20))
#         self.tb_new_car_rpic.setObjectName("tb_new_car_rpic")
#         self.label_6 = QtWidgets.QLabel(self.tab_new_car)
#         self.label_6.setGeometry(QtCore.QRect(10, 80, 81, 16))
#         self.label_6.setScaledContents(False)
#         self.label_6.setWordWrap(False)
#         self.label_6.setObjectName("label_6")
#         self.tb_new_car_lzpic = QtWidgets.QLineEdit(self.tab_new_car)
#         self.tb_new_car_lzpic.setGeometry(QtCore.QRect(110, 109, 381, 20))
#         self.tb_new_car_lzpic.setObjectName("tb_new_car_lzpic")
#         self.label_7 = QtWidgets.QLabel(self.tab_new_car)
#         self.label_7.setGeometry(QtCore.QRect(10, 110, 91, 16))
#         self.label_7.setScaledContents(False)
#         self.label_7.setWordWrap(False)
#         self.label_7.setObjectName("label_7")
#         self.tb_new_car_rzpic = QtWidgets.QLineEdit(self.tab_new_car)
#         self.tb_new_car_rzpic.setGeometry(QtCore.QRect(110, 139, 381, 20))
#         self.tb_new_car_rzpic.setObjectName("tb_new_car_rzpic")
#         self.label_8 = QtWidgets.QLabel(self.tab_new_car)
#         self.label_8.setGeometry(QtCore.QRect(10, 140, 101, 16))
#         self.label_8.setScaledContents(False)
#         self.label_8.setWordWrap(False)
#         self.label_8.setObjectName("label_8")
#         self.tlb_new_car_lpic = QtWidgets.QToolButton(self.tab_new_car)
#         self.tlb_new_car_lpic.setGeometry(QtCore.QRect(510, 50, 31, 20))
#         self.tlb_new_car_lpic.setObjectName("tlb_new_car_lpic")
#         self.tlb_new_car_lpic.clicked.connect(self.openFile)
#         self.tlb_new_car_rpic = QtWidgets.QToolButton(self.tab_new_car)
#         self.tlb_new_car_rpic.setGeometry(QtCore.QRect(510, 80, 31, 20))
#         self.tlb_new_car_rpic.setObjectName("tlb_new_car_rpic")
#         self.tlb_new_car_rpic.clicked.connect(self.openFile)
#         self.tlb_new_car_lzpic = QtWidgets.QToolButton(self.tab_new_car)
#         self.tlb_new_car_lzpic.setGeometry(QtCore.QRect(510, 110, 31, 20))
#         self.tlb_new_car_lzpic.setObjectName("tlb_new_car_lzpic")
#         self.tlb_new_car_lzpic.clicked.connect(self.openFile)
#         self.tlb_new_car_rzpic = QtWidgets.QToolButton(self.tab_new_car)
#         self.tlb_new_car_rzpic.setGeometry(QtCore.QRect(510, 140, 31, 20))
#         self.tlb_new_car_rzpic.setObjectName("tlb_new_car_rzpic")
#         self.tlb_new_car_rzpic.clicked.connect(self.openFile)
#         self.tb_new_car_length = QtWidgets.QLineEdit(self.tab_new_car)
#         self.tb_new_car_length.setGeometry(QtCore.QRect(110, 169, 361, 20))
#         self.tb_new_car_length.setObjectName("tb_new_car_length")
#         self.label_9 = QtWidgets.QLabel(self.tab_new_car)
#         self.label_9.setGeometry(QtCore.QRect(10, 170, 41, 16))
#         self.label_9.setScaledContents(False)
#         self.label_9.setWordWrap(False)
#         self.label_9.setObjectName("label_9")
#         self.horizontalLayoutWidget = QtWidgets.QWidget(self.tab_new_car)
#         self.horizontalLayoutWidget.setGeometry(QtCore.QRect(0, 450, 581, 31))
#         self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
#         self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
#         self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
#         self.horizontalLayout.setObjectName("horizontalLayout")
#         self.btn_new_car = QtWidgets.QPushButton(self.horizontalLayoutWidget)
#         self.btn_new_car.setObjectName("btn_new_car")
#         self.horizontalLayout.addWidget(self.btn_new_car)
#         self.label_10 = QtWidgets.QLabel(self.tab_new_car)
#         self.label_10.setGeometry(QtCore.QRect(10, 201, 41, 16))
#         self.label_10.setScaledContents(False)
#         self.label_10.setWordWrap(False)
#         self.label_10.setObjectName("label_10")
#         self.tb_new_car_info = QtWidgets.QLineEdit(self.tab_new_car)
#         self.tb_new_car_info.setGeometry(QtCore.QRect(110, 200, 381, 20))
#         self.tb_new_car_info.setObjectName("tb_new_car_info")
#         self.label_36 = QtWidgets.QLabel(self.tab_new_car)
#         self.label_36.setGeometry(QtCore.QRect(478, 171, 16, 16))
#         self.label_36.setScaledContents(False)
#         self.label_36.setWordWrap(False)
#         self.label_36.setObjectName("label_36")
#         self.tab_all.addTab(self.tab_new_car, "")
#         self.tab_options = QtWidgets.QWidget()
#         self.tab_options.setObjectName("tab_options")
#         self.tb_options_wait_time = QtWidgets.QLineEdit(self.tab_options)
#         self.tb_options_wait_time.setGeometry(QtCore.QRect(130, 20, 341, 20))
#         self.tb_options_wait_time.setObjectName("tb_options_wait_time")
#         self.label_25 = QtWidgets.QLabel(self.tab_options)
#         self.label_25.setGeometry(QtCore.QRect(30, 21, 91, 16))
#         self.label_25.setScaledContents(False)
#         self.label_25.setWordWrap(False)
#         self.label_25.setObjectName("label_25")
#         self.label_26 = QtWidgets.QLabel(self.tab_options)
#         self.label_26.setGeometry(QtCore.QRect(30, 50, 91, 16))
#         self.label_26.setScaledContents(False)
#         self.label_26.setWordWrap(False)
#         self.label_26.setObjectName("label_26")
#         self.tb_sx_ip = QtWidgets.QLineEdit(self.tab_options)
#         self.tb_sx_ip.setGeometry(QtCore.QRect(130, 49, 361, 20))
#         self.tb_sx_ip.setObjectName("tb_sx_ip")
#         self.label_27 = QtWidgets.QLabel(self.tab_options)
#         self.label_27.setGeometry(QtCore.QRect(30, 81, 91, 16))
#         self.label_27.setScaledContents(False)
#         self.label_27.setWordWrap(False)
#         self.label_27.setObjectName("label_27")
#         self.tb_xx_ip = QtWidgets.QLineEdit(self.tab_options)
#         self.tb_xx_ip.setGeometry(QtCore.QRect(130, 80, 361, 20))
#         self.tb_xx_ip.setObjectName("tb_xx_ip")
#         self.label_28 = QtWidgets.QLabel(self.tab_options)
#         self.label_28.setGeometry(QtCore.QRect(30, 111, 91, 16))
#         self.label_28.setScaledContents(False)
#         self.label_28.setWordWrap(False)
#         self.label_28.setObjectName("label_28")
#         self.tb_sx_z_ip = QtWidgets.QLineEdit(self.tab_options)
#         self.tb_sx_z_ip.setGeometry(QtCore.QRect(130, 110, 361, 20))
#         self.tb_sx_z_ip.setObjectName("tb_sx_z_ip")
#         self.label_29 = QtWidgets.QLabel(self.tab_options)
#         self.label_29.setGeometry(QtCore.QRect(30, 141, 91, 16))
#         self.label_29.setScaledContents(False)
#         self.label_29.setWordWrap(False)
#         self.label_29.setObjectName("label_29")
#         self.tb_xx_z_ip = QtWidgets.QLineEdit(self.tab_options)
#         self.tb_xx_z_ip.setGeometry(QtCore.QRect(130, 140, 361, 20))
#         self.tb_xx_z_ip.setObjectName("tb_xx_z_ip")
#         self.label_30 = QtWidgets.QLabel(self.tab_options)
#         self.label_30.setGeometry(QtCore.QRect(30, 171, 91, 16))
#         self.label_30.setScaledContents(False)
#         self.label_30.setWordWrap(False)
#         self.label_30.setObjectName("label_30")
#         self.tb_pic_socket_ip = QtWidgets.QLineEdit(self.tab_options)
#         self.tb_pic_socket_ip.setGeometry(QtCore.QRect(130, 170, 361, 20))
#         self.tb_pic_socket_ip.setObjectName("tb_pic_socket_ip")
#         self.tb_pic_socket_port = QtWidgets.QLineEdit(self.tab_options)
#         self.tb_pic_socket_port.setGeometry(QtCore.QRect(130, 199, 361, 20))
#         self.tb_pic_socket_port.setObjectName("tb_pic_socket_port")
#         self.label_31 = QtWidgets.QLabel(self.tab_options)
#         self.label_31.setGeometry(QtCore.QRect(30, 200, 91, 16))
#         self.label_31.setScaledContents(False)
#         self.label_31.setWordWrap(False)
#         self.label_31.setObjectName("label_31")
#         self.label_32 = QtWidgets.QLabel(self.tab_options)
#         self.label_32.setGeometry(QtCore.QRect(480, 22, 16, 16))
#         self.label_32.setScaledContents(False)
#         self.label_32.setWordWrap(False)
#         self.label_32.setObjectName("label_32")
#         self.horizontalLayoutWidget_6 = QtWidgets.QWidget(self.tab_options)
#         self.horizontalLayoutWidget_6.setGeometry(QtCore.QRect(0, 450, 581, 31))
#         self.horizontalLayoutWidget_6.setObjectName("horizontalLayoutWidget_6")
#         self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_6)
#         self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
#         self.horizontalLayout_6.setObjectName("horizontalLayout_6")
#         self.btn_options_save = QtWidgets.QPushButton(self.horizontalLayoutWidget_6)
#         self.btn_options_save.setObjectName("btn_options_save")
#         self.horizontalLayout_6.addWidget(self.btn_options_save)
#         self.tab_all.addTab(self.tab_options, "")
#         MainWindow.setCentralWidget(self.centralwidget)
#         self.statusbar = QtWidgets.QStatusBar(MainWindow)
#         self.statusbar.setObjectName("statusbar")
#         MainWindow.setStatusBar(self.statusbar)
#         self.actiona = QtWidgets.QAction(MainWindow)
#         self.actiona.setObjectName("actiona")
#         self.actionb = QtWidgets.QAction(MainWindow)
#         self.actionb.setObjectName("actionb")
#         self.actionc = QtWidgets.QAction(MainWindow)
#         self.actionc.setObjectName("actionc")
#
#         self.retranslateUi(MainWindow)
#         self.tab_all.setCurrentIndex(1)
#         QtCore.QMetaObject.connectSlotsByName(MainWindow)
#         self.setDefaultValue()
#
#     def setDefaultValue(self):
#         self.tb_options_wait_time.setText('30')
#         self.tb_sx_ip.setText('202.202.202.2')
#         self.tb_xx_ip.setText('202.202.202.3')
#         self.tb_sx_z_ip.setText('202.202.202.4')
#         self.tb_xx_z_ip.setText('202.202.202.5')
#         self.tb_pic_socket_ip.setText(CONSTVALUES.LOCAL_IP)
#         self.tb_pic_socket_port.setText('9999')
#         self.tb_new_case_sx_delay.setText('0')
#         self.tb_new_case_xx_delay.setText('0')
#
#     def retranslateUi(self, MainWindow):
#         _translate = QtCore.QCoreApplication.translate
#         MainWindow.setWindowTitle(_translate("MainWindow", "自动化测试平台"))
#         self.tab_all.setTabText(self.tab_all.indexOf(self.tab_monitor), _translate("MainWindow", "状态监控"))
#         self.cb_line_mode.setItemText(0, _translate("MainWindow", "双线单向"))
#         self.cb_line_mode.setItemText(1, _translate("MainWindow", "单线单向"))
#         self.cb_line_mode.setItemText(2, _translate("MainWindow", "单线双向"))
#         self.label.setText(_translate("MainWindow", "线路模式："))
#         self.cb_loop_mode.setItemText(0, _translate("MainWindow", "不循环"))
#         self.cb_loop_mode.setItemText(1, _translate("MainWindow", "循环"))
#         self.label_2.setText(_translate("MainWindow", "循环模式："))
#         self.cb_pic_mode.setItemText(0, _translate("MainWindow", "SOCKET传输"))
#         self.cb_pic_mode.setItemText(1, _translate("MainWindow", "文件传输"))
#         self.label_3.setText(_translate("MainWindow", "图片模式："))
#         self.label_11.setText(_translate("MainWindow", "场景列表："))
#         self.btn_start_case.setText(_translate("MainWindow", "启动"))
#         self.tab_all.setTabText(self.tab_all.indexOf(self.tab_do), _translate("MainWindow", "执行场景"))
#         self.cb_new_line_mode.setItemText(0, _translate("MainWindow", "双线单向"))
#         self.cb_new_line_mode.setItemText(1, _translate("MainWindow", "单线单向"))
#         self.cb_new_line_mode.setItemText(2, _translate("MainWindow", "单线双向"))
#         self.label_12.setText(_translate("MainWindow", "线路模式："))
#         self.label_13.setText(_translate("MainWindow", "上 行"))
#         self.label_14.setText(_translate("MainWindow", "下 行"))
#         self.label_15.setText(_translate("MainWindow", "场景名称："))
#         self.btn_new_case.setText(_translate("MainWindow", "新增"))
#         self.label_19.setText(_translate("MainWindow", "启动延时："))
#         self.label_20.setText(_translate("MainWindow", "INDEX模式："))
#         self.cb_new_case_sx_index.setItemText(0, _translate("MainWindow", "正常"))
#         self.cb_new_case_sx_index.setItemText(1, _translate("MainWindow", "丢失"))
#         self.label_21.setText(_translate("MainWindow", "启动延时："))
#         self.cb_new_case_xx_index.setItemText(0, _translate("MainWindow", "正常"))
#         self.cb_new_case_xx_index.setItemText(1, _translate("MainWindow", "丢失"))
#         self.label_22.setText(_translate("MainWindow", "INDEX模式："))
#         self.label_23.setText(_translate("MainWindow", "秒"))
#         self.label_24.setText(_translate("MainWindow", "秒"))
#         self.label_33.setText(_translate("MainWindow", "来车方向："))
#         self.cb_new_case_sx_direction.setItemText(0, _translate("MainWindow", "正向"))
#         self.cb_new_case_sx_direction.setItemText(1, _translate("MainWindow", "反向"))
#         self.label_34.setText(_translate("MainWindow", "来车方向："))
#         self.cb_new_case_xx_direction.setItemText(0, _translate("MainWindow", "正向"))
#         self.cb_new_case_xx_direction.setItemText(1, _translate("MainWindow", "反向"))
#         self.tab_all.setTabText(self.tab_all.indexOf(self.tab_new_case), _translate("MainWindow", "新增场景"))
#         self.label_16.setText(_translate("MainWindow", "列车名称："))
#         # self.label_17.setText(_translate("MainWindow", "时速："))
#         self.label_18.setText(_translate("MainWindow", "车辆列表："))
#         self.btn_new_train.setText(_translate("MainWindow", "新增"))
#         # self.label_35.setText(_translate("MainWindow", "公里/小时"))
#         self.tab_all.setTabText(self.tab_all.indexOf(self.tab_new_train), _translate("MainWindow", "新增列车"))
#         self.label_4.setText(_translate("MainWindow", "车型："))
#         self.label_5.setText(_translate("MainWindow", "左侧车厢图片："))
#         self.label_6.setText(_translate("MainWindow", "右侧车厢图片："))
#         self.label_7.setText(_translate("MainWindow", "左侧走行部图片："))
#         self.label_8.setText(_translate("MainWindow", "右侧走行部图片："))
#         self.tlb_new_car_lpic.setText(_translate("MainWindow", "..."))
#         self.tlb_new_car_rpic.setText(_translate("MainWindow", "..."))
#         self.tlb_new_car_lzpic.setText(_translate("MainWindow", "..."))
#         self.tlb_new_car_rzpic.setText(_translate("MainWindow", "..."))
#         self.label_9.setText(_translate("MainWindow", "车长："))
#         self.btn_new_car.setText(_translate("MainWindow", "新增"))
#         self.label_10.setText(_translate("MainWindow", "备注："))
#         self.label_36.setText(_translate("MainWindow", "米"))
#         self.tab_all.setTabText(self.tab_all.indexOf(self.tab_new_car), _translate("MainWindow", "新增车辆"))
#         self.label_25.setText(_translate("MainWindow", "空闲等待时间："))
#         self.label_26.setText(_translate("MainWindow", "上行线路IP："))
#         self.label_27.setText(_translate("MainWindow", "下行线路IP："))
#         self.label_28.setText(_translate("MainWindow", "上行走行部IP："))
#         self.label_29.setText(_translate("MainWindow", "下行走行部IP："))
#         self.label_30.setText(_translate("MainWindow", "传图服务IP："))
#         self.label_31.setText(_translate("MainWindow", "传图服务端口："))
#         self.label_32.setText(_translate("MainWindow", "秒"))
#         self.btn_options_save.setText(_translate("MainWindow", "保存"))
#         self.tab_all.setTabText(self.tab_all.indexOf(self.tab_options), _translate("MainWindow", "首选项"))
#         self.actiona.setText(_translate("MainWindow", "列车编组"))
#         self.actionb.setText(_translate("MainWindow", "车辆配置"))
#         self.actionc.setText(_translate("MainWindow", "首选项"))
#
#         self.lst_case.setVerticalScrollBar(self.verticalScrollBar)
#         self.tr_new_case_sx.setVerticalScrollBar(self.vsb_new_case_sx)
#         self.tr_new_case_xx.setVerticalScrollBar(self.vsb_new_case_xx)
#         self.tr_new_train.setVerticalScrollBar(self.verticalScrollBar_2)
#
#         self.lst_case.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
#         self.lst_case.customContextMenuRequested.connect(self.showInsertMenu)
#
#         self.tr_new_case_sx.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
#         self.tr_new_case_sx.customContextMenuRequested.connect(self.showInsertMenu)
#         self.tr_new_case_xx.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
#         self.tr_new_case_xx.customContextMenuRequested.connect(self.showInsertMenu)
#         self.tr_new_train.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
#         self.tr_new_train.customContextMenuRequested.connect(self.showInsertMenu)
#
#
#
#         self.tr_new_train.itemDoubleClicked.connect(self.trDbClicked)
#         self.tr_new_train.itemSelectionChanged.connect(self.trSelectChg)
#         # self.tr_new_train.itemClicked.connect(self.trClicked)
#
#         self.btn_new_car.clicked.connect(self.saveNewCar)
#         self.btn_new_train.clicked.connect(self.saveNewTrain)
#         self.btn_new_case.clicked.connect(self.saveNewCase)
#         self.btn_options_save.clicked.connect(self.saveOptions)
#
#         self.lastOpen = None
#         self.lastOpenCol = None
#
#         self.logic = logic()
#
#     def trDbClicked(self, item, col):
#         if col in [1,2,3]:
#             self.sender().openPersistentEditor(item, col)
#             self.lastOpen = item
#             self.lastOpenCol = col
#
#     def trClicked(self, item, col):
#         if col not in [1,2,3] and self.lastOpen is not None:
#             self.sender().closePersistentEditor(self.lastOpen, self.lastOpenCol)
#             self.lastOpen = None
#             self.lastOpenCol = None
#
#     def trSelectChg(self):
#         if self.lastOpen is not None:
#             self.sender().closePersistentEditor(self.lastOpen, self.lastOpenCol)
#             self.lastOpen = None
#             self.lastOpenCol = None
#
#     def showInsertMenu(self):
#         try:
#             _sender = self.sender()
#             self.lastRightSender = _sender
#             _rightMenu = QtWidgets.QMenu(_sender)
#             _action_1 = _rightMenu.addAction(u'添加')
#             _action_2 = _rightMenu.addAction(u'删除')
#             _action_1.triggered.connect(self.showDialog)
#             _action_2.triggered.connect(self.deleteItem)
#             _rightMenu.exec_(QtGui.QCursor.pos())
#             self.lastRightSender = None
#         except Exception as e:
#             self.toPrint(repr(e))
#
#     def deleteItem(self):
#         try:
#             if self.lastRightSender.objectName() == 'lst_case':
#                 _item = self.lastRightSender.takeItem(self.lastRightSender.row(self.lastRightSender.currentItem()))
#                 item = self.lastRightSender.itemWidget(_item)
#                 self.lastRightSender.removeItemWidget(item)
#             else:
#                 root = self.lastRightSender.invisibleRootItem()
#
#                 for item in self.lastRightSender.selectedItems():
#                     (item.parent() or root).removeChild(item)
#         except Exception as e:
#             pass
#
#     def showDialog(self):
#         _d = QtWidgets.QDialog()
#         _ui = Loader(self)
#         _ui.setupUi(_d)
#         _d.show()
#         _d.exec_()
#
#     def openFile(self):
#         _filePath, filetype = QFileDialog.getOpenFileName(self,
#                                                           "选取文件",
#                                                           "C:/",
#                                                           "全部 (*);;图像 (*.jpg)")
#         if self.sender().objectName() == 'tlb_new_car_lpic':
#             self.tb_new_car_lpic.setText(_filePath)
#         if self.sender().objectName() == 'tlb_new_car_rpic':
#             self.tb_new_car_rpic.setText(_filePath)
#         if self.sender().objectName() == 'tlb_new_car_lzpic':
#             self.tb_new_car_lzpic.setText(_filePath)
#         if self.sender().objectName() == 'tlb_new_car_rzpic':
#             self.tb_new_car_rzpic.setText(_filePath)
#
#     def toPrint(self, _message):
#         _item = QtWidgets.QListWidgetItem(str(_message))
#         self.listView_3.insertItem(0, _item)
#
#     def saveNewCar(self):
#         _imgs = []
#         _imgs.append(self.tb_new_car_lpic.text())
#         _imgs.append(self.tb_new_car_rpic.text())
#         _imgs.append(self.tb_new_car_lzpic.text())
#         _imgs.append(self.tb_new_car_rzpic.text())
#         for img in _imgs:
#             if not os.path.exists(img):
#                 self.statusbar.showMessage('指定的车辆图片不存在！')
#                 return
#         _car = Car(
#             self.tb_new_car_kind.text(),
#             _imgs,
#             self.tb_new_car_info.text(),
#             _length=float(self.tb_new_car_length.text())
#         )
#         self.logic.car_mgr[self.tb_new_car_info.text()] = _car
#         with open('car.data', 'wb') as f:
#             pickle.dump(self.logic.car_mgr, file=f)
#         self.toPrint(repr(self.logic.car_mgr))
#         self.statusbar.showMessage('新增车辆已保存！')
#
#     def saveNewTrain(self):
#         _cars = []
#         try:
#             for i in range(1000):
#                 _item = self.tr_new_train.topLevelItem(i)
#                 _car = copy.deepcopy(self.logic.car_mgr[_item.text(5)])
#                 _car.setLength(_item.text(1))
#                 _car.setSpeed(_item.text(2))
#                 _car.setCode(_item.text(3))
#                 _car.setIndex(i+1)
#                 if _item.checkState(4) != QtCore.Qt.Checked:
#                     _car.setPriority(False)
#                 _cars.append(_car)
#         except Exception as e:
#             pass
#         try:
#             _trainName = self.tb_new_train_name.text()
#             _train = Train(
#                 _trainName,
#                 _cars
#             )
#             if _trainName in self.logic.train_mgr.keys():
#                 _r = QtWidgets.QMessageBox.information(
#                     self,
#                     '请注意',
#                     '同名列车已存在，是否覆盖？',
#                     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
#                 )
#             else:
#                 self.logic.train_mgr[_trainName] = _train
#             with open('train.data', 'wb') as f:
#                 pickle.dump(self.logic.train_mgr, file=f)
#             self.toPrint(repr(self.logic.train_mgr))
#             self.statusbar.showMessage('新增列车已保存！')
#         except Exception as e:
#             pass
#
#     def saveNewCase(self):
#
#         _sx_trains = []
#         _xx_trains = []
#         try:
#             i = 0
#             while 1:
#                 _item = self.tr_new_case_sx.topLevelItem(i)
#                 _train = self.logic.train_mgr[_item.text(0)]
#                 if self.cb_new_case_sx_index.currentText() == '丢失':
#                     _train.setIndexMode(CONSTVALUES.INDEX_MODE_MISS)
#                 _sx_trains.append(_train)
#                 i += 1
#         except Exception as e:
#             pass
#
#         try:
#             i = 0
#             while 1:
#                 _item = self.tr_new_case_xx.topLevelItem(i)
#                 _train = self.logic.train_mgr[_item.text(0)]
#                 if self.cb_new_case_xx_index.currentText() == '丢失':
#                     _train.setIndexMode(CONSTVALUES.INDEX_MODE_MISS)
#                 _xx_trains.append(_train)
#                 i += 1
#         except Exception as e:
#             pass
#
#         try:
#             _case = Case(
#                 self.tb_case_name.text(),
#                 sx_trains=_sx_trains,
#                 xx_trains=_xx_trains,
#                 sx_delay=int(float(self.tb_new_case_sx_delay.text())),
#                 xx_delay=int(float(self.tb_new_case_xx_delay.text())),
#                 sx_direction='forward' if self.cb_new_case_sx_direction.currentText() == '正向' else 'backward',
#                 xx_direction='forward' if self.cb_new_case_xx_direction.currentText() == '正向' else 'backward'
#             )
#             self.logic.case_mgr[self.tb_case_name.text()] = _case
#
#             with open('case.data', 'wb') as f:
#                 pickle.dump(self.logic.case_mgr, file=f)
#             self.toPrint(repr(self.logic.case_mgr))
#             self.statusbar.showMessage('新增场景已保存！')
#         except Exception as e:
#             pass
#
#     def saveOptions(self):
#         self.logic.setSocketIP(self.tb_pic_socket_ip.text())
#         self.logic.setSocketPort(int(self.tb_pic_socket_port.text()))
#         self.logic.setSxIP(self.tb_sx_ip.text())
#         self.logic.setXxIP(self.tb_xx_ip.text())
#         self.logic.setSxZIP(self.tb_sx_z_ip.text())
#         self.logic.setXxZIP(self.tb_xx_z_ip.text())
#         self.logic.setFreeTime(int(self.tb_options_wait_time.text()))
#         self.toPrint('首选项参数已保存！')
#
#     def go(self):
#         self.logic.setUI(self)
#         if self.cb_line_mode.currentText() == '双线单向':
#             self.logic.setLineMode(CONSTVALUES.LINE_MODE_2L1D)
#         elif self.cb_line_mode.currentText() == '单线单向':
#             self.logic.setLineMode(CONSTVALUES.LINE_MODE_1L1D)
#         elif self.cb_line_mode.currentText() == '单线双向':
#             self.logic.setLineMode(CONSTVALUES.LINE_MODE_1L2D)
#         if self.cb_loop_mode.currentText() == '不循环':
#             self.logic.setLoopMode(CONSTVALUES.LOOP_MODE_NO)
#         else:
#             self.logic.setLoopMode(CONSTVALUES.LOOP_MODE_YES)
#
#         if self.cb_pic_mode.currentText() == 'SOCKET传输':
#             self.logic.setPicMode(CONSTVALUES.PIC_MODE_SOCKET)
#         elif self.cb_pic_mode.currentText() == '文件传输':
#             self.logic.setPicMode(CONSTVALUES.PIC_MODE_FILE)
#         self.logic.setFreeTime(int(self.tb_options_wait_time.text()))
#         _cases = []
#         try:
#             for i in range(self.lst_case.count()):
#                 _item = self.lst_case.takeItem(0)
#                 _cases.append(_item.text())
#         except Exception as e:
#             pass
#         self.logic.setCasePool(_cases)
#         self.logic.start()

class logic():
    def __init__(self):
        self.sx = None
        self.xx = None
        self.sx_com = 9
        self.xx_com = 11
        self.sx_in_use = False
        self.xx_in_use = False
        self.free_time = 120
        self.sx_ip = '202.202.202.2'
        self.xx_ip = '202.202.202.3'
        self.sx_zip = '202.202.202.4'
        self.xx_zip = '202.202.202.5'
        self.picSocketIP = CONSTVALUES.LOCAL_IP
        self.picSocketPort = 9999
        self.STOP = False
        self.mainUI = None
        self.loopMode = CONSTVALUES.LOOP_MODE_NO
        self.lineMode = CONSTVALUES.LINE_MODE_2L1D
        self.picMode = CONSTVALUES.PIC_MODE_SOCKET
        self.casePool = None
        self.sx_current_index = -1
        self.xx_current_index = -1


        self.sx_serial = None
        self.xx_serial = None

        self._startThread = None

        self.car_mgr = dict()
        self.train_mgr = dict()
        self.case_mgr = dict()

        self.serial_init()
        self.data_init()

    def setCasePool(self, _cases):
        self.casePool = _cases

    def setPicMode(self, _mode):
        self.picMode = _mode

    def setLoopMode(self, _mode):
        self.loopMode = _mode

    def setLineMode(self, _mode):
        self.lineMode = _mode

    def setFreeTime(self, _ms):
        self.free_time = _ms

    def setUI(self, _obj):
        self.mainUI = _obj

    def setSxIP(self, _ip):
        self.sx_ip = _ip

    def setXxIP(self, _ip):
        self.xx_ip = _ip

    def setSxZIP(self, _ip):
        self.sx_zip = _ip

    def setXxZIP(self, _ip):
        self.xx_zip = _ip

    def setSocketIP(self, _ip):
        self.picSocketIP = _ip

    def setSocketPort(self, _port):
        self.picSocketPort = _port

    def data_init(self):    #todo 重写车厢、场景数据保存
        try:
            with open('car.data', 'rb') as f:
                self.car_mgr = pickle.load(f)
        except:
            self.car_mgr = dict()
        try:
            with open('train.data', 'rb') as f:
                self.train_mgr = pickle.load(f)
        except:
            self.train_mgr = dict()
        try:
            with open('case.data', 'rb') as f:
                self.case_mgr = pickle.load(f)
        except:
            self.case_mgr = dict()

    def sendIndex(self, _train, _path):
        """
        生成index文件
        :param _line: 线路名
        :return: 
        """
        dstpath = _path
        reader = open(dstpath, 'a')
        for i in _train.INDEX:
            reader.write(i)


    # 废弃
    async def serialSrv(self, line, case):
        all_trains = []
        if self.lineMode == CONSTVALUES.LINE_MODE_1L2D:
            if line == 'sx':
                _serial = self.sx_serial
            else:
                _serial = self.xx_serial
            if case.sx_delay <= case.xx_delay:
                all_trains = [case.sx, case.xx]
                _direction = case.sx_direction
                _delay = case.sx_delay
            else:
                all_trains = [case.xx, case.sx]
                _direction = case.xx_direction
                _delay = case.xx_delay
        else:
            if line == 'sx':
                _serial = self.sx_serial
                all_trains = [case.sx]
                _direction = case.sx_direction
                _delay = case.sx_delay
            else:
                _serial = self.xx_serial
                all_trains = [case.xx]
                _direction = case.xx_direction
                _delay = case.xx_delay

        try:
            self.serial_write_data(_serial, 'F')
            self.mainUI.toPrint('=%s= %s 握手 ' % (str(datetime.datetime.now()), line))
            await asyncio.sleep(1)
            for _trains in all_trains:
                for _train in _trains:
                    if self.STOP:
                        break
                    await asyncio.sleep(_delay)
                    self.serial_write_data(
                        _serial, 'S' + ('0' if _direction == 'forward' else '1'))
                    self.mainUI.toPrint('=%s= %s %s 来车了 ' %
                          (str(datetime.datetime.now()), line, _direction))
                    # await asyncio.sleep(1)
                    self.serial_write_data(
                        _serial, 'T' + UTIL.getTime(_type='file')[2:])
                    # _train.updaqteTime()
                    self.mainUI.toPrint('=%s= %s ' %
                                        (str(datetime.datetime.now()), UTIL.getTime(_type='file')))
                    # 来车信息
                    if (line == 'sx' and self.lineMode != CONSTVALUES.LINE_MODE_1L2D) or (_direction == 'forward' and self.lineMode == CONSTVALUES.LINE_MODE_1L2D):
                        self.sx_in_use = True
                    elif (line == 'xx' and self.lineMode != CONSTVALUES.LINE_MODE_1L2D) or (_direction == 'backward' and self.lineMode == CONSTVALUES.LINE_MODE_1L2D):
                        self.xx_in_use = True
                    for car in _train.car:
                        if self.STOP:
                            break
                        _index = _train.car.index(car)
                        if not car.Priority:
                            if (self.lineMode != CONSTVALUES.LINE_MODE_1L2D and line == 'sx') or (self.lineMode == CONSTVALUES.LINE_MODE_1L2D and _direction == 'forward'):
                                while self.sx_current_index < _index:
                                    await asyncio.sleep(1)
                            elif (self.lineMode != CONSTVALUES.LINE_MODE_1L2D and line == 'xx') or (self.lineMode == CONSTVALUES.LINE_MODE_1L2D and _direction == 'backward'):
                                while self.xx_current_index < _index:
                                    await asyncio.sleep(1)

                        _c = _train.get_serial(_index)
                        for c in _c:
                            self.serial_write_data(_serial, c)
                        self.mainUI.toPrint('=%s= %s >>> %s (%d/%d) ' % (str(datetime.datetime.now()), line, _c, _index + 1, len(
                            _train.car)))
                        if car.Priority:
                            if (line == 'sx' and self.lineMode != CONSTVALUES.LINE_MODE_1L2D) or (
                                    _direction == 'forward' and self.lineMode == CONSTVALUES.LINE_MODE_1L2D):
                                self.sx_current_index = _index
                            elif (line == 'xx' and self.lineMode != CONSTVALUES.LINE_MODE_1L2D) or (
                                    _direction == 'backward' and self.lineMode == CONSTVALUES.LINE_MODE_1L2D):
                                self.xx_current_index = _index

                        _t =  float(UTIL.getSpeed(car.length, _s=car.speed))
                        # self.mainUI.toPrint('> ' + str(_t))
                        await asyncio.sleep(1)


                    for t in range(1, 13):
                        if self.STOP:
                            break

                        if int(t) % 3 == 0:
                            self.serial_write_data(_serial, 'F')
                        await asyncio.sleep(1)

                    # 结束标志
                    self.serial_write_data(_serial, 's')
                    if line == 'sx':
                        self.sx_in_use = False
                    else:
                        self.xx_in_use = False
                    self.mainUI.toPrint('=%s= %s 过车结束 ' % (str(datetime.datetime.now()), line))
                    if _train.indexMode == CONSTVALUES.INDEX_MODE_NORMAL:
                        if self.lineMode == CONSTVALUES.LINE_MODE_1L2D:
                            index_path = os.path.join(
                                'e:\\',
                                'gqpics',
                                self.sx_ip if _direction == 'forward' else self.xx_ip,
                                str(UTIL.getTime(_time=_train.time, _type='file')),
                                'index.txt'
                            )
                            zindex_path = os.path.join(
                                'e:\\',
                                'ZXGQPics',
                                self.sx_zip if _direction == 'forward' else self.xx_zip,
                                str(UTIL.getTime(_time=_train.time, _type='file')),
                                'index.txt'
                            )
                        else:
                            index_path = os.path.join(
                                'e:\\',
                                'gqpics',
                                self.sx_ip if line == 'sx' else self.xx_ip,
                                str(UTIL.getTime(_time=_train.time, _type='file')),
                                'index.txt'
                            )
                            zindex_path = os.path.join(
                                'e:\\',
                                'ZXGQPics',
                                self.sx_zip if line == 'sx' else self.xx_zip,
                                str(UTIL.getTime(_time=_train.time, _type='file')),
                                'index.txt'
                            )
                        self.sendIndex(_train, index_path)
                        self.sendIndex(_train, zindex_path)
                        self.mainUI.toPrint('=%s= %s index已生成' % (str(datetime.datetime.now()), line))
                    else:
                        self.mainUI.toPrint('=%s= %s index按设定未生成' % (str(datetime.datetime.now()), line))
                    # 空闲
                    for t in range(1, self.free_time+1):
                        if self.STOP:
                            break

                        if int(t) % 3 == 0:
                            self.serial_write_data(_serial, 'F')
                            self.mainUI.toPrint('=%s= %s >>> 空闲中 (%d/%d) ' % (str(datetime.datetime.now()), line, range(1, self.free_time+1).index(t), len(
                                range(1, self.free_time+1))))
                        await asyncio.sleep(1)
                if _direction == 'forward':
                    _direction = 'backward'
                else:
                    _direction = 'forward'
        except Exception as e:
            self.mainUI.toPrint('in serial > ' + repr(e))

    def serial_write_data(self, serial, _data):
        #   单行数据
        serial.write(bytes.fromhex('02'))
        for _c in _data:
            serial.write(_c.encode(encoding='utf-8'))
        serial.write(bytes.fromhex('03'))

    #废弃
    async def picSrv(self, line, case):
        all_trains = []
        if self.lineMode == CONSTVALUES.LINE_MODE_1L2D:
            if case.sx_delay <= case.xx_delay:
                all_trains = [case.sx, case.xx]
                _direction = case.sx_direction
            else:
                all_trains = [case.xx, case.sx]
                _direction = case.xx_direction
        else:
            if line == 'sx':
                all_trains = [case.sx]
                _direction = case.sx_direction
            else:
                all_trains = [case.xx]
                _direction = case.xx_direction
        try:
            for _trains in all_trains:
                for _train in _trains:
                    if (line == 'sx' and self.lineMode != CONSTVALUES.LINE_MODE_1L2D) or (_direction == 'forward' and self.lineMode == CONSTVALUES.LINE_MODE_1L2D):
                        while not self.sx_in_use:
                            await asyncio.sleep(1)
                    elif (line == 'xx' and self.lineMode != CONSTVALUES.LINE_MODE_1L2D) or (_direction == 'backward' and self.lineMode == CONSTVALUES.LINE_MODE_1L2D):
                        while not self.xx_in_use:
                            await asyncio.sleep(1)

                    for car in _train.car:
                        if self.STOP:
                            break
                        _index = _train.car.index(car)
                        _carIndex = str(_train.car.index(car) + 1)
                        if car.Priority:
                            if (self.lineMode != CONSTVALUES.LINE_MODE_1L2D and line == 'sx') or (self.lineMode == CONSTVALUES.LINE_MODE_1L2D and _direction == 'forward'):
                                while self.sx_current_index < _index:
                                    await asyncio.sleep(0.1)
                            elif (self.lineMode != CONSTVALUES.LINE_MODE_1L2D and line == 'xx') or (self.lineMode == CONSTVALUES.LINE_MODE_1L2D and _direction == 'backward'):
                                while self.xx_current_index < _index:
                                    await asyncio.sleep(0.1)
                        if self.picMode == CONSTVALUES.PIC_MODE_FILE:
                            dstbasepath = os.path.join('e:\\', 'gqpics')
                            dstZXbasepath = os.path.join('e:\\', 'ZXGQPics')
                            dst_l_path = ''
                            dst_r_path = ''
                            dst_zl_path = ''
                            dst_zr_path = ''
                            if self.lineMode != CONSTVALUES.LINE_MODE_1L2D and line == 'sx':
                                dst_r_path = os.path.join(dstbasepath, self.sx_ip,
                                                          str(UTIL.getTime(_time=_train.time, _type='file')),
                                                          'R%s_%s.jpg' % (_carIndex.zfill(
                                                              3), _carIndex))
                                dst_l_path = os.path.join(dstbasepath, self.sx_ip,
                                                          str(UTIL.getTime(_time=_train.time, _type='file')),
                                                          'L%s_%s.jpg' % (_carIndex.zfill(
                                                              3), _carIndex))
                                dst_zr_path = os.path.join(dstZXbasepath, self.sx_zip,
                                                           str(UTIL.getTime(_time=_train.time, _type='file')),
                                                           'ZR%s_%s.jpg' % (_carIndex.zfill(
                                                               3), _carIndex))
                                dst_zl_path = os.path.join(dstZXbasepath, self.sx_zip,
                                                           str(UTIL.getTime(_time=_train.time, _type='file')),
                                                           'ZL%s_%s.jpg' % (_carIndex.zfill(
                                                               3), _carIndex))
                                if self.lineMode == CONSTVALUES.LINE_MODE_1L1D and self.xx_in_use:
                                    car.R_src = os.path.join(
                                        'resources', 'jiaocuo_R.jpg')
                            elif self.lineMode != CONSTVALUES.LINE_MODE_1L2D and line == 'xx':
                                dst_r_path = os.path.join(dstbasepath, self.xx_ip,
                                                          str(UTIL.getTime(_time=_train.time, _type='file')),
                                                          'R%s_%s.jpg' % (_carIndex.zfill(
                                                              3), _carIndex))
                                dst_l_path = os.path.join(dstbasepath, self.xx_ip,
                                                          str(UTIL.getTime(_time=_train.time, _type='file')),
                                                          'L%s_%s.jpg' % (_carIndex.zfill(
                                                              3), _carIndex))
                                dst_zr_path = os.path.join(dstZXbasepath, self.xx_zip,
                                                           str(UTIL.getTime(_time=_train.time, _type='file')),
                                                           'ZR%s_%s.jpg' % (_carIndex.zfill(
                                                               3), _carIndex))
                                dst_zl_path = os.path.join(dstZXbasepath, self.xx_zip,
                                                           str(UTIL.getTime(_time=_train.time, _type='file')),
                                                           'ZL%s_%s.jpg' % (_carIndex.zfill(
                                                               3), _carIndex))
                                if self.lineMode == CONSTVALUES.LINE_MODE_1L1D and self.sx_in_use:
                                    car.R_src = os.path.join(
                                        'resources', 'jiaocuo_R.jpg')
                            elif self.lineMode == CONSTVALUES.LINE_MODE_1L2D and _direction == 'forward':
                                dst_r_path = os.path.join(dstbasepath, self.sx_ip,
                                                          str(UTIL.getTime(_time=_train.time, _type='file')),
                                                          'R%s_%s.jpg' % (_carIndex.zfill(
                                                              3), _carIndex))
                                dst_l_path = os.path.join(dstbasepath, self.sx_ip,
                                                          str(UTIL.getTime(_time=_train.time, _type='file')),
                                                          'L%s_%s.jpg' % (_carIndex.zfill(
                                                              3), _carIndex))
                                dst_zr_path = os.path.join(dstZXbasepath, self.sx_zip,
                                                           str(UTIL.getTime(_time=_train.time, _type='file')),
                                                           'ZR%s_%s.jpg' % (_carIndex.zfill(
                                                               3), _carIndex))
                                dst_zl_path = os.path.join(dstZXbasepath, self.sx_zip,
                                                           str(UTIL.getTime(_time=_train.time, _type='file')),
                                                           'ZL%s_%s.jpg' % (_carIndex.zfill(
                                                               3), _carIndex))
                            elif self.lineMode == CONSTVALUES.LINE_MODE_1L2D and _direction == 'backward':
                                dst_r_path = os.path.join(dstbasepath, self.xx_ip,
                                                          str(UTIL.getTime(_time=_train.time, _type='file')),
                                                          'R%s_%s.jpg' % (_carIndex.zfill(
                                                              3), _carIndex))
                                dst_l_path = os.path.join(dstbasepath, self.xx_ip,
                                                          str(UTIL.getTime(_time=_train.time, _type='file')),
                                                          'L%s_%s.jpg' % (_carIndex.zfill(
                                                              3), _carIndex))
                                dst_zr_path = os.path.join(dstZXbasepath, self.xx_zip,
                                                           str(UTIL.getTime(_time=_train.time, _type='file')),
                                                           'ZR%s_%s.jpg' % (_carIndex.zfill(
                                                               3), _carIndex))
                                dst_zl_path = os.path.join(dstZXbasepath, self.xx_zip,
                                                           str(UTIL.getTime(_time=_train.time, _type='file')),
                                                           'ZL%s_%s.jpg' % (_carIndex.zfill(
                                                               3), _carIndex))

                            if self.lineMode == CONSTVALUES.LINE_MODE_1L2D and _direction == 'forward':
                                if not os.path.exists(os.path.join(dstbasepath, self.sx_ip, str(UTIL.getTime(_time=_train.time, _type='file')))):
                                    os.mkdir(os.path.join(dstbasepath, self.sx_ip, str(
                                        UTIL.getTime(_time=_train.time, _type='file'))))
                                if not os.path.exists(os.path.join(dstZXbasepath, self.sx_zip, str(UTIL.getTime(_time=_train.time, _type='file')))):
                                    os.mkdir(os.path.join(dstZXbasepath, self.sx_zip, str(
                                        UTIL.getTime(_time=_train.time, _type='file'))))
                            elif self.lineMode == CONSTVALUES.LINE_MODE_1L2D and _direction == 'backward':
                                if not os.path.exists(os.path.join(dstbasepath, self.xx_ip, str(UTIL.getTime(_time=_train.time, _type='file')))):
                                    os.mkdir(os.path.join(dstbasepath, self.xx_ip, str(
                                        UTIL.getTime(_time=_train.time, _type='file'))))
                                if not os.path.exists(os.path.join(dstZXbasepath, self.xx_zip, str(UTIL.getTime(_time=_train.time, _type='file')))):
                                    os.mkdir(os.path.join(dstbasepath, self.xx_zip, str(
                                        UTIL.getTime(_time=_train.time, _type='file'))))
                            else:
                                if line == 'sx':
                                    if not os.path.exists(os.path.join(dstbasepath, self.sx_ip, str(UTIL.getTime(_time=_train.time, _type='file')))):
                                        os.mkdir(os.path.join(dstbasepath, self.sx_ip, str(
                                            UTIL.getTime(_time=_train.time, _type='file'))))
                                elif line == 'xx':
                                    if not os.path.exists(os.path.join(dstbasepath, self.xx_ip, str(UTIL.getTime(_time=_train.time, _type='file')))):
                                        os.mkdir(os.path.join(dstbasepath, self.xx_ip, str(
                                            UTIL.getTime(_time=_train.time, _type='file'))))
                            if os.path.exists(car.L_src):
                                __import__('shutil').copy(car.L_src, dst_l_path)
                            if os.path.exists(car.R_src):
                                __import__('shutil').copy(car.R_src, dst_r_path)
                            if os.path.exists(car.ZL_src):
                                __import__('shutil').copy(car.ZL_src, dst_zl_path)
                            if os.path.exists(car.ZR_src):
                                __import__('shutil').copy(car.ZR_src, dst_zr_path)
                        elif self.picMode == CONSTVALUES.PIC_MODE_SOCKET: # SOCKET发图
                            _lst = list()
                            _zlst = list()
                            _xml = list()
                            _zxml = list()
                            if os.path.exists(car.L_src):
                                _lst.append(('L', car.L_src))
                            if os.path.exists(car.R_src):
                                _lst.append(('R', car.R_src))
                            if os.path.exists(car.ZL_src):
                                _zlst.append(('ZL', car.ZL_src))
                            if os.path.exists(car.ZR_src):
                                _zlst.append(('ZR', car.ZR_src))

                            if self.lineMode == CONSTVALUES.LINE_MODE_1L2D and _direction == 'forward':
                                _xml = self.build_xml(
                                    _lst,
                                    line_id='1',
                                    direction='0',
                                    traintime=str(UTIL.getTime(_time=_train.time, _type='file')),
                                    trainlabel=car.code,
                                    trainindex=_carIndex
                                )
                                _zxml = self.build_xml(
                                    _zlst,
                                    Type='1',
                                    line_id='1',
                                    direction='0',
                                    traintime=str(UTIL.getTime(_time=_train.time, _type='file')),
                                    trainlabel=car.code,
                                    trainindex=_carIndex
                                )

                            if self.lineMode == LINE_MODE_1L2D and _direction == 'backward':
                                _xml = self.build_xml(
                                    _lst,
                                    line_id='2',
                                    direction='0',
                                    traintime=str(UTIL.getTime(_time=_train.time, _type='file')),
                                    trainlabel=car.code,
                                    trainindex=_carIndex
                                )
                                _zxml = self.build_xml(
                                    _zlst,
                                    Type='1',
                                    line_id='2',
                                    direction='0',
                                    traintime=str(UTIL.getTime(_time=_train.time, _type='file')),
                                    trainlabel=car.code,
                                    trainindex=_carIndex
                                )
                            if self.lineMode != LINE_MODE_1L2D:
                                _xml = self.build_xml(
                                    _lst,
                                    line_id='1' if line == 'sx' else '2',
                                    direction='0' if _direction == 'forward' else '1',
                                    traintime=str(UTIL.getTime(_time=_train.time, _type='file')),
                                    trainlabel=car.code,
                                    trainindex=_carIndex
                                )
                                _zxml = self.build_xml(
                                    _zlst,
                                    Type='1',
                                    line_id='1' if line == 'sx' else '2',
                                    direction='0' if _direction == 'forward' else '1',
                                    traintime=str(UTIL.getTime(_time=_train.time, _type='file')),
                                    trainlabel=car.code,
                                    trainindex=_carIndex
                                )

                            _lst_pt = list()
                            _lst_zpt = list()
                            for pic in _lst:
                                _lst_pt.append(threading.Thread(
                                    target=self.processPicSocket,
                                    args=(
                                        pic,
                                        _xml[_lst.index(pic)]
                                    )
                                ))

                            for _p in _lst_pt:
                                _p.start()

                            for pic in _zlst:
                                _lst_zpt.append(threading.Thread(
                                    target=self.processPicSocket,
                                    args=(
                                        pic,
                                        _zxml[_zlst.index(pic)]
                                    )
                                ))
                            for _p in _lst_zpt:
                                _p.start()
                            self.mainUI.toPrint('=%s= %s pic>>> %s (%d/%d) ' % (str(datetime.datetime.now()), line, car, _train.car.index(car) + 1, len(
                                _train.car)))
                        if not car.Priority:
                            if (line == 'sx' and self.lineMode != CONSTVALUES.LINE_MODE_1L2D) or (
                                    _direction == 'forward' and self.lineMode == CONSTVALUES.LINE_MODE_1L2D):
                                self.sx_current_index = _index
                            elif (line == 'xx' and self.lineMode != CONSTVALUES.LINE_MODE_1L2D) or (
                                    _direction == 'backward' and self.lineMode == CONSTVALUES.LINE_MODE_1L2D):
                                self.xx_current_index = _index

                if _direction == 'forward':
                    _direction = 'backward'
                else:
                    _direction = 'forward'
        except Exception as e:
            self.mainUI.toPrint('in pic > ' + repr(e))

    def processPicSocket(self, _lst, _xml):
        s = socket.socket()
        s.connect((self.picSocketIP, self.picSocketPort))
        s.send(_xml.encode(encoding='utf-8'))
        with open(_lst[1], 'rb') as _f:
            while True:
                filedata = _f.read(1024)
                if not filedata:
                    break
                s.send(filedata)
        s.close()

    def build_xml(
        self, 
        imgs,
        line_id='', 
        Type='0',
        command='Passing', 
        cam1_name='V3CM02K036', 
        cam1_sts='1',
        cam2_name='V3CC02K018',
        cam2_sts='1',
        direction='',
        traintime='',
        trainspeed='1000',
        trainlabel='',
        trainindex=''
        ):
        _r = list()
        for n in range(len(imgs)):
            _xml = ET.Element('TOEC_MSG')
            _head = ET.SubElement(_xml, 'Head')
            _h_LineID = ET.SubElement(_head, 'LineID')
            _h_LineID.text = line_id
            _h_Type = ET.SubElement(_head, 'Type')
            _h_Type.text = Type
            _h_Command = ET.SubElement(_head, 'Command')
            _h_Command.text = command
            _h_Camera1 = ET.SubElement(_head, 'Camera')
            _h_Camera1_Name = ET.SubElement(_h_Camera1, 'Name')
            _h_Camera1_Name.text = cam1_name
            _h_Camera1_Status = ET.SubElement(_h_Camera1, 'Status')
            _h_Camera1_Status.text = cam1_sts
            _h_Camera2 = ET.SubElement(_head, 'Camera')
            _h_Camera2_Name = ET.SubElement(_h_Camera2, 'Name')
            _h_Camera2_Name.text = cam2_name
            _h_Camera2_Status = ET.SubElement(_h_Camera2, 'Status')
            _h_Camera2_Status.text = cam2_sts
            _h_BodyLen = ET.SubElement(_head, 'BodyLen')
            _body = ET.SubElement(_xml, 'Body')
            _b_Direction = ET.SubElement(_body, 'Direction')
            _b_Direction.text = direction
            _b_TrainTime = ET.SubElement(_body, 'TrainTime')
            _b_TrainTime.text = traintime
            _b_TrainSpeed = ET.SubElement(_body, 'TrainSpeed')
            _b_TrainSpeed.text = trainspeed
            _b_TrainLabel = ET.SubElement(_body, 'TrainLabel')
            _b_TrainLabel.text = trainlabel
            _b_TrainIndex = ET.SubElement(_body, 'TrainIndex')
            _b_TrainIndex.text = trainindex
                # ['R', 'xxx.jpg']
            _b_Image = ET.SubElement(_body, 'Image')
            _b_Image_Fix = ET.SubElement(_b_Image, 'Fix')
            _b_Image_Fix.text = imgs[n][0]
            _info = self._get_pic_info(imgs[n][1])
            _b_Image_Width = ET.SubElement(_b_Image, 'Width')
            _b_Image_Width.text = str(_info[0])
            _b_Image_Height = ET.SubElement(_b_Image, 'Height')
            _b_Image_Height.text = str(_info[1])
            _b_Image_Name = ET.SubElement(_b_Image, 'Name')
            _b_Image_Name.text = '%s%s_%s.jpg' % (imgs[n][0], str(trainindex).zfill(3), str(trainindex))
            _b_Image_Size = ET.SubElement(_b_Image, 'Size')
            _b_Image_Size.text = str(_info[2])
            _h_BodyLen.text = str(len(ET.tostring(_body, encoding='unicode')))
            _r.append('<?xml version="1.0" encoding="UTF-8"?>' + ET.tostring(_xml, encoding='unicode'))
        return _r
        

    def start(self):
        if self._startThread is None or not self._startThread.is_alive():
            self.STOP = False
            self._startThread = threading.Thread(target=self._start)
            self._startThread.start()

    # todo 需要重写启动逻辑，包括socketserver
    def _start(self):
        while 1:
            try:
                for _case in self.casePool:
                    case = self.case_mgr[_case]
                    self.start_init()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    _sx_case = copy.deepcopy(case)
                    _xx_case = copy.deepcopy(case)
                    tasks = [
                        self.serialSrv('sx', _sx_case),
                        self.serialSrv('xx', _xx_case),
                        self.picSrv('sx', _sx_case),
                        self.picSrv('xx', _xx_case)
                    ]
                    loop.run_until_complete(asyncio.wait(tasks))
                    loop.close()
                if self.loopMode == CONSTVALUES.LOOP_MODE_NO or self.STOP:
                    break
            except Exception as e:
                self.mainUI.toPrint(repr(e))
                continue

    def start_init(self):
        try:
            if not self.sx_serial.isOpen():
                self.sx_serial.open()
            if not self.xx_serial.isOpen():
                self.xx_serial.open()
        except Exception as e:
            self._serialReg()
            self.sx_serial.open()
            self.xx_serial.open()

    def serial_init(self):
        try:
            self.sx_serial = serial.Serial(
                port='COM10', baudrate=38400)
            self.xx_serial = serial.Serial(
                port='COM12', baudrate=38400)
        except Exception as e:
            self._regSerial()
            self.sx_serial = serial.Serial(
                port='COM10', baudrate=38400)
            self.xx_serial = serial.Serial(
                port='COM12', baudrate=38400)

    #
    # def _findPorts(self, port1, port2):
    #     _rootkey = 'SYSTEM\CurrentControlSet\Services'
    #     _keypair1 = 'COM' + str(int(port1)) + 'COM' + str(int(port1) + 10)
    #     _keypair2 = 'COM' + str(int(port2)) + 'COM' + str(int(port2) + 10)
    #     key1 = r'%s\VSBC8\Ports\%s' % (_rootkey, _keypair1)
    #     key2 = r'%s\VSBC8\Ports\%s' % (_rootkey, _keypair2)
    #     try:
    #         port1_root = winreg.OpenKey(
    #             winreg.HKEY_LOCAL_MACHINE, key1, access=winreg.KEY_ALL_ACCESS)
    #     except FileNotFoundError:
    #         return 1
    #     try:
    #         port2_root = winreg.OpenKey(
    #             winreg.HKEY_LOCAL_MACHINE, key2, access=winreg.KEY_ALL_ACCESS)
    #     except FileNotFoundError:
    #         return 2
    #     return 0
    #
    # def _clearSerialPorts(self):
    #     _rootkey = r'SYSTEM\CurrentControlSet\Services'
    #     try:
    #         root = winreg.OpenKey(
    #             winreg.HKEY_LOCAL_MACHINE, _rootkey + r'\VSBC9', access=winreg.KEY_ALL_ACCESS)
    #         winreg.DeleteKey(root, 'Ports')
    #     except:
    #         pass
    #
    # def _createRegisterKey(self, port1, port2):
    #     """
    #     系统注册表中添加虚拟串口配置
    #     """
    #     #winreg.LoadKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services\VSBC8', 'root.reg')
    #     _rootkey = r'SYSTEM\CurrentControlSet\Services'
    #     try:
    #         root = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, _rootkey + r'\VSBC9', winreg.KEY)
    #         # root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _rootkey + r'\VSBC9', 0, (winreg.KEY_WOW64_32KEY+winreg.KEY_ALL_ACCESS))
    #     except Exception as e:
    #         _root = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, _rootkey, winreg.KEY_SET_VALUE)
    #         # _root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _rootkey, 0, (winreg.KEY_WOW64_32KEY+winreg.KEY_ALL_ACCESS))
    #
    #         root = winreg.CreateKey(
    #             _root, 'VSBC9')
    #
    #     try:
    #
    #         # winreg.SetValue(root, 'DisplayName', winreg.REG_SZ, '')
    #         winreg.SetValueEx(root, 'ErrorControl', 0,
    #                           winreg.REG_DWORD, 0x00000001)
    #         winreg.SetValueEx(root, 'ForceFifoEnable', 0,
    #                           winreg.REG_DWORD, 0x00000001)
    #         winreg.SetValue(root, 'Group', winreg.REG_SZ, 'Extended Base')
    #         winreg.SetValueEx(root, 'ImagePath', 0,
    #                           winreg.REG_EXPAND_SZ, 'system32\DRIVERS\evsbc9.sys')
    #         winreg.SetValueEx(root, 'LogFifo', 0, winreg.REG_DWORD, 0x00000000)
    #         winreg.SetValueEx(root, 'RxFIFO', 0, winreg.REG_DWORD, 0x00000008)
    #         winreg.SetValueEx(root, 'Start', 0, winreg.REG_DWORD, 0x00000003)
    #         winreg.SetValueEx(root, 'Tag', 0, winreg.REG_DWORD, 0x00000017)
    #         winreg.SetValueEx(root, 'TxFIFO', 0, winreg.REG_DWORD, 0x0000000e)
    #         winreg.SetValueEx(root, 'Type', 0, winreg.REG_DWORD, 0x00000001)
    #
    #         _enum = winreg.CreateKey(root, 'Enum')
    #         winreg.SetValueEx(_enum, '0', 0, winreg.REG_SZ, r'Root\SYSTEM\0001')
    #         winreg.SetValueEx(_enum, 'Count', 0, winreg.REG_DWORD, 0x00000001)
    #         winreg.SetValueEx(_enum, 'NextInstance', 0,
    #                           winreg.REG_DWORD, 0x00000001)
    #
    #         _ports = winreg.CreateKey(root, 'Ports')
    #
    #         _pair1 = winreg.CreateKey(
    #             _ports, 'COM' + str(port1) + 'COM' + str(int(port1) + 10))
    #         winreg.SetValueEx(_pair1, 'Port1', 0,
    #                           winreg.REG_SZ, 'COM' + str(port1))
    #         winreg.SetValueEx(_pair1, 'Port2', 0, winreg.REG_SZ,
    #                           'COM' + str(int(port1) + 10))
    #         winreg.SetValueEx(_pair1, 'StictBaudrate', 0, winreg.REG_DWORD, 0)
    #         winreg.SetValueEx(_pair1, 'COM-Name-Arbiter1', 0, winreg.REG_DWORD, 0)
    #         winreg.SetValueEx(_pair1, 'COM-Name-Arbiter2', 0, winreg.REG_DWORD, 0)
    #         winreg.SetValueEx(_pair1, 'UserSession', 0, winreg.REG_SZ, '')
    #
    #         _pair2 = winreg.CreateKey(
    #             _ports, 'COM' + str(port2) + 'COM' + str(int(port2) + 10))
    #         winreg.SetValueEx(_pair2, 'Port1', 0,
    #                           winreg.REG_SZ, 'COM' + str(port2))
    #         winreg.SetValueEx(_pair2, 'Port2', 0, winreg.REG_SZ,
    #                           'COM' + str(int(port2) + 10))
    #         winreg.SetValueEx(_pair2, 'StictBaudrate', 0, winreg.REG_DWORD, 0)
    #         winreg.SetValueEx(_pair2, 'COM-Name-Arbiter1', 0, winreg.REG_DWORD, 0)
    #         winreg.SetValueEx(_pair2, 'COM-Name-Arbiter2', 0, winreg.REG_DWORD, 0)
    #         winreg.SetValueEx(_pair2, 'UserSession', 0, winreg.REG_SZ, '')
    #     except Exception as e:
    #         winreg.CloseKey(root)
    #

    def _regSerial(self):
        os.system('reg.exe')

    def _serialReg(self):
        os.system('vs.exe')


class departTCPHandler(socketserver.BaseRequestHandler):
    """
    %%P%% =>
    %%I%% =>
    %%T%% =>
    server.data => 服务器与客户端间通信
    """
    def handle(self):
        pass

class departThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def __init__(self, server_address, RequestHandlerClass, data):
        super(departThreadedTCPServer, self).__init__(server_address, RequestHandlerClass)
        self.data = data



class script_generator():
    def __init__(self):
        pass

class sender():
    def __init__(self):
        pass

    def handle(self):
        """
        处理脚本
        :return:
        """
        pass

    def generate_server(self):
        pass

class receiver:
    pass

class data_handler:
    pass


#
# def _ui():
#     app = QtWidgets.QApplication(sys.argv)
#     mw = QtWidgets.QMainWindow()
#     ui_1103 = ui1103.Ui_Form()
#     # ui = UI()
#     # ui.setupUi(mw)
#     # mw.show()
#     ui_1103.setupUi(mw)
#     mw.show()
#     sys.exit(app.exec_())

# def boot(argv):
#     """
#     -a --autotest > 自动化测试模式
#     -t --test > 自检模式
#     -p --port > 设置socket端口
#     -c --com > 设置串口设备号
#     -l --loop > 设置循环模式 0：不循环 1：单线循环 2：场景循环
#
#     :param argv:
#     :return:
#     """
#     argc = len(argv)
#     loop = 0
#     mode = 'serial'
#     port = 5006, 5007
#     com = 1, 2
#     if argc == 1:
#         # m = main()
#         _ui()
#     else:
#
#         if '-l' in argv:
#             try:
#                 loop = int(argv[argv.index('-l') + 1])
#             except IndexError:
#                 print('-l 缺少参数')
#             except ValueError:
#                 print('-l 参数应为数字')
#         if '-m' in argv:
#             try:
#                 mode = str(argv[argv.index('-m') + 1])
#             except IndexError:
#                 print('-m 缺少参数')
#             except ValueError:
#                 print('-m 参数应为字符')
#         if '-p' in argv:
#             try:
#                 port = int(argv[argv.index('-p') + 1]
#                            ), int(argv[argv.index('-p') + 2])
#             except IndexError:
#                 print('-p 缺少参数')
#             except ValueError:
#                 print('-p 参数应为数字')
#         if '-c' in argv:
#             try:
#                 com = int(argv[argv.index('-c') + 1]
#                           ), int(argv[argv.index('-c') + 2])
#             except ValueError:
#                 print('-c 参数应为数字')
#             except IndexError:
#                 print('-c 缺少参数')
#         if '-n' in argv:  # 无ui模式
#             if mode == 'serial':
#                 # _default = default(mode, loop, com)
#                 pass
#             if mode == 'socket':
#                 # _default = default(mode, loop, port)
#                 pass
#         if '-v' in argv:  # 自检模式
#             pass
#
# if __name__ == '__main__':
#     boot(argv=sys.argv)
