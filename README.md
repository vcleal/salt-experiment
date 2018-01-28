# salt-experiment
Experimento com salt + NAPALM em equipamentos de rede.

## Instalação
**Salt**

Ubuntu:
- `apt install salt-master`
- `apt install salt-minion`

Alternativo:
- [Saltstack bootstrap script](https://github.com/saltstack/salt-bootstrap)

**NAPALM**

Dependências:
- `apt install libffi-dev libssl-dev python-dev python-cffi libxslt1-dev python-pip`
- `pip install --upgrade cffi`

Bibliotecas:
- `pip install napalm-junos napalm-iosxr napalm-ios napalm-ros`
 
 ou
- `pip install napalm` _(todas)_

## Ambiente de teste
Máquinas virtuais (Virtualbox) e imagens de roteadores no GNS3
- JunOSOlive (Juniper)
- IOS (Cisco)
- RouterOS (Mikrotik)

![Imgur](https://i.imgur.com/dyXwfjk.png?2)

O ambiente de teste virtual foi definido conectado numa rede *host-only* representada pelo master, e a rota na máquina local para as outras redes virtuais deve ser adicionada.

## Configuração inicial
Arquivos [`/etc/salt/master`](master) e [`/etc/salt/proxy`](proxy).

Para as configurações simples e uso básico, somente *file_roots* (caso não deseje local padrão) e *interface* são necessários no master, e *master* no proxy.

**Arquivos SLS: YAML do pillar e top**

Criar arquivos top e pillars em `/srv/pillar` (local padrão no master).

- `/srv/pillar/top.sls`

Arquivo top associa os nomes dos minions proxy com os arquivos pillars.
```yaml
base:
  cisco1:
    - cisco1   # Arquivo sls do pillar
  mikro1:
    - mikro1
  junos1:
    - junos1
  junos2:
    - junos2
```

- `/srv/pillar/junos1.sls`

Arquivo pillar contém as configurações para conexão com o proxy e eventuais dados estáticos.
```yaml
proxy:
  proxytype: napalm
  driver: junos
  host: 192.168.122.31
  username: admin
  passwd admin123
```

## Primeira conexão
O salt utiliza chaves públicas para autenticação. Os minions enviam para o master e o master deve aceitá-las para que a conexão prossiga.

- Iniciar salt-master:
  + `systemctl start salt-master`
- Iniciar salt-proxy:
  + (log) `salt-proxy --proxyid=junos1 -l debug`
  + (daemon) `salt-proxy --proxyid=junos1 -d`
  + [(service)](test/salt-proxy@.service) `systemctl start salt-proxy@junos1`
- Aceitar chave associada ao minion (proxy):
  + `salt-key -a -y junos1`

Outros comandos
- Aceitar todas as chaves:
  + `salt-key -A -y`
- Listar chaves:
  + `salt-key -L`

## Enviando comandos
Com o master e o minion conectados é possível enviar comandos do salt via CLI. Os comandos tem três componentes principais que podem ser vistos na sintaxe abaixo:

```bash
salt '<target>' <function> [arguments]
salt '*' test.rand_sleep 120 # exemplo
```

Onde:

- `target` - permite selecionar/filtrar os minions que as funções serão executadas *(mais informações sobre as maneiras de selecionar abaixo)*
- `function` - funcionalidade provida por um módulo, geralmente especificada como `module.function`, podendo fazer uso dos módulos já existentes do NAPALM (net, ntp, bgp, etc...) e do próprio salt, além de criar seus próprios
- `arguments` - argumentos para a função especificada

###### Selecionando alvo (targeting)
Dentre as várias maneiras de selecionar o minion alvo, destaca-se algumas abaixo espeficicadas através de opções do comando salt:

- Padrão (glob para os ids dos minions)
  + `salt '*' test.ping` *(todos)*
  + `salt 'mikro1' test.ping`
- Grains
  + `salt -G 'os:ios' test.ping`
- Expressão regular
  + `salt -E 'junos[1-9]' test.ping`
- Lista
  + `salt -L 'mikro1,cisco1' test.ping`
- Nodegroup (grupo criado no arquivo de configuração do master)
  + `salt -N gns3 test.ping`
- Combinação
  + `salt -C 'G@os:ios and junos* or N@gns3' test.ping`

## Alteração de configurações
A alteração de configurações de uma maneira genérica nos equipamentos utiliza o módulo NAPALM network, através dos métodos `net.load_config` e `net.load_template`. Utilizando estes métodos pode-se enviar as configurações desejadas de diferentes maneiras listadas abaixo.

Outra forma é através dos estados (salt states) em arquivos sls, que utilizam, por exemplo, o método para aplicar um estado `state.apply` ou `state.sls`.

###### Flags de configuração
As alterações de configuração aceitam alguns flags como argumentos que são úteis para verificar mudanças antes de serem aplicadas.
* __test__ (padrão = `False`)
    * Se aplica as mudanças ou não, apenas mostrando as diferenças e descartando as alterações.
```
sudo salt junos1 net.load_config text='system ntp server 172.17.17.1;' test=True
junos1:
    ----------
    already_configured:
        False
    comment:
        Configuration discarded.
    diff:
        [edit system ntp]
             server 200.128.0.23 { ... }
        +    server 172.17.17.1;
    loaded_config:
    result:
        True

```
* __commit__ (padrão = `True`)
    * Se aplica as mudanças imediatamente ou não, entrando em vigor de fato apenas após commit (`net.commit` ou `net.config_control`).
* __replace__ (padrão = `False`)
    * Se descarta toda a configuração vigente, substituindo pela nova enviada.


### Diretamente na linha de comando
Utilizando diretamente a CLI deve-se passar a configuração desejada com argumento `txt`:
```bash
salt '*' net.load_config txt='system ntp server 172.17.17.1;'
```

### Upload de arquivo de configuração
Com o mesmo método pode-se passar como argumento o caminho para o arquivo que desejado:
```bash
salt '*' net.load_config /path/to/file
```

### Upload de template
No caso do uso de templates como arquivos Jinja, o método utilizado é `net.load_template`, podendo passar o caminho absoluto para o template (ou utilizar `salt://` para especificar dentro do file_roots definido na configuração do master), ou remotamente via `http://`, `https://` ou `ftp://`:
```bash
salt '*' net.load_template salt://template.jinja
```

###### Jinja e templates
O uso de templates facilita o controle de configurações de diferentes equipamentos. Embora a linguagem de templates mostrada nos exemplos seja Jinja, o salt aceita outros tipos.

Dentro dos templates pode-se utilizar informações que ajudam no fluxo de controle e condicionais de forma a abstrair ainda mais o envio do comando no salt para equipamentos de diferentes fabricantes. As informações podem ser obtidas através dos grains, de dados do pillar ou da saída de algum outro comando do salt.

Um exemplo de um template para modificar o hostname baseado em informação existente no pillar é mostrado a seguir.
```jinja
{% set router_vendor = grains.vendor -%}{# informação dos grains #}
{% set hostname = pillar.proxy.host -%}{# informação estática do pillar #}

{% if router_vendor|lower == 'juniper' %}
system {
    host-name {{hostname}}.novo;
}
{% elif router_vendor|lower in ['cisco', 'arista'] %}
hostname {{hostname}}.novo
{% endif %}

```

###### Dados adicionais no pillar
Como os templates podem utilizar dados adicionais, e os grains são informações limitadas fornecidas pelo equipamento, a inserção de dados estáticos do usuário no pillar é uma alternativa na utilização dos templates. Por exemplo no pillar de algum equipamento localizado no pillar_roots:

Acrescentar em `/srv/pillar/junos1.sls`:
```yaml
include:
  - ntp_config
```

A utilização do `include` permite a inclusão em vários equipamentos de um arquivo único que contém o dado, simplificando modificações.

Onde `/srv/pillar/ntp_config.sls`:
```yaml
ntp.servers:
  - 200.128.0.21
ntp.peers:
  - 200.128.0.211
  - 200.128.0.212
```

E podemos usar a expressão no Jinja a seguir para obter a informação no pillar:
```jinja
{% set servers = pillar.get('ntp.servers', []) %}
```

### Via states
Estados definidos dentro do file_roots do master podem ser aplicados com o módulo `state`, o arquivo sls conterá o estado que pode aplicar as configurações de alteração:
```
sudo salt junos1 state.apply router.ntp test=True
junos1:
----------
          ID: update_ntp_config
    Function: netntp.managed
      Result: None
     Comment: This is in testing mode, the device configuration was not changed!
     Started: 11:16:33.487789
    Duration: 239.214 ms
     Changes:   
              ----------
              servers:
                  ----------
                  added:
                      - 200.128.0.22
                  removed:
                      - 200.128.0.21

Summary for junos1
------------
Succeeded: 1 (unchanged=1, changed=1)
Failed:    0
------------
Total states run:     1
Total run time: 239.214 ms
```

###### States
States podem ser usados para definir um estado que o sistema ou equipamento deve ter, assim aplicar um estado pode carregar várias configurações que definem este estado de operação do equipamento.

Dentro do file_roots definido pode-se criar um diretório que abriga os states e também um arquivo `top.sls` para aplicar todo um diretório de states

Dentro dos arquivos sls, que usam YAML, também podem ser usados expressões Jinja.

Um exemplo do state `ntp.sls` para configurar o ntp de algum roteador, armazenado no diretório "router" é mostrado a seguir, o argumento passado para o método seria, neste caso, `router.ntp`, como no apresentado no exemplo acima.
```yaml
{% set ntp_peers = pillar.get('ntp.peers', []) %}
{% set ntp_servers = pillar.get('ntp.servers', []) %}

update_ntp_config:
  netntp.managed:
    - peers: {{ ntp_peers | json() }}
    - servers: {{ ntp_servers | json() }}
``` 

## Cronograma (schedule)
Uma característica explorada também foi a possibilidade de agendar certos comandos ou aplicação de estados em um período de tempo desejado, favorecendo a automação de certas tarefas ou reforçar certo estado de configuração para o equipamento.

A definição do schedule pode ser feita tanto no arquivo de configuração do `master` quanto do `proxy`, ou ainda em um pillar específico que pode ser adicionado ao arquivo `top.sls` que mapeia a identificação dos equipamentos com os pillars.

Exemplo:

Pillar específico em `/srv/pillar/schedule/init.sls`:

```yaml
schedule:
  update_ntp_config:
    function: state.sls
    args:
      - router.ntp
    hours: 1
```

Onde:

- ```schedule``` - obrigatório para informar que é um cronograma
- ```update_ntp_config``` - é somente o nome do job no cronograma, podendo ser qualquer
- ```function``` - dizer ao salt o que vai ser executado, no caso aplicar um estado
- ```args``` - especificar argumentos da função, no caso o nome do estado
- ```days``` - frequência para executar a função, checar e atualizar a configuração. Outras opções: ```seconds```, ```minutes```, ```days``` etc...
Pode-se adicionar também chaves adicionais:
- ```splay``` (opcional) - define um intervalo de tempo (em segundos) dentro do qual a função vai ser iniciada, um valor aleatório vai ser escolhido para distribuir o carregamento no caso de muitos agendamentos para o mesmo instante
- ```returner``` (opcional) - encaminhar a saída da função para um serviço diferente. [Muitos já implementados e disponíveis.](https://docs.saltstack.com/en/latest/ref/returners/#full-list-of-returners)
No arquivo `top.sls`:
```
base:
  '*':
    - schedule
```

## Salt Runners e backup
Runners são módulos do salt executados no próprio master através do comando `salt-run`, ao invés de mandar o comando diretamente para o minion/proxy. Foi utilizado para uma solução de backup das configurações do roteador em arquivos na própria máquina que executa o master, juntamente com a API Python do próprio salt.

Basicamente são scripts em python que o nome do script e qual função dentro dele se deseja, são passados como argumento para o `salt-run`.
Exemplo:
```bash
salt-run backup.all
```
```python
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
```

Runners também podem ser adicionados a cronogramas (schedule), estes devem ser adicionados no próprio arquivo de configuração do master, juntamente com a localização destes:

Em `/etc/salt/master`:
```yaml
runner_dirs:
  - /etc/salt/runners

schedule:
  backup_job:
    function: backup.all
    days: 1
```

## Salt Beacons e Reactors
Outros componentes explorados do salt foram os beacons e reactors, que utilizados conjuntamente automatizam o processo de atualização de configuração no acontecimento de algum evento dentro do salt.

_Beacons_ geram eventos no salt para algum processo não relacionado ao salt, como no exemplo apresentado de alterar algum arquivo no sistema de arquivos. Para isso foi utilizado o beacon `inotify`, que precisa do pacote inotify-tools presente no sistema.
```apt install inotify-tools``` e ```pip install inotify```

No arquivo de configuração do `proxy`, define-se o beacon para gerar um evento quando há modificação no arquivo `/srv/pillar/ntp_config.sls`:
```yaml
beacons:
  inotify:
    /srv/pillar/ntp_config.sls:
      mask:
        - modify
    disable_during_state_run: True
```

_Reactors_ executam alguma ação baseado em um evento definido no salt. No exemplo, uma reação ao evento gerado pelo beacon anterior.

No arquivo de configuração do master:
```yaml
reactor:
  - 'salt/beacon/*/inotify//srv/pillar/ntp_config.sls':
    - salt://ntp_changed.sls
```
Onde a ação tomada é definida no arquivo em `/etc/salt/reactors/ntp_changed.sls`, e consiste em executar o estado definido em `router.ntp`:
```yaml
run_ntp_state:
  local.state.sls:
    - tgt: {{ data['id'] }}
    - arg:
      - router.ntp
```

Os eventos no salt podem ser monitorados através do comando `salt-run state.event pretty=True`.

## Salt Mine
WIP

## Extras
Mudança do arquivo `napalm_junos/junos.py` na função get_facts() com amostra mostrada abaixo com acréscimo de teste da entrada do dicionário para problema encontrado na RE0 e uptime da máquina virtual JunosOlive.
```python
uptime = '0'
        if 'RE0' in output:
            if output['RE0'] is not None: # Fix for RE0: None
                uptime = output['RE0']['up_time']
```

###### Outras dificuldades encontradas
- Mikrotik
  + Erro de conexão sem senha configurada no roteador
  + Biblioteca NAPALM limitada, não suporta todas as funções (ex. alteração de configuração)
- Juniper
  + Habilitar SSH para conexão com salt
  + Alteração na biblioteca como mostrado acima
- Cisco
  + Habilitar SSH e senha de enable para conexão com salt
  + Necessidade de privilégio do username na conexão
  + `optional_args: secret` no pillar com senha de enable
  + Inclusão do disk0 na imagem no gns3
  + Configuração line vty (conexão e timeout)

###### Lista de outros comandos úteis
- `salt saltutil.refresh_pillar`
  + Atualiza informações do pillar (reload do arquivo sls)
- `salt pillar.items`
  + Lista conteúdo do pillar
- `salt pillar.get`
  + Obtem algum elemento do pillar
- `salt grains.ls`
  + Lista grains
- `salt grains.items`
  + Lista dados dos grains
- `salt net.config_changed`
  + Verifica se configuração foi alterada
- `salt net.compare_config`
  + Compara configuração antes do commit
- `salt net.config_control`
  + Realiza commit (ou rollback caso algum erro)
- `salt net.rollback`
  + Desfaz última alteração

## Referências
- [SaltStack Github](https://github.com/saltstack)
- [SaltStack Documentation](https://docs.saltstack.com/en/latest/)
- [Napalm](https://github.com/napalm-automation/napalm-salt)
- [Mircea Ulinic](https://mirceaulinic.net/)