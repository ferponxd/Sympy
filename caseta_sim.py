"""
Simulación de caseta de cobro con múltiples servidores
-----------------------------------------------------

Descripción:
Este programa simula el comportamiento de una caseta 
de cobro similar a la caseta Chamapa-Lechería.

Los autos llegan en tiempos aleatorios, esperan en 
una fila si las casetas están ocupadas, realizan 
el pago y posteriormente salen del sistema.

El modelo utiliza primitivas básicas de SimPy:

- Environment → controla el tiempo
- Process → representa autos
- Resource → representa casetas
- request() → forma la fila
- timeout() → simula el tiempo de pago

Se calculan métricas de desempeño:

W   → tiempo medio en sistema
Wq  → tiempo medio en cola
X   → throughput
N   → número medio en sistema
Nq  → número medio en cola

Finalmente se verifica la Ley de Little:

N  = X × W
Nq = X × Wq

Autor: Fernanda Ponce Maciel
"""

import simpy
import random
import statistics


# =========================================
# PARÁMETROS DEL SISTEMA
# =========================================

RANDOM_SEED = 42

NUM_CASETAS = 2
NUM_AUTOS = 50

TASA_LLEGADAS = 1 / 3

TIEMPO_MIN = 0.5
TIEMPO_MAX = 2.0


# =========================================
# VARIABLES GLOBALES
# =========================================

tiempos_sistema = []
tiempos_cola = []

A = 0   # Llegadas
C = 0   # Salidas

clientes_en_sistema = 0
clientes_en_cola = 0

area_N = 0
area_Nq = 0

ultimo_evento = 0


# =========================================
# FUNCIÓN: actualizar_areas
# =========================================

def actualizar_areas(env):
    """
    Actualiza el área bajo la curva N(t) y Nq(t).

    Esta función se ejecuta cada vez que ocurre 
    un evento importante (llegada o salida).

    El área se utiliza para calcular:

    N  → número medio en sistema
    Nq → número medio en cola
    """

    global area_N
    global area_Nq
    global ultimo_evento
    global clientes_en_sistema
    global clientes_en_cola

    delta_t = env.now - ultimo_evento

    area_N += clientes_en_sistema * delta_t
    area_Nq += clientes_en_cola * delta_t

    ultimo_evento = env.now


# =========================================
# FUNCIÓN: auto
# =========================================

def auto(env, nombre, casetas):
    """
    Representa el comportamiento de un auto.

    Flujo del proceso:

    1. Llega al sistema
    2. Se forma en la fila
    3. Solicita una caseta
    4. Espera si está ocupada
    5. Realiza el pago
    6. Sale del sistema
    """

    global A
    global C
    global clientes_en_sistema
    global clientes_en_cola

    llegada = env.now

    actualizar_areas(env)

    clientes_en_sistema += 1
    clientes_en_cola += 1

    A += 1

    print(f"{nombre} llega en t={llegada:.2f}")

    with casetas.request() as turno:

        yield turno

        actualizar_areas(env)

        clientes_en_cola -= 1

        inicio = env.now

        espera = inicio - llegada
        tiempos_cola.append(espera)

        print(f"{nombre} inicia pago en t={inicio:.2f}")

        # Tiempo de pago aleatorio
        tiempo_pago = random.uniform(
            TIEMPO_MIN,
            TIEMPO_MAX
        )

        yield env.timeout(tiempo_pago)

        salida = env.now

        actualizar_areas(env)

        clientes_en_sistema -= 1

        tiempo_total = salida - llegada
        tiempos_sistema.append(tiempo_total)

        C += 1

        print(f"{nombre} sale en t={salida:.2f}")


# =========================================
# FUNCIÓN: generador
# =========================================

def generador(env, casetas):
    """
    Genera autos que llegan al sistema.

    Los tiempos entre llegadas se generan 
    usando una distribución exponencial.

    Esto permite simular llegadas 
    impredecibles.
    """

    for i in range(NUM_AUTOS):

        dt = random.expovariate(
            TASA_LLEGADAS
        )

        yield env.timeout(dt)

        env.process(
            auto(
                env,
                f"Auto {i+1}",
                casetas
            )
        )


# =========================================
# FUNCIÓN: resultados
# =========================================

def resultados(env):
    """
    Calcula y muestra métricas del sistema.

    Métricas:

    W   → tiempo medio en sistema
    Wq  → tiempo medio en cola
    X   → throughput
    N   → número medio en sistema
    Nq  → número medio en cola

    También verifica la Ley de Little.
    """

    print("\n--- RESULTADOS ---")

    tiempo_total = env.now

    W = statistics.mean(
        tiempos_sistema
    )

    Wq = statistics.mean(
        tiempos_cola
    )

    X = C / tiempo_total

    N = area_N / tiempo_total
    Nq = area_Nq / tiempo_total

    print(f"A (llegadas): {A}")
    print(f"C (salidas): {C}")

    print(f"W: {W:.2f}")
    print(f"Wq: {Wq:.2f}")

    print(f"X (throughput): {X:.4f}")

    print(f"N (en sistema): {N:.2f}")
    print(f"Nq (en cola): {Nq:.2f}")

    print("\n--- LEY DE LITTLE ---")

    print(f"N = X × W: {(X * W):.2f}")
    print(f"Nq = X × Wq: {(X * Wq):.2f}")

    print(
        f"Diferencia N: {abs(N - (X * W)):.4f}"
    )

    print(
        f"Diferencia Nq: {abs(Nq - (X * Wq)):.4f}"
    )


# =========================================
# EJECUCIÓN PRINCIPAL
# =========================================

random.seed(RANDOM_SEED)

env = simpy.Environment()

casetas = simpy.Resource(
    env,
    capacity=NUM_CASETAS
)

env.process(
    generador(env, casetas)
)

env.run()

actualizar_areas(env)

resultados(env)