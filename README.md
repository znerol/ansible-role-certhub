Ansible Role: Certhub
=====================

[![Build Status](https://travis-ci.org/znerol/ansible-role-certhub.svg?branch=master)](https://travis-ci.org/znerol/ansible-role-certhub)

Installs [certhub](https://certhub.io/) and `git-gau` on linux servers
controlled by `systemd`.

Requirements
------------

- Git
- OpenSSL
- Rsync if target machine operates as an SSL/TLS server.
- Either `certbot`, `dehydrated` or `lego` when target machine operates as the
  controller.

Role Variables
--------------

This role contains multiple `task` files. The `main` task file only imports
some of them:

1. [certhub-system-setup.yml](#variables-for-certhub-system-setupyml): Creates
   the `certhub` user and group, the configuration directory and prepares the
   home directory.
1. [certhub-software-setup.yml](#variables-for-certhub-software-setupyml):
   Retrieves and installs `certhub` and `git-gau`.
1. [certhub-git-setup.yml](#variables-for-certhub-git-setupyml): Configures
   git `user.name` and `user.email`.
1. [certhub-repo-setup.yml](#variables-for-certhub-repo-setupyml): Initializes
   the local `certs` git repository.

The following task files contain additional configuration steps:

1. [certbot-noroot-config.yml](#variables-for-certbot-noroot-configyml):
   Simplifies running `certbot` as the unprivileged `certhub` user by placing
   an appropriate `cli.ini` file.

The following task files contain steps used to setup acquisition and deployment
of certificates.

1. [Environment for systemd units](#environment-for-systemd-units): Variables
   containing paths to environment files respected by all certhub systemd
   units.
1. [repo-push-units.yml](#variables-for-repo-push-unitsyml): Sets up `systemd`
   units responsible for pushing the certs repository to SSL/TLS servers
   whenever it changes.
1. [certbot-run-units.yml](#variables-for-certbot-run-unitsyml): Sets up `systemd`
   units responsible for issuing/renewing a certificate and also monitor it for
   expiry (controller).
1. [lego-run-units.yml](#variables-for-lego-run-unitsyml): Sets up `systemd`
   units responsible for issuing/renewing a certificate and also monitor it for
   expiry (controller).
1. [cert-export-units.yml](#variables-for-cert-export-unitsyml): Sets up
   `systemd` units responsible for deploying a certificate on an SSL/TLS server
   and reload affected services.

### Variables for certhub-system-setup.yml

Available variables are listed below, along with default values (see `defaults/main.yml`):

```
certhub_user_group: certhub
certhub_user_name: certhub
certhub_user_shell: /usr/bin/git-shell

certhub_home_dir_path: /var/lib/certhub
certhub_home_dir_mode: 0755

certhub_config_dir_path: /etc/certhub
certhub_config_dir_owner: root
certhub_config_dir_group: root
certhub_config_dir_mode: 0755

certhub_status_dir_path: "{{ certhub_home_dir_path }}/status"
certhub_status_dir_owner: "{{ certhub_user_name }}"
certhub_status_dir_group: "{{ certhub_user_group }}"
certhub_status_dir_mode: 0755

certhub_certs_dir_path: "{{ certhub_home_dir_path }}/certs"
certhub_certs_dir_owner: "{{ certhub_user_name }}"
certhub_certs_dir_group: "{{ certhub_user_group }}"
certhub_certs_dir_mode: 0755

certhub_private_dir_path: "{{ certhub_home_dir_path }}/private"
certhub_private_dir_owner: "{{ certhub_user_name }}"
certhub_private_dir_group: "{{ certhub_user_group }}"
certhub_private_dir_mode: 0700
```

### Variables for certhub-software-setup.yml

Available variables are listed below, along with default values (see `defaults/main.yml`):

```
certhub_certhub_version: v1.0.0-beta6
certhub_certhub_checksum: "{{ certhub_certhub_releases[certhub_certhub_version]['checksum'] }}"
certhub_certhub_url: "{{ certhub_certhub_releases[certhub_certhub_version]['url'] }}"
certhub_certhub_prefix: /usr/local
certhub_certhub_archive_path: "{{ certhub_private_dir_path }}/certhub-dist-{{ certhub_certhub_version }}.tar.gz"

certhub_gitgau_version: v1.1.0
certhub_gitgau_checksum: "{{ certhub_gitgau_releases[certhub_gitgau_version]['checksum'] }}"
certhub_gitgau_url: "{{ certhub_gitgau_releases[certhub_gitgau_version]['url'] }}"
certhub_gitgau_prefix: /usr/local
certhub_gitgau_archive_path: "{{ certhub_private_dir_path }}/git-gau-dist-{{ certhub_gitgau_version }}.tar.gz"
```

The variables `certhub_certhub_releases` and `certhub_gitgau_releases` contain
urls and checksum of all public releases. Set `certhub_certhub_version` and
`certhub_gitgau_version` to pin a specific version.

### Variables for certhub-git-setup.yml

Available variables are listed below, along with default values (see `defaults/main.yml`):

```
certhub_git_user_name: "{{ certhub_user_name }}"
certhub_git_user_email: "{{ certhub_user_name }}@{{ ansible_fqdn }}"
```

### Variables for certhub-repo-setup.yml

Available variables are listed below, along with default values (see `defaults/main.yml`):

```
certhub_repo_path: "{{ certhub_home_dir_path}}/certs.git"
certhub_repo_init_message: Init
```

### Variables for certbot-noroot-config.yml

Available variables are listed below, along with default values (see `defaults/main.yml`):

```
certhub_certbot_cli_ini_path: "{{ certhub_home_dir_path }}/.config/letsencrypt/cli.ini"
certhub_certbot_cli_ini_content: ""
certhub_certbot_work_dir: "{{ certhub_private_dir_path }}/certbot/work"
certhub_certbot_logs_dir: "{{ certhub_private_dir_path }}/certbot/logs"
certhub_certbot_config_dir: "{{ certhub_private_dir_path }}/certbot/config"
```

The `certhub_certbot_cli_ini_content` variable can be used to supply additional
certbot configuration. E.g., `staging=true` in order to select the staging
environment during evaluation.

### Environment for systemd units

Available variables are listed below, along with default values (see `defaults/main.yml`):

```
# Optional environment file shared by all instances and certhub services.
certhub_env_path: "{{ certhub_config_dir_path }}/env"
# Optional per-instance environment file shared by all certhub services.
certhub_cert_env_path: "{{ certhub_config_dir_path}}/{{ certhub_cert_slug }}.env"
# Optional per-service environment file shared by all certhub service instances.
certhub_unit_env_path: "{{ certhub_config_dir_path}}/{{ certhub_unit_prefix }}.env"
# Optional per-instance and per-service environment file.
certhub_cert_unit_env_path: "{{ certhub_config_dir_path}}/{{ certhub_cert_slug }}.{{ certhub_unit_prefix }}.env"

certhub_env_owner: root
certhub_env_group: "{{ certhub_user_group }}"
certhub_env_mode: 0640
```

Use this variables in custom `copy` or `template` tasks in order to populate
`env` files with configuration for certhub services. Note: There is no default
value for `certhub_unit_prefix`. This variable needs to be set to one of the
certhub service unit prefixes. The following values are currently valid:

- certhub-cert-expiry
- certhub-cert-export
- certhub-cert-reload
- certhub-certbot-run
- certhub-dehydrated-run
- certhub-lego-run

### Variables for repo-push-units.yml

Available variables are listed below, along with default values (see `defaults/main.yml`):

```
certhub_repo_push_user: "{{ certhub_user_name }}"
certhub_repo_push_host: "{{ inventory_hostname }}"
certhub_repo_push_path: "{{ certhub_repo_path }}"
certhub_repo_push_remote: "{{ '{:s}@{:s}:{:s}'.format(certhub_repo_push_user, certhub_repo_push_host, certhub_repo_push_path) }}"
certhub_repo_push_path_unit: "{{ lookup('pipe', 'systemd-escape --template=certhub-repo-push@.path ' + certhub_repo_push_remote | quote) }}"
```

Specify `certhub_repo_push_remote` in order to override the remote completely.

### Variables for certbot-run-units.yml

Available variables are listed below, along with default values (see `defaults/main.yml`):

```
certhub_cert_slug: "{{ inventory_hostname }}"

certhub_cert_expiry_path_unit: "certhub-cert-expiry@{{ certhub_cert_slug }}.path"
certhub_cert_expiry_timer_unit: "certhub-cert-expiry@{{ certhub_cert_slug }}.timer"
certhub_certbot_run_path_unit: "certhub-certbot-run@{{ certhub_cert_slug }}.path"
```

Set `certhub_cert_slug` in order to specify the certificate instance.

### Variables for lego-run-units.yml

Available variables are listed below, along with default values (see `defaults/main.yml`):

```
certhub_cert_slug: "{{ inventory_hostname }}"

certhub_cert_expiry_path_unit: "certhub-cert-expiry@{{ certhub_cert_slug }}.path"
certhub_cert_expiry_timer_unit: "certhub-cert-expiry@{{ certhub_cert_slug }}.timer"
certhub_lego_run_path_unit: "certhub-lego-run@{{ certhub_cert_slug }}.path"
```

Set `certhub_cert_slug` in order to specify the certificate instance.

### Variables for cert-export-units.yml

Available variables are listed below, along with default values (see `defaults/main.yml`):

```
certhub_cert_slug: "{{ inventory_hostname }}"

certhub_cert_services: []

certhub_cert_export_path_unit: "certhub-cert-export@{{ certhub_cert_slug }}.path"
certhub_cert_reload_config_path: "{{ certhub_config_dir_path }}/{{ certhub_cert_slug }}.services-reload.txt"
certhub_cert_reload_path_unit: "certhub-cert-reload@{{ certhub_cert_slug }}.path"
```

Set `certhub_cert_slug` in order to specify the certificate instance. A list of
systemd service units which should be reloaded whenever the certificate
instance changes can be specified using `certhub_cert_services`.

Dependencies
------------

None.

Example Playbook
----------------


    - name: Certhub controller setup
      hosts: certhub-controller
      tasks:
        - name: Certhub dependencies present
          loop:
            - certbot
            - git
            - lexicon
            - openssl
          package:
            name: "{{ item }}"
            state: present

        - name: Certhub present
          import_role:
            name: znerol.certhub

    - name: TLS Server Setup
      hosts: tls-server
      tasks:
        - name: Certhub dependencies present
          loop:
            - git
            - openssl
          package:
            name: "{{ item }}"
            state: present

        - name: Certhub present
          import_role:
            name: znerol.certhub

        - name: Repo push units setup
          delegate_to: name-of-certhub-controller
          import_role:
            name: ansible-role-certhub
            tasks_from: repo-push-units.yml

    - name: TLS Certificate Configuration
      hosts: tls-server
      tasks:
        - vars:
            certhub_cert_services:
              - nginx
          import_role:
            name: ansible-role-certhub
            tasks_from: cert-export-units.yml

        - name: Certbot run units setup
          delegate_to: name-of-certhub-controller
          import_role:
            name: ansible-role-certhub
            tasks_from: certbot-run-units.yml

        - name: Certbot CSR installed
          delegate_to: name-of-certhub-controller
          become: yes
          become_user: root
          copy:
            dest: "{{ certhub_cert_csr_path }}"
            owner: root
            group: root
            mode: 0644
            content: |
              -----BEGIN CERTIFICATE REQUEST-----
              MIH6MIGhAgEAMBYxFDASBgNVBAMMC2V4YW1wbGUuY29tMFkwEwYHKoZIzj0CAQYI
              KoZIzj0DAQcDQgAE1XubF1Uc4T595zSzikHAJTkXRlV5Fn5MhVUhr/18bm++5z2j
              759NpRh/gbEieCT4sKZ0fUcPWBrLp5zf0CFaYqApMCcGCSqGSIb3DQEJDjEaMBgw
              FgYDVR0RBA8wDYILZXhhbXBsZS5jb20wCgYIKoZIzj0EAwIDSAAwRQIhANwIuwCc
              45XooSB4bleXURLDGuChxcdFYYSHnnQjArizAiBYefMa83Kk1AJUIArnJ0Rk162D
              Fw3tPbiEVAmmvl0/5A==
              -----END CERTIFICATE REQUEST-----

        - name: Certbot config installed
          delegate_to: name-of-certhub-controller
          become: yes
          become_user: root
          copy:
            dest: "{{ certhub_certbot_config_path }}"
            owner: root
            group: root
            mode: 0644
            content: |
              staging=true
              agree-tos=true
              register-unsafely-without-email=true
              manual-public-ip-logging-ok=true
              preferred-challenges=dns
              manual=true
              manual-auth-hook=/usr/local/lib/certhub/certbot-hooks/hook-lexicon-auth
              manual-cleanup-hook=/usr/local/lib/certhub/certbot-hooks/hook-lexicon-cleanup

        - name: Certbot unit environment configured
          delegate_to: name-of-certhub-controller
          become: yes
          become_user: root
          vars:
            certhub_unit_prefix: certhub-certbot-run
          copy:
            dest: "{{ certhub_cert_unit_env_path }}"
            owner: "{{ certhub_env_owner }}"
            group: "{{ certhub_env_group }}"
            mode: "{{ certhub_env_mode }}"
            content: |
              CERTHUB_LEXICON_PROVIDER=cloudflare
              LEXICON_CLOUDFLARE_USERNAME="myusername@example.com"
              LEXICON_CLOUDFLARE_TOKEN="cloudflare-api-token"

License
-------

BSD
