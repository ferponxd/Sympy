"""
MODELO BASE
Simulación de una caseta de cobro utilizando SimPy.

El modelo representa:

- Llegadas aleatorias de autos
- Una fila
- Un recurso con múltiples servidores
- Tiempo de servicio aleatorio
- Salida del sistema

Conceptos utilizados:

- Environment
- Process
- Resource
- request()
- timeout()
- Variables aleatorias

Métricas calculadas:

W   : tiempo promedio en sistema
Wq  : tiempo promedio en cola
X   : throughput
N   : número promedio en sistema
Nq  : número promedio en cola

También se verifica la Ley de Little.
"""

import simpy
import random
import statistics

# =========================================================
# PARÁMETROS
# =========================================================

RANDOM_SEED = 42

# Tiempo total de simulación
T = 120

# Llegadas promedio
TASA_LLEGADAS = 1 / 3

# Tiempo de pago
TIEMPO_MIN = 1
TIEMPO_MAX = 4

# Número de servidores
NUM_CASETAS = 3

# =========================================================
# CONTADORES
# =========================================================

A = 0  # llegadas
C = 0  # salidas

clientes_en_sistema = 0

Ta = 0
ultimo_evento = 0

tiempos_sistema = []
esperas = []

# =========================================================
# ACTUALIZAR ÁREA
# =========================================================

def actualizar_area(env):

    global Ta
    global ultimo_evento
    global clientes_en_sistema

    delta_t = env.now - ultimo_evento

    Ta += clientes_en_sistema * delta_t

    ultimo_evento = env.now

# =========================================================
# AUTO
# =========================================================

def auto(env, nombre, casetas):

    global A
    global C
    global clientes_en_sistema

    llegada = env.now

    actualizar_area(env)

    clientes_en_sistema += 1
    A += 1

    print(f"{nombre} llega en t={llegada:.2f}")

    # solicitar caseta
    with casetas.request() as turno:

        yield turno

        inicio = env.now

        # tiempo en cola
        espera = inicio - llegada
        esperas.append(espera)

        # tiempo de pago aleatorio
        tiempo_pago = random.uniform(
            TIEMPO_MIN,
            TIEMPO_MAX
        )

        # timeout
        yield env.timeout(tiempo_pago)

        salida = env.now

        tiempo_total = salida - llegada

        tiempos_sistema.append(
            tiempo_total
        )

        actualizar_area(env)

        clientes_en_sistema -= 1

        C += 1

        print(f"{nombre} sale en t={salida:.2f}")

# =========================================================
# GENERADOR DE AUTOS
# =========================================================

def generador(env, casetas):

    i = 0

    while True:

        # tiempo entre llegadas
        dt = random.expovariate(
            TASA_LLEGADAS
        )

        yield env.timeout(dt)

        # detener nuevas llegadas
        if env.now > T:
            break

        i += 1

        env.process(
            auto(
                env,
                f"Auto {i}",
                casetas
            )
        )

# =========================================================
# RESULTADOS
# =========================================================

def resultados():

    print("\n--- RESULTADOS ---")

    W = statistics.mean(
        tiempos_sistema
    )

    Wq = statistics.mean(
        esperas
    )

    # throughput
    X = C / T

    # promedio en sistema
    N = Ta / T

    # promedio en cola
    Nq = X * Wq

    print(f"A (llegadas): {A}")
    print(f"C (salidas): {C}")

    print(f"W: {W:.2f}")
    print(f"Wq: {Wq:.2f}")

    print(f"X: {X:.4f}")

    print(f"N: {N:.2f}")
    print(f"Nq: {Nq:.2f}")

    # Ley de Little
    print("\n--- LEY DE LITTLE ---")

    print(f"N = X × W: {X * W:.2f}")
    print(f"Nq = X × Wq: {X * Wq:.2f}")

# =========================================================
# EJECUCIÓN
# =========================================================

random.seed(RANDOM_SEED)

env = simpy.Environment()

# recurso con 3 servidores
casetas = simpy.Resource(
    env,
    capacity=NUM_CASETAS
)

env.process(
    generador(env, casetas)
)

# tiempo de simulación
env.run(until=T)

# continuar hasta vaciar sistema
while C < A:

    env.run(
        until=env.now + 1
    )

actualizar_area(env)

resultados()