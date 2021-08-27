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

## Usage

Most systems define a production and development environment. Because each may have specific configurations, an overlay
exists representing each environment: ```prd``` for production and ```dev``` for development.

Based on the target environment, one should use the right overlay.

For instance, to have a development environment running for this service, it would be achieved this way:

```bash
$ kubctl apply -k overlays/env
```

At this point, all the pods should be running (or about to). An example output with default settings:

```bash
$ kubctl get pods
NAME                        READY   STATUS      RESTARTS    ...
ticket-api-XXX-XXX          1/1     Running     0           ...
ticket-api-XXX-XXX          1/1     Running     0           ...
ticket-bridge               1/1     Running     0           ...
```
