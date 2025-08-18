---
layout: home
title: "Slurm Factory - Modern HPC Cluster Builder"
description: "Build optimized Slurm packages using LXD containers and Spack package manager"
permalink: /
---

<div style="display: flex; justify-content: center; align-items: center; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap;">
  <img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/slurm-25.05-green.svg" alt="Slurm">
  <img src="https://img.shields.io/badge/platform-linux-lightgrey.svg" alt="Platform">
</div>
<div style="display: flex; justify-content: center; align-items: center; gap: 0.5rem; margin-bottom: 2rem; flex-wrap: wrap;">
  <img src="https://img.shields.io/github/contributors/vantagecompute/slurm-factory?logo=github&style=plastic" alt="Github Contributors">
  <img src="https://img.shields.io/github/issues-pr/vantagecompute/slurm-factory?label=pull-requests&logo=github&style=plastic" alt="Github Pull Requests">
  <img src="https://img.shields.io/github/issues/vantagecompute/slurm-factory?label=issues&logo=github&style=plastic" alt="Github Issues">
</div>

<div class="hero-section">
  <div style="display: flex; justify-content: center; align-items: center; gap: 4rem; margin-bottom: 2rem; flex-wrap: wrap;">
    <div style="display: flex; flex-direction: column; align-items: center; transform: scale(1.1);">
      <div style="background: #FFFFFF; padding: 20px; border-radius: 16px; box-shadow: 0 8px 25px rgba(107, 70, 193, 0.3); margin-bottom: 1rem; border: 2px solid #E5E7EB;">
        <img src="https://slurm.schedmd.com/slurm_logo.png" alt="Slurm Logo" style="width: 60px; height: 60px; object-fit: contain;">
      </div>
      <span style="font-size: 1rem; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Slurm HPC</span>
    </div>
    <div style="display: flex; align-items: center; justify-content: center;">
      <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #6B46C1, #9333EA); border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 15px rgba(107, 70, 193, 0.3);">
        <span style="color: white; font-size: 2rem; font-weight: 700; line-height: 1;">⚡</span>
      </div>
    </div>
    <div style="display: flex; flex-direction: column; align-items: center; transform: scale(1.1);">
      <div style="background: #FFFFFF; padding: 20px; border-radius: 16px; box-shadow: 0 8px 25px rgba(168, 85, 247, 0.3); margin-bottom: 1rem; border: 2px solid #E5E7EB;">
        <img src="https://raw.githubusercontent.com/spack/spack/develop/share/spack/logo/spack-logo.svg" alt="Spack Logo" style="width: 60px; height: 60px; object-fit: contain;">
      </div>
      <span style="font-size: 1rem; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Spack Packages</span>
    </div>
  </div>
  <h2 style="margin: 0; color: #111827; font-size: 2.5rem; font-weight: 800; margin-bottom: 1rem; background: linear-gradient(135deg, #6B46C1, #9333EA, #A855F7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">Slurm Factory Documentation</h2>
  <p style="margin: 0; color: #6B7280; font-size: 1.25rem; font-weight: 500; max-width: 600px; margin: 0 auto;">Relocatable HPC cluster builder with optimized caching and portable packages</p>
  <div style="margin-top: 2rem; display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
    <a href="#quick-start" style="background: linear-gradient(135deg, #6B46C1, #9333EA); color: white; padding: 1rem 2rem; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 1.1rem; box-shadow: 0 4px 15px rgba(107, 70, 193, 0.3); transition: all 0.2s ease; display: inline-block;">Get Started</a>
    <a href="https://github.com/vantagecompute/slurm-factory" style="background: white; color: #6B46C1; padding: 1rem 2rem; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 1.1rem; border: 2px solid #6B46C1; transition: all 0.2s ease; display: inline-block;">View on GitHub</a>
  </div>
</div>

Slurm Factory is a **modern Python CLI tool** built with Typer that automates the building of **relocatable** Slurm workload manager packages using LXD containers and the Spack package manager. It features a **modular architecture** with comprehensive exception handling, intelligent caching, and portable package generation for HPC environments.

## Key Features

- 🏗️ **Modern Architecture**: Built with Typer CLI framework and modular Python design
- 📦 **Relocatable Packages**: Runtime path configuration for cross-environment deployment
- ⚡ **Intelligent Caching**: Multi-layer build caching for ultra-fast rebuilds
- 🔧 **Exception Handling**: Comprehensive error management with custom exception hierarchy
- 🧪 **Tested**: 100% test coverage with 112 passing tests using proper LXD mocking
- 🚀 **GPU Support**: CUDA-enabled builds for GPU-accelerated workloads

## Quick Start {#quick-start}

### Installation

```bash
# Install from PyPI (recommended)
pip install slurm-factory

# Or install with pipx for isolation
pipx install slurm-factory

# Verify installation
slurm-factory --help
```

### Prerequisites

```bash
# Install and configure LXD
sudo snap install lxd
sudo lxd init
```

### Build Your First Relocatable Package
```bash
# Build latest Slurm with optimizations
slurm-factory build --slurm-version 25.05

# Build with GPU support
slurm-factory build --slurm-version 25.05 --gpu

# Build with custom configuration
slurm-factory build --slurm-version 25.05 --config-file custom.yaml

# Show available options
slurm-factory build --help
```

### Deploy Anywhere
```bash
# Standard deployment
sudo mkdir -p /opt/slurm
sudo tar -xzf ~/.slurm-factory/builds/slurm-25.05-software.tar.gz -C /opt/slurm/
sudo tar -xzf ~/.slurm-factory/builds/slurm-25.05-module.tar.gz -C /usr/share/lmod/lmod/modulefiles/

# Load with default path
module load slurm/25.05

# Or deploy to custom location  
sudo tar -xzf ~/.slurm-factory/builds/slurm-25.05-software.tar.gz -C /shared/apps/
export SLURM_INSTALL_PREFIX=/shared/apps/software
module load slurm/25.05
```

## Key Features

<div class="feature-grid">
  <div class="feature-card">
    <h3>� Relocatable Packages</h3>
    <p>Deploy the same package to any filesystem path using runtime environment variable overrides.</p>
  </div>
  
  <div class="feature-card">
    <h3>📦 Portable Packages</h3>
    <p>Self-contained software and module packages that deploy anywhere with compatible architecture.</p>
  </div>
  
  <div class="feature-card">
    <h3>🔧 Multiple Versions</h3>
    <p>Support for Slurm 25.05, 24.11, 24.05, 23.11, 23.02 with side-by-side installations.</p>
  </div>
  
  <div class="feature-card">
    <h3>⚡ Performance Optimized</h3>
    <p>CPU-specific optimizations with optional CUDA/GPU support for specialized workloads.</p>
  </div>
  
  <div class="feature-card">
    <h3>🛠 Modern Tech Stack</h3>
    <p>Python 3.11+ with UV package manager, LXD containers, and Spack integration.</p>
  </div>
  
  <div class="feature-card">
    <h3>📋 Module Integration</h3>
    <p>Automatic Environment Modules/Lmod configuration for easy deployment management.</p>
  </div>
</div>

## Use Cases

- **HPC Cluster Deployment**: Standardized Slurm installations across heterogeneous clusters
- **Development Environments**: Quick Slurm setup for testing and development
- **Multi-Version Support**: Running different Slurm versions side-by-side
- **Performance Testing**: Optimized builds for specific hardware configurations
- **Container Deployment**: Portable packages for containerized HPC environments

## Architecture Overview

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   slurm-factory │───▶│ LXD Container│───▶│ Spack Build     │
│   CLI Tool      │    │ (Ubuntu 24.04)│    │ Environment     │
└─────────────────┘    └──────────────┘    └─────────────────┘
                                                      │
                                                      ▼
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│ Target HPC      │◀───│ Portable     │◀───│ Optimized       │
│ Cluster         │    │ Packages     │    │ Slurm Build     │
└─────────────────┘    └──────────────┘    └─────────────────┘
```

## Package Information

| Build Type | Dependencies | Size | Build Time | Use Case |
|------------|-------------|------|------------|----------|
| **CPU-only** | ~45 packages | ~2-5GB | ~35 min | Production clusters |
| **GPU-enabled** | ~180 packages | ~15-25GB | ~75 min | GPU clusters |

## Documentation Structure

<div class="docs-nav">
  <div class="nav-section">
    <h3>Getting Started</h3>
    <ul>
      <li><a href="{{ site.baseurl }}/overview">Overview</a></li>
      <li><a href="{{ site.baseurl }}/installation">Installation Guide</a></li>
    </ul>
  </div>
  
  <div class="nav-section">
    <h3>Technical Details</h3>
    <ul>
      <li><a href="{{ site.baseurl }}/architecture">Architecture</a></li>
      <li><a href="{{ site.baseurl }}/api-reference">API Reference</a></li>
      <li><a href="{{ site.baseurl }}/troubleshooting">Troubleshooting</a></li>
    </ul>
  </div>
  
  <div class="nav-section">
    <h3>Guides</h3>
    <ul>
      <li><a href="{{ site.baseurl }}/deployment">Deployment Guide</a></li>
      <li><a href="{{ site.baseurl }}/optimization">Optimization Guide</a></li>
      <li><a href="{{ site.baseurl }}/contributing">Contributing</a></li>
      <li><a href="{{ site.baseurl }}/contact">Contact & Support</a></li>
    </ul>
  </div>
</div>

## Latest Features

- **Multi-Version Support**: Build and deploy Slurm versions 25.05, 24.11, 24.05, 23.11, 23.02
- **GPU Optimization**: Optional CUDA support for GPU-enabled HPC clusters  
- **Portable Packages**: Self-contained deployments with module system integration
- **Modern Architecture**: LXD containers with Spack package management
- **Performance Focused**: CPU-optimized builds with minimal package sizes

---

**Built with ❤️ by [Vantage Compute](https://vantagecompute.ai)**

<style>
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}

.feature-card {
  border: 1px solid #e1e4e8;
  border-radius: 8px;
  padding: 1.5rem;
  background: #f6f8fa;
  box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
  transition: all 0.3s cubic-bezier(.25,.8,.25,1);
}

.feature-card:hover {
  box-shadow: 0 14px 28px rgba(0,0,0,0.25), 0 10px 10px rgba(0,0,0,0.22);
  transform: translateY(-2px);
}

.feature-card h3 {
  margin-top: 0;
  color: #24292e;
  font-size: 1.2rem;
}

.feature-card p {
  color: #586069;
  margin-bottom: 0;
  line-height: 1.5;
}

.docs-nav {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  margin: 2rem 0;
  background: #f8f9fa;
  padding: 2rem;
  border-radius: 8px;
  border: 1px solid #e1e4e8;
}

.nav-section h3 {
  color: #24292e;
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.2rem;
  border-bottom: 2px solid #228B22;
  padding-bottom: 0.5rem;
}

.nav-section ul {
  list-style: none;
  padding-left: 0;
}

.nav-section li {
  margin: 0.5rem 0;
}

.nav-section a {
  text-decoration: none;
  color: #586069;
  font-weight: 500;
  transition: color 0.2s ease;
}

.nav-section a:hover {
  color: #228B22;
}
</style>

