from napalm_base import get_network_driver
d = get_network_driver('ios')
e = d('192.168.50.34', 'admin', 'admin', optional_args={'secret': 'admin'})
e.open()
print e.get_facts()
e.close()
