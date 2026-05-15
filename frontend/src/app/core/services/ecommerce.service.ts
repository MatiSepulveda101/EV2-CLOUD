import { Injectable } from '@angular/core';
import { Observable, catchError, map, switchMap, takeWhile, throwError, timer } from 'rxjs';
import { ApiClientService } from '../api/api-client.service';
import {
  CarritoLeer,
  ItemCarritoActualizar,
  ItemCarritoCrear,
  ItemCarritoLeer,
  OrdenLeer,
  Producto,
  RespuestaCheckout
} from '../models/ecommerce.models';

const FINAL_ORDER_STATUSES = new Set([
  'PAID',
  'REJECTED',
  'CANCELLED'
]);

@Injectable({
  providedIn: 'root'
})
export class EcommerceService {
  constructor(private readonly apiClient: ApiClientService) {}

  getProducts(): Observable<Producto[]> {
    return this.apiClient.get<unknown>('/products').pipe(map((response) => this.normalizeProducts(response)));
  }

  getProductById(productId: number): Observable<Producto> {
    return this.apiClient
      .get<unknown>(`/products/${productId}`)
      .pipe(map((response) => this.normalizeProduct(response)));
  }

  getCart(): Observable<CarritoLeer> {
    return this.apiClient.get<unknown>('/cart').pipe(map((response) => this.normalizeCart(response)));
  }

  addCartItem(payload: ItemCarritoCrear): Observable<CarritoLeer> {
    return this.apiClient
      .post<unknown>('/cart/items', payload)
      .pipe(map((response) => this.normalizeCart(response)));
  }

  updateCartItem(itemId: number, payload: ItemCarritoActualizar): Observable<CarritoLeer> {
    return this.apiClient
      .patch<unknown>(`/cart/items/${itemId}`, payload)
      .pipe(map((response) => this.normalizeCart(response)));
  }

  removeCartItem(itemId: number): Observable<CarritoLeer | null> {
    return this.apiClient
      .delete<unknown>(`/cart/items/${itemId}`)
      .pipe(map((response) => (response ? this.normalizeCart(response) : null)));
  }

  createCheckout(): Observable<RespuestaCheckout> {
    return this.apiClient
      .post<unknown>('/checkout', {})
      .pipe(map((response) => this.normalizeCheckoutResponse(response)));
  }

  getOrder(orderId: number | string): Observable<OrdenLeer> {
    return this.apiClient
      .get<unknown>(`/orders/${orderId}`)
      .pipe(map((response) => this.normalizeOrder(response)));
  }

  syncOrderUntilFinal(orderId: number | string): Observable<OrdenLeer> {
    return timer(0, 3000).pipe(
      switchMap(() => this.getOrder(orderId)),
      takeWhile((order) => !this.isFinalStatus(order.status), true),
      catchError((error) => throwError(() => error))
    );
  }

  private isFinalStatus(status: string): boolean {
    return FINAL_ORDER_STATUSES.has(status.trim().toUpperCase());
  }

  private normalizeProducts(payload: unknown): Producto[] {
    const container = payload as Record<string, unknown>;
    const productList = Array.isArray(payload)
      ? payload
      : Array.isArray(container['products'])
        ? container['products']
        : Array.isArray(container['items'])
          ? container['items']
          : [];

    return productList.map((item) => this.normalizeProduct(item));
  }

  private normalizeProduct(payload: unknown): Producto {
    const product = payload as Record<string, unknown>;

    return {
      id: Number(product['id'] ?? product['product_id'] ?? 0),
      name: String(product['name'] ?? product['title'] ?? product['product_name'] ?? 'Producto'),
      description: this.asOptionalString(product['description'] ?? product['detail']),
      price: Number(product['price'] ?? product['unit_price'] ?? product['amount'] ?? 0),
      image_url: this.asOptionalString(product['image_url'] ?? product['image'] ?? product['imageUrl']),
      category: this.asOptionalString(product['category']),
      stock: this.asOptionalNumber(product['stock'])
    };
  }

  private normalizeCart(payload: unknown): CarritoLeer {
    const cart = payload as Record<string, unknown>;
    const rawItems = Array.isArray(cart['items']) ? cart['items'] : [];
    const items = rawItems.map((item) => this.normalizeCartItem(item));
    const subtotal = Number(
      cart['subtotal'] ?? cart['total'] ?? items.reduce((acc, item) => acc + (item.subtotal ?? 0), 0)
    );

    return {
      id: Number(cart['id'] ?? cart['cart_id'] ?? 0),
      user_id: this.asOptionalNumber(cart['user_id']),
      items,
      total_items: Number(
        cart['total_items'] ?? cart['items_count'] ?? items.reduce((acc, item) => acc + item.quantity, 0)
      ),
      subtotal,
      updated_at: this.asOptionalString(cart['updated_at'])
    };
  }

  private normalizeCartItem(payload: unknown): ItemCarritoLeer {
    const item = payload as Record<string, unknown>;
    const product = this.tryNormalizeProduct(item['product']);
    const unitPrice = Number(item['unit_price'] ?? product?.price ?? 0);
    const quantity = Number(item['quantity'] ?? 0);

    return {
      id: Number(item['id'] ?? item['item_id'] ?? 0),
      cart_id: this.asOptionalNumber(item['cart_id']),
      product_id: Number(item['product_id'] ?? product?.id ?? 0),
      quantity,
      unit_price: unitPrice,
      subtotal: Number(item['subtotal'] ?? unitPrice * quantity),
      product
    };
  }

  private normalizeCheckoutResponse(payload: unknown): RespuestaCheckout {
    const checkout = payload as Record<string, unknown>;

    return {
      order_id: Number(checkout['order_id'] ?? checkout['id'] ?? 0),
      payment_id: String(checkout['payment_id'] ?? checkout['id_pago'] ?? ''),
      payment_url: String(checkout['payment_url'] ?? checkout['checkout_url'] ?? ''),
      payment_status: String(checkout['payment_status'] ?? checkout['status'] ?? 'PENDING'),
      message: this.asOptionalString(checkout['message'] ?? checkout['detail'])
    };
  }

  private normalizeOrder(payload: unknown): OrdenLeer {
    const order = payload as Record<string, unknown>;
    const rawItems = Array.isArray(order['items']) ? order['items'] : [];
    const paymentAttempts = Array.isArray(order['payment_attempts']) ? order['payment_attempts'] : [];

    return {
      id: Number(order['id'] ?? order['order_id'] ?? 0),
      user_id: this.asOptionalNumber(order['user_id']),
      status: String(order['status'] ?? 'PENDING'),
      subtotal: Number(order['subtotal'] ?? order['total'] ?? 0),
      total: Number(order['total'] ?? order['amount'] ?? 0),
      currency: this.asOptionalString(order['currency']),
      items: rawItems.map((item) => {
        const entry = item as Record<string, unknown>;

        return {
          id: Number(entry['id'] ?? 0),
          product_id: Number(entry['product_id'] ?? 0),
          product_name: this.asOptionalString(entry['product_name'] ?? entry['name']),
          quantity: Number(entry['quantity'] ?? 0),
          unit_price: Number(entry['unit_price'] ?? entry['price'] ?? 0),
          line_total: Number(entry['line_total'] ?? entry['subtotal'] ?? 0)
        };
      }),
      payment_attempts: paymentAttempts
        .map((attempt) => this.normalizePaymentAttempt(attempt))
        .filter((attempt): attempt is NonNullable<OrdenLeer['payment_attempts'][number]> => !!attempt),
      created_at: this.asOptionalString(order['created_at']),
      updated_at: this.asOptionalString(order['updated_at'])
    };
  }

  private normalizePaymentAttempt(payload: unknown): OrdenLeer['payment_attempts'][number] | null {
    if (!payload || typeof payload !== 'object') {
      return null;
    }

    const payment = payload as Record<string, unknown>;
    const appPagosId = String(payment['app_pagos_id'] ?? payment['id_pago'] ?? '').trim();
    if (!appPagosId) {
      return null;
    }

    return {
      id: Number(payment['id'] ?? 0),
      app_pagos_id: appPagosId,
      external_reference: this.asOptionalString(payment['external_reference']) ?? null,
      status: String(payment['status'] ?? 'pending'),
      payment_url: this.asOptionalString(payment['payment_url']) ?? null,
      created_at: this.asOptionalString(payment['created_at'])
    };
  }

  private tryNormalizeProduct(payload: unknown): Producto | undefined {
    if (!payload || typeof payload !== 'object') {
      return undefined;
    }

    return this.normalizeProduct(payload);
  }

  private asOptionalString(value: unknown): string | undefined {
    return typeof value === 'string' && value.trim() ? value : undefined;
  }

  private asOptionalNumber(value: unknown): number | undefined {
    if (typeof value === 'number' && Number.isFinite(value)) {
      return value;
    }

    if (typeof value === 'string' && value.trim() && !Number.isNaN(Number(value))) {
      return Number(value);
    }

    return undefined;
  }
}
