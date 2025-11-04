# Slurm Factory Documentation

This directory contains technical documentation and implementation plans for the Slurm Factory project.

## Package Signing Implementation

### [BUILDCACHE_SIGNING_IMPLEMENTATION_PLAN.md](./BUILDCACHE_SIGNING_IMPLEMENTATION_PLAN.md)

Comprehensive 6-week implementation plan for adding GPG signing support to the buildcache. This document includes:

- **Background**: Current state and security risks of unsigned packages
- **Goals**: Security, trust, compliance, and transparency objectives
- **Implementation Phases**: Detailed breakdown of 6 phases over 6 weeks
- **Code Examples**: Sample implementations for all components
- **CI/CD Integration**: GitHub Actions and AWS configuration
- **Documentation**: User and developer guides
- **Testing Strategy**: Unit and integration tests
- **Transition Plan**: Gradual rollout approach
- **Security Considerations**: Key management and best practices
- **Success Metrics**: How to measure implementation success

**Status**: Planning phase  
**Priority**: High - addresses security vulnerabilities  
**Estimated Effort**: 6 weeks

### [SIGNING_QUICK_REFERENCE.md](./SIGNING_QUICK_REFERENCE.md)

Quick reference guide for implementing and using package signing. Includes:

- GPG key generation commands
- GitHub Secrets setup
- Code snippets for common tasks
- Spack GPG commands
- Testing procedures
- Troubleshooting tips
- Security checklists

**Use this for**: Quick lookups during implementation and debugging.

### [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md)

Detailed roadmap of all code changes needed for signing implementation. Includes:

- Complete list of files to create/modify
- Line-by-line change specifications
- Code snippets for each modification
- GitHub workflow updates
- Test coverage requirements
- Summary statistics and effort estimates

**Use this for**: Tracking implementation progress and code review.

## Project Documentation

For user-facing documentation, see the [docusaurus](../docusaurus/) directory which contains:

- Installation guides
- API reference
- Architecture overview
- Deployment instructions
- Examples and tutorials
- Troubleshooting guides

## Contributing

When adding new documentation to this directory:

1. Use clear, descriptive filenames (e.g., `FEATURE_IMPLEMENTATION_PLAN.md`)
2. Include a summary in this README
3. Link related documents
4. Update the project's main README if needed
5. Follow the existing document structure and formatting

## Document Organization

```
docs/
├── README.md                                    # This file
├── BUILDCACHE_SIGNING_IMPLEMENTATION_PLAN.md   # Signing implementation plan (778 lines)
├── SIGNING_QUICK_REFERENCE.md                  # Signing quick reference (290 lines)
└── IMPLEMENTATION_ROADMAP.md                   # Code changes roadmap (327 lines)
```

## See Also

- [Main README](../README.md) - Project overview and quick start
- [Docusaurus Docs](../docusaurus/docs/) - User-facing documentation
- [Contributing Guide](../docusaurus/docs/contributing.md) - How to contribute
- [Architecture](../docusaurus/docs/architecture.md) - System architecture
