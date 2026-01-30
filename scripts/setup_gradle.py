import os
import urllib.request
import zipfile
import shutil

# This script attempts to download a full gradle distribution to get the wrapper files
# or directly downloads wrapper files if we knew a stable URL. 
# Better approach for "no gradle installed": Download the wrapper jar and properties from a repo.

WRAPPER_DIR = "android/gradle/wrapper"
WRAPPER_PROPS = "gradle-wrapper.properties"
WRAPPER_JAR = "gradle-wrapper.jar"
GRADLEW_BAT = "android/gradlew.bat"
GRADLEW_SH = "android/gradlew"

# Official Gradle Wrapper files from a generic template or a known workable source
# We will use a specific compatible version: 8.4
BASE_URL = "https://raw.githubusercontent.com/gradle/gradle/v8.4.0/gradle/wrapper/"
# Note: GitHub raw might not have the JAR binary directly usable or it might be LFS.
# Safest bet: Download a minimal gradle-wrapper.jar from a reliable maven/source.
# Actually, let's try to generate it using a "portable" approach or just write the text files and assume user can install gradle?
# User said "di sini", implies they don't want to install Android Studio. They probably don't have Gradle.

# Let's create the properties file manually.
# Then download the jar from services.gradle.org/distributions if we had to, but that's the whole distro.
# We need gradle-wrapper.jar.
# A common trick: Use the specific URL for the jar.
WRAPPER_JAR_URL = "https://raw.githubusercontent.com/gradle/gradle/v8.4.0/gradle/wrapper/gradle-wrapper.jar"
# Note: Raw git does not serve binary JARs correctly usually if LFS. Gradle repo seems to have it as binary. 
# Let's try downloading it.

def setup_gradle():
    os.makedirs(WRAPPER_DIR, exist_ok=True)
    
    # 1. gradle-wrapper.properties
    props_content = """distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.4-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
"""
    with open(os.path.join(WRAPPER_DIR, WRAPPER_PROPS), 'w') as f:
        f.write(props_content)
        
    # 2. scripts
    # We can write a simple Batch script that calls java -jar gradle-wrapper.jar
    # But we need the jar.
    print(f"Downloading {WRAPPER_JAR}...")
    try:
        # Try to download the JAR. If this fails, we are stuck.
        # Alternative: We can use a python script to act as the build runner if we assume 'gradle' command is missing but 'java' exists.
        # But `gradle` command IS missing. 
        # We need to bootstrap. 
        # Let's try a public URL for the wrapper jar.
        urllib.request.urlretrieve(
            "https://github.com/gradle/gradle/raw/master/gradle/wrapper/gradle-wrapper.jar", 
            os.path.join(WRAPPER_DIR, WRAPPER_JAR)
        )
        print("Wrapper JAR downloaded.")
        
        # 3. gradlew.bat
        # Minimal batch wrapper
        bat_content = """@rem
@echo off
set DIRNAME=%~dp0
if "%DIRNAME%" == "" set DIRNAME=.
set APP_BASE_NAME=%~n0
set APP_HOME=%DIRNAME%
java -jar "%APP_HOME%gradle/wrapper/gradle-wrapper.jar" %*
"""
        with open(GRADLEW_BAT, 'w') as f:
            f.write(bat_content)
            
        print("Gradlew.bat created.")
        
    except Exception as e:
        print(f"Failed to bootstrap gradle: {e}")

if __name__ == "__main__":
    setup_gradle()
