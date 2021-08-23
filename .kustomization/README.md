# Ticket service

Kubernetes configuration files for the ticket manager service. Full details on this service can be
found [here](https://github.com/rena2damas/ticket-manager).

## Install

Run the following instructions in the same order to have it installed:

```bash
$ cd kubernetes/services/ticket
$ kubectl apply -f sa.yaml
$ kubectl apply -f rbac.yaml
$ kubectl apply -f secrets.yaml
$ kubectl apply -f configmap.yaml
$ kubectl apply -f api.deployment.yaml
$ kubectl apply -f api.svc.yaml
$ kubectl apply -f api.ingress.yaml
$ kubectl apply -f bridge.pod.yaml
```

## Access

A web server application should now be running on ```http://<domain>/api/tickets```.

## License

[GPLv3](LICENSE) license
