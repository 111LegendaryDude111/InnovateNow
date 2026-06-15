import assert from "node:assert/strict";
import test from "node:test";

import { selectSupportedAudioMimeType } from "./voiceRecording.js";

test("selects the first supported audio MIME type", () => {
  const selected = selectSupportedAudioMimeType((mimeType) => mimeType === "audio/webm");

  assert.equal(selected, "audio/webm");
});

test("returns empty MIME type when browser supports no candidate", () => {
  const selected = selectSupportedAudioMimeType(() => false);

  assert.equal(selected, "");
});
