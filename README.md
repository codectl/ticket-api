# Ticket Service

A service for managing emails coming in/out from/to a O365 mailbox and integrates them with Jira.

## Install

Because installing an application is always the first step, lets jump right into the different way on achieving it. This
project can be installed in several ways, depending on what the target platform is.

### Python

If the project is meant to run as a ```python``` project, the recommended way of going about it is setting up a virtual
environment with ```virtualenv``` or ```anaconda```.

Using ```conda``` as an example, the sequence of instructions would look like this:

```bash
conda create ticket-service/ python=3.8
conda activate ticket-service/
pip install -r requirements.txt
```

### Kubernetes

The ```kubernetes``` resource manifests that describe the different components of the project are also included. These
files are found under ```.kustomization/```. A quick installation can be done this way:

```bash
ENV=dev  # change to prd (production), if applicable
cd .kustomization/
kubectl -k apply overlays/${ENV}/
```

And it's as simple as that! All the services should now be up and running.

For more information on this, check [README.md](.kustomization/README.md) under ```.kustomization/``` directory.

## How does it work?

This service is suitable for anyone looking to create Jira tickets from the emails arriving to a mailbox. The motivation
behind the creation of this project is that, on one hand, Jira provides good tools to track and manage tickets,
and ```O365``` mailbox is a convenient way to receive requests in the form of an email. This solution comes to merge the
best of both worlds by allowing one to create a Jira ticket directly from a ```O365``` email. Once a new email arrives
to a mailbox, the service picks up the message from the inbox folder, and contacts the Jira API for the creation of the
ticket.

The service provides different configuration properties so that it can best fit the user's needs.

### Configuration

An ```.env``` file should contain the relevant configuration settings. As mentioned, these should be set accordingly for
a correct service usage.

A possible configuration is:

    # Database
    SQLALCHEMY_DATABASE_URI=sqlite:///example.db

    # Application context
    APPLICATION_CONTEXT=/api/tickets/v3
    
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

### O365 auth

Because the service relies on ```O365``` services, one should start off by requesting permissions against the ```O365```
service:

```bash
$ flask o365 authenticate
> ... INFO in o365: Account not yet authenticated.
> Visit the following url to give consent:
> https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/authorize?response_type=code&...
> Paste the authenticated url here:
> ...
```

As seen above, the ```O365``` user must provide proper consent for this service to perform certain actions (see scopes)
on behalf of the user, as per defined in OAuth2 authorization flow. For the use case previously mentioned, the service
would require access to the ```O365``` user's inbox to read its content.

The best way to go about it is simply to open the link in a browser and accept the requested consents. The ```O365```
will redirect to a link containing the so desired authorization code. Simply paste that response link back to the
terminal, and it's done.

A new file ```o365_token.txt``` will be created which contains all the important OAuth2 parameters such as
the ```access_token``` and ```refresh_token```. The ```refresh_token``` has a duration of 90 days after which it
expires, so one must repeat the process just described to request new access codes.

### Running it !

To start listening for incoming events (aka emails), it would go like this:

```bash
$ flask o365 handle-incoming-email
> ... INFO in o365: Account already authenticated.
> ... INFO in o365_mailbox: Start streaming connection for 'users/me@example.com' ...
> ... INFO in base: Open new events channel ...
> ...
```

A new streaming connection is then initiated between our service and the ```O365``` notification service. From this
moment on, as soon as a new email reaches the inbox folder, a Jira API request is performed, and a new ticket is
created.

A thorough explanation on how the notification streaming mechanism works, can be
found [here](https://github.com/rena2damas/o365-notifications).

## Ticket API service

This project also comprises a ```Flask``` RESTful web server where a user can query to create, update and manage
tickets. Each endpoint is properly documented under [OpenAPI 3 standard](https://swagger.io/specification/) which makes
easy for humans and third party services to understand and talk to.

To start the development server, run:

```bash
flask run
```

If default options are set, an HTTP server is listening at [http://localhost:5000/](http://localhost:5000/). To modify
the ```Flask``` server properties, one should set them in ```.flaskenv``` file.

At this point, a Swagger UI instance is running - in which the user can interact with -
at [http://localhost:5000/api/tickets/v1/](http://localhost:5000/api/tickets/v1/).

### Under the hood

This project takes advantage of several python packages that leverage the service implementation. The core packages are:

* [Flask](https://pypi.org/project/Flask/): famous application web framework based on ```werkzeug``` WSGI
* [Flask-RESTful](https://pypi.org/project/Flask-RESTful/): serve RESTful endpoints in ```Flask```
* [Flasgger](https://pypi.org/project/flasgger/): generate OpenAPI specs from ```Flask``` views
* [Flask-SQLAlchemy](https://pypi.org/project/Flask-SQLAlchemy/): enable ```SQLAlchemy``` support for ```Flask```
* [marshmallow](https://pypi.org/project/marshmallow/): for data API serialization
* [jira](https://pypi.org/project/jira/): _pythonic_ implementation for Jira REST API
* [O365](https://pypi.org/project/jira/): _pythonic_ implementation for Microsoft Graph & Office 365 REST API
* [O365-notifications](https://github.com/rena2damas/o365-notifications): _pythonic_ implementation for notification
  connections for Microsoft Graph & Office 365 REST API

## Additional info

### Available commands

It is possible to check the list of available supported operations by:

```bash
$ flask
> ...
```

As any ```Flask``` application, the ```run``` and ```shell``` operations are present. It is also present a set of
commands to manage ```O365``` related operations:

```bash
$ flask o365
...
> authenticate               Set code used for OAuth2 authentication.
> check-for-missing-tickets  Check for possible tickets that went missing...
> handle-incoming-email      Handle incoming email.
```

Each command contains its own instructions and properties that are possible to specify. Enable ```--help``` flag to get
for more information on a command. Take the example below:

```bash
$ flask o365 check-for-missing-tickets --help
> Usage: flask o365 check-for-missing-tickets [OPTIONS]
>
>   Check for possible tickets that went missing in the last days.
>
> Options:
>   -d, --days TEXT  number of days to search back
>   --help           Show this message and exit.
```

### Local development

For local development, one will be running the service on ```localhost```. Therefore, it is recommended to set up a
```python``` environment, as mentioned [here](#Python).

Past that, cli commands are then ready to use.

### Dependencies

It is possible that some dependencies require changes to the source code. Oftentimes, new package releases contain bugs
that might break the code, and so a local patch must be rolled out. To do so, get the source code package that needs a
fix from the ```PiPy``` repository. It is usually a ```tar.gz``` file.

Extract the code:

```bash
tar -xvf package.tar.gz
```

... apply the code changes and recreate the package:

```bash
python setup.py sdist bdist_wheel
```

Add the file entry to the ```requirements.txt```.

## Requirements

See [requirements](requirements.txt)

## License

[GPLv3](LICENSE) license
