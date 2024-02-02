import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, dash_table, Input, Output, State

import requests

app = Dash(__name__)

url_default = 'https://graph.facebook.com/v19.0/'
cliente = ''
insights = '/insights?'
token = ''
params = {
    'time_increment': 1,
    'level': 'adset',
    'fields': 'campaign_name,adset_name,spend,cpc,clicks,impressions,reach,actions',
    'access_token': token
}

def get_updated_data(token_value, cliente_value, interval_type, start_date, end_date, single_date):
    updated_url = url_default + cliente_value + insights
    params['access_token'] = token_value
    
    if interval_type == 'range':
        params['time_range'] = f'{{"since":"{start_date}","until":"{end_date}"}}'
    elif interval_type == 'single_day':
        params['time_range'] = f'{{"since":"{single_date}","until":"{single_date}"}}'

    updated_response = requests.get(updated_url, params=params)
    updated_json_content = updated_response.json()

    return updated_json_content

def process_error(updated_json_content):
    return updated_json_content.get('error')

def process_empty_data(updated_json_content):
    return updated_json_content.get('data') == []

def extract_actions(row):
    #print(f"Processando: {row}")  # Debug
    try:
        actions_dict = {}
        for action in row:
            if 'action_type' in action and 'value' in action:
                actions_dict[action['action_type']] = action['value']
        #print(f"Extraído: {actions_dict}")  # Debug
        return pd.Series(actions_dict)
    except Exception as e:
        #print(f"Erro: {e}")  # Debug
        return pd.Series()


def process_data(updated_json_content):
    updated_df = pd.json_normalize(updated_json_content['data'])
    actions_expanded = updated_df['actions'].apply(extract_actions)
    updated_df_final = pd.concat([updated_df.drop('actions', axis=1), actions_expanded], axis=1)
    updated_df_final = updated_df_final.fillna(0)
    updated_df_final = updated_df_final.rename(columns={
        'onsite_conversion.post_save': 'post_save',
        'onsite_conversion.messaging_conversation_started_7d': 'messaging_conversation_started_7d',
    })

    return updated_df_final

def update_feedback_message(updated_json_content):
    if process_error(updated_json_content):
        return html.H3('STATUS: Erro ao carregar os dados. Verifique se o token é válido ou se o código de cliente está correto.', style={'text-align': 'center', 'color': 'red', 'background-color': 'white'})
    elif process_empty_data(updated_json_content):
        return html.H3('STATUS: Não existem campanhas deste cliente no intervalo de tempo solicitado', style={'text-align': 'center', 'color': 'red', 'background-color': 'white'})
    else:
        return html.H3('STATUS: Dados carregados com sucesso!', style={'text-align': 'center', 'color': 'green', 'background-color': 'white'})

def get_total_investment(data):
    data_spend = data['spend'].astype(float)
    return data_spend.sum()

app.layout = html.Div(children=[
    html.Div(children=[
        html.Img(src=app.get_asset_url('logo.png'), 
                 style={'height': '100px', 
                        'width': '100px', 
                        'margin-right': '10px'}),
        html.Div(children=[
            html.H1(children='Zero Um Company', 
                    style={'text-align': 'center', 
                           'color': 'white',
                           'margin-bottom': '0px',}),
        ], style={'display': 'flex', 
                  'flexDirection': 'column', 
                  'justifyContent': 'center',
                  'margin-bottom': '0px'}),
    ], style={'display': 'flex', 
              'align-items': 'center', 
              'background-color': '#040911',
              'margin-bottom': '0px',
              }),

    html.H2(children='Informações de Autenticação', 
            style={'text-align': 'center', 
                   'color': 'white',
                   'background-color': '#143159',
                   'line-height': '100px',
                   'margin-top': '0px',
                   'align-items': 'center'}),
    
    html.Div(children=[
        html.Div(children=[
            html.H3(children='Insira o Token de autenticação do Facebook', 
                    style={'margin-bottom': '10px', 
                           'color': 'white'}),
            dcc.Input(
                id='token-input', 
                type='text', 
                placeholder='Token',
                style={
                    'background-color': '#f0f0f0', 
                    'color': 'black', 
                    'border': '2px solid #ddd', 
                    'border-radius': '5px',  
                    'padding': '10px',
                    'cursor': 'pointer',}),
        ]),
        html.Div(children=[
            html.H3(children='Selecione o formato de dias desejado', 
                    style={'margin-bottom': '10px', 
                           'color': 'white'}),
            dcc.RadioItems(
                id='interval-type',
                options=[
                    {'label': 'Intervalo de Dias', 'value': 'range'},
                    {'label': 'Dia Único', 'value': 'single_day'}
                ],
                value='range',
                labelStyle={'display': 'block', 'margin-bottom': '5px'},
                style={'color': 'white'}
            ),
        ]),
    ], style={'display': 'flex', 'justify-content': 'space-between', 'margin-bottom': '20px', 'padding': '0 20px'}),
    
    html.Div(children=[
        html.Div(children=[
            html.H3(children='Insira o código de autenticação do cliente', 
                    style={'margin-bottom': '10px', 
                           'color': 'white'}),
            dcc.Input(
                id='client-input', 
                type='text', 
                placeholder='Cliente', 
                style={
                    'background-color': '#f0f0f0', 
                    'color': 'black', 
                    'border': '2px solid #ddd', 
                    'border-radius': '5px',  
                    'padding': '10px',
                    'cursor': 'pointer',}),
        ]),
        html.Div(children=[
            html.H3(children='Selecione a data desejada', style={'margin-bottom': '10px', 'color': 'white'}),
            dcc.DatePickerRange(
                id='date-range',
                start_date='2023-03-01',
                end_date='2023-03-31',
                display_format='DD-MM-YYYY',
                style={
                    'background-color': '#f0f0f0', 
                    'color': 'black', 
                    'border': '2px solid #ddd', 
                    'border-radius': '5px',  
                    'padding': '10px',
                    'cursor': 'pointer',
                    'display': 'none'
                }
            ),
            dcc.DatePickerSingle(
                id='date-picker',
                date='2023-01-01',
                display_format='DD-MM-YYYY',
                style={
                    'background-color': '#f0f0f0', 
                    'color': 'black', 
                    'border': '2px solid #ddd', 
                    'border-radius': '5px',  
                    'padding': '10px',
                    'cursor': 'pointer',
                    'display': 'none'
                }
            ),
        ]),
    ], style={'display': 'flex', 'justify-content': 'space-between', 'margin-bottom': '20px', 'padding': '0 20px'}),

    html.Button('Enviar', id='submit-button', n_clicks=0, style={
    'background-color': '#4CAF50',
    'color': 'white',
    'padding': '10px 20px',
    'border': 'none',
    'border-radius': '4px',
    'margin': 'auto',
    'display': 'block',
    'cursor': 'pointer'
    }),

    html.Div(id='feedback-msg', style={'margin-top': 10}),

    html.H2(children='Dashboard de Anúncios MetaAds', 
            style={'text-align': 'center', 
                   'color': 'white',
                   'background-color': '#143159',
                   'line-height': '100px',}),
    
    html.Div(children=[
        html.Div(children=[
            html.Div(children=[
                html.H3(children='Período', style={'margin-bottom': '10px', 'color': 'white'}),
            ]),
            html.Div(children=[
                html.H3(id='date-begin-field', 
                        style={
                            'margin-bottom': '10px', 
                            'color': 'white', 
                            'border': '2px solid #ddd', 
                            'border-radius': '5px',
                            'background-color': '#040911',
                            }),
                html.H3(id='date-end-field', 
                        style={
                            'margin-bottom': '10px', 
                            'color': 'white', 
                            'border': '2px solid #ddd', 
                            'border-radius': '5px',
                            'background-color': '#040911',
                            }),
            ]),
        ]),
        html.Div(children=[
            html.H3(children='Investimento', style={'margin-bottom': '10px', 'color': 'white'}),
            html.H3(id='spend-field', 
                    style={
                        'margin-bottom': '10px', 
                        'color': 'white', 
                        'border': '2px solid #ddd', 
                        'border-radius': '5px',
                        'background-color': '#040911',
                        }),
        ]),
    ], style={'display': 'flex', 'justify-content': 'space-evenly', 'margin-bottom': '20px', 'padding': '0 20px'}),
    
    dash_table.DataTable(data=[], page_size=30, id='table', style_table={'overflowX': 'auto', 'margin': 'auto', 'width': '80%'}),

], style={'background-color': '#081425'})


@app.callback(
    [Output('date-range', 'style'),
     Output('date-picker', 'style')],
    [Input('interval-type', 'value')]
)
def update_date_picker_style(interval_type):
    if interval_type == 'range':
        return {'display': 'block'}, {'display': 'none'}
    elif interval_type == 'single_day':
        return {'display': 'none'}, {'display': 'block'}
    else:
        return {'display': 'none'}, {'display': 'none'}

@app.callback(
    [Output('table', 'data'),
     Output('feedback-msg', 'children'),
     Output('spend-field', 'children')],
    [Input('submit-button', 'n_clicks')],
    [State('token-input', 'value'),
     State('client-input', 'value'),
     State('interval-type', 'value'),
     State('date-range', 'start_date'),
     State('date-range', 'end_date'),
     State('date-picker', 'date')]
)
def update_graph(n_clicks, token_value, cliente_value, interval_type, start_date, end_date, single_date):
    if n_clicks > 0:
        
        if token_value is None:
            return {
                [], 
                html.Div('Insira o Token!', style={'text-align': 'center', 'color': 'red', 'background-color': 'white'}), 
                ''
                }
        if cliente_value is None:
            return {
                [], 
                html.Div('Insira o Código do cliente desejado!', style={'text-align': 'center', 'color': 'red', 'background-color': 'white'}),
                ''
                }

        updated_json_content = get_updated_data(token_value, cliente_value, interval_type, start_date, end_date, single_date)

        if process_error(updated_json_content) or process_empty_data(updated_json_content):
            return [], update_feedback_message(updated_json_content)
        
        updated_df = process_data(updated_json_content)
        spend = get_total_investment(updated_df)
        spend = f'R$ {spend:.2f}'.replace('.', ',')

        return updated_df.to_dict('records'), update_feedback_message(updated_json_content), spend

    return [], html.H3('STATUS: Aguardando Envio...', style={'text-align': 'center', 'color': 'white'}), ''


if __name__ == '__main__':
    app.run(debug=True)
