# typed: false
# frozen_string_literal: true

# Atlas CLI Homebrew Formula
class AtlasCli < Formula
  desc "Atlas CLI - Command-line interface for Atlas AI (thor-1.1 model)"
  homepage "https://github.com/yourusername/atlas-ai"
  url "https://github.com/yourusername/atlas-ai/archive/v0.1.0.tar.gz"
  sha256 ""  # Update with actual SHA256 from release tarball
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
