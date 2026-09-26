from app.ai.router.router import IntentRouter
from app.rag.pipeline.retrieval_pipeline import retrieve
from app.ai.llm.response_generator import generate_response
router=IntentRouter()
def intent_node(s): s['intent']=router.route(s['query']).value; return s
def retrieve_node(s): s['evidence']=retrieve(s['query'],6); return s
def answer_node(s):
 s['answer']=generate_response(s['query'],s.get('evidence',[]),s.get('history',[]),s.get('intent','general'),s.get('language')); s['citations']=[{'source':x.get('source',''),'page':x.get('page'),'chunk_id':x.get('chunk_id'),'score':x.get('score')} for x in s.get('evidence',[])]; return s
