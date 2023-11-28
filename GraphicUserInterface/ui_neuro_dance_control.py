import time
from multiprocessing.shared_memory import ShareableList

from serial.tools import list_ports
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from OperationSystem.Streaming.NeuroDanceEEGProcess import NeuroDanceDevice


class UINeuroDanceController:

    def __init__(self, win):
        self.win = win
        self.port_infos = []
        self.neuro_dance_device_thread = None
        self.devices = []

    def UI_init(self):
        self.win.acquisitionSystemChanged()
        self.win.NeuroDanceSerialConnectButton.clicked.connect(self.serial_connect)
        self.win.NeuroDanceDeviceConnectButton.clicked.connect(self.device_pair)
        self.win.ScanBlesButton.clicked.connect(self.device_scan)
        self.serial_thread = SerialScan()
        self.serial_thread.update_com_signal.connect(self.scan_serial)
        self.serial_thread.start()
        self.battery_info_timer = QTimer()
        self.battery_info_timer.timeout.connect(self.battery_info_get)
        self.battery_info_timer.start(3000)

    def device_scan(self):
        if self.neuro_dance_device_thread is not None:
            self.neuro_dance_device_thread.device_scan()

    def device_pair(self):
        name = self.win.BleComboBox.currentText()
        pair_device = None
        for device in self.devices:
            if device['name'] == name:
                pair_device = device
                break
        if pair_device is not None:
            self.neuro_dance_device_thread.device_pair(device['mac_bytes'])

    def battery_info_get(self):
        if self.neuro_dance_device_thread is not None:
            self.neuro_dance_device_thread.device_battery()
            status = self.neuro_dance_device_thread.is_device_connected()
            if status:
                self.win.NeuroDanceConnectStatusLabel.setText("True")
            else:
                self.win.NeuroDanceConnectStatusLabel.setText("False")


    def scan_serial(self, ports):
        self.win.NeuroDanceSerialPortsComboBox.clear()
        self.port_infos = []
        for port in ports:
            show_name = str(port.device) + " - " + str(port.description)
            self.port_infos.append({'name': show_name, 'port': port.device})
            self.win.NeuroDanceSerialPortsComboBox.addItem(show_name)

    def serial_connect(self):
        name = self.win.NeuroDanceSerialPortsComboBox.currentText()
        port = None
        for port_info in self.port_infos:
            if name == port_info['name']:
                port = port_info['port']
                break
        if port is not None:
            print("neuro dance port:{0}".format(port))
            if self.neuro_dance_device_thread is None:
                self.neuro_dance_device_thread = NeuroDanceDevice(port)
                self.neuro_dance_device_thread.device_list_signal.connect(self.devices_report)
                self.neuro_dance_device_thread.host_version_update_signal.connect(self.host_version_update)
                self.neuro_dance_device_thread.host_mac_update_signal.connect(self.host_mac_update)
                self.neuro_dance_device_thread.host_sn_update_signal.connect(self.host_sn_update)
                self.neuro_dance_device_thread.device_sn_update_signal.connect(self.device_sn_update)
                self.neuro_dance_device_thread.device_mac_update_signal.connect(self.device_mac_update)
                self.neuro_dance_device_thread.device_version_update_signal.connect(self.device_version_update)
                self.neuro_dance_device_thread.device_battery_update_signal.connect(self.device_battery_update)
                self.neuro_dance_device_thread.start()
                self.neuro_dance_device_thread.host_info()
                self.neuro_dance_device_thread.device_info()
                self.win.config.neuro_dance_serial_port = port
            else:
                self.neuro_dance_device_thread.close()
                self.neuro_dance_device_thread.start()

    def devices_report(self, devices):
        self.devices = []
        self.devices = devices
        self.win.BleComboBox.clear()
        for device in devices:
            self.win.BleComboBox.addItem(device['name'])

    def stop(self):
        if self.neuro_dance_device_thread is not None:
            self.neuro_dance_device_thread.close()
        self.battery_info_timer.stop()

    def host_mac_update(self, host_mac):
        self.win.NeuroDanceUSBMacInfo.setText(host_mac)

    def host_sn_update(self, host_sn):
        self.win.NeuroDanceUSBSNInfo.setText(host_sn)

    def host_version_update(self, host_version):
        self.win.NeuroDanceUSBVersionInfo.setText(host_version)

    def device_mac_update(self, device_mac):
        self.win.NeuroDanceDeviceMacInfo.setText(device_mac)

    def device_sn_update(self, device_sn):
        self.win.NeuroDanceDeviceSNInfo.setText(device_sn)

    def device_version_update(self, device_version):
        self.win.NeuroDanceDeviceVersionInfo.setText(device_version)

    def device_battery_update(self, device_battery):
        self.win.NeuroDanceBatteryInfo.setText(str(device_battery) + '%')


class SerialScan(QThread):
    ports_list = []
    update_com_signal = pyqtSignal(list)
    keep_scanning = False

    def __init__(self):
        super(SerialScan, self).__init__()

    def run(self):
        print("neuro dance start scanning serial com")
        self.keep_scanning = True
        # if ports changed, change UI
        while self.keep_scanning:
            ports = list(list_ports.comports())
            select_port = []
            device_list = []
            for port in ports:
                if "USB" in port.description:
                    select_port.append(port)
                    device_list.append(str(port.device) + " - " + str(port.description))
            if self.ports_list != device_list:
                self.ports_list = device_list
                self.update_com_signal.emit(select_port)
                print("serial devices updated: " + str(device_list[0:]))
        print("stop scanning serial com")
        self.wait()

    def stop_scan(self):
        self.keep_scanning = False

