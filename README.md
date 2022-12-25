# SakuraBot
discordBotプロジェクトです。  


# Developer向け

## 最低要件
* python3.10以上

## このBotを個人でホストする場合

1.pipenv, pyenvのインストールを行う。

2.Pipfileがあるディレクトリで`pipenv install` を実行する。

3.`.env-template`を`.env`に変更し、TOKENを設定する。

4.`sakura_private`リポジトリを見る権限がある人はそれを`git clone`しておく

5.`pipenv run python3 main.py`または`python shell`を実行してから`python3 main.py`を実行すると起動できる
