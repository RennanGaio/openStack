mport shade
print "Iniciando script \n"
cloud = shade.openstack_cloud(cloud='Kontron')

ex_userdata='''#!/usr/bin/env bash
echo "nameserver 8.8.8.8" >> /etc/resolv.conf;
echo "127.0.0.1 teste2" >> /etc/hosts;
cd /home/ubuntu; bash run_all.sh'''

instance_name = 'teste2'
rede = "rede_privada"

cloud.create_server(instance_name, image='primeiro_save', flavor=flavor_name,
wait=True, auto_ip=True, key_name=keypair_name,
security_groups=[sec_group_name], network=rede,
userdata=ex_userdata)
