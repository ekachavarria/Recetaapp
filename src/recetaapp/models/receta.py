"""Entidades de dominio: Ingrediente y Receta."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Ingrediente:
    nombre: str
    cantidad: float
    unidad: str

    def to_dict(self) -> dict:
        return {
            "nombre": self.nombre,
            "cantidad": self.cantidad,
            "unidad": self.unidad,
        }

    @staticmethod
    def from_dict(data: dict) -> "Ingrediente":
        return Ingrediente(
            nombre=data["nombre"],
            cantidad=data["cantidad"],
            unidad=data["unidad"],
        )


@dataclass
class Receta:
    nombre: str
    categoria: str
    ingredientes: list[Ingrediente]
    pasos: list[str]
    tiempo_preparacion_min: int
    porciones: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    imagen: str | None = None
    fecha_creacion: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    fecha_actualizacion: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "categoria": self.categoria,
            "ingredientes": [i.to_dict() for i in self.ingredientes],
            "pasos": self.pasos,
            "tiempo_preparacion_min": self.tiempo_preparacion_min,
            "porciones": self.porciones,
            "imagen": self.imagen,
            "fecha_creacion": self.fecha_creacion,
            "fecha_actualizacion": self.fecha_actualizacion,
        }

    @staticmethod
    def from_dict(data: dict) -> "Receta":
        return Receta(
            id=data["id"],
            nombre=data["nombre"],
            categoria=data["categoria"],
            ingredientes=[Ingrediente.from_dict(i) for i in data["ingredientes"]],
            pasos=list(data["pasos"]),
            tiempo_preparacion_min=data["tiempo_preparacion_min"],
            porciones=data["porciones"],
            imagen=data.get("imagen"),
            fecha_creacion=data["fecha_creacion"],
            fecha_actualizacion=data["fecha_actualizacion"],
        )
