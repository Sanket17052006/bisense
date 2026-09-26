def format_source(r):
 s=r.get('source','unknown'); return s+(f" page {r['page']}" if r.get('page') else '')
