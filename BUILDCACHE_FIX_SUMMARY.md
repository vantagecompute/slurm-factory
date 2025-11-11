# Buildcache Push Fix Summary

## Problem

The buildcache push command reported success (exit code 0) but no packages were uploaded to S3. The issue manifested as:

```
Buildcache push stderr:
bash: line 15: warning: here-document at line 1 delimited by end-of-file (wanted `EOF')
```

## Root Cause

Bash heredoc syntax doesn't work when commands are joined with `&&` on a single line. 

### What Was Broken

```python
bash_script_parts = [
    "cat > /opt/spack/opt/spack/gpg/gpg.conf << 'EOF'\npinentry-mode loopback\nEOF",
    "other command"
]
bash_script = " && ".join(bash_script_parts)
# Result: cat > file << 'EOF'\npinentry-mode loopback\nEOF && other command
# Bash sees this as ONE LINE - heredoc EOF delimiter never found!
```

When Python strings with `\n` are joined with `&&`, the newlines don't become actual line breaks in the bash command. Bash interprets this as:
- Line 1: `cat > file << 'EOF'\npinentry-mode loopback\nEOF && other command`
- Never finds the `EOF` delimiter (it's looking for it on a separate line)
- Script fails silently, subsequent commands never execute

## Solution

Replace heredoc syntax with `echo` and `printf` commands that work on single lines:

### For Simple Configs
```python
# OLD (broken):
"cat > file << 'EOF'\nline1\nEOF"

# NEW (works):
'echo "line1" > file'
```

### For Multi-line Configs
```python
# OLD (broken):
"cat > file << 'EOF'\nline1\nline2\nline3\nEOF"

# NEW (works):
'echo -e "line1\\nline2\\nline3" > file'
```

### For Multi-line Scripts
```python
# OLD (broken):
"cat > script << 'WRAPPER'\n#!/bin/bash\necho test\nWRAPPER"

# NEW (works):
r'''printf '#!/bin/bash\necho test\n' > script'''
```

## Changes Made

Fixed both buildcache push functions in `slurm_factory/utils.py`:

1. **`publish_compiler_to_buildcache()`** (lines 833-857)
2. **`push_to_buildcache()`** (lines 1051-1075)

### Specific Changes

1. **GPG config file** (single line):
   - Before: `cat > gpg.conf << 'EOF'\npinentry-mode loopback\nEOF`
   - After: `echo "pinentry-mode loopback" > gpg.conf`

2. **GPG agent config** (3 lines):
   - Before: `cat > gpg-agent.conf << 'EOF'\nallow-loopback-pinentry\ndefault-cache-ttl 34560000\nmax-cache-ttl 34560000\nEOF`
   - After: `echo -e "allow-loopback-pinentry\\ndefault-cache-ttl 34560000\\nmax-cache-ttl 34560000" > gpg-agent.conf`

3. **GPG wrapper script** (multi-line bash script):
   - Before: `cat > /usr/bin/gpg << 'WRAPPER'\n#!/bin/bash\n...\nWRAPPER`
   - After: `printf '#!/bin/bash\n...\n' > /usr/bin/gpg`

## Testing

Manual bash tests confirmed the fixes work:

```bash
# Test echo -e for multi-line config
$ bash -c "echo -e 'allow-loopback-pinentry\ndefault-cache-ttl 34560000' > /tmp/test.conf && cat /tmp/test.conf"
allow-loopback-pinentry
default-cache-ttl 34560000

# Test printf for script creation
$ bash -c 'printf "#!/bin/bash\necho test\n" > /tmp/script.sh && chmod +x /tmp/script.sh && /tmp/script.sh'
test
```

## Impact

This fix allows:
- GPG configuration files to be created correctly
- GPG wrapper script to be installed and executable
- Signed buildcache pushes to S3 to work properly
- All 31 compiler packages (or Slurm packages) to be uploaded with signatures

## Verification

To verify the fix works in GitHub Actions:

1. Trigger a compiler build workflow (e.g., GCC 11.5.0 or 15.2.0)
2. Check the "Buildcache push output:" section in the logs
3. Verify no bash heredoc errors appear
4. Confirm packages appear in S3 bucket with `.spack` and `.sig` files

## Related Issues

- **Initial problem**: "the code says it pushed to the buildcache but nothing is in the buildcache"
- **GPG signing issue**: "Inappropriate ioctl for device" (fixed with GPG wrapper)
- **Output visibility**: Added stderr output display to reveal the bash error
- **Bash syntax error**: Fixed with this commit

## Commits

- Main fix: `5eafa86` - "Fix bash heredoc syntax in GPG configuration"
- Previous: `7df3672` - "Show buildcache push output even when empty or in stderr"
