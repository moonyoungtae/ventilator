#참고: http://blog.naver.com/PostView.nhn?blogId=kcal2845&logNo=221098528877
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import numpy as np
from multiprocessing import Process

timeOut=True
# 스코프 클래스 정의
class Scope(object):

    # 초기 설정
    def __init__(self,
                 ax, fn,
                 title='', xlabel='time', ylabel='flowrate'):
        self.y=0.0
        self.fn=fn
        self.ax =ax
        self.line, = ax.plot([], [], lw=2)

        self.max_points = 50
        self.line, = self.ax.plot(np.arange(self.max_points),
                        np.ones(self.max_points, dtype=np.float) * np.nan, lw=2)

        # 그래프 설정
        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)

        self.ti = time.time()  # 현재시각
        print("초기화 완료")

    # 그래프 설정
    def update(self, i):
        try:
            y = self.fn()
        except Exception as e:
            print("timout occur",str(e))
            y=0.0
        old_y = self.line.get_ydata()
        new_y = np.r_[old_y[1:], y]
        self.line.set_ydata(new_y)
        return self.line,



