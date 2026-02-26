package com.draftnexus.ai.core.model

data class DraftState(
    val heroes: List<Hero> = emptyList(),
    val allies: List<Hero?> = List(5) { null },
    val enemies: List<Hero?> = List(5) { null },
    val bans: List<Hero?> = List(10) { null },
    val recommendations: Map<String, List<Recommendation>> = emptyMap(),
    val isLoading: Boolean = true,
    val debugText: String = ""
)

data class Recommendation(
    val hero: Hero,
    val score: Float,
    val role: String
)
