from collections import defaultdict
class ConversationMemory:
    def __init__(self,max_messages=20): self.store=defaultdict(list); self.max_messages=max_messages
    def get(self,sid): return list(self.store[sid])
    def add(self,sid,role,content): self.store[sid]=(self.store[sid]+[{'role':role,'content':content}])[-self.max_messages:]
memory=ConversationMemory()
