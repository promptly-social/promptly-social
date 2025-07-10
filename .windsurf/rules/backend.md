---
trigger: model_decision
description: 
globs: backend/**/*,terraform/src/**/*
---
* follow the best practices and conventions in Python 
* always use the latest version of dependencies when possible
* follow the best security and compliance practices, e.g. create audit logs, user session management, least previlige principles, follow SOC-II and GDPR, create appropriate IAM roles and resources, etc.
* follow the best python file structure conventions for a monorepo
* follow object oriented design principles
* when developing AI agents or AI workflow, think of delegating to smaller agents and creating smaller workflow
* AI API calls should be provider agnostic, and try to implement logic that can be reused for other providers
* always writes tests and mock dependencies when necessary
* when you get stuck, try a different approach
* always check and update the dockerfile when unnecessary
* always include database migration when a new model or changes to an existing model is introduced
* always update the requirements.txt file when a new dependency is introduced
* Separation of concerns
* DRY (Don't Repeat Yourself) principles
* Consistent error handling
* Type safety throughout the application
* Update the corresponding tests when you make changes
* The logs should follow SOC-II and GDPR standards