import os
import pytest

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ["MOLECULE_INVENTORY_FILE"]).get_hosts("server")


@pytest.fixture
def link_nginx_config():

    created_links = []

    def _link_nginx_config(host, cert_slug):
        nginx_config_path = "/etc/certhub/{:s}.nginx.conf".format(cert_slug)
        nginx_config_dest = "/etc/nginx/conf.d/{:s}.conf".format(cert_slug)
        host.run_expect([0], "ln -s %s %s", nginx_config_path,
                        nginx_config_dest)
        created_links.append((host, cert_slug))

    yield _link_nginx_config

    for host, cert_slug in created_links:
        nginx_config_dest = "/etc/nginx/conf.d/{:s}.conf".format(cert_slug)
        host.run_expect([0], "rm -f %s", nginx_config_dest)


def test_certbot_issues_cert(host, link_nginx_config):
    host_vars = host.ansible.get_variables()
    cert_slug = host_vars["inventory_hostname"]
    controller = host.get_host("ansible://{:s}?ansible_inventory={:s}".format(
        host_vars["molecule_certhub_controller"],
        os.environ["MOLECULE_INVENTORY_FILE"]
    ))

    # Install nginx config.
    link_nginx_config(host, cert_slug)

    # Run certbot once on controller.
    service_name = "certhub-certbot-run@{:s}.service".format(cert_slug)
    controller.run_expect([0], "systemctl start %s", service_name)

    # Ensure there are no failed units on server and controller
    host.run_expect([0], "systemctl --quiet is-system-running")
    controller.run_expect([0], "systemctl --quiet is-system-running")

    # Retrieve pebble root certificate to the controller.
    ca_url = "https://pebble:14000/root"
    ca_path = "/tmp/pebble-root.crt"
    controller.run_expect([0], "curl --output %s %s", ca_path, ca_url)

    # Check certificate created by the controller and deployed to the server.
    server_url = "https://{:s}/".format(host_vars["inventory_hostname"])
    controller.run_expect([0], "curl --cacert %s %s", ca_path, server_url)
