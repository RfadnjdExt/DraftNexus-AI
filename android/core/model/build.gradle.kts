plugins {
    id("com.draftnexus.ai.android.library")
    id("com.draftnexus.ai.android.protobuf")
    alias(libs.plugins.compose.compiler)
}

android {
    namespace = "com.draftnexus.ai.core.model"
}

dependencies {
    api(platform(libs.androidx.compose.bom))
    api(libs.androidx.compose.runtime)
}
