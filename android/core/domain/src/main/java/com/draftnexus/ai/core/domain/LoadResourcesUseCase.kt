package com.draftnexus.ai.core.domain

import com.draftnexus.ai.core.data.repository.HeroRepository
import javax.inject.Inject

class LoadResourcesUseCase @Inject constructor(
    private val heroRepository: HeroRepository
) {
    suspend operator fun invoke() {
        heroRepository.loadResources()
    }
}
