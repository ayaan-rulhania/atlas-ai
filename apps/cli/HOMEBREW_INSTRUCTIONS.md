# Homebrew Installation Instructions for Atlas CLI

This guide explains how to publish and install the Atlas CLI via Homebrew.

## Prerequisites

1. **GitHub Repository**: Your code should be in a GitHub repository
2. **GitHub Releases**: You'll need to create releases with versioned tarballs
3. **Homebrew**: You'll need Homebrew installed on your system

## Step-by-Step Guide

### 1. Prepare Your Release

First, create a versioned release tarball:

```bash
# From the project root
cd /Users/arulhania/Coding/atlas-ai

# Create a release directory
mkdir -p releases
cd releases

# Create a clean tarball (exclude git, pycache, etc.)
tar -czf atlas-cli-0.1.0.tar.gz \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='node_modules' \
    --exclude='.venv*' \
    --exclude='*.egg-info' \
    --exclude='dist' \
    --exclude='build' \
    ../apps/cli/* \
    ../setup.py
```

### 2. Create a GitHub Release

1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"
3. Tag version: `v0.1.0`
4. Release title: `Atlas CLI v0.1.0`
5. Upload the tarball: `atlas-cli-0.1.0.tar.gz`
6. Publish the release

### 3. Get the SHA256 Hash

After uploading, get the SHA256 hash of your tarball:

```bash
shasum -a 256 atlas-cli-0.1.0.tar.gz
```

Or if you download from GitHub:
```bash
curl -L https://github.com/YOUR_USERNAME/YOUR_REPO/releases/download/v0.1.0/atlas-cli-0.1.0.tar.gz | shasum -a 256
```

### 4. Update the Homebrew Formula

Update `config/Formula/atlas-cli.rb`:

```ruby
# typed: false
# frozen_string_literal: true

# Atlas CLI Homebrew Formula
class AtlasCli < Formula
  desc "Atlas CLI - Command-line interface for Atlas AI (thor-1.1 model)"
  homepage "https://github.com/YOUR_USERNAME/YOUR_REPO"
  url "https://github.com/YOUR_USERNAME/YOUR_REPO/releases/download/v0.1.0/atlas-cli-0.1.0.tar.gz"
  sha256 "YOUR_SHA256_HASH_HERE"  # Replace with actual SHA256
  license "MIT"
  version "0.1.0"

  depends_on "python@3.11"

  def install
    python3 = Formula["python@3.11"].opt_bin/"python3.11"
    
    # Change to the directory containing setup.py
    cd buildpath do
      # Install the package and its dependencies
      system python3, "-m", "pip", "install", *std_pip_args, "."
    end
  end

  test do
    # Test that atlas-cli is installed and shows help
    output = shell_output("#{bin}/atlas-cli --help 2>&1", 1)
    assert_match "Atlas CLI", output
  end
end
```

**Important**: Replace:
- `YOUR_USERNAME` with your GitHub username
- `YOUR_REPO` with your repository name
- `YOUR_SHA256_HASH_HERE` with the actual SHA256 hash

### 5. Create a Homebrew Tap (Option 1 - Recommended for Testing)

A tap is your own Homebrew repository for formulas:

```bash
# Create a new tap repository on GitHub
# Repository name should be: homebrew-tap (or homebrew-<name>)

# Clone it locally
mkdir -p ~/homebrew-tap
cd ~/homebrew-tap
git init
git remote add origin https://github.com/YOUR_USERNAME/homebrew-tap.git

# Copy your formula
cp /Users/arulhania/Coding/atlas-ai/config/Formula/atlas-cli.rb Formula/

# Commit and push
git add Formula/atlas-cli.rb
git commit -m "Add atlas-cli formula"
git branch -M main
git push -u origin main
```

### 6. Install from Your Tap

Users can install from your tap:

```bash
brew tap YOUR_USERNAME/tap
brew install atlas-cli
```

### 7. Submit to Homebrew Core (Option 2 - For Public Distribution)

If you want to submit to official Homebrew:

1. **Fork Homebrew/homebrew-core**: 
   ```bash
   # Fork https://github.com/Homebrew/homebrew-core on GitHub
   ```

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/homebrew-core.git
   cd homebrew-core
   ```

3. **Add formula**:
   ```bash
   cp /Users/arulhania/Coding/atlas-ai/config/Formula/atlas-cli.rb Formula/atlas-cli.rb
   ```

4. **Test locally**:
   ```bash
   brew install --build-from-source ./Formula/atlas-cli.rb
   ```

5. **Create pull request**:
   ```bash
   git checkout -b atlas-cli
   git add Formula/atlas-cli.rb
   git commit -m "atlas-cli 0.1.0"
   git push origin atlas-cli
   ```

6. **Open PR on GitHub**: Go to your fork and create a pull request

**Note**: Homebrew Core has strict requirements:
- Must have at least 75 GitHub stars OR significant user base
- Must be notable software (not just a personal tool)
- Must have been stable for at least 30 days
- Must meet Homebrew's contribution guidelines

## Alternative: Install from Local Formula

For testing without publishing:

```bash
brew install --build-from-source /Users/arulhania/Coding/atlas-ai/config/Formula/atlas-cli.rb
```

## Testing Your Formula

Before publishing, test it:

```bash
# Install from local formula
brew install --build-from-source ./config/Formula/atlas-cli.rb

# Test the installation
atlas-cli --help

# Uninstall to test again
brew uninstall atlas-cli
```

## Updating Versions

When releasing a new version:

1. Update version in `setup.py` and `__init__.py`
2. Create new release tarball
3. Update `url` and `sha256` in formula
4. Update `version` in formula
5. Push to tap/repository

## Troubleshooting

### "No such file or directory" errors

Make sure your tarball includes all necessary files (check with `tar -tzf atlas-cli-0.1.0.tar.gz`).

### Python version issues

The formula specifies `python@3.11`. If you need a different version, update the `depends_on` line.

### Installation fails

Check the Homebrew logs:
```bash
brew install atlas-cli --verbose --debug
```

## Quick Reference

```bash
# Install from tap
brew tap YOUR_USERNAME/tap
brew install atlas-cli

# Or install directly from URL
brew install YOUR_USERNAME/tap/atlas-cli

# Uninstall
brew uninstall atlas-cli

# Update
brew update
brew upgrade atlas-cli
```
