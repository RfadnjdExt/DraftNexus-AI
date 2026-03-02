package com.draftnexus.ai.core.data.repository

import android.content.Context
import com.draftnexus.ai.core.model.Hero
import com.draftnexus.ai.core.model.Recommendation
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext
import com.draftnexus.ai.core.model.proto.HeroListProto
import com.draftnexus.ai.core.model.toDomain
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import ai.onnxruntime.OnnxTensor
import java.nio.FloatBuffer
import java.util.Collections
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DefaultHeroRepository @Inject constructor(
    @ApplicationContext private val context: Context
) : HeroRepository {

    private val _heroes = MutableStateFlow<List<Hero>>(emptyList())
    
    private var ortEnv: OrtEnvironment? = null
    private var ortSession: OrtSession? = null

    override fun getHeroes(): Flow<List<Hero>> = _heroes.asStateFlow()

    override suspend fun loadResources() = withContext(Dispatchers.IO) {
        try {
            // 1. Load Heroes Protobuf
            val inputStream = context.assets.open("heroes.pb")
            val heroListProto = HeroListProto.parseFrom(inputStream)
            val heroList = heroListProto.heroesList.map { it.toDomain() }.sortedBy { it.name }
            _heroes.value = heroList
            
            // 2. Load ONNX Model
            ortEnv = OrtEnvironment.getEnvironment()
            val modelBytes = context.assets.open("draft_model.onnx").readBytes()
            ortSession = ortEnv?.createSession(modelBytes)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }


    override suspend fun runInference(
        allies: List<Hero?>,
        enemies: List<Hero?>,
        candidates: List<Hero>
    ): Map<String, List<Recommendation>> = withContext(Dispatchers.Default) {
        val session = ortSession
        val env = ortEnv
        
        if (session == null || env == null) return@withContext emptyMap()
        if (candidates.isEmpty()) return@withContext emptyMap()

        try {
            val batchSize = candidates.size.toLong()
            val inputFeatureSize = 277L
            val totalFloats = (batchSize * inputFeatureSize).toInt()
            
            val floatBuffer = FloatBuffer.allocate(totalFloats)
            
            for (cand in candidates) {
                val vector = buildFeatureVector(allies, enemies, cand)
                floatBuffer.put(vector)
            }
            floatBuffer.rewind()
            
            val inputName = session.inputNames.iterator().next()
            val shape = longArrayOf(batchSize, inputFeatureSize)
            
            val tensor = OnnxTensor.createTensor(env, floatBuffer, shape)
            val result = session.run(Collections.singletonMap(inputName, tensor))
            
            val outputTensor = result.get(1) as OnnxTensor
            val floatArray = outputTensor.floatBuffer.array() 
            
            val recs = mutableListOf<Recommendation>()
            for (i in candidates.indices) {
                val score = floatArray[(i * 2) + 1]
                val h = candidates[i]
                val role = mapRole(h.primaryLane)
                recs.add(Recommendation(h, score, role))
            }
            
            val groupedRecs = mutableMapOf<String, MutableList<Recommendation>>()
            for (rec in recs) {
                val h = rec.hero
                // Add to primary lane
                val primaryRole = mapRole(h.primaryLane)
                groupedRecs.getOrPut(primaryRole) { mutableListOf() }.add(Recommendation(h, rec.score, primaryRole))
                // Also add to secondary lane if it exists and differs
                if (h.secondaryLane > 0 && h.secondaryLane != h.primaryLane) {
                    val secondaryRole = mapRole(h.secondaryLane)
                    groupedRecs.getOrPut(secondaryRole) { mutableListOf() }.add(Recommendation(h, rec.score, secondaryRole))
                }
            }
            val sortedRecs = groupedRecs.mapValues { (_, v) -> v.sortedByDescending { it.score }.take(5) }
            
            result.close()
            tensor.close()
            
            return@withContext sortedRecs
        } catch (e: Exception) {
            e.printStackTrace()
            return@withContext emptyMap()
        }
    }

    private fun buildFeatureVector(allies: List<Hero?>, enemies: List<Hero?>, candidate: Hero): FloatArray {
        val vector = FloatArray(277)
        val N_HEROES = 131 
        
        allies.filterNotNull().forEach { h ->
            val idx = h.id - 1
            if (idx in 0 until N_HEROES) vector[idx] = 1f
        }
        
        enemies.filterNotNull().forEach { h ->
             val idx = h.id - 1
             if (idx in 0 until N_HEROES) vector[N_HEROES + idx] = 1f
        }
        
        val rolesOffset = 2 * N_HEROES
        allies.filterNotNull().forEach { h ->
            val laneIdx = h.primaryLane - 1
            if (laneIdx in 0..4) {
                 vector[rolesOffset + laneIdx] += 1f
            }
        }
        
        val statsOffset = rolesOffset + 5
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
}
