package com.draftnexus.ai

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import ai.onnxruntime.OnnxTensor
import java.nio.FloatBuffer
import java.util.Collections

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

class DraftViewModel(application: Application) : AndroidViewModel(application) {

    private val _uiState = MutableStateFlow(DraftState())
    val uiState: StateFlow<DraftState> = _uiState.asStateFlow()

    private var ortEnv: OrtEnvironment? = null
    private var ortSession: OrtSession? = null

    init {
        loadResources()
    }

    private fun loadResources() {
        viewModelScope.launch(Dispatchers.IO) {
            val context = getApplication<Application>().applicationContext
            try {
                // 1. Load Heroes JSON
                val jsonString = context.assets.open("heroes.json").bufferedReader().use { it.readText() }
                val heroList = parseHeroes(jsonString)
                
                // 2. Load ONNX Model
                ortEnv = OrtEnvironment.getEnvironment()
                val modelBytes = context.assets.open("draft_model.onnx").readBytes()
                ortSession = ortEnv?.createSession(modelBytes)
                
                withContext(Dispatchers.Main) {
                    _uiState.value = _uiState.value.copy(
                        heroes = heroList, 
                        isLoading = false,
                        debugText = "Model Loaded. Heroes: ${heroList.size}"
                    )
                }
            } catch (e: Exception) {
                e.printStackTrace()
                withContext(Dispatchers.Main) {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        debugText = "Error Loading: ${e.message}"
                    )
                }
            }
        }
    }

    private fun parseHeroes(json: String): List<Hero> {
        val list = mutableListOf<Hero>()
        try {
            val array = JSONArray(json)
            for (i in 0 until array.length()) {
                val obj = array.getJSONObject(i)
                val statsJson = obj.getJSONArray("stats")
                val stats = FloatArray(statsJson.length())
                for (j in 0 until statsJson.length()) {
                    stats[j] = statsJson.getDouble(j).toFloat()
                }
                
                list.add(Hero(
                    id = obj.getInt("id"),
                    name = obj.getString("name"),
                    primaryLane = obj.getInt("primaryLane"),
                    secondaryLane = obj.getInt("secondaryLane"),
                    iconUrl = obj.getString("iconUrl"),
                    inRealLogs = obj.optBoolean("inRealLogs", true),
                    stats = stats
                ))
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return list.sortedBy { it.name }
    }
    
    // --- ACTIONS ---

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

    // --- INFERENCE ---

    private fun runInference() {
        val session = ortSession
        val env = ortEnv
        
        if (session == null || env == null) {
            _uiState.value = _uiState.value.copy(debugText = "Inference Skipped: Session/Env null")
            return
        }
        
        val state = _uiState.value

        viewModelScope.launch(Dispatchers.Default) {
            try {
                // Using !in checks to prevent duplicates
                // AND checking h.inRealLogs for recommendations only
                val candidates = state.heroes.filter { h -> 
                    h !in state.allies && h !in state.enemies && h.inRealLogs
                }

                if (candidates.isEmpty()) {
                    withContext(Dispatchers.Main) {
                        _uiState.value = _uiState.value.copy(debugText = "No candidates allowed (inRealLogs filter)")
                    }
                    return@launch
                }

                val batchSize = candidates.size.toLong()
                val inputFeatureSize = 277L
                val totalFloats = (batchSize * inputFeatureSize).toInt()
                
                val floatBuffer = FloatBuffer.allocate(totalFloats)
                
                for (cand in candidates) {
                    val vector = buildFeatureVector(state.allies, state.enemies, cand)
                    floatBuffer.put(vector)
                }
                floatBuffer.rewind()
                
                val inputName = session.inputNames.iterator().next()
                val shape = longArrayOf(batchSize, inputFeatureSize)
                
                val tensor = OnnxTensor.createTensor(env, floatBuffer, shape)
                val result = session.run(Collections.singletonMap(inputName, tensor))
                
                // Output 1 = Probabilities (Float Tensor [Batch, 2])
                val outputTensor = result.get(1) as OnnxTensor
                val floatArray = outputTensor.floatBuffer.array() 
                
                val recs = mutableListOf<Recommendation>()
                for (i in candidates.indices) {
                    val score = floatArray[(i * 2) + 1]
                    val h = candidates[i]
                    val role = mapRole(h.primaryLane)
                    recs.add(Recommendation(h, score, role))
                }
                
                // Group by Role and take Top 5 per Role
                val groupedRecs = recs
                    .groupBy { it.role }
                    .mapValues { (_, v) -> v.sortedByDescending { it.score }.take(5) }
                
                withContext(Dispatchers.Main) {
                    _uiState.value = _uiState.value.copy(
                        recommendations = groupedRecs,
                        debugText = "Inference Done."
                    )
                }
                
                result.close()
                tensor.close()
            } catch (e: Exception) {
                e.printStackTrace()
                withContext(Dispatchers.Main) {
                    _uiState.value = _uiState.value.copy(debugText = "Inference Error: ${e.message}")
                }
            }
        }
    }

    private fun buildFeatureVector(allies: List<Hero?>, enemies: List<Hero?>, candidate: Hero): FloatArray {
        // Must match python logic exactly!
        // 1. Ally One-Hot (0-130)
        // 2. Enemy One-Hot (131-261)
        // 3. Roles (262-266)
        // 4. Candidate Stats (267-276)
        
        val vector = FloatArray(277)
        val N_HEROES = 131 // Assuming max ID 131 based on CSV/JSON
        
        // 1. Ally Context
        allies.filterNotNull().forEach { h ->
            val idx = h.id - 1
            if (idx in 0 until N_HEROES) vector[idx] = 1f
        }
        
        // 2. Enemy Context
        enemies.filterNotNull().forEach { h ->
             val idx = h.id - 1
             if (idx in 0 until N_HEROES) vector[N_HEROES + idx] = 1f
        }
        
        // 3. Roles Context
        // For simplicity in prototype, just use PrimaryLane of picked allies
        val rolesOffset = 2 * N_HEROES
        allies.filterNotNull().forEach { h ->
            // PrimaryLane: 1=Exp, 2=Mid, 3=Roam, 4=Jungle, 5=Gold
            val laneIdx = h.primaryLane - 1
            if (laneIdx in 0..4) {
                 vector[rolesOffset + laneIdx] += 1f
            }
        }
        
        // 4. Candidate Stats
        val statsOffset = rolesOffset + 5
        // candidate.stats is array of 10 floats created in JSON export
        for (i in 0 until 10) {
            if (i < candidate.stats.size) {
                vector[statsOffset + i] = candidate.stats[i]
            }
        }
        
        return vector
    }
    
    private fun mapRole(laneId: Int): String {
        return when(laneId) {
            1 -> "Exp"
            2 -> "Mid"
            3 -> "Roam"
            4 -> "Jungle"
            5 -> "Gold"
            else -> "Flex"
        }
    }
    
    override fun onCleared() {
        super.onCleared()
        ortSession?.close()
        ortEnv?.close()
    }
}
