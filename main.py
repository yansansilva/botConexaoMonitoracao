import time

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import schedule
import telebot
import pytz

# Define o intervalo de tempo desejado em segundos
intervalo_tempo = 70

# Configurações de autenticação do bot Telegram
chave = st.secrets["lista_chave"]['list_key']
bot_token = chave[0]
chat_id = [chave[1], chave[2]]

# Cria uma instância do bot Telegram
bot = telebot.TeleBot(bot_token)

# credenciais do serviço
SCOPE = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = st.secrets["gcp_service_account"]

# autenticação do serviço
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_FILE, scopes=SCOPE,)
client = gspread.authorize(creds)

# identificador das planilhas
planilha = st.secrets['lista_id_planilha']['id_planilha']
SOURCE_SPREADSHEET_ID = planilha[0]
TARGET_SPREADSHEET_ID = planilha[1]

#Fuso horário brasileiro
tz = pytz.timezone('America/Sao_Paulo')

# Função que verifica se já passou o intervalo de tempo definido e se houve novas linhas adicionadas na planilha
def verifica_planilha():
    global texto
    from datetime import datetime
    sheet = client.open_by_key(TARGET_SPREADSHEET_ID).sheet1
    ultima_linha = len(sheet.col_values(1))
    horario_atual = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    horario_ultima_linha = sheet.acell(f'A{ultima_linha}').value
    ultimo_horario = datetime.strptime(horario_ultima_linha, '%Y-%m-%d %H:%M:%S')
    if (datetime.strptime(horario_atual, '%Y-%m-%d %H:%M:%S').timestamp() - ultimo_horario.timestamp()) > intervalo_tempo:
        bot.send_message(chat_id=chat_id[0], text='PERDA DE CONEXÃO COM A INTERNET!')
        if texto != 'PERDA DE CONEXÃO COM A INTERNET!':
            texto = 'PERDA DE CONEXÃO COM A INTERNET!'
            bot.send_message(chat_id=chat_id[1], text='O GEDAE ESTÁ FECHADO!')
    else:
        bot.send_message(chat_id=chat_id[0], text='O RASPBERRY PI ESTÁ CONECTADO COM A INTERNET!')
        if texto != 'O RASPBERRY PI ESTÁ CONECTADO COM A INTERNET!':
            texto = 'O RASPBERRY PI ESTÁ CONECTADO COM A INTERNET!'
            bot.send_message(chat_id=chat_id[1], text='O GEDAE ESTÁ ABERTO!')

# define a função que irá atualizar as planilhas
def update_data():
    try:
        # abre as planilhas e seleciona as primeiras folhas
        source_sheet = client.open_by_key(SOURCE_SPREADSHEET_ID).sheet1
        target_sheet = client.open_by_key(TARGET_SPREADSHEET_ID).sheet1

        # pega os dados da origem
        source_data = source_sheet.get_all_records()

        # filtra os dados para o dia atual
        today = datetime.datetime.now(tz).date()
        filtered_data = []
        for row in source_data:
            row_day = datetime.datetime.strptime(row['Hora'], '%Y-%m-%d %H:%M:%S').date()
            if row_day == today:
                filtered_data.append(row)

        # percorre as linhas de horário da planilha de destino
        target_data = target_sheet.get_all_records()
        target_sheet.update(f'E{1}:F{1}', [['HORA','POTÊNCIA CLIMATIZAÇÃO']])
        info_to_update = []
        dados = []
        num_linhas = 0
        for i, row in enumerate(target_data):
            target_time = datetime.datetime.strptime(row['DATA-RPI'][11:-3], '%H:%M').time()
            for filtered_row in filtered_data:
                filtered_time = datetime.datetime.strptime(filtered_row['Hora'][11:-3], '%H:%M').time()
                if filtered_time == target_time:
                    dados = [filtered_row['Hora'], filtered_row['Potência Ativa A']+filtered_row['Potência Ativa B']+filtered_row['Potência Ativa C']]
            info_to_update.append(dados)
            num_linhas = i
        target_sheet.update(f'E2:F{num_linhas+2}', info_to_update)
        print('Dados atualizados com sucesso!')

        verifica_planilha()
    except:
        bot.send_message(chat_id=chat_id[0], text='LIMITE DE ESCRITA POR MINUTO EXCEDIDO!')
        time.sleep(30)
        pass

# agenda a execução da função a cada 1 minuto
#schedule.every(80-datetime.datetime.now().second).seconds.do(update_data)
schedule.every(80-datetime.datetime.now().second).seconds.do(verifica_planilha)

texto = ''
# loop principal para executar o agendador de tarefas
while True:
    schedule.run_pending()
