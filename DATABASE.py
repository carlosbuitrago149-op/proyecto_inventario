import json
import aiofiles
import asyncio

ARCHIVO_BD = "inventario.json"
db_lock = asyncio.Lock()


async def leer_base_datos():
    try:
        async with aiofiles.open(ARCHIVO_BD, mode="r", encoding="utf-8") as f:
            contenido = await f.read()
            return json.loads(contenido)
    except FileNotFoundError:
        return []  # Lista vacía


async def guardar_base_datos(datos):
    async with aiofiles.open(ARCHIVO_BD, mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(datos, indent=4))


# === CREATE === Post
async def crear_producto(codigo, nombre, stock):
    async with db_lock:
        await asyncio.sleep(0.5)  # Simular latencia
        datos = await leer_base_datos()

        for dato in datos:
            if dato["codigo"] == codigo:
                raise ValueError(f"El producto con el código {codigo} ya existe.")

        nuevo_producto = {"codigo": codigo, "nombre": nombre, "stock": stock}
        datos.append(nuevo_producto)
        await guardar_base_datos(datos)
        return nuevo_producto


# === READ === Get
async def obtener_producto(codigo):
    async with db_lock:
        await asyncio.sleep(0.2)
        datos = await leer_base_datos()
        for dato in datos:
            if dato["codigo"] == codigo:
                return dato
        raise KeyError(f"Producto {codigo} no ha sido encontrado.")


# === UPDATE === Put
async def actualizar_stock(nuevo_stock, codigo):
    async with db_lock:
        await asyncio.sleep(0.5)
        datos = await leer_base_datos()
        for dato in datos:
            if dato["codigo"] == codigo:
                dato["stock"] = nuevo_stock
                await guardar_base_datos(datos)
                return dato
        raise KeyError(f"Producto {codigo} no ha sido encontrado.")


# === DELETE ===
async def eliminar_producto(codigo):
    async with db_lock:
        await asyncio.sleep(0.5)
        datos = await leer_base_datos()

        nuevos_datos = [dato for dato in datos if dato["codigo"] != codigo]

        if len(datos) == len(nuevos_datos):
            raise KeyError(f"Producto {codigo} no ha sido encontrado.")

        await guardar_base_datos(nuevos_datos)
        return True


# === alerta en segundo plano ===
UMBRAL_STOCK_BAJO = 3


async def alerta_stock_bajo(codigo, nombre, stock_actual):
    """Simula el envío de un correo al administrador (tarda 2 segundos)."""
    await asyncio.sleep(2)  # Simula el envío del correo
    print("\n" + "=" * 70)
    print(f"⚠️ ALERTA CRÍTICA: El producto {nombre} ({codigo}) ha bajado a "
          f"{stock_actual} unidades. Solicitar restock inmediato.")
    print("=" * 70 + "\n")


# === VENTA ===
async def vender_producto(codigo, cantidad_vendida):
    # El lock cubre leer -> validar -> guardar, para que dos ventas
    # simultáneas no lean el mismo stock y se pisen entre sí.
    async with db_lock:
        await asyncio.sleep(0.5)  # Simular latencia

        # 1. Búsqueda
        datos = await leer_base_datos()
        producto = next((p for p in datos if p["codigo"] == codigo), None)
        if producto is None:
            raise KeyError("Producto no encontrado")

        # 2. Validación
        if cantidad_vendida > producto["stock"]:
            raise ValueError("Stock insuficiente")

        # 3. Actualización: restar lo vendido y guardar
        producto["stock"] -= cantidad_vendida
        await guardar_base_datos(datos)

        nombre = producto["nombre"]
        stock_resultante = producto["stock"]

    # 4. Disparador de alerta (fuera del lock, en segundo plano):
    #    el cliente no espera los 2 s del "correo".
    if stock_resultante < UMBRAL_STOCK_BAJO:
        asyncio.create_task(alerta_stock_bajo(codigo, nombre, stock_resultante))

    # 5. Retorno
    return {
        "codigo": codigo,
        "nombre": nombre,
        "cantidad_vendida": cantidad_vendida,
        "stock_restante": stock_resultante,
        "estado": "Venta exitosa",
    }