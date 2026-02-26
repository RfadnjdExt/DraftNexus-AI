package com.draftnexus.ai.core.domain

import com.draftnexus.ai.core.data.repository.HeroRepository
import com.draftnexus.ai.core.model.Hero
import com.draftnexus.ai.core.model.Recommendation
import javax.inject.Inject

class GetRecommendationsUseCase @Inject constructor(
    private val heroRepository: HeroRepository
) {
    suspend operator fun invoke(
        allies: List<Hero?>,
        enemies: List<Hero?>,
        candidates: List<Hero>
    ): Map<String, List<Recommendation>> {
        return heroRepository.runInference(allies, enemies, candidates)
    }
}
