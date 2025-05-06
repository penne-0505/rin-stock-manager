from urllib.parse import urlparse


def get_param_value(url: str, param_name: str) -> str:
    """URL から指定したパラメータの値を取得する。`url`は完全なURLである必要がある。"""
    parsed_url = urlparse(url)
    query = parsed_url.query
    params = dict(q.split("=") for q in query.split("&"))
    return params.get(param_name, None)
