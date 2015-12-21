===================================
Tap as a Service installation guide
===================================

This is the installation guide for enabling Tap-as-a-Service(TaaS) feature in
OpenStack Neutron

We have tested TaaS with latest version DevStack running on Ubuntu 12.04 and
14.04. TaaS is currently under active development and we will update you of
new features and capabilities as and when they become available. Feel free to
approach us with any issues related to installing or using TaaS.

Dependencies
============

TaaS requires the 'Port Security' Neutron ML2 extension. Please make sure that
this extension has been enabled.

Adding the following to 'local.conf' while installing DevStack will enable
'Port Security' extension. (It's enabled by default)

    Q_ML2_PLUGIN_EXT_DRIVERS=port_security


Installation
============

You can use DevStack external plugin.
See `devstack/README.rst`.
