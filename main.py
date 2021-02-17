import sys
import time
from threading import Thread

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QMainWindow, QPushButton, QMessageBox, QApplication, QSlider
from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import numpy as np
import serialCom as sc
from graph import Scope

form_class = uic.loadUiType("gui.ui")[0]
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

speed=0
modeNum=-1
mode=[10,20,30,40]
currentPos=0
targetPos=180
stopped=True
exited=False
sc.setPostionControlMode(False)

#@to.timeout(0.5)

class mainWindow(QMainWindow,form_class,QWidget):
    def __init__(self):
        super().__init__()
        self.thread_stop = Thread_stop()
        self.thread_move=Thread_move()
        self.thread_feedback = Thread_getFeedback()

        self.setupUi(self)
        self.statusBar().showMessage('Ready')
        self.setWindowTitle('Ventilator')
        self.setWindowIcon(QIcon('ven.png'))
        #self.setGeometry(300, 200, 900, 600)  # 윈도우 위치/크기 설정
        self.fig = plt.figure()
        self.ax=plt.axes(xlim=(0, 60), ylim=(0, 360))
        self.ax.grid(True)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.timeInterval=0.01
        self.x = 0.0
        self.y = 0

        self.initUI()
        self.connectUI()

    def initUI(self):
        stop()
        self.vbox = QVBoxLayout()
        self.verticalLayout.addWidget(self.canvas)
        self.setLayout(self.verticalLayout)

        # 객체 생성
        self.scope = Scope(self.ax, self.getValue)

        # update 매소드 호출
        self.ani = animation.FuncAnimation(self.fig, self.scope.update, interval=100, blit=True,frames=10)
        self.canvas.draw()

    def connectUI(self):
        self.btn_start.clicked.connect(self.start)
        self.btn_stop.clicked.connect(self.thread_stop.start)
        self.btn_mode1.clicked.connect(lambda: self.setMode(0))
        self.btn_mode2.clicked.connect(lambda: self.setMode(1))
        self.btn_mode3.clicked.connect(lambda: self.setMode(2))
        self.btn_mode4.clicked.connect(lambda: self.setMode(3))
        self.btn_graph1.clicked.connect(lambda: self.setGraph(0))
        self.btn_graph2.clicked.connect(lambda: self.setGraph(1))
        self.btn_graph3.clicked.connect(lambda: self.setGraph(2))
        self.btn_graph4.clicked.connect(lambda: self.setGraph(3))
        self.textEdit.textChanged.connect(self.setSpeed)
        self.slider.valueChanged.connect(self.setSpeed)
        self.thread_move.start()

    def closeEvent(self, e):
        pass

    def setSpeed(self,val):
        global speed
        self.slider.setValue(int(val))
        #mainWindow.textBox.setText(str(val))
        print("setted")
        speed=int(val)

    def getValue(self):
        global currentPos
        #pos, speed = sc.getFeedback()
        #currentPos = pos
        return 30

    def setMode(self,num):
        self.thread_stop.start()
        self.setSpeed(mode[num])

    def setGraph(self,val):
        print(val)

        if(val==0):
            self.scope.ax.set_ylabel("Flow Rate")
        elif(val==1):
            self.scope.ax.set_ylabel("Pressure")
        elif (val == 2):
            self.scope.ax.set_ylabel("Position")
        elif (val == 3):
            self.scope.ax.set_ylabel("Speed")

    def start(self):
        global stopped
        if(stopped):
            stopped = False


class Thread_move(QtCore.QThread):
    def __init__(self,parent = None):
        super(Thread_move,self).__init__(parent)
    def run(self):
        currentDir=True
        while (exited):
            time.sleep(0.1)
            if (speed != 0 and not stopped):
                print("start moving")

                if(not currentDir):
                    pos1 = -currentPos
                    pos2 = targetPos-currentPos
                else:
                    pos2 = -currentPos
                    pos1 = targetPos-currentPos
                print(pos1, pos2)
                print("move")
                print(currentDir)
                sc.pos_control(pos2,abs(pos2 / (6 * speed)), currentDir)
                time.sleep(abs(pos2 / (6 * speed)))
                while (not stopped):
                    currentDir = not currentDir
                    print("move")
                    print(currentDir)
                    sc.pos_control( pos1, abs(30 / speed),currentDir)

                    time.sleep(abs(30 / speed))
                    if (stopped):
                        break

                    currentDir = not currentDir
                    print("move")
                    print(currentDir)
                    sc.pos_control( pos2, abs(30 / speed),currentDir)
                    time.sleep(abs(30 / speed))
                '''
                print("start moving")
                pos1 = -currentPos
                pos2 = targetPos - currentPos
                sc.speed_pos_control(speed, pos2, True)
                time.sleep(abs(pos2 / (6 * speed)))
                while (not stopped):
                    print("move")
                    sc.speed_pos_control(speed, pos1, False)
                    time.sleep(abs(30 / speed))
                    if (stopped):
                        break
                    sc.speed_pos_control(speed, pos2, True)
                    time.sleep(abs(30 / speed))
            '''

class Thread_stop(QtCore.QThread):
    def __init__(self,parent = None):
        super(Thread_stop,self).__init__(parent)
    def run(self):
        stop()

class Thread_getFeedback(QtCore.QThread):
    def __init__(self,parent = None):
        super(Thread_getFeedback,self).__init__(parent)
    def run(self):
        global stopped
        global currentPos
        pos, speed = sc.getFeedback()
        currentPos = pos
        print(pos)

def stop():
    global currentPos
    global stopped
    if (not stopped):
        stopped = True
    print("----")
    pos, val = sc.getFeedback()
    currentPos = pos
    print("stopped")
    sc.stop()

def ui():
    global exited
    # QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv)

    # WindowClass의 인스턴스 생성
    myWindow = mainWindow()
    # 프로그램 화면을 보여주는 코드
    myWindow.show()
    # 프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exit(app.exec_())
    print("finished")
    exited=False
    stopped=True

if __name__ == '__main__':
    exited=True
    ui()



