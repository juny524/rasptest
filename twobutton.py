import bluetooth
import struct
import machine
import _thread
import time

button_pin = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP)
button_pin2 = machine.Pin(18, machine.Pin.IN, machine.Pin.PULL_UP)
queue = []
lock = _thread.allocate_lock()

def button_polling():
    global queue
    while True:
        if not button_pin.value() and not button_pin2.value():  # ボタンが押されているとき
            with lock:
                queue.append(1)
            print("Button pressed, added 1 to queue")
            time.sleep(0.2)  # デバウンスのために少し待つ
        time.sleep(0.01)  # CPU負荷を下げるための短い待機


def button_handler(pin):
    global queue
    # ボタンが押されたときに呼び出される割り込みハンドラ
    if not pin.value():  # ボタンが押されているとき
        with lock:
            queue.append(1)
            print("queue.append(1)")
        print("Button pressed, added 1 to queue")

def button_handler2(pin):
    global queue
    # ボタンが押されたときに呼び出される割り込みハンドラ
    if not pin.value():  # ボタンが押されているとき
        with lock:
            queue.append(0)
            print("queue.append(0)")
        print("Button pressed, added 1 to queue")

#button_pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=button_handler)
#button_pin2.irq(trigger=machine.Pin.IRQ_FALLING, handler=button_handler2)

class BLEPeripheral:
    def __init__(self, name):
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self.ble_irq)
        self.conn_handle = None
        self.name = name
        self._start_advertising()

    def _start_advertising(self):
        adv_data = bytearray(b'\x02\x01\x06\x0b\x09' + self.name.encode())
        self.ble.gap_advertise(100, adv_data)
        print("Advertising...")

    def ble_irq(self, event, data):
        if event == 1:  # _IRQ_CENTRAL_CONNECT
            self.conn_handle, _, _ = data
            print("Connected")
            _thread.start_new_thread(button_polling, ())
        elif event == 2:  # _IRQ_CENTRAL_DISCONNECT
            self.conn_handle = None
            self._start_advertising()
            print("Disconnected")

    def send(self, data):
        if self.conn_handle is not None:
            self.ble.gatts_notify(self.conn_handle, self.tx_handle, data)
            print(f"Sent: {data}")

    def start(self):
        UART_SERVICE_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
        UART_TX_UUID = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
        UART_RX_UUID = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")

        self.tx = (UART_TX_UUID, bluetooth.FLAG_NOTIFY,)
        self.rx = (UART_RX_UUID, bluetooth.FLAG_WRITE,)

        self.service = (UART_SERVICE_UUID, (self.tx, self.rx,))
        ((self.tx_handle, self.rx_handle),) = self.ble.gatts_register_services((self.service,))

        
        count = 0
        while True:
            global queue
            #count = 1
            #data = struct.pack('i', count)  # 整数をバイト形式に変換
            with lock:
                if queue:
                    item = queue.pop(0)
                    data = struct.pack('i', item)
                    self.send(data)
                    print(f"Received {item} from queue")
            
            
            time.sleep(0.2)

ble_peripheral = BLEPeripheral("Pico_Sender")
ble_peripheral.start()
