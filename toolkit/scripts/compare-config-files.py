import sys
import argparse
import subprocess
import os
import sys
import time


def get_commit_info(repo_path, config_option):
    current_directory = os.getcwd()
    # Change to the repository directory
    os.chdir(repo_path)
    

    # Run the git log command to find when CONFIG_MLX5 was removed
    #config_option="CONFIG_ND_BLK"
    config="config " + config_option.replace("CONFIG_","")
    timeout_seconds=60
    git_command = f'git --no-pager log --after="2022-01-01" -S "{config}"'
    output_file = 'git_log_output.txt'
    if os.path.exists(output_file):
        os.remove(output_file)
    timeout_command = f'timeout {timeout_seconds}s {git_command} > {output_file}'
    print(timeout_command)
    
    try:
        subprocess.check_call(timeout_command, shell=True)
    except subprocess.CalledProcessError as e:
        if e.returncode == 124:
            print(f"Command timed out after {timeout_seconds} seconds.")
        else:
            print(f"Error executing command: {e}")

    with open(output_file, 'r') as file:
        log_output = file.read()
    os.remove(output_file)
    os.chdir(current_directory)
    return log_output


def read_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        config_options = {}
        
        for line in lines:
            if line.strip() is not "":
                if line.startswith('#') and "is not set" not in line:
                    continue
                if "is not set" in line:
                    line=line.replace("# ","")
                    option, value = line.strip().split('is', 1)
                    value = "is not set"
                    option=option.strip()
                else:
                    option, value = line.strip().split('=', 1)
                config_options[option] = value
        return config_options

parser = argparse.ArgumentParser(description="A script with optional arguments")

# Define the two required positional arguments
parser.add_argument('file1_path', type=str, help='First positional argument')
parser.add_argument('file2_path', type=str, help='Second positional argument')

# Define the optional argument
parser.add_argument('--commit_history_repo', type=str, help='Enable commit searching')

# Parse the command line arguments
args = parser.parse_args()

# Access the arguments
print(f'Positional argument 1: {args.file1_path}')
file1_path = args.file1_path
print(f'Positional argument 2: {args.file2_path}')
file2_path = args.file2_path
print(f'Optional argument: {args.commit_history_repo}')
check_configs=False
# Access the optional argument if provided
if args.commit_history_repo is not None:
    check_configs= True
    repo_path = args.commit_history_repo

file1_options = read_file(file1_path)
file2_options = read_file(file2_path)

common_options = set(file1_options.keys()) & set(file2_options.keys())
unique_file1_options = set(file1_options.keys()) - set(file2_options.keys())
unique_file2_options = set(file2_options.keys()) - set(file1_options.keys())

print(f"########### Common options with different values [{file1_path} : {file2_path}] ###########")
for option in common_options:
    if file1_options[option] != file2_options[option]:
        print(f"{option} = {file1_options[option]} : {file2_options[option]}")
print()
print(f"########### Options unique to {file1_path} ###########")
prev_value = ""
for option in sorted(unique_file1_options, key=file1_options.get):
    if file1_options[option] not in "is not set":
        if prev_value != file1_options[option]:
            print(f"---- {file1_options[option]} ---- ")
            prev_value = file1_options[option]
        print(f"{option} = {file1_options[option]}")
        if check_configs:
            print(get_commit_info(repo_path, option))

print()
prev_value = ""
print(f"########### Options unique to {file2_path} ########### ")
for option in sorted(unique_file2_options, key=file2_options.get):
    if file2_options[option] not in "is not set":
        if prev_value != file2_options[option] :
            print(f"---- {file2_options[option]} ---- ")
            prev_value = file2_options[option]
        print(f"{option} = {file2_options[option]}")

