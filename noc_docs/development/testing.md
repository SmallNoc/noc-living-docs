# Testing

## Project Test Commands

- Unit tests: `python -m unittest discover -s tests`
- Protocol validation: `python scripts/noc.py validate`
- Release check: `python scripts/release.py --check`
- Compile check: `python -m py_compile scripts/__init__.py scripts/noc.py scripts/init-noc-docs.py scripts/index-noc-docs.py scripts/release.py scripts/validate-noc-docs.py`

## Verification Policy

开发任务完成前，Agent 应根据影响范围运行相关测试。如果测试无法运行，必须说明原因和剩余风险。

## Required Reporting

Final responses should include:

- commands run
- pass/fail result
- skipped checks and reasons
- affected `test-record.md` updates
