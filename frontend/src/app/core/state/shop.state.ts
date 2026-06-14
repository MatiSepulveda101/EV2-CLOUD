import { Injectable, OnDestroy, signal } from '@angular/core';
import { firstValueFrom, Subscription } from 'rxjs';
import { ApiHttpError } from '../api/api-client.service';
import { AuthService } from '../services/auth.service';
import { EcommerceService } from '../services/ecommerce.service';
import {
  CarritoLeer,
  OrdenLeer,
  Producto,
  UsuarioCrear,
  UsuarioReenviarCodigo,
  UsuarioVerificarCodigo
} from '../models/ecommerce.models';
import { SessionStateService } from './session.state';

@Injectable({
  providedIn: 'root'
})
export class ShopStateService implements OnDestroy {
  readonly products = signal<Producto[]>([]);
  readonly cart = signal<CarritoLeer | null>(null);
  readonly selectedOrder = signal<OrdenLeer | null>(null);

  readonly loadingProducts = signal(false);
  readonly loadingCart = signal(false);
  readonly authSubmitting = signal(false);
  readonly actionLoading = signal(false);
  readonly checkoutLoading = signal(false);
  readonly orderSyncLoading = signal(false);

  readonly authError = signal('');
  readonly productsError = signal('');
  readonly cartError = signal('');
  readonly checkoutError = signal('');
  readonly orderSyncError = signal('');
  readonly successMessage = signal('');

  readonly lastOrderId = signal<number | string | null>(null);

  private orderSubscription: Subscription | null = null;

  constructor(
    private readonly authService: AuthService,
    private readonly ecommerceService: EcommerceService,
    readonly sessionState: SessionStateService
  ) {}

  ngOnDestroy(): void {
    this.stopOrderSync();
  }

  async register(payload: UsuarioCrear): Promise<void> {
    this.authSubmitting.set(true);
    this.authError.set('');
    this.successMessage.set('');

    try {
      await firstValueFrom(this.authService.register(payload));
      this.successMessage.set('Registro exitoso. Ingresa el codigo enviado para activar tu cuenta.');

    } catch (error) {
      this.authError.set(this.getErrorMessage(error));
    } finally {
      this.authSubmitting.set(false);
    }
  }

  async verifyAccount(payload: UsuarioVerificarCodigo): Promise<void> {
    this.authSubmitting.set(true);
    this.authError.set('');
    this.successMessage.set('');

    try {
      await firstValueFrom(this.authService.verifyAccount(payload));
      this.successMessage.set('Cuenta validada correctamente. Ahora puedes iniciar sesion.');
    } catch (error) {
      this.authError.set(this.getErrorMessage(error));
    } finally {
      this.authSubmitting.set(false);
    }
  }

  async resendCode(payload: UsuarioReenviarCodigo): Promise<void> {
    this.authSubmitting.set(true);
    this.authError.set('');
    this.successMessage.set('');

    try {
      await firstValueFrom(this.authService.resendCode(payload));
      this.successMessage.set('Codigo reenviado correctamente.');
    } catch (error) {
      this.authError.set(this.getErrorMessage(error));
    } finally {
      this.authSubmitting.set(false);
    }
  }

  async login(email: string, password: string): Promise<void> {
    this.authSubmitting.set(true);
    this.authError.set('');
    this.successMessage.set('');

    try {
      await firstValueFrom(this.authService.login(email, password));
      this.successMessage.set('Sesion iniciada correctamente.');
      await this.loadCart();
    } catch (error) {
      this.authError.set(this.getErrorMessage(error));
    } finally {
      this.authSubmitting.set(false);
    }
  }

  logout(): void {
    this.authService.logout();
    this.cart.set(null);
    this.selectedOrder.set(null);
    this.lastOrderId.set(null);
    this.stopOrderSync();
  }

  async loadProducts(): Promise<void> {
    this.loadingProducts.set(true);
    this.productsError.set('');

    try {
      const products = await firstValueFrom(this.ecommerceService.getProducts());
      this.products.set(products);
    } catch (error) {
      this.productsError.set(this.getErrorMessage(error));
    } finally {
      this.loadingProducts.set(false);
    }
  }

  async loadCart(): Promise<void> {
    if (!this.sessionState.isAuthenticated()) {
      return;
    }

    this.loadingCart.set(true);
    this.cartError.set('');

    try {
      const cart = await firstValueFrom(this.ecommerceService.getCart());
      this.cart.set(cart);
    } catch (error) {
      this.cartError.set(this.getErrorMessage(error));
    } finally {
      this.loadingCart.set(false);
    }
  }

  async addCartItem(productId: number): Promise<void> {
    await this.runCartAction(async () => {
      const updatedCart = await firstValueFrom(
        this.ecommerceService.addCartItem({
          product_id: productId,
          quantity: 1
        })
      );
      this.cart.set(updatedCart);
    });
  }

  async updateCartItem(itemId: number, quantity: number): Promise<void> {
    await this.runCartAction(async () => {
      const updatedCart = await firstValueFrom(
        this.ecommerceService.updateCartItem(itemId, {
          quantity
        })
      );
      this.cart.set(updatedCart);
    });
  }

  async removeCartItem(itemId: number): Promise<void> {
    await this.runCartAction(async () => {
      const updatedCart = await firstValueFrom(this.ecommerceService.removeCartItem(itemId));

      if (updatedCart) {
        this.cart.set(updatedCart);
        return;
      }

      await this.loadCart();
    });
  }

  async createCheckout(): Promise<void> {
    this.checkoutLoading.set(true);
    this.checkoutError.set('');

    try {
      const response = await firstValueFrom(this.ecommerceService.createCheckout());
      this.lastOrderId.set(response.order_id);

      if (response.payment_url) {
        window.location.href = response.payment_url;
        return;
      }

      this.checkoutError.set('No se recibio una URL de pago valida.');
    } catch (error) {
      this.checkoutError.set(this.getErrorMessage(error));
    } finally {
      this.checkoutLoading.set(false);
    }
  }

  startOrderSync(orderId: number | string): void {
    this.stopOrderSync();
    this.lastOrderId.set(orderId);
    this.orderSyncError.set('');
    this.orderSyncLoading.set(true);

    this.orderSubscription = this.ecommerceService.syncOrderUntilFinal(orderId).subscribe({
      next: (order) => {
        this.selectedOrder.set(order);
      },
      error: (error) => {
        this.orderSyncError.set(this.getErrorMessage(error));
        this.orderSyncLoading.set(false);
      },
      complete: () => {
        this.orderSyncLoading.set(false);
      }
    });
  }

  retryOrderSync(): void {
    const orderId = this.lastOrderId();
    if (!orderId) {
      return;
    }

    this.startOrderSync(orderId);
  }

  private stopOrderSync(): void {
    this.orderSubscription?.unsubscribe();
    this.orderSubscription = null;
  }

  private async runCartAction(action: () => Promise<void>): Promise<void> {
    if (!this.sessionState.isAuthenticated()) {
      this.cartError.set('Debes iniciar sesion para modificar el carrito.');
      return;
    }

    this.actionLoading.set(true);
    this.cartError.set('');

    try {
      await action();
    } catch (error) {
      this.cartError.set(this.getErrorMessage(error));
    } finally {
      this.actionLoading.set(false);
    }
  }

  private getErrorMessage(error: unknown): string {
    if (error instanceof ApiHttpError) {
      return error.detail;
    }

    return 'Operacion no disponible temporalmente.';
  }
}
