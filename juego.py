#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import random
from difflib import SequenceMatcher


class Juego:

    def __init__(
        self,
        palabras,
        consultar_traduccion,
        escuchar_voz,
        hablar,
        mover_actuador,
        normalizar_texto,
        registrar_evento=None,
    ):
        self.lista_juego = list(palabras)
        self.palabras_partida = []
        self.indice_juego = 0
        self.consultar_traduccion = consultar_traduccion
        self.escuchar_voz = escuchar_voz
        self.hablar = hablar
        self.mover_actuador = mover_actuador
        self.normalizar_texto = normalizar_texto
        self.registrar_evento = registrar_evento

    def reiniciar(self):
        cantidad = min(4, len(self.lista_juego))
        self.palabras_partida = random.sample(self.lista_juego, cantidad)
        self.indice_juego = 0

    def _respuesta_es_correcta(self, respuesta_usuario, respuesta_correcta):
        respuesta_usuario = self.normalizar_texto(respuesta_usuario)
        respuesta_correcta = self.normalizar_texto(respuesta_correcta)

        if respuesta_usuario == "" or respuesta_correcta == "":
            return False

        if respuesta_usuario == respuesta_correcta:
            return True

        compacta = (
            re.sub(r"\s+", "", respuesta_usuario)
            .replace("q", "k")
            .replace("v", "b")
            .replace("h", "")
            .replace("ll", "y")
        )
        compactb = (
            re.sub(r"\s+", "", respuesta_correcta)
            .replace("q", "k")
            .replace("v", "b")
            .replace("h", "")
            .replace("ll", "y")
        )

        if compacta == compactb:
            return True

        similitud_cruda = SequenceMatcher(
            None,
            respuesta_usuario,
            respuesta_correcta
        ).ratio()

        similitud_compacta = SequenceMatcher(
            None,
            compacta,
            compactb
        ).ratio()

        if similitud_compacta >= 0.75:
            return True

        if similitud_cruda >= 0.75 and (
            respuesta_usuario in respuesta_correcta
            or respuesta_correcta in respuesta_usuario
        ):
            return True

        return False

    def ejecutar_turno(self):
        if not self.palabras_partida:
            self.reiniciar()

        if self.indice_juego >= len(self.palabras_partida):
            self.hablar(
                "¡Felicidades! "
                "Completaste todas las palabras del juego. "
                "Regresemos al menú principal."
            )
            return "menu"

        palabra_es = self.palabras_partida[self.indice_juego]
        traduccion_correcta = self.consultar_traduccion(palabra_es)

        if not traduccion_correcta:
            mapeo_emergencia = {
                "gato": "michi",
                "perro": "allqu",
                "sol": "inti",
                "agua": "yaku",
                "casa": "wasi",
                "arbol": "sacha"
            }
            traduccion_correcta = mapeo_emergencia.get(
                self.normalizar_texto(palabra_es),
                ""
            )

        if not traduccion_correcta:
            self.hablar(
                "No pude cargar la respuesta correcta "
                "de esta pregunta."
            )
            return "continuar"

        if self.registrar_evento:
            self.registrar_evento(
                "question",
                question=f"¿Cómo se dice, {palabra_es}, en quechua?",
                answer=traduccion_correcta
            )

        self.hablar(
            f"¿Cómo se dice, {palabra_es}, en quechua?"
        )

        respuesta_ninio = self.escuchar_voz()

        if respuesta_ninio == "":
            self.hablar("No logré escucharte.")
            return "continuar"

        respuesta_ninio = self.normalizar_texto(respuesta_ninio)

        if respuesta_ninio == "":
            self.hablar("No logré escucharte.")
            return "continuar"

        if "salir" in respuesta_ninio or "menu" in respuesta_ninio:
            self.hablar("Saliendo al menú principal.")
            return "menu"

        respuesta_correcta_norm = self.normalizar_texto(
            traduccion_correcta
        )

        if respuesta_correcta_norm == "":
            self.hablar("No pude determinar la respuesta correcta.")
            return "continuar"

        es_correcta = self._respuesta_es_correcta(
            respuesta_ninio,
            respuesta_correcta_norm
        )

        similitud = SequenceMatcher(
            None,
            respuesta_ninio,
            respuesta_correcta_norm
        ).ratio()

        print(
            f"[EVALUACION]: "
            f"Usuario='{respuesta_ninio}' | "
            f"Correcta='{respuesta_correcta_norm}' | "
            f"Similitud={similitud:.2f}"
        )

        if es_correcta:
            self.mover_actuador("CELEBRAR_ALEGRE")
            if self.registrar_evento:
                self.registrar_evento(
                    "result",
                    question=f"¿Cómo se dice, {palabra_es}, en quechua?",
                    answer=traduccion_correcta,
                    correct=True
                )
            self.hablar(
                "¡Excelente! "
                "Lo dijiste de forma correcta. "
                "¡Muy bien hecho!"
            )
        else:
            self.mover_actuador("TRISTE")
            if self.registrar_evento:
                self.registrar_evento(
                    "result",
                    question=f"¿Cómo se dice, {palabra_es}, en quechua?",
                    answer=traduccion_correcta,
                    correct=False
                )
            self.hablar(
                "Sigue aprendiendo, tú puedes. "
                f"Se dice de la siguiente manera: "
                f"{traduccion_correcta}."
            )

        self.indice_juego += 1
        return "continuar"
