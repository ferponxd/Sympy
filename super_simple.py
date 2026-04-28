"""
MODELO BASE: Cola M/M/1 (Servidor único)

Descripción:
Este programa simula un sistema de colas con un solo servidor
(M/M/1). Los clientes llegan en tiempos aleatorios, esperan si el
servidor está ocupado y son atendidos posteriormente.

Modelo:
Una fila única
Un servidor
Llegadas exponenciales
Servicio exponencial

Se calculan las siguientes métricas:

T   : tiempo total de observación
A   : número total de llegadas
C   : número total de salidas
Ta  : área acumulada bajo N(t)

X   : throughput = C / T
W   : tiempo medio en sistema
Wq  : tiempo medio en cola

N   : número medio en sistema = Ta / T
Nq  : número medio en cola = X × Wq

Condición de término:
La simulación continúa hasta que A = C
(todos los clientes que llegaron han salido).

Autor: Fernanda Ponce Maciel
Modelo: M/M/1
"""

import simpy
import random
import statistics


# =========================================
# PARÁMETROS
# =========================================

RANDOM_SEED = 42

T = 120  # tiempo de simulación

TASA_LLEGADAS = 1 / 3
TIEMPO_SERVICIO_PROM = 2


# =========================================
# CONTADORES
# =========================================

A = 0
C = 0

clientes_en_sistema = 0

Ta = 0
ultimo_evento = 0

tiempos_sistema = []
esperas = []


# =========================================
# FUNCIÓN: actualizar_area
# =========================================

def actualizar_area(env):
    """
    Actualiza el área acumulada bajo N(t).

    Esta función calcula el área bajo la curva
    del número de clientes en el sistema.

    Se utiliza para calcular:

        N = Ta / T
    """

    global Ta
    global ultimo_evento
    global clientes_en_sistema

    delta_t = env.now - ultimo_evento

    Ta += clientes_en_sistema * delta_t

    ultimo_evento = env.now


# =========================================
# PROCESO: cliente
# =========================================

def cliente(env, nombre, servidor):
    """
    Representa el comportamiento de un cliente.

    Flujo del cliente:

    1. Llega al sistema
    2. Espera si el servidor está ocupado
    3. Recibe servicio
    4. Sale del sistema
    """

    global A
    global C
    global clientes_en_sistema

    llegada = env.now

    actualizar_area(env)

    clientes_en_sistema += 1
    A += 1

    print(f"{nombre} llega en t={llegada:.2f}")

    with servidor.request() as turno:

        yield turno

        inicio = env.now

        espera = inicio - llegada
        esperas.append(espera)

        tiempo_servicio = random.expovariate(
            1 / TIEMPO_SERVICIO_PROM
        )

        yield env.timeout(tiempo_servicio)

        salida = env.now

        tiempo_total = salida - llegada
        tiempos_sistema.append(tiempo_total)

        actualizar_area(env)

        clientes_en_sistema -= 1

        C += 1

        print(f"{nombre} sale en t={salida:.2f}")


# =========================================
# GENERADOR DE CLIENTES
# =========================================

def generador(env, servidor):
    """
    Genera clientes en tiempos aleatorios.

    El tiempo entre llegadas sigue
    una distribución exponencial.
    """

    i = 0

    while True:

        dt = random.expovariate(
            TASA_LLEGADAS
        )

        yield env.timeout(dt)

        if env.now > T:
            break

        i += 1

        env.process(
            cliente(env, f"Cliente {i}", servidor)
        )


# =========================================
# RESULTADOS
# =========================================

def resultados():
    """
    Calcula métricas del sistema
    y verifica la Ley de Little.
    """

    print("\n--- RESULTADOS ---")

    W = statistics.mean(tiempos_sistema)
    Wq = statistics.mean(esperas)

    X = C / T

    N = Ta / T
    Nq = X * Wq

    N_little = X * W

    print(f"A (llegadas): {A}")
    print(f"C (salidas): {C}")

    print(f"W: {W:.2f}")
    print(f"Wq: {Wq:.2f}")

    print(f"X: {X:.4f}")

    print(f"N: {N:.2f}")
    print(f"Nq: {Nq:.2f}")

    print("\n--- LEY DE LITTLE ---")

    print(f"N = X × W: {N_little:.2f}")

    print(
        f"Diferencia N: {abs(N - N_little):.2f}"
    )


# =========================================
# EJECUCIÓN PRINCIPAL
# =========================================

random.seed(RANDOM_SEED)

env = simpy.Environment()

servidor = simpy.Resource(
    env,
    capacity=1
)

env.process(
    generador(env, servidor)
)

env.run(until=T)

# continuar hasta vaciar sistema

while C < A:
    env.run(until=env.now + 1)

actualizar_area(env)

resultados()