from flask import render_template
from markupsafe import Markup

# --------------------------------------------------------------------------------------------
# In this Document are Constants which can be canged to make easy adjustments to the porgramm
# --------------------------------------------------------------------------------------------

# DATABASE CONNECTION
DB_USERNAME = "StockForecast_rw"
DB_PASSWORD = "sEZ_ctuB0-N?"
DB_HOST = "mongodb.lehre.texttechnologylab.org"
DB_PORT = 27022
DB_DATABASE = "StockForecast"

# TEMPLATE HEADER FOR THE WEBSITE
HEADER = '''
<div style="
    position: fixed;
    width: -webkit-fill-available;
    background-color: rgb(75, 150, 150);
    position-area: y-start;
    margin-top: -21px;
    padding-top: 25px;
">
<a style="margin-left: 4%;margin-right: 4%;" href="/">Startwebseite</a>
<a style="/* margin-right: 4%; */margin-left: 4%;margin-right: 4%;" href="/yahoo">Yahoo-Suchseite</a>
<a style="margin-right: 4%;margin-left: 4%;" href="/database">Datenbank-Suchseite</a>
<hr>
</div>
    <div style="
    height: 65px;
    width: 100%;
"></div>  
'''

# TEMPLATE FOOTER FOR THE WEBSITE
FOOTER = '''
<hr>
created by: tradeTheNews :) - Ioan & Kyan
'''


def create_collabsable_box(headline, content):
    '''
    this funciton creates with collabsable box with a headline and some content
    '''
    return f"""
        <div style='background-color: #3973ac; position: relative; z-index: -1; border: outset; text-align: center; padding: 5px;'>
            <p style='margin: 10px;'><strong>{headline}</strong></p>
        </div>
        <details> 
            <summary> show ...</summary>
            <div>
                {content}
            </div>
        </details> 
    """

def return_template(**kwargs):
    '''
    this function renders the html website with the HEADER and FOOTER
    '''
    kwargs["header"] = Markup(HEADER)
    kwargs["footer"] = Markup(FOOTER)
    return render_template(**kwargs)

# FOR QUERY 
# Query will look in the end: QUERY_INFRONT_OF_NEWS + {userInput} + QUERY_AFTER_NEWS
QUERY_INFRONT_OF_NEWS = "news"
QUERY_AFTER_NEWS = ""