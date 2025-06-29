import logging
import os
import shutil
from pathlib import Path
from typing import Union
from .exceptions import *

logger = logging.getLogger(__name__)


class FileSystemValidator:
    @staticmethod
    def validate_input_file(file_path: Union[str, Path]) -> None:
        path = Path(file_path)

        if not path.exists():
            raise FileValidationError(
                f"Input file not found: {path}",
                error_code="FILE_NOT_FOUND",
                details={"path": str(path)},
            )

        if not path.is_file():
            raise FileValidationError(
                f"Path is not a file: {path}",
                error_code="NOT_A_FILE",
                details={"path": str(path)},
            )

        if not os.access(path, os.R_OK):
            raise FilePermissionError(
                f"Cannot read file: {path}",
                error_code="READ_PERMISSION_DENIED",
                details={"path": str(path)},
            )

    @staticmethod
    def validate_output_path(
        file_path: Union[str, Path], min_disk_space_mb: int = 10
    ) -> None:
        path = Path(file_path)
        parent_dir = path.parent

        # Create parent directory if it doesn't exist
        try:
            parent_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise FilePermissionError(
                f"Cannot create output directory: {parent_dir}",
                error_code="DIRECTORY_CREATION_FAILED",
                details={"path": str(parent_dir), "original_error": str(e)},
            )

        # Check write permissions
        if not os.access(parent_dir, os.W_OK):
            raise FilePermissionError(
                f"Cannot write to directory: {parent_dir}",
                error_code="WRITE_PERMISSION_DENIED",
                details={"path": str(parent_dir)},
            )

        # Check disk space
        free_space_mb = shutil.disk_usage(parent_dir).free / (1024 * 1024)
        if free_space_mb < min_disk_space_mb:
            raise InsufficientDiskSpaceError(
                f"Insufficient disk space. Required: {min_disk_space_mb}MB, Available: {free_space_mb:.1f}MB",
                error_code="INSUFFICIENT_DISK_SPACE",
                details={
                    "required_mb": min_disk_space_mb,
                    "available_mb": free_space_mb,
                    "path": str(parent_dir),
                },
            )


class PDFValidator:
    """Validates PDF files before processing"""

    @staticmethod
    def validate_pdf_file(file_path: Union[str, Path]) -> None:
        """Comprehensive PDF file validation"""
        path = Path(file_path)

        # Basic file validation first
        FileSystemValidator.validate_input_file(path)

        # Check file extension
        if path.suffix.lower() != ".pdf":
            raise PDFValidationError(
                f"File is not a PDF: {path}",
                error_code="INVALID_PDF_EXTENSION",
                details={"path": str(path), "extension": path.suffix},
            )

        # Check file size (empty files)
        if path.stat().st_size == 0:
            raise PDFValidationError(
                f"PDF file is empty: {path}",
                error_code="EMPTY_PDF_FILE",
                details={"path": str(path)},
            )

        # Check file size (too large - optional limit)
        max_size_mb = 50  # Configurable limit
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > max_size_mb:
            raise PDFValidationError(
                f"PDF file too large: {size_mb:.1f}MB (max: {max_size_mb}MB)",
                error_code="PDF_FILE_TOO_LARGE",
                details={
                    "path": str(path),
                    "size_mb": size_mb,
                    "max_size_mb": max_size_mb,
                },
            )


def handle_pdf_processing_error(
    e: Exception, operation: str, file_path: str
) -> KeywordGeneratorError:
    """Convert generic PDF errors to specific exceptions"""
    if "password" in str(e).lower() or "encrypted" in str(e).lower():
        return PDFEncryptedError(
            f"PDF is password-protected: {file_path}",
            error_code="PDF_ENCRYPTED",
            details={"path": file_path, "operation": operation},
        )

    if "corrupt" in str(e).lower() or "damaged" in str(e).lower():
        return PDFCorruptedError(
            f"PDF file appears corrupted: {file_path}",
            error_code="PDF_CORRUPTED",
            details={
                "path": file_path,
                "operation": operation,
                "original_error": str(e),
            },
        )

    return PDFError(
        f"PDF processing failed during {operation}: {str(e)}",
        error_code="PDF_PROCESSING_FAILED",
        details={"path": file_path, "operation": operation, "original_error": str(e)},
    )
