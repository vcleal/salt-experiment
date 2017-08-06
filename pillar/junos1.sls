proxy:
  proxytype: napalm
  driver: junos
  host: 192.168.122.31
  username: admin
  passwd: admin123
#  optional_args:
#    port: 830

default_route_nh: 10.10.10.10

snmp_test:
  snmp_name: '"UNI - Campus"'
  community: "comm_name"

include:
  - ntp_config
