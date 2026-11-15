"""Command line: `flask --app app create-admin` makes the first owner account."""
import sqlite3

import click

from . import auth


@click.command("create-admin")
@click.option("--name", prompt="Full name")
@click.option("--email", prompt="Email")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@click.option("--role", type=click.Choice(list(auth.ROLES)), default="owner", show_default=True)
def create_admin(name, email, password, role):
    """Create an admin account."""
    problem = auth.password_problem(password)
    if problem:
        raise click.ClickException(problem)
    try:
        auth.create_user(name.strip(), email, password, role)
    except sqlite3.IntegrityError:
        raise click.ClickException(f"An account for {email} already exists.")
    click.echo(f"Created {role} account for {email}. Sign in at /admin")


def init_app(app):
    app.cli.add_command(create_admin)
