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
        st.info("📄 Archivo creado automáticamente en GitHub (pedidos.jsonl).")
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
# SISTEMA DE FEEDBACK
# -----------------------------------------
def guardar_feedback_en_github(feedback_data):
    """Guarda feedback en archivo separado en GitHub"""
    feedback_file = "feedback.jsonl"
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{feedback_file}"
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
        return False  # No mostrar error para feedback

    nueva_linea = json.dumps(feedback_data, ensure_ascii=False)
    nuevo_contenido = contenido_actual.rstrip() + "\n" + nueva_linea + "\n"

    update_data = {
        "message": f"Nuevo feedback - {feedback_data.get('usuario', 'Anónimo')}",
        "content": base64.b64encode(nuevo_contenido.encode("utf-8")).decode("utf-8")
    }

    if sha:
        update_data["sha"] = sha

    update_resp = requests.put(url, headers=headers, data=json.dumps(update_data))
    return update_resp.status_code in (200, 201)

def mostrar_sistema_feedback():
    """Muestra el sistema de feedback después de una compra"""
    if st.session_state.mem.get("compra_realizada"):
        st.markdown("---")
        st.markdown("### 📊 ¿Cómo calificarías tu experiencia?")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("⭐", use_container_width=True, key="fb1"):
                guardar_feedback(1)
        with col2:
            if st.button("⭐⭐", use_container_width=True, key="fb2"):
                guardar_feedback(2)
        with col3:
            if st.button("⭐⭐⭐", use_container_width=True, key="fb3"):
                guardar_feedback(3)
        with col4:
            if st.button("⭐⭐⭐⭐", use_container_width=True, key="fb4"):
                guardar_feedback(4)
        with col5:
            if st.button("⭐⭐⭐⭐⭐", use_container_width=True, key="fb5"):
                guardar_feedback(5)

def guardar_feedback(calificacion):
    """Guarda el feedback del usuario"""
    feedback_data = {
        "calificacion": calificacion,
        "usuario": st.session_state.mem.get("nombre", "Anónimo"),
        "pedido": st.session_state.mem.get("ultimo_pedido", "N/A"),
        "timestamp": datetime.now().isoformat(),
        "comentario": obtener_comentario_automatico(calificacion)
    }
    
    if guardar_feedback_en_github(feedback_data):
        st.success(f"¡Gracias por tu feedback de {calificacion} estrella{'s' if calificacion > 1 else ''}! 💫")
        st.session_state.mem["compra_realizada"] = False
    else:
        st.info("¡Gracias por tu feedback! 💖")

def obtener_comentario_automatico(calificacion):
    """Genera un comentario automático basado en la calificación"""
    comentarios = {
        1: "Experiencia muy pobre",
        2: "Hay aspectos a mejorar", 
        3: "Experiencia aceptable",
        4: "Muy buena experiencia",
        5: "Experiencia excelente"
    }
    return comentarios.get(calificacion, "Sin comentario")

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
        key="metodo_pago"
    )
    
    # Mostrar instrucciones del método seleccionado
    if metodo_seleccionado:
        metodo = METODOS_PAGO[metodo_seleccionado]
        st.info(f"**{metodo['nombre']}**: {metodo['instrucciones']}")
        
        # Campos para datos de tarjeta si es necesario
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
    # En un entorno real, aquí se integraría con APIs de pago
    codigo_pago = f"PAY{random.randint(10000, 99999)}"
    
    resultado = {
        "exitoso": True,  # Simulamos pago exitoso siempre
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
        "nombre": None,
        "preferencia": None,
        "producto_seleccionado": None,
        "cantidad": None,
        "estado_pago": None,  # 'pendiente', 'procesando', 'completado'
        "metodo_pago": None,
        "compra_realizada": False,
        "ultimo_pedido": None
    }

mem = st.session_state.mem

# -----------------------------------------
# CATÁLOGO (SIN IMÁGENES)
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
# EXTRACCIÓN DE NOMBRE
# -----------------------------------------
def extraer_nombre(texto):
    texto = texto.strip()

    patrones = [
        r"soy ([a-zA-ZáéíóúÁÉÍÓÚñÑ]+)",
        r"me llamo ([a-zA-ZáéíóúÁÉÍÓÚñÑ]+)",
        r"mi nombre es ([a-zA-ZáéíóúÁÉÍÓÚñÑ]+)"
    ]

    for p in patrones:
        m = re.search(p, texto, re.IGNORECASE)
        if m:
            return m.group(1).capitalize()

    if len(texto.split()) == 1 and texto.isalpha():
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
# LÓGICA DEL CHATBOT MEJORADA
# -----------------------------------------
def procesar(texto):
    texto_l = texto.lower()

    # 1) Nombre
    if mem["nombre"] is None:
        posible = extraer_nombre(texto)
        if posible:
            mem["nombre"] = posible
            return f"Encantado, **{mem['nombre']}** 😊 ¿Preferís café o té?"
        return "¿Cómo te llamás?"

    # 2) Mostrar catálogo (sin imágenes)
    if "catálogo" in texto_l or "catalogo" in texto_l:
        cat = "\n".join(
            [f"- **{n.title()}** — {d['perfil']} — ${d['precio']}" for n, d in catalogo.items()]
        )
        return f"📜 **Catálogo disponible:**\n\n{cat}"

    # 3) Preferencias por perfil
    perfiles = ["floral", "dulce", "herbal", "intenso", "suave", "cítrico", "citric"]
    for p in perfiles:
        if p in texto_l:
            if p == "citric":
                p = "cítrico"

            mem["preferencia"] = p
            nombre, datos = recomendar_por_perfil(p)

            if nombre:
                mem["producto_seleccionado"] = nombre
                return (
                    f"Te recomiendo **{nombre.title()}** — perfil *{datos['perfil']}* — "
                    f"Precio: **${datos['precio']}**.\n\n¿Lo querés o querés otra opción?"
                )

    # 4) Otra opción
    if any(p in texto_l for p in ["otro", "otra", "otra opción", "quiero otra", "mostrame otro"]):
        if mem["preferencia"]:
            actual = mem["producto_seleccionado"]
            nombre, datos = recomendar_por_perfil(mem["preferencia"], actual)

            if nombre:
                mem["producto_seleccionado"] = nombre
                return (
                    f"Probá esta alternativa:\n\n"
                    f"**{nombre.title()}** — {datos['perfil']} — **${datos['precio']}**\n"
                    f"¿Te gusta?"
                )
        return "¿Preferís café o té?"

    # 5) Selección por nombre
    for prod in catalogo.keys():
        if prod in texto_l:
            mem["producto_seleccionado"] = prod
            return f"Perfecto {mem['nombre']}. ¿Cuántas unidades querés?"

    # 6) Confirmación
    if texto_l in ["si", "sí", "si quiero", "lo quiero", "lo deseo", "dale", "meta", "quiero"] and mem["producto_seleccionado"]:
        return "Perfecto 😊 ¿Cuántas unidades querés comprar?"

    # 7) Cantidad
    if texto_l.isdigit() and mem["producto_seleccionado"]:
        mem["cantidad"] = int(texto_l)
        prod = mem["producto_seleccionado"]
        precio = catalogo[prod]["precio"]
        subtotal = precio * mem["cantidad"]

        return (
            f"Perfecto {mem['nombre']}:\n"
            f"**{mem['cantidad']} x {prod.title()}** — Subtotal **${subtotal}**.\n"
            f"Escribí **'comprar'** o **'confirmo'** para finalizar."
        )

    # 8) Confirmar compra - NUEVO FLUJO CON PAGOS
    if texto_l in ["comprar", "confirmo"] and mem["producto_seleccionado"] and mem["cantidad"]:
        prod = mem["producto_seleccionado"]
        cantidad = mem["cantidad"]
        precio = catalogo[prod]["precio"]
        total = precio * cantidad
        
        mem["estado_pago"] = "pendiente"
        mem["total_pendiente"] = total
        
        return (
            f"🛒 **Resumen de tu pedido:**\n\n"
            f"**Producto:** {prod.title()}\n"
            f"**Cantidad:** {cantidad} unidades\n"
            f"**Total a pagar:** ${total}\n\n"
            f"Ahora necesitamos procesar el pago. "
            f"Por favor, seleccioná tu método de pago en la sección de abajo. 👇"
        )

    # 9) Procesar pago desde chat
    if texto_l in ["pagar", "procesar pago", "pago"] and mem["estado_pago"] == "pendiente":
        return "Por favor, usá los controles de abajo para seleccionar y confirmar tu método de pago. 👇"

    # 10) Preguntas base
    if "café" in texto_l or "cafe" in texto_l:
        return "¿Buscás algo intenso, suave o cítrico?"

    if "té" in texto_l or "te" in texto_l:
        return "¿Preferís algo floral, herbal o dulce?"

    # 11) Ayuda
    if any(palabra in texto_l for palabra in ["ayuda", "help", "qué puedes hacer"]):
        return (
            "**Puedo ayudarte con:**\n\n"
            "• Recomendarte café o té según tu gusto\n"
            "• Mostrarte el catálogo completo\n" 
            "• Tomar tu pedido y procesar el pago\n"
            "• Recordar tus preferencias\n\n"
            "¡Decime qué necesitás! 😊"
        )

    return "No estoy seguro de haber entendido. ¿Querés ver el catálogo o buscás café o té?"

# -----------------------------------------
# INTERFAZ MEJORADA
# -----------------------------------------

# Botones de acción rápida
col1, col2, col3 = st.columns(3)

if col1.button("📜 Ver Catálogo"):
    st.session_state.historial.append({"role": "user", "content": "catálogo"})
    st.rerun()

if col2.button("🛒 Comprar"):
    st.session_state.historial.append({"role": "user", "content": "quiero comprar"})
    st.rerun()

if col3.button("❓ Ayuda"):
    st.session_state.historial.append({"role": "user", "content": "ayuda"})
    st.rerun()

# Sección de pago si hay pedido pendiente
if mem["estado_pago"] == "pendiente":
    st.markdown("---")
    st.markdown("### 💳 Procesar Pago")
    
    metodo = mostrar_metodos_pago()
    
    if st.button("✅ Confirmar Pago", type="primary"):
        with st.spinner("Procesando tu pago..."):
            # Simular procesamiento de pago
            resultado = procesar_pago(metodo, mem["total_pendiente"])
            
            if resultado["exitoso"]:
                # Completar la compra
                codigo_pedido = f"PED{random.randint(10000,99999)}"
                
                guardar_pedido_en_github({
                    "codigo": codigo_pedido,
                    "nombre": mem["nombre"],
                    "producto": mem["producto_seleccionado"],
                    "cantidad": mem["cantidad"],
                    "total": mem["total_pendiente"],
                    "metodo_pago": metodo,
                    "codigo_pago": resultado["codigo"],
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                # Actualizar estado
                mem.update({
                    "producto_seleccionado": None,
                    "cantidad": None,
                    "estado_pago": "completado",
                    "compra_realizada": True,
                    "ultimo_pedido": codigo_pedido
                })
                
                st.success(f"✅ **¡Pago exitoso!** Pedido **{codigo_pedido}** confirmado.")
                st.balloons()
                
                # Forzar rerun para mostrar feedback
                st.rerun()
            else:
                st.error("❌ El pago no pudo procesarse. Intentá nuevamente.")

# Chat interface
if "historial" not in st.session_state:
    st.session_state.historial = [
        {"role": "assistant", "content": "¡Hola! ¿Cómo te llamás?"}
    ]

user_msg = st.chat_input("Escribí tu mensaje...")

if user_msg:
    st.session_state.historial.append({"role": "user", "content": user_msg})
    respuesta = procesar(user_msg)
    st.session_state.historial.append({"role": "assistant", "content": respuesta})

# Mostrar historial de chat
for msg in st.session_state.historial:
    if msg["role"] == "user":
        st.markdown(f"🧑‍💬 **Tú:** {msg['content']}")
    else:
        st.markdown(f"🤖 **Asistente:** {msg['content']}")

# Mostrar sistema de feedback después de compra
if mem.get("compra_realizada"):
    mostrar_sistema_feedback()
