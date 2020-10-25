import csv
import sys
import tkinter as tk
import mojimoji
from tkinter import *
from tkinter import ttk
import serial
import threading
import time

# arduinoのkeyborad.hの特殊入力用コードの取得
def import_key_dict(dict):
    with open("keyboard.csv") as f:
        for row in csv.reader(f):
            dict[row[1]] = row[0]

# ASCIIコードから文字変換。arduino lenoardの特殊文字処理を含む
def ascii_to_chr(ascii_code):
    if ascii_code < 0x80:
        return chr(ascii_code)
    else:
        return HEX_KEY[hex(ascii_code)]

# 文字列からASCIIコードへの変換。arduino lenoardの特殊文字処理を含む
def chr_to_ascii(char):
    if len(char) == 1:
        return ord(char)
    else:
        for k,v in HEX_KEY.items():
            if char == v:
                return int(k,16)

# メインオブジェクト
class main_window():

    # 初期化
    def __init__(self):
        # ウインドウ作成
        self.window = tk.Tk()
        self.window.title("Key config")
        self.window.geometry("500x500")

        self.key = [0x58,0x5a,0x41,0x53,0xB1,0x51,0x57]   # 各ボタンの初期キー設定(x,z,a,s,Escape,q,w)
        self.button = [] # ボタンの状態用配列

        # ボタンのスタイル設定
        RED_BUTTON_STYLE = ttk.Style()
        RED_BUTTON_STYLE.configure("RB.TButton",background="#801E1E")

        GREEN_BUTTON_STYLE = ttk.Style()
        GREEN_BUTTON_STYLE.configure("GB.TButton",background="#AAB300")

    # フレーム作成用のメソッド
    def make_frame(self):
        self.frame = tk.Frame(self.window, relief="raised",bg='#303030') # Frame作成
        self.frame.grid()

    # ボタン作成用のメソッド
    def make_buttons(self):
        # ABXYボタンの設定
        for i in range(4):
            self.button.append(ttk.Button(
                self.frame,
                style = "RB.TButton",
                text = ascii_to_chr(self.key[i]),
                command = self.change_key(i)
                ))
            self.button[i].grid(column=ABXY_XPOS[i], row=ABXY_YPOS[i])

        # startボタンの設定
        self.button.append(ttk.Button(
            self.frame,
            text = ascii_to_chr(self.key[4]),
            style = "RB.TButton",
            command = self.change_key(4)
            ))
        self.button[4].grid(column=2,row=5)

        # LRボタンの設定
        for i in range(2):
            self.button.append(ttk.Button(
                self.frame,
                text=ascii_to_chr(self.key[i+5]),
                style = "GB.TButton",
                command = self.change_key(i+5)
                ))
            self.button[i+5].grid(column=LR_XPOS[i],row=0)
        
        # dataをarduinoに送るボタン
        self.button.append(ttk.Button(
            self.frame,
            text="Send config",
            command = self.send_data()
        ))
        self.button[7].grid(column=4,row=5)

        # Quiteボタン
        self.button.append(ttk.Button(
            self.frame,
            text="Quit",
            command = self.window.destroy
        ))
        self.button[8].grid(column=2,row=6)
    
    # 各キーの変更用のメソッド
    def change_key(self,num):
        def inner():
            # キー変更用ウインドウの作成
            self.window1 = tk.Tk()
            self.window1.title("Key change of button {}".format(num+1))
            self.window1.geometry("500x500")

            # 手動入力用のフレーム作成
            self.frame1 = ttk.Frame(self.window1)
            self.frame1.grid()

            # 手動入力用のラベル作成
            self.label1 = ttk.Label(self.frame1,text="please enter keyborad for button {}".format(num+1))
            self.label1.grid(row=0)

            # 手動入力用のテキストボックス
            self.entry1 = ttk.Entry(self.frame1,width=10)
            self.entry1.grid(row=1)

            # 手動入力完了ボタン
            self.button1 = ttk.Button(self.frame1,text='Apply',command=self.update_key("",num,0))
            self.button1.grid(row=2)

            # orラベル
            self.label2 = ttk.Label(self.frame1,text="or")
            self.label2.grid(row=3)

            # 手動入力用のフレーム作成
            self.frame2 = ttk.Frame(self.window1)
            self.frame2.grid()

            # 特殊キー用ボタン
            self.Skey = [ttk.Button(self.frame2,text="") for i in range(35)]
            i = 0
            for k,v in HEX_KEY.items():
                self.Skey[i]["text"]= v
                self.Skey[i]["command"]= self.update_key(v,num,1)
                self.Skey[i].grid(row=int(i/3),column=int(i%3))
                i = i + 1

            # Quitボタン
            self.button_q = ttk.Button(self.frame2,text='Quit',command=self.window1.destroy)
            self.button_q.grid(row=12,column=1)

            self.window1.mainloop()
        return inner

    # Arduinoにデータを送るメソッド
    def send_data(self):
        def inner():

            # ポートの確認。接続がなければエラーウインドウ
            try:
                self.serial = serial.Serial('/dev/ttyACM0',9600,timeout=5)

            except:
                self.msg("Gamepad is not connected")()
                return

            # 待ちウインドを別スレッド化で立てる
            thread1 = threading.Thread(target=self.msg("Please wait for data send"))
            thread1.setDaemon(True)
            thread1.start()

            # データ送信
            self.send_serial()

        return inner

    # データ送信用メソッド
    def send_serial(self):
        start_time = time.time()
        take_time = 0

        # OKが出るかタイムアウトまで無限ループ
        while(take_time < 30):

            # Gamepadからトグルの「Off」が来ていることを確認。
            self.serial.flushInput()
            line1 = self.serial.readline().decode("utf-8")
            
            # Offが来ていたらデータ送信開始
            if("Off" in line1):

                # 「OK」の受領が確認されるまで送信し続ける
                while("OK" not in line1):

                    # ヘッダ「255 = 0xff」を送信してブッファを削除
                    self.serial.write(b"\xff")
                    self.serial.flushInput()

                    # 受領確認用（255）
                    line1 = self.serial.readline().decode("utf-8")
                    print(line1)

                    # 各割当キーを送信
                    for i in range(7):
                        self.serial.write(self.key[i].to_bytes(1,"big"))

                    # 各割当キーの返信を確認
                    for i in range(7):
                        line1 = self.serial.readline().decode("utf-8")
                        print(line1)

                    # 上手く行っていればここで「OK」が帰ってくる
                    line1 = self.serial.readline().decode("utf-8")
                    print(line1)
                
                # 「OK」でループを抜けたら「Succeeded」を表示してBreak
                msg = "Succeeded"  
                print(msg)
                break
            take_time = time.time()-start_time
        else:
            msg = "Timeout"
            print(msg)

        self.msg(msg)()

    # 各ボタンのkeyを、ラベルからASCII_codeの数値に変換するメソッド
    def update_key(self,text,num,mode):
        def inner():
            key_text = text

            # 自由入力の場合の処理　→　半角大文字化、二文字以上だとエラー
            if mode == 0:
                key_text = self.entry1.get()
                key_text = mojimoji.zen_to_han(key_text.upper())
                if len(key_text) != 1:
                    error_letter = "Please input only one charactor"
                    self.msg(error_letter)()
                    return

            # 文字列からasciiに変換して、self.keyを更新する
            self.key[num] = chr_to_ascii(key_text)
            letter = "Change key config: button {} is {}.".format(num+1,key_text)
            self.button[num]["text"] = ascii_to_chr(self.key[num])

            self.msg(letter)()
        return inner

    # 汎用のメッセージ表示用ウインドウ作成用のメソッド
    def msg(self,letter):
        def inner():
            msg_win = tk.Tk()
            msg_win.title("Message")
            msg_win.geometry("400x100")

            frame_msg = ttk.Frame(msg_win)
            frame_msg.pack()
            
            label_msg = ttk.Label(frame_msg,text=letter)
            label_msg.pack()

            button_msg = ttk.Button(frame_msg,text='OK',command=msg_win.destroy)
            button_msg.pack()

            msg_win.mainloop()
        return inner

# arduino keybord.h用のASCII codeの宣言と取り込み
HEX_KEY = {}
import_key_dict(HEX_KEY)

# 各ボタンの配置用定数定義
ABXY_XPOS = [1,2,3,2]
ABXY_YPOS = [2,3,2,1]
LR_XPOS = [0,4]


main = main_window()
main.make_frame()
main.make_buttons()

main.window.mainloop()

