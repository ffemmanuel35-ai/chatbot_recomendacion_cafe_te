import streamlit as st
import re
import random
import base64
import json
import requests
from datetime import datetime

# -----------------------------------------
# CONFIGURACIÓN STREAMLIT
# -----------------------------------------
st.set_page_config(page_title="Asistente de Café/Té", page_icon="☕", layout="centered")
st.title("☕ Tienda Café & Té — Asistente de Compra")

st.markdown("""
Te ayudo a elegir y comprar café o té.  
Puedo recomendar productos según **sabor**, **intensidad** o **tipo**,  
y puedo recordar tus **preferencias** y **tu nombre**.  
""")

# -----------------------------------------
# CONFIGURACIÓN GITHUB PARA GUARDAR PEDIDOS
# -----------------------------------------
GITHUB_REPO = "ffemmanuel35-ai/chatbot_recomendacion_cafe_te"
FILE_PATH = "pedidos.jsonl"
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

def guardar_pedido_en_github(pedido):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        data = resp.json()
        sha = data["sha"]
        contenido_actual = base64.b64decode(data["content"]).decode("utf-8")
    elif resp.status_code == 404:
        sha = None
        contenido_actual = ""
    else:
        st.error(f"Error al acceder al archivo: {resp.text}")
        return

    nueva_linea = json.dumps(pedido, ensure_ascii=False)
    nuevo_contenido = contenido_actual.rstrip() + "\n" + nueva_linea + "\n"

    update_data = {
        "message": f"Nuevo pedido agregado - {pedido['codigo']}",
        "content": base64.b64encode(nuevo_contenido.encode("utf-8")).decode("utf-8")
    }

    if sha:
        update_data["sha"] = sha

    update_resp = requests.put(url, headers=headers, data=json.dumps(update_data))

    if update_resp.status_code in (200, 201):
        st.success("✅ Pedido guardado correctamente en GitHub.")
    else:
        st.error(f"⚠ Error al guardar en GitHub: {update_resp.text}")

# -----------------------------------------
# SISTEMA DE MÉTODOS DE PAGO
# -----------------------------------------
METODOS_PAGO = {
    "tarjeta_credito": {
        "nombre": "💳 Tarjeta de Crédito",
        "instrucciones": "Procesamiento seguro con MercadoPago",
        "requiere_datos": True
    },
    "tarjeta_debito": {
        "nombre": "💳 Tarjeta de Débito", 
        "instrucciones": "Pago inmediato con cualquier banco",
        "requiere_datos": True
    },
    "transferencia": {
        "nombre": "📲 Transferencia",
        "instrucciones": "CBU: 0000000000000000000 - Alias: tienda.cafe.te",
        "requiere_datos": False
    },
    "billetera_virtual": {
        "nombre": "📱 Billetera Virtual",
        "instrucciones": "MercadoPago, Ualá, o Modo",
        "requiere_datos": False
    }
}

def mostrar_metodos_pago():
    """Muestra la interfaz de selección de métodos de pago"""
    st.markdown("### 💰 Seleccioná tu método de pago")
    
    metodo_seleccionado = st.radio(
        "Elegí cómo querés pagar:",
        options=list(METODOS_PAGO.keys()),
        format_func=lambda x: METODOS_PAGO[x]["nombre"],
        key="metodo_pago_seleccionado"
    )
    
    if metodo_seleccionado:
        metodo = METODOS_PAGO[metodo_seleccionado]
        st.info(f"**{metodo['nombre']}**: {metodo['instrucciones']}")
        
        if metodo["requiere_datos"]:
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Número de tarjeta", placeholder="1234 5678 9012 3456", key="num_tarjeta")
                st.text_input("Nombre en la tarjeta", placeholder="JUAN PEREZ", key="nombre_tarjeta")
            with col2:
                col21, col22 = st.columns(2)
                with col21:
                    st.text_input("MM/AA", placeholder="12/25", key="vencimiento")
                with col22:
                    st.text_input("CVV", placeholder="123", key="cvv", type="password")
    
    return metodo_seleccionado

def procesar_pago(metodo, total, datos_pago=None):
    """Simula el procesamiento del pago"""
    codigo_pago = f"PAY{random.randint(10000, 99999)}"
    
    resultado = {
        "exitoso": True,
        "codigo": codigo_pago,
        "metodo": metodo,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": total
    }
    
    return resultado

# -----------------------------------------
# MEMORIA DE SESIÓN MEJORADA
# -----------------------------------------
if "mem" not in st.session_state:
    st.session_state.mem = {
        "nombre": None,  # Cambiado a None para forzar la obtención del nombre
        "preferencia": None,
        "producto_seleccionado": None,
        "cantidad": None,
        "estado_pago": None,
        "metodo_pago": None,
        "ultimo_pedido": None,
        "total_pendiente": None
    }

mem = st.session_state.mem

# -----------------------------------------
# CATÁLOGO
# -----------------------------------------
catalogo = {
    "café de colombia": {"tipo": "café", "perfil": "cítrico", "precio": 1200},
    "café peruano andes": {"tipo": "café", "perfil": "cítrico", "precio": 1250},
    "café espresso italiano": {"tipo": "café", "perfil": "intenso", "precio": 1100},
    "café dark roast brasil": {"tipo": "café", "perfil": "intenso", "precio": 1300},
    "café arábica light roast": {"tipo": "café", "perfil": "suave", "precio": 1000},
    "café colombiano especial": {"tipo": "café", "perfil": "suave", "precio": 1150},
    "té blanco con jazmín": {"tipo": "té", "perfil": "floral", "precio": 800},
    "té oolong floral blend": {"tipo": "té", "perfil": "floral", "precio": 850},
    "té rooibos con vainilla": {"tipo": "té", "perfil": "dulce", "precio": 750},
    "té negro miel & canela": {"tipo": "té", "perfil": "dulce", "precio": 790},
    "té verde sencha": {"tipo": "té", "perfil": "herbal", "precio": 780},
    "té menta patagónica": {"tipo": "té", "perfil": "herbal", "precio": 760},
}

# -----------------------------------------
# EXTRACCIÓN DE NOMBRE MEJORADA
# -----------------------------------------
def extraer_nombre(texto):
    """Extrae nombres reales, evitando palabras comunes"""
    texto = texto.strip().lower()
    
    # Lista de palabras que NO son nombres (comandos comunes)
    palabras_no_nombres = {
        "catálogo", "catalogo", "ayuda", "hola", "comprar", "compra", 
        "quiero", "deseo", "cafe", "café", "te", "té", "otro", "otra",
        "si", "sí", "no", "gracias", "help", "menu", "menú", "pagar",
        "intenso", "suave", "cítrico", "floral", "dulce", "herbal"
    }
    
    # Si es una palabra común, no es un nombre
    if texto in palabras_no_nombres:
        return None
    
    patrones = [
        r"soy\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ]{2,})",
        r"me\s+llamo\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ]{2,})",
        r"mi\s+nombre\s+es\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ]{2,})"
    ]
    
    for p in patrones:
        m = re.search(p, texto, re.IGNORECASE)
        if m:
            nombre = m.group(1).capitalize()
            # Verificar que no sea una palabra común
            if nombre.lower() not in palabras_no_nombres and len(nombre) >= 2:
                return nombre
    
    # Solo considerar como nombre si es una sola palabra y no es común
    if len(texto.split()) == 1 and texto.isalpha() and texto not in palabras_no_nombres and len(texto) >= 2:
        return texto.capitalize()
    
    return None

# -----------------------------------------
# RECOMENDADOR
# -----------------------------------------
def recomendar_por_perfil(preferencia, actual=None):
    preferencia = preferencia.lower()
    opciones = [(n, d) for n, d in catalogo.items() if preferencia in d["perfil"].lower()]
    if not opciones:
        return None, None
    if actual:
        for nombre, datos in opciones:
            if nombre != actual:
                return nombre, datos
    return opciones[0]

# -----------------------------------------
# LÓGICA DEL CHATBOT MEJORADA - MANTIENE EL NOMBRE
# -----------------------------------------
def procesar(texto):
    texto_l = texto.lower().strip()

    # 1) OBTENER NOMBRE - PRIORIDAD AL INICIO
    if mem["nombre"] is None:
        posible = extraer_nombre(texto)
        if posible:
            mem["nombre"] = posible
            return f"¡Encantado, **{mem['nombre']}**! 😊 ¿Preferís café o té?"
        else:
            # Si no es un nombre, pero es un comando, pedir nombre primero
            comandos_permitidos = {"ayuda", "help", "qué puedes hacer"}
            if texto_l not in comandos_permitidos:
                return "¡Hola! Para comenzar, ¿podrías decirme tu nombre? 😊"

    # 2) Mostrar catálogo - FUNCIONA SOLO CON NOMBRE
    if "catálogo" in texto_l or "catalogo" in texto_l:
        if mem["nombre"] is None:
            return "Primero decime tu nombre para poder mostrarte el catálogo 😊"
        cat = "\n".join([f"- **{n.title()}** — {d['perfil']} — ${d['precio']}" for n, d in catalogo.items()])
        return f"📜 **Catálogo disponible:**\n\n{cat}"

    # 3) Ayuda - FUNCIONA INMEDIATAMENTE
    if any(palabra in texto_l for palabra in ["ayuda", "help", "qué puedes hacer"]):
        return ("**Puedo ayudarte con:**\n\n• Recomendarte café o té según tu gusto\n• Mostrarte el catálogo completo\n" 
               "• Tomar tu pedido y procesar el pago\n• Recordar tus preferencias\n\n¡Decime qué necesitás! 😊")

    # 4) Preferencias por perfil - FUNCIONA SOLO CON NOMBRE
    perfiles = ["floral", "dulce", "herbal", "intenso", "suave", "cítrico", "citric"]
    for p in perfiles:
        if p in texto_l:
            if mem["nombre"] is None:
                return "Primero decime tu nombre para poder recomendarte productos 😊"
            if p == "citric":
                p = "cítrico"
            mem["preferencia"] = p
            nombre, datos = recomendar_por_perfil(p)
            if nombre:
                mem["producto_seleccionado"] = nombre
                return (f"Te recomiendo **{nombre.title()}** — perfil *{datos['perfil']}* — "
                       f"Precio: **${datos['precio']}**.\n\n¿Lo querés o querés otra opción?")

    # 5) Otra opción
    if any(p in texto_l for p in ["otro", "otra", "otra opción", "quiero otra", "mostrame otro"]):
        if mem["nombre"] is None:
            return "Primero decime tu nombre para poder ayudarte 😊"
        if mem["preferencia"]:
            actual = mem["producto_seleccionado"]
            nombre, datos = recomendar_por_perfil(mem["preferencia"], actual)
            if nombre:
                mem["producto_seleccionado"] = nombre
                return (f"Probá esta alternativa:\n\n**{nombre.title()}** — {datos['perfil']} — **${datos['precio']}**\n"
                       f"¿Te gusta?")
        return "¿Preferís café o té?"

    # 6) Selección por nombre
    for prod in catalogo.keys():
        if prod in texto_l:
            if mem["nombre"] is None:
                return "Primero decime tu nombre para poder tomar tu pedido 😊"
            mem["producto_seleccionado"] = prod
            return f"Perfecto {mem['nombre']}. ¿Cuántas unidades querés?"

    # 7) Confirmación
    if texto_l in ["si", "sí", "si quiero", "lo quiero", "lo deseo", "dale", "meta", "quiero"] and mem["producto_seleccionado"]:
        if mem["nombre"] is None:
            return "Primero decime tu nombre para poder continuar con tu compra 😊"
        return "Perfecto 😊 ¿Cuántas unidades querés comprar?"

    # 8) Cantidad
    if texto_l.isdigit() and mem["producto_seleccionado"]:
        if mem["nombre"] is None:
            return "Primero decime tu nombre para poder procesar tu pedido 😊"
        mem["cantidad"] = int(texto_l)
        prod = mem["producto_seleccionado"]
        precio = catalogo[prod]["precio"]
        subtotal = precio * mem["cantidad"]
        return (f"Perfecto {mem['nombre']}:\n**{mem['cantidad']} x {prod.title()}** — Subtotal **${subtotal}**.\n"
               f"Escribí **'comprar'** o **'confirmo'** para finalizar.")

    # 9) Confirmar compra
    if texto_l in ["comprar", "confirmo"] and mem["producto_seleccionado"] and mem["cantidad"]:
        if mem["nombre"] is None:
            return "Primero decime tu nombre para poder finalizar tu compra 😊"
        prod = mem["producto_seleccionado"]
        cantidad = mem["cantidad"]
        precio = catalogo[prod]["precio"]
        total = precio * cantidad
        mem["estado_pago"] = "pendiente"
        mem["total_pendiente"] = total
        return (f"🛒 **Resumen de tu pedido {mem['nombre']}:**\n\n**Producto:** {prod.title()}\n**Cantidad:** {cantidad} unidades\n"
               f"**Total a pagar:** ${total}\n\nAhora necesitamos procesar el pago. Seleccioná tu método de pago aquí abajo 👇")

    # 10) Preguntas base - FUNCIONAN SOLO CON NOMBRE
    if "café" in texto_l or "cafe" in texto_l:
        if mem["nombre"] is None:
            return "Primero decime tu nombre para poder recomendarte cafés 😊"
        return "¿Buscás algo intenso, suave o cítrico?"
    if "té" in texto_l or "te" in texto_l:
        if mem["nombre"] is None:
            return "Primero decime tu nombre para poder recomendarte tés 😊"
        return "¿Preferís algo floral, herbal o dulce?"

    # 11) Saludo
    if any(palabra in texto_l for palabra in ["hola", "hi", "hey"]):
        if mem["nombre"]:
            return f"¡Hola {mem['nombre']}! 😊 ¿En qué puedo ayudarte?"
        else:
            return "¡Hola! ¿Podrías decirme tu nombre para comenzar? 😊"

    return "No estoy seguro de haber entendido. ¿Querés ver el catálogo o buscás café o té?"

# -----------------------------------------
# INTERFAZ MEJORADA - BOTONES FUNCIONALES
# -----------------------------------------

# Botones de acción rápida
col1, col2, col3 = st.columns(3)

if col1.button("📜 Ver Catálogo", use_container_width=True):
    st.session_state.historial.append({"role": "user", "content": "catálogo"})
    respuesta = procesar("catálogo")
    st.session_state.historial.append({"role": "assistant", "content": respuesta})
    st.rerun()

if col2.button("🛒 Comprar", use_container_width=True):
    st.session_state.historial.append({"role": "user", "content": "quiero comprar"})
    respuesta = procesar("quiero comprar")
    st.session_state.historial.append({"role": "assistant", "content": respuesta})
    st.rerun()

if col3.button("❓ Ayuda", use_container_width=True):
    st.session_state.historial.append({"role": "user", "content": "ayuda"})
    respuesta = procesar("ayuda")
    st.session_state.historial.append({"role": "assistant", "content": respuesta})
    st.rerun()

# Inicializar historial si no existe
if "historial" not in st.session_state:
    st.session_state.historial = [
        {"role": "assistant", "content": "¡Hola! Soy tu asistente de café y té. ¿Podrías decirme tu nombre para comenzar? 😊"}
    ]

# Input de chat
user_msg = st.chat_input("Escribí tu mensaje...")

if user_msg:
    st.session_state.historial.append({"role": "user", "content": user_msg})
    respuesta = procesar(user_msg)
    st.session_state.historial.append({"role": "assistant", "content": respuesta})
    st.rerun()

# Mostrar historial de chat
st.markdown("---")
for msg in st.session_state.historial:
    if msg["role"] == "user":
        st.markdown(f"🧑‍💬 **Tú:** {msg['content']}")
    else:
        st.markdown(f"🤖 **Asistente:** {msg['content']}")

# -----------------------------------------
# SECCIÓN DE PAGOS (ABAJO DEL CHAT)
# -----------------------------------------
if mem["estado_pago"] == "pendiente":
    st.markdown("---")
    st.markdown("## 💳 Procesar Pago")
    
    metodo = mostrar_metodos_pago()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("✅ Confirmar Pago", type="primary", use_container_width=True):
            if metodo:
                with st.spinner("Procesando tu pago..."):
                    resultado = procesar_pago(metodo, mem["total_pendiente"])
                    if resultado["exitoso"]:
                        codigo_pedido = f"PED{random.randint(10000,99999)}"
                        pedido_completo = {
                            "codigo": codigo_pedido,
                            "nombre": mem["nombre"],  # EL NOMBRE SE MANTIENE HASTA EL FINAL
                            "producto": mem["producto_seleccionado"],
                            "cantidad": mem["cantidad"],
                            "total": mem["total_pendiente"],
                            "metodo_pago": metodo,
                            "nombre_metodo_pago": METODOS_PAGO[metodo]["nombre"],
                            "codigo_pago": resultado["codigo"],
                            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "estado": "completado"
                        }
                        guardar_pedido_en_github(pedido_completo)
                        
                        # GUARDAR EL NOMBRE PARA EL MENSAJE FINAL
                        nombre_cliente = mem["nombre"]
                        
                        # LIMPIAR SOLO LOS DATOS TEMPORALES, MANTENER EL NOMBRE
                        mem.update({
                            "producto_seleccionado": None,
                            "cantidad": None,
                            "estado_pago": None,
                            "ultimo_pedido": codigo_pedido,
                            "metodo_pago": None,
                            "total_pendiente": None
                            # NO LIMPIAMOS EL NOMBRE - SE MANTIENE PARA FUTURAS INTERACCIONES
                        })
                        
                        # AGREGAR MENSAJE DE AGRADECIMIENTO PERSONALIZADO AL HISTORIAL
                        mensaje_agradecimiento = f"✅ **¡Compra confirmada {nombre_cliente}!** Pedido **{codigo_pedido}** procesado exitosamente. ¡Gracias por su compra! 🎉"
                        st.session_state.historial.append({"role": "assistant", "content": mensaje_agradecimiento})
                        
                        st.success("¡Pago procesado exitosamente!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ El pago no pudo procesarse. Intentá nuevamente.")
            else:
                st.warning("⚠️ Por favor, seleccioná un método de pago primero.")
    
    with col2:
        if st.button("❌ Cancelar Pago", use_container_width=True):
            mem["estado_pago"] = None
            mem["metodo_pago"] = None
            st.rerun()
