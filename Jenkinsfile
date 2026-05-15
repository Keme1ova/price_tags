node('master') {
    try {
        def appName = "price_tags"
        def addVersion = "main"

        stage('Checkout') {
            println("Checkout $appName-$addVersion")
            checkout scm
        }
        stage ('Start service') {
            sh "chown -R 777 /var/lib/jenkins/workspace/Front_Price_main/"
            sh "pip install -r requirements.txt"
            sh "python3 app.py"
        }
    } catch (Exception e) {
        currentBuild.result = "FAILURE"
        println "FAILURE $e"
        //commonNotifyAboutBuildStatus(status: currentBuild.result, exception: e)
        throw e
    } finally {
        println("finally action")
    }
}