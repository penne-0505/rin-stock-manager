class RecordNotFoundError(KeyError):
    """指定 ID のレコードが見つからない場合に送出."""


class ConflictError(RuntimeError):
    """同時更新など競合が起きた場合に送出."""
