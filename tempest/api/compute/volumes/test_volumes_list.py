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

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import test

CONF = config.CONF


class VolumesTestJSON(base.BaseV2ComputeTest):

    """
    This test creates a number of 1G volumes. To run successfully,
    ensure that the backing file for the volume group that Nova uses
    has space for at least 3 1G volumes!
    If you are running a Devstack environment, ensure that the
    VOLUME_BACKING_FILE_SIZE is atleast 4G in your localrc
    """

    @classmethod
    def resource_setup(cls):
        super(VolumesTestJSON, cls).resource_setup()
        cls.client = cls.volumes_extensions_client
        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        # Create 3 Volumes
        cls.volume_list = []
        cls.volume_id_list = []
        for i in range(3):
            v_name = data_utils.rand_name('volume-%s' % cls._interface)
            metadata = {'Type': 'work'}
            try:
                volume = cls.client.create_volume(size=1,
                                                  display_name=v_name,
                                                  metadata=metadata)
                cls.client.wait_for_volume_status(volume['id'], 'available')
                volume = cls.client.get_volume(volume['id'])
                cls.volume_list.append(volume)
                cls.volume_id_list.append(volume['id'])
            except Exception:
                if cls.volume_list:
                    # We could not create all the volumes, though we were able
                    # to create *some* of the volumes. This is typically
                    # because the backing file size of the volume group is
                    # too small. So, here, we clean up whatever we did manage
                    # to create and raise a SkipTest
                    for volume in cls.volume_list:
                        cls.delete_volume(volume['id'])
                    msg = ("Failed to create ALL necessary volumes to run "
                           "test. This typically means that the backing file "
                           "size of the nova-volumes group is too small to "
                           "create the 3 volumes needed by this test case")
                    raise cls.skipException(msg)
                raise

    @classmethod
    def resource_cleanup(cls):
        # Delete the created Volumes
        for volume in cls.volume_list:
            cls.delete_volume(volume['id'])
        super(VolumesTestJSON, cls).resource_cleanup()

    @test.attr(type='gate')
    def test_volume_list(self):
        # Should return the list of Volumes
        # Fetch all Volumes
        fetched_list = self.client.list_volumes()
        # Now check if all the Volumes created in setup are in fetched list
        missing_volumes = [
            v for v in self.volume_list if v not in fetched_list
        ]

        self.assertFalse(missing_volumes,
                         "Failed to find volume %s in fetched list" %
                         ', '.join(m_vol['displayName']
                                   for m_vol in missing_volumes))

    @test.attr(type='gate')
    def test_volume_list_with_details(self):
        # Should return the list of Volumes with details
        # Fetch all Volumes
        fetched_list = self.client.list_volumes_with_detail()
        # Now check if all the Volumes created in setup are in fetched list
        missing_volumes = [
            v for v in self.volume_list if v not in fetched_list
        ]

        self.assertFalse(missing_volumes,
                         "Failed to find volume %s in fetched list" %
                         ', '.join(m_vol['displayName']
                                   for m_vol in missing_volumes))

    @test.attr(type='gate')
    def test_volume_list_param_limit(self):
        # Return the list of volumes based on limit set
        params = {'limit': 2}
        fetched_vol_list = self.client.list_volumes(params=params)

        self.assertEqual(len(fetched_vol_list), params['limit'],
                         "Failed to list volumes by limit set")

    @test.attr(type='gate')
    def test_volume_list_with_detail_param_limit(self):
        # Return the list of volumes with details based on limit set.
        params = {'limit': 2}
        fetched_vol_list = self.client.list_volumes_with_detail(params=params)

        self.assertEqual(len(fetched_vol_list), params['limit'],
                         "Failed to list volume details by limit set")

    @test.attr(type='gate')
    def test_volume_list_param_offset_and_limit(self):
        # Return the list of volumes based on offset and limit set.
        # get all volumes list
        all_vol_list = self.client.list_volumes()
        params = {'offset': 1, 'limit': 1}
        fetched_vol_list = self.client.list_volumes(params=params)

        # Validating length of the fetched volumes
        self.assertEqual(len(fetched_vol_list), params['limit'],
                         "Failed to list volumes by offset and limit")
        # Validating offset of fetched volume
        for index, volume in enumerate(fetched_vol_list):
            self.assertEqual(volume['id'],
                             all_vol_list[index + params['offset']]['id'],
                             "Failed to list volumes by offset and limit")

    @test.attr(type='gate')
    def test_volume_list_with_detail_param_offset_and_limit(self):
        # Return the list of volumes details based on offset and limit set.
        # get all volumes list
        all_vol_list = self.client.list_volumes_with_detail()
        params = {'offset': 1, 'limit': 1}
        fetched_vol_list = self.client.list_volumes_with_detail(params=params)

        # Validating length of the fetched volumes
        self.assertEqual(len(fetched_vol_list), params['limit'],
                         "Failed to list volume details by offset and limit")
        # Validating offset of fetched volume
        for index, volume in enumerate(fetched_vol_list):
            self.assertEqual(volume['id'],
                             all_vol_list[index + params['offset']]['id'],
                             "Failed to list volume details by "
                             "offset and limit")
