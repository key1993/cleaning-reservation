#!/usr/bin/env python3
"""
Debug version of find_ip_sungrow.py with enhanced timeout handling and logging.
This script helps identify why the original script is timing out.
"""

import sys
import time
import logging
import signal
from datetime import datetime

# Configure logging to both file and stderr
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/config/Sungrow_find_IP/find_ip_sungrow_debug.log'),
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)

# Global timeout flag
timeout_occurred = False

def timeout_handler(signum, frame):
    """Handle timeout signal"""
    global timeout_occurred
    timeout_occurred = True
    logger.error(f"TIMEOUT: Script exceeded time limit at {datetime.now()}")
    logger.error(f"Current stack: {frame}")
    raise TimeoutError("Script execution timeout")

def main():
    """Main function with timeout protection"""
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Starting find_ip_sungrow.py debug version")
    logger.info(f"Start time: {datetime.now()}")
    logger.info(f"Arguments: {sys.argv}")
    
    # Set up timeout signal (50 seconds to allow cleanup before 60s timeout)
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(50)  # 50 second timeout
    
    try:
        # Get token from arguments
        if len(sys.argv) < 2:
            logger.error("ERROR: No token provided")
            logger.info("Usage: python3 find_ip_sungrow.py <token>")
            sys.exit(1)
        
        token = sys.argv[1]
        logger.info(f"Token received: {'*' * (len(token) - 4) + token[-4:] if len(token) > 4 else '****'}")
        
        # Step 1: Import required modules (common timeout cause)
        logger.info("Step 1: Importing modules...")
        step_start = time.time()
        
        try:
            import requests
            logger.info(f"  ✓ requests imported in {time.time() - step_start:.2f}s")
        except ImportError as e:
            logger.error(f"  ✗ Failed to import requests: {e}")
            sys.exit(1)
        
        # Step 2: Network operations (most common timeout cause)
        logger.info("Step 2: Performing network operations...")
        step_start = time.time()
        
        # Add your actual API calls here with timeouts
        # Example structure:
        try:
            # Replace with actual API endpoint
            api_url = "https://api.example.com/sungrow/ip"  # UPDATE THIS
            
            logger.info(f"  Making request to: {api_url}")
            logger.info(f"  Request timeout: 30 seconds")
            
            # Use requests with explicit timeout
            response = requests.get(
                api_url,
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                timeout=(10, 30)  # (connect timeout, read timeout)
            )
            
            logger.info(f"  ✓ Request completed in {time.time() - step_start:.2f}s")
            logger.info(f"  Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"  Response data: {data}")
                # Process the response here
                print(f"IP_ADDRESS={data.get('ip', 'NOT_FOUND')}")
            else:
                logger.warning(f"  Unexpected status code: {response.status_code}")
                logger.warning(f"  Response: {response.text[:200]}")
                
        except requests.exceptions.Timeout as e:
            logger.error(f"  ✗ Request timeout: {e}")
            logger.error(f"  This is likely the cause of the 60s timeout")
            sys.exit(1)
        except requests.exceptions.ConnectionError as e:
            logger.error(f"  ✗ Connection error: {e}")
            logger.error(f"  Check network connectivity")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            logger.error(f"  ✗ Request error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"  ✗ Unexpected error: {e}", exc_info=True)
            sys.exit(1)
        
        # Step 3: Processing (if any)
        logger.info("Step 3: Processing results...")
        step_start = time.time()
        
        # Add your processing logic here
        
        elapsed = time.time() - start_time
        logger.info(f"Step 3 completed in {time.time() - step_start:.2f}s")
        
        # Cancel timeout signal
        signal.alarm(0)
        
        logger.info("=" * 60)
        logger.info(f"Script completed successfully in {elapsed:.2f} seconds")
        logger.info(f"End time: {datetime.now()}")
        
    except TimeoutError:
        elapsed = time.time() - start_time
        logger.error("=" * 60)
        logger.error(f"Script timed out after {elapsed:.2f} seconds")
        logger.error("Possible causes:")
        logger.error("  1. Network request taking too long")
        logger.error("  2. API endpoint not responding")
        logger.error("  3. DNS resolution issues")
        logger.error("  4. Infinite loop in code")
        sys.exit(1)
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        logger.warning(f"Script interrupted by user after {elapsed:.2f} seconds")
        sys.exit(1)
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error("=" * 60)
        logger.error(f"Unexpected error after {elapsed:.2f} seconds: {e}", exc_info=True)
        sys.exit(1)
    finally:
        signal.alarm(0)  # Cancel any pending alarm

if __name__ == "__main__":
    main()

