#!/bin/bash
set -e

echo "🧹 Running all quality checks..."

echo "📦 Installing development dependencies..."
pip install -e ".[dev]"

echo "🔧 Running black formatting..."
python -m black src/ tests/

echo "📋 Running ruff linting..."
python -m ruff check src/ tests/ --fix

echo "🔍 Running mypy type checking..."
python -m mypy src/

echo "🧪 Running tests with coverage..."
python -m pytest tests/ -v --cov=src/greenplanet_energy_api --cov-report=term-missing

echo "📦 Testing package build..."
python -m build

echo "✅ Validating package..."
python -m twine check dist/*

echo ""
echo "🎉 All checks passed! Ready to push to GitHub."
echo ""
echo "To push changes:"
echo "  git add ."
echo "  git commit -m 'Your commit message'"
echo "  git push origin main"
