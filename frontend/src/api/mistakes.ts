import { apiRequest } from "./client";
import type { MistakeStatus, UserMistake } from "./types";

export function listMistakes(status?: MistakeStatus): Promise<UserMistake[]> {
  return apiRequest<UserMistake[]>(status ? `/mistakes?status=${status}` : "/mistakes");
}
