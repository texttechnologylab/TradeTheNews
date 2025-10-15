import requests
from bs4 import BeautifulSoup
import yfinance as yf
from website_part_news import search_for_news, scrape_newspaper_with_url
from datetime import datetime, timedelta
from variable import create_collabsable_box


def seach_in_yahoo(name, num_of_tickers=1, aktie=True, etfs=False, crypto=False):
    """
    This function accesses a Yahoo search page and searches for tickers by name.
    These are found through structured searching in the HTML web page.
    """
    HEADER =  {
        "User-Agent": "Mozilla/5.0"
    }

    # !!! !!! If more than one variable is True or all variables are False, a general URL is taken
    if aktie and (not etfs) and (not crypto):
        # Stock URL
        URL = f"https://de.finance.yahoo.com/lookup/equity/?s={name}"
    elif (not aktie) and etfs and (not crypto):
        # ETF URL
        URL = f"https://de.finance.yahoo.com/lookup/etf/?s={name}"
    elif (not aktie) and (not etfs) and crypto:
        # Crypto URL
        URL = f"https://de.finance.yahoo.com/lookup/cryptocurrency/?s={name}"
    else:
        # General URL
        URL = f"https://de.finance.yahoo.com/lookup/?s={name}"

    response = requests.get(URL, headers=HEADER)

    if response.status_code != 200:
        print("WEBSEITEN ZUFRIFF VON YAHOO BLOCKIERT")
        return False
    
    # read HTML with BeautifulSoup 
    scraping_count = 0
    data = []

    website = BeautifulSoup(response.text, "html.parser")
    table = website.find("table")
    if table:
        for row in table.find_all("tr"):
            if scraping_count >= num_of_tickers:
                break
            col = row.find_all("td")
            if len(col) >= 5:
                data.append([col[0].get_text(strip=True), col[1].get_text(strip=True)])
                scraping_count += 1
    return data


def scrape_yahoo_data(ticker, num_news, database, database_save, number_of_history_weeks, seach_query):
    '''
    This function scrapes all important stock data from the yahoo website and scraped newsarticles from DuckDuckGo
    and also creates the content of the HTML website where the information is displayed
    furthermore this function loads history data, stock data and news articles into the database, if the user wants to
    '''
    stock = yf.Ticker(ticker)

    # NEWS FOUND
    list_article_url = []
    query_for_news = seach_query[0] + " " + stock.info.get('displayName') + " " + seach_query[-1]
    results = search_for_news(query_for_news, num_news)
    website_content_news = "<ul>\n"
    for news_dict in results:
        news_url = news_dict.get('url', '/noURL')
        website_content_news += f"<li><a href='/news/{news_url}'>{news_dict.get('title', 'noTitle')} - {news_dict.get('source', 'noSource')} </a> </br> {news_dict.get('summary', 'noSummary')}</li> </br>\n"
        if news_url != '/noURL':
            list_article_url.append(news_dict)
        else:
            website_content_news += "Artikel oben drüber konnte nicht verabeitet werden"
    website_content_news += "</ul>\n"
    

    # Important Dates
    website_content_important_dates = ''
    for display_name in ["Dividends", "Stock Splits"]:
        website_content_important_dates += f"<h4>{display_name}</h4>\n<ul>"
        # Nur Zeilen, bei denen display_name != 0
        df_nonzero = stock.actions[stock.actions[display_name] != 0]
        for index, value in zip(df_nonzero.index, df_nonzero[display_name]):
            website_content_important_dates += f"<li><strong>{str(index)}:</strong> {str(value)} </li>"
        website_content_important_dates += "</ul>"
    
    # TODO: DISPLAY BETTER
    for item1, item2 in stock.calendar.items():
        website_content_important_dates += str(item1) + str(item2) +"</br>"

    # INFO stuff
    def unpack(object):
        r = ""
        if isinstance(object, dict):
            if "name" in object.keys():
                r += "<h4>" + object["name"] + "</h4>\n"
            r += "<ul>\n"
            for name, value in object.items():
                r += "<li><b style='margin-right: 20px'>" + str(name) + ":</b>" + unpack(value) + "</li>\n"
            r += "</ul>"
        elif isinstance(object, list):
            r += "<ol>\n"
            for item in object:
                r += unpack(item)
            r += "</ol>\n"
        else:
            r += str(object)
        return r
    
    website_content_info = unpack(stock.info)

    # DATABASE
    database_scraping_results_website_content = load_elements_to_database(database_save, database, stock, list_article_url, ticker, number_of_history_weeks, query_for_news)

    website_content = f"""
    {create_top_website_part(ticker, stock.info.get('displayName', ticker))}
    {create_collabsable_box('News', website_content_news)}
    {create_collabsable_box('Wichtige Termine', website_content_important_dates)}
    {create_collabsable_box('Info', website_content_info)}
    {create_collabsable_box('Scraping Results', database_scraping_results_website_content )}
    """
    return website_content


def create_top_website_part(ticker, stock_name):
    '''
    This creates the top website part for the yahoo website
    '''
    website_top = f"""
    <h1 style="text-align: center;">{ticker}</h1>
    <hr><hr>
    <form action="/yahoo/stock/{ticker}" method="post">
        <h3>Search-Query der zu scrapenden Zeitungsartikel:</h3>
        <span style='padding: 10px'></span> <input type="text" id="seach_query1" name="seach_query1" minlength="0" maxlength="50" placeholder="best ">
        <span style='padding: 5px'>{stock_name}</span>
        <input type="text" id="seach_query2" name="seach_query2" minlength="0" maxlength="50" placeholder=" News">
        </br>
        <h3>Welche daten sollen in der Datenbank gespeichert werden?</h3>
        <ul>
            <li>
                <input type="checkbox" name="options" value="stock">
                Aktieinformationen
            </li>
            <li>
                <input type="checkbox" name="options" value="article">
                <input style="width: 30px;" type="number" id="anzahl_news" name="anzahl_news" min="0" max="100" placeholder="3">
                Zeitungsartikel zu der Aktie
            </li>
            <li>
                <input type="checkbox" name="options" value="week_history">
                Historischer Aktienverlauf der letzten <input style="width:30px;" type="number" id="anzahl_history_weeks" name="anzahl_history_weeks" min="0" max="4" placeholder="1"> Wochen (maximal 3-4 Tage)
            </li>
        </ul>
        <input style="margin: 10px;" type="submit" value="Wertpapierdaten scrapen" name="daten_von_yahoo">
        </br>
        * die Kursdaten und Atieninformationen werden von Yahoo gescraped
        * Zeitungsartikel werden aus dem internet gescraped
    </form>
    <hr>
    """
    return website_top


def scrape_history_weeks(num_of_weeks, ticker_name):
    '''
    This function scrapes Yahoo History data in Weeks
    '''
    json_results = []

    end_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

    start_date = end_date - timedelta(days=30)

    chunks = []
    found_a_start = None
    # get week in chunks
    while start_date < end_date:
        if start_date.weekday() == 0 and not found_a_start:
            found_a_start = start_date
        elif start_date.weekday() == 6 and found_a_start:
            chunks.append((found_a_start, start_date))
            found_a_start = None
        start_date += timedelta(days=1)
    
    num_of_weeks = min(num_of_weeks, len(chunks))
    chunks_to_process = chunks[len(chunks) - num_of_weeks:]

    for processing_chunk in chunks_to_process:
        df = yf.download(
            tickers=ticker_name,
            start=processing_chunk[0].strftime("%Y-%m-%d"),
            end=processing_chunk[1].strftime("%Y-%m-%d"),
            interval="1m"
        )

        compressed_dict_1_min_data = []
        # convert df object to list of dicts
        compressed_dict_1_min_data = []
        for date, row in df.iterrows():
            date_naive = date.tz_localize(None)
            minute_offset = int((date_naive - processing_chunk[0]).total_seconds() // 60)
            compressed_dict_1_min_data.append({
                "min_offset_time": minute_offset,
                # "open": float(row["Open"]),
                # "high": float(row["High"]),
                # "low": float(row["Low"]),
                "close": float(row["Close"].iloc[0]),
                "volume": int(row["Volume"].iloc[0])
            })
        
        json_object = {
            'ticker': ticker_name,
            'date_week_monday': processing_chunk[0],
            'data': compressed_dict_1_min_data,
            'last_updated': datetime.now()
        }
        json_results.append(json_object)

    return json_results



def load_elements_to_database(database_save, database, stock, list_article_url, ticker_name, num_history_weeks, query_for_news):
    '''
    This function loads all important scraped into the Database:
    Newsarticles, HistoryData, Stockdata
    '''
    errorcounter_articls = 0
    succsesfull_articles = 0
    if 'stock' in database_save:
        json_object = {
            'ticker': ticker_name,
            'name': stock.info.get('longName', 'noName'), 
            'website': stock.info.get('website', 'noWebsite'),
            'ir_website': stock.info.get('irWebsite', 'noIr_website'),
            'description': stock.info.get('longBusinessSummary', 'noDefault'),
            'market': stock.info.get('market', 'noMarket'),
            'sector': stock.info.get('sector', 'noSector'),
            'industry': stock.info.get('industry', 'noIndustry'),
            'last_updated': datetime.now()
        }
        database.insert_to_collection('stocks', json_object)

    if 'article'in database_save:
        for dict_article in list_article_url:
            try:
                print("TRY SCRAPE NEWS")
                json_object = scrape_newspaper_with_url(dict_article.get('url'), dict_article, ticker_name)
                database.insert_to_collection('articles', json_object)
                succsesfull_articles += 1
            except Exception as e:
                print(f'{dict_article} cannot be read ... ERROR: {e}')
                errorcounter_articls += 1

    if 'week_history' in database_save:
        for object in scrape_history_weeks(num_history_weeks, ticker_name):
            print("WEEK HISTORY DATA")
            database.insert_to_collection('week_history', object)

    return f'''
    <ul>
        <li> {ticker_name + "-Informationen <b> wurde </b>  zur Datenbak hinzugefügt" if 'stock' in database_save else "Aktieninformationen <b> wurden nicht </b> zur Datenbank hinzugefügt"} </li>
        <li> Es wurden <b> {succsesfull_articles} Zeitungsarikel erfolgreich </b> in die Datenbank geladen. </li>
        <li> Bei <b> {errorcounter_articls} Zeitungsartikel ist ein Fehler aufgetreten </b> somit konnten diese nicht in die Datenbank geladen werden </li>
        {"<li> Es wurden die letzten " + str(num_history_weeks) + " Kursdaten-Wochen in die Datenbank geladen" if "week_history" in database_save else ""}
        <li> Es wurde mit der <b> Seachquery '{query_for_news}' </b>  gesucht
    </ul>
    '''
