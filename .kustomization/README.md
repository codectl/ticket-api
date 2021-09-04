# Kustomization

This directory contains the ```kubernetes``` resource manifests that provide a description on the different components
for this project. To do so, it resorts to ```kustomize```, a tool that allows the management of ```kubernetes```
resource objects using ```kustomization.yaml``` files.

More information on that is found in ```kubernetes```
documentation, [here](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/)

## Directory structure

In the root location, 3 directories are found:

* base: ```kubernetes``` resources that serve as a base for other components
* components: ```kubernetes``` components that are put together by each overlay
* overlays: high level object that represent an environment and defines a combination of bases and components

## Secret management

The need to have the repository under version control has led to the challenge of having storing sensitive information
in the remote repository, in this case, ```kubernetes``` secrets. This is where ```bitnami-labs/sealed-secrets``` comes
in, a tool that encrypts secrets so that one can safely store this information remotely. For instructions on how to
install & use, visit its documentation [here](https://github.com/bitnami-labs/sealed-secrets)
.

The idea is then converting regular ```kubernetes``` secrets into sealed secrets. Regular secrets are hidden files,
like ```.secrets.yaml``` and, in **no** circumstance, should they be committed to git repository. A rule
in ```.gitignore``` should prevent it from happening and is present for that reason. Sealed secrets are not hidden
files, like ```sealed.yaml``` and are safe to store in the repository.

Since ```kustomize``` is managing all the different project resources - secrets included -, a combination
of ```kustomize``` and ```kubeseal``` is needed for this process.

Starting off by running the command below:

```bash
$ kustomize build .kustomization/overlays/dev/secrets/
```

This produces a compilation of all the secrets needed in the project, and which need to be sealed individually, if there
are more than a single one. Unfortunately there is no better way to go about this than to execute the following:

```bash
(
ENV="dev"
basedir="$(pwd)/.kustomization"
cd "${basedir}/overlays/${ENV}/"
kustomize build secrets/ | yq e 'select(.metadata.name=="'ticket-service'")' | kubeseal > secrets/sealed/base.yaml 
kustomize build secrets/ | yq e 'select(.metadata.name=="'ticket-service-postgres'")' | kubeseal > secrets/sealed/postgres.yaml 
)
```

As a result, all the secrets are now sealed under ```secrets/sealed/```, and they can now safely be shared and stored
with no risk of compromising sensitive information.

## Usage

Most systems define a production and development environment. Because each may have specific configurations, an overlay
exists representing each environment: ```prd``` for production and ```dev``` for development.

Based on the target environment, one should use the right overlay.

For instance, to have a development environment running for this service, it would be achieved this way:

```bash
$ kubctl apply -k .kustomization/overlays/dev/
```

Note: it is required to seal the secrets first, as mentioned in [this](#Secret-management) section, before applying
this.

At this point, all the pods should be running (or about to). An example output with default settings:

```bash
$ kubctl get pods
NAME                        READY   STATUS      RESTARTS    ...
ticket-api-XXX-XXX          1/1     Running     0           ...
ticket-api-XXX-XXX          1/1     Running     0           ...
ticket-bridge               1/1     Running     0           ...
```
