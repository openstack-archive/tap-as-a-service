#!/usr/bin/python

# Copyright (C) 2015 Ericsson AB
# Copyright (C) 2015 Gigamon
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import argparse
import json
import os
import requests


SUCCESS = 0
FAILURE = 1


class taas_rest_api(object):

    def __init__(self):
        #
        # Initialize authentication service endpoint and user
        # credentials from environment variables
        #
        self.auth_url = os.environ['OS_AUTH_URL']
        self.tenant_name = os.environ['OS_TENANT_NAME']
        self.username = os.environ['OS_USERNAME']
        self.password = os.environ['OS_PASSWORD']

        self.token_id = None

        return

    def authenticate(self):
        # Generate a new authentication token
        req_data = {}
        req_data['auth'] = {
            'tenantName': self.tenant_name,
            'passwordCredentials': {
                'username': self.username,
                'password': self.password
            }
        }

        req_data_json = json.dumps(req_data)

        url = '%s/tokens' % self.auth_url

        response = requests.post(url, req_data_json)
        res_data = response.json()

        if response.status_code != 200:
            error = res_data['error']
            print ('Error code: %s (%s)' % (error['code'], error['title']))
            return FAILURE

        # Remember new token ID
        self.token_id = res_data['access']['token']['id']

        # Remember tenant ID
        self.tenant_id = res_data['access']['token']['tenant']['id']

        # Find network service endpoint
        found = False
        service_catalog = res_data['access']['serviceCatalog']
        for service in service_catalog:
            if service['type'] == 'network':
                endpoints = service['endpoints']
                endpoint = endpoints[0]
                network_service_url = endpoint['publicURL']
                found = True
                break

        if found is False:
            print ('Error: Could not find network service endpoint')
            return FAILURE

        # Formulate and remember TaaS endpoint
        self.taas_url = '%s/v2.0/taas/' % network_service_url

        return SUCCESS

    def tap_service_create(self,
                           name,
                           description,
                           port_id,
                           network_id):
        header_data = {}
        header_data['X-Auth-Token'] = self.token_id

        req_data = {}
        req_data['tap_service'] = {
            'tenant_id': self.tenant_id,
            'name': name,
            'description': description,
            'port_id': port_id,
            'network_id': network_id
        }

        req_data_json = json.dumps(req_data)

        url = '%s/tap-services' % self.taas_url

        response = requests.post(url, req_data_json, headers=header_data)
        res_data = response.json()

        if response.status_code != 201:
            error = res_data['NeutronError']
            print (error['message'])
            return FAILURE

        tap_service = res_data['tap_service']

        # Show information of the new tap service
        self.tap_service_show(tap_service['id'])

        return SUCCESS

    def tap_service_delete(self, tap_service_id):
        header_data = {}
        header_data['X-Auth-Token'] = self.token_id

        url = '%s/tap-services/%s' % (self.taas_url, tap_service_id)

        response = requests.delete(url, headers=header_data)

        if response.status_code != 204:
            res_data = response.json()
            error = res_data['NeutronError']
            print (error['message'])
            return FAILURE

        return SUCCESS

    def tap_service_list(self):
        header_data = {}
        header_data['X-Auth-Token'] = self.token_id

        url = '%s/tap-services' % self.taas_url

        response = requests.get(url, headers=header_data)
        res_data = response.json()

        if response.status_code != 200:
            error = res_data['NeutronError']
            print (error['message'])
            return FAILURE

        tap_services = res_data['tap_services']

        sep = '+' + '-' * 38 + '+' + '-' * 12 + '+' + '-' * 38 + '+'
        print (sep)
        print ('| {:36s} | {:10s} | {:36s} |'.format('ID', 'Name', 'Port ID'))
        print (sep)
        for tap_service in tap_services:
            print ('| {:36s} | {:10s} | {:36s} |'
                   .format(tap_service['id'],
                           tap_service['name'],
                           tap_service['port_id']))
        print (sep)

        return SUCCESS

    def tap_service_show(self, tap_service_id):
        header_data = {}
        header_data['X-Auth-Token'] = self.token_id

        url = '%s/tap-services/%s' % (self.taas_url, tap_service_id)

        response = requests.get(url, headers=header_data)
        res_data = response.json()

        if response.status_code != 200:
            error = res_data['NeutronError']
            print (error['message'])
            return FAILURE

        tap_service = res_data['tap_service']

        sep = '+' + '-' * 13 + '+' + '-' * 38 + '+'
        print (sep)
        print ('| {:11} | {:36s} |'.format('Field', 'Value'))
        print (sep)
        print ('| {:11} | {:36s} |'
               .format('Name', tap_service['name']))
        print ('| {:11} | {:36s} |'
               .format('Description', tap_service['description']))
        print ('| {:11} | {:36s} |'
               .format('ID', tap_service['id']))
        print ('| {:11} | {:36s} |'
               .format('Port ID', tap_service['port_id']))
        print ('| {:11} | {:36s} |'
               .format('Tenant ID', tap_service['tenant_id']))
        print (sep)

        return SUCCESS

    def tap_flow_create(self,
                        name,
                        description,
                        port_id,
                        direction,
                        tap_service_id):
        header_data = {}
        header_data['X-Auth-Token'] = self.token_id

        req_data = {}
        req_data['tap_flow'] = {
            'tenant_id': self.tenant_id,
            'name': name,
            'description': description,
            'source_port': port_id,
            'direction': direction,
            'tap_service_id': tap_service_id
        }

        req_data_json = json.dumps(req_data)

        url = '%s/tap-flows' % self.taas_url

        response = requests.post(url, req_data_json, headers=header_data)
        res_data = response.json()

        if response.status_code != 201:
            error = res_data['NeutronError']
            print (error['message'])
            return FAILURE

        tap_flow = res_data['tap_flow']

        # Show information of the new tap flow
        self.tap_flow_show(tap_flow['id'])

        return SUCCESS

    def tap_flow_delete(self, tap_flow_id):
        header_data = {}
        header_data['X-Auth-Token'] = self.token_id

        url = '%s/tap-flows/%s' % (self.taas_url, tap_flow_id)

        response = requests.delete(url, headers=header_data)

        if response.status_code != 204:
            res_data = response.json()
            error = res_data['NeutronError']
            print (error['message'])
            return FAILURE

        return SUCCESS

    def tap_flow_list(self, tap_service_id):
        header_data = {}
        header_data['X-Auth-Token'] = self.token_id

        url = '%s/tap-flows' % self.taas_url

        response = requests.get(url, headers=header_data)
        res_data = response.json()

        if response.status_code != 200:
            error = res_data['NeutronError']
            print (error['message'])
            return FAILURE

        tap_flows = res_data['tap_flows']

        sep = '+' + '-' * 38 + '+' + '-' * 12 + \
            '+' + '-' * 38 + '+' + '-' * 38 + '+'
        print (sep)
        print ('| {:36s} | {:10s} | {:36s} | {:36s} |'.format(
            'ID', 'Name', 'Port ID', 'Tap Service ID'))
        print (sep)
        for tap_flow in tap_flows:
            #
            # If a tap service has been specified only display tap flows
            # associated with that tap service; otherwise display all tap
            # flows that belong to the tenant
            #
            if (tap_service_id is None or
                    tap_service_id == tap_flow['tap_service_id']):

                print ('| {:36s} | {:10s} | {:36s} | {:36s} |'
                       .format(tap_flow['id'],
                               tap_flow['name'],
                               tap_flow['source_port'],
                               tap_flow['tap_service_id']))
        print (sep)

        return SUCCESS

    def tap_flow_show(self, tap_flow_id):
        header_data = {}
        header_data['X-Auth-Token'] = self.token_id

        url = '%s/tap-flows/%s' % (self.taas_url, tap_flow_id)

        response = requests.get(url, headers=header_data)
        res_data = response.json()

        if response.status_code != 200:
            error = res_data['NeutronError']
            print (error['message'])
            return FAILURE

        tap_flow = res_data['tap_flow']

        sep = '+' + '-' * 16 + '+' + '-' * 38 + '+'
        print (sep)
        print ('| {:14} | {:36s} |'.format('Field', 'Value'))
        print (sep)
        print ('| {:14} | {:36s} |'
               .format('Name', tap_flow['name']))
        print ('| {:14} | {:36s} |'
               .format('Description', tap_flow['description']))
        print ('| {:14} | {:36s} |'
               .format('ID', tap_flow['id']))
        print ('| {:14} | {:36s} |'
               .format('Port ID', tap_flow['source_port']))
        print ('| {:14} | {:36s} |'
               .format('Direction', tap_flow['direction']))
        print ('| {:14} | {:36s} |'
               .format('Tap Service ID', tap_flow['tap_service_id']))
        print ('| {:14} | {:36s} |'
               .format('Tenant ID', tap_flow['tenant_id']))
        print (sep)

        return SUCCESS


# Handler for 'tap-service-create' subcommand
def tap_service_create(args):
    api = taas_rest_api()

    retval = api.authenticate()
    if retval != SUCCESS:
        return retval

    return api.tap_service_create(args.name,
                                  args.description,
                                  args.port_id,
                                  args.network_id)


# Handler for 'tap-service-delete' subcommand
def tap_service_delete(args):
    api = taas_rest_api()

    retval = api.authenticate()
    if retval != SUCCESS:
        return retval

    return api.tap_service_delete(args.id)


# Handler for 'tap-service-list' subcommand
def tap_service_list(args):
    api = taas_rest_api()

    retval = api.authenticate()
    if retval != SUCCESS:
        return retval

    return api.tap_service_list()


# Handler for 'tap-service-show' subcommand
def tap_service_show(args):
    api = taas_rest_api()

    retval = api.authenticate()
    if retval != SUCCESS:
        return retval

    return api.tap_service_show(args.id)


# Handler for 'tap-flow-create' subcommand
def tap_flow_create(args):
    api = taas_rest_api()

    retval = api.authenticate()
    if retval != SUCCESS:
        return retval

    return api.tap_flow_create(args.name,
                               args.description,
                               args.port_id,
                               args.direction,
                               args.tap_service_id)


# Handler for 'tap-flow-delete' subcommand
def tap_flow_delete(args):
    api = taas_rest_api()

    retval = api.authenticate()
    if retval != SUCCESS:
        return retval

    return api.tap_flow_delete(args.id)


# Handler for 'tap-flow-list' subcommand
def tap_flow_list(args):
    api = taas_rest_api()

    retval = api.authenticate()
    if retval != SUCCESS:
        return retval

    return api.tap_flow_list(args.tap_service_id)


# Handler for 'tap-flow-show' subcommand
def tap_flow_show(args):
    api = taas_rest_api()

    retval = api.authenticate()
    if retval != SUCCESS:
        return retval

    return api.tap_flow_show(args.id)


def main():
    parser = argparse.ArgumentParser(
        description='Command-line interface \
                    to the OpenStack Tap-as-a-Service API')
    subparsers = parser.add_subparsers(title='subcommands')

    # Sub-parser for 'tap-service-create' subcommand
    parser_tap_service_create = subparsers.add_parser(
        'tap-service-create',
        help='Create a tap service for a given tenant')
    parser_tap_service_create.add_argument('--name',
                                           dest='name',
                                           required=False,
                                           default='')
    parser_tap_service_create.add_argument('--description',
                                           dest='description',
                                           required=False,
                                           default='')
    parser_tap_service_create.add_argument('--port-id',
                                           dest='port_id',
                                           required=True)
    parser_tap_service_create.add_argument('--network-id',
                                           dest='network_id',
                                           required=True)
    parser_tap_service_create.set_defaults(func=tap_service_create)

    # Sub-parser for 'tap-service-delete' subcommand
    parser_tap_service_delete = subparsers.add_parser(
        'tap-service-delete',
        help='Delete a given tap service')
    parser_tap_service_delete.add_argument('id')
    parser_tap_service_delete.set_defaults(func=tap_service_delete)

    # Sub-parser for 'tap-service-list' subcommand
    parser_tap_service_list = subparsers.add_parser(
        'tap-service-list',
        help='List tap services that belong to a given tenant')
    parser_tap_service_list.set_defaults(func=tap_service_list)

    # Sub-parser for 'tap-service-show' subcommand
    parser_tap_service_show = subparsers.add_parser(
        'tap-service-show',
        help='Show information of a given tap service')
    parser_tap_service_show.add_argument('id')
    parser_tap_service_show.set_defaults(func=tap_service_show)

    # Sub-parser for 'tap-flow-create' subcommand
    parser_tap_flow_create = subparsers.add_parser(
        'tap-flow-create',
        help='Create a tap flow for a given tap service')
    parser_tap_flow_create.add_argument('--name',
                                        dest='name',
                                        required=False,
                                        default='')
    parser_tap_flow_create.add_argument('--description',
                                        dest='description',
                                        required=False,
                                        default='')
    parser_tap_flow_create.add_argument('--port-id',
                                        dest='port_id',
                                        required=True)
    parser_tap_flow_create.add_argument('--direction',
                                        dest='direction',
                                        required=True)
    parser_tap_flow_create.add_argument('--tap-service-id',
                                        dest='tap_service_id',
                                        required=True)
    parser_tap_flow_create.set_defaults(func=tap_flow_create)

    # Sub-parser for 'tap-flow-delete' subcommand
    parser_tap_flow_delete = subparsers.add_parser(
        'tap-flow-delete',
        help='Delete a given tap flow')
    parser_tap_flow_delete.add_argument('id')
    parser_tap_flow_delete.set_defaults(func=tap_flow_delete)

    # Sub-parser for 'tap-flow-list' subcommand
    parser_tap_flow_list = subparsers.add_parser(
        'tap-flow-list',
        help='List tap flows that belong to given tenant')
    parser_tap_flow_list.add_argument('--tap-service-id',
                                      dest='tap_service_id',
                                      required=False,
                                      default=None)
    parser_tap_flow_list.set_defaults(func=tap_flow_list)

    # Sub-parser for 'tap-flow-show' subcommand
    parser_tap_flow_show = subparsers.add_parser(
        'tap-flow-show',
        help='Show information of a given tap flow')
    parser_tap_flow_show.add_argument('id')
    parser_tap_flow_show.set_defaults(func=tap_flow_show)

    args = parser.parse_args()

    return args.func(args)


if __name__ == '__main__':
    main()
