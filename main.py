import streamlit as st
import telebot
import datetime
import time

# Configurações de autenticação do bot Telegram
chave = st.secrets["lista_chave"]['list_key']
print(chave)
bot_token = chave[0]

# substituir o valor abaixo pelo id do canal que deseja monitorar
CANAL_ID = int(chave[1])

# substituir o valor abaixo pelo id do chat que receberá o alerta
chat_id = [chave[2], chave[3]]


# Cria uma instância do bot Telegram
bot = telebot.TeleBot(bot_token)


# Define o intervalo de tempo (em segundos) para verificar se há novas mensagens
INTERVALO_TEMPO_SEM_MENSAGENS = 30*60  # 30 minutos

# Variáveis para controlar o horário da última mensagem e o último aviso de falta de mensagens
ultima_mensagem_horario = None
ultimo_aviso_horario = None

# Função que puxa as mensagens do canal
def atualizacoes():
    # Obtém as atualizações do bot
    atualizacoes = bot.get_updates()
    # Filtra as mensagens do canal especificado
    mensagens = [mensagem for mensagem in atualizacoes if
                 mensagem.channel_post != None and mensagem.channel_post.chat.id == CANAL_ID]
    return mensagens

# Função que verifica se há novas mensagens no canal
def verificar_mensagens():
    global ultima_mensagem_horario, ultimo_aviso_horario, tamanho_mensagens_anterior, texto

    mensagens = atualizacoes()

    if mensagens != [] and tamanho_mensagens_anterior != len(mensagens):
        # Obtém o horário da primeira mensagem do dia
        horario_primeira_mensagem = datetime.datetime.fromtimestamp(mensagens[-1].channel_post.date)
        # Verifica se já passou da meia-noite
        if not ultima_mensagem_horario or horario_primeira_mensagem > ultima_mensagem_horario:
            # Atualiza a variável com o horário da última mensagem
            ultima_mensagem_horario = horario_primeira_mensagem
            # Envia a mensagem de notificação
            bot.send_message(chat_id=chat_id[0], text='O COMPUTADOR ESTÁ CONECTADO COM A INTERNET!')
            if texto != 'O COMPUTADOR ESTÁ CONECTADO COM A INTERNET!':
                texto = 'O COMPUTADOR ESTÁ CONECTADO COM A INTERNET!'
                bot.send_message(chat_id=chat_id[1], text='O GEDAE ESTÁ ABERTO!')
        tamanho_mensagens_anterior = len(mensagens)

    else:
        # Verifica se já passou o intervalo de tempo sem receber novas mensagens
        agora = datetime.datetime.now()
        if ultimo_aviso_horario and agora - ultimo_aviso_horario < datetime.timedelta(
                seconds=INTERVALO_TEMPO_SEM_MENSAGENS):
            return

        if not ultima_mensagem_horario or agora - ultima_mensagem_horario > datetime.timedelta(
                seconds=INTERVALO_TEMPO_SEM_MENSAGENS):
            # Atualiza a variável com o horário do último aviso
            ultimo_aviso_horario = agora
            # Envia a mensagem de alerta
            bot.send_message(chat_id=chat_id[0], text='PERDA DE CONEXÃO COM A INTERNET!')
            if texto != 'PERDA DE CONEXÃO COM A INTERNET!':
                texto = 'PERDA DE CONEXÃO COM A INTERNET!'
                bot.send_message(chat_id=chat_id[1], text='O GEDAE ESTÁ FECHADO!')

tamanho_mensagens_anterior = 0
texto = ''
# Loop infinito para verificar se há novas mensagens
while True:
    try:
        verificar_mensagens()
    except Exception as e:
        print(e)

    # Define o intervalo de tempo para verificar novamente se há novas mensagens
    time.sleep(10)
