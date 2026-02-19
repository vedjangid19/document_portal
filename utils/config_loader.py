# import yaml


# def load_config(config_path: str="config/config.yaml") -> dict:
#     """Load a YAML configuration file.

#     Args:
#         config_path (str): Path to the YAML configuration file.

#     Returns:
#         dict: Parsed configuration as a dictionary.
#     """
#     with open(config_path, 'r') as file:
#         config = yaml.safe_load(file)

#     return config


import os
import yaml
from pathlib import Path

def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]

def load_config(config_path: str | None = None) -> dict:
    """
    Resolve config path reliably irrespective of CWD.
    Priority: explicit arg > CONFIG_PATH env > <project_root>/config/config.yaml
    """

    env_path = os.getenv("CONFIG_PATH")

    if config_path is None:
        config_path = env_path or str(_project_root() / "config" / "config.yaml")

    config_path = Path(config_path)

    if not config_path.is_absolute():
        config_path = _project_root() / config_path

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    return config or {}


    