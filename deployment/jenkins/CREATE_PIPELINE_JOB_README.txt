CREATE JENKINS PIPELINE JOB BY SCRIPT
=====================================

This script creates or updates the Jenkins pipeline job without using the Jenkins UI.

Script:

deployment\jenkins\create-pipeline-job.ps1


WHAT IT DOES
============

It creates or updates a Jenkins Pipeline job with:

- job name:
  makan-society-deploy
- git repo:
  https://github.com/pulok529/Makan_Society_ReactPython.git
- branch:
  */main
- script path:
  Jenkinsfile
- Poll SCM:
  H/2 * * * *


REQUIREMENTS
============

1. Jenkins must already be running
2. You need a Jenkins user
3. You need that user's API token
4. Required Jenkins plugins should already exist:
   - Pipeline
   - Git


HOW TO GET API TOKEN
====================

In Jenkins:

1. Click your user name
2. Click Configure or Security
3. Open API Token section
4. Generate token
5. Copy token


EXAMPLE COMMAND
===============

Run from repo root:

powershell -ExecutionPolicy Bypass -File .\deployment\jenkins\create-pipeline-job.ps1 `
  -JenkinsUrl "http://localhost:8080" `
  -Username "admin" `
  -ApiToken "PASTE_YOUR_TOKEN_HERE" `
  -TriggerBuild


IF YOU DO NOT WANT POLL SCM
===========================

powershell -ExecutionPolicy Bypass -File .\deployment\jenkins\create-pipeline-job.ps1 `
  -JenkinsUrl "http://localhost:8080" `
  -Username "admin" `
  -ApiToken "PASTE_YOUR_TOKEN_HERE" `
  -DisablePollScm


CUSTOM JOB NAME EXAMPLE
=======================

powershell -ExecutionPolicy Bypass -File .\deployment\jenkins\create-pipeline-job.ps1 `
  -JenkinsUrl "http://localhost:8080" `
  -Username "admin" `
  -ApiToken "PASTE_YOUR_TOKEN_HERE" `
  -JobName "makan-society-deploy"


IMPORTANT
=========

This script only creates the Jenkins job.

Your Jenkins container/server must still already have:

- Docker access
- correct docker.sock permission
- deploy env file for pipeline:
  /var/jenkins_home/deploy-config/makan-society.env

If Jenkins cannot access Docker, job creation will work but build will still fail during deploy.
