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
The project uses `poetry <https://python-poetry.org/>`_ for dependency management
. Therefore to set up the project (recommended):

.. code-block:: bash

    # ensure poetry is installed
    $ poetry env use python3
    $ poetry install

That will configure a virtual environment for the project and install the respective
dependencies, which is particular useful during development stage.

Kubernetes
----------
Refer to `README <.kustomization/README.rst>`_ under ``.kustomization/``.

Configuration 📄
-------------
Since the project can read properties from the environment, one can use an ``.env``
file for application configurations. These should be set accordingly for a correct
service usage.

A possible configuration is:

.. code-block:: bash

    # Database
    SQLALCHEMY_DATABASE_URI=sqlite:///example.db

    # Application context
    APPLICATION_CONTEXT=/api/tickets/v1

    # version of OpenAPI
    OPENAPI=3.0.3

    # The application providing info about the ticket
    TICKET_CLIENT_APP=https://example.com/

    # The mailbox to manage
    MAILBOX=mailbox@example.com

    # O365 registered tenant
    O365_TENANT_ID=...

    # O365 OAuth2 properties

    # O365 client id & secret for this application
    O365_CLIENT_ID=...
    O365_CLIENT_SECRET=...

    #   * 'offline_access': to be eligible to retrieve a refresh_token.
    #      Otherwise user only has access to resources for a single hour.
    #   * 'message_all': alias for 'mail.readwrite' + 'mail.send'
    #      for own user mailbox actions
    #   * 'message_all_shared': alias for 'mail.read.shared' + 'mail.readwrite.shared'
    #      for shared mailbox actions
    O365_SCOPES=offline_access,message_all,message_all_shared

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

    # Filter settings
    EMAIL_WHITELISTED_DOMAINS=example.com
    EMAIL_BLACKLIST=malicious@example.com

Note ⚠️: one should use ``configmap`` and ``secret`` instead when configuring it for
``kubernetes``.

O365 Auth
^^^^^^^^^
Because the service relies on *O365* services, one should start off by requesting
permissions against the *O365* service:

.. code-block:: bash

    $ flask o365 authenticate
    > ... INFO in o365: Account not yet authenticated.
    > Visit the following url to give consent:
    > https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/authorize?response_type=code&...
    > Paste the authenticated url here:
    > ...

As seen above, the *O365* user must provide proper consent for this service to
perform certain actions (see scopes) on behalf of the user, as per defined in OAuth2
authorization flow. For the use case previously mentioned, the service would require
access to the *O365* user's inbox to read its content.

The best way to go about it is simply to open the link in a browser and accept the
requested consents. The *O365* will redirect to a link containing the so desired
authorization code. Simply paste that response link back to the terminal, and it's done.

A new file ``o365_token.txt`` will be created which contains all the important
*OAuth2* parameters such as the ``access_token`` and ``refresh_token``. The
``refresh_token`` has a duration of 90 days after which it expires, so one must
repeat the process just described to request new access codes.

Run 🚀
====
To start listening for incoming events (aka emails), it would go like this:

.. code-block:: bash

    $ flask o365 handle-incoming-email
    > ... INFO in o365: Account already authenticated.
    > ... INFO in o365_mailbox: Start streaming connection for 'users/me@example.com' ...
    > ... INFO in base: Open new events channel ...
    > ...

A new streaming connection is then initiated between our service and the *O365*
notification service. From this moment on, as soon as a new email reaches the inbox
folder, a *Jira* API request is performed, and a new ticket is created.

A thorough explanation on how the notification streaming mechanism works, can be
found `here <https://github.com/rena2damas/o365-notifications>`_.

REST API
--------
This project also comprises a ``Flask`` RESTful web server where a user can query to create, update and manage
tickets. Each endpoint is properly documented under `OpenAPI 3 standard <https://swagger.io/specification/>`_ which makes
easy for humans and third party services to understand and talk to.

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
This project takes advantage of several python packages that leverage the service implementation. The core packages are:

* `Flask <https://pypi.org/project/Flask/>`_ : famous application web framework based
  on ``werkzeug`` WSGI
* `Flask-RESTful <https://pypi.org/project/Flask-RESTful/>`_: serve RESTful endpoints
  in ``Flask``
* `Flask-SQLAlchemy <https://pypi.org/project/Flask-SQLAlchemy/>`_: enable
* `APISpec <https://pypi.org/project/apispec/>`_: the OpenAPI standard
  ``SQLAlchemy`` support for ``Flask``
* `marshmallow <https://pypi.org/project/marshmallow/>`_: for API data serialization
* `jira <https://pypi.org/project/jira/>`_: *pythonic* implementation for *Jira* REST
  API
* `O365 <https://pypi.org/project/o365/>`_: *pythonic* implementation for Microsoft
  Graph & Office 365 REST API
* `O365-notifications <https://github.com/rena2damas/o365-notifications>`_:
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
    > authenticate               Set code used for OAuth2 authentication.
    > check-for-missing-tickets  Check for possible tickets that went missing...
    > handle-incoming-email      Handle incoming email.

Each command contains its own instructions and properties. Enable ``--help`` flag to get
for more information on a command. Take the example below:

.. code-block:: bash

    $ flask o365 check-for-missing-tickets --help
    > Usage: flask o365 check-for-missing-tickets [OPTIONS]
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
MIT licensed. See `LICENSE <LICENSE>`_.
