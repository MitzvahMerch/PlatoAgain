from PIL import Image
import requests
from io import BytesIO

def place_logo():
    # 1. Load shirt and convert to RGB
    shirt = Image.open("./productimages/64000/Gildan_64000_Kelly_Green_Front_High.jpg").convert('RGB')
    
    # 2. Load logo and convert to RGB
    logo_url = "https://firebasestorage.googleapis.com/v0/b/mitzvahmerch-ac346.appspot.com/o/designs%2Fuser_0dl91099i%2F1739736557682_Psych.png?alt=media&token=a3336b7a-dc45-4f53-b9d9-d9cad87bb59f"
    response = requests.get(logo_url)
    logo = Image.open(BytesIO(response.content)).convert('RGB')
    
    # 3. Test each position
    positions = {
        'fullFront': {
            'size': (200, 200),
            'position': (500, 475)  # 50% left, 38% top of 1250px height
        },
        'centerChest': {
            'size': (154, 154),
            'position': (500, 437)  # 50% left, 35% top
        },
        'leftChest': {
            'size': (90, 90),
            'position': (640, 375)  # 64% left, 30% top
        },
        'centerBack': {
            'size': (180, 180),
            'position': (500, 350)  # 50% left, 28% top
        }
    }
    
    for placement, specs in positions.items():
        # Create a copy of the shirt
        preview = shirt.copy()
        
        # Resize logo
        resized_logo = logo.resize(specs['size'])
        
        # Simple paste without mask
        preview.paste(resized_logo, specs['position'])
        
        # Save
        preview.save(f"./productimages/previews/test/preview_{placement}.png")
        print(f"Created {placement} preview")

if __name__ == "__main__":
    place_logo()