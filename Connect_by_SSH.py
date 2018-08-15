import paramiko
import time
import re
import os
import datetime

sshClient=paramiko.SSHClient()
sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())#跳过远程连接中选择“是”的环节
IOBuffer=""#准备写入文件的字符串
whereIAm=None#此变量为False时表示在堡垒机，为true时表示在设备，为None时表示未赋值
cmd=""
enterStr="\n"#输入空格的时候不需要加"\n"
moreFlag=False#当需要more或者回显不完全的时候
sleepTime=3#回显等待时间
deviceName=None#设备名称
moreStr=None#more字符串的形式
nowTime=""#现在的时间
receivedStr=""#接收到的数据
cipherFlag=False#密码标志位，如果写入密码则不显示回显

selfPath=os.getcwd()#程序现在的位置
logFilePath=""#存储文件路径
cmdFilePath=selfPath+r"\CommandList.txt"#命令文件路径
iniFilePath=selfPath+r"\Config.ini"#配置文件路径
cmdQueue=[]#命令队列

sshHost=None#SSH主机名
sshPort=22#SSH端口号，默认22
sshUsername=None#SSH登陆用户名
sshPassword=None#SSH登陆密码

nowTime=datetime.datetime.now().strftime('%F_%T')
nowTime=str(nowTime).replace(':','-')#替换时间字符串中用于文件名不合法的字符


if os.path.exists("config.ini"):#配置文件存在,继续判断
    temp=open(iniFilePath,"r")
    iniReadBuffer=temp.readlines()
    temp.close()
    for eachItem in iniReadBuffer:
        if re.search(r'HOST\=\"([^\"]+)\"',eachItem)!=None:#判断是不是HOST表项
            temp=re.search(r'HOST\=\"([^\"]+)\"',eachItem).group(1)
            if re.match(r'(((2[0-5][0-5])|(1?[0-9]{1,2}))\.){3}((2[0-5][0-5])|(1?[0-9]{1,2}))$',temp)!=None:#IP格式匹配成功
                sshHost=temp
                pass
            else:#ip匹配不成功，报错弹出
                print("IP地址格式不正确，请修改配置文件")
                print("Press any key to exit")
                input()
                exit()
                pass
            pass
        if re.search(r'PORT\=\"([^\"]+)\"',eachItem)!=None:#判断是不是PORT表项
            temp=re.search(r'PORT\=\"([^\"]+)\"',eachItem).group(1)
            try:
                temp=int(temp)
                pass
            except BaseException as ex:#端口号不是数字
                print("端口号应为纯阿拉伯数字，请修改配置文件")
                print("Press any key to exit...")
                input()
                exit()
                pass
            if temp<=65535 and temp>0:
                sshPort=temp
                pass
            else:#端口号越界
                print("端口号应小于等于6553且大于0")
                print("Press any key to exit...")
                input()
                exit()
                pass
            pass
        if re.search(r'USERNAME\=\"([^\"]+)\"',eachItem)!=None:#判断是不是USERNAME表项
            sshUsername=re.search(r'USERNAME\=\"([^\"]+)\"',eachItem).group(1)
            pass
        if re.search(r'PASSWORD\=\"([^\"]+)\"',eachItem)!=None:#判断是不是PASSWORD表项
            sshPassword=re.search(r'PASSWORD\=\"([^\"]+)\"',eachItem).group(1)
            pass
        if re.search(r'DEVICENAME\=\"([^\"]+)\"',eachItem)!=None:
            deviceName=re.search(r'DEVICENAME\=\"([^\"]+)\"',eachItem).group(1)
            pass
        if re.search(r'MORESTR\=\"([^\"]+)\"',eachItem)!=None:
            moreStr=re.search(r'MORESTR\=\"([^\"]+)\"',eachItem).group(1)
            pass
        pass
    pass
else:#如果配置文件不存在，回显提示,创建配置文件，退出程序
    open(iniFilePath,"w").write('HOST=""\r\nPORT=""\r\nUSERNAME=""\r\nPASSWORD=""\r\nDEVICENAME=""\r\nMORESTR=""\r\n')
    print("配置文件不存在，程序已创建新的配置文件“Config.ini”请配置")
    print("Press any key to exit...")
    input()
    exit()
    pass
if sshHost==None or sshPort==None or sshUsername==None or sshPassword==None or moreStr==None:
    print("配置未完成，请完成配置文件以进行连接")
    print("Press any key to exit...")
    input()
    exit()
    pass
print("HOST:{}\r\nPORT:{}\r\nUSERNAME:{}\r\nDEVICENAME:{}\r\nMORESTR:{}\r\n".format(sshHost,sshPort,sshUsername,deviceName,moreStr))
if os.path.exists("CommandList.txt"):
    temp=open(cmdFilePath,"r")
    cmdQueue=temp.readlines()
    temp.close()
    pass
else:
    print("检测到命令文件未创建")
    open(cmdFilePath,"a").write("")
    print("已创建空白命令文件")
    print("Press any key to exit")
    input()
    exit()
    pass

logFilePath=selfPath+'\\'+nowTime+".log"

try:
    print("Connecting...")
    sshClient.connect(sshHost,sshPort,sshUsername,sshPassword)#python连接配置
    pass
except BaseException as ex:#登录失败错误处理
    print(str(ex))
    input()
    print("Pres any key to exit...")
    exit()
    pass
myChannel=sshClient.invoke_shell()#建立管道

while True:
    if moreFlag==False:#不需要more
        if cmdQueue!=[]:#命令队列不为空
            cmd=cmdQueue.pop(0)
            cmd=cmd.replace('\r','').replace('\n','').strip()
            if whereIAm==True:
                sleepTime=1
                if cipherFlag==True:
                    IOBuffer="**********"
                    cipherFlag=False
                    pass
                else:
                    IOBuffer="####Commadn:"+cmd
                    pass
            enterStr="\n"
            pass
        else:#命令队列为空
            print("命令执行完成")
            time.sleep(5)
            exit()
            pass
        pass
    else:#more标志位置位，需要more
        cmd=' '#more的时候只需要发送空格
        enterStr=""#不需要发送回车
        sleepTime=0.2#调短等待时间
        pass

    myChannel.send(cmd+enterStr)#发送命令
    time.sleep(sleepTime)#暂停
    receivedStr=myChannel.recv(4096)#接收回显
    receivedStr=bytes(receivedStr).decode("utf-8")#对字符串进行编码
    receivedStr=str(receivedStr).replace('\x1b','').replace("[42D",'').replace('[m[','[').replace('\x08','').replace('[16D','')#去除不能识别的字符

    if whereIAm==None:#未收到任何一次回显
        if re.search(r'\[[^\@]+\@[^\]]+\]\$',receivedStr)!=None:#出现堡垒机的设备名
            whereIAm=False#将操作标志位设为false，意为目前在操作堡垒机
            sleepTime=3#因为telnet回显时间长，所以需要更长的等待时间
            print("堡垒机")
            pass
        pass
    if whereIAm!=True:#如果收到过在堡垒机上的回显
        if re.search(r'[\>|\#]',receivedStr)!=None:#发现了满足输入的设备名
            whereIAm=True#将操作标志位设为false,意为在目前在操作设备
            sleepTime=1#已经进入设备
            print("设备")
            pass
        pass
    if whereIAm==True:
        if receivedStr.find(moreStr)==-1:#收到的字符串中不存在more
            if receivedStr.find('#')!=-1 or receivedStr.find('>')!=-1:
            #if receivedStr.find('>')!=-1:#说明回显结束
                if (receivedStr.find('\r\n#')!=-1 or receivedStr.find('  #')!=-1) and receivedStr.find('>')==-1:#某行里有一个单独的井号，说明不代表一个设备名而是代表华为/华三设备中回显的分隔符
                    moreFlag=True#more标志位置位
                    IOBuffer+=receivedStr
                    print("数据被截断")
                    print(receivedStr)
                    continue
                    pass
                moreFlag=False#more标志位置位
                IOBuffer+=receivedStr
                IOBuffer=IOBuffer.replace(moreStr,'')#去掉回显数据中的more
                with open(logFilePath,'a') as fileWriter:
                    fileWriter.write(IOBuffer)
                    pass
                IOBuffer=""
                pass
            elif receivedStr.find("assword:")!=-1:#需要输密码
                moreFlag=False
                cipherFlag=True
                IOBuffer+=receivedStr
                pass
            else:#回显被截断
                moreFlag=True#more标志位置位
                IOBuffer+=receivedStr
                print("数据被截断")
                pass
            pass
        else:
            moreFlag=True#more标志位置位
            IOBuffer+=receivedStr
            pass
        pass
    print(receivedStr)
    pass
