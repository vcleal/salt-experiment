#!/usr/bin/python
#encoding:utf-8

# Importar API módulos salt
import salt.client

import datetime
import os

client = salt.client.LocalClient()
# Formato da data para nome do arquivo
hoje = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# Diretório do destino dos arquivos
os.chdir('/srv/salt/backup')
# Dicionário de retorno
ret={}

def all():
  '''
  Backup das configurações (running) de todos os equipamentos
  '''
  # Comando a ser executado no master
  config = client.cmd('*', 'net.config')
  for key in config:
    if config[key] is False:
      # Equipamento não conectado
      ret.update({key: "Minion did not return. [No response]"})
    elif config[key]['result'] is False:
      # Problema na execução do módulo
      ret.update({key: config[key]['comment']})
    else:
      # Salvar arquivo
      with open(key+"-"+hoje+".cfg",'w') as file:
        file.write(config[key]['out']['running'])
        ret.update({key: config[key]['result']})
  return ret

def group(*group):
  '''
  Backup das configurações (running) de todos os equipamentos
  '''
  if not group:
    print('Please specify nodegroup')
    return []
  for g in group:
    config = client.cmd(g, 'net.config', tgt_type='nodegroup')
    for key in config:
      if config[key] is False:
        ret.update({key: "Minion did not return. [No response]"})
      elif config[key]['result'] is False:
        ret.update({key: config[key]['comment']})
      else:
        with open(key+"-"+hoje+".cfg",'w') as file:
          file.write(config[key]['out']['running'])
          ret.update({key: config[key]['result']})
  return ret

def config(*equip):
  '''
  Backup das configurações (running) de equipamento específico
  '''
  if not equip:
    print('Please specify equipment')
    return []
  for e in equip:
    config = client.cmd(e, 'net.config')
    for key in config:
      if config[key] is False:
        ret.update({key: "Minion did not return. [No response]"})
      elif config[key]['result'] is False:
        ret.update({key: config[key]['comment']})
      else:
        with open(key+"-"+hoje+".cfg",'w') as file:
          file.write(config[key]['out']['running'])
          ret.update({key: config[key]['result']})
  return ret