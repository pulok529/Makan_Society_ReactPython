pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  environment {
    DEPLOY_ROOT = '/var/jenkins_home/deploy/makan-society'
    ENV_SOURCE = '/var/jenkins_home/deploy-config/makan-society.env'
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
        sh '''
          set -eu
          mkdir -p "$(dirname "$DEPLOY_ROOT")"
          rm -rf "$DEPLOY_ROOT"
          mkdir -p "$DEPLOY_ROOT"
          cp -a "$WORKSPACE"/. "$DEPLOY_ROOT"/

          if [ ! -f "$ENV_SOURCE" ]; then
            echo "Deployment env file is missing at $ENV_SOURCE"
            exit 1
          fi

          cp "$ENV_SOURCE" "$DEPLOY_ROOT/.env"
        '''
      }
    }

    stage('Build And Deploy') {
      steps {
        sh '''
          set -eu
          cd "$DEPLOY_ROOT"
          docker compose -f "$COMPOSE_FILE" up -d --build
        '''
      }
    }

    stage('Health Check') {
      steps {
        sh '''
          set -eu
          sleep 10
          cd "$DEPLOY_ROOT"
          docker compose -f "$COMPOSE_FILE" ps
          docker exec society-modern-api python - <<'PY'
import urllib.request
urllib.request.urlopen("http://localhost:8000/docs", timeout=20).read()
PY
          docker exec society-modern-frontend node -e "fetch('http://localhost:5173').then(r=>{if(!r.ok) process.exit(1)}).catch(()=>process.exit(1))"
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
