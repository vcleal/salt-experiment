#!/usr/bin/env python
from netmiko import ConnectHandler
from getpass import getpass

#ip_addr = raw_input("Enter IP Address: ")

device = { 
    'device_type': 'cisco_ios',
    'ip': '192.168.50.34',
    'username': 'admin',
    'password': 'admin',
    'secret' : 'admin'
} 

net_connect = ConnectHandler(**device)
net_connect.enable()
output = net_connect.send_command("show ip int brief")
print(output)