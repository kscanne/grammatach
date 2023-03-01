import re
class Constraint:

  # value is a string; either a single feature value like "Len"
  # or else a pipe-separated set of options: "Ecl|Len"
  # "None" is permitted as a feature value; if it appears alone,
  # then the constraint means the feature should not appear at all.
  # If it appears piped together with other values, e.g. "Ecl|Len|None",
  # then the other values might appear, but not necessarily
  def __init__(self, value, message):
    self._permitted = set(value.split('|'))
    self._message = message

  # pass list of feature values (so, ['Len'] or ['Ecl','Emp'], usually,
  # but also None if feature not set) and
  # return True iff this constraint is satisfied
  def isSatisfied(self, udValues):
    if udValues==None:
      return 'None' in self._permitted
    else:
      return any(val in self._permitted for val in udValues)

  # slight variant of previous method
  # here, we pass a single feature value that appears in UD file
  # (so, just "Len", or "Emp", never None)
  # and return True iff constraint explains existence of this feature value
  def explainsValue(self, oneValue):
    return oneValue in self._permitted

  def getMessage(self):
    return self._message
  
  def __str__(self):
    return 'Constraint that feature value ' + '|'.join(self._permitted) + ' must appear'
