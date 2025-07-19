#!/usr/bin/env python3
"""
Test runner for LogBERT Hadoop RCA project.

This script provides a convenient way to run tests with different configurations.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description=""):
    """Run a command and handle errors."""
    if description:
        print(f"\n🔄 {description}")
    
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Success: {description}")
        if result.stdout:
            print(result.stdout)
    else:
        print(f"❌ Failed: {description}")
        if result.stderr:
            print(result.stderr)
        if result.stdout:
            print(result.stdout)
    
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run tests for LogBERT Hadoop RCA")
    parser.add_argument(
        "--type", 
        choices=["unit", "integration", "api", "ml", "performance", "all"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true",
        help="Include coverage report"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true", 
        help="Verbose output"
    )
    parser.add_argument(
        "--parallel", "-n",
        type=int,
        help="Number of parallel processes"
    )
    parser.add_argument(
        "--file",
        help="Run specific test file"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    
    # Add parallel processing
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    # Add coverage
    if args.coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing"
        ])
    
    # Add test type markers
    if args.type != "all":
        cmd.extend(["-m", args.type])
    
    # Add specific file
    if args.file:
        cmd.append(args.file)
    else:
        cmd.append("tests/")
    
    # Run the tests
    print("🧪 Running LogBERT Hadoop RCA Tests")
    print("=" * 50)
    
    success = run_command(cmd, f"Running {args.type} tests")
    
    if success:
        print("\n🎉 All tests passed!")
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    if project_root.name != "logbert_hadoop_rca":
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    main()
