class KeywordGeneratorError(Exception):
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

    def __str__(self):
        return f"[{self.error_code}] {self.message}"


# PDF-related exceptions
class PDFError(KeywordGeneratorError):
    pass


class PDFValidationError(PDFError):
    pass


class PDFCorruptedError(PDFError):
    pass


class PDFEncryptedError(PDFError):
    pass


class PDFPermissionError(PDFError):
    pass


class KeywordInjectionError(PDFError):
    pass


# File system exceptions
class FileSystemError(KeywordGeneratorError):
    pass


class FileValidationError(FileSystemError):
    pass


class InsufficientDiskSpaceError(FileSystemError):
    pass


class FilePermissionError(FileSystemError):
    pass


class PathValidationError(FileSystemError):
    pass


# Claude API exceptions
class ClaudeAPIError(KeywordGeneratorError):
    pass


class ClaudeRateLimitError(ClaudeAPIError):
    pass


class ClaudeNetworkError(ClaudeAPIError):
    pass


class ClaudeAuthenticationError(ClaudeAPIError):
    pass


class ClaudeResponseError(ClaudeAPIError):
    pass


# CLI exceptions
class CLIError(KeywordGeneratorError):
    pass


class InputValidationError(CLIError):
    pass


class ConfigurationError(CLIError):
    pass
