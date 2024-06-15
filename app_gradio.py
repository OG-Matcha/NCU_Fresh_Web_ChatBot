import gradio as gr
from llm import ConversationBot


def predict(message, history):
    bot = ConversationBot()
    response = bot.start_process(message)

    return response

gr.ChatInterface(predict).launch()