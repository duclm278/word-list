class Setup:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0"
        }
        self.proxies = {}
    
    def set_proxies(self):
        print("https://proxy.webshare.io/proxy/rotating")
        username = input("Proxy Username: ")
        password = input("Proxy Password: ")
        self.proxies = {
            "http": f"http://{username}:{password}@p.webshare.io:80/",
            "https": f"http://{username}:{password}@p.webshare.io:80/",
        }