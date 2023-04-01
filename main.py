import time
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import schedule
import telebot
import pytz
import pandas as pd

# Define o intervalo de tempo desejado em segundos
intervalo_tempo = 70
referencia_consumo = 1350

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
    try:
        source_sheet = pd.DataFrame(client.open_by_key(SOURCE_SPREADSHEET_ID).sheet1.get_all_records())
        target_sheet = pd.DataFrame(client.open_by_key(TARGET_SPREADSHEET_ID).sheet1.get_all_records())
        horario_atual = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
        horário_ultima_linha_rpi = pd.to_datetime(target_sheet['DATA-RPI']).dropna().tail(1).reset_index(drop=True)[0]
        horário_ultima_linha_pc = pd.to_datetime(target_sheet['DATA-PC']).dropna().tail(1).reset_index(drop=True)[0]
        consumo_ultima_linha = source_sheet[['Potência Ativa A', 'Potência Ativa B', 'Potência Ativa C']].tail(1).reset_index(drop=True).sum(axis=1)[0]

        rpi_on = datetime.strptime(horario_atual, '%Y-%m-%d %H:%M:%S').timestamp() - horário_ultima_linha_rpi.timestamp() <= intervalo_tempo
        pc_on = datetime.strptime(horario_atual, '%Y-%m-%d %H:%M:%S').timestamp() - horário_ultima_linha_pc.timestamp() <= intervalo_tempo
        consumo_alto = consumo_ultima_linha > referencia_consumo

        condicao_1 = not rpi_on and not pc_on and consumo_alto
        condicao_2 = not pc_on and (rpi_on or consumo_alto)
        condicao_3 = rpi_on or pc_on or consumo_alto

        energia = 0
        if condicao_1:
            energia = 1
            #print('O GEDAE ESTÁ SEM ENERGIA!')
        elif condicao_2:
            energia = 2
            #print('HOUVE QUEDA DE ENERGIA NO GEDAE, RELIGUE O COMPUTADOR!')
        else:
            #print('O GEDAE ESTÁ FUNCIONANDO NORMALMENTE!')
            pass

        aberto = 1
        if condicao_3:
            #print('O GEDAE ESTÁ ABERTO!')
            pass
        else:
            aberto = 0
            #print('O GEDAE ESTÁ FECHADO!')

        if aberto == 1:
            if energia == 0:
                print('O GEDAE ESTÁ ABERTO E TUDO ESTÁ FUNCIONANDO NORMALMENTE!')
                bot.send_message(chat_id=chat_id[0], text='O COMPUTADOR ESTÁ CONECTADO COM A INTERNET!')
                if texto != 'O COMPUTADOR ESTÁ CONECTADO COM A INTERNET!':
                    texto = 'O COMPUTADOR ESTÁ CONECTADO COM A INTERNET!'
                    bot.send_message(chat_id=chat_id[1], text='O GEDAE ESTÁ ABERTO!')
            elif energia == 1:
                print('O GEDAE ESTÁ SEM ENERGIA!')
                bot.send_message(chat_id=chat_id[0], text='PERDA DE CONEXÃO COM A INTERNET E ALTO CONSUMO DE ENERGIA!')
                if texto != 'PERDA DE CONEXÃO COM A INTERNET E ALTO CONSUMO DE ENERGIA!':
                    texto = 'PERDA DE CONEXÃO COM A INTERNET E ALTO CONSUMO DE ENERGIA!'
                    bot.send_message(chat_id=chat_id[1], text='O GEDAE ESTÁ SEM ENERGIA!')
            elif energia == 2:
                print('O GEDAE ESTÁ ABERTO, MAS HOUVE QUEDA DE ENERGIA. RELIGUE O COMPUTADOR!')
                bot.send_message(chat_id=chat_id[0], text='SOMENTE O RASPBERRY PI ESTÁ CONECTADO COM A INTERNET, RELIGUE O COMPUTADOR!')
                if texto != 'SOMENTE O RASPBERRY PI ESTÁ CONECTADO COM A INTERNET, RELIGUE O COMPUTADOR!':
                    texto = 'SOMENTE O RASPBERRY PI ESTÁ CONECTADO COM A INTERNET, RELIGUE O COMPUTADOR!'
                    bot.send_message(chat_id=chat_id[1], text='ENERGIA RESTABELECIDA NO GEDAE!')
        else:
            print('O GEDAE ESTÁ FECHADO!')
            bot.send_message(chat_id=chat_id[0], text='PERDA DE CONEXÃO COM A INTERNET E BAIXO CONSUMO DE ENERGIA!')
            if texto != 'PERDA DE CONEXÃO COM A INTERNET E BAIXO CONSUMO DE ENERGIA!':
                texto = 'PERDA DE CONEXÃO COM A INTERNET E BAIXO CONSUMO DE ENERGIA!'
                bot.send_message(chat_id=chat_id[1], text='O GEDAE ESTÁ FECHADO!')
    except:
        bot.send_message(chat_id=chat_id[0], text='LIMITE DE LEITURA POR MINUTO EXCEDIDO!')
        time.sleep(60-datetime.datetime.now(tz).second)
        pass
    
# agenda a execução da função a cada 1 minuto
schedule.every(80-datetime.datetime.now(tz).second).seconds.do(verifica_planilha)

texto = ''
# loop principal para executar o agendador de tarefas
while True:
    schedule.run_pending()
