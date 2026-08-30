export type GuestChatRequest = {
  question: string;
};

export type GuestChatResponse = {
  answer: string;
};

export type GuestChatErrorBody = {
  detail?: string;
};
