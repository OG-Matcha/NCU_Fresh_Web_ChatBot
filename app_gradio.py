import gradio as gr
from llm import ConversationBot


def predict(message, history):
    bot = ConversationBot()
    response = bot.start_process(message)

    return response

gr.ChatInterface(predict, chatbot=gr.Chatbot(value=[["🧡 哈囉哈囉~ 我是中央大學的吉祥物 - 松鼠🐿️！有什麼問題需要我的幫助嗎？啾啾~ 😊", None]], show_label=False),  textbox=gr.Textbox(placeholder="可以問我有關中央大學的問題喔~ 😊", container=False, scale=7), examples=["我想知道大一週會有哪些主題", "甚麼時候可以開始選課", "我要怎麼申請宿舍網路"], css="#component-0 { height:calc(120vh - 380px)!important; }", undo_btn=None, description="歡迎使用新知網 Fresh Bot，以下為 DEMO 版本，對話無延續功能，歡迎提出意見想法喔~").launch(server_name="0.0.0.0", server_port=443)