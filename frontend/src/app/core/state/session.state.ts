import { Injectable, computed, signal } from '@angular/core';

const AUTH_STORAGE_KEY = 'session_access_token';

@Injectable({
  providedIn: 'root'
})
export class SessionStateService {
  readonly token = signal<string | null>(localStorage.getItem(AUTH_STORAGE_KEY));
  readonly isAuthenticated = computed(() => !!this.token());

  setToken(token: string): void {
    this.token.set(token);
    localStorage.setItem(AUTH_STORAGE_KEY, token);
  }

  clearSession(): void {
    this.token.set(null);
    localStorage.removeItem(AUTH_STORAGE_KEY);
  }
}
