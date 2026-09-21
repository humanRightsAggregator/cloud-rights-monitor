import io
import requests
from PIL import Image, ImageDraw, ImageFont

def create_story_card(title: str, image_url: str = "") -> io.BytesIO:
    """Generates a vertical 1080x1920 (9:16) Story card with headline text overlay."""
    canvas_w, canvas_h = 1080, 1920

    bg_loaded = False
    if image_url and image_url.startswith("http"):
        try:
            resp = requests.get(image_url, timeout=10)
            if resp.status_code == 200:
                bg_img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                bg_loaded = True
        except Exception as e:
            print(f"[!] Base image download failed for story card: {e}")

    if bg_loaded:
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
    else:
        # Styled dark gradient fallback canvas for text-only reports
        canvas = Image.new("RGB", (canvas_w, canvas_h), color=(15, 20, 32))
        draw_bg = ImageDraw.Draw(canvas)
        for y in range(canvas_h):
            r = int(15 + (y / canvas_h) * 20)
            g = int(20 + (y / canvas_h) * 25)
            b = int(32 + (y / canvas_h) * 35)
            draw_bg.line([(0, y), (canvas_w, y)], fill=(r, g, b))

    # Add dark gradient overlay at bottom for high text contrast
    overlay = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    for y in range(800, canvas_h):
        alpha = int(235 * ((y - 800) / 1120))
        draw_overlay.line([(0, y), (canvas_w, y)], fill=(0, 0, 0, alpha))

    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # Safe default font loader
    try:
        font_tag = ImageFont.load_default(size=36)
        font_title = ImageFont.load_default(size=52)
    except Exception:
        font_tag = ImageFont.load_default()
        font_title = ImageFont.load_default()

    # Red accent badge & wrapped text
    draw.text((80, 1100), "HUMAN RIGHTS MONITOR", fill=(235, 87, 87), font=font_tag)

    words = title.split()
    lines = []
    current_line = []

    for word in words:
        current_line.append(word)
        test_str = " ".join(current_line)
        bbox = draw.textbbox((0, 0), test_str, font=font_title)
        if (bbox[2] - bbox[0]) > 900:
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    y_text = 1180
    for line in lines[:5]:
        draw.text((80, y_text), line, fill=(255, 255, 255), font=font_title)
        y_text += 70

    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=90)
    buf.seek(0)
    return buf
