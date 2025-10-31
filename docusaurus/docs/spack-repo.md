# Spack Repository Integration

Slurm Factory uses a custom Spack repository to provide specialized package definitions and patches for building optimized Slurm packages.

## vantagecompute/slurm-factory-spack-repo

The [vantagecompute/slurm-factory-spack-repo](https://github.com/vantagecompute/slurm-factory-spack-repo) repository contains custom Spack package recipes that are specifically designed for building relocatable, production-ready Slurm packages.

### Repository Purpose

This custom Spack repository provides:

1. **Custom Slurm Package** (`slurm_factory.slurm`)
   - Optimized build variants for HPC deployments
   - Patches for improved relocatability
   - Enhanced configuration options
   - Better integration with OpenMPI and PMIx

2. **Custom cURL Package** (`slurm_factory.curl`)
   - Additional protocol support (LDAP, RTMP, etc.)
   - Optimized for Slurm REST API requirements
   - Consistent TLS backend (OpenSSL)

3. **Build Optimizations**
   - CPU-specific optimizations (x86_64_v3 target)
   - Shared library preferences for smaller packages
   - RPATH configurations for relocatability

### How It's Used

Slurm Factory automatically:

1. **Clones the repository** during Docker container build
2. **Registers it with Spack** as a custom package source
3. **Uses the custom packages** when building Slurm
4. **Applies patches and variants** specific to relocatable builds

The integration happens transparently in the Dockerfile:

```dockerfile
# Clone custom Spack repository
RUN git clone https://github.com/vantagecompute/slurm-factory-spack-repo.git \
    /root/slurm-factory-spack-repo && \
    spack repo add /root/slurm-factory-spack-repo
```

### Package Namespacing

The custom packages use the `slurm_factory` namespace to avoid conflicts with upstream Spack packages:

- `slurm_factory.slurm` - Custom Slurm package
- `slurm_factory.curl` - Custom cURL package

This allows Spack to prefer our custom packages while still having access to all upstream packages.

### Key Differences from Upstream

| Aspect | Upstream Spack | slurm-factory-spack-repo |
|--------|----------------|---------------------------|
| **Relocatability** | Basic | Enhanced with RPATH fixes |
| **Variants** | Standard | Optimized for production |
| **Dependencies** | Flexible | Pinned for reproducibility |
| **GPU Support** | Optional | Tested with CUDA/ROCm |
| **OpenMPI Integration** | Basic | Enhanced PMIx support |
| **REST API** | Basic | Full LDAP/TLS support via custom curl |

### Package Maintenance

The custom Spack repository is maintained separately to:

- **Track Slurm releases** independently
- **Test patches** before applying to production builds
- **Contribute improvements** back to upstream Spack when appropriate
- **Maintain stability** across Slurm Factory versions

### Contributing

If you encounter issues with package builds or have improvements:

1. Check if the issue is in the [slurm-factory-spack-repo](https://github.com/vantagecompute/slurm-factory-spack-repo/issues)
2. Review the custom package definitions in `packages/`
3. Submit pull requests for improvements or fixes
4. Coordinate with Slurm Factory releases for compatibility

### Version Compatibility

| Slurm Factory | Spack Repo Branch | Spack Version |
|---------------|-------------------|---------------|
| 1.0.x         | main              | v1.0.0        |

## Related Documentation

- [Architecture](/slurm-factory/architecture/) - How Slurm Factory integrates components
- [Build Artifacts](/slurm-factory/build-artifacts/) - Output package structure
- [Contributing](/slurm-factory/contributing/) - How to contribute improvements
