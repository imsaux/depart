from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog
from depart_logic import *
import ui1103
import loadDialog
import sys

class _ui1103(ui1103.Ui_Form):
    def __init__(self, _form):
        super(_ui1103, self).setupUi(_form)

        self._form = _form
        self._logic = logic()
        self.lastOpen = None
        self.lastOpenCol = None

        self.setDefaultValue()
        self.setSingleAndSlot()

    def setSingleAndSlot(self):
        self.toolButton.clicked.connect(self.openFile)
        self.toolButton_2.clicked.connect(self.openFile)
        self.toolButton_3.clicked.connect(self.openFile)
        self.toolButton_4.clicked.connect(self.openFile)

        # self.vsb_sx = QtWidgets.QScrollBar(self.gridLayoutWidget)
        # self.vsb_sx.setOrientation(QtCore.Qt.Vertical)
        # self.vsb_sx.setObjectName("vsb_sx")
        # self.trChooseCase.setVerticalScrollBar(self.verticalScrollBar)
        # self.trSX.setVerticalScrollBar(self.vsb_sx)
        # self.tr_new_case_xx.setVerticalScrollBar(self.vsb_new_case_xx)
        # self.tr_new_train.setVerticalScrollBar(self.verticalScrollBar_2)

        self.trChooseCase.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.trChooseCase.customContextMenuRequested.connect(self.showMenu)

        self.trSX.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.trSX.customContextMenuRequested.connect(self.showMenu)
        self.trXX.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.trXX.customContextMenuRequested.connect(self.showMenu)

        self.trSX.itemDoubleClicked.connect(self.trDbClicked)
        self.trSX.itemSelectionChanged.connect(self.trSelectChg)
        self.trXX.itemDoubleClicked.connect(self.trDbClicked)
        self.trXX.itemSelectionChanged.connect(self.trSelectChg)

        self.btSaveSetting.clicked.connect(self.saveOptions)

    def trDbClicked(self, item, col):
        if col != 0:
            self._form.sender().openPersistentEditor(item, col)
            self.lastOpen = item
            self.lastOpenCol = col

    def trClicked(self, item, col):
        if col == 0 and self.lastOpen is not None:
            self._form.sender().closePersistentEditor(self.lastOpen, self.lastOpenCol)
            self.lastOpen = None
            self.lastOpenCol = None

    def trSelectChg(self):
        if self.lastOpen is not None:
            self._form.sender().closePersistentEditor(self.lastOpen, self.lastOpenCol)
            self.lastOpen = None
            self.lastOpenCol = None

    def openFile(self):
        import os.path
        try:
            _filePath, filetype = QFileDialog.getOpenFileName(self._form,
                                                              "选取文件",
                                                              "C:/",
                                                              "全部 (*);;图像 (*.jpg)")

            if self._form.sender().objectName() == 'toolButton':
                self.txtLeftImage.setText(os.path.normpath(_filePath))
            if self._form.sender().objectName() == 'toolButton_2':
                self.txtRightImage.setText(os.path.normpath(_filePath))
            if self._form.sender().objectName() == 'toolButton_3':
                self.txtLeftWheelImage.setText(os.path.normpath(_filePath))
            if self._form.sender().objectName() == 'toolButton_4':
                self.txtRightWheelImage.setText(os.path.normpath(_filePath))
        except Exception as e:
            self.lstInfo.addItem(repr(e))

    def setDefaultValue(self):
        self.txtFreeTime.setText('30')
        self.txtSXIP.setText('202.202.202.2')
        self.txtXXIP.setText('202.202.202.3')
        self.txtSXWheelIP.setText('202.202.202.4')
        self.txtXXWheelIP.setText('202.202.202.5')
        self.txtImageTransportIP.setText(CONSTVALUES.LOCAL_IP)
        self.txtImageTransportPort.setText('9999')

    def saveOptions(self):
        self._logic.setSocketIP(self.txtImageTransportIP.text())
        self._logic.setSocketPort(int(self.txtImageTransportPort.text()))
        self._logic.setSxIP(self.txtSXIP.text())
        self._logic.setXxIP(self.txtXXIP.text())
        self._logic.setSxZIP(self.txtSXWheelIP.text())
        self._logic.setXxZIP(self.txtXXWheelIP.text())
        self._logic.setFreeTime(int(self.txtFreeTime.text()))
        self.lstInfo.addItem('首选项参数已保存！')

    def showDialog(self):
        try:
            _d = QtWidgets.QDialog()
            _ui = _load_dialog(self, _d)
            _d.show()
            _d.exec_()
        except Exception as e:
            self.lstInfo.addItem(repr(e))

    def deleteItem(self):
        try:
            if self.lastRightSender.objectName() == 'trChooseCase':
                _item = self.lastRightSender.takeItem(self.lastRightSender.row(self.lastRightSender.currentItem()))
                item = self.lastRightSender.itemWidget(_item)
                self.lastRightSender.removeItemWidget(item)
            else:
                root = self.lastRightSender.invisibleRootItem()

                for item in self.lastRightSender.selectedItems():
                    (item.parent() or root).removeChild(item)
        except Exception as e:
            self.lstInfo.addItem(repr(e))

    def showMenu(self):
        try:
            _sender = self._form.sender()
            self.lastRightSender = _sender
            _rightMenu = QtWidgets.QMenu(_sender)
            _action_1 = _rightMenu.addAction(u'添加线路')
            _action_2 = _rightMenu.addAction(u'添加车厢')
            _action_3 = _rightMenu.addAction(u'删除')
            _action_1.triggered.connect(self.showDialog)
            _action_2.triggered.connect(self.showDialog)
            _action_3.triggered.connect(self.deleteItem)
            _rightMenu.exec_(QtGui.QCursor.pos())
            self.lastRightSender = None
        except Exception as e:
            self.lstInfo.addItem(repr(e))

class _load_dialog(loadDialog.LoadDialog):
    def __init__(self, caller, p):
        super(_load_dialog, self).__init__()
        super().setupUi(p)
        self.ui = p
        self.caller = caller
        self.pushButton_2.clicked.connect(self._ok)
        self.pushButton.clicked.connect(self._cancel)
        if self.caller.lastRightSender.objectName() == 'trChooseCase':
            self._type = CONSTVALUES.DATA_TYPE_CASE
        elif self.caller.lastRightSender.objectName() == 'trSX':
            self._type = CONSTVALUES.DATA_TYPE_CARRIAGE
        elif self.caller.lastRightSender.objectName() == 'trXX':
            self._type = CONSTVALUES.DATA_TYPE_CARRIAGE

        # self.data_init()


    def _ok(self):
        try:
            if self.caller.lastRightSender.objectName() == 'trChooseCase':
                for i in range(self.listView_2.count()):
                    _item = self.listView_2.takeItem(0).text()
                    _case = self.caller._logic.case_mgr[_item]
                    _root = QtWidgets.QListWidgetItem(self.eventSender.lastRightSender)
                    _root.setText(str(_case.name))
                    self.caller.lastRightSender.addItem(_root)

            elif self.caller.lastRightSender.objectName() in ['trSX', 'trXX']:
                _count = self.caller.lastRightSender.topLevelItemCount()
                _insertPos = -1
                if len(self.caller.lastRightSender.selectedItems()) > 0:
                    _insertPos = self.caller.lastRightSender.indexOfTopLevelItem(self.caller.lastRightSender.selectedItems()[0])
                for i in range(self.listView_2.count()):
                    _item = self.listView_2.takeItem(0).text()
                    _car = self.caller._logic.car_mgr[_item]
                    _root = QtWidgets.QTreeWidgetItem()
                    
                    _root.setText(0, str(_car.kind))
                    _root.setText(1, str(_car.length))
                    _root.setText(2, '100')
                    _root.setText(3, UTIL.getCode(str(_car.kind), _count + i))
                    _root.setCheckState(4, QtCore.Qt.Checked)
                    _root.setText(5, str(_car.info))
                    if _insertPos > -1:
                        self.caller.lastRightSender.insertTopLevelItem(_insertPos, _root)
                    else:
                        self.caller.lastRightSender.addTopLevelItem(_root)
        except Exception as e:
            self.lstInfo.addItem(repr(e))
        finally:
            self._cancel()

    def _cancel(self):
        self.ui.close()

    def itemDbClick(self):
        if self.sender().objectName() == 'listView':
            try:
                _item = self.sender().currentItem().text()
                self.listView_2.addItem(_item)
            except Exception as e:
                self.lstInfo.addItem(repr(e))
        elif self.sender().objectName() == 'listView_2':
            try:
                _item = self.listView_2.takeItem(self.listView_2.currentRow())
                _item = None
            except Exception as e:
                self.lstInfo.addItem(repr(e))

    def data_init(self):
        if self._type == CONSTVALUES.DATA_TYPE_CASE:
            try:
                for _case in list(self.eventSender.logic.case_mgr.keys()):
                    _item = QtWidgets.QListWidgetItem(_case)
                    self.listView.addItem(_item)
            except Exception as e:
                self.lstInfo.addItem(repr(e))
        elif self._type == CONSTVALUES.DATA_TYPE_CARRIAGE:
            try:
                for _car in list(self.eventSender.logic.car_mgr.keys()):
                    _item = QtWidgets.QListWidgetItem(_car)
                    self.listView.addItem(_item)
            except Exception as e:
                self.lstInfo.addItem(repr(e))

class LoadDialog(QtWidgets.QDialog):
    def __init__(self, _sender, parent=None):
        try:
            super(LoadDialog, self).__init__(parent)
            self.eventSender = _sender
            if self.eventSender.lastRightSender.objectName() == 'trChooseCase':
                self._type = CONSTVALUES.DATA_TYPE_CASE
            elif self.eventSender.lastRightSender.objectName() == 'trSX':
                self._type = CONSTVALUES.DATA_TYPE_CARRIAGE
            elif self.eventSender.lastRightSender.objectName() == 'trXX':
                self._type = CONSTVALUES.DATA_TYPE_CARRIAGE
        except Exception as e:
            self.lstInfo.addItem(repr(e))

    def setupUi(self, Dialog):
        self.ui = Dialog
        Dialog.setObjectName("Dialog")
        Dialog.resize(471, 409)
        self.horizontalLayoutWidget = QtWidgets.QWidget(Dialog)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(10, 30, 451, 321))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.listView = QtWidgets.QListWidget(self.horizontalLayoutWidget)
        self.listView.setObjectName("listView")
        self.horizontalLayout.addWidget(self.listView)
        self.verticalScrollBar = QtWidgets.QScrollBar(self.horizontalLayoutWidget)
        self.verticalScrollBar.setOrientation(QtCore.Qt.Vertical)
        self.verticalScrollBar.setObjectName("verticalScrollBar")
        self.horizontalLayout.addWidget(self.verticalScrollBar)
        self.listView_2 = QtWidgets.QListWidget(self.horizontalLayoutWidget)
        self.listView_2.setObjectName("listView_2")
        self.horizontalLayout.addWidget(self.listView_2)
        self.verticalScrollBar_2 = QtWidgets.QScrollBar(self.horizontalLayoutWidget)
        self.verticalScrollBar_2.setOrientation(QtCore.Qt.Vertical)
        self.verticalScrollBar_2.setObjectName("verticalScrollBar_2")
        self.horizontalLayout.addWidget(self.verticalScrollBar_2)
        self.horizontalLayoutWidget_2 = QtWidgets.QWidget(Dialog)
        self.horizontalLayoutWidget_2.setGeometry(QtCore.QRect(10, 360, 451, 41))
        self.horizontalLayoutWidget_2.setObjectName("horizontalLayoutWidget_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_2)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pushButton_2 = QtWidgets.QPushButton(self.horizontalLayoutWidget_2)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout_2.addWidget(self.pushButton_2)
        self.pushButton = QtWidgets.QPushButton(self.horizontalLayoutWidget_2)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_2.addWidget(self.pushButton)
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(91, 10, 41, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(320, 10, 31, 16))
        self.label_2.setObjectName("label_2")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "数据加载"))
        self.pushButton_2.setText(_translate("Dialog", "确定"))
        self.pushButton.setText(_translate("Dialog", "取消"))
        self.label.setText(_translate("Dialog", "数据源"))
        self.label_2.setText(_translate("Dialog", "目标"))
        self.listView.itemDoubleClicked.connect(self.itemDbClick)
        self.listView_2.itemDoubleClicked.connect(self.itemDbClick)
        self.pushButton_2.clicked.connect(self._ok)
        self.pushButton.clicked.connect(self._cancel)
        self.data_init()

def _ui():
    app = QtWidgets.QApplication(sys.argv)
    mw = QtWidgets.QMainWindow()
    ui_1103 = _ui1103(mw)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
    mw.show()
    sys.exit(app.exec_())

def boot(argv):
    """
    -a --autotest > 自动化测试模式
    -t --test > 自检模式
    -p --port > 设置socket端口
    -c --com > 设置串口设备号
    -l --loop > 设置循环模式 0：不循环 1：单线循环 2：场景循环

    :param argv:
    :return:
    """
    argc = len(argv)
    loop = 0
    mode = 'serial'
    port = 5006, 5007
    com = 1, 2
    if argc == 1:
        # m = main()
        _ui()
    else:

        if '-l' in argv:
            try:
                loop = int(argv[argv.index('-l') + 1])
            except IndexError:
                print('-l 缺少参数')
            except ValueError:
                print('-l 参数应为数字')
        if '-m' in argv:
            try:
                mode = str(argv[argv.index('-m') + 1])
            except IndexError:
                print('-m 缺少参数')
            except ValueError:
                print('-m 参数应为字符')
        if '-p' in argv:
            try:
                port = int(argv[argv.index('-p') + 1]
                           ), int(argv[argv.index('-p') + 2])
            except IndexError:
                print('-p 缺少参数')
            except ValueError:
                print('-p 参数应为数字')
        if '-c' in argv:
            try:
                com = int(argv[argv.index('-c') + 1]
                          ), int(argv[argv.index('-c') + 2])
            except ValueError:
                print('-c 参数应为数字')
            except IndexError:
                print('-c 缺少参数')
        if '-n' in argv:  # 无ui模式
            if mode == 'serial':
                # _default = default(mode, loop, com)
                pass
            if mode == 'socket':
                # _default = default(mode, loop, port)
                pass
        if '-v' in argv:  # 自检模式
            pass

if __name__ == '__main__':
    boot(argv=sys.argv)
