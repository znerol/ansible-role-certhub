Ansible Role: Certhub
=====================

Installs `git-gau` and `certhub` on linux servers.

Requirements
------------

- Git
- Either `certbot`, `dehydrated` or `lego` when target machine is supposed to
  operate as certhub controller.

Role Variables
--------------



Dependencies
------------

None.

Example Playbook
----------------


    - hosts: certhub-controllers
      tasks:
        - name: Certbot/Lexicon present
          loop:
            - certbot
            - lexicon
          package:
            name: "{{ item }}"
            state: present

        - name: Certhub present
          import_role:
            name: certhub.certhub

License
-------

BSD
