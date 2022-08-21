*************
Kustomization
*************

Refer to the `main <https://github.com/rena2damas/microservices.git#kustomization>`__
repository.

Directory structure
===================
Refer to the
`main <https://github.com/rena2damas/microservices.git#directory-structure>`__
repository.

Secret management
=================
Refer to the `main <https://github.com/rena2damas/microservices
.git#secret-management>`__ repository.

Sealing secrets can be done with one single instruction:

.. code-block:: bash

    $ (
        ENV="dev"
        basedir="$(pwd)/.kustomization"
        cd "${basedir}/overlays/${ENV}/"
        kustomize build secrets/ |
            yq e 'select(.metadata.name=="'ticket-api'")' - |
            kubeseal > secrets/sealed/base.yaml
        kustomize build secrets/ |
            yq e 'select(.metadata.name=="'ticket-api-db'")' - |
            kubeseal > secrets/sealed/db.yaml
    )

Usage
=====
Refer to the `main <https://github.com/rena2damas/microservices.git#usage>`__
repository.

Upon following those steps, the ``pods`` should be running (or about to). An example
output with default settings:

.. code-block:: bash

    $ kubectl get pods
    NAME                       READY   STATUS      RESTARTS    ...
    ticket-api-XXX-XXX         1/1     Running     0           ...
    ticket-api-XXX-XXX         1/1     Running     0           ...
    ticket-bridge              1/1     Running     0           ...
