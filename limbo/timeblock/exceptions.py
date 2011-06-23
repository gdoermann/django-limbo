""" General Time Block calculation errors """
class TimeblockError(ValueError):
    pass

class TimeblockOverlapError(TimeblockError):
    pass

class TimeblockFullOverlapError(TimeblockOverlapError):
    pass

class TimeblockArithmeticError(TimeblockError):
    pass

class TimeblockSplitError(TimeblockArithmeticError):
    pass
