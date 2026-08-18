"""Repositorio de recetas: CRUD, búsqueda, filtrado y persistencia en JSON."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from recetaapp.models.receta import Ingrediente, Receta


class RecetaNoEncontradaError(Exception):
    pass


class RecetaInvalidaError(Exception):
    pass


class Recetario:
    def __init__(self, ruta_json: Path | str):
        self._ruta = Path(ruta_json)
        self._recetas: dict[str, Receta] = {}
        self._cargar()

    # -- persistencia -----------------------------------------------------

    def _cargar(self) -> None:
        if not self._ruta.exists():
            self._ruta.parent.mkdir(parents=True, exist_ok=True)
            self._ruta.write_text("[]", encoding="utf-8")

        contenido = self._ruta.read_text(encoding="utf-8").strip()
        datos = json.loads(contenido) if contenido else []
        self._recetas = {r["id"]: Receta.from_dict(r) for r in datos}

    def _guardar(self) -> None:
        datos = [r.to_dict() for r in self._recetas.values()]
        self._ruta.write_text(
            json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # -- validación ---------------------------------------------------------

    def _validar(
        self,
        nombre: str,
        ingredientes: list[Ingrediente],
        pasos: list[str],
        tiempo_preparacion_min: int,
        porciones: int,
        id_actual: str | None = None,
    ) -> None:
        if not nombre or not nombre.strip():
            raise RecetaInvalidaError("El nombre no puede estar vacío.")

        for receta in self._recetas.values():
            if receta.id != id_actual and receta.nombre.strip().lower() == nombre.strip().lower():
                raise RecetaInvalidaError(f"Ya existe una receta llamada '{nombre}'.")

        if not ingredientes:
            raise RecetaInvalidaError("La receta debe tener al menos un ingrediente.")
        for ing in ingredientes:
            if not ing.nombre or not ing.nombre.strip():
                raise RecetaInvalidaError("Cada ingrediente debe tener nombre.")
            if ing.cantidad <= 0:
                raise RecetaInvalidaError("La cantidad de cada ingrediente debe ser mayor a 0.")

        if not pasos:
            raise RecetaInvalidaError("La receta debe tener al menos un paso.")
        if any(not p or not p.strip() for p in pasos):
            raise RecetaInvalidaError("Ningún paso puede estar vacío.")

        if tiempo_preparacion_min <= 0:
            raise RecetaInvalidaError("El tiempo de preparación debe ser mayor a 0.")
        if porciones <= 0:
            raise RecetaInvalidaError("Las porciones deben ser mayor a 0.")

    # -- CRUD -----------------------------------------------------------

    def crear(
        self,
        nombre: str,
        categoria: str,
        ingredientes: list[Ingrediente],
        pasos: list[str],
        tiempo_preparacion_min: int,
        porciones: int,
        imagen: str | None = None,
    ) -> Receta:
        self._validar(nombre, ingredientes, pasos, tiempo_preparacion_min, porciones)
        receta = Receta(
            nombre=nombre.strip(),
            categoria=categoria.strip(),
            ingredientes=ingredientes,
            pasos=[p.strip() for p in pasos],
            tiempo_preparacion_min=tiempo_preparacion_min,
            porciones=porciones,
            imagen=imagen or None,
        )
        self._recetas[receta.id] = receta
        self._guardar()
        return receta

    def listar(self) -> list[Receta]:
        return sorted(self._recetas.values(), key=lambda r: r.nombre.lower())

    def obtener_por_id(self, id_receta: str) -> Receta:
        receta = self._recetas.get(id_receta)
        if receta is None:
            raise RecetaNoEncontradaError(f"No existe una receta con id '{id_receta}'.")
        return receta

    def actualizar(
        self,
        id_receta: str,
        *,
        nombre: str | None = None,
        categoria: str | None = None,
        ingredientes: list[Ingrediente] | None = None,
        pasos: list[str] | None = None,
        tiempo_preparacion_min: int | None = None,
        porciones: int | None = None,
        imagen: str | None = None,
    ) -> Receta:
        actual = self.obtener_por_id(id_receta)

        nuevo_nombre = actual.nombre if nombre is None else nombre
        nuevos_ingredientes = actual.ingredientes if ingredientes is None else ingredientes
        nuevos_pasos = actual.pasos if pasos is None else pasos
        nuevo_tiempo = (
            actual.tiempo_preparacion_min
            if tiempo_preparacion_min is None
            else tiempo_preparacion_min
        )
        nuevas_porciones = actual.porciones if porciones is None else porciones

        self._validar(
            nuevo_nombre,
            nuevos_ingredientes,
            nuevos_pasos,
            nuevo_tiempo,
            nuevas_porciones,
            id_actual=id_receta,
        )

        actualizada = replace(
            actual,
            nombre=nuevo_nombre.strip(),
            categoria=(actual.categoria if categoria is None else categoria.strip()),
            ingredientes=nuevos_ingredientes,
            pasos=[p.strip() for p in nuevos_pasos],
            tiempo_preparacion_min=nuevo_tiempo,
            porciones=nuevas_porciones,
            imagen=(actual.imagen if imagen is None else imagen),
            fecha_actualizacion=datetime.now(timezone.utc).isoformat(),
        )
        self._recetas[id_receta] = actualizada
        self._guardar()
        return actualizada

    def eliminar(self, id_receta: str) -> None:
        self.obtener_por_id(id_receta)
        del self._recetas[id_receta]
        self._guardar()

    # -- búsqueda / filtrado ------------------------------------------------

    def buscar(self, texto: str) -> list[Receta]:
        texto = texto.strip().lower()
        if not texto:
            return self.listar()

        resultado = []
        for receta in self.listar():
            en_nombre = texto in receta.nombre.lower()
            en_ingredientes = any(texto in ing.nombre.lower() for ing in receta.ingredientes)
            if en_nombre or en_ingredientes:
                resultado.append(receta)
        return resultado

    def filtrar(
        self, categoria: str | None = None, tiempo_max: int | None = None
    ) -> list[Receta]:
        resultado = self.listar()
        if categoria:
            categoria = categoria.strip().lower()
            resultado = [r for r in resultado if r.categoria.lower() == categoria]
        if tiempo_max is not None:
            resultado = [r for r in resultado if r.tiempo_preparacion_min <= tiempo_max]
        return resultado
