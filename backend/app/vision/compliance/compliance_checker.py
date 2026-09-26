from app.vision.compliance.requirement_matcher import retrieve_requirements
from app.vision.compliance.gap_detector import detect_gaps
def check_compliance(info):
 e=retrieve_requirements(info); return {'overall_status':'needs_verification' if e or info.get('is_numbers') else 'unavailable','product':info,'findings':detect_gaps(info,e),'evidence':e,'disclaimer':'OCR/image recognition does not by itself establish legal compliance.'}
