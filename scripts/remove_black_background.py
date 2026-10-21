from PIL import Image

def remove_black(input_path, output_path, threshold=30):
    img = Image.open(input_path).convert("RGBA")
    pixels = img.getdata()

    new_pixels = []
    for r, g, b, a in pixels:
        if r < threshold and g < threshold and b < threshold:
            new_pixels.append((r, g, b, 0))  # 
        else:
            new_pixels.append((r, g, b, a))

    img.putdata(new_pixels)
    img.save(output_path, "PNG")

remove_black(r"C:\Users\yassi\Downloads\580453277_184851154_1280x1280.webp", "output.png")