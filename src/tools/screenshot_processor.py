import os
import time
from datetime import datetime
from PIL import Image
import json

class ScreenshotProcessor:
    def __init__(self):
        self.input_dir = "/home/lasko/akoben-clean/setups_manuels/a_traiter"
        self.output_dir = "/home/lasko/akoben-clean/setups_manuels/traites"
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_metadata(self, filename):
        """Extrait les infos du nom de fichier"""
        parts = filename.split('_')
        return {
            'date': parts[0],
            'time': parts[1],
            'timeframe': parts[2],
            'symbol': parts[3].split('.')[0]
        }

    def analyze_image(self, image_path):
        """Analyse simplifiée sans modifier Kora"""
        img = Image.open(image_path)
        return {
            'width': img.width,
            'height': img.height,
            'format': img.format,
            'analysis_timestamp': datetime.now().isoformat()
        }

    def run(self):
        while True:
            for filename in os.listdir(self.input_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    src = os.path.join(self.input_dir, filename)
                    dest = os.path.join(self.output_dir, filename)
                    
                    # Métadonnées + analyse de base
                    result = {
                        **self.extract_metadata(filename),
                        **self.analyze_image(src),
                        'status': 'processed'
                    }
                    
                    # Sauvegarde des résultats
                    with open(f"{dest}.json", "w") as f:
                        json.dump(result, f, indent=2)
                    
                    os.rename(src, dest)
                    print(f"Processed: {filename} -> {dest}.json")
            
            time.sleep(10)

if __name__ == "__main__":
    processor = ScreenshotProcessor()
    processor.run()