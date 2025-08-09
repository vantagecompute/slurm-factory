---
layout: default
title: Examples
nav_order: 8
permalink: /examples/
---

# Slurm Factory Examples

This page contains examples demonstrating how to use Slurm Factory for various HPC deployment scenarios.

## Examples Coming Soon

We're working on adding comprehensive examples for:

- **Basic Slurm Cluster**: Simple single-node setup
- **Multi-node Cluster**: Distributed Slurm deployment
- **Custom Spack Packages**: Building specialized HPC software
- **Performance Optimization**: Tuning for specific workloads
- **Integration Examples**: Using with existing infrastructure

## Contributing Examples

Have a useful Slurm Factory example? We'd love to include it! Please see our [Contributing Guide](/slurm-factory/contributing/) for details on how to submit examples.

## Quick Start Examples

For basic usage examples, check out the main documentation:
- [Installation Guide](/slurm-factory/installation/)
- [Architecture Overview](/slurm-factory/architecture/)
- [API Reference](/slurm-factory/api-reference/)

## Basic Usage

### Building Latest Slurm
```bash
# Build latest Slurm (CPU-optimized)
slurm-factory build
```

### Building Specific Version
```bash
# Build specific version with GPU support
slurm-factory build --slurm-version 24.11 --gpu
```

### Verbose Output
```bash
# Build with verbose output
slurm-factory --verbose build
```

### Deployment Example
```bash
# Extract software package on target system
sudo tar -xzf ~/.slurm-factory/builds/25.05/slurm-25.05-software.tar.gz -C /opt/

# Extract module files
sudo tar -xzf ~/.slurm-factory/builds/25.05/slurm-25.05-module.tar.gz -C /usr/share/lmod/

# Load the module
module load slurm/25.05
```

For more detailed examples and tutorials, please refer to our [main documentation](/slurm-factory/).
