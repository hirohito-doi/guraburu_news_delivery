from bs4 import BeautifulSoup as soup
from argparse import ArgumentParser
import requests, json, pickle, os, configparser

NEWS_URL = "http://granbluefantasy.jp/news/"
PICKLED_FILE = "data_guraburu_news"
ABS_DIR = os.path.dirname(os.path.abspath(__file__))

ini = configparser.ConfigParser()
ini.read(os.path.join(ABS_DIR, './config.ini'), 'UTF-8')
WEBHOOK_URL = ini['DEFAULT']['webhook_url']

def post_on_discord(message):
    """Discordへメッセージを投稿する。"""
    # ヘッダー情報 とりあえずコピペ
    headers = {
        'User-Agent': 'discord-simple-webhook (0.0.1)',
        'Content-Type': 'application/json'
    }

    data = json.dumps({'content': message})
    response = requests.post(WEBHOOK_URL, headers = headers, data = data)

    if response.status_code == 204:
        return True
    else:
        # 投稿に失敗した場合は例外を投げる
        raise Exception("Error on post : " + str(response.status_code))


def get_articles():
    """グラブル公式のNEWSページから記事を取得する。"""
    # ニュース記事のデータを集める
    response = requests.get(NEWS_URL)
    response.raise_for_status() # 取得に失敗した場合は例外を上げる
    page = response.text
    doc = soup(page, "html.parser")

    aritcles = articles = doc.select('article h1 .change_news_trigger')

    return articles


def get_saved_articles():
    """過去に取得して保存したニュース記事のデータを取得する。保存したファイルがなければ空のリストを返す。"""
    try:
        with open(os.path.join(ABS_DIR, PICKLED_FILE), 'rb') as f:
            saved_articles = pickle.load(f)
    except Exception: # 割と雑だけど…
        saved_articles = []

    return saved_articles

def get_new_articles(articles, saved_articles):
    """取得したニュースと過去のニュースを比較して新しい記事を返す"""
    new_articles = []

    for article in articles:
        new_article_flg = True
        href = str(article['href']) # データ保存の際にうまくいかないので型を文字列に変換する
        title = str(article.string)

        for saved_article in saved_articles:
            if href == saved_article['href'] and title == saved_article['title']:
                new_article_flg = False;
                break

        if new_article_flg:
            new_article = {
                'title': title,
                'href': href,
            }
            new_articles.insert(0, new_article)

    return new_articles


def run_delivery_service(args):
    """メイン処理。最新ニュースがあれば,、それをDiscordに投稿する"""
    # サイトから現在のニュース記事を取得する
    articles = get_articles()

    # 過去に取得して保存したニュース記事のデータを取得する
    saved_articles = get_saved_articles()

    # 新しいニュースを取得する
    new_articles = get_new_articles(articles, saved_articles)

    if args.readonly:
        # オプション引数が指定されていれば記事をマージするだけ
        saved_articles = new_articles + saved_articles
    else:
        # Discordに投稿する
        for article in new_articles:
            try:
                # まずDiscordに投稿
                message = article['title'] + "\n\n" + article['href']
                post_on_discord(message)
            except Exception:
                pass
            else:
                # 投稿完了したら記事データを保存する
                saved_articles.insert(0, article)


    # 最新20件のデータだけ残して保存する
    saved_articles = saved_articles[0: 20];
    with open(os.path.join(ABS_DIR, PICKLED_FILE), 'wb') as f:
        pickle.dump(saved_articles, f)

    return True

def get_option():
    "オプション引数の取得"
    argparser = ArgumentParser()
    argparser.add_argument('-r', '--readonly', action='store_true',
                           help='Readonly flag')

    return argparser.parse_args();

if __name__ == '__main__':
    args = get_option()
    run_delivery_service(args)
