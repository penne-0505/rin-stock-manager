from urllib.parse import parse_qs, urlparse  # parse_qs をインポート


def get_param_value(url: str, param_name: str) -> str | None:
    """URL から指定したパラメータの値を取得する。`url`は完全なURLである必要がある。"""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    param_values_list = query_params.get(param_name)

    return param_values_list[0] if param_values_list else None


def get_param_list(url: str) -> list[str]:
    """URL から全てのパラメータ名を取得する。`url`は完全なURLである必要がある。"""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return list(query_params.keys())
