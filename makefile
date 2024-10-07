config_pattern = re.compile(r'\$\((CONFIG_[A-Za-z0-9_]+)\)\s*:=\s*(\w+)\.o')

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




from django.db import models

class KernelVersion(models.Model):
    version = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.version

class CFile(models.Model):
    file_path = models.TextField(unique=True)  # Full path to the .c file

    def __str__(self):
        return self.file_path

class ConfigOption(models.Model):
    config_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.config_name

class KernelConfig(models.Model):
    kernel_version = models.ForeignKey(KernelVersion, on_delete=models.CASCADE, related_name='configs')
    c_file = models.ForeignKey(CFile, on_delete=models.CASCADE, related_name='configs')
    config_option = models.ForeignKey(ConfigOption, on_delete=models.CASCADE, related_name='configs')

    class Meta:
        unique_together = ('kernel_version', 'c_file', 'config_option')

    def __str__(self):
        return f"{self.kernel_version.version} -> {self.c_file.file_path} -> {self.config_option.config_name}"



import os
import re
import django
from pathlib import Path

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project_name.settings')
django.setup()

from your_app.models import KernelVersion, CFile, ConfigOption, KernelConfig

# Regular expression to match lines with CONFIG options
config_pattern = re.compile(r'obj-\$\((CONFIG_[A-Z0-9_]+)\)\s*\+=\s*([a-zA-Z0-9_\-]+)\.o')

def find_makefiles(directory):
    """Find all Makefiles in the kernel source directory."""
    makefiles = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file == "Makefile":
                makefiles.append(os.path.join(root, file))
    return makefiles

def parse_makefile(makefile_path, kernel_version_obj):
    """Parse a Makefile and extract CONFIG options with full path of corresponding .c files."""
    makefile_dir = os.path.dirname(makefile_path)  # Get the directory of the Makefile
    with open(makefile_path, 'r') as makefile:
        for line in makefile:
            match = config_pattern.search(line)
            if match:
                config_option_name = match.group(1)
                c_file_name = match.group(2) + ".c"
                # Get the full relative path of the .c file
                full_c_file_path = os.path.join(makefile_dir, c_file_name)

                # Save the extracted data to the database
                save_to_db(kernel_version_obj, full_c_file_path, config_option_name)

def save_to_db(kernel_version_obj, full_c_file_path, config_option_name):
    """Save the kernel version, C file path, and CONFIG option to the database."""

    # Retrieve or create the CFile object
    c_file_obj, created = CFile.objects.get_or_create(file_path=full_c_file_path)

    # Retrieve or create the ConfigOption object
    config_option_obj, created = ConfigOption.objects.get_or_create(config_name=config_option_name)

    # Check if the combination of kernel version, c_file, and config_option already exists
    if not KernelConfig.objects.filter(kernel_version=kernel_version_obj, c_file=c_file_obj, config_option=config_option_obj).exists():
        # Create a new KernelConfig entry
        KernelConfig.objects.create(kernel_version=kernel_version_obj, c_file=c_file_obj, config_option=config_option_obj)

def process_kernel_version(root_dir, kernel_version_name):
    """Process a specific kernel version and save its configs to the database."""
    # Retrieve or create the KernelVersion object
    kernel_version_obj, created = KernelVersion.objects.get_or_create(version=kernel_version_name)
    
    # Find all Makefiles in the kernel source directory
    makefiles = find_makefiles(root_dir)

    # Parse each Makefile to extract CONFIG options
    for makefile in makefiles:
        parse_makefile(makefile, kernel_version_obj)

def main():
    # Root directory where different kernel versions are stored
    base_dir = "/path/to/downloaded/kernels"  # Change this to the location of the kernel source code
    
    # Loop through directories like v3.x, v4.x, v5.x, v6.x
    for version_dir in os.listdir(base_dir):
        version_path = os.path.join(base_dir, version_dir)
        
        # Only process directories
        if os.path.isdir(version_path):
            # Loop through individual kernel versions inside the version directory
            for kernel_version_dir in os.listdir(version_path):
                kernel_path = os.path.join(version_path, kernel_version_dir)
                
                # Process the kernel version if it's a directory
                if os.path.isdir(kernel_path):
                    print(f"Processing kernel version: {kernel_version_dir}")
                    process_kernel_version(kernel_path, kernel_version_dir)

if __name__ == "__main__":
    main()


