from langgraph.graph import StateGraph,START,END
from app.ai.graph.state import AgentState
from app.ai.graph.nodes import intent_node,retrieve_node,answer_node
g=StateGraph(AgentState); g.add_node('intent',intent_node); g.add_node('retrieve',retrieve_node); g.add_node('answer',answer_node); g.add_edge(START,'intent'); g.add_edge('intent','retrieve'); g.add_edge('retrieve','answer'); g.add_edge('answer',END); workflow=g.compile()
def run_workflow(query,session_id='default',history=None,language=None): return workflow.invoke({'query':query,'session_id':session_id,'history':history or [],'language':language})
