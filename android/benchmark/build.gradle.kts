plugins {
    id("com.draftnexus.ai.android.test")
    id("com.draftnexus.ai.android.baselineprofile")
}

android {
    namespace = "com.draftnexus.ai.benchmark"

    targetProjectPath = ":app"
    
    experimentalProperties["android.experimental.self-instrumenting"] = true

    testOptions {
        managedDevices {
            localDevices {
                create("pixel6Api31") {
                    device = "Pixel 6"
                    apiLevel = 31
                    systemImageSource = "aosp"
                }
            }
        }
    }
}

dependencies {
    implementation(libs.androidx.benchmark.macro)
    implementation(libs.androidx.test.uiautomator)
    implementation(libs.androidx.test.ext.junit)
}

baselineProfile {
    managedDevices.add("pixel6Api31")
    useConnectedDevices = false
}
