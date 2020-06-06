# Infrared
YS-IRTM 串口红外通讯 串口控制模块

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
