import math
import sys
import os
import time
from multiprocessing.shared_memory import ShareableList

import numpy as np
from linkedlist import linkedlist

from OperationSystem.Streaming.BaseStreaming import BaseStreaming

current_path = os.getcwd()
sys.path.append(current_path + "\\OperationSystem\\Streaming\\neuro_dancer")
import neuro_dancer_base
from PyQt5.QtCore import pyqtSignal, QObject, QTimer


def create_event_share_list():
    try:
        global share_memory
        share_memory = ShareableList([None, None], name='Event')
    except Exception as e:
        print("event is Exists:{0}".format(e))


def create_device_battery_share():
    try:
        global share_memory
        share_memory = ShareableList([None], name='Battery')
    except Exception as e:
        print("Battery is Exists:{0}".format(e))


class NeuroDanceEEGThread(neuro_dancer_base.NeuroDancerBase, QObject, BaseStreaming):

    # 保留5分钟的数据
    linkedlist_length = 5 * 60 * 5
    eeg_datas = linkedlist()
    srate = 250
    real_sample_rate = 1000

    def __init__(self, config):
        self.com = config.neuro_dance_serial_port
        QObject.__init__(self, config=config)
        neuro_dancer_base.NeuroDancerBase.__init__(self)
        BaseStreaming.__init__(self, config=config)
        super(NeuroDanceEEGThread, self).open(self.com)


    def device_battery_received(self, battery):
        device = ShareableList(name='Battery')
        device[0] = battery

    def eeg_received(self, data):
        self.eeg_datas.add(data)
        if self.eeg_datas.length() > self.linkedlist_length:
            self.eeg_datas.removeHead()

    def readFixedData(self, startPoint, length):
        # 读取刺激之后的时间窗口长度，达到时间长度就返回
        event_info = ShareableList(name='Event')
        if event_info[0] is not None and event_info[1] is not None:
            stimulation_time = event_info[0]
            event_type = event_info[1]
            if stimulation_time > 0 and 0 < event_type < 200:
                print("stimulation_time:{0},eventType:{1}".format(stimulation_time,event_type))
                data = None
                while data is None:
                    data = self.read_packet_data(stimulation_time, length * 1000)
                data = np.array(data)
                data = self.preprocess(data)
                return data, event_type
        return None, None

    def readFlowData(self, startPoint, length):
        # 读取刺激之后的时间窗口长度，达到时间长度就返回
        event_info = ShareableList(name='Event')
        if event_info[0] is not None and event_info[1] is not None:
            stimulation_time = event_info[0]
            event_type = event_info[1]
            if stimulation_time > 0 and 0 < event_type < 200:
                print("stimulation_time:{0},eventType:{1}".format(stimulation_time, event_type))
                data = None
                while data is None:
                    data = self.read_packet_data(stimulation_time, length * 1000)
                data = self.preprocess(data)
                return data, event_type
        return None, None

    def read_packet_data(self, start_millis_second, read_millisecond):
        start_millis_second = start_millis_second + 2
        eeg_data = self.read_eeg_data(start_millis_second, read_millisecond)
        if eeg_data is not None and self.enable_eog:
            eog_data = self.read_eog_data(start_millis_second, read_millisecond)
            if eog_data is not None:
                eeg_data = np.vstack([eeg_data, eog_data])
        return eeg_data

    def read_eeg_data(self, start_millis_second, read_millisecond):
        packet_size = 200
        point_per_millis = self.real_sample_rate / 1000
        self.downRatio = int(self.srate * read_millisecond / 1000)
        # 以防万一，多取两个包，保证截取时足够长
        packet_num = math.ceil(read_millisecond * point_per_millis / packet_size) + 2
        eeg_data = None
        while self.eeg_datas.length() > 0:
            eeg_left = self.eeg_datas.eleAt(0)
            if eeg_left is None:
                break
            eeg_packet_start_millis = eeg_left['timestamp']
            if eeg_packet_start_millis + 200 < start_millis_second:
                self.eeg_datas.removeHead()
                continue
            # 掐头去尾
            eeg_start_position = int((start_millis_second - eeg_packet_start_millis) * point_per_millis)
            if eeg_start_position < 0:
                print("eeg time error:{0}".format(eeg_start_position))
                eeg_start_position = 0
            need_points = int(read_millisecond * point_per_millis)

            if self.eeg_datas.length() > packet_num:
                eeg_tmp = []
                eeg_seqs = []
                for i in range(packet_num):
                    chan = self.eeg_datas.eleAt(i)
                    eeg_tmp.append(chan['data'])
                    eeg_seqs.append(chan['seqNo'])
                eeg_data = np.hstack(eeg_tmp)
                eeg_data = eeg_data[:, eeg_start_position:(eeg_start_position + need_points)]
                print("eeg start points:{0},needPoints:{1},start_millis_second:{2},eeg_packet_millis:{3},eeg_data_shape:{4},eeq_seqs:{5}".format(
                        eeg_start_position, need_points, start_millis_second, eeg_packet_start_millis, eeg_data.shape,
                        eeg_seqs))
                break
        return eeg_data

    def connect(self):
        super(NeuroDanceEEGThread, self).enable_channels()

    def disconnect(self):
        super(NeuroDanceEEGThread, self).close()


class NeuroDanceDevice(neuro_dancer_base.NeuroDancerBase, QObject):
    device_list_signal = pyqtSignal(list)
    host_version_update_signal = pyqtSignal(str)
    host_sn_update_signal = pyqtSignal(str)
    host_mac_update_signal = pyqtSignal(str)
    device_mac_update_signal = pyqtSignal(str)
    device_sn_update_signal = pyqtSignal(str)
    device_version_update_signal = pyqtSignal(str)
    device_battery_update_signal = pyqtSignal(int)

    def __init__(self, com):
        self.com = com
        neuro_dancer_base.NeuroDancerBase.__init__(self)
        QObject.__init__(self)
        super(NeuroDanceDevice, self).open(com)

    def host_info(self):
        super(NeuroDanceDevice, self).host_version_info()
        time.sleep(0.01)
        super(NeuroDanceDevice, self).host_sn_info()
        time.sleep(0.01)
        super(NeuroDanceDevice, self).host_mac_info()

    def device_info(self):
        super(NeuroDanceDevice, self).device_version_info()
        time.sleep(0.01)
        super(NeuroDanceDevice, self).device_sn_info()
        time.sleep(0.01)
        super(NeuroDanceDevice, self).device_mac_info()


    def device_battery(self):
        super(NeuroDanceDevice, self).device_battery()

    def device_pair(self, mac):
        super(NeuroDanceDevice, self).pair(mac)

    def device_scan(self):
        super(NeuroDanceDevice, self).device_scan()

    def host_mac_received(self, host_mac):
        print("host mac:{0}".format(host_mac))
        self.host_mac_update_signal.emit(host_mac)

    def host_sn_received(self, host_sn):
        print("host sn:{0}".format(host_sn))
        self.host_sn_update_signal.emit(host_sn)

    def channel_received(self, data):
        print("channel_received")

    def host_version_received(self, host_version):
        print("host version:{0}".format(host_version))
        self.host_version_update_signal.emit(host_version)

    def device_mac_received(self, device_mac):
        print("device mac:{0}".format(device_mac))
        self.device_mac_update_signal.emit(device_mac)

    def device_sn_received(self, device_sn):
        self.device_sn_update_signal.emit(device_sn)

    def device_battery_received(self, battery):
        self.device_battery_update_signal.emit(battery)

    def device_version_received(self, device_version):
        self.device_version_update_signal.emit(device_version)

    def eeg_received(self, data):
        pass

    def devices_received(self, devices):
        self.device_list_signal.emit(devices)

