// Cuerpo de Yura - ESP32 DevKit V1, conectado a la Raspberry Pi por USB.
//
// Órdenes (una por línea, 115200 baudios):
//   PING                   -> YURA_CUERPO v6
//   ESTADO:<estado>        HABLANDO, ESCUCHANDO, PENSANDO, ESPERANDO... (gestos del cuello)
//   ACCION:<accion>        CELEBRAR_ALEGRE, TRISTE, SALUDAR
//   MOVER:<dir>:<ms>       ADELANTE, ATRAS, IZQUIERDA, DERECHA (gira en el lugar; máx. 3 s)
//   ALTO                   detiene los motores
//   SENSORES:OFF|ON       prueba de motores sin sensores conectados (al reiniciar vuelve a ON)
//   DISTANCIAS             -> DIST <adelante> <izquierda> <derecha> <atras>  (cm, -1 = nada)
//   SERVO:<n>:<grados>     prueba: 1 brazo izq, 2 brazo der, 3 cuello
//   DIAG                   -> DIAG S<n> pin=<p> conectado=<0/1> pulso=<us> periodo=<us> (por servo)
// Responde OK <orden> o ERROR <motivo>.
//
// Seguridad: los motores solo se mueven con MOVER, como máximo 3 s, y se
// detienen ante un obstáculo a menos de 20 cm, con ALTO, o si la Raspberry
// no manda nada en 5 s.
//
// Cargar:  sh cuerpo_esp32/cargar.sh

#include <ESP32Servo.h>
#include <soc/gpio_periph.h>

// ---------------------------------------------------------------- pines (cableado del equipo, 07/10/2026)
#define ENA 13
#define IN1 12   // D12 se lee al arrancar: si el ESP32 no arranca, pasar IN1 a otro pin
#define IN2 14
#define IN3 27
#define IN4 26
#define ENB 25

// Sensores HC-SR04 {trig, echo}: adelante, izquierda, derecha, atrás.
// Echo da 5 V: divisor 1k/2k hacia el ESP32.
const int TRIG[4] = {23, 21, 18, 4};
const int ECHO[4] = {22, 19, 5, 2};

// Servos: brazo izquierdo, brazo derecho, cuello. -1 = no se usa.
// Los brazos estaban en D34/D35 (solo entradas en el ESP32): pasados a D15/D33.
// No usar D16 ni D17: en esta placa cuelgan el ESP32.
const int PIN_SERVO[3] = {15, 33, 32};

// ---------------------------------------------------------------- ajustes
const int VELOCIDAD = 200;
const unsigned long MAX_MOVIMIENTO = 3000;
const int DISTANCIA_MINIMA = 20;
const unsigned long WATCHDOG = 5000;
const int REPOSO[3] = {90, 90, 90};

// ---------------------------------------------------------------- estado
bool usarSensores = true;  // SENSORES:OFF solo para probar motores con los sensores desconectados
Servo servo[3];
int angulo[3] = {90, 90, 90};
String estado = "ESPERANDO", accion = "", movimiento = "", linea = "";
unsigned long inicioAccion = 0, finMovimiento = 0, ultimoMensaje = 0;

// ---------------------------------------------------------------- sensores
int medir(int i) {
  digitalWrite(TRIG[i], LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG[i], HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG[i], LOW);
  unsigned long eco = pulseIn(ECHO[i], HIGH, 25000);
  return eco ? eco / 58 : -1;
}

int sensorHacia(const String &dir) {
  if (dir == "ADELANTE") return 0;
  if (dir == "IZQUIERDA") return 1;
  if (dir == "DERECHA") return 2;
  return 3;
}

bool hayObstaculo(const String &dir) {
  if (!usarSensores) return false;
  int d = medir(sensorHacia(dir));
  return d > 0 && d < DISTANCIA_MINIMA;
}

// ---------------------------------------------------------------- motores
// Motor A (ENA, IN1, IN2) = rueda izquierda; motor B (ENB, IN3, IN4) = rueda derecha.
void ruedas(int izq, int der) {  // 1 adelante, -1 atrás, 0 quieta
  digitalWrite(IN1, izq > 0);
  digitalWrite(IN2, izq < 0);
  digitalWrite(IN3, der > 0);
  digitalWrite(IN4, der < 0);
  analogWrite(ENA, izq ? VELOCIDAD : 0);
  analogWrite(ENB, der ? VELOCIDAD : 0);
}

void alto() {
  movimiento = "";
  ruedas(0, 0);
}

void mover() {
  if (movimiento == "") return;
  if (millis() > finMovimiento || hayObstaculo(movimiento)) {
    alto();
    return;
  }
  if (movimiento == "ADELANTE") ruedas(1, 1);
  else if (movimiento == "ATRAS") ruedas(-1, -1);
  else if (movimiento == "IZQUIERDA") ruedas(-1, 1);
  else ruedas(1, -1);
}

// ---------------------------------------------------------------- servos
void ponerServo(int n, int grados) {
  angulo[n] = constrain(grados, 0, 180);
  if (PIN_SERVO[n] >= 0) servo[n].write(n == 1 ? 180 - angulo[n] : angulo[n]);  // brazo derecho espejado
}

// Acerca cada servo a su meta de a poco (gestos suaves).
void postura(int izq, int der, int cab) {
  int meta[3] = {izq, der, cab};
  for (int n = 0; n < 3; n++) ponerServo(n, angulo[n] + constrain(meta[n] - angulo[n], -3, 3));
}

bool fase(unsigned long periodo) { return (millis() / periodo) % 2; }

void gestos() {
  unsigned long t = millis() - inicioAccion;
  if (accion != "" && t < 2500) {
    if (accion == "CELEBRAR_ALEGRE") postura(fase(400) ? 20 : 70, fase(400) ? 20 : 70, fase(400) ? 100 : 80);
    else if (accion == "TRISTE") postura(90, 90, fase(700) ? 110 : 70);
    else if (accion == "SALUDAR") postura(90, fase(300) ? 20 : 50, 90);
    return;  // SERVO: se queda en la posición de prueba
  }
  accion = "";
  if (estado == "HABLANDO") postura(80, fase(700) ? 65 : 80, fase(600) ? 98 : 82);
  else if (estado == "ESCUCHANDO") postura(90, 90, 78);
  else if (estado == "PENSANDO") postura(90, 50, 105);
  else postura(REPOSO[0], REPOSO[1], REPOSO[2]);
}

// ---------------------------------------------------------------- órdenes
void responder(const String &orden) {
  if (orden == "PING") { Serial.println("YURA_CUERPO v6"); return; }
  if (orden == "DIAG") {
    // Mide la señal que sale de verdad por cada pin de servo (50 Hz, 500-2400 us).
    for (int n = 0; n < 3; n++) {
      int p = PIN_SERVO[n];
      if (p < 0) { Serial.printf("DIAG S%d sin pin\n", n + 1); continue; }
      PIN_INPUT_ENABLE(GPIO_PIN_MUX_REG[p]);  // leer el pin sin quitarle la salida PWM
      unsigned long alto = pulseIn(p, HIGH, 50000), bajo = pulseIn(p, LOW, 50000);
      Serial.printf("DIAG S%d pin=%d conectado=%d pulso=%lu periodo=%lu\n", n + 1, p, servo[n].attached(), alto, alto + bajo);
    }
    return;
  }
  if (orden == "DISTANCIAS") {
    Serial.printf("DIST %d %d %d %d\n", medir(0), medir(1), medir(2), medir(3));
    return;
  }
  if (orden == "ALTO") alto();
  else if (orden == "SENSORES:OFF") { usarSensores = false; alto(); }
  else if (orden == "SENSORES:ON") usarSensores = true;
  else if (orden.startsWith("ESTADO:")) estado = orden.substring(7);
  else if (orden.startsWith("ACCION:")) { accion = orden.substring(7); inicioAccion = millis(); }
  else if (orden.startsWith("MOVER:")) {
    int dos = orden.indexOf(':', 6);
    String dir = dos > 0 ? orden.substring(6, dos) : orden.substring(6);
    unsigned long ms = dos > 0 ? orden.substring(dos + 1).toInt() : 1000;
    if (dir != "ADELANTE" && dir != "ATRAS" && dir != "IZQUIERDA" && dir != "DERECHA") { Serial.println("ERROR direccion"); return; }
    if (hayObstaculo(dir)) { Serial.println("ERROR obstaculo"); return; }
    movimiento = dir;
    finMovimiento = millis() + min(ms, MAX_MOVIMIENTO);
  } else if (orden.startsWith("SERVO:")) {
    int n = orden.substring(6, 7).toInt() - 1;
    if (n < 0 || n > 2) { Serial.println("ERROR servo"); return; }
    if (PIN_SERVO[n] < 0) { Serial.println("ERROR servo sin pin de salida"); return; }
    ponerServo(n, orden.substring(8).toInt());
    accion = "SERVO";
    inicioAccion = millis();
  } else { Serial.println("ERROR orden"); return; }
  Serial.println("OK " + orden);
}

void leerOrdenes() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      linea.trim();
      if (linea.length()) { ultimoMensaje = millis(); responder(linea); }
      linea = "";
    } else if (c >= ' ' && c <= '~' && linea.length() < 64) {
      linea += c;  // solo texto: el ruido eléctrico no forma órdenes
    }
  }
}

// ---------------------------------------------------------------- inicio
void setup() {
  int motores[] = {ENA, IN1, IN2, IN3, IN4, ENB};
  for (int p : motores) { pinMode(p, OUTPUT); digitalWrite(p, LOW); }  // quietos al encender
  for (int i = 0; i < 4; i++) { pinMode(TRIG[i], OUTPUT); pinMode(ECHO[i], INPUT); }
  ESP32PWM::allocateTimer(0);  // temporizadores PWM para los servos
  ESP32PWM::allocateTimer(1);
  for (int n = 0; n < 3; n++) {
    if (PIN_SERVO[n] < 0) continue;
    servo[n].setPeriodHertz(50);
    servo[n].attach(PIN_SERVO[n], 500, 2400);
  }
  for (int n = 0; n < 3; n++) ponerServo(n, REPOSO[n]);
  Serial.begin(115200);
  ultimoMensaje = millis();
  Serial.println("YURA_CUERPO v6 listo");
}

void loop() {
  leerOrdenes();
  mover();
  if (millis() - ultimoMensaje > WATCHDOG) alto();  // sin Raspberry, nada se mueve
  gestos();
  delay(15);
}
