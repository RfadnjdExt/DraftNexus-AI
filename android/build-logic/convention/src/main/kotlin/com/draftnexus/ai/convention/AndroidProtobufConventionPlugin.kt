package com.draftnexus.ai.convention

import com.google.protobuf.gradle.ProtobufExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.getByType

class AndroidProtobufConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("com.google.protobuf")
            }

            val libs = extensions.getByType<VersionCatalogsExtension>().named("libs")
            
            // Add necessary runtime dependencies
            dependencies {
                "api"(libs.findLibrary("protobuf.kotlin.lite").get())
            }

            extensions.configure<ProtobufExtension> {
                protoc {
                    artifact = libs.findLibrary("protobuf.protoc").get().get().toString()
                }
                generateProtoTasks {
                    all().forEach { task ->
                        task.builtins {
                            register("java") {
                                option("lite")
                            }
                            register("kotlin") {
                                option("lite")
                            }
                        }
                    }
                }
            }
        }
    }
}
