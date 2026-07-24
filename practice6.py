# 匯入 gradio 套件，用於建立互動式網頁介面
import gradio as gr

# 定義問候函式，接收名字和強度參數
def greet(name, intensity):
    return "Hello," + name + "!" * int(intensity)

# 建立 Interface 實體
demo = gr.Interface(
    fn=greet,                     # 指定要包裝的函式
    inputs=["text","slider"],     # 輸入元件：文字框 + 滑桿
    outputs = ["text"],           # 輸出元件：文字框
    examples=[["徐國堂",2], ["徐xx",1]]  # 提供範例輸入
)

# 啟動網頁應用程式
demo.launch()