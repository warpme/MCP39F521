# MCP39F521
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
