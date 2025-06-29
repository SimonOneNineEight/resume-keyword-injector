from pathlib import Path
import click
from typing import Optional

from ..pdf.reader import PDFReader
from ..pdf.writer import enhance_pdf_with_keywords

from .ui import (
    console,
    show_error,
    show_processing_panel,
    show_progress,
    show_success_panel,
    show_specific_error,
    show_validation_error,
    show_debug_info,
)

from ..utils.exceptions import *
from ..utils.error_handlers import PDFValidator, FileSystemValidator


@click.command()
@click.argument(
    "input_pdf", type=click.Path(exists=True, path_type=Path), required=False
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output PDF file path (default: input_optimized.pdf)",
)
@click.option(
    "--keywords",
    "-k",
    type=str,
    help="Comma-sparated list of keywords to inject (e.g., 'python,developer,software')",
)
@click.option(
    "--methods",
    "-m",
    type=str,
    default="white_text,tiny_font,transparent",
    help="Injection methods: white_text, tiny_font, margin, background, transparent",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode (makes invisible text visible for testing)",
)
# @click.option(
#     "--api-key",
#     envvar="ANTHROPIC_API_KEY",
#     help="Anthropic API key (or set ANTHROPIC_API_KEY env)",
# )
def main(
    input_pdf: Optional[Path],
    output: Optional[Path],
    keywords: Optional[str],
    methods: str = "white_text,tiny_font,transparent",
    debug: bool = False,
    # api_key: str,
):
    # if not api_key:
    #     console.print(
    #         "[red]Error: Anthropic API key required. Set ANTHROPIC_API_KEY environment variable or use --api-key option. [/red]"
    #     )
    #     raise click.Abort()
    #
    #
    console.print("[bold blue] PDF Keyword Injector [/bold blue]\n")

    if not input_pdf:
        console.print("[yellow] Select you PDF resume...[/yellow]")
        input_pdf = click.prompt(
            "Enter path to your resume", type=click.Path(exists=True, path_type=Path)
        )
        console.print()

    if not keywords:
        console.print("[yellow] Add some keywords to boost your ATS score...[/yellow]")
        keywords = click.prompt("Enter keywords (comma-separated)", type=str)
        console.print()

    if not output:
        default_output = input_pdf.parent / f"{input_pdf.stem}_optimized.pdf"
        console.print(
            "[yellow] Where should we save your enhanced (default: input_pdf_optimized.pdf) [/yellow]"
        )
        output_str = click.prompt(
            "Output filename", default=str(default_output), type=str
        )
        output = Path(output_str)
        console.print()

    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]

    if not keyword_list:
        show_error("No valid keywords provided")
        raise click.Abort()

    method_list = [m.strip() for m in methods.split(",") if m.strip()]

    show_processing_panel(input_pdf, output, keyword_list, method_list, debug)

    _validate_inputs(input_pdf, output)

    console.print()

    with show_progress() as progress:
        task = progress.add_task("Validating input PDF...", total=None)
        try:
            PDFValidator.validate_pdf_file(input_pdf)
            reader = PDFReader()
            validation_result = reader.extract_text(input_pdf)

            if not validation_result.success:
                progress.update(task, description="❌ PDF validation failed")
                if (
                    hasattr(validation_result, "exception")
                    and validation_result.exception
                ):
                    show_specific_error(
                        "PDF Validation Error",
                        validation_result.exception,
                        [
                            "Check that the PDF file is not corrupted",
                            "Try opening the PDF in a PDF viewer first",
                            "Use a different PDF file",
                        ],
                    )
                else:
                    show_error(f"Error reading PDF: {validation_result.error_message}")
                raise click.Abort()

            progress.update(
                task, description=f"PDF validated ({validation_result.page_count})"
            )
        except (PDFError, FileSystemError) as e:
            progress.update(task, description="Validation failed")
            show_specific_error(
                "PDF Validation Error",
                e,
                [
                    "Check that the PDF file exists and is readable",
                    "Ensure the PDF is not password protected",
                    "Try a different PDF file",
                ],
            )
            raise click.Abort()
        except Exception as e:
            progress.update(task, description="Validation failed")
            show_error(f"Error validating PDF: {str(e)}")
            raise click.Abort()

        progress.update(task, description="Injecting keywords...")

        try:
            result = enhance_pdf_with_keywords(
                input_pdf=input_pdf, keywords=keyword_list, output_path=output
            )

            if not result.success:
                progress.update(task, description="Process failed")
                _handle_processing_error(result)
                raise click.Abort()

            progress.update(task, description="Keyword injection completed")

        except (PDFError, FileSystemError) as e:
            progress.update(task, description="Processing failed")
            show_specific_error(
                "Processing Error",
                e,
                [
                    "Check your PDF file is valid",
                    "Try a different PDF file",
                    "Ensure you have sufficient disk space",
                ],
            )
            raise click.Abort()
        except Exception as e:
            progress.update(task, description="Unexpected error")
            show_error(f"Error during keyword injection: {str(e)}")
            if debug:
                import traceback

                console.print(f"[dim]{traceback.format_exc()}[/dim]")
            raise click.Abort()

        show_success_panel(output, result)


def _validate_inputs(
    input_pdf: Optional[Path],
    output: Optional[Path],
):
    if input_pdf:
        try:
            PDFValidator.validate_pdf_file(input_pdf)
        except PDFValidationError as e:
            show_validation_error("Input PDF", e)
            raise click.Abort()

        except FileValidationError as e:
            show_validation_error("Input PDF", e)
            raise click.Abort()

    if output:
        try:
            FileSystemValidator.validate_output_path(output)
        except FilePermissionError as e:
            show_validation_error("Output path", e)
            raise click.Abort()
        except InsufficientDiskSpaceError as e:
            show_validation_error("Output path", e)
            raise click.Abort()


def _handle_processing_error(result):
    error_code = result.error_code

    if error_code == "PDF_ENCRYPTED":
        error = PDFEncryptedError(
            result.error_message,
            error_code=error_code,
            details=result.error_detail or {},
        )
        show_specific_error(
            "🔒 Encrypted PDF",
            error,
            [
                "Remove password protection from the PDF",
                "Use a different PDF file",
                "Contact the PDF creator for the password",
            ],
        )
    elif error_code == "PDF_CORRUPTED":
        error = PDFCorruptedError(
            result.error_message,
            error_code=error_code,
            details=result.error_detail or {},
        )
        show_specific_error(
            "🗑️  Corrupted PDF",
            error,
            [
                "Try opening the PDF in a PDF viewer to verify",
                "Use a different PDF file",
                "Try to repair the PDF using online tools",
            ],
        )
    elif error_code == "INSUFFICIENT_DISK_SPACE":
        available_mb = (
            result.error_detail.get("available_mb", "unknown")
            if result.error_detail
            else "unknown"
        )
        error = InsufficientDiskSpaceError(
            result.error_message,
            error_code=error_code,
            details=result.error_detail or {},
        )
        show_specific_error(
            "💾 Disk Space Error",
            error,
            [
                f"Free up disk space (only {available_mb}MB available)",
                "Choose a different output location",
                "Use a smaller PDF file",
            ],
        )
    else:
        # For unknown errors, just use show_error
        show_error(f"Processing failed: {result.error_message}")


if __name__ == "__main__":
    main()
