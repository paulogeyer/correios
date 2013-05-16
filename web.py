from flask import Flask
from flask import render_template
import urllib2
import correio
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World"

@app.route("/track/<id>")
def track(id):
    page = urllib2.urlopen("http://websro.correios.com.br/sro_bin/txect01$.QueryList?P_LINGUA=001&P_TIPO=001&P_COD_UNI="+id)
    events = correio.parse(page.read())
    return render_template('track.html', events=events)

if __name__ == "__main__":
    app.run(debug=True)
