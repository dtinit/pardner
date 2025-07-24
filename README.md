# pardner

Python library for authorizing access and fetching personal data from portability APIs and services

## Using `pardner`

### With classes

In `services/` you'll find classes defined for different services that are supported by the library (e.g., Tumblr). You can make an instance of that class and use that same object for getting initial authorization from a user and for making data transfer requests.

### Stateless mode

In `stateless/` there are modules that expose functions grouped by service that allow you to complete the same tasks as in the classes described above. Unlike using pardner with the classes we provide, however, you supply the necessary data each time you make a request for each request.

## Developer set-up

> **tl;dr**:
>
> - [install `uv`](https://docs.astral.sh/uv/getting-started/installation/).
> - add [`uv run`](https://docs.astral.sh/uv/reference/cli/#uv-run) to beginning of a command to run it with dependencies and in a virtual environment.
> - `uv run pytest tests` to run tests.
> - [`uv add`](https://docs.astral.sh/uv/reference/cli/#uv-add)/[`uv remove`](https://docs.astral.sh/uv/reference/cli/#uv-remove) to install or uninstall packages.
> - `uv run ruff check --config=pyproject.toml` to run the linter.
> - `uv run mypy . --config-file=pyproject.toml` to run the type checker.
> - [`uv build`](https://docs.astral.sh/uv/reference/cli/#uv-build) to build package.

Package and project management is done using [`uv`](https://docs.astral.sh/uv/) ([install here](https://docs.astral.sh/uv/getting-started/installation/)).

Rather than managing your virtual environment and dependencies yourself, `uv` does that for you.
When you're running a command related to the project, you can usually just prepend it with `uv run` to run it within a virtual environment that will automatically install all necessary dependencies.
To build the project, for example, you can run [`uv build`](https://docs.astral.sh/uv/reference/cli/#uv-build) (or `uv run build`) and to run tests you can run `uv run pytest tests`.

Rather than using `requirements.txt` to manage dependencies, `uv` uses its own `uv.lock` file.
Every time you add a new dependency ([`uv add`](https://docs.astral.sh/uv/reference/cli/#uv-add)), it'll automatically update `pyproject.toml` and `uv.lock`.
Unfortunately, `uv.lock` is specific to `uv` (there are still some features the tool provides that can't be stored in `pylock.toml` at the moment).
But [`pylock.toml` (the new standard for listing dependencies)](https://peps.python.org/pep-0751/) isn't and can be used by most package managers available.
We don't store both in this project to prevent them from getting out of sync.
If you need a different lockfile format, you can use [`uv export`](https://docs.astral.sh/uv/reference/cli/#uv-export) to generate it.
