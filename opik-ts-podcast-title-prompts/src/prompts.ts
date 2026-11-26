export const PROMPT_NAME = "episode-title-writer";

export interface PromptSpec {
  text: string;
  changeDescription: string;
}

export const V1: PromptSpec = {
  text: "You write titles for podcast episodes. Read the episode notes and write a catchy, exciting title that makes people want to listen.",
  changeDescription: "First draft: generic catchy-title instruction",
};

export const V2: PromptSpec = {
  text: `You write titles for episodes of a podcast network. Read the episode notes and reply with one title and nothing else.

Rules:
- Eight words or fewer.
- One plain phrase: no colon and no subtitle.
- No hype words (ultimate, secrets, unlock, shocking, game-changing, "you won't believe").
- No emoji, hashtags, or quotation marks.
- If the notes name a guest, the title must include the guest's full name.`,
  changeDescription:
    "Add concrete rules: 8 words max, no subtitle, no hype words, no emoji or quotes, guest named",
};

// Plain-language assertions that the Opik test suite hands to an LLM judge.
export const GLOBAL_ASSERTIONS = [
  "The title is eight words or fewer",
  "The title does not contain a colon character (:)",
  "The title uses no hype or clickbait wording (for example ultimate, secrets, unlock, shocking, game-changing, you won't believe)",
  "The title contains no emoji, hashtag, or quotation marks",
];

export const guestAssertion = (guest: string) =>
  `The title includes the guest's full name, "${guest}"`;
