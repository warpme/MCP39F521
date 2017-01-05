# MCP39F521
This is ESP8266 micropython script designed to serve ESP8266 as web server showing readings from Microchip MCP39F521. 
Script was developed and tested on esp8266-20161110-v1.8.6.bin micropython.

Script listens on port 80 and implements following commands:

  'http://<esp8266_ip>'               - shows web page with MCP39F521 readings
  'http://<esp8266_ip>/json'          - sends json formated MCP39F521 readings
  'http://<esp8266_ip>/eng_acc=on'    - turns ON energy accumulation
  'http://<esp8266_ip>/eng_acc=off'   - turns OFF energy accumulation (and reset accumulated energy counters
  'http://<esp8266_ip>/reboot'        - reboots ESP8266

Repository has 2 versions of script: for 1-phase meter and 3-phase meter

To setup ESP8266 with micropython pls look on various tutorials. There is plenty of them on Internet
