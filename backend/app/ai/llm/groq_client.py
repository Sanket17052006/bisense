from functools import lru_cache
from app.core.config import get_settings
@lru_cache
def get_chat_model():
 s=get_settings()
 if not s.groq_api_key:return None
 from langchain_groq import ChatGroq
 return ChatGroq(api_key=s.groq_api_key,model=s.groq_model,temperature=.1)
