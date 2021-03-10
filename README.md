# Ticket Manager

A service for managing emails coming in/out from/to a mailbox and 
integrates them with Jira.

## Configuration

File ```.env``` contains the relevant configuration settings.

## Dependencies

Some dependencies require changes to the source code.
To do so, get the source package from the PiPy repository.
It is usually a ```tar.gz``` file.

Then, extract the code:

```bash
tar -xvf package.tar.gz
```

Apply the code changes and create the package:

```bash
python setup.py sdist bdist_wheel
```

Add the entry to the ```requirements.txt```.

## Commands

The project provides a set of commands to be performed.
To see the whole list of possible operations, run:

```bash
python main.py
```

Available options are:
* listen_for_incoming_email: start listening for incoming email.

### O365 Authentication

File ```o365_token.txt``` contains the authentication parameters to be
exchanged with Microsoft authentication server. The ```access_token```
is the token used in OAuth. It expires after 90 days and why it will
have to be refreshed manually. Simply follow the instructions shown in
the terminal when that happens.
