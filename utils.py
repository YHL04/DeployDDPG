

def read_tickers(filename):
    with open(filename) as f:
        tickers = f.readlines()
    tickers = [t.strip() for t in tickers]
    return tickers

def read_parameters(filename):
    d = {}
    with open(filename) as f:
        for line in f:
            (key, val) = line.split(" = ")
            d[key] = int(val)
    return d
