#!/usr/bin/env python

import sys
from PyQt4 import QtGui
from PyQt4 import QtCore
import time
import serial
import Adafruit_BluefruitLE
from Adafruit_BluefruitLE.services import UART, DeviceInformation
import glob
import subprocess
import os
import uuid
from datetime import datetime
from zebra import zebra


class Model():
    UARTport= None
    UARTPorts= []
    lot= 'FFFFFFFF'
    writeLot= 'FFFFFFFF'
    GUIVersion= 'v1.1.4.1'
    timeStamp= hex(0xFFFFFFFF)
    deviceVersion= '30315354'
    labelX= '1'
    labelY= '1'
    hwrevText= '00C2'
    facText= 'D_Wynnewood'
    llText= '01'
    shiftText= '1'

    def __init__(self):
        self.flag= False
        self.ble = Adafruit_BluefruitLE.get_provider()
        self.commands= []
        self.threads= []
        self.resultFlag= False
        self.bleFlag= False
        Model.UARTPorts= self.serial_ports()
        Model.UARTport= Model.UARTPorts[0]
        self.printer= zebra()
        queue= self.printer.getqueues()
        #self.printer.setqueue(queue[1])
        self.printer.setqueue('ZT230')
        self.curTimeStamp= 'FFFFFFFF'
        self.curLot= 'FFFFFFFF'
        self.curDeviceVersion= 'FFFFFFFF'

        print os.getcwd()
        os.chdir("./testgui/src")
        #for i in range(0, 3);
        #    os.chdir(os.path.dirname(os.getcwd()))

        self.filename= 'log_'+ time.strftime("%Y-%m-%d")
        self.filename2= 'debug_'+ time.strftime("%Y-%m-%d")
        self.logPath= '../log'
        self.completeName= os.path.join(self.logPath, self.filename+ ".txt")
        for files in os.walk(self.logPath):
            if self.filename in str(files):
                self.f= open(self.completeName, 'r+')
                self.f.seek(0, 2)
                break
            else:
                self.f= open(self.completeName, 'w')

        self.completeName2= os.path.join(self.logPath, self.filename2+ ".txt")
        for files in os.walk(self.logPath):
            if self.filename2 in str(files):
                self.f2= open(self.completeName2, 'r+')
                self.f2.seek(0, 2)
                break
            else:
                self.f2= open(self.completeName2, 'w')

        self.imgFolder= '../res/img'
        for file in os.listdir(self.imgFolder):
            if file.endswith(".bin"):
                #if 'softdevice' in file:
                if 's130' in file:
                    self.softDevName= file.replace('.bin', '')
                #if 'tester' in file:
                if 'abt-' in file:
                    self.testerName= file.replace('.bin', '')
                #if 'bootloader' in file:
                if 'rd' in file:
                    self.bootloaderName= file.replace('.bin', '')
                #if 'abrams' in file:
                if 'ab-' in file:
                    self.productName= file.replace('.bin', '')

        self.flashScriptPath= '../res/scripts'
        self.soundPath= '../res/sound/soundtest.mp3'
        self.soundPath2= '../res/sound/soundtest2.mp3'
        self.softDevPathAddr= '../res/img/%s.bin 0x00000000' %(self.softDevName)
        #self.testerPathAddr= '../res/img/%s.bin 0x00018000' %(self.testerName)
        self.testerPathAddr= '../res/img/%s.bin 0x0001b000' %(self.testerName)
        self.bootloaderPathAddr= '../res/img/%s.bin 0x3c000' %(self.bootloaderName)
        #self.productPathAddr= '../res/img/%s.bin 0x00018000' %(self.productName)
        self.productPathAddr= '../res/img/%s.bin 0x0001b000' %(self.productName)

        self.bleManufacturer= 'altroniq'
        self.bleModel= 'A0001'
        self.bleSoftRev= '0.0.1'
        self.bleHardRev= '0.0.1'
        self.bleManufacturerFlag= False
        self.bleModelFlag= False
        self.bleSoftRevFlag= False
        self.bleHardRevFlag= False
        self.bleRSSI= 0
        self.bleRSSILimit= -60
        self.bleServiceUUID= uuid.UUID('0d080000-99f7-48c5-ab62-e82ec55f48b6')
        self.bleServiceUUIDFlag= False
        self.bleCharUUID1= uuid.UUID('0d080001-99f7-48c5-ab62-e82ec55f48b6')
        self.bleCharUUID2= uuid.UUID('0d080002-99f7-48c5-ab62-e82ec55f48b6')
        self.bleCharUUIDFlag= False

    def init_ser(self):
        self.ser = serial.Serial(
                                 port= str(Model.UARTport),
                                 baudrate= 230400
                                )
        self.ser.isOpen()
        self.commands= []
        time.sleep(0.5)
        self.commands= self.getCommands()
        self.func_map = {
                        'mic': self.micrun,
                        'ble': self.blerun,
                        'all': self.runall_debug,
                        'stop': self.stop_debug,
                        }
        for command in self.commands:
            if 'ble' == command or 'all' == command or 'stop' == command or 'mic' == command:
                continue
            self.func_map[command]= self.run

    def serial_ports(self):
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
            ports.sort(reverse= True)
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result

    def getCommands(self):
        input= 'test'
        self.writeCommand(input)
        out= self.getOut()
        words= out.split()
        while '--' in words:
            cmd= words[words.index('--')-1]
            self.commands.append(cmd)
            words.remove('--')
        print self.commands
        #for line in self.commands:
        #    versame.model.display(line + ' ')
        return self.commands

    def writeCommand(self, input):
        for char in input:
            time.sleep(0.01)
            self.ser.write(char)
        self.ser.write('\r\n')

    def getOut(self):
        out= ''
        time.sleep(0.1)
        while self.ser.inWaiting() > 0:
            out += self.ser.read(1)
        return out

    def micrun(self, text):
        micrunner= MicThread(text)
        micrunner.data_run.connect(self.on_debug_data_ready)
        self.threads.append(micrunner)
        micrunner.start()

    def blerun(self, text):
        if self.bleFlag:
            self.debug_show('Ble is busy, please click Stop and try again.\n')
            return
        blerunner= BleThread(self.testble)
        blerunner.data_run.connect(self.on_debug_data_ready)
        self.threads.append(blerunner)
        blerunner.start()

    def testble(self):
        self.bleFlag= True
        self.bleManufacturerFlag= False
        self.bleModelFlag= False
        self.bleSoftRevFlag= False
        self.bleHardRevFlag= False
        self.bleServiceUUIDFlag= False
        self.bleCharUUIDFlag= False

        self.ble.clear_cached_data()

        try:
            # Get the first available BLE network adapter and make sure it's powered on.
            adapter = self.ble.get_default_adapter()
            adapter.power_on()
            print('Using adapter: {0}'.format(adapter.name))

            # Disconnect any currently connected UART devices.  Good for cleaning up and
            # starting from a fresh state.
            print('Disconnecting any connected UART devices...')
            UART.disconnect_devices()
        except:
            self.bleFlag= False

        # Scan for UART devices.
        print('Searching for UART device...')
        try:
            adapter.start_scan(5)
            device= None
            known_uarts = set()
            while True:
                if self.flag:
                    self.bleFlag= False
                    return
                flag= False
                found = set(UART.find_devices())
                new = found - known_uarts
                for dev in new:
                    print('Found UART: {0} [{1}] {2}'.format(dev.name, dev.id, dev))
                    if dev.name == 'DemoPeripheral':
                        device= dev
                        flag= True
                        break
                known_uarts.update(new)
                # Sleep for a second and see if new devices have appeared.
                if flag:
                    break
                time.sleep(0.5)
        except:
            self.bleFlag= False
        finally:
            # Make sure scanning is stopped before exiting.
            adapter.stop_scan(5)

        if self.bleServiceUUID != device.advertised[3]:
            self.bleServiceUUIDFlag= True
            self.bleFlag= False
            return

        try:
            print('RSSI: {0}'.format(device.rssi))
            self.bleRSSI= device.rssi
            print('Connecting to device...')
            device.connect(5)  # Will time out after 60 seconds, specify timeout_sec parameter
            # to change the timeout.
        except:
            self.bleFlag= False
            return

        # Once connected do everything else in a try/finally to make sure the device
        # is disconnected when done.
        try:
            device.discover([device.advertised[3]], [self.bleCharUUID2, self.bleCharUUID1])

            # Find the UART service and its characteristics.
            uart = device.find_service(device.advertised[3])
            rx = uart.find_characteristic(self.bleCharUUID1)
            tx = uart.find_characteristic(self.bleCharUUID2)

            print rx
            print tx

            if not rx or not tx:
                self.bleCharUUIDFlag= True
                self.bleFlag= False
                return
            # Wait for service discovery to complete for the DIS service.  Will
            # time out after 60 seconds (specify timeout_sec parameter to override).
            print('Discovering services...')
            DeviceInformation.discover(device)

            # Once service discovery is complete create an instance of the service
            # and start interacting with it.
            dis = DeviceInformation(device)

            # Print out the DIS characteristics.
            print('Manufacturer: {0}'.format(dis.manufacturer))
            print('Model: {0}'.format(dis.model))
            print('Serial: {0}'.format(dis.serial))
            print('Hardware Revision: {0}'.format(dis.hw_revision))
            print('Software Revision: {0}'.format(dis.sw_revision))
            print('Firmware Revision: {0}'.format(dis.fw_revision))
            print('System ID: {0}'.format(dis.system_id))
            print('Regulatory Cert: {0}'.format(dis.regulatory_cert))
            print('PnP ID: {0}'.format(dis.pnp_id))

            if(str(dis.manufacturer) != self.bleManufacturer
               or str(dis.model) != self.bleModel
               or str(dis.hw_revision) != self.bleHardRev
               or str(dis.sw_revision) != self.bleSoftRev):
                if (str(dis.manufacturer) != self.bleManufacturer):
                    self.bleManufacturerFlag= True
                if (str(dis.model) != self.bleModel):
                    self.bleModelFlag= True
                if (str(dis.hw_revision) != self.bleHardRev):
                    self.bleHardRev= True
                if (str(dis.sw_revision) != self.bleSoftRev):
                    self.bleSoftRev= True

        finally:
            # Make sure device is disconnected on exit.
            #time.sleep(1)
            device.disconnect(5)
            print "device disconnect"
            #time.sleep(1)
            self.bleFlag= False

    def runall(self, text):
        runallrunner= RunAllThread(self.testble)
        runallrunner.data_run.connect(self.on_data_ready)
        runallrunner.result_run.connect(self.on_result_ready)
        runallrunner.log_run.connect(self.on_log_ready)
        self.threads.append(runallrunner)
        runallrunner.start()

    def runall_debug(self, text):
        runallrunner= RunAllDebugThread(self.testble)
        runallrunner.data_run.connect(self.on_debug_data_ready)
        self.threads.append(runallrunner)
        runallrunner.start()

    def stop(self, text):
        versame.view.viewWidget.stopButt.setEnabled(False)
        versame.view.viewWidget.testAutoButt.setEnabled(True)
        self.clearResultBox()
        stopper= StopThread(text)
        stopper.data_run.connect(self.on_data_ready)
        stopper.result_run.connect(self.on_result_ready)
        stopper.log_run.connect(self.on_log_ready)
        self.threads.append(stopper)
        stopper.start()
        time.sleep(2)
        versame.view.viewWidget.stopButt.setEnabled(True)

    def stop_debug(self, text):
        debugPanel.stopButt.setEnabled(False)
        debugPanel.testButt.setEnabled(True)
        stopper= StopDebugThread(text)
        stopper.data_run.connect(self.on_debug_data_ready)
        self.threads.append(stopper)
        stopper.start()
        time.sleep(2)
        debugPanel.stopButt.setEnabled(True)

    def run(self, text):
        runner= RunThread(text)
        runner.data_run.connect(self.on_debug_data_ready)
        self.threads.append(runner)
        runner.start()

    def on_data_ready(self, data):
        self.display(data, versame.view.viewWidget.log)

    def on_debug_data_ready(self, data):
        self.debug_show(data)

    def debug_show(self, data):
        self.display(data, debugPanel.log)
        data= self.processLog(data)
        self.saveDebugLog(data)

    def on_result_ready(self):
        self.updateResultBox()

    def on_log_ready(self, data):
        self.saveLog(data)

    def run_function(self):
        debugPanel.testButt.setEnabled(False)
        debugPanel.stopButt.setEnabled(True)
        function = self.func_map[str(debugPanel.testCombo.currentText())]
        function(str(debugPanel.testCombo.currentText()))
        time.sleep(2)
        debugPanel.testButt.setEnabled(True)

    def save(self):
        filename= QtGui.QFileDialog.getSaveFileName(versame.view.viewWidget, 'Save File', selectedFilter= '*.txt')
        fname= open(filename, 'w')
        fname.write(debugPanel.log.toPlainText())
        fname.close()
    '''
    def flashTest(self):
        curPath= os.getcwd()
        os.chdir(self.flashScriptPath)
        self.writeTestFile()
        batcmd= 'JLinkExe flash_SignatureTest.jlink'
        result= subprocess.check_output(batcmd, shell=True)
        versame.model.display(result)
        os.chdir(curPath)
    #print self.port
    #if self.port:
    #    self.init_ser()

    def flashProd(self):
        curPath= os.getcwd()
        os.chdir(self.flashScriptPath)
        batcmd= 'JLinkExe flash_product.jlink'
        result= subprocess.check_output(batcmd, shell=True)
        #versame.model.display(result)
        os.chdir(curPath)
    #self.init_ser()
    '''
    def playmusic(self, audio):
        audio_file = audio
        return_code = subprocess.call(["afplay", audio_file])

    def autoTest(self):
        versame.view.viewWidget.testAutoButt.setEnabled(False)
        versame.view.viewWidget.stopButt.setEnabled(True)
        self.clearResultBox()
        self.flag = True
        time.sleep(1)
        self.flag = False
        versame.view.viewWidget.log.clear()
        versame.view.viewWidget.log.setTextColor(QtGui.QColor("black"))
        self.runall('all')
        time.sleep(2)
        versame.view.viewWidget.testAutoButt.setEnabled(True)

    def display(self, text, obj):
        obj.insertPlainText(text)
        cursor= obj.textCursor()
        format1= QtGui.QTextCharFormat()
        format1.setForeground(QtGui.QBrush(QtGui.QColor("green")))
        format2= QtGui.QTextCharFormat()
        format2.setForeground(QtGui.QBrush(QtGui.QColor("red")))
        format3= QtGui.QTextCharFormat()
        format3.setForeground(QtGui.QBrush(QtGui.QColor("yellow")))
        pattern1= "PASS"
        pattern2= "FAIL"
        pattern3= "ERROR"
        regex1= QtCore.QRegExp(pattern1)
        regex2= QtCore.QRegExp(pattern2)
        regex3= QtCore.QRegExp(pattern3)

        pos= 0
        index= regex1.indexIn(obj.toPlainText(), pos)
        while index != -1:
            cursor.setPosition(index)
            cursor.movePosition(QtGui.QTextCursor.Right, 1, 4)
            cursor.mergeCharFormat(format1)
            pos= index + regex1.matchedLength()
            index= regex1.indexIn(obj.toPlainText(), pos)

        pos= 0
        index= regex2.indexIn(obj.toPlainText(), pos)
        while index != -1:
            cursor.setPosition(index)
            cursor.movePosition(QtGui.QTextCursor.Right, 1, 4)
            cursor.mergeCharFormat(format2)
            pos= index + regex2.matchedLength()
            index= regex2.indexIn(obj.toPlainText(), pos)

        pos= 0
        index= regex3.indexIn(obj.toPlainText(), pos)
        while index != -1:
            cursor.setPosition(index)
            cursor.movePosition(QtGui.QTextCursor.Right, 1, 5)
            cursor.mergeCharFormat(format3)
            pos= index + regex3.matchedLength()
            index= regex3.indexIn(obj.toPlainText(), pos)
        obj.moveCursor(QtGui.QTextCursor.End)

    def saveLog(self, text):
        self.f.write(text)

    def saveDebugLog(self, text):
        self.f2.write(text)

    def processLog(self, text):
        fmt= "%Y-%m-%d_%H:%M:%S_UTC%z"
        text= '\r' + time.strftime(fmt) + '\t  ' + text.replace('\n', '\n\t\t\t\t  ')
        return text
    '''
    def textFilter(self, text, remStr):
        newtext= text.replace(remStr, "")
        return newtext
    '''
    def textMatch(self, text, pattern):
        if pattern in text:
            return True
        else:
            return False

    def lineMatch(self, text, pattern):
        lines= text.splitlines()
        for line in lines:
            if pattern in line:
                return line
        return ''

    def textInitialFilter(self, text):
        bad_words= ['shell', 'v 0.', 'VersaMe', 'help', 'test all']
        new_text= ''
        lines= text.splitlines()
        for line in lines:
            if not any(bad_word in line for bad_word in bad_words):
                new_text+= "\n" + line
        return new_text

    def searchLog(self):
        ID= str(debugPanel.prodTextbox.text())
        root_dir= self.logPath
        for subdir, dirs, files in os.walk(root_dir):
            for file in files:
                k= subdir+'/'+file
                with open(k, "r") as f:
                    data = f.read()
                    if ID in data:
                        os.system("open " + k)

    def getTimeStamp(self):
        now= datetime.utcnow()
        sec= int((now - datetime(1970, 1, 1)).total_seconds())
        return hex(sec)
    '''
    def writeTestFile(self):
        file= open("flash_SignatureTest.jlink", "w")
        file.write("device nrf51822\n")
        file.write("speed 1000\n")
        file.write("w4 4001e504 2  // enable erase\n")
        file.write("w4 4001e50c 1  // erase all\n")
        file.write("Sleep 50\n")
        file.write("r\n")
        file.write("w4 4001e504 1 // enable write\n")
        file.write("w4 10001084 %s  // set lot in UICR\n" % str(self.lot))
        file.write("w4 10001088 %s  // set timeStamp in UICR\n" % self.timeStamp)
        file.write("w4 10001014 3c000  // set bootloader start addr\n")
        file.write("w4 0003fc00 1      // set valid application flag\n")
        file.write("loadbin ../img/softdevice.bin 0x00000000\n")
        file.write("loadbin ../img/tester.bin 0x00018000\n")
        file.write("loadbin ../img/bootloader.bin 0x3c000\n")
        file.write("r\n")
        file.write("g\n")
        file.write("exit\n")
        file.close()

    def writeProdFile(self):
        file= open("flash_SignatureProdct.jlink", "w")
        file.write("device nrf51822\n")
        file.write("speed 1000\n")
        file.write("w4 4001e504 1      // enable write\n")
        file.write("loadbin ../img/product.bin 0x00018000\n")
        file.write("mem32 10001084 2\n")
        file.write("r\n")
        file.write("g\n")
        file.write("exit\n")
        file.close()
    '''
    def eraseDevice(self):
        jLinkFlag, flashedFlag, preResult= self.preReadUICR()
        if not jLinkFlag:
            resultFilter= 'jLink Connection [FAIL]\n'
            return (preResult, resultFilter)
        if flashedFlag:
            Model.writeLot= '00C2' + self.curLot[4:8]
            Model.timeStamp= '0x' + self.curTimeStamp.lower()
        else:
            Model.timeStamp= self.getTimeStamp()
            Model.writeLot= Model.lot
        batcmd= 'printf "si SWD\nspeed 4000\ndevice nrf51822\nr\nw4 4001e504 2\nw4 4001e50c 1\nsleep 50\nexit" | JLinkExe'
        result= preResult
        result+= subprocess.check_output(batcmd, shell=True)
        if self.textMatch(result, 'Writing 00000002 -> 4001E504') and \
           self.textMatch(result, 'Writing 00000001 -> 4001E50C') and \
           not self.textMatch(result, 'WARNING') and \
           not self.textMatch(result, 'UNKNOWN'):
            resultFilter= 'Erasing Device [PASS]\n'
        else:
            resultFilter= 'Erasing Device [FAIL]\n'
        return (result, resultFilter)

    def writeUICR(self):
        batcmd= 'printf "si SWD\nspeed 4000\ndevice nrf51822\nr\n' \
                'w4 4001e504 1\n' \
                'w4 10001080 %s\n' \
                'w4 10001084 %s\n' \
                'w4 10001088 %s\n' \
                'w4 10001014 3c000\n' \
                'w4 0003fc00 1\nexit" | JLinkExe' %(str(Model.deviceVersion), str(Model.writeLot), str(Model.timeStamp))
        result= subprocess.check_output(batcmd, shell=True)
        if self.textMatch(result, 'Writing 00000001 -> 4001E504') and \
           self.textMatch(result, 'Writing 0003C000 -> 10001014') and \
           self.textMatch(result, 'Writing 00000001 -> 0003FC00') and \
           self.textMatch(result, 'Writing %s -> 10001080' %(str(Model.deviceVersion)) ) and \
           self.textMatch(result, 'Writing %s -> 10001084' %(str(Model.writeLot)) ) and \
           self.textMatch(result, 'Writing %s -> 10001088' %(str(Model.timeStamp).replace('0x', '').upper()) ) and \
           not self.textMatch(result, 'WARNING') and \
           not self.textMatch(result, 'UNKNOWN'):
            resultFilter= 'Writing UICR [PASS]\n'
        else:
            resultFilter= 'Writing UICR [FAIL]\n'
        return (result, resultFilter)

    def flashbin(self, path, index):
        batcmd= 'printf "si SWD\nspeed 4000\ndevice nrf51822\nr\nw4 4001e504 1\nloadbin %s\nr\ng\nexit" | JLinkExe' %path
        result= subprocess.check_output(batcmd, shell=True)
        if index== 1:
            #binName= 'SoftDevice'
            binName= 'SoftDevice ' + self.softDevName
        elif index== 2:
            #binName= 'Tester'
            binName= 'Tester ' + self.testerName
        elif index== 3:
            #binName= 'Bootloader'
            binName= 'Bootloader ' + self.bootloaderName
            versame.model.init_ser()
        else:
            binName= 'BinFile'

        if self.textMatch(result, 'O.K.') and \
           not self.textMatch(result, 'fail') and \
           not self.textMatch(result, 'WARNING') and \
           not self.textMatch(result, 'UNKNOWN'):
            resultFilter= 'Flash %s [PASS]\n' %binName
        else:
            resultFilter= 'Flash %s [FAIL]\n' %binName
        return (result, resultFilter)

    def readUICR(self):
        time.sleep(1)
        batcmd= 'printf "si SWD\nspeed 4000\ndevice nrf51822\nr\nw4 4001e504 1\nloadbin %s\nmem32 10001080 3\nr\ng\nexit" | JLinkExe' %self.productPathAddr
        result= subprocess.check_output(batcmd, shell=True)
        if self.textMatch(result, 'O.K.') and \
           self.textMatch(result, '10001080 = %s %s %s' %(str(Model.deviceVersion), str(Model.writeLot), str(Model.timeStamp).replace('0x', '').upper()) ) and \
           not self.textMatch(result, 'fail') and \
           not self.textMatch(result, 'WARNING') and \
           not self.textMatch(result, 'UNKNOWN'):
            resultFilter= 'Flash Product %s [PASS]\n' %(self.productName)
            resultFilter+= self.lineMatch(result, '10001080')
            resultFilter+= '\n'
        else:
            resultFilter= 'Flash Product %s [FAIL]\n' %(self.productName)
            resultFilter+= self.lineMatch(result, '10001080') + '\n'
        return (result, resultFilter)

    def preReadUICR(self):
        batcmd= 'printf "si SWD\nspeed 4000\ndevice nrf51822\nr\nmem32 10001080 3\nexit" | JLinkExe'
        result= subprocess.check_output(batcmd, shell=True)
        if not '10001080' in result:
            return (False, False, result)
        for line in result.splitlines():
            if '10001080' in line:
                words= line.split()
                self.curDeviceVersion= words[words.index('=')+1]
                self.curLot= words[words.index('=')+2]
                self.curTimeStamp= words[words.index('=')+3]
                break
        if self.curLot[4] != 'D' or int(self.curTimeStamp, 16) > int(self.getTimeStamp(), 16) or int(self.curTimeStamp, 16) < 1451606399:
            return (True, False, result)
        else:
            return (True, True, result)

    def updateResultBox(self):
        pal= QtGui.QPalette()
        textc= QtGui.QColor(255, 255, 255)
        versame.view.viewWidget.resultBox.setAlignment(QtCore.Qt.AlignCenter)
        if self.resultFlag == True:
            versame.view.viewWidget.resultBox.insertPlainText('\n')
            versame.view.viewWidget.resultBox.insertPlainText('PASS')
            bgc= QtGui.QColor(0, 255, 0)
            pal.setColor(QtGui.QPalette.Base, bgc)
            pal.setColor(QtGui.QPalette.Text, textc)
            versame.view.viewWidget.resultBox.setPalette(pal)
        else:
            versame.view.viewWidget.resultBox.insertPlainText('\n')
            versame.view.viewWidget.resultBox.insertPlainText('FAIL')
            bgc= QtGui.QColor(255, 0, 0)
            pal.setColor(QtGui.QPalette.Base, bgc)
            pal.setColor(QtGui.QPalette.Text, textc)
            versame.view.viewWidget.resultBox.setPalette(pal)

    def clearResultBox(self):
        pal= QtGui.QPalette()
        textc= QtGui.QColor(255, 255, 255)
        versame.view.viewWidget.resultBox.clear()
        bgc= QtGui.QColor(128, 128, 128)
        pal.setColor(QtGui.QPalette.Base, bgc)
        pal.setColor(QtGui.QPalette.Text, textc)
        versame.view.viewWidget.resultBox.setPalette(pal)

    def labelPrint(self, lot, timeStamp):
        labelSerial= str(lot[4:].upper() + timeStamp.upper())
        xLabel= Model.labelX
        yLabel= Model.labelY
        xLabel2= xLabel
        yLabel2= str(int(yLabel) + 190)
        file= open("zebra.zpl", "w")
        file.write("^XA\n")
        file.write("^FO%s,%s\n" % (xLabel, yLabel))
        file.write("^BQ,2,7\n")
        file.write("^FDHM,A%s^FS\n" % labelSerial)
        file.write("^FO%s,%s\n" % (xLabel2, yLabel2))
        file.write("^A0, 20, 30\n")
        file.write("^FD%s^FS\n" % labelSerial)
        file.write("^XZ\n")
        file.close()
        batcmd= 'lpr -P ZT230 -o raw zebra.zpl'
        result= subprocess.check_output(batcmd, shell=True)

        #labelSerial= '"'+labelSerial+'"'
        label = """
N
B20,0,0,1A,2,4,50,B,"DEAF1234"
P1
"""
        #label= label.replace('"DEAF1234"', labelSerial)
        #self.printer.output(label)

class View(QtGui.QMainWindow):

    def __init__(self, parent= None):
        super(View, self).__init__(parent)
        self.viewWidget= ViewWidget(self)
        self.setCentralWidget(self.viewWidget)
        self.resize(800, 600)

        self.createAction()
        self.createMenu()

    #def updatePort(self):
    #    ports= versame.model.ports
    #    for port in ports:
    #        entry= self.configMenu.addAction(port)
    #        self.connect(entry, QtCore.SIGNAL('triggered()'), versame.model.init_ser())

    def createAction(self):
        self.action= QtGui.QAction(self.tr("&Set"), self, statusTip='Set')
        self.connect(self.action, QtCore.SIGNAL("triggered()"), self.showPasswordlPanel)

    def createMenu(self):
        self.menu= QtGui.QMenu(self.tr("&Configuration"), self)
        self.menu.addAction(self.action)
        self.menuBar().addMenu(self.menu)

    def showPasswordlPanel(self):
        self.passwordPanel = PasswordPanel()
        self.passwordPanel.show()

class ViewWidget(QtGui.QWidget):

    def __init__(self, parent= None):
        super(ViewWidget, self).__init__(parent)

        font= QtGui.QFont()
        font.setBold(True)
        font.setPointSize(25)
        self.label= QtGui.QLabel('Versame Starling Tester ' + Model.GUIVersion)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        widget1= QtGui.QWidget(self)
        widget1.setGeometry(QtCore.QRect(20, 20, 742, 42))
        h1= QtGui.QVBoxLayout(widget1)
        h1.setMargin(6)
        h1.setSpacing(6)
        h1.addWidget(self.label)

        self.log= QtGui.QTextEdit()
        self.log.setReadOnly(True)
        self.log.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        sizePolicy= QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.log.setSizePolicy(sizePolicy)
        widget2= QtGui.QWidget(self)
        widget2.setGeometry(QtCore.QRect(378, 80, 402, 442))
        h3= QtGui.QVBoxLayout(widget2)
        h3.setMargin(11)
        h3.setSpacing(0)
        h3.addWidget(self.log)

        font= QtGui.QFont()
        font.setPointSize(25)
        self.testAutoButt= QtGui.QPushButton('START')
        self.testAutoButt.setFont(font)
        self.testAutoButt.setMinimumSize(QtCore.QSize(0, 120))
        self.stopButt= QtGui.QPushButton('STOP')
        self.stopButt.setFont(font)
        self.stopButt.setMinimumSize(QtCore.QSize(0, 120))
        self.resultBox= QtGui.QTextEdit()
        self.resultBox.setReadOnly(True)
        self.resultBox.setAlignment(QtCore.Qt.AlignCenter)
        self.resultBox.setMinimumSize(QtCore.QSize(0, 40))
        self.resultBox.setFont(font)
        pal= QtGui.QPalette()
        bgc= QtGui.QColor(128, 128, 128)
        pal.setColor(QtGui.QPalette.Base, bgc)
        textc= QtGui.QColor(255, 255, 255)
        pal.setColor(QtGui.QPalette.Text, textc)
        self.resultBox.setPalette(pal)
        widget3= QtGui.QWidget(self)
        widget3.setGeometry(QtCore.QRect(20, 80, 320, 362))
        h4= QtGui.QVBoxLayout(widget3)
        h4.setMargin(11)
        h4.setSpacing(11)
        h4.addWidget(self.testAutoButt)
        h4.addWidget(self.stopButt)
        h4.addWidget(self.resultBox)

class PasswordPanel(QtGui.QWidget):
    def __init__(self, parent = None):
        super(PasswordPanel, self).__init__(parent)
        self.setFixedSize(300, 200)
        self.label= QtGui.QLabel('Please input password')
        self.textbox= QtGui.QLineEdit()
        self.textbox.setEchoMode(QtGui.QLineEdit.Password)
        self.butt= QtGui.QPushButton('OK')
        h= QtGui.QVBoxLayout()
        h.addWidget(self.label)
        h.addWidget(self.textbox)
        h.addWidget(self.butt)

        layout= QtGui.QHBoxLayout()
        layout.addLayout(h)

        self.setLayout(layout)
        self.createAction()

    def createAction(self):
        self.textbox.returnPressed.connect(self.compare)
        self.butt.clicked.connect(self.compare)

    def compare(self):
        text= self.textbox.text()
        password= 'deafbeef'

        if text == password:
            self.configure= ConfigurePanel()
            self.configure.show()
            self.close()
        else:
            self.textbox.clear()

class ConfigurePanel(QtGui.QWidget):
    def __init__(self, parent = None):
        super(ConfigurePanel, self).__init__(parent)
        self.setFixedSize(300, 400)
        self.label= QtGui.QLabel('Port Configuration')
        self.portCombo= QtGui.QComboBox()
        Model.UARTPorts= versame.model.serial_ports()
        self.portCombo.addItems(Model.UARTPorts)
        self.label2= QtGui.QLabel('H/w Rev')
        self.hwrev= QtGui.QComboBox()
        self.hwrev.addItem('00C2')
        self.label3= QtGui.QLabel('Factory')
        self.fac= QtGui.QComboBox()
        self.fac.addItem('D_Wynnewood')
        self.label4= QtGui.QLabel('Line')
        self.ll= QtGui.QComboBox()
        llList= ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10']
        self.ll.addItems(llList)
        llIndex= llList.index(Model.llText)
        self.ll.setCurrentIndex(llIndex)
        self.label5= QtGui.QLabel('Shift')
        self.shift= QtGui.QComboBox()
        shiftList= ['1', '2']
        self.shift.addItems(shiftList)
        shiftIndex= shiftList.index(Model.shiftText)
        self.shift.setCurrentIndex(shiftIndex)
        self.okButt= QtGui.QPushButton('OK')
        self.cancelButt= QtGui.QPushButton('Cancel')
        self.debugButt= QtGui.QPushButton('Debug')
        self.labelButt= QtGui.QPushButton('Label Position')

        h= QtGui.QVBoxLayout()
        h.addWidget(self.label)
        h.addWidget(self.portCombo)
        h.addWidget(self.label2)
        h.addWidget(self.hwrev)
        h.addWidget(self.label3)
        h.addWidget(self.fac)
        h.addWidget(self.label4)
        h.addWidget(self.ll)
        h.addWidget(self.label5)
        h.addWidget(self.shift)
        h2= QtGui.QHBoxLayout()
        h2.addWidget(self.okButt)
        h2.addWidget(self.cancelButt)

        layout= QtGui.QVBoxLayout()
        layout.addLayout(h)
        layout.addLayout(h2)
        layout.addWidget(self.labelButt)
        layout.addWidget(self.debugButt)

        self.setLayout(layout)
        self.createAction()

    def createAction(self):
        self.portCombo.activated.connect(self.selectPort)
        self.okButt.clicked.connect(self.setLot)
        self.cancelButt.clicked.connect(self.cancel)
        self.debugButt.clicked.connect(self.debug)
        self.labelButt.clicked.connect(self.labelPosition)

    def selectPort(self):
        Model.UARTport= str(self.portCombo.currentText())
        versame.model.init_ser()

    def setLot(self):
        Model.hwrevText= str(self.hwrev.currentText())
        Model.facText= str(self.fac.currentText())
        Model.llText= str(self.ll.currentText())
        Model.shiftText= str(self.shift.currentText())
        Model.lot= Model.hwrevText + Model.facText[0] + Model.llText + Model.shiftText
        Model.UARTport= str(self.portCombo.currentText())
        self.close()

    def cancel(self):
        self.close()

    def debug(self):
        Model.UARTport= str(self.portCombo.currentText())
        debugPanel.show()
        self.close()

    def labelPosition(self):
        self.labelPosition= LabelPanel()
        self.labelPosition.show()

class LabelPanel(QtGui.QWidget):
    def __init__(self, parent = None):
        super(LabelPanel, self).__init__(parent)
        self.setFixedSize(300, 200)
        self.label= QtGui.QLabel('Label Position')
        self.labelX= QtGui.QLabel('X')
        self.xPos= QtGui.QLineEdit(Model.labelX)
        self.labelY= QtGui.QLabel('Y')
        self.yPos= QtGui.QLineEdit(Model.labelY)
        self.okButt= QtGui.QPushButton('OK')
        self.cancelButt= QtGui.QPushButton('Cancel')

        h1= QtGui.QHBoxLayout()
        h1.addWidget(self.labelX)
        h1.addWidget(self.xPos)
        h2= QtGui.QHBoxLayout()
        h2.addWidget(self.labelY)
        h2.addWidget(self.yPos)
        h3= QtGui.QHBoxLayout()
        h3.addWidget(self.okButt)
        h3.addWidget(self.cancelButt)
        layout= QtGui.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addLayout(h1)
        layout.addLayout(h2)
        layout.addLayout(h3)

        self.setLayout(layout)
        self.createAction()

    def createAction(self):
        self.okButt.clicked.connect(self.setXY)
        self.cancelButt.clicked.connect(self.close)

    def setXY(self):
        Model.labelX= str(self.xPos.text())
        Model.labelY= str(self.yPos.text())
        self.close()

class DebugPanel(QtGui.QWidget):
    def __init__(self, parent = None):
        super(DebugPanel, self).__init__(parent)
        self.setFixedSize(800, 600)

        self.label= QtGui.QLabel('Debug Mode')
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        h1= QtGui.QVBoxLayout()
        h1.addWidget(self.label)

        #self.eraseDeviceButt= QtGui.QPushButton('Erase Device')
        self.erase_writeUICRButt= QtGui.QPushButton('Erase and Write UICR')
        self.flashSoftButt= QtGui.QPushButton('Flash SoftDevice')
        self.flashTesterButt= QtGui.QPushButton('Flash Tester')
        self.flashBootloaderButt= QtGui.QPushButton('Flash Bootloader')
        h2= QtGui.QVBoxLayout()
        #h2.addWidget(self.eraseDeviceButt)
        h2.addWidget(self.erase_writeUICRButt)
        h2.addWidget(self.flashSoftButt)
        h2.addWidget(self.flashTesterButt)
        h2.addWidget(self.flashBootloaderButt)

        self.testCombo= QtGui.QComboBox()
        self.testButt= QtGui.QPushButton('Test')
        self.stopButt= QtGui.QPushButton('Stop')
        h3= QtGui.QVBoxLayout()
        h4= QtGui.QHBoxLayout()
        h4.addWidget(self.testButt)
        h4.addWidget(self.stopButt)
        h3.addWidget(self.testCombo)
        h3.addLayout(h4)

        self.flashProdButt= QtGui.QPushButton('Flash Product Firmware')
        self.saveButt= QtGui.QPushButton('Save')
        self.printButt= QtGui.QPushButton('Print')
        h5= QtGui.QVBoxLayout()
        h5.addWidget(self.flashProdButt)
        h5.addWidget(self.saveButt)
        h5.addWidget(self.printButt)

        self.prodLabel= QtGui.QLabel('Log Product ID')
        self.prodTextbox= QtGui.QLineEdit()
        self.searchButt= QtGui.QPushButton('Search')
        h6= QtGui.QHBoxLayout()
        h6.addWidget(self.prodLabel)
        h6.addWidget(self.prodTextbox)
        h6.addWidget(self.searchButt)

        h7= QtGui.QVBoxLayout()
        h7.addLayout(h2)
        h7.addLayout(h3)
        h7.addLayout(h5)
        h7.addLayout(h6)

        self.log= QtGui.QTextEdit()
        self.log.setReadOnly(True)

        h8= QtGui.QHBoxLayout()
        h8.addLayout(h7)
        h8.addWidget(self.log)

        layout= QtGui.QVBoxLayout()
        layout.addLayout(h1)
        layout.addLayout(h8)

        self.setLayout(layout)
        self.createAction()

    def createAction(self):
        #self.eraseDeviceButt.clicked.connect(self.eraseDevice)
        self.erase_writeUICRButt.clicked.connect(self.erase_writeUICR)
        self.flashSoftButt.clicked.connect(lambda : self.flashBin(versame.model.softDevPathAddr, 1))
        self.flashTesterButt.clicked.connect(lambda : self.flashBin(versame.model.testerPathAddr, 2))
        self.flashBootloaderButt.clicked.connect(lambda  : self.flashBin(versame.model.bootloaderPathAddr, 3))
        self.testButt.clicked.connect(versame.model.run_function)
        self.stopButt.clicked.connect(lambda : versame.model.stop_debug('stop'))
        self.flashProdButt.clicked.connect(self.flashProd)
        self.saveButt.clicked.connect(versame.model.save)
        self.searchButt.clicked.connect(versame.model.searchLog)
        self.printButt.clicked.connect(self.debugPrint)

    def eraseDevice(self):
        if 'Bluetooth' in Model.UARTport or Model.UARTport == None:
            versame.model.debug_show('\nPlease check UART port connection and selection\n')
            return
        if Model.lot == 'FFFFFFFF':
            versame.model.debug_show('\nLot name is: FFFFFFFF, Please select Lot name.\n')
            return
        result, resultFilter= versame.model.eraseDevice()
        if 'jLink' in resultFilter:
            versame.model.debug_show(result)
            return
        versame.model.saveDebugLog('\r--- {Session Start} Lot Name: "%s", TimeStamp: "%s" ---\n' %(Model.writeLot, Model.timeStamp) )
        versame.model.debug_show(result)

    def erase_writeUICR(self):
        if 'Bluetooth' in Model.UARTport or Model.UARTport == None:
            versame.model.debug_show('\nPlease check UART port connection and selection\n')
            return
        if Model.lot == 'FFFFFFFF':
            versame.model.debug_show('\nLot name is: FFFFFFFF, Please select Lot name.\n')
            return
        result, resultFilter= versame.model.eraseDevice()
        if 'jLink' in resultFilter:
            versame.model.debug_show(result)
            return
        versame.model.saveDebugLog('\r--- {Session Start} Lot Name: "%s", TimeStamp: "%s" ---\n' %(Model.writeLot, Model.timeStamp) )
        versame.model.debug_show(result)
        result2, resultFilter2= versame.model.writeUICR()
        versame.model.debug_show(result2)

    def flashBin(self, path, index):
        versame.model.flag= True
        time.sleep(1)
        versame.model.flag= False
        result, resultFilter= versame.model.flashbin(path, index)
        if index == 3:
            #time.sleep(1)
            self.testCombo.clear()
            self.testCombo.addItems(versame.model.commands)
            self.testCombo.update()
        versame.model.debug_show(result)

    def flashProd(self):
        result, resultFilter= versame.model.readUICR()
        versame.model.debug_show(result)
        versame.model.saveDebugLog('\r--- {Session END} ---\n')

    def debugPrint(self):
        batcmd= 'printf "si SWD\nspeed 4000\ndevice nrf51822\nr\nmem32 10001080 3\nexit" | JLinkExe'
        result= subprocess.check_output(batcmd, shell=True)
        if not '10001080' in result:
            versame.model.debug_show('Please check JLink and Power connection\n')
            return
        for line in result.splitlines():
            if '10001080' in line:
                words= line.split()
                deviceVersion= words[words.index('=')+1]
                lot= words[words.index('=')+2]
                timeStamp= words[words.index('=')+3]
        if deviceVersion != Model.deviceVersion or not lot.startswith('00C2D') or int(timeStamp, 16) > int(versame.model.getTimeStamp(), 16) or int(timeStamp, 16) < 1451606399:
            versame.model.debug_show('Serial Number is wrong, please click Start in Normal Mode.\n')
            return
        message= 'Print Serial Number: %s\n' % (lot[4:].upper() + timeStamp.upper())
        versame.model.debug_show(message)
        versame.model.labelPrint(lot, timeStamp)

class Controller():

    def __init__(self):
        self.model= Model()
        self.view= View()
        self.createConnection()

    def createConnection(self):
        self.view.viewWidget.stopButt.clicked.connect(lambda : self.model.stop('stop'))
        self.view.viewWidget.testAutoButt.clicked.connect(self.model.autoTest)

class RunThread(QtCore.QThread):

    data_run = QtCore.pyqtSignal(object)

    def __init__(self, text):
        QtCore.QThread.__init__(self)
        self.text = text

    def run(self):
        input= 'test ' + self.text
        versame.model.init_ser()
        versame.model.writeCommand(input)
        out= ''
        self.data_run.emit('\n')
        while not 'END' in out:
            out= versame.model.getOut()
            if out != '':
                self.data_run.emit('%s' % out)
            if versame.model.flag == True:
                return

class MicThread(QtCore.QThread):

    data_run = QtCore.pyqtSignal(object)

    def __init__(self, text):
        QtCore.QThread.__init__(self)
        self.text = text

    def run(self):
        input= 'test mic'
        versame.model.init_ser()
        versame.model.writeCommand(input)
        time.sleep(1)
        out= versame.model.getOut()
        self.data_run.emit('%s' % out)
        versame.model.playmusic(versame.model.soundPath)
        out= versame.model.getOut()
        if 'OK' in out:
            message= '\n[FAIL] dpot error.\n'
            self.data_run.emit('%s' % message)
            self.data_run.emit('%s' % out)
            return
        versame.model.playmusic(versame.model.soundPath2)
        while not 'END' in out:
            out= versame.model.getOut()
            if out != '':
                self.data_run.emit('%s' % out)
            if versame.model.flag == True:
                return

class StopThread(QtCore.QThread):

    data_run = QtCore.pyqtSignal(object)
    result_run= QtCore.pyqtSignal(object)
    log_run= QtCore.pyqtSignal(object)

    def __init__(self, text):
        QtCore.QThread.__init__(self)
        self.text = text

    def dataShow(self, dataFilter, dataLog):
        self.data_run.emit(dataFilter)
        dataLog= versame.model.processLog(dataLog)
        self.log_run.emit(dataLog)

    def resultFailShow(self):
        versame.model.resultFlag= False
        self.result_run.emit('%s' % versame.model.resultFlag)
        self.log_run.emit('\r--- {Session END} ---\n')

    def run(self):
        versame.model.flag= True
        time.sleep(1)
        input= 'test stop'
        versame.model.writeCommand(input)
        out= versame.model.getOut()
        outFilter= versame.model.textInitialFilter(out)
        self.dataShow(outFilter, out)
        self.resultFailShow()
        versame.model.flag= False

class StopDebugThread(QtCore.QThread):

    data_run = QtCore.pyqtSignal(object)

    def __init__(self, text):
        QtCore.QThread.__init__(self)
        self.text = text

    def run(self):
        #self.adapter.stop_scan()
        #versame.device.disconnect()
        versame.model.flag= True
        time.sleep(1)
        input= 'test stop'
        versame.model.init_ser()
        versame.model.writeCommand(input)
        out= versame.model.getOut()
        self.data_run.emit('%s' % out)
        versame.model.flag= False

class BleThread(QtCore.QThread):

    data_run = QtCore.pyqtSignal(object)

    def __init__(self, testble):
        QtCore.QThread.__init__(self)
        self.testble = testble

    def run(self):
        input= 'test ble'
        versame.model.init_ser()
        versame.model.writeCommand(input)
        out= versame.model.getOut()
        versame.model.flag = True
        time.sleep(1)
        versame.model.flag = False
        self.data_run.emit('%s' % out)
        versame.model.ble.initialize()
        versame.model.testble()
        time.sleep(0.5)
        self.data_run.emit('The RSSI value is %s \n' % versame.model.bleRSSI)
        if(int(versame.model.bleRSSI) <= versame.model.bleRSSILimit
           or versame.model.bleManufacturerFlag
           or versame.model.bleModelFlag
           or versame.model.bleHardRevFlag
           or versame.model.bleSoftRevFlag
           or versame.model.bleServiceUUIDFlag
           or versame.model.bleCharUUIDFlag):
            result= ''
            if int(versame.model.bleRSSI) <= versame.model.bleRSSILimit:
                result+= '\n[FAIL] RSSI signal is Poor.\n'
            if versame.model.bleManufacturerFlag:
                result+= '[FAIL] Manufacturer information is wrong.\n'
            if versame.model.bleModelFlag:
                result+= '[FAIL] Model information is wrong.\n'
            if versame.model.bleHardRevFlag:
                result+= '[FAIL] Hardware Revision information is wrong.\n'
            if versame.model.bleSoftRevFlag:
                result+= '[FAIL] Software Revision information is wrong.\n'
            if versame.model.bleServiceUUIDFlag:
                result+= '[FAIL] Service UUID information is wrong.\n'
            if versame.model.bleCharUUIDFlag:
                result+= '[FAIL] Characteristics UUID information is wrong.\n'
            self.data_run.emit('%s' % result)
            input= 'test stop'
            versame.model.writeCommand(input)
            out= versame.model.getOut()
            #self.data_run.emit('%s' % out)
            return

        while not 'END' in out:
            out= versame.model.getOut()
            if out != '':
                self.data_run.emit('%s' % out)
            if versame.model.flag == True:
                return

class RunAllThread(QtCore.QThread):

    data_run = QtCore.pyqtSignal(object)
    result_run= QtCore.pyqtSignal(object)
    log_run = QtCore.pyqtSignal(object)

    def __init__(self, text):
        QtCore.QThread.__init__(self)
        self.text = text

    def dataShow(self, dataFilter, dataLog):
        self.data_run.emit(dataFilter)
        dataLog= versame.model.processLog(dataLog)
        self.log_run.emit(dataLog)

    def resultFailShow(self):
        versame.model.resultFlag= False
        self.result_run.emit('%s' % versame.model.resultFlag)
        self.log_run.emit('\r--- {Session END} ---\n')

    def run(self):
        if 'Bluetooth' in Model.UARTport or Model.UARTport == None:
            message= 'Please check UART port connection and port selection\n'
            self.dataShow(message, message)
            self.resultFailShow()
            return
        if Model.lot == 'FFFFFFFF':
            message= 'Lot name is: FFFFFFFF, Please select Lot name.\n'
            self.dataShow(message, message)
            self.resultFailShow()
            return

        result, resultFilter= versame.model.eraseDevice()
        if 'jLink' in resultFilter:
            self.dataShow(resultFilter, result)
            self.resultFailShow()
            return

        self.log_run.emit('\r--- {Session Start} Lot Name: "%s", TimeStamp: "%s" ---\n' %(Model.writeLot, Model.timeStamp) )
        self.dataShow(resultFilter, result)
        if 'FAIL' in resultFilter or versame.model.flag == True:
            self.resultFailShow()
            return
        result, resultFilter= versame.model.writeUICR()
        self.dataShow(resultFilter, result)
        if 'FAIL' in resultFilter or versame.model.flag == True:
            self.resultFailShow()
            return
        result, resultFilter= versame.model.flashbin(versame.model.softDevPathAddr, 1)
        self.dataShow(resultFilter, result)
        if 'FAIL' in resultFilter or versame.model.flag == True:
            self.resultFailShow()
            return
        result, resultFilter= versame.model.flashbin(versame.model.testerPathAddr, 2)
        self.dataShow(resultFilter, result)
        if 'FAIL' in resultFilter or versame.model.flag == True:
            self.resultFailShow()
            return
        result, resultFilter= versame.model.flashbin(versame.model.bootloaderPathAddr, 3)
        self.dataShow(resultFilter, result)
        if 'FAIL' in resultFilter or versame.model.flag == True:
            self.resultFailShow()
            return

        #out= versame.model.getOut()
        time.sleep(1)
        input= 'test all'
        versame.model.writeCommand(input)
        out= ''
        while not 'END' in out:
            out= versame.model.getOut()
            if out != '':
                outFilter= versame.model.textInitialFilter(out)
                self.dataShow(outFilter, out)
            if versame.model.flag == True:
                return
            if 'FAIL' in out or 'ERROR' in out:
                input= 'test stop'
                time.sleep(0.5)
                versame.model.writeCommand(input)
                out= versame.model.getOut()
                outFilter= versame.model.textInitialFilter(out)
                self.dataShow(outFilter, out)
                self.resultFailShow()
                return
            if 'syllable' in out:
                #time.sleep(0.2)
                versame.model.playmusic(versame.model.soundPath)
                out= versame.model.getOut()
                if 'OK' in out:
                    message= '\n[FAIL] dpot error.\n'
                    self.dataShow(message, message)
                    outFilter= versame.model.textInitialFilter(out)
                    self.dataShow(outFilter, out)
                    input= 'test stop'
                    time.sleep(0.5)
                    versame.model.writeCommand(input)
                    out= versame.model.getOut()
                    outFilter= versame.model.textInitialFilter(out)
                    self.dataShow(outFilter, out)
                    self.resultFailShow()
                    return
                versame.model.playmusic(versame.model.soundPath2)
            if 'ADVERTISING' in out:
                if versame.model.bleFlag == True:
                    message= 'Ble is busy, please click Stop and try again.\n'
                    self.dataShow(message, message)
                time.sleep(0.5)
                versame.model.ble.initialize()
                versame.model.testble()
                time.sleep(0.5)
                message= 'The RSSI value is %s' % versame.model.bleRSSI
                self.dataShow('\n' + message, message)
                if(int(versame.model.bleRSSI) <= versame.model.bleRSSILimit
                   or versame.model.bleManufacturerFlag
                   or versame.model.bleModelFlag
                   or versame.model.bleHardRevFlag
                   or versame.model.bleSoftRevFlag
                   or versame.model.bleServiceUUIDFlag
                   or versame.model.bleCharUUIDFlag):
                    result= ''
                    if int(versame.model.bleRSSI) <= versame.model.bleRSSILimit:
                        result+= '\n[FAIL] RSSI signal is Poor.\n'
                    if versame.model.bleManufacturerFlag:
                        result+= '[FAIL] Manufacturer information is wrong.\n'
                    if versame.model.bleModelFlag:
                        result+= '[FAIL] Model information is wrong.\n'
                    if versame.model.bleHardRevFlag:
                        result+= '[FAIL] Hardware Revision information is wrong.\n'
                    if versame.model.bleSoftRevFlag:
                        result+= '[FAIL] Software Revision information is wrong.\n'
                    if versame.model.bleServiceUUIDFlag:
                        result+= '[FAIL] Service UUID information is wrong.\n'
                    if versame.model.bleCharUUIDFlag:
                        result+= '[FAIL] Characteristics UUID information is wrong.\n'
                    self.dataShow(result, result)
                    input= 'test stop'
                    versame.model.writeCommand(input)
                    self.resultFailShow()
                    return

        result, resultFilter= versame.model.readUICR()
        time.sleep(1.5)
        self.dataShow(resultFilter, result)
        if 'FAIL' in resultFilter:
            self.resultFailShow()
            return
        versame.model.resultFlag= True
        self.result_run.emit('%s' % versame.model.resultFlag)
        versame.model.labelPrint(Model.writeLot, Model.timeStamp.replace('0x', ''))
        message= 'Print Serial Number: %s' % (Model.writeLot[4:] + Model.timeStamp.replace('0x','').upper())
        self.dataShow(message, message)
        self.log_run.emit('\r--- {Session END} ---\n')
#self.init_ser()

class RunAllDebugThread(QtCore.QThread):

    data_run = QtCore.pyqtSignal(object)

    def __init__(self, text):
        QtCore.QThread.__init__(self)
        self.text = text

    def run(self):
        versame.model.flag= True
        time.sleep(1)
        versame.model.flag= False
        input= 'test all'
        versame.model.init_ser()
        versame.model.writeCommand(input)
        out= ''
        while not 'END' in out:
            out= versame.model.getOut()
            if out != '':
                self.data_run.emit('%s' % out)
            if versame.model.flag == True:
                return
            if 'syllable' in out:
                #time.sleep(0.2)
                versame.model.playmusic(versame.model.soundPath)
                out= versame.model.getOut()
                if 'OK' in out:
                    message= '\n[FAIL] dpot error.\n'
                    self.data_run.emit('%s' % message)
                    self.data_run.emit('%s' % out)
                versame.model.playmusic(versame.model.soundPath2)
            if 'ADVERTISING' in out:
                if versame.model.bleFlag == True:
                    self.data_run.emit('Ble is busy, please click Stop and try again.\n')
                time.sleep(0.5)
                versame.model.ble.initialize()
                versame.model.testble()
                time.sleep(0.5)
                self.data_run.emit('The RSSI value is %s \n' % versame.model.bleRSSI)
                if(int(versame.model.bleRSSI) <= versame.model.bleRSSILimit
                   or versame.model.bleManufacturerFlag
                   or versame.model.bleModelFlag
                   or versame.model.bleHardRevFlag
                   or versame.model.bleSoftRevFlag
                   or versame.model.bleServiceUUIDFlag
                   or versame.model.bleCharUUIDFlag):
                    result= ''
                    if int(versame.model.bleRSSI) <= versame.model.bleRSSILimit:
                        result+= '\n[FAIL] RSSI signal is Poor.\n'
                    if versame.model.bleManufacturerFlag:
                        result+= '[FAIL] Manufacturer information is wrong.\n'
                    if versame.model.bleModelFlag:
                        result+= '[FAIL] Model information is wrong.\n'
                    if versame.model.bleHardRevFlag:
                        result+= '[FAIL] Hardware Revision information is wrong.\n'
                    if versame.model.bleSoftRevFlag:
                        result+= '[FAIL] Software Revision information is wrong.\n'
                    if versame.model.bleServiceUUIDFlag:
                        result+= '[FAIL] Service UUID information is wrong.\n'
                    if versame.model.bleCharUUIDFlag:
                        result+= '[FAIL] Characteristics UUID information is wrong.\n'
                    self.data_run.emit('%s' % result)

if __name__ == '__main__':
    app= QtGui.QApplication(sys.argv)
    versame= Controller()
    debugPanel= DebugPanel()
    #versame.view.updatePort()
    versame.view.show()
    app.exec_()
