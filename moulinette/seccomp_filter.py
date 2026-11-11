"""Filtre seccomp BPF conservateur pour Bubblewrap (x86_64).

Ce filtre bloque un sous-ensemble d'appels système d'administration, de montage,
de traçage et de chargement noyau (ptrace, mount, umount2, pivot_root, chroot,
kexec_load, kexec_file_load, reboot, swapon, swapoff, init_module, finit_module,
delete_module, acct, quotactl, bpf, perf_event_open, userfaultfd, add_key,
request_key, keyctl, unshare, setns, open_by_handle_at) ainsi que l'ABI x32.
Il autorise le reste afin de préserver le fonctionnement de cc, nm, ar, make,
Python/Norminette et des binaires étudiants. Il ne suffit pas à sécuriser
l'exécution d'un code hostile.
"""
from contextlib import contextmanager
import errno
import platform
import struct
import tempfile

AUDIT_ARCH_X86_64 = 0xC000003E
SECCOMP_RET_ALLOW = 0x7FFF0000
SECCOMP_RET_ERRNO = 0x00050000 | errno.EPERM

# Numéros d'appels système Linux x86_64 bloqués à l'intérieur du conteneur bwrap.
BLOCKED_SYSCALLS_X86_64 = (
    101,  # ptrace
    155,  # pivot_root
    161,  # chroot
    163,  # acct
    165,  # mount
    166,  # umount2
    167,  # swapon
    168,  # swapoff
    169,  # reboot
    175,  # init_module
    176,  # delete_module
    179,  # quotactl
    246,  # kexec_load
    248,  # add_key
    249,  # request_key
    250,  # keyctl
    272,  # unshare
    298,  # perf_event_open
    304,  # open_by_handle_at
    308,  # setns
    313,  # finit_module
    320,  # kexec_file_load
    321,  # bpf
    323,  # userfaultfd
)


def seccomp_bpf_bytes(machine=None):
    """Construit le programme classic BPF pour bwrap --seccomp, ou None hors x86_64."""
    arch = machine if machine is not None else platform.machine()
    if arch != 'x86_64':
        return None
    insns = [
        (0x20, 0, 0, 4),                          # LD [seccomp_data.arch]
        (0x15, 1, 0, AUDIT_ARCH_X86_64),          # JEQ AUDIT_ARCH_X86_64 -> skip deny
        (0x06, 0, 0, SECCOMP_RET_ERRNO),          # RET EPERM
        (0x20, 0, 0, 0),                          # LD [seccomp_data.nr]
        (0x35, 0, 1, 0x40000000),                 # JGE __X32_SYSCALL_BIT -> deny
        (0x06, 0, 0, SECCOMP_RET_ERRNO),          # RET EPERM
    ]
    total = len(BLOCKED_SYSCALLS_X86_64)
    for idx, nr in enumerate(BLOCKED_SYSCALLS_X86_64):
        insns.append((0x15, total - idx, 0, nr))  # JEQ nr -> jump to RET EPERM
    insns.append((0x06, 0, 0, SECCOMP_RET_ALLOW))
    insns.append((0x06, 0, 0, SECCOMP_RET_ERRNO))
    return b''.join(struct.pack('<HBBI', code, jt, jf, k) for code, jt, jf, k in insns)


@contextmanager
def seccomp_fd():
    """Fournit un descripteur de fichier positionné au début du filtre BPF, ou None."""
    payload = seccomp_bpf_bytes()
    if payload is None:
        yield None
        return
    with tempfile.TemporaryFile() as handle:
        handle.write(payload)
        handle.flush()
        handle.seek(0)
        yield handle.fileno()
