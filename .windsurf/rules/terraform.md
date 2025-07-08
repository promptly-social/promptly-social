---
trigger: model_decision
description: 
globs: **/terraform/**,.github/**
---
* Always follow the best secruity practice in creating cloud resources
* Always support multi-environment deployment
* Always follow the least priviledge rule
* Only provide the IAM roles and permissions that are necesary
* Store the terraform states in GCP storage bucket
* If some resources already exist, import it into the terraform state