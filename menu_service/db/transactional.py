from functools import wraps


def transactional(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            result = method(self, *args, **kwargs)
            self.db.commit()
            return result
        except Exception:
            self.db.rollback()
            raise

    return wrapper
