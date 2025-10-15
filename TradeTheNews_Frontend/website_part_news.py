from datetime import datetime
from ddgs import DDGS
from newspaper import Article

def create_news_website(url, database, ticker):
    '''
    This function retruns the HTML code with is nessercary to display a news article on a website. 
    Therefore it accesses the Database.
    '''
    database_object = database.search_for_item('articles', {'url': url})
    if database_object:
        website_part = f"""
            <h1 style="text-align: center;">News zum Ticker - {database_object['ticker']}</h1>
            * Artikel wurde zur folgenden Zeit gescraped: {database_object["accessed_date"]}
            <hr><hr>
            <ul>
                <li><strong>ID: </strong></li> {database_object['_id']}
                <li><strong>URL: </strong></li> <a href='{url}'>{url}</a>
                <li><strong>Publikationsdatum: </strong></li> {database_object["publish_date"]}
                <li><strong>Author: </strong></li> {database_object["author"]}
            </ul>
            <h4>Titel</h4>
            {database_object['title']} 
            <h5>Zusammenfassung:</h5>
            {database_object["summary"]}
            <h3>Zeitungsartikelinhalt:</h3>
            {database_object["content"]}
            <hr>
        """

        if "llm_score" in database_object:
            website_part += f"""
            <ul>    
                <li><strong>ANALYSE DATUM: </strong></li> {database_object['analysedAt']}
                <li><strong>BEWERTUNG: </strong></li> {database_object['llm_score']}
                <li><strong>BERÜNGUNG: </strong></li> {database_object['llm_reason']}
            </ul>
            <strong>LLM -Promt: </strong> </br> 
            {database_object['llm_prompt']}
            """
        else:
            website_part += """
                ... Artikel wurde noch nicht analysiert
            """
        return website_part
    else:
        website_part = f"""
            Artikel wurde noch nicht analysiert ... </br>
            ... Artikel wurde zum Analysieren in die Datenbank geladen
            zum Anzeigen Webseite <a href='/news/{url}'> neu laden </a>
            <hr>
        """
        try:
            result_dict = scrape_newspaper_with_url(url, ticker)
            website_part += f"""
                <h3 style="text-align: center;">gescrapter Artikel - {result_dict['ticker']}</h3>
                * Artikel wurde zur folgenden Zeit gescraped: {result_dict["accessed_date"]}
                <hr><hr>
                <ul>
                    <li><strong>URL: </strong></li> <a href='{url}'>{url}</a>
                    <li><strong>Titel: </strong></li> {result_dict["title"]}
                    <li><strong>Author: </strong></li> {result_dict["author"]}
                </ul>
            """
            database.insert_to_collection('articles', result_dict)
        except Exception:
            website_part += f"""
                Artikel konnte leider nicht gescraped werden :( </br> 
                <strong>URL:</strong> {url}
            """
        

    return website_part


def search_for_news(query, num=1):
    '''
    This searches with DuckDuckGo for a certain amout of news Articles
    '''
    results_news = DDGS().news(query, max_results=num)
    return results_news


def scrape_newspaper_with_url(url, dict_article, ticker):
    '''
    this function scrapes with a moodlue named Newspaper the articles found with the Function "search_for_news".
    Then it returns a dict to save the news article in the database
    '''
    article = Article(url)
    article.download()
    article.parse()

    if not article.text:
        raise ValueError
    article_newspaper_date = article.publish_date
    summary = article.summary if article.summary else dict_article.get('body', "NoSummary")

    if article_newspaper_date and (article_newspaper_date.minute != 0 and article_newspaper_date.hour != 0):
        publish_date = article_newspaper_date
    else:
        publish_date = "noDate" if dict_article.get('date', "noDate") == "noDate" else datetime.fromisoformat(dict_article.get('date'))

    result_dict = {
        'ticker': ticker,
        'url': url,
        'title': article.title,
        'summary': summary,
        'content': article.text,
        'publish_date': publish_date,
        'accessed_date': datetime.now(),
        'author': " & ".join(article.authors),
        'source': dict_article.get('source', "NoSource")
    }
    return result_dict
