class RecordNotFoundError(KeyError):
    """指定 ID のレコードが見つからない場合に送出."""


class RepositoryError(RuntimeError):
    """汎用リポジトリのエラー基底クラス."""


class NotFoundError(RepositoryError):
    """指定 ID のレコードが見つからない場合に送出."""


class ConflictError(RepositoryError):
    """競合が発生した場合に送出."""


class ValidationError(RepositoryError):  # 使用未定
    """入力データの検証に失敗した場合に送出."""
