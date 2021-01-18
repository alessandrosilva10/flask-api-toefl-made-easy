import json

from flask import Flask, request
from flask_restful import Resource, Api
from deep_translator import GoogleTranslator
import sqlite3

app = Flask(__name__)
app.secret_key = "ETFKn!RCNTE&KTU_k6&!K*tU7uK2$xreGe@Q^@yKX74B^ydNkaj@F%746@A@*VU!"
api = Api(app)


class Translation(Resource):
    def get(self):
        data = request.get_json(force=True)
        word = data['word']
        target = data['target']
        # https://stackabuse.com/text-translation-with-google-translate-api-in-python/
        translated = GoogleTranslator(source='auto', target='pt').translate(word)
        print(translated)
        return translated, 200 if translated is not None else 404


class ToeflResources(Resource):
    def post(self):
        conn = sqlite3.connect("database.db")
        print("Opened database successfully")
        conn.execute("CREATE TABLE IF NOT EXISTS TB_TOEFL (id INTEGER PRIMARY KEY AUTOINCREMENT, texto TEXT, "
                     "tpo_id INTEGER)")

        try:
            data = request.get_json(force=True)
            texto = data['texto']
            tpo_id = data['tpo_id']

            with sqlite3.connect("database.db") as con:
                cur = con.cursor()
                cur.execute("INSERT INTO TB_TOEFL (texto, tpo_id) VALUES (?, ?)", (texto, tpo_id))
                print("Record successfully added")
        except ValueError as e:
            return e

        conn.close()
        return data, 201 if data is not None else 404


class ToeflResourcesList(Resource):
    def get(self):
        conn = sqlite3.connect("database.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT id, texto FROM TB_TOEFL")
        rows = cur.fetchall()
        conn.close()
        data = []
        for row in rows:
            data.append([x for x in row])

        return data


class ToeflItemResourcesList(Resource):
    def get(self, tpo):
        conn = sqlite3.connect("database.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM TB_TOEFL WHERE tpo_id=?;", [tpo])
        rows = cur.fetchall()
        conn.close()

        data = eval(json.dumps([tuple(row) for row in rows]))
        print(data[0][1])
        return eval(json.dumps([tuple(row) for row in rows]))


api.add_resource(Translation, '/translation')
api.add_resource(ToeflResourcesList, '/toefl')
api.add_resource(ToeflItemResourcesList, '/toefl/<int:tpo>')
api.add_resource(ToeflResources, '/store')

app.run(port=5000, debug=True)
