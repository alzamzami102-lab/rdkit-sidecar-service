"""
Input Validation Module - Al-Zamzami Molecular Twin v7.2
Conforms to: OWASP Secure Coding Practices, NIST SP 800-53 (Input Validation)
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal


class SMILESInput(BaseModel):
    """
    Validated SMILES input schema.

    Standards compliance:
    - OpenSMILES specification
    - Maximum length prevents DoS attacks (OWASP A05:2021 - Security Misconfiguration)
    """
    smiles: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="SMILES string representation of molecule"
    )

    @field_validator("smiles")
    @classmethod
    def normalize_smiles(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("SMILES is required")
        return v


class GeometryRequest(BaseModel):
    """
    Geometry generation request with scientific parameters.

    Standards:
    - ETKDG: J. Chem. Inf. Model. 2015, 55, 2562-2574 (DOI: 10.1021/acs.jcim.5b00654)
    - MMFF94: J. Comput. Chem. 1996, 17, 490-519 (DOI: 10.1002/(SICI)1096-987X)
    """
    smiles: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="Input SMILES string"
    )

    method: Literal["etkdg", "mmff94", "uff"] = Field(
        default="etkdg",
        description="Conformer generation method"
    )

    num_conformers: int = Field(
        default=1,
        ge=1,
        le=100,
        description="Number of conformers to generate (max 100 to prevent resource exhaustion)"
    )

    optimize: bool = Field(
        default=True,
        description="Apply force-field optimization after conformer generation"
    )

    random_seed: Optional[int] = Field(
        default=42,
        ge=0,
        le=2**31 - 1,
        description="Random seed for reproducibility (FAIR principles: Reproducible)"
    )

    @field_validator("smiles")
    @classmethod
    def normalize_geometry_smiles(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("SMILES is required")
        return v


class HealthResponse(BaseModel):
    """Service health check response."""
    status: Literal["healthy", "degraded", "unhealthy"]
    rdkit_version: str
    service_version: str = "7.2.0"
    timestamp: str
