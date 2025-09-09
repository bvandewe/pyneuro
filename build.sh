# This script is used by the Cisco Jenkins Build env
# to build a Python package using Poetry from inside a Docker container.

# Install Python and Poetry
yum install -y python3 python3-pip
pip3 install poetry

# Show versions
python3 --version
poetry --version

# Install dependencies and build the package
poetry install --no-root
poetry build

# Artifacts will be in dist/
