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
