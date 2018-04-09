from requests_oauthlib import OAuth2

def combine_headers(header_one, header_two):
    if header_two is None:
        return header_one
    elif header_one is None:
        return header_two
    else:
        return {**header_one, **header_two}


def save_attribute_items(target, response_attributes):
    for key,value in response_attributes.items():
        setattr(target, key, value)


def unwrap_data(response):
    if 'data' in response:
        return response['data']
    else:
        return response


def bearer_token_auth(token):
    token_dict = {
        'token_type': 'Bearer',
        'access_token': token
    }
    return OAuth2(token=token_dict)
