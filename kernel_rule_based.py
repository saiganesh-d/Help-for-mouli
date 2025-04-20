import re

# Map keywords (subsystems, drivers) to probable source directories
SUBSYSTEM_HINTS = {
    "netfilter": ["net/netfilter/"],
    "usb audio": ["sound/usb/"],
    "usb": ["drivers/usb/", "sound/usb/"],
    "alsa": ["sound/"],
    "sound": ["sound/"],
    "tty": ["drivers/tty/"],
    "xfs": ["fs/xfs/"],
    "ext4": ["fs/ext4/"],
    "ext3": ["fs/ext3/"],
    "btrfs": ["fs/btrfs/"],
    "f2fs": ["fs/f2fs/"],
    "nfs": ["fs/nfs/"],
    "cifs": ["fs/cifs/"],
    "vfat": ["fs/fat/"],
    "jfs": ["fs/jfs/"],
    "smb": ["fs/smbfs/"],
    "fuse": ["fs/fuse/"],
    "proc": ["fs/proc/"],
    "sysfs": ["fs/sysfs/"],
    "selinux": ["security/selinux/"],
    "apparmor": ["security/apparmor/"],
    "smack": ["security/smack/"],
    "seccomp": ["kernel/seccomp.c"],
    "sctp": ["net/sctp/"],
    "ipv6": ["net/ipv6/"],
    "ipv4": ["net/ipv4/"],
    "tcp": ["net/ipv4/tcp_*.c"],
    "udp": ["net/ipv4/udp.c"],
    "dns": ["net/dns_resolver.c"],
    "bluetooth": ["net/bluetooth/", "drivers/bluetooth/"],
    "rfkill": ["net/rfkill/", "drivers/rfkill/"],
    "wifi": ["drivers/net/wireless/"],
    "ethernet": ["drivers/net/ethernet/"],
    "bridge": ["net/bridge/"],
    "bonding": ["drivers/net/bonding/"],
    "drm": ["drivers/gpu/drm/"],
    "i915": ["drivers/gpu/drm/i915/"],
    "nouveau": ["drivers/gpu/drm/nouveau/"],
    "radeon": ["drivers/gpu/drm/radeon/"],
    "amdgpu": ["drivers/gpu/drm/amd/amdgpu/"],
    "gpu": ["drivers/gpu/"],
    "mm": ["mm/"],
    "slab": ["mm/slab.c", "mm/slub.c"],
    "kvm": ["arch/x86/kvm/", "virt/kvm/"],
    "irq": ["kernel/irq/"],
    "scheduler": ["kernel/sched/"],
    "futex": ["kernel/futex.c"],
    "x86": ["arch/x86/"],
    "arm": ["arch/arm/"],
    "arm64": ["arch/arm64/"],
    "powerpc": ["arch/powerpc/"],
    "mips": ["arch/mips/"],
    "riscv": ["arch/riscv/"],
    "acpi": ["drivers/acpi/"],
    "efi": ["drivers/firmware/efi/"],
    "firmware": ["drivers/firmware/"],
    "watchdog": ["drivers/watchdog/"],
    "thermal": ["drivers/thermal/"],
    "i2c": ["drivers/i2c/"],
    "spi": ["drivers/spi/"],
    "gpio": ["drivers/gpio/"],
    "pwm": ["drivers/pwm/"],
    "rtc": ["drivers/rtc/"],
    "serial": ["drivers/tty/serial/"],
    "block": ["block/", "drivers/block/"],
    "nvme": ["drivers/nvme/"],
    "scsi": ["drivers/scsi/"],
    "virtio": ["drivers/virtio/"],
    "zram": ["drivers/block/zram/"],
    "cgroup": ["kernel/cgroup/"],
    "io_uring": ["fs/io_uring/"],
    "audit": ["kernel/audit.c"],
    "vfs": ["fs/"],
    "crypto": ["crypto/", "drivers/crypto/"],
    "bpf": ["kernel/bpf/", "net/bpf/"],
    "printk": ["kernel/printk/"],
    "locking": ["kernel/locking/"],
    "timer": ["kernel/time/"],
    "rcu": ["kernel/rcu/"],
    "ipc": ["ipc/"],
    "signal": ["kernel/signal.c"],
    "syscall": ["arch/x86/entry/"],
    "module": ["kernel/module.c"],
    "sysfs": ["fs/sysfs/"],
    "debugfs": ["fs/debugfs/"],
}


FUNC_PATTERN = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]+)\s*\(')

def extract_candidates_from_description(description: str) -> list:
    candidates = set()

    # 1. Direct .c file mentions
    c_files = re.findall(r'\b([\w/.-]+\.c)\b', description)
    candidates.update(c_files)

    # 2. Subsystem keyword matching
    for keyword, folders in SUBSYSTEM_HINTS.items():
        if keyword in description.lower():
            for folder in folders:
                candidates.add(f"{folder}*.c")

    # 3. Function name matches
    funcs = FUNC_PATTERN.findall(description)
    for func in funcs:
        candidates.add(func.strip())

    return list(candidates)

from kernel_analysis.nlp_extractor import extract_candidates_from_description

def evaluate_cve_applicability(cve_obj, kernel_version_obj, config_file_path: str):
    candidates = extract_candidates_from_description(cve_obj.description)
    user_configs = parse_dot_config(config_file_path)
    applicable = False
    reason = "No matching config enabled."

    for item in candidates:
        if item.endswith(".c"):
            name = item.split("/")[-1]
            cfiles = CFile.objects.filter(name=name)
        elif item.endswith("*.c"):
            # wildcard based on folder name
            folder = item.strip("*/.c").split("/")[-1]
            cfiles = CFile.objects.filter(name__icontains=folder)
        else:
            # function name — fuzzy match
            cfiles = CFile.objects.filter(name__icontains=item)

        for cfile in cfiles:
            kernel_configs = KernelConfig.objects.filter(
                kernel_version=kernel_version_obj,
                cfile=cfile
            )
            for kconfig in kernel_configs:
                if kconfig.config.name in user_configs:
                    applicable = True
                    reason = f"{kconfig.config.name} enabled for {cfile.name} (match: {item})"
                    break
            if applicable:
                break
        if applicable:
            break

    cve_obj.applicable = applicable
    cve_obj.reason = reason
    cve_obj.status = "done"
    cve_obj.save()
