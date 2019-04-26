import os

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ["MOLECULE_INVENTORY_FILE"]).get_hosts("server")


def test_certbot_issues_cert(host):
    host_vars = host.ansible.get_variables()
    cert_slug = host_vars["inventory_hostname"]
    controller = host.get_host("ansible://{:s}?ansible_inventory={:s}".format(
        host_vars["molecule_certhub_controller"],
        os.environ["MOLECULE_INVENTORY_FILE"]
    ))

    # Ensure there are no failed units on server and controller
    host.run_expect([0], "systemctl --quiet is-system-running")
    controller.run_expect([0], "systemctl --quiet is-system-running")

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
