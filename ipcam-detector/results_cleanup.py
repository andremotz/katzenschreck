import os
import shutil

def cleanup_results_folder(results_folder, usage_threshold):
    """
    Löscht die ältesten Bilder im results_folder, wenn die Root-Partition mehr als usage_threshold (z.B. 0.8 für 80%) belegt ist.
    """
    try:
        total, used, free = shutil.disk_usage("/")
        usage = used / total
        if usage < usage_threshold:
            return  # Nichts zu tun

        # Prüfe, ob das Verzeichnis existiert
        if not os.path.exists(results_folder):
            return  # Verzeichnis existiert nicht, nichts zu löschen

        # Alle Bilddateien im results_folder (nur .jpg)
        try:
            images = [os.path.join(results_folder, f) for f in os.listdir(results_folder) if f.lower().endswith('.jpg')]
        except OSError:
            return  # Fehler beim Lesen des Verzeichnisses
            
        if not images:
            return  # Keine Bilder vorhanden
            
        # Nach Erstellungszeit sortieren (älteste zuerst)
        images.sort(key=lambda x: os.path.getctime(x))

        # Lösche so lange, bis usage wieder unter dem threshold ist oder keine Bilder mehr da sind
        for img in images:
            try:
                os.remove(img)
                total, used, free = shutil.disk_usage("/")
                usage = used / total
                if usage < usage_threshold:
                    break
            except OSError:
                continue  # Fehler beim Löschen, überspringe diese Datei
                
    except Exception as e:
        print(f"Error in cleanup_results_folder: {e}")
        return
