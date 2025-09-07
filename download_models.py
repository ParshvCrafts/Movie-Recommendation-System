import os
import requests
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_file(url, filename, chunk_size=8192):
    """Download a file from URL with progress tracking"""
    try:
        logger.info(f"Downloading {filename}...")
        
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        logger.info(f"Progress: {progress:.1f}%")
        
        logger.info(f"Successfully downloaded {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading {filename}: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        return False

def download_models():
    """Download large model files"""
    
    # Define your model URLs here
    # Option 1: Google Drive URLs (replace with your actual file IDs)
    models = {
        'movies.pkl': {
            'url': 'https://drive.google.com/file/d/1DRKYFjnFUjebFodUiz_Vp2fnmcSnJMta/view?usp=sharing',
            'size_mb': 1  # Approximate size in MB
        },
        'similarity.pkl': {
            'url': 'https://drive.google.com/file/d/1tYFyLDpDnIEzPSt3Az_Y7xL7BUR8jsF1/view?usp=sharing',
            'size_mb': 100  # Approximate size in MB
        }
    }
    
    # Option 2: Direct URLs (if you host them elsewhere)
    # models = {
    #     'movies.pkl': {
    #         'url': 'https://your-server.com/models/movies.pkl',
    #         'size_mb': 1
    #     },
    #     'similarity.pkl': {
    #         'url': 'https://your-server.com/models/similarity.pkl',
    #         'size_mb': 100
    #     }
    # }
    
    all_downloaded = True
    
    for filename, info in models.items():
        if not os.path.exists(filename):
            logger.info(f"{filename} not found. Downloading...")
            success = download_file(info['url'], filename)
            if not success:
                all_downloaded = False
                logger.error(f"Failed to download {filename}")
        else:
            file_size = os.path.getsize(filename) / (1024 * 1024)  # Size in MB
            logger.info(f"{filename} already exists ({file_size:.1f} MB)")
    
    if all_downloaded:
        logger.info("All model files are ready!")
    else:
        logger.error("Some model files failed to download!")
    
    return all_downloaded

def verify_models():
    """Verify that model files exist and are valid"""
    required_files = ['movies.pkl', 'similarity.pkl']
    
    for filename in required_files:
        if not os.path.exists(filename):
            logger.error(f"Required file {filename} is missing!")
            return False
        
        file_size = os.path.getsize(filename)
        if file_size == 0:
            logger.error(f"File {filename} is empty!")
            return False
        
        logger.info(f"✓ {filename} exists ({file_size / (1024*1024):.1f} MB)")
    
    return True

if __name__ == "__main__":
    logger.info("Starting model download process...")
    
    success = download_models()
    
    if success:
        logger.info("Verifying downloaded models...")
        if verify_models():
            logger.info("✓ All models downloaded and verified successfully!")
        else:
            logger.error("✗ Model verification failed!")
    else:
        logger.error("✗ Model download process failed!")
