import { apiRequest } from "./client";
import type { User } from "./types";

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export function register(email: string, password: string): Promise<User> {
  return apiRequest<User>("/auth/register", {
    method: "POST",
    body: { email, password },
    auth: false,
  });
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/auth/login", {
    method: "POST",
    body: { email, password },
    auth: false,
  });
}

export function me(): Promise<User> {
  return apiRequest<User>("/auth/me");
}
