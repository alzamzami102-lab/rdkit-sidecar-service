"""
RDKit Sidecar Service - FastAPI Application
Al-Zamzami Molecular Twin v7.2

Production-grade REST API for molecular geometry generation.
Compliant with: OpenAPI 3.0, JSON:API, FAIR principles.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
import logging
from datetime import datetime
import sys

from validation import SMILESInput, GeometryRequest, HealthResponse
from geometry import GeometryEngine

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RDKit Sidecar Service",
    description="Molecular geometry generation service for Al-Zamzami Molecular Twin v7.2",
    version="7.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware (configure allowed origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors with detailed messages."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "details": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - service information."""
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


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns RDKit version and service status.
    Compliant with: Kubernetes liveness/readiness probe standards.
    """
    try:
        from rdkit import rdBase
        rdkit_version = rdBase.rdkitVersion
        
        return HealthResponse(
            status="healthy",
            rdkit_version=rdkit_version,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            rdkit_version="unknown",
            timestamp=datetime.utcnow().isoformat()
        )


@app.post("/full", tags=["Geometry"])
async def generate_full_geometry(request: GeometryRequest):
    """
    Generate 3D molecular geometry with full optimization.
    
    Implements:
    - ETKDG conformer generation (Riniker & Landrum 2015)
    - MMFF94 or UFF force field minimization
    - Deterministic output (fixed random seed)
    
    Returns:
    - 3D coordinates (Cartesian)
    - Minimized energy (kcal/mol)
    - Canonical SMILES
    - Molecular properties (MW, atom counts)
    
    Compliance:
    - FAIR principles (Findable, Accessible, Interoperable, Reusable)
    - Reproducibility (random seed control)
    - Traceability (version metadata)
    """
    try:
        logger.info(f"Full geometry request: {request.smiles[:50]}... method={request.method}")
        
        result = GeometryEngine.generate_3d_conformer(
            smiles=request.smiles,
            method=request.method,
            num_conformers=request.num_conformers,
            optimize=request.optimize,
            random_seed=request.random_seed
        )
        
        logger.info(f"Generated {result['num_conformers_generated']} conformers, "
                   f"E={result.get('energy_kcal_mol', 'N/A')} kcal/mol")
        
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid input: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Geometry generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/2d", tags=["Geometry"])
async def generate_2d_coordinates(request: SMILESInput):
    """
    Generate 2D coordinates for molecular visualization.
    
    Returns:
    - 2D coordinates (x, y)
    - Canonical SMILES
    
    Use case: Web-based molecule rendering, structure diagrams.
    """
    try:
        logger.info(f"2D coordinates request: {request.smiles[:50]}...")
        
        result = GeometryEngine.generate_2d_coords(request.smiles)
        
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid SMILES: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"2D generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/3d", tags=["Geometry"])
async def generate_3d_coordinates(request: GeometryRequest):
    """
    Generate 3D coordinates (alias for /full with default parameters).
    
    Convenience endpoint for standard 3D conformer generation.
    """
    try:
        logger.info(f"3D coordinates request: {request.smiles[:50]}...")
        
        result = GeometryEngine.generate_3d_conformer(
            smiles=request.smiles,
            method=request.method,
            num_conformers=request.num_conformers,
            optimize=request.optimize,
            random_seed=request.random_seed
        )
        
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid input: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"3D generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
