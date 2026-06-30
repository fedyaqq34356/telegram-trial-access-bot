import type { Lang } from "@/i18n";

export interface ChatMsg { side: "in" | "out"; text: string; time: string }
export interface SeedReview {
  id: string;
  flag: string;
  countryKey: string;     
  age: number;
  date: string;
  results: { label: string; amount: string }[];
  messages: ChatMsg[];
}

export const reviewsI18n: Record<Lang, { countries: Record<string, string>; res: Record<string, string> }> = {
  ru: {
    countries: { ua: "Украины", pl: "Польши", cz: "Чехии", lt: "Литвы", kz: "Казахстана", de: "Германии" },
    res: { week: "Первая неделя", month: "Первый месяц", avg: "Средний доход" },
  },
  en: {
    countries: { ua: "Ukraine", pl: "Poland", cz: "Czechia", lt: "Lithuania", kz: "Kazakhstan", de: "Germany" },
    res: { week: "First week", month: "First month", avg: "Average income" },
  },
  ua: {
    countries: { ua: "України", pl: "Польщі", cz: "Чехії", lt: "Литви", kz: "Казахстану", de: "Німеччини" },
    res: { week: "Перший тиждень", month: "Перший місяць", avg: "Середній дохід" },
  },
};

export const REVIEWS: Record<Lang, SeedReview[]> = {
  ru: [
    { id: "ua", flag: "🇺🇦", countryKey: "ua", age: 22, date: "12 мая",
      results: [{ label: "week", amount: "$130" }, { label: "month", amount: "$820" }],
      messages: [
        { side: "in", text: "Привет! Хочу сказать огромное спасибо за помощь и поддержку на всех этапах 💜 Сегодня вывела свои первые $150 😍 Это только начало!", time: "20:15" },
        { side: "out", text: "Поздравляю! 🔥 Ты большая молодец!", time: "20:16" },
      ] },
    { id: "pl", flag: "🇵🇱", countryKey: "pl", age: 25, date: "25 мая",
      results: [{ label: "avg", amount: "$1200/мес" }],
      messages: [
        { side: "in", text: "Уже третий месяц работаю с вами и очень довольна результатом! ❤️ Свободный график позволяет совмещать с учёбой.", time: "18:42" },
        { side: "out", text: "Спасибо за отзыв! Рады, что тебе нравится 😊", time: "18:43" },
      ] },
    { id: "cz", flag: "🇨🇿", countryKey: "cz", age: 23, date: "30 мая",
      results: [{ label: "avg", amount: "$950/мес" }],
      messages: [
        { side: "in", text: "Английский у меня был на нуле, но благодаря встроенному переводчику всё получается отлично! Доход растёт с каждой неделей 📈", time: "21:11" },
        { side: "out", text: "Отличный результат! 🔥", time: "21:12" },
      ] },
    { id: "lt", flag: "🇱🇹", countryKey: "lt", age: 24, date: "18 мая",
      results: [{ label: "avg", amount: "$1000/мес" }],
      messages: [
        { side: "in", text: "Спасибо за обучение! Всё очень понятно и доступно объяснили. Первые дни было волнительно, а сейчас это моя любимая работа 💕", time: "17:22" },
        { side: "out", text: "Спасибо за тёплые слова! 🌸", time: "17:23" },
      ] },
    { id: "kz", flag: "🇰🇿", countryKey: "kz", age: 21, date: "10 мая",
      results: [{ label: "week", amount: "$120" }, { label: "month", amount: "$760" }],
      messages: [
        { side: "in", text: "Никогда не думала, что смогу зарабатывать онлайн столько! За первую неделю уже окупила новый телефон 😄 Спасибо вам!", time: "19:08" },
        { side: "out", text: "Круто! Продолжай в том же духе 🚀", time: "19:09" },
      ] },
    { id: "de", flag: "🇩🇪", countryKey: "de", age: 27, date: "28 мая",
      results: [{ label: "avg", amount: "$1500/мес" }],
      messages: [
        { side: "in", text: "Работаю каждый день по 3–4 часа и получаю стабильно высокий доход. Команда всегда на связи и помогает в любой ситуации!", time: "16:45" },
        { side: "out", text: "Спасибо за доверие! 💜", time: "16:46" },
      ] },
  ],
  en: [
    { id: "ua", flag: "🇺🇦", countryKey: "ua", age: 22, date: "May 12",
      results: [{ label: "week", amount: "$130" }, { label: "month", amount: "$820" }],
      messages: [
        { side: "in", text: "Hi! I just want to say a huge thank you for the help and support at every step 💜 Today I withdrew my first $150 😍 And this is only the beginning!", time: "20:15" },
        { side: "out", text: "Congrats! 🔥 You're doing amazing!", time: "20:16" },
      ] },
    { id: "pl", flag: "🇵🇱", countryKey: "pl", age: 25, date: "May 25",
      results: [{ label: "avg", amount: "$1200/mo" }],
      messages: [
        { side: "in", text: "It's my third month working with you and I'm so happy with the results! ❤️ The flexible schedule lets me combine it with my studies.", time: "18:42" },
        { side: "out", text: "Thanks for the review! Glad you enjoy it 😊", time: "18:43" },
      ] },
    { id: "cz", flag: "🇨🇿", countryKey: "cz", age: 23, date: "May 30",
      results: [{ label: "avg", amount: "$950/mo" }],
      messages: [
        { side: "in", text: "My English was zero, but thanks to the built-in translator everything works out great! My income grows every week 📈", time: "21:11" },
        { side: "out", text: "Excellent result! 🔥", time: "21:12" },
      ] },
    { id: "lt", flag: "🇱🇹", countryKey: "lt", age: 24, date: "May 18",
      results: [{ label: "avg", amount: "$1000/mo" }],
      messages: [
        { side: "in", text: "Thanks for the training! Everything was explained so clearly. The first days were nerve-wracking, now it's my favorite job 💕", time: "17:22" },
        { side: "out", text: "Thank you for the kind words! 🌸", time: "17:23" },
      ] },
    { id: "kz", flag: "🇰🇿", countryKey: "kz", age: 21, date: "May 10",
      results: [{ label: "week", amount: "$120" }, { label: "month", amount: "$760" }],
      messages: [
        { side: "in", text: "I never thought I could earn this much online! In the first week I already paid off a new phone 😄 Thank you!", time: "19:08" },
        { side: "out", text: "Awesome! Keep it up 🚀", time: "19:09" },
      ] },
    { id: "de", flag: "🇩🇪", countryKey: "de", age: 27, date: "May 28",
      results: [{ label: "avg", amount: "$1500/mo" }],
      messages: [
        { side: "in", text: "I work 3–4 hours a day and get a steady high income. The team is always in touch and helps in any situation!", time: "16:45" },
        { side: "out", text: "Thank you for trusting us! 💜", time: "16:46" },
      ] },
  ],
  ua: [
    { id: "ua", flag: "🇺🇦", countryKey: "ua", age: 22, date: "12 травня",
      results: [{ label: "week", amount: "$130" }, { label: "month", amount: "$820" }],
      messages: [
        { side: "in", text: "Привіт! Хочу сказати величезне дякую за допомогу та підтримку на всіх етапах 💜 Сьогодні вивела свої перші $150 😍 Це лише початок!", time: "20:15" },
        { side: "out", text: "Вітаю! 🔥 Ти велика молодець!", time: "20:16" },
      ] },
    { id: "pl", flag: "🇵🇱", countryKey: "pl", age: 25, date: "25 травня",
      results: [{ label: "avg", amount: "$1200/міс" }],
      messages: [
        { side: "in", text: "Уже третій місяць працюю з вами і дуже задоволена результатом! ❤️ Вільний графік дозволяє поєднувати з навчанням.", time: "18:42" },
        { side: "out", text: "Дякуємо за відгук! Раді, що тобі подобається 😊", time: "18:43" },
      ] },
    { id: "cz", flag: "🇨🇿", countryKey: "cz", age: 23, date: "30 травня",
      results: [{ label: "avg", amount: "$950/міс" }],
      messages: [
        { side: "in", text: "Англійська у мене була на нулі, але завдяки вбудованому перекладачу все виходить чудово! Дохід зростає щотижня 📈", time: "21:11" },
        { side: "out", text: "Чудовий результат! 🔥", time: "21:12" },
      ] },
    { id: "lt", flag: "🇱🇹", countryKey: "lt", age: 24, date: "18 травня",
      results: [{ label: "avg", amount: "$1000/міс" }],
      messages: [
        { side: "in", text: "Дякую за навчання! Все дуже зрозуміло й доступно пояснили. Перші дні було хвилююче, а зараз це моя улюблена робота 💕", time: "17:22" },
        { side: "out", text: "Дякуємо за теплі слова! 🌸", time: "17:23" },
      ] },
    { id: "kz", flag: "🇰🇿", countryKey: "kz", age: 21, date: "10 травня",
      results: [{ label: "week", amount: "$120" }, { label: "month", amount: "$760" }],
      messages: [
        { side: "in", text: "Ніколи не думала, що зможу заробляти онлайн стільки! За перший тиждень уже окупила новий телефон 😄 Дякую вам!", time: "19:08" },
        { side: "out", text: "Круто! Продовжуй у тому ж дусі 🚀", time: "19:09" },
      ] },
    { id: "de", flag: "🇩🇪", countryKey: "de", age: 27, date: "28 травня",
      results: [{ label: "avg", amount: "$1500/міс" }],
      messages: [
        { side: "in", text: "Працюю щодня по 3–4 години й отримую стабільно високий дохід. Команда завжди на зв'язку та допомагає в будь-якій ситуації!", time: "16:45" },
        { side: "out", text: "Дякуємо за довіру! 💜", time: "16:46" },
      ] },
  ],
};
