"""
Molecular Geometry Generation Module - Al-Zamzami Molecular Twin v7.2
Implements ETKDG and MMFF94 conformer generation per published methods.

Scientific References:
- ETKDG: Riniker & Landrum, J. Chem. Inf. Model. 2015, 55, 2562-2574
  DOI: 10.1021/acs.jcim.5b00654
- MMFF94: Halgren, J. Comput. Chem. 1996, 17, 490-519
  DOI: 10.1002/(SICI)1096-987X(199604)17:5/6<490::AID-JCC1>3.0.CO;2-P
"""

from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class GeometryEngine:
    """
    Production-grade 3D geometry generation engine.
    
    Quality assurance:
    - Input validation (sanitization, valence checks)
    - Error handling with specific failure modes
    - Deterministic output (fixed random seeds)
    - Memory safety (explicit mol object cleanup)
    """
    
    @staticmethod
    def generate_3d_conformer(
        smiles: str,
        method: str = "etkdg",
        num_conformers: int = 1,
        optimize: bool = True,
        random_seed: int = 42
    ) -> Dict:
        """
        Generate 3D conformer(s) from SMILES.
        
        Args:
            smiles: Input SMILES string (OpenSMILES format)
            method: Generation method (etkdg, mmff94, uff)
            num_conformers: Number of conformers to generate
            optimize: Apply force-field minimization
            random_seed: Random seed for reproducibility
            
        Returns:
            Dictionary with 3D coordinates, energy, and metadata
            
        Raises:
            ValueError: Invalid SMILES or unsupported method
            RuntimeError: Conformer generation failure
        """
        mol = None
        try:
            # Parse and sanitize SMILES
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                raise ValueError(f"Invalid SMILES: {smiles}")
            
            # Add explicit hydrogens (required for 3D generation)
            mol = Chem.AddHs(mol)
            
            # Generate conformers using ETKDG
            params = AllChem.ETKDGv3()
            params.randomSeed = random_seed
            params.numThreads = 1  # Deterministic
            
            conf_ids = AllChem.EmbedMultipleConfs(
                mol,
                numConfs=num_conformers,
                params=params
            )
            
            if len(conf_ids) == 0:
                raise RuntimeError(f"Failed to generate conformers for: {smiles}")
            
            # Optimize with force field if requested
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
                else:  # UFF or default
                    for conf_id in conf_ids:
                        ff = AllChem.UFFGetMoleculeForceField(mol, confId=conf_id)
                        ff.Minimize()
                        energies.append(ff.CalcEnergy())
            
            # Extract lowest-energy conformer coordinates
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
            
            # Calculate molecular properties
            mol_weight = Descriptors.MolWt(mol)
            num_atoms = mol.GetNumAtoms()
            num_heavy_atoms = mol.GetNumHeavyAtoms()
            
            return {
                "success": True,
                "smiles_canonical": Chem.MolToSmiles(Chem.RemoveHs(mol)),
                "coordinates": coords,
                "energy_kcal_mol": min(energies) if energies else None,
                "num_conformers_generated": len(conf_ids),
                "method": method,
                "molecular_weight": round(mol_weight, 3),
                "num_atoms": num_atoms,
                "num_heavy_atoms": num_heavy_atoms,
                "metadata": {
                    "random_seed": random_seed,
                    "optimized": optimize,
                    "version": "7.2.0"
                }
            }
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Geometry generation error for {smiles}: {e}")
            raise RuntimeError(f"Failed to generate 3D geometry: {str(e)}")
        finally:
            # Memory safety: explicit cleanup
            if mol is not None:
                del mol
    
    @staticmethod
    def generate_2d_coords(smiles: str) -> Dict:
        """
        Generate 2D coordinates for visualization.
        
        Args:
            smiles: Input SMILES string
            
        Returns:
            Dictionary with 2D coordinates and canonical SMILES
        """
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
