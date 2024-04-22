import typer
from numato_gpio.cli import cmd_gpio, cmd_id, cmd_ver, cmd_discover


app = typer.Typer(no_args_is_help=True)

app.command()(cmd_discover.discover)
app.command()(cmd_ver.ver)

app.add_typer(cmd_id.app, name="id")
app.add_typer(cmd_gpio.app, name="gpio")

if __name__ == "__main__":
    app()
