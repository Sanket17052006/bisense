import cv2
from pathlib import Path
def preprocess_image(path):
 im=cv2.imread(path)
 if im is None: raise ValueError('Cannot read image')
 g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY); g=cv2.resize(g,None,fx=1.5,fy=1.5); g=cv2.fastNlMeansDenoising(g); o=Path(path).with_name(Path(path).stem+'_prep.png'); cv2.imwrite(str(o),g); return str(o)
