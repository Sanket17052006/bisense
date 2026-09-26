from typing import TypedDict
class AgentState(TypedDict, total=False): query:str; session_id:str; language:str|None; history:list[dict]; intent:str; evidence:list[dict]; answer:str; citations:list[dict]
