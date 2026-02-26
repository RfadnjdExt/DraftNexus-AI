plugins {
    id("com.draftnexus.ai.android.library")
    id("com.draftnexus.ai.android.compose")
}

android {
    namespace = "com.draftnexus.ai.core.ui"
}

dependencies {
    implementation(project(":core:model"))
    
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)
    implementation(libs.coil.compose)
}
