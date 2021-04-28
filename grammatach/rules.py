import re
class Constraint:

  # value is a string; either a single feature value like "Len"
  # or else a pipe-separated set of options: "Ecl|Len"
  def __init__(self, value, message, isOptional=False):
    if '|' in value:
      self._value = '('+value+')'
    else:
      self._value = value
    self._message = message
    self._isOptional = isOptional

  # pass list of feature values (so, ['Len'] or ['Ecl','Emp'], usually,
  # but also None if feature not set) and
  # return True iff constraint is satisfied
  def isSatisfied(self, udValues):
    if self._isOptional:
      return True
    if udValues==None:
      return False
    else:
      return any(re.fullmatch(self._value, val) for val in udValues)

  # slight variant of previous method
  # here, we pass a single feature value that appears in UD file
  # (so, just "Len", or "Emp", never None)
  # and return True iff constraint explains existence of this feature value
  def explainsValue(self, oneValue):
    return re.fullmatch(self._value, oneValue)

  def getMessage(self):
    return self._message
  
  def __str__(self):
    if self._isOptional: 
      return 'Optional constraint that feature value ' + self._value + ' is allowed'
    else:
      return 'Obligatory constraint that feature value ' + self._value + ' must appear'
