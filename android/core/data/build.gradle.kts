plugins {
    id("com.draftnexus.ai.android.library")
    id("com.draftnexus.ai.android.hilt")
}

android {
    namespace = "com.draftnexus.ai.core.data"
}

dependencies {
    implementation(project(":core:model"))
    
    // Coroutines
    implementation(libs.kotlinx.coroutines.android)
    
    // ONNX Runtime
    implementation(libs.onnxruntime.android)
    
    implementation(libs.androidx.core.ktx)
}
