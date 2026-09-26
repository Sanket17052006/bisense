from app.ai.conversation.memory import memory
def get_history(sid): return memory.get(sid)
def append_message(sid,role,content): memory.add(sid,role,content)
