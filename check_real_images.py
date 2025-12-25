
from PIL import Image
from pathlib import Path

dir_path = Path(r"c:\Users\HP\Desktop\kartavya_submission\temp\images")
real_images = list(dir_path.glob("real_*.jpg"))

print(f"Found {len(real_images)} real images on disk.")

for img_path in real_images:
    try:
        with Image.open(img_path) as img:
            print(f"{img_path.name}: {img.size} ({img.format})")
    except Exception as e:
        print(f"{img_path.name}: Error {e}")
