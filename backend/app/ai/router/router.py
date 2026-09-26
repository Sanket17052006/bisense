from app.ai.router.intents import keyword_intent
class IntentRouter:
    def route(self,text): return keyword_intent(text)
