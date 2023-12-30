import sys

import talib.abstract

# Manually set TAlib's indicators as functions in this module
for fcn_name in talib.abstract.__TA_FUNCTION_NAMES__:
    setattr(sys.modules[__name__], fcn_name, getattr(talib.abstract, fcn_name))
