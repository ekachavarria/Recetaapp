"""Punto de entrada: crea la app Flask conectando Modelo, Vista y Controlador."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, url_for

from recetaapp.controllers.recetario_controller import CATEGORIAS, bp
from recetaapp.models.receta import Receta
from recetaapp.models.recetario import Recetario

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_DATOS = RAIZ_PROYECTO / "data" / "recetas.json"

IMAGENES_POR_CATEGORIA = {
    "Desayuno": "fotos/desayuno.jpg",
    "Almuerzo": "fotos/almuerzo.jpg",
    "Cena": "fotos/cena.jpg",
    "Postre": "fotos/postre.jpg",
    "Snack": "fotos/snack.jpg",
}


def imagen_categoria(categoria: str) -> str:
    return IMAGENES_POR_CATEGORIA.get(categoria, "fotos/default.jpg")


def url_imagen_receta(receta: Receta) -> str:
    if receta.imagen:
        if receta.imagen.startswith(("http://", "https://")):
            return receta.imagen
        return url_for("static", filename=f"img/{receta.imagen}")
    return url_for("static", filename=f"img/{imagen_categoria(receta.categoria)}")


def create_app(ruta_datos: Path | str = RUTA_DATOS) -> Flask:
    vistas_dir = Path(__file__).resolve().parent / "views"
    app = Flask(
        __name__,
        template_folder=str(vistas_dir / "templates"),
        static_folder=str(vistas_dir / "static"),
    )
    app.config["SECRET_KEY"] = "recetaapp-dev-secret"
    app.config["RECETARIO"] = Recetario(ruta_datos)

    app.jinja_env.globals["imagen_categoria"] = imagen_categoria
    app.jinja_env.globals["url_imagen_receta"] = url_imagen_receta
    app.jinja_env.globals["categorias_disponibles"] = CATEGORIAS

    app.register_blueprint(bp)
    return app


def main() -> None:
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    main()
