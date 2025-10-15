from variable import create_collabsable_box
from datetime import timedelta, time
import pandas as pd
import plotly
import plotly.graph_objs as go
import json
import numpy as np
from trading_strategies import STARTING_DEPOT_VOLUME, TRAINDING_STRATEGIES, COLORS, trading_strategies


def create_stock_view(database, ticker):
    '''
    This fuction craetes the Website part for displaying a stock in the Database.
    Therefore it also Trades with the Stock and its history data and uses the articles
    '''
    website_performance = ""
    # Display Ticker Information
    stock_object = database.search_for_item('stocks', {'ticker': ticker})
    if not stock_object:
        website_content = f"""
            Es existiert kein Ticker '{ticker}' in der Datenbank :( </br>
            Suche einen Ticker auf der <a href='/yahoo'>Yahoo-Suchseite</a> </br>
            oder lade den Ticker <a href='/yahoo/stock/{ticker}'>{ticker}</a> in die Datenbank
        """
    else:
        ticker_information = f"""
            <ul>
                <li><strong>ID:</strong> {stock_object['_id']}</li>
                <li><strong>Webseite:</strong> <a href="{stock_object['website']}">{stock_object['website']}</a></li>
                <li><strong>Investor Relationships Webseite:</strong> <a href="{stock_object['ir_website']}">{stock_object['ir_website']}</a></li>
                <li><strong>Beschreibung:</strong> </br> {stock_object['description']}</li>
                <li><strong>Markt:</strong> {stock_object['market']}</li>
                <li><strong>Sektor:</strong> {stock_object['sector']}</li>
                <li><strong>Industrie:</strong> {stock_object['industry']}</li>
                <li><strong>Letzte Änderung:</strong> {stock_object['last_updated']}</li>
            </ul>
        """

    # Display relevant Newspaper
    list_news = database.search_for_items('articles', {'ticker': ticker})
    if not list_news:
        ticker_news = f"""
            Es existiert keine Zeitungsartikel für den Ticker '{ticker}' in der Datenbank :( </br>
            ... lade Zeitungsartikel von der Yahoo Seite <a href='/yahoo/stock/{ticker}'>{ticker}</a> runter
        """
    else:
        ticker_news = "<ul>\n"
        for news_object in list_news:
            ticker_news += f"<li>{ticker} - <a href='/news/{news_object['url']}'>{news_object['title']}</a> - {news_object['author']}  </br> {news_object['summary']}</li> </br>\n"
        ticker_news += "</ul>"

    # Displays the Trades in Plotly
    list_stock_history = database.search_for_items('week_history', {'ticker': ticker})
    if not list_stock_history:
        ticker_history = f"""
            Es existiert keine historischen Daten zum Ticker '{ticker}' in der Datenbank :( </br>
            ... lade die historischen Daten von der Yahoo Seite <a href='/yahoo/stock/{ticker}'>{ticker}</a> runter
        """
    else:
        # dict_traiding_strategies contains (value overall, owned_stocks)
        dict_traiding_strategies = {}
        for _, trading_strategie in TRAINDING_STRATEGIES:
            dict_traiding_strategies[trading_strategie] = (STARTING_DEPOT_VOLUME, 0)
        
        # reads articles and displays them grouped together. furthermore this loop creates Trades with will be later used to backgroudtest the trading strategies
        useable_news = [article for article in list_news if (article.get("publish_date") is not None) and (article["publish_date"].time() != time(0, 0, 0)) and ("llm_score" in article)]
        grouped_articles = group_article(useable_news)
        grouped_articles = sorted(grouped_articles, key= lambda x: x[0]['publish_date'])
        
        trades_to_perform = []
        if bool(useable_news):
            html_list_articles = "<ul>"
            for useable_articles_group in grouped_articles:
                average_score = useable_articles_group[0].get("llm_score", 0) # SOLUTION WITH SUM: sum([article.get("llm_score") for article in useable_articles_group])
                published_date = useable_articles_group[0].get('publish_date')
                text_links = ""
                for article in useable_articles_group: 
                    text_links += f" - <a href='/news/{article['url']}'>{article['title']} (S: {article['llm_score']})</a>"

                html_list_articles += f"<li>{published_date} - SCORE: {average_score} {text_links}</li>\n"
                
                trading_list = trading_strategies(average_score, published_date)
                trades_to_perform.extend(trading_list)

            html_list_articles += "</ul>"
        else:
            print("Performance has no useable analysed Articles")
            html_list_articles = "Performance has no useable analysed Articles"

        website_performance += html_list_articles

        trades_to_perform = sorted(trades_to_perform, key=lambda x: x[0])
        
        # Here a panda Database with the Stock information and the tradingresults is created
        panda_data = create_panda_trade_database(list_stock_history, trades_to_perform, dict_traiding_strategies)
        
        # displaying the Graph
        linechart_list = [("darkblue", "Close", "y1"), ("darkred", "Volume", "y2")]

        for index, (_, name) in enumerate(TRAINDING_STRATEGIES):
            linechart_list.append((COLORS[index], name+"_v", "y3")) # value of trading strategie
            linechart_list.append((COLORS[index], name+"_os", "y2")) # numer of owned Stocks

        fig = create_history_graph(panda_data, linechart_list, grouped_articles)
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        ticker_history = f"""
            <div id="plot"></div>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <script>
                var graphs = {graph_json};
                Plotly.newPlot("plot", graphs.data, graphs.layout);
            </script>
            """
        
        additional_performance_information = """
            _v : ist der Depotwert </br> 
            _os: sind die aktuell gehaltenen Positionen
            <hr>
            <h2> Übersciht über Tradingerfolg (: </h2>
            <ul>
            """
        last_data = panda_data.iloc[-1]
        for trading_str in dict_traiding_strategies.keys():
            additional_performance_information += f"<li> <b> {trading_str} </b> Depotvolumen: {last_data[trading_str+'_v']} - Veränderung: <i> {round(((last_data[trading_str+'_v'] / STARTING_DEPOT_VOLUME)-1)*100, 3)} % </i> </li>"

        additional_performance_information += "</ul>"    
    
    website_content = f"""
    <h2> Ticker - {ticker} </h2>
    ... scrape mehr Daten zu diesem Ticker <a href='/yahoo/stock/{ticker}'>{ticker}</a>
    <hr>
    {create_collabsable_box('Allgemeine Informationen', ticker_information)} 
    {create_collabsable_box('relevante Neuigkeiten', ticker_news)}
    {create_collabsable_box('Performance', website_performance + ticker_history + additional_performance_information)}

    """
    return website_content


def create_history_graph(df, linechart_list, grouped_articles):
    '''
    here the graph with ploy is created
    '''
    fig = go.Figure()

    # Adds Stockprice and trading Strategies
    for color_line, data_name, y_axis_name in linechart_list:  
        fig.add_scatter(
                x=df["Datetime"], 
                y=df[data_name].values.tolist(), 
                name=data_name,
                yaxis=y_axis_name,
                line=dict(color=color_line),
                visible="legendonly"
        )

    color_list = ["#66CCFF", "#660000", "#7A0000", "#8C1A1A", "#A03333", "#B34D4D", "#C66666", "#D98080", "#E69999", "#F0B3B3", "#F5CCCC", "#BFBFBF",   "#CCE0CC", "#B3D9B3", "#99D199", "#80C880", "#66BF66", "#4DB34D", "#339933", "#1A801A", "#006600", "#004C00"]
    # Adds dots for articles
    show_legend = True
    for artilce_group in grouped_articles:
        representation_article = artilce_group[0]
        article_score = representation_article.get('llm_score', -11)
        dot_color = color_list[article_score+11]
        hoverable_content = f"""
        <b>Date  :</b> {representation_article.get('publish_date', '-')} <br>
        <b>Title :</b> {representation_article.get('title', '-')} <br>
        <b>Score :</b> {representation_article.get('llm_score', '-')} <br>
        <b>Reason:</b> {representation_article.get('llm_reason', '-')} <br>
        """
        x_axis = representation_article.get('publish_date')
        mask = (
            (df['Datetime'].dt.year  == x_axis.year) &
            (df['Datetime'].dt.month == x_axis.month) &
            (df['Datetime'].dt.day   == x_axis.day) &
            (df['Datetime'].dt.hour  == x_axis.hour) &
            (df['Datetime'].dt.minute== x_axis.minute)
        )
        y_axis = df[mask]

        y_axis = 1 if y_axis.empty else y_axis["Close"].iloc[0]

        fig.add_scatter(
            x=[x_axis],
            y=[y_axis],
            mode="markers",
            name="articleResult",
            marker=dict(size=1*len(artilce_group)+8, color=dot_color, symbol="circle"),
            hovertemplate=hoverable_content,
            yaxis="y",
            legendgroup="articleResult",
            showlegend=show_legend,
            visible="legendonly"
        )
        show_legend = False

    # Add y-Axis
    fig.update_layout(
        xaxis=dict(title="Zeitpunkt"),
        yaxis=dict(
            title="Kurspreis",
            side="left",
            tickfont=dict(color="darkblue"),
        ),
        yaxis2=dict(
            title="Stückzahl",
            side="right",
            tickfont=dict(color="darkred"),
            overlaying="y",
            position=1, 
        ),
        yaxis3=dict(
            title="Portfoliowert",
            side="right",
            tickfont=dict(color="#000099"),
            overlaying="y",
            position=0.96, 
        ),
        legend=dict(x=0.05, y=1.05, orientation="h"),
        legend_title="Stocks History Info : "
    )

    return fig


def group_article(usable_articles):
    '''
    This function takes a list for Articleobjects and returns a grouped list of articles which will be returned.
    The grouped are created with the the analysed embeding
    '''
    # finding almost simular embeddings
    threshold = 0.8
    similarity_high = []
    for index1, article1 in enumerate(usable_articles):
        for index2, article2 in enumerate(usable_articles):
            if index1 < index2:
                vector1 = np.array(article1.get("embedding"))
                vector2 = np.array(article2.get("embedding"))
                if np.dot(vector1, vector2) > threshold:
                    similarity_high.append((index1, index2))

    # groupes the list
    result_list = []
    for index in range(len(usable_articles)):
        if index not in [item for item_list in result_list for item in item_list]:
            counter = 0
            check_articles = [index]
            while counter < len(check_articles):
                node = check_articles[counter]
                for node1, node2 in similarity_high:
                    if node == node1 and node2 not in check_articles:
                        check_articles.append(node2)
                    elif node == node2 and node1 not in check_articles:
                        check_articles.append(node1)
                counter += 1
            result_list.append(check_articles)

    grouped_list = []
    for index_list in result_list:
        helper_list = [usable_articles[index] for index in index_list]
        helper_list = sorted(helper_list, key=lambda x: x['publish_date'])
        grouped_list.append(helper_list)

    return grouped_list


def create_panda_trade_database(list_stock_history, trades_to_perform, dict_traiding_strategies):
    '''
    this function ctraetes the database with a list of Trades a dict of Trading strategies and the History data
    '''
    sorted_data = sorted(list_stock_history, key=lambda x: x["date_week_monday"])
    if sorted_data:
        helper_pd_dataframe = []
        for week_data in sorted_data:
            monday_date = week_data['date_week_monday']
            for second_data in week_data['data']:
                date_time_db = monday_date + timedelta(minutes=second_data['min_offset_time'])
                helper_pd_dataframe.append((date_time_db, second_data['close'], second_data['volume'],))

        pd_data_rows = []
        time_counter = sorted_data[0]['date_week_monday']
        last_data = (time_counter, helper_pd_dataframe[0][1], helper_pd_dataframe[0][2])
        while len(helper_pd_dataframe) > 0:
            actual_data = helper_pd_dataframe.pop(0) if time_counter >= helper_pd_dataframe[0][0] else last_data
            last_data = (time_counter, actual_data[1], actual_data[2])
            try:
                while time_counter >= trades_to_perform[0][0]:
                    # perform a trade
                    trades_to_do_object = trades_to_perform.pop(0)
                    for strategie, trade in trades_to_do_object[1:]:
                        actual_state = dict_traiding_strategies[strategie]
                        dict_traiding_strategies[strategie] = (actual_state[0] - actual_data[1]*trade, actual_state[1] + trade)
            except Exception as e:
                print("TRADINGexception", e)

            row = {
                    'Datetime': actual_data[0],
                    'Close': actual_data[1],
                    'Volume': actual_data[2], 
                }

            for strategie, actual_state in dict_traiding_strategies.items():
                row[strategie + '_os'] = actual_state[1] # owned Stocks
                row[strategie + '_v'] = actual_state[0] + actual_state[1]*actual_data[1] # portfolio value

            pd_data_rows.append(row)
            time_counter += timedelta(minutes=1)

        return pd.DataFrame(pd_data_rows)
    else:
        print("No History Data of the Stock")
        return pd.DataFrame([])

