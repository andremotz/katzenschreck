"""Results folder cleanup utility for disk space management"""

import os
import shutil


def cleanup_results_folder(results_folder, usage_threshold):
    """
    Deletes the oldest images in results_folder when the root partition
    usage exceeds usage_threshold (e.g. 0.8 for 80%).
    """
    try:
        total, used, _ = shutil.disk_usage("/")
        usage = used / total
        if usage < usage_threshold:
            return  # Nothing to do

        # Check if directory exists
        if not os.path.exists(results_folder):
            return  # Directory doesn't exist, nothing to delete

        # All image files in results_folder (only .jpg)
        try:
            images = [os.path.join(results_folder, f)
                     for f in os.listdir(results_folder)
                     if f.lower().endswith('.jpg')]
        except OSError:
            return  # Error reading directory

        if not images:
            return  # No images present

        # Sort by creation time (oldest first)
        images.sort(key=os.path.getctime)

        # Delete until usage is below threshold or no images left
        for img in images:
            try:
                os.remove(img)
                total, used, _ = shutil.disk_usage("/")
                usage = used / total
                if usage < usage_threshold:
                    break
            except OSError:
                continue  # Error deleting, skip this file

    except (OSError, ValueError, PermissionError) as e:
        print(f"Error in cleanup_results_folder: {e}")
        return