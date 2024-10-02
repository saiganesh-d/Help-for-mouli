import os
import re

# Directory containing the extracted kernel source files
kernel_source_dir = "linux-6.5"

# Regular expression to match lines with CONFIG options
config_pattern = re.compile(r'obj-\$\((CONFIG_[A-Z0-9_]+)\)\s*\+=\s*([a-zA-Z0-9_\-]+)\.o')

# Dictionary to store the mapping of full path of .c files to CONFIG options
config_map = {}

def find_makefiles(directory):
    """Find all Makefiles in the kernel source directory."""
    makefiles = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file == "Makefile":
                makefiles.append(os.path.join(root, file))
    return makefiles

def parse_makefile(makefile_path):
    """Parse a Makefile and extract CONFIG options with full path of corresponding .c files."""
    makefile_dir = os.path.dirname(makefile_path)  # Get the directory of the Makefile
    with open(makefile_path, 'r') as makefile:
        for line in makefile:
            match = config_pattern.search(line)
            if match:
                config_option = match.group(1)
                c_file = match.group(2) + ".c"
                # Get the full relative path of the .c file
                full_c_file_path = os.path.join(makefile_dir, c_file)
                config_map[full_c_file_path] = config_option

# Find all Makefiles in the kernel source directory
makefiles = find_makefiles(kernel_source_dir)

# Parse each Makefile to extract CONFIG options
for makefile in makefiles:
    parse_makefile(makefile)

# Output the mapping of .c files (with full path) to CONFIG options
with open('config_mapping_with_paths.txt', 'w') as output_file:
    for c_file, config_option in config_map.items():
        output_file.write(f"{c_file} is controlled by {config_option}\n")
        print(f"{c_file} is controlled by {config_option}")
