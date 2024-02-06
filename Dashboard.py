import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, dash_table, Input, Output, State

import requests

app = Dash(__name__)
server = app.server

url_default = 'https://graph.facebook.com/v19.0/'
cliente = ''
insights = '/insights?'
token = ''
params = {
    'level': 'adset',
    'fields': 'campaign_name,adset_name,spend,cpc,ctr,clicks,impressions,reach,actions,frequency',
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
              }),

    
    html.Div(id='Autentication-fields',children=[
        html.H2(children='Informações de Autenticação', 
                style={'text-align': 'center', 
                    'color': 'white',
                    'background-color': '#143159',
                    'line-height': '100px',
                    'margin-top': '0px',
                    'align-items': 'center'}),
        html.Div(children=[
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
                html.H3(children='Insira o Alcance total', 
                        style={'margin-bottom': '10px', 
                            'color': 'white'}),
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
                            'cursor': 'pointer',}),
                ]),
            ]),
            html.Div(children=[
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
            ]),
        ], style={'display': 'flex', 'justify-content': 'space-evenly', 'margin-bottom': '20px', 'padding': '0 20px'}),
        
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
    ], style={'display': 'none', 'margin-bottom': '0px'}),


    html.H2(children='Dashboard de Anúncios MetaAds', 
            style={'text-align': 'center', 
                   'color': 'white',
                   'background-color': '#143159',
                   'line-height': '100px',
                   'margin-top': '0px',}),
    
    html.Button('Modo apresentação', id='presentation-button', n_clicks=0, style={
        'background-color': '#4CAF50',
        'color': 'white',
        'padding': '10px 20px',
        'border': 'none',
        'border-radius': '4px',
        'margin': 'auto',
        'display': 'block',
        'cursor': 'pointer'
        }),

    html.Div(children=[
        html.Div(children=[
            html.Div(children=[
                html.H3(children='Período', style={'margin-bottom': '10px', 'color': 'white'}),
            ]),
            html.Div(children=[
                html.Div(children=[
                    html.H6(children='Data Inicial', style={'margin-bottom': '10px', 'color': 'white'}),
                    html.H6(id='date-begin-field', 
                            style={
                                'margin-bottom': '10px', 
                                'color': 'white', 
                                'border': '2px solid #ddd', 
                                'border-radius': '5px',
                                'background-color': '#040911',
                                'text-align': 'center'
                                }),
                ]),
                html.Div(children=[
                    html.H6(children='Data Final', style={'margin-bottom': '10px', 'color': 'white'}),
                    html.H6(id='date-end-field', 
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
                        'text-align': 'center'
                        }),
        ]),
        html.Div(children=[
            html.H3(children='Conversas Iniciadas', style={'margin-bottom': '10px', 'color': 'white'}),
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
        html.Div(children=[
            html.H3(children='Custo por Conversas Iniciadas', style={'margin-bottom': '10px', 'color': 'white'}),
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
    ], style={'display': 'flex', 'justify-content': 'space-evenly', 'margin-bottom': '20px', 'padding': '0 20px'}),

    html.Div(children=[
        html.Div(children=[
            html.Div(children=[
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
            html.Div(children=[
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
        html.Div(children=[
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
            html.Div(children=[
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
        html.Div(children=[
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
            html.Div(children=[
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
            html.Div(children=[
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
            html.Div(children=[
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

    html.Div(children=[
        html.Div(id='funnel-graph-field', children=[
            dcc.Graph(id='funnel-graph', figure={}),
        ], style={'display': 'none'}),
    ], style={'display': 'flex', 'justify-content': 'space-evenly', 'margin-bottom': '20px', 'padding': '0 20px'}),

    html.Div(children=[
        html.Div(id='spend-graph-field',children=[
            html.H3(children='Gráfico de valor usado por campanha', style={'margin-bottom': '10px', 'color': 'white'}),
            dcc.Graph(id='spend-graph', figure={}),
        ], style={'display': 'none'}),

        html.Div(id= 'msg-graph-field',children=[
            html.H3(children='Gráfico de conversas iniciadas por campanha', style={'margin-bottom': '10px', 'color': 'white'}),
            dcc.Graph(id='msg-graph', figure={}),
        ], style={'display': 'none'}),
    ], style={'display': 'flex', 'justify-content': 'space-evenly', 'margin-bottom': '20px', 'padding': '0 20px'}),
    html.Div(id='table-field', children=[
        dash_table.DataTable(data=[], page_size=30, id='table', style_table={'overflowX': 'auto', 'margin': 'auto', 'width': '80%'}),
    ], style={'display': 'none'}),
], style={'background-color': '#081425'})

@app.callback(
    [Output('Autentication-fields', 'style'),
     Output('table-field', 'style'),
     Output('presentation-button', 'style')],
    [Input('presentation-button', 'n_clicks')]
)
def show_auth_fields(n_clicks):
    if n_clicks%2 == 0:
        return {'display': 'block'}, {'display': 'block'}, {'background-color': '#4CAF50', 
                                                            'color': 'white', 
                                                            'padding': '10px 20px', 
                                                            'border': 'none', 
                                                            'border-radius': '4px', 
                                                            'margin': 'auto', 
                                                            'display': 'block', 
                                                            'cursor': 'pointer'}
    
    return {'display': 'none'}, {'display': 'none'}, {'background-color': '#081425',
                                                        'color': 'white',
                                                        'padding': '10px 20px',
                                                        'border': '2px solid #000000',
                                                        'border-radius': '4px',
                                                        'margin': 'auto',
                                                        'display': 'block',
                                                        'cursor': 'pointer'}

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
    [Input('submit-button', 'n_clicks')],
    [State('token-input', 'value'),
     State('client-input', 'value'),
     State('reach-input', 'value'),
     State('interval-type', 'value'),
     State('date-range', 'start_date'),
     State('date-range', 'end_date'),
     State('date-picker', 'date')]
)
def update_graph(n_clicks, token_value, cliente_value, reach_input, interval_type, start_date, end_date, single_date):
    if n_clicks > 0:
        
        if token_value is None:
            return [], html.Div('Insira o Token!', style={'text-align': 'center', 'color': 'red', 'background-color': 'white'}), '', '', '', '', '', '', '', '', '', '', '', '', '', {'display': 'none'}, {}, {'display': 'none'}, {}, {'display': 'none'}, {}
                
        if cliente_value is None:
            return [], html.Div('Insira o Código do cliente desejado!', style={'text-align': 'center', 'color': 'red', 'background-color': 'white'}), '', '', '', '', '', '', '', '', '', '', '', '', '', {'display': 'none'}, {}, {'display': 'none'}, {}, {'display': 'none'}, {}
        
        if reach_input is None:
            return [], html.Div('Insira o Alcance total!', style={'text-align': 'center', 'color': 'red', 'background-color': 'white'}), '', '', '', '', '', '', '', '', '', '', '', '', '', {'display': 'none'}, {}, {'display': 'none'}, {}, {'display': 'none'}, {}

        updated_json_content = get_updated_data(token_value, cliente_value, interval_type, start_date, end_date, single_date)

        if process_error(updated_json_content) or process_empty_data(updated_json_content):
            return [], update_feedback_message(updated_json_content), '', '', '', '', '', '', '', '', '', '', '', '', '', {'display': 'none'}, {}, {'display': 'none'}, {}, {'display': 'none'}, {}
        
        updated_df = process_data(updated_json_content)
        spend = get_total_investment(updated_df)
        spend = f'R$ {spend:.2f}'.replace('.', ',')

        date_begin = start_date if interval_type == 'range' else single_date
        date_end = end_date if interval_type == 'range' else single_date

        total_msg = get_total_msg(updated_df)

        cost_per_msg = get_cost_per_msg(updated_df)
        cost_per_msg = f'R$ {cost_per_msg:.2f}'.replace('.', ',')

        reach = reach_input

        impressions = get_impressions(updated_df)

        frequency = get_frequency(updated_df, reach_input)
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

        spend_graph = px.pie(updated_df, 
                             values='spend', 
                             names='adset_name',
                             labels={'spend': 'Valor Gasto (R$)', 'adset_name': 'Conjunto de Anúncios'}
                             )
        
        spend_graph.update_traces(textinfo='percent+value')
        spend_graph.update_layout(paper_bgcolor='#143159', 
                                  font_color='white', 
                                  height=600, 
                                  width=600, 
                                  legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                                  )

        msg_graph = px.pie(updated_df, 
                           values='messaging_conversation_started_7d', 
                           names='adset_name', 
                           labels={'messaging_conversation_started_7d': 'Conversas Iniciadas', 'adset_name': 'Conjunto de Anúncios'}
                           )
        
        msg_graph.update_traces(textinfo='percent+value')
        msg_graph.update_layout(paper_bgcolor='#143159', 
                                font_color='white', 
                                height=600, 
                                width=600, 
                                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                                )
        
        spend_funnel = get_total_investment(updated_df)
        cost_msg_funnel = round(spend_funnel/total_msg, 2)

        funnel_data = dict(
            value = [spend_funnel, total_msg, cost_msg_funnel],
            labels = ['Investimento (R$)', 'Conversas Iniciadas', 'Custo por Conversa Iniciada (R$)']
        )

        funnel_graph = px.funnel(funnel_data,
                                      y='labels',
                                      x='value',
                                      )
        funnel_graph.update_traces(textinfo='value+label', textfont=dict(color='white'))
        funnel_graph.update_layout(paper_bgcolor='#143159',
                                   plot_bgcolor='#143159',
                                   font_color='white',
                                   height=600, 
                                   width=1200,
                                   showlegend=False,
                                   yaxis=dict(showgrid=False, visible=False),
                                   )

        return updated_df.to_dict('records'), update_feedback_message(updated_json_content), spend, date_begin, date_end, total_msg, cost_per_msg, reach, impressions, frequency, ctr, clicks_link, cost_click, engagement, cost_engagement, {'display': 'block'}, spend_graph, {'display': 'block'}, msg_graph, {'display': 'flex'}, funnel_graph

    return [], html.H3('STATUS: Aguardando Envio...', style={'text-align': 'center', 'color': 'white'}), '', '', '', '', '', '', '', '', '', '', '', '', '', {'display': 'none'}, {}, {'display': 'none'}, {}, {'display': 'none'}, {}


if __name__ == '__main__':
    app.run(debug=True)
