from app.core.config import get_settings
from app.vision.ocr.preprocessing import preprocess_image
def ocr_image(path):
 import pytesseract,os
 s=get_settings();
 if s.tesseract_cmd: pytesseract.pytesseract.tesseract_cmd=s.tesseract_cmd
 p=preprocess_image(path)
 try:return pytesseract.image_to_string(p,config='--psm 6').strip()
 finally: os.unlink(p) if os.path.exists(p) else None
