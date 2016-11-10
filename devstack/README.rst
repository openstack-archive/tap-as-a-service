========================
DevStack external plugin
========================

A `local.conf` recipe to enable tap-as-a-service::

    [[local|localrc]]
    enable_plugin tap-as-a-service https://github.com/openstack/tap-as-a-service
    enable_service taas
    enable_service taas_openvswitch_agent
    Q_PLUGIN_EXTRA_CONF_PATH=/etc/neutron
    Q_PLUGIN_EXTRA_CONF_FILES=(taas_plugin.ini)
    TAAS_SERVICE_DRIVER=TAAS:TAAS:neutron_taas.services.taas.service_drivers.taas_rpc.TaasRpcDriver:default


Horizon panels for Neutron Taas
===============================

To enable the taas-dashboard is add the following to local.conf::

    enable_service neutron_taas_dashboard
