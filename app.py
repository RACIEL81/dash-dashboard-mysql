import os
import pandas as pd
from sqlalchemy import create_engine
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def cargar_datos():
    try:
        # Obtener configuración de la base de datos
        DATABASE_URL = os.environ.get('DATABASE_URL')
        
        # Si no hay DATABASE_URL, usar configuración local
        if not DATABASE_URL:
            # Verificar si estamos en Render (tiene variable RENDER)
            if os.environ.get('RENDER'):
                raise ValueError("Se requiere DATABASE_URL en entorno de producción")
                
            # Configuración local
            DB_USER = os.getenv('DB_USER', 'root')
            DB_PASSWORD = os.getenv('DB_PASSWORD', '123456')
            DB_HOST = os.getenv('DB_HOST', 'localhost')
            DB_NAME = os.getenv('DB_NAME', 'mi_base_de_datos')
            DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
        
        # Ajustar para PostgreSQL si es necesario
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
        engine = create_engine(DATABASE_URL)
        df = pd.read_sql_query("SELECT * FROM mi_tabla", engine)
        
        # Verificar columnas necesarias
        required_columns = {'analisis', 'total_po', 'ciudad', 'aliado', 'región'}
        if not required_columns.issubset(set(df.columns)):
            missing = required_columns - set(df.columns)
            raise ValueError(f"Faltan columnas necesarias: {missing}")
        
        # Limpieza de datos
        df.columns = df.columns.str.lower().str.strip()
        df['porcentaje'] = (df['analisis'].sum() / df['total_po'].sum()) * 100
        
        return df
        
    except Exception as err:
        print(f"Error al cargar datos: {err}")
        
        # Crear datos de ejemplo si falla la conexión
        sample_data = {
            'analisis': [150, 200, 180],
            'total_po': [1000, 1200, 1500],
            'ciudad': ['Bogotá', 'Medellín', 'Cali'],
            'aliado': ['Aliado A', 'Aliado B', 'Aliado C'],
            'región': ['Centro', 'Antioquia', 'Valle']
        }
        df_backup = pd.DataFrame(sample_data)
        df_backup['porcentaje'] = (df_backup['analisis'].sum() / df_backup['total_po'].sum()) * 100
        
        print("Usando datos de ejemplo generados")
        return df_backup

# Cargar datos
df = cargar_datos()

# Inicializar app Dash
app = dash.Dash(__name__, 
               external_stylesheets=[dbc.themes.SOLAR],
               assets_folder='assets')  # Asegura que la carpeta assets sea encontrada
server = app.server  # Necesario para Render

# =============================================
# Diseño de la aplicación
# =============================================
app.layout = dbc.Container([
    # Logo
    dbc.Row([
        dbc.Col(html.Img(src='claro_logo.png', height="60px", 
                        style={'filter': 'brightness(0) invert(1)'}), 
               width=12, className="text-center mb-3")
    ]),

    # Tarjetas de resumen
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("📊 Porcentaje de Análisis", className="text-center text-white"),
            html.H3(id='resultado-porcentaje', className="text-center text-danger fw-bold")
        ]), className="shadow-sm bg-dark rounded"), width=4),

        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("🎯 Público Objetivo", className="text-center text-white"),
            html.H3(id='publico-objetivo', className="text-center text-primary fw-bold")
        ]), className="shadow-sm bg-dark rounded"), width=4),

        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("📥 Cargas en Presenze", className="text-center text-white"),
            html.H3(id='cargas-presenze', className="text-center text-success fw-bold")
        ]), className="shadow-sm bg-dark rounded"), width=4)
    ], className="mb-3"),

    # Filtros y gráficos principales
    dbc.Row([
        # Panel de filtros
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("🔍 Filtros", className="text-center text-white"),
            
            html.Label("Ciudad:", style={'font-weight': 'bold', 'color': 'white'}),
            dcc.Dropdown(
                id='filtro-ciudad',
                multi=True,
                placeholder="Seleccione una ciudad",
                style={'color': '#333'}  # Mejor contraste para el texto
            ),
            
            html.Label("Aliado:", style={'font-weight': 'bold', 'color': 'white', 'margin-top': '10px'}),
            dcc.Dropdown(
                id='filtro-aliado',
                multi=True,
                placeholder="Seleccione un aliado",
                style={'color': '#333'}
            ),
            
            html.Label("Región:", style={'font-weight': 'bold', 'color': 'white', 'margin-top': '10px'}),
            dcc.Dropdown(
                id='filtro-region',
                multi=True,
                placeholder="Seleccione una región",
                style={'color': '#333'}
            )
        ]), className="shadow-sm bg-dark rounded"), width=3),
        
        # Gráficos principales
        dbc.Col([
            dbc.Row([
                dbc.Col(dcc.Graph(id='grafico-barras'), width=12)
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(dcc.Graph(id='grafico-lineas'), width=12)
            ])
        ], width=9)
    ], className="mb-3"),

    # Gráfico adicional
    dbc.Row([
        dbc.Col(dcc.Graph(id='grafico-barras-aliados'), width=12)
    ])
], fluid=True, style={'backgroundColor': '#C3131F', 'padding': '20px'})

# =============================================
# Callbacks para interactividad
# =============================================
@app.callback(
    [Output('resultado-porcentaje', 'children'),
     Output('publico-objetivo', 'children'),
     Output('cargas-presenze', 'children'),
     Output('grafico-barras', 'figure'),
     Output('grafico-lineas', 'figure'),
     Output('grafico-barras-aliados', 'figure'),
     Output('filtro-ciudad', 'options'),
     Output('filtro-aliado', 'options'),
     Output('filtro-region', 'options')],
    [Input('filtro-ciudad', 'value'),
     Input('filtro-aliado', 'value'),
     Input('filtro-region', 'value')]
)
def actualizar_dashboard(ciudad, aliado, region):
    try:
        # Aplicar filtros
        df_filtrado = df.copy()
        if region:
            df_filtrado = df_filtrado[df_filtrado['región'].isin(region)]
        if ciudad:
            df_filtrado = df_filtrado[df_filtrado['ciudad'].isin(ciudad)]
        if aliado:
            df_filtrado = df_filtrado[df_filtrado['aliado'].isin(aliado)]
        
        # Calcular métricas
        total_po = df_filtrado['total_po'].sum()
        analisis = df_filtrado['analisis'].sum()
        
        porcentaje = (analisis / total_po * 100) if total_po > 0 else 0
        publico_objetivo = total_po
        cargas_presenze = analisis
        
        # Gráfico de barras por ciudad
        fig_barras = crear_grafico_barras(df_filtrado)
        
        # Gráfico de líneas por aliado
        fig_lineas = crear_grafico_lineas(df_filtrado)
        
        # Gráfico de porcentaje por aliado
        fig_barras_aliados = crear_grafico_porcentaje(df_filtrado)
        
        # Opciones para los dropdowns
        ciudades_options = [{'label': c, 'value': c} for c in sorted(df['ciudad'].unique())]
        aliados_options = [{'label': a, 'value': a} for a in sorted(df['aliado'].unique())]
        regiones_options = [{'label': r, 'value': r} for r in sorted(df['región'].unique())]
        
        return (
            f"{porcentaje:.1f}%", 
            f"{publico_objetivo:,}", 
            f"{cargas_presenze:,}", 
            fig_barras, 
            fig_lineas, 
            fig_barras_aliados,
            ciudades_options, 
            aliados_options, 
            regiones_options
        )
        
    except Exception as e:
        print(f"Error en callback: {e}")
        # Retornar valores por defecto en caso de error
        return ("0%", "0", "0", go.Figure(), go.Figure(), go.Figure(), [], [], [])

# =============================================
# Funciones auxiliares para gráficos
# =============================================
def crear_grafico_barras(df):
    df_barras = df.groupby('ciudad', as_index=False)['analisis'].sum()
    
    fig = go.Figure(go.Bar(
        x=df_barras['analisis'], 
        y=df_barras['ciudad'], 
        orientation='h',
        text=df_barras['analisis'], 
        textposition='outside', 
        marker_color='#1f77b4'
    ))
    
    fig.update_layout(
        title="Análisis por Ciudad",
        xaxis_title="Cantidad",
        yaxis_title="",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=20, r=20, b=50, t=50),
        height=400
    )
    
    return fig

def crear_grafico_lineas(df):
    df_lineas = df.groupby('aliado', as_index=False)['analisis'].sum()
    
    fig = go.Figure(go.Scatter(
        x=df_lineas['aliado'], 
        y=df_lineas['analisis'], 
        mode='lines+markers',
        line=dict(color='#ff7f0e', width=3),
        marker=dict(size=10, color='#ff7f0e')
    ))
    
    fig.update_layout(
        title="Análisis por Aliado",
        xaxis_title="Aliado",
        yaxis_title="Cantidad",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=20, r=20, b=50, t=50),
        height=400
    )
    
    return fig

def crear_grafico_porcentaje(df):
    df_porcentaje = df.groupby('aliado', as_index=False)['analisis'].sum()
    total = df_porcentaje['analisis'].sum()
    df_porcentaje['porcentaje'] = (df_porcentaje['analisis'] / total * 100) if total > 0 else 0
    
    fig = go.Figure(go.Bar(
        x=df_porcentaje['aliado'],
        y=df_porcentaje['porcentaje'],
        text=df_porcentaje['porcentaje'].round(1).astype(str) + '%',
        textposition='outside',
        marker_color='#2ca02c'
    ))
    
    fig.update_layout(
        title="Distribución Porcentual por Aliado",
        yaxis_title="Porcentaje (%)",
        xaxis_title="",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=20, r=20, b=100, t=50),
        yaxis=dict(range=[0, 100]),
        height=500
    )
    
    return fig

# =============================================
# Configuración para producción
# =============================================
if __name__ == '__main__':
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run_server(debug=debug_mode, host='0.0.0.0', port=int(os.environ.get('PORT', 8050)))
