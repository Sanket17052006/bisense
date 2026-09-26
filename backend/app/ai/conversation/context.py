def build_context(history,query): return '\n'.join([f"{x.get('role')}: {x.get('content')}" for x in history[-10:]]+[f'user: {query}'])
