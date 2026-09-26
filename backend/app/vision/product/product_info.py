from app.vision.extraction.is_number import extract_is_numbers
from app.vision.extraction.licence_number import extract_licence_numbers
from app.vision.extraction.mrp import extract_mrp
from app.vision.extraction.quantity import extract_quantity
from app.vision.extraction.manufacturer import extract_manufacturer
from app.vision.product.product_detector import detect_product_type
def extract_product_info(text): return {'product_type':detect_product_type(text),'is_numbers':extract_is_numbers(text),'licence_numbers':extract_licence_numbers(text),'mrp':extract_mrp(text),'quantities':extract_quantity(text),'manufacturer':extract_manufacturer(text),'raw_text':text}
