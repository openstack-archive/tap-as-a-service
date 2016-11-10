/* global Hogan */
/* Namespace for core functionality related to Network Topology. */

horizon.network_topology.balloon_tapserviceTmpl = null;
horizon.network_topology.balloon_tapflowTmpl = null;

horizon.network_topology.init = function() {
  var self = this;
  angular.element(self.svg_container).spin(horizon.conf.spinner_options.modal);
  if (angular.element('#networktopology').length === 0) {
    return;
  }

  self.data = {};
  self.data.networks = {};
  self.data.routers = {};
  self.data.servers = {};
  self.data.ports = {};

  // Setup balloon popups
  self.balloonTmpl = Hogan.compile(angular.element('#balloon_container').html());
  self.balloon_deviceTmpl = Hogan.compile(angular.element('#balloon_device').html());
  self.balloon_portTmpl = Hogan.compile(angular.element('#balloon_port').html());
  self.balloon_netTmpl = Hogan.compile(angular.element('#balloon_net').html());
  self.balloon_instanceTmpl = Hogan.compile(angular.element('#balloon_instance').html());
  self.balloon_tapserviceTmpl = Hogan.compile(angular.element('#balloon_tapservice').html());
  self.balloon_tapflowTmpl = Hogan.compile(angular.element('#balloon_tapflow').html());

  angular.element(document)
    .on('click', 'a.closeTopologyBalloon', function(e) {
      e.preventDefault();
      self.delete_balloon();
    })
    .on('click', '.topologyBalloon', function(e) {
      e.stopPropagation();
    })
    .on('click', 'a.vnc_window', function(e) {
      e.preventDefault();
      var vncWindow = window.open(angular.element(this).attr('href'), vncWindow,
                                  'width=760,height=560');
      self.delete_balloon();
    });

  angular.element('#toggle_labels').click(function() {
    if (angular.element('.nodeLabel').css('display') == 'none') {
      angular.element('.nodeLabel').show();
      horizon.cookies.put('show_labels', true);
    } else {
      angular.element('.nodeLabel').hide();
      horizon.cookies.put('show_labels', false);
    }
  });

  angular.element('#toggle_networks').click(function() {
    for (var n in self.nodes) {
      if ({}.hasOwnProperty.call(self.nodes, n)) {
        if (self.nodes[n].data instanceof Network || self.nodes[n].data instanceof ExternalNetwork) {
          self.collapse_network(self.nodes[n]);
        }
        if (horizon.cookies.get('show_labels')) {
          angular.element('.nodeLabel').show();
        }
      }
    }
    var current = horizon.cookies.get('are_networks_collapsed');
    horizon.cookies.put('are_networks_collapsed', !current);
  });

  angular.element('#topologyCanvasContainer').spin(horizon.conf.spinner_options.modal);
  self.create_vis();
  self.loading();
  self.force_direction(0.05,70,-700);
  if(horizon.networktopologyloader.model !== null) {
    self.retrieve_network_info(true);
  }

  d3.select(window).on('resize', function() {
    var width = angular.element('#topologyCanvasContainer').width();
    var height = angular.element('#topologyCanvasContainer').height();
    self.force.size([width, height]).resume();
  });

  angular.element('#networktopology').on('change', function() {
    self.retrieve_network_info(true);
  });

  // register for message notifications
  horizon.networktopologymessager.addMessageHandler(this.handleMessage, this);
};

// Create a new node
horizon.network_topology.new_node = function(data, x, y) {
  var self = this;
  data = {data: data};
  if (x && y) {
    data.x = x;
    data.y = y;
  }
  self.nodes.push(data);

  var node = self.vis.selectAll('g.node').data(self.nodes);
  var nodeEnter = node.enter().append('g')
    .attr('class', 'node')
    .style('fill', 'white')
    .call(self.force.drag);

  nodeEnter.append('circle')
    .attr('class', 'frame')
    .attr('r', function(d) {
      switch (Object.getPrototypeOf(d.data)) {
      case ExternalNetwork.prototype:
        return 35;
      case Network.prototype:
        return 30;
      case Router.prototype:
        return 25;
      case Server.prototype:
        return 20;
      }
    })
    .style('fill', function(d) {
      if (d.data.tapservice == "true") {
        return 'cyan';
      } else if (d.data.tapflow == "true") {
        return 'pink';
      } else {
        return 'white';
      }
    })
    .style('stroke', 'black')
    .style('stroke-width', 3);

  switch ( data.data.iconType ) {
  case 'text':
    nodeEnter.append('text')
      .style('fill', 'black')
      .style('font', '20px FontAwesome')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .text(function(d) { return d.data.icon; })
      .attr('transform', function(d) {
        switch (Object.getPrototypeOf(d.data)) {
        case ExternalNetwork.prototype:
          return 'scale(2.5)';
        case Network.prototype:
          return 'scale(1.5)';
        case Server.prototype:
          return 'scale(1)';
        }
      });
    break;
  case 'path':
    nodeEnter.append('path')
      .attr('class', 'svgpath')
      .style('fill', 'black')
      .attr('d', function(d) { return self.svgs(d.data.svg); })
      .attr('transform', function() {
        return 'scale(1.2)translate(-16,-15)';
      });
    break;
  }

  nodeEnter.append('text')
    .attr('class', 'nodeLabel')
    .style('display',function() {
      var labels = horizon.cookies.get('topology_labels');
      if (labels) {
        return 'inline';
      } else {
        return 'none';
      }
    })
    .style('fill','black')
    .text(function(d) {
      return d.data.name;
    })
    .attr('transform', function(d) {
      switch (Object.getPrototypeOf(d.data)) {
      case ExternalNetwork.prototype:
        return 'translate(40,3)';
      case Network.prototype:
        return 'translate(35,3)';
      case Router.prototype:
        return 'translate(30,3)';
      case Server.prototype:
        return 'translate(25,3)';
      }
    });

  if (data.data instanceof Network || data.data instanceof ExternalNetwork) {
    nodeEnter.append('svg:text')
      .attr('class','vmCount')
      .style('fill', 'black')
      .style('font-size','20')
      .text('')
      .attr('transform', 'translate(26,38)');
  }

  nodeEnter.on('click', function(d) {
    self.show_balloon(d.data, d, angular.element(this));
  });

  // Highlight the links for currently selected node
  nodeEnter.on('mouseover', function(d) {
    self.vis.selectAll('line.link').filter(function(z) {
      if (z.source === d || z.target === d) {
        return true;
      } else {
        return false;
      }
    }).style('stroke-width', '3px');
  });

  // Remove the highlight on the links
  nodeEnter.on('mouseout', function() {
    self.vis.selectAll('line.link').style('stroke-width','1px');
  });
};

horizon.network_topology.load_topology = function(data) {
  var self = this;
  var net, _i, _netlen, _netref, rou, _j, _roulen, _rouref, port, _l, _portlen, _portref,
  ser, _k, _serlen, _serref, obj, vmCount;
  var change = false;
  var filterNode = function(obj) {
    return function(d) {
      return obj == d.data;
    };
  };

  // Networks
  _netref = data.networks;
  for (_i = 0, _netlen = _netref.length; _i < _netlen; _i++) {
    net = _netref[_i];
    var network = null;
    if (net['router:external'] === true) {
      network = new ExternalNetwork(net);
    } else {
      network = new Network(net);
    }

    if (!self.already_in_graph(self.data.networks, network)) {
      self.new_node(network);
      change = true;
    } else {
      obj = self.find_by_id(network.id);
      if (obj) {
        network.collapsed = obj.data.collapsed;
        network.instances = obj.data.instances;
        obj.data = network;
      }
    }
    self.data.networks[network.id] = network;
  }

  // Routers
  _rouref = data.routers;
  for (_j = 0, _roulen = _rouref.length; _j < _roulen; _j++) {
    rou = _rouref[_j];
    var router = new Router(rou);
    if (!self.already_in_graph(self.data.routers, router)) {
      self.new_node(router);
      change = true;
    } else {
      obj = self.find_by_id(router.id);
      if (obj) {
        // Keep networks list
        router.networks = obj.data.networks;
        // Keep ports list
        router.ports = obj.data.ports;
        obj.data = router;
      }
    }
    self.data.routers[router.id] = router;
  }

  // Servers
  _serref = data.servers;
  for (_k = 0, _serlen = _serref.length; _k < _serlen; _k++) {
    ser = _serref[_k];
    var server = new Server(ser);
    if (!self.already_in_graph(self.data.servers, server)) {
      server.ports = self.select_ports(server.id, data.ports);
      if (server.tapservice == "true") {
        server.tapservices = self.select_tapservice(data.tapservices, server.ports);
      } else {
        server.tapservices = [];
      }
      if(server.tapflow == "true") {
        server.tapflows = self.select_tapflow(data.tapflows, server.ports);
      } else {
        server.tapflows = [];
      }
      self.new_node(server);
      change = true;
    } else {
      obj = self.find_by_id(server.id);
      if (obj) {
        // Keep networks list
        server.networks = obj.data.networks;
        // Keep ip address list
        server.ip_addresses = obj.data.ip_addresses;
        // Keep tap service list
        server.tapservices = obj.data.tapservices;
        // Keep tap flow list
        server.tapflows = obj.data.tapflows;
        obj.data = server;
      } else if (self.data.servers[server.id] !== undefined) {
        // This is used when servers are hidden because the network is
        // collapsed
        server.networks = self.data.servers[server.id].networks;
        server.ip_addresses = self.data.servers[server.id].ip_addresses;
      }
    }
    self.data.servers[server.id] = server;
  }

  // Ports
  _portref = data.ports;
  for (_l = 0, _portlen = _portref.length; _l < _portlen; _l++) {
    port = _portref[_l];
    if (!self.already_in_graph(self.data.ports, port)) {
      var device = self.find_by_id(port.device_id);
      var _network = self.find_by_id(port.network_id);
      if (angular.isDefined(device) && angular.isDefined(_network)) {
        if (port.device_owner == 'compute:nova' || port.device_owner == 'compute:None') {
          _network.data.instances++;
          device.data.networks.push(_network.data);
          if (port.fixed_ips) {
            for(var ip in port.fixed_ips) {
	      if (!listContains(port.fixed_ips[ip], device.data.ip_addresses)) {
                device.data.ip_addresses.push(port.fixed_ips[ip]);
	      }
            }
          }
          // Remove the recently added node if connected to a network which is
          // currently collapsed
          if (_network.data.collapsed) {
            if (device.data.networks.length == 1) {
              self.data.servers[device.data.id].networks = device.data.networks;
              self.data.servers[device.data.id].ip_addresses = device.data.ip_addresses;
              self.removeNode(self.data.servers[port.device_id]);
              vmCount = Number(self.vis.selectAll('.vmCount').filter(filterNode(_network.data))[0][0].textContent);
              self.vis.selectAll('.vmCount').filter(filterNode(_network.data))[0][0].textContent = vmCount + 1;
              continue;
            }
          }
        } else if (port.device_owner == 'network:router_interface') {
          device.data.networks.push(_network.data);
          device.data.ports.push(port);
        } else if (device.data.ports) {
          device.data.ports.push(port);
        }
        self.new_link(self.find_by_id(port.device_id), self.find_by_id(port.network_id));
        change = true;
      } else if (angular.isDefined(_network) && port.device_owner == 'compute:nova') {
        // Need to add a previously hidden node to the graph because it is
        // connected to more than 1 network
        if (_network.data.collapsed) {
          server = self.data.servers[port.device_id];
          server.networks.push(_network.data);
          if (port.fixed_ips) {
            for(var ip in port.fixed_ips) {
              server.ip_addresses.push(port.fixed_ips[ip]);
            }
          }
          self.new_node(server);
          // decrease collapsed vm count on network
          vmCount = Number(self.vis.selectAll('.vmCount').filter(filterNode(server.networks[0]))[0][0].textContent);
          if (vmCount == 1) {
            self.vis.selectAll('.vmCount').filter(filterNode(server.networks[0]))[0][0].textContent = '';
          } else {
            self.vis.selectAll('.vmCount').filter(filterNode(server.networks[0]))[0][0].textContent = vmCount - 1;
          }
          // Add back in first network link
          self.new_link(self.find_by_id(port.device_id), self.find_by_id(server.networks[0].id));
          // Add new link
          self.new_link(self.find_by_id(port.device_id), self.find_by_id(port.network_id));
          change = true;
        }
      }
    }
    self.data.ports[port.id+port.device_id+port.network_id] = port;
  }
  if (change) {
    self.force.start();
  }
  self.load_config();
};

horizon.network_topology.select_ports = function(device_id, ports){
  var local_ports = [];
  angular.element.each(ports, function(index, port){
    if (port.device_id === device_id) {
      local_ports.push(port);
    }
  });
  return local_ports;
};
horizon.network_topology.select_tapservice = function(tapservices, ports){
  var local_tapservices = [];
  angular.element.each(tapservices, function(index, tapservice){
    angular.element.each(ports, function(index, port) {
      if (tapservice.port_id === port.id) {
        local_tapservices.push(tapservice);
      }
    });
  });
  return local_tapservices;
};
horizon.network_topology.select_tapflow = function(tapflows, ports){
  var local_tapflows = [];
  angular.element.each(tapflows, function(index, tapflow){
    angular.element.each(ports, function(index, port) {
      if (tapflow.port_id === port.id) {
        local_tapflows.push(tapflow);
      }
    });
  });
  return local_tapflows;
};

horizon.network_topology.remove_node_on_delete = function(deleteData) {
  var self = this;
  var deviceId = deleteData.device_id;
  switch (deleteData.device_type) {
  case 'router':
    self.removeNode(self.data.routers[deviceId]);
    break;
  case 'instance':
    self.removeNode(self.data.servers[deviceId]);
    this.data.servers[deviceId] = undefined;
    break;
  case 'network':
    self.removeNode(self.data.networks[deviceId]);
    break;
  case 'port':
    self.removePort(deviceId, deleteData.device_data);
    break;
  case 'tapservice':
    self.removeTapService(deviceId);
    break;
  case 'tapflow':
    self.removeTapFlow(deleteData.device_data.tapflow_id);
    break;
  }
  self.delete_balloon();
};

horizon.network_topology.removeTapService = function(id) {
  var n, node, service, _i, _len, _ref, _t, _tref;
  _ref = this.nodes;
  for (_i = 0, _len = _ref.length; _i < _len && !node; _i++) {
    n = _ref[_i];
    _tref = n.data.tapservices;
    for (_t in _tref) { 
      var t = _tref[_t];
      if (t.id === id) {
        node = n;
        service = t;
        break;
      }
    }
  }
  if (node) {
    node.data.tapservices.splice(node.data.tapservices.indexOf(service), 1);
    filterTapService = function(node) {
      return function(d) {
        return node.data === d.data;
      };
    };
    this.vis.selectAll('circle.frame').filter(filterTapService(node)).style('fill', 'white');
  }
};

horizon.network_topology.removeTapFlow = function(id) {
  var n, node, flow, _i, _len, _ref, _t, _tref;
  _ref = this.nodes;
  for (_i = 0, _len = _ref.length; _i < _len && !node; _i++) {
    n = _ref[_i];
    _tref = n.data.tapflows;
    for (_t in _tref) { 
      var t = _tref[_t];
      if (t.id === id) {
        node = n;
        flow = t;
        break;
      }
    }
  }
  if (node) {
    node.data.tapflows.splice(node.data.tapflows.indexOf(flow), 1);
    filterTapFlow = function(node) {
      return function(d) {
        return node.data === d.data;
      };
    };
    this.vis.selectAll('circle.frame').filter(filterTapFlow(node)).style('fill', 'white');
  }
};

horizon.network_topology.delete_tapservice = function(tapserviceId) {
  var message = {id:tapserviceId};
  horizon.networktopologymessager.post_message(tapserviceId, 'deletetapservice', message, 'tapservice', 'delete', data={});
};

horizon.network_topology.delete_tapflow = function(tapserviceId, tapflowId) {
  var message = {id:tapflowId};
  var data = {tapservice_id:tapserviceId, tapflow_id:tapflowId};
  horizon.networktopologymessager.post_message(tapserviceId, 'tapservices/' + tapserviceId + '/', message, 'tapflow', 'delete', data);
};

horizon.network_topology.show_balloon = function(d,d2,element) {
  var self = this;
  var balloonTmpl = self.balloonTmpl;
  var deviceTmpl = self.balloon_deviceTmpl;
  var portTmpl = self.balloon_portTmpl;
  var netTmpl = self.balloon_netTmpl;
  var instanceTmpl = self.balloon_instanceTmpl;
  var tapserviceTmpl = self.balloon_tapserviceTmpl;
  var tapflowTmpl = self.balloon_tapflowTmpl;
  var balloonID = 'bl_' + d.id;
  var ports = [];
  var subnets = [];
  var tapservices = [];
  var tapflows = [];
  if (self.balloonID) {
    if (self.balloonID == balloonID) {
      self.delete_balloon();
      return;
    }
    self.delete_balloon();
  }
  self.force.stop();
  if (d.hasOwnProperty('ports')) {
    angular.element.each(d.ports, function(i, port) {
      var object = {};
      object.id = port.id;
      object.router_id = port.device_id;
      object.url = port.url;
      object.port_status = port.status;
      object.port_status_css = (port.original_status === 'ACTIVE') ? 'active' : 'down';
      var ipAddress = '';
      try {
        for (var ip in port.fixed_ips) {
          ipAddress += port.fixed_ips[ip].ip_address + ' ';
        }
      }catch(e) {
        ipAddress = gettext('None');
      }
      var deviceOwner = '';
      try {
        deviceOwner = port.device_owner.replace('network:','');
      }catch(e) {
        deviceOwner = gettext('None');
      }
      var networkId = '';
      try {
        networkId = port.network_id;
      }catch(e) {
        networkId = gettext('None');
      }
      object.ip_address = ipAddress;
      object.device_owner = deviceOwner;
      object.network_id = networkId;
      object.is_interface = (deviceOwner === 'router_interface' || deviceOwner === 'router_gateway');
      ports.push(object);
    });
  } else if (d.hasOwnProperty('subnets')) {
    angular.element.each(d.subnets, function(i, snet) {
      var object = {};
      object.id = snet.id;
      object.cidr = snet.cidr;
      object.url = snet.url;
      subnets.push(object);
    });
  }
  if (d.hasOwnProperty('tapservices')) {
    angular.element.each(d.tapservices,function(i, tapservice){
      var object = {};
      object.id = tapservice.id;
      object.name = tapservice.name;
      object.url = tapservice.url;
      tapservices.push(object);
    });
  }
  if (d.hasOwnProperty('tapflows')) {
    angular.element.each(d.tapflows,function(i, tapflow){
      var object = {};
      object.id = tapflow.id;
      object.name = tapflow.name;
      object.url = tapflow.url;
      object.tap_service_id = tapflow.tap_service_id;
      tapflows.push(object);
    });
  }
  var htmlData = {
    balloon_id:balloonID,
    id:d.id,
    url:d.url,
    name:d.name,
    type:d.type,
    delete_label: gettext('Delete'),
    status:d.status,
    status_class: (d.original_status === 'ACTIVE') ? 'active' : 'down',
    status_label: gettext('STATUS'),
    id_label: gettext('ID'),
    interfaces_label: gettext('Interfaces'),
    subnets_label: gettext('Subnets'),
    delete_interface_label: gettext('Delete Interface'),
    delete_subnet_label: gettext('Delete Subnet'),
    open_console_label: gettext('Open Console'),
    view_details_label: gettext('View Details'),
    ips_label: gettext('IP Addresses')
  };
  var html;
  if (d instanceof Router) {
    htmlData.delete_label = gettext('Delete Router');
    htmlData.view_details_label = gettext('View Router Details');
    htmlData.port = ports;
    htmlData.add_interface_url = 'router/' + d.id + '/addinterface';
    htmlData.add_interface_label = gettext('Add Interface');
    html = balloonTmpl.render(htmlData,{
      table1:deviceTmpl,
      table2:portTmpl
    });
  } else if (d instanceof Server) {
    htmlData.delete_label = gettext('Delete Instance');
    htmlData.view_details_label = gettext('View Instance Details');
    htmlData.console_id = d.id;
    htmlData.ips = d.ip_addresses;
    htmlData.console = d.console;
    htmlData.tapservice = tapservices;
    htmlData.tapflow = tapflows;
    htmlData.tapservice_label = gettext("Tap Service");
    htmlData.delete_tapservice_label = gettext("Delete Tap Service");
    htmlData.tapflow_label = gettext("Tap Flow");
    htmlData.create_tapflow_url = d.url + "createtapflow";
    htmlData.create_tapflow_label = gettext("Create Tap Flow");
    htmlData.delete_tapflow_label = gettext("Delete Tap Flow");
    html = balloonTmpl.render(htmlData,{
      table1:deviceTmpl,
      table2:instanceTmpl,
      table3:(d.tapservice == "true") ? tapserviceTmpl : null,
      table4:(self.is_tapservice() === true && d.tapservice == "false") ? tapflowTmpl : null
    });
  } else if (d instanceof Network || d instanceof ExternalNetwork) {
    for (var s in subnets) {
      subnets[s].network_id = d.id;
    }
    htmlData.subnet = subnets;
    if (d instanceof Network) {
      htmlData.delete_label = gettext('Delete Network');
    }
    htmlData.add_subnet_url = 'network/' + d.id + '/subnet/create';
    htmlData.add_subnet_label = gettext('Create Subnet');
    html = balloonTmpl.render(htmlData,{
      table1:deviceTmpl,
      table2:netTmpl
    });
  } else {
    return;
  }
  angular.element(self.svg_container).append(html);
  var devicePosition = self.getScreenCoords(d2.x, d2.y);
  var x = devicePosition.x;
  var y = devicePosition.y;
  var xoffset = 100;
  var yoffset = 95;
  angular.element('#' + balloonID).css({
    'left': x + xoffset + 'px',
    'top': y + yoffset + 'px'
  }).show();
  var _balloon = angular.element('#' + balloonID);
  if (element.x + _balloon.outerWidth() > angular.element(window).outerWidth()) {
    _balloon
      .css({
        'left': 0 + 'px'
      })
      .css({
        'left': (x - _balloon.outerWidth() + 'px')
      })
      .addClass('leftPosition');
  }
  _balloon.find('.delete-device').click(function() {
    var _this = angular.element(this);
    _this.prop('disabled', true);
    d3.select('#id_' + _this.data('device-id')).classed('loading',true);
    self.delete_device(_this.data('type'),_this.data('device-id'));
  });
  _balloon.find('.delete-port').click(function() {
    var _this = angular.element(this);
    self.delete_port(_this.data('router-id'),_this.data('port-id'),_this.data('network-id'));
    self.delete_balloon();
  });
  _balloon.find('.delete-tapservice').click(function(){
    var _this = angular.element(this);
    self.delete_tapservice(_this.data('tapservice-id'));
  });
  _balloon.find('.delete-tapflow').click(function(){
    var _this = angular.element(this);
    self.delete_tapflow(_this.data('tapservice-id'),_this.data('tapflow-id'));
  });
  self.balloonID = balloonID;
};

horizon.network_topology.is_tapservice = function(){
  var self = this;
  
  for(vm in self.data.servers){
    if (self.data.servers[vm] !== undefined) {
      if (self.data.servers[vm].tapservice == "true") {
	return true;
      }
    }
  }
  return false;

};
