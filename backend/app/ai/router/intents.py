from enum import Enum
class Intent(str,Enum): STANDARDS='standards'; CERTIFICATION='certification'; QCO='qco'; LABORATORY='laboratory'; HALLMARKING='hallmarking'; CONSUMER='consumer'; LICENSING='licensing'; COMPLIANCE='compliance'; GENERAL='general'
KEYWORDS={
Intent.STANDARDS:['standard','indian standard','specification','clause','is '],Intent.CERTIFICATION:['certificate','certification','scheme'],Intent.QCO:['qco','quality control order','compulsory'],Intent.LABORATORY:['laboratory','lab','testing'],Intent.HALLMARKING:['hallmark','gold','silver','jewellery','jewelry'],Intent.CONSUMER:['consumer','complaint','grievance'],Intent.LICENSING:['licence','license','licensing','application','renewal'],Intent.COMPLIANCE:['compliance','compliant','label','mrp','manufacturer','quantity']}
def keyword_intent(text):
 q=text.lower(); scores={i:sum(w in q for w in ws) for i,ws in KEYWORDS.items()}; best=max(scores,key=scores.get); return best if scores[best] else Intent.GENERAL
