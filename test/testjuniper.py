from pprint import pprint
from jnpr.junos import Device

dev = Device(host='192.168.122.31', user='admin', password='admin123' )
dev.open()

pprint( dev.facts )

dev.close()
