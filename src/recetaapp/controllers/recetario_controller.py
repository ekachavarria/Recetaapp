"""Controlador web: rutas Flask que conectan el Recetario (modelo) con las
plantillas (vista). No contiene reglas de negocio ni HTML.
"""

from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from recetaapp.models.receta import Ingrediente
from recetaapp.models.recetario import RecetaInvalidaError, RecetaNoEncontradaError

CATEGORIAS = ["Desayuno", "Almuerzo", "Cena", "Postre", "Snack"]

bp = Blueprint("recetario", __name__)


def _recetario():
    return current_app.config["RECETARIO"]


def _parsear_ingredientes(texto: str) -> list[Ingrediente]:
    ingredientes = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        partes = [p.strip() for p in linea.split(",", 2)]
        if len(partes) != 3:
            raise RecetaInvalidaError(
                f"Formato de ingrediente inválido: '{linea}'. Usa 'cantidad, unidad, nombre'."
            )
        cantidad_texto, unidad, nombre = partes
        try:
            cantidad = float(cantidad_texto)
        except ValueError as exc:
            raise RecetaInvalidaError(
                f"La cantidad '{cantidad_texto}' de '{nombre}' no es un número."
            ) from exc
        ingredientes.append(Ingrediente(nombre=nombre, cantidad=cantidad, unidad=unidad))
    return ingredientes


def _parsear_pasos(texto: str) -> list[str]:
    return [linea.strip() for linea in texto.splitlines() if linea.strip()]


def _datos_formulario(form) -> dict:
    return {
        "nombre": form.get("nombre", "").strip(),
        "categoria": form.get("categoria", CATEGORIAS[0]),
        "tiempo_preparacion_min": form.get("tiempo_preparacion_min", ""),
        "porciones": form.get("porciones", ""),
        "ingredientes_texto": form.get("ingredientes", ""),
        "pasos_texto": form.get("pasos", ""),
        "imagen": form.get("imagen", "").strip(),
    }


@bp.get("/")
def listar():
    q = request.args.get("q", "").strip()
    categoria = request.args.get("categoria", "").strip()
    tiempo_max_raw = request.args.get("tiempo_max", "").strip()
    tiempo_max = int(tiempo_max_raw) if tiempo_max_raw.isdigit() else None

    recetario = _recetario()
    recetas = recetario.buscar(q) if q else recetario.listar()
    if categoria:
        recetas = [r for r in recetas if r.categoria.lower() == categoria.lower()]
    if tiempo_max is not None:
        recetas = [r for r in recetas if r.tiempo_preparacion_min <= tiempo_max]

    return render_template(
        "index.html",
        recetas=recetas,
        categorias=CATEGORIAS,
        criterios={"q": q, "categoria": categoria, "tiempo_max": tiempo_max_raw},
    )


@bp.get("/recetas/<id_receta>")
def detalle(id_receta: str):
    try:
        receta = _recetario().obtener_por_id(id_receta)
    except RecetaNoEncontradaError:
        flash("La receta solicitada no existe.", "error")
        return redirect(url_for("recetario.listar"))
    return render_template("detalle.html", receta=receta)


@bp.route("/recetas/nueva", methods=["GET", "POST"])
def nueva():
    if request.method == "GET":
        return render_template(
            "form.html", titulo="Nueva receta", categorias=CATEGORIAS, valores={}
        )

    valores = _datos_formulario(request.form)
    try:
        ingredientes = _parsear_ingredientes(valores["ingredientes_texto"])
        pasos = _parsear_pasos(valores["pasos_texto"])
        receta = _recetario().crear(
            nombre=valores["nombre"],
            categoria=valores["categoria"],
            ingredientes=ingredientes,
            pasos=pasos,
            tiempo_preparacion_min=int(valores["tiempo_preparacion_min"] or 0),
            porciones=int(valores["porciones"] or 0),
            imagen=valores["imagen"] or None,
        )
    except (RecetaInvalidaError, ValueError) as exc:
        flash(str(exc), "error")
        return render_template(
            "form.html", titulo="Nueva receta", categorias=CATEGORIAS, valores=valores
        )

    flash(f"Receta '{receta.nombre}' creada correctamente.", "exito")
    return redirect(url_for("recetario.detalle", id_receta=receta.id))


@bp.route("/recetas/<id_receta>/editar", methods=["GET", "POST"])
def editar(id_receta: str):
    try:
        receta = _recetario().obtener_por_id(id_receta)
    except RecetaNoEncontradaError:
        flash("La receta solicitada no existe.", "error")
        return redirect(url_for("recetario.listar"))

    if request.method == "GET":
        valores = {
            "nombre": receta.nombre,
            "categoria": receta.categoria,
            "tiempo_preparacion_min": receta.tiempo_preparacion_min,
            "porciones": receta.porciones,
            "ingredientes_texto": "\n".join(
                f"{i.cantidad}, {i.unidad}, {i.nombre}" for i in receta.ingredientes
            ),
            "pasos_texto": "\n".join(receta.pasos),
            "imagen": receta.imagen or "",
        }
        return render_template(
            "form.html", titulo=f"Editar '{receta.nombre}'", categorias=CATEGORIAS, valores=valores
        )

    valores = _datos_formulario(request.form)
    try:
        ingredientes = _parsear_ingredientes(valores["ingredientes_texto"])
        pasos = _parsear_pasos(valores["pasos_texto"])
        actualizada = _recetario().actualizar(
            id_receta,
            nombre=valores["nombre"],
            categoria=valores["categoria"],
            ingredientes=ingredientes,
            pasos=pasos,
            tiempo_preparacion_min=int(valores["tiempo_preparacion_min"] or 0),
            porciones=int(valores["porciones"] or 0),
            imagen=valores["imagen"] or None,
        )
    except (RecetaInvalidaError, ValueError) as exc:
        flash(str(exc), "error")
        return render_template(
            "form.html",
            titulo=f"Editar '{receta.nombre}'",
            categorias=CATEGORIAS,
            valores=valores,
        )

    flash(f"Receta '{actualizada.nombre}' actualizada correctamente.", "exito")
    return redirect(url_for("recetario.detalle", id_receta=actualizada.id))


@bp.post("/recetas/<id_receta>/eliminar")
def eliminar(id_receta: str):
    try:
        receta = _recetario().obtener_por_id(id_receta)
        _recetario().eliminar(id_receta)
        flash(f"Receta '{receta.nombre}' eliminada.", "exito")
    except RecetaNoEncontradaError:
        flash("La receta solicitada no existe.", "error")
    return redirect(url_for("recetario.listar"))
