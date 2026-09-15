#!/usr/bin/env bash

echo
echo "=========================================="
echo " AI PLATFORM - PHASE 2M STATUS"
echo "=========================================="

echo
echo "NODES"
kubectl get nodes

echo
echo "AI PLATFORM PODS"
kubectl get pods \
  -n ai-platform \
  -o wide

echo
echo "AI PLATFORM SERVICES"
kubectl get svc \
  -n ai-platform

echo
echo "AI PLATFORM DEPLOYMENTS"
kubectl get deployments \
  -n ai-platform

echo
echo "KEYCLOAK"
kubectl get pods,svc \
  -n security

echo
echo "CONFIGMAP"
kubectl get configmap \
  ai-platform-api-config \
  -n ai-platform \
  -o yaml

echo
echo "PORTS"
echo "8080   -> Argo CD"
echo "18080  -> Keycloak"
echo "8001   -> Local FastAPI"
echo "18081  -> Kubernetes FastAPI"
