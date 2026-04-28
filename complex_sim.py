"""
MODELO COMPLEJO: Supermercado con 2 cajas

Descripción:
Este programa simula un sistema de colas con
dos servidores (cajas).

Cada cliente llega con un número aleatorio
de productos, y el tiempo de servicio depende
del número de productos.

Modelo:
Una fila única
Dos servidores
Tiempo de servicio variable

Se calculan:

A   : llegadas
C   : salidas
Ta  : área acumulada

X   : throughput
W   : tiempo medio en sistema
Wq  : tiempo medio en cola

N   : número medio en sistema
Nq  : número medio en cola

Condición de término:
La simulación termina cuando A = C.

Autor: Fernanda Ponce Maciel
Modelo: M/M/2 con servicio dependiente de productos
"""

import simpy
import random
import statistics


# =========================================
# PARÁMETROS
# =========================================

RANDOM_SEED = 42

T = 120

TASA_LLEGADAS = 1 / 2.2

PRODUCTOS_MIN = 1
PRODUCTOS_MAX = 25

TIEMPO_MIN_PRODUCTO = 0.12
TIEMPO_MAX_PRODUCTO = 0.30

NUM_CAJAS = 2


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
# ACTUALIZAR ÁREA
# =========================================

def actualizar_area(env):
    """
    Actualiza el área bajo la curva N(t).
    """

    global Ta
    global ultimo_evento
    global clientes_en_sistema

    delta_t = env.now - ultimo_evento

    Ta += clientes_en_sistema * delta_t

    ultimo_evento = env.now


# =========================================
# CLIENTE
# =========================================

def cliente(env, nombre, cajas):
    """
    Representa un cliente del supermercado.

    El tiempo de servicio depende
    del número de productos.
    """

    global A
    global C
    global clientes_en_sistema

    llegada = env.now

    actualizar_area(env)

    clientes_en_sistema += 1
    A += 1

    productos = random.randint(
        PRODUCTOS_MIN,
        PRODUCTOS_MAX
    )

    print(
        f"{nombre} llega con {productos} productos "
        f"en t={llegada:.2f}"
    )

    with cajas.request() as turno:

        yield turno

        inicio = env.now

        espera = inicio - llegada
        esperas.append(espera)

        tiempo_por_producto = random.uniform(
            TIEMPO_MIN_PRODUCTO,
            TIEMPO_MAX_PRODUCTO
        )

        tiempo_servicio = (
            productos * tiempo_por_producto
        )

        yield env.timeout(tiempo_servicio)

        salida = env.now

        tiempo_total = salida - llegada
        tiempos_sistema.append(tiempo_total)

        actualizar_area(env)

        clientes_en_sistema -= 1

        C += 1

        print(
            f"{nombre} sale en t={salida:.2f}"
        )


# =========================================
# GENERADOR
# =========================================

def generador(env, cajas):
    """
    Genera clientes aleatorios.
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
            cliente(
                env,
                f"Cliente {i}",
                cajas
            )
        )


# =========================================
# RESULTADOS
# =========================================

def resultados():
    """
    Calcula métricas y verifica Ley de Little.
    """

    print("\n--- RESULTADOS ---")

    W = statistics.mean(
        tiempos_sistema
    )

    Wq = statistics.mean(
        esperas
    )

    X = C / T

    N = Ta / T
    Nq = X * Wq

    N_little = X * W

    print(f"A: {A}")
    print(f"C: {C}")

    print(f"W: {W:.2f}")
    print(f"Wq: {Wq:.2f}")

    print(f"X: {X:.4f}")

    print(f"N: {N:.2f}")
    print(f"Nq: {Nq:.2f}")

    print("\n--- LEY DE LITTLE ---")

    print(f"N = X × W: {N_little:.2f}")

    print(
        f"Diferencia N: "
        f"{abs(N - N_little):.2f}"
    )


# =========================================
# EJECUCIÓN
# =========================================

random.seed(RANDOM_SEED)

env = simpy.Environment()

cajas = simpy.Resource(
    env,
    capacity=NUM_CAJAS
)

env.process(
    generador(env, cajas)
)

env.run(until=T)

while C < A:
    env.run(until=env.now + 1)

actualizar_area(env)

resultados()