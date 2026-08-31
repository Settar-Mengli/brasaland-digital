export type GuestChatRequest = {
  question: string;
  turnstileToken?: string;
};

export type GuestChatResponse = {
  answer: string;
};

export type GuestChatErrorBody = {
  detail?: string;
};
