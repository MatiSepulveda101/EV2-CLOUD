import { Injectable } from '@angular/core';
import { Observable, catchError, map, throwError, tap } from 'rxjs';
import { ApiClientService, ApiHttpError } from '../api/api-client.service';
import { Token, UsuarioCrear, UsuarioLeer } from '../models/ecommerce.models';
import { SessionStateService } from '../state/session.state';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  constructor(
    private readonly apiClient: ApiClientService,
    private readonly sessionState: SessionStateService
  ) {}

  register(payload: UsuarioCrear): Observable<UsuarioLeer> {
    return this.apiClient
      .post<UsuarioLeer | Record<string, unknown>>('/auth/register', payload)
      .pipe(map((response) => this.normalizeUser(response)));
  }

  login(email: string, password: string): Observable<Token> {
    return this.apiClient
      .post<Token | Record<string, unknown>>('/auth/login', {
        email,
        password
      })
      .pipe(
        catchError((error) => {
          if (
            error instanceof ApiHttpError &&
            (error.status === 400 || error.status === 401 || error.status === 422)
          ) {
            return this.apiClient.postForm<Token | Record<string, unknown>>('/auth/login', {
              username: email,
              password
            });
          }

          return throwError(() => error);
        }),
        map((response) => this.normalizeToken(response)),
        tap((token) => this.sessionState.setToken(token.access_token))
      );
  }

  logout(): void {
    this.sessionState.clearSession();
  }

  private normalizeToken(payload: Token | Record<string, unknown>): Token {
    const tokenPayload = payload as Record<string, unknown>;
    const accessToken = String(
      tokenPayload['access_token'] ?? tokenPayload['token'] ?? tokenPayload['accessToken'] ?? ''
    );
    const tokenType = String(tokenPayload['token_type'] ?? tokenPayload['tokenType'] ?? 'bearer');

    return {
      access_token: accessToken,
      token_type: tokenType
    };
  }

  private normalizeUser(payload: UsuarioLeer | Record<string, unknown>): UsuarioLeer {
    const userPayload = payload as Record<string, unknown>;

    return {
      id: Number(userPayload['id'] ?? userPayload['user_id'] ?? 0),
      email: String(userPayload['email'] ?? ''),
      full_name: this.asOptionalString(userPayload['full_name'] ?? userPayload['name']),
      is_active: this.asOptionalBoolean(userPayload['is_active']),
      created_at: this.asOptionalString(userPayload['created_at'])
    };
  }

  private asOptionalString(value: unknown): string | undefined {
    return typeof value === 'string' && value.trim() ? value : undefined;
  }

  private asOptionalBoolean(value: unknown): boolean | undefined {
    return typeof value === 'boolean' ? value : undefined;
  }
}
