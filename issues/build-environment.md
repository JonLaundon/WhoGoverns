# Build environment notes

- **Git does not run in the Cowork sandbox on this OneDrive mount.** `git init` writes internal files that OneDrive immediately turns into null-byte placeholders; the sandbox then cannot read the config or delete the files ("Operation not permitted"). Symptom: `fatal: bad config line 1 in file .git/config`. Resolution: run git on the host machine or in Claude Code, not in the sandbox. A `.git_corrupt_*` folder may remain from a failed sandbox init — delete it locally.
- **Implication for the build:** the "small explainable commit per session" (Annex A11.6) is done host-side or in Claude Code. Sandbox sessions still end packaged: schema-valid records + passing `validate.py` + a session review pack.
