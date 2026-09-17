# Examples

Runnable demos for Androguard v5. They double as regression tests via
`tests/test_examples.py`.

Default APK: `tests/data/APK/TestActivity.apk`.

```bash
# from repo root (with androguard + deps installed)
python -m examples.application_summary
python -m examples.disassemble          # needs androguard[disasm]
python -m examples.run_all

# or through the test suite
python -m unittest tests.test_examples -v
```

| Module | Needs |
|--------|-------|
| `application_summary` | core |
| `apk_and_dex` | core |
| `disassemble` | `[disasm]` |
| `decompile` | `[decompile]` |
| `arm` | `[arm]` |
| `patch_decode` | `[patch]` |
