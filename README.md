# RDKit Sidecar Service
**Al-Zamzami Molecular Twin v7.2**

Production-ready REST API for 3D molecular geometry generation using RDKit.

---

## Overview

This service provides the **Python RDKit sidecar** for the Al-Zamzami Molecular Twin architecture.

### Architecture
- **Lovable frontend** → RDKit-WASM (JavaScript) for 2D depiction and basic SMILES operations
- **Railway sidecar** → Full RDKit (Python) for 3D conformer generation and force-field optimization

### Scientific methods
- **ETKDG v3** for conformer generation
- **MMFF94** for force-field optimization
- **UFF** as fallback when MMFF94 is not applicable

This design keeps lightweight chemistry tasks inside Lovable and moves heavier 3D computation to the Python sidecar.[file:1089][file:968]

---

## Files Structure

```text
rdkit-sidecar-service/
├── Dockerfile
├── requirements.txt
├── app.py
├── README.md
└── .gitignore
