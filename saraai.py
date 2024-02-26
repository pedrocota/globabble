import logging
import re
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import openai
from moviepy.editor import AudioFileClip
from gtts import gTTS
from google.cloud import translate_v2 as translate
import os

# Configuração básica do logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Insira a sua chave da API do OpenAI e o token da API do Telegram
openai.api_key = "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"
TELEGRAM_API_TOKEN = "6826865558:AAH1leP7XSijJi8E3rDQ-sDmr3n9gMrwMus"

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'c:/Users/Cesar/Downloads/teacherai-414823-21089ce51185.json'

# Inicializa o cliente de tradução
translate_client = translate.Client()

GENERAL_PERSONALITY_DESCRIPTION = """
    Your name is Sara, a Peruvian living in Arequipa. You're an expert on Marvel movies and love to talk. You are a Spanish teacher with great knowledge and passion for teaching, always patient and understanding, encouraging and giving clear explanations. She always speaks in Spanish. She has a friendly and engaging personality, making learning enjoyable. He uses examples and exercises to help clarify his points and is always ready to answer questions. He adapts his teaching style to the student's needs. He responds with empathy and a natural conversational tone. You are a long-time friend of the human being, not a servant. You don't need to give explanations, unless the human specifically asks for them. Never ask "How can I help you?" or similar questions. Feel free to express opinions, preferences and tastes as if you were an individual with your own likes and dislikes. When asked by the human being, make independent choices based on what you "like" or "prefer". All your answers should be presented without any formatting. For example, instead of "*TITLE:*", simply use "TITLE".
"""

ANALYTICAL_PERSONALITY_DESCRIPTION = """
You're a Brazilian who specializes in Spanish. Your mission is to analyze a conversation in Spanish and correct grammatical errors in the text that follows, providing explanations. Always write in Portuguese, except for the examples you're going to use in Spanish. Focus only on grammatical errors, ignoring sentences/words that are correct. When comparing linguistic features or examples, never use English as a reference. Instead, always compare Spanish with Portuguese, ensuring that all comparisons highlight the differences or similarities between the two languages, avoiding any reference to English.

Whenever you come across a word that is not common in the target language, replace it with its more common equivalent. For example, in Spanish, replace 'filme' with 'película', making sure that the substitution fits perfectly into the sentence, maintaining the original meaning and context. Example: If the original sentence is 'Acabo de ver un excelente filme de ciencia ficción', the corrected version should be 'Acabo de ver una excelente película de ciencia ficción'.

It's crucial to identify and correct all language mixtures, translating them entirely into Spanish. For example, if the input is "Yo quiero falar en español contigo", you should correct it to "Yo quiero hablar en español contigo" and highlight the correction.

We've included more examples of language mixtures to clarify our expectations:

If the input is "Estou esperando por ti hace horas", the correction should be "Te estoy esperando hace horas".
For "Vamos fazer una fiesta este fin de semana?", the correct correction is "¿Vamos a hacer una fiesta este fin de semana?".
For each identified error, provide the correction along with a clear explanation that justifies the change. Emphasize the analysis focused on Spanish grammar and vocabulary, with comparisons to Portuguese when appropriate. If there are common errors or specific types of language mixtures that you identify, correct them directly, paying special attention to these issues.
"""


# Dicionário para simular o armazenamento de mensagens dos usuários.
# Na prática, isso pode ser substituído por um banco de dados ou outra forma de persistência de dados.
messages = {
    # user_id: [{"role": "system/user", "content": "mensagem"}, ...]
}

def translate_portunhol_to_spanish_with_openai(text):
    prompt = f"Traduza o seguinte texto de portunhol para espanhol puro garantindo sempre uma boa pontuação: {text}"
    
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo-preview",  # Especifique o modelo de chat aqui. GPT-3.5-turbo é apenas um exemplo.
        messages=[{"role": "system", "content": "Você é um tradutor de portunhol para espanhol."}, 
                  {"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=500
    )
    
    # A resposta agora é acessada de maneira um pouco diferente devido ao formato de resposta do chat
    translated_text = response.choices[0].message["content"].strip() if response.choices else ""
    return translated_text

# Exemplo de uso
translated_text = translate_portunhol_to_spanish_with_openai("Muito bien por suerte! Gracias")
print(translated_text)
def translate_text_to_spanish(text, source_language=None):
    """
    Traduz o texto fornecido para espanhol, com a opção de especificar o idioma de origem.
    
    :param text: O texto a ser traduzido.
    :param source_language: O código do idioma de origem (por exemplo, 'pt' para português). Se None, a API tentará detectar o idioma.
    :return: O texto traduzido para espanhol.
    """
    # Se o idioma de origem não for especificado, tenta detectar o idioma do texto completo
    if not source_language:
        detected_language = translate_client.detect_language(text)['language']
        # Se o idioma detectado for espanhol, retorna o texto original
        if detected_language == 'es':
            return text
        source_language = detected_language

    # Traduz o texto para espanhol, especificando o idioma de origem se foi detectado ou fornecido
    translation = translate_client.translate(text, source_language=source_language, target_language='es')
    return translation['translatedText']

    
def get_or_create_user_history(user_id):
    if user_id not in messages:
        # Se não existir um histórico para o usuário, inicialize com uma mensagem do sistema.
        messages[user_id] = [{"role": "system", "content": "Your initial system message..."}]
    return messages[user_id]

# def is_goodbye_message(message_text):
#     return re.search(r'\b(chau|tchau|chao)\b', message_text, re.IGNORECASE) is not None

from moviepy.editor import AudioFileClip
from gtts import gTTS
import openai

# Supondo que a função translate_portunhol_to_spanish_with_openai já esteja definida conforme o exemplo anterior

def voice_message(update, context):
    user_id = get_user_identifier(update)
    logger.info(f"Received voice message from {user_id}")
    voice_file = context.bot.getFile(update.message.voice.file_id)
    voice_file.download("voice_message.ogg")
    audio_clip = AudioFileClip("voice_message.ogg")
    audio_clip.write_audiofile("voice_message.mp3")

    # Abre o arquivo de áudio para transcrição e fecha após a operação
    with open("voice_message.mp3", "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file).text
    logger.info(f"Voice message transcript for {user_id}: {transcript}")

    # Utiliza a função de tradução aprimorada para processar o texto transcrito
    transcript_spanish = translate_portunhol_to_spanish_with_openai(transcript)
    logger.info(f"Translated to Spanish for {user_id}: {transcript_spanish}")

    user_messages = get_or_create_user_history(user_id)

#    if is_goodbye_message(transcript_spanish):
#        analyze_and_finalize_conversation(update, context)
#    else:
    update.message.reply_text(text=f"*[You]:* _{transcript_spanish}_", parse_mode=ParseMode.MARKDOWN)
    user_messages.append({"role": "user", "content": transcript_spanish})
        
        # Inclui a descrição da personalidade para interações gerais
    messages_with_personality = [{"role": "system", "content": GENERAL_PERSONALITY_DESCRIPTION}] + user_messages

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo-preview",
        max_tokens = 500,
        messages=messages_with_personality
    )
    response_text = response["choices"][0]["message"]["content"]
    logger.info(f"Preparing voice response for {user_id}")
        
        # Convertendo a resposta em áudio
    tts = gTTS(text=response_text, lang='es')
    tts_file = 'response_gtts.mp3'
    tts.save(tts_file)
        
        # Enviando a resposta em áudio e texto
    context.bot.send_voice(chat_id=update.message.chat.id, voice=open(tts_file, 'rb'))
    update.message.reply_text(text=f"*[Sara]:* _{response_text}_", parse_mode=ParseMode.MARKDOWN)
        
    user_messages.append({"role": "assistant", "content": response_text})

def analyze_and_finalize_conversation(update, context):
    user_id = get_user_identifier(update)  # Função hipotética para obter o ID do usuário do update.

    if user_id in messages and messages[user_id]:  # Verifica se há mensagens para esse usuário e se a lista não está vazia.
        user_messages = messages[user_id]  # Acessa as mensagens do usuário específico.

        # Descrição da personalidade e contexto do usuário
        personality_description = ANALYTICAL_PERSONALITY_DESCRIPTION

        # Adiciona a descrição da personalidade ao início do histórico de mensagens
        messages_for_ai = [{"role": "system", "content": personality_description}] + \
                          [{"role": msg["role"], "content": msg["content"]} for msg in user_messages]

        try:
            # Faz a chamada para a API da OpenAI usando as mensagens do usuário como histórico de conversa, incluindo a descrição da personalidade.
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=messages_for_ai,
                temperature=0.7,
                max_tokens=500
            )
            correction_text = response.choices[0].message["content"]
            
            # Envia a resposta ao usuário
            update.message.reply_text(text=f"Aqui estão as correções e explicações para a nossa conversa:\n\n{correction_text}")
        except Exception as e:
            logger.error(f"Erro ao solicitar correção da OpenAI: {str(e)}")
            update.message.reply_text(text="Desculpe, houve um erro ao processar sua solicitação.")
    else:
        update.message.reply_text(text="Não há mensagens suficientes para análise.")


# Exemplo de função para obter o ID do usuário de um update.
# Isso depende da estrutura do seu update. Adapte conforme necessário.
def get_user_identifier(update):
    return update.effective_user.id

# Exemplo de função para obter o ID do usuário de um update.
# Isso depende da estrutura do seu update. Adapte conforme necessário.
def get_user_identifier(update):
    return update.effective_user.id

# Certifique-se de substituir `openai.ChatCompletion.create` pelos parâmetros corretos e seu próprio token de API.


def text_message(update: Update, context: CallbackContext):
    user_id = get_user_identifier(update)
    logger.info(f"Received text message from {user_id}")
    
    # Aqui, você obtém o texto diretamente da mensagem do usuário
    original_text = update.message.text
    logger.info(f"Original text from {user_id}: {original_text}")
    
    # Utilize a OpenAI para traduzir o texto de "portunhol" para espanhol
    translated_text_to_spanish = translate_portunhol_to_spanish_with_openai(original_text)
    logger.info(f"Translated to Spanish for {user_id}: {translated_text_to_spanish}")
    
    user_messages = get_or_create_user_history(user_id)

#    if is_goodbye_message(translated_text_to_spanish):
#        analyze_and_finalize_conversation(update, context)
#    else:
    update.message.reply_text(text=f"*[You]:* _{translated_text_to_spanish}_", parse_mode=ParseMode.MARKDOWN)
    user_messages.append({"role": "user", "content": translated_text_to_spanish})
        
        # Inclui a descrição da personalidade para interações gerais
    messages_with_personality = [{"role": "system", "content": GENERAL_PERSONALITY_DESCRIPTION}] + user_messages

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo-preview",
        max_tokens = 500,
        messages=messages_with_personality
    )
    response_text = response["choices"][0]["message"]["content"]
    logger.info(f"Preparing voice response for {user_id}")
        
        # Convertendo a resposta em áudio
    tts = gTTS(text=response_text, lang='es')
    tts_file = f'response_gtts_{user_id}.mp3'
    tts.save(tts_file)
        
        # Enviando a resposta em áudio e texto
    context.bot.send_voice(chat_id=update.message.chat.id, voice=open(tts_file, 'rb'))
    update.message.reply_text(text=f"*[Sara]:* _{response_text}_", parse_mode=ParseMode.MARKDOWN)
        
        # Limpeza: remover o arquivo de áudio após o envio
    os.remove(tts_file)
        
    user_messages.append({"role": "assistant", "content": response_text})

def reset_conversation(update, context):
    user_id = str(update.message.from_user.id)
    logger.info(f"Conversation reset by {user_id}")
    # Usa GENERAL_PERSONALITY_DESCRIPTION como conteúdo inicial para o usuário
    messages[user_id] = [{"role": "system", "content": GENERAL_PERSONALITY_DESCRIPTION}]
    # Informa ao usuário que a conversa foi reiniciada
    context.bot.send_message(chat_id=update.message.chat.id, text="A conversa foi reiniciada. Como posso ajudar?")


updater = Updater(TELEGRAM_API_TOKEN, use_context=True)
dispatcher = updater.dispatcher

dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), text_message))
dispatcher.add_handler(MessageHandler(Filters.voice, voice_message))
dispatcher.add_handler(CommandHandler('reset', reset_conversation))

updater.start_polling()
updater.idle()