import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import * as fs from 'fs';
import * as path from 'path';

// Function to read version from pyproject.toml
function getVersionFromPyproject(): string {
  try {
    const pyprojectPath = path.join(__dirname, '../pyproject.toml');
    const content = fs.readFileSync(pyprojectPath, 'utf8');
    
    // Extract version using regex
    const versionMatch = content.match(/^version\s*=\s*["']([^"']+)["']/m);
    
    if (versionMatch) {
      return versionMatch[1];
    }
    
    throw new Error('Version not found in pyproject.toml');
  } catch (error) {
    console.error('Error reading version from pyproject.toml:', error);
    return '0.0.0'; // fallback version
  }
}

const projectVersion = getVersionFromPyproject();

const config: Config = {
  title: 'Slurm Factory',
  tagline: `Modern HPC cluster builder using Docker and Spack (v${projectVersion})`,
  favicon: 'img/favicon.ico',

  url: 'https://vantagecompute.github.io',
  baseUrl: '/slurm-factory/',

  organizationName: 'vantagecompute',
  projectName: 'slurm-factory',
  deploymentBranch: 'main',
  trailingSlash: false,

  onBrokenLinks: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },
  markdown: {
    format: 'detect',
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'warn'
    }
  },
  themes: ['@docusaurus/theme-mermaid'],
  presets: [
    [
      'classic',
      {
        docs: {
          path: './docs',
          routeBasePath: '/',
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/vantagecompute/slurm-factory/tree/main/docs/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      },
    ],
  ],
  plugins: [
    [ 
      'docusaurus-plugin-llms',
      {
        // Options here
        generateLLMsTxt: true,
        generateLLMsFullTxt: true,
        docsDir: 'docs',
        ignoreFiles: ['advanced/*', 'private/*'],
        title: 'Slurm Factory Documentation',
          description: 'Complete documentation for building relocatable Slurm packages.',
          includeBlog: false,
          // Content cleaning options
          excludeImports: true,
          removeDuplicateHeadings: true,
          // Generate individual markdown files following llmstxt.org specification
          generateMarkdownFiles: true,
          // Control documentation order
          includeOrder: [],
          includeUnmatchedLast: true,
          // Path transformation options
          pathTransformation: {
            // Paths to ignore when constructing URLs (will be removed if found)
            ignorePaths: ['docs'],
            // Paths to add when constructing URLs (will be prepended if not already present)
            // addPaths: ['api'],
          },
          // Custom LLM files for specific documentation sections
          customLLMFiles: [
            {
              filename: 'llms-index.txt',
              includePatterns: ['docs/index.md'],
              fullContent: true,
              title: 'Slurm Factory Documentation Index and Overview',
              description: 'Complete index and overview reference for Slurm Factory'
            },
            {
              filename: 'llms-installation.txt',
              includePatterns: ['docs/installation.md'],
              fullContent: true,
              title: 'Slurm Factory Tool Installation Documentation',
              description: 'Installation documentation for the slurm-factory build tool'
            },
            {
              filename: 'llms-installing-slurm-from-buildcache.txt',
              includePatterns: ['docs/installing-slurm-from-buildcache.md'],
              fullContent: true,
              title: 'Installing Slurm from Buildcache Documentation',
              description: 'Guide for installing pre-built Slurm binaries from the public buildcache using Spack'
            },
            {
              filename: 'llms-installing-slurm-from-tarball.txt',
              includePatterns: ['docs/installing-slurm-from-tarball.md'],
              fullContent: true,
              title: 'Installing Slurm from Tarball Documentation',
              description: 'Guide for installing pre-built Slurm tarball artifacts'
            },
            {
              filename: 'llms-deployment.txt',
              includePatterns: ['docs/deployment.md'],
              fullContent: true,
              title: 'Slurm Factory Deployment Documentation',
              description: 'Deployment documentation for Slurm Factory'
            },
            {
              filename: 'llms-architecture.txt',
              includePatterns: ['docs/architecture.md'],
              fullContent: true,
              title: 'Slurm Factory Architecture Documentation',
              description: 'Architecture documentation for Slurm Factory'
            },
            {
              filename: 'llms-contributing.txt',
              includePatterns: ['docs/contributing.md'],
              fullContent: true,
              title: 'Slurm Factory Contributing Documentation',
              description: 'Contributing documentation for Slurm Factory'
            },
            {
              filename: 'llms-troubleshooting.txt',
              includePatterns: ['docs/troubleshooting.md'],
              fullContent: true,
              title: 'Slurm Factory Troubleshooting Documentation',
              description: 'Troubleshooting documentation for Slurm Factory'
            },
            {
              filename: 'llms-contact.txt',
              includePatterns: ['docs/contact.md'],
              fullContent: true,
              title: 'Slurm Factory Contact Documentation',
              description: 'Contact documentation for Slurm Factory'
            },
            {
              filename: 'llms-api-reference.txt',
              includePatterns: ['docs/api-reference.md'],
              fullContent: true,
              title: 'Slurm Factory API Reference Documentation',
              description: 'API reference documentation for Slurm Factory'
            },
            {
              filename: 'llms-build-artifacts.txt',
              includePatterns: ['docs/build-artifacts.md'],
              fullContent: true,
              title: 'Slurm Factory Build Artifacts Documentation',
              description: 'Build artifacts documentation for Slurm Factory'
            },
            {
              filename: 'llms-examples.txt',
              includePatterns: ['docs/examples.md'],
              fullContent: true,
              title: 'Slurm Factory Examples Documentation',
              description: 'Examples documentation for Slurm Factory'
            },
            {
              filename: 'llms-optimization.txt',
              includePatterns: ['docs/optimization.md'],
              fullContent: true,
              title: 'Slurm Factory Optimization Documentation',
              description: 'Optimization documentation for Slurm Factory'
            },
            {
              filename: 'llms-spack-repo.txt',
              includePatterns: ['docs/spack-repo.md'],
              fullContent: true,
              title: 'Slurm Factory Spack Repository Documentation',
              description: 'Spack repository documentation for Slurm Factory'
            },
            {
              filename: 'llms-slurm-factory-spack-build-cache.txt',
              includePatterns: ['docs/slurm-factory-spack-build-cache.md'],
              fullContent: true,
              title: 'Slurm Factory Spack Build Cache Documentation',
              description: 'Spack build cache documentation for Slurm Factory'
            },
            {
              filename: 'llms-infrastructure.txt',
              includePatterns: ['docs/infrastructure.md'],
              fullContent: true,
              title: 'Slurm Factory Infrastructure Documentation',
              description: 'Infrastructure documentation for Slurm Factory'
            },
            {
              filename: 'llms-github-actions.txt',
              includePatterns: ['docs/github-actions.md'],
              fullContent: true,
              title: 'Slurm Factory GitHub Actions Documentation',
              description: 'GitHub Actions CI/CD documentation for Slurm Factory'
            },
          ],
        },
    ],
  ],

  customFields: {
    projectVersion: projectVersion,
  },

  themeConfig: {
    navbar: {
      title: `Slurm Factory Documentation v${projectVersion}`,
      logo: {
        alt: 'Vantage Compute Logo',
        src: 'https://vantage-compute-public-assets.s3.us-east-1.amazonaws.com/branding/vantage-logo-text-white-horz.png',
        srcDark: 'https://vantage-compute-public-assets.s3.us-east-1.amazonaws.com/branding/vantage-logo-text-white-horz.png',
        href: 'https://vantagecompute.github.io/slurm-factory/',
        target: '_self',
      },
      items: [
        {
          href: 'https://pypi.org/project/slurm-factory/',
          label: 'PyPI',
          position: 'right',
          className: 'pypi-button',
        },
        {
          href: 'https://github.com/vantagecompute/slurm-factory',
          label: 'GitHub',
          position: 'right',
          className: 'github-button',
        },
      ],
    },
    footer: {
      style: 'dark',
      logo: {
        alt: 'Vantage Compute Logo',
        src: 'https://vantage-compute-public-assets.s3.us-east-1.amazonaws.com/branding/vantage-logo-text-white-horz.png',
        href: 'https://vantagecompute.ai',
      },
      links: [
        {
          title: 'Documentation',
          items: [
            {
              label: 'Getting Started',
              to: '/',
            },
            {
              label: 'Installation',
              to: '/installation',
            },
            {
              label: 'Examples',
              to: '/examples',
            },
            {
              label: 'Deployment',
              to: '/deployment',
            },
            {
              label: 'Optimization',
              to: '/optimization',
            },
            {
              label: 'Architecture',
              to: '/architecture',
            },
            {
              label: 'API Reference',
              to: '/api-reference',
            },
          ],
        },

        {
          title: 'Community',
          items: [
            {
              label: 'GitHub Discussions',
              href: 'https://github.com/vantagecompute/slurm-factory/discussions',
            },
            {
              label: 'Issues',
              href: 'https://github.com/vantagecompute/slurm-factory/issues',
            },
            {
              label: 'Support',
              href: 'https://vantagecompute.ai/support',
            },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/vantagecompute/slurm-factory',
            },
            {
              label: 'Vantage Compute',
              href: 'https://vantagecompute.ai',
            },
            {
              label: 'PyPI',
              href: 'https://pypi.org/project/slurm-factory/',
            },
          ],
        },
      ],
      copyright: 'Copyright &copy; ' + new Date().getFullYear() + ' Vantage Compute.',
    },
    prism: {
    // dracula
    // duotoneDark
    // duotoneLight
    // github
    // gruvboxMaterialDark
    // gruvboxMaterialLight
    // jettwaveDark
    // jettwaveLight
    // nightOwl
    // nightOwlLight
    // oceanicNext
    // okaidia
    // oneDark
    // oneLight
    // palenight
    // shadesOfPurple
    // synthwave84
    // ultramin
    // vsDark
    // vsLight
      theme: prismThemes.vsLight,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['shell-session', 'python', 'bash'],
    },
    tableOfContents: {
      minHeadingLevel: 2,
      maxHeadingLevel: 5,
    },
  },
};

export default config;
