import java.util.Properties

// Auto-detect Android SDK if not configured
val localPropertiesFile = File(rootDir, "local.properties")
val hasSdkDir = if (localPropertiesFile.exists()) {
    val properties = java.util.Properties()
    localPropertiesFile.inputStream().use { properties.load(it) }
    properties.containsKey("sdk.dir")
} else false

if (System.getenv("ANDROID_HOME") == null && !hasSdkDir) {
    val osName = System.getProperty("os.name").lowercase()
    val userHome = System.getProperty("user.home")
    val sdkPath = when {
        osName.contains("mac") -> "$userHome/Library/Android/sdk"
        osName.contains("windows") -> "${System.getenv("LOCALAPPDATA")}\\Android\\Sdk"
        else -> "$userHome/Android/Sdk"
    }
    
    val sdkDir = File(sdkPath)
    if (sdkDir.exists()) {
        println("Auto-detected Android SDK at: $sdkPath")
        localPropertiesFile.appendText("sdk.dir=${sdkDir.absolutePath.replace("\\", "\\\\")}\n")
    } else {
        println("Warning: Could not auto-detect Android SDK. Please create local.properties manually or set ANDROID_HOME.")
    }
}

pluginManagement {
    includeBuild("build-logic")
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "DraftNexus-AI"
include(":app")
include(":core:model")
include(":core:data")
include(":core:domain")
include(":core:ui")
include(":feature:draft")
include(":benchmark")
