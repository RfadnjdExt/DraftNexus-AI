package com.draftnexus.ai.core.ui

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInteropFilter
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.draftnexus.ai.core.model.*
import kotlin.math.abs

import androidx.compose.ui.composed
import androidx.compose.ui.input.pointer.pointerInteropFilter

@OptIn(ExperimentalComposeUiApi::class)
fun Modifier.windowDragGestures(
    onDrag: (dx: Float, dy: Float) -> Unit,
    onTap: (() -> Unit)? = null
): Modifier = composed {
    var rawStartX by remember { mutableFloatStateOf(0f) }
    var rawStartY by remember { mutableFloatStateOf(0f) }
    var lastRawX by remember { mutableFloatStateOf(0f) }
    var lastRawY by remember { mutableFloatStateOf(0f) }
    var isDragging by remember { mutableStateOf(false) }

    this.pointerInteropFilter { event ->
        when (event.actionMasked) {
            android.view.MotionEvent.ACTION_DOWN -> {
                rawStartX = event.rawX
                rawStartY = event.rawY
                lastRawX = event.rawX
                lastRawY = event.rawY
                isDragging = false
                true
            }
            android.view.MotionEvent.ACTION_MOVE -> {
                val dx = event.rawX - lastRawX
                val dy = event.rawY - lastRawY
                
                // Threshold to prevent tap jitter
                if (!isDragging && (abs(event.rawX - rawStartX) > 10f || abs(event.rawY - rawStartY) > 10f)) {
                    isDragging = true
                }
                
                if (isDragging) {
                    onDrag(dx, dy)
                    lastRawX = event.rawX
                    lastRawY = event.rawY
                }
                true
            }
            android.view.MotionEvent.ACTION_UP, android.view.MotionEvent.ACTION_CANCEL -> {
                if (!isDragging) {
                    onTap?.invoke()
                }
                isDragging = false
                true
            }
            else -> false
        }
    }
}

@Composable
fun DraftScreen(
    state: DraftState,
    onAllySelected: (Int, Hero?) -> Unit,
    onEnemySelected: (Int, Hero?) -> Unit,
    onBanSelected: (Int, Hero?) -> Unit,
    onClearDraft: () -> Unit,
    isOverlay: Boolean = false,
    onCloseOverlay: (() -> Unit)? = null,
    onDrag: ((Float, Float) -> Unit)? = null, // dx, dy delta
    onMinimizedChange: ((Boolean) -> Unit)? = null, // notify when minimized state changes
    onHeroSelectorVisibilityChange: ((Boolean) -> Unit)? = null // notify when hero selector opens/closes
) {
    var showHeroSelector by remember { mutableStateOf(false) }
    
    // Notify parent when hero selector visibility changes
    LaunchedEffect(showHeroSelector) {
        onHeroSelectorVisibilityChange?.invoke(showHeroSelector)
    }

    var selectionMode by remember { mutableStateOf<SelectionMode?>(null) }
    
    // Hoisted State for Hero Selector Persistence
    var selectorTabIndex by remember { mutableIntStateOf(0) }
    val selectorScrollState = androidx.compose.foundation.lazy.grid.rememberLazyGridState()
    val configuration = LocalConfiguration.current
    val isLandscape = configuration.orientation == android.content.res.Configuration.ORIENTATION_LANDSCAPE
    
    // Shrink/Expand State for Overlay
    var isMinimized by remember { mutableStateOf(false) }
    
    // Notify parent when minimized changes
    LaunchedEffect(isMinimized) {
        onMinimizedChange?.invoke(isMinimized)
    }
    
    // Snackbar state
    val snackbarHostState = remember { SnackbarHostState() }

    Box(modifier = if (isMinimized) Modifier.wrapContentSize() else Modifier.fillMaxSize()) {
        if (isMinimized) {
            // Minimized FAB State matches its visual size (64dp) exactly
            Box(
                modifier = Modifier
                    .size(64.dp)
                    .clip(CircleShape)
                    .background(Color(0xFF3EA6FF)) // YouTube Action Blue
                    .windowDragGestures(
                        onDrag = { dx, dy -> onDrag?.invoke(dx, dy) },
                        onTap = { isMinimized = false }
                    ),
                contentAlignment = Alignment.Center
            ) {
                // DraftNexus / AI Icon
                Text("DN", color = Color(0xFF0F0F0F), fontWeight = FontWeight.Bold, fontSize = 20.sp)
            }
        } else if (showHeroSelector && selectionMode != null && isOverlay) {
            // Full-screen hero selector takeover (no chrome) for maximum grid space
            HeroSelectorDialog(
                heroes = state.heroes,
                isOverlay = true,
                selectedTabIndex = selectorTabIndex,
                onTabSelected = { selectorTabIndex = it },
                lazyGridState = selectorScrollState,
                onDismiss = { showHeroSelector = false },
                onHeroSelected = { hero ->
                    val mode = selectionMode!!
                    when (mode.type) {
                        SelectionType.ALLY -> onAllySelected(mode.index, hero)
                        SelectionType.ENEMY -> onEnemySelected(mode.index, hero)
                        SelectionType.BAN -> onBanSelected(mode.index, hero)
                    }
                    showHeroSelector = false
                }
            )
         } else {
            // Expanded State with Two-Tab Layout
            var selectedTab by remember { mutableIntStateOf(0) }
            val isCompactChrome = isOverlay && isLandscape
            
            Column(modifier = Modifier.fillMaxSize()) {
                // Drag Bar (outside tabs to prevent scroll conflict)
                if (isOverlay) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = if (isCompactChrome) 4.dp else 8.dp, bottom = if (isCompactChrome) 2.dp else 4.dp)
                            .windowDragGestures(
                                onDrag = { dx, dy -> onDrag?.invoke(dx, dy) }
                            ),
                        contentAlignment = Alignment.Center
                    ) {
                        Box(
                            modifier = Modifier
                                .width(32.dp)
                                .height(4.dp)
                                .background(Color(0xFF555555), RoundedCornerShape(2.dp))
                        )
                    }
                }
            
                // Header with Overlay Controls (Sticky)
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = if (isCompactChrome) 8.dp else 16.dp)
                        .padding(vertical = if (isCompactChrome) 2.dp else 8.dp), 
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "DraftNexus AI",
                        fontSize = if (isCompactChrome) 14.sp else 18.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFFF1F1F1)
                    )
                    
                    Row(horizontalArrangement = Arrangement.spacedBy(if (isCompactChrome) 0.dp else 4.dp)) {
                        if (isOverlay) {
                            IconButton(
                                onClick = { isMinimized = true },
                                modifier = Modifier.size(if (isCompactChrome) 24.dp else 32.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.KeyboardArrowDown,
                                    contentDescription = "Minimize",
                                    tint = Color(0xFFF1F1F1),
                                    modifier = if (isCompactChrome) Modifier.size(16.dp) else Modifier
                                )
                            }
                            IconButton(
                                onClick = { onCloseOverlay?.invoke() },
                                modifier = Modifier.size(if (isCompactChrome) 24.dp else 32.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Close,
                                    contentDescription = "Close",
                                    tint = Color(0xFFF1F1F1),
                                    modifier = if (isCompactChrome) Modifier.size(16.dp) else Modifier
                                )
                            }
                        }
                        TextButton(
                            onClick = { onClearDraft() },
                            contentPadding = PaddingValues(horizontal = if (isCompactChrome) 4.dp else 8.dp, vertical = 0.dp),
                            modifier = Modifier.height(if (isCompactChrome) 24.dp else 32.dp),
                            shape = RoundedCornerShape(if (isCompactChrome) 8.dp else 16.dp)
                        ) {
                            Text("Clear", fontSize = if (isCompactChrome) 11.sp else 13.sp, fontWeight = FontWeight.Medium, color = Color(0xFF3EA6FF))
                        }
                    }
                }

                // ===== TAB CONTENT =====
                Box(modifier = Modifier.weight(1f)) {
                    when (selectedTab) {
                        0 -> {
                            // === DRAFT TAB ===
                            val isCompact = isOverlay && isLandscape
                            Column(
                                modifier = Modifier
                                    .fillMaxSize()
                                    .padding(horizontal = if (isCompact) 6.dp else 12.dp)
                            ) {
                                // Banned Heroes
                                Text("Banned", color = Color(0xFFAAAAAA), fontSize = if (isCompact) 9.sp else 12.sp, fontWeight = FontWeight.Medium, modifier = Modifier.padding(bottom = if (isCompact) 2.dp else 6.dp))
                                LazyRow(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(if (isCompact) 3.dp else 6.dp)
                                ) {
                                    items(10) { idx ->
                                        val hero = state.bans.getOrNull(idx)
                                        HeroSlot(
                                            hero = hero,
                                            compact = isCompact,
                                            onClick = {
                                                selectionMode = SelectionMode(SelectionType.BAN, idx)
                                                showHeroSelector = true
                                            },
                                            modifier = Modifier.width(if (isCompact) 36.dp else 56.dp)
                                        )
                                    }
                                }
                                Spacer(modifier = Modifier.height(if (isCompact) 4.dp else 12.dp))
                                
                                // Enemy Team  
                                Text("Enemy", color = Color(0xFFAAAAAA), fontSize = if (isCompact) 9.sp else 12.sp, fontWeight = FontWeight.Medium, modifier = Modifier.padding(bottom = if (isCompact) 2.dp else 6.dp))
                                TeamRow(
                                    heroes = state.enemies,
                                    isAlly = false,
                                    compact = isCompact,
                                    onSlotClick = { idx ->
                                        selectionMode = SelectionMode(SelectionType.ENEMY, idx)
                                        showHeroSelector = true
                                    }
                                )
                                Spacer(modifier = Modifier.height(if (isCompact) 4.dp else 12.dp))

                                // Allied Team
                                Text("Ally", color = Color(0xFFAAAAAA), fontSize = if (isCompact) 9.sp else 12.sp, fontWeight = FontWeight.Medium, modifier = Modifier.padding(bottom = if (isCompact) 2.dp else 6.dp))
                                TeamRow(
                                    heroes = state.allies,
                                    isAlly = true,
                                    compact = isCompact,
                                    onSlotClick = { idx ->
                                        selectionMode = SelectionMode(SelectionType.ALLY, idx)
                                        showHeroSelector = true
                                    }
                                )
                                Spacer(modifier = Modifier.height(if (isCompact) 2.dp else 8.dp))

                                Text("Debug: ${state.debugText}", color = Color.Yellow, fontSize = if (isCompact) 7.sp else 9.sp)
                            }
                        }
                        1 -> {
                            // === RECS TAB ===
                            val isCompact = isOverlay && isLandscape
                            if (isCompact) {
                                // Compact: Column, no scroll, all 5 lanes evenly distributed
                                Column(
                                    modifier = Modifier
                                        .fillMaxSize()
                                        .padding(horizontal = 6.dp),
                                    verticalArrangement = Arrangement.spacedBy(2.dp)
                                ) {
                                    if (state.recommendations.isEmpty()) {
                                        Box(
                                            modifier = Modifier.fillMaxSize(),
                                            contentAlignment = Alignment.Center
                                        ) {
                                            Text("Select heroes in Draft tab\nto get AI suggestions", color = Color(0xFFAAAAAA), fontSize = 11.sp, textAlign = TextAlign.Center)
                                        }
                                    } else {
                                        val lanes = listOf("Exp", "Jungle", "Mid", "Gold", "Roam")
                                        lanes.forEach { lane ->
                                            val recs = state.recommendations[lane]
                                            if (!recs.isNullOrEmpty()) {
                                                Row(
                                                    modifier = Modifier
                                                        .fillMaxWidth()
                                                        .weight(1f),
                                                    verticalAlignment = Alignment.CenterVertically,
                                                    horizontalArrangement = Arrangement.spacedBy(3.dp)
                                                ) {
                                                    Text(
                                                        text = lane,
                                                        color = Color(0xFFAAAAAA),
                                                        fontSize = 8.sp,
                                                        fontWeight = FontWeight.Bold,
                                                        modifier = Modifier.width(30.dp)
                                                    )
                                                    val recsToShow = recs.take(3)
                                                    recsToShow.forEach { rec ->
                                                        RecommendationCard(
                                                            rec = rec,
                                                            compact = true,
                                                            modifier = Modifier.weight(1f),
                                                            onClick = {
                                                                val emptySlot = state.allies.indexOfFirst { it == null }
                                                                if (emptySlot != -1) {
                                                                    onAllySelected(emptySlot, rec.hero)
                                                                }
                                                            }
                                                        )
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            } else {
                                // Normal: LazyColumn with spacious layout
                                LazyColumn(
                                    modifier = Modifier
                                        .fillMaxSize()
                                        .padding(horizontal = 12.dp)
                                ) {
                                    if (state.recommendations.isEmpty()) {
                                        item {
                                            Box(
                                                modifier = Modifier
                                                    .fillMaxWidth()
                                                    .padding(vertical = 32.dp),
                                                contentAlignment = Alignment.Center
                                            ) {
                                                Text("Select heroes in Draft tab\nto get AI suggestions", color = Color(0xFFAAAAAA), fontSize = 14.sp, textAlign = TextAlign.Center)
                                            }
                                        }
                                    } else {
                                        val lanes = listOf("Exp", "Jungle", "Mid", "Gold", "Roam")
                                        items(lanes) { lane ->
                                            val recs = state.recommendations[lane]
                                            if (!recs.isNullOrEmpty()) {
                                                Text(
                                                    text = lane,
                                                    color = Color(0xFFF1F1F1),
                                                    fontSize = 13.sp,
                                                    fontWeight = FontWeight.Bold,
                                                    modifier = Modifier.padding(vertical = 6.dp)
                                                )
                                                Row(
                                                    modifier = Modifier.fillMaxWidth(),
                                                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                                                ) {
                                                    val recsToShow = recs.take(3)
                                                    recsToShow.forEach { rec ->
                                                        RecommendationCard(
                                                            rec = rec,
                                                            modifier = Modifier.weight(1f),
                                                            onClick = {
                                                                val emptySlot = state.allies.indexOfFirst { it == null }
                                                                if (emptySlot != -1) {
                                                                    onAllySelected(emptySlot, rec.hero)
                                                                }
                                                            }
                                                        )
                                                    }
                                                }
                                                Spacer(modifier = Modifier.height(4.dp))
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    // Show Selector for non-overlay mode
                    if (showHeroSelector && selectionMode != null && !isOverlay) {
                        HeroSelectorDialog(
                            heroes = state.heroes,
                            isOverlay = false,
                            selectedTabIndex = selectorTabIndex,
                            onTabSelected = { selectorTabIndex = it },
                            lazyGridState = selectorScrollState,
                            onDismiss = { showHeroSelector = false },
                            onHeroSelected = { hero ->
                                val mode = selectionMode!!
                                when (mode.type) {
                                    SelectionType.ALLY -> onAllySelected(mode.index, hero)
                                    SelectionType.ENEMY -> onEnemySelected(mode.index, hero)
                                    SelectionType.BAN -> onBanSelected(mode.index, hero)
                                }
                                showHeroSelector = false
                            }
                        )
                    }
                } // End Tab Content Box

                // ===== BOTTOM TAB BAR =====
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(Color(0xFF181818))
                        .padding(horizontal = if (isLandscape && isOverlay) 8.dp else 16.dp, vertical = if (isLandscape && isOverlay) 2.dp else 6.dp),
                    horizontalArrangement = Arrangement.spacedBy(if (isLandscape && isOverlay) 4.dp else 8.dp)
                ) {
                    // Draft Tab
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .background(
                                color = if (selectedTab == 0) Color(0xFFF1F1F1) else Color(0xFF272727),
                                shape = RoundedCornerShape(if (isLandscape && isOverlay) 12.dp else 20.dp)
                            )
                            .clickable { selectedTab = 0 }
                            .padding(vertical = if (isLandscape && isOverlay) 4.dp else 10.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            "Draft",
                            fontSize = if (isLandscape && isOverlay) 11.sp else 13.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (selectedTab == 0) Color(0xFF0F0F0F) else Color(0xFFF1F1F1)
                        )
                    }
                    // Recs Tab
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .background(
                                color = if (selectedTab == 1) Color(0xFF3EA6FF) else Color(0xFF272727),
                                shape = RoundedCornerShape(if (isLandscape && isOverlay) 12.dp else 20.dp)
                            )
                            .clickable { selectedTab = 1 }
                            .padding(vertical = if (isLandscape && isOverlay) 4.dp else 10.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                            Text(
                                "Recs",
                                fontSize = if (isLandscape && isOverlay) 11.sp else 13.sp,
                                fontWeight = FontWeight.Bold,
                                color = if (selectedTab == 1) Color(0xFF0F0F0F) else Color(0xFFF1F1F1)
                            )
                            if (state.recommendations.isNotEmpty()) {
                                Box(
                                    modifier = Modifier
                                        .size(if (isLandscape && isOverlay) 6.dp else 8.dp)
                                        .background(
                                            color = if (selectedTab == 1) Color(0xFF0F0F0F) else Color(0xFF3EA6FF),
                                            shape = CircleShape
                                        )
                                )
                            }
                        }
                    }
                }
            } // End Column for Expanded view
        } // End isMinimized else block
        
        // Snackbar Host
        SnackbarHost(
            hostState = snackbarHostState,
            modifier = Modifier.align(Alignment.BottomCenter)
        )
    }
}

@Composable
fun TeamRow(heroes: List<Hero?>, isAlly: Boolean, onSlotClick: (Int) -> Unit, compact: Boolean = false) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(if (compact) 3.dp else 4.dp)
    ) {
        for (i in 0 until 5) {
            val hero = heroes.getOrNull(i)
            HeroSlot(hero, compact = compact, onClick = { onSlotClick(i) }, modifier = Modifier.weight(1f))
        }
    }
}

@Composable
fun HeroSlot(hero: Hero?, onClick: () -> Unit, modifier: Modifier = Modifier, compact: Boolean = false) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = modifier
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .aspectRatio(if (compact) 1f else 0.75f)
                .clip(RoundedCornerShape(if (compact) 4.dp else 8.dp))
                .background(if (hero != null) Color(0xFF212121) else Color(0xFF272727))
                .clickable { onClick() },
            contentAlignment = Alignment.Center
        ) {
            if (hero != null) {
                AsyncImage(
                    model = hero.iconUrl,
                    contentDescription = hero.name,
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop
                )
            } else {
                Text("+", color = Color(0xFFAAAAAA), fontSize = if (compact) 14.sp else 24.sp, fontWeight = FontWeight.Light)
            }
        }
        if (!compact) {
            Text(
                text = hero?.name ?: "Empty",
                fontSize = 11.sp,
                color = if (hero != null) Color(0xFFF1F1F1) else Color(0xFFAAAAAA),
                fontWeight = if (hero != null) FontWeight.Medium else FontWeight.Normal,
                maxLines = 1,
                modifier = Modifier.padding(top = 6.dp)
            )
        }
    }
}

@Composable
fun RecommendationCard(rec: Recommendation, modifier: Modifier = Modifier, compact: Boolean = false, onClick: () -> Unit) {
    val scoreColor = when {
        rec.score >= 0.8f -> Color(0xFF2BA640)
        rec.score >= 0.6f -> Color(0xFFD4B237)
        else -> Color(0xFFC45E3B)
    }
    
    Column(
        modifier = modifier
            .background(Color(0xFF212121), RoundedCornerShape(if (compact) 4.dp else 12.dp))
            .clip(RoundedCornerShape(if (compact) 4.dp else 12.dp))
            .clickable { onClick() }
            .padding(if (compact) 3.dp else 8.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .aspectRatio(1f)
                .clip(RoundedCornerShape(if (compact) 3.dp else 8.dp))
        ) {
            AsyncImage(
                model = rec.hero.iconUrl,
                contentDescription = rec.hero.name,
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop
            )
        }
        if (compact) {
            Text(
                text = "${(rec.score * 100).toInt()}%",
                color = scoreColor,
                fontWeight = FontWeight.Bold,
                fontSize = 8.sp,
                modifier = Modifier.padding(top = 1.dp)
            )
        } else {
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = rec.hero.name, 
                fontWeight = FontWeight.Medium, 
                fontSize = 12.sp, 
                maxLines = 1,
                color = Color(0xFFF1F1F1)
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = "${(rec.score * 100).toInt()}% Match",
                color = scoreColor,
                fontWeight = FontWeight.Normal,
                fontSize = 10.sp
            )
        }
    }
} 

@Composable
fun HeroSelectorDialog(
    heroes: List<Hero>,
    isOverlay: Boolean,
    selectedTabIndex: Int,
    onTabSelected: (Int) -> Unit,
    lazyGridState: androidx.compose.foundation.lazy.grid.LazyGridState,
    onDismiss: () -> Unit,
    onHeroSelected: (Hero?) -> Unit
) {
    val tabs = listOf("All", "Exp", "Mid", "Roam", "Jungle", "Gold")
    val laneIds = listOf(0, 1, 2, 3, 4, 5)

    val filteredHeroes = remember(selectedTabIndex, heroes) {
        val targetLane = laneIds[selectedTabIndex]
        if (targetLane == 0) heroes.sortedBy { it.name }
        else heroes.filter { it.primaryLane == targetLane || it.secondaryLane == targetLane }.sortedBy { it.name }
    }

    val configuration = LocalConfiguration.current
    val isLandscape = configuration.orientation == android.content.res.Configuration.ORIENTATION_LANDSCAPE

    val content = @Composable { modifier: Modifier ->
        Column(
            modifier = modifier.padding(horizontal = 0.dp, vertical = if (isLandscape && isOverlay) 2.dp else 8.dp)
        ) {
            // YouTube-style Chips for Tabs
            LazyRow(
                modifier = Modifier.fillMaxWidth(),
                contentPadding = PaddingValues(horizontal = if (isLandscape && isOverlay) 8.dp else 16.dp),
                horizontalArrangement = Arrangement.spacedBy(if (isLandscape && isOverlay) 4.dp else 8.dp)
            ) {
                items(tabs.size) { index ->
                    val isSelected = selectedTabIndex == index
                    Box(
                        modifier = Modifier
                            .background(
                                color = if (isSelected) Color(0xFFF1F1F1) else Color(0xFF272727),
                                shape = RoundedCornerShape(if (isLandscape && isOverlay) 12.dp else 16.dp)
                            )
                            .clickable { onTabSelected(index) }
                            .padding(
                                horizontal = if (isLandscape && isOverlay) 10.dp else 16.dp,
                                vertical = if (isLandscape && isOverlay) 4.dp else 8.dp
                            )
                    ) {
                        Text(
                            text = tabs[index],
                            fontSize = if (isLandscape && isOverlay) 11.sp else 13.sp,
                            fontWeight = FontWeight.Medium,
                            color = if (isSelected) Color(0xFF0F0F0F) else Color(0xFFF1F1F1)
                        )
                    }
                }
            }
            
            if (!isLandscape || !isOverlay) {
                Spacer(modifier = Modifier.height(16.dp))
            }

            LazyVerticalGrid(
                state = lazyGridState,
                columns = if (isOverlay && isLandscape) GridCells.Fixed(5) else GridCells.Fixed(4),
                contentPadding = PaddingValues(
                    horizontal = if (isLandscape && isOverlay) 8.dp else 16.dp,
                    vertical = if (isLandscape && isOverlay) 4.dp else 8.dp
                ),
                verticalArrangement = Arrangement.spacedBy(if (isLandscape && isOverlay) 6.dp else 16.dp),
                horizontalArrangement = Arrangement.spacedBy(if (isLandscape && isOverlay) 6.dp else 12.dp),
                modifier = if (isOverlay) Modifier.weight(1f) else Modifier.height(500.dp)
            ) {
                items(filteredHeroes, key = { it.id }) { hero ->
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier
                            .clickable { onHeroSelected(hero) }
                    ) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .aspectRatio(1f)
                                .clip(RoundedCornerShape(if (isLandscape && isOverlay) 6.dp else 8.dp))
                                .background(Color(0xFF272727))
                        ) {
                            AsyncImage(
                                model = hero.iconUrl,
                                contentDescription = hero.name,
                                modifier = Modifier.fillMaxSize(),
                                contentScale = ContentScale.Crop
                            )
                        }
                        if (!isLandscape || !isOverlay) {
                            Spacer(modifier = Modifier.height(6.dp))
                            Text(
                                text = hero.name, 
                                fontSize = 11.sp, 
                                maxLines = 1, 
                                textAlign = TextAlign.Center, 
                                color = Color(0xFFF1F1F1),
                                modifier = Modifier.fillMaxWidth()
                            )
                        }
                    }
                }
            }
            
            // Custom Buttons Row - compact in landscape
            Row(
                 modifier = Modifier.fillMaxWidth().padding(
                     horizontal = if (isLandscape && isOverlay) 8.dp else 16.dp,
                     vertical = if (isLandscape && isOverlay) 2.dp else 8.dp
                 ),
                 horizontalArrangement = Arrangement.SpaceBetween
            ) {
                TextButton(
                    onClick = { onHeroSelected(null) },
                    contentPadding = if (isLandscape && isOverlay) PaddingValues(horizontal = 8.dp, vertical = 0.dp) else PaddingValues(horizontal = 16.dp, vertical = 8.dp)
                ) {
                    Text("Remove", color = Color(0xFFCF6679), fontSize = if (isLandscape && isOverlay) 12.sp else 14.sp)
                }
                
                TextButton(
                    onClick = onDismiss,
                    contentPadding = if (isLandscape && isOverlay) PaddingValues(horizontal = 8.dp, vertical = 0.dp) else PaddingValues(horizontal = 16.dp, vertical = 8.dp)
                ) {
                    Text("Cancel", color = Color(0xFFF1F1F1), fontSize = if (isLandscape && isOverlay) 12.sp else 14.sp)
                }
            }
        }
    }

    if (isOverlay) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = 0.5f))
                .clickable { onDismiss() },
            contentAlignment = Alignment.BottomCenter
        ) {
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .fillMaxHeight()
                    .clickable(enabled = false) {},
                color = Color(0xFF212121)
            ) {
                Column(modifier = Modifier.fillMaxSize()) {
                    // Compact header: title only, no drag handle in landscape
                    if (!isLandscape) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 6.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Box(
                                modifier = Modifier
                                    .width(36.dp)
                                    .height(4.dp)
                                    .background(Color(0xFF555555), RoundedCornerShape(2.dp))
                            )
                        }
                    }
                    Text(
                        "Select Hero", 
                        color = Color(0xFFF1F1F1), 
                        fontSize = if (isLandscape) 13.sp else 16.sp, 
                        fontWeight = FontWeight.Bold, 
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = if (isLandscape) 2.dp else 4.dp)
                    )
                    content(Modifier.weight(1f))
                }
            }
        }
    } else {
        AlertDialog(
            onDismissRequest = onDismiss,
            title = { Text("Select Hero", color = Color.White) }, 
            text = { content(Modifier) },
            confirmButton = {}, 
            dismissButton = {}, 
            containerColor = Color(0xFF333333)
        )
    }
}

enum class SelectionType { ALLY, ENEMY, BAN }
data class SelectionMode(val type: SelectionType, val index: Int)
