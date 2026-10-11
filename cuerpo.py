"""Cuerpo de Yura: un ESP32 conectado por USB (puerto serie).

El cerebro le manda líneas de texto cortas, una por orden (el programa del
ESP32 está en cuerpo_esp32/, con el protocolo completo y los pines):

    ESTADO:HABLANDO      lo que Yura está haciendo (gestos del cuello)
    ACCION:TRISTE        un gesto pedido (por ejemplo en el juego)
    MOVER:ADELANTE:1500  ruedas (el ESP32 limita a 3 s y frena ante obstáculos)
    ALTO                 detiene las ruedas
    PING                 el ESP32 responde una línea que empieza con "YURA"

Cada 2 s sin órdenes se manda PING: si el ESP32 no recibe nada en 5 s, frena
los motores. Sin ESP32 conectado, Yura funciona igual: las órdenes se
descartan y se vuelve a buscar el cuerpo cada pocos segundos.

Configuración (.env.local):
    YURA_CUERPO=0                    no usar el cuerpo
    YURA_CUERPO_PUERTO=/dev/ttyUSB0  puerto fijo en lugar de buscarlo
"""
import os
import queue
import threading
import time

import depuracion

# Fabricantes de los chips USB de las placas ESP32 más comunes.
_FABRICANTES_USB = {0x10C4, 0x1A86, 0x303A, 0x0403}  # CP210x, CH340, USB nativo, FTDI
_REINTENTO = 5.0
_LATIDO = 2.0
# Al abrir el puerto, el ESP32 puede reiniciarse: tiempo para que arranque.
ESPERA_ARRANQUE = 2.0
DIRECCIONES = ("ADELANTE", "ATRAS", "IZQUIERDA", "DERECHA")


def abrir_puerto(puerto, baudios=115200, **opciones):
    """Abre el puerto sin tocar DTR/RTS: en la ESP32 DevKit esas líneas
    manejan EN/BOOT, y con su chip USB (CP2102) dejaban al ESP32
    reiniciándose en bucle (07/10/2026)."""
    import serial

    conexion = serial.serial_for_url(puerto, baudios, do_not_open=True, **opciones)
    conexion.dtr = False
    conexion.rts = False
    conexion.open()
    return conexion


def buscar_puerto():
    """El puerto serie del ESP32, o None si no hay ninguno conectado."""
    try:
        from serial.tools import list_ports
    except ImportError:
        return None
    for puerto in list_ports.comports():
        if puerto.vid in _FABRICANTES_USB:
            return puerto.device
    return None


class CuerpoESP32:

    def __init__(self, puerto=None):
        self.activo = os.environ.get("YURA_CUERPO", "1").strip() != "0"
        self.puerto_fijo = puerto or os.environ.get("YURA_CUERPO_PUERTO", "").strip() or None
        self.conexion = None
        self.ultimo_estado = None
        self._cola = queue.Queue(maxsize=50)
        self._hilo = None
        if self.activo:
            self._hilo = threading.Thread(target=self._trabajar, name="cuerpo-esp32", daemon=True)
            self._hilo.start()

    @property
    def conectado(self):
        return self.conexion is not None

    # ------------------------------------------------------------ órdenes

    def estado(self, estado):
        """Avisa al cuerpo lo que Yura está haciendo (solo si cambió)."""
        if estado and estado != self.ultimo_estado:
            self.ultimo_estado = estado
            self._enviar(f"ESTADO:{estado}")

    def accion(self, accion):
        if accion:
            self._enviar(f"ACCION:{accion}")

    def mover(self, direccion, milisegundos=1000):
        direccion = str(direccion).upper()
        if direccion in DIRECCIONES:
            self._enviar(f"MOVER:{direccion}:{int(milisegundos)}")

    def alto(self):
        self._enviar("ALTO")

    def _enviar(self, linea):
        if not self.activo:
            return
        try:
            self._cola.put_nowait(linea)
        except queue.Full:
            pass  # el cuerpo no responde: no se frena al cerebro

    # ------------------------------------------------------------ conexión

    def _conectar(self):
        import serial

        puerto = self.puerto_fijo or buscar_puerto()
        if not puerto:
            return False
        try:
            conexion = abrir_puerto(puerto, timeout=0.2, write_timeout=1)
        except (serial.SerialException, OSError) as exc:
            depuracion.depurar(f"[CUERPO] No se pudo abrir {puerto}: {exc}")
            return False
        time.sleep(ESPERA_ARRANQUE)
        conexion.reset_input_buffer()
        self.conexion = conexion
        print(f"[CUERPO] ESP32 conectado en {puerto}.")
        respuesta = self._escribir("PING", esperar_respuesta=True)
        if respuesta:
            print(f"[CUERPO] El ESP32 respondió: {respuesta}")
        else:
            print("[CUERPO] El ESP32 no respondió al PING (¿programa cargado?). Se le envían igual las órdenes.")
        if self.ultimo_estado:
            self._escribir(f"ESTADO:{self.ultimo_estado}")
        return True

    def _desconectar(self, motivo):
        if self.conexion is not None:
            print(f"[CUERPO] Se perdió el ESP32 ({motivo}). Se vuelve a buscar.")
            try:
                self.conexion.close()
            except Exception:
                pass
        self.conexion = None

    def _escribir(self, linea, esperar_respuesta=False):
        import serial

        try:
            self.conexion.write((linea + "\n").encode("ascii", "ignore"))
            self.conexion.flush()
            depuracion.depurar(f"[CUERPO] -> {linea}")
            if esperar_respuesta:
                limite = time.time() + 1.5
                while time.time() < limite:
                    recibido = self.conexion.readline().decode("utf-8", "ignore").strip()
                    if recibido.upper().startswith("YURA"):
                        return recibido
            return None
        except (serial.SerialException, OSError) as exc:
            self._desconectar(exc)
            return None

    def _trabajar(self):
        try:
            import serial  # noqa: F401
        except ImportError:
            print("[CUERPO] Falta pyserial: pip install pyserial. Yura sigue sin cuerpo.")
            return
        while True:
            if self.conexion is None and not self._conectar():
                # Sin cuerpo: se descartan las órdenes viejas y se reintenta.
                time.sleep(_REINTENTO)
                while not self._cola.empty():
                    self._cola.get_nowait()
                continue
            try:
                linea = self._cola.get(timeout=_LATIDO)
            except queue.Empty:
                linea = "PING"  # latido: el ESP32 sabe que el cerebro sigue ahí
                try:
                    self.conexion.reset_input_buffer()
                except Exception:
                    pass
            self._escribir(linea)
