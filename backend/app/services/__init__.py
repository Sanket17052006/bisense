"""Services package.

Member 5 ships only `files.py` (upload storage). The remaining subpackages
(agents=Member 2, rag=Member 3, vision+compliance=Member 4,
verification=Member 6) are reserved — owners drop their implementations here
and wire them through the existing route shells. See docs/api.md.
"""