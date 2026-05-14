# RDKit Sidecar Service
**Al-Zamzami Molecular Twin v7.2 - Molecular Geometry Generation**

Production-grade REST API for 3D molecular conformer generation using RDKit.

---

## 🎯 Purpose

This service provides the **external Python RDKit sidecar** referenced in the 
Al-Zamzami Molecular Twin architecture. It implements:

- **ETKDG** conformer generation (Riniker & Landrum 2015, DOI: 10.1021/acs.jcim.5b00654)
- **MMFF94** force field minimization (Halgren 1996, DOI: 10.1002/(SICI)1096-987X)
- **UFF** universal force field

The Lovable frontend uses **RDKit-WASM** (JavaScript) for 2D depiction and basic 
SMILES operations. This sidecar handles the computationally intensive 3D geometry 
tasks that require full RDKit.

---

## 📦 Files Included

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage production Docker image |
| `app.py` | FastAPI REST API with `/full`, `/2d`, `/3d` endpoints |
| `geometry.py` | Scientific core - ETKDG/MMFF94 implementation |
| `validation.py` | Input validation per OpenSMILES spec |
| `requirements.txt` | Python dependencies (pinned versions) |

---

## 🚀 Deployment to Railway

### Prerequisites
1. GitHub account
2. Railway account (https://railway.app)
3. This repository pushed to GitHub

### Steps

**1. Push to GitHub**
```bash
git init
git add .
git commit -m "Initial commit: RDKit sidecar service v7.2"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/rdkit-sidecar-service.git
git push -u origin main
