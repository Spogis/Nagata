import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
from scipy.optimize import curve_fit
import pandas as pd
import numpy as np
import base64
import io

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

from Nagata_LaTeX import *

nagata_a = None
nagata_b = None
nagata_f = None
nagata_alfa = None
nagata_p = None

def create_nagata_input_row(label, input_id, input_value):
    return html.Div([
        html.Div(label, style={'width': '50px', 'textAlign': 'center', 'paddingLeft': '20px', 'fontWeight': 'bold'}),
        dcc.Input(
            id=input_id,
            type='number',
            value=input_value,
            disabled=True,
            style={'width': '100px', 'color': 'white', 'textAlign': 'center', 'fontWeight': 'bold'}
        )
    ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'marginBottom': '10px'})


# Inicializa o aplicativo Dash
app = dash.Dash(__name__)

# Layout do aplicativo
app.layout = html.Div([
    html.Div([
        html.Img(src='assets/Nagata_Logo.png'),
    ], style={'display': 'flex', 'width': '100%', 'justifyContent': 'center',
              'margin-left': 'auto', 'margin-right': 'auto'}),

    html.Div([
        dcc.Upload(id='upload-data',
                   children=html.Button('Upload File', style={'color': 'white', 'fontWeight': 'bold'}),
                   multiple=False,
                   accept='.xlsx',
                   style={'width': '10%', 'color': 'white', 'textAlign': 'Center',
                          'justifyContent': 'center', 'alignItems': 'center', 'resize': 'none',
                          'margin-right': '10px'}
                   ),

        html.Div([
            create_nagata_input_row("a:", 'a-value', ""),
        ], style={'display': 'flex', 'width': '150px', 'justifyContent': 'center', 'alignItems': 'center'}),

        html.Div([
            create_nagata_input_row("b:", 'b-value', ""),
        ], style={'display': 'flex', 'width': '150px', 'justifyContent': 'center', 'alignItems': 'center'}),

        html.Div([
            create_nagata_input_row("f:", 'f-value', ""),
        ], style={'display': 'flex', 'width': '150px', 'justifyContent': 'center', 'alignItems': 'center'}),

        html.Div([
            create_nagata_input_row("α:", 'alfa-value', ""),
        ], style={'display': 'flex', 'width': '150px', 'justifyContent': 'center', 'alignItems': 'center'}),

        html.Div([
            create_nagata_input_row("p:", 'p-value', ""),
        ], style={'display': 'flex', 'width': '150px', 'justifyContent': 'center', 'alignItems': 'center'}),

    ], id='div-nagata-fit',
        style={'display': 'flex', 'width': '80%', 'justifyContent': 'center',
               'margin-left': 'auto', 'margin-right': 'auto', 'padding': '20px'}),

    html.Div([
        html.Div([
            html.Img(id='nagata-equation',
                     src='',
                     style={'width': '500px', 'display': 'block', 'marginLeft': 'auto', 'marginRight': 'auto',
                            'textAlign': 'center'}),
            dcc.Download(id="download-python-code"),
            html.Button('Download Python Code - Nagata Equation!',
                        id='download-button',
                        disabled=False,
                        style={'display': 'flex', 'width': '500px', 'justifyContent': 'center',
                               'color': 'white', 'fontWeight': 'bold',
                               'margin-left': 'auto', 'margin-right': 'auto',
                               'margin-top': '20px', 'margin-bottom': '20px'}),
        ], id='div-nagata-equation',
            style={'display': 'none'}),

        dcc.Graph(id='graph-output',
                  style={'display': 'None'}),
    ], id='div-graph-nagata',
        style={'width': '80%', 'margin-left': 'auto', 'margin-right': 'auto', 'padding': '20px'}),

], style={'width': '80%', 'justifyContent': 'center', 'margin-left': 'auto', 'margin-right': 'auto', 'padding': '20px'})


@app.callback(
    Output("download-python-code", "data"),
    Input("download-button", "n_clicks"),
    prevent_initial_call=True
)
def download(n_clicks):
    global nagata_a, nagata_b, nagata_f, nagata_alfa, nagata_p

    function_content = f"""
    def Nagata(Re):
        a= {nagata_a}
        b = {nagata_b}
        f = {nagata_f}
        alfa = {nagata_alfa}
        p = {nagata_p}

        Np = a / Re + b * ((10 ** 3 + 0.6 * f * (Re ** alfa)) / (10 ** 3 + 1.6 * f * (Re ** alfa))) ** p

        return Np
    """
    file_path = 'assets/AjusteNagata.py'

    # Escrevendo o conteúdo no arquivo ajuste.py
    with open(file_path, "w") as file:
        file.write(function_content)

    return dcc.send_file(file_path)


# Callback para atualizar o gráfico e os valores dos parâmetros
@app.callback(
    [Output('graph-output', 'figure'),
     Output('graph-output', 'style'),
     Output('a-value', 'value'),
     Output('b-value', 'value'),
     Output('f-value', 'value'),
     Output('alfa-value', 'value'),
     Output('p-value', 'value'),
     Output('nagata-equation', 'src'),
     Output('div-nagata-equation', 'style')],
    [Input('upload-data', 'contents')]
)
def update_output(contents):
    global nagata_a, nagata_b, nagata_f, nagata_alfa, nagata_p
    if contents is None:
        raise dash.exceptions.PreventUpdate

    # Conversão do conteúdo para um DataFrame
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_excel(io.BytesIO(decoded))

    # Realiza o ajuste de curvas
    Re_Exp = df.iloc[:, 0]
    Np_Exp = df.iloc[:, 1]
    max_value = Np_Exp.max()

    def nagata_model(x, a, b, f, alfa, p):
        return a / x + b * ((10 ** 3 + 0.6 * f * (x ** alfa)) / (10 ** 3 + 1.6 * f * (x ** alfa))) ** p

    def nagata_model_Opt(x):
        return a_opt / x + b_opt * (
                (10 ** 3 + 0.6 * f_opt * (x ** alfa_opt)) / (10 ** 3 + 1.6 * f_opt * (x ** alfa_opt))) ** p_opt

    # Curve Fit
    bounds = ([0, 0, 0, 0, 0], [np.inf, np.inf, np.inf, np.inf, np.inf])
    popt, pcov = curve_fit(f=nagata_model, xdata=Re_Exp, ydata=Np_Exp, bounds=bounds)

    a_opt, b_opt, f_opt, alfa_opt, p_opt = popt

    nagata_a, nagata_b, nagata_f, nagata_alfa, nagata_p = popt
    nagata_a = round(nagata_a, 2)
    nagata_b = round(nagata_b, 2)
    nagata_f = round(nagata_f, 2)
    nagata_alfa = round(nagata_alfa, 2)
    nagata_p = round(nagata_p, 2)

    def generate_custom_sequence(start, end):
        # Gera sequências separadas para cada ordem de magnitude
        sequences = [np.arange(10 ** i, 10 ** (i + 1), 10 ** i) for i in range(start, end)]

        # Concatena todas as sequências em um único array
        result = np.concatenate(sequences)

        return result

    Re = generate_custom_sequence(0, 8)  # De 10^0 a 10^8
    Np = nagata_model_Opt(Re)

    # Cria a figura com os dados experimentais e a linha de ajuste
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=Re_Exp, y=Np_Exp, mode='markers', name='Experimental Data'))
    fig.add_trace(go.Scatter(x=Re, y=Np, mode='lines', name='Nagata Model Fit'))

    # Definindo os valores e os textos dos ticks para eixos logarítmicos
    tickvals = [10 ** i for i in range(0, 10)]
    ticktext = [f"10<sup>{i}</sup>" for i in range(0, 10)]

    # Define os eixos como logarítmicos
    fig.update_layout(xaxis_type="log",
                      yaxis_type="log",
                      xaxis=dict(tickvals=tickvals,
                                 ticktext=ticktext),
                      legend=dict(orientation="h",
                                  x=0.5,
                                  y=1.1,
                                  xanchor="center",
                                  yanchor="bottom")
                      )

    # Nome do arquivo para salvar a imagem
    filename = 'assets/equation.png'

    # Gera a imagem da equação de Nagata
    latex_to_png(nagata_a, nagata_b, nagata_f, nagata_alfa, nagata_p, filename)

    # Retorna a figura e os valores dos parâmetros
    return (fig, {'display': 'Block'},
            nagata_a, nagata_b, nagata_f, nagata_alfa, nagata_p,
            'assets/equation.png', {'display': 'Block'})


# Executa o aplicativo
if __name__ == '__main__':
    app.run_server(debug=False)