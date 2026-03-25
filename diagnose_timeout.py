#!/usr/bin/env python3
"""
Diagnostic script to identify timeout causes in find_ip_sungrow.py
Run this to check common issues that cause script timeouts.
"""

import sys
import subprocess
import time
import os
from pathlib import Path

def check_file_exists():
    """Check if the original script exists"""
    script_path = Path("/config/Sungrow_find_IP/find_ip_sungrow.py")
    if script_path.exists():
        print(f"✓ Script exists: {script_path}")
        print(f"  Size: {script_path.stat().st_size} bytes")
        print(f"  Permissions: {oct(script_path.stat().st_mode)}")
        return True
    else:
        print(f"✗ Script not found: {script_path}")
        return False

def check_dependencies():
    """Check if required Python packages are installed"""
    print("\nChecking dependencies...")
    required = ['requests', 'urllib3', 'json']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"  ✓ {package} installed")
        except ImportError:
            print(f"  ✗ {package} MISSING")
            missing.append(package)
    
    return len(missing) == 0

def check_network_connectivity():
    """Check basic network connectivity"""
    print("\nChecking network connectivity...")
    test_urls = [
        "https://www.google.com",
        "https://api.sungrowpower.com",  # Common Sungrow API
    ]
    
    try:
        import requests
        for url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                print(f"  ✓ {url} - Status: {response.status_code}")
            except requests.exceptions.Timeout:
                print(f"  ✗ {url} - TIMEOUT (this could be the issue!)")
            except requests.exceptions.ConnectionError:
                print(f"  ✗ {url} - Connection failed")
            except Exception as e:
                print(f"  ? {url} - {type(e).__name__}: {e}")
    except ImportError:
        print("  ✗ Cannot test - requests module not available")

def analyze_script_structure():
    """Try to analyze the script structure"""
    script_path = Path("/config/Sungrow_find_IP/find_ip_sungrow.py")
    if not script_path.exists():
        return
    
    print("\nAnalyzing script structure...")
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            print(f"  Total lines: {len(lines)}")
            
            # Check for common timeout causes
            issues = []
            
            if 'requests.get(' in content or 'requests.post(' in content:
                if 'timeout=' not in content:
                    issues.append("⚠ Network requests without explicit timeout")
                else:
                    print("  ✓ Network requests have timeout specified")
            
            if 'while True:' in content:
                issues.append("⚠ Infinite loop detected (while True)")
            
            if 'sleep(' in content:
                sleep_count = content.count('sleep(')
                print(f"  ⚠ Found {sleep_count} sleep() calls (could delay execution)")
            
            if 'input(' in content:
                issues.append("⚠ input() calls detected (will wait for user)")
            
            # Check for try/except blocks
            if 'try:' in content:
                print("  ✓ Error handling present (try/except)")
            
            if issues:
                print("\n  Potential issues found:")
                for issue in issues:
                    print(f"    {issue}")
            else:
                print("  ✓ No obvious timeout issues in structure")
                
    except Exception as e:
        print(f"  ✗ Could not analyze script: {e}")

def test_script_execution():
    """Test script execution with a short timeout"""
    print("\nTesting script execution...")
    script_path = Path("/config/Sungrow_find_IP/find_ip_sungrow.py")
    
    if not script_path.exists():
        print("  ✗ Script not found, cannot test")
        return
    
    # Get token from environment or use dummy
    token = os.environ.get('HA_TOKEN', 'test_token_12345')
    
    print(f"  Running script with test token (10 second timeout)...")
    print(f"  Command: python3 {script_path} {token}")
    
    try:
        start = time.time()
        result = subprocess.run(
            [sys.executable, str(script_path), token],
            capture_output=True,
            text=True,
            timeout=10
        )
        elapsed = time.time() - start
        
        print(f"  ✓ Script completed in {elapsed:.2f} seconds")
        if result.stdout:
            print(f"  Output: {result.stdout[:200]}")
        if result.stderr:
            print(f"  Errors: {result.stderr[:200]}")
            
    except subprocess.TimeoutExpired:
        print(f"  ✗ Script TIMED OUT after 10 seconds")
        print(f"  This confirms the timeout issue!")
    except Exception as e:
        print(f"  ✗ Error running script: {e}")

def main():
    """Run all diagnostic checks"""
    print("=" * 60)
    print("find_ip_sungrow.py Timeout Diagnostic Tool")
    print("=" * 60)
    
    checks = [
        ("File existence", check_file_exists),
        ("Dependencies", check_dependencies),
        ("Network connectivity", check_network_connectivity),
        ("Script structure", analyze_script_structure),
        ("Script execution", test_script_execution),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n✗ Error in {name}: {e}")
            results[name] = False
    
    print("\n" + "=" * 60)
    print("Diagnostic Summary")
    print("=" * 60)
    
    print("\nRecommendations:")
    print("1. Review the debug log: /config/Sungrow_find_IP/find_ip_sungrow_debug.log")
    print("2. Ensure all network requests have timeout parameters")
    print("3. Check if the API endpoint is accessible")
    print("4. Verify the token is valid and not expired")
    print("5. Consider increasing the timeout in Home Assistant automation")
    print("\nTo use the debug version:")
    print("  python3 /config/Sungrow_find_IP/find_ip_sungrow_debug.py <token>")

if __name__ == "__main__":
    main()

