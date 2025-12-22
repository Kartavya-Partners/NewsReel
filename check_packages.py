"""Verify all required packages are installed."""

import sys

packages_to_check = [
    'langgraph',
    'langchain',
    'langchain_community',
    'ollama',
    'feedparser',
    'requests',
    'bs4',  # beautifulsoup4
    'lxml',
    'PIL',  # Pillow
    'numpy',
    'streamlit',
    'pydantic',
    'yaml',  # pyyaml
    'loguru',
    'tqdm',
    'pandas',
]

print("=" * 60)
print("Checking Installed Packages")
print("=" * 60)

missing = []
installed = []

for package in packages_to_check:
    try:
        __import__(package)
        installed.append(package)
        print(f"✓ {package}")
    except ImportError:
        missing.append(package)
        print(f"✗ {package} - NOT INSTALLED")

print("\n" + "=" * 60)
print(f"Summary: {len(installed)}/{len(packages_to_check)} packages installed")
print("=" * 60)

if missing:
    print(f"\n❌ Missing packages: {', '.join(missing)}")
    print("\nRun: pip install " + " ".join(missing))
    sys.exit(1)
else:
    print("\n✅ All required packages are installed!")
    sys.exit(0)
