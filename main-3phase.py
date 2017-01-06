"""
This is ESP8266 micropython script designed to serve ESP8266 as web server showing readings from Microchip MCP39F521. 
Script was developed and tested on esp8266-20161110-v1.8.6.bin micropython.

Script listens on port 80 and implements following commands:

  'http://<esp8266_ip>'               - shows web page with MCP39F521 readings
  'http://<esp8266_ip>/json'          - sends json formated MCP39F521 readings
  'http://<esp8266_ip>/eng_acc=on'    - turns ON energy accumulation
  'http://<esp8266_ip>/eng_acc=off'   - turns OFF energy accumulation (and reset accumulated energy counters)
  'http://<esp8266_ip>/reboot'        - reboots ESP8266

  To setup ESP8266 with micropython pls look on various tutorials. There is plenty of them on Internet

  v3.21 04/01/2017
  (c) Piotr Oniszczuk
"""

ver = 3.21

#from ubinascii import hexlify
import uctypes
from time import sleep_ms
import socket
from micropython import mem_info
from machine import I2C, Pin, reset
bus =  I2C(scl=Pin(5), sda=Pin(2), freq=100000)

debug = 0
chip_id = 0

def send_raw_data_to_mcp39f521(chipid, buf):

    chip_addr = 0x74 + chipid

    try:
        bus.writeto(chip_addr, buf)
    except:
        print ('Erorr durring write on I2C bus...')


def get_raw_data_from_mcp39f521(chipid, buf):

    send_raw_data_to_mcp39f521(chipid,buf)

    sleep_ms(10)

    chip_addr = 0x74 + chipid

    buf = bytearray(b'\x00' * 35)
    try:
        bus.readfrom_into(chip_addr, buf)
        if (debug):
            print ('\nMCP39F521 returns following data:')
            print (hexlify(buf, b":"))
    except:
        print ('Erorr durring read on I2C bus...')

    return (buf)


def control_enery_acc_mcp39f521(chipid, state):
    if (state):
        # Write 0x01 at 0x0002 address 0x00DC (data sheet page29)
        buf = bytearray([0xA5, 0x0A, 0x41, 0x00, 0xDC, 0x4D, 0x02, 0x00, 0x01, 0x1C])
    else:
        # Write 0x00 at 0x0002 address 0x00DC (data sheet page29)
        buf = bytearray([0xA5, 0x0A, 0x41, 0x00, 0xDC, 0x4D, 0x02, 0x00, 0x00, 0x1B])

    send_raw_data_to_mcp39f521(chipid,buf)


def get_data_from_mcp39f521(chipid):

    # Read 32 bytes starting at 0x0002 address
    buf = bytearray([0xA5, 0x08, 0x41, 0x00, 0x02, 0x4E, 0x20, 0x5E])

    buf = get_raw_data_from_mcp39f521(chipid,buf)

    desc = {
    "SysStatus":    uctypes.UINT16 | 2,
    "SysVer":       uctypes.UINT16 | 4,
    "Voltage":      uctypes.UINT16 | 6,
    "Frequency":    uctypes.UINT16 | 8,
    "PwrFactor":    uctypes.INT16  | 12,
    "Current":      uctypes.UINT32 | 14,
    "ActivePwr":    uctypes.UINT32 | 18,
    "ReactvPwr":    uctypes.UINT32 | 22,
    "ApprntPwr":    uctypes.UINT32 | 26,
    }

    values = uctypes.struct(uctypes.addressof(buf), desc, uctypes.LITTLE_ENDIAN)

    SysVer    = values.SysVer
    SysStatus = values.SysStatus
    Voltage   = (values.Voltage)   / 10.0
    Current   = (values.Current)   / 10000.0
    Frequency = (values.Frequency) / 1000.0
    ActivePwr = (values.ActivePwr) / 100.0
    ReactvPwr = (values.ReactvPwr) / 100.0 
    ApprntPwr = (values.ApprntPwr) / 100.0
    PwrFactor = (values.PwrFactor) * 0.000030517578125

    # Read 32 bytes starting at 0x001E address
    buf = bytearray([0xA5, 0x08, 0x41, 0x00, 0x1E, 0x4E, 0x20, 0x7A])

    buf = get_raw_data_from_mcp39f521(chipid,buf)

    desc = {
    "ImportActEnergy":   uctypes.UINT64 | 2,
    "ExportActEnergy":   uctypes.UINT64 | 10,
    "ImportReactEnergy": uctypes.UINT64 | 18,
    "ExportReactEnergy": uctypes.UINT64 | 26,
    }

    values = uctypes.struct(uctypes.addressof(buf), desc, uctypes.LITTLE_ENDIAN)

    ImportActEnergy   = values.ImportActEnergy   / 1000000.0
    ExportActEnergy   = values.ExportActEnergy   / 1000000.0
    ImportReactEnergy = values.ImportReactEnergy / 1000000.0
    ExportReactEnergy = values.ExportReactEnergy / 1000000.0
    
    return [SysVer,    \
            SysStatus, \
            Voltage,   \
            Current,   \
            Frequency, \
            ActivePwr, \
            ReactvPwr, \
            ApprntPwr, \
            PwrFactor, \
            ImportActEnergy,  \
            ExportActEnergy,  \
            ImportReactEnergy,\
            ExportReactEnergy]






html_page = """<!DOCTYPE html>
<html>
<head><title>Pwr</title></head>
<body><h1>v%s</h1>
<table border="1"><tr><th></th><th>R</th><th>S</th><th>T</th></tr>%s</table>
</body>
</html>"""
# HTML page: 2 chars free out of 1024 send buffer

null_page = """%s"""
json_page = """
{
"line_R": {
%s
},
"line_S": {
%s
},
"line_T": {
%s
},
}
"""
    

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

print('\n-- MCP39F521 3-phase read agent v{} (4/01/2017)\n-- (c)Piotr Oniszczuk\n'.format(ver))

mem_info()

print('\n-- Now Listening on port 80...\n')

try:
    while True: 
        conn, addr = s.accept()
        print("Got request from %s" % str(addr)) 

        request = conn.recv(1024) 
        request = str(request)

        data_R = get_data_from_mcp39f521(0)
        data_S = get_data_from_mcp39f521(1)
        data_T = get_data_from_mcp39f521(2)

        vals = [['Voltage'               ,data_R[2], data_S[2], data_T[2],  'V'   ], \
                ['Current'               ,data_R[3], data_S[3], data_T[3],  'A'   ], \
                ['Frequency'             ,data_R[4], data_S[4], data_T[4],  'Hz'  ], \
                ['Active Pwr'            ,data_R[5], data_S[5], data_T[5],  'W'   ], \
                ['Reactive Pwr'          ,data_R[6], data_S[6], data_T[6],  'W'   ], \
                ['Apparent Pwr'          ,data_R[7], data_S[7], data_T[7],  'W'   ], \
                ['Power Factor'          ,data_R[8], data_S[8], data_T[8],  ' '   ], \
                ['Import Active Eng'     ,data_R[9], data_S[9], data_T[9],  'kWh' ], \
                ['Export Active Eng'     ,data_R[10],data_S[10],data_T[10], 'kWh' ], \
                ['Import Reactive Eng'   ,data_R[11],data_S[11],data_T[11], 'kWh' ], \
                ['Export Reactive Eng'   ,data_R[12],data_S[12],data_T[12], 'kWh' ]]

        json      = request.find('/json')
        reboot    = request.find('/reboot')
        eng_acc_on  = request.find('/eng_acc=on')
        eng_acc_off = request.find('/eng_acc=off')

        if reboot == 6:
            html = null_page
            response = html % '\n\nRebooting...\n\n'
            conn.send(response)
            conn.close()
            sleep_ms(3000)
            reset()
 
        elif json == 6:
            html = json_page
            rows_R = ['"%s":%.3f,' % (p[0], p[1]) for p in vals]
            rows_S = ['"%s":%.3f,' % (p[0], p[2]) for p in vals]
            rows_T = ['"%s":%.3f,' % (p[0], p[3]) for p in vals]
            response = html % ('\n'.join(rows_R), '\n'.join(rows_S), '\n'.join(rows_T)) 

        elif eng_acc_on == 6:
            control_enery_acc_mcp39f521(0, True)
            control_enery_acc_mcp39f521(1, True)
            control_enery_acc_mcp39f521(2, True)
            html = null_page
            response = html % '\n\nTurning ON Energy Accumulation...\n\n'

        elif eng_acc_off == 6:
            control_enery_acc_mcp39f521(0, False)
            control_enery_acc_mcp39f521(1, False)
            control_enery_acc_mcp39f521(2, False)
            html = null_page
            response = html % '\n\nTurning OFF Energy Accumulation...\n\n'

        else:
            rows = ['<tr><td>%s</td><td>%.3f %s</td><td>%.3f %s</td><td>%.3f %s</td></tr>' % (p[0], p[1], p[4], p[2], p[4], p[3], p[4]) for p in vals]
            html = html_page
            response = html % (ver, '\n'.join(rows))
 
        conn.send(response)
        conn.close()
        print('-- Before GC free: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
        gc.collect()
        print('-- After  GC free: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))


except:
        print ('\n\nException in main server loop. Rebooting...\n\n')
        sleep_ms(5000)
        reset()
