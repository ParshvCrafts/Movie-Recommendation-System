import os
import requests
import logging
from pathlib import Path
import pickle

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_file_id_from_url(url):
    """Extract Google Drive file ID from sharing URL"""
    if 'drive.google.com' in url:
        if '/file/d/' in url:
            # Extract ID from URL like: https://drive.google.com/file/d/FILE_ID/view?usp=sharing
            return url.split('/file/d/')[1].split('/')[0]
        elif 'id=' in url:
            # Extract ID from URL like: https://drive.google.com/uc?id=FILE_ID
            return url.split('id=')[1].split('&')[0]
    return None

def download_from_google_drive(file_id, filename):
    """Download file from Google Drive using file ID"""
    try:
        logger.info(f"Downloading {filename} from Google Drive...")
        
        # Use the direct download URL format
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        session = requests.Session()
        response = session.get(url, stream=True, timeout=30)
        
        # Check if we need to handle the virus scan warning
        if 'virus scan warning' in response.text.lower() or 'download_warning' in response.text:
            # Get the download confirmation token
            for key, value in response.cookies.items():
                if key.startswith('download_warning'):
                    params = {'id': file_id, 'export': 'download', 'confirm': value}
                    response = session.get(url, params=params, stream=True, timeout=30)
                    break
        
        response.raise_for_status()
        
        # Check if we actually got file content (not HTML)
        content_type = response.headers.get('content-type', '')
        if 'text/html' in content_type:
            logger.error(f"Received HTML instead of file content for {filename}")
            return False
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        if downloaded_size % (1024 * 1024) == 0:  # Log every MB
                            logger.info(f"Progress: {progress:.1f}%")
        
        logger.info(f"Successfully downloaded {filename} ({downloaded_size / (1024*1024):.1f} MB)")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading {filename}: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        return False

def verify_pickle_file(filename):
    """Verify that the downloaded file is a valid pickle file"""
    try:
        with open(filename, 'rb') as f:
            # Try to load just the first part to verify it's a valid pickle
            pickle.load(f)
        logger.info(f"✓ {filename} is a valid pickle file")
        return True
    except Exception as e:
        logger.error(f"✗ {filename} is not a valid pickle file: {e}")
        return False

def download_models():
    """Download large model files"""
    
    # Your Google Drive sharing URLs converted to file IDs
    models = {
        'movies.pkl': {
            'file_id': '1DRKYFjnFUjebFodUiz_Vp2fnmcSnJMta',  # Extracted from your URL
            'size_mb': 1
        },
        'similarity.pkl': {
            'file_id': '1tYFyLDpDnIEzPSt3Az_Y7xL7BUR8jsF1',  # Extracted from your URL
            'size_mb': 100
        }
    }
    
    all_downloaded = True
    
    for filename, info in models.items():
        if not os.path.exists(filename):
            logger.info(f"{filename} not found. Downloading...")
            success = download_from_google_drive(info['file_id'], filename)
            if success:
                # Verify the downloaded file is a valid pickle
                if not verify_pickle_file(filename):
                    logger.error(f"Downloaded {filename} is corrupted, removing...")
                    os.remove(filename)
                    success = False
            
            if not success:
                all_downloaded = False
                logger.error(f"Failed to download {filename}")
        else:
            file_size = os.path.getsize(filename) / (1024 * 1024)  # Size in MB
            logger.info(f"{filename} already exists ({file_size:.1f} MB)")
            
            # Verify existing file is valid
            if not verify_pickle_file(filename):
                logger.warning(f"Existing {filename} is corrupted, re-downloading...")
                os.remove(filename)
                success = download_from_google_drive(info['file_id'], filename)
                if not success or not verify_pickle_file(filename):
                    all_downloaded = False
    
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
        
        # Verify it's a valid pickle file
        if not verify_pickle_file(filename):
            return False
        
        logger.info(f"✓ {filename} exists and is valid ({file_size / (1024*1024):.1f} MB)")
    
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
