========================
DevStack external plugin
========================

A `local.conf` recipe to enable tap-as-a-service::

    [[local|localrc]]
    enable_plugin tap-as-a-service https://github.com/openstack/tap-as-a-service
    enable_service taas
    TAAS_SERVICE_DRIVER=TAAS:TAAS:neutron_taas.services.taas.service_drivers.taas_rpc.TaasRpcDriver:default

Quality of Service (QoS) support
================================

To enable QoS for TaaS, follow the steps below:
Add neutron as enable_plugin and enable `q-qos` in `local.conf`::

    enable_plugin neutron https://git.openstack.org/openstack/neutron
    enable_service q-qos

Enable `use_qos` in `neutron.conf`::

    [taas]
    use_qos = True
