import io
import requests
from PIL import Image, ImageDraw, ImageFont

def create_story_card(title: str, image_url: str) -> io.BytesIO:
    """Generates a vertical 1080x1920 (9:16) Story card with headline burned onto the image."""
    canvas_w, canvas_h = 1080, 1920

    # 1. Download and crop base image to 9:16 cover fit
    try:
        resp = requests.get(image_url, timeout=10)
        bg_img = Image.open(io.BytesIO(resp.content)).convert("RGB")
    except Exception:
        bg_img = Image.new("RGB", (canvas_w, canvas_h), color=(20, 24, 33))

    img_w, img_h = bg_img.size
    aspect_target = canvas_w / canvas_h
    aspect_img = img_w / img_h

    if aspect_img > aspect_target:
        new_w = int(img_h * aspect_target)
        offset = (img_w - new_w) // 2
        bg_img = bg_img.crop((offset, 0, offset + new_w, img_h))
    else:
        new_h = int(img_w / aspect_target)
        offset = (img_h - new_h) // 2
        bg_img = bg_img.crop((0, offset, img_w, offset + new_h))

    canvas = bg_img.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)

    # 2. Add semi-transparent gradient at bottom for text contrast
    overlay = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    for y in range(900, canvas_h):
        alpha = int(220 * ((y - 900) / 1020))
        draw_overlay.line([(0, y), (canvas_w, y)], fill=(0, 0, 0, alpha))

    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # 3. Load font
    try:
        font_tag = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 52)
    except Exception:
        font_tag = ImageFont.load_default()
        font_title = ImageFont.load_default()

    # 4. Draw Header Badge & Wrapped Title Text
    draw.text((80, 1150), "HUMAN RIGHTS MONITOR", fill=(235, 87, 87), font=font_tag)

    words = title.split()
    lines = []
    current_line = []

    for word in words:
        current_line.append(word)
        test_str = " ".join(current_line)
        bbox = draw.textbbox((0, 0), test_str, font=font_title)
        if (bbox[2] - bbox[0]) > 920:
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    y_text = 1220
    for line in lines[:5]:
        draw.text((80, y_text), line, fill=(255, 255, 255), font=font_title)
        y_text += 65

    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=90)
    buf.seek(0)
    return buf
