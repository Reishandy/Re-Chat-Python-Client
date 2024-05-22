import httpx

from rechat import api_endpoint


def register(name: str, email: str, password: str) -> tuple[bool, str]:
    response = httpx.post(api_endpoint + 'register',
                          headers={'Content-Type': 'application/json'},
                          json={
                              'email': email,
                              'name': name,
                              'password': password
                          })

    match response.status_code:
        case 422:
            return False, response.json()['detail'][0]['msg']
        case 400:
            return False, response.json()['detail']
        case 201:
            return True, response.json()['detail']
        case _:
            return False, response.json()['detail']


def login(uuid_or_email: str, password: str) -> tuple[bool, str]:
    response = httpx.post(api_endpoint + 'login',
                          headers={'Content-Type': 'application/json'},
                          json={
                              'uuid_or_email': uuid_or_email,
                              'password': password
                          })

    match response.status_code:
        case 422:
            return False, response.json()['detail'][0]['msg']
        case 401:
            return False, response.json()['detail']
        case 200:
            response_json = response.json()
            credentials = {
                'uuid': response_json['uuid'],
                'access_token': response_json['access_token'],
                'refresh_token': response_json['refresh_token']
            }
            return True, '|'.join(credentials.values())
        case _:
            return False, response.json()['detail']


def get_details(uuid: str, access_token: str) -> str:
    response = httpx.get(api_endpoint + 'user/' + uuid,
                         headers={
                             'Content-Type': 'application/json',
                             'user_uuid': uuid,
                             'access-token': access_token,
                             'uuid': uuid
                         })

    match response.status_code:
        case 404:
            raise ValueError('User not found')
        case 401:
            raise RuntimeError('Unauthorized')
        case 200:
            response_json = response.json()
            user_data = {
                'uuid': response_json['uuid'],
                'email': response_json['email'],
                'name': response_json['name'],
            }
            return '|'.join(user_data.values())
        case _:
            raise ValueError(response.json()['detail'])


def get_contacts(uuid: str, access_token: str) -> list[str]:
    response = httpx.get(api_endpoint + 'get_contacts',
                         headers={
                             'Content-Type': 'application/json',
                             'access-token': access_token,
                             'uuid': uuid
                         })

    match response.status_code:
        case 404:
            raise ValueError('User not found')
        case 401:
            raise RuntimeError('Unauthorized')
        case 200:
            return response.json()['contacts']
        case _:
            raise ValueError(response.json()['detail'])


def refresh_token(uuid: str, refresh_token: str) -> str:
    response = httpx.post(api_endpoint + 'refresh',
                          headers={
                              'Content-Type': 'application/json',
                              'refresh-token': refresh_token,
                              'uuid': uuid
                          })

    match response.status_code:
        case 401:
            raise RuntimeError('Unauthorized')
        case 200:
            return response.json()['access_token']
        case _:
            raise ValueError(response.json()['detail'])


def logout(uuid: str, access_token: str) -> bool:
    response = httpx.delete(api_endpoint + 'logout',
                            headers={
                                'Content-Type': 'application/json',
                                'access-token': access_token,
                                'uuid': uuid
                            })

    match response.status_code:
        case 401:
            raise ValueError('Session does not exist')
        case 401:
            raise RuntimeError('Unauthorized')
        case 202:
            return True
        case _:
            raise ValueError(response.json()['detail'])


def add_contact(uuid: str, access_token: str, partner_uuid: str) -> tuple[bool, str]:
    response = httpx.post(api_endpoint + 'user/' + partner_uuid + '/add_to_contact',
                          headers={
                              'Content-Type': 'application/json',
                              'partner_uuid': partner_uuid,
                              'access-token': access_token,
                              'uuid': uuid
                          })

    match response.status_code:
        case 401:
            raise RuntimeError('Unauthorized')
        case 404:
            return False, response.json()['detail']
        case 201:
            return True, response.json()['detail']
        case _:
            return False, response.json()['detail']


if __name__ == '__main__':
    print(register('a', 'a@a.com', 'aaaaaaaa'))
    print(login('a@a.com', 'aaaaaaaa'))
