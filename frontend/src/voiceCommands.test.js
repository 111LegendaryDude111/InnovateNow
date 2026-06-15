import assert from "node:assert/strict";
import test from "node:test";

import { createVoiceAssistantResponse } from "./voiceCommands.js";

const FIXED_NOW = new Date("2026-06-15T10:05:00.000Z");
const UTC_OPTIONS = { now: FIXED_NOW, timeZone: "UTC" };

test("recognizes Russian greeting and self-introduction", () => {
  const result = createVoiceAssistantResponse("  Привет, кто ты?  ", {
    language: "ru",
  });

  assert.equal(result.intent, "greeting");
  assert.equal(
    result.responseText,
    "Привет! Я голосовой ассистент Task Learn. Могу назвать дату, время или рассказать короткую шутку.",
  );
});

test("recognizes English greeting and self-introduction", () => {
  const result = createVoiceAssistantResponse("Hello, who are you?", {
    language: "en",
  });

  assert.equal(result.intent, "greeting");
  assert.equal(
    result.responseText,
    "Hello! I am the Task Learn voice assistant. I can tell the date, time, or a short joke.",
  );
});

test("returns stable Russian date and time", () => {
  const result = createVoiceAssistantResponse("Сколько сейчас времени?", {
    language: "ru",
    ...UTC_OPTIONS,
  });

  assert.deepEqual(result, {
    intent: "datetime",
    responseText: "Сейчас 10:05, понедельник, 15 июня 2026.",
  });
});

test("returns stable English date and time", () => {
  const result = createVoiceAssistantResponse("WHAT TIME IS IT?", {
    language: "en",
    ...UTC_OPTIONS,
  });

  assert.deepEqual(result, {
    intent: "datetime",
    responseText: "It is 10:05, Monday, June 15, 2026.",
  });
});

test("recognizes Russian joke request", () => {
  const result = createVoiceAssistantResponse("Расскажи шутку!", {
    language: "ru",
  });

  assert.equal(result.intent, "joke");
  assert.equal(
    result.responseText,
    "Почему программисты любят темную тему? Потому что свет притягивает баги.",
  );
});

test("normalizes English punctuation and case for joke request", () => {
  const result = createVoiceAssistantResponse("TELL... A JOKE!!!", {
    language: "en",
  });

  assert.equal(result.intent, "joke");
  assert.equal(result.responseText, "Why do programmers like dark mode? Because light attracts bugs.");
});

test("returns clarification for unknown command", () => {
  const result = createVoiceAssistantResponse("open settings", {
    language: "en",
  });

  assert.deepEqual(result, {
    intent: "unknown",
    responseText: "I can handle a greeting, date or time, and a simple joke request.",
  });
});

test("returns clarification for empty input", () => {
  const result = createVoiceAssistantResponse("   ", {
    language: "ru",
  });

  assert.deepEqual(result, {
    intent: "unknown",
    responseText: "Я пока понимаю приветствие, время или дату и просьбу пошутить.",
  });
});
