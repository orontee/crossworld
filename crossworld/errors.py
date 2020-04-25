class ApplicationError(RuntimeError):
    pass


class CrosswordNotFoundError(ApplicationError):
    pass


class FileAlreadyExistError(ApplicationError):
    pass
