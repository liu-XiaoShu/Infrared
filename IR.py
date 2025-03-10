#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#----------- YS-IRTM 串口红外通讯 串口控制模块 -------------------
#  功能:  串口通讯协议控制串口红外模块收发指令
#  说明:  模块: NEC红外收发模块
#  流程:  pc/单片机等等设备连接串口TX/RX
#         通过模块指定的协议,发送控制指令到模块STC单片机上
#         单片机内置代码把指令通过NEC协议调制成红外发射脉冲
#         红外发射出去,接受就是相反过程
#
#  NEC红外收发协议:              用户码1+用户码2+命令码+命令码反码
#  YS-IRTM串口红外模块 通讯协议: 地址位+操作位+用花1+用户码2+命令码
#  作者：小树
#  时间:  2020-05-11
#-----------------------------------------------------------------

import sys
import serial
import time
import yaml
import os
import re

class IR_Control:
    def __init__(self, serialPort, baudRate=115200):
        """
            功能:  IR控制模块串口创建,通讯协议定义
            参数:  serialPort 串口号
                　 BaudRate　 波特率
            返回值 无
        """
        #YS-IRTM串口红外模块 通讯协议
        #协议组成: 地址位+操作位+用户码1+用户码2+命令码

        #协议地址位
        #self.DEFAULT_ADDR = "A1"        #默认通讯地址 可修改 1~FF
        #self.UNIVERSAL_ADDR = "FA"      #通用通讯地址 不可修改
        self.ADDR = "A1"

        #协议操作位
        self.IR_TX_STATE = "F1"            #红外发射状态
        self.MODIFY_ADDR_STATE = "F2"      #修改通讯地址状态
        self.MODIFY_BAUD_RATE_STATE = "F3" #修改模块波特率状态

        #数据位 具体指令数据
        #self.DATA_BITS_1 = ""   #用户码高位
        #self.DATA_BITS_2 = ""   #用户码低位
        #self.DATA_BITS_3 = ""   #命令码

        #波特率修改指令
        self.BAUD_RATE_DICT = { 4800: "01", 
                                9600:"02",
                                19200:"03",
                                57600:"04"} #支持波特率字典

        #操作反馈
        self.IR_TX_SUCCESS = "f1"               #红外发射成功
        self.MODIFY_ADDR_SUCCESS = "f2"         #修改通讯地址成功
        self.MODIFY_BAUD_RATE_SUCCESS = "f3"    #修改模块波特率成功

        #串口波特率
        self.baudRate = baudRate
        self.serialPort = serialPort

        #路径
        self.base_path = "modules/Infrared/"

    def load_urat(self, BaudRate=0):
        """
            功能:   加载串口
            参数:   serialPort: 串口号
            返回值: 无
        """
        try:
            #print(self.serialPort)
            if BaudRate:
                baudrate = BaudRate
            else:
                baudrate = self.baudRate
            #print(baudrate)
            self.uart = serial.Serial(self.serialPort, baudrate, timeout=2)
        except:
            print("\033[0;36;31m[IR IR UART串口]: %s设备不存在!!\033[0m"%serialPort)
            sys.exit()


    def read_yaml(self, yaml_file):
        """
            功能:   读取遥控码值配置
            参数:   配置文件
            返回值: 配置文件信息字典
        """
        yaml_version = yaml.__version__
        yaml_version = yaml_version[0:3]
        with open(yaml_file, 'r') as f:
            if float(yaml_version) < 5.1:
                yaml_config = yaml.load(f)
            else:
                yaml_config = yaml.load(f, Loader=yaml.FullLoader)
        return yaml_config

    def get_code_config(self, configPath, key):
        """
            功能:   获取对应遥控的用户码和指令码
            参数:   configFile 遥控配置文件路径/遥控名称
                    key: 遥控按键丝印名称
            返回值: str 用户码, 指令码
        """
        config_dict = {}
        UserCode = ""   #用户码
        KeyCmdCode = "" #键值/指令码
        if not configPath.find("_码值表.yaml") >= 0:
            configPath = configPath + "_码值表.yaml"
        if not os.path.isfile(configPath):
            configPath = os.path.join(self.base_path, configPath)
        config_dict = self.read_yaml(configPath)
        UserCode = config_dict["用户码"]
        try:
            KeyCmdCode = config_dict['键值/命令码'][key]
        except:
            print("\033[0;36;31m[IR IR UART串口]: 遥控器丝印键值输入错误 可以进入%s 查看!!\033[0m"%configPath)
        return UserCode, KeyCmdCode


    def serial_send(self, sendCmd, sendFormat="utf-8"):
        """
            功能:   IR模块串口发送指令函数
            参数:   sendCmd 需要发送的指令
            返回值: bool: True/False
        """
        try:
            if sendFormat == "hex":
                #sendCmd = "A1F122dd12"
                #print(sendCmd)
                self.uart.write(bytes.fromhex(sendCmd))
            else:
                self.uart.write(str(sendCmd + '\n').encode("utf-8"))
            print("\033[0;36;32m[IR UART串口]: %s --> 指令发送成功!!\033[0m"%sendCmd)
            return True
        except:
            print("\033[0;36;31m[IR UART串口: %s --> 指令发送失败!!\033[0m"%sendCmd)
            return False

    def serial_receive(self, timeOut, receiveFormat="utf-8", CmdRsult=0, keyword="NULL"):
        """
           功能:   IR模块串口接收数据
           参数:   timeOut 接收超时
                   receiveFormat 读取的编码格式
                   CmdRsult 是否快速获取命令执行结果
                   keyword 查询关键字
           返回值: 读取信息列表/False
        """
        count = 0
        serial_content_list = []
        try:
            while count < timeOut:
                if receiveFormat == "hex":
                    if CmdRsult:
                        serial_content = self.uart.read().hex()
                    else:
                        serial_content = self.uart.readline().hex()
                else:
                    serial_content = self.uart.readline()
                if serial_content:
                    if serial_content.find(keyword) >= 0:
                        return True
                    print(serial_content)
                    serial_content_list.append(serial_content)
                count += 1
            print(serial_content_list)
            return serial_content
        except:
            print("\033[0;36;31m[IR UART串口]: 串口信息接收失败!!\033[0m")
            return False


    def IR_Send(self, UserCode, KeyCmdCode):
        """
            功能:   通讯协议组装及
                    红外指令发送
            参数:   UserCode      用户码
                    KeyCmdCode: 键值码,命令码
            返回值: True/False    成功/失败
        """
        #加载串口
        self.load_urat()

        IR_sendCmd = "" #发送指令
        success_flag = 0
        if isinstance(UserCode, str) and isinstance(KeyCmdCode, str):
            IR_sendCmd = IR_sendCmd + self.ADDR
            IR_sendCmd = IR_sendCmd + self.IR_TX_STATE
            IR_sendCmd = IR_sendCmd + UserCode
            IR_sendCmd = IR_sendCmd + KeyCmdCode
            if self.serial_send(IR_sendCmd, "hex"):
                success_flag += 1
            else: 
                success_flag = 0
            if self.serial_receive(2, "hex", 1, self.IR_TX_SUCCESS):
                success_flag += 1
            else:
                success_flag = 0
        else:
            success_flag = 0
            print("\033[0;36;31m[IR UART串口]: 用户码/键值码/命令码类型应该为字符串!!\033[0m")
        #关闭串口
        self.close_uart()
        if success_flag == 2:
            return True
        else:
            return False

    def StartIrSend(self, IrRemoteControlName, CmdKey):
        """
            功能: 　根据遥控丝印名称发送
                    红外指令
            参数：　IrRemoteControlName 红外遥控名称
                    CmdKey: 遥控丝印值
            返回值: True/False
        """
        UserCode = ""   #用户码
        KeyCmdCode = "" ##键值/指令码
        RX_SUCCESS = 0
        if isinstance(IrRemoteControlName, str) and isinstance(CmdKey, str):
            UserCode, KeyCmdCode = self.get_code_config(IrRemoteControlName, CmdKey)
            if KeyCmdCode and self.IR_Send(UserCode, KeyCmdCode):
                RX_SUCCESS = 1
            else:
                RX_SUCCESS = 0
        else:
            RX_SUCCESS = 0
            print("\033[0;36;31m[IR UART串口]: 遥控器名称/配置路径/丝印名称，类型应该为字符串!!\033[0m")
        if RX_SUCCESS:
            return True
        else:
            return False

    def ModifyIrBaudRate(self, BaudRate):
        """
            功能:   修改模块串口通讯波特率
            参数:   BaudRate 波特率
            返回值: True/False 修改成功/失败
        """
        cmd_success_flag = 0
        BaudRate = int(BaudRate)
        if not BaudRate in self.BAUD_RATE_DICT:
            print("\033[0;36;31m[IR UART串口]: 模块不支持该[%s]特率!!\033[0m"%BaudRate)
            return False
        #加载串口
        self.load_urat()
        modify_baud_rate_Cmd = ""
        modify_baud_rate_Cmd_list = []
        modify_baud_rate_Cmd_list.append(self.ADDR)  #地址 
        modify_baud_rate_Cmd_list.append(self.MODIFY_BAUD_RATE_STATE)  #修改波特率
        modify_baud_rate_Cmd_list.append(self.BAUD_RATE_DICT[BaudRate])  #修改波特率
        modify_baud_rate_Cmd_list.append("0000")  #修改波特率
        modify_baud_rate_Cmd = "".join(modify_baud_rate_Cmd_list)
        if self.serial_send(modify_baud_rate_Cmd, "hex"):
            cmd_success_flag += 1
            #关闭串口
            self.close_uart()
        else:
            cmd_success_flag = 0
        #加载串口
        self.load_urat(BaudRate)
        if self.serial_receive(2, "hex", 1, self.MODIFY_BAUD_RATE_SUCCESS):
            cmd_success_flag += 1
        else:
            cmd_success_flag = 0
        #关闭串口
        self.close_uart()

        if cmd_success_flag == 2:
            self.baudRate = BaudRate
            print("\033[0;36;32m[IR UART串口]: 模块波特率修改成功，后续请使用:%s!!\033[0m"%BaudRate)
            return True
        else:
            return False

    def startIrReceive(self, timeOut, receiveFormat):
        """
            功能:   红外遥控信息接收
            参数:   无
            返回值: list 接收数据 
        """
        infor_list = []
        self.load_urat()
        infor_list = self.serial_receive(timeOut, receiveFormat)
        print(infor_list)
        self.close_uart()

    def __del__(self):
        """
            功能:   清理串口
            参数:   无
            返回值: 无
        """
        self.close_uart()

    def close_uart(self):
        """
            功能:   关闭串口
            参数:   无
            返回值: 无
        """
        self.uart.close()

if __name__=="__main__":
    keyCmd = sys.argv[1]
    keyCmd = str(keyCmd)
    IR = IR_Control("/dev/ttyUSB0", 9600)
    if IR.StartIrSend("示例遥控", keyCmd):
        print("%s: 指令红外发送成功!"%keyCmd)
    else:
        print("%s: 指令红外发送失败!"%keyCmd)
