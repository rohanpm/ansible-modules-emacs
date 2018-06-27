#!/usr/bin/env python
"""Set an emacs "customize" variable.

name:  name of variable to set
value: value of variable to set, as elisp expression
"""

import subprocess
import getpass
from ansible.module_utils.basic import AnsibleModule


class EmacsError(RuntimeError):
    def __init__(self, returncode, stderr, message=None, command=None):
        super(EmacsError, self).__init__(message or 'emacs failed')
        self.returncode = returncode
        self.stderr = stderr
        self.command = command


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
    return (proc, stdout, stderr, command)


def get_value(name):
    prog = """
        (print
            (let ((val (custom-variable-theme-value '%s)))
                (if val
                    (car val)
                    'ANSIBLE-UNSET-SENTINEL)))
    """.strip() % name
    (proc, stdout, stderr, command) = run_emacs(prog)
    if proc.returncode != 0:
        raise EmacsError(proc.returncode, stderr, command)

    out = stdout.strip()
    if out == "ANSIBLE-UNSET-SENTINEL":
        out = None
    return out


def set_value(name, value):
    prog = "(customize-save-variable '%s %s)" % (name, value)
    (proc, _, stderr, command) = run_emacs(prog)
    if proc.returncode != 0:
        raise EmacsError(proc.returncode, stderr, command)


def canonicalize(value):
    prog = "(print '%s)" % value
    (proc, stdout, stderr, command) = run_emacs(prog)
    if proc.returncode != 0:
        raise EmacsError(proc.returncode, stderr, command)
    return stdout.strip()


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

    try:
        new_value = canonicalize(module.params['value'])
        result['new_value'] = new_value

        old_value = get_value(module.params['name'])
        result['old_value'] = old_value
        if old_value != new_value:
            result['changed'] = True

        if module.check_mode:
            return result

        if result['changed']:
            set_value(module.params['name'], new_value)

        module.exit_json(**result)
    except EmacsError as err:
        result['emacs_returncode'] = err.returncode
        result['emacs_stderr'] = err.stderr
        result['emacs_command'] = err.command
        result['msg'] = err.message
        module.fail_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
