import os
from pathlib import Path

def load_secrets():
    """
    Reads secret files defined in environment variables (ending in _FILE)
    and loads their content into the actual environment variable.
    """
    
    secret_names = ["SECRET_KEY", "EMAIL", "PASSWORD"]

    for name in secret_names:
        file_env_var = f"{name}_FILE"
        file_path = os.getenv(file_env_var)
        
        if file_path and os.path.exists(file_path) and name not in os.environ:
            try:
                value = Path(file_path).read_text(encoding="utf-8").strip()
                os.environ[name] = value
            except Exception as e:
                print(f"Warning: Could not load secret {name} from {file_path}: {e}")
