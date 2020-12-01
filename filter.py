import argparse
import json
import requests
import sys
from os.path import basename, splitext


def send_request(url, method, query=None, data=None):
    headers = {
        "Content-Type": "application/json",
        "Authorization": authorization_header,
    }

    if method.upper() == 'GET':
        resp = requests.get(url=url, params=query, headers=headers)
    elif method.upper() == 'POST':
        resp = requests.post(url=url, data=json.dumps(data), headers=headers)
    resp_obj = resp.json()
    if resp.status_code not in [200, 201, 204]:
        msg = resp_obj['Message'] if 'Message' in resp_obj else resp_obj['message']
        print(resp.status_code, msg, file=sys.stderr)
        sys.exit(1)
    return resp_obj

def get_vocabulary_list_id(name):
    query = {"language": "en"}
    resp_obj = send_request(url='https://api.frdic.com/api/open/v1/studylist/category',method='GET',query=query)
    data = resp_obj['data']
    vocab_list_id_arr = [l['id'] for l in data if l['name'] == name]
    if not vocab_list_id_arr:
        return None
    else:
        return vocab_list_id_arr[0]

def create_new_vocabulary_list(name):
    data = {
        "language": "en",
        "name": name
    }
    resp_obj = send_request(url="https://api.frdic.com/api/open/v1/studylist/category", method="POST", data=data)
    resp_data = resp_obj['data']
    return resp_data['id']

def add_words_to_vocab_list(list_id, words):
    data = {"id": list_id, "words": words, "language": "en"}
    send_request(url="https://api.frdic.com/api/open/v1/studylist/words", method="POST", data=data)  

if __name__ == "__main__":
    authorization_header = ""
    parser = argparse.ArgumentParser(description='Extract marked words')
    parser.add_argument('src', metavar='ORIGINAL FILE', type=str, nargs='?',
                        help='the original file containing all the words')
    parser.add_argument('--out', metavar='OUTPUT FILE', type=str, nargs='?',
                        help='the output file containing only the marked words')
    parser.add_argument('--upload', action='store_true', help="upload the marked words to EUDIC vocabulary list.")
    parser.add_argument('--name', metavar='VOCABULARY LIST NAME', nargs='?', help='the name of the vocabulary list to upload the marked words to')
    parser.add_argument('--mark', metavar='MARK', nargs="?", default='*', help="the mark at the beginning of marked words. Defaults to '*' ")

    args = parser.parse_args()

    src = args.src
    out = args.out
    upload = args.upload
    name = args.name
    mark = args.mark

    if not name:
        name = splitext(basename(src))[0]
    marked_words = []
    with open(src, "r") as s:
        words = s.readlines()
        for word in words:
            if word.lstrip().startswith(mark):
                marked_words.append(word.lstrip()[len(mark):].lstrip())
        if not marked_words:
            print("no words marked!", file=sys.stderr)
            sys.exit(1)
    if out:
        with open(out, "w") as o:
            o.writelines(marked_words)
        print(f"Successfully wrote {len(marked_words)} words to {out}!" )
    if upload:
        uploaded_words = [word.strip() for word in marked_words]
        list_id = get_vocabulary_list_id(name)
        if not list_id:
            list_id = create_new_vocabulary_list(name)
        add_words_to_vocab_list(list_id, uploaded_words)
        print(f"Successfully added {len(uploaded_words)} words to EUDIC list {name}!")
    