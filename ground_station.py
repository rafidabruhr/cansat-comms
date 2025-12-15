import serial
import time
import threading
import queue

PORT = "COM4"
BAUD = 9600

# PUT FLIGHT XBEE ADDRESS HERE
DEST = bytes([0x00,0x13,0xA2,0x00,0x41,0x07,0x04,0x29])

ser = serial.Serial(PORT, BAUD, timeout=0.01)
cmd_q = queue.Queue()

def input_thread():
    while True:
        cmd = input()
        if cmd:
            cmd_q.put(cmd.strip())
threading.Thread(target=input_thread, daemon=True).start()

# --------------------------
# Send Command
# --------------------------
def send_cmd(cmd):
    data = cmd.encode()
    length = 14 + len(data)
    frame = bytearray([0x7E, length >> 8, length & 0xFF])
    s = 0

    def put(b):
        nonlocal s
        frame.append(b)
        s = (s + b) & 0xFF

    put(0x10)
    put(0x01)
    frame += DEST
    put(0xFF); put(0xFE)
    put(0x00); put(0x00)

    for c in data: put(c)

    frame.append((0xFF - s) & 0xFF)
    ser.write(frame)

# --------------------------
# Read Telemetry
# --------------------------
def read_frame():
    if ser.read(1) != b'\x7E':
        return None

    lb = ser.read(2)
    if len(lb) < 2:
        return None

    length = (lb[0] << 8 | lb[1])
    data = b""
    while len(data) < length + 1:
        chunk = ser.read(length + 1 - len(data))
        if not chunk:
            return None
        data += chunk

    if data[0] != 0x90:
        return None

    rf = data[12:-1]
    try:
        return rf.decode()
    except:
        return None

print("GS Ready")

# MAIN LOOP
while True:
    tel = read_frame()
    if tel:
        print("RX:", tel)

    while not cmd_q.empty():
        c = cmd_q.get()
        send_cmd(c)
        print("SENT:", c)

    time.sleep(0.01)