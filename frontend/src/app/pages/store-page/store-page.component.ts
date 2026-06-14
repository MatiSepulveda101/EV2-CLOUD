import { CommonModule } from '@angular/common';
import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ItemCarritoLeer, Producto } from '../../core/models/ecommerce.models';
import { ShopStateService } from '../../core/state/shop.state';

type ModoAutenticacion = 'login' | 'register' | 'verify';

@Component({
  selector: 'app-store-page',
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './store-page.component.html',
  styleUrl: './store-page.component.css'
})
export class StorePageComponent implements OnInit {
  readonly tienda = inject(ShopStateService);
  private readonly ruta = inject(ActivatedRoute);
  private readonly destruir = inject(DestroyRef);

  readonly modoAutenticacion = signal<ModoAutenticacion>('login');
  readonly terminoBusqueda = signal('');
  readonly categoriaActiva = signal('Todos');
  readonly modalSesionAbierto = signal(false);
  readonly carritoAbierto = signal(false);
  readonly motivoSesion = signal('Ingresa para continuar con tu compra.');
  readonly archivoSeleccionado = signal<File | null>(null);

  readonly itemsCarrito = computed(() => this.tienda.cart()?.items ?? []);
  readonly subtotalCarrito = computed(() => this.tienda.cart()?.subtotal ?? 0);
  readonly cantidadCarrito = computed(() => this.tienda.cart()?.total_items ?? 0);
  readonly totalResultados = computed(() => this.productosFiltrados().length);

  readonly porcentajeAlmacenamiento = computed(() => this.tienda.almacenamiento()?.porcentaje_usado ?? 0);
  readonly espacioUsadoTexto = computed(() => this.formatearBytes(this.tienda.almacenamiento()?.usado_bytes ?? 0));
  readonly espacioDisponibleTexto = computed(() => this.formatearBytes(this.tienda.almacenamiento()?.disponible_bytes ?? 0));
  readonly limiteAlmacenamientoTexto = computed(() => this.formatearBytes(this.tienda.almacenamiento()?.limite_bytes ?? 0));

  readonly categorias = computed(() => {
    const categorias = new Set<string>(['Todos']);

    for (const producto of this.tienda.products()) {
      categorias.add(this.obtenerCategoriaProducto(producto));
    }

    return Array.from(categorias);
  });

  readonly productosFiltrados = computed(() => {
    const busqueda = this.terminoBusqueda().trim().toLowerCase();
    const categoria = this.categoriaActiva();

    return this.tienda.products().filter((producto) => {
      const categoriaProducto = this.obtenerCategoriaProducto(producto);
      const coincideCategoria = categoria === 'Todos' || categoriaProducto === categoria;
      const nombre = producto.name?.toLowerCase() ?? '';
      const descripcion = producto.description?.toLowerCase() ?? '';
      const coincideBusqueda = !busqueda || nombre.includes(busqueda) || descripcion.includes(busqueda);

      return coincideCategoria && coincideBusqueda;
    });
  });

  readonly formularioLogin = new FormGroup({
    email: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.email]
    }),
    password: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required]
    })
  });

  readonly formularioRegistro = new FormGroup({
    full_name: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.minLength(2)]
    }),
    email: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.email]
    }),
    password: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.minLength(8)]
    })
  });

  readonly formularioVerificacion = new FormGroup({
    email: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.email]
    }),
    codigo: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.minLength(4), Validators.maxLength(10)]
    })
  });

  ngOnInit(): void {
    this.tienda.loadProducts();

    if (this.tienda.sessionState.isAuthenticated()) {
      this.tienda.loadCart();
      this.tienda.loadFiles();
      this.tienda.loadStorage();
    }

    this.ruta.queryParamMap
      .pipe(takeUntilDestroyed(this.destruir))
      .subscribe((parametros) => {
        const idOrden = parametros.get('order_id');

        if (!idOrden) {
          return;
        }

        this.tienda.startOrderSync(idOrden);
      });
  }

  async iniciarSesion(): Promise<void> {
    if (this.formularioLogin.invalid) {
      this.formularioLogin.markAllAsTouched();
      return;
    }

    await this.tienda.login(
      this.formularioLogin.controls.email.value.trim().toLowerCase(),
      this.formularioLogin.controls.password.value
    );

    if (this.tienda.sessionState.isAuthenticated()) {
      this.cerrarModalSesion();
    }
  }

  async registrarCuenta(): Promise<void> {
    if (this.formularioRegistro.invalid) {
      this.formularioRegistro.markAllAsTouched();
      return;
    }

    const emailRegistrado = this.formularioRegistro.controls.email.value.trim().toLowerCase();

    await this.tienda.register({
      full_name: this.formularioRegistro.controls.full_name.value.trim(),
      email: emailRegistrado,
      password: this.formularioRegistro.controls.password.value
    });

    if (!this.tienda.authError()) {
      this.formularioVerificacion.reset({
        email: emailRegistrado,
        codigo: ''
      });

      this.modoAutenticacion.set('verify');

      this.formularioRegistro.reset({
        full_name: '',
        email: '',
        password: ''
      });
    }
  }

  async verificarCuenta(): Promise<void> {
    if (this.formularioVerificacion.invalid) {
      this.formularioVerificacion.markAllAsTouched();
      return;
    }

    const email = this.formularioVerificacion.controls.email.value.trim().toLowerCase();
    const codigo = this.formularioVerificacion.controls.codigo.value.trim();

    await this.tienda.verifyAccount({
      email,
      codigo
    });

    if (!this.tienda.authError()) {
      this.modoAutenticacion.set('login');

      this.formularioLogin.reset({
        email,
        password: ''
      });

      this.formularioVerificacion.reset({
        email: '',
        codigo: ''
      });
    }
  }

  async reenviarCodigo(): Promise<void> {
    const email = this.formularioVerificacion.controls.email.value.trim().toLowerCase();

    if (!email) {
      this.tienda.authError.set('Ingresa el correo para reenviar el codigo.');
      return;
    }

    await this.tienda.resendCode({
      email
    });
  }

  cerrarSesionActual(): void {
    this.tienda.logout();
    this.archivoSeleccionado.set(null);
    this.carritoAbierto.set(false);
    this.cerrarModalSesion();
  }

  abrirSesion(
    modo: ModoAutenticacion = 'login',
    motivo = 'Ingresa para continuar con tu compra.'
  ): void {
    this.modoAutenticacion.set(modo);
    this.motivoSesion.set(motivo);
    this.modalSesionAbierto.set(true);
  }

  cerrarModalSesion(): void {
    this.modalSesionAbierto.set(false);
  }

  cambiarModoAutenticacion(modo: ModoAutenticacion): void {
    this.modoAutenticacion.set(modo);
  }

  actualizarBusqueda(valor: string): void {
    this.terminoBusqueda.set(valor);
  }

  seleccionarCategoria(categoria: string): void {
    this.categoriaActiva.set(categoria);
  }

  async agregarProductoAlCarrito(productoId: number): Promise<void> {
    if (!this.tienda.sessionState.isAuthenticated()) {
      this.abrirSesion('login', 'Inicia sesion para agregar productos al carrito.');
      return;
    }

    await this.tienda.addCartItem(productoId);

    if (!this.tienda.cartError()) {
      this.carritoAbierto.set(true);
    }
  }

  async abrirCarrito(): Promise<void> {
    if (!this.tienda.sessionState.isAuthenticated()) {
      this.abrirSesion('login', 'Inicia sesion para revisar tu carrito.');
      return;
    }

    this.carritoAbierto.set(true);
    await this.tienda.loadCart();
  }

  cerrarCarrito(): void {
    this.carritoAbierto.set(false);
  }

  async aumentarCantidad(item: ItemCarritoLeer): Promise<void> {
    await this.tienda.updateCartItem(item.id, item.quantity + 1);
  }

  async disminuirCantidad(item: ItemCarritoLeer): Promise<void> {
    const nuevaCantidad = item.quantity - 1;

    if (nuevaCantidad <= 0) {
      await this.tienda.removeCartItem(item.id);
      return;
    }

    await this.tienda.updateCartItem(item.id, nuevaCantidad);
  }

  async eliminarItemCarrito(itemId: number): Promise<void> {
    await this.tienda.removeCartItem(itemId);
  }

  async irAPagar(): Promise<void> {
    await this.tienda.createCheckout();
  }

  abrirMisCompras(): void {
    if (!this.tienda.sessionState.isAuthenticated()) {
      this.abrirSesion('login', 'Inicia sesion para revisar tus compras.');
      return;
    }

    document.getElementById('estado-orden')?.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });
  }

  reintentarEstadoOrden(): void {
    this.tienda.retryOrderSync();
  }

  seleccionarArchivo(evento: Event): void {
    const input = evento.target as HTMLInputElement;
    const archivo = input.files?.[0] ?? null;

    this.archivoSeleccionado.set(archivo);
    this.tienda.fileError.set('');
  }

  limpiarArchivoSeleccionado(): void {
    this.archivoSeleccionado.set(null);
  }

  async subirArchivoSeleccionado(): Promise<void> {
    if (!this.tienda.sessionState.isAuthenticated()) {
      this.abrirSesion('login', 'Inicia sesion para subir archivos.');
      return;
    }

    const archivo = this.archivoSeleccionado();

    if (!archivo) {
      this.tienda.fileError.set('Selecciona un archivo antes de subirlo.');
      return;
    }

    await this.tienda.uploadFile(archivo);

    if (!this.tienda.fileError()) {
      this.archivoSeleccionado.set(null);
    }
  }

  async actualizarArchivos(): Promise<void> {
    if (!this.tienda.sessionState.isAuthenticated()) {
      this.abrirSesion('login', 'Inicia sesion para revisar tus archivos.');
      return;
    }

    await this.tienda.loadFiles();
    await this.tienda.loadStorage();
  }

  obtenerCategoriaProducto(producto: Producto): string {
    if (producto.category) {
      return producto.category;
    }

    const texto = `${producto.name} ${producto.description ?? ''}`.toLowerCase();

    if (texto.includes('notebook') || texto.includes('monitor') || texto.includes('ssd')) {
      return 'Computacion';
    }

    if (texto.includes('teclado') || texto.includes('mouse') || texto.includes('audifono')) {
      return 'Perifericos';
    }

    return 'Tecnologia';
  }

  obtenerMarcaProducto(producto: Producto): string {
    return producto.name.split(' ')[0] || 'Producto';
  }

  obtenerPrecioReferencia(precio: number): number {
    return Math.round(precio * 1.12);
  }

  obtenerPrecioItem(item: ItemCarritoLeer): number {
    return item.unit_price ?? item.product?.price ?? 0;
  }

  obtenerTotalItem(item: ItemCarritoLeer): number {
    return item.subtotal ?? this.obtenerPrecioItem(item) * item.quantity;
  }

  formatearBytes(bytes: number): string {
    if (!bytes || bytes <= 0) {
      return '0 MB';
    }

    const mb = bytes / 1024 / 1024;

    if (mb < 1024) {
      return `${mb.toFixed(2)} MB`;
    }

    return `${(mb / 1024).toFixed(2)} GB`;
  }

  formatearFecha(fecha: string | undefined): string {
    if (!fecha) {
      return 'Sin fecha';
    }

    return new Date(fecha).toLocaleString('es-CL', {
      dateStyle: 'short',
      timeStyle: 'short'
    });
  }
}