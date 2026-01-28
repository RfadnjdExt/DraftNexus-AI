# Android On-Device Architecture (DraftNexus AI)

## Overview
This document outlines the architecture for porting DraftNexus AI to Native Android using **Kotlin** and **Jetpack Compose**. The core requirement is **On-Device ML** (no backend dependency) using the ONNX Runtime.

## Tech Stack
*   **Language**: Kotlin (100%)
*   **UI Toolkit**: Jetpack Compose (Material 3)
*   **ML Runtime**: `com.microsoft.onnxruntime:onnxruntime-android`
*   **Data Integration**: Room Database (SQLite) or JSON Assets
*   **Architecture**: MVVM + Clean Architecture

## 1. Data Layer
The Python app relies on `hero_base_stats.csv`. On Android, we will package this as a pre-populated Room Database or a raw JSON asset.

### Hero Entity (Room Table)
```kotlin
@Entity(tableName = "heroes")
data class Hero(
    @PrimaryKey val id: Int, // Hero_ID
    val name: String,
    val primaryLane: Int,
    val secondaryLane: Int,
    val iconUrl: String,
    // ... other stats (damage type, etc.)
    val earlyPower: Double,
    val midPower: Double,
    val latePower: Double
)
```

## 2. ML Pipeline (The Hard Part)
We need to replicate the Python feature engineering logic in Kotlin to generate the input tensor for the ONNX model.

### Input Tensor Shape
*   **Size**: `[1, 277]` (Float32)
*   **Structure**: 
    1.  **Ally One-Hot** (Size: N_Heroes)
    2.  **Enemy One-Hot** (Size: N_Heroes)
    3.  **Roles Vector** (Size: 5) - `[Exp, Mid, Roam, Jungle, Gold]`
    4.  **Candidate Stats** (Size: 10) - `[Primary_Lane, DmgType, CC, FlexScore, ...]`

### Feature Engineering in Kotlin
```kotlin
fun buildFeatureVector(
    allies: List<Hero>, 
    enemies: List<Hero>, 
    candidate: Hero
): FloatArray {
    val totalHeroes = 131 // Must match training N_Heroes
    val vector = FloatArray(277)
    
    // 1. Ally One-Hot
    allies.forEach { vector[it.id] = 1f }
    
    // 2. Enemy One-Hot (Offset by N_Heroes)
    enemies.forEach { vector[totalHeroes + it.id] = 1f }
    
    // 3. Roles Context (Offset by 2*N_Heroes)
    // Need a simple role predictor logic here
    val rolesOffset = 2 * totalHeroes
    val predictedRoles = predictRoles(allies) 
    predictedRoles.forEach { role -> 
        vector[rolesOffset + role.index] += 1f 
    }
    
    // 4. Candidate Stats (Offset by 2*N_Heroes + 5)
    val statsOffset = rolesOffset + 5
    vector[statsOffset + 0] = candidate.primaryLane.toFloat()
    vector[statsOffset + 1] = candidate.damageType.toFloat()
    // ... fill remaining 8 stats
    
    return vector
}
```

## 3. UI Layer (Jetpack Compose)
Modern, declarative UI similar to YouTube Android.

### Components
*   **DraftScreen**: Main scaffold with specific slots for Allies and Enemies.
*   **HeroSelectorConfig / BottomSheet**: A grid of hero icons to pick from.
*   **RecommendationRail**: Horizontal scrolling list (LazyRow) showing top recommendations.

### libraries needed
```gradle
dependencies {
    implementation("com.microsoft.onnxruntime:onnxruntime-android:1.15.0")
    implementation("androidx.room:room-runtime:2.6.0")
    implementation("io.coil-kt:coil-compose:2.4.0") // For Icon URLs
}
```

## 4. Migration Steps
1.  **Asset Prep**: 
    *   Convert `hero_base_stats.csv` + `hero_meta_performance.csv` -> `heroes.json`.
    *   Copy `draft_model.onnx` to `app/src/main/assets`.
2.  **Core Logic**: Write the `FeatureExtractor` class in Kotlin.
3.  **UI**: Build simple Draft UI to populate the state.
4.  **Integration**: Feed UI State -> FeatureExtractor -> ONNX Runtime -> UI List.
