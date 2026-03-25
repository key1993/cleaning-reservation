# Debugging find_ip_sungrow.py Timeout Issues

## Problem
The `find_ip_sungrow.py` script is timing out after 60 seconds in Home Assistant automation, causing the watchdog automation to fail repeatedly.

## Quick Diagnosis Steps

### Step 1: Run the Diagnostic Script
```bash
# On your Home Assistant system
python3 /config/Sungrow_find_IP/diagnose_timeout.py
```

This will check:
- If the script file exists and is accessible
- If required dependencies are installed
- Network connectivity to common endpoints
- Script structure for common timeout causes
- Test script execution with a short timeout

### Step 2: Use the Debug Version
Replace your automation to use the debug version temporarily:

**In Home Assistant automation:**
```yaml
service: shell_command.find_ip_sungrow
data:
  command: python3 /config/Sungrow_find_IP/find_ip_sungrow_debug.py '{{ states(''input_text.ha_token'') }}'
```

The debug version will:
- Log detailed progress to `/config/Sungrow_find_IP/find_ip_sungrow_debug.log`
- Show which step is taking too long
- Automatically timeout after 50 seconds (before the 60s limit)
- Provide detailed error messages

### Step 3: Check the Debug Log
```bash
tail -f /config/Sungrow_find_IP/find_ip_sungrow_debug.log
```

## Common Causes of Timeouts

### 1. **Network Requests Without Timeout** (Most Common)
**Problem:** API calls without explicit timeout parameters can hang indefinitely.

**Solution:** Always specify timeouts:
```python
# BAD
response = requests.get(url, headers=headers)

# GOOD
response = requests.get(url, headers=headers, timeout=(10, 30))
```

### 2. **Slow or Unresponsive API**
**Problem:** The Sungrow API endpoint might be slow or down.

**Check:**
```bash
curl -v --max-time 10 https://your-api-endpoint.com
```

**Solution:** 
- Increase timeout in Home Assistant automation
- Add retry logic with exponential backoff
- Implement caching to avoid repeated calls

### 3. **DNS Resolution Issues**
**Problem:** DNS lookup taking too long.

**Check:**
```bash
time nslookup api.sungrowpower.com
```

**Solution:** Use IP address directly or check DNS settings.

### 4. **Infinite Loops**
**Problem:** Code stuck in a loop waiting for a condition that never occurs.

**Check:** Look for `while True:` without proper exit conditions.

### 5. **Blocking I/O Operations**
**Problem:** Waiting for user input, file locks, or other blocking operations.

**Check:** Look for `input()`, file operations without timeouts, etc.

## Fixing Your Original Script

### Template for Fixed Version:
```python
#!/usr/bin/env python3
import sys
import requests
import signal
from datetime import datetime

def timeout_handler(signum, frame):
    print("ERROR: Script timeout", file=sys.stderr)
    sys.exit(1)

# Set 50 second timeout
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(50)

try:
    token = sys.argv[1]
    
    # Make API call with explicit timeout
    response = requests.get(
        "https://api-endpoint.com/ip",
        headers={'Authorization': f'Bearer {token}'},
        timeout=(10, 30)  # 10s connect, 30s read
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"IP_ADDRESS={data.get('ip')}")
    else:
        print(f"ERROR: API returned {response.status_code}", file=sys.stderr)
        sys.exit(1)
        
except requests.exceptions.Timeout:
    print("ERROR: Request timeout", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    signal.alarm(0)  # Cancel timeout
```

## Home Assistant Automation Fix

### Option 1: Increase Timeout
```yaml
service: shell_command.find_ip_sungrow
data:
  command: timeout 120 python3 /config/Sungrow_find_IP/find_ip_sungrow.py '{{ states(''input_text.ha_token'') }}'
```

### Option 2: Add Error Handling
```yaml
automation:
  - alias: "Watchdog - Reconnection Handler"
    trigger:
      # your triggers
    action:
      - service: shell_command.find_ip_sungrow
        continue_on_error: true  # Don't fail automation on script error
      - delay: "00:00:05"
      - condition: template
        value_template: "{{ states('sensor.sungrow_ip') != 'unavailable' }}"
      # rest of automation
```

### Option 3: Use Python Script Integration
Instead of shell_command, use Home Assistant's Python Script integration for better error handling.

## Monitoring

Add this to your Home Assistant configuration to monitor script execution:

```yaml
sensor:
  - platform: command_line
    name: Sungrow Script Status
    command: "python3 /config/Sungrow_find_IP/find_ip_sungrow.py '{{ states(''input_text.ha_token'') }}' && echo 'SUCCESS' || echo 'FAILED'"
    scan_interval: 300
```

## Next Steps

1. **Run the diagnostic script** to identify the specific issue
2. **Review the debug log** to see where it's hanging
3. **Update your original script** with proper timeout handling
4. **Test the fix** with the debug version first
5. **Update your automation** once confirmed working

## Files Created

- `find_ip_sungrow_debug.py` - Enhanced version with logging and timeout protection
- `diagnose_timeout.py` - Diagnostic tool to identify issues
- `TIMEOUT_DEBUG_GUIDE.md` - This guide

Copy these files to your Home Assistant `/config/Sungrow_find_IP/` directory to use them.

