import pytest
import task_Torshin_Dmitrii_asset_web_service as task


@pytest.fixture
def client():
    with task.app.test_client() as client:
        yield client


def test_route_does_not_exist(client):
    response = client.get("/abc")
    assert 404 == response.status_code


def test_parse_cbr_currency_base_daily():
    with open("cbr_currency_base_daily.html") as fin:
        daily_currencies_html = fin.read()
    currencies_dict = task.parse_cbr_currency_base_daily(daily_currencies_html)
    assert "AUD" in currencies_dict
    assert 0.0681688 == currencies_dict["KRW"]


def test_parse_cbr_key_indicators():
    with open("cbr_key_indicators.html") as fin:
        key_indicators_html = fin.read()
    key_indicators_dict = task.parse_cbr_key_indicators(key_indicators_html)
    assert 75.4571 == key_indicators_dict["USD"]
    assert 4529.59 == key_indicators_dict["Au"]


def test_add_asset(client):
    response = client.get("/api/asset/add/RUB/First/1000/1.01")
    assert 200 == response.status_code


def test_show_list_of_assets_to_json(client):
    client.get("/api/asset/add/RUB/First/1000/1.01")
    client.get("/api/asset/add/EUR/Second/100/1.02")
    response = client.get('/api/asset/list')
    assert 200 == response.status_code

    good_response = '[["EUR","Second",100.0,1.02],["RUB","First",1000.0,1.01]]\n'
    assert response.data.decode(response.charset) == good_response


def test_remove_all_assets_from_bank(client):
    client.get("/api/asset/add/RUB/First/1000/1.01")
    client.get("/api/asset/add/EUR/Second/100/1.02")
    response = client.get('/api/asset/cleanup')
    assert 200 == response.status_code

    response = client.get('/api/asset/list')
    assert response.data.decode(response.charset) == '[]\n'


def test_get_assets_info(client):
    client.get('/api/asset/cleanup')
    client.get("/api/asset/add/RUB/First/1000/1.01")
    client.get("/api/asset/add/EUR/Second/100/1.02")
    response = client.get('/api/asset/get?name=First&name=Second')
    assert 200 == response.status_code
    good_response = '[["EUR","Second",100.0,1.02],["RUB","First",1000.0,1.01]]\n'
    assert response.data.decode(response.charset) == good_response


def test_calculate_revenue(client):
    client.get('/api/asset/cleanup')
    client.get("/api/asset/add/EUR/Second/100/0.01")
    response = client.get('/api/asset/calculate_revenue?period=1&period=2')
    assert 200 == response.status_code
    good_response = '{"1":90.7932,"2":182.494332}\n'
    assert response.data.decode(response.charset) == good_response