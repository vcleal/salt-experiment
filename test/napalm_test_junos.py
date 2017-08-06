from napalm_base import get_network_driver
d = get_network_driver('junos')
e = d('192.168.122.31', 'admin', 'admin123')
e.open()
print e.get_facts()
e.close()
