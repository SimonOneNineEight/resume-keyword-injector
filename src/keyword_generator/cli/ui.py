import os
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
from typing import List
from contextlib import contextmanager

from ..utils.exceptions import KeywordGeneratorError

console = Console()


def show_validation_error(context: str, error: KeywordGeneratorError):
    console.print(
        Panel(
            f"[red]{context} Validation Failed[/red]\n\n"
            f"Error: {error.message}\n"
            f"Code: {error.error_code} \n\n"
            f"Details: {error.details}",
            title=f"{context} Error",
        )
    )


def show_specific_error(title: str, error: KeywordGeneratorError, solutions: List[str]):
    solutions_text = "\n".join(f"- {solution}" for solution in solutions)

    console.print(
        Panel(
            f"[red]{error.message}[/red]\n\n"
            f"[yellow]Suggested Solutions:[/yellow]\n"
            f"{solutions_text}\n\n"
            f"[dim]Error Code: {error.error_code}[/dim]",
            title=title,
        )
    )


def show_debug_info(error: KeywordGeneratorError):
    console.print(
        Panel(
            f"[red]Error Details[/red]\n\n"
            f"Message: {error.message}\n"
            f"Code: {error.error_code}\n"
            f"Details: {error.details}\n"
            f"Exception Type: {type(error).__name__}",
            title=" Debug Information",
        )
    )


def show_processing_panel(
    input_pdf: Path, output: Path, keywords: List[str], methods: List[str], debug: bool
):
    console.print(
        Panel(
            f"[bold green]PDF Keyword Injector[/bold green]\n"
            f"Input: {input_pdf}\n"
            f"Output: {output}\n"
            f"Keywords: {', '.join(keywords)}\n"
            f"Methods: {', '.join(methods)}\n"
            f"Debug Mode: {'ON' if debug else 'OFF'}",
            title="Processing Configuration",
        )
    )


def show_success_panel(output_path: Path, result):
    console.print(
        Panel(
            f"[bold green]✓ Success![/bold green]\n"
            f"Enhanced PDF saved: {output_path}\n"
            f"Keywords injected: {len(result.keywords_injected)}\n"
            f"Processing time: {result.processing_time:.2f}s\n"
            f"Original text length: {result.original_text_length}\n"
            f"Final text length: {result.final_text_length}",
            title="Processing Complete",
        )
    )


def show_error(message: str):
    console.print(f"[red]Error: {message}[/red]")


def show_warning(message: str):
    console.print(f"[yellow]Warning: {message}[/yellow]")


def show_info(message: str):
    console.print(f"[blue]Info: {message}[/blue]")


@contextmanager
def show_progress():
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        yield progress
