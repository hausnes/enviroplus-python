import time
import colorsys
import os
import sys
import ST7735
try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559
    ltr559 = LTR559()
except ImportError:
    import ltr559

from bme280 import BME280
from pms5003 import PMS5003, ReadTimeoutError as pmsReadTimeoutError
from enviroplus import gas
from subprocess import PIPE, Popen
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import logging
from datetime import datetime
import csv

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

logging.info("""all-in-one.py - Displays readings from all of Enviro plus' sensors

Press Ctrl+C to exit!

""")

# BME280 temperature/pressure/humidity sensor
bme280 = BME280()

# PMS5003 particulate sensor
pms5003 = PMS5003()

# Get the temperature of the CPU for compensation
def get_cpu_temperature():
    process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE, universal_newlines=True)
    output, _error = process.communicate()
    return float(output[output.index('=') + 1:output.rindex("'")])


# Tuning factor for compensation. Decrease this number to adjust the
# temperature down, and increase to adjust up
factor = 0.8

cpu_temps = [get_cpu_temperature()] * 5

delay = 0.5  # Debounce the proximity tap
mode = 0     # The starting mode
last_page = 0
light = 1

# Create a values dict to store the data
variables = ["temperature",
             "pressure",
             "humidity",
             "light",
             "oxidised",
             "reduced",
             "nh3",
             "pm1",
             "pm25",
             "pm10"]

listeAlleVerdata = []

# The main loop
try:
    while True:
        with open('data.csv', mode='w', newline='') as datafil: # mode='a' legg til nye data, 'w' skriv over
            dataskriver = csv.writer(datafil)
            
            tidspunkt = datetime.now()
            print("Tidspunkt:",tidspunkt)

            proximity = ltr559.get_proximity()

            # variable = "temperature"
            unit = "C"
            cpu_temp = get_cpu_temperature()
            # Smooth out with some averaging to decrease jitter
            cpu_temps = cpu_temps[1:] + [cpu_temp]
            avg_cpu_temp = sum(cpu_temps) / float(len(cpu_temps))
            raw_temp = bme280.get_temperature()
            dataTemp = raw_temp - ((avg_cpu_temp - raw_temp) / factor)
            #display_text(variables[mode], data, unit)
            print(dataTemp,unit)

            # variable = "pressure"
            unit = "hPa"
            dataTrykk = bme280.get_pressure()
            #display_text(variables[mode], data, unit)
            print(dataTrykk,unit)

            # variable = "humidity"
            unit = "%"
            dataFukt = bme280.get_humidity()
            #display_text(variables[mode], data, unit)
            print(dataFukt,unit)

            # variable = "light"
            unit = "Lux"
            if proximity < 10:
                dataProx = ltr559.get_lux()
            else:
                dataProx = 1
            #display_text(variables[mode], data, unit)
            print(dataProx,unit)

            # variable = "oxidised"
            unit = "kO"
            dataGass = gas.read_all()
            dataGass = dataGass.oxidising / 1000
            #display_text(variables[mode], data, unit)
            print(dataGass,unit)

            # variable = "reduced"
            unit = "kO"
            dataGassReduced = gas.read_all()
            dataGassReduced = dataGassReduced.reducing / 1000
            #display_text(variables[mode], data, unit)
            print(dataGassReduced,unit)

            # variable = "nh3"
            unit = "kO"
            dataGassNH3 = gas.read_all()
            dataGassNH3 = dataGassNH3.nh3 / 1000
            #display_text(variables[mode], data, unit)
            print(dataGassNH3,unit)

            # variable = "pm1"
            unit = "ug/m3"
            try:
                dataPM1 = pms5003.read()
            except pmsReadTimeoutError:
                logging.warn("Failed to read PMS5003")
            else:
                dataPM1 = float(dataPM1.pm_ug_per_m3(1.0))
                #display_text(variables[mode], data, unit)
                print(dataPM1,unit)

            # variable = "pm25"
            unit = "ug/m3"
            try:
                data = pms5003.read()
            except pmsReadTimeoutError:
                logging.warn("Failed to read PMS5003")
            else:
                data = float(data.pm_ug_per_m3(2.5))
                #display_text(variables[mode], data, unit)
                print(data,unit)

            # variable = "pm10"
            unit = "ug/m3"
            try:
                data = pms5003.read()
            except pmsReadTimeoutError:
                logging.warn("Failed to read PMS5003")
            else:
                data = float(data.pm_ug_per_m3(10))
                #display_text(variables[mode], data, unit)
                print(data,unit)
        
        # Sjoelve skrivinga
        dataskriver.writerows(listeAlleVerdata)
        print("Data er skrive til CSV-fil.")

        # Sover 5 sek mellom kvar registrering
        print("Ventar litt...")
        time.sleep(5)        


# Exit cleanly
except KeyboardInterrupt:
    print("Avsluttar...")
    sys.exit(0)

'''
# Tomme lister ved oppstart
listeTemperaturar = []
listeLuftfuktighet = []
listeCO2 = []
listeAlleVerdata = []

def returnerAlleVerdata():
    print("---")

# Ein funksjon som registrer over tid, heilt til brukaren avsluttar med CTRL+C
def registrerSaaLenge():
    kjorer = True
    while kjorer:
        try:
            listeAlleVerdata.append(returnerAlleVerdata())
            print("Legg til data i lista med alle verdata.")
            time.sleep(0.5)
        except KeyboardInterrupt:
            kjorer = False
            print("Avsluttar registrering.")
            print(listeAlleVerdata)

registrerSaaLenge()

'''
#Skrive verdata til CSV-fil, basert paa listene fraa funksjonen registrerSaaLenge()
'''
print("-------------------------")
with open('data.csv', mode='w', newline='') as datafil: # mode='a' legg til nye data, 'w' skriv over
    dataskriver = csv.writer(datafil)
    dataskriver.writerows(listeAlleVerdata)
    print("Data er skrive til CSV-fil.")
    #dataskriver.writerows([verdi] for verdi in listeTemperaturar) # Brukte denne naar eg berre hadde tall (temperatur), ikkje tidskode. Skjoenar ikkje kvifor det var noedvendig.

'''
