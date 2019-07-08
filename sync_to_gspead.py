#!/usr/bin/env python

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import sqlite3
import hashlib
from datetime import datetime
import platform


def main():
    start_time = datetime.now()
    try:
        db = create_connection()
        connection = db[1]
        cursor = db[0]

        data = query(cursor)


        sync_to_google(data)

        log_run_metrics(connection, start_time, datetime.now(), datetime.now() - start_time, 'gspreadsync', 'SUCCESS', '')

        connection.close()
    except sqlite3.Error as e:
        log_run_metrics(cursor, start_time, datetime.now(), datetime.now() - start_time, 'gspreadsync', 'SUCCESS', e)


def log_run_metrics(connection, start_time, end_time, duration, operation, status, error):

    package = [str(start_time), str(end_time), str(duration), str(operation), str(status), str(error)]

    connection.cursor().execute("""
        INSERT INTO SystemLog(StartTime, EndTime, Duration, Operation, Status, ErrorMessage) 
        VALUES (?,?,?,?,?,?)""", package)
    connection.commit()

def create_connection():
    # determine platform that's running
    db_path = ''
    if platform.system() == 'Windows':
        db_path = "C:\\Users\\jluellen\\Desktop\\plants.db"
    if platform.system() == 'Linux':
        db_path = "/home/pi/plants.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor(), conn
        return cursor
    except sqlite3.Error as e:
        return


def query(cursor):
    cursor.execute('''
        SELECT 
            Timestamp, 
            Humidity, 
            Temperature, 
            DewPoint, 
            Location, 
            SensorId,
            md5Checksum
        FROM SensorReading 
        WHERE 
            MD5Checksum IS NOT NULL
        ''')
    data = cursor.fetchall()

    return data


def sync_to_google(db_data):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    credentials = ServiceAccountCredentials.from_json_keyfile_name('main-presence-245818-65c82e7266d7.json', scope)

    gc = gspread.authorize(credentials)

    worksheet = gc.open("sqlite3 database").sheet1

    # get header labels and process them into a dict
    header_labels = worksheet.row_values(1)
    header_dict = {}
    md5_checksum_column = []

    # get md5checksum column if it exists as a header label
    for i in range(len(header_labels)):
        header_dict[i] = header_labels[i]
        if header_labels[i] == 'md5Checksum':
            md5_checksum_column = worksheet.col_values(i + 1)

    query_md5_dict = {}
    for i in db_data:
        query_md5_dict[i[6]] = i

    transfer_list = []
    row_count = 0
    for i in query_md5_dict:
        if i not in md5_checksum_column:
            row_count += 1
            for k in query_md5_dict.get(i):
                transfer_list.append(k)

    if len(transfer_list) > 0:

        # obtain cell range from Google Sheets
        start_row = len(md5_checksum_column) + 1
        start_column = 1
        end_row = len(md5_checksum_column) + row_count
        end_column = len(header_labels)

        cell_list = worksheet.range(start_row, start_column, end_row, end_column)

        for i in range(len(transfer_list)):
            cell_list[i].value = transfer_list[i]

        # worksheet.update_cells(cell_list)


# cell_list = worksheet.range('A1:C7') OR worksheet.range(1, 1, 7, 2) aka (start row, start column, end row, end column)
# .row, .col, .value


if __name__ == '__main__':
    main()
