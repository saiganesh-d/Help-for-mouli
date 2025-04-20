def parse_dot_config(filepath):
    configs = set()
    with open(filepath, "r") as f:
        for line in f:
            if line.startswith("CONFIG_") and "=y" in line:
                key = line.split("=")[0].strip()
                configs.add(key)
    return configs
