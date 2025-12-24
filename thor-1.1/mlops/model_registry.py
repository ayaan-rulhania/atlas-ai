"""
Model Registry for tracking and versioning models.
Integrates with MLflow for production-grade model management.
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib


class ModelRegistry:
    """
    Model registry for tracking model versions, metrics, and metadata.
    Can integrate with MLflow for advanced tracking.
    """
    
    def __init__(self, registry_path: str = "models/registry"):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.registry_path / "metadata.json"
        self._metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load registry metadata."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"models": [], "versions": {}}
    
    def _save_metadata(self):
        """Save registry metadata."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self._metadata, f, indent=2)
        except Exception as e:
            print(f"[ModelRegistry] Error saving metadata: {e}")
    
    def register_model(
        self,
        model_name: str,
        model_path: str,
        version: Optional[str] = None,
        metrics: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        training_data_hash: Optional[str] = None
    ) -> str:
        """
        Register a new model version.
        
        Args:
            model_name: Name of the model
            model_path: Path to the model file
            version: Version string (auto-generated if None)
            metrics: Evaluation metrics
            metadata: Additional metadata
            training_data_hash: Hash of training data for reproducibility
            
        Returns:
            Version string
        """
        if version is None:
            # Auto-generate version based on timestamp
            version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        model_entry = {
            "name": model_name,
            "version": version,
            "path": str(model_path),
            "registered_at": datetime.now().isoformat(),
            "metrics": metrics or {},
            "metadata": metadata or {},
            "training_data_hash": training_data_hash,
            "is_production": False
        }
        
        # Add to registry
        if model_name not in self._metadata["versions"]:
            self._metadata["versions"][model_name] = []
        
        self._metadata["versions"][model_name].append(model_entry)
        self._metadata["models"].append(model_entry)
        
        self._save_metadata()
        print(f"[ModelRegistry] Registered {model_name} v{version}")
        
        return version
    
    def get_model_versions(self, model_name: str) -> List[Dict]:
        """Get all versions of a model."""
        return self._metadata["versions"].get(model_name, [])
    
    def get_latest_version(self, model_name: str) -> Optional[Dict]:
        """Get the latest version of a model."""
        versions = self.get_model_versions(model_name)
        if not versions:
            return None
        # Sort by registered_at, most recent first
        return sorted(versions, key=lambda x: x["registered_at"], reverse=True)[0]
    
    def set_production_version(self, model_name: str, version: str):
        """Mark a specific version as production."""
        versions = self.get_model_versions(model_name)
        for v in versions:
            v["is_production"] = (v["version"] == version)
        self._save_metadata()
        print(f"[ModelRegistry] Set {model_name} v{version} as production")
    
    def get_production_version(self, model_name: str) -> Optional[Dict]:
        """Get the production version of a model."""
        versions = self.get_model_versions(model_name)
        for v in versions:
            if v.get("is_production"):
                return v
        return None
    
    def compare_versions(self, model_name: str, version1: str, version2: str) -> Dict:
        """Compare two model versions."""
        versions = {v["version"]: v for v in self.get_model_versions(model_name)}
        
        v1 = versions.get(version1)
        v2 = versions.get(version2)
        
        if not v1 or not v2:
            return {"error": "One or both versions not found"}
        
        comparison = {
            "version1": v1,
            "version2": v2,
            "metrics_diff": {}
        }
        
        # Compare metrics
        for metric in set(list(v1.get("metrics", {}).keys()) + list(v2.get("metrics", {}).keys())):
            val1 = v1.get("metrics", {}).get(metric, 0)
            val2 = v2.get("metrics", {}).get(metric, 0)
            comparison["metrics_diff"][metric] = val2 - val1
        
        return comparison
    
    def list_models(self) -> List[str]:
        """List all registered model names."""
        return list(self._metadata["versions"].keys())


def get_model_registry(registry_path: Optional[str] = None) -> ModelRegistry:
    """Get or create a model registry instance."""
    if registry_path is None:
        registry_path = "models/registry"
    return ModelRegistry(registry_path)

