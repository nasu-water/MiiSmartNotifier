import requests
import json
import copy
import sqlite3
import itertools
import argparse

from pySMART import DeviceList
from pySMART import Device


class NotificationMessage:

    def __init__(self):
        self.status = 0
        self.device_name = ''
        self.notification_message = []

        
    def set_status(self, status):
        if status == 'error':
            self.status = 2
            
        elif status == 'warn' and not self.status == 2:
            self.status = 1
            
    def append_message(self, message):
        self.notification_message.append(message)

            
class MiiSmartNotify:
    
    def __init__(self, args):
        config_file_name = "./config.json"
        config = self.read_config_file(config_file_name)

        self.smart_config = config['smart']
        self.notif_config = config['notification']
        self.args = args
        self.create_db()

            
    def __del__(self):
        self.conn.close()

    def remove_all_table(self):
        remove_table_sql = 'DROP TABLE {}'.format(self.table_name)
        self.conn.execute(remove_table_sql)
        self.conn.commit()

    def remove_device_history(self, device_name):
        device_history_delete_sql = 'DELETE FROM {} WHERE device = ?'.format(self.table_name)
        self.conn.execute(device_history_delete_sql, [device_name])
        self.conn.commit()

                
    def create_db(self):
        self.db_name = 'history.db'
        self.table_name = 'message_history_table'
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

        table_create_sql = '''CREATE TABLE IF NOT EXISTS {} (
                                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                                      device STRING, 
                                      status STRING,
                                      attribute STRING,
                                      datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''.format(self.table_name)

        self.cursor.execute(table_create_sql)
        self.conn.commit()

        
    def read_config_file(self, config_file_name):
        with open(config_file_name, mode='r') as conf_file:
            config = json.load(conf_file)
        return config

    
    def get_devices_list(self):
        devices_list = DeviceList()
        return devices_list

    
    def get_device(self, device_name):
        device = Device(device_name)
        return device


    def validate_device(self, device):
        message = NotificationMessage()
        message.device_name = device.name
        
        for attribute in self.smart_config:
            message = self.validate_attribute(device.attributes[attribute["id"]], attribute, message)

        return message


    def validate_attribute(self, device_attribute, attribute, orig_message):
        message = copy.copy(orig_message)

        # Only for 'temperature_celsius', the comparison should be vise versa.
        comp = ">" if attribute["id"] == 194 else "<"
        # Test
        #comp = "<" if attribute["id"] == 194 else ">"

        levels = ['error','warn']        
        limits = list(map(lambda lev:str(int(attribute[lev])) if not attribute[lev] == 0 else str(int(device_attribute.thresh)), levels))

        target_attribute = dict(zip(levels,limits))

        device_attribute_worst = str(int(device_attribute.worst))

        for level in levels:
            row_exists = self.in_table(message.device_name, level, attribute['name'])

            if eval(device_attribute_worst + comp + target_attribute[level]) and \
               not row_exists:
                message.set_status(level)
                message.append_message(attribute['name'])
                self.insert_table(message.device_name, level, attribute['name'])
                break
            
            elif row_exists:
                break

        return message


    def in_table(self, device_name, level, attribute_name):
        select_sql = 'SELECT COUNT(*) FROM {} WHERE device = ? AND status = ? AND attribute = ?'.format(self.table_name)
        
        self.cursor.execute(select_sql, [device_name, level, attribute_name])
        return list(itertools.chain.from_iterable(self.cursor.fetchall()))[0]


    def insert_table(self, device_name, level, attribute_name):

        insert_sql = 'INSERT INTO {}(device, status, attribute) VALUES (?, ?, ?)'.format(self.table_name)

        self.cursor.execute(insert_sql,[ device_name, level, attribute_name])
        self.conn.commit()


    def notify_messages(self, messages):
        line_notify_token = self.notif_config["token"]
        line_notify_api = self.notif_config["api_url"]
        headers = {'Authorization': f'Bearer {line_notify_token}'}

        notification_message = ''
        notification_flag = False
        
        for message in messages:
            if message.status == 0:
                status_message = "\n正常@" + message.device_name + '\n'
                main_message = "問題は見つかりませんでした."

            else:
                status_message = "\n警告@" if message.status == 1 else "\n深刻なエラー@"
                status_message += message.device_name + '\n'
                main_message = '\n'.join(message.notification_message)
                notification_flag = True
                
            notification_message += status_message + main_message + '\n'

        data = {'message': f'{notification_message}'}

        if notification_flag or self.notif_config["dont_send_when_no_alert"] == 0:
            requests.post(line_notify_api, headers = headers, data = data)

        
    def start(self):
        if self.args.remove_all:
            self.remove_all_table()
            
        elif self.args.remove_device:
            self.remove_device_history(args.remove_device)

        elif self.args.device:
            device = self.get_device(self.args.device)
            messages = []
            messages.append(self.validate_device(device))
            self.notify_messages(messages)

        else:
            devices_list = self.get_devices_list()
            messages = []
            for device in devices_list.devices:
                messages.append(self.validate_device(device))

            self.notify_messages(messages)

            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='S.M.A.R.T value check and send notification.')

    parser.add_argument('-d', '--device', type = str, help = 'Check and notify for the assgined device.')
    parser.add_argument('-r','--remove-device', type = str, help = 'Remove specific device\'s history')
    parser.add_argument('-R', '--remove-all', action='store_true', help = 'Remove all decies\'s history')

    args = parser.parse_args()

    
    msn = MiiSmartNotify(args)
    msn.start()



