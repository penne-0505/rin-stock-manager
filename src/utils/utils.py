from urllib.parse import parse_qs, urlparse


def get_param_value(url: str, param_name: str) -> str | None:
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    param_values_list = query_params.get(param_name)

    return param_values_list[0] if param_values_list else None


def get_param_list(url: str) -> list[str]:
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return list(query_params.keys())
