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
FILE_PATH = "pedidos.jsonl"     # JSON Lines
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

def guardar_pedido_en_github(pedido):
    """Guarda un pedido como una línea JSON en pedidos.jsonl del repo."""
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    # 1. Intentar obtener el archivo
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

    # 2. Agregar nueva línea en JSONL
    nueva_linea = json.dumps(pedido, ensure_ascii=False)
    nuevo_contenido = contenido_actual.rstrip() + "\n" + nueva_linea + "\n"

    # 3. Construir payload para actualizar archivo
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
# MEMORIA DE SESIÓN
# -----------------------------------------
if "mem" not in st.session_state:
    st.session_state.mem = {
        "nombre": None,
        "preferencia": None,
        "producto_seleccionado": None,
        "cantidad": None
    }

mem = st.session_state.mem

# -----------------------------------------
# CATÁLOGO con imágenes (URLs corregidas)
# -----------------------------------------
catalogo = {
    # ☕ CAFÉ — Perfil cítrico
    "café de colombia": {
        "tipo": "café",
        "perfil": "cítrico",
        "precio": 1200,
        "imagen": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=800&q=80"
    },
    "café peruano andes": {
        "tipo": "café",
        "perfil": "cítrico",
        "precio": 1250,
        "imagen": "https://images.unsplash.com/photo-1520971342232-7da1c9a9112a?auto=format&fit=crop&w=800&q=80"
    },

    # ☕ CAFÉ — Perfil intenso
    "café espresso italiano": {
        "tipo": "café",
        "perfil": "intenso",
        "precio": 1100,
        "imagen": "https://images.unsplash.com/photo-1511920170033-f8396924c348?auto=format&fit=crop&w=800&q=80"
    },
    "café dark roast brasil": {
        "tipo": "café",
        "perfil": "intenso",
        "precio": 1300,
        "imagen": "https://images.unsplash.com/photo-1529070538774-1843cb3265df?auto=format&fit=crop&w=800&q=80"
    },

    # ☕ CAFÉ — Perfil suave
    "café arábica light roast": {
        "tipo": "café",
        "perfil": "suave",
        "precio": 1000,
        "imagen": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=800&q=80"
    },
    "café colombiano especial": {
        "tipo": "café",
        "perfil": "suave",
        "precio": 1150,
        "imagen": "https://images.unsplash.com/photo-1442512595331-e89e73853f31?auto=format&fit=crop&w=800&q=80"
    },

    # 🍵 TÉ — Perfil floral
    "té blanco con jazmín": {
        "tipo": "té",
        "perfil": "floral",
        "precio": 800,
        "imagen": "https://images.unsplash.com/photo-1505579168101-4f0a919a8a3d?auto=format&fit=crop&w=800&q=80"
    },
    "té oolong floral blend": {
        "tipo": "té",
        "perfil": "floral",
        "precio": 850,
        "imagen": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=800&q=80"
    },

    # 🍵 TÉ — Perfil dulce
    "té rooibos con vainilla": {
        "tipo": "té",
        "perfil": "dulce",
        "precio": 750,
        "imagen": "https://images.unsplash.com/photo-1505576391880-b3f9d713dc53?auto=format&fit=crop&w=800&q=80"
    },
    "té negro miel & canela": {
        "tipo": "té",
        "perfil": "dulce",
        "precio": 790,
        "imagen": "https://images.unsplash.com/photo-1513639725746-c5d3e861f32d?auto=format&fit=crop&w=800&q=80"
    },

    # 🍵 TÉ — Perfil herbal
    "té verde sencha": {
        "tipo": "té",
        "perfil": "herbal",
        "precio": 780,
        "imagen": "https://images.unsplash.com/photo-1497534446932-c925b458314e?auto=format&fit=crop&w=800&q=80"
    },
    "té menta patagónica": {
        "tipo": "té",
        "perfil": "herbal",
        "precio": 760,
        "imagen": "https://images.unsplash.com/photo-1518976024611-28bf1f35b5d1?auto=format&fit=crop&w=800&q=80"
    },
}



def mostrar_catalogo_con_imagenes():
    for nombre, datos in catalogo.items():
        try:
            st.image(datos["imagen"], width=220)
        except:
            st.warning(f"No se pudo cargar la imagen de {nombre}")

        st.markdown(
            f"### {nombre.title()}\n"
            f"- Perfil: **{datos['perfil']}**\n"
            f"- Precio: **${datos['precio']}**\n"
        )


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
# LÓGICA DEL CHATBOT
# -----------------------------------------
def procesar(texto):
    texto_l = texto.lower()

    # 1. Nombre
    if mem["nombre"] is None:
        posible = extraer_nombre(texto)
        if posible:
            mem["nombre"] = posible
            return f"Encantado, **{mem['nombre']}** 😊 ¿Preferís café o té?"
        return "¿Cómo te llamás?"

    # 2. Catálogo
    if "catálogo" in texto_l or "catalogo" in texto_l:
        return mostrar_catalogo()

    # 3. Preferencias por perfil
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

    # 4. Otra opción
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

    # 5. Selección por nombre
    for prod in catalogo.keys():
        if prod in texto_l:
            mem["producto_seleccionado"] = prod
            return f"Perfecto {mem['nombre']}. ¿Cuántas unidades querés?"

    # 6. Confirmación después de la recomendación
    if texto_l in ["si","si quiero","lo quiero","lo deseo","meta","sí", "ok", "dale", "quiero"] and mem["producto_seleccionado"]:
        return "Perfecto 😊 ¿Cuántas unidades querés comprar?"

    # 7. Cantidad
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

    # 8. Finalizar compra
    if texto_l in ["comprar", "confirmo"] and mem["producto_seleccionado"] and mem["cantidad"]:
        prod = mem["producto_seleccionado"]
        cantidad = mem["cantidad"]
        precio = catalogo[prod]["precio"]
        total = precio * cantidad
        codigo = f"PED{random.randint(10000,99999)}"

        # Guardar pedido en GitHub
        guardar_pedido_en_github({
            "codigo": codigo,
            "nombre": mem["nombre"],
            "producto": prod,
            "cantidad": cantidad,
            "total": total,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # Limpiar
        mem["producto_seleccionado"] = None
        mem["cantidad"] = None

        return (
            f"✅ **Compra confirmada, {mem['nombre']}!**\n"
            f"Pedido **{codigo}**: {cantidad} x {prod.title()} — Total **${total}**.\n"
            f"Gracias por tu compra ☕✨"
        )

    # 9. Preguntas base
    if "café" in texto_l or "cafe" in texto_l:
        return "¿Buscás algo intenso, suave o cítrico?"

    if "té" in texto_l or "te" in texto_l:
        return "¿Preferís algo floral, herbal o dulce?"

    return "No estoy seguro de haber entendido. ¿Querés ver el catálogo o buscás café o té?"

# -----------------------------------------
# INTERFAZ
# -----------------------------------------

col1, col2 = st.columns(2)

if col1.button("📸 Ver Catálogo con imágenes"):
    mostrar_catalogo_con_imagenes()

if col2.button("🛒 Comprar"):
    st.markdown("Decime qué producto querés comprar.")

if "historial" not in st.session_state:
    st.session_state.historial = [
        {"role": "assistant", "content": "¡Hola! ¿Cómo te llamás?"}
    ]

user_msg = st.chat_input("Escribí tu mensaje...")

if user_msg:
    st.session_state.historial.append({"role": "user", "content": user_msg})
    respuesta = procesar(user_msg)
    st.session_state.historial.append({"role": "assistant", "content": respuesta})

for msg in st.session_state.historial:
    if msg["role"] == "user":
        st.markdown(f"🧑‍💬 **Tú:** {msg['content']}")
    else:
        st.markdown(f"🤖 **Asistente:** {msg['content']}")





