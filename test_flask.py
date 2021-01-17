from hello_world import app as hello_world_app
import hello_world
import pytest


@pytest.fixture
def client():
    with hello_world_app.test_client() as client:
        yield client


def test_service_reply_to_root_path(client):
    response = client.get("/")
    assert 'world' in response.data.decode(response.charset)


def test_service_reply_to_username(client):
    response = client.get("/hello/Vasya", follow_redirects=True)
    assert 'Vasya' in response.data.decode(response.charset)


def test_service_reply_to_usernames_several_times(client):
    username = 'Petya'
    expected_count = 10
    response = client.get(f"/hello/{username}/{expected_count}", follow_redirects=True)
    response_text = response.data.decode(response.charset)
    petya_count = response_text.count(username)
    assert petya_count == expected_count


def test_service_reply_to_escaped_username(client):
    html_tag = '<br>'
    username = 'Kostya'
    response = client.get(f"/hello/{html_tag}{username}")
    response_text = response.data.decode(response.charset)
    assert username in response_text
    assert 0 == response_text.count(html_tag)


def test_service_hello_to_username_with_slash(client):
    username = 'Vasya'
    response = client.get(f"/hello/{username}/")
    assert 200 == response.status_code


def test_service_reply_to_usernames_over_max_times(client):
    username = 'Petya'
    greeting_count = hello_world.MAX_GREETING_COUNT + 1
    expected_count = hello_world.MAX_GREETING_COUNT
    response = client.get(f"/hello/{username}/{greeting_count}", follow_redirects=True)
    response_text = response.data.decode(response.charset)
    petya_count = response_text.count(username)
    assert petya_count == expected_count


def test_service_reply_to_usernames_loads_of_times(client):
    username = 'Petya'
    greeting_count = hello_world.REALLY_TOO_MANY_GREETING_COUNT
    response = client.get(f"/hello/{username}/{greeting_count}", follow_redirects=True)
    assert 404 == response.status_code

    response_text = response.data.decode(response.charset)
    petya_count = response_text.count(username)
    assert petya_count == 0