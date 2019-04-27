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

1. [repo-push-units.yml](#variables-for-repo-push-unitsyml): Sets up `systemd`
   units responsible for pushing the certs repository to SSL/TLS servers
   whenever it changes.
1. [certbot-run-units.yml](#variables-for-certbot-run-unitsyml): Sets up `systemd`
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
certhub_certhub_version: v1.0.0-beta5
certhub_certhub_checksum: >
  sha256:a3a148759f7b8d4474a4a5bf3e9f33edd94322d9dcfc9d0c0dad880f7a14fca9
certhub_certhub_prefix: /usr/local

certhub_gitgau_version: v1.1.0
certhub_gitgau_checksum: >
  sha256:a5f02e4989706948f6cc903883e39a25c8e6d6efd4a72dfc34e3e34013c2082a
certhub_gitgau_prefix: /usr/local

certhub_certhub_url: "https://github.com/certhub/certhub/releases/download/{{ certhub_certhub_version }}/certhub-dist.tar.gz"
certhub_certhub_archive_path: "{{ certhub_private_dir_path }}/certhub-dist-{{ certhub_certhub_version }}.tar.gz"
certhub_gitgau_url: "https://github.com/znerol/git-gau/releases/download/{{ certhub_gitgau_version }}/git-gau-dist.tar.gz"
certhub_gitgau_archive_path: "{{ certhub_private_dir_path }}/git-gau-dist-{{ certhub_gitgau_version }}.tar.gz"
```

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
```

### Variables for cert-export-units.yml

Available variables are listed below, along with default values (see `defaults/main.yml`):

```
certhub_cert_slug: "{{ inventory_hostname }}"
certhub_cert_services: []
```

Dependencies
------------

None.

Example Playbook
----------------


    - hosts: certhub-controllers
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

License
-------

BSD
