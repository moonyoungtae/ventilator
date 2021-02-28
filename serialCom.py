import binascii

import serial
import time
import struct
import timeOut as to


port_1 = serial.Serial("/dev/ttyUSB1", baudrate=9600, timeout=3.0)
# port_2 = serial.Serial("/dev/ttyUSB2", baudrate=9600, timeout=3.0)

slow = bytearray.fromhex("FF FE 00 07 2F 01 00 46 50 00 32")
fast = bytearray.fromhex("FF FE 00 06 98 02 01 8C A0 32")
speed_control_10 = bytearray.fromhex("FF FE 00 06 88 03 00 00 64 0A")
speed_control_25 = bytearray.fromhex("FF FE 00 06 F2 03 00 00 FA 0A")
speed_control_10_rev = bytearray.fromhex("FF FE 00 06 87 03 01 00 64 0A")
speed_control_25_rev = bytearray.fromhex("FF FE 00 06 F1 03 01 00 FA 0A")
speed_control_50 = bytearray.fromhex("FF FE 00 06 F7 03 00 01 F4 0A")
speed_control_0 = bytearray.fromhex("FF FE 00 06 EC 03 00 00 00 0A")

absolute = bytearray.fromhex("FF FE 00 03 F1 0B 00")

changeControlDir=bytearray.fromhex("FF FE 00 03 EC 0F 01")

init_pos = bytearray.fromhex("FF FE 00 02 F1 0C")

#port_1.write(bytearray.fromhex("FF FE FF 02 F1 0D"))

port_1.write(absolute)
def to_hex_string(n):
    first = n // 16
    second = n % 16
    if first == 10:
        first = 'A'
    elif first == 11:
        first = 'B'
    elif first == 12:
        first = 'C'
    elif first == 13:
        first = 'D'
    elif first == 14:
        first = 'E'
    elif first == 15:
        first = 'F'

    if second == 10:
        second = 'A'
    elif second == 11:
        second = 'B'
    elif second == 12:
        second = 'C'
    elif second == 13:
        second = 'D'
    elif second == 14:
        second = 'E'
    elif second == 15:
        second = 'F'
    return str(first) + str(second)

def hex_to_num(a=' '):
    if(a=='f' or a=='F'):
        return 15
    elif (a == 'e' or a == 'E'):
        return 14
    elif (a == 'd' or a == 'D'):
        return 13
    elif (a == 'c' or a == 'C'):
        return 12
    elif (a == 'b' or a == 'B'):
        return 11
    elif (a == 'a' or a == 'A'):
        return 10
    else:
        return int(a)

def string_to_num(l1="",l2=""):

    if(l1==""):
        num1=0
    else:
        num1 = hex_to_num(l1[0]) * 16 + hex_to_num(l1[1])
    if(l2==""):
        num2=0
    else:
        num2 = hex_to_num(l2[0]) * 16 + hex_to_num(l2[1])
    return num1*16*16+num2

def speed_to_protocol(speed):
    if speed >= 25.6:
        hex_speed_1 = int((speed * 10) // 256)
        hex_speed_2 = int((speed * 10) % 256)
        hex_speed = to_hex_string(hex_speed_1) + " " + to_hex_string(hex_speed_2) + " "
    else:
        hex_speed_1 = int(speed * 10)
        hex_speed = "00 " + to_hex_string(hex_speed_1) + " "
    return hex_speed

def time_to_protocol(t):
    return to_hex_string(int(t*10))+" "

def get_checksum(speed, pos,t=0,mode=0):
    #mode=0:pos,speed control
    #mode=1:pos control
    #mode=2: speed control

    cks_tmp = 0
    if pos >= 2.56:
        hex_pos_1 = int((pos * 100) // 256)
        hex_pos_2 = int((pos * 100) % 256)
        cks_tmp = hex_pos_2 + hex_pos_1
    else:
        hex_pos_1 = int(pos * 100)
        cks_tmp = hex_pos_1

    if speed >= 25.6:
        hex_speed_1 = int((speed * 10) // 256)
        hex_speed_2 = int((speed * 10) % 256)
        cks_tmp += (hex_speed_1 + hex_speed_2)
    else:
        hex_speed_1 = int(speed * 10)
        cks_tmp += hex_speed_1

    if(mode!=0):
        cks_tmp+=int(t*10)

    cks_value=0 # diff for protocol modes
    if(mode==0):
        cks_value=8
    elif(mode==1):
        cks_value=8
    else:
        cks_value=9
    checksum = to_hex_string(255 - (cks_tmp + cks_value) % 256) + " "
    rev_checksum = to_hex_string(255 - (cks_tmp + cks_value+1) % 256) + " "
    return checksum, rev_checksum

def pos_to_protocol(pos):
    if pos >= 2.56:
        hex_pos_1 = int((pos * 100) // 256)
        hex_pos_2 = int((pos * 100) % 256)
        hex_pos = to_hex_string(hex_pos_1) + " " + to_hex_string(hex_pos_2) + " "
    else:
        hex_pos_1 = int(pos * 100)
        hex_pos = "00 " + to_hex_string(hex_pos_1) + " "
    return hex_pos

def pos_control(pos,t,dir):
    # t: time to arrive target position
    # dir: true for ccw, false for cw
    if (pos < -1):
        dir=not dir
    print(pos)
    hex_pos = pos_to_protocol(abs(pos))
    hex_time=time_to_protocol(t)
    cks, rev_cks = get_checksum(0, abs(pos),t,1)
    s1 = "FF FE 00 06 "
    s2 = cks
    rev_s2 = rev_cks
    s3 = "02 00 "
    rev_s3 = "02 01 "
    s4 = hex_pos
    s5 = hex_time
    control = (s1 + s2 + s3 + s4 + s5)
    reverse = (s1 + rev_s2 + rev_s3 + s4 + s5)
    if (dir):
        port_1.write(bytearray.fromhex(control))
    else:
        port_1.write(bytearray.fromhex(reverse))

def speed_control(speed,t,dir):
    #t: time to arrive target speed
    #dir: true for ccw, false for cw

    hex_speed = speed_to_protocol(speed)
    hex_time = time_to_protocol(t)
    cks, rev_cks = get_checksum(speed, 0,t,2)

    s1 = "FF FE 00 06 "
    s2 = cks
    rev_s2 = rev_cks
    s3 = "03 00 "
    rev_s3 = "03 01 "
    s4 = hex_speed
    s5 = hex_time
    control = (s1 + s2 + s3 + s4 + s5)
    reverse = (s1 + rev_s2 + rev_s3 + s4 + s5)

    if (dir):
        port_1.write(bytearray.fromhex(control))
    else:
        port_1.write(bytearray.fromhex(reverse))

def speed_pos_control(speed, pos, dir):
    # move to start pos (pos1)

    # reciprocation from pos1 to pos2
    if(speed<0):
        dir=not dir
    if(pos<-1.0):
        dir=not dir
    hex_pos = pos_to_protocol(pos)
    hex_speed = speed_to_protocol(abs(speed))
    cks, rev_cks = get_checksum(abs(speed), pos,0,0)
    s1 = "FF FE 00 07 "
    s2 = cks
    rev_s2 = rev_cks
    s3 = "01 00 "
    rev_s3 = "01 01 "
    s4 = hex_pos
    s5 = hex_speed
    control = (s1 + s2 + s3 + s4 + s5)
    reverse = (s1 + rev_s2 + rev_s3 + s4 + s5)

    if (dir):
        port_1.write(bytearray.fromhex(control))
    else:
        port_1.write(bytearray.fromhex(reverse))

def setPostionControlMode(rel=True):
    #True for relative postion control
    #False for absolute position control
    if(rel):
        port_1.write((bytearray.fromhex("FF FE 00 03 F0 0B 01")))
    else:
        port_1.write((bytearray.fromhex("FF FE 00 03 F1 0B 00")))

def stop():
    #stop moving, automatically initailize position
    speed_control(0,1,True)

def initPos():
    port_1.write(init_pos)
    #port_1.write(changeControlDir)
    print("Position initialized")
    time.sleep(1)

def getFeedback(mode):
    #mode: 0~9
    len=12
    out=[]

    cks=to_hex_string(255 - (2+hex_to_num("A")*16+mode) % 256)

    feed="FF FE 00 02 "+cks+" A"+str(mode)
    pos_feedback = bytearray.fromhex(feed)
    port_1.write(pos_feedback)
    for i in range(len):
        tmp=port_1.read()
        out.append((binascii.hexlify(bytearray(tmp))).decode('ascii'))
    if(mode==1):
        dir=string_to_num(out[6])
        pos = string_to_num(out[7], out[8])
        speed = string_to_num(out[9], out[10])
        if(dir==0):
            pos=-pos
        return pos / 100, speed / 10
    elif(mode==2):
        dir = string_to_num(out[6])
        speed = string_to_num(out[7], out[8])
        pos = string_to_num(out[9], out[10])
        if (dir == 0):
            speed = -speed
        return pos / 100, speed / 10
    elif(mode==3 or mode==4):
        kp=string_to_num("",out[6])
        ki = string_to_num("", out[7])
        kd = string_to_num("", out[8])
        return [kp,ki,kd]
    else:
        print("---")

@to.timeout(0.5)
def getPos():
    pos,speed=getFeedback(1)
    return pos
'''
setPostionControlMode(False)
initPos()
print("--------------------")
speed_pos_control(20, 180, True)
time.sleep(3)

getFeedback()
time.sleep(1)

print("------------")
speed_pos_control(20, 180, False)

'''

def setGains(val,type):
    #type: true for pos, false for speed
    #val=[kp,ki,kd]
    print("")
    s1 = "FF FE 00 06 "
    cks_tmp=val[0]+val[1]+val[2]+32 # always use 3.2A current, 100mA for 1
    gains = to_hex_string(val[0]) + " " + to_hex_string(val[1]) + " " + to_hex_string(val[2]) + " " + to_hex_string(32) + " "

    #for set gain value of position controler
    if(type):
        checksum = to_hex_string(255 - (cks_tmp+10) % 256) + " "
        port_1.write(bytearray.fromhex(s1+checksum+"04 "+gains))
        print(s1+checksum+"04 "+gains)
    #for set gain value of speed controler
    else:
        checksum = to_hex_string(255 - (cks_tmp + 11) % 256) + " "
        port_1.write(bytearray.fromhex(s1 + checksum + "05 " + gains))
        print(s1 + checksum + "05 " + gains)
