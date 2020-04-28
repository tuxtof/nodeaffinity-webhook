# nodeaffinity-webhook

This project is an example of Kubernetes nodeAffinity enforcement based on the dynamic ValidatingWebhook and MutatingWebhook Ressources.

### Quickstart

```bash
kubectl apply -f webhook-base.yaml
./gen-self-cert.sh
```
put the output CABundle certificate in webhook-configuration.yaml (each REPLACE_CERT_HERE iteration)

```bash
kubectl apply -f webhook-configuration.yaml
```

### Usage

Add a `nodeaffinity` label to your namespace with the following value:
- `isolated` to isolate your pod on specific node
- `enforced` to isolate your node on node not associated to specific namespace

Add a `ns-affinity` label to your node(s) with a namespace name as value if you want to restrict this node(s) for this specific namespace


### Hack

you can build your own container based on the source in the `webhook-server` directory

```bash
docker build -t nodeaffinity-webhook webhook-server
```