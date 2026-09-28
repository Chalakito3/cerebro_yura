#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import random
from difflib import SequenceMatcher

import resultados
import depuracion
import pronunciaciones
import texto as texto_util


# Si no hay diccionario, el juego usa estas palabras (con traducción de respaldo).
PALABRAS_DE_RESPALDO = ["gato", "perro", "sol", "agua", "casa", "arbol"]


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
        reproducir_pronunciacion=None,
    ):
        # palabras puede ser una lista o una función que la devuelve (se
        # consulta en cada partida para usar el diccionario actualizado).
        self.fuente_palabras = palabras
        self.lista_juego = [] if callable(palabras) else list(palabras)
        self.palabras_partida = []
        self.indice_juego = 0
        self.consultar_traduccion = consultar_traduccion
        self.escuchar_voz = escuchar_voz
        self.hablar = hablar
        self.mover_actuador = mover_actuador
        self.normalizar_texto = normalizar_texto
        self.registrar_evento = registrar_evento
        # Hace escuchar la grabación de la docente (modo docente), si existe.
        self.reproducir_pronunciacion = reproducir_pronunciacion
        self.aciertos = 0
        self.silencios_seguidos = 0
        self.partida = resultados.nueva_sesion()

    def reiniciar(self):
        if callable(self.fuente_palabras):
            self.lista_juego = list(self.fuente_palabras()) or list(PALABRAS_DE_RESPALDO)
        cantidad = min(4, len(self.lista_juego))
        self.palabras_partida = random.sample(self.lista_juego, cantidad)
        self.indice_juego = 0
        self.aciertos = 0
        self.silencios_seguidos = 0
        self.partida = resultados.nueva_sesion()

    def _respuesta_es_correcta(self, respuesta_usuario, respuesta_correcta):
        # Antes bastaba un 75 % de parecido y se aceptaban palabras distintas
        # (wawa por Tawa, Sara por Sach'a).
        return texto_util.respuesta_quechua_correcta(
            respuesta_usuario,
            respuesta_correcta,
            pronunciaciones.variantes(respuesta_correcta)
        )

    def ejecutar_turno(self):
        if not self.palabras_partida:
            self.reiniciar()

        if self.indice_juego >= len(self.palabras_partida):
            self.hablar(self._mensaje_final())
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
                "arbol": "sach'a"
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

        respuesta_ninio = self.normalizar_texto(
            self.escuchar_voz(pistas=self._pistas(traduccion_correcta))
        )

        if respuesta_ninio == "":
            # Sin límite, la misma pregunta se repetía para siempre.
            self.silencios_seguidos += 1
            if self.silencios_seguidos >= 3:
                self.hablar(
                    "No escucho a nadie. Terminamos el juego por ahora "
                    "y regreso al menú principal."
                )
                return "menu"
            self.hablar("No logré escucharte.")
            return "continuar"

        self.silencios_seguidos = 0

        if texto_util.pide_orden(respuesta_ninio, ("salir", "menu", "terminar")):
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

        depuracion.depurar(
            f"[EVALUACION]: "
            f"Usuario='{respuesta_ninio}' | "
            f"Correcta='{respuesta_correcta_norm}' | "
            f"Similitud={similitud:.2f}"
        )

        resultados.registrar_intento(
            "juego",
            palabra_es,
            traduccion_correcta,
            respuesta_ninio,
            es_correcta,
            self.partida,
        )

        if es_correcta:
            self.aciertos += 1
            self.mover_actuador("CELEBRAR_ALEGRE")
            if self.registrar_evento:
                self.registrar_evento(
                    "result",
                    question=f"¿Cómo se dice, {palabra_es}, en quechua?",
                    answer=traduccion_correcta,
                    word=palabra_es,
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
                    word=palabra_es,
                    correct=False
                )
            self.hablar(
                "Sigue aprendiendo, tú puedes. "
                f"Se dice de la siguiente manera: "
                f"{traduccion_correcta}."
            )
            if self.reproducir_pronunciacion:
                self.reproducir_pronunciacion(traduccion_correcta)

        self.indice_juego += 1
        return "continuar"

    def _pistas(self, traduccion_correcta):
        """Palabras que el reconocedor debe esperar: la respuesta mezclada
        con las demás de la partida y otras del juego, para no favorecerla."""
        otras = [p for p in self.lista_juego if p not in self.palabras_partida]
        candidatas = list(self.palabras_partida) + random.sample(otras, min(3, len(otras)))
        pistas = [traduccion_correcta]
        for palabra in candidatas:
            try:
                traduccion = self.consultar_traduccion(palabra)
            except Exception:
                traduccion = None
            if traduccion and traduccion not in pistas:
                pistas.append(traduccion)
        random.shuffle(pistas)
        return pistas

    def _mensaje_final(self):
        total = len(self.palabras_partida)
        if self.aciertos == total:
            inicio = "¡Felicidades! Acertaste todas"
        elif self.aciertos * 2 >= total:
            inicio = f"¡Muy bien! Acertaste {self.aciertos} de {total}"
        else:
            inicio = (
                f"Acertaste {self.aciertos} de {total}. "
                "Sigue practicando, tú puedes"
            )
        return f"{inicio}. Regresemos al menú principal."
