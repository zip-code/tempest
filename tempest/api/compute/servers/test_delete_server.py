# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import testtools

from tempest.api.compute import base
from tempest import config
from tempest import test

CONF = config.CONF


class DeleteServersTestJSON(base.BaseV2ComputeTest):

    # NOTE: Server creations of each test class should be under 10
    # for preventing "Quota exceeded for instances"

    @classmethod
    def resource_setup(cls):
        super(DeleteServersTestJSON, cls).resource_setup()
        cls.client = cls.servers_client

    @test.attr(type='gate')
    def test_delete_server_while_in_building_state(self):
        # Delete a server while it's VM state is Building
        server = self.create_test_server(wait_until='BUILD')
        self.client.delete_server(server['id'])
        self.client.wait_for_server_termination(server['id'])

    @test.attr(type='gate')
    def test_delete_active_server(self):
        # Delete a server while it's VM state is Active
        server = self.create_test_server(wait_until='ACTIVE')
        self.client.delete_server(server['id'])
        self.client.wait_for_server_termination(server['id'])

    @test.attr(type='gate')
    def test_delete_server_while_in_shutoff_state(self):
        # Delete a server while it's VM state is Shutoff
        server = self.create_test_server(wait_until='ACTIVE')
        resp, body = self.client.stop(server['id'])
        self.client.wait_for_server_status(server['id'], 'SHUTOFF')
        self.client.delete_server(server['id'])
        self.client.wait_for_server_termination(server['id'])

    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    @test.attr(type='gate')
    def test_delete_server_while_in_pause_state(self):
        # Delete a server while it's VM state is Pause
        server = self.create_test_server(wait_until='ACTIVE')
        resp, body = self.client.pause_server(server['id'])
        self.client.wait_for_server_status(server['id'], 'PAUSED')
        self.client.delete_server(server['id'])
        self.client.wait_for_server_termination(server['id'])

    @testtools.skipUnless(CONF.compute_feature_enabled.suspend,
                          'Suspend is not available.')
    @test.attr(type='gate')
    def test_delete_server_while_in_suspended_state(self):
        # Delete a server while it's VM state is Suspended
        server = self.create_test_server(wait_until='ACTIVE')
        self.client.suspend_server(server['id'])
        self.client.wait_for_server_status(server['id'], 'SUSPENDED')
        self.client.delete_server(server['id'])
        self.client.wait_for_server_termination(server['id'])

    @testtools.skipUnless(CONF.compute_feature_enabled.shelve,
                          'Shelve is not available.')
    @test.attr(type='gate')
    def test_delete_server_while_in_shelved_state(self):
        # Delete a server while it's VM state is Shelved
        server = self.create_test_server(wait_until='ACTIVE')
        resp, body = self.client.shelve_server(server['id'])
        self.assertEqual(202, resp.status)

        offload_time = CONF.compute.shelved_offload_time
        if offload_time >= 0:
            self.client.wait_for_server_status(server['id'],
                                               'SHELVED_OFFLOADED',
                                               extra_timeout=offload_time)
        else:
            self.client.wait_for_server_status(server['id'],
                                               'SHELVED')
        self.client.delete_server(server['id'])
        self.client.wait_for_server_termination(server['id'])

    @testtools.skipIf(not CONF.compute_feature_enabled.resize,
                      'Resize not available.')
    @test.attr(type='gate')
    def test_delete_server_while_in_verify_resize_state(self):
        # Delete a server while it's VM state is VERIFY_RESIZE
        server = self.create_test_server(wait_until='ACTIVE')
        resp, body = self.client.resize(server['id'], self.flavor_ref_alt)
        self.assertEqual(202, resp.status)
        self.client.wait_for_server_status(server['id'], 'VERIFY_RESIZE')
        self.client.delete_server(server['id'])
        self.client.wait_for_server_termination(server['id'])

    @test.services('volume')
    @test.attr(type='gate')
    def test_delete_server_while_in_attached_volume(self):
        # Delete a server while a volume is attached to it
        volumes_client = self.volumes_extensions_client
        device = '/dev/%s' % CONF.compute.volume_device_name
        server = self.create_test_server(wait_until='ACTIVE')

        volume = volumes_client.create_volume(1)
        self.addCleanup(volumes_client.delete_volume, volume['id'])
        volumes_client.wait_for_volume_status(volume['id'], 'available')
        self.client.attach_volume(server['id'],
                                  volume['id'],
                                  device=device)
        volumes_client.wait_for_volume_status(volume['id'], 'in-use')

        self.client.delete_server(server['id'])
        self.client.wait_for_server_termination(server['id'])
        volumes_client.wait_for_volume_status(volume['id'], 'available')


class DeleteServersAdminTestJSON(base.BaseV2ComputeAdminTest):
    # NOTE: Server creations of each test class should be under 10
    # for preventing "Quota exceeded for instances".

    @classmethod
    def resource_setup(cls):
        super(DeleteServersAdminTestJSON, cls).resource_setup()
        cls.non_admin_client = cls.servers_client
        cls.admin_client = cls.os_adm.servers_client

    @test.attr(type='gate')
    def test_delete_server_while_in_error_state(self):
        # Delete a server while it's VM state is error
        server = self.create_test_server(wait_until='ACTIVE')
        resp, body = self.admin_client.reset_state(server['id'], state='error')
        self.assertEqual(202, resp.status)
        # Verify server's state
        server = self.non_admin_client.get_server(server['id'])
        self.assertEqual(server['status'], 'ERROR')
        self.non_admin_client.delete_server(server['id'])
        self.servers_client.wait_for_server_termination(server['id'],
                                                        ignore_error=True)

    @test.attr(type='gate')
    def test_admin_delete_servers_of_others(self):
        # Administrator can delete servers of others
        server = self.create_test_server(wait_until='ACTIVE')
        self.admin_client.delete_server(server['id'])
        self.servers_client.wait_for_server_termination(server['id'])
