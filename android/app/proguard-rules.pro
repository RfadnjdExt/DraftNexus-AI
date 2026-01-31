# ONNX Runtime Proguard Rules
-keep class ai.onnxruntime.** { *; }
-keep interface ai.onnxruntime.** { *; }

# Keep standard Android/Java classes that might be needed by JNI
-keepclassmembers class * {
    @ai.onnxruntime.* <methods>;
}

# General Compose/Kotlin rules (usually handled by default but good to have)
-keep class androidx.compose.ui.platform.** { *; }
