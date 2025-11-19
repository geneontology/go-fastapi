"""Network diagnostic utilities."""

import socket
import subprocess
import requests

from app.utils.settings import logger


def get_network_info():
    """
    Get network diagnostic information for debugging GOLr connectivity issues.
    
    :return: Dictionary with network information
    """
    info = {}
    
    try:
        # Get local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        info['local_ip'] = s.getsockname()[0]
        s.close()
    except Exception as e:
        info['local_ip'] = f"Unable to determine: {e}"
    
    try:
        # Get public IP (if accessible)
        response = requests.get('https://httpbin.org/ip', timeout=5)
        if response.status_code == 200:
            info['public_ip'] = response.json().get('origin', 'Unknown')
        else:
            info['public_ip'] = f"HTTP {response.status_code}"
    except Exception as e:
        info['public_ip'] = f"Unable to determine: {e}"
    
    try:
        # Check GOLr DNS resolution
        golr_ip = socket.gethostbyname('golr.geneontology.org')
        info['golr_resolved_ip'] = golr_ip
    except Exception as e:
        info['golr_resolved_ip'] = f"DNS resolution failed: {e}"
    
    try:
        # Get network route info (macOS/Linux)
        route_result = subprocess.run(['route', 'get', 'golr.geneontology.org'], 
                                    capture_output=True, text=True, timeout=10)
        info['route_info'] = route_result.stdout if route_result.returncode == 0 else f"Route failed: {route_result.stderr}"
    except Exception as e:
        info['route_info'] = f"Route check failed: {e}"
    
    return info