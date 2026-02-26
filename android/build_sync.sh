#!/bin/bash
export JAVA_HOME=/usr/local/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home
export PATH="/usr/local/opt/openjdk@17/bin:$PATH"

# Force execution in foreground without daemon
/usr/local/opt/openjdk@17/bin/java -Dorg.gradle.daemon=false -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain assembleRelease --console=plain > build_sync.log 2>&1
