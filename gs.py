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
# Send Command - UPDATED from gs_echo_test.py
# --------------------------
def send_cmd(cmd):
    # Add newline to command as in gs_echo_test.py for compatibility
    data = (cmd + "\n").encode()
    
    length = 14 + len(data)
    frame = bytearray([0x7E, length >> 8, length & 0xFF])
    checksum = 0

    def put(b):
        nonlocal checksum
        frame.append(b)
        checksum = (checksum + b) & 0xFF

    put(0x10)       # TX Request
    put(0x01)       # Frame ID
    
    # Add destination address to frame and checksum
    frame += DEST
    for b in DEST: 
        checksum = (checksum + b) & 0xFF

    put(0xFF)       # 16-bit dest address (high byte)
    put(0xFE)       # 16-bit dest address (low byte)
    put(0x00)       # Broadcast radius
    put(0x00)       # Options

    # Add command data to frame
    for b in data:
        put(b)

    # Calculate and append checksum
    frame.append((0xFF - checksum) & 0xFF)
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
    # Read telemetry frames
    tel = read_frame()
    if tel:
        print("RX:", tel)

    # Send commands from queue
    while not cmd_q.empty():
        c = cmd_q.get()
        send_cmd(c)
        print("GS COMMAND:", c)

    time.sleep(0.01)