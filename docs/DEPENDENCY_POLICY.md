# Dependency and platform policy

Quantum Fly supports CPython 3.10 through 3.13 on Windows, Linux, and macOS. The primary local evidence is produced on Windows with PowerShell. The cross-platform clean-environment workflow runs on Linux and must remain green before a release claim.

`pyproject.toml` declares compatible dependency ranges for users. `requirements-lock.txt` records the exact environment used by the clean verification workflow, including the optional PennyLane path. This is a verification snapshot, not a promise that every compatible combination has been tested.

Dependency updates should be narrow and deliberate:

1. update the declared range only when compatibility requirements change;
2. refresh exact versions in `requirements-lock.txt`;
3. run the full test suite, compile/import checks, and the no-data quickstart check in a fresh environment;
4. preserve failures and platform limitations in the resulting evidence.

Security reports should not include secrets, private data, brokerage information, or unpublished strategy material. Until a private reporting channel is selected, report only reproducible, non-sensitive defects through the repository's normal maintainer contact. The software is MIT-licensed, but the repository does not claim a supported production service.
