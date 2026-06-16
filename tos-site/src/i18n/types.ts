export interface Item { title: string; text: string }
export interface Step { title: string; text: string }
export interface QA { q: string; a: string }

export interface Dict {
  langName: string;
  nav: {
    home: string; about: string; start: string; training: string;
    benefits: string; reviews: string; faq: string; contacts: string; apply: string; download: string;
  };
  download: {
    title: string; lead: string; androidFemale: string; androidMale: string;
    iphoneFemale: string; iphoneMale: string; female: string; male: string;
    btnDownload: string; btnOpen: string; soon: string;
  };
  instruction: {
    eyebrow: string; title: string; lead: string; importantTitle: string; linksTitle: string;
    dlTitle: string; dlSub: string; tgTitle: string; tgSub: string; waTitle: string; waSub: string; empty: string;
  };
  common: {
    apply: string; learnMore: string; next: string; back: string; send: string;
    online247: string; brand: string; tagline: string; menu: string; partner: string;
  };
  home: {
    heroTitle: string; heroSubtitle: string;
    statsEarn: string; statsLabel: string;
    stats: { big: string; small: string }[];
    incomeTitle: string; income: Item[];
    whyTitle: string; why: string[];
    howTitle: string; how: string[];
    ctaTitle: string; ctaText: string;
    visualPerMinute: string; visualPayouts: string; visualPayoutDays: string; visualGift: string;
  };
  about: {
    title: string; lead: string;
    incomeTitle: string; income: Item[];
    needTitle: string; need: string[];
  };
  start: {
    title: string; lead: string;
    stepsTitle: string; steps: Step[];
    testWeekTitle: string; testWeekText: string;
    successTitle: string; successCond: string[]; successResult: string[];
    minimalTitle: string; minimalCond: string[]; minimalResult: string[];
    riskTitle: string; riskText: string; riskNotes: string[];
    withdrawTitle: string; withdrawText: string; withdrawCond: string[]; withdrawDenied: string;
    coefTitle: string; coefText: string[];
    whereTitle: string; where: string[];
  };
  benefits: { title: string; lead: string; items: Item[] };
  reviews: { title: string; subtitle: string; verified: string; cardFrom: string; empty: string; lastSeen: string; safetyNote: string };
  faq: { title: string; lead: string; items: QA[] };
  contacts: {
    title: string; lead: string; writeTg: string; writeWa: string; telegram: string; instagram: string; tiktok: string; whatsapp: string; online247: string;
  };
  training: {
    title: string; lead: string; password: string; appId: string; login: string;
    wrong: string; note: string; lessonsTitle: string; locked: string; logout: string;
    menuCheck: string; menuCheckDesc: string; menuCheckBtn: string;
    menuTrain: string; menuTrainDesc: string; menuTrainBtn: string; back: string;
    checkTitle: string; checkSub: string; checkIdLabel: string; checkBtn: string; checkRefresh: string;
    coefLabel: string; detailsTitle: string; dProfile: string; dMonth: string; dIncome: string;
    dLevel: string; dAgency: string; dRank: string; recTitle: string;
    recSafe: string; recWarning: string; recDanger: string;
    statusSafe: string; statusWarning: string; statusDanger: string; coins: string; limitUpTo: string;
    botId: string; rankUnit: string; allGood: string;
    riskTitle: string; riskReason: string; riskProfile: string; riskMonthly: string;
    riskLimit: string; riskYourCoef: string; riskYourCoef30: string; punishTitle: string; riskRec: string;
    gradeDesc: Record<string, string>; punishment: Record<string, string>;
    trainTitle: string; trainSub: string; recommended: string; emptyLessons: string; startLessons: string;
    quickTitle: string; quickBadge: string; quickDesc: string; quickBtn: string;
    fullTitle: string; fullBadge: string; fullDesc: string; fullBtn: string;
    finish: string; markComplete: string; completedMark: string;
    quickIntroSub: string; startBtn: string; quickDuration: string; nextStep: string;
    checklistLabel: string; calloutTip: string; calloutImportant: string; calloutForbidden: string; calloutExample: string;
  };
  apply: {
    title: string; lead: string;
    step: string; of: string;
    s1Title: string; age: string; country: string; contactTg: string; contactWa: string; email: string; contactHint: string;
    chooseContact: string; optional: string;
    s2Title: string; expQ: string; expYes: string; expNo: string; expWhich: string;
    noExpText: string; seeExample: string; exampleTitle: string; exampleSoon: string;
    s3Title: string; timeQ: string; timeHint: string; timePlaceholder: string;
    s4Title: string; photoReqTitle: string; photoReqs: string[]; aiWarning: string; addPhoto: string; photoCount: string;
    s5Title: string; confirmHint: string; experience: string; time: string; photos: string; yes: string; no: string;
    submit: string; sending: string;
    successTitle: string; successText: string; another: string;
    errAge: string; errCountry: string; errContact: string; errPhotos: string;
  };
}
