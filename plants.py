#!/usr/bin/python

from pi_sht1x import SHT1x
import time
import RPi.GPIO as GPIO
import Adafruit_DHT as dht
import sqlite3
import math
#import gspread
#import oauthclient
import hashlib
from datetime import datetime


    
def main():
    database = "/home/pi/plants.db"
 
    # create a database connection
    for i in range(1):
        sqlConnection = sqlite3.connect(database)
        cursor = sqlConnection.cursor()
        with sqlConnection:
            sht10 = EnglishIvySensor1();
            dht22 = AmbientRoomSensor();
            InsertSensorData(cursor, sht10);
            InsertSensorData(cursor, dht22);
        sqlConnection.close()
        #time.sleep(300);

def MD5_hash(dataList):
    string = ''
    for i in dataList:
        string += str(i)

    md5 = hashlib.md5((string).encode('utf-8')).hexdigest()
    return md5

def InsertSensorData(cursor, values):
    # timestmap, humidity, temp, dew, location, sensorid
    insertList = [values.get("timestamp", ""),
        values.get("humidity", ""),
        values.get("fahrenheit", ""),
        values.get("dewPoint", ""),
        values.get("location", ""),
        values.get("sensorId", "")]
    md5 = MD5_hash(insertList)
    insertList.append(md5)

    cursor.execute("""
        INSERT INTO SensorReading(Timestamp, Humidity, Temperature, DewPoint, Location, SensorId, MD5Checksum) 
        VALUES (?,?,?,?,?,?,?)""", insertList)
    print(insertList)

def EnglishIvySensor1():
    fahrenheitAVG = 0
    humidityAVG = 0
    dewPointAVG = 0
    timestamp = datetime.now()
    location = "Office"

    count = 5
    for i in range(count):
        with SHT1x(17, 21, gpio_mode=GPIO.BCM) as sensor:
            fahrenheitAVG = fahrenheitAVG + round((sensor.read_temperature() * (9/5)) + 32, 2)
            humidityAVG = humidityAVG + sensor.read_humidity(sensor.read_temperature())
            dewPointAVG = dewPointAVG + calculateFahrenheit(sensor.calculate_dew_point(sensor.read_temperature(), sensor.read_humidity(sensor.read_temperature())))
            
            
    values = dataDict(str(timestamp), round(fahrenheitAVG/count, 2), round(humidityAVG/count, 2), round(dewPointAVG/count, 2), location, 1)
    return values

def AmbientRoomSensor():
    fahrenheitAVG = 0
    humidityAVG = 0
    dewPointAVG = 0
    timestamp = datetime.now()
    location = "Office"

    count = 5 
    for i in range(count):
        humidity,celsius = dht.read_retry(dht.DHT22, 12)
        fahrenheitAVG = fahrenheitAVG + calculateFahrenheit(celsius)
        humidityAVG = humidityAVG + round(humidity, 2)
        dewPointAVG = dewPointAVG + calculateDewPoint(celsius, humidity)
    values = dataDict(str(timestamp), round(fahrenheitAVG/count, 2), round(humidityAVG/count, 2), round(dewPointAVG/count, 2),location, 2)
    return values

def dataDict(timestamp, fahrenheit, humidity, dewPoint, location, sensor):
    values = {
        "timestamp" : timestamp,
        "fahrenheit" : fahrenheit,
        "humidity" : humidity,
        "dewPoint" : dewPoint,
        "location" : location,
        "sensorId" : sensor
    }
    return values

def calculateFahrenheit(temperature):
    fahrenheit = round((temperature * (9/5)) + 32, 2)
    return fahrenheit

def calculateDewPoint(celsius, humidity):
    A = 17.27
    B = 237.7
    alpha = ((A * celsius) / (B + celsius)) + math.log(humidity/100.0)
    dewPointC = (B * alpha) / (A - alpha)
    dewPointF = calculateFahrenheit(dewPointC)
    return dewPointF
    
if __name__ == '__main__':
    main()
