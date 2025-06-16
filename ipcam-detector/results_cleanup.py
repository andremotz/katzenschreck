import os
import shutil

def cleanup_results_folder(results_folder, usage_threshold):
    """
    Löscht die ältesten Bilder im results_folder, wenn die Root-Partition mehr als usage_threshold (z.B. 0.8 für 80%) belegt ist.
    """
    total, used, free = shutil.disk_usage("/")
    usage = used / total
    if usage < usage_threshold:
        return  # Nichts zu tun

    # Alle Bilddateien im results_folder (nur .jpg)
    images = [os.path.join(results_folder, f) for f in os.listdir(results_folder) if f.lower().endswith('.jpg')]
    # Nach Erstellungszeit sortieren (älteste zuerst)
    images.sort(key=lambda x: os.path.getctime(x))

    # Lösche so lange, bis usage wieder unter dem threshold ist oder keine Bilder mehr da sind
    for img in images:
        os.remove(img)
        total, used, free = shutil.disk_usage("/")
        usage = used / total
        if usage < usage_threshold:
            break
