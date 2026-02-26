package com.draftnexus.ai.feature.draft

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.draftnexus.ai.core.domain.GetHeroesUseCase
import com.draftnexus.ai.core.domain.GetRecommendationsUseCase
import com.draftnexus.ai.core.domain.LoadResourcesUseCase
import com.draftnexus.ai.core.model.DraftState
import com.draftnexus.ai.core.model.Hero
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class DraftViewModel @Inject constructor(
    private val getHeroesUseCase: GetHeroesUseCase,
    private val getRecommendationsUseCase: GetRecommendationsUseCase,
    private val loadResourcesUseCase: LoadResourcesUseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow(DraftState())
    val uiState: StateFlow<DraftState> = _uiState.asStateFlow()

    init {
        observeHeroes()
        loadResources()
    }

    private fun observeHeroes() {
        viewModelScope.launch {
            getHeroesUseCase().collectLatest { heroList ->
                _uiState.value = _uiState.value.copy(
                    heroes = heroList,
                    debugText = "Heroes Loaded: ${heroList.size}"
                )
            }
        }
    }

    private fun loadResources() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            loadResourcesUseCase()
            _uiState.value = _uiState.value.copy(isLoading = false)
        }
    }

    fun selectAlly(index: Int, hero: Hero?) {
        val newList = _uiState.value.allies.toMutableList()
        newList[index] = hero
        _uiState.value = _uiState.value.copy(allies = newList)
        runInference()
    }

    fun selectEnemy(index: Int, hero: Hero?) {
        val newList = _uiState.value.enemies.toMutableList()
        newList[index] = hero
        _uiState.value = _uiState.value.copy(enemies = newList)
        runInference()
    }
    
    fun clearDraft() {
        _uiState.value = _uiState.value.copy(
            allies = List(5) { null },
            enemies = List(5) { null },
            recommendations = emptyMap(),
            debugText = "Draft Cleared"
        )
    }

    private fun runInference() {
        val state = _uiState.value
        viewModelScope.launch {
            val candidates = state.heroes.filter { h -> 
                h !in state.allies && h !in state.enemies && h.inRealLogs
            }

            if (candidates.isEmpty()) {
                _uiState.value = _uiState.value.copy(debugText = "No candidates allowed")
                return@launch
            }

            val result = getRecommendationsUseCase(state.allies, state.enemies, candidates)
            _uiState.value = _uiState.value.copy(
                recommendations = result,
                debugText = "Inference Done."
            )
        }
    }
}
