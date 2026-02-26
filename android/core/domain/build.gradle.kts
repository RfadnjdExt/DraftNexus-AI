plugins {
    id("com.draftnexus.ai.android.library")
    id("com.draftnexus.ai.android.hilt")
}

android {
    namespace = "com.draftnexus.ai.core.domain"
}

dependencies {
    implementation(project(":core:model"))
    implementation(project(":core:data"))
}
