#!/usr/bin/env python
"""Set an emacs "customize" variable.

name:  name of variable to set
value: value of variable to set, as elisp expression
"""

import subprocess
import getpass
from ansible.module_utils.basic import AnsibleModule


def run_emacs(prog):
    command = [
        'emacs',
        '-q',
        '--batch',
        '--user',
        getpass.getuser(),
        '--eval',
        prog
    ]
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = proc.communicate()
    return (proc, stdout, stderr)


def get_value(name):
    prog = "(print (car (custom-variable-theme-value '%s)))" % name
    (proc, stdout, stderr) = run_emacs(prog)
    if proc.returncode != 0:
        raise ValueError("Error from emacs, exitcode=%s, stderr=%s" % (proc.returncode, stderr))

    return stdout.strip()


def set_value(name, value):
    prog = "(customize-save-variable '%s %s)" % (name, value)
    (proc, _, stderr) = run_emacs(prog)
    if proc.returncode != 0:
        raise ValueError("Error from emacs, exitcode=%s, stderr=%s" % (proc.returncode, stderr))


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        value=dict(type='str', required=True),
    )

    result = dict(changed=False)
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    old_value = get_value(module.params['name'])
    result['old_value'] = old_value
    if old_value != module.params['value']:
        result['changed'] = True

    if module.check_mode:
        return result

    if result['changed']:
        set_value(module.params['name'], module.params['value'])

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
