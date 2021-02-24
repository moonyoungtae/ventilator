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

import timeOut as to

form_class = uic.loadUiType("gui.ui")[0]
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

#speed: rpm, pos: degree, => rotation time(sec)=pos/(360*speed/60)
speed=0
modeNum=-1
mode=[10,20,30,40]
startPos=0.0
currentPos=0.0
targetPos=180.0
stopped=True
exited=False

class mainWindow(QMainWindow,form_class,QWidget):
    def __init__(self):
        super().__init__()
        self.thread_stop = Thread_stop()
        self.thread_move=Thread_move()
        self.thread_init=Thread_init()
        self.initial_settings=Setting()
        self.changed_settings=Setting()
        self.setupUi(self)
        self.statusBar().showMessage('Ready')
        self.setWindowTitle('Ventilator')
        self.setWindowIcon(QIcon('ven.png'))

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
        self.slider.valueChanged.connect(self.setSpeed)
        self.thread_move.start()

        self.pos_kp_slider.valueChanged.connect(
            lambda: self.changed_settings.setControler(self.pos_kp_slider.value(), 0, True,self))
        self.pos_ki_slider.valueChanged.connect(
            lambda: self.changed_settings.setControler(self.pos_ki_slider.value(), 1, True,self))
        self.pos_kd_slider.valueChanged.connect(
            lambda: self.changed_settings.setControler(self.pos_kd_slider.value(), 2, True,self))
        self.speed_kp_slider.valueChanged.connect(
            lambda: self.changed_settings.setControler(self.speed_kp_slider.value(), 0, False,self))
        self.speed_ki_slider.valueChanged.connect(
            lambda: self.changed_settings.setControler(self.speed_ki_slider.value(), 1, False,self))
        self.speed_kd_slider.valueChanged.connect(
            lambda: self.changed_settings.setControler(self.speed_kd_slider.value(), 2, False,self))

        self.set_start.clicked.connect(lambda: self.changed_settings.setStart(self))
        self.set_end.clicked.connect(lambda: self.changed_settings.setEnd(self))
        self.move_cw.pressed.connect(lambda: sc.speed_control(5,0.5,True))
        self.move_ccw.pressed.connect(lambda: sc.speed_control(5,0.5,False))
        self.move_cw.released.connect(stop_imm)
        self.move_ccw.released.connect(stop_imm)

        self.apply_setting.clicked.connect(self.changeSetting)
        self.init_setting.clicked.connect(self.initSettings)

        sc.setPostionControlMode(False)
        pos_con=sc.getFeedback(3)
        speed_con=sc.getFeedback(4)
        print(pos_con)
        print(speed_con)

        self.pos_kp_slider.setValue(pos_con[0])
        self.pos_ki_slider.setValue(pos_con[1])
        self.pos_kd_slider.setValue(pos_con[2])

        self.speed_kp_slider.setValue(speed_con[0])
        self.speed_ki_slider.setValue(speed_con[1])
        self.speed_kd_slider.setValue(speed_con[2])

        self.pos_kp_lcd.display(pos_con[0])
        self.pos_ki_lcd.display(pos_con[1])
        self.pos_kd_lcd.display(pos_con[2])

        self.speed_kp_lcd.display(speed_con[0])
        self.speed_ki_lcd.display(speed_con[1])
        self.speed_kd_lcd.display(speed_con[2])

    def closeEvent(self, e):
        pass

    def setSpeed(self,val):
        global speed
        self.slider.setValue(int(val))
        self.lcd_speed.display(int(val))
        #mainWindow.textBox.setText(str(val))
        print("setted")
        speed=int(val)

    @to.timeout(0.5)
    def getValue(self):
        global currentPos
        pos, speed = sc.getFeedback(1)
        currentPos = pos
        return pos

    def setMode(self,num):
        if(not stopped):
            self.thread_stop.start()
            time.sleep(0.5)
            self.thread_init.start()
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

    def initSettings(self):
        global startPos
        global targetPos
        reply = QMessageBox.question(self, "Initialize Settings", "Do you want to initialize settings?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if (reply == QMessageBox.Yes):
            startPos = self.initial_settings.start
            targetPos = self.initial_settings.end
            sc.setGains(self.initial_settings.pos_controler, True)
            sc.setGains(self.initial_settings.speed_controler, False)

            pos_con = sc.getFeedback(3)
            speed_con = sc.getFeedback(4)

            self.pos_kd_slider.setValue(pos_con[0])
            self.pos_ki_slider.setValue(pos_con[1])
            self.pos_kd_slider.setValue(pos_con[2])

            self.speed_kd_slider.setValue(speed_con[0])
            self.speed_ki_slider.setValue(speed_con[1])
            self.speed_kd_slider.setValue(speed_con[2])

            self.pos_kp_lcd.display(pos_con[0])
            self.pos_ki_lcd.display(pos_con[1])
            self.pos_kd_lcd.display(pos_con[2])

            self.speed_kp_lcd.display(speed_con[0])
            self.speed_ki_lcd.display(speed_con[1])
            self.speed_kd_lcd.display(speed_con[2])

            QMessageBox.information(self, "Initialized", "Settings Initialized")


    def changeSetting(self):
        global startPos
        global targetPos
        reply = QMessageBox.question(self, "Apply Settings", "Do you want to apply changed settings?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if(reply==QMessageBox.Yes):
            startPos = self.changed_settings.start
            targetPos = self.changed_settings.end
            sc.setGains(self.changed_settings.pos_controler, True)
            sc.setGains(self.changed_settings.speed_controler, False)
            print(startPos,targetPos)
            QMessageBox.information(self,"Applied","Changed Settings Applied")


class Thread_move(QtCore.QThread):
    def __init__(self,parent = None):
        super(Thread_move,self).__init__(parent)
    def run(self):
        currentDir=False
        while (exited):
            time.sleep(0.1)
            if (speed != 0 and not stopped):
                pos1 = startPos
                pos2 = targetPos
                print("start moving")

                print(pos1, pos2)
                print("move")
                mov=abs(targetPos-startPos)
                while (not stopped):
                    currentDir = not currentDir
                    print("move")
                    print(currentDir)
                    sc.pos_control( pos2, abs(mov /(6*speed)),currentDir)

                    time.sleep(abs(mov /(6*speed)))
                    if (stopped):
                        break

                    currentDir = not currentDir
                    print("move")
                    print(currentDir)
                    sc.pos_control( pos1, abs(mov /(6*speed)),currentDir)
                    time.sleep(abs(mov /(6*speed)))
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
        stop_imm()
        global stopped
        global currentPos
        if (not stopped):
            stopped = True
            sc.pos_control(startPos, abs((startPos - currentPos) / (6 * 5)), False)
            time.sleep(abs((startPos - currentPos) / (6 * 5)))
            currentPos = startPos

class Thread_init(QtCore.QThread):
    def __init__(self,parent = None):
        super(Thread_init,self).__init__(parent)

    def run(self):
        global stopped
        global currentPos
        if(stopped):
            stopped=True
            sc.pos_control(startPos, abs((startPos-currentPos)/ (6 * 5)), False)
            time.sleep(abs((startPos-currentPos)/ (6 * 5)))
            currentPos = startPos
            stop()

class Setting():
    def __init__(self):
        self.start=0
        self.end=0
        self.pos_controler=[254,0,0]
        self.speed_controler=[254,0,0]

    def setStart(self,main):
        try:
            pos = main.getValue()
        except Exception as e:
            print("timout occur", str(e))
            QMessageBox.information(main,"Error", "Time out, Try again!!")
            return
        QMessageBox.information(main,"Success", "Start Position Setted")
        self.start = pos

    def setEnd(self,main):
        try:
            pos = main.getValue()
        except Exception as e:
            print("timout occur", str(e))
            QMessageBox.information(main,"Error", "Time out, Try again!!")
            return
        QMessageBox.information(main,"Success", "End Position Setted")
        self.end = pos

    def setControler(self,val,gainType,type,main):
        # true: pos, false: speed
        if(type):
            self.pos_controler[gainType]=val
            if(gainType==0):
                main.pos_kp_lcd.display(main.pos_kp_slider.value())
                print(main.pos_kd_slider.value())
            elif(gainType==1):
                main.pos_ki_lcd.display(main.pos_ki_slider.value())
            else:
                main.pos_kd_lcd.display(main.pos_kd_slider.value())

        else:
            self.speed_controler[gainType]=val
            if (gainType == 0):
                main.speed_kp_lcd.display(main.speed_kp_slider.value())
            elif (gainType == 1):
                main.speed_ki_lcd.display(main.speed_ki_slider.value())
            else:
                main.speed_kd_lcd.display(main.speed_kd_slider.value())


def stop_imm():
    global currentPos
    global stopped
    if (not stopped):
        stopped = True
    print("----")
    try:
        pos=sc.getPos()
        currentPos = pos
    except Exception as e:
        print("timout occur", str(e))
    sc.speed_control(0, 0.1, True)



def stop():
    global currentPos
    global stopped
    if (not stopped):
        stopped = True
    print("----")
    try:
        pos=sc.getPos()
        currentPos = pos
    except Exception as e:
        print("timout occur", str(e))
    print("stopped")
    time.sleep(0.5)
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



