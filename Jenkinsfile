pipeline {
    agent any

    environment {
        SONAR_PROJECT_KEY = 'mspr-data-etl'
        PYTHON_VERSION    = '3.10'
        IMAGE_NAME        = 'mspr/data-etl'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install flake8
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '''
                    . .venv/bin/activate
                    flake8 . \
                        --exclude=.venv \
                        --max-line-length=120 \
                        --count \
                        --statistics || true
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    script {
                        def scannerHome = tool 'SonarQube Scanner'
                        sh """
                            ${scannerHome}/bin/sonar-scanner \
                                -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                                -Dsonar.sources=. \
                                -Dsonar.inclusions="**/*.py" \
                                -Dsonar.exclusions="**/.venv/**" \
                                -Dsonar.python.version=${PYTHON_VERSION}
                        """
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} -t ${IMAGE_NAME}:latest ."
            }
        }
    }

    post {
        success {
            echo "Pipeline data-etl : SUCCESS (build #${BUILD_NUMBER})"
        }
        failure {
            echo "Pipeline data-etl : FAILURE (build #${BUILD_NUMBER})"
        }
        always {
            cleanWs()
        }
    }
}
