"""
RDKit Sidecar Service - Single-file edition
Al-Zamzami Molecular Twin v7.2

This file merges:
- validation.py
- geometry.py
- app.py
for easier manual upload to GitHub/Railway.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Optional, Literal, Dict
from datetime import datetime
import logging
import sys
import re

from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class SMILESInput(BaseModel):
    smiles: str = Field(..., min_length=1, max_length=2048)

    @field_validator("smiles")
    @classmethod
    def validate_smiles_charset(cls, v: str) -> str:
        allowed_pattern = r'^[A-Za-z0-9@+-[]()=#$:/\\.*%]+$'
        if not re.match(allowed_pattern, v):
            raise ValueError("SMILES contains invalid characters")
        return v.strip()


class GeometryRequest(BaseModel):
    smiles: str = Field(..., min_length=1, max_length=2048)
    method: Literal["etkdg", "mmff94", "uff"] = "etkdg"
    num_conformers: int = Field(default=1, ge=1, le=100)
    optimize: bool = True
    random_seed: Optional[int] = Field(default=42, ge=0, le=2147483647)

    @field_validator("smiles")
    @classmethod
    def validate_smiles_charset(cls, v: str) -> str:
        allowed_pattern = r'^[A-Za-z0-9@+-[]()=#$:/\\.*%]+$'
        if not re.match(allowed_pattern, v):
            raise ValueError("SMILES contains invalid characters")
        return v.strip()


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    rdkit_version: str
    service_version: str = "7.2.0"
    timestamp: str


def generate_3d_conformer(
    smiles: str,
    method: str = "etkdg",
    num_conformers: int = 1,
    optimize: bool = True,
    random_seed: int = 42
) -> Dict:
    mol = None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES: {smiles}")

        mol = Chem.AddHs(mol)

        params = AllChem.ETKDGv3()
        params.randomSeed = random_seed
        params.numThreads = 1

        conf_ids = AllChem.EmbedMultipleConfs(
            mol,
            numConfs=num_conformers,
            params=params
        )

        if len(conf_ids) == 0:
            raise RuntimeError(f"Failed to generate conformers for: {smiles}")

        energies = []
        if optimize:
            if method == "mmff94":
                for conf_id in conf_ids:
                    props = AllChem.MMFFGetMoleculeProperties(mol)
                    ff = AllChem.MMFFGetMoleculeForceField(mol, props, confId=conf_id)
                    if ff is None:
                        logger.warning(f"MMFF94 not applicable, falling back to UFF for {smiles}")
                        ff = AllChem.UFFGetMoleculeForceField(mol, confId=conf_id)
                    ff.Minimize()
                    energies.append(ff.CalcEnergy())
            else:
                for conf_id in conf_ids:
                    ff = AllChem.UFFGetMoleculeForceField(mol, confId=conf_id)
                    ff.Minimize()
                    energies.append(ff.CalcEnergy())

        best_conf_id = conf_ids[0] if not energies else conf_ids[energies.index(min(energies))]
        conf = mol.GetConformer(best_conf_id)

        coords = []
        for i in range(mol.GetNumAtoms()):
            pos = conf.GetAtomPosition(i)
            coords.append({
                "atom": mol.GetAtomWithIdx(i).GetSymbol(),
                "x": round(pos.x, 6),
                "y": round(pos.y, 6),
                "z": round(pos.z, 6)
            })

        return {
            "success": True,
            "smiles_canonical": Chem.MolToSmiles(Chem.RemoveHs(mol)),
            "coordinates": coords,
            "energy_kcal_mol": min(energies) if energies else None,
            "num_conformers_generated": len(conf_ids),
            "method": method,
            "molecular_weight": round(Descriptors.MolWt(mol), 3),
            "num_atoms": mol.GetNumAtoms(),
            "num_heavy_atoms": mol.GetNumHeavyAtoms(),
            "metadata": {
                "random_seed": random_seed,
                "optimized": optimize,
                "version": "7.2.0"
            }
        }

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Geometry generation error for {smiles}: {e}")
        raise RuntimeError(f"Failed to generate 3D geometry: {str(e)}")
    finally:
        if mol is not None:
            del mol


def generate_2d_coords(smiles: str) -> Dict:
    mol = None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES: {smiles}")

        AllChem.Compute2DCoords(mol)
        conf = mol.GetConformer()

        coords = []
        for i in range(mol.GetNumAtoms()):
            pos = conf.GetAtomPosition(i)
            coords.append({
                "atom": mol.GetAtomWithIdx(i).GetSymbol(),
                "x": round(pos.x, 6),
                "y": round(pos.y, 6)
            })

        return {
            "success": True,
            "smiles_canonical": Chem.MolToSmiles(mol),
            "coordinates_2d": coords
        }

    except Exception as e:
        logger.error(f"2D generation error for {smiles}: {e}")
        raise RuntimeError(f"Failed to generate 2D coordinates: {str(e)}")
    finally:
        if mol is not None:
            del mol


app = FastAPI(
    title="RDKit Sidecar Service",
    description="Molecular geometry generation service for Al-Zamzami Molecular Twin v7.2",
    version="7.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "details": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.get("/")
async def root():
    return {
        "service": "RDKit Sidecar Service",
        "version": "7.2.0",
        "architecture": "Al-Zamzami Molecular Twin",
        "endpoints": {
            "health": "/health",
            "full_geometry": "/full",
            "2d_coordinates": "/2d",
            "3d_coordinates": "/3d",
            "documentation": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        from rdkit import rdBase
        return HealthResponse(
            status="healthy",
            rdkit_version=rdBase.rdkitVersion,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception:
        return HealthResponse(
            status="unhealthy",
            rdkit_version="unknown",
            timestamp=datetime.utcnow().isoformat()
        )


@app.post("/full")
async def full_geometry(request: GeometryRequest):
    try:
        return generate_3d_conformer(
            smiles=request.smiles,
            method=request.method,
            num_conformers=request.num_conformers,
            optimize=request.optimize,
            random_seed=request.random_seed or 42
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/2d")
async def coords_2d(request: SMILESInput):
    try:
        return generate_2d_coords(request.smiles)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/3d")
async def coords_3d(request: GeometryRequest):
    try:
        return generate_3d_conformer(
            smiles=request.smiles,
            method=request.method,
            num_conformers=request.num_conformers,
            optimize=request.optimize,
            random_seed=request.random_seed or 42
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
