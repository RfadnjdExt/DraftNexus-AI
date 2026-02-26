package com.draftnexus.ai.core.data.di

import com.draftnexus.ai.core.data.repository.DefaultHeroRepository
import com.draftnexus.ai.core.data.repository.HeroRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class DataModule {

    @Binds
    @Singleton
    abstract fun bindHeroRepository(
        heroRepository: DefaultHeroRepository
    ): HeroRepository
}
