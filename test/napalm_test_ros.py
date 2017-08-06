from napalm_base import get_network_driver
d = get_network_driver('ros')
e = d('192.168.50.32', 'admin', 'admin')
e.open()
print e.get_facts()
e.close()
