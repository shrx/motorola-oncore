import time
import serial

def mas2deg(mas):
    return mas / 3600000

MODES = [
    "Code Search",
    "Code Acquire",
    "AGC Set",
    "Freq Acquire",
    "Bit Sync Detect",
    "Message Sync Detect",
    "Satellite Time Available",
    "Ephemeris Acquire",
    "Available for Position"
]

ACCURACIES = [
    0.0,
    2.4,
    3.4,
    4.85,
    6.85,
    9.65,
    13.65,
    24.0,
    48.0,
    96.0,
    192.0,
    384.0,
    768.0,
    1536.0,
    3072.0,
    6144.0,
    "∞"
]

CHANNEL_BYTES = 6

CODE_LOCATION = [
    "EXTERNAL",
    "INTERNAL"
]

ANTENNA_SENSE = [
    "OK",
    "OC",
    "UC",
    "NV"
]

RECEIVER_STATUS = [
    "Reserved",
    "Reserved",
    "Bad Geometry",
    "Acquiring Satellites",
    "Position Hold",
    "Propagate Mode",
    "2D Fix",
    "3D Fix"
]

UTC_OFFSET = [
    "NOT decoded",
    "decoded"
]

UTC_MODE = [
    "disabled",
    "enabled"
]

def getCheckSum(sentence):
    calc_cksum = 0
    for s in sentence:
        calc_cksum ^= ord(s)
    return bytes.fromhex(f"{calc_cksum:02x}")

def binaryCommand(cmd):
    return str.encode(cmd) + getCheckSum(cmd) + str.encode("\r\n")

ser = serial.Serial(port='/dev/ttyAMA0', baudrate=9600, timeout=2)
ser.write(binaryCommand("@@Ha\x00"))
time.sleep(1)
result = b""
while ser.inWaiting():
    result += ser.read(ser.inWaiting())
    time.sleep(1)
ser.close()

body = result[4:-3]
print(result)

# Date
print("Date")
month = int(body[0])
day = int(body[1])
# 2 bytes, MSB first
year = int.from_bytes(body[2:4], byteorder='big')
print(f"{month:02}/{day:02}/{year}")

# Time
print("Time")
hours = int(body[4])
minutes = int(body[5])
seconds = int(body[6])
# 4 bytes, MSB first
nanos = int.from_bytes(body[7:11], byteorder='big')
print(f"{hours}:{minutes:02}:{seconds:02}.{nanos:09}")

# Position
print("Position (Filtered or Unfiltered following Filter Select)")
lat_mas = int.from_bytes(body[11:15], byteorder='big', signed=True)
lon_mas = int.from_bytes(body[15:19], byteorder='big', signed=True)
gps_height = int.from_bytes(body[19:23], byteorder='big', signed=True)
msl_height = int.from_bytes(body[23:27], byteorder='big', signed=True)
print(f"lat:{mas2deg(lat_mas)}° lon:{mas2deg(lon_mas)}° GPS height:{gps_height/100}m MSL height:{msl_height/100}m")

print("Position (Always Unfiltered)")
lat_mas = int.from_bytes(body[27:31], byteorder='big', signed=True)
lon_mas = int.from_bytes(body[31:35], byteorder='big', signed=True)
gps_height = int.from_bytes(body[35:39], byteorder='big', signed=True)
msl_height = int.from_bytes(body[39:43], byteorder='big', signed=True)
print(f"lat:{mas2deg(lat_mas)}° lon:{mas2deg(lon_mas)}° GPS height:{gps_height/100}m MSL height:{msl_height/100}m")

# Speed
print("Speed/Heading")
speed_3d = int.from_bytes(body[43:45], byteorder='big')
speed_2d = int.from_bytes(body[45:47], byteorder='big')
heading = int.from_bytes(body[47:49], byteorder='big')
print(f"3D speed:{speed_3d/100}m/s 2D speed:{speed_2d/100}m/s 2D heading:{heading/10}°")

# Geometry
print("Geometry")
dop = int.from_bytes(body[49:51], byteorder='big')
print(f"{dop/10} DOP")

# Satellite Data
print("Satellite Data")
n_visible = int(body[51])
n_tracked = int(body[52])
print(f"visible:{n_visible} tracked:{n_tracked}")

# Channel Data
print("Channel Data")
for c in range(12):
    print(f"Channel {c}:")
    svid = int(body[53 + c*CHANNEL_BYTES])
    mode = int(body[54 + c*CHANNEL_BYTES])
    strength = int(body[55 + c*CHANNEL_BYTES])
    iode = int(body[56 + c*CHANNEL_BYTES])
    status = int.from_bytes(body[57 + c*CHANNEL_BYTES:59 + c*CHANNEL_BYTES], byteorder='big')
    accuracy = status & 0b1111
    unhealthy = bool((status >> 4) & 1)
    antispoof = bool((status >> 5) & 1)
    momentum = bool((status >> 6) & 1)
    position_fix = bool((status >> 7) & 1)
    parity_error = bool((status >> 8) & 1)
    invalid_data = bool((status >> 9) & 1)
    corrections_available = bool((status >> 10) & 1)
    time_solution = bool((status >> 11) & 1)
    narrow_band = bool((status >> 12) & 1)
    print(f"SVID:{svid} mode:\"{MODES[mode]}\" signal strength:{strength/255}% IODE:{iode}", end=" ")
    print(f"accuracy:{ACCURACIES[accuracy]}m - {ACCURACIES[accuracy+1]}m", end=" ")
    print(f"unhealthy:{unhealthy}", end=" ")
    print(f"anti-spoof flag:{antispoof}", end=" ")
    print(f"momentum alert:{momentum}", end=" ")
    print(f"used for position fix:{position_fix}", end=" ")
    print(f"parity error:{parity_error}", end=" ")
    print(f"invalid data:{invalid_data}", end=" ")
    print(f"differential corrections available:{corrections_available}", end=" ")
    print(f"used for time solution:{time_solution}", end=" ")
    print(f"narrow-band search mode:{narrow_band}")

# Receiver status
print("Receiver Status")
status = int.from_bytes(body[125:127], byteorder='big')
code = status & 1
antenna = (status >> 1) & 0b11
insufficient_visible = bool((status >> 3) & 1)
autosurvey = bool((status >> 4) & 1)
position_lock = bool((status >> 5) & 1)
differential_fix = bool((status >> 6) & 1)
cold_start = bool((status >> 7) & 1)
filter_reset = bool((status >> 8) & 1)
fast_acquisition = bool((status >> 9) & 1)
narrow_band = bool((status >> 10) & 1)
status_extra = (status >> 13) & 0b111
print(f"Code location:{CODE_LOCATION[code]}")
print(f"Antenna sense:{ANTENNA_SENSE[antenna]}")
print(f"Insufficient Visible Satellites:{insufficient_visible}")
print(f"Autosurvey Mode:{autosurvey}")
print(f"Position Lock:{position_lock}")
print(f"Differential Fix:{differential_fix}")
print(f"Cold Start:{cold_start}")
print(f"Filter Reset To Raw GPS Solution:{filter_reset}")
print(f"Fast Acquisition Position:{fast_acquisition}")
print(f"Narrow band tracking mode:{narrow_band}")
print(f"Status:{RECEIVER_STATUS[status_extra]}")

# reserved
# body[127:129]

# Oscillator and Clock Parameters
print("Oscillator and Clock Parameters")
bias = int.from_bytes(body[129:131], byteorder='big')
offset = int.from_bytes(body[131:135], byteorder='big')
temperature = int.from_bytes(body[135:137], byteorder='big')
print(f"Bias:{bias}ns offset:{offset/1000}kHz temperature:{temperature/2}°C")

# UTC Parameters
print("UTC Parameters")
params = int(body[137])
offset_value = status & 0b111111
offset = bool((params >> 6) & 1)
mode = bool((params >> 7) & 1)
print(f"UTC mode:{UTC_MODE[mode]} UTC offset:{UTC_OFFSET[offset]} UTC offset value:{offset_value}")

# GMT Offset
print("GMT Offset")
sign = int(body[138])
hour = int(body[139])
minute = int(body[140])
print(f"{'+' if sign == 0 else '-'}{hour:02}:{minute:02}")

# ID tag
id_tag = body[141:147].decode()
print(f"ID tag:{id_tag}")

# Message length
print(f"Message length:{len(result)}")
print()

print("Switching to NMEA-0183 format")
ser = serial.Serial(port='/dev/ttyAMA0', baudrate=9600, timeout=1)
ser.write(binaryCommand("@@Ci\x01"))
time.sleep(1)
result = ser.read(ser.inWaiting())
ser.close()
print()
time.sleep(10)

print("GPRMC Recommended Minimum Specific GPS/Transit Data")
ser = serial.Serial(port='/dev/ttyAMA0', baudrate=4800, timeout=1)
ser.write(str.encode("$PMOTG,RMC,0000\r\n"))
time.sleep(1)
result = b""
while ser.inWaiting():
    result += ser.read(ser.inWaiting())
    time.sleep(1)
ser.close()
try:
    print(result)
    result = result.decode().strip().split(",")
    
    # Status
    print("Status")
    print("valid" if result[1] == "A" else "invalid")
    
    # Time
    print("Time")
    if result[2] == "A":
        hour = result[1][:2]
        minute = result[1][2:4]
        second = result[1][4:6]
        millis = result[1][7:]
    else:
        hour = minute = second = millis = "??"
    print(f"{hour}:{minute}:{second}.{millis}")
    
    # Latitude
    print("Latitude")
    degrees = result[3][:2]
    minutes = result[3][2:]
    direction = result[4]
    print(f"{degrees}° {minutes}' {direction}")
    
    # Longitude
    print("Longitude")
    degrees = result[5][:3]
    minutes = result[5][3:]
    direction = result[6]
    print(f"{degrees}° {minutes}' {direction}")
    
    # Speed
    print("Speed over ground")
    speed = result[7] if result[2] == "A" else "??"
    print(f"{speed} kts")
    
    # Track made good
    print("Track made good")
    track = result[8] if result[2] == "A" else "??"
    print(f"{track}°")
    
    # UTC date
    print("UTC date of position fix")
    if result[2] == "A":
        day = result[9][:2]
        month = result[9][2:4]
        year = result[9][4:6]
    else:
        day = month = year = "??"
    print(f"{day}. {month}. '{year}")
    
    # Magnetic variation
    print("Magnetic variation")
    degrees = result[10] if result[2] == "A" else "??"
    sense = result[11] if result[2] == "A" else "??"
    print(f"{degrees}° {sense}")
except:
    pass
print()

print("Switching to Motorola binary format")
ser = serial.Serial(port='/dev/ttyAMA0', baudrate=4800, timeout=1)
ser.write(str.encode("$PMOTG,FOR,0\r\n"))
time.sleep(1)
result = ser.read(ser.inWaiting())
ser.close()
print()
time.sleep(10)

print("Getting receiver ID")
ser = serial.Serial(port='/dev/ttyAMA0', baudrate=9600, timeout=2)
ser.write(binaryCommand("@@Cj"))
time.sleep(1)
result = b""
while ser.inWaiting():
    result += ser.read(ser.inWaiting())
    time.sleep(1)
ser.close()
print(result.decode())
