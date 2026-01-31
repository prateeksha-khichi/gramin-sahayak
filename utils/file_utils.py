"""
File utilities - Handle file operations
"""

import os
import shutil
from typing import Optional
from loguru import logger


def ensure_directory(path: str):
    """Create directory if it doesn't exist"""
    os.makedirs(path, exist_ok=True)
    logger.debug(f"📁 Directory ensured: {path}")


def cleanup_temp_files(directory: str = "temp_audio", max_age_hours: int = 24):
    """
    Delete old temporary files
    
    Args:
        directory: Temp directory to clean
        max_age_hours: Delete files older than this
    """
    import time
    
    if not os.path.exists(directory):
        return
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    deleted_count = 0
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        if os.path.isfile(filepath):
            file_age = current_time - os.path.getmtime(filepath)
            
            if file_age > max_age_seconds:
                os.remove(filepath)
                deleted_count += 1
    
    if deleted_count > 0:
        logger.info(f"🧹 Cleaned up {deleted_count} temp files from {directory}")


def get_file_size_mb(filepath: str) -> float:
    """Get file size in MB"""
    if os.path.exists(filepath):
        return os.path.getsize(filepath) / (1024 * 1024)
    return 0.0


def safe_file_delete(filepath: str):
    """Safely delete a file"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.debug(f"🗑️ Deleted: {filepath}")
    except Exception as e:
        logger.warning(f"⚠️ Could not delete {filepath}: {e}")


def copy_with_backup(source: str, destination: str):
    """Copy file with backup of existing destination"""
    if os.path.exists(destination):
        backup = f"{destination}.backup"
        shutil.copy2(destination, backup)
        logger.info(f"💾 Backup created: {backup}")
    
    shutil.copy2(source, destination)
    logger.info(f"📋 Copied: {source} -> {destination}")


# Initialize common directories
def init_project_directories():
    """Create all required project directories"""
    directories = [
        'data/pdfs',
        'data/processed',
        'data/processed/faiss_index',
        'models/loan_eligibility',
        'models/fraud_detection',
        'models/embeddings',
        'logs',
        'temp_audio'
    ]
    
    for directory in directories:
        ensure_directory(directory)
    
    logger.info("✅ All project directories initialized")


if __name__ == "__main__":
    init_project_directories()