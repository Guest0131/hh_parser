import requests, base64, json

class ApiParser:
    """ApiParser

        Api class for connect server from API and executing commands
    """
    def __init__(self, ip, token):
        """Initialize

        Args:
            ip (str): ip address server
        """
        self.__ip    = str(ip)
        self.__token = str(token)
        if 'http' not in self.__ip:
            self.__ip = 'https://' + self.__ip

        if '/api.php' not in  self.__ip:
            self.__ip += '/api.php'

    def parse_status(self):
        """
        Get status parsing
            0 - no parsing
            1 - have one parsing-task
            2 - have 2 parsing-tasks
            ...

        Returns:
            int : count parsing-task(s)
        """
        response = requests.get(self.__ip + '?method=status&token=' + self.__token)
        return json.loads(response.content)

    def execute_parse(self, url, mode='current'):
        """
        Execute parsing for special url.
        Or append parsing-task

        Args:
            url (str): url from hh.ru
            mode (str, optional): 'current' or 'all'. Defaults to 'current'.

        Returns:
            bool: start parsing or not
        """
        b64url = base64.b64encode(url.encode()).decode("ascii")

        if mode not in ('current', 'all'):
            return False

        try:
            print(url)
            print(self.__ip + '?method={method}&url={url}&mode={mode}&token={token}'.format(
                    method='execute',
                    url=b64url,
                    mode=mode,
                    token=self.__token))
            requests.get(
                self.__ip + '?method={method}&url={url}&mode={mode}&token={token}'.format(
                    method='execute',
                    url=b64url,
                    mode=mode,
                    token=self.__token
                ),
            timeout=2)
        except requests.exceptions.ReadTimeout: 
            pass

        return True

