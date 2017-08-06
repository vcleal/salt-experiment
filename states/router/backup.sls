backup_test:
 {% set router_vendor = grains.vendor -%}
 {# get the vendor grains #}
 {% if router_vendor|lower == 'juniper' %}
 module.run:
   - name: net.cli
   - args:
     - 'show configuration | display set'
 {% elif router_vendor|lower == 'cisco' %}
 {#  #}
 module.run:
   - name: net.cli
   - args:
     - 'show run'
 {% endif %}
