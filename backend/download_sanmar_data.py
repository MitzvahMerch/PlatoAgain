import pysftp
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_sanmar_files():
    """Download required files from SanMar SFTP server"""
    
    # SanMar SFTP credentials
    HOSTNAME = "ftp.sanmar.com"
    PORT = 2200
    USERNAME = 283788  # Replace with your SanMar FTP username
    PASSWORD = McixrUs85yY7Lb  # Replace with your SanMar FTP password
    
    # Files to download from SanMarPDD directory
    files_to_download = [
        'SanMar_SDL_N.csv',
        'SanMar_EPDD.csv',
        'sanmar_dip.txt'  # Hourly inventory updates
    ]
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Disable host key checking (only for testing - in production, use proper host keys)
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    
    try:
        # Connect to SFTP server
        logger.info(f"Connecting to {HOSTNAME}...")
        with pysftp.Connection(
            host=HOSTNAME,
            username=USERNAME,
            password=PASSWORD,
            port=PORT,
            cnopts=cnopts
        ) as sftp:
            logger.info("Connected successfully")
            
            # Change to SanMarPDD directory
            sftp.chdir('SanMarPDD')
            
            # Download each file
            for filename in files_to_download:
                local_path = os.path.join('data', filename)
                logger.info(f"Downloading {filename}...")
                sftp.get(filename, local_path)
                logger.info(f"Successfully downloaded {filename}")
                
    except Exception as e:
        logger.error(f"Error downloading files: {str(e)}")
        sys.exit(1)
        
    logger.info("All files downloaded successfully!")

if __name__ == "__main__":
    download_sanmar_files()