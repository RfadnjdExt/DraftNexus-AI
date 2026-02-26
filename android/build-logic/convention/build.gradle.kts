plugins {
    `kotlin-dsl`
}

group = "com.draftnexus.ai.buildlogic"

java {
    sourceCompatibility = JavaVersion.VERSION_18
    targetCompatibility = JavaVersion.VERSION_18
}

dependencies {
    compileOnly(libs.android.gradlePlugin)
    compileOnly(libs.kotlin.gradlePlugin)
    compileOnly(libs.ksp.gradlePlugin)
    compileOnly(libs.compose.compiler.gradlePlugin)
    compileOnly(libs.baselineprofile.gradlePlugin)
    implementation(libs.protobuf.gradlePlugin)
}

gradlePlugin {
    plugins {
        register("androidApplication") {
            id = "com.draftnexus.ai.android.application"
            implementationClass = "com.draftnexus.ai.convention.AndroidApplicationConventionPlugin"
        }
        register("androidLibrary") {
            id = "com.draftnexus.ai.android.library"
            implementationClass = "com.draftnexus.ai.convention.AndroidLibraryConventionPlugin"
        }
        register("androidHilt") {
            id = "com.draftnexus.ai.android.hilt"
            implementationClass = "com.draftnexus.ai.convention.HiltConventionPlugin"
        }
        register("androidCompose") {
            id = "com.draftnexus.ai.android.compose"
            implementationClass = "com.draftnexus.ai.convention.AndroidComposeConventionPlugin"
        }
        register("androidBaselineProfile") {
            id = "com.draftnexus.ai.android.baselineprofile"
            implementationClass = "com.draftnexus.ai.convention.AndroidBaselineProfileConventionPlugin"
        }
        register("androidTest") {
            id = "com.draftnexus.ai.android.test"
            implementationClass = "com.draftnexus.ai.convention.AndroidTestConventionPlugin"
        }
        register("androidProtobuf") {
            id = "com.draftnexus.ai.android.protobuf"
            implementationClass = "com.draftnexus.ai.convention.AndroidProtobufConventionPlugin"
        }
    }
}
