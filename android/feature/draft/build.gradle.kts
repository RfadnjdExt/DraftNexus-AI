plugins {
    id("com.draftnexus.ai.android.library")
    id("com.draftnexus.ai.android.hilt")
}

android {
    namespace = "com.draftnexus.ai.feature.draft"
}

dependencies {
    implementation(project(":core:model"))
    implementation(project(":core:domain"))
    api(project(":core:data"))
    
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.ktx)
    implementation(libs.kotlinx.coroutines.android)
}
