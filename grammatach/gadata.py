
compoundPrepositions = frozenset([
  'ar aghaidh',
  'ar chúl',
  'ar feadh',
  'ar fud',
  'ar lorg',
  'ar nós',
  'ar son',
  'd\' ainneoin',
  'de bharr',
  'de chois',
  'de chóir',
  'de dheasca',
  'de dheascaibh',
  'de dhíobháil',
  'de réir',
  'de thairbhe',
  'faoi bhráid',
  'fá bhráid',
  'fé bhráid',
  'faoi bhun',
  'faoi cheann',
  'faoi choinne',
  'fá choinne',
  'fé choinne',
  'faoi dhéin',
  'faoi réir',
  'go ceann',
  'i bhfeighil',
  'i bhfianaise',
  'i bhfochair',
  'i dteannta',
  'i dtrátha',
  'i dtuilleamaí',
  'i gcaitheamh',
  'i gceann',
  'i gcionn',
  'i gcoinne',
  'i gcóir',
  'i gcomhair',
  'i gcosamar',
  'i gcuideachta',
  'i lar',
  'i lár',
  'i láthair',
  'i leith',
  'i mbun',
  'i measc',
  'i ndiaidh',
  'i rith',
  'in aghaidh',
  'in aice',
  'in ainneoin',
  'in airicis',
  'in éadan',
  'in ionad',
  'le cois',
  'le haghaidh',
  'le hais',
  'le linn',
  'os cionn',
  'ós cionn',
  'os coinne',
  'os comhair',
  'ós comhair',
  'tar eis',
  'tar éis',
  'thar ceann'
])

# surface tokens for which we need to permit None after "ar"
unlenitedAfterAr = frozenset([
  'ball',
  'bannaí',
  'barr',
  'bior',
  'bís',
  'bith',
  'bolg',
  'bord',
  'bóthar',
  'buile',
  'bun',
  'cairde',
  'camchuairt',
  'ceal',
  'ceann',
  'ceant',
  'cíos',
  'clár',
  'clé',
  'cóimhéid',
  'comhaois',
  'comhchéim',
  'comhréir',
  'comhscór',
  'conradh',
  'cosa',
  'cothrom',
  'crith',
  'crochadh',
  'cuairt',
  'deireadh',
  'deis',
  'deoraíocht',
  'díol',
  'díotáil',
  'dóigh',
  'domhan',
  'dualgas',
  'fad',
  'fáil',
  'fán',
  'farraige',
  'feadh',
  'féarach',
  'feitheamh',
  'fionraí',
  'foluain',
  'fónamh',
  'foscadh',
  'fostú',
  'fuaid',
  'fud',
  'gor',
  'maidin',
  'maos',
  'marthain',
  'meán',
  'meisce',
  'mire',
  'muin',
  'muir',
  'pinsean',
  'saoire',
  'seachrán',
  'seilbh',
  'seirbhís',
  'sileadh',
  'siúl',
  'snámh',
  'sodar',
  'son',
  'taifead',
  'tairiscint',
  'taispeáint',
  'talamh',
  'teachtadh',
  'tí',
  'tinneall',
  'tír',
  'trastomhas',
  'turas'
])

# surface tokens for which we need to permit None after "thar"
unlenitedAfterThar = frozenset([
  'baile',
  'barr',
  'bóchna',
  'bord',
  'bráid',
  'bruach',
  'cailc',
  'caladh',
  'ceal',
  'ceann',
  'ceart',
  'cionn',
  'claí',
  'clár',
  'cnoc',
  'cuimse',
  'droichead',
  'droim',
  'fál',
  'farraige',
  'fóir',
  'fulaingt',
  'goimh',
  'gualainn',
  'maoil',
  'meán',
  'muir',
  'paróiste',
  'sáile',
  'sliabh',
  'tairseach',
  'taobh',
  'téarma',
  'teora',
  'teorainn',
  'timpeall',
  'tír',
  'toinn',
  'tréanmhuir',
  'tréimhse'
])
