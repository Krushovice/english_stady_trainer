import { apiRequest } from "./client";
import type { Title } from "./types";

export function getMyTitle(): Promise<Title> {
  return apiRequest<Title>("/titles/me");
}
