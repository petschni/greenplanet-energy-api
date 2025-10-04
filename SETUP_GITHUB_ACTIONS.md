# GitHub Actions Setup für greenplanet-energy-api

## Was du manuell konfigurieren musst:

### 1. PyPI Trusted Publishing (EMPFOHLEN)

1. **PyPI Account erstellen/einloggen**: https://pypi.org/
2. **Erstelle das Paket einmalig manuell**:
   ```bash
   python -m build
   python -m twine upload dist/*
   ```
3. **Trusted Publishing konfigurieren**:
   - Gehe zu deinem Projekt auf PyPI: https://pypi.org/project/greenplanet-energy-api/
   - Klicke "Manage" → "Publishing"
   - "Add a new pending publisher"
   - Fülle aus:
     - **Repository name**: `petschni/greenplanet-energy-api`
     - **Workflow filename**: `publish.yml`
     - **Environment**: `pypi`

### 2. GitHub Environment erstellen

1. **Gehe zu**: https://github.com/petschni/greenplanet-energy-api/settings/environments
2. **New environment** → Name: `pypi`
3. **Optional**: Protection rules hinzufügen

### 3. SSH Key Problem lösen

Falls `git push` fehlschlägt:

```bash
# SSH Key testen
ssh -T git@github.com

# Falls das fehlschlägt, SSH Key hinzufügen:
cat ~/.ssh/id_rsa.pub
# Kopiere den Output und füge ihn zu GitHub hinzu:
# https://github.com/settings/ssh/new

# Oder verwende HTTPS statt SSH:
git remote set-url origin https://github.com/petschni/greenplanet-energy-api.git
```

### 4. Erste Commits pushen

```bash
git add .
git commit -m "Add GitHub Actions for PyPI publishing"
git push origin main
```

### 5. Wie es funktioniert

- **Push auf main**: Tests laufen, bei neuer Version wird published
- **Pull Requests**: Nur Tests, kein Publishing
- **Manual**: Über GitHub UI mit Force-Publish

## Quick Test:

1. Version in `pyproject.toml` ändern (z.B. `0.1.0` → `0.1.1`)
2. `git add . && git commit -m "Bump version" && git push`
3. GitHub Actions sollte automatisch laufen

## Troubleshooting:

- **Push fehlschlägt**: SSH Key Problem (siehe oben)
- **PyPI Upload fehlschlägt**: Trusted Publishing nicht konfiguriert
- **Tests fehlschlagen**: Dependencies installieren und lokal testen
