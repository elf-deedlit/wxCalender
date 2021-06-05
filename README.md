# wxCalender
wxPythonを使ったカレンダー  
["内閣府のウェブサイト"](https://www8.cao.go.jp/chosei/shukujitsu/gaiyou.html)から祭日情報を持ってくるので祭日は正しいです。

## Windows10での実行方法
* Python3をインストール
* 仮想環境を作る  
python -m venv venv

* 仮想環境を有効化  
venv\Scripts\activate

* pipを最新にする  
py -m pip install --upgrade pip  
※ Windowsはpip.exeがpip.exeを更新出来ないため、上記のように実行する。

* 他のモジュールを最新にする  
pip install --upgrade setuptools

* 必要なモジュールをインストール  
pip install wxWidgets requests python-dateutil

## 実行方法
python3 main.py

## Windows10用EXE作成
1. pyinstallerをインストール  
pip install pyinstaller

1. mk.batを実行  
distパスの下に実行ファイルが作られる。