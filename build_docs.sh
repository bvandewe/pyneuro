#!/bin/bash

# MkDocs Build Script with Mermaid Support
# This script builds the Neuroglia Python Framework documentation with Mermaid diagrams

set -e

echo "🚀 Building Neuroglia Python Framework Documentation"
echo "=================================================="

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [[ ! -f "mkdocs.yml" ]]; then
    print_error "mkdocs.yml not found. Please run this script from the project root."
    exit 1
fi

print_status "Checking Poetry environment..."
if ! command -v poetry &> /dev/null; then
    print_error "Poetry is not installed. Please install Poetry first."
    exit 1
fi

print_status "Installing/updating dependencies..."
poetry install

print_status "Checking MkDocs and Mermaid plugin..."
if poetry run python -c "import mkdocs_mermaid2_plugin" 2>/dev/null; then
    print_success "MkDocs Mermaid plugin is available"
else
    print_error "MkDocs Mermaid plugin not found. Installing..."
    poetry add mkdocs-mermaid2-plugin
fi

print_status "Validating Mermaid diagrams in documentation..."
MERMAID_COUNT=$(find docs -name "*.md" -exec grep -l '```mermaid' {} \; | wc -l)
print_status "Found Mermaid diagrams in $MERMAID_COUNT documentation files"

print_status "Building documentation site..."
poetry run mkdocs build --clean

if [[ $? -eq 0 ]]; then
    print_success "Documentation built successfully!"
    
    # Check if site directory was created
    if [[ -d "site" ]]; then
        HTML_COUNT=$(find site -name "*.html" | wc -l)
        print_success "Generated $HTML_COUNT HTML files in ./site directory"
        
        # Check for Mermaid content in generated files
        MERMAID_HTML_COUNT=$(find site -name "*.html" -exec grep -l 'mermaid' {} \; | wc -l)
        if [[ $MERMAID_HTML_COUNT -gt 0 ]]; then
            print_success "Mermaid diagrams detected in $MERMAID_HTML_COUNT HTML files"
        else
            print_warning "No Mermaid content detected in generated HTML files"
        fi
    else
        print_error "Site directory was not created"
        exit 1
    fi
    
    print_status "Documentation is ready for deployment!"
    echo ""
    echo "📁 Site files: ./site/"
    echo "🌐 To serve locally: poetry run mkdocs serve"
    echo "🚀 To deploy: poetry run mkdocs gh-deploy (if using GitHub Pages)"
    
else
    print_error "Documentation build failed!"
    exit 1
fi

echo ""
print_success "Build completed successfully! 🎉"
