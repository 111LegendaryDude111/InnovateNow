import assert from "node:assert/strict";
import test from "node:test";

import { describeRecognitionError } from "./voiceSpeech.js";

test("explains browser speech recognition network failures", () => {
  assert.equal(
    describeRecognitionError("network"),
    "Browser speech recognition service is unavailable. Check internet access and browser speech-service blocking, or switch this MVP to cloud/local STT for reliable recognition.",
  );
});

test("keeps microphone permission denial explicit", () => {
  assert.equal(describeRecognitionError("not-allowed"), "Microphone permission denied.");
});
