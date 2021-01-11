from flask import Flask, abort, jsonify, request
from bs4 import BeautifulSoup
import requests


app = Flask(__name__)

DAILY_CURRENCY_LINK = "https://www.cbr.ru/eng/currency_base/daily/"
KEY_INDICATORS_LINK = "https://www.cbr.ru/eng/key-indicators/"


def parse_cbr_currency_base_daily(document):
    """returns currencies from hmtl file into dict"""
    currency_dict = {}
    soup = BeautifulSoup(document, 'html.parser')
    table = soup.find('tbody')
    for index, line in enumerate(table.find_all('tr')):
        if index > 0:
            items = line.find_all('td')
            currency_dict[items[1].get_text()] = round(float(items[4].get_text()) / \
                int(items[2].get_text()), 8)
    return currency_dict


def parse_cbr_key_indicators(document):
    """puts indicators from hmtl file into dict"""
    indicators_dict = {}
    soup = BeautifulSoup(document, 'html.parser')
    currencies = soup.find("div", {"class": "key-indicator_content offset-md-2"})
    currencies_table = currencies.find('tbody')
    for index, line in enumerate(currencies_table.find_all('tr')):
        if index > 0:
            currency = line.find("div", \
                {"class": "col-md-3 offset-md-1 _subinfo"}).get_text()
            value = line.find_all("td")[2].get_text()
            indicators_dict[currency] = float(value)

    metals = soup.find_all("div", {"class": "key-indicator_content offset-md-2"})[1]
    metals_table = metals.find('tbody')
    for index, line in enumerate(metals_table.find_all('tr')):
        if index > 0:
            metal = line.find("div", \
                {"class": "col-md-3 offset-md-1 _subinfo"}).get_text()
            value = line.find_all("td")[1].get_text()
            indicators_dict[metal] = float(value.replace(",", ""))

    return indicators_dict


@app.errorhandler(404)
def page_not_found(error):
    """fix 404 page"""
    return "This route is not found", 404


@app.errorhandler(503)
def cbr_unavailable(error):
	"""fix 503 page"""
	return "CBR service is unavailable", 503


@app.route('/cbr/daily')
def get_cbr_daily_currencies():
    """api to get json data from cbr currencies"""
    cbr_response = requests.get(DAILY_CURRENCY_LINK)
    if not cbr_response.ok:
        abort(503)
    currency_dict = parse_cbr_currency_base_daily(cbr_response.text)
    return jsonify(currency_dict)


@app.route('/cbr/key_indicators')
def get_cbr_key_indicators():
    """api to get json data from cbr indicators"""
    cbr_response = requests.get(KEY_INDICATORS_LINK)
    if not cbr_response.ok:
        abort(503)
    indicators_dict = parse_cbr_key_indicators(cbr_response.text)
    return jsonify(indicators_dict)


class Asset:
    """Asset class"""
    def __init__(self, char_code: str, name: str, capital: float, interest: float):
        """Init asset"""
        self.char_code = char_code
        self.name = name
        self.capital = capital
        self.interest = interest

    def calculate_revenue(self, years: int) -> float:
        """Calculate revenue in roubles"""
        revenue = self.capital * ((1.0 + self.interest) ** years - 1.0)
        return revenue


class CompositeAsset:
    """Bank of assets"""
    def __init__(self, assets=None):
        """Init composite of assets"""
        self.assets = []
        self.assets.extend(assets or [])

    def calculate_revenue(self, years: int, rates_dict) -> float:
        """Calculate revenue of all assets included"""
        revenue = 0
        for asset in self.assets:
            try:
                rate = rates_dict[asset.char_code]
            except Exception:
                rate = 1
            revenue += rate * asset.calculate_revenue(years)
            print(revenue)
        return revenue

    def add(self, asset: Asset):
        """Add new asset to list"""
        self.assets.append(asset)


app.bank = CompositeAsset()

@app.route('/api/asset/add/<char_code>/<name>/<capital>/<interest>')
def add_asset_to_bank(char_code, name, capital, interest):
    """api which creates Asset object and adds it to the bank"""
    for asset in app.bank.assets:
        if asset.name == name:
            abort(403)

    try:
        capital = float(capital)
        interest = float(interest)
    except Exception:
        abort(404)

    new_asset = Asset(char_code, name, capital, interest)
    app.bank.add(new_asset)
    return f"Asset {name} was successfully added"


@app.route('/api/asset/list')
def show_list_of_assets_to_json():
    """show list of assets in the bank"""
    assets = app.bank.assets
    assets_list = [[asset.char_code, asset.name, round(asset.capital, 8), \
        round(asset.interest, 8)] for asset in assets]
    return jsonify(sorted(assets_list))


@app.route('/api/asset/cleanup')
def remove_all_assets_from_bank():
    """empty bank of assets"""
    app.bank.assets = []
    return "All assets were removed"


@app.route('/api/asset/get')
def get_assets_info():
    """get info about interesting assets to json"""
    good_asset_names = request.args.getlist('name')
    assets_list = []
    for asset in app.bank.assets:
        if asset.name in good_asset_names:
            assets_list.append([asset.char_code, asset.name, \
                round(asset.capital, 8), round(asset.interest, 8)])
    return jsonify(sorted(assets_list))


@app.route('/api/asset/calculate_revenue')
def calculate_revenue():
    """Get total revenue of listed periods"""
    periods = request.args.getlist('period')
    result = {}

    cbr_response = requests.get(KEY_INDICATORS_LINK)
    if not cbr_response.ok:
        abort(503)
    indicators_dict = parse_cbr_key_indicators(cbr_response.text)

    cbr_response = requests.get(DAILY_CURRENCY_LINK)
    if not cbr_response.ok:
        abort(503)
    currency_dict = parse_cbr_currency_base_daily(cbr_response.text)
    del currency_dict['USD']
    del currency_dict['EUR']

    rates_dict = {**indicators_dict, **currency_dict}

    for period in periods:
        period = int(period)
        result[period] = round(app.bank.calculate_revenue(years=period, rates_dict=rates_dict), 8)
    return jsonify(result)
