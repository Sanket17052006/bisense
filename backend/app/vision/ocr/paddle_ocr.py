def ocr_image_paddle(path):
 from paddleocr import PaddleOCR
 ocr=PaddleOCR(use_angle_cls=True,lang='en'); result=ocr.ocr(path,cls=True); return '\n'.join(item[1][0] for page in result or [] for item in page or [])
