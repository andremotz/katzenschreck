"""Hardware detection for automatic model selection"""

import platform
import subprocess
import os
from typing import Tuple, Optional


class HardwareDetector:
    """Detects hardware platform and suggests optimal YOLO model"""
    
    def __init__(self):
        self.platform = self._detect_platform()
        self.is_jetson = self._is_jetson_device()
        self.is_raspberry_pi = self._is_raspberry_pi()
        self.memory_gb = self._get_memory_gb()
        self.cpu_cores = self._get_cpu_cores()
    
    def _detect_platform(self) -> str:
        """Detect the current platform"""
        return platform.system().lower()
    
    def _is_jetson_device(self) -> bool:
        """Check if running on NVIDIA Jetson device"""
        try:
            # Check for Jetson-specific files and commands
            if os.path.exists('/proc/device-tree/model'):
                with open('/proc/device-tree/model', 'r') as f:
                    model = f.read().strip()
                    return 'jetson' in model.lower() or 'xavier' in model.lower()
            
            # Check for nvidia-smi or tegrastats
            try:
                subprocess.run(['tegrastats', '--help'], 
                             capture_output=True, check=True, timeout=5)
                return True
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                pass
                
            return False
        except Exception:
            return False
    
    def _is_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi"""
        try:
            if os.path.exists('/proc/device-tree/model'):
                with open('/proc/device-tree/model', 'r') as f:
                    model = f.read().strip()
                    return 'raspberry pi' in model.lower()
            return False
        except Exception:
            return False
    
    def _get_memory_gb(self) -> float:
        """Get total memory in GB"""
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        kb = int(line.split()[1])
                        return kb / (1024 * 1024)  # Convert to GB
        except Exception:
            pass
        return 4.0  # Default fallback
    
    def _get_cpu_cores(self) -> int:
        """Get number of CPU cores"""
        try:
            return os.cpu_count() or 1
        except Exception:
            return 1
    
    def get_optimal_model(self) -> Tuple[str, str]:
        """
        Get optimal YOLO model and requirements file based on hardware
        
        Returns:
            Tuple of (model_name, requirements_file)
        """
        if self.is_jetson:
            if self.memory_gb >= 8:
                return 'yolo11x.pt', 'requirements_jetson.txt'
            elif self.memory_gb >= 4:
                return 'yolo11l.pt', 'requirements_jetson.txt'
            else:
                return 'yolo11m.pt', 'requirements_jetson.txt'
        
        elif self.is_raspberry_pi:
            if self.memory_gb >= 8:
                return 'yolo11x.pt', 'requirements.txt'
            elif self.memory_gb >= 4:
                return 'yolo11l.pt', 'requirements.txt'
            else:
                return 'yolo11m.pt', 'requirements.txt'
        
        else:
            # Default for other platforms (e.g., desktop)
            if self.memory_gb >= 16:
                return 'yolo11x.pt', 'requirements.txt'
            elif self.memory_gb >= 8:
                return 'yolo11l.pt', 'requirements.txt'
            else:
                return 'yolo11m.pt', 'requirements.txt'
    
    def get_hardware_info(self) -> dict:
        """Get detailed hardware information"""
        return {
            'platform': self.platform,
            'is_jetson': self.is_jetson,
            'is_raspberry_pi': self.is_raspberry_pi,
            'memory_gb': self.memory_gb,
            'cpu_cores': self.cpu_cores,
            'optimal_model': self.get_optimal_model()[0],
            'requirements_file': self.get_optimal_model()[1]
        }
    
    def print_hardware_info(self):
        """Print hardware information to console"""
        info = self.get_hardware_info()
        print("🔍 Hardware Detection Results:")
        print(f"   Platform: {info['platform']}")
        print(f"   Jetson Device: {'Yes' if info['is_jetson'] else 'No'}")
        print(f"   Raspberry Pi: {'Yes' if info['is_raspberry_pi'] else 'No'}")
        print(f"   Memory: {info['memory_gb']:.1f} GB")
        print(f"   CPU Cores: {info['cpu_cores']}")
        print(f"   Recommended Model: {info['optimal_model']}")
        print(f"   Requirements File: {info['requirements_file']}")


if __name__ == "__main__":
    detector = HardwareDetector()
    detector.print_hardware_info()
