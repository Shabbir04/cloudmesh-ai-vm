"""Real-cloud check: ``cmx vm list`` shows the floating IP OpenStack reports.

The expected IPs are fetched from the OpenStack network service (floating IP
-> port -> server), which is independent of the ``server.addresses`` data that
``OpenstackManager.list()`` reads. No IP address is written in this test.

Read-only: it lists servers and floating IPs and creates nothing. Opt-in:

    CLOUDMESH_RUN_OPENSTACK_LIST_TESTS=1 OS_CLOUD=jetstream \
        pytest tests/integration/test_openstack_list_ip.py
"""

import os

import pytest

from cloudmesh.ai.vm.providers import get_provider

OPENSTACK_CLOUDS = ("jetstream", "openstack")


def floating_ips_from_network_service(conn):
    """Map server id to its floating IP using the network service."""
    result = {}
    for fip in conn.network.ips():
        if fip.port_id:
            port = conn.network.get_port(fip.port_id)
            result[port.device_id] = fip.floating_ip_address
    return result


def test_list_ip_matches_network_service():
    if os.environ.get("CLOUDMESH_RUN_OPENSTACK_LIST_TESTS") != "1":
        pytest.skip(
            "Set CLOUDMESH_RUN_OPENSTACK_LIST_TESTS=1 to enable the "
            "read-only OpenStack list check."
        )

    cloud = os.environ.get("OS_CLOUD")
    if cloud not in OPENSTACK_CLOUDS:
        pytest.skip(f"Set OS_CLOUD to one of {', '.join(OPENSTACK_CLOUDS)}.")

    provider = get_provider(cloud)
    vms = provider.list()
    if not vms:
        pytest.skip(f"No servers on {cloud} to compare.")

    expected = floating_ips_from_network_service(provider._get_sdk_conn())

    for vm in vms:
        assert vm["ip"] == expected.get(vm["id"], "No IP"), vm["name"]
