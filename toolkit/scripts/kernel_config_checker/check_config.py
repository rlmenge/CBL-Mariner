#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Simple kernel config checker script.
Checks a Linux kernel .config file against intentional configuration settings.
"""

import argparse
import json
from pathlib import Path
from typing import Dict

from kernel_config_checker.schema.schema import (
    IntentionalKernelConfigSchema,
)


def parse_kernel_config(config_path: Path) -> Dict[str, str]:
    """Parse a Linux kernel .config file."""
    config = {}
    with open(config_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") and "is not set" in line:
                # Handle "# CONFIG_FOO is not set"
                config_name = line.split()[1]
                config[config_name] = "n"
            elif line and not line.startswith("#") and "=" in line:
                # Handle "CONFIG_FOO=y"
                key, value = line.split("=", 1)
                config[key] = value
    return config


def load_intentional_config(config_path: Path) -> IntentionalKernelConfigSchema:
    """Load and validate the intentional kernel config file."""
    with open(config_path, "r") as f:
        data = json.load(f)
    return IntentionalKernelConfigSchema.model_validate(data)


def check_kernel_config(
    actual_config: Dict[str, str],
    schema: IntentionalKernelConfigSchema,
    kernel_name: str,
    architecture: str,
) -> bool:
    """Check if actual kernel config matches intentional config."""
    print(f"Checking kernel config for: {kernel_name} ({architecture})")

    # Start with default configs
    all_configs = {}

    # Add default configurations
    for kernel_config in schema.default.kernel_configs:
        config_name = kernel_config.name
        for arch_pair in kernel_config.values:
            if arch_pair.architecture.value == architecture:
                all_configs[config_name] = {
                    "expected": arch_pair.value,
                    "justification": kernel_config.justification,
                    "source": "default",
                }
                break

    # Apply kernel-specific overrides
    for override in schema.overrides:
        if override.name == kernel_name:
            print(f"✓ Found kernel-specific overrides for '{kernel_name}'")
            for kernel_config in override.kernel_configs:
                config_name = kernel_config.name
                for arch_pair in kernel_config.values:
                    if arch_pair.architecture.value == architecture:
                        all_configs[config_name] = {
                            "expected": arch_pair.value,
                            "justification": kernel_config.justification,
                            "source": f"override ({kernel_name})",
                        }
                        break
            break

    print(f"✓ Checking {len(all_configs)} configurations (default + overrides)")

    # Check each configuration
    errors = []
    correct_count = 0
    for config_name, config_info in all_configs.items():
        expected_value = config_info["expected"]
        actual_value = actual_config.get(config_name, "n")

        if actual_value != expected_value:
            error_msg = f"  ✗ {config_name}: expected '{expected_value}', got '{actual_value}' (from {config_info['source']})"
            errors.append(error_msg)
            print(error_msg)
        else:
            correct_count += 1

    if errors:
        print(f"\n✗ Found {len(errors)} configuration errors ({correct_count} correct)")
        return False
    else:
        print(f"\n✓ All {len(all_configs)} configurations are correct")
        return True


def add_config_interactive(schema_path: Path) -> None:
    """Interactively add a new kernel configuration to the JSON file."""
    print("Adding new kernel configuration...")

    # Get config name
    config_name = input("Enter config name (e.g., CONFIG_EXAMPLE): ").strip()
    if not config_name.startswith("CONFIG_"):
        config_name = "CONFIG_" + config_name

    # Get values for architectures
    print("\nEnter values for each architecture (y/n/m or specific value, leave blank to skip):")
    x86_64_value = input("x86_64 value: ").strip()
    arm64_value = input("arm64 value: ").strip()

    # Get justification
    justification = input("\nEnter justification: ").strip()

    # Load existing schema to check available overrides
    with open(schema_path, "r") as f:
        data = json.load(f)

    # Get target section (default or kernel override)
    target = input("\nAdd to [d]efault or [o]verride? [d]: ").strip().lower()

    if target.startswith("o"):
        # Show available override options
        overrides = data.get("overrides", [])
        if not overrides:
            print("No override sections found. Creating 'kernel' override...")
            override_name = "kernel"
        else:
            print("\nAvailable override sections:")
            for i, override in enumerate(overrides):
                override_name = override.get("name", f"override-{i}")
                config_count = len(override.get("kernel_configs", []))
                print(f"  {i + 1}. {override_name} ({config_count} configs)")

            if len(overrides) == 1:
                override_name = overrides[0].get("name", "kernel")
                print(f"Using: {override_name}")
            else:
                while True:
                    try:
                        choice = input(
                            f"\nSelect override (1-{len(overrides)}) or enter new name: "
                        ).strip()
                        if choice.isdigit():
                            idx = int(choice) - 1
                            if 0 <= idx < len(overrides):
                                override_name = overrides[idx].get(
                                    "name", f"override-{idx}"
                                )
                                break
                        else:
                            override_name = choice
                            break
                    except (ValueError, IndexError):
                        print("Invalid selection. Try again.")

        target_section = ("override", override_name)
    else:
        target_section = ("default", None)

    # Create new config object
    values = []
    if x86_64_value:
        values.append({"architecture": "x86_64", "value": x86_64_value})
    if arm64_value:
        values.append({"architecture": "arm64", "value": arm64_value})
    
    if not values:
        print("❌ Error: At least one architecture value must be provided")
        return

    new_config = {
        "name": config_name,
        "values": values,
        "justification": justification,
    }

    # Add to appropriate section
    if target_section[0] == "default":
        if "default" not in data:
            data["default"] = {"name": "default", "kernel_configs": []}
        data["default"]["kernel_configs"].append(new_config)
        print(f"✓ Added {config_name} to default section")
    else:
        override_name = target_section[1]

        # Find or create the specified override
        target_override = None
        for override in data.get("overrides", []):
            if override.get("name") == override_name:
                target_override = override
                break

        if not target_override:
            # Create new override section
            if "overrides" not in data:
                data["overrides"] = []
            target_override = {"name": override_name, "kernel_configs": []}
            data["overrides"].append(target_override)
            print(f"Created new override section: {override_name}")

        target_override["kernel_configs"].append(new_config)
        print(f"✓ Added {config_name} to '{override_name}' override section")

    # Save updated data
    with open(schema_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✓ Updated {schema_path}")


def check_config_across_all(
    schema: IntentionalKernelConfigSchema, config_name: str
) -> None:
    """Check the value of a specific config across all architectures and kernels."""
    print(f"Config: {config_name}")

    found_configs = []

    # Check default section
    for kernel_config in schema.default.kernel_configs:
        if kernel_config.name == config_name:
            found_configs.append(("default", kernel_config))
            break

    # Check all override sections
    for override in schema.overrides:
        for kernel_config in override.kernel_configs:
            if kernel_config.name == config_name:
                found_configs.append((override.name, kernel_config))
                break

    if not found_configs:
        print("❌ Not found")
        return

    # Collect all values by architecture
    all_values = {}
    justifications = []

    for section_name, kernel_config in found_configs:
        justifications.append(f"{section_name}: {kernel_config.justification}")
        for arch_pair in kernel_config.values:
            arch = arch_pair.architecture
            value = arch_pair.value

            if arch not in all_values:
                all_values[arch] = []
            all_values[arch].append((section_name, value))

    # Show values by architecture
    for arch in sorted(all_values.keys()):
        values = [f"{section}={value}" for section, value in all_values[arch]]
        print(f"  {arch}: {', '.join(values)}")

    # Show conflicts if any
    conflicts = []
    for arch in all_values:
        values = [value for _, value in all_values[arch]]
        if len(set(values)) > 1:
            conflicts.append(arch)

    if conflicts:
        print(f"  ⚠️  Conflicts in: {', '.join(conflicts)}")

    # Show first justification (they're usually the same)
    if justifications:
        print(f"  Reason: {justifications[0].split(': ', 1)[1]}")


def main():
    parser = argparse.ArgumentParser(
        description="Check kernel .config file against intentional configuration"
    )
    parser.add_argument(
        "--add-config",
        metavar="JSON_FILE",
        help="Interactively add a new config to the JSON file",
    )
    parser.add_argument(
        "--check-all",
        nargs=2,
        metavar=("JSON_FILE", "CONFIG_NAME"),
        help="Check a config value across all architectures and kernels",
    )
    parser.add_argument("kernel_config", nargs="?", help="Path to kernel .config file")
    parser.add_argument(
        "intentional_config", nargs="?", help="Path to intentional config JSON file"
    )
    parser.add_argument("kernel_name", nargs="?", help="Name of the kernel to check")
    parser.add_argument(
        "architecture", nargs="?", help="Architecture (x86_64 or arm64)"
    )

    args = parser.parse_args()

    # Handle add-config mode
    if args.add_config:
        try:
            add_config_interactive(Path(args.add_config))
            return 0
        except Exception as e:
            print(f"✗ Error adding config: {e}")
            return 1

    # Handle check-all mode
    if args.check_all:
        try:
            json_file, config_name = args.check_all
            schema = load_intentional_config(Path(json_file))
            print(f"✓ Loaded intentional config: {json_file}")
            check_config_across_all(schema, config_name)
            return 0
        except Exception as e:
            print(f"✗ Error checking config: {e}")
            return 1

    # Validate required arguments for normal mode
    if not all(
        [
            args.kernel_config,
            args.intentional_config,
            args.kernel_name,
            args.architecture,
        ]
    ):
        parser.error(
            "kernel_config, intentional_config, kernel_name, and architecture are required when not using --add-config or --check-all"
        )

    try:
        # Parse actual kernel config
        kernel_config_path = Path(args.kernel_config)
        actual_config = parse_kernel_config(kernel_config_path)
        print(
            f"✓ Parsed kernel config: {kernel_config_path} ({len(actual_config)} settings)"
        )

        # Load intentional config
        intentional_config_path = Path(args.intentional_config)
        schema = load_intentional_config(intentional_config_path)
        print(f"✓ Loaded intentional config: {intentional_config_path}")

        # Check kernel config
        is_valid = check_kernel_config(
            actual_config, schema, args.kernel_name, args.architecture
        )

        if is_valid:
            print("✓ Kernel configuration check passed")
            return 0
        else:
            print("✗ Kernel configuration check failed")
            return 1

    except Exception as e:
        print(f"✗ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
