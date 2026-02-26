package com.draftnexus.ai.core.domain

import com.draftnexus.ai.core.data.repository.HeroRepository
import com.draftnexus.ai.core.model.Hero
import javax.inject.Inject

import kotlinx.coroutines.flow.Flow

class GetHeroesUseCase @Inject constructor(
    private val heroRepository: HeroRepository
) {
    operator fun invoke(): Flow<List<Hero>> {
        return heroRepository.getHeroes()
    }
}
