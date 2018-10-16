# test_radl - Test for module ``radl``.
# Copyright (C) 2014 - GRyCAP - Universitat Politecnica de Valencia
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import unittest
import logging
from mock import patch, MagicMock
from collections import namedtuple
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from urlparse import urlparse

sys.path.append("..")
sys.path.append(".")

from ec3 import CLI, CmdLaunch, CmdList 


class TestEC3(unittest.TestCase):

    def __init__(self, *args):
        unittest.TestCase.__init__(self, *args)

    def get_response(self, method, url, verify, headers, data=None):
        resp = MagicMock()
        resp.status_code = 400
        parts = urlparse(url)
        url = parts[2]
        params = parts[4]

        if method == "GET":
            if url == "/infrastructures/infid" or url == "/infrastructures/newinfid":
                resp.status_code = 200
                resp.json.return_value = {"uri-list": [{ "uri": "http://server.com/infid/vms/0"},
                                                       { "uri": "http://server.com/infid/vms/1"}]}
            elif url == "/infrastructures/infid/state":
                resp.status_code = 200
                resp.json.return_value = {"state": {"state": "configured",
                                                    "vm_states": {"0": "configured",
                                                                  "1": "configured"}}}
            elif url == "/infrastructures/infid/vms/0":
                resp.status_code = 200
                resp.text = "network public (outbound='yes')\n"
                resp.text += "system front (net_interface.0.connection = 'public' and net_interface.0.ip = '8.8.8.8')"
            elif url == "/infrastructures/infid/data":
                resp.status_code = 200
                resp.json.return_value = {"data": "data"}
        elif method == "POST":
            if url == "/infrastructures":
                resp.status_code = 200
                resp.text = 'http://server.com/infid'
        elif method == "PUT":
            if url == "/infrastructures":
                resp.status_code = 200
                resp.text = 'http://server.com/newinfid'
        elif method == "DELETE":
            if url == "/infrastructures/infid":
                resp.status_code = 200

        return resp

    def test_list(self):
        Options = namedtuple('Options', ['json'])
        options = Options(json=False)
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        CmdList.run(options)
        res = sys.stdout.getvalue()
        sys.stdout = old_stdout
        self.assertEquals(res, " name  state  IP  nodes \n------------------------\n")

    @patch('ec3.ClusterStore')
    @patch('ec3.CLI.display')
    @patch('requests.request')
    def test_launch(self, requests, display, cluster_store):
        Options = namedtuple('Options', ['quiet'])
        cli_options = Options(quiet=False)
        CLI.logger = logging.getLogger('ec3')
        CLI.options = cli_options
        cluster_store.list.return_value = ["name"]
        Options = namedtuple('Options', ['not_store', 'clustername', 'auth_file', 'restapi', 'dry_run', 'templates',
                                         'add', 'golden_image', 'print_radl', 'json', 'yes', 'destroy'])
        auth_file = [MagicMock()]
        auth_file[0].readlines.return_value = ["type = InfrastructureManager; username = user; password = pass"]
        options = Options(not_store=False, clustername="name", auth_file=auth_file, restapi=['http://server.com:8800'],
                          dry_run=True, templates=['ubuntu-ec2','kubernetes'], add=False, golden_image=False,
                          print_radl=True, json=False, yes=True, destroy=False)
        with self.assertRaises(SystemExit) as ex1:
            CmdLaunch.run(options)
        self.assertEquals("1" ,str(ex1.exception))

        cluster_store.list.return_value = []
        with self.assertRaises(SystemExit) as ex2:
            CmdLaunch.run(options)
        self.assertEquals("0" ,str(ex2.exception))
        
        radl = """system front (
  net_interface.1.dns_name = 'kubeserverpublic' and
  disk.0.os.credentials.username = 'ubuntu' and
  disk.0.applications contains (
    name = 'ansible.modules.grycap.kubernetes'
  ) and
  disk.0.applications contains (
    name = 'ansible.modules.grycap.clues'
  ) and
  disk.0.applications contains (
    name = 'ansible.modules.grycap.im'
  ) and
  cpu.count >= 2 and
  net_interface.1.connection = 'public' and
  queue_system = 'kubernetes' and
  net_interface.0.dns_name = 'kubeserver' and
  instance_type = 't1.micro' and
  ec3_templates = 'im,clues2,kubernetes' and
  disk.0.image.url = 'aws://us-east-1/ami-30519058' and
  auth = 'username = user ; password = pass ; type = InfrastructureManager
' and
  net_interface.0.connection = 'private' and
  memory.size >= 2048m and
  disk.0.os.name = 'linux' and
  ec3_templates_cmd = 'ubuntu-ec2 kubernetes'
)

system wn (
  disk.0.image.url = 'aws://us-east-1/ami-30519058' and
  instance_type = 't1.micro' and
  ec3_max_instances = 10 and
  memory.size >= 2048m and
  net_interface.0.connection = 'private' and
  disk.0.os.name = 'linux' and
  disk.0.os.credentials.username = 'ubuntu'
)

network public (
  outbound = 'yes' and
  outports = '6443/tcp,8800/tcp'
)

network private (

)

configure front (
@begin
- tasks:
  - iptables:
      action: insert
      chain: INPUT
      destination_port: '{{item|dirname}}'
      jump: ACCEPT
      protocol: '{{item|basename}}'
    when: ansible_os_family == "RedHat"
    with_items: '{{OUTPORTS.split('','')}}'
  - firewalld:
      immediate: true
      permanent: true
      port: '{{item}}'
      state: enabled
    ignore_errors: true
    when: ansible_os_family == "RedHat"
    with_items: '{{OUTPORTS.split('','')}}'
  vars:
    OUTPORTS: 6443/tcp,8800/tcp
- roles:
  - kube_api_server: '{{ IM_NODE_PRIVATE_IP }}'
    kube_apiserver_options:
    - option: --insecure-port
      value: '8080'
    kube_server: kubeserver
    role: grycap.kubernetes
- roles:
  - role: grycap.im
- roles:
  - auth: '{{AUTH}}'
    clues_queue_system: '{{QUEUE_SYSTEM}}'
    max_number_of_nodes: '{{ NNODES }}'
    role: grycap.clues
    vnode_prefix: wn
  vars:
    AUTH: 'username = user ; password = pass ; type = InfrastructureManager

      '
    NNODES: '{{ SYSTEMS | selectattr("ec3_max_instances_max", "defined") | sum(attribute="ec3_max_instances_max")
      }}'
    QUEUE_SYSTEM: kubernetes
    SYSTEMS:
    - auth: 'username = user ; password = pass ; type = InfrastructureManager

        '
      class: system
      cpu.count_max: inf
      cpu.count_min: 2
      disk.0.applications:
      - name: ansible.modules.grycap.kubernetes
      - name: ansible.modules.grycap.clues
      - name: ansible.modules.grycap.im
      disk.0.image.url: aws://us-east-1/ami-30519058
      disk.0.os.credentials.username: ubuntu
      disk.0.os.name: linux
      ec3_templates:
      - im
      - clues2
      - kubernetes
      ec3_templates_cmd: ubuntu-ec2 kubernetes
      id: front
      instance_type: t1.micro
      memory.size_max: inf
      memory.size_min: 2048
      net_interface.0.connection:
        class: network
        id: private
        reference: true
      net_interface.0.dns_name: kubeserver
      net_interface.1.connection:
        class: network
        id: public
        reference: true
      net_interface.1.dns_name: kubeserverpublic
      queue_system: kubernetes
    - class: network
      id: public
      outbound: 'yes'
      outports:
      - 6443/tcp
      - 8800/tcp
    - class: network
      id: private
    - class: system
      disk.0.image.url: aws://us-east-1/ami-30519058
      disk.0.os.credentials.username: ubuntu
      disk.0.os.name: linux
      ec3_max_instances_max: 10
      ec3_max_instances_min: 10
      id: wn
      instance_type: t1.micro
      memory.size_max: inf
      memory.size_min: 2048
      net_interface.0.connection:
        class: network
        id: private
        reference: true

@end
)

configure wn (
@begin
- tasks:
  - iptables:
      action: insert
      chain: INPUT
      destination_port: '{{item|dirname}}'
      jump: ACCEPT
      protocol: '{{item|basename}}'
    when: ansible_os_family == "RedHat"
    with_items: '{{OUTPORTS.split('','')}}'
  - firewalld:
      immediate: true
      permanent: true
      port: '{{item}}'
      state: enabled
    ignore_errors: true
    when: ansible_os_family == "RedHat"
    with_items: '{{OUTPORTS.split('','')}}'
  vars:
    OUTPORTS: 6443/tcp,8800/tcp
- roles:
  - kube_server: kubeserver
    kube_type_of_node: wn
    role: grycap.kubernetes

@end
)

deploy front 1
"""
        self.assertEquals(display.call_args_list[1][0][0], radl)

        requests.side_effect = self.get_response
        options = Options(not_store=False, clustername="name", auth_file=auth_file, restapi=['http://server.com:8800'],
                          dry_run=False, templates=['ubuntu-ec2','kubernetes'], add=False, golden_image=False,
                          print_radl=False, json=False, yes=True, destroy=False)

        with self.assertRaises(SystemExit) as ex2:
            CmdLaunch.run(options)
        self.assertEquals("0" ,str(ex2.exception))

        self.assertEquals(display.call_args_list[4][0][0], "Infrastructure successfully created with ID: infid")
        self.assertEquals(display.call_args_list[5][0][0], "Front-end configured with IP 8.8.8.8")
        self.assertEquals(display.call_args_list[6][0][0], "Transferring infrastructure")
        self.assertEquals(display.call_args_list[7][0][0], "Front-end ready!")


if __name__ == "__main__":
    unittest.main()
