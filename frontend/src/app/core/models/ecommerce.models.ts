export interface UsuarioCrear {
  email: string;
  password: string;
  full_name?: string;
}

export interface UsuarioLeer {
  id: number;
  email: string;
  full_name?: string;
  is_active?: boolean;
  created_at?: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  user?: UsuarioLeer;
}

export interface Producto {
  id: number;
  name: string;
  description?: string;
  price: number;
  image_url?: string;
  category?: string;
  stock?: number;
}

export interface ItemCarritoCrear {
  product_id: number;
  quantity: number;
}

export interface ItemCarritoActualizar {
  quantity: number;
}

export interface ItemCarritoLeer {
  id: number;
  cart_id?: number;
  product_id: number;
  quantity: number;
  unit_price?: number;
  subtotal?: number;
  product?: Producto;
}

export interface CarritoLeer {
  id: number;
  user_id?: number;
  items: ItemCarritoLeer[];
  total_items: number;
  subtotal: number;
  updated_at?: string;
}

export interface RespuestaCheckout {
  order_id: number;
  payment_id: string;
  payment_url: string;
  payment_status: string;
  message?: string;
}

export interface ItemOrdenLeer {
  id: number;
  product_id: number;
  product_name?: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

export interface IntentoPagoLeer {
  id: number;
  app_pagos_id: string;
  external_reference?: string | null;
  status: string;
  payment_url?: string | null;
  created_at?: string;
}

export interface OrdenLeer {
  id: number;
  user_id?: number;
  status: string;
  subtotal?: number;
  total: number;
  currency?: string;
  items: ItemOrdenLeer[];
  payment_attempts: IntentoPagoLeer[];
  created_at?: string;
  updated_at?: string;
}
