---
layout: default
title: Installation Guide
nav_order: 2
permalink: /installation/
---

# Installation Guide

This guide covers the different ways to install and set up Slurm Factory for building optimized Slurm packages.

## Prerequisites

Before installing Slurm Factory, you need to have LXD installed and configured:

```bash
# Install LXD
sudo snap install lxd

# Initialize LXD (follow the prompts)
sudo lxd init
```

## Installation Methods

### Option 1: Install from PyPI (Recommended)

The easiest way to install Slurm Factory is from PyPI using pip:

```bash
# Install slurm-factory from PyPI
pip install slurm-factory

# Verify installation
slurm-factory --help
```

### Option 2: Install with pipx (Isolated Environment)

For an isolated installation that doesn't interfere with your system Python:

```bash
# Install pipx if you don't have it
pip install pipx

# Install slurm-factory with pipx
pipx install slurm-factory

# Verify installation
slurm-factory --help
```

### Option 3: Install from Source

For development or to get the latest features:

```bash
# Install UV (modern Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/vantagecompute/slurm-factory.git
cd slurm-factory

# Install dependencies and activate environment
uv sync

# Run slurm-factory
uv run slurm-factory --help
```

## Quick Start

Once installed, you can immediately start building Slurm packages:

```bash
# Build latest Slurm (CPU-optimized)
slurm-factory build

# Build with GPU support
slurm-factory build --gpu

# Build specific version
slurm-factory build --slurm-version 24.11
```

## Next Steps

- See the [Architecture Overview](/slurm-factory/architecture/) to understand how Slurm Factory works
- Check out [Examples](/slurm-factory/examples/) for common usage patterns
- Review [Deployment Guide](/slurm-factory/deployment/) for installing built packages
