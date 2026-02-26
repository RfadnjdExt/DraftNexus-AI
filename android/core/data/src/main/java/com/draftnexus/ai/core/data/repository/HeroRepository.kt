package com.draftnexus.ai.core.data.repository

import com.draftnexus.ai.core.model.Hero
import kotlinx.coroutines.flow.Flow

interface HeroRepository {
    fun getHeroes(): Flow<List<Hero>>
    suspend fun loadResources()
    suspend fun runInference(allies: List<Hero?>, enemies: List<Hero?>, candidates: List<Hero>): Map<String, List<com.draftnexus.ai.core.model.Recommendation>>
}
