import os
import re
import sys
import rpm

def check_unused_patches(spec_files):
    unused_patches = {}

    for spec_file in spec_files:
        if not os.path.isfile(spec_file):
            print(f"Spec file {spec_file} does not exist.")
            continue

        spec_dir = os.path.dirname(spec_file)
        specs_dir = os.path.join(spec_dir)
        if not os.path.isdir(specs_dir):
            print(f"SPECS directory does not exist in {spec_dir}.")
            continue

        patches = [f for f in os.listdir(specs_dir) if f.endswith('.patch')]
        
        # output the rpmdev-spectool spec_file and grab all the patches
        # run rpmdev-spectool and collect the output
        cmd = f"rpmdev-spectool --patches {spec_file}"
        output = os.popen(cmd).read()
        used_patches = re.findall(r'^\s*Patch\d+\s*:\s*(.+)', output, re.MULTILINE)
        used_patches = [patch.strip() for patch in used_patches]
        # check if the patches are used in the spec file
        unused_patches[spec_file] = []
        for patch in patches:
            if patch not in used_patches:
                unused_patches[spec_file].append(patch)
    return unused_patches

def main():
    if len(sys.argv) < 2:
        print("Usage: python check_unused_patch.py <spec_file1> <spec_file2> ...")
        sys.exit(1)
    
    # confirm rpmdev-spectool is installed
    try:
        rpmdev_spectool_version = os.popen("rpmdev-spectool --version").read()
    except Exception as e:
        print(f"Error: {e}")
        print("Please install rpmdevtools to use this script.")
        sys.exit(1)

    spec_files = sys.argv[1:]

    unused_patches = check_unused_patches(spec_files)

    for spec_file, patches in unused_patches.items():
        if patches:
            print(f"Unused patches in {spec_file}:")
            for patch in patches:
                print(f"  {patch}")
                exit(1)
        else:
            print(f"All patches are used in {spec_file}.")

if __name__ == "__main__":
    main()
