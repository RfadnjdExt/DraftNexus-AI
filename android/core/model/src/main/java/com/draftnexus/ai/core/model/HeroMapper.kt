package com.draftnexus.ai.core.model

import com.draftnexus.ai.core.model.proto.HeroProto

fun HeroProto.toDomain(): Hero {
    return Hero(
        id = id,
        name = name,
        primaryLane = primaryLane,
        secondaryLane = secondaryLane,
        iconUrl = iconUrl,
        inRealLogs = inRealLogs,
        stats = statsList.toFloatArray()
    )
}

fun Hero.toProto(): HeroProto {
    return HeroProto.newBuilder()
        .setId(id)
        .setName(name)
        .setPrimaryLane(primaryLane)
        .setSecondaryLane(secondaryLane)
        .setIconUrl(iconUrl)
        .setInRealLogs(inRealLogs)
        .addAllStats(stats.toList())
        .build()
}
