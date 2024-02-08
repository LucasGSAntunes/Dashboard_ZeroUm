import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, dash_table, Input, Output, State

import requests

app = Dash(__name__)
app.title = 'Zero Um Company - MetaAds Dashboard'
app._favicon = ("logo.png")
server = app.server

url_default = 'https://graph.facebook.com/v19.0/'
cliente = ''
insights = '/insights?'
token = ''
params = {
    'level': 'adset',
    'fields': 'campaign_name,adset_name,adset_id,spend,cpc,ctr,clicks,impressions,reach,actions,frequency',
    'access_token': token
}

def generate_campaign_elements(df):
    campaign_elements = []
    
    grouped_df = df.groupby('campaign_name')
    
    for campaign_name, group_df in grouped_df:
        campaign_elements.append(html.H3(f'CAMPANHA {campaign_name}', style={'margin-bottom': '10px', 'color': 'white', 'text-align': 'center'}))
        for adset_name in group_df['adset_name'].unique():
            campaign_elements.append(html.H5(adset_name, style={'margin-bottom': '10px', 'color': 'white', 'text-align': 'center'}))
    return campaign_elements

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

def get_targeting_data(token_value, adset_id):
    updated_url = url_default + adset_id
    params_targeting = {
        'access_token': token_value,
        'fields': 'name,targeting'
    }

    updated_response = requests.get(updated_url, params=params_targeting)
    updated_json_content = updated_response.json()
    df_targeting = pd.json_normalize(updated_json_content)
    return df_targeting

def get_client_list(token_value):
    updated_url = url_default + 'me/adaccounts'
    params_client = {
        'access_token': token_value,
        'fields': 'name, id',
        'order_by': 'name',
        'limit': 100
    }
    updated_response = requests.get(updated_url, params=params_client)
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

def get_total_msg(data):
    data_msg = data['messaging_conversation_started_7d'].astype(int)
    return data_msg.sum()

def get_cost_per_msg(data):
    return get_total_investment(data) / get_total_msg(data)

def get_impressions(data):
    return data['impressions'].astype(int).sum()

def get_frequency(data, reach_input):
    return get_impressions(data) / int(reach_input)

def get_ctr(data):
    return get_clicks_link(data) / get_impressions(data) * 100

def get_clicks_link(data):
    return data['link_click'].astype(int).sum()

def get_cost_click(data):
    return get_total_investment(data) / get_clicks_link(data)

def get_engagement(data):
    return data['page_engagement'].astype(int).sum()

def get_cost_engagement(data):
    return get_total_investment(data) / get_engagement(data)

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
              'position': 'fixed',
              'top': '0',
              'width': '100%',
              'z-index': '1000'
              }),

    
    html.Div(id='Autentication-fields',children=[
        html.H2(children='Informações de Autenticação', 
                style={'text-align': 'center', 
                    'color': 'white',
                    'background-color': '#040911',
                    'line-height': '100px',
                    'margin-top': '100px',
                    'align-items': 'center',
                    'text-font': 'bold',
                    'border': '2px solid #ddd',
                    'border-radius': '5px'}),
        html.Div(children=[
            html.Div(children=[
                html.Div(children=[
                    html.H3(children='Insira o Token de autenticação do Facebook', style={'margin-bottom': '10px', 'color': 'white', 'text-font': 'bold'}),
                    html.Div(children=[
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
                        html.Button('Validar Token', id='token-button', n_clicks=0, style={
                                                                                    'background-color': '#4CAF50',
                                                                                    'color': 'white',
                                                                                    'padding': '10px 20px',
                                                                                    'border': 'none',
                                                                                    'border-radius': '4px',
                                                                                    'margin': 'auto',
                                                                                    'display': 'block',
                                                                                    'cursor': 'pointer'
                                                                                    }),
                        dcc.Loading(id="loading-token", type="circle", children=[html.Div(id='loading-token-output')]),
                    ], style={'display': 'flex', 'justify-content': 'center', 'margin-bottom': '20px', 'padding': '0 20px'}),

                    html.Div(id='token-feedback-msg', style={'margin-top': 10}),
                ]),

                html.Div(id='client-field' ,children=[
                    html.H3(children='Selecione o cliente desejado', style={'margin-bottom': '10px', 'color': 'white', 'text-font': 'bold', 'text-align': 'center'}),
                    html.Div(children=[
                        dcc.Dropdown(
                            id='client-dropdown',
                            options=[{'label': '', 'value': ''}],
                            placeholder='Selecione o cliente',
                            style={
                                'background-color': '#f0f0f0', 
                                'color': 'black', 
                                'border': None,
                                'padding': '10px',
                                'cursor': 'pointer',
                                'width': '330px',
                                'height': '50px',
                                'text-align': 'center',
                                'margin': 'auto',
                                'display': 'flex',
                                'align-items': 'center',
                                'justify-content': 'space-beetween'
                            }
                        ),
                    ], style={'display': 'flex', 'justify-content': 'center', 'margin-bottom': '20px', 'padding': '0 20px'}),
                ], style={'display': 'none'}),
            ]),

            html.Div(id='date-field',children=[
                html.Div(children=[
                    html.Div(children=[
                        html.H3(children='Selecione o formato de dias desejado', style={'margin-bottom': '10px', 'color': 'white', 'text-font': 'bold', 'text-align': 'center'}),
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
                    html.Div(children=[
                        html.H3(children='Selecione a data desejada', style={'margin-bottom': '10px', 'color': 'white', 'text-font': 'bold', 'text-align': 'center'}),
                        dcc.DatePickerRange(
                            id='date-range',
                            start_date_placeholder_text='Data Inicial',
                            end_date_placeholder_text='Data Final',
                            start_date=None,
                            end_date=None,
                            display_format='DD-MM-YYYY',
                            style={
                                'background-color': '#f0f0f0', 
                                'color': 'black', 
                                'border': '2px solid #ddd', 
                                'border-radius': '5px',  
                                'padding': '10px',
                                'cursor': 'pointer',
                            }
                        ),
                        dcc.DatePickerSingle(
                            id='date-picker',
                            placeholder='Data',
                            date=None,
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
                    ], style={'display': 'flex', 'flex-direction': 'column', 'justify-content': 'center', 'align-items': 'center', 'margin-bottom': '20px', 'padding': '0 20px'}),
                ]),

                html.Div(children=[
                    html.H3('Insira o Alcance total', style={'color': 'white', 'text-align': 'center', 'text-font': 'bold', 'margin-bottom': '10px'}),
                    dcc.Input(
                        id='reach-input',
                        type='text', 
                        placeholder='Alcance', 
                        style={
                            'background-color': '#f0f0f0', 
                            'color': 'black', 
                            'border': '2px solid #ddd', 
                            'border-radius': '5px',  
                            'padding': '10px',
                            'cursor': 'pointer',
                            'margin': '0 auto',
                        }),
                ], style={'display': 'flex', 'flex-direction': 'column', 'justify-content': 'center', 'align-items': 'center', 'margin-bottom': '20px', 'padding': '0 20px'}),
            ], style={'display': 'none'}),
        ], style={'display': 'flex', 'justify-content': 'space-evenly', 'margin-bottom': '20px', 'padding': '0 20px'}),
        
        html.Button('Enviar', id='submit-button', n_clicks=0, style={
        'background-color': '#4CAF50',
        'color': 'white',
        'padding': '10px 20px',
        'border': 'none',
        'border-radius': '4px',
        'margin': 'auto',
        'display': 'block',
        'cursor': 'pointer',
        }),

        html.Div(children=[
            dcc.Store(id='data-store', data={}),
        ], style={'display': 'none'}),

        html.Div(id='feedback-msg', style={'margin-top': 10}),

    ], style={'display': 'none', 'margin-bottom': '0px', 'margin-top': '0px', 'z-index': '50'}),

    html.Div(children=[
        dcc.Loading(
            id="loading-enviar",
            type="circle",
            children=[html.Div(id='loading-output')],
        ),
    ], style={'text-align': 'center', 'margin-top': '20px', 'z-index': '50'}),


    html.H2(children='Dashboard de Anúncios MetaAds', 
            style={'text-align': 'center', 
                   'color': 'white',
                   'background-color': '#040911',
                   'line-height': '100px',
                   'margin-top': '100px',
                   'align-items': 'center',
                   'text-font': 'bold',
                   'border': '2px solid #ddd',
                   'border-radius': '5px'}),
    
    html.Button('Modo apresentação', id='presentation-button', n_clicks=0, style={
        'background-color': '#4CAF50',
        'color': 'white',
        'padding': '10px 20px',
        'border': 'none',
        'border-radius': '4px',
        'margin': '10px auto 20px',
        'display': 'block',
        'cursor': 'pointer'
        }),

    html.Div(id='presentation-fields-setup', children=[
        html.H3(children='Selecione as métricas principais desejadas', style={'margin-bottom': '10px', 'color': 'white', 'text-align': 'center'}),
        html.Div(children=[
            dcc.Checklist(
                id='main-metrics-checklist',
                options=[
                    {'label': 'Investimento', 'value': 'spend'},
                    {'label': 'Conversas Iniciadas', 'value': 'total_msg'},
                    {'label': 'Custo por Conversas Iniciadas', 'value': 'cost_per_msg'},
                    {'label': 'Funil de Conversão', 'value': 'funnel'},
                    {'label': 'Selecionar Campanhas', 'value': 'campaigns'},
                    {'label': 'Campanhas', 'value': 'campaigns_names'},
                ],
                value=['spend', 'total_msg', 'cost_per_msg', 'funnel'],
                style={'display': 'flex', 'justify-content': 'space-evenly', 'color': 'white', 'align-items': 'center', 'margin-bottom': '20px', 'padding': '0 20px'},
                inputStyle={'margin-right': '5px', 'margin-left': '30px'}
            ),
        ], style={'display': 'flex', 'justify-content': 'space-evenly', 'margin-bottom': '20px', 'padding': '0px 20px 10px 20px'}),
    ]),

    html.Div(id='presentation-fields', children=[
        html.Div(children=[
            html.Div(children=[
                html.Div(children=[
                    html.H2(children='Período', style={'margin-bottom': '10px', 'color': 'white', 'font-weight': 'bold', 'text-align': 'center'}),
                ]),
                html.Div(children=[
                    html.Div(children=[
                        html.H2(children='Data Inicial', style={'margin-bottom': '5px','margin-right': '10px', 'color': 'white', 'text-align': 'center'}),
                        html.H2(id='date-begin-field', style={'margin-bottom': '10px', 'margin-right': '10px', 'color': 'white', 'border': '2px solid #ddd', 'border-radius': '5px', 'background-color': '#040911', 'text-align': 'center', 'width': '150px'}),
                    ]),
                    html.Div(children=[
                        html.H2(children='Data Final', style={'margin-bottom': '5px', 'margin-left': '10px', 'color': 'white', 'text-align': 'center'}),
                        html.H2(id='date-end-field', style={'margin-bottom': '10px', 'margin-left': '10px', 'color': 'white', 'border': '2px solid #ddd', 'border-radius': '5px', 'background-color': '#040911', 'text-align': 'center', 'width': '150px'}),
                    ]),
                ], style={'display': 'flex', 'justify-content': 'space-evenly', 'margin-bottom': '20px', 'padding': '0 20px'}),
            ]),

            html.Div(id='campaigns-names-show', children=[
                html.Div(id='campaigns-names')
            ]),

        ], style={'display': 'flex', 'flex-direction': 'column', 'justify-content': 'center', 'align-items': 'center', 'margin-bottom': '20px', 'padding': '0 20px'}),

        html.Div(children=[
            html.Div(id='campaigns-show', children=[
                html.H3(children='Selecione as campanhas desejadas', style={'margin-bottom': '10px', 'color': 'white', 'text-align': 'center'}),
                dcc.Dropdown(
                    id='campaign-dropdown',
                    options=[{'label': '', 'value': ''}],
                    placeholder='Todas as campanhas',
                    style={
                        'text-align': 'center',
                        'background-color': '#f0f0f0', 
                        'color': 'black', 
                        'border': '2px solid #ddd', 
                        'border-radius': '5px',  
                        'padding': '10px',
                        'cursor': 'pointer',
                        'width': '330px',
                        'height': '60px',
                        'margin': 'auto',
                        'display': 'flex',
                        'align-items': 'center',
                        'justify-content': 'space-beetween'
                    }
                ),
            ]),

            html.Div(id='spend-show', children=[
                html.H3(children='Investimento', style={'margin-bottom': '10px', 'color': 'white', 'text-align': 'center'}),
                html.H3(id='spend-field', 
                        style={
                            'margin-bottom': '10px', 
                            'color': 'white', 
                            'border': '2px solid #ddd', 
                            'border-radius': '5px',
                            'background-color': '#040911',
                            'text-align': 'center'
                            }),
            ]),
            html.Div(id='msg-show', children=[
                html.H3(children='Conversas Iniciadas', style={'margin-bottom': '10px', 'color': 'white', 'text-align': 'center'}),
                html.H3(id='total-msg-field', 
                        style={
                            'margin-bottom': '10px', 
                            'color': 'white', 
                            'border': '2px solid #ddd', 
                            'border-radius': '5px',
                            'background-color': '#040911',
                            'text-align': 'center'
                            }),
            ]),
            html.Div(id='cost-msg-show', children=[
                html.H3(children='Custo por Conversas Iniciadas', style={'margin-bottom': '10px', 'color': 'white', 'text-align': 'center'}),
                html.H3(id='cost-per-msg-field', 
                        style={
                            'margin-bottom': '10px', 
                            'color': 'white', 
                            'border': '2px solid #ddd', 
                            'border-radius': '5px',
                            'background-color': '#040911',
                            'text-align': 'center'
                            }),
            ]),
        ], style={'display': 'block', 'justify-content': 'space-beetween', 'margin-bottom': '20px', 'padding': '0 20px'}),

        html.Div(id='funnel-show', children=[
            html.Div(children=[
                html.Div(id='funnel-graph-field', children=[
                    html.H3(children='Funil de Conversão', style={'margin': '0', 'padding-bottom': '10px', 'color': 'white', 'text-align': 'center'}),
                    dcc.Graph(id='funnel-graph', figure={}),
                ], style={'display': 'none'}),
            ], style={'display': 'flex', 'justify-content': 'center', 'margin-bottom': '20px', 'margin-top':'10px', 'padding': '0 20px', 'z-index': '50'})
        ]),
    ], style={'display': 'flex', 'justify-content': 'space-evenly', 'align-items': 'center', 'margin-bottom': '20px', 'padding': '0 20px'}),
    
    html.Div(id='metrics-fields-setup', children=[
        html.H3(children='Selecione as métricas secundárias desejadas', style={'margin-bottom': '10px', 'color': 'white', 'text-align': 'center'}),
        html.Div(children=[
            dcc.Checklist(
                id='secundary-metrics-checklist',
                options=[
                    {'label': 'Alcance', 'value': 'reach'},
                    {'label': 'Impressões', 'value': 'impressions'},
                    {'label': 'Frequência', 'value': 'frequency'},
                    {'label': 'CTR', 'value': 'CTR'},
                    {'label': 'Cliques no Link', 'value': 'clicks_link'},
                    {'label': 'Custo por Clique', 'value': 'cost_click'},
                    {'label': 'Engajamento', 'value': 'engagement'},
                    {'label': 'Custo por Engajamento', 'value': 'cost_engagement'},
                ],
                value=['reach', 'impressions', 'frequency', 'CTR', 'clicks_link', 'cost_click', 'engagement', 'cost_engagement'],
                style={'display': 'flex', 'justify-content': 'space-evenly', 'color': 'white', 'align-items': 'center', 'margin-bottom': '20px', 'padding': '0 20px'},
                inputStyle={'margin-right': '5px', 'margin-left': '30px'}
            ),
        ], style={'display': 'flex', 'justify-content': 'space-evenly', 'margin-bottom': '20px', 'padding': '0px 20px 10px 20px'}),
    ]),

    html.Div(children=[
        html.Div(children=[
            html.Div(id='reach-show', children=[
                html.H3(children='Alcance', style={'margin-bottom': '10px', 'color': 'white'}),
                html.H3(id='reach-field', 
                        style={
                            'margin-bottom': '10px', 
                            'color': 'white', 
                            'border': '2px solid #ddd', 
                            'border-radius': '5px',
                            'background-color': '#040911',
                            'text-align': 'center'
                            }),
            ]),
            html.Div(id='impressions-show', children=[
                html.H3(children='Impressões', style={'margin-bottom': '10px', 'color': 'white'}),
                html.H3(id='impressions-field', 
                        style={
                            'margin-bottom': '10px', 
                            'color': 'white', 
                            'border': '2px solid #ddd', 
                            'border-radius': '5px',
                            'background-color': '#040911',
                            'text-align': 'center'
                            }),
            ]),
        ]),
        html.Div(id='frequency-show', children=[
            html.Div(children=[
                html.H3(children='Frequência', style={'margin-bottom': '10px', 'color': 'white'}),
                html.H3(id='frequency-field', 
                        style={
                            'margin-bottom': '10px', 
                            'color': 'white', 
                            'border': '2px solid #ddd', 
                            'border-radius': '5px',
                            'background-color': '#040911',
                            'text-align': 'center'
                            }),
            ]),
            html.Div(id='ctr-show', children=[
                html.H3(children='CTR', style={'margin-bottom': '10px', 'color': 'white'}),
                html.H3(id='CTR-field', 
                        style={
                            'margin-bottom': '10px', 
                            'color': 'white', 
                            'border': '2px solid #ddd', 
                            'border-radius': '5px',
                            'background-color': '#040911',
                            'text-align': 'center'
                            }),
            ]),
        ]),
        html.Div(id='link-clicks-show', children=[
            html.Div(children=[
                html.H3(children='Cliques no Link', style={'margin-bottom': '10px', 'color': 'white'}),
                html.H3(id='clicks-link-field', 
                        style={
                            'margin-bottom': '10px', 
                            'color': 'white', 
                            'border': '2px solid #ddd', 
                            'border-radius': '5px',
                            'background-color': '#040911',
                            'text-align': 'center'
                            }),
            ]),
            html.Div(id='cpc-show', children=[
                html.H3(children='Custo por Clique', style={'margin-bottom': '10px', 'color': 'white'}),
                html.H3(id='cost-click-field', 
                        style={
                            'margin-bottom': '10px', 
                            'color': 'white', 
                            'border': '2px solid #ddd', 
                            'border-radius': '5px',
                            'background-color': '#040911',
                            'text-align': 'center'
                            }),
            ]),
        ]),
        html.Div(children=[
            html.Div(id='engegament-show', children=[
                html.H3(children='Engajamento', style={'margin-bottom': '10px', 'color': 'white'}),
                html.H3(id='engagement-field', 
                        style={
                            'margin-bottom': '10px', 
                            'color': 'white', 
                            'border': '2px solid #ddd', 
                            'border-radius': '5px',
                            'background-color': '#040911',
                            'text-align': 'center'
                            }),
            ]),
            html.Div(id='cost-engagement-show', children=[
                html.H3(children='Custo por Engajamento', style={'margin-bottom': '10px', 'color': 'white'}),
                html.H3(id='cost-engagement-field', 
                        style={
                            'margin-bottom': '10px', 
                            'color': 'white', 
                            'border': '2px solid #ddd', 
                            'border-radius': '5px',
                            'background-color': '#040911',
                            'text-align': 'center'
                            }),
            ]),
        ]),
    ], style={'display': 'flex', 'justify-content': 'space-evenly', 'margin-bottom': '20px', 'padding': '0 20px'}),

    html.Hr(style={'page-break-after': 'always', 'margin-bottom': '100px'}),

    html.Div(children=[
        html.Div(id='spend-graph-field',children=[
            html.H3(children='Valor usado por Conjunto de Anúncio', style={'margin-bottom': '10px', 'color': 'white', 'text-align': 'center'}),
            dcc.Graph(id='spend-graph', figure={}),
        ], style={'display': 'none'}),

        html.Div(id= 'msg-graph-field',children=[
            html.H3(children='Conversas iniciadas por Conjunto de Anúncio', style={'margin-bottom': '10px', 'color': 'white', 'text-align': 'center'}),
            dcc.Graph(id='msg-graph', figure={}),
        ], style={'display': 'none'}),
    ], style={'display': 'flex', 'justify-content': 'space-evenly', 'margin-bottom': '20px', 'padding': '0 20px'}),

    html.Div(id='table-field', children=[
        dash_table.DataTable(data=[], page_size=30, id='table', style_table={'overflowX': 'auto', 'margin': 'auto', 'width': '80%'}),
    ], style={'display': 'none'}),


], style={'background-color': '#081425'})



@app.callback(
    [Output('spend-show', 'style'),
     Output('msg-show', 'style'),
     Output('cost-msg-show', 'style'),
     Output('funnel-show', 'style'),
     Output('campaigns-show', 'style'),
     Output('campaigns-names-show', 'style')],
    [Input('main-metrics-checklist', 'value')]
)
def show_main_metrics(metrics_value):
    return [{'display': 'block'} if 'spend' in metrics_value else {'display': 'none'},
            {'display': 'block'} if 'total_msg' in metrics_value else {'display': 'none'},
            {'display': 'block'} if 'cost_per_msg' in metrics_value else {'display': 'none'},
            {'display': 'block'} if 'funnel' in metrics_value else {'display': 'none'},
            {'display': 'block'} if 'campaigns' in metrics_value else {'display': 'none'},
            {'display': 'block'} if 'campaigns_names' in metrics_value else {'display': 'none'}]

@app.callback(
    [Output('reach-show', 'style'),
     Output('impressions-show', 'style'),
     Output('frequency-show', 'style'),
     Output('ctr-show', 'style'),
     Output('link-clicks-show', 'style'),
     Output('cpc-show', 'style'),
     Output('engegament-show', 'style'),
     Output('cost-engagement-show', 'style')],
    [Input('secundary-metrics-checklist', 'value')]
)
def show_secundary_metrics(metrics_value):
    return [{'display': 'block'} if 'reach' in metrics_value else {'display': 'none'},
            {'display': 'block'} if 'impressions' in metrics_value else {'display': 'none'},
            {'display': 'block'} if 'frequency' in metrics_value else {'display': 'none'},
            {'display': 'block'} if 'CTR' in metrics_value else {'display': 'none'},
            {'display': 'block'} if 'clicks_link' in metrics_value else {'display': 'none'},
            {'display': 'block'} if 'cost_click' in metrics_value else {'display': 'none'},
            {'display': 'block'} if 'engagement' in metrics_value else {'display': 'none'},
            {'display': 'block'} if 'cost_engagement' in metrics_value else {'display': 'none'}]

@app.callback(
    [Output('date-field', 'style')],
    [Input('client-dropdown', 'value')],
)
def show_date_field(cliente_value):
    if cliente_value is not None:
        return [{'display': 'flex', 'flex-direction': 'column', 'justify-content': 'center', 'align-items': 'top', 'margin-bottom': '20px', 'padding': '0 20px'}]
    return [{'display': 'none'}]

@app.callback(
    [Output('loading-token-output', 'children'),
     Output('client-field', 'style'),
     Output('token-feedback-msg', 'children'),
     Output('client-dropdown', 'options')],
    [Input('token-button', 'n_clicks')],
    [State('token-input', 'value')]
)
def show_client_field(n_clicks, token_value):
    if n_clicks > 0:
        if token_value is None:
            return ['', {'display': 'none'}, html.H4('STATUS: Insira o Token de Autenticação!', style={'text-align': 'center', 'color': 'red', 'background-color': 'white'}), {}]
        
        client_list = get_client_list(token_value)
        
        if process_error(client_list):
            return ['', {'display': 'none'},html.H4('STATUS: Token Inválido!', style={'text-align': 'center', 'color': 'red', 'background-color': 'white'}), {}] 
        
        client_list_df = pd.json_normalize(client_list['data'])
        client_list_df = client_list_df.rename(columns={'id': 'value', 'name': 'label'})
        client_list_df = client_list_df.astype({'value': str, 'label': str})
        client_list_df = client_list_df.sort_values(by='label')
        client_list_options = client_list_df.to_dict('records')

        return ['', {'display': 'block'},html.H5('STATUS: Token Válido!', style={'text-align': 'center', 'color': 'Green', 'background-color': 'white'}), client_list_options]
    return ['', {'display': 'none'}, html.H5('STATUS: Aguardando Envio do Token...', style={'text-align': 'center', 'color': 'white'}), {}]


@app.callback(
    [Output('Autentication-fields', 'style'),
     Output('table-field', 'style'),
     Output('metrics-fields-setup', 'style'),
     Output('presentation-fields-setup', 'style'),
     Output('presentation-button', 'style')],
    [Input('presentation-button', 'n_clicks')]
)
def show_auth_fields(n_clicks):
    if n_clicks%2 == 0:
        return [{'display': 'block'}, 
                {'display': 'block'},
                {'margin-bottom': '20px', 'padding': '0 20px', 'border': '2px solid #ddd', 'border-radius': '5px', 'background-color': '#040911'},
                {'margin-top': '20px','margin-bottom': '20px', 'padding': '0 20px', 'border': '2px solid #ddd', 'border-radius': '5px', 'background-color': '#040911'},
                {'background-color': '#4CAF50', 'color': 'white', 'padding': '10px 20px', 'border': 'none', 'border-radius': '4px', 'margin': 'auto', 'display': 'block', 'cursor': 'pointer'}]
    
    return [{'display': 'none'},
            {'display': 'none'}, 
            {'display': 'none'},
            {'display': 'none'},
            {'background-color': '#081425', 'color': 'white', 'padding': '10px 20px', 'border': '2px solid #000000', 'border-radius': '4px', 'margin': 'auto', 'display': 'block', 'cursor': 'pointer'}]

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
    [Output('feedback-msg', 'children'),
     Output('loading-enviar', 'children'),
     Output('campaign-dropdown', 'options'),
     Output('campaign-dropdown', 'value'),
     Output('data-store', 'data')],
    [Input('submit-button', 'n_clicks')],
    [State('token-input', 'value'),
     State('client-dropdown', 'value'),
     State('reach-input', 'value'),
     State('interval-type', 'value'),
     State('date-range', 'start_date'),
     State('date-range', 'end_date'),
     State('date-picker', 'date',)]
)
def get_data(n_clicks, token_value, cliente_value, reach_input, interval_type, start_date, end_date, single_date):
    if n_clicks > 0:
        
        if token_value is None:
            return [
                html.Div('Insira o Token!', style={'text-align': 'center', 'color': 'red', 'background-color': 'white'}),
                '',
                [], 
                '',
                {}
                ]
        
        if cliente_value is None:
            return [
                html.Div('Selecione o cliente desejado!', style={'text-align': 'center', 'color': 'red', 'background-color': 'white'}),
                '',
                [], 
                '',
                {}
                ]
        
        if interval_type == 'range' and (start_date is None or end_date is None):
            return [
                html.Div('Selecione as datas!', style={'text-align': 'center', 'color': 'red', 'background-color': 'white'}),
                '',
                [], 
                '',
                {}
                ]
        
        elif interval_type == 'single_day' and single_date is None:
            return [
                html.Div('Selecione a data!', style={'text-align': 'center', 'color': 'red', 'background-color': 'white'}),
                '',
                [], 
                '',
                {}
                ]
        
        if reach_input is None:
            return [
                html.Div('Insira o Alcance total!', style={'text-align': 'center', 'color': 'red', 'background-color': 'white'}),
                '',
                [], 
                '',
                {}
                ]

        updated_json_content = get_updated_data(token_value, cliente_value, interval_type, start_date, end_date, single_date)

        if process_error(updated_json_content) or process_empty_data(updated_json_content):
            return [update_feedback_message(updated_json_content), '', [], '', {}]
        
        updated_df = process_data(updated_json_content)
        updated_df['age_min'] = None
        updated_df['age_max'] = None
        updated_df['gender'] = None
        
        for index, row in updated_df.iterrows():
            adset_id = row['adset_id']
            ad_set_targeting = get_targeting_data(token_value, adset_id)
            if not ad_set_targeting.empty:
                updated_df.at[index, 'age_min'] = ad_set_targeting['targeting.age_min'].values[0]
                updated_df.at[index, 'age_max'] = ad_set_targeting['targeting.age_max'].values[0]
            
        campaign_options = [{'label':'Todas as campanhas', 'value':''}]
        all_campaign_options = campaign_options + [{'label': i, 'value': i} for i in updated_df['campaign_name'].unique()]
        
        return [update_feedback_message(updated_json_content), '', all_campaign_options, campaign_options[0]['value'], updated_df.to_dict('records')]
    
    return [html.Div('STATUS: Aguardando Envio...', style={'text-align': 'center', 'color': 'white'}), '', [], '', {}]

@app.callback(
    [Output('campaigns-names', 'children'),
     Output('table', 'data'),
     Output('spend-field', 'children'),
     Output('date-begin-field', 'children'),
     Output('date-end-field', 'children'),
     Output('total-msg-field', 'children'),
     Output('cost-per-msg-field', 'children'),
     Output('reach-field', 'children'),
     Output('impressions-field', 'children'),
     Output('frequency-field', 'children'),
     Output('CTR-field', 'children'),
     Output('clicks-link-field', 'children'),
     Output('cost-click-field', 'children'),
     Output('engagement-field', 'children'),
     Output('cost-engagement-field', 'children'),
     Output('spend-graph-field', 'style'),
     Output('spend-graph', 'figure'),
     Output('msg-graph-field', 'style'),
     Output('msg-graph', 'figure'),
     Output('funnel-graph-field', 'style'),
     Output('funnel-graph', 'figure')],
    [Input('campaign-dropdown', 'value')],
    [State('reach-input', 'value'),
     State('interval-type', 'value'),
     State('date-range', 'start_date'),
     State('date-range', 'end_date'),
     State('date-picker', 'date'),
     State('data-store', 'data')]
)
def update_graph(campaign_value, reach_input, interval_type, start_date, end_date, single_date, df):
    if df != {}:
        updated_df = pd.DataFrame(df)
        if campaign_value != '':
            updated_df = updated_df[updated_df['campaign_name'] == campaign_value]

        updated_df = updated_df.sort_values(by='adset_name', ascending=True)

        campaign_elements = generate_campaign_elements(updated_df)

        spend = get_total_investment(updated_df)
        spend = f'R$ {spend:.2f}'.replace('.', ',')

        date_begin = start_date if interval_type == 'range' else single_date
        date_begin = date_begin.replace('-', '/')
        date_begin = date_begin.split('/')
        date_begin = f'{date_begin[2]}/{date_begin[1]}/{date_begin[0]}'

        date_end = end_date if interval_type == 'range' else single_date
        date_end = date_end.replace('-', '/')
        date_end = date_end.split('/')
        date_end = f'{date_end[2]}/{date_end[1]}/{date_end[0]}'

        total_msg = get_total_msg(updated_df)

        cost_per_msg = get_cost_per_msg(updated_df)
        cost_per_msg = f'R$ {cost_per_msg:.2f}'.replace('.', ',')

        if campaign_value == '':
            reach = reach_input
        else:
            reach = updated_df['reach'].astype(int).sum()

        impressions = get_impressions(updated_df)

        frequency = get_frequency(updated_df, reach)
        frequency = f'{frequency:.2f}'.replace('.', ',')

        ctr = get_ctr(updated_df)
        ctr = f'{ctr:.2f}%'.replace('.', ',')

        clicks_link = get_clicks_link(updated_df)

        cost_click = get_cost_click(updated_df)
        cost_click = f'R$ {cost_click:.2f}'.replace('.', ',')

        engagement = get_engagement(updated_df)

        cost_engagement = get_cost_engagement(updated_df)
        cost_engagement = f'R$ {cost_engagement:.2f}'.replace('.', ',')

        updated_df = updated_df.astype({'spend': float, 'messaging_conversation_started_7d': int})
        updated_df = updated_df.sort_values(by='adset_name', ascending=False)

        spend_graph = px.pie(updated_df, 
                                values='spend', 
                                names='adset_name',
                                labels={'spend': 'Valor Gasto (R$)', 'adset_name': 'Conjunto de Anúncios'}
                                )
        
        spend_graph.update_traces(textinfo='percent+value')
        spend_graph.update_layout(paper_bgcolor='#143159', 
                                    font_color='white', 
                                    height=500, 
                                    width=500, 
                                    legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5)
                                    )

        msg_graph = px.pie(updated_df, 
                            values='messaging_conversation_started_7d', 
                            names='adset_name', 
                            labels={'messaging_conversation_started_7d': 'Conversas Iniciadas', 'adset_name': 'Conjunto de Anúncios'}
                            )
        
        msg_graph.update_traces(textinfo='percent+value')
        msg_graph.update_layout(paper_bgcolor='#143159', 
                                font_color='white', 
                                height=500, 
                                width=500, 
                                legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5)
                                )
        
        common_colors = dict(zip(updated_df['adset_name'], px.colors.qualitative.Plotly))

        spend_graph.update_traces(marker=dict(colors=updated_df['adset_name'].map(common_colors)))
        msg_graph.update_traces(marker=dict(colors=updated_df['adset_name'].map(common_colors)))


        spend_funnel = get_total_investment(updated_df)
        cost_msg_funnel = round(spend_funnel/total_msg, 2)

        funnel_data = dict(
            value = [spend_funnel, total_msg, cost_msg_funnel],
            labels = ['Investimento (R$)', 'Conversas Iniciadas', 'CPC (R$)']
        )

        funnel_graph = px.funnel(funnel_data,
                                        y='labels',
                                        x='value',
                                        )
        funnel_graph.update_traces(textinfo='value+label', textfont=dict(color='white'))
        funnel_graph.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                                    plot_bgcolor='#081425',
                                    font_color='white',
                                    height=300,
                                    width=400,
                                    showlegend=False,
                                    yaxis=dict(showgrid=False, visible=False),
                                    )
        

        return [campaign_elements,
                updated_df.to_dict('records'),
                spend,
                date_begin, 
                date_end, 
                total_msg, 
                cost_per_msg, 
                reach, 
                impressions, 
                frequency, 
                ctr, 
                clicks_link, 
                cost_click, 
                engagement, 
                cost_engagement, 
                {'display': 'block', 'margin-bottom': '100px', 'margin-top': '100px'}, 
                spend_graph, 
                {'display': 'block', 'margin-bottom': '100px', 'margin-top': '100px'}, 
                msg_graph, 
                {'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'}, 
                funnel_graph]
    return ['',
            [],
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            {'display': 'none'},
            {},
            {'display': 'none'},
            {},
            {'display': 'none'},
            {}]


if __name__ == '__main__':
    app.run(debug=True)
