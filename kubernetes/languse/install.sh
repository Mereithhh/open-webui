helm upgrade --install --namespace app langfuse langfuse/langfuse -f values.yaml

helm uninstall --namespace app langfuse