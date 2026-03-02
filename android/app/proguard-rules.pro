# ONNX Runtime Proguard Rules
-keep class ai.onnxruntime.** { *; }
-keep interface ai.onnxruntime.** { *; }

# Keep standard Android/Java classes that might be needed by JNI
-keepclassmembers class * {
    @ai.onnxruntime.* <methods>;
}

# General Compose/Kotlin rules (usually handled by default but good to have)
-keep class androidx.compose.ui.platform.** { *; }

# Protobuf - prevent R8 from stripping generated proto classes
-keep class com.google.protobuf.** { *; }
-keep class * extends com.google.protobuf.GeneratedMessageLite { *; }
-keep class * extends com.google.protobuf.GeneratedMessage { *; }

# App proto models
-keep class com.draftnexus.ai.core.model.proto.** { *; }
