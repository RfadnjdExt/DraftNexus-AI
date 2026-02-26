import java.util.Properties
import java.io.FileInputStream

plugins {
    id("com.draftnexus.ai.android.application")
    id("com.draftnexus.ai.android.compose")
    id("com.draftnexus.ai.android.hilt")
    id("com.draftnexus.ai.android.baselineprofile")
}

// Load signing properties from keystore.properties (or local.properties) to avoid checking secrets into VCS
val keystorePropertiesFile = rootProject.file("keystore.properties")
val keystoreProperties = Properties()
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(FileInputStream(keystorePropertiesFile))
}

android {
    namespace = "com.draftnexus.ai"

    defaultConfig {
        applicationId = "com.draftnexus.ai"
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables {
            useSupportLibrary = true
        }
        
        ndk {
            abiFilters.add("arm64-v8a")
        }
    }

    signingConfigs {
        create("release") {
            storeFile = file(keystoreProperties.getProperty("MYAPP_RELEASE_STORE_FILE") ?: "my-release-key.jks")
            storePassword = keystoreProperties.getProperty("MYAPP_RELEASE_STORE_PASSWORD") ?: ""
            keyAlias = keystoreProperties.getProperty("MYAPP_RELEASE_KEY_ALIAS") ?: "my-key-alias"
            keyPassword = keystoreProperties.getProperty("MYAPP_RELEASE_KEY_PASSWORD") ?: ""
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true 
            isShrinkResources = true 
            signingConfig = signingConfigs.getByName("debug")
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    // suppress deprecation warnings from generated Hilt code during Java compilation
    tasks.withType<JavaCompile>().configureEach {
        options.encoding = "UTF-8"
        options.compilerArgs.addAll(listOf("-Xlint:unchecked", "-Xlint:deprecation"))
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
        jniLibs {
            // prevent stripping of ONNX native libs which fail the default stripper
            keepDebugSymbols.add("**/libonnxruntime.so")
            keepDebugSymbols.add("**/libonnxruntime4j_jni.so")
        }
    }
}

dependencies {
    implementation(project(":core:model"))
    implementation(project(":core:data"))
    implementation(project(":core:domain"))
    implementation(project(":core:ui"))
    implementation(project(":feature:draft"))
    baselineProfile(project(":benchmark"))
    
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)
    
    // Image Loading
    implementation(libs.coil.compose)
    
    // Retrofit - Networking
    implementation(libs.retrofit)
    implementation(libs.retrofit.converter.gson)

    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(libs.androidx.ui.test.junit4)
    debugImplementation(libs.androidx.ui.tooling)
    debugImplementation(libs.androidx.ui.test.manifest)
}
