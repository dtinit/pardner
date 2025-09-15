# pardner

A Python library for authorizing access and fetching personal data from
portability APIs and services.

## Using pardner

Pardner is a tool for facilitating, streamlining, and standardizing access to
data associated with a user on an online service. You can use it to access your
own data, to create applications for others to access their data, or to collect
other people's data (of course, following the terms of use of the services from
which you're fetching data).

For a prototype of how an application could use pardner, check out
[pardner-site](https://github.com/dtinit/pardner-site). It's a web-app for
collecting personal data for academic research studies.

### Installation

Install the repository directly from Github. I.e., `pip install` or `uv add`
with `git+ssh://git@github.com/dtinit/pardner.git@main` as the package.

### Requirements

To use pardner with your desired service you must first register an application
or client with that service. If that service uses OAuth 2.0, this will entail
obtaining a client ID and a client secret. If you're not using pardner for
personal use, you'll also need to have a server listening for an authorization
response and register that URL with the service.

<details>
<summary>Note on personal use</summary>

When using pardner for your own data, you don't need to set up a server. You can
manually navigate to the authorization URL in your browser, authorize access,
copy the URL you're redirected to, and pass that into the `fetch_token` method
for your transfer service. </details>

### Quickstart example

```python
from pardner.services import StravaTransferService
from pardner.verticals import PhysicalActivityVertical

# initialize your transfer service
strava_service = StravaTransferService(
    client_id='<YOUR_STRAVA_CLIENT_ID>',
    client_secret='<YOUR_STRAVA_CLIENT_SECRET>',
    redirect_uri='<YOUR_REDIRECT_URI>',
    verticals={PhysicalActivityVertical},
)

# construct your authorization URL and have the target user navigate to it
auth_url = strava_service.authorization_url()

# direct target user to `auth_url`

# target user is redirected to `redirect_uri` passed into the constructor
# with special URL parameters set by the service
response_url = '...obtained from the target user browser...'

# make request to service to get access token using the URL to which
# the user was redirected
strava_service.fetch_token(authorization_response=response_url)

# fetch target user's 10 most recent activities logged on Strava
activities = strava_service.fetch_physical_activity_vertical(count=10)

# calculate average max speed across those activities
speeds: list[float] = [
    activity.max_speed for activity in activities if activity.max_speed
]
avg_speed = sum(speeds) / len(speeds)
```

### Services and verticals supported

The table below shows which verticals are currently supported by each service
(✓), which we have plans to support (👀), and which we cannot support due to
limitations of the service or service's API (left blank in the table). We
indicate service-vertical pairs that support fully defined schemas with an
additional ✓ (as in the [Quickstart example](#quickstart-example) above).

|                    | GroupMe | Strava | Tumblr |
| ------------------ | ------- | ------ | ------ |
| BlockedUser        | ✓✓      |        | 👀     |
| ChatBot            | ✓✓      |        |        |
| ConversationDirect | ✓✓      |        |        |
| ConversationGroup  | ✓✓      |        |        |
| Message            |         |        |        |
| PhysicalActivity   |         | ✓✓     |        |
| SocialPosting      |         | ✓✓     | ✓      |

The transfer services are defined in
[`pardner/services/`](https://github.com/dtinit/pardner/tree/main/src/pardner/services)
and verticals are defined in
[`pardner/verticals/`](https://github.com/dtinit/pardner/tree/main/src/pardner/verticals).

## Developer set-up

**tl;dr**:

> - [install `uv`](https://docs.astral.sh/uv/getting-started/installation/).
> - add [`uv run`](https://docs.astral.sh/uv/reference/cli/#uv-run) to beginning
>   of a command to run it with dependencies and in a virtual environment.
> - `uv run pytest tests` to run tests.
> - [`uv add`](https://docs.astral.sh/uv/reference/cli/#uv-add)/[`uv remove`](https://docs.astral.sh/uv/reference/cli/#uv-remove)
>   to install or uninstall packages.
> - `uv run ruff check --config=pyproject.toml` to run the linter.
> - `uv run mypy . --config-file=pyproject.toml` to run the type checker.
> - [`uv build`](https://docs.astral.sh/uv/reference/cli/#uv-build) to build
>   package.

Package and project management is done using [`uv`](https://docs.astral.sh/uv/)
([install here](https://docs.astral.sh/uv/getting-started/installation/)).

When you're running a command related to the project, you can usually just
prepend it with `uv run` to run it within a virtual environment that will
automatically install all necessary dependencies. To build the project, for
example, you can run
[`uv build`](https://docs.astral.sh/uv/reference/cli/#uv-build) (or
`uv run build`) and to run tests you can run `uv run pytest tests`.

## Glossary

- **Service**: an online platform that provides some sort of service. Can be a
  subservice of a larger company (e.g., Youtube) or the platform itself (e.g.,
  GroupMe).
- **Target user**: the user whose data is being fetched.
- **Vertical**: a category or type of data.

For OAuth 2.0 questions and definitions, see
[The OAuth 2.0 Authorization Framework (RFC6749)](https://datatracker.ietf.org/doc/html/rfc6749)
for a comprehensive definition of each term and a description of the flow from
start to finish.
