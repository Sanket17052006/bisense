from app.vision.ocr.tesseract_ocr import ocr_image
from app.vision.product.product_info import extract_product_info
from app.vision.product.vision_fallback import analyze_with_vision, is_meaningful_extraction

def scan_label(path):
    text = ocr_image(path)
    extracted = extract_product_info(text)
    
    if not is_meaningful_extraction(extracted):
        vision_result = analyze_with_vision(path)
        if "error" not in vision_result:
            extracted = {
                **extracted,
                "is_number": vision_result.get("is_number"),
                "licence_number": vision_result.get("licence_number"),
                "mrp": vision_result.get("mrp"),
                "quantity": vision_result.get("quantity"),
                "manufacturer": vision_result.get("manufacturer"),
                "product_name": vision_result.get("product_name"),
                "batch": vision_result.get("batch"),
                "hsn_code": vision_result.get("hsn_code"),
                "raw_text": vision_result.get("raw_text") or text
            }
    
    return extracted
