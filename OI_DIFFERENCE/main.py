creds = {
    "API_KEY": "",
    "ACCESS_TOKEN": ""
}

from kiteconnect import KiteConnect, KiteTicker

def get_zerodha_client(creds):
    zerodha = KiteConnect(api_key = creds["API_KEY"])
    zerodha.set_access_token(creds["ACCESS_TOKEN"])
    return zerodha


zerodha = get_zerodha_client(creds)
ins = zerodha.instruments()
ce = [one_ins for one_ins in ins if one_ins["tradingsymbol"].startswith("NIFTY") and one_ins["instrument_type"] == "CE"]
print(len(ce))