import asyncio
# Importar funciones de otro archivo
from DATABASE import crear_producto, obtener_producto, actualizar_stock, eliminar_producto

async def prueba_de_estres():
    print("--- Iniciando prueba ---")
    tareas_creacion = [
        crear_producto("M001", "Llanta trasera", 10),
        crear_producto("M002", "Filtro de aire", 25),
        crear_producto("M003", "Bujía", 50),
    ]

    try:
        await asyncio.gather(*tareas_creacion)
        print("Productos creados exitosamente")
    except Exception as e:
        print(f"Error de creación: {e}")

    print("\nActualizar y consultar...")
    try:
        resultado = await asyncio.gather(
            actualizar_stock(8, "M001"),
            obtener_producto("M002")
        )
        print("Operaciones mixtas completadas.")
        print(f" - Update devolvió: {resultado[0]}")
        print(f" - Get devolvió: {resultado[1]}")
    except Exception as e:
        print("Error en operaciones mixtas.")

asyncio.run(prueba_de_estres())
    