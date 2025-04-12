from sklearn.linear_model import LinearRegression
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ⬆️ Diseño de página más ancho
st.set_page_config(layout="wide")

st.title("📦 Análisis de Ventas por Volumen (Unidades) desde archivo Excel")


sheet_id = "1HzfrskvlDvAPAziXqJIERSQp0m-jMKZq"
sheet_name = "Hoja 1"  # Cambia esto si tu hoja tiene otro nombre

url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

df = pd.read_csv(url)


    # 🧹 Formatear datos
    df["Código"] = df["Código"].astype(str)
    df["Unidades periodo"] = pd.to_numeric(df["Unidades periodo"], errors="coerce")
    df["Unidades periodo anterior"] = pd.to_numeric(df["Unidades periodo anterior"], errors="coerce")

    df = df.dropna(subset=["Unidades periodo", "Unidades periodo anterior"])

    # 📈 Modelo logarítmico
    df_modelo = df[(df["Unidades periodo anterior"] > 0) & (df["Unidades periodo"] > 0)]
    X = np.log(df_modelo[["Unidades periodo anterior"]])
    y = np.log(df_modelo["Unidades periodo"])

    modelo = LinearRegression()
    modelo.fit(X, y)

    st.markdown(f"⚠️ **Modelo logarítmico:** ln(y) = {modelo.coef_[0]:.2f} · ln(x) + {modelo.intercept_:.2f}")

    # 🔮 Predicción 2025
    df["Proyeccion 2025"] = np.nan
    pred_input = df[df["Unidades periodo"] > 0][["Unidades periodo"]].rename(columns={"Unidades periodo": "Unidades periodo anterior"})
    pred_log = np.log(pred_input)
    df.loc[df["Unidades periodo"] > 0, "Proyeccion 2025"] = np.exp(modelo.predict(pred_log))

    df["Proyeccion 2025"] = df["Proyeccion 2025"].round(0)
    df["Diferencia proyeccion"] = df["Proyeccion 2025"] - df["Unidades periodo"]
    df["Crecimiento %"] = ((df["Diferencia proyeccion"]) / df["Unidades periodo"]) * 100

    # ⚠️ Advertencia de caídas fuertes
    caen = df[df["Diferencia proyeccion"] < -df["Unidades periodo"] * 0.4]
    if not caen.empty:
        st.warning(f"⚠️ {len(caen)} productos presentan caídas superiores al 40% en volumen proyectado.")
        st.dataframe(caen[["Código", "articulo ", "Unidades periodo", "Proyeccion 2025", "Diferencia proyeccion"]], use_container_width=True)

    # 📉 Gráfico: caída en volumen (Top 10)
    top_caidas = df.sort_values("Diferencia proyeccion").head(10)
    fig1 = go.Figure(go.Bar(
        y=top_caidas["articulo "][::-1],
        x=top_caidas["Diferencia proyeccion"][::-1],
        orientation='h',
        marker_color='crimson',
        text=top_caidas["Diferencia proyeccion"][::-1].astype(int).astype(str),
        textposition='auto',
        name="Caída en unidades"
    ))

    fig1.update_layout(
        title="📉 Caída en Volumen: Top 10 productos",
        xaxis_title="Diferencia (Unidades)",
        yaxis_title="Producto",
        height=600,
        width=1400,
        margin=dict(l=200, r=40, t=60, b=40)
    )
    st.plotly_chart(fig1, use_container_width=True)

    # 📈 Gráfico: crecimiento en porcentaje (Top 10)
    top_subidas = df[df["Diferencia proyeccion"] > 0].sort_values("Crecimiento %", ascending=False).head(10)
    fig2 = go.Figure(go.Bar(
        y=top_subidas["articulo "][::-1],
        x=top_subidas["Crecimiento %"][::-1],
        orientation='h',
        marker_color='seagreen',
        text=top_subidas["Crecimiento %"][::-1].round(1).astype(str) + '%',
        textposition='auto',
        name="Crecimiento %"
    ))
    fig2.update_layout(
        title="📈 Subida en Volumen: Top 10 productos con mayor crecimiento (%)",
        xaxis_title="Crecimiento (%)",
        yaxis_title="Producto",
        height=600,
        width=1400,
        margin=dict(l=200, r=40, t=60, b=40)
    )
    st.plotly_chart(fig2, use_container_width=True)

    # 🧾 Tabla de diferencias
    def resaltar_dif(val):
        return 'color: red' if val < 0 else 'color: black'

    df[["Unidades periodo", "Proyeccion 2025", "Diferencia proyeccion"]] = df[["Unidades periodo", "Proyeccion 2025", "Diferencia proyeccion"]].round(0)
    styled = df[["Código", "articulo ", "Unidades periodo", "Proyeccion 2025", "Diferencia proyeccion"]] \
        .style.format("{:.0f}", subset=["Unidades periodo", "Proyeccion 2025", "Diferencia proyeccion"]) \
        .applymap(resaltar_dif, subset=["Diferencia proyeccion"])

    st.subheader("📦 Tabla de Proyección de Volumen 2025 con diferencias")
    st.dataframe(styled, use_container_width=True)

except FileNotFoundError:
    st.error("❌ No se encontró el archivo 'datos.xlsx'")
except Exception as e:
    st.error(f"❌ Error al procesar el archivo: {e}")
