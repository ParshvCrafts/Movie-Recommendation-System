import os
import requests
import logging
import pickle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_from_github_release(repo_owner, repo_name, tag, filename):
    """Download file from GitHub releases"""
    try:
        logger.info(f"📥 Downloading {filename} from GitHub releases...")
        
        # GitHub releases direct download URL
        url = f"https://github.com/{repo_owner}/{repo_name}/releases/download/{tag}/{filename}"
        logger.info(f"Download URL: {url}")
        
        response = requests.get(url, stream=True, timeout=120)
        
        if response.status_code == 404:
            logger.error(f"❌ File not found at {url}")
            logger.info(f"Please check if the file is uploaded to releases with tag '{tag}'")
            return False
        
        response.raise_for_status()
        
        # Get file size from headers
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        logger.info(f"File size: {total_size / (1024*1024):.1f} MB")
        
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # Log progress every 10MB
                    if downloaded_size % (10 * 1024 * 1024) == 0:
                        progress = (downloaded_size / total_size) * 100 if total_size > 0 else 0
                        logger.info(f"Progress: {progress:.1f}% ({downloaded_size / (1024*1024):.1f} MB)")
        
        final_size = os.path.getsize(filename)
        logger.info(f"✅ Successfully downloaded {filename} ({final_size / (1024*1024):.1f} MB)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error downloading {filename}: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        return False

def verify_pickle_file(filename):
    """Verify that the downloaded file is a valid pickle file"""
    try:
        with open(filename, 'rb') as f:
            header = f.read(10)
            
        if header.startswith(b'\x80'):  # Pickle protocol header
            logger.info(f"✅ {filename} is a valid pickle file")
            return True
        else:
            logger.error(f"❌ {filename} doesn't have valid pickle header")
            return False
                
    except Exception as e:
        logger.error(f"❌ Error verifying {filename}: {e}")
        return False

def download_models():
    """Download models from GitHub releases"""
    
    # Your GitHub repository details
    REPO_OWNER = "ParshvCrafts"
    REPO_NAME = "Movie-Recommendation-System"
    TAG = "v1.0.0"  # Change this to match your release tag
    
    models = {
        'similarity.pkl': True  # Required file
    }
    
    all_downloaded = True
    
    for filename, required in models.items():
        # Skip if file exists and is valid
        if os.path.exists(filename) and verify_pickle_file(filename):
            file_size = os.path.getsize(filename) / (1024 * 1024)
            logger.info(f"✅ {filename} already exists and is valid ({file_size:.1f} MB)")
            continue
        
        # Remove invalid file if exists
        if os.path.exists(filename):
            logger.warning(f"🗑️ Removing invalid/corrupted {filename}")
            os.remove(filename)
        
        # Download the file
        success = download_from_github_release(REPO_OWNER, REPO_NAME, TAG, filename)
        
        if success:
            # Verify the downloaded file
            if verify_pickle_file(filename):
                logger.info(f"✅ {filename} downloaded and verified successfully")
            else:
                logger.error(f"❌ {filename} downloaded but verification failed")
                if os.path.exists(filename):
                    os.remove(filename)
                success = False
        
        if not success and required:
            logger.error(f"❌ Failed to download required file {filename}")
            all_downloaded = False
    
    return all_downloaded

if __name__ == "__main__":
    logger.info("🚀 Starting model download from GitHub releases...")
    
    success = download_models()
    
    if success:
        logger.info("✅ All models downloaded and verified successfully!")
    else:
        logger.error("❌ Model download failed!")
        logger.info("""
        📋 Instructions to upload to GitHub releases:
        
        1. Go to: https://github.com/ParshvCrafts/Movie-Recommendation-System
        2. Click 'Releases' (on the right sidebar)
        3. Click 'Create a new release'
        4. Tag version: v1.0.0
        5. Upload 'similarity.pkl' as an asset
        6. Click 'Publish release'
        """)
