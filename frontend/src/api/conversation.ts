import { apiRequest } from "./client";
import type { ConversationMessage, ConversationSession } from "./types";

export function startConversation(topic?: string): Promise<ConversationSession> {
  return apiRequest<ConversationSession>("/conversation/sessions", {
    method: "POST",
    body: { topic: topic || undefined },
  });
}

export function getConversation(sessionId: string): Promise<ConversationSession> {
  return apiRequest<ConversationSession>(`/conversation/sessions/${sessionId}`);
}

export function sendConversationMessage(
  sessionId: string,
  text: string,
): Promise<ConversationMessage> {
  return apiRequest<ConversationMessage>(`/conversation/sessions/${sessionId}/messages`, {
    method: "POST",
    body: { text },
  });
}

export function endConversation(sessionId: string): Promise<ConversationSession> {
  return apiRequest<ConversationSession>(`/conversation/sessions/${sessionId}/end`, {
    method: "POST",
  });
}
