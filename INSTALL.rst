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

Adding the folowing to 'local.conf' while installing devstack will enable
'Port Security' extension. (It's enabled by default)

    Q_ML2_PLUGIN_EXT_DRIVERS=port_security


Installation
============

1. Install DevStack (remember to have 'port security' extension enabled)

2. Clone the TaaS git repository from git://git.openstack.org/stackforge/tap-as-a-service

3. Find the installation script named 'install.sh' in the base directory (Located along with
   README.rst and INSTALL.rst files) A complete installation of TaaS requires installation
   of TaaS Plugin, TaaS Agent, and TaaS cli.

4. To install the TaaS plugin invoke the following command

   	./install.sh install_plugin <directory where devstack neutron is installed> <mysql password>

	Example: ./install.sh install_plugin /opt/stack/neutron/ stackdb

   Install the TaaS plugin on the node where Neutron Service is running (usually the controller node)

5. To install the TaaS agent invoke the following command

   	./install.sh install_agent <directory where devstack neutron is installed>

	Example: ./install.sh install_agent /opt/stack/neutron/ stackdb

   Install the TaaS agent on all the compute nodes.

   **Important**: Note that if controller and compute are running on the same node, only run install_plugin
   and it will install both the TaaS plugin and agent 

Running TaaS
============

1. Running devstack neutron with TaaS plugin enabled (on the node where neutron server is running)

   Once the installation is complete, go to the devstack screen session where neutron
   server is running and kill the process and start it again. This should now start
   neutron with TaaS plugin enabled.

2. Running the TaaS Agent (on all the compute nodes)

   Run ./install.sh run_agent <directory where devstack neutron is installed>
   example ./install.sh run_agent /opt/stack/neutron/

   This should start up the TaaS agent and run it on the terminal.

Note
====

When you restack the devstack, make sure to run the TaaS installation process again
We are working towards making TaaS more seemlessly integrated with devstack and make
the installation process easier.


