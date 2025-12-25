from PIL import Image, ImageDraw, ImageFont
import os

def create_pdf(input_file, output_file):
    print(f"Reading {input_file}...")
    
    # A4 size at 150 DPI approx (1240 x 1754)
    # 2480 x 3508 is 300 DPI (Better quality)
    W, H = 2480, 3508
    img = Image.new('RGB', (W, H), "white")
    draw = ImageDraw.Draw(img)
    
    # Load Font
    try:
        # Use large font for 300 DPI
        font = ImageFont.truetype("arial.ttf", 40)
        font_bold = ImageFont.truetype("arialbd.ttf", 50)
    except:
        font = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        
    x, y = 100, 100
    line_height = 60
    
    draw.text((x, y), "TECH STACK DOCUMENTATION", font=font_bold, fill="black")
    y += 100
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                y += line_height // 2
                continue
                
            # Handle Headers
            if line.startswith("#"):
                current_font = font_bold
                text = line.replace("#", "").strip()
                y += 20
            else:
                current_font = font
                text = line
            
            # Simple wrapping (naive)
            # For this specific file, lines are short enough usually.
            # If line is super long, we might clip, but for a tech stack list it's fine.
            draw.text((x, y), text, font=current_font, fill="black")
            y += line_height
            
            if y > H - 100:
                print("Warning: Page overflow (Note: Single page implementation)")
                break
                
    img.save(output_file, "PDF", resolution=300.0)
    print(f"SUCCESS: Generated {output_file}")

if __name__ == "__main__":
    create_pdf("TECH_STACK.txt", "TECH_STACK.pdf")
