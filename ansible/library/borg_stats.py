#!/usr/bin/python

# Copyright: (c) 2025, Paolo Stet <info@pcstet.nl>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
from datetime import datetime
import subprocess
import json
__metaclass__ = type

DOCUMENTATION = r'''
---
module: borg_stats

short_description: This is my test module

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: This is my longer description explaining my test module.

options:
    pool_path:
        description: The path where all borg repos are stored
        required: true
        type: str
    clients:
        description: All clients for which stats should be retrieved
        required: true
        type: list

author:
    - Paolo Stet (info@pcstet.nl)
'''

# EXAMPLES = r'''
# # Pass in a message
# - name: Test with a message
#   my_namespace.my_collection.borg_stats:
#     name: hello world
#
# # pass in a message and have changed true
# - name: Test with a message and changed output
#   my_namespace.my_collection.borg_stats:
#     name: hello world
#     new: true
#
# # fail the module
# - name: Test failure of the module
#   my_namespace.my_collection.borg_stats:
#     name: fail me
# '''
#
# RETURN = r'''
# # These are examples of possible return values, and in general should use other names for return values.
# original_message:
#     description: The original name param that was passed in.
#     type: str
#     returned: always
#     sample: 'hello world'
# message:
#     description: The output message that the test module generates.
#     type: str
#     returned: always
#     sample: 'goodbye'
# '''

from ansible.module_utils.basic import AnsibleModule

def run_borg_command(cmd: list[str]) -> str:
    try:
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, _stderr = p.communicate()
        output = stdout.decode("utf-8").strip()
        return output
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command failed: {e.stderr.strip()}")

def human_readable_bytes(size: float) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        pool_path=dict(type='str', required=True),
        clients=dict(type='list', elements=str, required=True)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    pool_path: str = module.params['pool_path']
    clients: list[str] = module.params['clients']
    borg_stats = {'items': []}

    try:
        for client in clients:
            repo = f"{pool_path}/{client}/main"

            archive_list: list[str] = run_borg_command(["borg", "list", "--short", repo]).splitlines()
            num_archives = len(archive_list)
            last_archive = archive_list[-1]
            backup_datetime = datetime.fromisoformat(last_archive).strftime("%d %B %Y %H:%M")

            borg_info = json.loads(run_borg_command(["borg", "info", "--json", f"{repo}::{last_archive}"]))
            backup_duration = f"{round(borg_info['archives'][0]['duration'], 2)} s"
            backup_size_raw = borg_info['archives'][0]['stats']['deduplicated_size']
            backup_number_files = borg_info['archives'][0]['stats']['nfiles']
            backup_total_size_raw = borg_info['cache']['stats']['unique_csize']
            backup_total_size = human_readable_bytes(backup_total_size_raw)
            backup_size = human_readable_bytes(backup_size_raw)

            borg_stats['items'].append( {
                "client": client,
                "datetime": backup_datetime,
                "number_archives": num_archives,
                "duration": backup_duration,
                "size_raw": backup_size_raw,
                "total_size_raw": backup_total_size_raw,
                "number_files": backup_number_files,
                "size": backup_size,
                "total_size": backup_total_size,
            })

    except Exception as e:
        module.fail_json(msg=str(e))

    all_repo_backup_size_raw = 0
    all_repo_backup_total_size_raw = 0
    all_repo_backup_number_files = 0
    all_repo_backup_number_archives = 0

    for item in borg_stats['items']:
        all_repo_backup_size_raw += item['size_raw']
        all_repo_backup_total_size_raw += item['total_size_raw']
        all_repo_backup_number_files += item['number_files']
        all_repo_backup_number_archives += item['number_archives']

    borg_stats['totals'] = {
        "size_raw": all_repo_backup_size_raw,
        "total_size_raw": all_repo_backup_total_size_raw,
        "number_files": all_repo_backup_number_files,
        "number_archives": all_repo_backup_number_archives,
        "size": human_readable_bytes(all_repo_backup_size_raw),
        "total_size": human_readable_bytes(all_repo_backup_total_size_raw),
    }


    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(changed=False, stats=borg_stats)


def main():
    run_module()


if __name__ == '__main__':
    main()
