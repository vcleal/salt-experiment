#!/usr/bin/python
#encoding:utf-8

# Import salt modules
import salt.client

def up():
    '''
    Print a list of all of the minions that are up
    '''
    client = salt.client.LocalClient(__opts__['conf_file'])
    minions = client.cmd('*', 'test.ping', timeout=1)
    print minions
    for minion in sorted(minions):
        print minion