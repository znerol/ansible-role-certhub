import math
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


def _run_expect_retry(host, attempts, expected, command, *args, **kwds):
    __tracebackhide__ = True  # pylint: disable=unused-variable

    for i in range(0, attempts):
        out = host.run(command, *args, **kwds)
        if out.rc in expected:
            break
        else:
            backoff = math.pow(i, 2) / 4
            host.run("sleep %s", backoff)

    assert out.rc in expected, (
        'Unexpected exit code %s for %s' % (out.rc, out))

    return out


def test_certbot_issues_cert(host, link_nginx_config):
    host_vars = host.ansible.get_variables()
    hostname = host_vars["inventory_hostname"]
    cert_slug = hostname
    controller = host.get_host("ansible://{:s}?ansible_inventory={:s}".format(
        host_vars["molecule_certhub_controller"],
        os.environ["MOLECULE_INVENTORY_FILE"]
    ))

    # Install nginx config.
    link_nginx_config(host, cert_slug)

    # Run certbot once on controller.
    service_name = "certhub-certbot-run@{:s}.service".format(cert_slug)
    controller.run_expect([0], "systemctl start %s", service_name)

    # Retrieve pebble root certificate to the controller.
    ca_url = "https://pebble:14000/root"
    ca_path = "/tmp/pebble-root.crt"
    _run_expect_retry(controller, 5, [0], "curl --fail --output %s %s",
                      ca_path, ca_url)

    # Check certificate created by the controller and deployed to the server.
    server_url = "https://{:s}/".format(hostname)
    _run_expect_retry(controller, 5, [0], "curl --fail --cacert %s %s",
                      ca_path, server_url)

    # Ensure there are no failed units on the server.
    host_units = [
        'certhub-cert-export@{:s}'.format(cert_slug),
        'certhub-cert-reload@{:s}'.format(cert_slug),
        'certhub-cert-send@{:s}'.format(cert_slug),
        'nginx',
    ]
    for pattern in host_units:
        host.run_expect([1], "systemctl --quiet is-failed %s", pattern)

    # Ensure there are no failed units on the controller.
    controller_units = [
        'certhub-cert-expiry@{:s}'.format(cert_slug),
        'certhub-certbot-run@{:s}'.format(cert_slug),
        'certhub-repo-push',
    ]
    for pattern in controller_units:
        controller.run_expect([1], "systemctl --quiet is-failed %s", pattern)


def test_lego_issues_cert(host, link_nginx_config):
    host_vars = host.ansible.get_variables()
    hostname = "{:s}-lego-test.ci.certhub.io".format(
        host_vars["inventory_hostname"]
    )
    cert_slug = hostname
    controller = host.get_host("ansible://{:s}?ansible_inventory={:s}".format(
        host_vars["molecule_certhub_controller"],
        os.environ["MOLECULE_INVENTORY_FILE"]
    ))

    # Install nginx config.
    link_nginx_config(host, cert_slug)

    # Run lego once on controller.
    service_name = "certhub-lego-run@{:s}.service".format(cert_slug)
    controller.run_expect([0], "systemctl start %s", service_name)

    # Retrieve pebble root certificate to the controller.
    ca_url = "https://pebble:14000/root"
    ca_path = "/tmp/pebble-root.crt"
    _run_expect_retry(controller, 5, [0], "curl --fail --output %s %s",
                      ca_path, ca_url)

    # Check certificate created by the controller and deployed to the server.
    server_url = "https://{:s}/".format(hostname)
    _run_expect_retry(controller, 5, [0], "curl --fail --cacert %s %s",
                      ca_path, server_url)

    # Ensure there are no failed units on the server.
    host_units = [
        'certhub-cert-export@{:s}'.format(cert_slug),
        'certhub-cert-reload@{:s}'.format(cert_slug),
        'certhub-cert-send@{:s}'.format(cert_slug),
        'nginx',
    ]
    for pattern in host_units:
        host.run_expect([1], "systemctl --quiet is-failed %s", pattern)

    # Ensure there are no failed units on the controller.
    controller_units = [
        'certhub-cert-expiry@{:s}'.format(cert_slug),
        'certhub-lego-run@{:s}'.format(cert_slug),
        'certhub-repo-push',
    ]
    for pattern in controller_units:
        controller.run_expect([1], "systemctl --quiet is-failed %s", pattern)
