# YNL Netlink Schema Compatibility

## Summary

The HWE source `6.18.54.1` includes new Netlink validation rules:

- Commit `2fd0880f0272` adds `max: 32767` to `rt-link.yaml`.
- Commit `982c7f66c041` adds `min: 1` and `max: 86400000` to `rt-neigh.yaml`.

However, the source's `Documentation/netlink/netlink-raw.yaml` schema does not define `checks.max`. The schema still accepts `checks.min` only as an integer.

## Build failure

The failure occurs while building the YNL tools, not while building `rtla` or kernel modules:

```text
make ... -C tools/net/ynl install
  -> make generated
  -> pyynl/ynl_gen_c.py
  -> jsonschema validation
  -> ValidationError: Additional properties are not allowed ('max' was unexpected)
```

## Compatibility patch

`netlink-raw-allow-max-check.patch` backports upstream Linux commit `bf5a54bc0e3d`:

<https://github.com/torvalds/linux/commit/bf5a54bc0e3d8962474fcd611f1266eba036232f>

The patch updates only the build-time YAML schema. It adds the `len-or-limit` definition and permits `checks.max`. It does not change kernel runtime code or module behavior.

The patch is applied in the existing HWE source commit because it is required to build the selected source with YNL enabled.

## Stable-tree status

The stable `v6.18.55` schema still lacks `len-or-limit` and `checks.max`, so the same YNL build issue can affect distributions that build YNL against that source. Builds that do not build or install YNL may not encounter it.
