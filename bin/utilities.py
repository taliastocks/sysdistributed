
import sys
import os
import re
import subprocess
from subprocess import PIPE

__all__ = ['execute', 'node_usage', 'copy_to_node', 'SYSDISTRIBUTED',
    'decode_node', 'PIPE', 'test_ssh', 'remote_execute']

SYSDISTRIBUTED = os.environ.get('SYSDISTRIBUTED')


def node_usage ():
    print('   Nodes: USER@[HOST]:PORT:DIRECTORY', file=sys.stderr)
    print('       Note: The brackets above are literal brackets.',
        file=sys.stderr)



def decode_node (node):
    match = re.match(r'^([^@]*)@\[([^\]]*)\]:(\d+):(.*)$', node)
    if match == None:
        return False
    user, host, port, directory = match.groups()
    return user, host, port, directory



def execute (command, *argv,
    stdin=None, stdout=None, stderr=None):
    stdin = sys.stdin if stdin == None else stdin
    stdout = sys.stdout if stdout == None else stdout
    stderr = sys.stderr if stderr == None else stderr
    if command in os.listdir(
        os.path.join(SYSDISTRIBUTED, 'bin')):
        command = os.path.join(SYSDISTRIBUTED, 'bin', command)
    proc = subprocess.Popen([command] + list(argv),
        stdin=stdin, stdout=stdout, stderr=stderr)
    return proc



def remote_execute (user, host, port, command,
    stdin=None, stdout=None, stderr=None):
    return execute('ssh',
        '-i', os.path.join(SYSDISTRIBUTED, 'key'),
        '-p', str(port),
        '%s@%s' % (user, host),
        '-o', 'PreferredAuthentications=publickey',
        '-o', 'IdentitiesOnly=yes',
        command,
        stdin=stdin, stdout=stdout, stderr=stderr
    )



def test_ssh (user, host, port):
    return remote_execute(user, host, port, 'true').wait() == 0



def copy_to_node (node, fname, content, permissions=None):
    if type(content) == str:
        content = bytes(content, 'utf-8')
    remotesum = b''
    localsum = b''
    if permissions == None:
        command = 'cat >"%s"; sha512sum <"%s"' % (fname, fname)
    else:
        command = 'cat >"%s"; chmod %s "%s"; sha512sum <"%s"' % \
            (fname, permissions, fname, fname)
    if hasattr(content, 'fileno'): # Is an open file.
        content.seek(0)
        remotesum, _ = execute('run-node', node, command,
            stdin=content, stdout=PIPE).communicate()
        content.seek(0)
        localsum, _ = execute('sha512sum',
            stdin=content, stdout=PIPE).communicate()
    elif type(content) == bytes:
        remotesum, _ = execute('run-node', node, command,
            stdin=PIPE, stdout=PIPE).communicate(content)
        localsum, _ = execute('sha512sum',
            stdin=PIPE, stdout=PIPE).communicate(content)
    return remotesum == localsum and \
        re.match(b'^[0-9a-fA-F]{128} ', localsum) != None


