def detect_product_type(text):
 q=text.lower();
 for typ,words in {'food':['food','milk','spice','flour'],'electrical':['switch','cable','wire','socket'],'jewellery':['gold','silver','hallmark','jewellery'],'cement':['cement'],'steel':['steel','bar','rod']}.items():
  if any(w in q for w in words): return typ
 return 'unknown'
