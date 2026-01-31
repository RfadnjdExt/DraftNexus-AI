package com.draftnexus.ai

data class Hero(
    val id: Int,
    val name: String,
    val primaryLane: Int,
    val secondaryLane: Int,
    val iconUrl: String,
    val inRealLogs: Boolean = true,
    val stats: FloatArray // Raw stats for ML Input
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false

        other as Hero

        if (id != other.id) return false
        if (name != other.name) return false

        return true
    }

    override fun hashCode(): Int {
        var result = id
        result = 31 * result + name.hashCode()
        return result
    }
}
