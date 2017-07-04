========================
DevStack external plugin
========================

A `local.conf` recipe to enable tap-as-a-service::

    [[local|localrc]]
    enable_plugin tap-as-a-service https://github.com/openstack/tap-as-a-service
    enable_service taas
    TAAS_SERVICE_DRIVER=TAAS:TAAS:neutron_taas.services.taas.service_drivers.taas_rpc.TaasRpcDriver:default
