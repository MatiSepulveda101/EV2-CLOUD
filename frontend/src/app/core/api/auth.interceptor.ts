import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { SessionStateService } from '../state/session.state';

const AUTH_STORAGE_KEY = 'session_access_token';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const sessionState = inject(SessionStateService);

  const isPublicRoute =
    req.url.includes('/auth/login') ||
    req.url.includes('/auth/register') ||
    req.url.includes('/products');

  const token = localStorage.getItem(AUTH_STORAGE_KEY);
  const requestToSend = !isPublicRoute && token
    ? req.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`
        }
      })
    : req;

  return next(requestToSend).pipe(
    catchError((error) => {
      if (error?.status === 401 && !isPublicRoute) {
        sessionState.clearSession();
      }

      return throwError(() => error);
    })
  );
};
