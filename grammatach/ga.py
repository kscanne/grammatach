import re
import gadata
from goidelic import GoidelicToken
from rules import Constraint

class GAToken(GoidelicToken):

  def __init__(self, lineNumber=None, line=None):
    super().__init__(lineNumber, line)

  # don't want these as constraints since then a word mutated for no
  # linguistic reason wouldn't get flagged...
  # Irish-specific since gd only uses Form=Emp
  def autosetFeatures(self):
    if self.isLenited():
      self.addFeature('Form','Len')
    else:
      self.killFeature('Form','Len')
    if self.isEclipsed():
      self.addFeature('Form','Ecl')
    else:
      self.killFeature('Form','Ecl')
    if self.hasPrefixH():
      self.addFeature('Form','HPref')
    else:
      self.killFeature('Form','HPref')
    # pseudo-features
    if self.hasPrefixT():
      self.addFeature('XForm','TPref')

  def __getitem__(self, arg):
    answer = super().__getitem__(arg)
    if arg == 'deprel' and answer == 'compound':
      return 'nmod'
    else:
      return answer

  # others we're not bothering trying to predict:
  # Abbr, Dialect, Foreign, Typo
  def checkableFeatures(self):
    return [
            'Aspect',
            'Case',
            'Definite',
            #'Degree',
            'Form',
            'Gender',   # same as Number...
            'NounType',
            'Number',   # go léir, dhá X móra, chomh X...
            'NumType',
            'Mood',
            #'PartType',
            'Person',
            'Polarity',
            'Poss',
            'PrepForm',  # in ann, i gcomhair, faoi réir
            'PronType',
            'Reflex',
            'Tense',
            'VerbForm',
            'XForm'
           ]

  def predictFeatureValue(self, feat):
    return getattr(GAToken, 'predict'+feat+self['upos'], GAToken.noConstraint)(self)

  ####################### BOOLEAN METHODS ##########################

  # ok on Foreign=Yes b/c of gd words
  def isLenitable(self):
    return re.match(r'([bcdfgmpt]|sh?[lnraeiouáéíóú])', self['token'], flags=re.IGNORECASE)

  # ok on Foreign=Yes b/c of gd words
  def isLenited(self):
    return re.match(r'([bcdfgmpt]h[^f]|sh[lnraeiouáéíóú])', self['token'], flags=re.IGNORECASE) and re.match(r'(.[^h]|bheith)', self['lemma'], flags=re.IGNORECASE)

  def isEclipsable(self):
    return re.match(r'[aeiouáéíóúbcdfgpt]', self.demutatedToken(), flags=re.IGNORECASE)

  # permits mBriathar, MBRIATHAR, but not Mbriathar (to avoid "Ndugi", etc.)
  # allowed on Foreign=Yes too (ón bpier, ón dTower)
  # allowed on Abbr=Yes ("gCo.")
  def isEclipsed(self):
    return re.match(r'(n-?[AEIOUÁÉÍÓÚ]|n-[aeiouáéíóú]|m[Bb]|MB|g[Cc]|GC|n[DdGg]|N[DG]|bh[Ff]|BHF|b[Pp]|BP|d[Tt]|DT)', self['token'])

  # "lemmas" is a tuple of lemmas to match
  # lemma of self should be the last in the tuple
  def isInPhrase(self, lemmas):
    curr = self
    for i in range(len(lemmas)):
      if curr['lemma'] != lemmas[-1-i]:
        return False
      curr = curr.getPredecessor()
      if curr==None:
        return False
    return True

  def hasInitialF(self):
    return re.match(r'[fF]', self['lemma'])

  def hasInitialBMP(self):
    return re.match(r'[bmpBMP]', self['lemma'])

  def hasInitialDental(self):
    return re.match(r'[dntlsDNTLS]', self['lemma'])

  def hasFinalDental(self):
    return re.search(r'[dntls]$', self['token'].lower())

  # TODO: but what about déarfainn,abair? check token too?
  def hasInitialVowel(self):
    return re.match(r'[aeiouáéíóúAEIOUÁÉÍÓÚ]', self['lemma'])

  def hasLenitableS(self):
    return re.match(r's[lnraeiouáéíóú]', self['lemma'], flags=re.IGNORECASE)

  # this means must end in a consonant
  def hasSlenderFinalConsonant(self):
    return re.search('([^a]e|[éií])[^aeiouáéíóú]+$', self['token'].lower())

  # this means must end in a consonant
  def hasBroadFinalConsonant(self):
    return re.search('([aáoóuú]|ae)[^aeiouáéíóú]+$', self['token'].lower())

  def admitsPrefixT(self):
    return self.hasInitialVowel() or self.hasLenitableS()

  def hasPrefixT(self):
    return re.match(r't(-[aeiouáéíóú]|[AEIOUÁÉÍÓÚsS])', self['token'])

  def admitsPrefixH(self):
    return self.hasInitialVowel()

  def hasPrefixH(self):
    return re.match(r'h-?[aeiouáéíóúAEIOUÁÉÍÓÚ]', self['token']) and self.admitsPrefixH()

  def precedingCen(self):
    head = self.getHead()
    return head['index']==self['index']-1 and head['token'].lower()=='cén'

  # this really means preceding "sa", "san", "den", "don"
  # These must lenite a following noun according to C.O.
  def precedingLenitingPrepPlusArticle(self):
    pr = self.getPredecessor()
    if pr==None:
      return False
    return pr['lemma'] in ['i', 'de', 'do'] and self.anyPrecedingDefiniteArticle()

  # this really means "an" or variants, not "na"
  def precedingDefiniteArticle(self):
    pr = self.getPredecessor()
    if pr==None:
      return False
    tok = pr['token'].lower()
    return tok in ['an', "'n", 'a', "a'"] and self.anyPrecedingDefiniteArticle()

  # preceding an/na but also sa, san, den, don, ón, faoin, etc.
  # used primarily for propagating definiteness
  def anyPrecedingDefiniteArticle(self):
    pr = self.getPredecessor()
    if pr==None:
      return False
    return pr.has('PronType','Art')

  def isVerbalNounWithAg(self):
    pr = self.getPredecessor()
    if pr==None:
      return False
    return pr['lemma']=='ag' and self.has('VerbForm','Vnoun')

  def isPossessed(self):
    return any(t.has('Poss','Yes') for t in self.getDependents())

  def hasGachDependent(self):
    return any(t['lemma']=='gach' and t['upos']=='DET' for t in self.getDependents())

  def isQualifiedNoun(self):
    return self.isNominal() and any((t.isNominal() and t.has('Case','Gen')) or (t['upos']=='ADJ' and t['deprel']=='amod') for t in self.getDependents())

  # First any is for "Airteagal III" or "rang 5"
  # Second any is for stuff like "bus a dó", "rang a 5"
  def hasNumberSpecifier(self):
    return any(t['upos']=='NUM' and t['index']==self['index']+1 and t['deprel']=='nmod' for t in self.getDependents()) or any(t['lemma']=='a' and t['upos']=='PART' and t.has('PartType','Num') and t['index']==self['index']+1 and t.getHead()['upos']=='NUM' and t.getHead()['deprel']=='nmod' and t.getHead()['index']==self['index']+2 for t in self.getDependents())

  # nouns governing a definite noun in the genitive should be definite
  # *except* for cases like "rang Gaeilge", "fear Gaeltachta", etc.
  def hasPropagatingDefiniteDependent(self):
    exceptions = ['Gaeilge','Béarla','Gaeltacht','Eabhrais','Fraincis','Breatnais']
    return any(t.isNominal() and t['deprel']=='nmod' and t.has('Definite','Def') and not t.isInPP() and (t['lemma'] not in exceptions or t.anyPrecedingDefiniteArticle()) for t in self.getDependents())

  # not necessarily preceding; e.g. "sa dá chogadh"
  def anyDependentDefiniteArticle(self):
    return any(t.has('PronType','Art') for t in self.getDependents())

  # verbal particles that lenite following verb as in C.O. 10.4.2
  def isLenitingVerbalParticle(self):
    t = self['token'].lower()
    # handle "cha"?
    if t not in ['ní',"n'"] and t[-1]!='r':
      return False
    return (self['upos']=='PART' and self.has('PartType','Vb')) or \
           (self['upos']=='PART' and t=='nár') or \
           (self['upos']=='ADV' and t=='cár') or \
           (self['upos']=='SCONJ' and t in ['munar','murar','sarar','sular'])

  # a, ina, lena, etc. but *not* past tense ar, inar, lenar, etc.
  # Also includes the PRON case: "sin a bhfuil agam"; note we can't use
  # self.has('Tense','Past') to discard "duine ar chuir..." b/c of PRON case
  def isEclipsingRelativizer(self):
    return self.has('PronType','Rel') and not re.search('r$', self['token'].lower()) and (self.has('Form','Indirect') or self['upos']=='PRON')

  # Eclipsed forms after "ní": "ní bhfuair", "ní bhfaighidh", "ní bhfaighfeá"...
  def isEclipsedFaigh(self):
    return self['lemma']=='faigh' and \
      ((self.has('Mood','Ind') and self.has('Tense','Past')) or \
       self.has('Tense','Fut') or self.has('Mood','Cnd'))

  # "go" will be "go dtí" in fixed expression
  # CO also specifies prepositions that do take the dative as an alternative:
  # a, ag, ar, as, chuig, dar, de, do, faoi, fara,
  # go, i, ionsar, le, ó, roimh, trí, um
  def isInDativePP(self):
    nominativePrepositions = ['ach','amhail','gan','go','idir','mar','murach','ná','seachas']
    return self.isInPP() and not any(t['lemma'] in nominativePrepositions and t['deprel']=='case' for t in self.getDependents())

  # upos is 'NUM' and value is between 2 and 19 (though doesn't check "déag")
  def is2Thru19(self):
    if self['upos'] != 'NUM':
      return False
    if re.search('^[1-9][0-9]*$', self['lemma']):
      val = int(self['lemma'])
      return (val >= 2 and val <= 19)
    else:
      return self['lemma'] in ['dó','trí','ceathair','cúig','sé','seacht','ocht','naoi','deich']

  def has2Thru19(self):
    pr = self.getPredecessor()
    if pr==None:
      return False
    return pr['deprel']=='nummod' and pr.is2Thru19()

  def is3Thru6(self):
    if self['upos'] != 'NUM':
      return False
    return re.search('^[3-6]$', self['lemma']) or self['lemma'] in ['trí','ceathair','cúig','sé']

  def has3Thru6(self):
    pr = self.getPredecessor()
    if pr==None:
      return False
    return pr['deprel']=='nummod' and pr.is3Thru6()

  def is7Thru10(self):
    return self['lemma'] in ['seacht','7','ocht','8','naoi','9','deich','10']

  def has7Thru10(self):
    pr = self.getPredecessor()
    if pr==None:
      return False
    return pr['deprel']=='nummod' and pr.is7Thru10()

  # checking for "AUX" or lemma "is" does not suffice; there are some
  # with tag SCONJ ("más", "murar", etc.), or PART ("ba" in "ba mhó")
  def isCopula(self):
    return self.has('VerbForm','Cop')

  # at Goidelic level, basically checks for amod of a nominal
  # with some exceptions; Irish-specific exceptions added here
  def isAttributiveAdjective(self):
    pr = self.getPredecessor()
    if pr==None:
      return False
    return super().isAttributiveAdjective() and \
           not self.has('VerbForm','Part')  and \
           not (pr['lemma']=='go' and self['lemma']=='léir') and \
           pr['lemma']!='sách' and pr['lemma']!='chomh'

  ####################### END BOOLEAN METHODS ##########################

  def noConstraint(self):
    return [Constraint('None', 'This feature is incompatible with this part-of-speech tag')]

  # TODO: ar an gcéad dul síos, mar aon leis an gcaisleán (fixed),
  #
  # also called for NUM's that precede the NOUN they modify
  def predictNounEclipsis(self):
    if not self.isEclipsable():
      return [Constraint('!Ecl', '10.6: Not an eclipsable initial letter')]
    noun = self.getHead() if self['upos']=='NUM' else self
    pr = self.getPredecessor()
    if pr==None:
      return [Constraint('!Ecl', '10.6: Never eclipse a noun or number at the beginning of a sentence')]
    prToken = pr['token'].lower()
    if self.isInPhrase(('mar','an','céanna')) or \
       self.isInPhrase(('thar','ais')) or \
       self.isInPhrase(('um','an','taca')):
      return [Constraint('Ecl', '10.6.1.a: Should be eclipsed in set phrase')]
    if pr.has('PronType','Art') and pr.has('Number','Sing') and \
         pr['lemma'] not in ['de','do','i'] and \
         not self.hasInitialDental() and not self.hasInitialVowel() and \
         noun.isInDativePP() and noun.has('Case','Nom'):
      return [Constraint('Ecl|Len', '10.6.1.a: Should be eclipsed or lenited by the preceding definite article')]
    # NB. gpl noun can be Number=Sing: "seolta na dtrí bhád"
    if prToken=='na' and noun.has('Case','Gen') and pr.has('Number','Plur'):
      return [Constraint('Ecl', '10.6.1.b: Should be eclipsed by preceding “na” in genitive plural')]
    if self['token'].lower()=='dhá':  # bhur dhá mbád; in dhá bhád
      return [Constraint('!Ecl', '10.6.2.e1: Do not eclipse “dhá”')]
    if pr.isPluralPossessive():
      if self['lemma']=='céile' and self.isInPP() and pr.has('Person','3'):
        # TODO: change IDT annotation?
        return [Constraint('Len','Lenite “chéile” in various prepositional phrases')]
      else:
        return [Constraint('Ecl','10.6.2: Should be eclipsed by preceding plural possessive')]
    if prToken=='dhá' and pr.getPredecessor()!=None and pr.getPredecessor().isPluralPossessive():
      return [Constraint('Ecl','10.6.2.e2: Should be eclipsed by plural possessive + dhá')]
    if pr['deprel']=='nummod' and pr.is7Thru10():
      if self['lemma'] in ['cent', 'euro', 'déag']:
        return [Constraint('!Ecl', '10.6.3.e1: Never eclipse “cent”, “euro”, or “déag”')]
      else:
        return [Constraint('Ecl', '10.6.3: Should be eclipsed by number 7-10')]
    if prToken=='i' and (pr['deprel']=='case' or self['deprel']=='fixed'):
      return [Constraint('Ecl', '10.6.4.a: Should be eclipsed by preceding “i”')]
    if prToken=='ar' and pr['upos']=='ADP':
      if self['lemma']=='diaidh': # i ndiaidh ar ndiaidh
        return [Constraint('Ecl', '10.6.4.b: Should be eclipsed in set phrase')]
      # ar dhóigh, ar ndóigh, ar dóigh are all possible!
      if self['lemma']=='dóigh':
        return [Constraint('Ecl|!Ecl', '10.6.4.b: Optionally eclipsed in set phrase')]
      if self['lemma'] in ['cúl','tús']:
        return [Constraint('Ecl|Len', '10.6.4.b: Can be eclipsed in set phrase')]
    if prToken=='dar' and self['lemma'] in ['dóigh']:
      return [Constraint('Ecl', '10.6.4.b: Should be eclipsed in set phrase')]
    if re.match('d[aá]r$', prToken) and self.demutatedToken().lower()=='cionn':
      return [Constraint('Ecl', '10.6.4.b: Should be eclipsed in set phrase')]
    if prToken=='fá' and pr['upos']=='ADP' and self['lemma']=='taobh':
      return [Constraint('Ecl|Len', '10.6.4.b: Can be eclipsed in set phrase')]
    if prToken=='go' and self['lemma'] in ['cuimhin', 'díth', 'dtí', 'fios']:
      return [Constraint('Ecl', '10.6.4.b: Should be eclipsed in set phrase')]
    if prToken=='cá' and self['lemma']=='fios':
      return [Constraint('Ecl', '10.6.5: Should be eclipsed in set phrase “cá bhfios”')]
    return [Constraint('!Ecl','10.6: Not sure why this is eclipsed')]

  def predictVerbEclipsis(self):
    if not self.isEclipsable():
      return [Constraint('!Ecl', '10.8: Not an eclipsable initial letter')]
    pr = self.getPredecessor()
    if pr==None:
      return [Constraint('!Ecl', '10.8: Sentence initial verb cannot be eclipsed')]
    prToken = pr['token'].lower()
    # TODO: ADP "faoina ndearna", "gáire faoina ndúirt sé", 'dá bhfuil agam'
    if pr.isEclipsingRelativizer():
      return [Constraint('Ecl', '10.8.1: Should be eclipsed by preceding verbal particle introducting a relative clause')]
    if (pr.has('PartType','Vb') and prToken in ['go','nach']) or \
       (pr.has('PartType','Cmpl') and prToken in ['go','nach']) or \
       (pr['upos']=='ADV' and prToken=='cá') or \
       (pr['upos']=='SCONJ' and \
           prToken in ['dá','go','mara','muna','mura','sula']):
      return [Constraint('Ecl', '10.8.2.a: Should be eclipsed by preceding verbal particle')]
    if pr.has('PartType','Vb') and prToken=='an':
      if self.hasInitialVowel():
        return [Constraint('!Ecl', '10.8.2.a.e1: Do not eclipse an initial vowel after interrogative particle “an”')]
      else:
        return [Constraint('Ecl', '10.8.2.a: Should be eclipsed by preceding interrogative particle “an”')]

    if self.isEclipsedFaigh() and prToken=='ní':
      return [Constraint('Ecl', '10.8.2.b: Special forms of the verb “faigh” should be eclipsed following “ní”')]
    return [Constraint('!Ecl','10.8: Not sure why this verb is eclipsed')]

  def predictAdjectiveLenition(self):
    if not self.isLenitable():
      return [Constraint('!Len', '10.3: Cannot lenite an unlenitable letter')]
    # 10.3.1
    if self.isAttributiveAdjective():
      h = self.getHead()
      # TODO: exception "saor in aisce", "cothrom le dáta", srl. 10.3.1.e1
      # TODO: tuairisc réasúnta cuimsitheach... ADV blocks lenition?
      #   or "cuma chomh socair" (train 2554)
      # TODO: need ultimate head "príosúnaigh Bheilgeacha agus Fhrancacha"
      # TODO: idir bheag agus mhór (not in CO... CB+corpus only)
      # TODO: after beirt+gpl? CB+corpus
      if h.has('Gender','Fem') and h.has('Number','Sing'):
        if h.has('Case','Nom') or h.has('Case','Dat') or h.has('Case','Voc'):
          return [Constraint('Len', '10.3.1.a: Adjective is lenited after a feminine noun in the nominative, dative, or vocative singular')]
      elif h.has('Gender','Masc') and h.has('Number','Sing'):
        if h.has('Case','Gen') or h.has('Case','Voc'):
          return [Constraint('Len', '10.3.1.b: Adjective is lenited after genitive or vocative singular masculine noun')]
      elif h.has('Number','Plur') and h.has('Case','Nom') and \
           h.hasSlenderFinalConsonant():
        if h['lemma'].lower()=='caora':
          return [Constraint('!Len', '10.3.1.c.e1: Do not lenite adjectives after “caoirigh”')]
        else:
          return [Constraint('Len', '10.3.1.c: Adjective is lenited after a nominative plural noun ending in a slender consonant')]
      hpr = h.getPredecessor()
      if hpr!=None:
        if h.has('Number','Sing'):
          if re.search(r'^dh?á$', hpr['token'].lower()):
            return [Constraint('Len', '10.3.1.d.i: Adjective is lenited after a noun preceded by “dá” or “dhá”')]
          if hpr.is3Thru6() or hpr.is7Thru10():
            return [Constraint('Len', '10.3.1.d.ii: Adjective is lenited after a noun preceded by numbers 3–10')]
        if h.demutatedToken().lower()=='cinn': # "chinn" itself an error
          if hpr.is3Thru6() or hpr.is7Thru10():
            return [Constraint('Len', '10.3.1.d.iii: Adjective is lenited after plural noun “cinn” preceded by numbers 3–10')]
      if h.isInDativePP() and h.has('Gender','Masc') and h.has('Number','Sing'):
        return [Constraint('Len|!Len', '10.3.1.e: Lenition is optional adjectives following masculine nouns in the dative')]
    # 10.3.3 dhá agus dháréag... tagged as NUM and NOUN resp in UD (see FGB)
    # 10.3.4 déag agus fichead... tagged as NOUN in UD
    # 10.3.5 in compounds (ollmhór, etc.)
    # 10.3.6 After copula:
    pr = self.getPredecessor()
    if pr!=None and pr.isCopula() and (pr.has('Tense','Past') or pr.has('Mood','Cnd')):
      return [Constraint('Len', '10.3.6: Adjective is lenited after past or conditional copula')]
    return [Constraint('!Len', '10.3: Not sure why this adjective is lenited')]

  def predictNounLenition(self):
    if not self.isLenitable():
      return [Constraint('!Len', 'Cannot lenite an unlenitable letter')]
    pr = self.getPredecessor()
    prToken = pr['token'].lower()

    # 10.2.1
    if pr!=None and self.anyPrecedingDefiniteArticle() and pr.has('Number','Sing') and prToken!='na':
      if self.hasInitialDental():
        return [Constraint('!Len', '10.2.1.e1: Do not lenite a noun beginning with d, t, or s after the definite article')]
      if self.precedingDefiniteArticle():  # just "an"
        if self.has('Case','Gen') and self.has('Gender','Masc') and \
           self.has('Number','Sing'):
          return [Constraint('Len', '10.2.1.b: Must lenite a masculine singular noun in the genitive after the definite article')]
        elif self.isInDativePP():
          return [Constraint('Ecl|Len', '10.2.1.c: Can either eclipse or lenite in the dative after the definite article')]
        elif self.has('Case','Nom') and self.has('Gender','Fem') and \
           self.has('Number','Sing'):
          return [Constraint('Len', '10.2.1.a: Must lenite a feminine singular noun after the definite article')]
      elif self.precedingLenitingPrepPlusArticle(): # san, sa, den, don
        return [Constraint('Len', '10.2.1.c: Always lenite after sa, san, den, or don')]
      else: # remainder are examples like "faoin", "fén", "ón"
        return [Constraint('Ecl|Len', '10.2.1.c: Can either eclipse or lenite after faoin, ón, etc.')]

    # 10.2.2
    if self.has('Case', 'Voc') and any(t.has('PartType','Voc') for t in self.getDependents()):
      return [Constraint('Len', '10.2.2: Always lenite after vocative particle')]

    # 10.2.3
    if pr.has('Poss','Yes'):
      if pr['lemma'] in ['mo', 'do'] or pr.has('Gender','Masc'):
        return [Constraint('Len','10.2.3.a: Always lenite after possessives mo, do, or singular masculine “a”')]
      if pr.has('Gender','Fem'):
        return [Constraint('!Len','10.2.3.a: Never lenite after feminine possessive')]
    if pr['lemma'] in ['gach_uile', 'uile']:
      return [Constraint('Len','10.2.3.b: Always lenite after the adjective “uile”')]
    if pr['lemma'] in ['aon', 'céad']:
      if self.hasInitialDental():
        return [Constraint('!Len', '10.2.3.c.e1: Do not lenite a noun beginning with d, t, or s after “aon” or “céad”')]
      else:
        if pr['upos']=='DET':
          return [Constraint('Len', '10.2.3.c: Lenite a noun after “aon”')]
        elif pr['upos']=='NUM':
          if pr.has('NumType','Ord') or pr['lemma']=='aon':
            return [Constraint('Len', '10.2.4.a: Lenite a noun after “aon” or ordinal “céad”')]

    # 10.2.4
    if pr['upos']=='NUM':
      if prToken in ['dá','dhá']:
        prpr = pr.getPredecessor()
        if prpr.has('Poss','Yes') and (prpr.has('Gender','Fem') or prpr.has('Number','Plur')):
          return [Constraint('!Len', '10.2.4.b.e1: Do not lenite after “dhá” if preceded by plural or feminine possessive')]
        return [Constraint('Len', '10.2.4.b: Lenite after numbers “dá” or “dhá”')]
      elif self.has3Thru6():
        if self['lemma'] in ['cent', 'bliain', 'seachtain', 'ceann', 'cloigeann', 'fiche', 'pingin', 'trian', 'troigh', 'uair']:
          return [Constraint('!Len', '10.2.4.c.e1: Do not lenite certain special plural forms after numbers 3-6')]
        else:
          return [Constraint('Len', '10.2.4.c: Lenite nouns after numbers 3-6')]

    # 10.2.5
    if pr['upos']=='PART' and pr.has('PartType','Inf') and pr['lemma']=='a' and self.has('VerbForm','Inf'):
      return [Constraint('Len', '10.2.5.a: Always lenite a verbal noun after the preposition “a”')]
    if pr['upos']=='ADP' and not pr.has('Poss','Yes'):
      if pr['lemma'] in ['de', 'do', 'a', 'faoi', 'ionsar', 'mar', 'ó', 'roimh', 'trí']:
        return [Constraint('Len', '10.2.5.a: Always lenite after certain simple prepositions')]
      elif pr['lemma']=='um':
        if self.hasInitialBMP():
          return [Constraint('!Len', '10.2.5.a.e1: Do not lenite nouns starting with b, m, or p after “um”')]
        else:
          return [Constraint('Len', '10.2.5.a: Always lenite after certain simple prepositions')]
      elif pr['lemma']=='ar':
        if self['lemma'] in gadata.unlenitedAfterAr:
          if self.isQualifiedNoun():
            return [Constraint('Len', '10.2.5.b.e1: Lenite a noun after “ar” when it has an adjective or genitive noun dependent')]
          else:
            return [Constraint('Len|!Len', '10.2.5.b.e2: Noun may be unlenited after “ar” when used in an adverbial phrase')]
        else:
          return [Constraint('Len', '10.2.5.b: Typically we lenite a noun after “ar”')]
      elif pr['lemma']=='gan':
        if self.isQualifiedNoun():
          return [Constraint('!Len', '10.2.5.c.e1: Do not lenite a noun after “gan” when it has an adjective or genitive noun dependent')]
        elif pr['head']!=self['index']:
          return [Constraint('!Len', '10.2.5.c.e2: Do not lenite a noun after “gan” when it is the object of a verbal noun')]
        elif self.hasInitialDental() or self.hasInitialF():
          if self['lemma']=='fios':
            return [Constraint('Len', '10.2.5.c.e3: Lenite after “gan” in the set phrase “gan fhios”')]
          else:
            return [Constraint('!Len', '10.2.5.c.e4: Do not lenite a noun after “gan” when it starts with d, t, s, or f')]
        elif self['VerbForm']!=None:
          return [Constraint('!Len', '10.2.5.c.e5: Do not lenite a verbal noun after “gan”')]
        elif self['upos']=='PROPN':
          return [Constraint('!Len', '10.2.5.c.e6: Do not lenite a proper name after “gan”')]
        else:
          return [Constraint('Len', '10.2.5.c: Lenite a noun after “gan”')]
      elif pr['lemma']=='thar':
        if self['lemma'] in gadata.unlenitedAfterThar:
          return [Constraint('Len|!Len', '10.2.5.e.e2: Noun may be unlenited after “thar” when used in an adverbial phrase')]
        else:
          return [Constraint('Len', '10.2.5.e: Lenite a noun after “thar”')]

    # handle idir separately since we need to check coordination, no "pr"

    # 10.2.6

    # 10.2.7; use head not predecessor for "tuairisc pharlaiminte agus phobail"
    hd = self.getHead()
    if hd.isNominal() and hd.has('Case','Nom') and hd.has('Gender','Fem') and hd.has('Number','Sing') and self.has('Case','Gen') and not self.has('Definite','Def'):
      if hd.hasFinalDental() and self.hasInitialDental():
        return [Constraint('!Len', '10.2.7.a: Do not lenite an initial dental after a feminine noun ending in a dental')]
      if self.hasInitialF():
        if hd['lemma'] in ['beirt', 'dís']:
          return [Constraint('Len', '10.2.7.b.e1: Lenite an initial f after “beirt” or “dís”')]
        else:
          return [Constraint('!Len', '10.2.7.b: Do not lenite an initial f after a feminine noun')]
      if self.has('Number','Plur'):
        if hd['lemma'] in ['beirt', 'dís']:
          return [Constraint('Len', '10.2.7.c.e1: Lenite a genitive plural after “beirt” or “dís”')]
        elif hd['lemma']=='clann' and self['lemma']=='mac':
          return [Constraint('Len', '10.2.7.c.e2: Lenite a genitive plural in the set phrase “clann mhac”')]
        else:
          return [Constraint('!Len', '10.2.7.c: Do not lenite a genitive plural noun after a feminine noun')]
      if hd['lemma'] in ['barraíocht', 'breis', 'díobháil', 'easpa', 'iomarca', 'roinnt']:
        return [Constraint('!Len', '10.2.7.d: Do not lenite a genitive noun after a feminine noun that expresses an indefinite quantity')]
      # TODO 10.2.7.e,f,g :(  Need big lists....

      if hd.isVerbalNounWithAg():
        return [Constraint('!Len', '10.2.7.h: Do not lenite the object of a feminine verbal noun following “ag”')]

      # TODO 10.2.7.i  Might need a list, even then tricky to tell
      # whether word is being used as common or verbal noun (e.g. lorg)

      if hd['lemma'] in gadata.feminineGroups:
        return [Constraint('!Len', '10.2.7.j: Do not lenite a genitive noun after various feminine noun for groups or organizations')]

      if self['lemma'] in ['dlí', 'sí']:
        return [Constraint('!Len', '10.2.7.k: Do not lenite “dlí” or “sí” after a feminine noun')]

      if self['lemma'] in ['bliain', 'coicís', 'mí', 'seachtain']:
        return [Constraint('!Len', '10.2.7.l: Do not lenite various units of time after a feminine noun')]

      if self.isQualifiedNoun():
        if hd['lemma'] in ['beirt', 'dís']:
          return [Constraint('Len', '10.2.7.m.e1: Lenite nouns after “beirt” or “dís” even if the genitive noun is modified by an adjective or another noun')]
        return [Constraint('!Len', '10.2.7.m: Do not lenite after a feminine noun if the genitive noun is modified by an adjective or another noun')]

      return [Constraint('Len', '10.2.7: Lenite a genitive singular noun following a feminine noun')]


    # 10.2.8
    if hd.isNominal() and hd.has('Case','Nom') and hd.has('Number','Plur') and hd.hasSlenderFinalConsonant() and self.has('Case','Gen') and self.has('Number','Sing') and not self.has('Definite','Def'):
      if hd.hasFinalDental() and self.hasInitialDental():
        return [Constraint('!Len', '10.2.8.a: Do not lenite an initial dental after a plural noun ending in a slender dental')]
      if self.hasInitialF():
        return [Constraint('!Len', '10.2.8.b: Do not lenite an initial f after a plural noun ending in a slender consonant')]
      # 10.2.8.d,e need lists :(
      if self.isQualifiedNoun():
        if self['lemma']=='beirt':
          return [Constraint('Len', '10.2.8.f.e1: Lenite “beirt” following a plural noun ending in a slender consonant even when it is followed by a genitive')]
        else:
          return [Constraint('!Len', '10.2.8.f: Do not lenite a genitive singular noun following a plural noun ending in a slender consonant if it is modified by an adjective or another genitive noun')]

      return [Constraint('Len', '10.2.8: Lenite a genitive singular noun following a plural ending in a slender consonant')]

    # 10.2.9; include just for clearer error message
    if pr.isNominal() and pr.has('Case','Gen') and not self.has('Definite','Def') and self['head']==self['index']-1:
      return [Constraint('!Len','10.2.9: Do not lenite a noun following a genitive')]


    return [Constraint('!Len','10.2: Not sure why this noun is lenited')]

  # TODO: need to handle initial m,s in eclipsed context too :( :(
  def predictVerbLenition(self, eclipsisConstraints):
    if not self.isLenitable():
      return [Constraint('!Len', 'Cannot lenite an unlenitable letter')]
    if any(c.isSatisfied(['Ecl']) for c in eclipsisConstraints):
      return [Constraint('!Len', 'Should not lenite in an eclipsis context')]
    lemma = self['lemma']
    if lemma=='abair':
      return [Constraint('!Len', '10.4.2.b: Forms of the verb “abair” are never lenited')]
    if lemma=='bí' and self['token'][0]=='t':
      return [Constraint('!Len', '10.4: Do not lenite “tá”, “táimid”, etc.')]
    if self.has('Tense','Past') and self.has('Mood','Ind'):
      if self.has('Person','0'):
        if lemma in ['bí','clois','feic','tar','téigh']:
          return [Constraint('Len', '10.4.1.i.e1: Past autonomous verbs “bhíothas”, “chonacthas”, “chualathas”, “chuathas”, “thángthas” must be lenited')]
        else:
          return [Constraint('!Len', '10.4.1.i: Past autonomous verbs are normally not lenited')]
      else:
        if lemma=='faigh':  # abair handled above
          return [Constraint('!Len', '10.4.1.ii: Never lenite past tense forms of “faigh”')]
        else:
          return [Constraint('Len', '10.4.1.a: This past tense verb should be lenited')]
    if self.has('Aspect','Imp') and self.has('Tense','Past'):
      return [Constraint('Len', '10.4.1.a: This imperfect verb should be lenited')]
    if self.has('Mood','Cnd'):
      return [Constraint('Len', '10.4.1.a: This conditional verb should be lenited')]
    pr = self.getPredecessor()
    if pr==None:
      return [Constraint('!Len', '10.4: This verb could only be lenited by a preceding particle')]
    # also "do" e.g. train line 1467?
    if pr['lemma']=='a' and pr['upos']=='PART' and pr.has('Form','Direct'):
      return [Constraint('Len', '10.4.1.b+c: Lenite after the direct relative particle “a”')]
    if pr['lemma'] in ['má','ó'] and pr['upos']=='SCONJ' and not pr.has('VerbForm','Cop'):
      return [Constraint('Len', '10.4.1.b: Lenite after the conjunction “má” or “ó”')]
    if pr.isLenitingVerbalParticle():
      return [Constraint('Len', '10.4.2: Verb is lenited after this verbal particle')]
    return [Constraint('!Len','10.2: Not sure why this noun is lenited')]

  def predictAdjectivePrefixH(self):
    if not self.admitsPrefixH():
      return [Constraint('!HPref', '10.12: Can only have a prefix h before initial vowel')]
    pr = self.getPredecessor()
    if pr==None:
      return [Constraint('!HPref', '10.12: Cannot have a prefix h on an adjective at the start of a sentence')]
    prToken = pr['token'].lower()
    if prToken=='chomh':
      return [Constraint('HPref', '10.12.1: Adjective should have a prefix h after “chomh”')]
    if prToken=='go' and pr.has('PartType','Ad'):
      return [Constraint('HPref', '10.12.1: Adjective should have a prefix h after “go”')]
    if prToken=='ní' and pr['upos']=='AUX':
      # ní haon is NUM
      if self['lemma'] in ['amháin', 'annamh', 'eagal', 'ionann', 'iondúil', 'oircheas']:
        return [Constraint('HPref', '10.12.2.e1: Certain adjectives should have a prefix h after “ní”')]
      else:
        return [Constraint('!HPref', '10.12.2: Most adjectives do not take a prefix h after “ní”')]
    # "le haon" handled in predictFormDET
    # a haon, a hocht handled in predictOtherPrefixH
    return [Constraint('!HPref', '10.12.2: Not sure why this adjective has a prefix h')]

  # a (her), a dhá, á (her), cá, go, le, na (gsf), na (common pl)
  # Ó patronym, ordinals except chéad, and trí/ceithre/sé+uaire
  def predictNounPrefixH(self):
    if not self.admitsPrefixH():
      return [Constraint('!HPref', 'Can only have a prefix h before initial vowel')]
    pr = self.getPredecessor()
    prToken = pr['token'].lower()
    if prToken=='ó' and pr.has('PartType','Pat'):
      return [Constraint('HPref', 'Surnames should have prefix h after “Ó”')]
    if pr['lemma']=='Dé':
      return [Constraint('HPref', 'Should have prefix h after “Dé”')]
    if prToken in ['cá','go','le']:
      return [Constraint('HPref', 'Should have prefix h')]
    if pr.has('Poss','Yes') and pr.has('Gender','Fem'):
      return [Constraint('HPref', 'Should have prefix h following feminine possessive')]
    if prToken=='dhá' and pr.getPredecessor().has('Poss','Yes') and \
          pr.getPredecessor().has('Gender','Fem'):
      return [Constraint('HPref','Should have prefix h after feminine possessive + dhá')]
    if pr.has('NumType','Ord') and pr['lemma']!='céad':
      return [Constraint('HPref', 'Should have prefix h following an ordinal')]
    if prToken=='na' and self.has('Gender','Fem') and \
          self.has('Case','Gen') and self.has('Number','Sing'):
      return [Constraint('HPref', 'Should have prefix h following an ordinal')]
    if prToken in ['na','sna'] and self.has('Case','Nom') and \
          self.has('Number','Plur'):
      return [Constraint('HPref', 'Should have prefix h following “na”')]
    if prToken=='de' and self['lemma']=='Íde':
      return [Constraint('HPref', 'Should have prefix h in “de hÍde”')]
    return []

  def predictVerbPrefixH(self):
    if not self.admitsPrefixH():
      return [Constraint('!HPref', 'Can only have a prefix h before initial vowel')]
    pr = self.getPredecessor()
    if pr!=None and pr['token'].lower()=='ná' and pr.has('Mood','Imp'):
      return [Constraint('HPref', '10.14.1: Should have prefix h after “ná”')]
    return [Constraint('!HPref', '10.14: Not sure why this verb has a prefix h')]

  def predictOtherPrefixH(self):
    if not self.admitsPrefixH():
      return [Constraint('!HPref', 'Can only have a prefix h before initial vowel')]
    pr = self.getPredecessor()
    prToken = pr['token'].lower()
    if self['upos']=='PRON' and prToken in ['cé','le','ní','pé']:
      return [Constraint('HPref', 'Should have prefix h')]
    if self['upos']=='NUM' and prToken == 'a' and pr.has('PartType','Num'):
      return [Constraint('HPref', 'Number should have a prefix h')]
    # annoying fixed ADPs
    if self['deprel']=='fixed' and prToken=='le' and \
          self['token'].lower()=='hais':
      return [Constraint('HPref', 'Should have prefix h in set phrase')]
    return []

  def predictEmphasis(self):
    # TODO: draw on lexicon to make iff prediction of Emp
    if re.search("([sn][ea]|se?an)$", self['token'].lower()):
      return [Constraint('Emp|!Emp', 'Could possibly be an emphatic ending but not certain')]
    return [Constraint('!Emp', 'Word does not have an emphatic ending')]

  def predictVowelForm(self):
    if re.search("b[’'h]?$", self['token'].lower()):
      return [Constraint('VF', 'Copula before vowel or f must have Form=VF')]
    return [Constraint('!VF', 'Form=VF not allowed without initial vowel or f')]

##################### predictFeatureUPOS methods #####################

  def predictAspectVERB(self):
    if self.has('Mood','Ind') and self.has('Tense','Pres') and \
        self['lemma']=='bí' and re.match('m?bh?í', self['token'].lower()):
      return [Constraint('Hab', 'Present habitual needs feature Aspect=Hab')]
    if self.has('Tense','Past') and self['Mood']==None:
      return [Constraint('Imp', 'Past tense but no Mood needs Aspect=Imp')]
    return []

  def predictCaseADJ(self):
    return super().predictCaseADJ()

  def predictCaseDET(self):
    head = self.getUltimateHead()
    # TODO: exception if genitive head noun is nummod of a cardinal
    # "dúshlán na seacht dtúr"
    if head.isNominal() and self['lemma']=='an':
      if head.has('Case','Gen'):
        return [Constraint('Gen', 'Article before genitive singular noun should have Case=Gen')]
    return []

  def predictCaseNOUN(self):
    return [Constraint('Nom|Gen|Dat|Voc|None', 'placeholder...')]
    if self.getDeprel()=='vocative':
      return [Constraint('Voc', 'Should have feature Case=Voc')]
    # TODO: words with no case, Abbr, Foreign?
    #noCase = ['ann', 'céile', 'dála', 'dea', 'doh', '(e)amar', 'foláir', 'gach', 'go', 'leith', 'leor', 'márach', 'scan', 'scun', 'seach', 'sul', 'té', 'thuilleadh', 'tólamh', 'uile']

  def predictCasePROPN(self):
    return self.predictCaseNOUN()

  def predictDefiniteDET(self):
    lemma = self['lemma']
    if lemma=='an' or re.search('^(an|gach.*|achan)$', lemma):
      return [Constraint('Def', 'This determiner should have Definite=Def')]
    return []

  def predictDefiniteNOUN(self):
    if self.precedingCen() or self.anyDependentDefiniteArticle():
      return [Constraint('Def', 'Needs Definite=Def because of preceding article')]
    if self.isPossessed():
      return [Constraint('Def', 'Needs Definite=Def because of preceding possessive adjective')]
    if self.hasGachDependent():
      return [Constraint('Def', 'Needs Definite=Def because of “gach”')]
    if self.has('Case','Voc') or self['deprel']=='vocative':
      return [Constraint('Def', 'All vocatives need Definite=Def')]
    if self.hasPropagatingDefiniteDependent():
      return [Constraint('Def', 'Needs Definite=Def because of definite nominal dependent')]
    if self.hasNumberSpecifier():
      return [Constraint('Def', 'Needs Definite=Def because of the number that follows')]
    return []

  def predictDefinitePROPN(self):
    return [Constraint('Def', 'All proper nouns need Definite=Def')]

  def predictDegreeADJ(self):
    pr = self.getPredecessor()
    prToken = pr['token'].lower()
    # stuff preceding Cmp,Sup is currently always AUX or PART
    # and lemmas are always is, níos, ba, or a
    # níos always has PartType=Comp, a always has PartType=Deg
    # When "ba" is the lemma it's always PART, but tagging is a mixed bag
    # When "is" is the lemma, it's sometimes PART sometimes AUX
    # When it's AUX, features are a mixed bag
    # When it's PART, always has PartType=Comp or Sup

    # if it's nmod and not comp/sup, it gets features from NOUN => no Degree
    if self.getDeprel()=='amod':
      return []
    if self.has('VerbForm','Part'):
      return []
    return [Constraint('Pos', 'Should default to Degree=Pos')]

  def predictFormADJ(self):
    ans = self.predictAdjectiveLenition()
    ans.extend(self.predictAdjectivePrefixH())
    return ans

  def predictFormADP(self):
    ans = []
    pr = self.getPredecessor()
    prToken = pr['token'].lower()
    # annoying fixed phrases...
    if self['deprel']=='fixed' and \
       ((prToken=='go' and self['token'].lower()=='dtí') or \
        (prToken=='i' and self['token'].lower() in ['bhfeighil','dteannta','dtrátha','dtús','gceann','gcionn','gcoinne','gcóir','gcoitinne','mbun','ndiaidh'])):
      return [Constraint('Ecl', 'Should be eclipsed in set phrase')]
    else:
      return [Constraint('None', 'Prepositions usually do not have a Form')]

  # just in one set phrase; get rid of fixed or retag components?
  # TODO: ní hamhlaidh  10.12.2?
  def predictFormADV(self):
    if self['lemma']=='bheith' and self['deprel']=='fixed' and \
         self.getHead()['lemma']=='thar':
      return [Constraint('Len', 'Need Form=Len on “bheith” in this set phrase')]
    return []

  # VF, Ecl, Len
  def predictFormAUX(self):
    ans = self.predictVowelForm()
    # Eclipsis: go mba, dá mba, etc.
    if self.isEclipsable() and self.getPredecessor()['lemma'] in ['dá','go']:
      ans.append(Constraint('Ecl', 'Should be eclipsed by preceding particle'))
    return ans

  # Ecl, Len, HPref, e.g. i ngach, chuile, haon (10.12.1)
  def predictFormDET(self):
    ans = []
    if self.getPredecessor()['token'].lower()=='i' and self['lemma']=='gach':
      ans.append(Constraint('Ecl', 'Should be eclipsed by preceding “i”'))
    return ans

  # Ecl, Len, HPref, Emp
  def predictFormNOUN(self):
    ans = self.predictEmphasis()
    ans.extend(self.predictNounLenition())
    ans.extend(self.predictNounEclipsis())
    ans.extend(self.predictNounPrefixH())
    return ans

  # Ecl, Len, HPref
  def predictFormNUM(self):
    ans = []
    pr = self.getPredecessor()
    prToken = pr['token'].lower()
    # Eclipsis
    if prToken=='faoin' and self['lemma'].lower()=='céad':
      ans.append(Constraint('Ecl', 'Should be eclipsed in set phrase'))
    elif self['head']==self['index']+1:
      ans.extend(self.predictNounEclipsis())
    return ans

  # Direct, Indirect, and (rarely) Len, VF, Ecl
  def predictFormPART(self):
    ans = self.predictVowelForm()
    if self.has('PronType','Rel'):
      ans.append(Constraint('Direct|Indirect', 'Relative particles must have Form feature'))
    return ans

  # Len, HPref (10.13 TODO), and 1x VF ("cérbh")
  def predictFormPRON(self):
    ans = self.predictVowelForm()
    return ans

  # Ecl, Len, HPref
  def predictFormPROPN(self):
    return self.predictFormNOUN()

  # (rarely) VF (murab, arb), 1x Len (dhá for dá)
  def predictFormSCONJ(self):
    ans = self.predictVowelForm()
    return ans

  # Ecl, Len, HPref, Emp, plus some with Direct (atá + relative forms)
  def predictFormVERB(self):
    ans = self.predictVerbEclipsis()
    ans.extend(self.predictVerbLenition(ans))
    ans.extend(self.predictEmphasis())
    if self.has('PronType','Rel') and re.match(r'at[aá]',self['token'].lower()):
      ans.append(Constraint('Direct', 'Anything resembling atá should be have direct relative feature Form=Direct'))
    ans.extend(self.predictVerbPrefixH())
    return ans

  def predictGenderADP(self):
    if self.has('Number','Sing') and self.has('Person','3'):
      return [Constraint('Fem|Masc', '3rd person singular ADP must be marked for Gender')]
    return []

  def predictGenderADJ(self):
    return super().predictGenderADJ()

  def predictGenderAUX(self):
    mapping = {'sé': 'Masc', 'sí': 'Fem'}
    if self['token'].lower() in mapping:
      return [Constraint(mapping[self['token'].lower()], 'Combined copula requires correct Gender feature')]
    return []

  def predictGenderDET(self):
    if self.has('Number','Sing'):
      if self.has('Poss','Yes') and self.has('Person','3'):
        return [Constraint('Fem|Masc', '3rd person singular possessive must be marked for Gender')]
      if self.has('PronType','Art') and self.has('Case','Gen'):
        if re.match("'?[Nn]", self['token']):
          return [Constraint('Fem', 'Article before genitive singular feminine noun must be marked for Gender')]
        if re.match("'?[Aa]", self['token']):
          return [Constraint('Masc', 'Article before genitive singular masculine noun must be marked for Gender')]
    return []

  # could have a list of exceptions but doesn't add much value
  # since missing genders would be picked up by lexicon check
  def predictGenderNOUN(self):
    return [Constraint('Fem|Masc|None', 'placeholder...')]

  def predictGenderPROPN(self):
    return self.predictGenderNOUN()

  def predictGenderPRON(self):
    pronouns = {'é': 'Masc', 'eisean': 'Masc', 'í': 'Fem', 'ise': 'Fem', 'sé': 'Masc', 'seisean': 'Masc', 'sí': 'Fem', 'sise': 'Fem'}
    if self['lemma'] in pronouns:
      return [Constraint(pronouns[self['lemma']], 'Personal pronouns require correct Gender feature')]
    return []

  def predictMoodAUX(self):
    return [Constraint('Cnd|Int|None', 'Copula can sometimes have Mood=Int or Mood=Cnd')]

  def predictMoodPART(self):
    head = self.getHead()
    if self['lemma']=='ná' and head.has('Mood','Imp'):
      return [Constraint('Imp', 'Negative imperative particle requires feature Mood=Imp')]
    if self['lemma'] in ['go', 'nár'] and head.has('Mood','Sub'):
      return [Constraint('Sub', 'Subjunctive particle requires feature Mood=Sub')]
    return []

  def predictMoodVERB(self):
    # distinguishing the moods is a lexical thing; handle with dict lookup
    if not self.has('Aspect','Imp'):
      return [Constraint('Cnd|Imp|Ind|Int|Sub', 'All non-imperfect verbs must have the Mood feature')]
    return []

  def predictNounTypeADJ(self):
    # include deprel nmod here because of coordinations through gen. sing nouns
    if self.has('Number','Plur') and self.getDeprel() in ['amod','nmod']:
      head = self.getUltimateHead()
      if head.has('Case','Nom'):
        if head.hasSlenderFinalConsonant():
          #if self['NounType']==None:
          #  self.addFeature('NounType','Slender')
          return [Constraint('Slender', 'Plural adjective modifying noun with slender ending; needs NounType=Slender feature')]
        else:
          #if self['NounType']==None:
          #  self.addFeature('NounType','NotSlender')
          return [Constraint('NotSlender', 'Plural adjective modifying noun ending in broad consonant or vowel needs NounType=NotSlender feature')]
      elif head.has('Case','Gen'):
        if head['NounType']!=None:
          val = head['NounType'][0]
          #if self['NounType']==None:
          #  self.addFeature('NounType',val)
          return [Constraint(val, 'Plural adjective must have NounType=Strong or Weak matching the noun it modifies')]
    return []

  def predictNounTypeNOUN(self):
    # NB nouns don't take Slender/NotSlender feature, only their dependent adjs
    if self.has('Number','Plur') and self.has('Case','Gen'):
      return [Constraint('Strong|Weak', 'Genitive plural nouns need NounType=Strong or Weak')]
    return []

  def predictNounTypePROPN(self):
    return self.predictNounTypeNOUN()

  def predictNumberAUX(self):
    if self['token'].lower() in ['sé','sí']:
      return [Constraint('Sing', 'Combined copula requires Number feature')]
    return []

  # TODO: beirt; does this generalize to Goidelic?
  def predictNumberADJ(self):
    if self.isAttributiveAdjective():
      head = self.getUltimateHead()
      if head.has2Thru19():
        return [Constraint('Plur', 'Should be plural adjective after 2-19')]
      if head['Number']!=None:
        theNumber = head['Number'][0]
        return [Constraint(theNumber, 'Adjective number should match noun it modifies')]
    return []

  def predictNumberADP(self):
    return [Constraint('Sing|Plur|None', 'Some pronomials have Number feature')]

  def predictNumberDET(self):
    possessives = {'ár': 'Plur', 'bhur': 'Plur', 'do': 'Sing', 'mo': 'Sing'}
    if self['lemma'] in possessives:
      return [Constraint(str(possessives[self['lemma']]), 'Possessives should have the correct Number feature')]
    if self['lemma']=='an':
      return [Constraint('Sing|Plur', 'Articles must have Number feature')]
    if self['lemma']=='a':
      return [Constraint('Sing|Plur', 'Possessive “a” must be annotated either singular or plural')]
    return []

  def predictNumberNOUN(self):
    if self['Abbr']==None and self['Foreign']==None and self['VerbForm']==None:
      return [Constraint('Sing|Plur', 'All nouns except verbal nouns should have a Number feature')]
    return []

  def predictNumberPRON(self):
    # cén is Sing, but cé, céard have no Number
    if self['lemma']=='cé':
      if self['token'].lower()=='cén':
        return [Constraint('Sing', 'Pronoun “cén” must be Number=Sing')]
      else:
        return []
    pronouns = {'é': 'Sing', 'ea': 'Sing', 'eisean': 'Sing', 'í': 'Sing', 'iad': 'Plur', 'ise': 'Sing', 'mé': 'Sing', 'mise': 'Sing', 'muid': 'Plur', 'sé': 'Sing', 'seisean': 'Sing', 'sí': 'Sing', 'siad': 'Plur', 'sibh': 'Plur', 'sinn': 'Plur', 'sise': 'Sing', 'tú': 'Sing', 'tusa': 'Sing'}
    if self['lemma'] in pronouns:
      return [Constraint(pronouns[self['lemma']], 'Pronouns should have the correct Number feature')]
    return []

  def predictNumberPROPN(self):
    return self.predictNumberNOUN()

  def predictNumberVERB(self):
    return [Constraint('Sing|Plur|None', 'Some verbs have Number feature')]
    return []

  def predictNumTypeNUM(self):
    return [Constraint('Card|Ord|None', 'Numbers have optional NumType feature')]

  def predictPartTypePART(self):
    if self['lemma'] in ['an','ar','cha','chan','gur','ná','níor']:
      return [Constraint('Vb', 'This particle should always be PartType=Vb')]
    if self['lemma'] in ['de','mac','mag','nic','o','ó','uí']:
      return [Constraint('Pat', 'This particle should always be PartType=Pat')]
    if self['lemma']=='a':
      return [Constraint('Cop|Deg|Inf|Num|Vb|Voc', 'If the word “a” is a particle, it must be one of these particle types')]
    if self['lemma']=='ba':
      return [Constraint('Comp', 'If “ba” is a particle, it must be PartType=Comp')]
    if self['lemma']=='do':
      if self.getHead()['upos']=='NOUN':
        return [Constraint('Inf', 'Here, “do” should be PartType=Inf')]
      if self.getHead()['upos']=='VERB' and not self.has('Form','Indirect'):
        return [Constraint('Vb', 'Here, “do” should be PartType=Vb')]
    # go => Cmpl, Ad, Vb
    if self['lemma']=='go':
      if self.getHead()['upos']=='ADJ':
        return [Constraint('Ad','Should have PartType=Ad in adverbial phrase')]
      if self.has('Mood','Sub'):
        return [Constraint('Vb','Subjunctive particle should have PartType=Vb')]
      # TODO: handle go+AUX  (go mba shólás leis sin); copula isn't the head!
      if self.getHead()['upos'] in ['VERB']:
        return [Constraint('Cmpl','Here, “go” should have PartType=Cmpl')]
    if self['lemma']=='is':
      return [Constraint('Comp|Sup', 'The particle “is” should have PartType=Comp or Sup')]
    if self['lemma'] in ['nach', 'nár'] and self.getHead()['upos']=='VERB':
      # Form=Direct or Direct, also Mood=Sub (nár lige Dia é) => Vb
      if self['Form']!=None: # Direct or Indirect
        return [Constraint('Vb', 'Relative particle needs PartType=Vb')]
      else:
        return [Constraint('Cmpl', 'Here, complementizer needs PartType=Cmpl')]
    if self['lemma']=='ní':
      return [Constraint('Comp|Pat|Vb', 'The particle “ní” is one of these types')]
    if self['lemma']=='níos':
      return [Constraint('Comp', 'The particle “níos” needs PartType=Comp')]
    return []

  def predictPersonADP(self):
    return [Constraint('0|1|2|3|None', 'Tokens tagged ADP sometimes have the Person feature')]

  def predictPersonAUX(self):
    if self['token'].lower() in ['sé','sí']:
      return [Constraint('3', 'Combined copula requires Person feature')]
    return []

  def predictPersonDET(self):
    if self.has('Poss','Yes'):
      possessives = { 'a': 3, 'ár': 1, 'bhur': 2, 'do': 2, 'mo': 1 }
      if self['lemma'] in possessives:
        return [Constraint(str(possessives[self['lemma']]), 'Possessives should have the correct Person feature')]
    return []

  def predictPersonPRON(self):
    pronouns = {'é': 3, 'ea': 3, 'eisean': 3, 'í': 3, 'iad': 3, 'ise': 3, 'mé': 1, 'mise': 1, 'muid': 1, 'sé': 3, 'seisean': 3, 'sí': 3, 'siad': 3, 'sibh': 2, 'sinn': 1, 'sise': 3, 'tú': 2, 'tusa': 2}
    if self['lemma'] in pronouns:
      return [Constraint(str(pronouns[self['lemma']]), 'Pronouns should have the correct Person feature')]
    return []

  def predictPersonVERB(self):
    return [Constraint('0|1|2|3|None', 'Verbs sometimes have the Person feature')]

  def predictPolarityAUX(self):
    if re.match('(n|cha)', self['token'].lower()):
      return [Constraint('Neg', 'Negative copula should have Polarity=Neg')]
    return []

  def predictPolarityPART(self):
    if not self.has('PartType','Comp') and not self.has('PartType','Pat') and \
          re.match('(n[^-]|cha)', self['token'].lower()):
      return [Constraint('Neg', 'Negative particle should have Polarity=Neg')]
    return []

  def predictPolarityVERB(self):
    pr = self.getPredecessor()
    if re.match('níl',self['token'].lower()) or pr.has('Polarity','Neg'):
      #self.addFeature('Polarity','Neg')
      return [Constraint('Neg', 'Verb following negative particle must have Polarity=Neg feature')]
    return []

  def predictPossADP(self):
    return [Constraint('Yes|None', 'ADP could have Poss=Yes')]

  def predictPossDET(self):
    return [Constraint('Yes|None', 'DET could have Poss=Yes')]

  # Usually case in PPs, but can be mark ("go dtí go mbeidh...")
  def predictPrepFormADP(self):
    if self['deprel'] in ['case','mark'] and self['head']>self['index']+1 and \
          any(t['index']==self['index']+1 and t['upos']=='NOUN' and t['deprel']=='fixed' for t in self.getDependents()):
      return [Constraint('Cmpd', 'First part of compound preposition should have feature PrepForm=Cmpd')]
    return []

  # second halves tagged NOUN as of April 2021
  # note the check that head of the ADP isn't "self"
  def predictPrepFormNOUN(self):
    pr = self.getPredecessor()
    cmpd = pr['token'].lower()+' '+self['token'].lower()
    if self['deprel']=='fixed':
      h = self.getHead()
      if (cmpd in gadata.compoundPrepositions  or cmpd == 'go dtí') and\
           h['upos']=='ADP' and h['deprel'] in ['case','mark'] and \
           h['head']>self['index'] and self['head']==self['index']-1:
        return [Constraint('Cmpd', 'Second part of compound preposition should have feature PrepForm=Cmpd')]
    else:
      if (cmpd in gadata.compoundPrepositions or cmpd == 'go dtí') and \
          any(t.isNominal() and t['deprel']=='nmod' and not t.isInPP() for t in self.getDependents()):
        return [Constraint('Cmpd', 'This should be fixed and PrepForm=Cmpd')]
    return []

  def predictPronTypeADP(self):
    tok = self['token'].lower()
    # values: Art, Emp, Prs, Rel (rare)
    if tok in ['á', 'dhá'] and self['lemma']=='do' and \
        self.getDeprel()=='case' and self.getHead().has('VerbForm','Inf'):
      return [Constraint('Prs', 'Particle “á” before verbal noun needs PronType=Prs feature')]
    if re.match('(dá|(faoi|i|le|ó|trí)nar?)$',tok) and \
        not self.has('Poss','Yes') and self.getDeprel() != 'case':
      return [Constraint('Rel', 'Appears to be combined preposition with “a” (all that) and need PronType=Rel feature')]
    # no need to be comprehensive here, caught by lexicon
    if re.search('(s[ae]|ne|se?an)$', tok):
      return [Constraint('Art|Emp|None', 'This could be an emphatic form')]
    if self.getDeprel()=='case':
      return [Constraint('Art|None', 'This could be PronType=Art')]
    return []

  def predictPronTypeADV(self):
    if self['lemma'] in ['cá', 'conas']:
      return [Constraint('Int', 'These interrogatives require PronType=Int')]
    return []

  def predictPronTypeAUX(self):
    if self['token'].lower() in ['seo','sin']:
      return [Constraint('Dem', 'Feature PronType=Dem is required here')]
    else:
      return [Constraint('Rel|None', 'Some copulas are PronType=Rel')]

  def predictPronTypeDET(self):
    if not self.has('Poss','Yes'):
      if self['lemma']=='an':
        return [Constraint('Art', 'Definite article requires PronType=Art')]
      if self['lemma'] in ['eile','s','seo','sin','siúd','úd']:
        return [Constraint('Dem', 'Demonstratives require PronType=Dem')]
      if self['lemma'] in ['aon','cibé','uile']:
        return [Constraint('Ind', 'Indef. determiner requires PronType=Ind')]
    return []

  def predictPronTypePART(self):
    # lemmas: a, ar, do, faoi, i, le, nach, nár, trí
    if self.has('Form','Direct') or self.has('Form','Indirect') or \
        self.has('PartType','Cop'):
      return [Constraint('Rel', 'Relativizing particles must have feature PronType=Rel')]
    return []

  def predictPronTypePRON(self):
    # values: Dem, Int, Emp, Rel, Ind   TODO
    return [Constraint('Dem|Emp|Ind|Int|Rel|None', 'placeholder...')]

  def predictPronTypeVERB(self):
    tok = self['token'].lower()
    if re.match('at[aá]',tok):
      return [Constraint('Rel', 'Forms like “atá” require the feature PronType=Rel')]
    if re.search('s$',tok):
      return [Constraint('Rel|None', 'Verb forms ending in s are sometimes relative which would require PronType=Rel')]
    return []

  def predictReflexPRON(self):
    if self['lemma']=='féin':
      return [Constraint('Yes', 'The word “féin” needs feature Reflex=Yes')]
    return []

  # Sinn Féin
  def predictReflexPROPN(self):
    if self['lemma']=='Féin':
      return [Constraint('Yes', 'The word “Féin” in “Sinn Féin” needs feature Reflex=Yes')]
    return []

  def predictTenseADV(self):
    if self['token'].lower()=='cár':
      return [Constraint('Past', 'Past tense interrogative “cár” should have Tense=Past before a regular verb')]
    return []

  def predictTenseAUX(self):
    if not self.has('Mood','Cnd'):
      return [Constraint('Past|Pres', 'Copulas that are not conditional must be marked as present or past tense')]
    return []

  def predictTensePART(self):
    # same condition as in predictVerbFormPART
    tok = self['token'].lower()
    if re.search('r$',tok) and not self.has('Mood','Sub'):
      return [Constraint('Past', 'Special past tense particles ending in -r should have Tense=Past feature')]
    if self['lemma']=='is' and re.match('b',tok) and \
       (self.has('PartType','Comp') or self.has('PartType','Sup')):
      return [Constraint('Past', "Particle ”ba” in comparative or superlative constructions must have Tense=Past feature")]
    return []

  def predictTenseSCONJ(self):
    tok = self['token'].lower()
    if tok in ['murar','sarar','sular']:
      return [Constraint('Past', 'Special past tense conjunctions should have Tense=Past before a regular verb')]
    if tok in ['mura','murab'] and self.has('VerbForm','Cop'):
      return [Constraint('Pres', 'Special past tense conjunctions should have Tense=Past before a regular verb')]
    return []

  def predictTenseVERB(self):
    return super().predictTenseVERB()

  def predictVerbFormADJ(self):
    return [Constraint('Part|None', 'Adjectives can have VerbForm=Part feature')]

  def predictVerbFormAUX(self):
    return [Constraint('Cop', 'Copulas must have VerbForm=Cop feature')]

  def predictVerbFormNOUN(self):
    return super().predictVerbFormNOUN()

  def predictVerbFormPART(self):
    # same condition as in predictTensePART
    if self['lemma']=='is' and re.match('b',self['token'].lower()) and \
       (self.has('PartType','Comp') or self.has('PartType','Sup')):
      return [Constraint('Cop', 'Some comparative/superlative particles have VerbForm=Cop feature')]
    return []

  def predictVerbFormPRON(self):
    # rare: caidé, cérbh, cér currently
    return [Constraint('Cop|None', 'Pronouns sometimes have VerbForm=Cop feature')]

  def predictVerbFormSCONJ(self):
    # short list? currently arb, dar, más, mura, murab, murar, ós, sular
    return [Constraint('Cop|None', 'Conjunctions sometimes have VerbForm=Cop feature')]

  # TODO: 'maidir leis an airgead a leagan amach'
  # airgead is obj of leagan, maidir is case of leagan
  def predictXFormDET(self):
    if self['lemma']=='aon':
      if (self.precedingDefiniteArticle() or self.precedingCen()) and \
           not self.getHead().isInDativePP():
        return [Constraint('TPref', 'Should be “t-aon” after definite article')]
    return []

  def predictXFormNOUN(self):
    if self.hasLenitableS():
      if self.has('Number','Sing') and self.has('Gender','Fem') and \
           self.has('Case','Nom') and \
          (self.anyPrecedingDefiniteArticle() or self.precedingCen()):
        return [Constraint('TPref', 'Should have prefix t before feminine noun after an article')]
      if self.has('Number','Sing') and self.has('Gender','Masc') and \
           self.has('Case','Gen') and self.precedingDefiniteArticle():
        return [Constraint('TPref', 'Should have prefix t before genitive masculine noun after an article')]
    elif self.hasInitialVowel():
      # Exceptions in CO for oiread/iomad but these are genderless in treebank
      if self.has('Number','Sing') and self.has('Gender','Masc') and \
           self.has('Case','Nom') and not self.isInDativePP() and \
          (self.precedingDefiniteArticle() or self.precedingCen()):
        return [Constraint('TPref', 'Should have prefix t before masculine noun after an article')]
    return []

  def predictXFormPROPN(self):
    return self.predictXFormNOUN()

  ########################################################################

  def lowerToken(self):
    s = self['token']
    if len(s) > 1 and (s[0]=='t' or s[0]=='n') and s[1] in 'AEIOUÁÉÍÓÚ':
      return s[0]+'-'+s[1:].lower()
    else:
      return s.lower()

  def demutatedToken(self):
    s = self['token']
    if s[:2] in ['n-','t-']:
      return s[2:]
    if re.match('[nt][AEIOUÁÉÍÓÚ]',s):
      return s[1:]
    if re.match('h[aeiouáéíóú]',s,flags=re.IGNORECASE) and self.hasInitialVowel():
      return s[1:]
    if re.match('bhf',s,flags=re.IGNORECASE):
      return s[2:]
    if re.match('(mb|gc|n[dg]|bp|ts|dt)',s,flags=re.IGNORECASE):
      return s[1:]
    if re.match('[bcdfgmpst]h',s,flags=re.IGNORECASE):
      return s[0]+s[2:]
    return s
