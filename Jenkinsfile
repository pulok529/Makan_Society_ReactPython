pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  environment {
    DEPLOY_DIR = 'C:\\deploy\\makan-society'
    COMPOSE_FILE = 'docker-compose.deploy.yml'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Prepare Deploy Folder') {
      steps {
        powershell '''
          $ErrorActionPreference = "Stop"
          if (!(Test-Path "$env:DEPLOY_DIR")) {
            New-Item -ItemType Directory -Force -Path "$env:DEPLOY_DIR" | Out-Null
          }
          robocopy "$env:WORKSPACE" "$env:DEPLOY_DIR" /MIR /XD ".git" "node_modules" "client-deployment-output" | Out-Null
          if (!(Test-Path "$env:DEPLOY_DIR\\.env")) {
            throw "Deployment .env file is missing at $env:DEPLOY_DIR\\.env"
          }
        '''
      }
    }

    stage('Build And Deploy') {
      steps {
        powershell '''
          $ErrorActionPreference = "Stop"
          Set-Location "$env:DEPLOY_DIR"
          docker compose -f "$env:COMPOSE_FILE" up -d --build
        '''
      }
    }

    stage('Health Check') {
      steps {
        powershell '''
          $ErrorActionPreference = "Stop"
          Start-Sleep -Seconds 10
          $api = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 20
          $web = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 20
          if ($api.StatusCode -ne 200) { throw "API health check failed" }
          if ($web.StatusCode -ne 200) { throw "Frontend health check failed" }
          Set-Location "$env:DEPLOY_DIR"
          docker compose -f "$env:COMPOSE_FILE" ps
        '''
      }
    }
  }

  post {
    success {
      echo 'Deployment completed successfully.'
    }
    failure {
      echo 'Deployment failed. Check build logs and docker compose output.'
    }
  }
}
