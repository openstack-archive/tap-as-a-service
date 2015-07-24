#!/bin/bash

taas_get_mac_addr()
{
	NEUTRON_PORT=$1

	MAC_ADDR=`neutron port-show $NEUTRON_PORT | grep mac_address | cut -d'|' -f 3 | cut -d' ' -f 2`

	echo $MAC_ADDR
}

taas_get_ovs_portname()
{
	NEUTRON_PORT=$1

	echo "qvo${NEUTRON_PORT:0:11}"
}

taas_get_ovs_portid()
{
	BRIDGE=$1
	OVS_PORT_NAME=$2

	PORT_ID=`ovs-ofctl show $BRIDGE | grep $OVS_PORT_NAME | cut -d' ' -f 2 | cut -d'(' -f 1`

	echo $PORT_ID
}

taas_init()
{
	HOST_IP=$1

	# br-tap
	BRIDGE="tcp:$HOST_IP:6632"
	PATCHTAPINT_PORT_ID=`taas_get_ovs_portid $BRIDGE patch-tapint`
	PATCHTAPTUN_PORT_ID=`taas_get_ovs_portid $BRIDGE patch-taptun`
	ovs-ofctl add-flow $BRIDGE "table=0,priority=1,in_port=$PATCHTAPINT_PORT_ID,actions=resubmit(,1)"
	ovs-ofctl add-flow $BRIDGE "table=0,priority=1,in_port=$PATCHTAPTUN_PORT_ID,actions=resubmit(,2)"
	ovs-ofctl add-flow $BRIDGE "table=0,priority=0,actions=drop"
	ovs-ofctl add-flow $BRIDGE "table=1,priority=0,actions=output:$PATCHTAPTUN_PORT_ID"
	ovs-ofctl add-flow $BRIDGE "table=2,priority=0,actions=drop"

	# br-tun
	BRIDGE="tcp:$HOST_IP:6633"
	PATCHTUNTAP_PORT_ID=`taas_get_ovs_portid $BRIDGE patch-tuntap`
	ovs-ofctl add-flow $BRIDGE "table=0,priority=1,in_port=$PATCHTUNTAP_PORT_ID,actions=resubmit(,30)"
	ovs-ofctl add-flow $BRIDGE "table=30,priority=0,actions=move:NXM_OF_VLAN_TCI[0..11]->NXM_NX_TUN_ID[0..11],mod_vlan_vid:1,output:2,output:3"
	ovs-ofctl add-flow $BRIDGE "table=31,priority=2,reg0=0,actions=output:$PATCHTUNTAP_PORT_ID"
	ovs-ofctl add-flow $BRIDGE "table=31,priority=1,reg0=1,actions=output:$PATCHTUNTAP_PORT_ID,move:NXM_OF_VLAN_TCI[0..11]->NXM_NX_TUN_ID[0..11],mod_vlan_vid:2,output:in_port"
	ovs-ofctl add-flow $BRIDGE "table=31,priority=0,reg0=2,actions=learn(table=30,hard_timeout=60,priority=1,NXM_OF_VLAN_TCI[0..11],load:NXM_OF_VLAN_TCI[0..11]->NXM_NX_TUN_ID[0..11],load:0->NXM_OF_VLAN_TCI[0..11],output:NXM_OF_IN_PORT[])"
}

taas_clean()
{
	HOST_IP=$1

	# br-tap
	BRIDGE="tcp:$HOST_IP:6632"
	ovs-ofctl del-flows $BRIDGE "table=0"
	ovs-ofctl del-flows $BRIDGE "table=1"
	ovs-ofctl del-flows $BRIDGE "table=2"

	# br-tun
	BRIDGE="tcp:$HOST_IP:6633"
	PATCHTUNTAP_PORT_ID=`taas_get_ovs_portid $BRIDGE patch-tuntap`
	ovs-ofctl del-flows $BRIDGE "table=0,in_port=$PATCHTUNTAP_PORT_ID"
	ovs-ofctl del-flows $BRIDGE "table=30"
	ovs-ofctl del-flows $BRIDGE "table=31"
}

taas_create()
{
	HOST_IP=$1
	TAAS_ID=$2
	NEUTRON_PORT=$3
	VLAN=$4

	taas_init $HOST_IP

	# br-int
	BRIDGE="tcp:$HOST_IP:6631"
	PATCHINTTAP_PORT_ID=`taas_get_ovs_portid $BRIDGE patch-inttap`
	OVS_PORT_NAME=`taas_get_ovs_portname $NEUTRON_PORT`
	OVS_PORT_ID=`taas_get_ovs_portid $BRIDGE $OVS_PORT_NAME`
	ovs-ofctl add-flow $BRIDGE "table=0,priority=20,in_port=$PATCHINTTAP_PORT_ID,dl_vlan=$TAAS_ID,actions=mod_vlan_vid:$VLAN,output:$OVS_PORT_ID"

	# br-tap
	BRIDGE="tcp:$HOST_IP:6632"
	PATCHTAPINT_PORT_ID=`taas_get_ovs_portid $BRIDGE patch-tapint`
	ovs-ofctl add-flow $BRIDGE "table=1,priority=1,dl_vlan=$TAAS_ID,actions=output:in_port"
	ovs-ofctl add-flow $BRIDGE "table=2,priority=1,dl_vlan=$TAAS_ID,actions=output:$PATCHTAPINT_PORT_ID"

	# br-tun
	BRIDGE="tcp:$HOST_IP:6633"
	ovs-ofctl add-flow $BRIDGE "table=2,priority=1,tun_id=$TAAS_ID,actions=move:NXM_OF_VLAN_TCI[0..11]->NXM_NX_REG0[0..11],move:NXM_NX_TUN_ID[0..11]->NXM_OF_VLAN_TCI[0..11],resubmit(,31)"
}

taas_destroy()
{
	HOST_IP=$1
	TAAS_ID=$2

	# br-int
	BRIDGE="tcp:$HOST_IP:6631"
	PATCHINTTAP_PORT_ID=`taas_get_ovs_portid $BRIDGE patch-inttap`
	ovs-ofctl del-flows $BRIDGE "table=0,in_port=$PATCHINTTAP_PORT_ID,dl_vlan=$TAAS_ID"

	# br-tap
	BRIDGE="tcp:$HOST_IP:6632"
	ovs-ofctl del-flows $BRIDGE "table=1,dl_vlan=$TAAS_ID"
	ovs-ofctl del-flows $BRIDGE "table=2,dl_vlan=$TAAS_ID"

	# br-tun
	BRIDGE="tcp:$HOST_IP:6633"
	ovs-ofctl del-flows $BRIDGE "table=2,tun_id=$TAAS_ID"
}

taas_src_add()
{
	HOST_IP=$1
	TAAS_ID=$2
	NEUTRON_PORT=$3
	VLAN=$4
	DIR=$5

	taas_init $HOST_IP

	# br-int
	BRIDGE="tcp:$HOST_IP:6631"
	if [ $DIR = "e" ] || [ $DIR = "b" ]
	then
		PATCHINTTAP_PORT_ID=`taas_get_ovs_portid $BRIDGE patch-inttap`
		OVS_PORT_NAME=`taas_get_ovs_portname $NEUTRON_PORT`
		OVS_PORT_ID=`taas_get_ovs_portid $BRIDGE $OVS_PORT_NAME`
		ovs-ofctl add-flow $BRIDGE "table=0,priority=10,in_port=$OVS_PORT_ID,actions=normal,mod_vlan_vid:$TAAS_ID,output:$PATCHINTTAP_PORT_ID"
	fi
	if [ $DIR = "i" ] || [ $DIR = "b" ]
	then
		MAC_ADDR=`taas_get_mac_addr $NEUTRON_PORT`
		ovs-ofctl add-flow $BRIDGE "table=0,priority=10,dl_vlan=$VLAN,dl_dst=$MAC_ADDR,actions=normal,mod_vlan_vid:$TAAS_ID,output:$PATCHINTTAP_PORT_ID"
		ovs-ofctl add-flow $BRIDGE "table=0,priority=10,dl_vlan=$VLAN,dl_dst=01:00:00:00:00:00/01:00:00:00:00:00,actions=normal,mod_vlan_vid:$TAAS_ID,output:$PATCHINTTAP_PORT_ID"
	fi

	# br-tun
	BRIDGE="tcp:$HOST_IP:6633"
	ovs-ofctl add-flow $BRIDGE "table=2,priority=1,tun_id=$TAAS_ID,actions=move:NXM_OF_VLAN_TCI[0..11]->NXM_NX_REG0[0..11],move:NXM_NX_TUN_ID[0..11]->NXM_OF_VLAN_TCI[0..11],resubmit(,31)"
}

taas_src_delete()
{
	HOST_IP=$1
	TAAS_ID=$2
	NEUTRON_PORT=$3
	VLAN=$4
	DIR=$5

	# br-int
	BRIDGE="tcp:$HOST_IP:6631"
	if [ $DIR = "e" ] || [ $DIR = "b" ]
	then
		OVS_PORT_NAME=`taas_get_ovs_portname $NEUTRON_PORT`
		OVS_PORT_ID=`taas_get_ovs_portid $BRIDGE $OVS_PORT_NAME`
		ovs-ofctl del-flows $BRIDGE "table=0,in_port=$OVS_PORT_ID"
	fi
	if [ $DIR = "i" ] || [ $DIR = "b" ]
	then
		MAC_ADDR=`taas_get_mac_addr $NEUTRON_PORT`
		ovs-ofctl del-flows $BRIDGE "table=0,dl_vlan=$VLAN,dl_dst=$MAC_ADDR"
		ovs-ofctl del-flows $BRIDGE "table=0,dl_vlan=$VLAN,dl_dst=01:00:00:00:00:00/01:00:00:00:00:00"
	fi

	# br-tun
	BRIDGE="tcp:$HOST_IP:6633"
	ovs-ofctl del-flows $BRIDGE "table=2,tun_id=$TAAS_ID"
}

taas_dumpflows()
{
	HOST_IP=$1

	echo -e "\n*** Tap-aaS Flows ($HOST_IP) ***\n"

	# br-int
	echo "br-int"
	BRIDGE="tcp:$HOST_IP:6631"
	ovs-ofctl dump-flows $BRIDGE table=0
	echo -e "\n"

	# br-tap
	echo "br-tap"
	BRIDGE="tcp:$HOST_IP:6632"
	ovs-ofctl dump-flows $BRIDGE
	echo -e "\n"

	# br-tun
	echo "br-tun"
	BRIDGE="tcp:$HOST_IP:6633"
	ovs-ofctl dump-flows $BRIDGE table=0
	ovs-ofctl dump-flows $BRIDGE table=2
	ovs-ofctl dump-flows $BRIDGE table=30
	ovs-ofctl dump-flows $BRIDGE table=31
	echo -e "\n"
}


CMD=$1
case $CMD in
	"clean")
		HOST_IP=$2
		if [ -z $HOST_IP ]
		then
			echo "Usage: $0 $CMD <host-ip>"
			exit 1
		fi
		taas_clean $HOST_IP
	;;
	"create")
		HOST_IP=$2
		TAAS_ID=$3
		NEUTRON_PORT=$4
		VLAN=$5
		if [ -z $HOST_IP ] || [ -z $TAAS_ID ] || [ -z $NEUTRON_PORT ] || [ -z $VLAN ] 
		then
			echo "Usage: $0 $CMD <host-ip> <taas-id> <neutron-port> <vlan>"
			exit 1
		fi
		taas_create $HOST_IP $TAAS_ID $NEUTRON_PORT $VLAN
	;;
	"destroy")
		HOST_IP=$2
		TAAS_ID=$3
		if [ -z $HOST_IP ] || [ -z $TAAS_ID ] 
		then
			echo "Usage: $0 $CMD <host-ip> <taas-id>"
			exit 1
		fi
		taas_destroy $HOST_IP $TAAS_ID
	;;
	"src-add")
		HOST_IP=$2
		TAAS_ID=$3
		NEUTRON_PORT=$4
		VLAN=$5
		DIR=$6
		if [ -z $HOST_IP ] || [ -z $TAAS_ID ] || [ -z $NEUTRON_PORT ] || [ -z $VLAN ] || [ -z $DIR ]
		then
			echo "Usage: $0 $CMD <host-ip> <taas-id> <neutron-port> <vlan> <dir>"
			exit 1
		fi
		taas_src_add $HOST_IP $TAAS_ID $NEUTRON_PORT $VLAN $DIR
	;;
	"src-delete")
		HOST_IP=$2
		TAAS_ID=$3
		NEUTRON_PORT=$4
		VLAN=$5
		DIR=$6
		if [ -z $HOST_IP ] || [ -z $TAAS_ID ] || [ -z $NEUTRON_PORT ] || [ -z $VLAN ] || [ -z $DIR ]
		then
			echo "Usage: $0 $CMD <host-ip> <taas-id> <neutron-port> <vlan> <dir>"
			exit 1
		fi
		taas_src_delete $HOST_IP $TAAS_ID $NEUTRON_PORT $VLAN $DIR
	;;
	"dumpflows")
		HOST_IP=$2
		if [ -z $HOST_IP ]
		then
			echo "Usage: $0 $CMD <host-ip>"
			exit 1
		fi
		taas_dumpflows $HOST_IP
	;;
	*)
		echo "Usage: $0 <cmd> [option] [option] ..."
		exit 1
	;;
esac

exit 0
