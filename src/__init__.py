"""Spanish frequency list maker package."""

# Apply rioplatense lemma post-processing extensions (issues #17/#18) on import.
from src import utils as _utils
from src import lemma_fixes_1718 as _lemma_fixes_1718

_lemma_fixes_1718.apply_to_module(vars(_utils))
