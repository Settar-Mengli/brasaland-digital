/**
 * Wire types for the knowledge Q&A API (`POST /knowledge/query`).
 */
export type KnowledgeQueryRequest = {
  question: string;
};

export type KnowledgeQueryResponse = {
  answer: string;
};
