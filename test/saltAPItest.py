#!/usr/bin/python
#encoding:utf-8

import salt.client
import datetime

hoje = str(datetime.date.today())
client = salt.client.LocalClient()
config = client.cmd('gns3', 'net.config', tgt_type='nodegroup')
for key in config:
	with open(key+"-"+hoje+".cfg",'w') as file:
		file.write(config[key]['out']['running'])