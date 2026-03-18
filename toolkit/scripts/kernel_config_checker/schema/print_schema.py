# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ---------------------------------------------------------

import json

from .schema import IntentionalKernelConfigSchema


def print_schema() -> str:
    """Print the schema for kernel configuration settings."""
    schema = IntentionalKernelConfigSchema.model_json_schema()
    print(json.dumps(schema, indent=2))
    return ""


if __name__ == "__main__":
    print(print_schema())
