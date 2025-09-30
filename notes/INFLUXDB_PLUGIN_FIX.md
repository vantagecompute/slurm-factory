# InfluxDB Plugin Fix - slurmstepd Error

## Problem Summary

Jobs fail with the error:
```
[2025-10-04T14:51:02.122] error: _handle_return_code: Can not read return code from slurmstepd: Input/output error
```

## Root Cause

The `acct_gather_profile_influxdb.so` plugin requires the following symbols:
- `slurm_curl_init`
- `slurm_curl_fini`
- `slurm_curl_request`

These symbols are provided by **`libslurm_curl.so`**, which is manually compiled from `slurm_curl.c` as a convenience library. However, the influxdb plugin was **NOT being linked** against this library during the build process, causing undefined symbol errors at runtime.

## Investigation Results

### What We Found:

1. ✅ **InfluxDB is running and configured correctly**
   - Service is active
   - Database `slurm-job-metrics` exists
   - Can write data to InfluxDB successfully

2. ✅ **http-parser library is present and linked**
   - Library exists at `/opt/slurm/software/http-parser-2.9.4-apuomdv/lib/libhttp_parser.so.2.9.4`
   - Present in the RPATH of slurmstepd binary

3. ✅ **curl library is present and linked**
   - slurmd links to `/opt/slurm/software/curl-8.15.0-2ref7ue/lib/libcurl.so.4`

4. ✅ **libslurm_curl.so is being built manually**
   - Compiled from `slurm_curl.c` by the Spack package
   - Exports the required symbols: `slurm_curl_init`, `slurm_curl_fini`, `slurm_curl_request`
   ```bash
   $ nm -D /opt/slurm/software/lib/libslurm_curl.so | grep slurm_curl
   00000000000016d0 T slurm_curl_fini
   0000000000001640 T slurm_curl_init
   00000000000016e0 T slurm_curl_request
   ```

5. ❌ **influxdb plugin NOT linked against libslurm_curl.so**
   - Plugin was built BEFORE `libslurm_curl.so` was created
   - Plugin has undefined symbols at runtime:
   ```bash
   $ nm -D /opt/slurm/software/lib/slurm/acct_gather_profile_influxdb.so | grep ' U '
                    U slurm_curl_fini
                    U slurm_curl_init
                    U slurm_curl_request
   ```
   - No NEEDED entry for libslurm_curl.so in the plugin's ELF headers

## The Bug Location

In `slurm-factory-spack-repo.git`, file `packages/slurm/package.py`:

### Issue 1: Build Order Problem

The `install_curl_library()` method manually compiles `libslurm_curl.so` from the `slurm_curl.c` source file (which is a convenience library in Slurm's build system). However, the influxdb plugin was already built during the main Slurm build, **before** `libslurm_curl.so` existed.

```python
def install_curl_library(self):
    # ... compile slurm_curl.c into libslurm_curl.so ...
    # Create libslurm_curl.so.0 and libslurm_curl.so symlinks
    
    # ❌ PROBLEM: influxdb plugin was already built earlier
    # It has no knowledge of libslurm_curl.so at compile time
```

### Issue 2: Missing Linking Flags

Even after creating `libslurm_curl.so`, the influxdb plugin was never rebuilt with the proper LDFLAGS to link against it. The plugin needs:
- `-L{lib_dir}` to find the library directory
- `-lslurm_curl` to link against libslurm_curl.so
- `-Wl,-rpath,{lib_dir}` to embed the library path for runtime relocation

### Issue 3: Optional Variant Complexity

The `+influxdb` variant made the build conditional, but since we always want influxdb support, this added unnecessary complexity and potential for the plugin to be accidentally omitted.

## The Solution

We implemented a three-part fix in the `slurm-factory-spack-repo` repository:

### Part 1: Rebuild InfluxDB Plugin After libslurm_curl.so Creation

Modified `install_curl_library()` method in `packages/slurm/package.py`:

```python
def install_curl_library(self):
    # ... existing code to compile libslurm_curl.so ...
    
    # NEW: Rebuild influxdb plugin with proper linking
    plugin_dir = join_path(
        self.build_directory,
        "src/plugins/acct_gather_profile/influxdb"
    )
    
    if os.path.exists(plugin_dir):
        # Clean previous build artifacts
        make("-C", plugin_dir, "clean")
        
        # Rebuild with LDFLAGS to link against libslurm_curl.so
        ldflags = f"-L{lib_dir} -lslurm_curl -Wl,-rpath,{lib_dir}"
        make("-C", plugin_dir, f"LDFLAGS={ldflags}", "install")
```

**Result**: The influxdb plugin now:
- Has a `NEEDED` entry for `libslurm_curl.so.0` in its ELF headers
- Has an RPATH pointing to the Slurm lib directory
- Can resolve `slurm_curl_*` symbols at runtime

### Part 2: Remove +influxdb Variant

In `packages/slurm/package.py`:

```python
# REMOVED: variant("influxdb", default=False, ...)
# Added comment: "InfluxDB plugin is always built"

# SIMPLIFIED: Always include http-parser dependency
depends_on("http-parser")  # No longer conditional
```

In `slurm_factory/spack_yaml.py`:

```python
# REMOVED: "+influxdb" from default variant string
# Now just: "+readline +hwloc +pmix +hdf5 +kafka +restd +cgroup +pam"
```

**Result**: InfluxDB support is always enabled, eliminating conditional complexity.

### Part 3: Add zlib Dependency

In `slurm_factory/spack_yaml.py`:

```python
# Added to specs:
"zlib@1.3.1 %gcc@13.3.0"

# Added to view_packages:
"zlib"
```

**Result**: MySQL now has the required `libz.so.1` library (zlib-ng alone was insufficient).

## Verification

After applying the fix and rebuilding, we verified:

1. **Plugin is present in tarball**:
   ```bash
   $ tar -tzf slurm-25.05-software.tar.gz | grep acct_gather_profile_influxdb.so
   software/lib/slurm/acct_gather_profile_influxdb.so
   ```

2. **Plugin is linked against libslurm_curl.so**:
   ```bash
   $ readelf -d software/lib/slurm/acct_gather_profile_influxdb.so | grep NEEDED
   0x0000000000000001 (NEEDED)    Shared library: [libslurm_curl.so.0]
   0x0000000000000001 (NEEDED)    Shared library: [libhttp_parser.so.2]
   # ... other dependencies ...
   ```

3. **Plugin has proper RPATH**:
   ```bash
   $ readelf -d software/lib/slurm/acct_gather_profile_influxdb.so | grep RPATH
   0x000000000000000f (RPATH)     Library rpath: [/opt/slurm/software/slurm-25-05-.../lib:...]
   ```

4. **libslurm_curl.so exports required symbols**:
   ```bash
   $ nm -D software/lib/libslurm_curl.so | grep slurm_curl
   00000000000016d0 T slurm_curl_fini
   0000000000001640 T slurm_curl_init
   00000000000016e0 T slurm_curl_request
   ```

**Expected Runtime Behavior**: When the Lmod module is loaded, `LD_LIBRARY_PATH` will include the Slurm lib directory, and the plugin will successfully resolve all symbols from `libslurm_curl.so`.

## Commits

### In slurm-factory-spack-repo

- `6e948e4` - Add zlib dependency for MySQL libz.so.1 requirement
- `f586fd3` - Remove +influxdb variant, always build influxdb plugin
- `4a081aa` - Remove duplicate --with-libcurl configure args
- `bd381c1` - Fix influxdb plugin linking against libslurm_curl.so

### In slurm-factory

- `3ff527b` - Add zlib to spack packages
- `b66d73b` - Remove +influxdb from default variants

## Summary

The influxdb plugin failure was caused by a **build order and linking issue**. The plugin was built during the main Slurm build, before `libslurm_curl.so` was manually compiled, and it was never rebuilt with the proper LDFLAGS to link against the library.

The fix ensures:
1. `libslurm_curl.so` is compiled first (as before)
2. The influxdb plugin is **rebuilt** with LDFLAGS linking it to libslurm_curl.so
3. The plugin has proper RPATH for relocatable deployments
4. InfluxDB support is always enabled (no more optional variant)
5. All dependencies (zlib, http-parser, curl) are properly included

## Next Steps

1. ✅ Code changes committed to `fix_influx_plugin_deps` branch
2. ⏳ Test deployment in multipass instance to verify runtime functionality
3. ⏳ Merge `fix_influx_plugin_deps` branch to main
4. ⏳ Update documentation with influxdb configuration examples
