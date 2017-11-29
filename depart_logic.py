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
    def __init__(self, _name):
        self.name = _name
        self.items = list()

    def add_item(self, _item):
        self.items.append(_item)

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

    def get_serial(self):
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

class Line():
    def __init__(self, _name):
        self.name = _name
        self.IP = None
        self.ZIP = None
        self.items = list()

    def set_z_ip(self, _ip):
        self.ZIP = _ip

    def set_ip(self, _ip):
        self.IP = _ip

    def add_item(self, _item):
        self.items.append(_item)

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


    def serial_write_data(self, serial, _data):
        #   单行数据
        serial.write(bytes.fromhex('02'))
        for _c in _data:
            serial.write(_c.encode(encoding='utf-8'))
        serial.write(bytes.fromhex('03'))

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


