from app.vision.ocr.tesseract_ocr import ocr_image
from app.vision.product.product_info import extract_product_info
def scan_label(path):
 text=ocr_image(path); return extract_product_info(text)
