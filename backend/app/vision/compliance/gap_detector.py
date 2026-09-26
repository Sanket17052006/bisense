def detect_gaps(info,evidence):
 f=[]
 if info.get('is_numbers'): f.append({'field':'is_number','value':', '.join(info['is_numbers']),'status':'needs_verification','reason':'IS number detected; image OCR alone does not establish legal compliance.','evidence':evidence[:5]})
 else: f.append({'field':'is_number','value':None,'status':'unavailable','reason':'No IS number was reliably extracted.','evidence':[]})
 status='needs_verification' if info.get('licence_numbers') else 'unavailable'
 f.append({'field':'licence_number','value':', '.join(info.get('licence_numbers',[])) or None,'status':status,'reason':'Detected licence information should be checked against authoritative BIS records.','evidence':evidence[:3]})
 return f
