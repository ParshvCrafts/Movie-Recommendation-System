import os
import gdown
import logging
import pickle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_pickle_file(filename):
    """Verify that the downloaded file is a valid pickle file"""
    try:
        with open(filename, 'rb') as f:
            # Just check if we can load the first few bytes without loading the entire file
            f.read(10)  # Read first 10 bytes to check if it's binary
            f.seek(0)   # Reset file pointer
            # For very large files, don't load entirely, just check the header
            header = f.read(10)
            if header.startswith(b'\x80\x03') or header.startswith(b'\x80\x04') or header.startswith(b'\x80\x05'):
                logger.info(f"✓ {filename} appears to be a valid pickle file")
                return True
        return False
    except Exception as e:
        logger.error(f"✗ {filename} is not a valid pickle file: {e}")
        return False

def download_with_gdown(file_id, filename, fuzzy=True):
    """Download file using gdown with better error handling"""
    try:
        logger.info(f"Attempting to download {filename} using gdown...")
        
        # Try multiple URL formats
        urls_to_try = [
            f'https://drive.google.com/uc?id={file_id}',
            f'https://drive.google.com/file/d/{file_id}/view?usp=sharing'
        ]
        
        for url in urls_to_try:
            try:
                logger.info(f"Trying URL: {url}")
                gdown.download(url, filename, quiet=False, fuzzy=fuzzy)
                
                if os.path.exists(filename) and os.path.getsize(filename) > 1000:  # File should be larger than 1KB
                    if verify_pickle_file(filename):
                        return True
                    else:
                        logger.warning(f"Downloaded file is not a valid pickle, trying next URL...")
                        os.remove(filename)
                else:
                    logger.warning(f"Download failed or file too small, trying next URL...")
                    if os.path.exists(filename):
                        os.remove(filename)
            except Exception as e:
                logger.warning(f"gdown failed with URL {url}: {e}")
                if os.path.exists(filename):
                    os.remove(filename)
                continue
        
        return False
        
    except Exception as e:
        logger.error(f"Error with gdown for {filename}: {e}")
        return False

def download_models():
    """Download large model files from Google Drive"""
    
    models = {
        'movies.pkl': {
            'file_id': '1DRKYFjnFUjebFodUiz_Vp2fnmcSnJMta'
        },
        'similarity.pkl': {
            'file_id': '1tYFyLDpDnIEzPSt3Az_Y7xL7BUR8jsF1'
        }
    }
    
    all_downloaded = True
    
    for filename, info in models.items():
        if os.path.exists(filename) and verify_pickle_file(filename):
            file_size = os.path.getsize(filename) / (1024 * 1024)
            logger.info(f"{filename} already exists and is valid ({file_size:.1f} MB)")
            continue
        
        if os.path.exists(filename):
            logger.warning(f"Removing invalid {filename}")
            os.remove(filename)
        
        logger.info(f"Downloading {filename}...")
        success = download_with_gdown(info['file_id'], filename)
        
        if not success:
            logger.error(f"Failed to download {filename}")
            all_downloaded = False
        else:
            file_size = os.path.getsize(filename) / (1024 * 1024)
            logger.info(f"✅ Successfully downloaded {filename} ({file_size:.1f} MB)")
    
    return all_downloaded

if __name__ == "__main__":
    logger.info("Starting model download process...")
    success = download_models()
    
    if success:
        logger.info("✅ All models ready!")
    else:
        logger.error("❌ Model download failed!")
