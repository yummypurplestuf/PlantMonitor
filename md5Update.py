#!/usr/bin/env python

import sqlite3
import hashlib
from sqlite3 import Error
from datetime import datetime
 
 
def main():

    start = datetime.now()

    db = create_connection()
    connection = db [1]
    cursor = db[0]

    data = query(cursor)

    dict = md5(data)
    update(connection, dict)

    connection.close()
    end = datetime.now()
    print ('start: ', start)
    print ('end: ', end)
 
def create_connection():
    db_file = "/home/pi/plants.db"
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)

    cursor = conn.cursor(), conn
    return cursor

def md5(data):
    dict = {}
    for i in data:
        tblId = i[0]
        timestamp = i[1]
        humidity = i[2]
        temperature = i[3]
        dewpoint = i[4]
        location = i[5]
        sensorId = i[6]
        string = str(timestamp) + str(humidity) + str(temperature) + str(dewpoint) + str(location) + str(sensorId)

        md5 = hashlib.md5((string).encode('utf-8')).hexdigest()
        dict[tblId] = md5

    return dict 

def query(connection):
    connection.execute('''
        SELECT 
            SensorReadingId, 
            Timestamp, 
            Humidity, 
            Temperature, 
            DewPoint, 
            Location, 
            SensorId 
        FROM SensorReading 
        WHERE 
            MD5Checksum IS NULL
        ORDER BY SensorReadingId
        ''')
    data = connection.fetchall()

    return data

def update(connection, dict):
    record_count = len(dict)
    record_on = 0

    for i in dict:
        SensorReadingId = i
        md5 = dict.get(i)
        
        connection.execute('''UPDATE SensorReading SET MD5Checksum = ? WHERE SensorReadingId = ?''', (md5, SensorReadingId))
        connection.commit()
        record_on += 1
        print(str(round((record_on/record_count), 3) * 100) + '%', str(record_on) + ' of ' + str(record_count))


if __name__ == '__main__':
    main()