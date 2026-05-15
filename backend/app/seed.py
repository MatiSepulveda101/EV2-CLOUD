from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Producto


PRODUCTOS_DEMO = [
    {
        "name": "Notebook Lenovo IdeaPad 15",
        "description": "Notebook para estudio y trabajo con SSD y pantalla Full HD.",
        "price": Decimal("459990"),
        "stock": 12,
        "image_url": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853",
    },
    {
        "name": "Monitor Samsung 24 pulgadas",
        "description": "Monitor IPS Full HD para escritorio y clases remotas.",
        "price": Decimal("129990"),
        "stock": 18,
        "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf",
    },
    {
        "name": "Teclado mecanico Redragon",
        "description": "Teclado compacto con switches mecanicos y retroiluminacion.",
        "price": Decimal("49990"),
        "stock": 30,
        "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3",
    },
    {
        "name": "Mouse Logitech inalambrico",
        "description": "Mouse ergonomico para productividad diaria.",
        "price": Decimal("24990"),
        "stock": 40,
        "image_url": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46",
    },
    {
        "name": "Audifonos Bluetooth JBL",
        "description": "Audifonos con cancelacion pasiva y bateria de larga duracion.",
        "price": Decimal("69990"),
        "stock": 22,
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e",
    },
    {
        "name": "Disco SSD Kingston 1TB",
        "description": "Unidad SSD SATA para mejorar velocidad de carga y almacenamiento.",
        "price": Decimal("84990"),
        "stock": 16,
        "image_url": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b",
    },
]


def cargar_productos_demo(db: Session) -> None:
    producto_existente = db.scalar(select(Producto.id).limit(1))
    if producto_existente is not None:
        return

    db.add_all(Producto(**producto) for producto in PRODUCTOS_DEMO)
    db.commit()
