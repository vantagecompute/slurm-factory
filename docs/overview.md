---
layout: default
title: Overview
nav_order: 1
permalink: /overview/
---

# Slurm Factory Overview

Slurm Factory is a modern Python CLI tool that automates building optimized, portable Slurm workload manager packages using LXD containers and the Spack package manager.

## What is Slurm Factory?

Slurm Factory simplifies the complex process of building and packaging Slurm for HPC environments by:

- **Automating the build process** with one-command package creation
- **Creating portable packages** that can be deployed across different HPC clusters
- **Optimizing performance** with CPU-specific optimizations using Spack
- **Ensuring reproducibility** through container isolation
- **Supporting multiple versions** of Slurm (25.05, 24.11, 23.11, 23.02)

## Key Benefits

- **Simplified Deployment**: No more manual compilation and dependency management
- **Consistency**: Same packages work across different environments
- **Speed**: Intelligent caching makes rebuilds ultra-fast
- **Optimization**: Packages are optimized for your specific hardware
- **Reliability**: Container isolation ensures reproducible builds

## Use Cases

- **Research Computing Centers**: Standardize Slurm deployments across multiple clusters
- **Cloud HPC Providers**: Rapidly provision clusters with consistent software stacks
- **Educational Institutions**: Provide reproducible HPC environments for teaching
- **Industry HPC**: Deploy compliance-ready solutions with full audit trails

## Next Steps

- [Installation Guide](/slurm-factory/installation/) - Get started with Slurm Factory
- [Architecture](/slurm-factory/architecture/) - Learn how it works under the hood
- [API Reference](/slurm-factory/api-reference/) - Complete CLI documentation
