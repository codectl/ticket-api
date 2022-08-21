**********
ticket-api
**********

.. image:: https://github.com/rena2damas/ticket-api/actions/workflows/ci.yaml/badge.svg
    :target: https://github.com/rena2damas/ticket-api/actions/workflows/ci.yaml
    :alt: CI
.. image:: https://codecov.io/gh/rena2damas/ticket-api/branch/master/graph/badge.svg
    :target: https://app.codecov.io/gh/rena2damas/ticket-api/branch/master
    :alt: codecov
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: code style: black
.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT
    :alt: license: MIT

A service for managing emails coming in/out from/to a *O365* mailbox and integrates
them with *Jira*.

This service is suitable for anyone looking to create *Jira* tickets from the emails
arriving to a mailbox. The motivation behind the creation of this project is that, on
one hand, *Jira* provides good tools to track and manage tickets, and *O365* mailbox is
a convenient way to receive requests in the form of an email. This solution comes to
merge the best of both worlds by allowing one to create a *Jira* ticket directly from
a *O365* email. Once a new email arrives to a mailbox, the service picks up the message
from the inbox folder, and contacts the *Jira* API for the creation of the ticket.

Setup 🔧
=====
The application can run in several ways, depending on what the target platform is.
One can run it directly on the system with ``python`` or get it running on a
``kubernetes`` cluster.

Python
------
The project uses `poetry <https://python-poetry.org/>`__ for dependency management
. Therefore to set up the project (recommended):

.. code-block:: bash

    # ensure poetry is installed
    $ poetry env use python3
    $ poetry install

That will configure a virtual environment for the project and install the respective
dependencies, which is particular useful during development stage.

Kubernetes
----------
Refer to `README <.kustomization/README.rst>`__ under ``.kustomization/``.

Configuration 📄
-------------
Since the project can read properties from the environment, one can use an ``.env``
file for application configurations. These should be set accordingly for a correct
service usage.

A possible configuration is:

.. code-block:: bash

    # database
    SQLALCHEMY_DATABASE_URI=sqlite:///example.db

    # application context
    APPLICATION_CONTEXT=/api/tickets/v1

    # version of OpenAPI
    OPENAPI=3.0.3

    # the application providing info about the ticket
    TICKET_CLIENT_APP=https://example.com/

    # the mailbox to manage
    MAILBOX=mailbox@example.com

    # O365 registered tenant
    O365_TENANT_ID=...

    # O365 client credentials
    O365_CLIENT_ID=...
    O365_CLIENT_SECRET=...

    # O365 scopes (optional)
    O365_SCOPES=...

    # Atlassian credentials
    ATLASSIAN_URL=https://atlassian.net
    ATLASSIAN_USER=me@example.com
    ATLASSIAN_API_TOKEN=...

    # Jira settings
    JIRA_TICKET_TYPE=Task
    JIRA_TICKET_LABELS=ticket
    JIRA_TICKET_LABEL_CATEGORIES=general,bug
    JIRA_TICKET_LABEL_DEFAULT_CATEGORY=general

    # Jira supported boards
    JIRA_SUPPORT_BOARD=support
    JIRA_BOARDS=JIRA_SUPPORT_BOARD
    JIRA_DEFAULT_BOARD=JIRA_SUPPORT_BOARD

    # filter settings
    EMAIL_WHITELISTED_DOMAINS=example.com
    EMAIL_BLACKLIST=malicious@example.com

Note ⚠️: one should use ``configmap`` and ``secret`` instead when configuring it for
``kubernetes``.

O365 Auth
^^^^^^^^^
Because the service relies on *O365* services, the access is done through *oauth2*
protocol. The services runs best with the "client credentials" flow, which in that
case one simply sets the environment variables ``O365_CLIENT_ID`` and
``O365_CLIENT_SECRET``. To generate an *access token*, run the following:

.. code-block:: bash

    $ flask O365 authorize

At this point, a new *access token* is issued and stored in the default backend
provider, which is the SQL table ``access_tokens``. For each token, a *refresh token*
is also issued with an expiration date of 90 days, at which point one must issue a
new one.

Alternatively, and less recommended, the "authorization code" flow can be used. See
file ``src/cli/o365/cli.py`` and apply changes mentioned there. Then run the same
instruction:

    $ flask O365 authorize
    > ... INFO in O365: Authorizing account ...
    > Visit the following url to give consent:
    > https://.../oauth2/v2.0/authorize?response_type=code&...
    > Paste the authenticated url here:
    > ...

In this flow, the *O365* user must provide proper consent for this service to
perform certain actions (see scopes) on behalf of the user, as per defined in *OAuth2*
authorization flow. For instance, the service requires access to the *O365* user's
inbox to read its content, and therefore user must consent those permissions.

The best way to go about it is simply to open the link in a browser and accept the
requested consents. The *O365* will redirect to a link containing the *authorization
code*. Simply paste that response link back to the terminal, and the service handles
the rest.

Run 🚀
====
To start listening for incoming events (aka emails), it would go like this:

.. code-block:: bash

    $ flask O365 handle-incoming-email
    > ... INFO in O365: Account already authorized.
    > ... INFO in O365_mailbox: Start streaming connection for 'users/me@example.com'...
    > ... INFO in base: Open new events channel ...
    > ...

A new streaming connection is then initiated between our service and the *O365*
notification service. From this moment on, as soon as a new email reaches the inbox
folder, a *Jira* API request is performed, and a new ticket is created.

A thorough explanation on how the notification streaming mechanism works, can be
found `here <https://github.com/rena2damas/O365-notifications>`__.

REST API
--------
This project also comprises a ``Flask`` RESTful web server where a user can query to
create, update and manage tickets. Each endpoint is properly documented under
`OpenAPI 3 standard <https://swagger.io/specification/>`__ which makes easy for
humans and third party services to understand and talk to.

For a quick run with ``Flask``, run it like:

.. code-block:: bash

    $ poetry run flask run

Configure ``flask`` environments with environment variables or in a ``.flaskenv`` file.

``Flask`` uses ``Werkzeug`` which is a ``WSGI`` library intended for development
purposes. Do not use it in production! For a production like environment, one should
use instead a production server, like ``gunicorn``:

.. code-block:: bash

    $ poetry run gunicorn src.app:create_app

Additional information
======================
For those who are more curious, this section adds a some more information on this
project.

Core packages
--------------
This project takes advantage of several python packages that leverage the service
implementation. The core packages are:

* `Flask <https://pypi.org/project/Flask/>`__ : famous application web framework based
  on ``werkzeug`` WSGI
* `Flask-RESTful <https://pypi.org/project/Flask-RESTful/>`__: serve RESTful endpoints
  in ``Flask``
* `Flask-SQLAlchemy <https://pypi.org/project/Flask-SQLAlchemy/>`__: enable
  ``SQLAlchemy`` support for ``Flask``
* `APISpec <https://pypi.org/project/apispec/>`__: the OpenAPI standard
* `marshmallow <https://pypi.org/project/marshmallow/>`__: for API data serialization
* `jira <https://pypi.org/project/jira/>`__: *pythonic* implementation for *Jira* REST
  API
* `O365 <https://pypi.org/project/O365/>`__: *pythonic* implementation for Microsoft
  Graph & Office 365 REST API
* `O365-notifications <https://github.com/rena2damas/O365-notifications>`__:
  *pythonic* implementation for O365 notifications

CLI Commands
------------
The list of available supported operations is given by running the command:

.. code-block:: bash

    $ flask
    > ...

As any ``Flask`` application, the ``run`` and ``shell`` operations are present.
Additionally, a set of commands to manage *O365* are also provided:

.. code-block:: bash

    $ flask o365
    ...
    > authorize                  Grant service authorization to O365 resources.
    > check-for-missing-tickets  Check for possible tickets that went missing ...
    > handle-incoming-email      Handle incoming email.

Each command contains its own instructions and properties. Enable ``--help`` flag to get
for more information on a command. Take the example below:

.. code-block:: bash

    $ flask O365 check-for-missing-tickets --help
    > Usage: flask O365 check-for-missing-tickets [OPTIONS]
    >
    >   Check for possible tickets that went missing in the last days.
    >
    > Options:
    >   -d, --days TEXT  number of days to search back
    >   --help           Show this message and exit.

Tests & linting 🚥
===============
Run tests with ``tox``:

.. code-block:: bash

    # ensure tox is installed
    $ tox

Run linter only:

.. code-block:: bash

    $ tox -e lint

Optionally, run coverage as well with:

.. code-block:: bash

    $ tox -e coverage

License
=======
MIT licensed. See `LICENSE <LICENSE>`__.
