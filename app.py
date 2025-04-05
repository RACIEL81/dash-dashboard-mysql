<<<<<<< HEAD
import pandas as pd
from sqlalchemy import create_engine
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
import plotly.graph_objects as go
from dash.dependencies import Input, Output

# Conexión a MySQL
DB_USER = "root"
DB_PASSWORD = "123456"
DB_HOST = "localhost"
DB_NAME = "mi_base_de_datos"

def cargar_datos():
    try:
        engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
        df = pd.read_sql_query("SELECT * FROM mi_tabla", engine)
        df.columns = df.columns.str.lower().str.strip()
        return df
    except Exception as err:
        print(f"Error de MySQL: {err}")
        return None

df = cargar_datos()
if df is None:
    raise ValueError("No se pudieron cargar los datos desde MySQL.")

columnas_necesarias = {'analisis', 'total_po', 'ciudad', 'aliado', 'región'}
if not columnas_necesarias.issubset(set(df.columns)):
    raise ValueError(f"Faltan columnas necesarias en la base de datos. Columnas disponibles: {df.columns}")

df['porcentaje'] = (df['analisis'].sum() / df['total_po'].sum()) * 100

# Inicializar app Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SOLAR])

# Diseño de la app
app.layout = dbc.Container([
    # Logo
    dbc.Row([
        dbc.Col(html.Img(src="assets/claro_logo.png", height="60px"), width=12, className="text-center mb-3")
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

    # Filtros
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("🔍 Filtros", className="text-center text-white"),
            html.Label("Ciudad:", style={'font-weight': 'bold', 'color': 'white'}),
            dcc.Dropdown(id='filtro-ciudad', multi=True, placeholder="Seleccione una ciudad"),
            
            html.Label("Aliado:", style={'font-weight': 'bold', 'color': 'white', 'margin-top': '10px'}),
            dcc.Dropdown(id='filtro-aliado', multi=True, placeholder="Seleccione un aliado"),
            
            html.Label("Región:", style={'font-weight': 'bold', 'color': 'white', 'margin-top': '10px'}),
            dcc.Dropdown(id='filtro-region', multi=True, placeholder="Seleccione una región")
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

    # Gráfico de porcentaje por aliado
    dbc.Row([
        dbc.Col(dcc.Graph(id='grafico-barras-aliados'), width=12)
    ])
], fluid=True, style={'backgroundColor': '#C3131F'})

# Callbacks
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
    df_filtrado = df.copy()
    if region:
        df_filtrado = df_filtrado[df_filtrado['región'].isin(region)]
    if ciudad:
        df_filtrado = df_filtrado[df_filtrado['ciudad'].isin(ciudad)]
    if aliado:
        df_filtrado = df_filtrado[df_filtrado['aliado'].isin(aliado)]
    
    porcentaje = (df_filtrado['analisis'].sum() / df_filtrado['total_po'].sum()) * 100 if not df_filtrado.empty else 0
    publico_objetivo = df_filtrado['total_po'].sum()
    cargas_presenze = df_filtrado['analisis'].sum()
    
    # Gráfico de barras por ciudad
    df_barras = df_filtrado.groupby('ciudad', as_index=False)['analisis'].sum()
    fig_barras = go.Figure(go.Bar(
        x=df_barras['analisis'], y=df_barras['ciudad'], orientation='h',
        text=df_barras['analisis'], textposition='outside', marker_color='#1f77b4'
    ))
    fig_barras.update_layout(
        title="Análisis por Ciudad",
        xaxis_title="Cantidad",
        yaxis_title="Ciudad",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=100, r=50, b=50, t=50),
        height=400
    )
    
    # Gráfico de líneas por aliado
    df_lineas = df_filtrado.groupby('aliado', as_index=False)['analisis'].sum()
    fig_lineas = go.Figure(go.Scatter(
        x=df_lineas['aliado'], y=df_lineas['analisis'], mode='lines+markers',
        line=dict(color='#ff7f0e', width=3),
        marker=dict(size=10, color='#ff7f0e')
    ))
    fig_lineas.update_layout(
        title="Análisis por Aliado",
        xaxis_title="Aliado",
        yaxis_title="Cantidad",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=50, r=50, b=50, t=50),
        height=400
    )
    
    # Gráfico de barras de porcentaje por aliado
    df_barras_aliados = df_filtrado.groupby('aliado', as_index=False)['analisis'].sum()
    total_analisis = df_barras_aliados['analisis'].sum()
    df_barras_aliados['porcentaje'] = (df_barras_aliados['analisis'] / total_analisis * 100) if total_analisis > 0 else 0
    
    fig_barras_aliados = go.Figure(go.Bar(
        x=df_barras_aliados['aliado'],
        y=df_barras_aliados['porcentaje'],
        text=df_barras_aliados['porcentaje'].round(1).astype(str) + '%',
        textposition='outside',
        marker_color='#2ca02c'
    ))
    
    fig_barras_aliados.update_layout(
        title="Distribución Porcentual por Aliado",
        yaxis_title="Porcentaje (%)",
        xaxis_title="Aliado",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=50, r=50, b=100, t=50),
        yaxis=dict(range=[0, 100]),
        height=500
    )
    
    ciudades_options = [{'label': c, 'value': c} for c in df_filtrado['ciudad'].unique()]
    aliados_options = [{'label': a, 'value': a} for a in df_filtrado['aliado'].unique()]
    regiones_options = [{'label': r, 'value': r} for r in df['región'].unique()]
    
    return (f"{porcentaje:.2f}%", 
            f"{publico_objetivo:,}", 
            f"{cargas_presenze:,}", 
            fig_barras, 
            fig_lineas, 
            fig_barras_aliados,
            ciudades_options, 
            aliados_options, 
            regiones_options)

if __name__ == '__main__':
=======
import pandas as pd
from sqlalchemy import create_engine
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
import plotly.graph_objects as go
from dash.dependencies import Input, Output

# Conexión a MySQL
DB_USER = "root"
DB_PASSWORD = "123456"
DB_HOST = "localhost"
DB_NAME = "mi_base_de_datos"

def cargar_datos():
    try:
        engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
        df = pd.read_sql_query("SELECT * FROM mi_tabla", engine)
        df.columns = df.columns.str.lower().str.strip()
        return df
    except Exception as err:
        print(f"Error de MySQL: {err}")
        return None

df = cargar_datos()
if df is None:
    raise ValueError("No se pudieron cargar los datos desde MySQL.")

columnas_necesarias = {'analisis', 'total_po', 'ciudad', 'aliado', 'región'}
if not columnas_necesarias.issubset(set(df.columns)):
    raise ValueError(f"Faltan columnas necesarias en la base de datos. Columnas disponibles: {df.columns}")

df['porcentaje'] = (df['analisis'].sum() / df['total_po'].sum()) * 100

# Inicializar app Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SOLAR])

# Diseño de la app
app.layout = dbc.Container([
    # Logo
    dbc.Row([
        dbc.Col(html.Img(src="assets/claro_logo.png", height="60px"), width=12, className="text-center mb-3")
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

    # Filtros
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("🔍 Filtros", className="text-center text-white"),
            html.Label("Ciudad:", style={'font-weight': 'bold', 'color': 'white'}),
            dcc.Dropdown(id='filtro-ciudad', multi=True, placeholder="Seleccione una ciudad"),
            
            html.Label("Aliado:", style={'font-weight': 'bold', 'color': 'white', 'margin-top': '10px'}),
            dcc.Dropdown(id='filtro-aliado', multi=True, placeholder="Seleccione un aliado"),
            
            html.Label("Región:", style={'font-weight': 'bold', 'color': 'white', 'margin-top': '10px'}),
            dcc.Dropdown(id='filtro-region', multi=True, placeholder="Seleccione una región")
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

    # Gráfico de porcentaje por aliado
    dbc.Row([
        dbc.Col(dcc.Graph(id='grafico-barras-aliados'), width=12)
    ])
], fluid=True, style={'backgroundColor': '#C3131F'})

# Callbacks
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
    df_filtrado = df.copy()
    if region:
        df_filtrado = df_filtrado[df_filtrado['región'].isin(region)]
    if ciudad:
        df_filtrado = df_filtrado[df_filtrado['ciudad'].isin(ciudad)]
    if aliado:
        df_filtrado = df_filtrado[df_filtrado['aliado'].isin(aliado)]
    
    porcentaje = (df_filtrado['analisis'].sum() / df_filtrado['total_po'].sum()) * 100 if not df_filtrado.empty else 0
    publico_objetivo = df_filtrado['total_po'].sum()
    cargas_presenze = df_filtrado['analisis'].sum()
    
    # Gráfico de barras por ciudad
    df_barras = df_filtrado.groupby('ciudad', as_index=False)['analisis'].sum()
    fig_barras = go.Figure(go.Bar(
        x=df_barras['analisis'], y=df_barras['ciudad'], orientation='h',
        text=df_barras['analisis'], textposition='outside', marker_color='#1f77b4'
    ))
    fig_barras.update_layout(
        title="Análisis por Ciudad",
        xaxis_title="Cantidad",
        yaxis_title="Ciudad",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=100, r=50, b=50, t=50),
        height=400
    )
    
    # Gráfico de líneas por aliado
    df_lineas = df_filtrado.groupby('aliado', as_index=False)['analisis'].sum()
    fig_lineas = go.Figure(go.Scatter(
        x=df_lineas['aliado'], y=df_lineas['analisis'], mode='lines+markers',
        line=dict(color='#ff7f0e', width=3),
        marker=dict(size=10, color='#ff7f0e')
    ))
    fig_lineas.update_layout(
        title="Análisis por Aliado",
        xaxis_title="Aliado",
        yaxis_title="Cantidad",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=50, r=50, b=50, t=50),
        height=400
    )
    
    # Gráfico de barras de porcentaje por aliado
    df_barras_aliados = df_filtrado.groupby('aliado', as_index=False)['analisis'].sum()
    total_analisis = df_barras_aliados['analisis'].sum()
    df_barras_aliados['porcentaje'] = (df_barras_aliados['analisis'] / total_analisis * 100) if total_analisis > 0 else 0
    
    fig_barras_aliados = go.Figure(go.Bar(
        x=df_barras_aliados['aliado'],
        y=df_barras_aliados['porcentaje'],
        text=df_barras_aliados['porcentaje'].round(1).astype(str) + '%',
        textposition='outside',
        marker_color='#2ca02c'
    ))
    
    fig_barras_aliados.update_layout(
        title="Distribución Porcentual por Aliado",
        yaxis_title="Porcentaje (%)",
        xaxis_title="Aliado",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=50, r=50, b=100, t=50),
        yaxis=dict(range=[0, 100]),
        height=500
    )
    
    ciudades_options = [{'label': c, 'value': c} for c in df_filtrado['ciudad'].unique()]
    aliados_options = [{'label': a, 'value': a} for a in df_filtrado['aliado'].unique()]
    regiones_options = [{'label': r, 'value': r} for r in df['región'].unique()]
    
    return (f"{porcentaje:.2f}%", 
            f"{publico_objetivo:,}", 
            f"{cargas_presenze:,}", 
            fig_barras, 
            fig_lineas, 
            fig_barras_aliados,
            ciudades_options, 
            aliados_options, 
            regiones_options)

if __name__ == '__main__':
>>>>>>> 2b00b7546286852222761ac453d7f5853fbaa2d5
    app.run(debug=True)