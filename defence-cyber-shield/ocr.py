import cv2
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
def _preprocess(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return None
    height, width = image.shape[:2]
    if max(height, width) < 1600:
        scale = 1600 / max(height, width)
        image = cv2.resize(
            image,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_CUBIC
        )
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    processed = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )
    return processed
def extract_text(image_path):
    try:
        processed = _preprocess(image_path)
        if processed is None:
            return ""
        text = pytesseract.image_to_string(
            processed,
            config="--oem 3 --psm 6"
        )
        if not text.strip():
            text = pytesseract.image_to_string(
                processed,
                config="--oem 3 --psm 11"
            )
        if not text.strip():
            text = pytesseract.image_to_string(
                image_path,
                config="--oem 3 --psm 6"
            )
        return text.strip()
    except Exception as e:
        print("OCR ERROR:", e)
        return ""
