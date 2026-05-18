import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { Observable, catchError, throwError } from 'rxjs';

const AUTH_STORAGE_KEY = 'session_access_token';

export class ApiHttpError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
    public readonly payload?: unknown
  ) {
    super(detail);
    this.name = 'ApiHttpError';
  }
}

@Injectable({
  providedIn: 'root'
})
export class ApiClientService {

  readonly baseUrl = 'http://ev2-alb-873341758.us-east-1.elb.amazonaws.com/api';

  constructor(private readonly http: HttpClient) {}

  get<T>(path: string): Observable<T> {
    return this.http
      .get<T>(this.buildUrl(path), {
        headers: this.getAuthHeaders()
      })
      .pipe(catchError((error) => this.handleError(error)));
  }

  post<T>(path: string, body?: unknown): Observable<T> {
    return this.http
      .post<T>(this.buildUrl(path), body, {
        headers: this.getAuthHeaders()
      })
      .pipe(catchError((error) => this.handleError(error)));
  }

  postForm<T>(path: string, form: Record<string, string>): Observable<T> {
    const formBody = new URLSearchParams(form).toString();

    return this.http
      .post<T>(this.buildUrl(path), formBody, {
        headers: this.getAuthHeaders(new HttpHeaders({
          'Content-Type': 'application/x-www-form-urlencoded'
        }))
      })
      .pipe(catchError((error) => this.handleError(error)));
  }

  patch<T>(path: string, body: unknown): Observable<T> {
    return this.http
      .patch<T>(this.buildUrl(path), body, {
        headers: this.getAuthHeaders()
      })
      .pipe(catchError((error) => this.handleError(error)));
  }

  delete<T>(path: string): Observable<T> {
    return this.http
      .delete<T>(this.buildUrl(path), {
        headers: this.getAuthHeaders()
      })
      .pipe(catchError((error) => this.handleError(error)));
  }

  private buildUrl(path: string): string {
    return `${this.baseUrl}${path.startsWith('/') ? path : `/${path}`}`;
  }

  private getAuthHeaders(headers = new HttpHeaders()): HttpHeaders {
    const token = localStorage.getItem(AUTH_STORAGE_KEY);
    return token ? headers.set('Authorization', `Bearer ${token}`) : headers;
  }

  private handleError(error: unknown): Observable<never> {

    if (!(error instanceof HttpErrorResponse)) {
      return throwError(
        () => new ApiHttpError(0, 'Error inesperado de conexion.')
      );
    }

    const statusMessage = this.getMessageByStatus(error.status);
    const detailMessage = this.extractDetail(error.error);
    const finalMessage = detailMessage || statusMessage;

    return throwError(
      () => new ApiHttpError(error.status, finalMessage, error.error)
    );
  }

  private getMessageByStatus(status: number): string {

    switch (status) {

      case 400:
        return 'Solicitud invalida.';

      case 401:
        return 'No autorizado. Inicia sesion nuevamente.';

      case 404:
        return 'Recurso no encontrado.';

      case 409:
        return 'Conflicto de datos en la operacion.';

      case 422:
        return 'Datos de entrada no validos.';

      case 503:
        return 'Servicio no disponible temporalmente.';

      default:
        return 'No fue posible completar la solicitud.';
    }
  }

  private extractDetail(errorBody: unknown): string {

    if (!errorBody) {
      return '';
    }

    if (typeof errorBody === 'string') {
      return errorBody;
    }

    if (typeof errorBody === 'object') {

      const body = errorBody as Record<string, unknown>;
      const detail = body['detail'];

      if (typeof detail === 'string') {
        return detail;
      }

      if (Array.isArray(detail)) {

        return detail
          .map((entry) => {

            if (typeof entry === 'string') {
              return entry;
            }

            if (entry && typeof entry === 'object') {

              const value = (entry as Record<string, unknown>)['msg'];

              if (typeof value === 'string') {
                return value;
              }
            }

            return 'Error de validacion';
          })
          .join(' | ');
      }
    }

    return '';
  }
}
