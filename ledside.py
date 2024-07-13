import bluetooth
import struct
from machine import Pin

led = Pin(15, Pin.OUT)

def ledtest(received_value):
    lighting = received_value % 2
    led.value(lighting)

class BLECentral:
    def __init__(self, name):
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self.ble_irq)
        self.conn_handle = None
        self.name = name
        self._start_scanning()

    def _start_scanning(self):
        self.ble.gap_scan(2000, 30000, 30000)
        print("Scanning...")

    def ble_irq(self, event, data):
        if event == 5:  # Scan result
            addr_type, addr, adv_type, rssi, adv_data = data
            if self.name.encode() in bytes(adv_data):
                print("Found device, connecting...")
                self.ble.gap_connect(addr_type, addr)
        elif event == 1:  # Central connected
            self.conn_handle, _, _ = data
            print("Connected")
            self.ble.gattc_discover_services(self.conn_handle)
        elif event == 2:  # Central disconnected
            self.conn_handle = None
            self._start_scanning()
            print("Disconnected")
        elif event == 9:  # Service discovered
            conn_handle, start_handle, end_handle, uuid = data
            if uuid == bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E"):
                self.ble.gattc_discover_characteristics(self.conn_handle, start_handle, end_handle)
        elif event == 11:  # Characteristic discovered
            conn_handle, def_handle, value_handle, properties, uuid = data
            if uuid == bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"):
                self.rx_handle = value_handle
        elif event == 18:  # Notification
            conn_handle, value_handle, notify_data = data
            received_value = struct.unpack('i', notify_data)[0]  # バイトデータを整数に変換
            print(f"Received: {received_value}")
            ledtest(received_value)

    def start(self):
        while True:
            pass

ble_central = BLECentral("Pico_Sender")
ble_central.start()


