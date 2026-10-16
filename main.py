import asyncio
import os
import time

# Importar funciones de otro archivo (el nombre debe coincidir con Database.py)
from DATABASE import ARCHIVO_BD, crear_producto, vender_producto


async def venta_segura(etiqueta, codigo, cantidad, t0):
    """Ejecuta una venta capturando sus errores para que no tumben al gather."""
    try:
        resumen = await vender_producto(codigo, cantidad)
        t = time.perf_counter() - t0
        print(f"[{t:4.1f}s] {etiqueta}: {resumen['nombre']} -> "
              f"quedan {resumen['stock_restante']} unidades")
        return resumen
    except ValueError as e:
        print(f"[{time.perf_counter() - t0:4.1f}s]  {etiqueta}: ValueError atrapado -> {e}")
    except KeyError as e:
        print(f"[{time.perf_counter() - t0:4.1f}s]  {etiqueta}: KeyError atrapado -> {e}")
    except Exception as e:  # cualquier imprevisto tampoco colapsa el programa
        print(f"[{time.perf_counter() - t0:4.1f}s]  {etiqueta}: error inesperado -> {e}")
    return None


async def prueba_de_estres():
    print("--- Iniciando prueba ---")

    # Empezar siempre con una base limpia para que la prueba sea repetible
    if os.path.exists(ARCHIVO_BD):
        os.remove(ARCHIVO_BD)

    try:
        await asyncio.gather(
            crear_producto("M001", "Llanta trasera", 10),
            crear_producto("M002", "Filtro de aire", 25),
            crear_producto("M003", "Bujía", 50),
        )
        print("Productos creados exitosamente")
    except Exception as e:
        print(f"Error de creación: {e}")

    print("\n--- 4 ventas simultáneas ---")
    t0 = time.perf_counter()
    resultados = await asyncio.gather(
        # 1. Venta normal: 50 -> 45 (buen stock)
        venta_segura("Venta normal", "M003", 5, t0),
        # 2. Deja stock <= 2: 10 -> 1 (dispara la alerta en segundo plano)
        venta_segura("Venta stock bajo", "M001", 9, t0),
        # 3. Pide más de lo que hay: 25 < 100 -> ValueError
        venta_segura("Venta excesiva", "M002", 100, t0),
        # 4. Producto inexistente -> KeyError
        venta_segura("Producto inexistente", "M999", 1, t0),
    )
    t_ventas = time.perf_counter() - t0
    exitosas = [r for r in resultados if r is not None]
    print(f"\nVentas terminadas en {t_ventas:.1f}s: "
          f"{len(exitosas)} exitosas, {len(resultados) - len(exitosas)} fallidas")

    # Las alertas corren en segundo plano: antes de cerrar, esperarlas.
    pendientes = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if pendientes:
        print(f"Esperando {len(pendientes)} alerta(s) en segundo plano...")
        await asyncio.gather(*pendientes)

    print(f"Todo terminado en {time.perf_counter() - t0:.1f}s")

asyncio.run(prueba_de_estres())
