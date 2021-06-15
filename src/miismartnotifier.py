import requests
import json
import copy

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
    
    def __init__(self):
        config_file_name = "./config.json"
        config = self.read_config_file(config_file_name)

        self.smart_config = config['smart']
        self.notif_config = config['notification']

        
    def read_config_file(self, config_file_name):
        with open(config_file_name, mode='r') as conf_file:
            config = json.load(conf_file)
        return config

    
    def get_devices_list(self):
        devices_list = DeviceList()
        return devices_list

    
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
            if eval(device_attribute_worst + comp + target_attribute[level]):
                message.set_status(level)
                message.append_message(attribute['name'])
                break

        return message
                

    def notify_messages(self, messages):
        line_notify_token = self.notif_config["token"]
        line_notify_api = self.notif_config["api_url"]
        headers = {'Authorization': f'Bearer {line_notify_token}'}

        notification_message = ''
        for message in messages:
            if message.status == 0:
                status_message = "\n正常@" + message.device_name + '\n'
                main_message = "問題は見つかりませんでした."

            else:
                status_message = "\n警告@" if message.status == 1 else "\n深刻なエラー@"
                status_message += message.device_name + '\n'
                main_message = '\n'.join(message.notification_message)
                
            notification_message += status_message + main_message + '\n'

        data = {'message': f'{notification_message}'}

        requests.post(line_notify_api, headers = headers, data = data)
    
    def start(self):
        devices_list = self.get_devices_list()
        
        messages = []
        for device in devices_list.devices:
            messages.append(self.validate_device(device))
            
        self.notify_messages(messages)    

        
if __name__ == "__main__":

    msn = MiiSmartNotify()
    msn.start()

