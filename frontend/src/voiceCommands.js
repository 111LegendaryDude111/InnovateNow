const INTENT_PHRASES = {
  greeting: [
    "привет",
    "здравствуй",
    "здравствуйте",
    "добрый день",
    "кто ты",
    "как тебя зовут",
    "представься",
    "hello",
    "hi",
    "hey",
    "who are you",
    "what is your name",
    "introduce yourself",
  ],
  datetime: [
    "сколько времени",
    "сколько сейчас времени",
    "который час",
    "текущее время",
    "какая дата",
    "какое сегодня число",
    "какой сегодня день",
    "дата",
    "время",
    "time",
    "date",
    "what time",
    "what is the date",
    "today",
    "day is it",
  ],
  joke: [
    "шутка",
    "пошути",
    "расскажи шутку",
    "расскажи анекдот",
    "рассмеши",
    "joke",
    "tell a joke",
    "make me laugh",
    "funny",
  ],
};

const RESPONSES = {
  ru: {
    greeting:
      "Привет! Я голосовой ассистент Task Learn. Могу назвать дату, время или рассказать короткую шутку.",
    joke: "Почему программисты любят темную тему? Потому что свет притягивает баги.",
    unknown: "Я пока понимаю приветствие, время или дату и просьбу пошутить.",
  },
  en: {
    greeting:
      "Hello! I am the Task Learn voice assistant. I can tell the date, time, or a short joke.",
    joke: "Why do programmers like dark mode? Because light attracts bugs.",
    unknown: "I can handle a greeting, date or time, and a simple joke request.",
  },
};

const WEEKDAYS = {
  ru: ["воскресенье", "понедельник", "вторник", "среда", "четверг", "пятница", "суббота"],
  en: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
};
const MONTHS = {
  ru: [
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
  ],
  en: [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ],
};

export function createVoiceAssistantResponse(commandText, options = {}) {
  const language = options.language === "en" ? "en" : "ru";
  const normalized = normalizeCommand(commandText);

  if (matchesIntent(normalized, INTENT_PHRASES.greeting)) {
    return { intent: "greeting", responseText: RESPONSES[language].greeting };
  }
  if (matchesIntent(normalized, INTENT_PHRASES.datetime)) {
    return {
      intent: "datetime",
      responseText: createDateTimeResponse(language, options.now ?? new Date(), options.timeZone),
    };
  }
  if (matchesIntent(normalized, INTENT_PHRASES.joke)) {
    return { intent: "joke", responseText: RESPONSES[language].joke };
  }

  return { intent: "unknown", responseText: RESPONSES[language].unknown };
}

function normalizeCommand(commandText) {
  return String(commandText ?? "")
    .toLocaleLowerCase()
    .replace(/[^\p{L}\p{N}\s]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function matchesIntent(command, phrases) {
  if (!command) return false;
  return phrases.some((phrase) => hasPhrase(command, phrase));
}

function hasPhrase(command, phrase) {
  return (
    command === phrase ||
    command.startsWith(`${phrase} `) ||
    command.endsWith(` ${phrase}`) ||
    command.includes(` ${phrase} `)
  );
}

function createDateTimeResponse(language, now, timeZone) {
  const parts = getDateTimeParts(now, timeZone);
  const time = `${parts.hour}:${parts.minute}`;

  if (language === "en") {
    return `It is ${time}, ${WEEKDAYS.en[parts.weekday]}, ${
      MONTHS.en[parts.month - 1]
    } ${parts.day}, ${parts.year}.`;
  }

  return `Сейчас ${time}, ${WEEKDAYS.ru[parts.weekday]}, ${parts.day} ${
    MONTHS.ru[parts.month - 1]
  } ${parts.year}.`;
}

function getDateTimeParts(now, timeZone) {
  const options = {
    weekday: "long",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  };
  if (timeZone) options.timeZone = timeZone;

  const parts = new Intl.DateTimeFormat("en-US", options).formatToParts(now);
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));

  return {
    year: Number(values.year),
    month: Number(values.month),
    day: Number(values.day),
    hour: values.hour === "24" ? "00" : values.hour,
    minute: values.minute,
    weekday: WEEKDAYS.en.indexOf(values.weekday),
  };
}
