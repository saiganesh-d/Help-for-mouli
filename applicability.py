import re
from your_app.models import CFile, KernelConfig, CVEState

def extract_c_files(description):
    return list(set(re.findall(r'\b([a-zA-Z0-9_/.-]+\.c)\b', description)))

def parse_dot_config(filepath):
    configs = set()
    with open(filepath, "r") as f:
        for line in f:
            if line.startswith("CONFIG_") and "=y" in line:
                key = line.split("=")[0].strip()
                configs.add(key)
    return configs

def evaluate_cve_applicability(cve_obj, kernel_version_obj, config_file_path: str):
    c_files = extract_c_files(cve_obj.description)
    user_configs = parse_dot_config(config_file_path)
    applicable = False
    reason = "No matching config enabled."

    for cfile_name in c_files:
        short_name = cfile_name.split("/")[-1]  # in case description has path
        try:
            cfile_obj = CFile.objects.get(name=short_name)
        except CFile.DoesNotExist:
            continue

        kernel_configs = KernelConfig.objects.filter(
            kernel_version=kernel_version_obj,
            cfile=cfile_obj
        )

        for kconfig in kernel_configs:
            if kconfig.config.name in user_configs:
                applicable = True
                reason = f"{kconfig.config.name} is enabled for {cfile_obj.name}"
                break
        if applicable:
            break

    cve_obj.applicable = applicable
    cve_obj.reason = reason
    cve_obj.save()
