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
            #'Form',
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
    return re.match(r'([bcdfgmpt]|s[lnraeiouáéíóú])', self['lemma'], flags=re.IGNORECASE) and self['token'][0].lower() != 'r'

  # ok on Foreign=Yes b/c of gd words
  def isLenited(self):
    return re.match(r'([bcdfgmpt]h[^f]|sh[lnraeiouáéíóú])', self['token'], flags=re.IGNORECASE) and re.match(r'(.[^h]|bheith)', self['lemma'], flags=re.IGNORECASE)

  def isEclipsable(self):
    return (self.isEclipsed() or re.match(r'[aeiouáéíóúbcdfgpt]', self['token'], flags=re.IGNORECASE))

  # permits mBriathar, MBRIATHAR, but not Mbriathar (to avoid "Ndugi", etc.)
  # allowed on Foreign=Yes too (ón bpier, ón dTower)
  # allowed on Abbr=Yes ("gCo.")
  def isEclipsed(self):
    return re.match(r'(n-?[AEIOUÁÉÍÓÚ]|n-[aeiouáéíóú]|m[Bb]|MB|g[Cc]|GC|n[DdGg]|N[DG]|bh[Ff]|BHF|b[Pp]|BP|d[Tt]|DT)', self['token'])

  def isSevenThruTen(self):
    return self['lemma'] in ['seacht','7','ocht','8','naoi','9','deich','10']

  def hasInitialDental(self):
    return re.match(r'[dntlsDNTLS]', self['lemma'])

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

  def precedingDefiniteArticle(self):
    return self.getPredecessor()['token'].lower()=='an'

  # preceding an, but also sa, den, ón, etc.
  def anyPrecedingDefiniteArticle(self):
    return self.getPredecessor().has('PronType','Art')

  def isPossessed(self):
    return any(t.has('Poss','Yes') for t in self.getDependents())

  def hasGachDependent(self):
    return any(t['lemma']=='gach' and t['upos']=='DET' for t in self.getDependents())

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

  def isLenitedPastVerbContext(self):
    pers = self['Person']
    if pers==None:
      return False
    pers = int(pers[0])
    lemma = self['lemma']
    return self.has('Tense','Past') and \
           ((pers==0 and lemma in ['bí','clois','feic','tar','téigh']) or \
            (pers>0 and lemma not in ['abair','faigh']))

  # verbal particles that lenite following verb, excepting
  # past tense version like gur, murar, etc. since those verbs
  # are already lenited anyway
  # ní, níor, gur, nár, má, murar, sular, ar, cár, a (direct rel)
  def isLenitingParticle(self):
    return False

  # the PRON case is "sin a bhfuil agam"; note we can't use
  # self.has('Tense','Past') to discard "ar chuir..." b/c of PRON case
  def isEclipsingRelativizer(self):
    return self.has('PronType','Rel') and not re.search('r$', self['token'].lower()) and (self.has('Form','Indirect') or self['upos']=='PRON')

  def isPastFaigh(self):
    return self['lemma']=='faigh' and self.has('Mood','Ind') and self.has('Tense','Past')

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
    return pr['deprel']=='nummod' and pr.is2Thru19()

  # at Goidelic level, basically checks for amod of a nominal
  # with some exceptions; Irish-specific exceptions added here
  def isAttributiveAdjective(self):
    pr = self.getPredecessor()
    return super().isAttributiveAdjective() and \
           not self.has('VerbForm','Part')  and \
           not (pr['lemma']=='go' and self['lemma']=='léir') and \
           pr['lemma']!='sách' and pr['lemma']!='chomh'

  ####################### END BOOLEAN METHODS ##########################

  def noConstraint(self):
    return []

  # called separately for NUM's that precede the NOUN they modify
  def predictNounEclipsis(self):
    if not self.isEclipsable():
      return []
    noun = self.getHead() if self['upos']=='NUM' else self
    pr = self.getPredecessor()
    prToken = pr['token'].lower()
    if self['token'].lower()=='dhá':  # bhur dhá mbád; exception to super()
      return []
    panG = super.predictNounEclipsis()
    if len(panG)>0:
      return panG
    if prToken=='dhá' and pr.getPredecessor().isPluralPossessive():
      return [Constraint('Ecl','Should be eclipsed by possessive + dhá')]
    if pr['deprel']=='case' and prToken=='i':
      return [Constraint('Ecl', 'Should be eclipsed by preceding “i”')]
    # NB. gpl noun can be Number=Sing: "seolta na dtrí bhád"
    if prToken=='na' and noun.has('Case','Gen') and pr.has('Number','Plur'):
      return [Constraint('Ecl', 'Should be eclipsed by preceding “na” in genitive plural')]
    if prToken=='ar' and pr['upos']=='ADP':
      if self['lemma']=='diaidh': # i ndiaidh ar ndiaidh
        return [Constraint('Ecl', 'Should be eclipsed in set phrase')]
      # ar dhóigh, ar ndóigh, ar dóigh are all possible!
      if self['lemma']=='dóigh':
        return [Constraint('Ecl', 'Optionally eclipsed in set phrase', True)]
      if self['lemma'] in ['cúl','tús']:
        return [Constraint('Ecl|Len', 'Can be eclipsed in set phrase')]
    if prToken=='dar' and self['lemma'] in ['dóigh']:
      return [Constraint('Ecl', 'Should be eclipsed in set phrase')]
    if prToken=='fá' and pr['upos']=='ADP' and self['lemma'] in ['taobh']:
      return [Constraint('Ecl|Len', 'Can be eclipsed in set phrase')]
    if prToken in ['cá','go'] and self['lemma']=='fios':
      return [Constraint('Ecl', 'Should be eclipsed in set phrase')]
    # TODO "um an dtaca"
    if pr['deprel']=='nummod' and pr.isSevenThruTen():
      return [Constraint('Ecl', 'Should be eclipsed by number 7-10')]
    if pr.has('PronType','Art') and pr.has('Number','Sing') and \
         not self.hasInitialDental() and not self.hasInitialVowel() and \
         noun.isInPP() and noun.has('Case','NomAcc'):
      return [Constraint('Ecl|Len', 'Should be eclipsed or lenited by the preceding definite article')]
    return []

  def predictVerbEclipsis(self):
    if not self.isEclipsable():
      return []
    pr = self.getPredecessor()
    prToken = pr['token'].lower()
    # TODO: ADP "faoina ndearna", "gáire faoina ndúirt sé", 'dá bhfuil agam'
    if (pr.has('PartType','Vb') and prToken in ['an','go','nach']) or \
       (pr.has('PartType','Cmpl') and prToken in ['go','nach']) or \
       pr.isEclipsingRelativizer() or \
       (self.isPastFaigh() and prToken=='ní') or \
       (pr['upos']=='ADV' and prToken=='cá') or \
       (pr['upos']=='SCONJ' and \
           prToken in ['dá','go','mara','muna','mura','sula']):
      return [Constraint('Ecl', 'Should be eclipsed by preceding verbal particle')]
    return []

  def predictAdjectiveLenition(self):
    if not self.isLenitable():
      return []
    pr = self.getPredecessor()
    if pr['upos']=='AUX' and (pr.has('Tense','Past') or pr.has('Mood','Cnd')):
      return [Constraint('Len', 'Adjective is lenited after past or conditional copula')]
    if self['deprel']=='amod':
      h = self.getHead()
      if h.has('Number','Sing'):
        if h.has('Case','Gen') and h.has('Gender','Masc'):
          return [Constraint('Len', 'Adjective is lenited after genitive singular masculine noun')]
        if h.has('Case','NomAcc') and h.has('Gender','Fem'):
          return [Constraint('Len', 'Adjective is lenited after nominative singular feminine noun')]
        if h.has('Case','Voc'):
          return [Constraint('Len', 'Adjective is lenited after a vocative singular noun')]
      elif h.has('Number','Plur') and h.has('Case','NomAcc') and \
           h.hasSlenderFinalConsonant() and h['lemma'].lower()!='caora':
        return [Constraint('Len', 'Adjective is lenited after a nominative plural noun ending in a slender consonant')]
    return []
    
  def predictNounLenition(self):
    return [Constraint('Len','Allow any len',True)]
    if not self.isLenitable():
      return []

  def predictVerbLenition(self):
    if not self.isLenitable():
      return []
    if self.isLenitedPastVerbContext(self):
      return [Constraint('Len', 'This past tense verb must be lenited')]
    if self.has('Aspect','Imp') and self.has('Tense','Past') and self['lemma'] != 'abair':
      return [Constraint('Len', 'Imperfect verb must be lenited')]
    if self.has('Mood','Cnd') and self['lemma'] != 'abair':
      return [Constraint('Len', 'Conditional verb must be lenited')]
    if self.getPredecessor().isLenitingParticle():
      return [Constraint('Len', 'Verb is lenited after this verbal particle')]
    return []

  def predictAdjectivePrefixH(self):
    pr = self.getPredecessor()
    prToken = pr['token'].lower()
    if prToken in ['chomh','go']:
      return [Constraint('HPref', 'Adjective should have a prefix h')]
    # a haon, a hocht handled in predictOtherPrefixH
    return []

  # a (her), a dhá, á (her), cá, go, le, na (gsf), na (common pl)
  # Ó patronym, ordinals except chéad, and trí/ceithre/sé+uaire
  def predictNounPrefixH(self):
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
    if prToken in ['na','sna'] and self.has('Case','NomAcc') and \
          self.has('Number','Plur'):
      return [Constraint('HPref', 'Should have prefix h following “na”')]
    if prToken=='de' and self['lemma']=='Íde':
      return [Constraint('HPref', 'Should have prefix h in “de hÍde”')]
    return []

  def predictVerbPrefixH(self):
    pr = self.getPredecessor()
    prToken = pr['token'].lower()
    if prToken=='ná' and pr.has('Mood','Imp'):
      return [Constraint('HPref', 'Should have prefix h after “ná”')]
    return []

  def predictOtherPrefixH(self):
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
      return [Constraint('Emp', 'Could possibly be an emphatic ending but not certain', True)]
 
  def predictVowelForm(self):
    if re.search("b[’'h]?$", self['token'].lower()):
      return [Constraint('VF', 'Copula before vowel or f must have Form=VF')]

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
    return [Constraint('NomAcc|Gen|Dat|Voc', 'placeholder...', True)]
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
    return []

  def predictFormADP(self):
    ans = []
    pr = self.getPredecessor()
    prToken = pr['token'].lower()
    # annoying fixed phrases...
    if self['deprel']=='fixed' and \
       ((prToken=='go' and self['token'].lower()=='dtí') or \
        (prToken=='i' and self['token'].lower() in ['bhfeighil','dteannta','dtrátha','dtús','gceann','gcionn','gcoinne','gcóir','gcoitinne','mbun','ndiaidh'])):
      ans.append(Constraint('Ecl', 'Should be eclipsed in set phrase'))
    return ans

  # just in one set phrase; get rid of fixed or retag components?
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

  # Ecl, Len, HPref, e.g. i ngach, chuile, haon
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
    ans.extend(self.predictNounHPref())
    return ans

  # Ecl, Len, HPref
  def predictFormNUM(self):
    ans = []
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

  # Len, HPref, and 1x VF ("cérbh")
  def predictFormPRON(self):
    ans = self.predictVowelForm()
    return ans

  # Ecl, Len, HPref
  def predictFormPROPN(self):
    ans = self.predictNounLenition()
    return ans

  # (rarely) VF (murab, arb), 1x Len (dhá for dá)
  def predictFormSCONJ(self):
    ans = self.predictVowelForm()
    return ans

  # Ecl, Len, HPref, Emp, plus some with Direct (atá + relative forms)
  def predictFormVERB(self):
    ans = self.predictEmphasis()
    if self.has('PronType','Rel') and re.match(r'at[aá]',self['token'].lower()):
      ans.append(Constraint('Direct', 'Anything resembling atá should be have direct relative feature Form=Direct'))
    ans.extend(self.predictVerbEclipsis())
    ans.extend(self.predictVerbLenition())
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
    return [Constraint('Fem|Masc', 'placeholder...', True)]

  def predictGenderPROPN(self):
    return self.predictGenderNOUN()

  def predictGenderPRON(self):
    pronouns = {'é': 'Masc', 'eisean': 'Masc', 'í': 'Fem', 'ise': 'Fem', 'sé': 'Masc', 'seisean': 'Masc', 'sí': 'Fem', 'sise': 'Fem'}
    if self['lemma'] in pronouns:
      return [Constraint(pronouns[self['lemma']], 'Personal pronouns require correct Gender feature')]
    return []

  def predictMoodAUX(self):
    return [Constraint('Cnd|Int', 'Copula can sometimes have Mood=Int or Mood=Cnd', True)]

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
      if head.has('Case','NomAcc'):
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
    return [Constraint('Sing|Plur', 'Some pronomials have Number feature', True)]

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
    return [Constraint('Sing|Plur', 'Some verbs have Number feature', True)]
    return []

  def predictNumTypeNUM(self):
    return [Constraint('Card|Ord', 'Numbers have optional NumType feature', True)]

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
    return [Constraint('0|1|2|3', 'Tokens tagged ADP sometimes have the Person feature', True)]

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
    return [Constraint('0|1|2|3', 'Verbs sometimes have the Person feature', True)]

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
    return [Constraint('Yes', 'ADP could have Poss=Yes', True)]

  def predictPossDET(self):
    return [Constraint('Yes', 'DET could have Poss=Yes', True)]

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
      return [Constraint('Art|Emp', 'This could be an emphatic form', True)]
    if self.getDeprel()=='case':
      return [Constraint('Art', 'This could be PronType=Art', True)]
    return []

  def predictPronTypeADV(self):
    if self['lemma'] in ['cá', 'conas']:
      return [Constraint('Int', 'These interrogatives require PronType=Int')]
    return []
     
  def predictPronTypeAUX(self):
    if self['token'].lower() in ['seo','sin']:
      return [Constraint('Dem', 'Feature PronType=Dem is required here')]
    else:
      return [Constraint('Rel', 'Some copulas are PronType=Rel', True)]

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
    return [Constraint('Dem|Emp|Ind|Int|Rel', 'placeholder...',True)]

  def predictPronTypeVERB(self):
    tok = self['token'].lower()
    if re.match('at[aá]',tok):
      return [Constraint('Rel', 'Forms like “atá” require the feature PronType=Rel')]
    if re.search('s$',tok):
      return [Constraint('Rel', 'Verb forms ending in s are sometimes relative which would require PronType=Rel', True)]
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
    return [Constraint('Part', 'Adjectives can have VerbForm=Part feature', True)]

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
    return [Constraint('Cop', 'Pronouns sometimes have VerbForm=Cop feature', True)]

  def predictVerbFormSCONJ(self):
    # short list? currently arb, dar, más, mura, murab, murar, ós, sular
    return [Constraint('Cop', 'Conjunctions sometimes have VerbForm=Cop feature', True)]

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
           self.has('Case','NomAcc') and \
          (self.anyPrecedingDefiniteArticle() or self.precedingCen()):
        return [Constraint('TPref', 'Should have prefix t before feminine noun after an article')]
      if self.has('Number','Sing') and self.has('Gender','Masc') and \
           self.has('Case','Gen') and self.precedingDefiniteArticle():
        return [Constraint('TPref', 'Should have prefix t before genitive masculine noun after an article')]
    elif self.hasInitialVowel():
      # Exceptions in CO for oiread/iomad but these are genderless in treebank
      if self.has('Number','Sing') and self.has('Gender','Masc') and \
           self.has('Case','NomAcc') and not self.isInDativePP() and \
          (self.precedingDefiniteArticle() or self.precedingCen()):
        return [Constraint('TPref', 'Should have prefix t before masculine noun after an article')]
    return []

  def predictXFormPROPN(self):
    return self.predictXFormNOUN()

  ########################################################################

  def toLower(self, s):
    if len(s) > 1 and (s[0]=='t' or s[0]=='n') and s[1] in 'AEIOUÁÉÍÓÚ':
      return s[0]+'-'+s[1:].lower()
    else:
      return s.lower()
