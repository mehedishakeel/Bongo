/**
 * Bongo · Avro Phonetic Engine for Web
 * Full OmicronLab Avro Phonetic scheme rules ported from okkhor (Rust)
 * Real-time, zero-dependency, bidirectional phonetic transliteration
 */
(function (global) {
    'use strict';

    var AVRO_PATTERNS = [{"find":"NgkSh","default":"ঙ্ক্ষ","rules":[]},{"find":"Ngkkh","default":"ঙ্ক্ষ","rules":[]},{"find":"kkhN","default":"ক্ষ্ণ","rules":[]},{"find":"kShN","default":"ক্ষ্ণ","rules":[]},{"find":"kkhm","default":"ক্ষ্ম","rules":[]},{"find":"kShm","default":"ক্ষ্ম","rules":[]},{"find":"NGch","default":"ঞ্ছ","rules":[]},{"find":"Nggh","default":"ঙ্ঘ","rules":[]},{"find":"Ngkh","default":"ঙ্খ","rules":[]},{"find":"NGjh","default":"ঞ্ঝ","rules":[]},{"find":"ngOU","default":"ঙ্গৌ","rules":[]},{"find":"ngOI","default":"ঙ্গৈ","rules":[]},{"find":"Ngkx","default":"ঙ্ক্ষ","rules":[]},{"find":"rri`","default":"ৃ","rules":[]},{"find":"shch","default":"শ্ছ","rules":[]},{"find":"ShTh","default":"ষ্ঠ","rules":[]},{"find":"Shph","default":"ষ্ফ","rules":[]},{"find":"psh","default":"পশ","rules":[]},{"find":"bhl","default":"ভ্ল","rules":[]},{"find":"bdh","default":"ব্ধ","rules":[]},{"find":"cNG","default":"চ্ঞ","rules":[]},{"find":"cch","default":"চ্ছ","rules":[]},{"find":"dhn","default":"ধ্ন","rules":[]},{"find":"dhm","default":"ধ্ম","rules":[]},{"find":"dgh","default":"দ্ঘ","rules":[]},{"find":"ddh","default":"দ্ধ","rules":[]},{"find":"dbh","default":"দ্ভ","rules":[]},{"find":"...","default":"...","rules":[]},{"find":"ghn","default":"ঘ্ন","rules":[]},{"find":"Ghn","default":"ঘ্ন","rules":[]},{"find":"gdh","default":"গ্ধ","rules":[]},{"find":"Gdh","default":"গ্ধ","rules":[]},{"find":"jjh","default":"জ্ঝ","rules":[]},{"find":"jNG","default":"জ্ঞ","rules":[]},{"find":"kxN","default":"ক্ষ্ণ","rules":[]},{"find":"kxm","default":"ক্ষ্ম","rules":[]},{"find":"kkh","default":"ক্ষ","rules":[]},{"find":"kSh","default":"ক্ষ","rules":[]},{"find":"ksh","default":"কশ","rules":[]},{"find":"lbh","default":"ল্ভ","rules":[]},{"find":"ldh","default":"ল্ধ","rules":[]},{"find":"lkh","default":"লখ","rules":[]},{"find":"lgh","default":"লঘ","rules":[]},{"find":"lph","default":"লফ","rules":[]},{"find":"mth","default":"ম্থ","rules":[]},{"find":"mph","default":"ম্ফ","rules":[]},{"find":"mbh","default":"ম্ভ","rules":[]},{"find":"mpl","default":"মপ্ল","rules":[]},{"find":"NGc","default":"ঞ্চ","rules":[]},{"find":"nch","default":"ঞ্ছ","rules":[]},{"find":"njh","default":"ঞ্ঝ","rules":[]},{"find":"ngh","default":"ঙ্ঘ","rules":[]},{"find":"Ngk","default":"ঙ্ক","rules":[]},{"find":"Ngx","default":"ঙ্ষ","rules":[]},{"find":"Ngg","default":"ঙ্গ","rules":[]},{"find":"Ngm","default":"ঙ্ম","rules":[]},{"find":"NGj","default":"ঞ্জ","rules":[]},{"find":"ndh","default":"ন্ধ","rules":[]},{"find":"nTh","default":"ন্ঠ","rules":[]},{"find":"NTh","default":"ণ্ঠ","rules":[]},{"find":"nth","default":"ন্থ","rules":[]},{"find":"nkh","default":"ঙ্খ","rules":[]},{"find":"ngo","default":"ঙ্গ","rules":[]},{"find":"nga","default":"ঙ্গা","rules":[]},{"find":"ngi","default":"ঙ্গি","rules":[]},{"find":"ngI","default":"ঙ্গী","rules":[]},{"find":"ngu","default":"ঙ্গু","rules":[]},{"find":"ngU","default":"ঙ্গূ","rules":[]},{"find":"nge","default":"ঙ্গে","rules":[]},{"find":"ngO","default":"ঙ্গো","rules":[]},{"find":"NDh","default":"ণ্ঢ","rules":[]},{"find":"nsh","default":"নশ","rules":[]},{"find":"Ngr","default":"ঙর","rules":[]},{"find":"NGr","default":"ঞর","rules":[]},{"find":"ngr","default":"ংর","rules":[]},{"find":"OI`","default":"ৈ","rules":[]},{"find":"OU`","default":"ৌ","rules":[]},{"find":"phl","default":"ফ্ল","rules":[]},{"find":"rri","default":"ৃ","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"}],"replace":"ঋ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ঋ"}]},{"find":"rrZ","default":"রর‍্য","rules":[]},{"find":"rry","default":"রর‍্য","rules":[]},{"find":"Sch","default":"শ্ছ","rules":[]},{"find":"skl","default":"স্ক্ল","rules":[]},{"find":"skh","default":"স্খ","rules":[]},{"find":"sth","default":"স্থ","rules":[]},{"find":"sph","default":"স্ফ","rules":[]},{"find":"shc","default":"শ্চ","rules":[]},{"find":"sht","default":"শ্ত","rules":[]},{"find":"shn","default":"শ্ন","rules":[]},{"find":"shm","default":"শ্ম","rules":[]},{"find":"shl","default":"শ্ল","rules":[]},{"find":"Shk","default":"ষ্ক","rules":[]},{"find":"ShT","default":"ষ্ট","rules":[]},{"find":"ShN","default":"ষ্ণ","rules":[]},{"find":"Shp","default":"ষ্প","rules":[]},{"find":"Shf","default":"ষ্ফ","rules":[]},{"find":"Shm","default":"ষ্ম","rules":[]},{"find":"spl","default":"স্প্ল","rules":[]},{"find":"oo`","default":"ু","rules":[]},{"find":"tth","default":"ত্থ","rules":[]},{"find":"t``","default":"ৎ","rules":[]},{"find":"ee`","default":"ী","rules":[]},{"find":"bj","default":"ব্জ","rules":[]},{"find":"bd","default":"ব্দ","rules":[]},{"find":"bb","default":"ব্ব","rules":[]},{"find":"bl","default":"ব্ল","rules":[]},{"find":"bh","default":"ভ","rules":[]},{"find":"vl","default":"ভ্ল","rules":[]},{"find":"cc","default":"চ্চ","rules":[]},{"find":"ch","default":"ছ","rules":[]},{"find":"dv","default":"দ্ভ","rules":[]},{"find":"dm","default":"দ্ম","rules":[]},{"find":"DD","default":"ড্ড","rules":[]},{"find":"Dh","default":"ঢ","rules":[]},{"find":"dh","default":"ধ","rules":[]},{"find":"dg","default":"দ্গ","rules":[]},{"find":"dd","default":"দ্দ","rules":[]},{"find":".`","default":".","rules":[]},{"find":"..","default":"।।","rules":[]},{"find":"gN","default":"গ্ণ","rules":[]},{"find":"GN","default":"গ্ণ","rules":[]},{"find":"gn","default":"গ্ন","rules":[]},{"find":"Gn","default":"গ্ন","rules":[]},{"find":"gm","default":"গ্ম","rules":[]},{"find":"Gm","default":"গ্ম","rules":[]},{"find":"gl","default":"গ্ল","rules":[]},{"find":"Gl","default":"গ্ল","rules":[]},{"find":"gg","default":"জ্ঞ","rules":[]},{"find":"GG","default":"জ্ঞ","rules":[]},{"find":"Gg","default":"জ্ঞ","rules":[]},{"find":"gG","default":"জ্ঞ","rules":[]},{"find":"gh","default":"ঘ","rules":[]},{"find":"Gh","default":"ঘ","rules":[]},{"find":"hN","default":"হ্ণ","rules":[]},{"find":"hn","default":"হ্ন","rules":[]},{"find":"hm","default":"হ্ম","rules":[]},{"find":"hl","default":"হ্ল","rules":[]},{"find":"jh","default":"ঝ","rules":[]},{"find":"jj","default":"জ্জ","rules":[]},{"find":"kx","default":"ক্ষ","rules":[]},{"find":"kk","default":"ক্ক","rules":[]},{"find":"kT","default":"ক্ট","rules":[]},{"find":"kt","default":"ক্ত","rules":[]},{"find":"kl","default":"ক্ল","rules":[]},{"find":"ks","default":"ক্স","rules":[]},{"find":"kh","default":"খ","rules":[]},{"find":"lk","default":"ল্ক","rules":[]},{"find":"lg","default":"ল্গ","rules":[]},{"find":"lT","default":"ল্ট","rules":[]},{"find":"lD","default":"ল্ড","rules":[]},{"find":"lp","default":"ল্প","rules":[]},{"find":"lv","default":"ল্ভ","rules":[]},{"find":"lm","default":"ল্ম","rules":[]},{"find":"ll","default":"ল্ল","rules":[]},{"find":"lb","default":"ল্ব","rules":[]},{"find":"mn","default":"ম্ন","rules":[]},{"find":"mp","default":"ম্প","rules":[]},{"find":"mv","default":"ম্ভ","rules":[]},{"find":"mm","default":"ম্ম","rules":[]},{"find":"ml","default":"ম্ল","rules":[]},{"find":"mb","default":"ম্ব","rules":[]},{"find":"mf","default":"ম্ফ","rules":[]},{"find":"nj","default":"ঞ্জ","rules":[]},{"find":"Ng","default":"ঙ","rules":[]},{"find":"NG","default":"ঞ","rules":[]},{"find":"nk","default":"ঙ্ক","rules":[]},{"find":"ng","default":"ং","rules":[]},{"find":"nn","default":"ন্ন","rules":[]},{"find":"NN","default":"ণ্ণ","rules":[]},{"find":"Nn","default":"ণ্ন","rules":[]},{"find":"nm","default":"ন্ম","rules":[]},{"find":"Nm","default":"ণ্ম","rules":[]},{"find":"nd","default":"ন্দ","rules":[]},{"find":"nT","default":"ন্ট","rules":[]},{"find":"NT","default":"ণ্ট","rules":[]},{"find":"nD","default":"ন্ড","rules":[]},{"find":"ND","default":"ণ্ড","rules":[]},{"find":"nt","default":"ন্ত","rules":[]},{"find":"ns","default":"ন্স","rules":[]},{"find":"nc","default":"ঞ্চ","rules":[]},{"find":"O`","default":"ো","rules":[]},{"find":"OI","default":"ৈ","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"}],"replace":"ঐ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ঐ"}]},{"find":"OU","default":"ৌ","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"}],"replace":"ঔ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ঔ"}]},{"find":"pT","default":"প্ট","rules":[]},{"find":"pt","default":"প্ত","rules":[]},{"find":"pn","default":"প্ন","rules":[]},{"find":"pp","default":"প্প","rules":[]},{"find":"pl","default":"প্ল","rules":[]},{"find":"ps","default":"প্স","rules":[]},{"find":"ph","default":"ফ","rules":[]},{"find":"fl","default":"ফ্ল","rules":[]},{"find":"rZ","default":"র‍্য","rules":[{"matches":[{"type":"PrefixIs","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"r"},{"type":"PrefixIsNot","scope":"Char","val":"y"},{"type":"PrefixIsNot","scope":"Char","val":"w"},{"type":"PrefixIsNot","scope":"Char","val":"x"}],"replace":"্র্য"}]},{"find":"ry","default":"র‍্য","rules":[{"matches":[{"type":"PrefixIs","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"r"},{"type":"PrefixIsNot","scope":"Char","val":"y"},{"type":"PrefixIsNot","scope":"Char","val":"w"},{"type":"PrefixIsNot","scope":"Char","val":"x"}],"replace":"্র্য"}]},{"find":"rr","default":"রর","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Vowel"},{"type":"SuffixIsNot","scope":"Char","val":"r"},{"type":"SuffixIsNot","scope":"Punctuation"}],"replace":"র্"},{"matches":[{"type":"PrefixIs","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"r"}],"replace":"্রর"}]},{"find":"Rg","default":"ড়্গ","rules":[]},{"find":"Rh","default":"ঢ়","rules":[]},{"find":"sk","default":"স্ক","rules":[]},{"find":"Sc","default":"শ্চ","rules":[]},{"find":"sT","default":"স্ট","rules":[]},{"find":"st","default":"স্ত","rules":[]},{"find":"sn","default":"স্ন","rules":[]},{"find":"sp","default":"স্প","rules":[]},{"find":"sf","default":"স্ফ","rules":[]},{"find":"sm","default":"স্ম","rules":[]},{"find":"sl","default":"স্ল","rules":[]},{"find":"sh","default":"শ","rules":[]},{"find":"Sc","default":"শ্চ","rules":[]},{"find":"St","default":"শ্ত","rules":[]},{"find":"Sn","default":"শ্ন","rules":[]},{"find":"Sm","default":"শ্ম","rules":[]},{"find":"Sl","default":"শ্ল","rules":[]},{"find":"Sh","default":"ষ","rules":[]},{"find":"oo","default":"ু","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"উ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"উ"}]},{"find":"o`","default":"","rules":[]},{"find":"oZ","default":"অ্য","rules":[]},{"find":"TT","default":"ট্ট","rules":[]},{"find":"Tm","default":"ট্ম","rules":[]},{"find":"Th","default":"ঠ","rules":[]},{"find":"tn","default":"ত্ন","rules":[]},{"find":"tm","default":"ত্ম","rules":[]},{"find":"th","default":"থ","rules":[]},{"find":"tt","default":"ত্ত","rules":[]},{"find":"aZ","default":"অ্যা","rules":[]},{"find":"AZ","default":"অ্যা","rules":[]},{"find":"a`","default":"া","rules":[]},{"find":"A`","default":"া","rules":[]},{"find":"i`","default":"ি","rules":[]},{"find":"I`","default":"ী","rules":[]},{"find":"u`","default":"ু","rules":[]},{"find":"U`","default":"ূ","rules":[]},{"find":"ee","default":"ী","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঈ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঈ"}]},{"find":"e`","default":"ে","rules":[]},{"find":":`","default":":","rules":[]},{"find":"^`","default":"^","rules":[]},{"find":",,","default":"্‌","rules":[]},{"find":"b","default":"ব","rules":[]},{"find":"v","default":"ভ","rules":[]},{"find":"c","default":"চ","rules":[]},{"find":"D","default":"ড","rules":[]},{"find":"d","default":"দ","rules":[]},{"find":".","default":"।","rules":[{"matches":[{"type":"SuffixIs","scope":"Number"}],"replace":"."}]},{"find":"g","default":"গ","rules":[]},{"find":"G","default":"গ","rules":[]},{"find":"h","default":"হ","rules":[]},{"find":"j","default":"জ","rules":[]},{"find":"J","default":"জ","rules":[]},{"find":"k","default":"ক","rules":[]},{"find":"l","default":"ল","rules":[]},{"find":"m","default":"ম","rules":[]},{"find":"0","default":"০","rules":[]},{"find":"1","default":"১","rules":[]},{"find":"2","default":"২","rules":[]},{"find":"3","default":"৩","rules":[]},{"find":"4","default":"৪","rules":[]},{"find":"5","default":"৫","rules":[]},{"find":"6","default":"৬","rules":[]},{"find":"7","default":"৭","rules":[]},{"find":"8","default":"৮","rules":[]},{"find":"9","default":"৯","rules":[]},{"find":"n","default":"ন","rules":[]},{"find":"N","default":"ণ","rules":[]},{"find":"O","default":"ো","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"}],"replace":"ও"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ও"}]},{"find":"f","default":"ফ","rules":[]},{"find":"p","default":"প","rules":[]},{"find":"R","default":"ড়","rules":[]},{"find":"r","default":"র","rules":[{"matches":[{"type":"PrefixIs","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"r"},{"type":"PrefixIsNot","scope":"Char","val":"y"},{"type":"PrefixIsNot","scope":"Char","val":"w"},{"type":"PrefixIsNot","scope":"Char","val":"x"},{"type":"PrefixIsNot","scope":"Char","val":"Z"}],"replace":"্র"}]},{"find":"s","default":"স","rules":[]},{"find":"S","default":"শ","rules":[]},{"find":"o","default":"","rules":[{"matches":[{"type":"PrefixIs","scope":"Vowel"},{"type":"PrefixIsNot","scope":"Char","val":"o"}],"replace":"ও"},{"matches":[{"type":"PrefixIs","scope":"Vowel"},{"type":"PrefixIs","scope":"Char","val":"o"}],"replace":"অ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"অ"}]},{"find":"T","default":"ট","rules":[]},{"find":"t","default":"ত","rules":[]},{"find":"a","default":"া","rules":[{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"আ"},{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"a"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"য়া"},{"matches":[{"type":"PrefixIs","scope":"Char","val":"a"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"আ"}]},{"find":"i","default":"ি","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ই"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ই"}]},{"find":"I","default":"ী","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঈ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঈ"}]},{"find":"u","default":"ু","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"উ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"উ"}]},{"find":"U","default":"ূ","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঊ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঊ"}]},{"find":"e","default":"ে","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"এ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"এ"}]},{"find":"z","default":"য","rules":[]},{"find":"Z","default":"্য","rules":[]},{"find":"y","default":"্য","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Punctuation"}],"replace":"য়"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ইয়"}]},{"find":"Y","default":"য়","rules":[]},{"find":"q","default":"ক","rules":[]},{"find":"w","default":"ও","rules":[{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIs","scope":"Vowel"}],"replace":"ওয়"},{"matches":[{"type":"PrefixIs","scope":"Consonant"}],"replace":"্ব"}]},{"find":"x","default":"ক্স","rules":[{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"এক্স"}]},{"find":":","default":"ঃ","rules":[]},{"find":"^","default":"ঁ","rules":[]},{"find":",","default":",","rules":[]},{"find":"$","default":"৳","rules":[]},{"find":"`","default":"","rules":[]}];

    var AVRO_DICTIONARY = {
  "ami": [
    "আমি",
    "আম",
    "আমায়",
    "আমেরিকায়",
    "আমার"
  ],
  "amader": [
    "আমাদের",
    "আমোদ",
    "আমড়া"
  ],
  "amar": [
    "আমার",
    "আমরা",
    "অমর"
  ],
  "amra": [
    "আমরা"
  ],
  "amake": [
    "আমাকে"
  ],
  "tumi": [
    "তুমি",
    "তোমরা",
    "তোমার"
  ],
  "tomader": [
    "তোমাদের"
  ],
  "tomar": [
    "তোমার"
  ],
  "tomake": [
    "তোমাকে"
  ],
  "tomay": [
    "তোমায়",
    "তোমাকে"
  ],
  "apni": [
    "আপনি",
    "আপনে",
    "আপ্নি"
  ],
  "apnader": [
    "আপনাদের"
  ],
  "apnar": [
    "আপনার"
  ],
  "apnake": [
    "আপনাকে"
  ],
  "she": [
    "সে",
    "শে"
  ],
  "tini": [
    "তিনি"
  ],
  "tara": [
    "তারা"
  ],
  "tader": [
    "তাদের"
  ],
  "taderke": [
    "তাদেরকে"
  ],
  "ora": [
    "ওরা"
  ],
  "oder": [
    "ওদের"
  ],
  "era": [
    "এরা"
  ],
  "eder": [
    "এদের"
  ],
  "kemon": [
    "কেমন",
    "কেমনে"
  ],
  "achen": [
    "আছেন",
    "আছি",
    "আছে"
  ],
  "achi": [
    "আছি"
  ],
  "ache": [
    "আছে"
  ],
  "achilo": [
    "ছিল",
    "আছিল"
  ],
  "chilo": [
    "ছিল"
  ],
  "chilam": [
    "ছিলাম"
  ],
  "chile": [
    "ছিলে"
  ],
  "chilen": [
    "ছিলেন"
  ],
  "bhalo": [
    "ভালো",
    "ভাল",
    "ভালা"
  ],
  "valo": [
    "ভালো",
    "ভাল"
  ],
  "bhalobashi": [
    "ভালোবাসি",
    "ভালোবাসা"
  ],
  "valobashi": [
    "ভালোবাসি"
  ],
  "bhalobasha": [
    "ভালোবাসা",
    "ভালোবাসায়"
  ],
  "valobasha": [
    "ভালোবাসা"
  ],
  "dhonnobad": [
    "ধন্যবাদ",
    "ধন্য",
    "ধন"
  ],
  "bangla": [
    "বাংলা",
    "বাঙলা",
    "বাঙালি",
    "বাংলাদেশ"
  ],
  "bangladesh": [
    "বাংলাদেশ",
    "বাংলাদেশী"
  ],
  "banglay": [
    "বাংলায়",
    "বাংলায়",
    "বাঙলায়"
  ],
  "shonar": [
    "সোনার",
    "শোনার",
    "সুন্দর"
  ],
  "sonar": [
    "সোনার"
  ],
  "gan": [
    "গান",
    "গণ",
    "জ্ঞান"
  ],
  "gai": [
    "গাই",
    "গায়ে"
  ],
  "bongo": [
    "বঙ্গ",
    "বঙ্গবন্ধু",
    "বঙ্গোপসাগর"
  ],
  "lekho": [
    "লেখো",
    "লেখা",
    "লেখক"
  ],
  "likhi": [
    "লিখি"
  ],
  "likhte": [
    "লিখতে"
  ],
  "lekha": [
    "লেখা"
  ],
  "onek": [
    "অনেক",
    "অনেকে",
    "অনুপ"
  ],
  "shob": [
    "সব",
    "শব",
    "সবাই"
  ],
  "sob": [
    "সব",
    "সবাই"
  ],
  "shobai": [
    "সবাই"
  ],
  "sobai": [
    "সবাই"
  ],
  "shobar": [
    "সবার",
    "শোবার"
  ],
  "sobar": [
    "সবার"
  ],
  "shobaike": [
    "সবাইকে"
  ],
  "shanti": [
    "শান্তি",
    "শান্ত"
  ],
  "kolkata": [
    "কলকাতা",
    "কলিকাতা"
  ],
  "dhaka": [
    "ঢাকা",
    "ঢাকাই",
    "ঢাক"
  ],
  "robindronath": [
    "রবীন্দ্রনাথ",
    "রবি",
    "রব"
  ],
  "kazi": [
    "কাজী",
    "কাজি"
  ],
  "nazrul": [
    "নজরুল"
  ],
  "koto": [
    "কত",
    "কতো"
  ],
  "kichu": [
    "কিছু",
    "কিছুই"
  ],
  "desh": [
    "দেশ",
    "দেশে",
    "দেশের"
  ],
  "deshe": [
    "দেশে"
  ],
  "desher": [
    "দেশের"
  ],
  "manush": [
    "মানুষ",
    "মানুষের",
    "মানুষকে"
  ],
  "manushe": [
    "মানুষে"
  ],
  "manusher": [
    "মানুষের"
  ],
  "bondhu": [
    "বন্ধু",
    "বন্ধুরা",
    "বন্ধুর"
  ],
  "bondhura": [
    "বন্ধুরা"
  ],
  "khabar": [
    "খাবার",
    "খবর"
  ],
  "khobor": [
    "খবর",
    "খবরে"
  ],
  "shundor": [
    "সুন্দর",
    "সুন্দরী"
  ],
  "sundor": [
    "সুন্দর"
  ],
  "ranna": [
    "রান্না",
    "রান্নাঘর"
  ],
  "kothay": [
    "কোথায়",
    "কথায়"
  ],
  "shomoy": [
    "সময়",
    "সাময়িক"
  ],
  "somoy": [
    "সময়"
  ],
  "protidin": [
    "প্রতিদিন"
  ],
  "notun": [
    "নতুন",
    "নূতন"
  ],
  "purono": [
    "পুরোনো",
    "পুরনো"
  ],
  "shobdo": [
    "শব্দ",
    "শব্দকোষ"
  ],
  "sobdo": [
    "শব্দ"
  ],
  "ki": [
    "কি",
    "কী"
  ],
  "keno": [
    "কেন",
    "কেনো"
  ],
  "kobe": [
    "কবে"
  ],
  "kothao": [
    "কোথাও"
  ],
  "kokhon": [
    "কখন",
    "কখনো"
  ],
  "ekhon": [
    "এখন",
    "এখনো"
  ],
  "tokhon": [
    "তখন",
    "তখনো"
  ],
  "jokhon": [
    "যখন",
    "যখনই"
  ],
  "ei": [
    "এই"
  ],
  "oi": [
    "ওই",
    "ঐ"
  ],
  "shei": [
    "সেই"
  ],
  "je": [
    "যে",
    "যেসব"
  ],
  "o": [
    "ও"
  ],
  "ebong": [
    "এবং"
  ],
  "ar": [
    "আর",
    "আরও"
  ],
  "kintu": [
    "কিন্তু"
  ],
  "ba": [
    "বা"
  ],
  "othoba": [
    "অথবা"
  ],
  "na": [
    "না",
    "নাই"
  ],
  "hacche": [
    "হচ্ছে"
  ],
  "hocche": [
    "হচ্ছে"
  ],
  "hobe": [
    "হবে",
    "হবেন"
  ],
  "hobar": [
    "হবার"
  ],
  "hoyeche": [
    "হয়েছে"
  ],
  "kaj": [
    "কাজ",
    "কাজে"
  ],
  "kaje": [
    "কাজে"
  ],
  "basha": [
    "বাসা",
    "ভাষা"
  ],
  "bhasha": [
    "ভাষা",
    "ভাষায়"
  ],
  "bari": [
    "বাড়ি",
    "বারি"
  ],
  "ghor": [
    "ঘর",
    "ঘরে"
  ],
  "boi": [
    "বই",
    "বইয়ের"
  ],
  "kotha": [
    "কথা",
    "কথায়"
  ],
  "shune": [
    "শুনে",
    "শুনেছি"
  ],
  "shunbo": [
    "শুনব",
    "শুনবো"
  ],
  "shunte": [
    "শুনতে"
  ],
  "shuni": [
    "শুনি"
  ],
  "dekhe": [
    "দেখে",
    "দেখেছি"
  ],
  "dekha": [
    "দেখা",
    "দেখার"
  ],
  "dekho": [
    "দেখো",
    "দেখ"
  ],
  "dekhi": [
    "দেখি"
  ],
  "dekhte": [
    "দেখতে"
  ],
  "ashun": [
    "আসুন"
  ],
  "ashbo": [
    "আসব",
    "আসবো"
  ],
  "ashchi": [
    "আসছি"
  ],
  "aschi": [
    "আসছি"
  ],
  "ashlam": [
    "আসলাম"
  ],
  "jao": [
    "যাও"
  ],
  "jai": [
    "যাই"
  ],
  "jacchi": [
    "যাচ্ছি"
  ],
  "jabo": [
    "যাব",
    "যাবো"
  ],
  "gelam": [
    "গেলাম"
  ],
  "geche": [
    "গেছে",
    "গিয়েছে"
  ],
  "korbo": [
    "করব",
    "করবো"
  ],
  "korchi": [
    "করছি"
  ],
  "kori": [
    "করি"
  ],
  "koro": [
    "করো",
    "কর"
  ],
  "korben": [
    "করবেন"
  ],
  "kore": [
    "করে",
    "করেছি"
  ],
  "korechi": [
    "করেছি"
  ],
  "shokal": [
    "সকাল",
    "সকালে"
  ],
  "sokal": [
    "সকাল"
  ],
  "dupur": [
    "দুপুর",
    "দুপুরে"
  ],
  "shondha": [
    "সন্ধ্যা",
    "সন্ধ্যায়"
  ],
  "sondha": [
    "সন্ধ্যা"
  ],
  "rat": [
    "রাত",
    "রাতে"
  ],
  "din": [
    "দিন",
    "দিনে"
  ],
  "mash": [
    "মাস",
    "মাসে"
  ],
  "bochor": [
    "বছর",
    "বছরে"
  ],
  "mon": [
    "মন",
    "মনে"
  ],
  "mone": [
    "মনে",
    "মনেও"
  ],
  "janina": [
    "জানিনা",
    "জানি না"
  ],
  "parina": [
    "পারিনা",
    "পারি না"
  ],
  "pari": [
    "পারি"
  ],
  "parbo": [
    "পারব",
    "পারবো"
  ],
  "parbe": [
    "পারবে"
  ],
  "bhabchi": [
    "ভাবছি"
  ],
  "bhabi": [
    "ভাবি"
  ],
  "bhabo": [
    "ভাবো",
    "ভাব"
  ],
  "bhabte": [
    "ভাবতে"
  ],
  "khub": [
    "খুব",
    "খুবি"
  ],
  "shotti": [
    "সত্যি",
    "সত্য"
  ],
  "sotti": [
    "সত্যি"
  ],
  "shothik": [
    "সঠিক"
  ],
  "sothik": [
    "সঠিক"
  ],
  "bhul": [
    "ভুল",
    "ভুলে"
  ],
  "thik": [
    "ঠিক",
    "ঠিকই"
  ],
  "shohoj": [
    "সহজ",
    "সহজে"
  ],
  "sohoj": [
    "সহজ"
  ],
  "kothin": [
    "কঠিন"
  ],
  "shobcheye": [
    "সবচেয়ে",
    "সবচাইতে"
  ],
  "sobcheye": [
    "সবচেয়ে"
  ],
  "prothom": [
    "প্রথম",
    "প্রথমে"
  ],
  "shesh": [
    "শেষ",
    "শেষে"
  ],
  "shuru": [
    "শুরু",
    "শুরুতে"
  ],
  "suru": [
    "শুরু"
  ],
  "subheccha": [
    "শুভেচ্ছা"
  ],
  "shubheccha": [
    "শুভেচ্ছা"
  ],
  "shuvo": [
    "শুভ"
  ],
  "shubh": [
    "শুভ"
  ],
  "computer": [
    "কম্পিউটার"
  ],
  "keyboard": [
    "কীবোর্ড",
    "কিবোর্ড"
  ],
  "software": [
    "সফটওয়্যার",
    "সফটওয়্যার"
  ],
  "native": [
    "নেটিভ"
  ],
  "apple": [
    "অ্যাপল",
    "আপেল"
  ],
  "silicon": [
    "সিলিকন"
  ],
  "mac": [
    "ম্যাক"
  ],
  "macos": [
    "ম্যাকওএস"
  ],
  "macbook": [
    "ম্যাকবুক"
  ],
  "font": [
    "ফন্ট"
  ],
  "download": [
    "ডাউনলোড"
  ],
  "install": [
    "ইনস্টল"
  ],
  "free": [
    "ফ্রি"
  ],
  "typing": [
    "টাইপিং"
  ],
  "bengali": [
    "বাঙালি",
    "বেঙ্গলি"
  ],
  "mehedi": [
    "মেহেদি",
    "মেহেদী"
  ],
  "shakeel": [
    "শাকিল",
    "শাকীল"
  ]
};

    function conditionalLowercase(c) {
        var lc = c.toLowerCase();
        if (lc === 'o' || lc === 'i' || lc === 'u' || lc === 'd' || lc === 'g' ||
            lc === 'j' || lc === 'n' || lc === 'r' || lc === 's' || lc === 't' ||
            lc === 'y' || lc === 'z') {
            return c;
        }
        return lc;
    }

    function isVowel(c) {
        return c === 'a' || c === 'e' || c === 'i' || c === 'o' || c === 'u' ||
               c === 'A' || c === 'E' || c === 'I' || c === 'O' || c === 'U';
    }

    function isConsonant(c) {
        return !isVowel(c) && ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z'));
    }

    function isPunctuation(c) {
        return !((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z'));
    }

    function isDigit(c) {
        return c >= '0' && c <= '9';
    }

    function matchCondition(cond, prefix, suffix) {
        var isPrefix = cond.type === 'PrefixIs' || cond.type === 'PrefixIsNot';
        var isPositive = cond.type === 'PrefixIs' || cond.type === 'SuffixIs';
        var ch = isPrefix ? prefix : suffix;
        var ok = false;
        switch (cond.scope) {
            case 'Vowel': ok = isVowel(ch); break;
            case 'Consonant': ok = isConsonant(ch); break;
            case 'Punctuation': ok = isPunctuation(ch); break;
            case 'Number': ok = isDigit(ch); break;
            case 'Char': ok = (ch === cond.val); break;
            default: ok = false;
        }
        return isPositive ? ok : !ok;
    }

    function getReplacement(pattern, prefix, suffix) {
        if (pattern.rules && pattern.rules.length > 0) {
            for (var i = 0; i < pattern.rules.length; i++) {
                var rule = pattern.rules[i];
                var allMatch = true;
                for (var j = 0; j < rule.matches.length; j++) {
                    if (!matchCondition(rule.matches[j], prefix, suffix)) {
                        allMatch = false;
                        break;
                    }
                }
                if (allMatch) {
                    return rule.replace;
                }
            }
        }
        return pattern.default;
    }

    /**
     * Convert an English phonetic word/token to Bengali
     */
    function convertWord(rawWord) {
        if (!rawWord) return '';
        var inputChars = [];
        for (var c = 0; c < rawWord.length; c++) {
            inputChars.push(conditionalLowercase(rawWord[c]));
        }
        var input = inputChars.join('');
        var prefix = ' ';
        var output = '';
        var i = 0;
        var len = input.length;

        while (i < len) {
            var sub = input.substring(i);
            var matched = null;
            for (var p = 0; p < AVRO_PATTERNS.length; p++) {
                var pat = AVRO_PATTERNS[p];
                if (sub.indexOf(pat.find) === 0) {
                    matched = pat;
                    break;
                }
            }

            if (matched) {
                var flen = matched.find.length;
                var suffix = (i + flen < len) ? input.charAt(i + flen) : ' ';
                output += getReplacement(matched, prefix, suffix);
                prefix = matched.find.charAt(flen - 1);
                i += flen;
            } else {
                prefix = input.charAt(i);
                output += prefix;
                i++;
            }
        }
        return output;
    }

    /**
     * Transliterate a full text string, honoring whitespace & punctuation
     */
    function convertText(text) {
        if (!text) return '';
        // Tokenize into words and delimiters
        var tokens = text.split(/([A-Za-z0-9`~@#\$%\^&\*\_\+\-=\[\]\{}\|;':",\.\/<>?]+)/);
        var result = '';
        for (var i = 0; i < tokens.length; i++) {
            var tok = tokens[i];
            if (!tok) continue;
            if (/^[A-Za-z]/.test(tok)) {
                var lower = tok.toLowerCase();
                if (AVRO_DICTIONARY[lower] && AVRO_DICTIONARY[lower].length > 0) {
                    result += AVRO_DICTIONARY[lower][0];
                } else {
                    result += convertWord(tok);
                }
            } else {
                result += convertWord(tok);
            }
        }
        return result;
    }

    /**
     * Return up to 5 suggested candidates for an active typing word
     */
    function getCandidates(word) {
        var cleaned = (word || '').trim();
        if (!cleaned) return [];
        var lower = cleaned.toLowerCase();
        var candidates = [];
        var seen = {};

        function add(cand) {
            if (!cand || seen[cand]) return;
            seen[cand] = true;
            candidates.push(cand);
        }

        // 1. Check curated dictionary first
        if (AVRO_DICTIONARY[lower]) {
            for (var i = 0; i < AVRO_DICTIONARY[lower].length; i++) {
                add(AVRO_DICTIONARY[lower][i]);
            }
        }

        // 2. Phonetic engine primary conversion
        var ruleBased = convertWord(cleaned);
        add(ruleBased);

        // 3. Fallback variations if fewer than 4 candidates
        if (candidates.length < 5) {
            // Capitalized or alternative vowel
            var alt1 = convertWord(cleaned.charAt(0).toUpperCase() + cleaned.slice(1));
            add(alt1);
        }
        if (candidates.length < 5) {
            // Sibilant variant: sh <-> s
            if (lower.indexOf('sh') !== -1) {
                add(convertWord(cleaned.replace(/sh/gi, 's')));
            } else if (lower.indexOf('s') !== -1) {
                add(convertWord(cleaned.replace(/s/gi, 'sh')));
            }
        }
        if (candidates.length < 5) {
            // Dental/Retroflex: d <-> D, t <-> T
            if (lower.indexOf('d') !== -1) {
                add(convertWord(cleaned.replace(/d/gi, 'D')));
            }
            if (lower.indexOf('t') !== -1) {
                add(convertWord(cleaned.replace(/t/gi, 'T')));
            }
        }

        // 4. Literal English word as last option
        add(cleaned);

        return candidates.slice(0, 5);
    }

    // Export module
    global.BongoAvro = {
        convertWord: convertWord,
        convertText: convertText,
        getCandidates: getCandidates,
        dictionary: AVRO_DICTIONARY
    };

})(typeof window !== 'undefined' ? window : this);
