from token import UDToken
from rules import Constraint

class GoidelicToken(UDToken):
  
  def __init__(self, lineNumber=None, line=None):
    super().__init__(lineNumber, line)
    self.autosetFeatures()

 #################### Pan-Gaelic booleans ####################
 
  # see predictCaseADJ, predictGenderADJ, predictNumberADJ
  # Determines when the features of the adjective should agree with noun
  # True even for "dhá fhear mhóra"... deal with that in predictNumberADJ
  # Can add additional conditions/exceptions in children...
  def isAttributiveAdjective(self):
    # need ultimate head: "príosúnaigh Bheilgeacha agus Fhrancacha"
    head = self.getUltimateHead()
    # allow nmod: "saincheisteanna comhshaoil agus áitiula" 
    return self['upos']=='ADJ' and head.isNominal() and \
           self.getDeprel() in ['amod', 'flat:name', 'nmod'] and \
           self['index'] > head['index'] and \
           not self.has('Degree','Cmp') and not self.has('Degree','Sup')

  def isPluralPossessive(self):
    return self['Poss']!=None and self.has('Number','Plur')

 #################### Pan-Gaelic feature predictions ##################

  # isEclipsable already checked in child class
  def predictNounEclipsis(self):
    pr = self.getPredecessor()
    if pr.isPluralPossessive():
      return [Constraint('Ecl','Should be eclipsed by preceding possessive')]
    return []

  def predictCaseADJ(self):
    if self.isAttributiveAdjective():
      head = self.getUltimateHead()
      if head['Case']!=None:
        theCase = head['Case'][0]
        return [Constraint(theCase, 'Adjective case should match noun it modifies')]
    return []

  def predictGenderADJ(self):
    if self.isAttributiveAdjective():
      head = self.getUltimateHead()
      if head['Gender']!=None:
        theGender = head['Gender'][0]
        return [Constraint(theGender, 'Adjective gender should match noun it modifies')]
    return []

  def predictTenseVERB(self):
    if self.has('Mood','Cnd') or self.has('Mood','Imp') or \
         self.has('Foreign','Yes'):
      return []
    return [Constraint('Fut|Past|Pres', 'Verbs that are not conditional, imperfect, or foreign must be past, present, or future tense')]
    return []

 ################### Methods requiring override in children ##################

  def predictVerbFormNOUN(self):
    return [Constraint('Inf|Vnoun|None', 'Nouns can have VerbForm feature')]

  def hasInitialVowel(self):
    raise NotImplementedError('should only be called for specific language')
    
  def isLenitable(self):
    raise NotImplementedError('should only be called for specific language')

  def isLenited(self):
    raise NotImplementedError('should only be called for specific language')

  def isEclipsable(self):
    raise NotImplementedError('should only be called for specific language')

  def isEclipsed(self):
    raise NotImplementedError('should only be called for specific language')

  def autosetFeatures(self):
    raise NotImplementedError('should only be called for specific language')
