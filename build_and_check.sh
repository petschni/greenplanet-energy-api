#!/bin/bash
set -e

echo "🔧 Running code quality checks..."

echo "📋 Running Black formatter..."
black src tests

echo "🔍 Running Ruff linter..."
ruff check src tests

echo "🔍 Running MyPy type checker..."
mypy src

echo "🧪 Running tests..."
pytest tests/ -v --cov=greenplanet_energy_api --cov-report=term-missing

echo "📦 Building package..."
python -m build

echo "✅ All checks passed! Package is ready for publishing."
echo ""
echo "To publish to PyPI:"
echo "1. Install twine: pip install twine"
echo "2. Upload to test PyPI: twine upload --repository testpypi dist/*"  
echo "3. Upload to PyPI: twine upload dist/*"
