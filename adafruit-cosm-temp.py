#!/usr/bin/env python
import time
import os
import RPi.GPIO as GPIO
import eeml
 
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
DEBUG = 1
#DELAY = 1
DELAY = 30
LOGGER = 1
ADJUST = 1950.0
COUNT = 0 # to help smooth temp
# initialize to 77.0 (25.0C) 
temp_F_smooth = 77.0
 
# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
  if ((adcnum > 7) or (adcnum < 0)):
    return -1

  GPIO.output(cspin, True)
 
  GPIO.output(clockpin, False)  # start clock low
  GPIO.output(cspin, False)     # bring CS low
 
  commandout = adcnum
  commandout |= 0x18  # start bit + single-ended bit
  commandout <<= 3    # we only need to send 5 bits here
  for i in range(5):
    if (commandout & 0x80):
      GPIO.output(mosipin, True)
    else:   
      GPIO.output(mosipin, False)
    commandout <<= 1
    GPIO.output(clockpin, True)
    GPIO.output(clockpin, False)
 
  adcout = 0
  # read in one empty bit, one null bit and 10 ADC bits
  for i in range(12):
    GPIO.output(clockpin, True)
    GPIO.output(clockpin, False)
    adcout <<= 1
    if (GPIO.input(misopin)):
      adcout |= 0x1
 
  GPIO.output(cspin, True)
 
  adcout /= 2       # first bit is 'null' so drop it
  return adcout
 
# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK = 18
SPIMISO = 23
SPIMOSI = 24
SPICS = 25
GREEN = 17
BLUE = 27
RED = 22
 
# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)
GPIO.setup(GREEN, GPIO.OUT)
GPIO.setup(BLUE, GPIO.OUT)
GPIO.setup(RED, GPIO.OUT)
 
# COSM variables. The API_KEY and FEED are specific to your COSM account and must be changed 
#API_KEY = '5RNOO3ShYJxYiq2V2sgSRtz3112SAKxFQjNDQmNXc0RScz0g'
#FEED = 68872
API_KEY = 'NFxCj4g2ByBPqcQ5aUQkziscU4jxFetL0yhtaZpaMBlNhCfN'
FEED = 845567437 
 
API_URL = '/v2/feeds/{feednum}.xml' .format(feednum = FEED)
 
# temperature sensor connected channel 0 of mcp3008
adcnum = 0

GPIO.output(GREEN, False)
GPIO.output(BLUE, False)
GPIO.output(RED, False)

while True:
        # read the analog pin (temperature sensor LM35)
        read_adc0 = readadc(adcnum, SPICLK, SPIMOSI, SPIMISO, SPICS)
				# invert since NTE7225 temp sensor reads 0 at max temp
        read_adc0 = 1024 - read_adc0
 
        # convert analog reading to millivolts = ADC * ( 5000.0 / 1024.0 )
        millivolts = read_adc0 * ( 5000.0 / 1024.0)
 
        # 10 mv per degree & adjust based on NTE7225
        temp_C = ((millivolts - ADJUST) / 10.0) 

        # convert celsius to fahrenheit 
        temp_F = ( temp_C * 9.0 / 5.0 ) + 32

        # smooth the small fluctuations
        if (temp_F != temp_F_smooth):
          COUNT += 1 
        if (COUNT == 5):
          COUNT = 0
          temp_F_smooth = temp_F
 
        if (temp_F < 80.0):
          GPIO.output(GREEN, True)
          GPIO.output(BLUE, False)
          GPIO.output(RED, False)
        if ((temp_F >= 80.0) and (temp_F < 85)):
          GPIO.output(GREEN, False)
          GPIO.output(BLUE, True)
          GPIO.output(RED, False)
        if (temp_F >= 85.0): 
          GPIO.output(GREEN, False)
          GPIO.output(BLUE, False)
          GPIO.output(RED, True)

        # remove decimal point from millivolts
        millivolts = "%d" % millivolts
 
        # show only one decimal place for temperature and voltage readings
        temp_C = "%.1f" % temp_C
        temp_F = "%.1f" % temp_F
        #temp_F_smooth = "%.1f" % temp_F_smooth
 
        if DEBUG:
          print("read_adc0:\t", read_adc0)
          print("millivolts:\t", millivolts)
          print("temp_C:\t\t", temp_C)
          print("temp_F:\t\t", temp_F)
          print("temp_F_smooth:\t\t", temp_F_smooth)
          print("\n")
 
        if LOGGER:
          # open up your cosm feed
          pac = eeml.Pachube(API_URL, API_KEY)
 
          #send celsius data
          pac.update([eeml.Data(0, temp_C, unit=eeml.Celsius())])
 
          #send fahrenheit data
          pac.update([eeml.Data(1, temp_F, unit=eeml.Fahrenheit())])
 
          #send smoothed data
          pac.update([eeml.Data(2, temp_F_smooth, unit=eeml.Fahrenheit())])
 
          # send data to cosm
          pac.put()
 
        # hang out and do nothing for 10 seconds, avoid flooding cosm
        time.sleep(DELAY)
