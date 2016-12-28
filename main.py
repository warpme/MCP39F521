
"""
This is ESP8266 micropython script designed to serve ESP8266 as web server showing readings from Microchip MCP39F521. 
Script was developed and tested on esp8266-20161110-v1.8.6.bin micropython.

Script listens on port 80 and implements following commands:

  'http://<esp8266_ip>'               - shows web page with MCP39F521 readings
  'http://<esp8266_ip>/raw'           - sends list of strings with MCP39F521 readings
  'http://<esp8266_ip>/json'          - sends json formated MCP39F521 readings
  'http://<esp8266_ip>/set_chip_id=x' - sets MCP39F521 chip ID to read. Allowed values are: 0(default), 1,2,3
                                        (chip ID is hardware defined by MCP39F521 A0 and A1 pins)
  'http://<esp8266_ip>/reboot'        - reboots ESP8266
  'http://<esp8266_ip>/debug=on'      - turns ON debbuging on micropython REPL console
  'http://<esp8266_ip>/debug=off'     - turns ON debbuging on micropython REPL console

  To setup ESP8266 with micropython pls look on various tutorials. There is plenty of them on Internet

  v1.0 28/12/2016
  (c) Piotr Oniszczuk
"""


from ubinascii import hexlify
from time import sleep_ms
import socket
from micropython import mem_info
from machine import I2C, Pin, reset
bus =  I2C(scl=Pin(5), sda=Pin(2), freq=100000)

debug = 0
chip_id = 0

def get_data_from_mcp39f521(chipid):

    if (debug):
        print ('\nI2C bus scan discovered devices:')
        devs = bus.scan()
        print (devs)

    chip_addr = 0x74 + chipid

    buf = bytearray([0xA5, 0x08, 0x41, 0x00, 0x02, 0x4E, 0x20, 0x5E])
    try:
        bus.writeto(chip_addr, buf)
    except:
        print ('Erorr durring write on I2C bus...')

    sleep_ms(10)

    buf = bytearray(b'\x00' * 35)
    try:
        bus.readfrom_into(chip_addr, buf)
        if (debug):
            print ('\nMCP39F521 returns following data:')
            print (hexlify(buf, b":"))
    except:
        print ('Erorr durring read on I2C bus...')
 
    SysStatus_L  = buf[2]
    SysStatus_H  = buf[3]  
    SysVer_L     = buf[4]
    SysVer_H     = buf[5]
    Voltage_L    = buf[6]
    Voltage_H    = buf[7]
    Frequency_L  = buf[8]
    Frequency_H  = buf[9]
    AnalogIn_L   = buf[10]
    AnalogIn_H   = buf[11]
    PwrFactor_L  = buf[12]
    PwrFactor_H  = buf[13]
    Current_LL   = buf[14]
    Current_L    = buf[15]
    Current_H    = buf[16]
    Current_HH   = buf[17]
    ActivePwr_LL = buf[18]
    ActivePwr_L  = buf[19]
    ActivePwr_H  = buf[20]
    ActivePwr_HH = buf[21]
    ReactvPwr_LL = buf[22]
    ReactvPwr_L  = buf[23]
    ReactvPwr_H  = buf[24]
    ReactvPwr_HH = buf[25]
    ApprntPwr_LL = buf[26]
    ApprntPwr_L  = buf[27]
    ApprntPwr_H  = buf[28]
    ApprntPwr_HH = buf[29]

    SysStatus = (SysStatus_H * 256) + SysStatus_L 
    SysVer    = (SysVer_H    * 256) + SysVer_L 
    Voltage   = ((Voltage_H   * 256) + Voltage_L) / 10.0 
    Frequency = ((Frequency_H * 256) + Frequency_H) / 1000.0
    PwrFactor = ((PwrFactor_H * 256) + PwrFactor_H) * 0.000030517578125
    Current   = ((Current_HH   * 16777216) + (Current_H   * 65536) + (Current_L   * 256) + Current_LL) / 10000.0
    ActivePwr = ((ActivePwr_HH * 16777216) + (ActivePwr_H * 65536) + (ActivePwr_L * 256) + ActivePwr_LL) / 100.0 
    ReactvPwr = ((ReactvPwr_HH * 16777216) + (ReactvPwr_H * 65536) + (ReactvPwr_L * 256) + ReactvPwr_LL) / 100.0
    ApprntPwr = ((ApprntPwr_HH * 16777216) + (ApprntPwr_H * 65536) + (ApprntPwr_L * 256) + ApprntPwr_LL) / 100.0
    
    return [SysVer, SysStatus, Voltage, Current, Frequency, ActivePwr, ReactvPwr, ApprntPwr, PwrFactor]


def set_chip_id(id):
    global chip_id, html, response
    if (debug): print('Remote asked for chip_id=' + str(id) + '...')
    chip_id = id
    html = null_page
    response = html % ('\n\nSetting ChipID to ' + str(id) + '...\n\n')






html_page = """<!DOCTYPE html>
<html>
    <head> <title>MCP39F521 Readings</title> 
    <style>
        table {
            width:300px;
        }
        table, th, td {
            border: 1px solid grey;
            border-collapse: collapse;
        }
        th, td {
            padding: 5px;
            text-align: left;
        }
        table#t01 tr:nth-child(even) {
            background-color: #eee;
        }
        table#t01 tr:nth-child(odd) {
            background-color: #fff;
        }
        table#t01 th {
            background-color: #99e;
            color: white;
        }
    </style>
    </head>
    <body> <h1>MCP39F521 id=%s Readings</h1>
        <table id="t01"> <tr><th>Parameter</th><th>Value</th></tr> %s </table>
    </body>
</html>
"""

null_page = """%s"""
json_page = """{%s}"""
    

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

print('\nMCP39F521 read agent v1.0\n (c)Piotr Oniszczuk\n')

mem_info()

print('\nNow Listening on port 80...\n')

try:
    while True: 
        conn, addr = s.accept()
        print("Got request from %s" % str(addr)) 

        request = conn.recv(1024) 
        if (debug): print("Content = %s" % str(request)) 
        request = str(request)
        if (debug): print (request)

        data = get_data_from_mcp39f521(chip_id)
        vals = [['Voltage',       data[2], 'V' ], \
                ['Current',       data[3], 'A' ], \
                ['Frequency',     data[4], 'Hz'], \
                ['Active Power',  data[5], 'W' ], \
                ['Reactive Power',data[6], 'W' ], \
                ['Apparent Power',data[7], 'W' ], \
                ['Power Factor',  data[8], ''  ]]

        raw       = request.find('/raw')
        json      = request.find('/json')
        reboot    = request.find('/reboot')
        debug_on  = request.find('/debug=on')
        debug_off = request.find('/debug=off')
        chip_id0  = request.find('/set_chip_id=0')
        chip_id1  = request.find('/set_chip_id=1')
        chip_id2  = request.find('/set_chip_id=2')
        chip_id3  = request.find('/set_chip_id=3')

        if chip_id0 == 6:
            chip_id = 0
            set_chip_id(chip_id)

        elif chip_id1 == 6:
            chip_id = 1
            set_chip_id(chip_id)

        elif chip_id2 == 6:
            chip_id = 2
            set_chip_id(chip_id)

        elif chip_id3 == 6:
            chip_id = 3
            set_chip_id(chip_id)

        elif debug_on == 6:
            if (debug): print('Remote asked for Debug=ON...')
            debug = 1
            html = null_page
            response = html % '\n\nTurning DEBUG ON...\n\n'

        elif debug_off == 6:
            if (debug): print('Remote asked for Debug=OFF...')
            debug = 0
            html = null_page
            response = html % '\n\nTurning DEBUG OFF...\n\n'

        elif reboot == 6:
            if (debug): print('Remote asked for reboot...')
            html = null_page
            response = html % '\n\nRebooting...\n\n'
            conn.send(response)
            conn.close()
            sleep_ms(3000)
            reset()

        elif json == 6:
            if (debug): print('Remote asked for json formated data...')
            rows = ['"%s":%.1f,' % (p[0], p[1]) for p in vals]
            html = json_page
            response = html % '\n'.join(rows)

        elif raw == 6:
            if (debug): print('Remote asked for raw formated data...')
            rows = ['%.1f' % (p[1]) for p in vals]
            html = null_page
            response = html % '\n'.join(rows)

        else:
            if (debug): print('Remote asked for HTML formated data...')
            rows = ['<tr><td>%s</td><td><b>%.1f %s</></td></tr>' % (p[0], p[1], p[2]) for p in vals]
            html = html_page
            response = html % (chip_id, '\n'.join(rows))
 
        conn.send(response)
        conn.close()
        if (debug): mem_info()

except:
        print ('\n\nException in main server loop. Rebooting...\n\n')
        sleep_ms(5000)
        reset()
