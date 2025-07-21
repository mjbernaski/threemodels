#!/usr/bin/env python3
"""
Setup script for Python dependencies
"""
import subprocess
import sys
import os


def main():
    """Setup the Python environment"""
    print("Setting up Three Models Python environment...")
    
    # Check if virtual environment exists
    if not os.path.exists('venv'):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
        print("✓ Virtual environment created")
    
    # Install dependencies
    print("Installing dependencies...")
    if os.name == 'nt':  # Windows
        activate_script = 'venv\\Scripts\\activate'
        pip_cmd = 'venv\\Scripts\\pip'
    else:  # Unix/Linux/macOS
        activate_script = 'venv/bin/activate'
        pip_cmd = 'venv/bin/pip'
    
    subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt'], check=True)
    print("✓ Dependencies installed")
    
    print("\nSetup complete!")
    print("\nTo run the application:")
    print("1. Activate the virtual environment:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("2. Run the application:")
    print("   python run.py")
    print("\nOr use the provided run scripts.")


if __name__ == '__main__':
    main()