"""
Input Validation Module - Al-Zamzami Molecular Twin v7.2
Conforms to: OWASP Secure Coding Practices, NIST SP 800-53 (Input Validation)
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
import re


class SMILESInput(BaseModel):
    """
    Validated SMILES input schema.
    
    Standards compliance:
    - OpenSMILES specification (http://opensmiles.org/opensmiles.html)
    - Maximum length prevents DoS attacks (OWASP A05:2021 - Security Misconfiguration)
    """
    smiles: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="SMILES string representation of molecule"
    )
    
    @validator('smiles')
    def validate_smiles_charset(cls, v):
        """Validate SMILES contains only allowed characters per OpenSMILES spec."""
        # Allowed: atoms, bonds, branches, rings, charges, isotopes
        allowed_pattern = r'^[A-Za-z0-9@+-[]()=#$:/\\.*%]+$'
        if not re.match(allowed_pattern, v):
            raise ValueError(
                "SMILES contains invalid characters. "
                "Allowed: atoms, bonds, branches, rings, charges, isotopes per OpenSMILES spec"
            )
        return v.strip()


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
        le=2**31-1,
        description="Random seed for reproducibility (FAIR principles: Reproducible)"
    )


class HealthResponse(BaseModel):
    """Service health check response."""
    status: Literal["healthy", "degraded", "unhealthy"]
    rdkit_version: str
    service_version: str = "7.2.0"
    timestamp: str
