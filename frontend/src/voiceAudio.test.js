import assert from "node:assert/strict";
import test from "node:test";

import { buildAudioDataUrl } from "./voiceAudio.js";

test("builds audio data URL from server TTS response", () => {
  assert.equal(buildAudioDataUrl("YWJj", "audio/wav"), "data:audio/wav;base64,YWJj");
});

test("rejects missing server TTS audio", () => {
  assert.throws(() => buildAudioDataUrl("", "audio/wav"), /TTS audio/);
});
