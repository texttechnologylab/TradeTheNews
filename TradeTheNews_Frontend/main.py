from flask import Flask, request, abort
from markupsafe import Markup

from website_part_yahoo import seach_in_yahoo, scrape_yahoo_data, create_top_website_part

from variable import return_template, QUERY_INFRONT_OF_NEWS, QUERY_AFTER_NEWS, DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT, DB_DATABASE
from website_part_news import create_news_website
from database import Database
from website_part_database import create_stock_view


database = Database(DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT, DB_DATABASE)

app = Flask(__name__)

# ------------------------------------
# HAUPTWEBSEITE - ÜBERSICHTSWEBSIETE
# ------------------------------------
@app.route('/', methods=['GET', 'POST'])
def overview_website():
    '''
    On this Website you can search for a Stock in the Database
    '''
    return return_template(template_name_or_list='index.html')


# ------------------------------------
# SUCH WEBSEITE - YAHOO ...
# ------------------------------------
@app.route('/yahoo', methods=['GET', 'POST'])
def search_website_yahoo():
    '''
    On this Website you can search for a Stock on the Yahoo-Website
    '''
    if request.method == 'POST':
        # Hier wird der Userinput auf der Webseite eingelesen und verarbeitet
        input_name = request.form.get("namen_suche").strip()

        if not input_name:
            result = "Nichts in das Textfeld eingegeben ... </br> \nSomit konnte nicht nach irgendwas gesucht werden"
            return return_template(template_name_or_list='ticker_yahoo.html', search_result=Markup(result))

        input_num_results = request.form.get("anzahl_suchergebnisse")
        input_num_results = int(input_num_results) if input_num_results else 5

        # Dieser Code ließt die Radiobuttons [aktien, etf, krypto] aus
        value_aktien = request.form["suchtyp_auswahl"] == "aktien"
        value_etf = request.form["suchtyp_auswahl"] == "etf"
        value_crypto = request.form["suchtyp_auswahl"] == "krypto"

        # Dieser Teil code generiert eine Übersciht über die Suchparameter die durch den Benutzer eingegeben wurden
        result = f"""<h4>Es wird mit den folgenden Werten gesucht:</h4> 
                        <ul style="margin: 25px"> <li> Name: {input_name} </li>
                             <li> Anzahl der Suchergebnisse: {input_num_results} </li>
                             <li> Suche nach ... [Aktien = {value_aktien}] , [ETF = {value_etf}] , [Cryptp = {value_crypto}] </li> </ul>\n<hr>"""


        # Suche auf der Yahoo Webseite
        result += "<h5> Yahoo-Suche ... </h5>"
        yahoo_answer = seach_in_yahoo(input_name, input_num_results, value_aktien, value_etf, value_crypto)
        if not yahoo_answer:
            result += "Es ist ein Fehler beim Scraping de Yahoo Webseite aufgetreten :("
        else:
            result += "<ul>\n"
            for ticker, name in yahoo_answer:
                result += f"<li><a href='/yahoo/stock/{ticker}'>{ticker} - {name}</a></li>\n"
            result += "</ul>\n"

        return return_template(template_name_or_list='ticker_yahoo.html', search_result=Markup(result))
    elif request.method == 'GET':
        print("GET")
        return return_template(template_name_or_list='ticker_yahoo.html', search_result="Noch nichts gesucht ....")
    else:
        abort(401)

# ------------------------------------
# SUCH WEBSEITE - DATENABANK ...
# ------------------------------------
@app.route('/database', methods=['GET', 'POST'])
def search_website_db():
    '''
    On this Website you can search for a Stock in the Database
    '''
    if request.method == 'POST':
        if 'suche_db' in request.form:
            # Hier wird der Userinput auf der Webseite eingelesen und verarbeitet
            input_name = request.form.get("ticker_suche").strip()

            if not input_name:
                result = "Nichts in das Textfeld eingegeben ... </br> \nSomit konnte nicht nach irgendwas gesucht werden"
                return return_template(template_name_or_list='ticker_db.html', search_result=Markup(result))

            # Dieser Teil code generiert eine Übersciht über die Suchparameter die durch den Benutzer eingegeben wurden
            result = f"<h4>Es wird nach folgendem Ticker gesucht: {input_name} </h4>"
            # Es wird in der Datenbank gesucht
            result += "<h5> Datenbanksuche ... </h5>"
            found_stock = database.search_for_item('stocks', {'ticker': input_name})
        elif 'zufallssuche' in request.form:
            # Es wird in der Datenbank gesucht
            result = "<h5> zufällige Datenbanksuche ... </h5>"
            found_stock = database.read_something('stocks')
        else:
            abort(123)

        if found_stock:
            result += f"""
                <a href='/database/stock/{found_stock.get("ticker", "NoTicker")}'>{found_stock.get("ticker", "NoTicker")} - {found_stock.get("name", "NoName")}</a> </br>
                {found_stock.get("description", "NoDescription")}
                """
        else:
            result += f"Es konnte kein Ticker gefunden werden :("
        
        return return_template(template_name_or_list='ticker_db.html', search_result=Markup(result))
    elif request.method == 'GET':
        return return_template(template_name_or_list='ticker_db.html', search_result="Noch nichts gesucht ....")
    else:
        abort(401)


# ------------------------------------
# WERTPAPIER WEBSEITE - YAHOO ...
# ------------------------------------
@app.route('/yahoo/stock/<ticker>', methods=['GET', 'POST'])
def stock_view_yahoo(ticker):
    '''
        This website scrapes information from yahoo website and displays these
        Furthermore it searches for Newarticles and gives the order to analyse them
    '''
    if request.method == 'POST':
        input_seach_query_infront = request.form.get("seach_query1") if request.form.get("seach_query1") else QUERY_INFRONT_OF_NEWS
        input_seach_query_after = request.form.get("seach_query2") if request.form.get("seach_query2") else QUERY_AFTER_NEWS
        input_news_results = request.form.get("anzahl_news")
        input_news_results = int(input_news_results) if input_news_results else 3
        num_history_weeks = request.form.get("anzahl_history_weeks")
        num_history_weeks = int(num_history_weeks) if num_history_weeks else 1
        website_content = scrape_yahoo_data(ticker=ticker, num_news=input_news_results, database=database, database_save=request.form.getlist("options"), number_of_history_weeks=num_history_weeks, seach_query=(input_seach_query_infront, input_seach_query_after))
        return return_template(template_name_or_list='blank_website.html', content=Markup(website_content), title='GetRichFast - WertpapierYahoo')
    elif request.method == 'GET':
        return return_template(template_name_or_list='blank_website.html', content=Markup(create_top_website_part(ticker, "stockName") + "Es wurde noch nichts gescraped ..."), title='GetRichFast - WertpapierYahoo')
    else:
        abort(401)


# ------------------------------------
# WERTPAPIER WEBSEITE - DATENBANK ...
# ------------------------------------
@app.route('/database/stock/<ticker>', methods=['GET', 'POST'])
def stock_view_db(ticker):
    '''
        This website gets information from database and displays these
    '''
    return return_template(template_name_or_list='blank_website.html', content=Markup(create_stock_view(database, ticker)), title='GetRichFast - WertpapierDB')


# ------------------------------------
# NEWS WEBSEITE 
# ------------------------------------
@app.route('/news/<path:url>', methods=['GET', 'POST'])
def online_news_Web(url):
    '''
    This website gets Article from database and displays it
    '''
    if ("."  not in url) or ("/" not in url):
        return not_found("NEWS-URL NOT CORRECT =(")
    possible_ticker = request.args.get("ticker", "notSpecified")

    return return_template(template_name_or_list='blank_website.html', title="GetRichFast - News", content=Markup(create_news_website(url, database, possible_ticker)))


# ------------------------------------
# FEHLER WEBSEITE ...
# ------------------------------------
@app.errorhandler(Exception)
def not_found(error):
    '''
    Website for debugging - displays an error
    '''
    return return_template(template_name_or_list='error.html', fehler=error)


if __name__ == '__main__':
    app.run()
