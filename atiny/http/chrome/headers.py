

def justify_dict_by_line(dt):

    print("{")
    for key, value in dt.items():
        print(f"\t'{key}': '{value}',")

    print("}")

def convert_request_headers_to_dict(headers):
    text_headers = '''
    '''
    headers = {}
    for line in text_headers.split('\n'):
        if not line:
            continue

        if not line.replace(' ', ''):
            continue

        word = line[0]
        while word == ' ':
            ind = line.index(word)
            line = line[ind+1:]
            word = line[0]

        key = line.split(':')[0]
        value = line.replace(f'{key}: ', '')

        headers[key] = value

    justify_dict_by_line(headers)
