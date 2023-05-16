# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import argparse
import sys

def check_config_arch(input_file):
    with open(input_file, 'r') as file:
        contents = file.read()
    file.close()
    if "Linux/x86_64" in contents:
        return "AMD64"
    elif "Linux/arm64" in contents:
        return "ARM64"
    else:
        return None

def check_strings_in_file(json_file, input_file):
    arch = check_config_arch(input_file)
    with open(json_file, 'r') as file:
        data = json.load(file)
        configData = data['required-configs']

    with open(input_file, 'r') as file:
        contents = file.read().split("\n")

    matched_strings = {}

    for key, value in configData.items():
        # check for arch
        if arch not in value['arch']:
            continue
        found = False
        for line in contents:
            # check for key in line without extra _VALUE
            if "{0}=".format(key) in line or "{0} is not set".format(key) in line:
                for val in value['value']:
                    if val in line:
                        found = True
                        break
                else:
                    matched_strings[key] = (line.split(key)[1].replace('=',''), value['value'], value['comment'])
                    found = True
                    break
        if not found:
            # check if config can be missing
            if "" not in value['value']:
                matched_strings[key] = (line, value['value'], value['comment'])

    return matched_strings

## Main
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Tool for checking if an RPM spec file follows CBL-Mariner's guidelines.")


    parser.add_argument('--required_configs', help='path to json of required configs', required=True)
    parser.add_argument('--config_file', help='path to config being checked', required=True)
    args = parser.parse_args()
    requiredConfigs = args.required_configs
    configFile = args.config_file
    result = check_strings_in_file(requiredConfigs, configFile)
    if result == {}:
        print("All required configs are present")
    else:
        print ("====================== Kernel config verification FAILED ======================")
        for key, value in result.items():
            if value[0] == "" :
                print('{0} is missing, expected {1}. Reason: {2}'.format(key, value[1], value[2]))
            else: 
                print('{0} is "{1}", expected {2}. Reason: {3}'.format(key, value[0], value[1], value[2]))
        sys.exit(1)
