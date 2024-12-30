# Homelab

I will try to put all homelab config files, ansible playbooks, docker-compose files in this repo. Consistency and organization ain't in my genes, but let's try. 

### Ansible

For the initial setup of devices, run the `playbooks/initial-setup.yml` playbook. This playbook expects an initial user with ssh and sudo access to be present on the remote host. Run it with:
```bash
ansible-playbook ./playbooks/initial-setup.yml --ask-pass --ask-become-pass
```


