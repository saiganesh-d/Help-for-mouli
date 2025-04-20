import os
import re
import subprocess
from collections import defaultdict
from django.db import transaction
from your_app.models import KernelVersion, CFile, Config, KernelConfig

KERNEL_CACHE_DIR = "/tmp/linux-kernels"


def download_and_extract_kernel(version: str) -> str:
    short_version = ".".join(version.split(".")[:2])
    target_dir = os.path.join(KERNEL_CACHE_DIR, short_version)
    if os.path.exists(target_dir):
        return target_dir

    os.makedirs(KERNEL_CACHE_DIR, exist_ok=True)
    print(f"Cloning kernel version {short_version} ...")
    subprocess.run([
        "git", "clone",
        "--depth", "1",
        "--branch", f"v{short_version}",
        "https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git",
        target_dir
    ], check=True)

    return target_dir


def preprocess_lines(lines):
    new_lines = []
    continuation = ''
    for line in lines:
        line = line.rstrip()
        if line.endswith('\\'):
            continuation += line[:-1] + ' '
        else:
            new_lines.append((continuation + line).strip())
            continuation = ''
    return new_lines


@transaction.atomic
def parse_makefiles_and_save(version: str):
    root_dir = download_and_extract_kernel(version)
    kernel_version_obj, _ = KernelVersion.objects.get_or_create(version=version)

    # Regex patterns
    obj_line_pattern = re.compile(r'obj-[^=]+\s*\+=\s*(.*)')
    config_ref_pattern = re.compile(r'\$\((CONFIG_[A-Z0-9_]+)\)')
    group_assign_pattern = re.compile(r'([a-zA-Z0-9_.-]+)-objs\s*[:+]?=\s*(.*)')
    ifdef_pattern = re.compile(r'^\s*ifdef\s+(CONFIG_[A-Z0-9_]+)')
    ifeq_pattern = re.compile(r'^\s*ifeq\s*\(\s*\$\(CONFIG_([A-Z0-9_]+)\)\s*,\s*y\s*\)')
    ifneq_pattern = re.compile(r'^\s*ifneq\s*\(\s*\$\(CONFIG_([A-Z0-9_]+)\)\s*,\s*y\s*\)')
    else_pattern = re.compile(r'^\s*else\s*$')
    endif_pattern = re.compile(r'^\s*endif\s*$')

    o_groups = {}
    context_stack = []

    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if fname.lower() in ("makefile", "kbuild"):
                filepath = os.path.join(dirpath, fname)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        lines = preprocess_lines(f.readlines())
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
                    continue

                for line in lines:
                    # Context stack for ifdef / ifeq / ifneq
                    if ifdef_match := ifdef_pattern.match(line):
                        context_stack.append((ifdef_match.group(1), True))
                        continue
                    if ifeq_match := ifeq_pattern.match(line):
                        context_stack.append((f"CONFIG_{ifeq_match.group(1)}", True))
                        continue
                    if ifneq_match := ifneq_pattern.match(line):
                        context_stack.append((f"CONFIG_{ifneq_match.group(1)}", False))
                        continue
                    if else_pattern.match(line):
                        if context_stack:
                            var, val = context_stack.pop()
                            context_stack.append((var, not val))
                        continue
                    if endif_pattern.match(line):
                        if context_stack:
                            context_stack.pop()
                        continue

                    # Handle foo-objs := a.o b.o
                    if group_match := group_assign_pattern.match(line):
                        group, members = group_match.groups()
                        member_objs = members.strip().split()
                        o_groups[group + ".o"] = [m for m in member_objs if m.endswith(".o")]
                        continue

                    # Handle obj-$(CONFIG_...) += foo.o
                    if obj_match := obj_line_pattern.search(line):
                        objs = obj_match.group(1).split()
                        configs = config_ref_pattern.findall(line)

                        # If no direct config but inside a context block
                        if not configs and context_stack:
                            configs = [cfg for cfg, active in context_stack if active]

                        for obj in objs:
                            if not obj.endswith(".o"):
                                continue

                            c_files = []
                            if obj in o_groups:
                                c_files = [o.replace(".o", ".c") for o in o_groups[obj]]
                            else:
                                c_files = [obj.replace(".o", ".c")]

                            for cfile in c_files:
                                cfile_path = os.path.normpath(os.path.join(dirpath, cfile))
                                if not os.path.isfile(cfile_path):
                                    continue

                                cfile_name = os.path.basename(cfile_path)
                                cfile_obj, _ = CFile.objects.get_or_create(name=cfile_name)

                                for config in configs:
                                    config_obj, _ = Config.objects.get_or_create(name=config)
                                    KernelConfig.objects.get_or_create(
                                        kernel_version=kernel_version_obj,
                                        config=config_obj,
                                        cfile=cfile_obj
                                    )

    print(f"[✅] Kernel parsing complete for version {version}")


import tarfile
import urllib.request

def download_and_extract_kernel(version: str) -> str:
    short_version = ".".join(version.split(".")[:2])
    major_digit = version.split(".")[0]
    major_series = f"v{major_digit}.x"
    url = f"https://cdn.kernel.org/pub/linux/kernel/{major_series}/linux-{version}.tar.xz"
    dest_dir = os.path.join(KERNEL_CACHE_DIR, version)
    archive_path = os.path.join(KERNEL_CACHE_DIR, f"linux-{version}.tar.xz")

    if os.path.exists(dest_dir):
        print(f"[✓] Kernel source already extracted at {dest_dir}")
        return dest_dir

    print(f"[↓] Downloading kernel source: {url}")
    urllib.request.urlretrieve(url, archive_path)

    print(f"[📦] Extracting kernel source to {dest_dir}")
    with tarfile.open(archive_path, "r:xz") as tar:
        tar.extractall(path=KERNEL_CACHE_DIR)

    os.rename(os.path.join(KERNEL_CACHE_DIR, f"linux-{version}"), dest_dir)
    return dest_dir

