<div align="center">
<img src="assets/nasa-logo.png" height="120" alt="NASA"> &nbsp;&nbsp;&nbsp;&nbsp; <img src="assets/cansat-logo.png" height="120" alt="CanSat Competition — American Astronautical Society">
 
*CanSat Payload-GroundStation Communications Systems*
 
[![Payload](https://img.shields.io/badge/payload-Arduino%20C%2B%2B-00979D?style=for-the-badge&logo=arduino&logoColor=white)](./payload.ino)
[![Ground Station](https://img.shields.io/badge/ground%20station-Python%203-3776AB?style=for-the-badge&logo=python&logoColor=white)](./ground_station.py)
[![Radio](https://img.shields.io/badge/radio-XBee%20%2F%20ZigBee%20API-8A2BE2?style=for-the-badge)](#-the-protocol)
[![License](https://img.shields.io/badge/license-MIT-brightgreen?style=for-the-badge)](./LICENSE)
 
</div>
---


## Information

Picture a soda-can-sized satellite falling out of the sky (on purpose, gently, under a parachute). It has no cell signal, no Wi-Fi, no cry for help beyond a **900 MHz whisper**. This repo is that whisper — and the ears on the ground listening for it.

`cansat-comms` is the **two-sided radio brain** of a CanSat mission:

| Side | Lives on | Speaks |
|---|---|---|
| **Payload** | An Arduino tucked inside the can, falling through the sky | Altitude, temperature, pressure, GPS — once every second, whether you're listening or not |
| **Ground Station** | Your laptop, feet on solid ground | Commands going up, telemetry coming down, simultaneously, without missing a beat |

Both sides speak the exact same dialect: hand-rolled **XBee API frames**, byte-for-byte, checksum and all.

---

## The Anatomy

```
                         900 MHz RF LINK (XBee / ZigBee, API mode)
   ┌───────────────────┐   ════════════════════════════════════▶   ┌────────────────────────┐
   │      PAYLOAD       │        altitude · temp · pressure          │      GROUND STATION      │
   │   (payload.ino)    │              · lat · lon                   │    (ground_station.py)   │
   │                     │   ◀════════════════════════════════════   │                          │
   │  Arduino + XBee     │           uplink commands                 │   Python + pyserial      │
   └───────────────────┘                                            └────────────────────────┘
          │                                                                    │
          │  1 Hz heartbeat                                          background thread
          │  packet counter                                          hangs on stdin,
          │  synthetic sensor                                        queues commands,
          │  read (swap in                                           never blocks the
          │  real sensors here)                                      telemetry loop
          ▼                                                                    ▼
   "pkt,time,alt,temp,press,lat,lon"                              RX >> console
                                                                    TX << you, typing
```

---

## The Protocol

No libraries hiding the bytes from you. Every frame is built (and torn back apart) by hand, on **both** ends, so the two halves stay honest with each other.

```
  0x7E │ len_hi │ len_lo │ 0x10 │ frameID │  64-bit dest addr (8B) │ 0xFF │ 0xFE │ 0x00 │ 0x00 │ payload… │ checksum
   │        │        │      │      │              │                                              │
 start   length of  (below)  TX    outgoing      who this frame                                the whole frame,
 delim   the frame          frame  frame ID       is addressed to                               0xFF minus the
                             type                (payload ↔ ground)                              running sum
```

**Telemetry payload** (payload → ground), plain CSV riding inside the frame:

```
pkt , t(s) , altitude(m) , temperature(°C) , pressure(Pa) , latitude , longitude
 42 , 41.02,   118.37    ,      27.85       ,   100822     , 23.810512, 90.412331
```

**Uplink commands** (ground → payload) ride the *same* frame format in reverse — type a line into the ground station's terminal, and it's wrapped, checksummed, and shot skyward before your `Enter` key finishes bouncing.

> Swap the CSV fields for real sensor reads (BMP280, GPS module, whatever your can is carrying) — the frame plumbing doesn't care what's inside it.

---

## Getting Off the Ground

### 1. Flash the payload

```bash
# Open payload.ino in the Arduino IDE
# Wire your XBee to pins 9 (RX) / 10 (TX) via SoftwareSerial
# Set GS_ADDR[] to your ground station's XBee 64-bit address
# Upload, then watch it broadcast "FLIGHT READY" over Serial
```

### 2. Bring the ground station online

```bash
pip install pyserial
```

```python
# in ground_station.py, set:
PORT = "COM4"          # or "/dev/ttyUSB0" on Linux/macOS
DEST = bytes([...])    # your payload's XBee address
```

```bash
python ground_station.py
```

```
GS Ready
RX: 1,1.00,127.44,33.91,101422,23.810498,90.412550
RX: 2,2.00,142.08,29.03,100774,23.810533,90.412489
> abort_descent
SENT: abort_descent
```

Telemetry streams in on its own. Type anytime to send a command uplink — a background thread queues it so the radio never misses a beat waiting on your keyboard.

---

## Design Notes

- **Non-blocking by construction** — the ground station's input thread and telemetry loop never wait on each other. Bad connections don't freeze your console; a slow typist doesn't drop a packet.
- **Symmetric parsing** — the frame-builder and frame-reader logic is mirrored across C++ and Python so the protocol can't silently drift between payload and ground.
- **Fails loud, not silent** — malformed frames, bad checksums, and truncated reads are all caught and discarded rather than crashing the link.
- **Sensor-agnostic core** — the demo payload fakes its sensor data with `random()`; the frame format doesn't know or care, so swapping in real hardware is a one-function change.

---

## Roadmap Ideas

- [ ] Live plotting of altitude / descent-rate on the ground station
- [ ] Packet-loss and RSSI logging per session
- [ ] CSV/JSON telemetry logging to disk for post-flight analysis
- [ ] Swap synthetic sensor data for real BMP/GPS modules on the payload

---

<div align="center">

**Built for a CanSat mission — because the only thing worse than a hardware failure is a comms failure.**

`payload.ino` ⇄ 📡 ⇄ `ground_station.py`

</div>
