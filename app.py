from datetime import datetime

import requests
from bson import ObjectId
from flask import Flask, jsonify, redirect, render_template, request, url_for
from pymongo import MongoClient

client = MongoClient(
    "mongodb+srv://test:asan@cluster0.hmhssac.mongodb.net/?retryWrites=true&w=majority")

app = Flask(__name__)
db = client.dbsparta


@app.route('/')
def main():
    words_result = db.words.find({}, {'_id': False})
    words = []
    for word in words_result:
        definition = (word['definitions'][0]['shortdef'])
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })
    msg = request.args.get('msg')
    return render_template(
        'index.html',
        words=words,
        msg=msg
    )


@app.route('/error')
def error():
    word = request.args.get('word')
    suggestions = request.args.get('suggestions')
    if suggestions:
        suggestions = suggestions.split(',')
    return render_template(
        'error.html',
        word=word,
        suggestions=suggestions
    )


@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = "a222de28-5651-402e-8a5d-222fcd2263ef"
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()

    if not definitions:
        return redirect(url_for(
            'error',
            word=keyword
        ))

    if type(definitions[0]) is str:
        return redirect(url_for(
            'error',
            word=keyword,
            suggestions=','.join(definitions)
        ))

    status = request.args.get('status_give', 'new')
    return render_template(
        'detail.html',
        word=keyword,
        definitions=definitions,
        status=status
    )

#bagian button save and delete
@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    doc = {
        'word': word,
        'definitions': definitions,
        'date': datetime.now().strftime('%Y.%m.%d'),
    }
    db.words.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'the word was saved',
        'date': datetime.now().strftime('%Y.%m.%d'),
    })


@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    word = request.form.get('word_give')
    db.words.delete_one({'word': word})
    db.examples.delete_many({"word" : word})

    return jsonify({
        'result': 'success',
        'msg': f'the word was deleted'
    })

#bagian save,delete,get example
@app.route("/api/get_exs", methods=["GET"])
def get_exs():
    word = request.args.get("word_give")
    exdata = db.examples.find({"word": word})
    examples = []
    for example in exdata :
        examples.append({
            "example" : example.get("example"),
            "id" : str(example.get("_id"))
        })

    return jsonify({"result":"success","examples" : examples})

@app.route("/api/save_ex", methods=["POST"])
def save_ex():
    word = request.form.get("word_give")
    example = request.form.get("example")
    doc = {
        "word" : word,
        "example" : example,
    }
    db.examples.insert_one(doc)
    return jsonify({"result":"success","msg": f"Your sentence was saved"})

@app.route("/api/delete_ex", methods=["POST"])
def delete_ex():
    id = request.form.get("id")
    word = request.form.get("word")
    db.examples.delete_one({"id": ObjectId(id)})

    return jsonify({"result":"success", "msg":f"Your sentence was deleted"})


if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
